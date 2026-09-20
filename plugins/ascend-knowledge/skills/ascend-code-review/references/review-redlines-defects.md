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
  note: "从 cannbot ascendc-code-review core/methodology.md 抽取红线问题（Host 6 + Kernel SIMT 5）、PR 模式交叉验证与常见缺陷自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# 红线问题与常见算子缺陷

> 红线问题是**必须检查的强制条例**（违反即 FAIL，不走假设检验评分）。本文列 Host 侧 6 条 + Kernel SIMT 5 条红线 + PR 模式交叉验证 + 常见缺陷模式。假设检验方法论见 `review-methodology.md`。

## 一、Host 侧红线（6 条）

Host 侧代码（op_host/ tiling 代码）必须满足：

1. **除法/求余操作必须除零保护**——除数可能为 0 时须 OP_CHECK_IF/assert 非零校验。
2. **数组访问必须越界保护**——下标来自外部输入/计算时须边界判断。
3. **加法/乘法/减法操作必须溢出和减翻保护**——大数运算须检查溢出。
4. **指针操作必须先赋值后访问并进行指针保护**——禁野指针/空指针解引用。
5. **变量使用前必须有效初始化**——禁未初始化变量参与运算。
6. **资源申请/使用/释放必须匹配**——AllocTensor/FreeTensor、EnQue/DeQue、文件/锁开闭配对。

## 二、Kernel 侧 SIMT 红线（5 条）

SIMT kernel（C++ 风格 API 转 C 风格）必须满足：

1. **SIMT kernel 必须将 C++ 风格 API 转换为 C 风格 API**——如 `GetThreadNum` → `blockDim.x`。
2. **`Simt::UintDiv` 必须保留，禁止转换**——UintDiv 是硬件除法，转 C 风格会破坏语义。
3. **变量名不能命名为 `threadIdx`/`blockIdx`/`blockDim`/`gridDim`**——与 C 风格 API 冲突。
4. **头文件 `simt_api/asc_simt.h` 必须在 namespace 外部**——否则编译错。
5. **转换后必须通过编译验证**——AscendCompilerBridge（`python3 setup.py build_ext`）编译通过。

> SIMT kernel 检视前必读 `references/simt-api-analysis.md`（cannbot 源，引用不 vendor）。

## 三、PR 模式交叉验证

判定 FAIL(HIGH) 前，Grep 完整源码确认上游是否已有校验：

| 场景 | 检查内容 | 处理 |
|---|---|---|
| 变量作除数 | grep 非零校验 | 有 → PASS |
| 变量未初始化 | grep 构造函数/Init 赋值 | 有 → PASS |
| 外部输入未校验 | grep TilingData/硬件配置来源 | 是 → PASS |

上游已有校验 → PASS；源码不可用 → LOW +「无法确认上游校验」。

> **校验有效性验证**（关键反模式）：找到上游校验后，必须确认校验保护的变量与当前风险变量是**同一个**（或赋值链可证等价）。反模式：ShapeChecker 校验 `maxActualseq > 0`，但除数是 `sInnerFactor_`（另一赋值路径）→ 校验不覆盖风险变量 → 该证据得分 0。

## 四、常见算子缺陷模式

从红线 + 假设检验证据类型归纳的高频缺陷：

| 缺陷模式 | 红线/证据 | 典型场景 |
|---|---|---|
| 除零 | Host §1 | tiling 计算 `x / dim`，dim 来自 shape 未校验非零 |
| 越界访问 | Host §2 | `tensor[offset]`，offset 来自计算未边界判断 |
| 溢出 | Host §3 | `a * b` 大 shape 累加溢出 |
| 资源不匹配 | Host §6 | AllocTensor 循环内未配对 FreeTensor → 内存泄漏/UB 溢出 |
| 未初始化 | Host §5 | 成员变量未在 Init 赋值直接用 |
| SIMT API 未转 C 风格 | Kernel §1 | `GetThreadNum()` 未转 `blockDim.x` |
| UintDiv 误转 | Kernel §2 | `Simt::UintDiv` 被转 C 风格破坏硬件除法 |
| 变量名冲突 | Kernel §3 | 变量命名 `threadIdx` 与 C 风格 API 冲突 |
| 上下文防御缺失 | 证据 +30% | 风险代码作用域内无防御 |
| 调用链风险 | 证据 +15% | 调用函数内部有风险未查 |
| 数据流风险 | 证据 +15% | 变量来源不明/运算路径不可控 |

## 五、检视输出要求

- 每个 FAIL/SUSPICIOUS 附**代码片段**（≥ 10 行含上下文 + 准确行号 + 问题描述 + 修复建议）。
- 所有风险代码块都应被引用，不能只展示行数。
- 仔细检查风险代码行号是否正确。

## 关联

- `review-methodology.md` — 假设检验 5 步 + 证据评分（红线违规 = +40% 规范违反）
- `review-workflow-routing.md` — 5 workflow 路由 + 侧别识别
- `review-fix-routing.md` — 缺陷发现后 → AscendCodeGen 重生成路由
