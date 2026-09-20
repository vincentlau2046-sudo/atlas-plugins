---
name: cannbot-infra-skills
description: 官方 CANNBot 基础设施 skill 包（5 技能）的 Atlas 策展封装：Skill 审查/GitCode Issue 生成与处理/PR 处理/GitCode 工具集 + 故障采集/错误分类/性能分析路由。触发：NPU 问题定位、故障采集与分诊、CANNBot 工程问题处理。
when_to_use: Use for NPU fault triage + CANNBot infra workflow: fault collection, error classification, profiling analysis, and GitCode issue/PR handling. Curation over the official CANNBot infra pack.
allowed-tools: AscendFaultCollector, AscendErrorClassifier, AscendProfileAnalyzer
---

# CANNBot 基础设施/问题定位（官方策展）

Curated **Atlas curation wrapper** for the official **`cannbot-infra-skills`** skill-pack (5 skills).
This wrapper adds the Atlas governance layers on top of the official knowledge:
a **provenance pointer** (authoritative source, never vendored) + a **tool-routing layer**
(execution routes to the Atlas 16 Ascend tools). Read the official pack for *method*;
use the Atlas tools for *evidence*. There is no fixed step order — you decide what to read
and which tool to call from the current goal + evidence.

## Goal

Triage an NPU problem (fault → classify → profile) and route the CANNBot engineering workflow, using the Atlas fault/perf tools for evidence.

## Gates（产出须含）

- [ ] fault scene captured (npucollector)
- [ ] error classified (msaicerr scenario)
- [ ] profiling bottleneck evidence
- [ ] actionable triage conclusion

## Tool catalog（工具面 — route to Atlas tools）

- **AscendFaultCollector** — npucollector fault dump — capture a fault scene for offline triage
- **AscendErrorClassifier** — msaicerr error classification (6 canonical error scenarios)
- **AscendProfileAnalyzer** — ada-pa profiling analysis — bottleneck evidence, not a decision

Each tool returns **evidence, not a decision** — you decide the next action from the evidence.

## 溯源（provenance — 权威来源，非 vendor）

- Official pack: `cannbot-infra-skills` (5 skills)
- Source of truth: `cannbot-skills` @ `c24e8b5b` · path `official/CANNBot/infra`
- License: CANN OSL v2.0 (non-sublicensable) — **referenced + provenance-pointed, NEVER vendored**.
- Full provenance block: see `references/provenance.md`.

## Rules

- Fault tools return EVIDENCE, not a fix — you decide the next action from evidence.
- CANN OSL v2.0 content is referenced + provenance-pointed, NEVER vendored.

- When a tool returns `mocked: true`, treat its output as a liveness signal, NOT proof of correctness — say so in your report.

## Gotchas

- msaicerr has 6 canonical scenarios — classify into one before deep-diving.
- npucollector capture must happen on the failing node before state is lost.

Read `references/provenance.md` for the full provenance block (tier / confidence / pinned SHA / license).
Read the official pack's SKILL.md files for the authoritative method (via the provenance pointer, not a local copy).
