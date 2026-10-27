"""Exact receiving-end series-impedance OLTC equations, in explicit units.

Independent AC replay constructs its own two-port admittance from case records;
this module only implements optimization equations and initialization.
"""
from __future__ import annotations
import math
from typing import Any
import pyomo.environ as pyo

def source_bus_voltage(case: dict, network: str, bus: Any) -> float:
    """Explicit source voltage for a state absent from DC; never an optimized V."""
    record = next(b for n in case['networks'] if n['id'] == network
                  for b in n['buses'] if b['id'] == bus)
    value = record.get('vm_pu')
    if value is None or not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError(f'missing/nonpositive source bus voltage: {network}:{bus}')
    return float(value)

MODEL = 'series_impedance_oltc_v1'


def parameters(record: dict, base_mva: float) -> dict:
    rating=float(record['s_rating_mva']);r=float(record['physical_replay_vkr_percent'])/100.
    z=float(record['physical_replay_vk_percent'])/100.
    if rating<=0 or base_mva<=0 or not math.isfinite(r+z+rating+base_mva) or z<=0 or r<0 or z<r:
        raise ValueError('invalid series interface impedance/base/rating')
    if any(record.get(k,0.) for k in ('iron_loss_kw','no_load_current_percent','shift_degree','b_pu')):
        raise ValueError('series interface requires zero shift/charging/iron loss/magnetizing current')
    return dict(base_mva=base_mva,r_pu=r*base_mva/rating,x_pu=math.sqrt(z*z-r*r)*base_mva/rating)


def add_endpoint_variables(m: Any) -> None:
    base=float(next(n['base_mva'] for n in m._case_data['networks'] if n['layer']=='TN'))
    m._interface_parameters={r:parameters(p,base) for r,p in m._ports.items()}
    def bounds(m,r,t):return (-m._ports[r]['s_rating_mva'],m._ports[r]['s_rating_mva'])
    m.port_from_p=pyo.Var(m.PORT,m.T,bounds=bounds,initialize=0.)
    m.port_from_q=pyo.Var(m.PORT,m.T,bounds=bounds,initialize=0.)
    m.port_ell=pyo.Var(m.PORT,m.T,within=pyo.NonNegativeReals,initialize=0.)
    m.port_from_rating=pyo.Constraint(m.PORT,m.T,rule=lambda m,r,t:m.port_from_p[r,t]**2+m.port_from_q[r,t]**2<=m._ports[r]['s_rating_mva']**2)
    m.port_to_rating=pyo.Constraint(m.PORT,m.T,rule=lambda m,r,t:m.port_p[r,t]**2+m.port_q[r,t]**2<=m._ports[r]['s_rating_mva']**2)


def parent_voltage_squared(m: Any, record: dict, time: Any) -> Any:
    """Use represented TN voltage or the explicitly transferred boundary state."""
    if record['parent_network'] not in m.network:
        profile = m._case_scenario.get('_boundary_voltage', {}).get(record['id'])
        if profile is None:
            raise ValueError(f"missing parent-voltage exchange for {record['id']}")
        return float(profile[list(m.T).index(time)])**2
    block = m.network[record['parent_network']]
    if hasattr(block, 'v'):
        return block.v[record['parent_bus'], time]**2
    if hasattr(block, 'u'):
        return block.u[record['parent_bus'], time]
    return source_bus_voltage(m._case_data, record['parent_network'], record['parent_bus'])**2


def add_dc_reactive_capacity(m: Any) -> None:
    """DC has no Q-flow model; bound its declared aggregate reactive support.

    This necessary source-capability condition does not claim AC deliverability.
    Independent replay uses finite per-generator Q limits and tests every bus.
    """
    tn = [n for n in m._case_data['networks'] if n['layer'] == 'TN']
    m.dc_reactive_capacity = pyo.ConstraintList()
    for network in tn:
        nid = network['id']
        if nid not in m.network:
            continue
        generators = [d for d in m._devices.values() if d['network_id'] == nid
                      and d['kind'] == 'GEN' and d.get('status', 1)]
        low = sum(float(d['q_min_mvar']) for d in generators)
        high = sum(float(d['q_max_mvar']) for d in generators)
        if not generators or not math.isfinite(low+high):
            raise ValueError('DC replay requires finite physical generator reactive capability')
        shunt = sum(b.get('bs_mvar', 0.)*source_bus_voltage(m._case_data,nid,b['id'])**2
                    for b in network['buses'])
        for t in m.T:
            required = (sum(m.port_from_q[r,t] for r,p in m._ports.items() if p['parent_network'] == nid)
                        + sum(m.load_q[r,t] for r,d in m._loads.items() if d['network_id'] == nid)
                        - sum(m._resource_q(r,t) for r,d in m._devices.items()
                              if d['network_id'] == nid and d['kind'] != 'GEN') - shunt)
            m.dc_reactive_capacity.add((low, required, high))


def add_endpoint_constraints(m: Any) -> None:
    params=m._interface_parameters
    def has_child(m, r):
        return m._ports[r]['child_network'] in m.network
    # A TN-only subproblem optimizes the sending endpoint. The receiving
    # endpoint and exact series element live in the DN subproblem and are
    # exchanged through sending-end P/Q consensus.
    for r, record in m._ports.items():
        if not has_child(m, r):
            for t in m.T:
                m.port_p[r,t].fix(0.)
                m.port_q[r,t].fix(0.)
                m.port_ell[r,t].fix(0.)
                m.tap[r,t].fix(record['neutral_position'])
    def voltage(m,r,t):
        if not has_child(m, r):
            return pyo.Constraint.Skip
        p=m._ports[r];s=params[r];base=s['base_mva'];rr,xx=s['r_pu'],s['x_pu']
        uh=parent_voltage_squared(m,p,t)
        ul=m.network[p['child_network']].u[p['child_bus'],t]
        return m.tau[r,t]**2*uh==ul+2*(rr*m.port_p[r,t]+xx*m.port_q[r,t])/base+(rr*rr+xx*xx)*m.port_ell[r,t]
    m.port_active_loss=pyo.Constraint(m.PORT,m.T,rule=lambda m,r,t:
        m.port_from_p[r,t]-m.port_p[r,t]==params[r]['base_mva']*params[r]['r_pu']*m.port_ell[r,t]
        if has_child(m,r) else pyo.Constraint.Skip)
    m.port_reactive_loss=pyo.Constraint(m.PORT,m.T,rule=lambda m,r,t:
        m.port_from_q[r,t]-m.port_q[r,t]==params[r]['base_mva']*params[r]['x_pu']*m.port_ell[r,t]
        if has_child(m,r) else pyo.Constraint.Skip)
    m.port_voltage=pyo.Constraint(m.PORT,m.T,rule=voltage)
    m.port_current_power=pyo.Constraint(m.PORT,m.T,rule=lambda m,r,t:
        (m.port_p[r,t]/params[r]['base_mva'])**2+(m.port_q[r,t]/params[r]['base_mva'])**2
        ==m.network[m._ports[r]['child_network']].u[m._ports[r]['child_bus'],t]*m.port_ell[r,t]
        if has_child(m,r) else pyo.Constraint.Skip)
    m.port_declared_current=pyo.ConstraintList()
    for r,p in m._ports.items():
        if p.get('i_max_ka') is not None:
            # Currents use the same actual bus voltage bases as independent PF.
            buses={(n['id'],b['id']):b for n in m._case_data['networks'] for b in n.get('buses',[])}
            hv=buses[p['parent_network'],p['parent_bus']]['base_kv']
            lv=buses[p['child_network'],p['child_bus']]['base_kv']
            for t in m.T:
                uh=parent_voltage_squared(m,p,t);ul=m.network[p['child_network']].u[p['child_bus'],t]
                m.port_declared_current.add(m.port_from_p[r,t]**2+m.port_from_q[r,t]**2<=3*hv**2*uh*p['i_max_ka']**2)
                m.port_declared_current.add(m.port_p[r,t]**2+m.port_q[r,t]**2<=3*lv**2*ul*p['i_max_ka']**2)


def initialize_endpoints(m: Any, time: Any | None = None) -> None:
    """Initialize new variables from receiving state; does not claim feasibility."""
    for r,p in m._ports.items():
        s=m._interface_parameters[r];base=s['base_mva']
        for t in ([time] if time is not None else m.T):
            pl,ql=pyo.value(m.port_p[r,t]),pyo.value(m.port_q[r,t]);ul=pyo.value(m.network[p['child_network']].u[p['child_bus'],t])
            if ul<=0:raise ValueError('nonpositive receiving voltage for interface seed')
            ell=(pl*pl+ql*ql)/(base*base*ul)
            m.port_ell[r,t].set_value(ell)
            m.port_from_p[r,t].set_value(pl+base*s['r_pu']*ell,skip_validation=True)
            m.port_from_q[r,t].set_value(ql+base*s['x_pu']*ell,skip_validation=True)


def export_endpoints(m: Any, dispatch: dict) -> None:
    dispatch['interface_model']=MODEL;dispatch['interface_parameters']=m._interface_parameters
    for field,comp in [('interface_from_p',m.port_from_p),('interface_from_q',m.port_from_q),('interface_to_p',m.port_p),('interface_to_q',m.port_q),('interface_current_squared',m.port_ell)]:
        dispatch[field]={r:[float(pyo.value(comp[r,t])) for t in m.T] for r in m.PORT}
    for q in ('p','q'):
        dispatch['interface_loss_'+q]={r:[a-b for a,b in zip(dispatch['interface_from_'+q][r],dispatch['interface_to_'+q][r])] for r in m.PORT}
    if m._tn_component == 'TN_DCOPF':
        dispatch['interface_parent_voltage_pu'] = {r:[math.sqrt(float(pyo.value(parent_voltage_squared(m,p,t)))) for t in m.T] for r,p in m._ports.items()}
        dispatch['interface_parent_voltage_source'] = 'declared_source_vm_pu; not a DC voltage state'
    dispatch['interface_alias_semantics']='interface_p/q = low-voltage receiving P/Q; TN uses interface_from_p/q'


def equation_residuals(m: Any) -> dict:
    rows=[]
    for r,p in m._ports.items():
        if p['child_network'] not in m.network:
            continue
        s=m._interface_parameters[r];base=s['base_mva']
        for t in m.T:
            pl,ql=pyo.value(m.port_p[r,t]),pyo.value(m.port_q[r,t]);ell=pyo.value(m.port_ell[r,t]);ul=pyo.value(m.network[p['child_network']].u[p['child_bus'],t])
            rows.append(dict(id=r,time=t,active_loss_mw=abs(pyo.value(m.port_active_loss[r,t].body)),reactive_loss_mvar=abs(pyo.value(m.port_reactive_loss[r,t].body)),voltage_squared_pu=abs(pyo.value(m.port_voltage[r,t].body)),current_power_mva=abs(math.hypot(pl,ql)-base*math.sqrt(max(0.,ul*ell))),current_squared_pu=ell))
    return dict(rows=rows,maxima={k:max((x[k] for x in rows),default=0.) for k in ('active_loss_mw','reactive_loss_mvar','voltage_squared_pu','current_power_mva')},units='each metric carries its own unit; no pu to MW equivalence claim')
