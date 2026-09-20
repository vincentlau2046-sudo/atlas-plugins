# Tiling Design Document Template

> 自撰模板（AtlasHarness 自有许可，非外部源）。算子 tiling 设计文档（DESIGN.md）的四要素骨架。按本模板撰写后逐项自检；配合 `references/tiling-methodology.md` 四要素方法论 + 算法类专属 reference 使用。

## 算子信息

| 项 | 值 |
|---|---|
| 算子名 | |
| 输入 shape(s) | |
| 输出 shape(s) | |
| dtype | |
| 硬件 / 芯片 | DAV_2201 (910B) / DAV_3510 (950) |
| 算法类 | Reduction / Sort / EleWise / Broadcast / Conversion / MatMul / Conv / NN / SIMT（见 algorithm-categories.md） |

## 一、多核切分

- 切分维度：____（哪个轴参与核间切分，K 轴通常核内迭代不参与）
- 单核任务量：`singleCoreX = ____`
- 核数计算：`usedCoreNum = CeilDiv(____, ____)`（**动态计算，禁硬编码**）
- 负载均衡策略：____（蛇形调度 / 均分 / batch 优先并行）
- 尾核处理：____

**自检**：[ ] 切分方案 [ ] singleCore 取值 [ ] 核数动态计算

## 二、UB 切分

- UB 容量：DAV_2201 = 192KB / DAV_3510 = 248KB
- `maxElemNum = (ubSize - extraSize) * 8 / (bufferNum * maxDtypeBits)`
- 对齐粒度：____（128B CACHE_LINE / 256B REPEAT / 32B / 32 元素，按算子类定）
- `ubFormer / ubOuter / ubTail`：____
- `ubSplitAxis`：____（从最内轴向外累乘找放不下的轴）
- 核利用率不足时缩小策略：____（每次减 CACHE_LINE / 翻倍核数，下限 ____）

**自检**：[ ] ubFormer 取值 + 算式 [ ] 对齐方案 [ ] ≤ UB 上限 [ ] 核利用率优化

## 三、Buffer 规划

| Buffer | dtype | 大小 | 用途 | Queue/TBuf |
|---|---|---|---|---|
| | | | | |

- bufferNum（存活节点数）：____
- Double Buffer：____（开 / 不开，原因）
- 总 UB 用量：`____ ≤ UB_SIZE`
- tmpBuffer（如需）：`____`（由 API Get*TmpSize 获取，禁手动估算）
- 静态偏移分配 vs TPipe：____（融合算子禁 TPipe 用静态偏移）

**自检**：[ ] buffer 清单 [ ] 无冲突 [ ] 总 UB 用量 [ ] DB 策略

## 四、分支覆盖

| 分支维度 | 条件 | 处理策略 |
|---|---|---|
| dtype | FP32 / FP16 / BF16 / INT8 | |
| shape 大小 | 满核 / 不满核 / 单核 / 边界 | |
| 对齐 | 32B 对齐 / 非对齐 | |
| 尾块 | ODD-M / ODD-N / 残缺 tile | |
| 转置（如适用） | NN / NT / TN / TT | |

**自检**：[ ] dtype 组合 [ ] 大小 shape [ ] 对齐 [ ] 尾块 [ ] 转置

## 算法类专属

- 归入算法类：____
- 引用专属 reference：`references/<category>-tiling.md`
- 专属算法/分支：____（如 Reduction → Welford/Dichotomy/Group Reduce/With-Index；Sort → Pattern A/B/C；Broadcast → 四分支；MatMul → SWAT/StreamK/variants）

## 产出 Gate

- [ ] 多核切分（切分维度 + 单核任务 + 动态核数 + 负载均衡）
- [ ] UB 切分（ubFormer + 容量算式 ≤ 上限 + 对齐）
- [ ] Buffer 规划（清单 + 无冲突 + 总用量 + DB）
- [ ] 分支覆盖（dtype/shape/对齐/尾块/转置枚举）
- [ ] 算法类匹配（归入 9 类 + 引用专属算法）
