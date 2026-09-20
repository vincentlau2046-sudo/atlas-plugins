---
name: ascend-code-review
description: Ascend C 算子代码检视技能。覆盖假设检验驱动逐条检视（5 步假设建立→证据收集评分→有效性校验→决策判断）、置信度分级（HIGH/MED/LOW）、5 workflow 路由（file/quick/pr/design-consistency/extend）、红线问题（Host 6 + Kernel SIMT 5）、PR 模式交叉验证、常见算子缺陷模式、审完发现→修复路由。触发关键词：代码检视、代码审查、review、检视 PR、快速检视、设计一致性、红线、除零、越界、溢出、SIMT。
when_to_use: Use when the user asks to review/audit Ascend C operator code, review a PR, check for code issues, or verify design-implementation consistency. The agent identifies the code side (Host/Kernel/SIMT), reads the applicable rules from cannbot references, runs the hypothesis-testing methodology per rule, checks red-lines, and produces a defect report with evidence + fix suggestions (routing structural defects to AscendCodeGen for regeneration). No fixed step order.
allowed-tools: AscendCodeGen
---

# Ascend C 算子代码检视

Drive a hypothesis-testing code review for an Ascend C operator. You identify the code side (Host/Kernel/SIMT), read the applicable coding rules from cannbot references (referenced, not vendored), run the 5-step hypothesis test per rule (evidence scoring → confidence → decision), check the mandatory red-lines, and produce a defect report with code-fragment evidence + fix suggestions. Structural defects route to AscendCodeGen for regeneration; parametric defects use base Read/Edit. There is no fixed step order — you decide which workflow and rules apply based on the input.

## Goal

Produce a code-review defect report: code-side identification + applicable rules + hypothesis-tested defects (with confidence level + evidence) + red-line violations + fix suggestions (routing to AscendCodeGen or Read/Edit).

## Gates（产出须含）

- [ ] **代码侧别识别**：判 Host 侧（op_host/tiling）/ Kernel 侧（op_kernel/.asc）/ SIMT Kernel，据侧别提适用条例（Host 红线 / Kernel API 最佳实践 / SIMT 红线）.
- [ ] **workflow 路由**：据输入类型选 workflow（file-review 全量 / quick-review 定向 / pr-review diff 范围 / design-consistency 设计核对 / extend 扩展），附判定依据.
- [ ] **假设检验证据**：对每条条例执行 5 步假设检验（`review-methodology.md`），附正向/负向证据 + 分值 + 自信值。负向证据（防御存在/上游校验）必须附可验证代码引用（`[文件]:[行] [代码]`），否则得分 0.
- [ ] **置信度分级**：每个缺陷标 HIGH(80%+)/MED(70-80%)/LOW(<70%)，附分级依据。LOW 不判违规.
- [ ] **红线检查**：对照 `review-redlines-defects.md` Host 6 + Kernel SIMT 5 红线逐条检查，违反即 FAIL（不走评分）.
- [ ] **代码片段**：每个 FAIL/SUSPICIOUS 附 ≥ 10 行代码片段 + 准确行号 + 问题描述 + 修复建议.
- [ ] **修复路由**：据缺陷类型给修复方向（参数级 → Read/Edit；结构性 → AscendCodeGen 重生成；SIMT → Read/Edit + 编译验证），附 `review-fix-routing.md` 依据.

## Tool catalog

