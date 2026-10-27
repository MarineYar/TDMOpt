"""Collection-driven physical assembly for validated balanced cases.

Legacy inputs remain at their explicit compatibility boundary. Every canonical
network, resource and port is bound once; models differ only by formulation.
"""
from __future__ import annotations
import hashlib
import inspect
import math
from collections import defaultdict
from typing import Any
import pyomo.environ as pyo
from pyomo.repn import generate_standard_repn
from tdm_workflow_agent.data.case_schema import validate_case
from tdm_workflow_agent.model_component.registry import REGISTRY, TN_BASE_MODELS, DN_BASE_MODELS


def _finite_profile(values, count, label):
    if not isinstance(values, (list,tuple)) or len(values)!=count:
        raise ValueError(f'{label}: incomplete time grid')
    if any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in values):
        raise ValueError(f'{label}: nonfinite profile')
    return list(values)


def _resource_setup(m,case,s,selected):
    times=list(m.T);count=len(times);dt=m._dt
    devices={d['id']:d for d in case['devices'] if d['network_id'] in m._scope_networks}
    loads={d['id']:d for d in case['loads'] if d['network_id'] in m._scope_networks}
    m._devices=devices;m._loads=loads
    kinds=defaultdict(list)
    for rid,d in devices.items():kinds[d['kind']].append(rid)
    gen=kinds['GEN']+kinds['GT']+kinds['PV']+kinds['WT']
    batteries=kinds['BESS'];renew=kinds['PV']+kinds['WT'];flex=kinds['FLEX']
    qids=[rid for rid in gen if devices[rid]['kind']!='GEN' or m._tn_component!='TN_DCOPF']+kinds['SVC']
    support=[rid for rid in renew if devices[rid].get('owner_type')=='MG'] if 'MG_REN_Q_SUPPORT' in selected else []
    m._q_support_device_ids=support
    for lid in loads:
        _finite_profile(s['load_p'].get(lid),count,f'load P {lid}')
        _finite_profile(s['load_q'].get(lid),count,f'load Q {lid}')
    for rid in renew:_finite_profile(s['available_p'].get(rid),count,f'available {rid}')
    m.G=pyo.Set(initialize=gen);m.QG=pyo.Set(initialize=qids);m.BESS=pyo.Set(initialize=batteries);m.RE=pyo.Set(initialize=renew)
    m.FLEX=pyo.Set(initialize=flex);m.LOAD=pyo.Set(initialize=list(loads))
    def pbound(m,r,t):
        d=devices[r]
        if not d.get('status',1):return (0.,0.)
        if r in renew:return (0.,s['available_p'][r][times.index(t)])
        return (0. if 'MG_GT_UC' in selected and d.get('owner_type')=='MG' and d['kind']=='GT' else d['p_min_mw'],d['p_max_mw'])
    def qbound(m,r,t):
        d=devices[r]
        if not d.get('status',1):return (0.,0.)
        if d['kind'] in ('GEN','SVC'):return (d['q_min_mvar'],d['q_max_mvar'])
        if d['kind']=='GT':
            q=math.tan(math.acos(d.get('power_factor',1.)))*d['p_max_mw']
            return (0.,q)
        if r in support:return (-d['s_rating_mva'],d['s_rating_mva'])
        return (0.,0.)
    m.pg=pyo.Var(m.G,m.T,bounds=pbound,initialize=0.)
    m.qg=pyo.Var(m.QG,m.T,bounds=qbound,initialize=0.)
    m.curtail=pyo.Var(m.RE,m.T,within=pyo.NonNegativeReals,initialize=0.)
    m.renewable_balance=pyo.Constraint(m.RE,m.T,rule=lambda m,r,t:m.pg[r,t]+m.curtail[r,t]==s['available_p'][r][times.index(t)])
    gt=kinds['GT']
    m.gt_pf=pyo.Constraint(gt,m.T,rule=lambda m,r,t:m.qg[r,t]==m.pg[r,t]*math.tan(math.acos(devices[r].get('power_factor',1.))))
    m.inverter_rating=pyo.Constraint(support,m.T,rule=lambda m,r,t:m.pg[r,t]**2+m.qg[r,t]**2<=devices[r]['s_rating_mva']**2)
    m.charge=pyo.Var(m.BESS,m.T,bounds=lambda m,r,t:(0,devices[r]['p_charge_max_mw']),initialize=0.)
    m.discharge=pyo.Var(m.BESS,m.T,bounds=lambda m,r,t:(0,devices[r]['p_discharge_max_mw']),initialize=0.)
    m.mode=pyo.Var(m.BESS,m.T,bounds=(0,1),initialize=.5)
    m.EBOUND=pyo.RangeSet(0,count)
    m.energy=pyo.Var(m.BESS,m.EBOUND,bounds=lambda m,r,k:(devices[r]['soc_min']*devices[r]['e_nameplate_mwh'],devices[r]['soc_max']*devices[r]['e_nameplate_mwh']),initialize=lambda m,r,k:devices[r]['soc_initial']*devices[r]['e_nameplate_mwh'])
    m.storage_charge_mode=pyo.Constraint(m.BESS,m.T,rule=lambda m,r,t:m.charge[r,t]<=devices[r]['p_charge_max_mw']*m.mode[r,t])
    m.storage_discharge_mode=pyo.Constraint(m.BESS,m.T,rule=lambda m,r,t:m.discharge[r,t]<=devices[r]['p_discharge_max_mw']*(1-m.mode[r,t]))
    m.storage_initial=pyo.Constraint(m.BESS,rule=lambda m,r:m.energy[r,0]==devices[r]['soc_initial']*devices[r]['e_nameplate_mwh'])
    m.storage_update=pyo.Constraint(m.BESS,m.T,rule=lambda m,r,t:m.energy[r,times.index(t)+1]==m.energy[r,times.index(t)]+dt*(devices[r]['eta_charge']*m.charge[r,t]-m.discharge[r,t]/devices[r]['eta_discharge']))
    m.storage_terminal=pyo.Constraint(m.BESS,rule=lambda m,r:m.energy[r,count]==m.energy[r,0])
    m._flex_load_map={}
    for rid in flex:
        dd=devices[rid];ls=dd['baseline_load_ids'];nom=sum(loads[l]['p_nominal_mw'] for l in ls)
        if nom<=0:raise ValueError(f'{rid}: nonpositive flex portfolio baseline')
        for lid in ls:
            if lid in m._flex_load_map:raise ValueError('overlapping flex baseline loads')
            m._flex_load_map[lid]=(rid,loads[lid]['p_nominal_mw']/nom)
    def flexbound(m,r,t):
        if 'DN_FLEX_LOAD_MODEL' not in selected:return (0.,0.)
        cap=devices[r]['max_shift_fraction']*sum(s['load_p'][l][times.index(t)] for l in devices[r]['baseline_load_ids'])
        return (-cap,cap)
    m.flex_shift=pyo.Var(m.FLEX,m.T,bounds=flexbound,initialize=0.)
    m.flex_neutral=pyo.Constraint(m.FLEX,rule=lambda m,r:sum(m.flex_shift[r,t]*dt for t in times)==0)
    m.flex_abs=pyo.Var(m.FLEX,m.T,within=pyo.NonNegativeReals,initialize=0.)
    m.flex_abs_positive=pyo.Constraint(m.FLEX,m.T,rule=lambda m,r,t:m.flex_abs[r,t]>=m.flex_shift[r,t])
    m.flex_abs_negative=pyo.Constraint(m.FLEX,m.T,rule=lambda m,r,t:m.flex_abs[r,t]>=-m.flex_shift[r,t])
    def demand(m,l,t,q=False):
        base=s['load_q' if q else 'load_p'][l][times.index(t)]
        if l not in m._flex_load_map:return base
        r,_=m._flex_load_map[l]
        i=times.index(t); p0=s['load_p'][l][i]
        total=sum(s['load_p'][lid][i] for lid in devices[r]['baseline_load_ids'])
        weight=p0/total if total else 0.
        ratio=(s['load_q'][l][i]/p0 if p0 else 0.) if q else 1.
        return base+weight*ratio*m.flex_shift[r,t]
    m.load_p=pyo.Expression(m.LOAD,m.T,rule=lambda m,l,t:demand(m,l,t))
    m.load_q=pyo.Expression(m.LOAD,m.T,rule=lambda m,l,t:demand(m,l,t,True))
    m._resource_p=lambda r,t:m.pg[r,t] if r in m.G else (m.discharge[r,t]-m.charge[r,t] if r in m.BESS else 0.)
    m._resource_q=lambda r,t:m.qg[r,t] if r in m.QG else 0.
    mg={x['id']:x for x in case.get('microgrids',[]) if x['parent_dn'] in m._scope_networks}
    m.MG=pyo.Set(initialize=list(mg));m._microgrids=mg
    m.mg_p=pyo.Var(m.MG,m.T,bounds=lambda m,r,t:(-mg[r]['port_s_rating_mva'] if mg[r].get('allow_export',False) else 0.,mg[r]['port_s_rating_mva']),initialize=0.)
    m.mg_q=pyo.Var(m.MG,m.T,bounds=lambda m,r,t:(-mg[r]['port_s_rating_mva'],mg[r]['port_s_rating_mva']),initialize=0.)
    own_dev={rid:[d for d in devices if devices[d].get('owner_type')=='MG' and devices[d].get('owner_id')==rid] for rid in mg}
    own_load={rid:[l for l in loads if loads[l].get('owner_type')=='MG' and loads[l].get('owner_id')==rid] for rid in mg}
    m.mg_balance_p=pyo.Constraint(m.MG,m.T,rule=lambda m,r,t:m.mg_p[r,t]+sum(m._resource_p(d,t) for d in own_dev[r])==sum(m.load_p[l,t] for l in own_load[r]))
    m.mg_balance_q=pyo.Constraint(m.MG,m.T,rule=lambda m,r,t:m.mg_q[r,t]+sum(m._resource_q(d,t) for d in own_dev[r])==sum(m.load_q[l,t] for l in own_load[r]))
    m.mg_rating=pyo.Constraint(m.MG,m.T,rule=lambda m,r,t:m.mg_p[r,t]**2+m.mg_q[r,t]**2<=mg[r]['port_s_rating_mva']**2)


