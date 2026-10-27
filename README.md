# Component Library

基于 Pyomo 的输电网（TN）、配电网（DN）和聚合微电网（MG）优化建模组件库。
组件可通过 Python 函数组合，组件描述同时提供为 JSON，便于程序查询和 LLM 调用。

## 组件

| 类别 | 内容 |
|---|---|
| TN 模型 | DC OPF、线性化 AC OPF、SOCP AC OPF、完整 AC OPF |
| DN 模型 | LinDistFlow、固定损耗 LinDistFlow、SOCP DistFlow、分段线性 SOCP DistFlow、完整 DistFlow |
| MG 扩展 | GT 爬坡、连续启停松弛、储能预充、柔性负荷削峰 |
| 可选目标 | 电压偏差、接口功率使用、TN 机组爬坡、内部电流平方惩罚 |
| 可选约束 | TN 爬坡、备用裕度、碳强度限制 |
| 基础物理与资源 | 功率平衡、储能能量状态、可再生出力与弃电、设备容量、接口耦合、燃料与碳成本 |

注册表包含 20 个可选条目和 39 个随模型组装的核心条目。完整列表见 [组件说明](docs/components.md)。

## 安装

Python 3.10+，依赖 Pyomo 和 NumPy。

```shell
python -m pip install "pyomo>=6.8,<7" "numpy>=1.24"
```

将本目录的 `src` 和 `examples` 加入 Python 搜索路径。在组件库根目录执行：

Windows PowerShell：

```powershell
$env:PYTHONPATH = "$PWD/src;$PWD/examples"
```

Linux / macOS：

```shell
export PYTHONPATH="$PWD/src:$PWD/examples"
```

## 快速开始

```shell
python examples/build_tn_network.py
python examples/build_acopf.py
python examples/compose_components.py
```

三个示例分别演示单独 TN ACOPF、TN–DN–MG 联合建模及可选组件组合。
示例数据由 `examples/case_fixtures.py` 生成。

```python
from tdm_workflow_agent.model_component.case_builders import build_case_model

model, audit = build_case_model(
    ["TN_ACOPF_FULL", "DN_DISTFLOW_FULL", "MG_GT_RAMP_MODEL"],
    case, scenario, None,
)
```

函数向 Pyomo 模型添加变量、约束和目标。构建后可交给合适的求解器；完整示例见 `examples/solve_acopf.py`：

```shell
python examples/solve_acopf.py --solver ipopt
```

该示例固定 OLTC 中性档位，使用连续 NLP 求解器。

## 文件与接口

| 文件 | 作用 |
|---|---|
| case_tn_models.py | `build_tn_network()`：按组件 ID 构建 TN 方程 |
| case_dn_models.py | `build_dn_network()`：按组件 ID 构建 DN 方程 |
| case_interfaces.py | 接口功率、串联损耗、电压耦合与 OLTC 方程 |
| case_builders.py | 资源、网络、接口、约束和目标组装 |
| base.py、registry.py、__init__.py | 组件定义、注册和查询 |
| compatibility.py | 组合依赖与互斥检查 |
| builders.py、compiler.py | 统一建模入口 |
| network_math.py | 支路导纳与网络数学工具 |
| model_knowledge.json | 功能、状态变量、依赖、假设与调用入口 |

以上文件位于 `src/tdm_workflow_agent/model_component/`。
模型使用显式网络数据：TN 可为网状，DN 为平衡径向网络，MG 为聚合模型。
储能模式、OLTC 档位及 GT 启停采用连续变量；具体适用条件见 [输入与变量说明](docs/data_contract.md)。

## 文档

- [组件说明](docs/components.md)
- [输入数据与变量](docs/data_contract.md)
- [组件组合与调用](docs/composition.md)
- [测试记录](docs/VERIFICATION.md)

更新组件描述和运行测试：

```shell
python scripts/export_model_knowledge.py
python -m pip install "pytest>=8"
python -m pytest -q
```
