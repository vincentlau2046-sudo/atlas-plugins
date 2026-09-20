---
name: cannbot-model-infer
description: 官方 CANNBot NPU 模型推理优化 skill 包（11 技能）的 Atlas 策展封装：框架适配/并行策略/KVCache+FA/融合算子/图模式/精度运行时调试/多流/预取/SuperKernel。触发：LLM/大模型在 NPU 上的推理性能优化。
when_to_use: Use for NPU model-inference optimization: framework adaptation, parallel strategy, KVCache/flash-attn, fusion, graph mode, multi-stream, prefetch, SuperKernel. Curation over the official CANNBot model-infer pack.
allowed-tools: AscendBenchmarkRunner, AscendProfileReportParser, AscendDiagnoser
---

# NPU 模型推理优化（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-model-infer-skills`** skill-pack (11 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Optimize model inference on NPU across the 11 official sub-skills, using the Atlas benchmark/profile tools to measure the effect.

## Gates（产出须含）

- [ ] target optimization axis chosen (KVCache/fusion/multi-stream/...)
- [ ] change applied
- [ ] benchmark + profile delta measured
- [ ] no precision regression

## Tool catalog（工具面 — route to Atlas tools）

- **AscendBenchmarkRunner** — ais-bench benchmark (IEEE 2937) — throughput/latency evidence
- **AscendProfileReportParser** — parse `msprof --analyze` op_summary — per-op performance breakdown
- **AscendDiagnoser** — collect + return fault EVIDENCE (log/error fragments); it never emits a next_tool — you decide from the evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-model-infer-skills` (11 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/model`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- Measure with the Atlas benchmark/profile tools before/after each optimization axis.
- CANN OSL v2.0 content is referenced + provenance-pointed, NEVER vendored.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- 11 sub-skills span very different axes — scope ONE axis per iteration.
- KVCache/flash-attn changes can silently regress precision — re-run the golden gate.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