def _ports_and_injections(m,case):
    ports={x['id']:x for x in case['interfaces'] if x['parent_network'] in m._scope_networks or x['child_network'] in m._scope_networks};m._ports=ports
    m.PORT=pyo.Set(initialize=list(ports))
    m.port_p=pyo.Var(m.PORT,m.T,bounds=lambda m,r,t:(-ports[r]['s_rating_mva'] if ports[r].get('allow_active_export',False) else 0.,ports[r]['s_rating_mva']),initialize=0.)
    m.port_q=pyo.Var(m.PORT,m.T,bounds=lambda m,r,t:(-ports[r]['s_rating_mva'] if ports[r].get('allow_reactive_export',False) else 0.,ports[r]['s_rating_mva']),initialize=0.)
    if case.get('interface_model') == 'series_impedance_oltc_v1':
        from .case_interfaces import add_endpoint_variables
        add_endpoint_variables(m)
    else:
        m.port_rating=pyo.Constraint(m.PORT,m.T,rule=lambda m,r,t:m.port_p[r,t]**2+m.port_q[r,t]**2<=ports[r]['s_rating_mva']**2)
    m.tap=pyo.Var(m.PORT,m.T,bounds=lambda m,r,t:(0,ports[r]['tap_positions']-1),initialize=lambda m,r,t:ports[r]['neutral_position'])
    m.tau=pyo.Expression(m.PORT,m.T,rule=lambda m,r,t:ports[r]['tau_min']+ports[r]['tau_step']*m.tap[r,t])
    direct_dev=defaultdict(list);direct_load=defaultdict(list);mg_bybus=defaultdict(list);port_terms=defaultdict(list)
    for r,d in m._devices.items():
        if d.get('owner_type')!='MG' and d['kind']!='FLEX':direct_dev[d['network_id'],d['bus_id']].append(r)
    for l,d in m._loads.items():
        if d.get('owner_type')!='MG':direct_load[d['network_id'],d['bus_id']].append(l)
    for r,d in m._microgrids.items():mg_bybus[d['parent_dn'],d['pcc_bus']].append(r)
    for r,d in ports.items():
        port_terms[d['parent_network'],d['parent_bus']].append((r,-1))
        port_terms[d['child_network'],d['child_bus']].append((r,1))
    def injection(n,b,t,q):
        k=n,b;isq=q=='q';rv=m._resource_q if isq else m._resource_p;lv=m.load_q if isq else m.load_p;mv=m.mg_q if isq else m.mg_p;pv=m.port_q if isq else m.port_p
        return sum(rv(r,t) for r in direct_dev[k])-sum(lv[l,t] for l in direct_load[k])-sum(mv[r,t] for r in mg_bybus[k])+sum(sign*(getattr(m,'port_from_'+q)[r,t] if sign<0 and hasattr(m,'port_from_p') else pv[r,t]) for r,sign in port_terms[k])
    m._injection=injection


