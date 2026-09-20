---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-perf-optimize/SKILL.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-perf-optimize SKILL.md 抽取三层管线优化流程与四步方法论自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# 性能优化三层管线方法论

> Ascend C 算子性能优化按**三层管线**逐层下钻：卡间 → 核间 → 核内。每层独立分析瓶颈、出优化策略、回写 tiling 修正建议。 cannbot ascendc-perf-optimize 把流程固化为四步：理论建模 → 通算演算 → 核间流水 → 单核流水。本文是流程骨架；瓶颈判定细则见 `bottleneck-location.md`，采集细则见 `msprof-collection.md`。

## 一、三层管线

| 层 | 切分对象 | 关键问题 | 分析手段 |
|---|---|---|---|
| **卡间** (inter-card) | 多卡数据切分 | 卡间通信与计算是否重叠、切分是否均衡 | 仿真图 + 通信时序 |
| **核间** (inter-core) | 单卡多核 (blockDim) | 各核负载是否均衡、核间流水是否建立 | msprof PipeUtilization 逐核 cycle |
| **核内** (intra-core) | 单核流水 (Cube/Vector/MTE) | 哪个执行单元是 bound、流水气泡 | msprof --aic-metrics 7 组利用率 |

> 下钻顺序：先卡间（多卡场景）→ 再核间（负载均衡）→ 最后核内（bound 定位）。**不要跳层**——核内 bound 可能实为核间不均衡的表象。

## 二、四步优化流程

### Step 1：Tiling 理论建模

- **卡间切分**：多卡场景定数据切分策略（按 batch/seq 切），保证各卡计算量均衡。
- **多核切分**：定 blockDim（核数）+ 每核处理的数据块。目标：各核负载均衡（尾块均匀分配）。
- **单核切分**：定核内 tile 大小（UB tiling）、tile 循环次数、DoubleBuffer 份数。
- **Buffer 规划**：UB 空间分配（输入/输出/中间 tensor + workspace），避免溢出。
- **分支覆盖**：TilingKey 分支全覆盖（不同 shape 走不同 tiling 分支，每支都要测性能，不只测主分支）。

> Step 1 的输出是**初始 tiling plan**。建模依据见 `ascend-tiling-design` skill（四要素方法论 + 9 算法类别）。性能优化**回溯** tiling-design 修正切分参数。

### Step 2：通算演算（卡间流水）

- 分析卡间通信与计算是否重叠（comm-compute overlap）。
- 仿真图看通信时序是否被计算掩盖；若通信裸露，调整切分使通信可与计算并行。
- 输出：卡间流水优化策略 + tiling 修正建议（切分粒度/通信合并）。

### Step 3：核间流水（inter-core pipeline）

- msprof 采 PipeUtilization，看各核 `ai*_time`（cycle）差异。
- 判定：各核 cycle 差异 > 10% → 核间负载不均衡（见 `bottleneck-location.md` §5）。
- 优化：均匀分配尾块、调整 blockDim、动态负载均衡。
- 输出：核间负载均衡策略 + tiling 修正建议（blockDim/尾块分配）。

### Step 4：单核流水（核内 bound 诊断）

- msprof 采 7 组 --aic-metrics（PipeUtilization/ArithmeticUtilization/Memory/MemoryL0/MemoryUB/L2Cache/ResourceConflictRatio）。
- 按 Main Bound 判定优先级定位瓶颈执行单元（MTE2/CUBE/VEC/FIXP/MTE3/SCALAR）。
- 优化：据 bound 类型施策（见 `bottleneck-location.md` 10 类 bound 的定向优化）。
- 输出：核内 bound 优化策略 + tiling 修正建议（tile 大小/DoubleBuffer/对齐）。

## 三、每步产出格式

每步完成后产出四件：

1. **仿真图分析**（如有）：流水时序图解读，哪个 stage 是瓶颈。
2. **profiling 数据报告**：msprof op_summary 关键字段值（aiv_vec_ratio / aiv_mte2_ratio / aic_cube_ratio 等）。
3. **优化策略**：针对该层瓶颈的具体改法。
4. **tiling 修正建议**：回溯 Step 1 tiling plan 改哪些参数（blockDim/tile 大小/Buffer 份数/对齐）。

## 四、迭代闭环

```
Step 1 初始 tiling plan
  ↓ 跑一版 → msprof 采数
Step 2/3/4 分析瓶颈 → 修正建议
  ↓ 回改 tiling plan（Step 1 重建模）
再跑一版 → 对比前后 throughput（AscendBenchmarkRunner）
  ↓ 未达目标 → 回 Step 2/3/4
```

> 每轮优化**必须用 AscendBenchmarkRunner 量化前后吞吐**（before/after throughput），否则优化无依据。mock 模式返 `mocked: true` 是 liveness 信号非真实性能——不可据 mock 数值下优化结论。

## 关联

- `msprof-collection.md` — msprof 7 组指标采集 + warm-up + 归档
- `bottleneck-location.md` — 10 类 bound 判定阈值 + 定向优化
- `perf-tiling-recorrection.md` — tiling 修正回溯 ascend-tiling-design
- `profiling-tool-routing.md` — 何时用哪个 profile/bench 工具
- `ascend-tiling-design` skill — Step 1 理论建模的方法论基础
