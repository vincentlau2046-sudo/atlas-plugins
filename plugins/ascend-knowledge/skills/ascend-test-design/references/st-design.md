---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-st-design/SKILL.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-st-design SKILL.md 抽取 9 步 ST 设计流程、3 大类 6 种参数类型、9 约束类型、L0/L1/L2 用例分级与 6 脚本自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# ST 系统测试设计方法论（aclnn L0/L1/L2）

> Ascend C 算子 ST（系统测试）设计基于 aclnn 接口文档，完成参数定义→测试因子→约束分析→求解→用例生成（L0/L1/L2）全流程，输出结构化 CSV 支撑功能与精度验证。本文是 ST 设计方法论骨架；UT 见 `ut-develop.md`，白盒见 `whitebox-design.md`，测试策略选择见 `test-strategy.md`。

## 一、输入与输出

**输入**：
- 需求文档：`operators/{op}/docs/REQUIREMENTS.md`
- ACLNN 接口文档：`operators/{op}/docs/aclnn{OperatorName}.md`

**输出**：
```
operators/{op}/tests/st/
├── testcases/                        # 最终测试用例（下游直接消费）
│   ├── {op}_L0_test_cases.csv + L0_coverage_report.yaml
│   ├── {op}_L1_test_cases.csv + L1_coverage_report.yaml
│   └── {op}_L2_test_cases.csv
└── design/                           # 测试设计中间产物
    ├── 03_参数定义.yaml / 04_测试因子.yaml / 05_约束定义.yaml
    ├── 06_求解配置.yaml / 07_因子值.csv
```

## 二、9 步设计流程

### Step 1：输入文件校准
从 REQUIREMENTS.md + aclnn{Op}.md 获取算子接口信息。

### Step 2：算子参数定义
**3 大类 6 种参数类型**：

| 类别 | type 值 | 值配置字段 |
|---|---|---|
| Tensor 类 | aclTensor, aclTensorList | dtype_with_ranges |
| Array 类 | aclIntArray, aclFloatArray, aclBoolArray, aclScalarList | dtype_with_ranges |
| Scalar 类 | aclScalar（18 种标量 int4_t~string） | dtype_with_values |

关键要点：
- `aclnn_name` 必填（顶层，从接口文档名获取）。
- 每参数定义 name/type/required/io_type。
- 数据类型必须完整复制（不遗漏）。
- Tensor 需定义 format/dimensions；TensorList 加 length_ranges。
- dimensions 取值范围：通用最小 1 最大 8，结合接口文档约束调整。
- 明确 value_range 和 special_range/special_value。
- 无需定义 workspaceSize 和 executor 参数。

### Step 3：测试因子提取
`generate_test_factors.py` 自动识别参数类型，提取所有测试因子（存在性/格式/维度/数据类型/取值范围/特殊值），生成规范 YAML。

### Step 4：参数依赖关系分析
解析算子数学公式及计算逻辑，提取 GetWorkspaceSize 中参数依赖关系。

**9 种约束类型**：

| 类型 | 语义 | 典型场景 |
|---|---|---|
| calculate | 计算约束 | 类型等值/形状计算/自引用/多 shape 广播 |
| broadcast_dim | 指定维度广播 | 单维度广播兼容性 |
| broadcast_shape | 张量广播 | 完整形状广播（单向/双向） |
| conditional | 条件约束 | if-then-else 分支 |
| match | 匹配约束（双向） | 维度/属性双向匹配 |
| existential | 存在性约束 | 可选参数联动 |
| convertible | 可转换约束 | 类型兼容性检查 |
| inferable_filter | 链式依赖约束 | 多 Tensor 类型互推导 |
| inferable | 可推导约束 | 类型推导检查 |

约束分析维度优先级：数据类型依赖 > 形状依赖 > 数值依赖 > 存在性依赖。

### Step 5：生成隐式约束
`generate_implicit_constraints.py` 自动生成 6 类通用隐式约束（幂等性保证）：
1. Tensor/TensorList 输入：shape 依赖 dimensions。
2. 所有输入：value_range 依赖 dtype。
3. TensorList/Array 类：length 依赖 length_ranges。
4. TensorList：shape_list 依赖 length + dimensions。
5. Array 类：value 依赖 length + value_range。
6. 非 Tensor 非枚举：value 依赖 value_range。

### Step 6：构建依赖图
`generate_solver_config.py` 解析约束，构建因子依赖图，拓扑排序定求解层级，识别锚点因子（入度为 0）。

### Step 7：约束求解与因子值生成
`generate_factor_values.py` 加载求解配置，识别锚点因子独立采样，按拓扑顺序逐层推导，验证每用例满足所有约束，输出 CSV（`--max-cases 10000`）。

### Step 8：测试用例生成（L0/L1/L2）
`generate_test_cases.py` 统一生成三档（建议分三步执行，5 分钟超时）：

| 级别 | 定义 | 覆盖目标 | 用例数 |
|---|---|---|---|
| L0 | 门槛用例 | 核心功能直通 | ≤ 200 |
| L1 | 功能/精度/性能用例 | 参数 BC 组合，正常+典型边界，DFX 基准 | 500~700 |
| L2 | 异常用例 | dtype/dim 等异常 | ≤ 20 |

L0 和 L1 自动生成空 tensor 用例（从正常用例派生）。

### Step 9：测试设计结果总结
归档参数定义/因子/约束/依赖图/求解/用例生成全过程。

## 三、6 个自动化脚本

| 脚本 | 功能 |
|---|---|
| generate_test_factors.py | 测试因子提取 |
| generate_implicit_constraints.py | 隐式约束生成 |
| generate_solver_config.py | 求解配置生成（依赖图 + 拓扑排序） |
| generate_factor_values.py | 满足约束的因子值生成 |
| generate_test_cases.py | 用例生成（L0/L1/L2 + 空tensor派生） |
| generate_empty_tensor_cases_derive.py | 空tensor用例派生 |

> 脚本是 cannbot 源（CANN OSL v2.0）—— AtlasHarness **引用不 vendor**：测试设计时 agent 用基座 coding 调用脚本（从 cannbot 仓读脚本执行），不把脚本搬进本 skill。

## 关联

- `ut-develop.md` — UT 覆盖增强方法论
- `whitebox-design.md` — 白盒用例生成方法论
- `test-strategy.md` — ST vs UT vs whitebox vs golden 选择决策树
