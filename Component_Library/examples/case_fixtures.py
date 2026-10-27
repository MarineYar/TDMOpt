"""Synthetic software fixtures; never a published electrical benchmark."""
import copy
import hashlib
import json


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def make_case(mixed=False, hours=3, dt=.25):
    tn_buses=[101,205,900]
    def bus(i,kv):
        return dict(id=i,base_kv=kv,v_min_pu=.95,v_max_pu=1.05,gs_mw=0.,bs_mvar=0.,vm_pu=1.,va_degree=0.,type=1)
    def branch(i,f,t,rate=100):
        return dict(id=i,from_bus=f,to_bus=t,r_pu=.001,x_pu=.01,b_pu=0.,tap=1.,shift_degree=0.,rate_mva=rate,status=1,ang_min_degree=-30.,ang_max_degree=30.)
    tn=dict(id='grid',layer='TN',base_mva=100.,phase_model='balanced',reference_bus=205,buses=[bus(i,138) for i in tn_buses],branches=[branch('a',101,205),branch('parallel',101,205),branch('c',205,900)])
    names=['orchard','harbor','hill'] if mixed else ['orchard']
    sizes=[33,5,69] if mixed else [5]
    mgnums=[0,2,4] if mixed else [1]
    networks=[tn];devices=[];loads=[];interfaces=[];microgrids=[]
    for j,(n,size,nmg) in enumerate(zip(names,sizes,mgnums)):
        ids=[100,17,90,4,33]+list(range(1001,1001+size-5))
        networks.append(dict(id=n,layer='DN',base_mva=10.,phase_model='balanced',root_bus=100,buses=[bus(i,35) for i in ids],branches=[branch(f'{n}-edge-{k}',ids[k-1],ids[k],20.) for k in range(1,len(ids))]))
        interfaces.append(dict(id=f'port:{n}',parent_network='grid',parent_bus=tn_buses[j],child_network=n,child_bus=100,hv_nominal_kv=138.,lv_nominal_kv=35.,s_rating_mva=20.,allow_active_export=True,allow_reactive_export=True,model='legacy_near_ideal_oltc',tau_min=.9,tau_step=.00625,tap_positions=33,neutral_position=16,physical_replay_vkr_percent=.0001,physical_replay_vk_percent=.001,iron_loss_kw=0.,no_load_current_percent=0.))
        loads.append(dict(id=f'{n}:native',network_id=n,bus_id=17,owner_type='DN',owner_id=n,p_nominal_mw=.05,q_nominal_mvar=.01,profile_id='LoadShape_pu'))
        for k in range(nmg):
            mid=f'{n}:campus-{k+5}'
            microgrids.append(dict(id=mid,parent_dn=n,pcc_bus=ids[2+k%3],allow_export=True,port_s_rating_mva=1.))
            loads.append(dict(id=f'{mid}:load',network_id=n,bus_id=ids[2+k%3],owner_type='MG',owner_id=mid,p_nominal_mw=.02,q_nominal_mvar=.004,profile_id='LoadShape_pu'))
            devices.extend([
             dict(id=f'{mid}:pv',network_id=n,bus_id=ids[2+k%3],owner_type='MG',owner_id=mid,kind='PV',p_nameplate_mw=.1,s_rating_mva=.11,profile_id='sun'),
             dict(id=f'{mid}:gt',network_id=n,bus_id=ids[2+k%3],owner_type='MG',owner_id=mid,kind='GT',p_min_mw=0.,p_max_mw=.1,cost_cny_per_mwh=560.,emission_kg_per_mwh=610.,power_factor=1.,ramp_up_mw_per_hour=.05,ramp_down_mw_per_hour=.05),
             dict(id=f'{mid}:battery',network_id=n,bus_id=ids[2+k%3],owner_type='MG',owner_id=mid,kind='BESS',p_charge_max_mw=.1,p_discharge_max_mw=.1,e_nameplate_mwh=.4,eta_charge=.95,eta_discharge=.94,soc_min=.15,soc_max=.95,soc_initial=.5,terminal_policy='equal_initial',throughput_cost_cny_per_mwh=2.)])
    for i,b in enumerate([205,205,900]):
        devices.append(dict(id=f'grid:source:{i}',kind='GEN',network_id='grid',bus_id=b,owner_type='TN',owner_id='grid',p_min_mw=0.,p_max_mw=5. if i<2 else 0.,q_min_mvar=-3.,q_max_mvar=3.,cost_coefficients=[0.,7.,0.],emission_kg_per_mwh=500.,ramp_up_mw_per_hour=2.,ramp_down_mw_per_hour=2.,status=1,fuel='NG' if i<2 else 'SYNC'))
    case=dict(case_format='tdm_case_v1',system_id='synthetic_mixed' if mixed else 'synthetic_small',data_version='test_only',networks=networks,devices=devices,loads=loads,interfaces=interfaces,microgrids=microgrids,profiles={'LoadShape_pu':[1.]*hours,'sun':[.5]*hours},time_grid={'intervals':list(range(hours)),'dt_hours':dt},safety={'voltage_min_pu':.95,'voltage_max_pu':1.05,'voltage_numerical_tol_pu':1e-4,'unified_pf_tolerance_mva':1e-4,'dn_input_audit_abs_tol_mw':1e-6,'input_audit_rel_tol':1e-9,'tn_slack_input_audit_abs_tol_mw':.001},cost_and_carbon={'carbon_price_cny_per_kg':.06142,'curtailment_cny_per_mwh':5.,'bess_throughput_cny_per_mwh':2.,'mandatory_load_shed_max_mw':0.},capabilities={'balanced':True,'radial_dn':True},source_manifest={'synthetic':True})
    case['system_hash']=fingerprint(case)
    return case


def scenario_for(case):
    count=len(case['time_grid']['intervals'])
    s=dict(scenario_id='TEST',day=1,system_hash=case['system_hash'],time_grid=copy.deepcopy(case['time_grid']),load_p={x['id']:[x['p_nominal_mw']]*count for x in case['loads']},load_q={x['id']:[x['q_nominal_mvar']]*count for x in case['loads']},available_p={x['id']:[x['p_nameplate_mw']*.5]*count for x in case['devices'] if x['kind'] in ('PV','WT')})
    s['scenario_hash']=fingerprint(s)
    return s
