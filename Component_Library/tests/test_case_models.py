import copy

import importlib.util

from pathlib import Path

import pytest

import pyomo.environ as pyo

from pyomo.repn import generate_standard_repn

spec=importlib.util.spec_from_file_location('case_fixtures',Path(__file__).resolve().parents[1]/'examples/case_fixtures.py')

f=importlib.util.module_from_spec(spec)

spec.loader.exec_module(f)

def test_small_model_storage_energy_and_dt_bound():
    from tdm_workflow_agent.model_component.case_builders import build_case_model
    case=f.make_case();s=f.scenario_for(case)
    m,a=build_case_model(['TN_ACOPF_FULL','DN_DISTFLOW_FULL'],case,s,None)
    assert not a['errors']
    rid=next(d['id'] for d in case['devices'] if d['kind']=='BESS')
    assert len(list(m.energy[rid,:]))==4
    assert m.energy[rid,0].lb==pytest.approx(.4*.15)
    rep=generate_standard_repn(m.storage_update[rid,0].body)
    coeff={v.name:c for v,c in zip(rep.linear_vars,rep.linear_coefs)}
    assert coeff[m.charge[rid,0].name]==pytest.approx(-.95*.25)
    assert coeff[m.discharge[rid,0].name]==pytest.approx(.25/.94)
    m2,_=build_case_model(['TN_ACOPF_FULL','DN_DISTFLOW_FULL'],dict(case,devices=[dict(d,e_nameplate_mwh=.8) if d['id']==rid else d for d in case['devices']]),s,None)
    assert m2.energy[rid,0].ub==pytest.approx(.8*.95)

@pytest.mark.parametrize('tn',['TN_DCOPF','TN_LINEARIZED_ACOPF','TN_ACOPF_SOCP','TN_ACOPF_FULL'])
@pytest.mark.parametrize('dn',['DN_LINDISTFLOW','DN_LINDISTFLOW_LOSS_FIXED','DN_DISTFLOW_SOCP','DN_DISTFLOW_SOCP_LIN','DN_DISTFLOW_FULL'])
def test_all_network_formulations_build(tn,dn):
    from tdm_workflow_agent.model_component.case_builders import build_case_model
    c=f.make_case();m,a=build_case_model([tn,dn],c,f.scenario_for(c),None)
    assert not a['errors'];assert len(m.network)==2
    assert m._network_components['grid']==tn
    assert m._network_components['orchard']==dn
    assert len(m.network['grid'].BR)==3
    if tn=='TN_DCOPF': assert not hasattr(m.network['grid'],'u')

def test_mixed_networks_and_resource_binding():
    from tdm_workflow_agent.model_component.case_builders import build_case_model, audit_case_bindings
    c=f.make_case(mixed=True);m,a=build_case_model(['TN_ACOPF_FULL','DN_DISTFLOW_FULL'],c,f.scenario_for(c),None)
    assert not a['errors']
    assert [len(m.network[n].BUS) for n in ['orchard','harbor','hill']]==[33,5,69]
    assert len(m.MG)==6
    evidence=audit_case_bindings(m)
    assert evidence['all_resources_bound']
    assert len(evidence['devices'])==len(c['devices'])
    assert m.pg['grid:source:2',0].ub==0
    assert m.qg['grid:source:2',0].ub==3

def test_branch_admittance_parallel_and_tap():
    from tdm_workflow_agent.model_component.network_math import branch_admittance
    b=dict(r_pu=.02,x_pu=.15,b_pu=.03,tap=1.1,shift_degree=13,status=1)
    yff,yft,ytf,ytt=branch_admittance(b)
    import numpy as np
    y=1/complex(.02,.15);a=1.1*np.exp(1j*np.deg2rad(13))
    assert abs(yff-(y+.015j)/1.21)<1e-12
    assert abs(yft+y/a.conjugate())<1e-12
    assert abs(ytf+y/a)<1e-12
    assert abs(ytt-y-.015j)<1e-12

