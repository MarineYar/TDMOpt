"""Build an ACOPF + DistFlow model without an LLM or solver."""
import pyomo.environ as pyo
from case_fixtures import make_case, scenario_for
from tdm_workflow_agent.model_component.case_builders import build_case_model


def main():
    case = make_case()
    model, audit = build_case_model(
        ['TN_ACOPF_FULL', 'DN_DISTFLOW_FULL'], case, scenario_for(case), None)
    print(model.name)
    print('Variables:', model.nvariables(), 'Constraints:', model.nconstraints())
    print('Bindings:', len(audit['builder_invocations']))
    print('Built only; no optimization has been run.')
    return model


if __name__ == '__main__':
    main()