def _couple_voltage(m):
    def coupling(m,r,t):
        p=m._ports[r]
        if p['child_network'] not in m.network:
            m.tap[r,t].fix(p['neutral_position'])
            return pyo.Constraint.Skip
        parent=m.network[p['parent_network']] if p['parent_network'] in m.network else None
        child=m.network[p['child_network']]
        boundary=m._case_scenario.get('_boundary_voltage',{}).get(r)
        if boundary is not None:return child.u[p['child_bus'],t]==m.tau[r,t]**2*boundary[list(m.T).index(t)]**2
        # A DC TN has no voltage decision. Its frozen replay AVR is source vm.
        if hasattr(parent,'u'):up=parent.u[p['parent_bus'],t]
        else:up=next(b.get('vm_pu',1.)**2 for n in m._case_data['networks'] if n['id']==p['parent_network'] for b in n['buses'] if b['id']==p['parent_bus'])
        return child.u[p['child_bus'],t]==m.tau[r,t]**2*up
    if hasattr(m,'port_from_p'):
        from .case_interfaces import add_endpoint_constraints
        add_endpoint_constraints(m)
        if (m._tn_component == 'TN_DCOPF'
                and any(p['parent_network'] in m.network for p in m._ports.values())):
            from .case_interfaces import add_dc_reactive_capacity
            add_dc_reactive_capacity(m)
    else:
        m.port_voltage=pyo.Constraint(m.PORT,m.T,rule=coupling)
    times=list(m.T);m.tap_motion=pyo.Var(m.PORT,m.T,within=pyo.NonNegativeReals,initialize=0.)
    m.tap_move_p=pyo.ConstraintList();m.tap_move_n=pyo.ConstraintList()
    for r in m.PORT:
        m.tap_motion[r,times[0]].fix(0.)
        for i,t in enumerate(times[1:],1):
            m.tap_move_p.add(m.tap_motion[r,t]>=m.tap[r,t]-m.tap[r,times[i-1]])
            m.tap_move_n.add(m.tap_motion[r,t]>=m.tap[r,times[i-1]]-m.tap[r,t])


