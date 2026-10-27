"""Standalone canonical-case assembly entry point; legacy data loaders excluded."""
from typing import Any
from .case_builders import build_case_model


def build_component_model(selected_ids: list[str], system_data: dict,
                          scenario_config: dict, method_config: Any = None, *,
                          strict_selection: bool = False) -> tuple[Any, dict]:
    """Build only. All choices are checked, regardless of strict_selection."""
    if system_data.get('case_format') != 'tdm_case_v1':
        raise ValueError('Standalone library requires case_format=tdm_case_v1')
    return build_case_model(selected_ids, system_data, scenario_config, method_config)
