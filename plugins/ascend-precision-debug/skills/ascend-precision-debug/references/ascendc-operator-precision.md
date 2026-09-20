---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-precision-debug/{SKILL,references/common-traps,references/diagnosis-workflow,references/tools-reference}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-precision-debug 的 SKILL + common-traps + diagnosis-workflow + tools-reference 抽取算子级数值限制/9 陷阱/7 步诊断流程/调试计数规则自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Ascend C 算子级精度根因定位

> 本文是 **算子级精度调试的主源**（T1，cannbot@c24e8b5 验真，4 源文件）。面向"单算子 golden 测试 fail / FP32 pass 但 FP16 fail"这类算子级问题。区别于模型级 msprobe（整网 loss/NaN）—— 算子级聚焦单个算子的数值正确性。

## 一、数值精度基础

不同 dtype 的数值表达限制是算子级精度问题的根因之一：

| dtype | 位宽 | 精度位 | 范围 | 典型风险 |
|---|---|---|---|---|
| FP32 | 32 | 23 | ±3.4e38 | 基准（golden 常用） |
| FP16 | 16 | 10 | ±65504 | 溢出（>65504→inf）+ 累加误差 |
| BF16 | 16 | 7 | ±3.4e38 | 范围大但精度低，累加误差更明显 |
| INT8 | 8 | — | [-128,127] | 量化误差 |

默认比对阈值（rtol/atol，参考值，非硬标准 —— 正式标准见 `precision-standard.md`）：FP16 `1e-3`/`1e-4`，FP32 `1e-5`/`1e-6`，INT `0`（精确匹配）。

## 二、典型诊断模式

### 2.1 FP32 pass / FP16 fail

算子 FP32 实现正确但 FP16 失败 → **FP16 精度不足 / 溢出**。排查方向：
- 中间累加是否用 FP16（应升 FP32 累加器）。
- 是否存在 exp/log 等易溢出运算。
- 输入数值范围是否触 FP16 上限（65504）。

### 2.2 BF16 pass 诊断

BF16 范围与 FP32 同但精度位仅 7 → 范围类问题（溢出）pass，精度类问题（累加误差）可能 fail。区分范围 vs 精度根因。

## 三、9 大常见陷阱

| # | 陷阱 | 根因 | 修复方向 |
|---|---|---|---|
| 1 | **FP16 精度不足** | FP16 中间累加误差 | 混合精度：中间累加升 FP32 |
| 2 | **exp/log 溢出** | exp(大值)→inf | 数值稳定化（Softmax 减最大值再 exp） |
| 3 | **减法抵消** | 近似数相减丢有效位 | 重排公式 / 有理化 |
| 4 | **Reduce 精度损失** | FP16 逐元素累加误差累积 | FP32 累加器（Welford 等稳定算法） |
| 5 | **除零风险** | golden=0 致相对误差 inf | 加 epsilon（`abs(golden)+1e-7`） |
| 6 | **硬件约束** | Reduce 最小 8 元素 / 32B 对齐 | 对齐填充或边界特判 |
| 7 | **类型转换** | 中间 cast 丢精度 | 推迟 cast 到最后 / 保留高精度中间态 |
| 8 | **Cast RoundMode** | half→float 用 CAST_NONE（不舍入），float→half 用 CAST_ROUND（舍入） | 按方向选对 RoundMode |
| 9 | **输出全 0** | 流水线同步缺失 / DataCopy 非对齐 / GlobalTensor.SetValue 误用 | 修流水线同步 + 对齐 + SetValue 用法 |

## 四、7 步系统化诊断流程

（attribution: cannbot@c24e8b5 `diagnosis-workflow.md`）

1. **问题定位**：明确现象（输出错/NaN/精度超阈值）。
2. **误差分析**：识别误差模式 —— 系统性偏差（整体偏移）/ 随机（噪声）/ 聚集（特定区域）/ 稀疏大误差（个别点极大偏离）。
3. **最小化复现**：构造最小 shape 复现问题。
4. **中间结果检查**：DumpTensor 采中间 tensor 逐段比对（见 `dumptensor-7step.md`）。
5. **根因分析**：结合陷阱表定位根因。
6. **解决方案**：实施修复（升精度/改算法/修同步等）。
7. **验证修复**：重跑 golden 测试确认 pass。

## 五、调试计数规则（何时切二分）

- **≤ 7 次**：用 DumpTensor 快速方法（在关键点加 Dump、逐段比对）定位。
- **> 7 次**仍未定位：切**二分对比隔离**（PyPTO 二分定位法，见 `pypto-binary-search.md`）—— 添加检查点 tensor 二分找首个出错 op。

> 这是效率纪律：快速方法够用就别上二分（二分要改 kernel 签名 + golden 返回值，成本高）；快速方法不够再上二分。

## 六、误差模式识别

误差分布模式暗示不同根因：
- **系统性偏差**（整体偏移）→ 算法/公式实现错或 dtype 系统性损失。
- **随机噪声** → 累加顺序/并行归约不确定性。
- **聚集误差**（特定区域）→ 该区域 shape 触硬件约束或边界分支错。
- **稀疏大误差**（个别点极大）→ 溢出/除零/特殊值（inf/nan）处理缺失。

## 关联

- `dumptensor-7step.md` — DumpTensor 7 步法（中间结果采集的具体操作）
- `pypto-binary-search.md` — 二分定位法（>7 次切此）
- `precision-standard.md` — 正式精度阈值与分级（rtol/atol 标准）
- `debug-decision-tree.md` — 模型级 vs 算子级判定
