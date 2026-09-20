---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ops-profiling/references/optimization_quickref.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ops-profiling optimization_quickref.md 抽取 10 类 bound 判定阈值、定向优化方法、交叉关联诊断与 4 案例自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# 瓶颈定位与定向优化（10 类 bound）

> msprof 采数后按 Main Bound 判定（见 `msprof-collection.md` §三）定位瓶颈执行单元，本文给出**每类 bound 的判定阈值 + 定向优化方法 + 交叉关联诊断 + 实战案例**。判定字段来自 op_summary_*.csv 的 PipeUtilization / ResourceConflictRatio / L2Cache 组。

## 1. VEC Bound

| 判定 | 优化方法 |
|---|---|
| `aiv_vec_ratio` > 50% 占比最大 | UB 融合（多 elementwise 合一）/ 减少 Cast（类型转换合并）/ 融合指令（Fusion 优化）/ 低延迟归约 / AIC:AIV = 1:2（Cube:Vector 核比）/ Counter 模式（统计类用 counter 寄存器） |

> VEC bound = 向量计算是瓶颈。减少向量指令数（融合/去 Cast）或加 Vector 核（AIC:AIV 调比）。

## 2. MTE2 Bound

| 判定 | 优化方法 |
|---|---|
| `ai*_mte2_ratio` 最高（> 80% 或占比最大 > 70%） | 增大单次搬运量（大 tile）/ 512B 对齐（地址对齐提带宽）/ L2 CacheMode（缓存命中）/ 避免同地址重复搬 / DoubleBuffer（搬入与计算重叠）/ 增大 Tile（减搬运次数） |

> MTE2 = 搬入（DDR→UB）瓶颈。核心是**提带宽**（对齐 + 大块 + 缓存）和**重叠**（DoubleBuffer 让搬运与计算并行）。

## 3. CUBE Bound

| 判定 | 优化方法 |
|---|---|
| `aic_cube_ratio` 占比最大 | L0C 累加（中间结果驻 L0C 不落 L1）/ L1 复用（输入驻 L1 多次用）/ BT Buffer / FP Buffer / AtomicAdd（累加用原子加免中转） |

> CUBE = 矩阵乘瓶颈。优化 L0/L1 缓存复用，减少中间结果往返。

## 4. SCALAR Bound

| 判定 | 优化方法 |
|---|---|
| `ai*_scalar_ratio` > 30% | 缩小 TilingData（减标量循环）/ 减少核数（标量串行部分核多无用）/ TPipe 外置 / 移出不变量（常量提到循环外） |

> SCALAR = 标量处理瓶颈（地址计算/循环控制）。减标量工作量或把不变量提出循环。Atlas A2 单 head 约 20-21us。

## 5. 核间负载不均衡

| 判定 | 优化方法 |
|---|---|
| PipeUtilization 各核 `ai*_time`（cycle）差异 > 10% | 均匀分配尾块 / 调整 blockDim（核数）/ 动态负载均衡 |

> 逐核 cycle 差异大 = 尾核拖慢整体。均匀分尾块或减核数让每核满载。逐核 cycle 须 sample aicore.db（见 `msprof-collection.md` §1.3）。

## 6. Bank Conflict

| 判定 | 优化方法 |
|---|---|
| ResourceConflictRatio `aiv_vec_total_cflt_ratio` > 5% | bankgroup 冲突 / bank 冲突 / 资源冲突 / MTE 冲突四类——按冲突类型调整访问模式 |

> UB 有 48 banks / 16 groups，每 bank 32B。连续访问同 bank 会串行化。调整访问步长让访问落不同 bank。

## 7. DoubleBuffer 未生效

| 判定 | 优化方法 |
|---|---|
| MTE2 和 VEC 串行（无重叠），bufNum = 1 | InitBuffer `bufNum = 2` / EnQue-DeQue 严格配对 / 避免 Sync 同步阻塞 |

> DoubleBuffer = 搬入与计算重叠。bufNum=2 时双缓冲，搬运 A 时算 B。重叠 > 30% 才算生效。配对错（EnQue 无 DeQue）会退化成单缓冲。

## 8. 流水线气泡

| 判定 | 优化方法 |
|---|---|
| 多单元 30-50% 无明显主导（无 bound） | 增 workspace 份数 / DoubleBuffer / 异步迭代 / 调 AIC:AIV 比例 |

> 无单点 bound 但整体利用低 = 流水气泡（stage 间等待）。增缓冲份数让各 stage 都有数据可处理。

## 9. L2 Cache 命中率低

| 判定 | 优化方法 |
|---|---|
| L2Cache `hit_rate` < 50% | SetL2CacheHint（显式缓存提示）/ 禁用不需要缓存的数据 / L2 切分 / 小矩阵驻 L1 |

> L2 miss 多 = 反复从 DDR 取。提示热点数据缓存，冷数据不缓存（避免挤占）。

## 10. 交叉关联诊断

多指标关联时，先解根因再解表象：

| 关联 | 先解 | 依据 |
|---|---|---|
| 高 vec_ratio + 高 bank_cflt | 先解 bank conflict | bank 串行化拉高 vec 占比假象 |
| 高 mte2 + 低 L2 hit | 先设 CacheMode | L2 miss 致反复搬入拉高 mte2 |
| 高 fixpipe | 512B 对齐 | fixpipe 对地址对齐敏感 |
| 高 mte2 + 高 mte3 | 联合看 | 带宽共享，互相拉高 |

## 实战案例

### 案例 1：GroupedMatmul（AIC:AIV 比例，41% 提升）

瓶颈：Cube 计算重、Vector 闲。优化：调 AIC:AIV 核比（加 Cube 核减 Vector 核）+ workspace 份数 + DoubleBuffer。收益 41%。

### 案例 2：Matmul Tiling（BlockDim 不足，4.75x）

瓶颈：blockDim 太少，核间负载不均且单核 tile 过大。优化：增 blockDim + 调 tile 大小（L1 复用）。收益 4.75x（低垂果实——核数不足是首要瓶颈）。

### 案例 3：FlashAttention（地址对齐，fixpipe 80%→55%）

瓶颈：fixpipe 占比 80%（地址未对齐）。优化：512B 地址对齐。fixpipe 降至 55%。

### 案例 4：MC² 通算融合（32.7%）

瓶颈：通信与计算串行。优化：MC² 通算融合（通信与计算重叠）。收益 32.7%。

## 关联

- `msprof-collection.md` — msprof 采集 + 7 组指标 + Main Bound 判定优先级
- `perf-pipeline-methodology.md` — 三层管线流程（本文是 Step 4 核内 bound 层）
- `perf-tiling-recorrection.md` — bound 定位后回溯 tiling 修正
