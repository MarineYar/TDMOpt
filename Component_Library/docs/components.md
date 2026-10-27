# 组件说明 / Component Cards

共 59 个注册条目：20 个可选项和 39 个随模型组装的核心条目。

TN 为平衡网络，DN 为平衡径向网络，MG 为聚合模型。输入、变量单位和通用假设见 [data_contract.md](data_contract.md)，调用方法见 [composition.md](composition.md)。

## CON_BOUNDARY_POWER_CONSISTENCY

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 边界功率一致性
- 功能: Boundary Power Consistency
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_CARBON_INTENSITY_LIMIT

- 层: Constraint；组合角色: `adaptive_multi_select`
- 名称: 碳强度限制
- 功能: Carbon Intensity Limit
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_BESS_CH_DIS_MUTEX

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网储能充放电互斥
- 功能: Continuous [0,1] storage mode envelope; simultaneous partial charge/discharge is not strictly excluded.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_BESS_SOC

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网储能SOC约束
- 功能: DN BESS SOC
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_BRANCH_FLOW_LIMIT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网线路潮流限制
- 功能: DN Branch Flow Limit
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_FLEX_LOAD_LIMIT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网柔性负荷限制
- 功能: DN Flex Load Limit (already built by DN resource builders)
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_GT_P_LIMIT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网GT有功限制
- 功能: DN GT P Limit
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_GT_Q_SUPPORT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网GT无功支撑
- 功能: DN GT Q Support (Q_gt = P_gt * tan(acos(pf)) already in Q balance)
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_PV_WT_CURTAILMENT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网PV/WT弃电限制
- 功能: DN PV/WT Curtailment
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_P_BALANCE

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网有功平衡
- 功能: DN P Balance
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_Q_BALANCE

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网无功平衡
- 功能: DN Q Balance
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_SVC_Q_SUPPORT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网SVC无功支撑
- 功能: DN SVC Q Support
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_DN_VOLTAGE_LIMIT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 配网电压限制
- 功能: DN Voltage Limit
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_LOAD_SHEDDING_LIMIT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 切负荷限制
- 功能: No controllable load-shedding variable: load shedding is fixed at zero by construction.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_MG_ACTIVE_BALANCE

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 微网有功平衡
- 功能: MG Active Balance
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_MG_BESS_CH_DIS_MUTEX

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 微网储能充放电互斥
- 功能: Continuous [0,1] storage mode envelope; simultaneous partial charge/discharge is not strictly excluded.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_MG_BESS_SOC

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 微网储能SOC
- 功能: MG BESS SOC
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_MG_GT_LIMIT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 微网GT限制
- 功能: MG GT Limit
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_RESERVE_MARGIN

- 层: Constraint；组合角色: `adaptive_multi_select`
- 名称: 备用裕度
- 功能: Reserve Margin
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_SYSTEM_POWER_BALANCE

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 系统功率平衡
- 功能: System Power Balance
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_TN_BRANCH_FLOW_LIMIT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 主网线路潮流限制
- 功能: TN Branch Flow Limit
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_TN_GENERATOR_LIMIT

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 主网发电机出力限制
- 功能: TN Generator Limit
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_TN_POWER_BALANCE

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 主网功率平衡
- 功能: TN Power Balance
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_TN_RAMP_LIMIT

- 层: Constraint；组合角色: `adaptive_multi_select`
- 名称: 主网爬坡限制
- 功能: TN Ramp Limit
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## CON_TN_VOLTAGE_LIMIT_AC

