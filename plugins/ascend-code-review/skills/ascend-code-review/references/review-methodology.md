---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-code-review/core/methodology.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-code-review core/methodology.md 抽取假设检验流程、证据评分表、置信度分级、条款边界检查与代码片段格式自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# 代码检视方法论（假设检验驱动）

> Ascend C 算子代码检视用**假设检验**驱动逐条条例检查，非主观扫读。对每条编码规范条例执行 5 步假设检验，用正向/负向证据累加得自信值，≥ 70% 判违规。本文是检视的方法论骨架；红线问题见 `review-redlines-defects.md`，workflow 路由见 `review-workflow-routing.md`，审完修复路由见 `review-fix-routing.md`。

## 一、假设检验 5 步

### 步骤 1：代码段识别

将代码划分为独立代码段（函数、语句块、逻辑单元），逐段检验。

### 步骤 2：假设建立

- **原假设 H0**：该代码段安全。
- **备择假设 H1**：该代码段存在风险。
- 自信值初始 0%。

### 步骤 3：证据收集与评估

**正向证据**（增加置信度）：

| 证据类型 | 分值 | 分析动作 |
|---|---|---|
| 规范违反 | +40% | 对照规范条款识别违规点 |
| 上下文防御缺失 | +30% | 检查作用域内是否有防御代码 |
| PR 归属 | +20% | 仅 PR 模式：问题代码在 diff 变更范围内 |
| 调用链风险 | +15% | LSP/Grep 分析调用函数内部逻辑 |
| 数据流风险 | +15% | 变量来源不明确、运算路径不可控 |
| 领域关联 | +10% | 代码命中规则文件的领域触发特征 |

**负向证据**（降低置信度，单项分值低，须多条叠加才能显著降级）：

| 证据类型 | 分值 | 分析动作 |
|---|---|---|
| 防御存在 | -20% | 作用域内有零值检查/边界判断/非空校验 |
| 上游校验 | -15% | 作用域外已有 OP_CHECK_IF/assert，且校验变量与风险变量相同 |
| 范围外 | -50% | PR 模式：问题代码不在 diff 变更范围内 |

> **设计原则**：负向证据单项分值低于正向，防 AI 偷懒——找到一条模糊防御就大幅扣分。真正充分防御需**多条负向证据叠加**（防御存在 + 上游校验 + 编译期常量）才能降至安全区间。单条 -15%/-20% 不应单独决定判定。

### 步骤 4：证据有效性校验

满足任一即排除误报：
- 负向证据累加 ≤ -50% → 风险降级，不进入 FAIL。
- 上下文可证明不可能触发风险 → 排除。

### 步骤 5：决策判断

- 自信值 = Σ 正向证据 + Σ 负向证据（负向为负数）。
- 自信值 ≥ 70% → 判定违规。

## 二、负向证据强制引用

每条「防御存在」和「上游校验」证据**必须附可验证代码引用**，否则得分 0：

```
格式: [文件路径]:[行号] [具体代码行内容]
示例: fia_tiling.cpp:90 OP_CHECK_IF(aicNum_ == 0, return GRAPH_FAILED)
```

- 声称 TilingData 已校验 → 必须 Grep Tiling 代码找 OP_CHECK_IF/assert/条件判断。
- 声称硬件配置保证 → 引用 GetCoreNumAic() 等 API 或芯片参数表。
- 声称编译期常量 → 引用 constexpr 声明行。
- **找不到校验代码 → 得分 0，不得虚构「上游已校验」**。
- **校验有效性验证**：找到上游校验后，必须确认校验保护的变量与当前风险变量是**同一个**（或赋值链可证等价）。反模式：ShapeChecker 校验 `maxActualseq > 0`，但除数是 `sInnerFactor_`（另一赋值路径）→ 校验不覆盖 → 得分 0。

## 三、置信度分级

| 等级 | 区间 | 含义 | 分类 |
|---|---|---|---|
| HIGH | 80%+ | 明确违规证据 | 发现问题 |
| MED | 70-80% | 可疑迹象需人工确认 | 需关注 |
| LOW | <70% | 证据不足，不判定违规 | 疑似 |

## 四、条款边界检查

每条条例有明确适用范围（见条例描述和示例代码）。**只检查条款本身范围内的问题，禁止将条款当万能筐扩展到不相关代码模式**。代码模式不在当前条款适用范围内 → PASS。

输出前自检：每个 FAIL/SUSPICIOUS 必须能对应到所分配条款的问题描述或示例代码中的具体模式。对不上号 → 撤回改 PASS。

## 五、代码片段格式

FAIL/SUSPICIOUS 结果必须附代码片段：
- 至少 10 行含上下文。
- 标注准确行号。
- 附问题描述和修复建议。

## 六、分析要求

- 用 LSP 获取符号定义，用 Grep 查依赖关系。
- 风险代码必须检查是否在当前文件作用域内其他位置防御。
- 遇函数调用必须查看函数内部逻辑综合判断。
- 遇风险结构体/成员变量必须查看定义和运算过程。
- 变量溯源定位声明位置，但**「来源类型=TilingData」≠「已校验」**——须进一步 Grep Tiling 代码确认校验语句。
- Kernel 代码涉及 API 用法时，必须查官方文档（`/ascendc-docs-search`），禁止凭记忆推测。

## 关联

- `review-redlines-defects.md` — 红线问题（Host 6 + Kernel SIMT 5）+ PR 交叉验证
- `review-workflow-routing.md` — 5 workflow 路由 + 执行规则
- `review-fix-routing.md` — 审完发现 → AscendCodeGen 重生成路由
