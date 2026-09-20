---
name: cannbot-ops-direct-invoke
description: 官方 CANNBot 直调算子 skill 包（27 技能）的 Atlas 策展封装：API 检索/Tiling 设计/精度调试/性能采集/代码模板/SIMT 最佳实践，路由到 Atlas 算子开发工具链。触发：Ascend C 算子端到端开发（API 检索→tiling→codegen→编译→golden 验证）。
when_to_use: Use when developing an Ascend C direct-invoke operator end-to-end: API lookup, tiling design, codegen, compile, golden verification, SIMT best practices. Curation over the official CANNBot ops-direct-invoke pack.
allowed-tools: AscendSpecParser, AscendTilingPlanner, AscendCodeGen, AscendCompilerBridge, AscendGoldenTest, AscendDiagnoser
---

# Ascend C 直调算子开发（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-ops-direct-invoke-skills`** skill-pack (27 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Drive an Ascend C direct-invoke operator from spec to a verified four-piece, using the official pack as knowledge and the Atlas tools as execution.

## Gates（产出须含）

- [ ] operator spec parsed (shape/dtype/attrs)
- [ ] four-piece scaffold present (kernel+binding+setup.py+test)
- [ ] bisheng compile evidence returned
- [ ] golden (numpy vs NPU) correctness gate passed

## Tool catalog（工具面 — route to Atlas tools）

- **AscendSpecParser** — parse an operator spec (shape/dtype/attributes) into a structured OperatorSpec — entry point of the operator-dev chain
- **AscendTilingPlanner** — return a 3×2 mock preset table (throughput/latency/balanced × 2 plans) — T0 mock liveness signal, NOT a tiling methodology
- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)
- **AscendCompilerBridge** — compile via bisheng (`python3 setup.py build_ext`) with NPU arch probe (910→dav-2201 / 950→dav-3510) — returns compile evidence
- **AscendGoldenTest** — run numpy reference vs NPU — the correctness gate (NOT a simulator cycle)
- **AscendDiagnoser** — collect + return fault EVIDENCE (log/error fragments); it never emits a next_tool — you decide from the evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-ops-direct-invoke-skills` (27 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/ops`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- Route execution to the Atlas tools below; treat the official pack as knowledge, not as executable steps.
- CANN OSL v2.0 content is referenced + provenance-pointed, NEVER vendored.
- GoldenTest is the correctness gate — do not substitute a simulator.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- TilingPlanner returns a mock preset table, not a tiling methodology — read the official tiling-design skill for the real method.
- Direct-invoke vs registry-invoke have distinct templates; pick the one matching the target calling convention.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
