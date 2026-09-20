---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-tiling-design/references/reduction/{patterns,algorithms,alg-welford,alg-dichotomy,alg-group-reduce,multi-axis-transform,multi-output-buffer,tiling-fields,with-index,ar-fullload,ar-colsplit,ara-fullload,ara-rowsplit}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "草稿来自 cannbot ascendc-tiling-design/references/reduction（全 13 文件），本参考抽取 patterns 场景路由 + welford/dichotomy 算法 + group-reduce/multi-axis/multi-output/tiling-fields/with-index 自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Reduction 类算子 Tiling 设计

> 本文档是 Reduction 类 tiling 详细参考（T2，cannbot@c24e8b5 验真，源 references/reduction/ 13 文件）。覆盖场景路由、AR/ARA 分支决策、Welford/Dichotomy 核心算法。

## 一、合轴（场景判定的前置步骤）

将 N 维 shape + axes 简化为更少维度。每个维度标记 **A**（保留轴）或 **R**（归约轴），然后：
1. 消除冗余维度（size=1 且内存连续）。
2. 合并相邻同类型轴（相邻 A 或相邻 R → 乘积合并）。

**示例**：`shape=[2,100,4], axes=[1,2]` → 标记 A,R,R → 相邻 R 合并 → `[2, 400]` = (A, R) → 单轴 AR。

## 二、场景路由（S1-S6）

```
给定 shape, axes（归约轴）

Step 0: 合轴 → 标记 A/R → 消除冗余 → 合并相邻同类
Step 1: 合轴后单轴还是多轴？
  ├─ 单轴（AR 或 ARA）→ Step 2
  └─ 多轴（ARAR 交替）→ 多轴归约（三步 shape 变换展开为嵌套循环）

Step 2: A0 决定模式
  ├─ A0 = 1 → AR 模式（每行 R 个元素连续，Level 2 Reduce API）
  │   ├─ UB 能装 ≥1 整行 → AR-FullLoad
  │   └─ 否则           → AR-ColSplit（列方向分段，跨 chunk 合并）
  └─ A0 > 1 → ARA 模式（[R, A0] 块连续，Pattern::Reduce::RA）
      ├─ UB 能装所有 R×tileA0Len（32B 对齐）→ ARA-FullLoad
      └─ 否则                              → ARA-RowSplit（行方向分段，跨 chunk 合并）
```

| 场景 | 适用 | 核心策略 |
|------|------|---------|
| **S1 AR** | 单轴归约，归约轴是尾轴（A0=1） | 每行 R 元素连续，Level 2 Reduce API 逐行归约 |
| **S2 ARA** | 单轴归约，归约轴非尾轴（A0>1） | [R, A0] 块连续，Pattern::Reduce::RA 归约 |
| **S3 多轴** | 合轴后多轴（ARARA 等） | 三步 shape 变换 → 嵌套循环，每 R 维按 S1/S2 判定 |
| **S4 Welford** | ARA 分载 + 流式计算两个相关统计量 | 单遍增量更新（见 §三） |
| **S5 Group Reduce** | R 太大单核处理不完 + A 太小不足多核并行 | 跨核分 R，workspace 同步合并 |
| **S6 全局归约** | 全轴归约（reduce_sum(axes=all)） | 各核独立归约 → 两阶段合并（AtomicAdd 或 core0 合并） |

## 三、核心算法

### 3.1 算法选择对照

| 条件 | 推荐算法 | 原因 |
|------|---------|------|
| FullLoad | 直接顺序计算 | 数据整块驻留 UB |
| FullLoad + 两次顺序归约 | TwoPass | 两遍分别求 A、B |
| 分载 + 两次相关归约 | **Welford Online** | 单遍流式，省一轮 IO |
| 分载 + 单核处理不完 R 且 A 小 | **Group Reduce** | 跨核分 R + workspace 同步 |
| Sum 精度敏感 | **二分累加** | 相近量级先加，解决大数吃小数 |

### 3.2 Welford Online（在线单遍）

**适用**：分载模式下流式计算两个相关统计量（如 mean + variance），单遍扫描完成。

**核心更新公式**：
```
初始: mean=0, M2=0, count=0
对每个新元素 x:
    count += 1
    delta1 = x - mean          ← 旧偏差
    mean = mean + delta1/count ← 增量更新均值
    delta3 = x - mean          ← 新偏差
    M2 = M2 + delta1 * delta3  ← 增量更新方差
最终: var = M2 / (count - correction)
```

**两组合并**（多核/多分组局部结果合并为全局）：
```
count_total = count_a + count_b
delta = mean_b - mean_a
mean_total = mean_a + delta * count_b / count_total
M2_total = M2_a + M2_b + delta² * count_a * count_b / count_total
```

