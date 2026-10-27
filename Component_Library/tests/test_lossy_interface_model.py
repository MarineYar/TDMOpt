"""Independent complex-current checks of exact receiving-end interface equations."""
import cmath
import math
from types import SimpleNamespace
import pytest
import pyomo.environ as pyo


def fixture(tau=1.,base=100.,rating=60.,current=.2+.1j):
    from tdm_workflow_agent.model_component import case_interfaces as api
    m=pyo.ConcreteModel();m._tn_component='TN_ACOPF_FULL';m.T=pyo.Set(initialize=[0]);m.PORT=pyo.Set(initialize=['opaque:7'])
    record=dict(id='opaque:7',parent_network='upper',parent_bus=77,child_network='lower',child_bus=9,s_rating_mva=rating,physical_replay_vkr_percent=.0001,physical_replay_vk_percent=.001,tau_min=.9,tau_step=.00625,tap_positions=33,neutral_position=16,allow_active_export=True,allow_reactive_export=True)
    m._ports={'opaque:7':record};m._case_data=dict(interface_model='series_impedance_oltc_v1',networks=[dict(id='upper',layer='TN',base_mva=base),dict(id='lower',layer='DN',base_mva=10.)])
    m.port_p=pyo.Var(m.PORT,m.T,initialize=0.);m.port_q=pyo.Var(m.PORT,m.T,initialize=0.)
    m.tap=pyo.Var(m.PORT,m.T,initialize=(tau-.9)/.00625);m.tau=pyo.Expression(m.PORT,m.T,rule=lambda m,r,t:.9+.00625*m.tap[r,t])
    m.network=pyo.Block(['upper','lower']);m.network['upper'].u=pyo.Var([77],[0],initialize=1.);m.network['lower'].u=pyo.Var([9],[0],initialize=1.)
    api.add_endpoint_variables(m);api.add_endpoint_constraints(m)
    # Independent phasor derivation from the unchanged physical two-port impedance.
    r=.0001/100*base/rating;x=math.sqrt((.001/100)**2-(.0001/100)**2)*base/rating
    vh=1.01*cmath.exp(.17j);vl=tau*vh-complex(r,x)*current
    sl=base*vl*current.conjugate();sh=base*tau*vh*current.conjugate()
    for comp,val in [(m.port_p,sl.real),(m.port_q,sl.imag),(m.port_from_p,sh.real),(m.port_from_q,sh.imag),(m.port_ell,abs(current)**2)]:comp['opaque:7',0].set_value(val)
    m.network['upper'].u[77,0].set_value(abs(vh)**2);m.network['lower'].u[9,0].set_value(abs(vl)**2)
    return m,api


@pytest.mark.parametrize('tau',[.9,1.,1.1])
@pytest.mark.parametrize('base,rating',[(100.,60.),(10.,80.)])
@pytest.mark.parametrize('current',[.3+.2j,.3-.2j,-.3+.2j,-.3-.2j])
def test_two_port_equivalent_to_independent_phasors(tau,base,rating,current):
    m,api=fixture(tau,base,rating,current)
    for name in ['port_active_loss','port_reactive_loss','port_voltage','port_current_power']:
        c=getattr(m,name)['opaque:7',0];assert abs(pyo.value(c.body-c.lower))<1e-10
    assert not hasattr(m,'port_ideal_voltage')
    assert pyo.value(m.port_from_p['opaque:7',0]-m.port_p['opaque:7',0])>0


def test_removing_loss_is_detected_and_both_capacities_exist():
    m,api=fixture(current=.5+.1j)
    m.port_from_p['opaque:7',0].set_value(pyo.value(m.port_p['opaque:7',0]))
    assert abs(pyo.value(m.port_active_loss['opaque:7',0].body))>1e-6
    assert len(m.port_from_rating)==1 and len(m.port_to_rating)==1


def test_export_parameter_basis_and_alias():
    m,api=fixture();out={};api.export_endpoints(m,out)
    assert out['interface_model']=='series_impedance_oltc_v1'
    assert out['interface_parameters']['opaque:7']['base_mva']==100.
    assert out['interface_to_p']['opaque:7']==[pyo.value(m.port_p['opaque:7',0])]
    assert out['interface_loss_p']['opaque:7'][0]>0


@pytest.mark.parametrize('sign',[-1,1])
def test_near_rating_and_independent_endpoint_overload(sign):
    # High-end loading 99.99% of rating; both current directions are tested.
    current=sign*.9999*60./(100.*1.01)*complex(.8,.6)
    m,api=fixture(current=current)
    high=m.port_from_rating['opaque:7',0];low=m.port_to_rating['opaque:7',0]
    assert pyo.value(high.body)<=pyo.value(high.upper)
    assert pyo.value(low.body)<=pyo.value(low.upper)
    m.port_from_p['opaque:7',0].set_value(61.,skip_validation=True)
    assert pyo.value(high.body)>pyo.value(high.upper)
    assert pyo.value(low.body)<=pyo.value(low.upper)
