---
name: cannbot-pypto-op-orchestrator
description: 官方 CANNBot PyPTO 算子 skill 包（8 技能）的 Atlas 策展封装：API 探索/Golden 生成/需求理解/算子设计与开发/性能调优/精度调试。触发：PyPTO（Python 算子）开发或精度/性能调优。
when_to_use: Use when developing a PyPTO (Python-based) operator — intent understanding, op design/dev, golden generation, perf-tune, precision debug. Curation over the official CANNBot PyPTO pack.
allowed-tools: AscendSpecParser, AscendCodeGen, AscendGoldenTest, AscendBenchmarkRunner
---

# PyPTO 算子开发编排（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-pypto-op-orchestrator-skills`** skill-pack (8 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Orchestrate a PyPTO operator from intent to a verified, tuned implementation, using the official pack for method and the Atlas tools for execution.

## Gates（产出须含）

- [ ] intent/spec understood
- [ ] op design + dev complete
- [ ] golden (numpy vs NPU) passed
- [ ] perf/precision tune loop run with evidence

## Tool catalog（工具面 — route to Atlas tools）

- **AscendSpecParser** — parse an operator spec (shape/dtype/attributes) into a structured OperatorSpec — entry point of the operator-dev chain
- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)
- **AscendBenchmarkRunner** — ais-bench benchmark (IEEE 2937) — throughput/latency evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-pypto-op-orchestrator-skills` (8 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/ops`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- The orchestrator skill sets the METHOD; the Atlas tools provide EVIDENCE — you decide from evidence.
- CANN OSL v2.0 content is referenced + provenance-pointed, NEVER vendored.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- Precision issues: use the precision-debug sub-skill + AscendGoldenTest, not trial-and-error.
- Golden generation must match the target dtypes/shapes or the correctness gate is meaningless.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
