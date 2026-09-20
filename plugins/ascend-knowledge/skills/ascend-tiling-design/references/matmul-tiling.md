---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/{ascendc-tiling-design/references/matmul/patterns,ascendc-perf-optimize/references/tiling/matmul/fallback/tiling-variants,ascendc-perf-optimize/references/tiling/matmul/fallback/tiling-fields}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "草稿合两源（同 cannbot@c24e8b5）：ascendc-tiling-design/references/matmul/patterns.md（mxfp8+eltwise 融合四要素）+ ascendc-perf-optimize/references/tiling/matmul/fallback/{tiling-variants,tiling-fields}.md（SWAT/StreamK/variants/字段语义）；本参考抽取事实自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# MatMul 类算子 Tiling 设计

> MatMul 类 tiling 参考（T2，cannbot@c24e8b5 验真，合两源：tiling-design matmul/patterns + perf-optimize matmul/fallback）。覆盖 mxfp8+eltwise 融合四要素 + matmul 族（a16w16/mxfp4/mxfp8/batch/group）SWAT→FullLoad→StreamK 推导链 + 变体差异 + TilingData 字段语义。

## 一、场景分类

cannbot tiling-design 当前覆盖 **mxfp8 quantized matmul + eltwise 融合**（Div/Mul/Add/Relu/Cast/组合算子）。其它 matmul 形态（fp16/bf16 matmul、BatchMatmul 等）的 **Tiling 算法**在 perf-optimize matmul/fallback（SWAT/StreamK/variants）。两者同属 cannbot@c24e8b5，互补：

- tiling-design/patterns → 融合算子的**四要素设计**（多核/UB/Buffer/分支）。
- perf-optimize/fallback → matmul 族的**Tiling 算法推导链**（SWAT/FullLoad/StreamK）+ 变体差异 + 字段语义。

## 二、融合算子四要素（mxfp8 + eltwise）

### 1. 多核切分

- M × N 二维切分（K 轴核内迭代，不参与核间切分）。
- 蛇形调度（BlockScheduler）保证同 row/col 核工作量一致。
- `singleCoreM × singleCoreN` 由 SWAT Tiling 引擎自动计算。
- `usedCoreNum = CeilDiv(M, singleCoreM) × CeilDiv(N, singleCoreN)` **强制动态计算，禁止硬编码**。

### 2. UB 切分

- `baseM / baseN / baseK` 由 SWAT 引擎根据 L1/UB 容量与算子约束优化得出。
- 使用 **Fixpipe SPLIT_M** 将 L0C 输出拆分给两个 AIV。
- **ODD-M**：M 为奇数时，Fixpipe DUAL_DST_SPLIT_M 要求 M 偶数才能等分双 AIV → L0C/UB 视图 M 向上取偶 `curMPad = (curM+1)&~1`，MMAD 仍用原始 `curM`，Epilogue 仅访问有效行。
- **ODD-N**：UB 侧 Fixpipe row stride 须对齐 32B（8 float）→ `curNUbAlign = AlignUp(curN, 8)`，DataCopyPad 按 `rowBytes = curN×sizeof(float)` 仅写出有效列。
- **SPLIT_M 偏移**：`offset += GetSubBlockIdx() * halfM * N`，`halfM = CeilDiv(curM, 2)`。
- UB 容量自检：`UB 总用量 = matmulArea + stageNum × stageSize_ ≤ TOTAL_UB_SIZE`。

### 3. Buffer 规划

**AIC 侧**（SWAT 引擎统一管理，`[PATTERN]` 区**禁止业务修改**）：L1_A（A 滚动窗口）、L1_B（B 滚动窗口）、L0A、L0B、L0C（`dbL0C × baseM × baseN × sizeof(float)`）、L1_ScaleA/B（mxfp8 scale）。

**AIV 侧 UB**（**融合算子禁用 TPipe，采用静态偏移分配**）：UB_L0COut（Fixpipe 输出）、UB_Eltwise（第二路输入暂存）、UB_Cast。`stageNum` 按输入路数：1（Relu/Cast）→ 仅 resultLocal；2（Div/Mul/Add）→ second + result；3（Mul+Add）→ second + third + result。

### 4. 分支场景

| 分支 | 条件 | 策略 |
|---|---|---|
| 转置 | transA/transB ∈ NN/NT/TN/TT | Host 按 trans 选 RowMajor/ColumnMajor；L1 Layout 始终 Nz/Zn（Cube 硬件要求） |
| 大 shape | M×N ≫ singleCoreM×singleCoreN | 多核 M×N 切分 + 核内 K 轴 L1 滚动 |
| 小 shape | M/K/N 较小 | 减核数；baseM/baseN 适当缩小匹配 |
| ODD-M | curM 奇数 | UB/L0C 视图 M 取偶；Epilogue 仅访问有效行 |
| ODD-N | curN 非 8 倍数 | UB 视图 N 对齐 32B；DataCopyPad 按实际 curN 读写 |
| K 对齐 | mxfp8 | Host 侧 padding K 到 64 倍数（mxfp8 Cube 硬件要求） |

## 三、matmul 族 Tiling 算法（SWAT → FullLoad → StreamK）

所有变体共享同一套推导链，仅初始参数/Cube 粒度/布局/特有约束有差异。

### 推导链三分支

