---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-tiling-design/references/sort/{patterns,alg-two-level-mrgsort}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "草稿来自 cannbot ascendc-tiling-design/references/sort（2 文件），本参考抽取归并排序原理/UB约束/Pattern A-C 决策树/两级归并四阶段自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Sort 类算子 Tiling 设计

> Sort 类（Top-K / 全排序）tiling 参考（T2，cannbot@c24e8b5 验真，源 references/sort/ 2 文件）。覆盖归并排序原理、UB 容量约束、Pattern A/B/C 决策树、两级归并四阶段架构。

## 一、归并排序原理

**分治**：将无序序列递归拆分至长度 1（自然有序）→ 有序子序列两两归并逐层合并。归并排序是**稳定排序**（相同值保持原始相对顺序）。

AscendC `MrgSort` API 支持 **M 路归并**（`MRG_SORT_ELEMENT_LEN`，通常 M=4）：一次调用将 M 路有序数列归并为一条。

**并行策略**：数据量超 UB 容量时，按 UB 容量切分为多个 tile → 各核并行排序 tile（Divide）→ 多核多轮归并（Conquer）。UB 容量决定一次能排序多少元素，进而决定归并层级数。

## 二、UB 容量约束

**每元素 UB 占用**（Sort 操作需同时容纳多 buffer）：

```
sortBytesPerElem = sizeof(dtype) + sizeof(float) + sizeof(uint32_t) + PROPOSAL_SIZE
                 + concatTmpPerElem + sortTmpPerElem
```
- `PROPOSAL_SIZE = 8`（4B value + 4B index）；`PROPOSAL_FACTOR = 4`。
- float16/bf16 ≈ **34B**；float32 ≈ **32B**（无需 Cast，省类型转换 buffer）。
- `concatTmpPerElem` / `sortTmpPerElem` **必须通过 `GetConcatTmpSize` / `GetSortTmpSize` API 获取**，不应手动估算（平台相关）。

**tileSize 推导**：`tileSize = ubSize / sortBytesPerElem`，对齐到 `TOPK_SORT_NUM = 32`。工程实践中取 **4096**（实测性能最优值，留 UB 余量给对齐填充和 API 内部峰值）。

## 三、Pattern 决策树

```
给定 N(总元素数), tileSize, coreNum, K(Top-K)

Step 1: tileSize = ubSize / sortBytesPerElem，对齐 32，工程建议 4096
Step 2:
  ├─ N ≤ tileSize                          → Pattern A: 单核排序
  ├─ tileSize < N ≤ tileSize × coreNum     → Pattern B: 多核一级归并
  └─ N > tileSize × coreNum                → Pattern C: 多核两级归并
```

| Pattern | 判定 | 方案 |
|---|---|---|
| **A** | `N ≤ tileSize` | 单核 `Sort<T,true>` 一次完成，`GM→UB→Sort→GM` |
| **B** | `tileSize < N ≤ tileSize×coreNum` | 各核并行排序 tile（每核 ≤1 tile）→ 跨核归并（一级） |
| **C** | `N > tileSize×coreNum` | 各核排序多 tile → 核内归并（第一级）→ 跨核归并（第二级）→ Top-K 输出 |

> **Pattern C 为何不能直接跨核归并所有 tile**：跨核归并每轮需 `SyncAll`，直接归并 `totalTiles` 路时轮次 = `ceil(log_M(totalTiles))`，SyncAll 开销不可接受。先核内归并把路数从 totalTiles 降到 coreNum，大幅减少跨核轮次。

## 四、Pattern C 两级归并四阶段

| Phase | 职责 | 核参与 | 数据流 |
|---|---|---|---|
| **1** | 各核并行 tile 排序 | 全核 | GM→UB→Sort→workspace |
| **2** | 核内多 tile 归并（S_c 个 tile → 1 有序数列） | 全核 | workspace→UB→MrgSort→workspace |
| **3** | 跨核归并（coreNum 路 → ≤M 路） | 递减 | workspace→UB→MrgSort→workspace |
| **4** | Core 0 最终归并 + Extract 输出 | 1 核 | workspace→UB→Extract→GM |

**归并轮次**：Phase 2 = `ceil(log_M(S_c))`；Phase 3 = `ceil(log_M(coreNum)) - 1`；Phase 4 = 1 轮 ≤M-way。Phase 3 退出条件 `listNum > M`（≤M 时单次 MrgSort 完成，交 Phase 4 含 Extract 输出）。

### UB 分阶段重置

不同阶段 buffer 组合不同，分阶段分配让归并阶段用更大批次：
- Phase 1：6 buffer，34B/elem（float16）。
- Phase 1 结束 `pipe_.Reset()` → Phase 2/3：2 buffer，64B/elem，`onceMaxElementsMerge = (ubSize/64B)/32×32`（192KB→3008）。
- Phase 3 结束 `pipe_.Reset()` → Phase 4：5 buffer，104B/elem，`onceMaxElementsOutput = (ubSize/104B)/32×32`（192KB→1824）。

### workspace 双缓存 + SyncAll 时序

`workSpaceFlag` 在两半区间交替实现读写分离，每轮归并后交换。**SyncAll 时机**：Phase 1 无（0 次）；Phase 2 全部结束后（1 次）；Phase 3 每轮归并后（每轮 1 次，非每 group 后——同 group 内 M 路归并单核完成，round 内各 group 不同核并行）；Phase 4 Core 0 完成后（1 次）。总次数 = `ceil(log_M(coreNum)) + 1`。

### 截断逻辑（truncationFlag）

Top-K 只需最大 K 个。归并保证输出有序，某轮输出 ≥K 时后续只需前 K 个有效元素。`truncationFlag` 跨 Phase 2/3 持久化，**在每轮归并执行后**根据 `currentElements × M ≥ K` 设置（确保首次触发时读入完整数据），影响下一轮读入长度：false→全量 `currentElements`，true→`min(currentElements, K)`。

## 五、Tiling 切分公式

```
totalTiles     = ceil(N / tileSize)
frontCoreTiles = ceil(totalTiles / coreNum)
usedCore       = ceil(totalTiles / frontCoreTiles)
lastCoreTiles  = totalTiles - (usedCore-1) × frontCoreTiles
lastTileSize   = N - tileSize × (totalTiles-1)      # 末 tile 可能残缺
elementsPerCore= frontCoreTiles × tileSize
```

workspace 按核数分配（非按总元素数）+ 双缓存：`wsPerCoreBytes = (E_c × 8B × 2 + 31)/32 × 32`，`GetCoreWsOffset(i) = i × E_c × 2`（直接乘法）。

## 六、SortTilingData 结构

```cpp
struct SortTilingData {
    int64_t coreNum, frontCoreTiles, lastCoreTiles, totalTiles;
    int64_t elementsPerCore, tileSize, lastTileSize, totalElements;
    int64_t onceMaxElementsMerge, onceMaxElementsOutput;
};
```

## 关联
- 方法论主源：`tiling-methodology.md`（T1，四要素）
- 分类总览：`algorithm-categories.md`（T2）
