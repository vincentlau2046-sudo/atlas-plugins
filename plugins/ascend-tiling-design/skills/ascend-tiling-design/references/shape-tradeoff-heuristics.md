---
tier: T3
confidence: heuristic
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-tiling-design/references/{broadcast,sort,elewise,conversion,reduction,matmul}/patterns.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: composite
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "T3 启发式综合：跨 cannbot 6 类 patterns 的 shape→切分策略 trade-off 直觉，由各 category reference 的场景路由综合而成；basis（6 patterns）cannbot@c24e8b5 可验真，但 trade-off 结论是启发式假设非事实断言，agent 用时须配证据"
license: CANN-OSL-2.0
---

# Shape → 切分策略 Trade-off 启发式（T3）

> T3 启发式参考。综合 cannbot 6 类算子 patterns 的场景路由，提炼 shape 特征 → 切分策略的 trade-off 直觉。**basis（各 category patterns）可验真，但 trade-off 结论是启发式假设，非事实断言**——agent 用时须配实际运行证据，启发式只作假设来源。

## 一、shape 特征 → 推荐范式

| shape 特征 | 推荐范式 | 依据 | 详见 |
|---|---|---|---|
| 输入输出 shape 完全相同 | EleWise 展平 1D 线性 | 无跨元素依赖，逐元素独立 | elewise-tiling.md |
| 输入 shape 不同（含 dim=1 轴） | Broadcast 合轴 + 四分支 | 需沿广播轴扩展 | broadcast-tiling.md |
| 归约轴是尾轴（A0=1） | AR 模式 Level 2 Reduce | 每行 R 连续 | reduction-tiling.md |
| 归约轴非尾轴（A0>1） | ARA 模式 Pattern::Reduce::RA | [R,A0] 块连续 | reduction-tiling.md |
| 合轴后多轴交替（ARAR） | 多轴嵌套循环 | 每 R 维独立 AR/ARA 判定 | reduction-tiling.md |
| 转置 + 小通道（C≤16） | small-channel transpose [C,N]→[N,C] | 重排代价非归约 | conversion-tiling.md |
| 矩阵乘 + 融合后处理 | mxfp8 matmul + eltwise 四要素 | M×N 切分 K 滚动 | matmul-tiling.md |
| SIMT 算子（非 Vector） | 核数切分 + 线程数 | 线程级并行非 UB 切分 | simt-tiling.md |

## 二、UB 容量 vs 数据量的 trade-off

**核心判据**：数据量与 UB 容量（DAV_2201≈192KB，DAV_3510 更大）的关系决定 tile 切分层级。

| 数据量 | 策略 | 启发式理由 |
|---|---|---|
| ≤ UB 单次容量 | FullLoad（整块驻留） | 无需分载，直接顺序计算 |
| > UB 但 ≤ UB×coreNum | 多核分担，每核 1 tile | 一级归并/合并即可 |
| > UB×coreNum | 两级归并 / Group Reduce | 需核内归并再跨核，减 SyncAll |

- **Sort**：tileSize 工程值 4096（实测最优），N>tileSize×coreNum → Pattern C 两级归并四阶段。
- **Reduction**：R 太大单核处理不完 + A 太小不足多核 → Group Reduce（跨核分 R + workspace 同步）。
- **Broadcast**：从最内轴向外累乘找 ubSplitAxis，`maxElemNum = (ubSize-extraSize)*8/(bufferNum*maxDtypeBits)`。

## 三、对齐粒度 trade-off

不同分支对齐要求不同，选错会性能损失或结果错误：

| 场景 | 对齐粒度 | 启发式理由 |
|---|---|---|
| OneDim / EleWise 单维 | 128B（CACHE_LINE）/ 256B（REPEAT） | Vector 指令最优 |
| Broadcast 多维 | 256B（REPEAT） | 多维 repeat |
| Broadcast UB 静态接口 | 32B（srcShape 对齐约束） | Broadcast API 硬件要求 |
| Conversion transpose | 32 元素（tileNA） | 兼顾 FP32 32B + half 16-half block |
| Sort | 32（TOPK_SORT_NUM） | Sort API 粒度 |
| MatMul ODD-N | 8 float（32B） | Fixpipe row stride |
| Reduction 索引跟踪 Compare | 256B（64 float） | Compare mask 对齐，非 32B |

## 四、多核利用率 trade-off

**核心启发式**：核利用率不足时缩小 tile 使核数翻倍，但不可无限缩小（有下限）。

- **Broadcast**：`blockNum < coreNum` → 循环缩小 maxElemNum（每次减 CACHE_LINE）直到喂满更多核。
- **OneDim**：`blockNum < coreNum/2` → 缩小 ubFormer 翻倍核数，下限开 DB 后每核 ≥8KB。
- **EleWise**：每核 ≥4KB（`MIN_TILING_BITS=32768`），否则不值得开核。
- **Conversion**：`totalTiles < coreNum` → 只开 totalTiles 个核，不做空核占位。
- **SIMT**：避免总数据量少但启动核数多（空转）；调核数而非线程数。

## 五、广播方式 trade-off（DAV_3510）

广播输入的广播方式选择是典型的性能 trade-off：

| 条件 | 选 | 启发式理由 |
|---|---|---|
| NLast + 尾轴 ≥ dcache/2 | UB BRC | NDDMA 反复读刷 dcache，UB 内 Broadcast API 更优 |
| INT8/FP16/BF16 + 尾轴 32B 对齐 | UB BRC | 满足对齐，UB API 高效 |
| 其他 | NDDMA | 硬件 stride=0 自动复制，无额外指令，搬入即结果 |
| UB 内中间结果需广播 | Dynamic UB（rank 1~9） | 非搬入阶段，只能 UB 内 API |
| DAV_2201 | UB 静态（rank 1/2）或搬运指令 fallback | 不支持 NDDMA |

> NDDMA 优势：仅占 dst 空间（搬入即结果）、无 tmpBuffer、硬件完成无额外指令。UB BRC 优势：无对齐限制（动态接口）、适合 NLast 大尾轴。trade-off 本质是 dcache 刷新开销 vs UB API 指令开销。

## 六、精度 trade-off

| 场景 | 策略 | 启发式理由 |
|---|---|---|
| EleWise FP16/BF16 Add/Sub + 未声明同量级 | 升精度 Cast→FP32→Cast | 半精度大数吃小数 |
| Reduction sum 大向量精度敏感 | 二分累加（Dichotomy） | 相近量级先加 |
| Reduction 分载 + 流式双统计量 | Welford Online | 单遍省一轮 IO |
| Reduction Max/Min | 无需二分 | 不受精度影响 |
| MatMul mxfp8 | K padding 到 64 倍数 | Cube 硬件要求 |

## 七、使用注意

- 本参考是**假设来源非事实断言**。agent 提出切分策略后，须用工具证据（AscendTilingPlanner 输出 / golden test / msprof 实测）验证，不能仅凭启发式定案。
- shape 边界条件（恰好等于 UB 容量、恰好 coreNum 倍数等）须实际计算，启发式给方向不给精确阈值。
- 各 category reference（broadcast/sort/elewise/conversion/reduction/matmul/simt）是 T2 验真事实源；本参考只综合其路由决策的 trade-off 直觉。

## 关联
- 各 category reference：`broadcast-tiling.md` / `sort-tiling.md` / `elewise-tiling.md` / `conversion-tiling.md` / `reduction-tiling.md` / `matmul-tiling.md` / `simt-tiling.md`
- 方法论主源：`tiling-methodology.md`（T1，四要素）
- AISS 自动求解：`aiss-solver.md`（T3/external，免上机求最优 tiling）