- **SWAT**（默认）：K 维流式，A/B/Scale 反复 GM→MTE→L1→Cube→L0 乘加。L1 pingpong 缓冲实现 MTE2 与 Cube 重叠。
- **Full-Load（驻留层）**：A 或 B 全载驻留 L1。`isAFullLoad`/`isBFullLoad` 二选一（严禁同时 true）。全载侧 `stepK = CeilDiv(K, baseK)`、`scaleFactor = 1`、`{m/n}TailTile = 1`。Kernel 选 `BlockMmadMxAFullLoad`/`BFullLoad`/`Swat` 三套模板之一。
- **StreamK**：K 方向跨核分段归约。强制常量：`l1BufferNum=2`、`l0cDB=1`、`mBaseTailSplitCnt=nBaseTailSplitCnt=1`、`mTailMain=nTailMain=0`、`usedCoreNum=aicNum`。

### 关键取值约束

- **stepK ∈ {1, 2, 4}**（2 的幂）：`_get_depth_a1b1()` 倍增搜索 `depth_scale *= 2` 使 depth 只能为 2 的幂，`stepK = depth // DB_SIZE(=2)`。若用户期望 stepK=3，应解释为"depth 倍增搜索机制 vs 实施层 L1_BUFFER_NUM 最大化利用"的设计差异。
- **nBufferNum 仅 4 / 2**（无 1）：4 缓冲占用 ≤ L1 取 4，否则 2。无 1 是因为单缓冲无法 MTE2/Cube 重叠（流式 + 重叠默认目标）。

## 四、变体差异

| 维度 | a16w16 | mxfp4/8 | batch_matmul | group_matmul |
|---|---|---|---|---|
| dtype(A/B) | FP16/BF16 | FP4(0.5B)/FP8(1B) | 随子变体 | 随子变体 |
| Scale | 无 | UE8 per-group=32 | 随子变体 | 随子变体 |
| 特有维度 | — | — | batch(B) | group(g), M_i 不等 |
| baseK | 16 | 32 | 随子变体 | 随子变体 |
| StreamK | 可用 | 可用 | **默认不启用**（与 batch 并行冲突） | **默认不启用** |
| 多核切分 | M×N | M×N | B×M×N 三维（batch 优先并行） | split-M / split-N 子路由 |

- **a16w16**（基线）：SWAT 七步完全适用；BLOCK_TABLE 负载均衡为 a16w16 专属；字段名 `l0cDB`（其他变体 `dbL0C`）。
- **mxfp4/mxfp8**：共享流程，仅 dtype 字节宽度/baseK 上限不同（mxfp4 baseK 256，mxfp8 baseK 128）。Scale 几何 `scale_per_K = CeilDiv(K, 32)`；`scaleFactorA/B` 控制单次 Scale 搬移量（受 `SCALE_FACTOR_MAX=127`、`MTE2_MIN_LOAD_SIZE=32KB` 约束）；`stepKa/stepKb` 下发（a16w16 不下发）。
- **batch_matmul** `(B,M,K)×(B,K,N)→(B,M,N)`：多核切分 B×M×N 三维决策树（totalTiles≥aicNum 优先 batch 维分核；<aicNum 退化单 batch 粒度复制；B>aicNum 纯 batch 切分）。
- **group_matmul**（g groups (M_i,K,N)，M_i 可不等，常用于 MoE）：split-M（M_i 大、负载易均衡、全量对称量化）vs split-N（M_i 小 N 大、weight-quant）。kL1 拆 kAL1/kBL1；尾块 Kernel 端按 groupListGm 动态推导。

## 五、TilingData 字段语义（跨变体并集）

- **通用基础**：`m,n,k, baseM/baseN/baseK, usedCoreNum, dbL0c`（a16w16 名 `l0cDB`）。
- **K 维流水**：`stepKa/stepKb`（SWAT/FullLoad）、`depthA1/depthB1`、`nBufferNum`（仅 4/2）、`kL1 = baseK × min(stepKa,stepKb)`。
- **StreamK 专属**：`skSingleCoreK`、`tailInfo.kCnt`、`mL1/nL1`、`l1BufferNum`（强制 2）。
- **尾块/边缘合并**（SWAT 机制 B/C）：`mTailTile/nTailTile`、`mBaseTailSplitCnt/nBaseTailSplitCnt`（滑动窗口 WINDOW_LEN=4 搜索）、`mTailMain/nTailMain`。
- **Scale**（仅 mxfp/group 量化）：`scaleFactorA/B`、`scaleKL1`、`scaleL1BufferNum`（[16,8,4,2] 回退）、`scaleBufferNum`（固定 2）。
- **驻留层**：`isAFullLoad`/`isBFullLoad`（二选一）。

> 字段—变体—分支三维交叉：参考源 `tiling-fields.md` §9 表。建模专家写报告前须过 §10 自检清单（变体识别 / 2 的幂规则 / StreamK 强制常量 / 驻留层字段 / Scale 合并载入 / MTE2 Preload 标志）。

## 关联
- 方法论主源：`tiling-methodology.md`（T1，四要素）
- 分类总览：`algorithm-categories.md`（T2，9 类 support status）
- matmul 融合代码级模板：cannbot `ascendc-direct-invoke-template` skill（references/matmul_fusion_kernel/，Developer 用）