def _optional(m,cid):
    """Apply one selected component using actual device/port handles."""
    ds=m._devices;ts=list(m.T);dt=m._dt;c=m._case_data;settings=c.get('component_parameters',{}).get(cid,{})
    if cid in ('MG_GT_RAMP_MODEL','CON_TN_RAMP_LIMIT'):
        group=[r for r in m.G if ds[r]['kind']=='GEN'] if cid=='CON_TN_RAMP_LIMIT' else [r for r in m.G if ds[r]['kind']=='GT' and ds[r].get('owner_type')=='MG']
        cons=pyo.ConstraintList();m.add_component(cid,cons)
        for r in group:
            for i,t in enumerate(ts[1:],1):
                cons.add(m.pg[r,t]-m.pg[r,ts[i-1]]<=ds[r]['ramp_up_mw_per_hour']*dt)
                cons.add(m.pg[r,ts[i-1]]-m.pg[r,t]<=ds[r]['ramp_down_mw_per_hour']*dt)
        return [cid]
    if cid=='MG_GT_UC':
        ids=[r for r in m.G if ds[r]['kind']=='GT' and ds[r].get('owner_type')=='MG']
        m.commit=pyo.Var(ids,m.T,bounds=(0,1),initialize=1.);m.start=pyo.Var(ids,m.T,bounds=(0,1),initialize=0.);m.stop=pyo.Var(ids,m.T,bounds=(0,1),initialize=0.);m.commitment=pyo.ConstraintList()
        steps=math.ceil(2./dt)
        for r in ids:
            m.start[r,ts[0]].fix(0);m.stop[r,ts[0]].fix(0)
            for i,t in enumerate(ts):
                m.commitment.add(m.pg[r,t]<=ds[r]['p_max_mw']*m.commit[r,t]);m.commitment.add(m.pg[r,t]>=ds[r]['p_min_mw']*m.commit[r,t]);m.commitment.add(m.start[r,t]+m.stop[r,t]<=1)
                if i:m.commitment.add(m.start[r,t]-m.stop[r,t]==m.commit[r,t]-m.commit[r,ts[i-1]])
                if i+steps<=len(ts):m.commitment.add(sum(m.commit[r,tt] for tt in ts[i:i+steps])>=steps*m.start[r,t])
                else:m.start[r,t].fix(0.)
        return ['commitment']
    if cid=='MG_BESS_PRECONDITION':
        target=round(float(settings.get('target_hour',16))/dt)
        m.precharge=pyo.ConstraintList()
        if 0<=target<=len(ts):
            for r in m.BESS:
                if ds[r].get('owner_type')=='MG':m.precharge.add(m.energy[r,target]>=float(settings.get('soc_target_fraction',.8))*ds[r]['soc_max']*ds[r]['e_nameplate_mwh'])
        m._precharge_applicability={'status':'present' if len(m.precharge) else 'not_applicable','target_energy_boundary':target,'reason':None if len(m.precharge) else 'target hour outside horizon or no MG BESS'}
        return ['precharge']
    if cid=='MG_FLEX_PEAK_SHAVING':
        m.peak_shave=pyo.ConstraintList()
        for r,p in m._ports.items():
            if p['child_network'] not in m._scope_networks:continue
            ls=[l for l,d in m._loads.items() if d['network_id']==p['child_network'] and d.get('owner_type')!='MG']
            peak=max(sum(m._case_scenario['load_p'][l][i] for l in ls) for i in range(len(ts)))
            for t in ts:m.peak_shave.add(m.port_p[r,t]<=float(settings.get('peak_ratio',.9))*peak)
        return ['peak_shave']
    if cid=='CON_RESERVE_MARGIN':
        ids=[r for r in m.G if ds[r]['kind'] in ('GEN','GT') and ds[r].get('status',1)]
        ratio=float(settings.get('reserve_margin_ratio',.05));m.reserve=pyo.ConstraintList()
        for t in ts:m.reserve.add(sum(ds[r]['p_max_mw']-m.pg[r,t] for r in ids)>=ratio*sum(m.load_p[l,t] for l in m.LOAD))
        return ['reserve']
    if cid=='CON_CARBON_INTENSITY_LIMIT':
        cap=float(settings.get('carbon_intensity_limit_kg_per_mwh',500.))
        m.carbon_intensity=pyo.Constraint(expr=m.carbon_kg<=cap*sum(m.pg[r,t]*dt for r in m.G for t in ts))
        return ['carbon_intensity']
    if cid=='MG_REN_Q_SUPPORT':return ['inverter_rating']
    if cid.startswith('OBJ_'):return ['obj']
    if cid in ('DN_REACTIVE_SUPPORT_EXTENSION','DN_RENEWABLE_CURTAILMENT_MODEL','DN_BESS_ACTIVE_MODEL','DN_FLEX_LOAD_MODEL','MG_TERMINAL_SOC_CONSTRAINT','MG_CARBON_MODEL','COORD_BOUNDARY_POWER_EXCHANGE'):
        return {'DN_REACTIVE_SUPPORT_EXTENSION':['qg'],'DN_RENEWABLE_CURTAILMENT_MODEL':['renewable_balance'],'DN_BESS_ACTIVE_MODEL':['storage_update'],'DN_FLEX_LOAD_MODEL':['flex_neutral'],'MG_TERMINAL_SOC_CONSTRAINT':['storage_terminal'],'MG_CARBON_MODEL':['carbon_kg'],'COORD_BOUNDARY_POWER_EXCHANGE':['port_p','port_q','port_voltage']}[cid]
    raise ValueError(f'canonical component not implemented: {cid}')


