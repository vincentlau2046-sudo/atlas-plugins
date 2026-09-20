---
name: ascend-precision-debug
description: Ascend 精度调试技能，提供模型级（msprobe PrecisionDebugger/L0-L1/ATB dump/compare）vs 算子级（DumpTensor 7步/PyPTO二分/golden）两层级定位方法论 + 误差标准 + 判定决策树。触发：训练 loss NaN/尖刺/不对齐、推理乱码/重复、单算子 golden fail、FP32-pass-FP16-fail、需判定模型级 vs 算子级。
when_to_use: Use when the user asks to debug an Ascend precision problem — model-level (training loss NaN/spike/misalignment, inference garbled/repeat) or operator-level (single-op golden fail, FP32-pass-FP16-fail). The agent decides model-level (msprobe dump+compare) vs operator-level (DumpTensor/PyPTO binary search) from symptoms, reads references on demand, and produces a root-cause hypothesis with evidence. No fixed step order.
allowed-tools: AscendGoldenTest, AscendDiagnoser
---

# Ascend 精度调试

Drive a precision root-cause analysis for an Ascend model/operator. You decide model-level (msprobe) vs operator-level (DumpTensor/PyPTO) from symptoms, read references on demand (progressive disclosure), and produce a root-cause hypothesis backed by dump/golden evidence. There is no fixed step order — you decide what to read and which tool to call based on the symptom class.

## Goal

Produce a precision root-cause report for the given symptom: level judgment (model-level vs operator-level) + dump/golden evidence + candidate root cause + fix direction.

## Gates（产出须含）

- [ ] **层级判定**：明确判模型级（整网 loss/NaN/乱码）还是算子级（单算子 golden fail / FP32-pass-FP16-fail），附判定依据（症状信号）.
- [ ] **dump 证据**：模型级→msprobe PrecisionDebugger L0/L1 或 ATB dump 采集说明；算子级→DumpTensor 关键点或 PyPTO 检查点 tensor 说明（指明 CopyIn/Compute/CopyOut 或检查点位置）.
- [ ] **golden 对比**：模型级→`msprobe compare` 首差异 API/层 + 误差；算子级→numpy golden vs NPU 的 MERE/MARE + 是否超阈值（对照 `precision-standard.md`）.
- [ ] **候选根因**：对照 9 陷阱表（FP16精度/溢出/减法抵消/Reduce/除零/硬件约束/类型转换/Cast RoundMode/输出全0）或模型级 CheckList（超参/三方库/数据/结构/传参/环境），给出候选根因.
- [ ] **修复方向**：升精度 / 改算法 / 修同步 / 修传参 / 对齐配置 等具体方向 + 验证方式（重跑 golden / compare）.

## Tool catalog

- **AscendGoldenTest** (T0 Tool) — numpy ref vs NPU 输出，按 MERE/MARE + dtype 阈值判 pass/fail。返回 `mocked: true` 时是 liveness 信号非正确性证明（须在报告说明）.
- **AscendDiagnoser** (T0 Tool) — 返回诊断 evidence（非 `next_tool` 决策）；配合 trap 表推断根因.
- **msprobe** (Shape B Python 库，非 shell Tool) — 模型级精度主工具。agent 用基座 coding 写 `from msprobe.pytorch import PrecisionDebugger` + config.json，或 source `load_atb_probe.sh`（ATB 推理侧），CLI `msprobe compare` 比对。不包 shell Tool（Shape B 约定）.

**references**（按需读，progressive disclosure）:

- **references/msprobe-usage.md** (T1) — PrecisionDebugger API + config.json schema + L0/L1/mix 粒度 + task 模式（statistics/tensor/md5/xor/nan_check）。模型级训练侧 dump 主入口。读此做模型级 dump。(msprobe@6824676, MulanPSL-2.0, verified)
- **references/msprobe-infer-dump.md** (T1) — ATB 推理侧 dump：`source load_atb_probe.sh`（非 Python import）+ atb_probe 源码装 + op/Operation/Kernel 概念 + CANN 8.3.RC1+。读此做推理侧 dump。(msprobe@6824676, verified)
- **references/msprobe-compare.md** (T1) — `msprobe compare -tp -gp` 子命令 + 参数 + API 匹配规则 + 首差异定位 `-da`。dump 后比对主入口。读此做逐层比对。(msprobe@6824676, verified)
- **references/msprobe-best-practices.md** (T2) — 训练/推理精度问题二分（模型精度 vs 数值精度）+ 5 现象 + CheckList + 复现前置（seed_all/确定性）+ 模型级→算子级转判。模型级方法论主源。读此定模型级定位思路。(msprobe@6824676, verified)
- **references/ascendc-operator-precision.md** (T1) — 算子级数值限制 + 9 陷阱表 + 7 步诊断流程 + 调试计数规则（≤7 次 DumpTensor / >7 切二分）+ 误差模式识别。算子级根因主源。读此做算子级根因。(cannbot@c24e8b5, CANN-OSL-2.0, verified)
- **references/pypto-binary-search.md** (T1) — PyPTO 二分定位法 6 步 + 检查点 tensor 原理 + 关键技巧（assemble/shape/dtype）+ verify 文件保存法。>7 次切此。读此做算子级二分。(cannbot@c24e8b5, verified)
- **references/precision-standard.md** (T2) — MERE/MARE 指标 + 生态开源阈值（FP16 2⁻¹⁰/FP32 2⁻¹³/...）+ 商业分级 L0/L1/L2 + 通过标准。比对判据。读此判 pass/fail。(cannbot@c24e8b5, verified)
- **references/dumptensor-7step.md** (T2) — DumpTensor 7 步法 + desc 编号（100-199/200-299/300-399）+ 使用陷阱（DeQue 后 Dump/blockIdx/dumpSize≤32/调试完移除）。算子级快速调试操作参考。读此做算子级快速 dump。(cannbot@c24e8b5, verified)
- **references/debug-decision-tree.md** (T3) — 模型级 vs 算子级判定决策树 + 关键判定信号 + 常见误判。**启发式综合**（confidence:heuristic），路径选择参考。读此做层级判定。(composite, heuristic)