**vs TwoPass**：FullLoad + 两次顺序归约用 TwoPass（实现简单）；分载 + 两次相关归约用 Welford（单遍省一轮 IO）。Group Welford：每 8 个 chunk 中间合并防误差累积。

### 3.3 二分累加（Dichotomy / Half-Interval）

**适用**：Sum 归约专用，解决顺序累加中大数吃小数的精度问题。

**原理**：用二叉树结构折叠求和，使相近量级的数先相加。
```
Step 1: 找最大 2^k ≤ count
Step 2: 尾部折叠（count - 2^k 个元素并到前面）
Step 3: 二分折叠（powerTwo /= 2，Add(src, src, src[half], half)，直到 ≤64）
Step 4: WholeReduceSum 硬件指令（≤64 元素）
```

**vs 顺序累加**：顺序累加大数吃小数；二分累加相近量级先加，精度更好。UB 开销：原地操作无额外 buffer。Max/Min 不受精度影响（无需二分）。

## 四、通用规则

**rLength vs rLengthAlign 参数使用**：
| 参数位置 | 用 rLength（有效数据） | 用 rLengthAlign（对齐后） |
|---------|:---:|:---:|
| DataCopyPad blockLen | ✅ | ❌ |
| Reduce API count（Level 2） | ✅ | ❌ |
| UB 内 rowOffset 计算 | ❌ | ✅ |
| Buffer 大小分配 | ❌ | ✅ |

**正交维度**（确定 AR/ARA 分支后按算子特征选）：
- 算法选择：Welford（分载 + 流式双统计量）/ Group Reduce（R 跨核）
- 精度策略：二分累加（大向量 sum 精度敏感）
- 索引跟踪：With-Index（归约 + 返回极值位置，用 Compare+Select 逐行迭代）

## 五、Group Reduce（S5 跨核归约详述）

**适用**：R 太大单核遍历不完，同时 A 轴太小不能充分利用多核。两阶段执行模型：

```
Phase 1（各核独立）: 各核处理 R 的一段 → 局部 ReduceOp → partial 写 workspace[coreIdx]
                      ↓ SyncAll()
Phase 2（合并核）:   read workspace[0..coreNum] → merge all partials → final output
```

- Phase 1 `partialBuf` 初始化：sum→0，max→-inf。`wsOffset = blockIdx × SLOT_STRIDE`（64B 对齐防 bank conflict）。
- Phase 2 合并所有 partial：`ReduceOp(finalBuf, finalBuf, partialLocal, outSize)` 逐 group 合并。
- **Welford Group Reduce**（reduce_var）：Phase 1 输出 (mean, M2, count) 三元组，Phase 2 用 Welford 合并公式（见 §3.2 两组合并）逐组合并。每 8 chunk 中间合并防误差累积。

## 六、多轴归约（S3 详述）

合轴后仍为多段 A/R 交替序列（如 ARAR）时展开执行。

**典型场景**：BatchNorm `bn_training_reduce` 对 NCHW 沿 N,H,W 归约保留 C：`[N,C,H,W] axes=[0,2,3]` → 合并相邻 R(N,H,W) → 前置 A[1] → `ARAR [1, N, C, H×W]`，双输出 sum[C] + squareSum[C]。

**高维 Pattern（≥5 维）**：通过 `PadDimOne()` 填充 size=1 维度统一到 **8 维（ARARARAR）或 9 维（ARARARARA）**。

**Kernel 执行**：多轴展开为嵌套循环，递归模板 `IterateInnerA<N>()` 编译期展开遍历所有 A 轴，每层 R 轴独立走 AR/ARA 判定：
- R 轴是最内层（右侧无 A）→ **AR 模式**（Level 2 Reduce API）。
- R 轴右侧还有 A 维度 → **ARA 模式**（Pattern::Reduce::RA）。

**非连续多轴数据搬运**：axes 使 R 轴散布内存中时，DAV_3510 用 `CopyInWithNddma()`（多维 DMA 自动处理 stride）；DAV_2201 用 DataCopyPad 的 `blockCount/blockLen/srcStride` 配置 stride copy 或外层循环逐 slice 搬运。

## 七、多输出归约 Buffer 规划

许多归约算子同一遍扫描输出多个结果（bn_training_reduce 2 输出、reduce_var 2 输出、arg_max 2 输出 value+index）。

**通用 UB 方程**（K 个输出）：

```
inBuf × 2              = tileSize × T_in × 2          ← 输入双缓冲
castBuf (仅低精度)      = tileSize × T_acc             ← FP16/BF16 → FP32
accumBuf × K           = A_aligned × T_acc × K         ← K 个累加器
tmpBuf                 = A_aligned × T_acc             ← 中间计算（如 x²）
outBuf × 2             = A_aligned × T_acc × 2         ← 输出双缓冲（可选）

UB 方程: tileSize × (T_in × 2 + T_acc) + A_aligned × T_acc × (K + 1 + 2) ≤ UB_SIZE
求解 tileSize = (UB_SIZE - A_aligned × T_acc × (K+3)) / (T_in × 2 + T_acc)
```

