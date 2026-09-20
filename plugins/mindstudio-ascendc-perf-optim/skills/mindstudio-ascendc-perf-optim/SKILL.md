---
name: mindstudio-ascendc-perf-optim
description: "MindStudio Ascend C 算子性能优化 skill 的 Atlas 策展封装：基于 Profiling 数据的端到端性能优化（API 调优/数据搬运/流水线/Tiling 参考）。触发：对 Ascend C 算子做数据驱动的性能优化。"
when_to_use: "Use for data-driven Ascend C operator performance optimization: API tuning, data movement, pipelining, tiling — grounded in profiling. Curation over the MindStudio Ascend C perf-opt skill."
allowed-tools: AscendBenchmarkRunner, AscendProfileReportParser, AscendTilingPlanner
---

# MindStudio Ascend C 算子性能优化（官方策展）

Curated **Atlas curation wrapper** for the official **`mindstudio-ascendc-perf-optim-skills`** skill-pack (1 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Optimize an Ascend C operator's performance using profiling evidence + the official method, verified by the Atlas benchmark tool.

## Gates（产出须含）

- [ ] profiling baseline captured (msprof)
- [ ] bottleneck identified (op_summary)
- [ ] optimization applied (API/move/pipeline/tiling)
- [ ] benchmark delta measured

## Tool catalog（工具面 — route to Atlas tools）

- **AscendBenchmarkRunner** — ais-bench benchmark (IEEE 2937) — throughput/latency evidence
- **AscendProfileReportParser** — parse `msprof --analyze` op_summary — per-op performance breakdown
- **AscendTilingPlanner** — return a 3×2 mock preset table (throughput/latency/balanced × 2 plans) — T0 mock liveness signal, NOT a tiling methodology

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `mindstudio-ascendc-perf-optim-skills` (1 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `official/MindStudio/skills`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- Optimize against the profiler, not intuition — the report-parser tool feeds the loop.
- Apache-2.0 + CC-BY-SA-4.0 — quote with attribution.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- The TilingPlanner Atlas tool is a mock — use the official tiling reference for real tiling changes.
- Benchmark before/after must use the same shape/dtype or the delta is meaningless.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
