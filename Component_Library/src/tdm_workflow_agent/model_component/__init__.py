"""Model Component Library — registers all components on import."""
from tdm_workflow_agent.model_component.base import ModelComponent
from tdm_workflow_agent.model_component.registry import (
    DN_BASE_MODELS,
    REGISTRY,
    TN_BASE_MODELS,
)

_CANONICAL_COORDINATION_IDS = frozenset({
    "COORD_CENTRALIZED_TDM",
    "COORD_SEQUENTIAL_TD_MG",
    "COORD_HIERARCHICAL_TD_MG",
    "COORD_ADMM_TDM",
    "COORD_PRICE_BASED",
})

_INTEGRATED_CORE_IDS = frozenset({
    "MG_ACTIVE_BALANCE", "MG_BESS_SOC_MODEL",
    "MG_RENEWABLE_CURTAILMENT_MODEL", "MG_GT_DISPATCH_MODEL",
    "DN_REACTIVE_SUPPORT_EXTENSION", "DN_RENEWABLE_CURTAILMENT_MODEL",
    "DN_BESS_ACTIVE_MODEL", "COORD_BOUNDARY_POWER_EXCHANGE",
    "CON_TN_POWER_BALANCE", "CON_TN_BRANCH_FLOW_LIMIT",
    "CON_TN_GENERATOR_LIMIT", "CON_TN_VOLTAGE_LIMIT_AC",
    "CON_DN_P_BALANCE", "CON_DN_Q_BALANCE",
    "CON_DN_VOLTAGE_LIMIT", "CON_DN_BRANCH_FLOW_LIMIT",
    "CON_DN_GT_P_LIMIT", "CON_DN_GT_Q_SUPPORT",
    "CON_DN_PV_WT_CURTAILMENT", "CON_DN_BESS_SOC",
    "CON_DN_BESS_CH_DIS_MUTEX", "CON_DN_FLEX_LOAD_LIMIT",
    "CON_MG_ACTIVE_BALANCE", "CON_MG_GT_LIMIT",
    "CON_MG_BESS_SOC", "CON_MG_BESS_CH_DIS_MUTEX",
    "CON_SYSTEM_POWER_BALANCE", "CON_BOUNDARY_POWER_CONSISTENCY",
})

def _reg(**kwargs) -> ModelComponent:
    component_id = kwargs["component_id"]
    category = kwargs["category"]
    layer = kwargs["layer"]
    implemented = bool(kwargs.get("implemented", True))
    selectable = bool(kwargs.get("selectable_by_llm", True))
    mandatory = bool(kwargs.get("mandatory", False))

    if mandatory or component_id in _INTEGRATED_CORE_IDS:
        selection_mode = "mandatory_core"
    elif not implemented or not selectable:
        selection_mode = "non_formal"
    elif category == "tn_base":
        selection_mode = "adaptive_exclusive"
    elif category == "dn_base":
        selection_mode = "adaptive_exclusive"
    elif component_id in _CANONICAL_COORDINATION_IDS:
        selection_mode = "adaptive_exclusive"
    else:
        selection_mode = "adaptive_multi_select"

    if category == "tn_base":
        selection_group = "tn_formulation"
    elif category == "dn_base":
        selection_group = "dn_formulation"
    elif component_id in _CANONICAL_COORDINATION_IDS:
        selection_group = "coordination_formulation"
    elif selection_mode == "adaptive_multi_select":
        selection_group = f"{layer.casefold()}_extensions"
    else:
        selection_group = ""

    if component_id in _CANONICAL_COORDINATION_IDS:
        execution_binding = "solve_route"
    elif mandatory or component_id in _INTEGRATED_CORE_IDS:
        execution_binding = "integrated"
    else:
        execution_binding = "builder"

    kwargs.setdefault("selection_mode", selection_mode)
    kwargs.setdefault("selection_group", selection_group)
    kwargs.setdefault("execution_binding", execution_binding)
    kwargs.setdefault("topology_applicability", {"layers": [layer]})
    kwargs.setdefault("requires", [])
    kwargs.setdefault("provides", [f"{layer.upper()}::{component_id}"])
    kwargs.setdefault("deterministic_metadata", {})
    kwargs.setdefault("expected_effects", {
        "variables": list(kwargs.get("variables", [])),
        "constraints": list(kwargs.get("constraints", [])),
        "objective_terms": list(kwargs.get("objective_terms", [])),
    })
    c = ModelComponent(**kwargs)
    REGISTRY.register(c)
    return c