def _objectives(m,selected):
    ds=m._devices;ts=list(m.T);dt=m._dt;cfg=m._case_data['cost_and_carbon'];method=m._method
    carbon=cfg['carbon_price_cny_per_kg']*getattr(method,'soft_carbon_penalty_multiplier',1.)
    def fuel(r,t):
        d=ds[r];x=m.pg[r,t]
        if d['kind']=='GEN':
            coeff=d['cost_coefficients'];return sum(a*x**(len(coeff)-i-1) for i,a in enumerate(coeff))
        return d.get('cost_cny_per_mwh',0.)*x
    m.fuel_cost=pyo.Expression(expr=sum(fuel(r,t)*dt for r in m.G for t in ts))
    m.carbon_kg=pyo.Expression(expr=sum(ds[r].get('emission_kg_per_mwh',0)*m.pg[r,t]*dt for r in m.G for t in ts))
    m.carbon_cost=pyo.Expression(expr=carbon*m.carbon_kg)
    m.bess_cost=pyo.Expression(expr=sum(ds[r].get('throughput_cost_cny_per_mwh',cfg['bess_throughput_cny_per_mwh'])*(m.charge[r,t]+m.discharge[r,t])*dt for r in m.BESS for t in ts)*getattr(method,'bess_throughput_cost_multiplier',1.))
    m.base_cost=pyo.Expression(expr=m.fuel_cost+m.carbon_cost+m.bess_cost)
    penalty=cfg['curtailment_cny_per_mwh']*getattr(method,'curtailment_penalty_multiplier',1.)*sum(m.curtail[r,t]*dt for r in m.RE for t in ts)
    penalty+=float(cfg.get('flex_shift_cny_per_mwh',getattr(method,'flex_shift_cny_per_mwh',15.)))*sum(m.flex_abs[r,t]*dt for r in m.FLEX for t in ts)
    params=m._case_data.get('component_parameters',{})
    weights={cid:float(params.get(cid,{}).get('weight',REGISTRY.get(cid).deterministic_metadata.get('weight',0.))) for cid in selected if REGISTRY.get(cid) and REGISTRY.get(cid).layer=='Objective'}
    if 'OBJ_INTERFACE_USAGE' in selected:penalty+=.1*weights['OBJ_INTERFACE_USAGE']*sum(m.port_p[r,t]**2*dt for r in m.PORT for t in ts)
    if 'OBJ_VOLTAGE_DEVIATION' in selected:
        tn_ids={n['id'] for n in m._case_data['networks'] if n['layer']=='TN'}
        penalty+=weights['OBJ_VOLTAGE_DEVIATION']*sum((.1 if nid in tn_ids else 1.)*((b.v[i,t] if hasattr(b,'v') else b.u[i,t])-1)**2*dt for nid,b in m.network.items() if hasattr(b,'u') for i in b.BUS for t in ts)
    if 'OBJ_GT_RAMPING' in selected:penalty+=weights['OBJ_GT_RAMPING']*sum((m.pg[r,t]-m.pg[r,ts[i-1]])**2*dt for r in m.G if ds[r]['kind']=='GEN' and ds[r]['p_max_mw']>0 for i,t in enumerate(ts) if i)
    if 'OBJ_LOSS_PENALTY' in selected:penalty+=weights['OBJ_LOSS_PENALTY']*sum(b.ell[r,t]*dt for b in m.network.values() if hasattr(b,'ell') for r in b.BR for t in ts)
    # Preserve objective-only exactness regularization and report separately.
    exact=0.
    for n,b in m.network.items():
        if m._network_components[n]=='TN_ACOPF_SOCP':
            nw=next(x for x in m._case_data['networks'] if x['id']==n)
            exact+=sum(b.u[x['from_bus'],t]*b.u[x['to_bus'],t]-b.wr[x['id'],t]**2-b.wi[x['id'],t]**2 for x in nw['branches'] if x['status'] for t in ts)
        elif m._network_components[n]=='DN_DISTFLOW_SOCP':
            nw=next(x for x in m._case_data['networks'] if x['id']==n);base=nw['base_mva']
            exact+=sum(b.u[x['from_bus'],t]*b.ell[r,t]-(b.pf[r,t]/base)**2-(b.qf[r,t]/base)**2 for r,x in b._oriented_branches.items() for t in ts)
    m.exactness=pyo.Expression(expr=exact)
    m.obj=pyo.Objective(expr=m.base_cost+penalty+getattr(method,'socp_exactness_weight',1000.)*m.exactness+sum(m.tap_motion[r,t] for r in m.PORT for t in ts))
    objs=[cid for cid in selected if REGISTRY.get(cid) is not None and REGISTRY.get(cid).layer=='Objective']
    mandatory=[cid for cid in objs if REGISTRY.get(cid).selection_mode=='mandatory_core']
    m._objective_component_summary={'selected_objective_components':objs,'mandatory_objective_components':mandatory,'case_parameters':dict(cfg),'frozen_weights':weights,'fixed_normalization':{'OBJ_INTERFACE_USAGE':.1,'OBJ_VOLTAGE_DEVIATION_TN':.1,'OBJ_GT_RAMPING_scope':'active TN GEN','OBJ_MG_COMFORT_LOSS_cny_per_mwh':float(cfg.get('flex_shift_cny_per_mwh',getattr(method,'flex_shift_cny_per_mwh',15.)))},'formulation_note':'actual polynomial degree reported, including port and selected objective terms','optional_loss_penalty_scope':'existing internal network ell only; interface ell excluded; mandatory core adds no loss penalty'}


