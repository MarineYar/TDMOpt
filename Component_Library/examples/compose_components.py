"""Explicit selection of network formulations and optional model features."""
from case_fixtures import make_case, scenario_for
from tdm_workflow_agent.model_component.compiler import compile_model
from tdm_workflow_agent.model_component.registry import REGISTRY

case = make_case(hours=3, dt=1.)
selected = ['TN_ACOPF_FULL', 'DN_DISTFLOW_FULL', 'MG_GT_RAMP_MODEL',
            'MG_GT_UC', 'OBJ_INTERFACE_USAGE', 'CON_RESERVE_MARGIN']
result = compile_model(selected, case, scenario_for(case))
if not result.success:
    raise ValueError(result.errors)
for cid in selected:
    comp = REGISTRY.get(cid)
    print(cid, comp.selection_mode, comp.builder_import_path)
print('Built:', result.model.nvariables(), result.model.nconstraints())
