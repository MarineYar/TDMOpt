"""Model Component Registry — singleton registry for all components."""
from __future__ import annotations
from typing import Any
from tdm_workflow_agent.model_component.base import ModelComponent


# The single public source of truth for base-model IDs.  Every compiler,
# compatibility, schema, and LLM selection path imports these sets.
TN_BASE_MODELS = frozenset({
    "TN_DCOPF",
    "TN_LINEARIZED_ACOPF",
    "TN_ACOPF_SOCP",
    "TN_ACOPF_FULL",
})
DN_BASE_MODELS = frozenset({
    "DN_LINDISTFLOW",
    "DN_LINDISTFLOW_LOSS_FIXED",
    "DN_DISTFLOW_SOCP",
    "DN_DISTFLOW_SOCP_LIN",
    "DN_DISTFLOW_FULL",
})


class ComponentRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._components: dict[str, ModelComponent] = {}
        return cls._instance

    def register(self, comp: ModelComponent) -> None:
        if comp.component_id in self._components:
            raise ValueError(f"Duplicate component_id: {comp.component_id}")
        self._components[comp.component_id] = comp

    def get(self, component_id: str) -> ModelComponent | None:
        return self._components.get(component_id)

    def list_components(self, category: str | None = None, layer: str | None = None,
                        selectable_only: bool = True, implemented_only: bool = True) -> list[ModelComponent]:
        result = []
        for c in self._components.values():
            if implemented_only and not c.implemented:
                continue
            if selectable_only and c.selection_mode not in {
                "mandatory_core", "adaptive_exclusive", "adaptive_multi_select",
            }:
                continue
            if category and c.category != category:
                continue
            if layer and c.layer != layer:
                continue
            result.append(c)
        return result

    def list_selectable(self) -> list[ModelComponent]:
        return [
            c for c in self._components.values()
            if c.implemented and c.selectable_by_llm and c.selection_mode in {
                "adaptive_exclusive", "adaptive_multi_select",
            }
        ]

    def list_mandatory(self) -> list[ModelComponent]:
        return [
            c for c in self._components.values()
            if c.implemented and c.selection_mode == "mandatory_core"
        ]

    def list_formal_by_layer(self, layer: str) -> list[ModelComponent]:
        return [
            c for c in self._components.values()
            if c.implemented and c.layer == layer and c.selection_mode != "non_formal"
        ]

    def selection_groups(self) -> dict[str, tuple[str, ...]]:
        groups: dict[str, list[str]] = {}
        for component in self.list_selectable():
            groups.setdefault(component.selection_group, []).append(component.component_id)
        return {key: tuple(sorted(value)) for key, value in sorted(groups.items())}

    def to_llm_catalog_list(self) -> list[dict]:
        """Export selectable component catalog for LLM prompt."""
        return [c.to_dict() for c in self.list_selectable()]

    def validate_ids(self, component_ids: list[str], allow_mandatory: bool = True) -> tuple[bool, list[str]]:
        """Check all IDs are registered and implemented.
        If allow_mandatory=True, mandatory components pass even if not selectable_by_llm."""
        errors = []
        for cid in component_ids:
            comp = self._components.get(cid)
            if comp is None:
                errors.append(f"Unknown component: {cid}")
            elif not comp.implemented:
                errors.append(f"Not implemented: {cid}")
            elif comp.selection_mode == "non_formal":
                errors.append(f"Non-formal component: {cid}")
            elif comp.selection_mode == "mandatory_core" and not allow_mandatory:
                errors.append(f"Mandatory component is not an adaptive selection: {cid}")
        return len(errors) == 0, errors

    def validate_case_ids(self, component_ids: list[str], case: dict) -> tuple[bool, list[str]]:
        """Apply the loaded case's route restrictions without global registry mutation."""
        from tdm_workflow_agent.data.interface_support import lossy_case, validate_supported
        ok, errors = self.validate_ids(component_ids)
        if not ok or not lossy_case(case):
            return ok, errors
        choices = [[cid for cid in component_ids if cid in base]
                   for base in (TN_BASE_MODELS, DN_BASE_MODELS)]
        if any(len(ids) != 1 for ids in choices):
            return False, ['requires exactly one TN and DN component']
        try:
            validate_supported(case, choices[0][0], choices[1][0], 'centralized')
        except ValueError as exc:
            return False, [str(exc)]
        return True, []

    def __contains__(self, component_id: str) -> bool:
        return component_id in self._components

    def __len__(self) -> int:
        return len(self._components)


# Global singleton
REGISTRY = ComponentRegistry()
