---
name: common-migration
description: "昇腾 NPU 通用模型迁移 skill 包（5 技能）的 Atlas 策展封装：推理仓库智能问答/ATC 模型转换全流程/msverl 回归分诊/NPU 适配审查/PyTorch 模型 NPU 迁移。触发：模型迁移到 NPU、GPU→NPU 适配。"
when_to_use: "Use for generic model migration to NPU: inference-repo Q&A, ATC conversion, msverl regression triage, NPU-adapter review, PyTorch→NPU migration. Curation over the official Common migration pack."
allowed-tools: AscendModelConverter, AscendInferValidator
---

# 昇腾通用模型迁移（官方策展）

Curated **Atlas curation wrapper** for the official **`common-migration-skills`** skill-pack (5 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Migrate a model (esp. PyTorch) to NPU, using the official pack for method and the Atlas converter/validator for the →.om + verify stages.

## Gates（产出须含）

- [ ] migration plan (GPU→NPU) documented
- [ ] atc conversion evidence
- [ ] NPU-adapter review passed
- [ ] inference validated

## Tool catalog（工具面 — route to Atlas tools）

- **AscendModelConverter** — atc conversion (the →.om chokepoint) — returns conversion evidence
- **AscendInferValidator** — msame run + msquickcmp compare — inference-correctness evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `common-migration-skills` (5 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `official/Common`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- GPU→NPU migration is mostly about the atc chokepoint + operator coverage gaps.
- Apache-2.0 + CC-BY-SA-4.0 — quote with attribution.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- Operator-coverage gaps surface at atc — triage before blaming the conversion flags.
- PyTorch→ONNX is torch.onnx.export (not atc); atc only does ONNX→.om.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
