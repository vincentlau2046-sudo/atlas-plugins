---
name: common-infra-skills
description: "昇腾 NPU 通用基础设施 skill 包（6 技能）的 Atlas 策展封装：Docker 容器创建/驱动固件安装/CANN 全套组件安装/算子环境配置/SwanLab 追踪/npu-smi 设备管理。触发：昇腾 NPU 开发环境搭建与运维、设备状态检查。"
when_to_use: "Use for Ascend NPU environment setup + ops: Docker, driver/firmware install, CANN install, operator-env config, SwanLab tracking, npu-smi device management. Curation over the official Common infra pack."
allowed-tools: AscendRealHWBridge
---

# 昇腾通用基础设施/环境（官方策展）

Curated **Atlas curation wrapper** for the official **`common-infra-skills`** skill-pack (6 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Stand up / verify an Ascend NPU dev environment and check device state, using the official pack for install method and the Atlas RealHWBridge for live device evidence.

## Gates（产出须含）

- [ ] target env (driver+CANN) state captured
- [ ] device state via npu-smi (RealHWBridge)
- [ ] operator env configured
- [ ] tracked (SwanLab) if applicable

## Tool catalog（工具面 — route to Atlas tools）

- **AscendRealHWBridge** — query real NPU via npu-smi / msprof — hardware-liveness evidence

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `common-infra-skills` (6 skills)
- Source of truth: `agent-skills` @ `d4504945` · path `official/Common`
- License: Apache-2.0 (code) + CC-BY-SA-4.0 (docs) — **quote with attribution**; prefer the Atlas tools for execution.
- Full provenance block: see `references/provenance.md`.

## Rules

- Apache-2.0 + CC-BY-SA-4.0 — quote with attribution; prefer the Atlas RealHWBridge for live device reads.
- Install steps come from the official pack; verification comes from the Atlas tool.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- npu-smi reads are live hardware — in mock mode the RealHWBridge returns a liveness signal, not real device state.
- Version pinning (driver ↔ CANN ↔ firmware) is the usual failure mode — check compatibility first.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
