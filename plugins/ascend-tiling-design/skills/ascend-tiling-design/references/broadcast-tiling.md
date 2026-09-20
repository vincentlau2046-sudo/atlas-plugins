---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-tiling-design/references/broadcast/{patterns,ub-broadcast,dynamic-ub-broadcast,nddma-broadcast,onedim}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "草稿来自 cannbot ascendc-tiling-design/references/broadcast（5 文件），本参考抽取合轴/场景路由/UB·多核切分/四分支 API 自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Broadcast 类算子 Tiling 设计

> Broadcast 类（输入 shape 不同、需沿 dim=1 轴扩展）tiling 参考（T2，cannbot@c24e8b5 验真，源 references/broadcast/ 5 文件）。覆盖合轴前置、四分支路由、UB/多核切分公式。

## 一、合轴（DimensionCollapse，所有分支公共前置）

目的是减少维度以简化 Kernel 循环。四步：

1. **补维**：输入 shape 维度不足输出时，左侧补 1。
2. **标记广播轴**：为每个轴计算 flag 位图，第 j 个输入在该轴 dim=1 → flag 第 j bit 置 1。
3. **合并相邻同 flag 轴**：相邻两轴所有输入 flag 相同 → 合并（维度相乘）。
4. **计算 stride**：从右到左累乘；广播轴（dim=1 而输出 dim>1）stride 置 0。

**示例**：`Add(x=[4,3,8], y=[1,3,8])` → 合并轴 1/2（flag 均为 00）→ `x=[4,24] strides[24,1]`、`y=[1,24] strides[0,1]`（轴 0 stride=0 需广播）、`out=[4,24]`。

## 二、场景判定流程

```
合轴后维度？
├─ 1 维 → OneDim（纯 Elementwise，可能有标量输入）
└─ > 1 维 → 选择广播方式：
    ├─ DAV_2201 → UB Broadcast 静态接口（rank 1/2），不满足对齐约束时用搬运指令 fallback
    └─ DAV_3510 → 广播发生在哪个阶段？
        ├─ GM→UB 搬入阶段 → NDDMA 或 UB BRC（见决策链）
        └─ UB 内部（中间计算结果需广播）→ Dynamic UB Broadcast（rank 1~9）
```

**DAV_3510 搬入阶段广播方式决策链**（按优先级）：

| 优先级 | 条件 | 选择 |
|---|---|---|
| 1 | 用户强制指定 NDDMA 或 UB BRC | 遵从 |
| 2 | NLast 场景，尾轴 ≥ dcache/2 | UB BRC（Dynamic UB） |
| 3 | dtype INT8/FP16/BF16 且尾轴 32B 对齐 | UB BRC（Dynamic UB） |
| 4 | 其他 | NDDMA |

> **NLast** = 尾轴不需广播（stride≠0）但非尾轴需广播（stride=0）。尾轴数据量大时 NDDMA 反复读刷 dcache，不如 UB 内 Broadcast API。

## 三、通用切分公式（所有分支共用）

**UB 切分**（从最内轴向外累乘，找第一个放不下的轴作 ubSplitAxis）：

```
maxElemNum = (ubSize - extraSize) * 8 / (bufferNum * maxDtypeBits)
maxElemNum = floor_align(maxElemNum, 256 * 8 / minDtypeBits)   # 256B repeat 对齐

curProduct = 1; ubSplitAxis = 0; allFit = true
for i = shapeLen-1 downto 0:
    curProduct *= dims[i]
    if curProduct > maxElemNum: ubSplitAxis = i; curProduct /= dims[i]; allFit = false; break
if allFit: curProduct /= dims[0]           # 全放得进，在最外维切分
ubFormer = maxElemNum / curProduct
ubOuter  = ceil(dims[ubSplitAxis] / ubFormer)
ubTail   = dims[ubSplitAxis] - (ubOuter-1) * ubFormer
```

**多核切分**（ubSplitAxis 及其外层轴展平均分）：

```
fusedProduct = ubOuter × (ubSplitAxis 之前所有轴乘积)
blockFormer  = ceil(fusedProduct / coreNum)
blockNum     = ceil(fusedProduct / blockFormer)
blockTail    = fusedProduct - (blockNum-1) * blockFormer
```

核利用率不足（`blockNum < coreNum`）时循环缩小 maxElemNum（每次减 CACHE_LINE）重算，直到喂满更多核。

**对齐**：OneDim 128B（CACHE_LINE）；多维 256B（REPEAT）。

## 四、OneDim 分支（合轴后单维）

本质 Elementwise，线性处理。标量输入（合轴后 dim=1）优先用 **TensorScalar 接口**（Adds/Muls 等，省 Duplicate + 省 1 buffer），无对应接口才 Duplicate 展开为向量 + TensorTensor。

