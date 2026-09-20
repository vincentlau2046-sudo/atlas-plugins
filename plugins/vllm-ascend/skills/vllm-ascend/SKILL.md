---
name: vllm-ascend
description: "vLLM-Ascend 推理部署与测试 skill 包（3 技能）的 Atlas 策展封装：vLLM Ascend 服务部署/FAQ 生成/测试失败分析。触发：vLLM 在昇腾 NPU 上的部署与问题排查。"
when_to_use: "Use for deploying + troubleshooting vLLM on Ascend NPU: service deploy, FAQ generation, test-failure analysis. Curation over the official vllm-ascend pack."
allowed-tools: AscendInferValidator, AscendModelConverter, AscendRealHWBridge
---

# vLLM-Ascend 推理部署（官方策展）

Curated **Atlas curation wrapper** for the official **`vllm-ascend-skills`** skill-pack (3 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Deploy a vLLM-Ascend inference service and triage test failures, using the official pack for method and the Atlas tools for verify/evidence.

## Gates（产出须含）

- [ ] vLLM-Ascend service deployed
- [ ] inference validated (msame+msquickcmp)
- [ ] test failures triaged with root-cause evidence

## Tool catalog（工具面 — route to Atlas tools）

- **AscendInferValidator** — msame run + msquickcmp compare — inference-correctness evidence
- **AscendModelConverter** — atc conversion (the →.om chokepoint) — returns conversion evidence
- **AscendRealHWBridge** — query real NPU via npu-smi / msprof — hardware-liveness evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `vllm-ascend-skills` (3 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `official/vllm-ascend`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- Validate the deployed service with the Atlas InferValidator, not just a smoke test.
- Apache-2.0 + CC-BY-SA-4.0 — quote with attribution.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- vLLM version ↔ CANN ↔ NPU arch compatibility is the top failure cause.
- In mock mode InferValidator returns a liveness signal, not a real inference result.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
