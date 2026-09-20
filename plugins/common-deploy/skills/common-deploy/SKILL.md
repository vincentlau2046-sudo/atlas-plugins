---
name: common-deploy
description: 昇腾 NPU 通用部署 skill 包（3 技能）的 Atlas 策展封装：OM 部署器/OM Pipeline 适配器/ONNX-ATC 推理 Pipeline。触发：模型部署、推理服务构建。
when_to_use: Use for generic Ascend model deployment: OM deployer, OM pipeline adapter, ONNX→ATC inference pipeline. Curation over the official Common deploy pack.
allowed-tools: AscendModelConverter, AscendOnnxOptimizer, AscendInferValidator, AscendDataPrepTool
---

# 昇腾通用模型部署（官方策展）

Curated **Atlas curation wrapper** for the official **`common-deploy-skills`** skill-pack (3 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Build an NPU inference pipeline (ONNX→optimize→atc→.om→validate) using the official method + the Atlas deploy tools.

## Gates（产出须含）

- [ ] ONNX prepared + optimized
- [ ] atc →.om conversion evidence
- [ ] pipeline deployed
- [ ] inference validated (msquickcmp)

## Tool catalog（工具面 — route to Atlas tools）

- **AscendModelConverter** — atc conversion (the →.om chokepoint) — returns conversion evidence
- **AscendOnnxOptimizer** — auto_optimizer graph optimization — returns optimization evidence
- **AscendInferValidator** — msame run + msquickcmp compare — inference-correctness evidence
- **AscendDataPrepTool** — img2bin preprocessing data prep — returns preprocessing evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `common-deploy-skills` (3 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `official/Common`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- Pipeline order: DataPrep → OnnxOptimizer → ModelConverter(atc) → InferValidator.
- Apache-2.0 + CC-BY-SA-4.0 — quote with attribution.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- atc is the →.om chokepoint — a conversion failure blocks the whole pipeline.
- msquickcmp compare must be against the reference model's outputs, not a golden constant.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
