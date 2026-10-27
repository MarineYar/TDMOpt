"""Four TN formulations bound to one canonical physical network.

All powers are MW/MVAr. The AC edge expressions use Vi*conj(Vj), and
charging/transformer losses remain inside each independent branch record.
"""
from __future__ import annotations
import math
from collections.abc import Callable
import pyomo.environ as pyo
from .network_math import branch_admittance

COMPONENTS = {'TN_DCOPF', 'TN_LINEARIZED_ACOPF', 'TN_ACOPF_SOCP', 'TN_ACOPF_FULL'}


def build_tn_network(model: pyo.ConcreteModel, block: pyo.Block, network: dict,
                     component_id: str, injection: Callable) -> None:
    if component_id not in COMPONENTS:
        raise ValueError(f'unsupported TN component {component_id}')
    buses = {b['id']: b for b in network['buses']}
    branches = {b['id']: b for b in network['branches']}
    if len(branches) != len(network['branches']):
        raise ValueError('duplicate branch IDs')
    base = network['base_mva']; ref = network['reference_bus']
    dc = component_id == 'TN_DCOPF'
    linear = component_id == 'TN_LINEARIZED_ACOPF'
    full = component_id == 'TN_ACOPF_FULL'
    block._component_id = component_id
    block._represented_quantities = ['P', 'theta'] if dc else ['P', 'Q', 'V']
    block._formulation_notes = {
        'TN_DCOPF': 'DC x/tap/shift; fixed unit voltage for active shunt; no model Q or V',
        'TN_LINEARIZED_ACOPF': 'Fixed first-order AC pi-model expansion at source vm/va; no optimal-point data',
        'TN_ACOPF_SOCP': 'Edge W conic relaxation; no fabricated recovered bus angles or cycle exactness',
        'TN_ACOPF_FULL': 'Exact rectangular AC pi model',
    }[component_id]
    block.BUS = pyo.Set(initialize=list(buses), ordered=True)
    block.BR = pyo.Set(initialize=list(branches), ordered=True)
    block.pf = pyo.Var(block.BR, model.T, initialize=0.)
    block.pt = pyo.Var(block.BR, model.T, initialize=0.)
    if not dc:
        block.qf = pyo.Var(block.BR, model.T, initialize=0.)
        block.qt = pyo.Var(block.BR, model.T, initialize=0.)
    reference_angle = math.radians(buses[ref].get('va_degree', 0.))
    v0 = {bid: bus.get('vm_pu', 1.) for bid, bus in buses.items()}
    theta0 = {bid: math.radians(bus.get('va_degree', 0.))-reference_angle for bid, bus in buses.items()}
    if full:
        block.e = pyo.Var(block.BUS, model.T, bounds=lambda _, b, t: (-buses[b]['v_max_pu'], buses[b]['v_max_pu']),
                          initialize=lambda _, b, t: v0[b]*math.cos(theta0[b]))
        block.f = pyo.Var(block.BUS, model.T, bounds=lambda _, b, t: (-buses[b]['v_max_pu'], buses[b]['v_max_pu']),
                          initialize=lambda _, b, t: v0[b]*math.sin(theta0[b]))
        block.u = pyo.Expression(block.BUS, model.T, rule=lambda _, b, t: block.e[b,t]**2+block.f[b,t]**2)
        block.voltage = pyo.Constraint(block.BUS, model.T, rule=lambda _, b, t: (buses[b]['v_min_pu']**2, block.u[b,t], buses[b]['v_max_pu']**2))
        for t in model.T:
            block.f[ref,t].fix(0.); block.e[ref,t].setlb(0.)
    elif dc or linear:
        block.theta = pyo.Var(block.BUS, model.T, initialize=lambda _, b, t: theta0[b])
        for t in model.T:
            block.theta[ref,t].fix(0.)
        if linear:
            block.v = pyo.Var(block.BUS, model.T, bounds=lambda _, b, t: (buses[b]['v_min_pu'], buses[b]['v_max_pu']),
                              initialize=lambda _, b, t: v0[b])
            block.u = pyo.Expression(block.BUS, model.T, rule=lambda _, b, t: v0[b]**2+2*v0[b]*(block.v[b,t]-v0[b]))
            block._linearization_point = {b: {'vm_pu': v0[b], 'va_radian': theta0[b]} for b in buses}
    else:
        block.u = pyo.Var(block.BUS, model.T, bounds=lambda _, b, t: (buses[b]['v_min_pu']**2, buses[b]['v_max_pu']**2),
                          initialize=lambda _, b, t: v0[b]**2)
        def w_init(edge: str, imag: bool) -> float:
            i,j=branches[edge]['from_bus'],branches[edge]['to_bus']
            angle=theta0[i]-theta0[j]
            return v0[i]*v0[j]*(math.sin(angle) if imag else math.cos(angle))
        def w_bound(_, edge, t):
            i,j=branches[edge]['from_bus'],branches[edge]['to_bus']
            bound=buses[i]['v_max_pu']*buses[j]['v_max_pu']
            return -bound,bound
        block.wr=pyo.Var(block.BR, model.T, bounds=w_bound, initialize=lambda _,e,t:w_init(e,False))
        block.wi=pyo.Var(block.BR, model.T, bounds=w_bound, initialize=lambda _,e,t:w_init(e,True))
        block.conic=pyo.Constraint(block.BR, model.T, rule=lambda _,e,t:
            block.wr[e,t]**2+block.wi[e,t]**2 <= block.u[branches[e]['from_bus'],t]*block.u[branches[e]['to_bus'],t]
            if branches[e]['status'] else pyo.Constraint.Skip)
        # Parallel physical circuits share the same voltage product. Reverse
        # orientation conjugates its imaginary part; branch flows stay separate.
        pairs={};block.parallel_real=pyo.ConstraintList();block.parallel_imag=pyo.ConstraintList()
        for edge,branch in branches.items():
            if not branch['status']: continue
            i,j=branch['from_bus'],branch['to_bus'];key=frozenset((i,j))
            if key in pairs:
                other,oi,oj=pairs[key];sign=1 if (i,j)==(oi,oj) else -1
                for t in model.T:
                    block.parallel_real.add(block.wr[edge,t]==block.wr[other,t])
                    block.parallel_imag.add(block.wi[edge,t]==sign*block.wi[other,t])
            else: pairs[key]=(edge,i,j)
    for edge,branch in branches.items():
        if not branch['status']:
            for t in model.T:
                block.pf[edge,t].fix(0.);block.pt[edge,t].fix(0.)
                if not dc:
                    block.qf[edge,t].fix(0.);block.qt[edge,t].fix(0.)
                if not (dc or linear or full):
                    block.wr[edge,t].fix(0.);block.wi[edge,t].fix(0.)
    if dc:
        for branch in branches.values():
            if branch['status'] and branch['x_pu']==0:
                raise ValueError('DC formulation cannot represent a zero-X in-service branch')
        def dc_flow(_,edge,t):
            branch=branches[edge]
            if not branch['status']:return pyo.Constraint.Skip
            f,to=branch['from_bus'],branch['to_bus']
            return block.pf[edge,t]==base/(branch['x_pu']*(branch.get('tap',1.) or 1.))*(block.theta[f,t]-block.theta[to,t]-math.radians(branch.get('shift_degree',0.)))
        block.flow_from_p=pyo.Constraint(block.BR,model.T,rule=dc_flow)
        block.flow_to_p=pyo.Constraint(block.BR,model.T,rule=lambda _,e,t: block.pt[e,t]==-block.pf[e,t] if branches[e]['status'] else pyo.Constraint.Skip)
    else:
        def voltage_product(edge,t):
            branch=branches[edge];i,j=branch['from_bus'],branch['to_bus']
            if full:
                return block.e[i,t]*block.e[j,t]+block.f[i,t]*block.f[j,t], block.f[i,t]*block.e[j,t]-block.e[i,t]*block.f[j,t]
            if linear:
                vi,vj=v0[i],v0[j];delta0=theta0[i]-theta0[j]
                c,s=math.cos(delta0),math.sin(delta0)
                dv= vj*(block.v[i,t]-vi)+vi*(block.v[j,t]-vj)
                delta=block.theta[i,t]-block.theta[j,t]-delta0
                return vi*vj*c+c*dv-vi*vj*s*delta, vi*vj*s+s*dv+vi*vj*c*delta
            return block.wr[edge,t],block.wi[edge,t]
        coeffs={edge:branch_admittance(branch) for edge,branch in branches.items()}
        def edge_expression(edge,t,quantity,side):
            branch=branches[edge];i,j=branch['from_bus'],branch['to_bus'];wr,wi=voltage_product(edge,t)
            ff,ft,tf,tt=coeffs[edge]
            if side=='from' and quantity=='p': value=ff.real*block.u[i,t]+ft.real*wr+ft.imag*wi
            elif side=='from': value=-ff.imag*block.u[i,t]-ft.imag*wr+ft.real*wi
            elif quantity=='p':value=tt.real*block.u[j,t]+tf.real*wr-tf.imag*wi
            else:value=-tt.imag*block.u[j,t]-tf.imag*wr-tf.real*wi
            return base*value
        def flow_rule(quantity,side):
            variable=getattr(block,('p' if quantity=='p' else 'q')+('f' if side=='from' else 't'))
            return lambda _,e,t: variable[e,t]==edge_expression(e,t,quantity,side) if branches[e]['status'] else pyo.Constraint.Skip
        block.flow_from_p=pyo.Constraint(block.BR,model.T,rule=flow_rule('p','from'))
        block.flow_from_q=pyo.Constraint(block.BR,model.T,rule=flow_rule('q','from'))
        block.flow_to_p=pyo.Constraint(block.BR,model.T,rule=flow_rule('p','to'))
        block.flow_to_q=pyo.Constraint(block.BR,model.T,rule=flow_rule('q','to'))
    outgoing={bus:[] for bus in buses};incoming={bus:[] for bus in buses}
    for edge,branch in branches.items():
        outgoing[branch['from_bus']].append(edge);incoming[branch['to_bus']].append(edge)
    def balance_p(_,b,t):
        outgoing_p=sum(block.pf[e,t] for e in outgoing[b])+sum(block.pt[e,t] for e in incoming[b])
        return outgoing_p==injection(b,t,'p')-buses[b].get('gs_mw',0.)*(1. if dc else block.u[b,t])
    block.balance_p=pyo.Constraint(block.BUS,model.T,rule=balance_p)
    if not dc:
        block.balance_q=pyo.Constraint(block.BUS,model.T,rule=lambda _,b,t:
            sum(block.qf[e,t] for e in outgoing[b])+sum(block.qt[e,t] for e in incoming[b])==injection(b,t,'q')+buses[b].get('bs_mvar',0.)*block.u[b,t])
    # Source angle limits are raw bus-angle differences, not differences with
    # transformer shift subtracted. W inequalities enforce both sector edges.
    for edge,branch in branches.items():
        lo,hi=branch.get('ang_min_degree',-360.),branch.get('ang_max_degree',360.)
        if not (dc or linear) and branch['status'] and not (lo<=-180 and hi>=180) and hi-lo>180:
            raise ValueError('AC W angle sector wider than 180 degrees is unsupported')
    def angle_rule(upper):
        def rule(_,edge,t):
            branch=branches[edge];lo,hi=branch.get('ang_min_degree',-360.),branch.get('ang_max_degree',360.)
            if not branch['status'] or (lo<=-180 and hi>=180):return pyo.Constraint.Skip
            i,j=branch['from_bus'],branch['to_bus'];angle=math.radians(hi if upper else lo)
            if dc or linear:
                expression=block.theta[i,t]-block.theta[j,t]
                return expression<=angle if upper else expression>=angle
            wr,wi=voltage_product(edge,t);expression=wi*math.cos(angle)-wr*math.sin(angle)
            return expression<=0 if upper else expression>=0
        return rule
    block.angle_upper=pyo.Constraint(block.BR,model.T,rule=angle_rule(True))
    block.angle_lower=pyo.Constraint(block.BR,model.T,rule=angle_rule(False))
    if dc:
        block.thermal_from=pyo.Constraint(block.BR,model.T,rule=lambda _,e,t:
            (-branches[e]['rate_mva'],block.pf[e,t],branches[e]['rate_mva']) if branches[e]['status'] and branches[e]['rate_mva'] is not None else pyo.Constraint.Skip)
        block.thermal_to=pyo.Constraint(block.BR,model.T,rule=lambda _,e,t:
            (-branches[e]['rate_mva'],block.pt[e,t],branches[e]['rate_mva']) if branches[e]['status'] and branches[e]['rate_mva'] is not None else pyo.Constraint.Skip)
    elif linear:
        block.FACET=pyo.RangeSet(0,15)
        def thermal_rule(from_side):
            pvar,qvar=(block.pf,block.qf) if from_side else (block.pt,block.qt)
            return lambda _,e,t,k: math.cos(2*math.pi*k/16)*pvar[e,t]+math.sin(2*math.pi*k/16)*qvar[e,t] <= branches[e]['rate_mva']*math.cos(math.pi/16) if branches[e]['status'] and branches[e]['rate_mva'] is not None else pyo.Constraint.Skip
        block.thermal_from=pyo.Constraint(block.BR,model.T,block.FACET,rule=thermal_rule(True))
        block.thermal_to=pyo.Constraint(block.BR,model.T,block.FACET,rule=thermal_rule(False))
        block._thermal_approximation='conservative_inscribed_16_polygon'
    else:
        block.thermal_from=pyo.Constraint(block.BR,model.T,rule=lambda _,e,t:
            block.pf[e,t]**2+block.qf[e,t]**2<=branches[e]['rate_mva']**2 if branches[e]['status'] and branches[e]['rate_mva'] is not None else pyo.Constraint.Skip)
        block.thermal_to=pyo.Constraint(block.BR,model.T,rule=lambda _,e,t:
            block.pt[e,t]**2+block.qt[e,t]**2<=branches[e]['rate_mva']**2 if branches[e]['status'] and branches[e]['rate_mva'] is not None else pyo.Constraint.Skip)
