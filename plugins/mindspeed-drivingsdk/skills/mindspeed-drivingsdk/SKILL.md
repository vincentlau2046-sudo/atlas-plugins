---
name: mindspeed-drivingsdk
description: MindSpeed 自驾 SDK 模型迁移 skill 包（14 技能）的 Atlas 策展封装：模型代码迁移/NPU 训练/SSH 远程开发套件/MMLab 安装套件。触发：自驾（VLA）模型 NPU 适配迁移。
when_to_use: Use for autonomous-driving (VLA) model NPU migration: model code migration, NPU training, SSH remote dev, MMLab install suites. Curation over the official MindSpeed drivingsdk pack.
allowed-tools: AscendModelConverter, AscendInferValidator
---

# MindSpeed 自驾 SDK 模型迁移（官方策展）

Curated **Atlas curation wrapper** for the official **`mindspeed-drivingsdk-skills`** skill-pack (14 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Migrate a driving/VLA model to NPU, using the official pack for the migration method and the Atlas converter/validator for the →.om + inference stages.

## Gates（产出须含）

- [ ] model code migrated
- [ ] atc conversion (→.om) evidence
- [ ] inference validated
- [ ] training/deploy target reached

## Tool catalog（工具面 — route to Atlas tools）

- **AscendModelConverter** — atc conversion (the →.om chokepoint) — returns conversion evidence
- **AscendInferValidator** — msame run + msquickcmp compare — inference-correctness evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `mindspeed-drivingsdk-skills` (14 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `official/MindSpeed/drivingsdk-ascend-model-migration`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- The →.om chokepoint is atc (AscendModelConverter) — the whole migration hinges on it.
- Apache-2.0 + CC-BY-SA-4.0 — quote with attribution.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- 14 sub-skills — the SSH-remote + MMLab suites are orthogonal to the model-migration core; scope carefully.
- atc does NOT do PyTorch→ONNX (that's torch.onnx.export) — don't route ONNX export here.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