- **AscendCodeGen** (T0 Tool) — 结构性缺陷审完后重生成四件套（kernel .asc + pybind + setup.py + golden test）。提供 spec + output_dir。重生成后须 AscendCompilerBridge 重编译 + AscendGoldenTest 验证（非本 skill allowedTools，agent 跨 skill 调用或基座 coding）。`mocked: true` = liveness.
- **基座 coding 工具** (Shape B，非 Ascend 专属 Tool) — agent 用基座 Read/Grep/LSP 读码与检视、Read/Edit 定点改参数级缺陷。检视的核心工具是基座 Read/Grep（非 Ascend Tool）.
- **cannbot 编码规范** (Shape B，引用不 vendor) — 安全编码/API 最佳实践/性能/TOPK 条例在 cannbot references/*.md，agent 用基座 Read 读条款，不 vendor 文本进本 skill.

**references**（按需读，progressive disclosure）:

- **references/review-methodology.md** (T1) — 假设检验 5 步（代码段识别→假设建立 H0安全/H1风险→证据收集评分 正向+40/+30/+20/+15/+15/+10 负向-20/-15/-50→有效性校验→决策 ≥70%判违规）+ 负向证据强制引用 + 置信度分级（HIGH/MED/LOW）+ 条款边界检查 + 代码片段格式。方法论骨架主源。读此做逐条检视。(cannbot@c24e8b5, CANN-OSL-2.0, verified)
- **references/review-workflow-routing.md** (T1) — 5 workflow 路由表（file-review/quick-review/pr-review/design-consistency/extend）+ 执行规则（严格阶段顺序/禁提前 Read 未执行阶段）+ 侧别识别（Host/Kernel/SIMT）+ 资源索引（workflows/steps/core/references）。workflow 路由主源。读此选 workflow 与侧别。(cannbot@c24e8b5, verified)
- **references/review-redlines-defects.md** (T1) — 红线问题（Host 6：除零/越界/溢出/指针/初始化/资源匹配 + Kernel SIMT 5：C 风格 API 转换/UintDiv 保留/变量名禁/头文件位置/编译验证）+ PR 模式交叉验证 + 校验有效性验证反模式 + 常见算子缺陷模式表。红线与缺陷主源。读此查红线与缺陷模式。(cannbot@c24e8b5, verified)
- **references/review-fix-routing.md** (T3) — 审完发现→修复路由决策树（参数级→Read/Edit / 结构性→AscendCodeGen 重生成 / SIMT→Read/Edit+编译验证）+ 3 协作链 + 修复后必走验证（CompilerBridge 重编译→GoldenTest 正确性门→重检视）。**启发式综合**（confidence:heuristic），工具选择参考。读此选修复路径。(composite, heuristic)

Read references via their relative path in this skill's base directory (the base directory path is injected above). Read on demand — do not load all at once.

## Rules

- **先识侧别再检视**：判 Host/Kernel/SIMT 据侧别提适用条例。Host 走 Host 红线，Kernel 走 API 最佳实践，SIMT 走 SIMT 红线.
- **假设检验非主观扫读**：对每条条例执行 5 步假设检验，用证据评分得自信值，≥ 70% 判违规。不凭感觉下结论.
- **负向证据必须附代码引用**：声称「防御存在」/「上游校验」必须附 `[文件]:[行] [代码]`，找不到校验代码 → 得分 0，不得虚构「上游已校验」.
- **校验有效性验证**：上游校验保护的变量必须与风险变量是同一个（或赋值链可证等价）。ShapeChecker 校验 A 但除数是 B → 不覆盖 → 得分 0.
- **红线必查**：Host 6 + Kernel SIMT 5 红线违反即 FAIL，不走假设检验评分.
- **条款边界不扩展**：只查条款范围内的问题，代码模式不在条款范围 → PASS。禁把条款当万能筐.
- **编码规范引用不 vendor**：安全/API/性能/TOPK 条例在 cannbot references/*.md，agent 用基座 Read 读，不搬进本 skill.
- **工具返证据非决策**：AscendCodeGen 重生成是修复执行，检视本身返缺陷证据 + 修复建议，不返回 `next_tool`.
- **当工具返 `mocked: true`**：视作 liveness 信号非正确性证明，须在报告说明.
- **许可**：cannbot refs = CANN OSL v2.0（non-sublicensable，引用+溯源不 vendor 文本，含编码规范条例只引用不 vendor）；references 均自撰验真文本（抽取事实重写），非逐字 copy.

## Gotchas

- **负向证据偷懒**：找到一条模糊防御就大幅扣分是反模式——负向证据单项分值低，须多条叠加（防御+上游校验+编译期常量）才能降至安全区间.
- **校验变量错配**：ShapeChecker 校验 `maxActualseq > 0` 但除数是 `sInnerFactor_`（另一赋值路径）→ 校验不覆盖 → 得分 0，勿当有效防御.
- **「来源=TilingData」≠「已校验」**：变量溯源定位到 TilingData 来源，但不等于已校验——须进一步 Grep Tiling 代码确认校验语句.
- **SIMT API 未转 C 风格**：`GetThreadNum()` 须转 `blockDim.x`，但 `Simt::UintDiv` 必须保留禁转.
- **变量名冲突**：变量命名 `threadIdx`/`blockIdx`/`blockDim`/`gridDim` 与 C 风格 API 冲突——红线.
- **参数级缺陷过度重生成**：加一个 assert 能修的缺陷无需 AscendCodeGen 重生成——Read/Edit 定点改.
- **改后跳过 GoldenTest**：修复可能破坏正确性——改后必跑 AscendGoldenTest（跨 skill 或基座调用）.
- **凭记忆推测 API**：Kernel API 用法必须查官方文档（`/ascendc-docs-search`），禁止凭记忆——常见误判源.
- **行号不准**：风险代码行号必须准确，所有风险代码块都应被引用，不能只展示行数.
