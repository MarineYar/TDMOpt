"""Standalone compiler: no Agent configuration, execution routes or solvers."""
from dataclasses import dataclass, field
from typing import Any
from .builders import build_component_model


@dataclass
class CompileResult:
    model: Any
    success: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    component_audit: dict = field(default_factory=dict)


def compile_model(selected_ids: list[str], system_data: dict, scenario_config: dict,
                  method_config: Any = None) -> CompileResult:
    """Build a canonical case, returning input/selection errors without solving."""
    try:
        model, audit = build_component_model(selected_ids, system_data, scenario_config, method_config)
    except ValueError as exc:
        return CompileResult(None, False, errors=[str(exc)])
    return CompileResult(model, True, component_audit=audit)