def build_case_model(selected_ids:list[str],case:dict,scenario:dict,method_config:Any,*,scope_network_ids:list[str]|None=None)->tuple[Any,dict]:
    # Publication API validates actual registered choices, not a private LLM schema.
    ok, errors = REGISTRY.validate_ids(selected_ids)
    if not ok:
        raise ValueError('; '.join(errors))
    from .compatibility import check_compatibility
    ok, errors, _ = check_compatibility(selected_ids)
    if not ok:
        raise ValueError('; '.join(errors))
    validate_case(case)
    if scenario.get('system_hash')!=case.get('system_hash'):raise ValueError('system_hash mismatch at model build')
    selected=list(dict.fromkeys(selected_ids));tn=[x for x in selected if x in TN_BASE_MODELS];dn=[x for x in selected if x in DN_BASE_MODELS]
    if len(tn)!=1 or len(dn)!=1:raise ValueError('exactly one TN and DN formulation required')
    from tdm_workflow_agent.data.interface_support import validate_supported
    if scope_network_ids is None:
        support_mode = 'centralized'
    elif 'COORD_ADMM_TDM' in selected:
        support_mode = 'admm'
    else:
        support_mode = 'decomposed'
    validate_supported(case, tn[0], dn[0], support_mode)
    times=scenario['time_grid']['intervals'];dt=scenario['time_grid']['dt_hours']
    if not times or len(set(times))!=len(times) or dt<=0:raise ValueError('invalid scenario time grid')
    m=pyo.ConcreteModel(name=case['system_id']);m.T=pyo.Set(initialize=times,ordered=True)
    m._scope_networks=set(scope_network_ids or [n['id'] for n in case['networks']]);m._case_data=case;m._case_scenario=scenario;m._dt=dt;m._method=method_config;m._tn_component=tn[0];m._dn_component=dn[0];m._selected_component_ids=selected
    m._network_components={n['id']:tn[0] if n['layer']=='TN' else dn[0] for n in case['networks'] if n['id'] in m._scope_networks}
    _resource_setup(m,case,scenario,selected);_ports_and_injections(m,case)
    m.network=pyo.Block([n['id'] for n in case['networks'] if n['id'] in m._scope_networks])
    from .case_tn_models import build_tn_network
    from .case_dn_models import build_dn_network
    invocations=[]
    for cid in [tn[0],dn[0]]:
        fn=build_tn_network if cid in TN_BASE_MODELS else build_dn_network
        layer='TN' if cid in TN_BASE_MODELS else 'DN'
        for n in case['networks']:
            if n['layer']==layer and n['id'] in m._scope_networks:fn(m,m.network[n['id']],n,cid,lambda b,t,q,nid=n['id']:m._injection(nid,b,t,q))
        invocations.append(_invocation(cid,fn,['network'],m))
    _couple_voltage(m);_objectives(m,selected)
    for cid in selected:
        if cid in tn+dn:continue
        comp=REGISTRY.get(cid)
        if comp is None:raise ValueError(f'unknown component {cid}')
        if comp.execution_binding=='builder':
            evidence=_optional(m,cid);invocations.append(_invocation(cid,_optional,evidence,m))
    degree=m.obj.expr.polynomial_degree();nonlinear=any(c.body.polynomial_degree() not in (0,1) for c in m.component_data_objects(pyo.Constraint,active=True))
    m._formulation_type='NLP' if nonlinear else ('QP' if degree==2 else 'LP')
    m._requires_nonconvex=nonlinear
    audit={'errors':[],'warnings':[],'build_order':selected,'builder_invocations':invocations,'glue_invocations':[{'component_id':'tn_dn_adapter','source_fingerprint':hashlib.sha256(inspect.getsource(_couple_voltage).encode()).hexdigest(),'evidence':['port_p','port_q','port_voltage']}], 'components':{cid:{'status':'ok'} for cid in selected},'system_hash':case['system_hash'],'scenario_hash':scenario['scenario_hash']}
    m._build_audit=audit
    return m,audit


def _invocation(cid,fn,evidence,m):
    return {'component_id':cid,'callable':f'{fn.__module__}.{fn.__name__}','source_fingerprint':hashlib.sha256(inspect.getsource(fn).encode()).hexdigest(),'result_status':'ok','reported_added':evidence,'structural_delta':{'evidence':evidence,'present':all(hasattr(m,x) for x in evidence)}}


def audit_case_bindings(m)->dict:
    ds=m._devices;times=list(m.T);t=times[0];entries=[]
    for r,d in ds.items():
        names=[];bounds={};objective={}
        for name in ('pg','qg','charge','discharge','energy','flex_shift'):
            comp=getattr(m,name);key=(r,0 if name=='energy' else t)
            if key in comp:
                v=comp[key];names.append(v.name);bounds[name]=[pyo.value(v.lb),pyo.value(v.ub)]
        if r in m.G:
            if d['kind']=='GEN':objective['cost_coefficients_times_dt']=[x*m._dt for x in d['cost_coefficients']]
            else:objective['fuel_linear_times_dt']=d.get('cost_cny_per_mwh',0)*m._dt
            objective['carbon_linear_times_dt']=d.get('emission_kg_per_mwh',0)*m._case_data['cost_and_carbon']['carbon_price_cny_per_kg']*m._dt
        if r in m.BESS:objective['throughput_linear_times_dt']=d['throughput_cost_cny_per_mwh']*m._dt
        entries.append({'resource_id':r,'owner_id':d.get('owner_id'),'network_id':d['network_id'],'kind':d['kind'],'variables':names,'bounds_first_interval':bounds,'objective_data':objective,'input':d,'bound':bool(names)})
    return {'system_hash':m._case_data['system_hash'],'scenario_hash':m._case_scenario['scenario_hash'],'all_resources_bound':all(x['bound'] for x in entries),'devices':entries,'network_instances':list(m.network),'mg_instances':list(m.MG),'time_intervals':len(times),'energy_states':len(m.EBOUND),'storage_mode_semantics':'continuous relaxation; min(charge,discharge)<=1e-6 audited only after solve','evidence_level':'actual Pyomo variable bounds/constraints and coefficient input, no solve implied'}


def extract_case_dispatch(m)->dict:
    def val(v):
        x=pyo.value(v,exception=False)
        if x is None or not math.isfinite(float(x)):raise ValueError(f'uninitialized/nonfinite dispatch {v.name}')
        return float(x)
    ts=list(m.T);c=m._case_data;s=m._case_scenario
    d={'system_id':c['system_id'],'scenario_id':s['scenario_id'],'execution_id':s.get('_execution_id'),'code_hash':s.get('_code_hash'),'system_hash':c['system_hash'],'scenario_hash':s['scenario_hash'],'time_grid':dict(s['time_grid']),'tn_model':m._tn_component,'dn_model':m._dn_component,'active_components':list(m._selected_component_ids),'q_support_device_ids':m._q_support_device_ids,'device_p':{},'device_q':{},'device_curtailment':{},'charge':{},'discharge':{},'energy':{},'load_p':{},'load_q':{},'voltage':{},'angle':{},'interface_p':{},'interface_q':{},'oltc_tap_pos':{},'mg_p':{},'mg_q':{}}
    for r,dev in m._devices.items():
        if dev['kind']=='FLEX':continue
        d['device_p'][r]=[val(m._resource_p(r,t)) for t in ts]
        if r in m.QG or dev['kind']!='GEN' or m._tn_component!='TN_DCOPF':d['device_q'][r]=[val(m._resource_q(r,t)) for t in ts]
    if hasattr(m,'commit'):
        d['commitment_semantics']='continuous_unit_interval_relaxation'
        for field,comp in [('commitment',m.commit),('startup',m.start),('shutdown',m.stop)]:
            d[field]={r:[val(comp[r,t]) for t in ts] for r in dict.fromkeys(r for r,t in comp)}
    for r in m.RE:d['device_curtailment'][r]=[val(m.curtail[r,t]) for t in ts]
    for r in m.BESS:
        for name in ('charge','discharge'):d[name][r]=[val(getattr(m,name)[r,t]) for t in ts]
        d['energy'][r]=[val(m.energy[r,k]) for k in m.EBOUND]
    for l in m.LOAD:
        d['load_p'][l]=[val(m.load_p[l,t]) for t in ts];d['load_q'][l]=[val(m.load_q[l,t]) for t in ts]
    for r in m.MG:
        d['mg_p'][r]=[val(m.mg_p[r,t]) for t in ts];d['mg_q'][r]=[val(m.mg_q[r,t]) for t in ts]
    for r,p in m._ports.items():
        d['interface_p'][r]=[val(m.port_p[r,t]) for t in ts];d['interface_q'][r]=[val(m.port_q[r,t]) for t in ts]
        raw=[val(m.tap[r,t]) for t in ts]
        if any(abs(x-round(x))>1e-7 for x in raw):raise ValueError('continuous tap schedule is not a physical dispatch')
        d['oltc_tap_pos'][p['child_network']]=[int(round(x)) for x in raw]
    for n,b in m.network.items():
        if hasattr(b,'v'):d['voltage'][n]={str(bus):[val(b.v[bus,t]) for t in ts] for bus in b.BUS}
        elif hasattr(b,'u'):d['voltage'][n]={str(bus):[math.sqrt(max(val(b.u[bus,t]),0.)) for t in ts] for bus in b.BUS}
        if hasattr(b,'e') and hasattr(b,'f'):d['angle'][n]={str(bus):[math.degrees(math.atan2(val(b.f[bus,t]),val(b.e[bus,t]))) for t in ts] for bus in b.BUS}
        elif hasattr(b,'theta'):d['angle'][n]={str(bus):[math.degrees(val(b.theta[bus,t])) for t in ts] for bus in b.BUS}
    if hasattr(m,'port_from_p'):
        from .case_interfaces import export_endpoints
        export_endpoints(m,d)
    d.update(total_cost_cny=val(m.base_cost),objective_cny=val(m.obj),total_carbon_kg=val(m.carbon_kg),renewable_curtailment_mwh=sum(val(m.curtail[r,t])*m._dt for r in m.RE for t in ts),load_shedding_mwh=0.)
    d['cost_components'] = dict(fuel_cost_cny=val(m.fuel_cost),carbon_cost_cny=val(m.carbon_cost),
        bess_throughput_cost_cny=val(m.bess_cost),base_cost_cny=val(m.base_cost),
        penalty_and_regularization_cny=val(m.obj)-val(m.base_cost),
        objective_cny=val(m.obj),cost_basis='existing model expressions; qualification required; PF slack adjustments separate')
    return d
