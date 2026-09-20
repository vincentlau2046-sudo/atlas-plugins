---
tier: T1
confidence: verified
source-of-truth:
  repo: cann-learning-hub
  sha: d59ef392b0b6afc16e90c1c7a7effbdd41415291
  path: tutorials/ascendc_operator_development/03_intermediate_vector_operator_development/03.04_generalized_tiling_design.ipynb
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: self-authored
  ref: https://gitcode.com/cann/cann-learning-hub@d59ef392
  note: "从 cann-learning-hub 泛化 Tiling 设计教程抽取设计原则/切分场景/示例自撰表述；CANN OSL v2.0 field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Ascend C 算子 Tiling 设计方法论

> 本文档是 Tiling 设计的**方法论主源**（T1，经 cann-learning-hub 官方教程验真）。设计任何 Ascend C 算子 tiling 时先读本文，再按算子类别查 `algorithm-categories.md` 和对应的 `<category>-tiling.md`。

## 一、Tiling 概念

Local Memory（Unified Buffer, UB）通常无法容纳算子的全部输入输出，需分块搬运、计算、搬出，循环直至完成。这个数据切分与分块计算的过程称为 **Tiling**。

- **Tiling 块**：每次搬运的那一部分数据块。
- **Tiling 算法**（Tiling 策略）：根据输入形状确定搬入基本块大小的算法。
- **Tiling 函数**（Tiling Function）：实现 Tiling 算法的函数，一般定义在 Host 侧 tiling 头文件中。

> **职责分层**：Kernel 侧代码决定运算逻辑，Host 侧 Tiling 实现决定数据分块策略。泛化算子（支持任意合法 shape/dtype/处理器型号）的关键是泛化 Tiling 开发。

## 二、三大设计原则（官方教程 3.1-3.3）

### 2.1 内存对齐原则
AI Core 的 Unified Buffer 要求数据空间 **32 字节对齐**。
- 输入数据长度不满足 32B 对齐时，**向上对齐至 32 字节**参与后续计算。
- 所有 Tiling 计算逻辑以 **32 字节为最小粒度**。

### 2.2 访存优化原则
AI Core 与 Global Memory 间的数据搬运开销显著，频繁搬运易成瓶颈。
- 核心目标：**充分利用 UB 空间**，增大单次搬运数据块，最大限度减少搬运总次数。
- 即在 UB 容量允许范围内，单次搬入尽量多的数据。

### 2.3 多核均衡原则
昇腾 AI 处理器集成多个 AI Core，需合理任务调度。
- 核心目标：**均衡利用多核**，将计算任务均匀分配到各核，避免算力闲置或负载不均。

## 三、四个通用设计要素（所有算子类别必须）

将上述原则落地为四个可检查的设计要素（与 `algorithm-categories.md` 的要素对齐）：

| 要素 | 核心问题 | 产出（须含） |
|------|---------|-------------|
| **1. 多核切分策略** | 任务如何分配给多个 AI Core？ | 切分维度 + 每核任务量 + 使用的核数；负载均衡依据 |
| **2. UB 切分策略** | 单次能处理多少数据？ | 单次数据量 + 是否分 chunk + chunk 大小算式（≤ UB 上限） |
| **3. Buffer 规划** | 需要哪些 buffer？各多大？ | inQueue/outQueue/tmpBuf/workBuf 列表 + 各 buffer 大小算式 + 总 UB 用量 + Double Buffer |
| **4. 分支场景覆盖** | 需处理哪些不同场景？ | 分支决策条件（dtype/shape 大小/对齐/边界）+ 各分支策略 + 边界用例 |

**UB 容量参考**：DAV_2201（910 系列）= 192KB；DAV_3510（950 系列）= 248KB。

## 四、核间/核内切分场景（官方教程 3.3）

将长度 TOTAL_LENGTH 的输入分配到多核，每核计算 BLOCK_LENGTH，核内再切分为 TILE_NUM 块，每块 TILE_LENGTH。根据均分与否有四种场景：

| 场景 | 核间 | 核内 | 处理 |
|------|------|------|------|
| 1 | 均分 | 均分 | 多核 Tiling 均匀分配，每核每次数据长度相同 |
| 2 | 均分 | 不均分 | 核内无法切成等长 32B 对齐块 → **尾块 Tiling** 处理尾块 |
| 3 | 不均分 | 均分 | 数据无法在核间均分 → **尾核 Tiling** 处理尾核 |
| 4 | 不均分 | 不均分 | 同时处理尾核 + 尾块 |

## 五、设计示例框架（shape (1,660) half, 4 核 Add）

以官方教程示例归纳设计流程（数值为教程实证，作为流程范本）：

1. **32B 对齐**：`660×2B=1320B` 不被 32 整除 → 向上对齐 `(660×2+31)//32×32 = 672×2 = 1344B`（42 个 32B 块）。
2. **核间拆分**：42 块 / 4 核 → 基础 10 块/核，余 2 块给前 2 核（大核 11 块/小核 10 块）。
3. **核内切分**（UB 768B，3 路 2 输入+1 输出）：单路 `768//3=256B` = 8 个 32B 块 → 大核 11 块分 2 批（8+3），小核 10 块分 2 批（8+2）。
4. **Tiling 结构体**：`smallCoreDataNum`/`bigCoreDataNum`/`finalBigTileNum`/`finalSmallTileNum`/`tileDataNum`/`smallTailDataNum`/`bigTailDataNum`/`tailBlockNum`。

> **关键纪律**：Tiling 参数用**直接公式计算**，不做二分搜索（官方原则）。tmpBufSize/sharedTmpBuffer 按算式推导。

## 六、与 TilingPlanner Tool 的关系

`AscendTilingPlanner` Tool 返回的 3×2 切分建议表（throughput/latency/balanced × 2 plans）是 **T0 mock 占位**——它是构造保证的存活信号（`mocked: true`），**不替代本方法论**。设计真实算子 tiling 时，必读本文 + 对应类别参考，按四要素产出方案，而非直接采用 mock 表。

## 关联
- 算子分类与各类专属策略：`algorithm-categories.md`
- Reduction 类详细 tiling：`reduction-tiling.md`
- AISS 自动求解器（T3/external）：`aiss-solver.md`