**scripts/assets**:

- **scripts/precision-verify-template.py** — numpy golden vs NPU 输出 rtol/atol 比对模板（自撰，自有许可）.
- **assets/msprobe-config-template.json** — L0/L1/mix dump config.json 模板（自撰，自有许可）.

Read references via their relative path in this skill's base directory (the base directory path is injected above). Read on demand — do not load all at once.

## Rules

- **先判层级再下手**：模型级症状（loss NaN/乱码）先过 msprobe CheckList（大部分精度问题源于非算子因素：超参/三方库/数据/结构），别直接钻单算子；算子级症状（单算子 golden fail）走 DumpTensor/PyPTO。判定走 `debug-decision-tree.md`.
- **msprobe 是 Shape B Python 库**：训练侧 `from msprobe.pytorch import PrecisionDebugger`（Python API），推理侧 `source load_atb_probe.sh`（sourced shell，非 Python import），比对 `msprobe compare`（CLI 子命令）。不包 shell Tool —— agent 用基座 coding 写调用。
- **ATB dump 非 msit CLI**：ATB dump 入口是 `source .../load_atb_probe.sh`，不是 `msit llm dump`（msit=umbrella 仓非 CLI），不是 `msprobe -m atb_dump`（臆造模块形式）。
- **数值偏差 ≠ 精度问题**：不同硬件细微数值偏差在 `precision-standard.md` 阈值内属正常，勿过度定位。
- **调试计数规则**：算子级 ≤7 次用 DumpTensor 快速方法，>7 次切 PyPTO 二分（二分要改 kernel 签名 + golden 返回值，成本高，非首选）。
- **工具返证据非决策**：AscendGoldenTest/AscendDiagnoser 返回 evidence（误差数据/诊断信息），不返回 `next_tool`；agent 据证据 + 陷阱表推断根因。
- **当工具返 `mocked: true`**：视作 liveness 信号非正确性证明，须在报告说明。
- **许可**：msprobe refs = MulanPSL-2.0（宽松，关键 API 摘录带 attribution）；cannbot refs = CANN OSL v2.0（non-sublicensable，引用+溯源不 vendor 文本）；references 均自撰验真文本（抽取事实重写），非逐字 copy.

## Gotchas

- **msit 是 umbrella 仓非 CLI**：精度模块已从 msit 日落抽到 msprobe 独立仓。真虚构仅 msopcom + `msit llm dump`（后者臆造）；msprobe 是真实独立工具（gitcode.com/Ascend/msprobe）。
- **ATB dump 入口形态易错**：训练侧 PrecisionDebugger 是 Python API，推理侧 ATB 是 `source load_atb_probe.sh`（sourced shell）—— 两者形态完全不同，勿混。`msprobe -m compare`（模块形式）是臆造，正确是 `msprobe compare`（子命令）。
- **算子级 vs 模型级勿混**：单算子 FP16 溢出也会引发整网 NaN，但根因在算子；msprobe compare 定位首差异 API 后须转单算子验证。反之 loss 不对齐常源于超参/三方库，别直接钻单算子。
- **工具副作用**：msprobe 的 item 同步/hook 可能略改 loss/gnorm；DumpTensor 改执行流 —— 区分工具副作用与真实精度问题。
- **github 零命中≠虚构**：msprobe 真源在 gitcode.com/Ascend/msprobe（github 仅部分镜像），验 CLI 必查官方文档命令形态（msit_llm_dump + msprobe -m 两臆造都因没验入口形态）。
- **DumpTensor 必 DeQue 后 Dump**：在 `DeQue`（出队）之后调用，不能 `AllocTensor`（分配）后立即 dump（数据未填充）；多核按 blockIdx 编 desc；dumpSize≤32；调试完移除全部 dump 代码.