**跨核 workspace** 也要乘 K：`workspace = coreNum × CeilAlign(A_aligned × T_acc × K, cacheLineSize)`。

## 八、Tiling 字段与 tmpBufSize

**设计原则**（直接公式计算，不用二分查找）：
1. `a0TileBase = VECTOR_REG_WIDTH / sizeof(T)`（FP32=64）是最小对齐单位，所有 Buffer 大小是其整数倍。
2. 约束取最小：`a0Inner = min(UB容量限制, A0维度限制, 多核均衡限制)`。
3. 保守估算：用 a0TileBase 算 `ubPerTileBase`，实际 `tileA0Len ≤ 估算值`。
4. API 参数限制传导：若 Reduce API `repeatTimes ≤ 255` 且与 R 相关，则 `R_max = min(R_max, 255)`。

**tmpBufSize（sharedTmpBuffer）**：

```cpp
uint32_t ComputeReduceBufSize(uint32_t rLengthAlign, uint32_t typeSize) {
    uint32_t perRepeat = 256 / typeSize;         // 64 for FP32
    uint32_t perBlock  = 32 / typeSize;          // 8 for FP32
    uint32_t repeats   = (rLengthAlign + perRepeat - 1) / perRepeat;
    uint32_t tmpBufSize = ((repeats + perBlock - 1) / perBlock) * perBlock * typeSize;
    return std::max(tmpBufSize, 4096u);          // 最小 4KB
}
```

**全载 vs 分载判定**：全载 = 加载数据 + 计算过程全部 Buffer ≤ UB_SIZE。不同算子中间 Buffer 不同，阈值公式因算子而异。

**常用 TilingData 字段**：`factorACntPerCore/factorATotalCnt/ubFactorA`（A 轴）、`factorRCntPerCore/factorRTotalCnt/ubFactorR`（R 轴）、`groupR`（>1 触发 Group Reduce）、`outSize`、`basicBlock`、`coreNum`、`useNddma`、`shape[8]/stride[8]`。ArgMax 系列增 `aSize/rSize/nextASize/cutASize/cutRSize/cutNextASize/aRaMode/workSpaceSize`。Norm 类（RmsNorm/LayerNorm）增 `num_row/num_col/num_col_align/block_factor/row_factor/ub_factor/epsilon`。

## 九、索引跟踪变体（With-Index）

归约 + 记录极值位置的正交变体。Tiling 方法论完全复用标准 Reduction，仅 API 替换 + 额外约束 + Buffer 增量。

| 分支 | 标准 Reduction | 索引跟踪 |
|---|---|---|
| AR-FullLoad | `ReduceMax(dst, src, tmp, count)` | `ReduceMax(dst, src, tmp, count, calIndex=true)`（dst[0]=值, dst[1]=索引） |
| AR-ColSplit | chunk → ReduceMax → 标量合并 | chunk → `ArgMaxV1` → 跨片索引偏移合并 |
| ARA-FullLoad | Pattern::Reduce::RA → 向量结果 | `Compare(LE) + Select(TT) + Select(TS)` 逐行迭代 |

**额外约束**（DAV_2201）：Select 不支持 int32 dst → 索引必须用 float 存储最后 Cast 为 int32；float32 精确表示 [0, 2^24] 整数；返回**第一个**极值索引（LE/GE 自动保证）；Compare count 须 **256 字节对齐**（float: 64 元素倍数，非 32B）；DataCopyPad rightPadding ≤32B。

**ARA LE 反转 + TENSOR_SCALAR 优化**：Compare 用 LE（非 GT）反转 mask 极性，bit=1 表示"保留旧值"。索引更新 Select 用 `VSEL_TENSOR_SCALAR_MODE` 将当前行索引作 scalar 传入，省 Duplicate + 省 1 buffer，循环内 3 条指令/轮。`xLocal[r]==maxLocal` 时 LE 成立保留旧索引 → 与 numpy.argmax 一致。Min-Index 唯一区别是 Compare 用 GE。

**Buffer 规划（5 个 vs 标准 3 个）**：inQueueX（R×a0Aligned×4）、outQueueY（int32，a0Aligned×4）、maxBuf（float 当前最大值，**新增**）、idxBuf（float 当前索引，**新增**）、cmpBuf（uint8 mask `max(a0Aligned/8, 32)`，**新增**）。`a0Aligned = ((A0+63)/64)*64`（256B 对齐）。

## 关联
- 方法论主源：`tiling-methodology.md`（T1，四要素）
- 分类总览：`algorithm-categories.md`（T2）
- AISS 自动求解：`aiss-solver.md`（T3/external）
