"""Component Compatibility Checker."""
from __future__ import annotations
from tdm_workflow_agent.model_component.registry import (
    DN_BASE_MODELS,
    REGISTRY,
    TN_BASE_MODELS,
)

# Base-model IDs are imported from registry.py, the sole public source of truth.
MG_BASE_MODELS = {"MG_ACTIVE_BALANCE"}
COORDINATION_MODELS = {"COORD_CENTRALIZED_TDM", "COORD_SEQUENTIAL_TD_MG",
                       "COORD_HIERARCHICAL_TD_MG",
                       "COORD_PRICE_BASED",
                       "COORD_ADMM_TDM", "COORD_SLP", "COORD_SQP"}

# Extensions that need a base
TN_EXTENSIONS = {"TN_LOW_CARBON_EXTENSION", "TN_RESERVE_EXTENSION", "TN_RAMP_EXTENSION", "TN_LINEARIZED_AC_EXTENSION"}
DN_EXTENSIONS = {"DN_REACTIVE_SUPPORT_EXTENSION", "DN_VOLTAGE_MARGIN_EXTENSION", "DN_RENEWABLE_CURTAILMENT_MODEL",
                 "DN_BESS_ACTIVE_MODEL", "DN_FLEX_LOAD_MODEL", "DN_LOSS_AWARE_MODEL", "DN_DISCRETE_DEVICE_MODEL"}

# Forbidden and required dependencies
DEPENDENCIES = {
    "MG_TERMINAL_SOC_CONSTRAINT": [],  # MG_BESS_SOC built into MG builder
    "MG_GT_RAMP_MODEL": [],  # MG_GT_DISPATCH built into MG builder
    "CON_CARBON_CAP": ["TN_LOW_CARBON_EXTENSION"],
    "COORD_ADMM_TDM": ["COORD_BOUNDARY_POWER_EXCHANGE"],
    "COORD_HIERARCHICAL_TD_MG": ["COORD_BOUNDARY_POWER_EXCHANGE"],
    "COORD_PRICE_BASED": ["COORD_BOUNDARY_POWER_EXCHANGE"],
}

FORBIDDEN = {"COORD_PCE_EQUIVALENT_PROJECTION", "P_only_LinDistFlow", "safe_fallback_conservative"}


def check_compatibility(component_ids: list[str]) -> tuple[bool, list[str], list[str]]:
    """Check selected component compatibility.
    Returns (ok, errors, warnings).
    """
    errors = []
    warnings = []
    ids = set(component_ids)

    # Reject unavailable IDs without relying on a private schema.
    for cid in component_ids:
        comp = REGISTRY.get(cid)
        if comp is None:
            errors.append(f"Unknown component: {cid}")
        elif not comp.implemented:
            errors.append(f"Not implemented: {cid}")
        elif comp.selection_mode == "non_formal":
            errors.append(f"Non-formal component: {cid}")

    # 1. Check no forbidden components
    for fid in FORBIDDEN:
        if fid in ids:
            errors.append(f"Forbidden component: {fid}")

    # 2. Check at least one TN base
    tn_bases = ids & TN_BASE_MODELS
    if not tn_bases:
        errors.append("No TN base model selected")
    if len(tn_bases) > 1:
        errors.append(f"Multiple TN base models: {tn_bases}")

    # 3. Check at least one DN base
    dn_bases = ids & DN_BASE_MODELS
    if not dn_bases:
        errors.append("No DN base model selected")
    if len(dn_bases) > 1:
        errors.append(f"Multiple DN base models: {dn_bases}")

    # 4. Check MG base — auto-included, not selectable by LLM
    mg_bases = ids & MG_BASE_MODELS
    if not mg_bases:
        pass  # MG_ACTIVE_BALANCE is auto-included by compiler

    # 5. Check coordination — exactly one
    coord_models = ids & COORDINATION_MODELS
    if len(coord_models) > 1:
        errors.append(f"Multiple coordination methods: {coord_models}")
        # MG_ACTIVE_BALANCE is auto-included by compiler; not an error if missing
        pass

    # 5. Check dependencies
    for cid, deps in DEPENDENCIES.items():
        if cid in ids:
            for dep in deps:
                if dep not in ids:
                    errors.append(f"{cid} requires {dep} (not selected)")

    # 6. Check incompatible pairs (from component definitions)
    for cid in ids:
        comp = REGISTRY.get(cid)
        if comp:
            for inc in comp.incompatible_with:
                if inc in ids:
                    errors.append(f"Incompatible: {cid} with {inc}")

    # 7. DN_REACTIVE_SUPPORT_EXTENSION needs Q-capable DN
    if "DN_REACTIVE_SUPPORT_EXTENSION" in ids:
        q_capable = DN_BASE_MODELS
        if not (dn_bases & q_capable):
            errors.append("DN_REACTIVE_SUPPORT_EXTENSION requires Q-capable DN model")

    # 8. TN_LINEARIZED_AC_EXTENSION requires a TN base model
    if "TN_LINEARIZED_AC_EXTENSION" in ids and not tn_bases:
        errors.append("TN_LINEARIZED_AC_EXTENSION requires a canonical TN base model")

    # 9. Continuous nonconvex solve; the backend is selected centrally.
    nonconvex = {"TN_ACOPF_FULL", "DN_DISTFLOW_FULL"}
    needs_nonconvex = bool(ids & nonconvex)
    if needs_nonconvex:
        warnings.append("Selected components require a continuous nonconvex solve")

    # 10. ADMM/price/hierarchical viability
    if "COORD_ADMM_TDM" in ids:
        warnings.append("ADMM T-D-MG coordination selected — may require more iterations than centralized")

    return len(errors) == 0, errors, warnings


def get_formulation_type(component_ids: list[str]) -> str:
    """Determine formulation type from selected components.

    Design rule:
      - BESS ch/dis is genuinely continuous (bounds [0,Pmax]) — no relaxation needed.
      - GT dispatch is continuous (bounds [0,Pmax]) — base MG model has no binaries.
      - MG_GT_UC and its internal alias add continuous commitment fractions.
      - Actual integer domains are checked by compiler and solver, not inferred
        from a component's historical name.

    Returns one of: LP, SOCP, nonconvex_QCQP
    """
    ids = set(component_ids)
    has_nonconvex = bool(ids & {"TN_ACOPF_FULL", "DN_DISTFLOW_FULL"})
    has_socp = bool(ids & {"DN_DISTFLOW_SOCP", "DN_DISTFLOW_SOCP_LIN", "TN_ACOPF_SOCP"})

    if has_nonconvex:
        return "nonconvex_QCQP"
    elif has_socp:
        return "SOCP"
    return "LP"
