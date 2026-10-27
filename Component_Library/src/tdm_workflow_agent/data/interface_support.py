"""Case-local support contract for the exact lossy two-terminal interface."""
from __future__ import annotations

INTERFACE_MODEL = 'series_impedance_oltc_v1'
SUPPORTED_TN = ('TN_DCOPF', 'TN_LINEARIZED_ACOPF', 'TN_ACOPF_SOCP', 'TN_ACOPF_FULL')
SUPPORTED_DN = ('DN_LINDISTFLOW', 'DN_LINDISTFLOW_LOSS_FIXED', 
                'DN_DISTFLOW_SOCP', 'DN_DISTFLOW_SOCP_LIN', 'DN_DISTFLOW_FULL')
SUPPORTED_COORDINATION = ()
SUPPORTED_COORDINATION_MODES = ('CENTRALIZED',)


def lossy_case(case: dict) -> bool:
    return case.get('interface_model') == INTERFACE_MODEL


def component_supported(case: dict, component_id: str, layer: str) -> bool:
    if not lossy_case(case):
        return True
    from tdm_workflow_agent.model_component.registry import REGISTRY

    component = REGISTRY.get(component_id)
    if (component is not None and component.layer == layer and component.implemented
            and component.selection_mode == 'mandatory_core'):
        # Required resource/interface equations are not competing base formulations.
        return True
    allowed = {'TN': SUPPORTED_TN, 'DN': SUPPORTED_DN,
               'Coordination': SUPPORTED_COORDINATION}.get(layer)
    return allowed is None or component_id in allowed


def validate_supported(case: dict, tn_component: str, dn_component: str,
                       coordination_mode: str) -> None:
    """Reject unsupported new-case routes; legacy routes retain their own rules."""
    declared = case.get('interface_model')
    if declared and declared not in (INTERFACE_MODEL, 'legacy_near_ideal_oltc'):
        raise ValueError(f'unsupported interface_model: {declared}')
    if not lossy_case(case):
        if any(i.get('interface_model') == INTERFACE_MODEL for i in case.get('interfaces', [])):
            raise ValueError('unsupported mixed root/interface model declarations')
        return
    mode = coordination_mode.upper()
    if (tn_component not in SUPPORTED_TN or dn_component not in SUPPORTED_DN
            or mode not in SUPPORTED_COORDINATION_MODES):
        raise ValueError(f'unsupported {INTERFACE_MODEL} combination: '
                         f'{tn_component}/{dn_component}/{coordination_mode}; '
                         'requires an adapted balanced TN/radial DN pair and an '
                         'explicitly supported coordination route')
    interfaces = case.get('interfaces', [])
    if any(i.get('interface_model') != INTERFACE_MODEL for i in interfaces):
        raise ValueError('unsupported mixed ideal/lossy interfaces')
    if 'networks' in case:
        dns = {n['id'] for n in case['networks'] if n['layer'] == 'DN'}
        children = [i['child_network'] for i in interfaces]
        if len(children) != len(set(children)) or set(children) != dns:
            raise ValueError('unsupported topology: exact angle elimination requires one interface per DN')


def support_declaration() -> dict:
    return {'interface_model': INTERFACE_MODEL,
            'tn_components': list(SUPPORTED_TN),
            'dn_components': list(SUPPORTED_DN),
            'coordination_components': [],
            'assembled_problem_class': 'Inspect assembled model: exact interfaces and device constraints can be nonconvex NLP even with linear network models.',
            'numerical_validation': 'Build tests only; no AC replay or coordination algorithm included.'}
