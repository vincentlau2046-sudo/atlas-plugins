---
name: cannbot-tilelang-op
description: 官方 CANNBot TileLang 算子 skill 包（9 技能）的 Atlas 策展封装：环境检查/子模块拉取/算子设计/开发/测试设计/API 最佳实践/编程模式指南/性能优化/代码审查。触发：TileLang 算子端到端开发。
when_to_use: Use when developing a TileLang operator end-to-end — env check, submodule pull, design/dev, test design, API best practices, programming-model guide, perf-opt, review. Curation over the official CANNBot TileLang pack.
allowed-tools: AscendCodeGen, AscendCompilerBridge, AscendGoldenTest
---

# TileLang 算子开发编排（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-tilelang-op-orchestrator-skills`** skill-pack (9 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Develop a TileLang operator end-to-end, using the official pack for method and the Atlas tools for codegen/compile/verify.

## Gates（产出须含）

- [ ] env + submodule ready
- [ ] op design + dev complete
- [ ] test design done
- [ ] golden correctness evidence

## Tool catalog（工具面 — route to Atlas tools）

- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendCompilerBridge** — compile via bisheng (`python3 setup.py build_ext`) with NPU arch probe (910→dav-2201 / 950→dav-3510) — returns compile evidence
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-tilelang-op-orchestrator-skills` (9 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/ops-lab/tilelang/skills`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- The TileLang backend is a RESERVED stub in Atlas (Ascend C is the MVP) — the official pack supplies the TileLang method.
- CANN OSL v2.0 content is referenced + provenance-pointed, NEVER vendored.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- TileLang dev needs its submodule pulled (tilelang-submodule-pull sub-skill) — env-check first.
- Like Triton, the Atlas TileLang backend is a reserved stub today.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
