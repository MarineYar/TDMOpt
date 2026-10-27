# 测试记录

环境：Python 3.11、Pyomo 6.10.0。日期：2026-10-27。

| 检查 | 结果 |
|---|---|
| pytest | 83 项通过 |
| 基础模型组合 | 4 种 TN × 5 种 DN，含有损接口 |
| 数学不变量 | 储能能量与 dt 系数、目标二次项、FLEX 负荷分配、接口相量方程 |
| 示例 | 单 TN、联合模型和组件组合均通过 |
| 源码运行 | 独立目录的源码导入、示例和 JSON 读取通过 |
| 数值求解 | 当前环境未安装 IPOPT |

按 README 设置 Python 搜索路径后运行：

```shell
python -m pip install "pytest>=8"
python -m pytest -q
```