- `scalarFlag` 位图：合轴后某输入 dims[i][0]==1 → 该输入标量，`scalarFlag |= (1<<i)`。
- UB 切分按 128B 对齐：`ubFormer = (ubFormerByte / CACHE_LINE) * CACHE_LINE / maxDtypeBytes`。
- 核利用率低（`blockNum < coreNum/2`）时缩小 ubFormer 翻倍核数，下限开 DB 后每核 ≥8KB。

## 五、UB Broadcast 静态接口（DAV_2201，DAV_3510 也可用）

搬入未广播数据 → UB 内 `Broadcast()` API 扩展 → 计算。dim/axis 为编译期模板参数，仅支持 **1D/2D、axis=0/1**。

```cpp
Broadcast<T, dim, axis>(dstLocal, srcLocal, dstShape, srcShape, tmpBuffer);
// 或框架自动申请 tmpBuffer 版本
Broadcast<T, dim, axis>(dstLocal, srcLocal, dstShape, srcShape);
```

**约束**：dim=2,axis=0 时 srcShape[1] 须 32B 对齐；dim=2,axis=1 时 srcShape[0] 须 32B 对齐；src/dst 不能重叠。tmpBuffer 大小由 `GetBroadCastMaxMinTmpSize(platform, srcShape, dstShape, sizeof(T), false, maxTmpSize, minTmpSize)` 获取。

**搬运指令 fallback**（不满足对齐约束时，省 tmpBuffer、搬运流水完成广播）：
- axis=-1（`(M,1)→(M,N)`）：DataCopyPad blockLen=sizeof(T) 用首元素值 dummy 填充到 32B → Copy(srcStride=0) 扩展 → GatherMask 裁剪。
- axis=-2（`(1,N)→(M,N)`）：DataCopyPad 搬入单行（自动 32B 对齐）→ Copy 行复制 → GatherMask 裁剪。

> ⚠️ 对齐判断用**原始 shape 维度值 × sizeof(T)**，不是 DataCopyPad 搬到 UB 后的对齐值。

## 六、Dynamic UB Broadcast（DAV_3510，rank 1~9）

无 32B 对齐限制，任意轴运行时广播。API 两步：Host/Kernel 侧 `GetBroadcastTilingInfo<T>(rank, dstShape, srcShape, false, tiling)` 算 tiling → `Broadcast<T>(dstLocal, srcLocal, dstShape, srcShape, &tiling)` 执行。

- rank ∈ [1,9]；srcShape[i]=1 且 dstShape[i]>1 时该轴广播。
- src/dst 不能重叠；srcInnerPad 当前仅支持 false。
- dtype 支持 int8/uint8/int16/uint16/half/bfloat16/int32/uint32/float/int64/uint64。
- Tiling 参数计算、多核切分、多维索引管理与静态接口完全相同。

## 七、NDDMA Broadcast（DAV_3510，GM→UB 搬入阶段）

通过 NDDMA 硬件 stride=0 配置自动广播，数据到达 UB 时已是广播后完整 tile。**DAV_2201 不支持 NDDMA**。

```cpp
// NDDMA 最大 5 维
AscendC::MultiCopyParams<T, 5> params = {loopInfo, constValue};
static constexpr AscendC::MultiCopyConfig config = {false, 0, 0, false};
AscendC::DataCopy<T, 5, config>(localTensor, globalTensor[gmOffset], params);
// loopInfo.loopSrcStride[i]=0 → 硬件在该轴重复读不推进地址
```

**两种模式**（按 UB 切分后剩余轴数 `axisInsideUB = shapeLen - ubSplitAxis`）：
- **WithoutLoop**（schMode=1，axisInsideUB ≤ 5）：一次 DataCopy 完成。
- **WithLoop**（schMode=2，axisInsideUB > 5）：最内 5 维交 NDDMA，外层轴 Kernel for-loop 遍历。

**优化**：某广播输入 `inputStrides[ubSplitAxis] == outputStrides[ubSplitAxis]`（该输入在切分轴无需广播）→ 退化为普通 DataCopyPad。CopyBrc 节点 3~4 时可合并相邻同广播模式轴减 NDDMA 调用数。

## 八、四分支对比

| 维度 | OneDim | UB 静态 (DAV_2201) | Dynamic UB (DAV_3510) | NDDMA (DAV_3510) |
|---|---|---|---|---|
| 广播时机 | 无（标量用 TensorScalar） | 搬入后 UB 内 API | 搬入后 UB 内 API | 搬入时硬件自动 |
| rank/维度 | 1 维 | 1D/2D, axis 0/1 | rank 1~9 | ≤5 维（>5 外层循环） |
| 对齐 | 128B | 32B 约束 | 无 | stride=0 语义 |
| UB 占用 | 标量省 1 buf | src+dst+tmp | src+dst | 仅 dst（搬入即结果） |
| tmpBuffer | 无 | 需要 | Tiling 内部管理 | 不需要 |

## 关联
- 方法论主源：`tiling-methodology.md`（T1，四要素）
- 分类总览：`algorithm-categories.md`（T2，9 类 support status）
