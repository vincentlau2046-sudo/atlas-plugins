---
name: community-ascendc-op
description: 社区 Ascend C 算子开发全流程 skill 包（17 技能）的 Atlas 策展封装：项目初始化→设计→codegen→开发→编译调试→code review→精度调试/评估→性能评估/优化→测试用例→文档。触发：社区 Ascend C 算子端到端开发。
when_to_use: Use for the full community Ascend C operator lifecycle: init → design → codegen → dev → compile-debug → review → precision → performance → testcase → docs. Curation over the community/Op Ascend C pack.
allowed-tools: AscendSpecParser, AscendTilingPlanner, AscendCodeGen, AscendCompilerBridge, AscendGoldenTest, AscendBenchmarkRunner, AscendProfileReportParser
---

# 社区 Ascend C 算子全流程（官方策展）

Curated **Atlas curation wrapper** for the official **`community-ascendc-op-skills`** skill-pack (17 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Drive a community Ascend C operator through the full lifecycle, using the official pack for method and the Atlas tools for each execution stage.

## Gates（产出须含）

- [ ] project initialized
- [ ] design + codegen + dev complete
- [ ] compile-debug clean
- [ ] precision + performance evaluated
- [ ] testcase + docs produced

## Tool catalog（工具面 — route to Atlas tools）

- **AscendSpecParser** — parse an operator spec (shape/dtype/attributes) into a structured OperatorSpec — entry point of the operator-dev chain
- **AscendTilingPlanner** — return a 3×2 mock preset table (throughput/latency/balanced × 2 plans) — T0 mock liveness signal, NOT a tiling methodology
- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendCompilerBridge** — compile via bisheng (`python3 setup.py build_ext`) with NPU arch probe (910→dav-2201 / 950→dav-3510) — returns compile evidence
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)
- **AscendBenchmarkRunner** — ais-bench benchmark (IEEE 2937) — throughput/latency evidence
- **AscendProfileReportParser** — parse `msprof --analyze` op_summary — per-op performance breakdown

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `community-ascendc-op-skills` (17 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `community/Op`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — you may quote with attribution, but prefer routing to the Atlas tools.
- Each lifecycle stage maps to a specific Atlas tool (see Tool catalog).

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- 17 sub-skills — don't load them all; route by the current lifecycle stage.
- Precision-eval and performance-optim are separate sub-skills; don't conflate them.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
