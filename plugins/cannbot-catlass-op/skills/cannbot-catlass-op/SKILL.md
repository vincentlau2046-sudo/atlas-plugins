---
name: cannbot-catlass-op
description: 官方 CANNBot Catlass 算子 skill 包（3 技能）的 Atlas 策展封装：Catlass 算子设计/开发/性能调优。触发：用 Catlass 模板做 GEMM/卷积类算子开发或性能调优。
when_to_use: Use when developing or performance-tuning a Catlass template operator (GEMM/conv-class) — design, develop, perf-tune. Curation over the official CANNBot Catlass pack.
allowed-tools: AscendCodeGen, AscendCompilerBridge, AscendGoldenTest, AscendBenchmarkRunner
---

# Catlass 模板算子开发（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-catlass-op-skills`** skill-pack (3 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Develop a Catlass template operator and tune its performance, using the official pack for template knowledge and the Atlas tools for execution + verification.

## Gates（产出须含）

- [ ] operator design (Catlass template selection) documented
- [ ] four-piece scaffold via AscendCodeGen
- [ ] bisheng compile evidence
- [ ] golden correctness + benchmark evidence

## Tool catalog（工具面 — route to Atlas tools）

- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendCompilerBridge** — compile via bisheng (`python3 setup.py build_ext`) with NPU arch probe (910→dav-2201 / 950→dav-3510) — returns compile evidence
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)
- **AscendBenchmarkRunner** — ais-bench benchmark (IEEE 2937) — throughput/latency evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-catlass-op-skills` (3 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/ops`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- Route execution to the Atlas tools; official Catlass knowledge is referenced, not vendored (CANN OSL v2.0).
- Use the benchmark tool for the perf-tune loop, not manual timing.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- Catlass template selection is the hard part — read the official design skill before touching code.
- Reserve TileLang/Triton backends; only Ascend C is the MVP backend today.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
