---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-code-review/SKILL.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-code-review SKILL.md 抽取 5 workflow 路由表、执行规则与资源索引自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# 代码检视 workflow 路由

> 据用户意图和输入类型选 workflow，严格按阶段顺序执行。本文是 workflow 路由 + 执行规则；假设检验方法论见 `review-methodology.md`，红线见 `review-redlines-defects.md`。

## 一、workflow 路由表

| 触发条件 | workflow | 场景 |
|---|---|---|
| 全量检视代码、审核代码、代码审查、帮我检视 xxx | file-review | 整文件逐条例检视 |
| 检查是否有、有没有问题、快速检视、有什么风险、是否存在.*问题 | quick-review | 定向快速检视（只查风险点） |
| 全量检视 PR、全面审核 PR、pr #、pull request、PR # | pr-review | PR diff 范围内检视（大 PR 自动切换） |
| 设计实现一致性、设计一致性检查、对照 DESIGN.md | design-consistency | 实现与设计文档一致性核对 |
| 扩展能力、新增规则、新增场景、怎么加规则、扩展检视、接入新规范 | extend | 新增检视条例/规则 |

## 二、执行规则

1. **Read 对应 workflow 文件**，获取编排定义（阶段顺序、上下文传递、任务追踪）。
2. **严格按 workflow 的阶段顺序执行**，禁止跳步。
3. 每个阶段开始时 **Read 对应 steps/ 文件**，执行完成后再 Read 下一个。
4. **禁止提前 Read 未执行阶段的 step 文件**（上下文隔离——防上下文拥塞）。

## 三、自动识别代码侧别

检视前自动识别代码侧别（Host 侧 / Kernel 侧 / SIMT Kernel），据侧别提取适用条例：
- **Host 侧**（op_host/ tiling 代码）：适用 Host 红线（除零/越界/溢出/指针/初始化/资源匹配，见 `review-redlines-defects.md`）。
- **Kernel 侧**（op_kernel/ .asc 代码）：适用 Kernel API 最佳实践 + 性能条例；SIMT kernel 适用 SIMT 红线（C 风格 API 转换/UintDiv 保留/变量名禁/头文件位置/编译验证）。

## 四、资源索引

| 资源 | 路径 | 说明 |
|---|---|---|
| 工作流编排 | workflows/ | 阶段顺序、上下文传递、任务追踪 |
| 执行步骤 | steps/ | 每步完整操作指令 |
| 检视方法论 | core/methodology.md | 假设检验流程、置信度标准、红线（→ `review-methodology.md`） |
| 编码规范 | references/*.md | 安全编码、API 最佳实践、性能、TOPK 等规则文档（cannbot 源，引用不 vendor） |
| SIMT API 分析 | references/simt-api-analysis.md | SIMT kernel 检视前必读 |
| 常用算子仓 | ops-transformer / ops-math / ops-nn / ops-cv | gitcode.com/cann/{repo}，PR 检视时从完整 URL 推断 repo 名 |

> **编码规范条例**（安全编码/API/性能/TOPK）是 cannbot references/*.md 的内容——AtlasHarness **引用不 vendor**：检视时 agent 用基座 Read/Grep 读 cannbot 规范条款，不把规范文本搬进本 skill。本 skill 提供**方法论 + 红线 + 路由**，条例本身指向 cannbot 源。

## 五、AtlasHarness 集成层差异

cannbot code-review 是**纯知识层**（方法论 + 条例 + workflow 编排）。AtlasHarness 补的**集成层**：
- 检视发现缺陷后 → `review-fix-routing.md` 路由到 **AscendCodeGen** 重生成（cannbot 无 CLI 工具包装）。
- 检视用基座 Read/Grep/LSP（base coding 工具，非 Ascend 专属 Tool）。

## 关联

- `review-methodology.md` — 假设检验 5 步 + 证据评分 + 置信度分级
- `review-redlines-defects.md` — 红线问题（Host 6 + Kernel SIMT 5）
- `review-fix-routing.md` — 审完发现 → AscendCodeGen 重生成路由
