---
name: community-triton-op
description: 社区 Triton 算子开发全流程 skill 包（11 技能）的 Atlas 策展封装：设计→codegen→开发→code review→文档→环境配置→精度评估→性能评估/优化→内存检测。触发：社区 Triton-Ascend 算子开发。
when_to_use: Use for the community Triton-Ascend operator flow: design → codegen → dev → review → docs → env-config → precision-eval → performance → memory-check. Curation over the community/Op Triton pack.
allowed-tools: AscendCodeGen, AscendCompilerBridge, AscendGoldenTest, AscendBenchmarkRunner
---

# 社区 Triton 算子全流程（官方策展）

Curated **Atlas curation wrapper** for the official **`community-triton-op-skills`** skill-pack (11 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Develop a community Triton-Ascend operator through the full flow using the Atlas tools for each stage.

## Gates（产出须含）

- [ ] op designed + codegen
- [ ] dev + review complete
- [ ] precision evaluated
- [ ] performance + memory checks run

## Tool catalog（工具面 — route to Atlas tools）

- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendCompilerBridge** — compile via bisheng (`python3 setup.py build_ext`) with NPU arch probe (910→dav-2201 / 950→dav-3510) — returns compile evidence
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)
- **AscendBenchmarkRunner** — ais-bench benchmark (IEEE 2937) — throughput/latency evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `community-triton-op-skills` (11 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `community/Op`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- The Triton backend is a RESERVED stub in Atlas — the official pack supplies the method.
- Apache-2.0 + CC-BY-SA-4.0 — quote with attribution.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- Triton-Ascend codegen is not wired to a real Atlas backend yet (reserved stub).
- Memory-check (mssanitizer) is a distinct sub-skill — run it after perf-opt.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
