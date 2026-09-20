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
  note: "从 cannbot ascendc-perf-optimize SKILL.md 四步流程中每步的 tiling 修正建议抽取自撰重写，桥接性能瓶颈→tiling 重设计；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# 性能驱动的 tiling 修正（回溯 ascend-tiling-design）

> 性能优化的每步（卡间/核间/核内）定位瓶颈后，产出**tiling 修正建议**回溯 `ascend-tiling-design` skill 的 Step 1 理论建模。本文是**瓶颈→tiling 参数**的映射表：据 `bottleneck-location.md` 定的 bound 类型，改哪个 tiling 参数。

## 一、修正闭环

```
ascend-tiling-design Step 1：初始 tiling plan（blockDim / tile 大小 / Buffer 份数 / 对齐）
  ↓ 跑一版 + msprof 采数
bottleneck-location.md：定 bound 类型
  ↓ 本文：bound → tiling 参数修正
回改 tiling plan（重建模）
  ↓ AscendBenchmarkRunner 量化前后吞吐
```

> tiling 修正是**回溯**，不是新设计——基于 ascend-tiling-design 的四要素（多核切分 / UB tiling / Buffer 规划 / 分支覆盖）改参数。

## 二、bound → tiling 参数映射

| bound 类型 | 改的 tiling 参数 | 方向 |
|---|---|---|
| MTE2 Bound | tile 大小 / DoubleBuffer 份数 / 512B 对齐 | 增大 tile（减搬运次数）/ bufNum=2（搬算重叠）/ 地址对齐 |
| CUBE Bound | L0C/L1 复用策略 / tile 大小 | 中间结果驻 L0C / 输入驻 L1 / 调 tile 让 L1 装下 |
| VEC Bound | AIC:AIV 核比 / 融合策略 | 加 Vector 核 / elementwise 融合减指令 |
| SCALAR Bound | TilingData 大小 / 核数 / 不变量位置 | 缩 TilingData / 减核 / 不变量提出循环 |
| 核间不均衡 | blockDim / 尾块分配 | 增减核数 / 均匀分尾块 |
| Bank Conflict | 访问步长 / tile 形状 | 调步长让访问落不同 bank |
| DoubleBuffer 未生效 | bufNum / EnQue-DeQue 配对 | bufNum=2 / 修配对 |
| 流水气泡 | workspace 份数 / AIC:AIV | 增缓冲份数 / 调核比 |
| L2 Cache 低 | SetL2CacheHint / tile 大小 | 提示缓存 / 小矩阵驻 L1 |

## 三、分层修正（与三层管线对应）

### 卡间层（Step 2）

- 瓶颈：通信裸露（未与计算重叠）。
- 修正：卡间切分粒度（按 batch/seq 切的大小）、通信合并策略。
- 回溯：ascend-tiling-design 卡间切分。

### 核间层（Step 3）

- 瓶颈：各核 cycle 差异 > 10%。
- 修正：blockDim（核数）、尾块分配算法。
- 回溯：ascend-tiling-design 多核切分。

### 核内层（Step 4）

- 瓶颈：某执行单元 bound（见 `bottleneck-location.md`）。
- 修正：tile 大小、DoubleBuffer 份数、对齐、L0C/L1 复用、AIC:AIV 比例。
- 回溯：ascend-tiling-design 单核切分 + Buffer 规划。

## 四、修正后验证

每轮 tiling 修正后**必须**：

1. **AscendCodeGen 重生成**（若 kernel 结构变）或 **Read/Edit** 改 tiling 参数（若仅参数变）。
2. **AscendCompilerBridge** 重编译（`python3 setup.py build_ext`）。
3. **AscendGoldenTest** 确认正确性未回归（优化不能破坏正确性——这是硬门）。
4. **AscendBenchmarkRunner** 量化前后吞吐对比（before/after throughput）。

> 优化破坏正确性是常见坑：增 tile 可能溢出 UB、调对齐可能改变语义。**每轮先跑 GoldenTest 再看性能**。

## 五、何时停止迭代

- 目标吞吐达成 → 停。
- 连续 2 轮无提升（< 5%）→ 边际收益递减，停。
- 单层 bound 解了但整体无提升 → 上溯一层（核内解了看核间，核间解了看卡间）。

## 关联

- `bottleneck-location.md` — bound 判定（本文修正的输入）
- `msprof-collection.md` — 采数（本文修正的依据来源）
- `perf-pipeline-methodology.md` — 三层管线流程（本文是每步的修正环节）
- `ascend-tiling-design` skill — Step 1 理论建模（本文回溯的目标）
