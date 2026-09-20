---
name: cannbot-cuda2ascend-simt
description: 官方 CANNBot CUDA→Ascend SIMT 迁移 skill 的 Atlas 策展封装：CUDA 到 Ascend C SIMT 编程模型的代码迁移（API 映射/语法规则/约束校验）。触发：把 CUDA kernel 迁移到 Ascend C SIMT。
when_to_use: Use when migrating a CUDA kernel to the Ascend C SIMT programming model — API mapping, grammar rules, constraint checks. Curation over the official CANNBot cuda2ascend-simt skill.
allowed-tools: AscendCodeGen, AscendCompilerBridge, AscendGoldenTest
---

# CUDA→Ascend SIMT 迁移（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-cuda2ascend-simt-skills`** skill-pack (1 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Migrate a CUDA kernel to Ascend C SIMT with API mapping + constraint checks, then compile + golden-verify via the Atlas tools.

## Gates（产出须含）

- [ ] CUDA→SIMT API mapping documented
- [ ] grammar/constraint checks passed
- [ ] four-piece via AscendCodeGen
- [ ] compile + golden evidence

## Tool catalog（工具面 — route to Atlas tools）

- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendCompilerBridge** — compile via bisheng (`python3 setup.py build_ext`) with NPU arch probe (910→dav-2201 / 950→dav-3510) — returns compile evidence
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-cuda2ascend-simt-skills` (1 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/ops-lab`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- SIMT (≠SIMD) — the SIMT tiling reference applies (core-split + thread count, DCache≥32KB).
- CANN OSL v2.0 content is referenced + provenance-pointed, NEVER vendored.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- Not all CUDA semantics map 1:1 to SIMT — constraint-check before codegen.
- Migrated kernels still need a golden-test pass; a clean compile is not proof of correctness.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
