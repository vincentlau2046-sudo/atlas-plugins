---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-tiling-design/references/conversion/patterns.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "草稿来自 cannbot ascendc-tiling-design/references/conversion/patterns.md，本参考抽取 small-channel transpose 统一建模/路由/tiling 参数/UB 预算/offset table 自撰重写；cannbot conversion 仅展开 transpose 这一支，其余 conversion 子场景待补；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Conversion 类算子 Tiling 设计

> Conversion 类 tiling 参考（T2，cannbot@c24e8b5 验真，源 references/conversion/patterns.md）。cannbot 当前仅展开 **small-channel transpose** 这一支（合轴/routing/unified modeling/offset table）；其余 conversion 子场景待补。

## 一、适用场景（small-channel transpose）

- 输入输出元素总数相同，但维度顺序重排（transpose / permute / NCHW→NHWC / `[M,N]→[N,M]`）。
- 核心代价来自数据重排，非跨元素归约。
- 通道维较小，先按 `C ≤ 16` 判断；其余维度展平成一条长轴 `N`。
- kernel 按 `[C, N] → [N, C]` 理解。

## 二、合轴（统一建模）

把问题整理成：

```
输入:  [C, N]      # C = 小通道维，N = 展平后长轴
输出:  [N, C]
```

- 先保留被转到末维或首维的那组小通道轴，合成总通道数 `C`。
- 其余轴保持原有相对顺序，合成一条长轴 `N`。
- 例：`[3, H, W] → [H, W, 3]` → `C = 3, N = H × W`。

> 若被移动的轴在目标布局中不再相邻，或 transpose 后混入更复杂 layout 变换，不要强行套这条分支。

## 三、路由原则

| 路线 | 是否优先 | 原因 |
|---|---|---|
| TransDataTo5HD + Gather 融合实现 | ✅ 优先 | small-channel 融合场景高效 |
| 通用 transpose 高级 API | ❌ | small-channel 融合场景内部固定开销可能过大 |
| 标量抽取再重排（GetValue/SetValue） | ❌ | 吞吐太差 |
| 逐像素 DMA 提取 | ❌ | blockLen 太小，DMA setup 成本占主导 |

若问题除 transpose 外还带逐元素后处理或类型转换，可放到同一 tile pipeline 一起实现。

## 四、Tiling 核心参数

| 参数 | 含义 |
|---|---|
| `C` | 小通道维 |
| `N` | 展平后长轴 |
| `tileN` | 每个 tile 处理的有效元素数 |
| `tileNA` | `tileN` 对齐后 UB 宽度 |
| `repeats` | TransDataTo5HD 重复次数 |
| `totalTiles` | 总 tile 数 |
| `blockDim` | 实际使用 vector core 数 |

**对齐规则**：

```cpp
tileNA  = AlignUp(tileN, 32);     // 兼顾 FP32 32B 对齐 + half vnchwconv 16-half block
repeats = tileNA / 16;
```

> `tileNA` 属 host/tiling 口径；尾块执行时 `repeats` 按 `AlignUp(curN, 16)/16` 计算（runtime tail-tile 口径，与固定 tile 宽度不冲突）。

## 五、UB 预算公式

```
ubBytes = tileNA * (16 * C + 32)      # 拆解：VECIN 双缓冲(2*C*tileNA*4) + VECOUT 双缓冲(2*C*tileNA*1)
                                      #        + half 中间(C*tileNA*2) + vnchwconv 输出(16*tileNA*2) + offset table(C*tileNA*4)
# C = 3 时：ubBytes = tileNA * 80
```

**repeat 上限**：`repeats = tileNA/16 ≤ 255` → `tileNA ≤ 4080`。`tileN` 须同时满足 UB 容量约束、`repeats ≤ 255`、向量对齐。

## 六、tile 大小计算

```cpp
uint32_t ubBudget  = ubSize - reservedBytes;
uint32_t perElemBytes = 16 * C + 32;
uint32_t tileNMax  = AlignDown(ubBudget / perElemBytes, 32);
tileNMax = Min(tileNMax, 255 * 16);                    // 同时满足 UB 和 repeats 上限

uint32_t tileN = AlignUp(CeilDiv(N, blockDim), 32);    // 先按目标核数均分
if (tileN > tileNMax) {                                 // 放不下 → 增 tile 数铺满核
    uint32_t minTiles = CeilDiv(N, tileNMax);
    uint32_t alignedTiles = CeilDiv(minTiles, blockDim) * blockDim;
    tileN = AlignUp(CeilDiv(N, alignedTiles), 32);
}
```

目标：单 tile 尽量大减调度开销，但总 tile 数足够多铺满所有核。

## 七、多核切分

```cpp
blockDim     = Min(coreNum, totalTiles);     // totalTiles = CeilDiv(N, tileN)
tilesPerCore = CeilDiv(totalTiles, blockDim);
startTile    = blockIdx * tilesPerCore;
endTile      = Min(startTile + tilesPerCore, totalTiles);
```

`totalTiles < coreNum` 时只开 `totalTiles` 个核，不做空核占位。

## 八、offset table 设计

Gather 所需 offset 在 device 侧提前生成（TBuff，全局只申请一次，后续 tile 复用）：

```cpp
for (uint32_t p = 0; p < tileNA; ++p)
    for (uint32_t c = 0; c < C; ++c)
        offsetBuff.SetValue(p * C + c, (p * 16 + c) * sizeof(half));
```

- offset 表按**对齐后 `tileNA`** 构建（非 `tileN`）；每个 16-half block 只前 `C` 个位置有效。
- `C` 变化时 offset table 必须重建，不要硬编码成某通道数常量表。

## 九、Kernel 执行骨架

```cpp
for (uint32_t t = startTile; t < endTile; ++t) {
    CopyIn(t);    // GM→UB，按通道连续搬运 [C, tileN]（非逐像素 gather）
    Compute(t);   // elementwise → round → half → vnchwconv → gather
    CopyOut(t);   // UB→GM，写回 [tileN, C]，非对齐优先 DataCopyPad
}
```

## 十、设计检查表

- [ ] 已统一建模为 `[C, N] → [N, C]`
- [ ] 如需融合，问题命中已展开分支
- [ ] `tileN` 按 32 对齐
- [ ] `tileNA/16` 满足 `repeats ≤ 255`
- [ ] UB 预算用 `tileNA * (16*C + 32)` 公式
- [ ] `totalTiles` 足够铺满核
- [ ] `blockDim` 受 `totalTiles` 限制
- [ ] offset table 按 `tileNA` 构建
- [ ] 尾块保留 `curN` 与 `tileNA` 区分
- [ ] transpose 与后处理融合在同一 tile pipeline

## 关联
- 方法论主源：`tiling-methodology.md`（T1，四要素）
- 分类总览：`algorithm-categories.md`（T2，9 类 support status）
