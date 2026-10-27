# 输入、变量和模型假设

## 低层网络函数

`case_tn_models.build_tn_network(model, block, network, component_id, injection)` 与
`case_dn_models.build_dn_network(...)` 保留原签名，返回 `None`，把变量与约束添加到传入 block。
调用方提供 `model.T`，一个空的 Pyomo Block，以及 `injection(bus,t,'p'/'q')` 回调。
回调返回净注入表达式：发电正、负荷负，单位分别 MW/MVAr；可包含调用方创建的资源变量。
低层函数不创建燃料成本目标，不自动解决外部资源/接口约束，也不执行求解。
TN-only 完整调用见 `examples/build_tn_network.py`。

## 联合组装输入

`build_case_model(selected_ids, case, scenario, method_config)` 返回 `(model, audit)`。
`build_component_model(...)` 是相同建模入口的兼容封装；要求 `case_format='tdm_case_v1'`。
`compile_model(...)` 返回精简 `CompileResult`，ValueError 写入 errors，不执行求解或自动回退。

`case` 必含 system_id、data_version、networks、devices、loads、interfaces、profiles、time_grid、safety、source_manifest、capabilities。
组装还使用 system_hash、cost_and_carbon；microgrids 可为空列表。完整字段和数值校验在 `data/case_schema.py`。
`scenario` 使用 scenario_id、system_hash、scenario_hash、time_grid、load_p、load_q、available_p。
每个 load_p/load_q/available_p 数组必须覆盖完整时间网格，且数值有限。scenario 的 system_hash 必须匹配 case。
内容哈希可通过 data.case_schema.case_hash/hash_payload 计算。

| 记录 | 主要字段 |
|---|---|
| network | id, layer=TN/DN, base_mva, phase_model=balanced, buses, branches；TN reference_bus、DN root_bus |
| bus | id, base_kv, v_min_pu, v_max_pu, gs_mw, bs_mvar, vm_pu, va_degree |
| branch | id, from_bus, to_bus, r_pu, x_pu, b_pu, tap, shift_degree, rate_mva, status, ang_min_degree, ang_max_degree |
| device | id, kind, network_id, bus_id, owner_type, owner_id，加各类型容量/效率/成本字段 |
| load | id, network_id, bus_id, owner_type, owner_id, p_nominal_mw, q_nominal_mvar, profile_id |
| microgrid | id, parent_dn, pcc_bus, allow_export, port_s_rating_mva |
| interface | parent/child 网络与母线、额定容量、进出口许可、tau_min/tau_step/tap_positions/neutral_position，以及物理阻抗字段 |

GEN/GT/PV/WT/BESS/SVC/FLEX 的完整字段见校验器和 examples/case_fixtures.py。
FLEX 使用 baseline_load_ids 和 max_shift_fraction，输入负荷时间序列为权威基线。

## 主要状态、单位与符号

| 变量/表达式 | 含义及单位 |
|---|---|
| pg[device,t], qg[device,t] | 设备 P/Q，MW/MVAr |
| curtail[device,t] | 可再生弃电功率，MW |
| charge/discharge[bess,t] | 非负充/放电功率，MW |
| energy[bess,k] | 储能能量，MWh，N 个区间对应 N+1 个边界 |
| mode[bess,t] | 充放电模式连续变量 [0,1] |
| network[n].pf/qf, pt/qt | 从支路两个端点进入支路的 P/Q，MW/MVAr；不是同方向的首末端潮流 |
| network[n].u | 电压幅值平方，pu² |
| network[n].v | 线性化 TN 的电压幅值变量，pu |
| network[n].e/f | 完整 TN AC 的直角坐标电压，pu |
| network[n].ell | 当前网络基准下的电流幅值平方，pu² |
| port_p/port_q | 接口 DN 接收功率，MW/MVAr；正值表示 DN 从 TN 取电 |
| port_from_p/port_from_q | 有损接口 TN 送端功率；包含串联损耗 |
| mg_p/mg_q | MG 从所属 DN 的进口功率，MW/MVAr |
| tap[port,t], tau | 档位位置、无量纲电压变比；tau=tau_min+tau_step*tap |
| flex_shift, flex_abs | 负荷移位及绝对值上界，MW；按 dt 满足能量中性 |
| commit/start/stop | MG GT 启停连续松弛，均 [0,1] |

dt_hours 是时长（小时），并非假定 24 小时；成本字段使用 CNY/MWh、碳排放 kg/MWh。
原始注册的 formulation_type 是组件标签，不是整个组装问题的严格代数分类。

## 模型假设与适用条件

1. 网络为平衡稳态；DN 必须是连通径向图，内部支路不支持并联充电、变比、相移或跨电压基准。
2. MG 是聚合资源，没有内部潮流网络。TN 的 DC 模型不产生优化的 Q/V 状态；DC 接口电压取数据中明确声明的源电压。
3. SOCP 是网络松弛，不自动保证精确恢复。PWL SOCP 是外近似，不是精确或必然紧的锥表示。
4. 储能模式 mode 为连续 [0,1]，保留原始约束，不能保证严格充放电互斥。
5. OLTC 档位组装时连续；不包含离散恢复流程。extract_case_dispatch 对分数档位报错。求解示例显式固定中性档位。
6. MG_GT_UC 是连续启停松弛，不提供离散启停保证。MG_BESS_PRECONDITION 默认目标 16 小时；短时间网格可能不适用并产生空约束列表。
7. 本路径不包含可控负荷切除变量，负荷切除固定为零。相关 mandatory 标签不代表存在独立可调负荷切除组件。
8. 燃料、碳、储能、弃电及柔性负荷成本通过共享目标组装；还保留 tap_motion 和 SOCP exactness 正则项。obj 不等于单独的 base_cost。
9. OBJ_GT_RAMPING 作用于 TN GEN；OBJ_LOSS_PENALTY 为内部 ell 惩罚，不等于按 r*ell 计算的物理总网损。具体作用范围见逐组件说明。
10. build_case_model 的 scope_network_ids 只保留子模型构建能力，用于构建指定网络范围的子模型。低层原函数仍保留非正式迭代损耗分支，该分支不在公开高层入口的选择集合内。


## 可选方法配置

`method_config=None` 使用原实现默认值。也可传入具有以下属性的对象（如 SimpleNamespace）：
soft_carbon_penalty_multiplier=1、bess_throughput_cost_multiplier=1、curtailment_penalty_multiplier=1、flex_shift_cny_per_mwh=15、socp_exactness_weight=1000。
可选组件参数通过 case['component_parameters'][component_id] 传入；查阅 case_builders._optional/_objectives。
配置对象使用普通 Python 属性。
