---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ops-precision-standard/reference/golden/{COMMERCIAL_OPS_PRECISION_DOCS,OPS_PRECISION_STANDARDS}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ops-precision-standard/reference/golden 的 COMMERCIAL_OPS_PRECISION_DOCS + OPS_PRECISION_STANDARDS 抽取 MERE/MARE 指标/分级 L0-L2/阈值表自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Ascend 算子精度标准（误差指标 + 分级阈值）

> 本文是 **精度比对的判据标准**（T2，cannbot@c24e8b5 验真，2 源文件）。`msprobe compare` 或 golden 测试得到误差后，用本标准的阈值判 pass/fail。覆盖生态开源标准 + 商业算子分级两套。

## 一、误差指标

精度评价用相对误差指标（attribution: cannbot@c24e8b5 `OPS_PRECISION_STANDARDS.md`）：

**平均相对误差 MERE**（Mean Relative Error）—— 采样点相对误差的平均值：
```
MERE = avg( abs(actual - golden) / (abs(golden) + 1e-7) )
```
> 引入小值 `1e-7` 避免 golden=0 时除零。

**最大相对误差 MARE**（Max Relative Error）—— 采样点相对误差的最大值：
```
MARE = max( abs(actual - golden) / (abs(golden) + 1e-7) )
```

另有 **RMSE**（均方根误差）用于商业算子分级（COMMERCIAL_OPS_PRECISION_DOCS）。

## 二、生态算子开源精度标准（单标杆比对）

与更高精度实现（CPU/GPU/昇腾小算子拼接）的单一精度标杆直接比对，通过阈值（attribution: cannbot@c24e8b5 `OPS_PRECISION_STANDARDS.md`）：

| 数据类型 | 通过阈值 Threshold |
|---|---|
| **FLOAT16** | 2⁻¹⁰ (≈9.77e-4) |
| **BFLOAT16** | 2⁻⁷ (≈7.81e-3) |
| **FLOAT32** | 2⁻¹³ (≈1.22e-4) |
| **HiFLOAT32** | 2⁻¹¹ (≈4.88e-4) |
| **FLOAT8 E4M3** | 2⁻³ (≈0.125) |
| **FLOAT8 E5M2** | 2⁻² (≈0.25) |

**通过标准**：`MERE < Threshold` **且** `MARE < 10 × Threshold` → 判通过。

> 阈值随 dtype 精度位宽递减而放宽（FP32 最严 2⁻¹³，FP8 最宽 2⁻²/2⁻³），反映各 dtype 的固有表达限制。

## 三、商业算子精度分级（L0/L1/L2）

商业算子按重要性分级，测试用例规模与阈值逐级加严（attribution: cannbot@c24e8b5 `COMMERCIAL_OPS_PRECISION_DOCS.md`，阈值单位为 ×10⁻³，列序 MARE / MERE / RMSE）：

| 精度等级 | 等级定义 | 用例规模 | 阈值 MARE/MERE/RMSE (×10⁻³) | 适用场景 |
|---|---|---|---|---|
| **L0** | 常规算子 | ≥ 5,000 | ≤10 / ≤2 / ≤2 | 满足基本数值正确性，非敏感业务 |
| **L1** | 重要算子 | ≥ 10,000 | ≤5 / ≤1.5 / ≤1.5 | 多模态/LLM-MOE/推荐系统等高精度要求 |
| **L2** | 关键算子 | ≥ 30,000 | ≤2 / ≤1.2 / ≤1.2 | 上述业务中的关键算子，最严苛验收 |

> 用例规模是最低要求（L0≥5000/L1≥10000/L2≥30000），保证统计有效性；阈值随等级升高而收严（L2 的 MARE≤2e-3 最严）。

## 四、标准核心思想

验证流程三环节：

1. **用例生成规则** —— 构建覆盖算子典型与边界场景的测试数据（规模达分级要求）。
2. **执行策略** —— 依据分级在 NPU 和三方芯片（CPU/GPU）分别执行，得两套输出。
3. **输出比对** —— 按误差指标（MERE/MARE/RMSE）比对，对照分级阈值判 pass/fail。

## 五、范围与应用场景

- **范围**：Kernel（算子最小实现/调用单位）+ ACLNN-API（对 Kernel 的封装及组合调用，单个 API 含一个或多个 Kernel）。
- **适用**：昇腾算子开发/测试人员、框架 API 开发者、模型开发者。

## 六、与 AtlasHarness 工具的衔接

- `AscendGoldenTest`（T0 Tool）：numpy ref vs NPU 输出，按本标准的 MERE/MARE + dtype 阈值判 pass/fail（`mocked:true` 时是 liveness 信号非正确性证明）。
- `scripts/precision-verify-template.py`：numpy golden vs NPU 的 rtol/atol 比对模板（速查版，正式分级用本标准）。
- `msprobe compare`：整网/逐 API 比对，结果 csv 可对照本标准阈值判各 API 是否达标。

> 默认 rtol 速查（`ascendc-operator-precision.md`）：FP16 1e-3/1e-4、FP32 1e-5/1e-6、INT 0 —— 是调试期速判，正式交付用本标准的分级阈值。

## 关联

- `ascendc-operator-precision.md` — 算子级调试期默认 rtol/atol（速查）
- `msprobe-compare.md` — 比对产出误差数据，本标准提供判据
- `scripts/precision-verify-template.py` — numpy 比对模板
