---
name: community-catlass-op
description: "社区 Catlass 算子开发全流程 skill 包（4 技能）的 Atlas 策展封装：设计→codegen→开发→性能优化。触发：社区 Catlass 模板算子开发。"
when_to_use: "Use for the community Catlass template operator flow: design → codegen → dev → performance optimization. Curation over the community/Op Catlass pack."
allowed-tools: AscendCodeGen, AscendCompilerBridge, AscendGoldenTest, AscendBenchmarkRunner
---

# 社区 Catlass 算子全流程（官方策展）

Curated **Atlas curation wrapper** for the official **`community-catlass-op-skills`** skill-pack (4 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Develop a community Catlass template operator through design/codegen/dev/perf-opt using the Atlas tools.

## Gates（产出须含）

- [ ] Catlass template designed
- [ ] four-piece via AscendCodeGen
- [ ] compile evidence
- [ ] perf-opt loop run

## Tool catalog（工具面 — route to Atlas tools）

- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendCompilerBridge** — compile via bisheng (`python3 setup.py build_ext`) with NPU arch probe (910→dav-2201 / 950→dav-3510) — returns compile evidence
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)
- **AscendBenchmarkRunner** — ais-bench benchmark (IEEE 2937) — throughput/latency evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `community-catlass-op-skills` (4 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `community/Op`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- Apache-2.0 + CC-BY-SA-4.0 — quote with attribution; prefer the Atlas tools for execution.
- Route the perf-opt loop to the benchmark tool.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- Catlass template selection dominates the outcome — design before code.
- Only the Ascend C backend is real today; Catlass maps onto it.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
