import ast
import copy
import importlib
import json
from pathlib import Path
import pytest
from case_fixtures import make_case, scenario_for
from tdm_workflow_agent.model_component.case_builders import build_case_model
from tdm_workflow_agent.model_component.compiler import compile_model
from tdm_workflow_agent.model_component.registry import REGISTRY


def test_private_workflow_imports_are_absent():
    root = Path(__file__).resolve().parents[1] / 'src'
    for path in root.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            names = ([node.module or ''] if isinstance(node, ast.ImportFrom)
                     else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
            for name in names:
                assert not name.startswith(('tdm_workflow_agent.llm', 'tdm_workflow_agent.baseline',
                                            'tdm_workflow_agent.solvers'))


def test_catalog_matches_public_registry_and_callable_paths():
    path = Path(importlib.import_module('tdm_workflow_agent.model_component').__file__).with_name('model_knowledge.json')
    cards = json.loads(path.read_text(encoding='utf-8'))['cards']
    assert len(cards) == len(REGISTRY) == 59
    assert sum(c['formal_selectable'] for c in cards) == 20
    for card in cards:
        comp = REGISTRY.get(card['component_id'])
        assert comp.selection_mode == card['selection_mode']
        module, name = card['builder_import_path'].rsplit('.', 1)
        assert callable(getattr(importlib.import_module(module), name))
        assert 'source_fingerprint' not in card


@pytest.mark.parametrize('cid', ['DN_LINDISTFLOW_LOSS_ITER', 'COORD_ADMM_TDM',
                                 'COORD_CENTRALIZED_TDM', 'MG_REN_Q_SUPPORT', 'missing'])
def test_excluded_ids_fail_explicitly(cid):
    case = make_case()
    with pytest.raises(ValueError):
        build_case_model(['TN_ACOPF_FULL', 'DN_DISTFLOW_FULL', cid], case, scenario_for(case), None)


def test_invalid_selection_and_profile_do_not_silently_fallback():
    case = make_case(); scenario = scenario_for(case)
    result = compile_model(['TN_DCOPF', 'TN_ACOPF_FULL', 'DN_DISTFLOW_FULL'], case, scenario)
    assert not result.success and result.model is None
    bad = copy.deepcopy(scenario)
    bad['load_p'][next(iter(bad['load_p']))] = [0.]
    with pytest.raises(ValueError, match='incomplete time grid'):
        build_case_model(['TN_ACOPF_FULL', 'DN_DISTFLOW_FULL'], case, bad, None)


def test_optional_constraints_create_actual_components():
    case = make_case(hours=3, dt=1.)
    selected = ['TN_ACOPF_FULL', 'DN_DISTFLOW_FULL', 'MG_GT_UC',
                'MG_GT_RAMP_MODEL', 'CON_TN_RAMP_LIMIT', 'CON_RESERVE_MARGIN',
                'CON_CARBON_INTENSITY_LIMIT', 'MG_BESS_PRECONDITION', 'MG_FLEX_PEAK_SHAVING']
    model, _ = build_case_model(selected, case, scenario_for(case), None)
    assert len(model.commitment) > 0
    assert len(model.MG_GT_RAMP_MODEL) > 0
    assert len(model.CON_TN_RAMP_LIMIT) > 0
    assert len(model.reserve) > 0
    assert model.carbon_intensity.active
    assert model._precharge_applicability['status'] == 'not_applicable'
    assert len(model.peak_shave) > 0


@pytest.mark.parametrize('tn', ['TN_DCOPF', 'TN_LINEARIZED_ACOPF', 'TN_ACOPF_SOCP', 'TN_ACOPF_FULL'])
@pytest.mark.parametrize('dn', ['DN_LINDISTFLOW', 'DN_LINDISTFLOW_LOSS_FIXED', 'DN_DISTFLOW_SOCP', 'DN_DISTFLOW_SOCP_LIN', 'DN_DISTFLOW_FULL'])
def test_lossy_assembled_models_have_distinct_endpoint_equations(tn, dn):
    from tdm_workflow_agent.data.case_schema import case_hash
    case = make_case()
    case['interface_model'] = 'series_impedance_oltc_v1'
    for interface in case['interfaces']:
        interface['interface_model'] = 'series_impedance_oltc_v1'
    case['system_hash'] = case_hash(case)
    model, _ = build_case_model([tn, dn], case, scenario_for(case), None)
    assert len(model.port_active_loss) == len(model.T)
    assert len(model.port_current_power) == len(model.T)
    if tn == 'TN_DCOPF':
        assert len(model.dc_reactive_capacity) == len(model.T)
