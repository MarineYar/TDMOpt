"""Use the original low-level function for a TN-only ACOPF formulation."""
import pyomo.environ as pyo
from case_fixtures import make_case
from tdm_workflow_agent.model_component.case_tn_models import build_tn_network

model = pyo.ConcreteModel()
model.T = pyo.Set(initialize=[0])
model.tn = pyo.Block()
network = make_case()['networks'][0]
model.p = pyo.Var(model.T, bounds=(0., 5.))
model.q = pyo.Var(model.T, bounds=(-3., 3.))


def injection(bus, t, quantity):
    # P generation/load in MW, Q generation/load in MVAr, generation positive.
    if bus == 205:
        return model.p[t] if quantity == 'p' else model.q[t]
    if bus == 101:
        return -.1 if quantity == 'p' else -.02
    return 0.


build_tn_network(model, model.tn, network, 'TN_ACOPF_FULL', injection)
model.obj = pyo.Objective(expr=sum(model.p[t] for t in model.T))
print('TN-only ACOPF built:', model.nvariables(), model.nconstraints())