_reg(component_id="TN_DCOPF", name_cn="主网DC-OPF", name_en="DC Optimal Power Flow", category="tn_base", layer="TN", formulation_type="LP/MILP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="9-bus DC OPF: 纯有功优化，V=1.0固定。最快LP。适用于无电压/无功问题的常规经济调度。", description_en="DC OPF: P-only, V=1.0 fixed. Fast LP. Sufficient for normal economic dispatch without voltage issues.", formula_latex=["∑P_g + ∑F_in - ∑F_out = P_L + P_TD", "F_ij=B_ij(θ_i-θ_j)", "-F_max≤F_ij≤F_max"])
_reg(component_id="DN_REACTIVE_SUPPORT_EXTENSION", name_cn="配网无功支撑", name_en="DN Reactive Support", category="dn_extension", layer="DN", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_cn="DN Reactive Support (built into canonical DN base builders — GT Q + SVC Q in Q balance)", description_en="DN Reactive Support", formula_latex=["Q_GT=P_GT·tan(acos(pf))", "-Qmax≤Q_SVC≤Qmax"], implementation_note="Built into canonical DN base builders — not a separate selectable component")
_reg(component_id="DN_RENEWABLE_CURTAILMENT_MODEL", name_cn="配网可再生弃电", name_en="DN Renewable Curtailment", category="dn_extension", layer="DN", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_cn="DN Renewable Curtailment (built into DN resource builders)", description_en="DN Renewable Curtailment", formula_latex=["P_curt=P_avail-P_used"], implementation_note="Built into _add_dn_pv/_add_dn_wt resource builders — not a separate selectable component")
_reg(component_id="DN_BESS_ACTIVE_MODEL", name_cn="配网储能模型", name_en="DN BESS Active Model", category="dn_extension", layer="DN", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_cn="DN BESS Active Model (built into DN resource builders)", description_en="DN BESS Active Model", formula_latex=["0≤P_ch≤zP_max", "SOC_{t+1}=SOC_t+ηP_ch-P_dis/η"], implementation_note="Built into _add_dn_bess resource builder — not a separate selectable component")
_reg(component_id="DN_FLEX_LOAD_MODEL", name_cn="配网柔性负荷", name_en="DN Flex Load Model", category="dn_extension", layer="DN", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="DN Flex Load Model", description_en="DN Flex Load Model", formula_latex=["0≤P_flex≤P_max"])
_reg(component_id="MG_ACTIVE_BALANCE", name_cn="微网有功平衡", name_en="MG Active Balance", category="mg_base", layer="MG", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_cn="MG has NO internal topology — aggregate resource model. Auto-included by DN builders.", description_en="MG Active Balance", formula_latex=["P_ex+P_GT+P_PV+P_WT+P_dis=P_load+P_ch"], implementation_note="Auto-built by _add_mg() in DN builders — not a separate selectable component")
_reg(component_id="MG_BESS_SOC_MODEL", name_cn="微网储能SOC", name_en="MG BESS SOC", category="mg_extension", layer="MG", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_cn="MG BESS SOC (built into MG builder)", description_en="MG BESS SOC", formula_latex=["SOC_{t+1}=SOC_t+ηP_ch-P_dis/η"], implementation_note="Built into _add_mg() — SOC dynamics always included in MG model")
_reg(component_id="MG_TERMINAL_SOC_CONSTRAINT", name_cn="微网终端SOC", name_en="MG Terminal SOC", category="mg_extension", layer="MG", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="MG Terminal SOC", description_en="MG Terminal SOC", formula_latex=["SOC_T=SOC_0"])
_reg(component_id="MG_RENEWABLE_CURTAILMENT_MODEL", name_cn="微网可再生弃电", name_en="MG Renewable Curtailment", category="mg_extension", layer="MG", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_cn="MG Renewable Curtailment (built into MG builder)", description_en="MG Renewable Curtailment", formula_latex=["P_curt=P_avail-P_used"], implementation_note="Built into _add_mg() — PV/WT curtailment always included in MG model")
_reg(component_id="MG_GT_DISPATCH_MODEL", name_cn="微网GT调度", name_en="MG GT Dispatch", category="mg_extension", layer="MG", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_cn="MG GT Dispatch (built into MG builder)", description_en="MG GT Dispatch", formula_latex=["0≤P_GT≤P_max"], implementation_note="Built into _add_mg() — GT dispatch always included in MG model")
_reg(component_id="MG_GT_RAMP_MODEL", name_cn="微网GT爬坡", name_en="MG GT Ramp", category="mg_extension", layer="MG", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="MG GT Ramp", description_en="MG GT Ramp", formula_latex=["-R_down≤ΔP≤R_up"])
_reg(component_id="MG_CARBON_MODEL", name_cn="微网碳排放", name_en="MG Carbon", category="mg_extension", layer="MG", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="MG Carbon", description_en="MG Carbon", formula_latex=["E=Σε·P_GT"])
_reg(component_id="COORD_BOUNDARY_POWER_EXCHANGE", name_cn="边界功率一致性", name_en="Boundary Power Consistency", category="coordination", layer="Coordination", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_cn="Boundary Power Consistency (implicit in centralized coupling)", description_en="Boundary Power Consistency", formula_latex=["P_TD+P_DT=0"], implementation_note="Implicit in centralized T-D-MG model — not a separate selectable component")
_reg(component_id="OBJ_FUEL_COST", name_cn="燃料成本", name_en="Fuel Cost", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Fuel Cost", formula_latex=["Fuel Cost"])
_reg(component_id="OBJ_CARBON_COST", name_cn="碳成本", name_en="Carbon Cost", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Carbon Cost", formula_latex=["Carbon Cost"])
_reg(component_id="OBJ_RENEWABLE_CURTAILMENT", name_cn="弃电惩罚", name_en="Renewable Curtailment", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Renewable Curtailment", formula_latex=["Renewable Curtailment"])
_reg(component_id="OBJ_LOAD_SHEDDING", name_cn="切负荷惩罚", name_en="Load Shedding", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Load Shedding", formula_latex=["Load Shedding"])
_reg(component_id="OBJ_VOLTAGE_DEVIATION", name_cn="电压偏差惩罚", name_en="Voltage Deviation", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Voltage Deviation", formula_latex=["Voltage Deviation"])
_reg(component_id="OBJ_INTERFACE_USAGE", name_cn="接口使用成本", name_en="Interface Usage", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Interface Usage", formula_latex=["Interface Usage"])
_reg(component_id="OBJ_BESS_THROUGHPUT", name_cn="储能吞吐成本", name_en="BESS Throughput", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="BESS Throughput", formula_latex=["BESS Throughput"])
_reg(component_id="OBJ_GT_RAMPING", name_cn="GT爬坡成本", name_en="GT Ramping", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="GT Ramping", formula_latex=["GT Ramping"])
_reg(component_id="OBJ_MG_COMFORT_LOSS", name_cn="微网舒适度损失", name_en="MG Comfort Loss", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="MG Comfort Loss", formula_latex=["MG Comfort Loss"])
_reg(component_id="CON_SYSTEM_POWER_BALANCE", name_cn="系统功率平衡", name_en="System Power Balance", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="System Power Balance", formula_latex=["System Power Balance"])
_reg(component_id="CON_LOAD_SHEDDING_LIMIT", name_cn="切负荷限制", name_en="Load Shedding Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Load Shedding Limit", formula_latex=["Load Shedding Limit"])
_reg(component_id="CON_RESERVE_MARGIN", name_cn="备用裕度", name_en="Reserve Margin", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Reserve Margin", formula_latex=["Reserve Margin"])
_reg(component_id="CON_CARBON_INTENSITY_LIMIT", name_cn="碳强度限制", name_en="Carbon Intensity Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="Carbon Intensity Limit", formula_latex=["Carbon Intensity Limit"])
_reg(component_id="CON_TN_POWER_BALANCE", name_cn="主网功率平衡", name_en="TN Power Balance", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="TN Power Balance", formula_latex=["TN Power Balance"])
_reg(component_id="CON_TN_BRANCH_FLOW_LIMIT", name_cn="主网线路潮流限制", name_en="TN Branch Flow Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="TN Branch Flow Limit", formula_latex=["TN Branch Flow Limit"])
_reg(component_id="CON_TN_GENERATOR_LIMIT", name_cn="主网发电机出力限制", name_en="TN Generator Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="TN Generator Limit", formula_latex=["TN Generator Limit"])
_reg(component_id="CON_TN_RAMP_LIMIT", name_cn="主网爬坡限制", name_en="TN Ramp Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="TN Ramp Limit", formula_latex=["TN Ramp Limit"])
_reg(component_id="CON_TN_VOLTAGE_LIMIT_AC", name_cn="主网AC电压限制", name_en="TN AC Voltage Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_en="TN AC Voltage Limit (not applicable in DC-OPF)", formula_latex=["TN AC Voltage Limit"], implementation_note="Not applicable in DC-OPF (no TN voltage variables). Relevant to canonical AC TN models, including TN_ACOPF_FULL")
_reg(component_id="CON_DN_P_BALANCE", name_cn="配网有功平衡", name_en="DN P Balance", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="DN P Balance", formula_latex=["DN P Balance"])
_reg(component_id="CON_DN_Q_BALANCE", name_cn="配网无功平衡", name_en="DN Q Balance", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="DN Q Balance", formula_latex=["DN Q Balance"])
_reg(component_id="CON_DN_VOLTAGE_LIMIT", name_cn="配网电压限制", name_en="DN Voltage Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="DN Voltage Limit", formula_latex=["DN Voltage Limit"])
_reg(component_id="CON_DN_BRANCH_FLOW_LIMIT", name_cn="配网线路潮流限制", name_en="DN Branch Flow Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="DN Branch Flow Limit", formula_latex=["DN Branch Flow Limit"])
_reg(component_id="CON_DN_GT_P_LIMIT", name_cn="配网GT有功限制", name_en="DN GT P Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="DN GT P Limit", formula_latex=["DN GT P Limit"])
_reg(component_id="CON_DN_GT_Q_SUPPORT", name_cn="配网GT无功支撑", name_en="DN GT Q Support", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_en="DN GT Q Support (Q_gt = P_gt * tan(acos(pf)) already in Q balance)", formula_latex=["DN GT Q Support"], implementation_note="Already modeled in Q balance via _dn_q_gen — not a separate selectable component")
_reg(component_id="CON_DN_SVC_Q_SUPPORT", name_cn="配网SVC无功支撑", name_en="DN SVC Q Support", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=True, implemented=True, mandatory=False, description_en="DN SVC Q Support", formula_latex=["DN SVC Q Support"])
_reg(component_id="CON_DN_PV_WT_CURTAILMENT", name_cn="配网PV/WT弃电限制", name_en="DN PV/WT Curtailment", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="DN PV/WT Curtailment", formula_latex=["DN PV/WT Curtailment"])
_reg(component_id="CON_DN_BESS_SOC", name_cn="配网储能SOC约束", name_en="DN BESS SOC", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="DN BESS SOC", formula_latex=["DN BESS SOC"])
_reg(component_id="CON_DN_BESS_CH_DIS_MUTEX", name_cn="配网储能充放电互斥", name_en="DN BESS Ch/Dis Mutex", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="DN BESS Ch/Dis Mutex", formula_latex=["DN BESS Ch/Dis Mutex"])
_reg(component_id="CON_DN_FLEX_LOAD_LIMIT", name_cn="配网柔性负荷限制", name_en="DN Flex Load Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=False, description_en="DN Flex Load Limit (already built by DN resource builders)", formula_latex=["DN Flex Load Limit"], implementation_note="Flex load limits are already built by _add_dn_flex resource builder — not a separate selectable component")
_reg(component_id="CON_MG_ACTIVE_BALANCE", name_cn="微网有功平衡", name_en="MG Active Balance", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="MG Active Balance", formula_latex=["MG Active Balance"])
_reg(component_id="CON_MG_GT_LIMIT", name_cn="微网GT限制", name_en="MG GT Limit", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="MG GT Limit", formula_latex=["MG GT Limit"])
_reg(component_id="CON_MG_BESS_SOC", name_cn="微网储能SOC", name_en="MG BESS SOC", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="MG BESS SOC", formula_latex=["MG BESS SOC"])
_reg(component_id="CON_MG_BESS_CH_DIS_MUTEX", name_cn="微网储能充放电互斥", name_en="MG BESS Ch/Dis Mutex", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="MG BESS Ch/Dis Mutex", formula_latex=["MG BESS Ch/Dis Mutex"])
_reg(component_id="CON_BOUNDARY_POWER_CONSISTENCY", name_cn="边界功率一致性", name_en="Boundary Power Consistency", category="constraint", layer="Constraint", formulation_type="MILP", solver_class="MILP", selectable_by_llm=False, implemented=True, mandatory=True, description_en="Boundary Power Consistency", formula_latex=["Boundary Power Consistency"])

# ── NEW: TN_LINEARIZED_ACOPF (separate from TN_LINEARIZED_AC_EXTENSION) ──
_reg(component_id="TN_LINEARIZED_ACOPF", name_cn="主网线性化AC-OPF", name_en="TN Linearized AC OPF", category="tn_base", layer="TN", formulation_type="LP/QP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="Linearized AC OPF: V/theta变量 + P/Q潮流（box近似），V∈[0.95,1.05]。LP求解。在DCOPF基础上增加电压/无功变量，适用于有电压问题的场景。", description_en="Linearized AC OPF: V/theta + P/Q flow (box approx), V∈[0.95,1.05]. LP. Adds voltage/reactive variables vs DCOPF.")

# ── NEW: TN_ACOPF_FULL (LLM-facing full AC OPF, wraps rectangular backend) ──
_reg(component_id="TN_ACOPF_FULL", name_cn="主网全AC-OPF", name_en="TN Full AC OPF", category="tn_base", layer="TN", formulation_type="nonconvex_QCQP", solver_class="nonconvex_QCQP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="全AC-OPF: 直角坐标(e+jf) + V2约束 + Ybus P/Q平衡。需要Gurobi NonConvex=2。最高精度。", description_en="Full AC OPF: rectangular coords + V2 bounds + Ybus P/Q. Gurobi NonConvex=2.")

# ── NEW: Additional coordination methods ──

# ═══════════════════════════════════════════════════════════════
# NEW: Unified component IDs (v5) — mapping to existing builders
# ═══════════════════════════════════════════════════════════════

# ── TN: SOCP convex relaxation ──
_reg(component_id="TN_ACOPF_SOCP", name_cn="主网SOCP-ACOPF", name_en="TN ACOPF SOCP Relaxation", category="tn_base", layer="TN", formulation_type="SOCP/QCP", solver_class="QCP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="SOCP凸松弛ACOPF: W/T变量 + SOC锥 W²+T²≤U_i·U_j + V/Q/网损。精度介于DCOPF和ACOPF之间，Gurobi可解。", description_en="SOCP relaxation of AC OPF: W/T vars + cone W²+T²≤U·U. Convex, Gurobi-solvable.")

# ── DN: new unified DistFlow variants ──
_reg(component_id="DN_LINDISTFLOW", name_cn="线性DistFlow", name_en="Linear DistFlow", category="dn_base", layer="DN", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="标准LinDistFlow: 线性电压降U_j=U_i-2(rP+xQ)/S_base。最快LP。适用于无电压问题的常规场景。", description_en="Standard LinDistFlow: linear voltage drop, fastest LP. Sufficient when voltage is not a concern.")
_reg(component_id="DN_LINDISTFLOW_LOSS_FIXED", name_cn="固定损耗DistFlow", name_en="LinDistFlow Fixed Loss", category="dn_base", layer="DN", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="LinDistFlow + 固定损耗因子: P_loss=κ·|P_flow|, κ=1.5%。LP+损耗近似。", description_en="LinDistFlow with fixed loss factor: LP + loss approximation.")
_reg(component_id="DN_DISTFLOW_SOCP", name_cn="SOCP DistFlow", name_en="SOCP DistFlow", category="dn_base", layer="DN", formulation_type="SOCP/MISOCP", solver_class="SOCP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="SOCP锥松弛: P²+Q²≤U·L。凸QCP求解。注意：锥松弛在过电压场景可能高估电压，需要更精确模型时考虑SOCP_LIN或FULL。", description_en="SOCP cone relaxation: P²+Q²≤U·L. Convex QCP. Note: relaxation can over-estimate voltages; consider SOCP_LIN or FULL when precision matters.")
_reg(component_id="DN_DISTFLOW_SOCP_LIN", name_cn="线性化锥DistFlow", name_en="SOCP DistFlow PWL", category="dn_base", layer="DN", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="PWL锥近似: 8个切平面线性化P²+Q²≤U·L。LP求解。需要比LinDistFlow更精确的电压建模时使用。", description_en="PWL cone approximation: 8 tangent planes linearizing P²+Q²≤U·L. LP. Use when LinDistFlow voltage accuracy is insufficient.")
_reg(component_id="DN_DISTFLOW_FULL", name_cn="完整DistFlow", name_en="Full DistFlow", category="dn_base", layer="DN", formulation_type="nonconvex_QCQP", solver_class="nonconvex_QCQP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="精确DistFlow: 等式锥P²+Q²=U·L+完整V drop含(r²+x²)L。最高精度, 需NonConvex=2。", description_en="Exact DistFlow: equality cone + full V drop. NonConvex=2 required.")

# ── MG: new extension components ──
_reg(component_id="MG_GT_UC", name_cn="微网GT启停连续松弛", name_en="MG GT Continuous Commitment Relaxation", category="mg_extension", layer="MG", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="MG GT启停连续松弛: u/start/stop∈[0,1]，保留出力关联、转换及两小时最小开机的线性不等式；不提供整数启停保证。", description_en="Continuous [0,1] commitment/start/stop relaxation retaining dispatch coupling, transition and two-hour minimum-up inequalities; not exact binary unit commitment.", variables=["u[t] in [0,1]", "start[t] in [0,1]", "stop[t] in [0,1]"], formula_latex=["0<=u_t,start_t,stop_t<=1", "Pmin*u_t<=P_t<=Pmax*u_t", "start_t-stop_t=u_t-u_(t-1)", "u_t+u_(t+1)>=2*start_t", "start_t+stop_t<=1"], implementation_note="Integrality is relaxed. Fractional commitment and startup/shutdown are allowed; no exact on/off schedule, discrete minimum-up guarantee or integer recovery. Existing initial/terminal and temporal inequalities are retained.")
_reg(component_id="MG_BESS_PRECONDITION", name_cn="微网BESS预充电", name_en="MG BESS Precondition", category="mg_extension", layer="MG", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="BESS预充电: 峰荷时段前SOC≥80%·SOCmax。为削峰做准备。", description_en="BESS pre-charge: SOC≥80% before peak hours.")
_reg(component_id="MG_FLEX_PEAK_SHAVING", name_cn="微网柔性削峰", name_en="MG Flex Peak Shaving", category="mg_extension", layer="MG", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="削峰约束: DN净进口≤90%·峰荷。强制柔性负荷在峰时削减。", description_en="Peak shaving: net import ≤ 90% of peak load.")

# ── Objective: new terms ──
_reg(component_id="OBJ_LOSS_PENALTY", name_cn="网损惩罚", name_en="Loss Penalty", category="objective", layer="Objective", formulation_type="LP", solver_class="LP", selectable_by_llm=True, implemented=True, mandatory=False, description_cn="惩罚网损: w_loss·Σr·L[t]。仅对含L变量的DN模型生效。", description_en="Penalize network losses in objective.")

# ── Constraint: new constraints ──

# ── Coordination: new SLP/SQP methods ──

# Task B.6 formal classification: one canonical identity and only independently
# executable adaptive choices.  Integrated physics stays mandatory core.
_FORMAL_EXCLUSIVE = {
    **{component_id: "tn_formulation" for component_id in TN_BASE_MODELS},
    **{component_id: "dn_formulation" for component_id in DN_BASE_MODELS
       if component_id != "DN_LINDISTFLOW_LOSS_ITER"},
    **{component_id: "coordination_formulation"
       for component_id in _CANONICAL_COORDINATION_IDS},
}
_MANDATORY_CORE = {
    "MG_ACTIVE_BALANCE", "MG_BESS_SOC_MODEL",
    "MG_TERMINAL_SOC_CONSTRAINT", "MG_RENEWABLE_CURTAILMENT_MODEL",
    "MG_GT_DISPATCH_MODEL", "MG_CARBON_MODEL",
    "DN_REACTIVE_SUPPORT_EXTENSION", "DN_RENEWABLE_CURTAILMENT_MODEL",
    "DN_BESS_ACTIVE_MODEL", "DN_FLEX_LOAD_MODEL",
    "COORD_BOUNDARY_POWER_EXCHANGE",
    "OBJ_FUEL_COST", "OBJ_CARBON_COST", "OBJ_BESS_THROUGHPUT",
    "OBJ_RENEWABLE_CURTAILMENT", "OBJ_LOAD_SHEDDING",
    "OBJ_MG_COMFORT_LOSS",
    "CON_SYSTEM_POWER_BALANCE", "CON_TN_POWER_BALANCE",
    "CON_TN_BRANCH_FLOW_LIMIT", "CON_TN_GENERATOR_LIMIT",
    "CON_TN_VOLTAGE_LIMIT_AC", "CON_DN_P_BALANCE",
    "CON_DN_Q_BALANCE", "CON_DN_VOLTAGE_LIMIT",
    "CON_DN_BRANCH_FLOW_LIMIT", "CON_DN_GT_P_LIMIT",
    "CON_DN_GT_Q_SUPPORT", "CON_DN_SVC_Q_SUPPORT",
    "CON_DN_PV_WT_CURTAILMENT", "CON_DN_BESS_SOC",
    "CON_DN_BESS_CH_DIS_MUTEX", "CON_DN_FLEX_LOAD_LIMIT",
    "CON_MG_ACTIVE_BALANCE", "CON_MG_GT_LIMIT",
    "CON_MG_BESS_SOC", "CON_MG_BESS_CH_DIS_MUTEX",
    "CON_LOAD_SHEDDING_LIMIT", "CON_BOUNDARY_POWER_CONSISTENCY",
}
_MANDATORY_BUILDER_BINDINGS = {
    "MG_TERMINAL_SOC_CONSTRAINT", "MG_CARBON_MODEL",
    "DN_REACTIVE_SUPPORT_EXTENSION", "DN_RENEWABLE_CURTAILMENT_MODEL",
    "DN_BESS_ACTIVE_MODEL", "DN_FLEX_LOAD_MODEL",
    "COORD_BOUNDARY_POWER_EXCHANGE",
}
_ADAPTIVE_MULTI = {
    "MG_GT_RAMP_MODEL", "MG_GT_UC", "MG_BESS_PRECONDITION",
    "MG_FLEX_PEAK_SHAVING",
    "OBJ_VOLTAGE_DEVIATION", "OBJ_INTERFACE_USAGE",
    "OBJ_GT_RAMPING", "OBJ_LOSS_PENALTY",
    "CON_TN_RAMP_LIMIT", "CON_RESERVE_MARGIN",
    "CON_CARBON_INTENSITY_LIMIT",
}
_SELECTABLE_EXPECTED_EFFECTS = {
    "TN_DCOPF": {
        "variables": ["theta", "P_TU1", "F_tn"],
        "constraints": ["tn_flow", "tn_nbal"],
    },
    "TN_LINEARIZED_ACOPF": {
        "variables": ["V_lin", "Q_flow_lin"],
        "constraints": ["tn_lin_pbal", "tn_lin_qbal"],
    },
    "TN_ACOPF_SOCP": {
        "variables": ["U_tn", "W_tn", "T_tn"],
        "constraints": ["tn_socp_pbal", "tn_socp_cone"],
    },
    "TN_ACOPF_FULL": {
        "variables": ["e_tn", "f_tn", "Q_TU1_ac", "P_flow_ac"],
        "constraints": ["tn_ac_pbal", "tn_ac_qbal", "tn_ac_thermal"],
    },
    "DN_LINDISTFLOW": {
        "variables": ["P_flow_DN1", "Q_flow_DN1", "U_DN1"],
        "constraints": ["DN1_pbal", "DN1_qbal", "DN1_vd"],
    },
    "DN_LINDISTFLOW_LOSS_FIXED": {
        "variables": ["P_abs_DN1", "P_flow_DN1", "U_DN1"],
        "constraints": ["DN1_pabs_ub", "DN1_pbal", "DN1_vd"],
    },
    "DN_DISTFLOW_SOCP_LIN": {
        "variables": ["L_DN1", "U_DN1"],
        "constraints": ["DN1_cone_pwl_0", "DN1_pbal"],
    },
    "DN_DISTFLOW_SOCP": {
        "variables": ["L_DN1", "U_DN1"],
        "constraints": ["DN1_cone", "DN1_pbal_socp"],
    },
    "DN_DISTFLOW_FULL": {
        "variables": ["L_DN1", "U_DN1"],
        "constraints": ["DN1_cone_eq", "DN1_pbal_nl"],
    },
    "MG_GT_RAMP_MODEL": {
        "constraints": ["DN1_MG1_gt_ramp_up", "DN1_MG1_gt_ramp_down"],
    },
    "MG_GT_UC": {
        "variables": ["u_DN1_MG1", "start_DN1_MG1"],
        "constraints": ["DN1_MG1_uc_lb", "DN1_MG1_uc_ss"],
    },
    "MG_BESS_PRECONDITION": {
        "constraints": ["DN1_MG1_precharge"],
    },
    "MG_FLEX_PEAK_SHAVING": {
        "constraints": ["DN1_peak_shave", "DN2_peak_shave"],
    },
    "COORD_CENTRALIZED_TDM": {"solve_route": ["centralized"]},
    "COORD_SEQUENTIAL_TD_MG": {"solve_route": ["sequential"]},
    "COORD_HIERARCHICAL_TD_MG": {"solve_route": ["hierarchical"]},
    "COORD_ADMM_TDM": {"solve_route": ["admm"]},
    "COORD_PRICE_BASED": {"solve_route": ["price_based"]},
    "OBJ_VOLTAGE_DEVIATION": {
        "objective_terms": ["voltage_deviation"],
    },
    "OBJ_INTERFACE_USAGE": {"objective_terms": ["interface_usage"]},
    "OBJ_GT_RAMPING": {"objective_terms": ["gt_ramping"]},
    "OBJ_LOSS_PENALTY": {"objective_terms": ["network_loss"]},
    "CON_TN_RAMP_LIMIT": {
        "constraints": ["tn_ramp_up_TU1", "tn_ramp_down_TU1"],
    },
    "CON_RESERVE_MARGIN": {"constraints": ["reserve_adequacy"]},
    "CON_CARBON_INTENSITY_LIMIT": {
        "constraints": ["con_carbon_intensity"],
    },
}
_FROZEN_OBJECTIVE_METADATA = {
    "OBJ_VOLTAGE_DEVIATION": {
        "weight": 1.0, "normalization": "squared_per_unit_voltage",
    },
    "OBJ_INTERFACE_USAGE": {
        "weight": 1.0, "normalization": "squared_MW",
    },
    "OBJ_GT_RAMPING": {
        "weight": 10.0, "normalization": "squared_MW_change",
    },
    "OBJ_LOSS_PENALTY": {
        "weight": 5.0, "normalization": "DN_current_proxy",
    },
}
_FROZEN_ADAPTIVE_METADATA = {
    **_FROZEN_OBJECTIVE_METADATA,
    "MG_GT_RAMP_MODEL": {"ramp_limit_mw_per_hour": 0.5},
    "MG_GT_UC": {"minimum_up_hours": 2, "integrality_relaxed": True},
    "MG_BESS_PRECONDITION": {
        "soc_target_fraction": 0.8, "target_hour": 16,
    },
    "MG_FLEX_PEAK_SHAVING": {"peak_ratio": 0.9},
    "CON_TN_RAMP_LIMIT": {
        "TU1_mw_per_hour": 80.0,
        "TU2_mw_per_hour": 100.0,
        "TU3_mw_per_hour": 70.0,
        "explicit_user_task_override": "one positive MW/h limit for monitored TN units",
    },
    "CON_RESERVE_MARGIN": {"reserve_margin_ratio": 0.05},
    "CON_CARBON_INTENSITY_LIMIT": {
        "carbon_intensity_limit_kg_per_mwh": 500.0,
        "explicit_user_task_override": "positive kgCO2/MWh limit",
        "accounting_boundary": (
            "operational emissions per MWh of actual GEN/GT/PV/WT generation; "
            "no interface, storage discharge, or curtailment double count"
        ),
    },
}
for _component in REGISTRY._components.values():
    if _component.layer not in {
        "TN", "DN", "MG", "Coordination", "Objective", "Constraint",
    }:
        continue
    _component.mandatory = False
    if _component.component_id in _FORMAL_EXCLUSIVE:
        _component.selection_mode = "adaptive_exclusive"
        _component.selection_group = _FORMAL_EXCLUSIVE[_component.component_id]
        _component.execution_binding = (
            "solve_route" if _component.layer == "Coordination" else "builder"
        )
    elif _component.component_id in _MANDATORY_CORE:
        _component.selection_mode = "mandatory_core"
        _component.selection_group = ""
        _component.mandatory = True
        _component.execution_binding = (
            "builder"
            if _component.component_id in _MANDATORY_BUILDER_BINDINGS
            else "integrated"
        )
    elif _component.component_id in _ADAPTIVE_MULTI:
        _component.selection_mode = "adaptive_multi_select"
        _component.selection_group = f"{_component.layer.casefold()}_extensions"
        _component.execution_binding = "builder"
    else:
        _component.selection_mode = "non_formal"
        _component.selection_group = ""
    _component.selectable_by_llm = _component.selection_mode in {
        "adaptive_exclusive", "adaptive_multi_select",
    }
    if _component.selection_mode != "non_formal":
        # Historical MILP labels on integrated continuous components do not
        # imply binary variables; the host determines their algebraic class.
        if _component.formulation_type == "MILP":
            _component.formulation_type = "continuous (host-model dependent)"
        elif _component.formulation_type == "LP/MILP":
            _component.formulation_type = "LP"
        elif _component.formulation_type == "SOCP/MISOCP":
            _component.formulation_type = "SOCP"
        if _component.solver_class == "MILP":
            _component.solver_class = "continuous"
    if _component.component_id in _FROZEN_ADAPTIVE_METADATA:
        _component.deterministic_metadata = dict(
            _FROZEN_ADAPTIVE_METADATA[_component.component_id]
        )
    if _component.component_id in _SELECTABLE_EXPECTED_EFFECTS:
        _component.expected_effects = {
            key: list(value)
            for key, value in _SELECTABLE_EXPECTED_EFFECTS[
                _component.component_id
            ].items()
        }

_mg_q_support = REGISTRY.get("MG_REN_Q_SUPPORT")
_uc_alias = REGISTRY.get("MG_GT_UC_MODEL")
if _uc_alias is not None:
    _uc_canonical = REGISTRY.get("MG_GT_UC")
    for _field in ("formulation_type", "solver_class", "description_cn",
                   "description_en", "implementation_note", "variables", "formula_latex"):
        setattr(_uc_alias, _field, getattr(_uc_canonical, _field))
if _mg_q_support is not None:
    _mg_q_support.implementation_note = (
        "Builder creates bounded MG inverter-Q variables but the current MG/DN "
        "balance does not consume them; classified non_formal until coupled."
    )


# Publication boundary: only canonical buildable model components are registered.
# Callbacks are not separately bound: integrated components share one assembly.
for _component in REGISTRY._components.values():
    if _component.component_id in TN_BASE_MODELS:
        _component.builder_import_path = "tdm_workflow_agent.model_component.case_tn_models.build_tn_network"
    elif _component.component_id in DN_BASE_MODELS:
        _component.builder_import_path = "tdm_workflow_agent.model_component.case_dn_models.build_dn_network"
    else:
        _component.builder_import_path = "tdm_workflow_agent.model_component.case_builders.build_case_model"
