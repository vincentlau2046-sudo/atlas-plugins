---
name: cannbot-aiss-tiling-solver
description: "官方 AISS-TilingSolver skill 的 Atlas 策展封装：Ascend C 算子 Tiling 参数自动求解（MatMul/Vector），JSON 输入构造→求解→结果解读与故障排查。触发：不想手动设计 tiling、想自动求解最优 tiling 参数。"
when_to_use: "Use when you want to AUTO-SOLVE tiling parameters for a MatMul/Vector Ascend C operator instead of hand-designing — the official AISS-TilingSolver skill, curated. Read as a heuristic pointer; validate against real run output."
allowed-tools: AscendTilingPlanner, AscendCodeGen
---

# AISS Tiling 自动求解（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-aiss-tiling-solver`** skill-pack (1 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Auto-solve tiling parameters for the operator via the AISS solver and interpret the result, then feed the plan into the Atlas codegen chain.

## Gates（产出须含）

- [ ] solver JSON input constructed (op type + shapes + dtypes)
- [ ] solver run output captured
- [ ] tiling plan fed into AscendCodeGen four-piece
- [ ] plan sanity-checked against UB capacity limits

## Tool catalog（工具面 — route to Atlas tools）

- **AscendTilingPlanner** — return a 3×2 mock preset table (throughput/latency/balanced × 2 plans) — T0 mock liveness signal, NOT a tiling methodology
- **AscendCodeGen** — emit the four-piece scaffold (kernel + pybind binding + setup.py + test) via a pluggable KernelBackend (Ascend C = MVP; TileLang/Triton reserved stubs)

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-aiss-tiling-solver` (1 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/ops`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- AISS is a third-party/academic tool — a heuristic pointer, NOT a fact source; validate with real output.
- CANN OSL v2.0 content is referenced + provenance-pointed, NEVER vendored.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- Do not treat the auto-solved plan as authoritative without a golden-test pass.
- The TilingPlanner Atlas tool is a mock — the real method lives in the official AISS skill.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
