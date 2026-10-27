# 组件组合与调用

## 单独构建网络模型

TN 和 DN 使用以下入口：

```python
build_tn_network(model, block, network, component_id, injection)
build_dn_network(model, block, network, component_id, injection)
```

调用方提供时间集合 `model.T`、目标 Pyomo Block、网络数据和净注入回调。
`injection(bus, time, 'p'/'q')` 返回净注入表达式，发电为正、负荷为负，单位 MW/MVAr。
函数按 component_id 添加相应方程。完整 TN-only 例子见 `examples/build_tn_network.py`。

## 组装网络与资源

```python
from tdm_workflow_agent.model_component.case_builders import build_case_model

selected = ['TN_ACOPF_FULL', 'DN_DISTFLOW_FULL',
            'MG_GT_RAMP_MODEL', 'OBJ_INTERFACE_USAGE']
model, audit = build_case_model(selected, case, scenario, None)
```

选择一个 TN 基础模型、一个 DN 基础模型，再添加所需的 MG、目标和约束扩展。
功率平衡、设备容量、储能动态等核心物理随数据自动组装。
`build_component_model()` 提供统一构建入口；`compile_model()` 返回包含 model、success 和 errors 的结果对象。

## 查询组件

```python
from tdm_workflow_agent.model_component.registry import REGISTRY

component = REGISTRY.get('TN_ACOPF_FULL')
print(component.to_dict())
print(REGISTRY.to_llm_catalog_list())
```

`builder_import_path` 给出实际函数路径，JSON 卡片中的 `call_signature` 给出调用签名。
TN/DN 在统一函数中按 ID 分派；资源和核心约束共享组装入口。

## 组件描述

`model_knowledge.json` 提供机器可读的功能、变量引用、依赖、适用拓扑和调用入口。
`formal_selectable=true` 表示可按任务选择；`mandatory_core` 表示随模型组装的核心内容。
调用者可通过普通程序查询这些描述，也可把描述提供给 LLM 选择组件。

## 求解和输出

构建得到 Pyomo ConcreteModel，调用方随后选择求解器。
`extract_case_dispatch(model)` 可提取设备出力、电压、储能与接口状态；OLTC 输出要求整数档位。
`examples/solve_acopf.py` 演示固定中性档位、调用 IPOPT、检查终止状态和读取目标值。

模型和输入约定见 [data_contract.md](data_contract.md)。