def test_optional_objective_preserves_tn_ramp_and_interface_coefficients():
    from tdm_workflow_agent.model_component.case_builders import build_case_model
    c=f.make_case();s=f.scenario_for(c)
    selected=['TN_ACOPF_FULL','DN_DISTFLOW_FULL','OBJ_GT_RAMPING','OBJ_INTERFACE_USAGE']
    m,_=build_case_model(selected,c,s,None)
    rep=generate_standard_repn(m.obj.expr)
    quadratic={(a.name,b.name):v for (a,b),v in zip(rep.quadratic_vars,rep.quadratic_coefs)}
    r=next(r for r in m.G if m._devices[r]['kind']=='GEN' and m._devices[r]['p_max_mw']>0)
    a,b=m.pg[r,0].name,m.pg[r,1].name
    assert quadratic.get((a,b),quadratic.get((b,a)))==pytest.approx(-20*m._dt)
    lower=next(r for r in m.G if m._devices[r]['kind']=='GT')
    assert (m.pg[lower,0].name,m.pg[lower,1].name) not in quadratic
    r=next(iter(m.PORT));name=m.port_p[r,0].name
    assert quadratic[(name,name)]==pytest.approx(.1*m._dt)

def test_flex_allocation_uses_authoritative_hourly_pq():
    from tdm_workflow_agent.model_component.case_builders import build_case_model
    c=f.make_case();s=f.scenario_for(c)
    native=[d for d in c['loads'] if d.get('owner_type')!='MG' and d['network_id']=='orchard']
    original=native[0];second=copy.deepcopy(original);second['id']='orchard:load:extra';c['loads'].append(second)
    c['devices'].append(dict(id='orchard:FLEX',kind='FLEX',network_id='orchard',bus_id=original['bus_id'],owner_type='DN',owner_id='orchard',baseline_load_ids=[original['id'],second['id']],max_shift_fraction=.1,energy_neutral_per_day=True,status=1))
    s['load_p'][original['id']]=[.1]*3;s['load_q'][original['id']]=[.04]*3
    s['load_p'][second['id']]=[.3]*3;s['load_q'][second['id']]=[.06]*3
    m,_=build_case_model(['TN_ACOPF_FULL','DN_DISTFLOW_FULL','DN_FLEX_LOAD_MODEL'],c,s,None)
    m.flex_shift['orchard:FLEX',0].value=.02
    assert pyo.value(m.load_p[second['id'],0])==pytest.approx(.315)
    assert pyo.value(m.load_q[second['id'],0])==pytest.approx(.063)

def test_bus_renumber_and_row_reorder_preserve_ybus_and_objective():
    import numpy as np
    from tdm_workflow_agent.model_component.network_math import ybus
    from tdm_workflow_agent.model_component.case_builders import build_case_model
    c=f.make_case(mixed=True);changed=copy.deepcopy(c)
    maps={n['id']:{b['id']:f"node-{k+80}" for k,b in enumerate(n['buses'])} for n in c['networks']}
    for n in changed['networks']:
        mapping=maps[n['id']]
        for b in n['buses']:b['id']=mapping[b['id']]
        for branch in n['branches']:
            for field in ('from_bus','to_bus'):branch[field]=mapping[branch[field]]
        for key in ('root_bus','reference_bus'):
            if key in n:n[key]=mapping[n[key]]
        n['buses'].reverse();n['branches'].reverse()
    for d in changed['devices']+changed['loads']:d['bus_id']=maps[d['network_id']][d['bus_id']]
    for p in changed['interfaces']:
        for side in ('parent','child'):p[side+'_bus']=maps[p[side+'_network']][p[side+'_bus']]
    for mg in changed['microgrids']:mg['pcc_bus']=maps[mg['parent_dn']][mg['pcc_bus']]
    changed['devices'].reverse();changed['loads'].reverse();changed['networks'].reverse()
    for network in c['networks']:
        reordered=next(n for n in changed['networks'] if n['id']==network['id'])
        assert np.allclose(ybus(network),ybus(reordered)[::-1,::-1],rtol=0,atol=1e-12)
    def coefficients(case):
        m,_=build_case_model(['TN_ACOPF_FULL','DN_DISTFLOW_FULL'],case,f.scenario_for(case),None)
        rep=generate_standard_repn(m.obj.expr)
        return dict(linear={v.name:float(a) for v,a in zip(rep.linear_vars,rep.linear_coefs)},quadratic={tuple(sorted((a.name,b.name))):float(v) for (a,b),v in zip(rep.quadratic_vars,rep.quadratic_coefs)},constant=rep.constant)
    assert coefficients(c)==coefficients(changed)
