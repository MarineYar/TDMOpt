"""Model Component Base — dataclass for all selectable/compilable components."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ModelComponent:
    component_id: str
    name_cn: str
    name_en: str
    category: str          # e.g. "tn_base", "dn_base", "mg_base", "coordination", "objective", "constraint", "uncertainty", "validation"
    layer: str             # "TN", "DN", "MG", "Coordination", "Objective", "Constraint", "Uncertainty", "Validation"
    formulation_type: str  # "LP", "MILP", "QP", "MIQP", "SOCP", "MISOCP", "nonconvex_QCQP", "MIQCP"
    solver_class: str      # "LP", "MILP", "SOCP", "nonconvex_QCQP"
    implemented: bool = True
    selectable_by_llm: bool = True
    mandatory: bool = False
    description_cn: str = ""
    description_en: str = ""
    formula_latex: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    parameters: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    objective_terms: list[str] = field(default_factory=list)
    required_data: list[str] = field(default_factory=list)
    output_variables: list[str] = field(default_factory=list)
    compatible_with: list[str] = field(default_factory=list)
    incompatible_with: list[str] = field(default_factory=list)
    implementation_note: str = ""

    # Formal six-layer selection/execution contract.  These fields are the
    # registry source of truth used by Model RAG, composition validation, and
    # the pre-solver fidelity gate.
    selection_mode: str = "non_formal"
    selection_group: str = ""
    execution_binding: str = "builder"
    builder_import_path: str = ""
    topology_applicability: dict[str, Any] = field(default_factory=dict)
    requires: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    deterministic_metadata: dict[str, Any] = field(default_factory=dict)
    expected_effects: dict[str, list[str]] = field(default_factory=dict)

    # ── Callbacks ──
    # add_variables(model, system_data, scenario_data, config) → adds Pyomo vars
    add_variables_fn: Callable | None = None
    # add_constraints(model, system_data, scenario_data, config) → adds Pyomo constraints
    add_constraints_fn: Callable | None = None
    # add_objective_terms(model, system_data, scenario_data, config) → returns list of Pyomo expressions
    add_objective_fn: Callable | None = None

    def validate_data(self, system_data: Any, scenario_data: Any, config: dict) -> bool:
        """Check if required data is present. Return True if OK."""
        return True

    def to_dict(self) -> dict:
        return {
            "component_id": self.component_id,
            "name_cn": self.name_cn, "name_en": self.name_en,
            "category": self.category, "layer": self.layer,
            "formulation_type": self.formulation_type, "solver_class": self.solver_class,
            "implemented": self.implemented, "selectable_by_llm": self.selectable_by_llm,
            "mandatory": self.mandatory,
            "description_cn": self.description_cn, "description_en": self.description_en,
            "formula_latex": self.formula_latex,
            "variables": self.variables, "parameters": self.parameters,
            "constraints": self.constraints, "objective_terms": self.objective_terms,
            "compatible_with": self.compatible_with, "incompatible_with": self.incompatible_with,
            "selection_mode": self.selection_mode,
            "selection_group": self.selection_group,
            "execution_binding": self.execution_binding,
            "builder_import_path": self.builder_import_path,
            "topology_applicability": self.topology_applicability,
            "requires": self.requires, "provides": self.provides,
            "deterministic_metadata": self.deterministic_metadata,
            "expected_effects": self.expected_effects,
        }
