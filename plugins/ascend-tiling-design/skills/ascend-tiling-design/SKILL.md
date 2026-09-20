---
name: ascend-tiling-design
description: Ascend C 算子 Tiling 设计技能，提供多核切分/UB切分/Buffer规划/分支覆盖四要素设计方法论 + 9 算法分类专属策略 + AISS 自动求解器指针。触发：设计新算子 tiling 方案、UB 容量不足需分块、多核负载不均、shape 分支未覆盖、需评估 AISS 自动求解 vs 手动设计。
when_to_use: Use when the user asks to design a tiling plan for an Ascend C operator — multi-core split, UB tiling, buffer planning, branch coverage, or per-category tiling strategy. The agent reads the methodology references on demand and produces a four-element plan; it does not prescribe a fixed step order.
allowed-tools: AscendTilingPlanner
---

# Ascend C 算子 Tiling 设计

Drive a tiling design for an Ascend C operator. You read the methodology references on demand (progressive disclosure) and produce a four-element plan. There is no fixed step order — you decide what to read and which tool to call based on the operator's category and shape.

## Goal

Produce a compliant tiling plan for the given operator (shape + dtype + hardware spec): four design elements complete + algorithm-category match + branch coverage.

## Gates（产出须含）

- [ ] **多核切分**：核间切分策略 + 负载均衡依据（非"随便切"）—— which dim to split, per-core task, core count.
- [ ] **UB 切分**：Unified Buffer 分块大小 + 容量计算（≤ UB 上限，附算式；DAV_2201=192KB / DAV_3510=248KB）.
- [ ] **Buffer 规划**：输入/输出/临时 buffer 分配 + 无冲突 + 总 UB 用量 + Double Buffer.
- [ ] **分支覆盖**：shape 分支枚举（满核/不满核/单核/边界，dtype FP32/FP16/BF16/INT8，32B 对齐/非对齐）.
- [ ] **算法类匹配**：算子归入 9 类之一 + 引用该类专属 tiling 算法（如 Reduction → welford/dichotomy/ara-rowsplit）.

## Tool catalog

- **AscendTilingPlanner** (T0 Tool) — returns a 3×2 mock preset table (throughput/latency/balanced × 2 plans). This is a **T0 mock placeholder** (`mocked: true` liveness signal), NOT a methodology. Use it for a quick baseline, then read references to complete the four elements.
- **references/tiling-methodology.md** (T1) — the four design elements + three design principles + core/intra split scenarios. Read this FIRST for any tiling design. (cann-learning-hub official tutorial, verified)
- **references/algorithm-categories.md** (T2) — the 9 algorithm categories (Reduction/Sort/Elementwise/Broadcast/Conversion/Random/MatMul/Convolution/NN) + per-category support status. Read to classify the operator. (cannbot@c24e8b5, verified)

**Per-category detailed tiling** (read the one matching the classified operator):

- **references/reduction-tiling.md** (T2) — Reduction: scene routing S1-S6 (AR/ARA/multi-axis/group-reduce), Welford/Dichotomy, multi-output buffer, with-index variant. (cannbot@c24e8b5, 13 source files, verified)
- **references/broadcast-tiling.md** (T2) — Broadcast: DimensionCollapse 合轴, four-branch routing (OneDim / UB 静态 DAV_2201 / Dynamic UB DAV_3510 / NDDMA), UB·多核切分公式. (cannbot@c24e8b5, verified)
- **references/matmul-tiling.md** (T2) — MatMul: mxfp8+eltwise 融合四要素 + matmul 族 (a16w16/mxfp4/mxfp8/batch/group) SWAT→FullLoad→StreamK 推导链 + 变体差异 + TilingData 字段. (cannbot@c24e8b5, 合两源, verified)
- **references/sort-tiling.md** (T2) — Sort: 归并排序原理, UB 容量约束 (tileSize=4096), Pattern A/B/C 决策树, 两级归并四阶段. (cannbot@c24e8b5, verified)
- **references/elewise-tiling.md** (T2) — EleWise: shape 相同逐元素, 多核(512对齐)/UB(256B对齐)切分, FP16/BF16 升精度分支 UB 预算. (cannbot@c24e8b5, verified)
- **references/conversion-tiling.md** (T2) — Conversion: small-channel transpose [C,N]→[N,C], 统一建模/路由/offset table/UB 预算. (cannbot@c24e8b5, 仅 transpose 展开, verified)
- **references/simt-tiling.md** (T2) — SIMT (≠SIMD): 核数切分 + 线程数 constexpr + DCache≥32KB, 不涉及 UB 切分. (cannbot@c24e8b5, verified)

**Heuristic / external** (T3 — hypothesis source, not fact assertions; validate with evidence):

- **references/shape-tradeoff-heuristics.md** (T3) — shape→切分策略 trade-off 直觉 (UB/对齐/多核/广播/精度), 综合各 category patterns. (heuristic, basis cannbot@c24e8b5 可验真, 结论是假设)
- **references/aiss-solver.md** (T3/external) — AISS-TilingSolver CLI pointer (auto-solve MatMul/Vector tiling, third-party/preview). Read when the user wants auto-solve vs manual design. (heuristic, not a fact source)

**Asset**:

- **assets/tiling-design-template.md** — self-authored four-element DESIGN.md template + checklist. Use as the output skeleton.

Read references via their relative path in this skill's base directory (the base directory path is injected above). Read on demand — do not load all at once.

## Rules

- **TilingPlanner's 3×2 table is a T0 mock** — do not treat it as the methodology. Designing a real operator tiling requires reading `references/tiling-methodology.md` and the category-specific reference to complete the four elements.
- **AISS is T3/external** (third-party/academic/preview) — use as a heuristic pointer +启发式参考, NOT as a fact source (cannot pin SHA). Parameters must be validated by actual run output.
- **Methodology主源 = cann-learning-hub** (gitcode.com/cann, CANN OSL v2.0 — referenced + provenance-pointed, not vendored).
- **Tiling params use direct formulas, not binary search** (official principle).
- When a tool returns `mocked: true`, treat its output as a liveness signal, not proof of correctness — say so in your report.

## Gotchas

- **AISS was once misjudged as fictional**: because the search stopped at github (faiss false hit) and never checked gitcode. It is real at gitcode.com/HIT1920/TilingSolver, but T3/external (code not fully open). See references/aiss-solver.md.
- **TilingPlanner mock ≠ methodology**: the Tool returns a construct-guaranteed placeholder table; the four elements in references/ are what the agent reads when designing.
- **github zero-hit ≠ fictional**: the tiling methodology真源 is at gitcode.com/cann/cann-learning-hub (not github). Always check gitcode主源 before concluding a source is fictional.
- **AR vs ARA勿混**: AR (A0=1, tail-axis reduction, Level 2 Reduce API) vs ARA (A0>1, non-tail-axis, Pattern::Reduce::RA) — different APIs, different branches.