- 层: Constraint；组合角色: `mandatory_core`
- 名称: 主网AC电压限制
- 功能: TN AC Voltage Limit (not applicable in DC-OPF)
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; constraints can be integrated or variable bounds`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## COORD_BOUNDARY_POWER_EXCHANGE

- 层: Coordination；组合角色: `mandatory_core`
- 名称: 边界功率一致性
- 功能: Boundary Power Consistency
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `port_p/port_q[port,t]`, `tap[port,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## DN_BESS_ACTIVE_MODEL

- 层: DN；组合角色: `mandatory_core`
- 名称: 配网储能模型
- 功能: DN BESS Active Model
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## DN_DISTFLOW_FULL

- 层: DN；组合角色: `adaptive_exclusive`
- 名称: 完整DistFlow
- 功能: Exact DistFlow equality cone, complete voltage drop, and P/Q losses on a balanced series radial network.
- 入口: `tdm_workflow_agent.model_component.case_dn_models.build_dn_network`
- 签名: `build_dn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

## DN_DISTFLOW_SOCP

- 层: DN；组合角色: `adaptive_exclusive`
- 名称: SOCP DistFlow
- 功能: Rotated cone inequality in MW/MVAr with base^2 scaling; complete DistFlow voltage drop and P/Q losses.
- 入口: `tdm_workflow_agent.model_component.case_dn_models.build_dn_network`
- 签名: `build_dn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

## DN_DISTFLOW_SOCP_LIN

- 层: DN；组合角色: `adaptive_exclusive`
- 名称: 线性化锥DistFlow
- 功能: Legacy eight-plane necessary outer approximation in consistent per-unit P/Q; not an exact or tight rotated cone. Lossless voltage drop and base*r/x*ell losses.
- 入口: `tdm_workflow_agent.model_component.case_dn_models.build_dn_network`
- 签名: `build_dn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

## DN_FLEX_LOAD_MODEL

- 层: DN；组合角色: `mandatory_core`
- 名称: 配网柔性负荷
- 功能: DN Flex Load Model
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## DN_LINDISTFLOW

- 层: DN；组合角色: `adaptive_exclusive`
- 名称: 线性DistFlow
- 功能: Lossless linear P/Q balances and voltage drop; physical current checked in independent replay.
- 入口: `tdm_workflow_agent.model_component.case_dn_models.build_dn_network`
- 签名: `build_dn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

## DN_LINDISTFLOW_LOSS_FIXED

- 层: DN；组合角色: `adaptive_exclusive`
- 名称: 固定损耗DistFlow
- 功能: Legacy P-loss surrogate .015*r*Pabs; Pabs is an epigraph relaxation of abs(P). Legacy Q balance and voltage drop remain lossless.
- 入口: `tdm_workflow_agent.model_component.case_dn_models.build_dn_network`
- 签名: `build_dn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

## DN_REACTIVE_SUPPORT_EXTENSION

- 层: DN；组合角色: `mandatory_core`
- 名称: 配网无功支撑
- 功能: DN Reactive Support
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## DN_RENEWABLE_CURTAILMENT_MODEL

- 层: DN；组合角色: `mandatory_core`
- 名称: 配网可再生弃电
- 功能: DN Renewable Curtailment
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `network[dn].pf/qf/pt/qt`, `network[dn].u`, `network[dn].ell (current-based variants)`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_ACTIVE_BALANCE

- 层: MG；组合角色: `mandatory_core`
- 名称: 微网有功平衡
- 功能: MG Active Balance
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_BESS_PRECONDITION

- 层: MG；组合角色: `adaptive_multi_select`
- 名称: 微网BESS预充电
- 功能: Require MG energy at the configured target boundary (default 16 h) >= .8 * soc_max * e_nameplate. A short horizon or absent MG BESS gives an empty/not_applicable constraint list.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_BESS_SOC_MODEL

- 层: MG；组合角色: `mandatory_core`
- 名称: 微网储能SOC
- 功能: Energy in MWh on N+1 boundaries with per-device efficiencies, dt and initial/terminal energy. Storage mode is continuous [0,1], not exact binary charge/discharge exclusion.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_CARBON_MODEL

- 层: MG；组合角色: `mandatory_core`
- 名称: 微网碳排放
- 功能: MG Carbon
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_FLEX_PEAK_SHAVING

- 层: MG；组合角色: `adaptive_multi_select`
- 名称: 微网柔性削峰
- 功能: Cap each child-DN net interface import at .9 of its non-MG peak load. May be infeasible; no automatic load shedding or fallback.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_GT_DISPATCH_MODEL

- 层: MG；组合角色: `mandatory_core`
- 名称: 微网GT调度
- 功能: MG GT Dispatch
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_GT_RAMP_MODEL

- 层: MG；组合角色: `adaptive_multi_select`
- 名称: 微网GT爬坡
- 功能: MG GT Ramp
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_GT_UC

- 层: MG；组合角色: `adaptive_multi_select`
- 名称: 微网GT启停连续松弛
- 功能: MG GT commitment, startup and shutdown are continuous [0,1]; two-hour minimum-up inequalities are retained without integer guarantees.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_RENEWABLE_CURTAILMENT_MODEL

- 层: MG；组合角色: `mandatory_core`
- 名称: 微网可再生弃电
- 功能: MG Renewable Curtailment
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## MG_TERMINAL_SOC_CONSTRAINT

- 层: MG；组合角色: `mandatory_core`
- 名称: 微网终端SOC
- 功能: MG Terminal SOC
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `pg[device,t]`, `charge/discharge[bess,t]`, `energy[bess,k]`, `mg_p/mg_q[mg,t]`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_BESS_THROUGHPUT

- 层: Objective；组合角色: `mandatory_core`
- 名称: 储能吞吐成本
- 功能: BESS Throughput
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_CARBON_COST

- 层: Objective；组合角色: `mandatory_core`
- 名称: 碳成本
- 功能: Carbon Cost
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_FUEL_COST

- 层: Objective；组合角色: `mandatory_core`
- 名称: 燃料成本
- 功能: Fuel Cost
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_GT_RAMPING

- 层: Objective；组合角色: `adaptive_multi_select`
- 名称: GT爬坡成本
- 功能: Squared consecutive active TN GEN output changes, not MG GT ramping; default weight 10 and dt scaling.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_INTERFACE_USAGE

- 层: Objective；组合角色: `adaptive_multi_select`
- 名称: 接口使用成本
- 功能: Squared receiving-end interface P, default weight 1 with additional fixed .1 normalization and dt scaling.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_LOAD_SHEDDING

- 层: Objective；组合角色: `mandatory_core`
- 名称: 切负荷惩罚
- 功能: No load-shedding objective variable in this canonical path; reported shedding is zero.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_LOSS_PENALTY

- 层: Objective；组合角色: `adaptive_multi_select`
- 名称: 网损惩罚
- 功能: Default weight 5 on internal network ell summed over branches/time with dt; not a literal r*ell physical MW loss and excludes interface ell.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_MG_COMFORT_LOSS

- 层: Objective；组合角色: `mandatory_core`
- 名称: 微网舒适度损失
- 功能: MG Comfort Loss
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_RENEWABLE_CURTAILMENT

- 层: Objective；组合角色: `mandatory_core`
- 名称: 弃电惩罚
- 功能: Renewable Curtailment
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## OBJ_VOLTAGE_DEVIATION

- 层: Objective；组合角色: `adaptive_multi_select`
- 名称: 电压偏差惩罚
- 功能: Squared departure of available v (TN linearized) or u=V^2 from 1. TN factor .1. The source implementation checks for u before including a network; preserve its existing behavior.
- 入口: `tdm_workflow_agent.model_component.case_builders.build_case_model`
- 签名: `build_case_model(selected_ids, case, scenario, method_config)`
- 状态变量引用: `existing network/resource/interface states; objective components share obj`
- 依赖: validated tdm_case_v1 case and matching scenario; one TN base and one supported DN base

## TN_ACOPF_FULL

- 层: TN；组合角色: `adaptive_exclusive`
- 名称: 主网全AC-OPF
- 功能: Exact rectangular AC pi model
- 入口: `tdm_workflow_agent.model_component.case_tn_models.build_tn_network`
- 签名: `build_tn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[tn].pf`, `network[tn].pt`, `network[tn].qf/qt (AC only)`, `network[tn].e/f/u or v/theta or wr/wi (formulation-dependent)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

## TN_ACOPF_SOCP

- 层: TN；组合角色: `adaptive_exclusive`
- 名称: 主网SOCP-ACOPF
- 功能: Edge W conic relaxation; no fabricated recovered bus angles or cycle exactness
- 入口: `tdm_workflow_agent.model_component.case_tn_models.build_tn_network`
- 签名: `build_tn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[tn].pf`, `network[tn].pt`, `network[tn].qf/qt (AC only)`, `network[tn].e/f/u or v/theta or wr/wi (formulation-dependent)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

## TN_DCOPF

- 层: TN；组合角色: `adaptive_exclusive`
- 名称: 主网DC-OPF
- 功能: DC x/tap/shift; fixed unit voltage for active shunt; no model Q or V
- 入口: `tdm_workflow_agent.model_component.case_tn_models.build_tn_network`
- 签名: `build_tn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[tn].pf`, `network[tn].pt`, `network[tn].qf/qt (AC only)`, `network[tn].e/f/u or v/theta or wr/wi (formulation-dependent)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

## TN_LINEARIZED_ACOPF

- 层: TN；组合角色: `adaptive_exclusive`
- 名称: 主网线性化AC-OPF
- 功能: Fixed first-order AC pi-model expansion at source vm/va; no optimal-point data
- 入口: `tdm_workflow_agent.model_component.case_tn_models.build_tn_network`
- 签名: `build_tn_network(model, block, network, component_id, injection)`
- 状态变量引用: `network[tn].pf`, `network[tn].pt`, `network[tn].qf/qt (AC only)`, `network[tn].e/f/u or v/theta or wr/wi (formulation-dependent)`
- 依赖: parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback

