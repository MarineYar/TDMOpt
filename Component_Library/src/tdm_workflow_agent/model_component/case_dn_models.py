"""Six balanced radial DN formulations over the same canonical physical tree.

P/Q use MW/MVAr, U is squared per-unit voltage, and ell is squared per-unit
current on the network base. Branch powers use rooted parent-to-child direction;
pt/qt are powers entering the branch from the child (negative received power).
The root voltage is exclusively controlled by the external TD coupling builder.
"""
from __future__ import annotations

from collections.abc import Callable
import math

import pyomo.environ as pyo

from tdm_workflow_agent.data.indexing import network_index

COMPONENTS = {
    'DN_LINDISTFLOW', 'DN_LINDISTFLOW_LOSS_FIXED', 'DN_LINDISTFLOW_LOSS_ITER',
    'DN_DISTFLOW_SOCP', 'DN_DISTFLOW_SOCP_LIN', 'DN_DISTFLOW_FULL',
}


def build_dn_network(model: pyo.ConcreteModel, block: pyo.Block, network: dict,
                     component_id: str, injection: Callable) -> None:
    """Bind a physical DN to one formulation; resources remain in injection()."""
    if component_id not in COMPONENTS:
        raise ValueError(f'unsupported DN component {component_id}')
    if network['layer'] != 'DN' or network.get('phase_model', 'balanced') != 'balanced':
        raise ValueError('DN DistFlow requires a balanced radial DN network')
    index = network_index(network)
    buses = {b['id']: b for b in network['buses']}
    base = float(network['base_mva'])
    if base <= 0 or not math.isfinite(base):
        raise ValueError('invalid DN base_mva')
    branches = {}
    for source in network['branches']:
        edge = dict(source)
        f, t = source['from_bus'], source['to_bus']
        edge.update(original_from_bus=f, original_to_bus=t, orientation_sign=1)
        if source['status']:
            if source.get('b_pu', 0.) or (source.get('tap', 1.) or 1.) != 1. or source.get('shift_degree', 0.):
                raise ValueError(f"{network['id']}:{edge['id']}: series-only DN cannot represent charging/tap/shift")
            if buses[f]['base_kv'] != buses[t]['base_kv']:
                raise ValueError('series-only DN branch cannot join different voltage bases')
            if source['r_pu'] == 0 and source['x_pu'] == 0:
                raise ValueError('series-only DN branch has zero impedance')
            if index['parent'][f] == t:
                edge.update(from_bus=t, to_bus=f, orientation_sign=-1,
                            ang_min_degree=-source.get('ang_max_degree', 360.),
                            ang_max_degree=-source.get('ang_min_degree', -360.))
            elif index['parent'][t] != f:
                raise ValueError('active branch does not match the rooted radial tree')
        if source.get('rate_mva') is not None and source['rate_mva'] < 0:
            raise ValueError('negative finite branch rating')
        branches[edge['id']] = edge
    active = [e for e, b in branches.items() if b['status']]
    full = component_id == 'DN_DISTFLOW_FULL'
    socp = component_id == 'DN_DISTFLOW_SOCP'
    polyhedral = component_id == 'DN_DISTFLOW_SOCP_LIN'
    fixed = component_id == 'DN_LINDISTFLOW_LOSS_FIXED'
    iterative = component_id == 'DN_LINDISTFLOW_LOSS_ITER'
    current_variable = full or socp or polyhedral
    block._component_id = component_id
    block._network_id = network['id']
    block._oriented_branches = branches
    block._represented_quantities = ['P', 'Q', 'V'] + (['I_squared'] if current_variable else [])
    block._formulation_notes = {
        'DN_LINDISTFLOW': 'Lossless linear P/Q balances and voltage drop; physical current checked in independent replay.',
        'DN_LINDISTFLOW_LOSS_FIXED': 'Legacy P-loss surrogate .015*r*Pabs; Pabs is an epigraph relaxation of abs(P). Legacy Q balance and voltage drop remain lossless.',
        'DN_LINDISTFLOW_LOSS_ITER': 'Mutable network-local fixed ell=Ipu^2, initially zero; P/Q losses base*r/x*ell and lossless voltage drop; maximum three solver passes.',
        'DN_DISTFLOW_SOCP': 'Rotated cone inequality in MW/MVAr with base^2 scaling; complete DistFlow voltage drop and P/Q losses.',
        'DN_DISTFLOW_SOCP_LIN': 'Legacy eight-plane necessary outer approximation in consistent per-unit P/Q; not an exact or tight rotated cone. Lossless voltage drop and base*r/x*ell losses.',
        'DN_DISTFLOW_FULL': 'Exact DistFlow equality cone, complete voltage drop, and P/Q losses on a balanced series radial network.',
    }[component_id]
    block.BUS = pyo.Set(initialize=list(buses), ordered=True)
    block.BR = pyo.Set(initialize=list(branches), ordered=True)
    block.ACTIVE_BR = pyo.Set(initialize=active, ordered=True)

    def flow_bounds(_, edge, time):
        rate = branches[edge].get('rate_mva')
        return (None, None) if rate is None else (-rate, rate)

    block.pf = pyo.Var(block.BR, model.T, bounds=flow_bounds, initialize=0.)
    block.qf = pyo.Var(block.BR, model.T, bounds=flow_bounds, initialize=0.)
    block.pt = pyo.Var(block.BR, model.T, bounds=flow_bounds, initialize=0.)
    block.qt = pyo.Var(block.BR, model.T, bounds=flow_bounds, initialize=0.)
    block.u = pyo.Var(block.BUS, model.T,
        bounds=lambda _, b, t: (buses[b]['v_min_pu']**2, buses[b]['v_max_pu']**2),
        initialize=lambda _, b, t: buses[b].get('vm_pu', 1.)**2)
    current_cap, current_sources = {}, {}
    for edge, branch in branches.items():
        current = branch.get('i_max_ka')
        if current is not None:
            if current < 0:
                raise ValueError('negative current limit')
            kv = buses[branch['from_bus']]['base_kv']
            current_cap[edge] = (current * math.sqrt(3.) * kv / base)**2
            current_sources[edge] = 'declared_i_max_ka'
        elif branch.get('rate_mva') is not None:
            current_cap[edge] = (branch['rate_mva']/base)**2
            current_sources[edge] = 'nominal_current_from_declared_mva_rating'
        else:
            current_cap[edge] = None
            current_sources[edge] = 'no_finite_current_or_mva_rating'
    block._current_limit_source = current_sources
    if current_variable:
        block.ell = pyo.Var(block.BR, model.T, domain=pyo.NonNegativeReals,
                            bounds=lambda _, e, t: (0., current_cap[e]), initialize=0.)
    elif iterative:
        block.ell = pyo.Param(block.BR, model.T, mutable=True, within=pyo.NonNegativeReals, initialize=0.)
        block.current_limit = pyo.Constraint(block.ACTIVE_BR, model.T,
            rule=lambda _, e, t: block.ell[e,t] <= current_cap[e] if current_cap[e] is not None else pyo.Constraint.Skip)
        block._loss_iter_data = dict(network_id=network['id'], ell=block.ell, base_mva=base,
                                    oriented_branches=branches, iterations=0,
                                    max_iterations=3, last_residual=None)
        if not hasattr(model, '_loss_iter_data'):
            model._loss_iter_data = {}
        if network['id'] in model._loss_iter_data:
            raise ValueError(f"duplicate loss-iteration network state: {network['id']}")
        model._loss_iter_data[network['id']] = block._loss_iter_data
        model._loss_iter_active = True
    elif fixed:
        block.pabs = pyo.Var(block.BR, model.T, domain=pyo.NonNegativeReals,
                             bounds=lambda _, e, t: (0., branches[e].get('rate_mva')), initialize=0.)
        block.abs_positive = pyo.Constraint(block.ACTIVE_BR, model.T,
                                            rule=lambda _, e, t: block.pf[e,t] <= block.pabs[e,t])
        block.abs_negative = pyo.Constraint(block.ACTIVE_BR, model.T,
                                            rule=lambda _, e, t: -block.pf[e,t] <= block.pabs[e,t])
    for edge, branch in branches.items():
        if branch['status']:
            continue
        for t in model.T:
            for name in ('pf', 'qf', 'pt', 'qt'):
                getattr(block, name)[edge,t].fix(0.)
            if current_variable:
                block.ell[edge,t].fix(0.)
            if fixed:
                block.pabs[edge,t].fix(0.)

    def loss(edge, t, quantity):
        if not branches[edge]['status']:
            return 0.
        impedance = branches[edge]['r_pu' if quantity == 'p' else 'x_pu']
        if fixed:
            return .015 * impedance * block.pabs[edge,t] if quantity == 'p' else 0.
        if current_variable or iterative:
            return base * impedance * block.ell[edge,t]
        return 0.

    block.p_loss = pyo.Expression(block.BR, model.T, rule=lambda _, e, t: loss(e,t,'p'))
    block.q_loss = pyo.Expression(block.BR, model.T, rule=lambda _, e, t: loss(e,t,'q'))
    block.flow_to_p = pyo.Constraint(block.ACTIVE_BR, model.T,
        rule=lambda _, e, t: block.pt[e,t] == -block.pf[e,t] + block.p_loss[e,t])
    block.flow_to_q = pyo.Constraint(block.ACTIVE_BR, model.T,
        rule=lambda _, e, t: block.qt[e,t] == -block.qf[e,t] + block.q_loss[e,t])

    def voltage_drop(_, edge, t):
        branch = branches[edge]
        f, to = branch['from_bus'], branch['to_bus']
        r, x = branch['r_pu'], branch['x_pu']
        second_order = (r*r+x*x)*block.ell[edge,t] if full or socp else 0.
        return block.u[to,t] == block.u[f,t] - 2.*(r*block.pf[edge,t]+x*block.qf[edge,t])/base + second_order

    block.voltage_drop = pyo.Constraint(block.ACTIVE_BR, model.T, rule=voltage_drop)
    if full or socp:
        def cone(_, edge, t):
            value = block.pf[edge,t]**2 + block.qf[edge,t]**2
            rhs = base**2 * block.u[branches[edge]['from_bus'],t] * block.ell[edge,t]
            return value == rhs if full else value <= rhs
        block.conic = pyo.Constraint(block.ACTIVE_BR, model.T, rule=cone)
    elif polyhedral:
        block.CONE_PLANE = pyo.RangeSet(0, 7)
        block.cone_planes = pyo.Constraint(block.ACTIVE_BR, model.T, block.CONE_PLANE,
            rule=lambda _, e, t, k: (math.cos(2.*math.pi*k/8)*block.pf[e,t]
                + math.sin(2.*math.pi*k/8)*block.qf[e,t])/base
                <= .5*(block.u[branches[e]['from_bus'],t]+block.ell[e,t]))
    incoming, outgoing = {b: [] for b in buses}, {b: [] for b in buses}
    for edge in active:
        outgoing[branches[edge]['from_bus']].append(edge)
        incoming[branches[edge]['to_bus']].append(edge)
    block._incoming_branches, block._outgoing_branches = incoming, outgoing
    block.balance_p = pyo.Constraint(block.BUS, model.T, rule=lambda _, b, t:
        sum(block.pf[e,t] for e in outgoing[b]) + sum(block.pt[e,t] for e in incoming[b])
        == injection(b,t,'p') - buses[b].get('gs_mw',0.)*block.u[b,t])
    block.balance_q = pyo.Constraint(block.BUS, model.T, rule=lambda _, b, t:
        sum(block.qf[e,t] for e in outgoing[b]) + sum(block.qt[e,t] for e in incoming[b])
        == injection(b,t,'q') + buses[b].get('bs_mvar',0.)*block.u[b,t])
    # Source limits describe bus angle differences. On a series branch,
    # Vparent*conj(Vchild) has real U-(rP+xQ)/base and imag (xP-rQ)/base.
    # These are exact for FULL and explicitly relaxed/approximate otherwise.
    for edge in active:
        branch = branches[edge]
        lo, hi = branch.get('ang_min_degree',-360.), branch.get('ang_max_degree',360.)
        if not (lo <= -180. and hi >= 180.) and (hi < lo or hi-lo > 180.):
            raise ValueError('unsupported DN branch angle sector')

    def angle_rule(upper):
        def rule(_, edge, t):
            branch = branches[edge]
            lo, hi = branch.get('ang_min_degree',-360.), branch.get('ang_max_degree',360.)
            if lo <= -180. and hi >= 180.:
                return pyo.Constraint.Skip
            angle = math.radians(hi if upper else lo)
            r, x = branch['r_pu'], branch['x_pu']
            real = block.u[branch['from_bus'],t]-(r*block.pf[edge,t]+x*block.qf[edge,t])/base
            imag = (x*block.pf[edge,t]-r*block.qf[edge,t])/base
            side = math.cos(angle)*imag-math.sin(angle)*real
            return side <= 0. if upper else side >= 0.
        return rule
    block.angle_upper = pyo.Constraint(block.ACTIVE_BR, model.T, rule=angle_rule(True))
    block.angle_lower = pyo.Constraint(block.ACTIVE_BR, model.T, rule=angle_rule(False))
    if full or socp:
        block._thermal_approximation = 'exact_circle'
        block.thermal_from = pyo.Constraint(block.ACTIVE_BR, model.T, rule=lambda _, e, t:
            block.pf[e,t]**2+block.qf[e,t]**2 <= branches[e]['rate_mva']**2
            if branches[e].get('rate_mva') is not None else pyo.Constraint.Skip)
        block.thermal_to = pyo.Constraint(block.ACTIVE_BR, model.T, rule=lambda _, e, t:
            block.pt[e,t]**2+block.qt[e,t]**2 <= branches[e]['rate_mva']**2
            if branches[e].get('rate_mva') is not None else pyo.Constraint.Skip)
    else:
        block._thermal_approximation = 'conservative_inscribed_16_polygon'
        block.FACET = pyo.RangeSet(0, 15)
        def thermal_rule(from_side):
            pvar, qvar = (block.pf, block.qf) if from_side else (block.pt, block.qt)
            return lambda _, e, t, k: math.cos(2.*math.pi*k/16)*pvar[e,t]+math.sin(2.*math.pi*k/16)*qvar[e,t] <= branches[e]['rate_mva']*math.cos(math.pi/16) if branches[e].get('rate_mva') is not None else pyo.Constraint.Skip
        block.thermal_from = pyo.Constraint(block.ACTIVE_BR, model.T, block.FACET, rule=thermal_rule(True))
        block.thermal_to = pyo.Constraint(block.ACTIVE_BR, model.T, block.FACET, rule=thermal_rule(False))
