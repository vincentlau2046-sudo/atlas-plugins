---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-ut-develop/SKILL.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-ut-develop SKILL.md 抽取入口参数、强制前置步骤、主流程执行规则与 UT 覆盖增强方法论自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# UT 单元测试开发与覆盖率增强方法论

> Ascend C 算子 UT（单元测试）开发通过分析 op_host / op_api / op_kernel 的测试空白，生成或补充 UT 用例并定位未覆盖代码，提升覆盖率并支持生成覆盖率报告。本文是 UT 方法论骨架；ST 见 `st-design.md`，白盒见 `whitebox-design.md`，测试策略选择见 `test-strategy.md`。

## 一、入口参数

| 参数名 | 含义 | 取值约束 | 初值推断 |
|---|---|---|---|
| op_name | 算子名 | 下划线命名法 | 驼峰自动转换，无法推断时询问 |
| repo_type | 仓库类型 | ops-math / ops-nn / ops-transformer / ops-cv / custom | 据工作目录推断 |
| soc_type | 芯片架构 | ascend310p / ascend910b / ascend910_93 / ascend950 | 未提及则全选 |
| test_model | 测试模块 | opapi / ophost / opkernel | 未提及则全选 |
| interactive_mode | 使用模式 | auto / interactive | 默认 auto |

> 格式约定：文档中入口参数用 `${参数名}` 标记，需替换为真实值。

## 二、强制前置步骤（不可跳过）

> 在此前禁止阅读任何 references/ 文档和工作目录文件；子步骤逐一执行，不允许同时或跳步。

### 0.1 发送问卷确认入口参数
据「初值推断」规则获取所有入口参数值（仅简单推断，不读代码/子目录），用 `question` 工具向用户确认（问卷用 `assets/question.json`，推断选项 label 后加「【推荐】」）。

### 0.2 创建 TODO.md
用 `todowrite` 工具创建 Todos（内容用 `assets/todo.json`，不允许修改）。

### 0.3 创建 tmp 目录
```bash
mkdir -p /tmp/cannbot_${op_name}
```
- 入口参数存 `params.json`。
- 所有中间文件存该目录。
- 子 Agent 临时文件也存该目录。

## 三、主流程（Step 1-5）

| 步骤 | 文件 | 说明 |
|---|---|---|
| Step 1 | references/workflow/step1.md | 测试空白分析 |
| Step 2 | references/workflow/step2.md | UT 用例生成/补充 |
| Step 3 | references/workflow/step3.md | 未覆盖代码定位 |
| Step 4 | references/workflow/step4.md | 覆盖率增强 |
| Step 5 | references/workflow/step5.md | 覆盖率报告生成 |

## 四、执行规则

1. **严格顺序执行**：Step 1 → 2 → 3 → ... 不得跳过或乱序。
2. **禁止提前阅读**：执行到某步骤前，绝对禁止阅读该步骤文档。
3. **即时更新进度**：每完成/跳过一子步骤，立即 `todowrite` 标记 `[x]`。
4. **交互模式强制约束**：`interactive_mode == "interactive"` 时，每个询问点必须用 `question` 工具与用户确认，禁止绕过用户自行决策。Step 4.4a 询问是交互模式核心特征。

## 五、UT 覆盖增强目标

- **分析测试空白**：识别 op_host / op_api / op_kernel 中未覆盖的代码路径。
- **生成/补充 UT**：为空白路径生成 UT 用例。
- **定位未覆盖代码**：精确定位未覆盖的代码行/分支。
- **覆盖率报告**：生成覆盖率报告（支持 opapi / ophost / opkernel 三个测试模块）。

> UT 不适用于 ST 测试——ST 走 `st-design.md`（aclnn 接口级 L0/L1/L2）。UT 是模块级（opapi/ophost/opkernel）覆盖率增强。

## 六、test_model 三模块

| 模块 | 范围 | 说明 |
|---|---|---|
| opapi | op_api 层 | 算子 API 接口测试 |
| ophost | op_host 层 | tiling/host 逻辑测试 |
| opkernel | op_kernel 层 | kernel 计算逻辑测试 |

> 未指定 test_model 时默认全选（三模块都做）。

## 关联

- `st-design.md` — ST 系统测试设计（aclnn L0/L1/L2）
- `whitebox-design.md` — 白盒用例生成（路径覆盖）
- `test-strategy.md` — ST vs UT vs whitebox vs golden 选择决策树
