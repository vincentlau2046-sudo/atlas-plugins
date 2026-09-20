---
name: cannbot-triton-op-generator
description: "官方 CANNBot Triton-Ascend 算子 skill 包（6 技能）的 Atlas 策展封装：任务提取/算法设计/代码生成/功能验证/性能优化/NPU 架构参考。触发：Triton-Ascend 算子代码生成或优化。"
when_to_use: "Use when generating/optimizing a Triton-Ascend operator — task extraction, algorithm design, codegen, verification, perf optimization, NPU arch reference. Curation over the official CANNBot Triton pack."
allowed-tools: AscendCodeGen, AscendCompilerBridge, AscendGoldenTest, AscendBenchmarkRunner
---

# Triton-Ascend 算子代码生成（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-triton-op-generator-skills`** skill-pack (6 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Generate and optimize a Triton-Ascend operator, using the official pack for the design/coding method and the Atlas tools for compile/verify/bench.

## Gates（产出须含）

- [ ] task extracted + algorithm designed
- [ ] code generated
- [ ] functionality verified (golden)
- [ ] latency-optimization pass with evidence

## Tool catalog（工具面 — route to Atlas tools）

- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendCompilerBridge** — compile via bisheng (`python3 setup.py build_ext`) with NPU arch probe (910→dav-2201 / 950→dav-3510) — returns compile evidence
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)
- **AscendBenchmarkRunner** — ais-bench benchmark (IEEE 2937) — throughput/latency evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-triton-op-generator-skills` (6 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/ops`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- The Triton backend is a RESERVED stub in Atlas (Ascend C is the MVP) — the official pack supplies the Triton method.
- CANN OSL v2.0 content is referenced + provenance-pointed, NEVER vendored.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- Triton-Ascend codegen is not yet wired to a real Atlas backend — treat AscendCodeGen's Triton path as a reserved stub.
- NPU arch reference (npu-arch) is shared with the ops-direct-invoke pack.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
