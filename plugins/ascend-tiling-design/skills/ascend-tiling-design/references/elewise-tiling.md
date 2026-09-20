---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-tiling-design/references/elewise/{patterns,tiling}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "草稿来自 cannbot ascendc-tiling-design/references/elewise（2 文件），本参考抽取场景路由/多核·UB切分/升精度分支 UB 预算自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# EleWise 类算子 Tiling 设计

> EleWise（Elementwise）类 tiling 参考（T2，cannbot@c24e8b5 验真，源 references/elewise/ 2 文件）。输入输出 shape 完全相同、逐元素独立计算、无跨元素依赖（Sin/Cos/Abs/Add/Mul 等均可，不区分一元/二元）。

## 一、场景判定

```
给定: N 个输入 shape + M 个输出 shape

Step 1 — Shape 判定:
  所有输入输出 shape 完全相同？
    ├─ YES → EleWise，展平为 dim0，1D 线性处理 → Step 2
    └─ NO  → Broadcast → broadcast-tiling.md

Step 2 — dtype × 运算 判定（决定 Compute 路径）:
  运算为 Add/Sub / 以加减为主的累加链路 AND dtype ∈ {FP16, BF16} AND spec 未声明"输入同量级"？
    ├─ YES → 升精度分支：Cast→FP32 计算→Cast，需额外 K 份 FP32 中间 Buffer
    └─ NO  → 原 dtype 直接计算分支
```

> 半精度"大数吃小数"问题需升精度规避。K 值与 Cast 写法属 API 实现细节，tiling-design 负责宏观切块（分支判定、UB 预算、ubFormer），乘法/除法等暂未覆盖，沿用原 dtype 直算分支。

## 二、多核切分（blockFormer / blockNum）

确保每核处理量 ≥ 最小阈值，按 512 元素对齐。

```
coreNum = (dim0 * minDtypeBits + MIN_TILING_BITS - 1) / MIN_TILING_BITS   # MIN_TILING_BITS=32768 (4KB, 单位 bits)
coreNum = min(coreNum, availableCoreNum)

blockFormer = ((dim0 + coreNum - 1) / coreNum + ELEM_ALIGN_FACTOR - 1)    # ELEM_ALIGN_FACTOR=512
             / ELEM_ALIGN_FACTOR * ELEM_ALIGN_FACTOR
blockNum = (dim0 + blockFormer - 1) / blockFormer
```

核间偏移：`CalcBlockOffset() = blockFormer * GetBlockIdx() * sizeof(DataType)`。

## 三、UB 切分（ubFormer / ubLoop / tail）

确保 UB 处理量是 256B 整数倍（Vector 指令最优）。

```
bufferDivisor = bufferNum * elemBytes
maxElemNum    = (ubSize - extraSize) * 8 / bufferDivisor
alignFactor   = REPEAT_BYTES * 8 / minDtypeBits        # REPEAT_BYTES=256，FP32 → 64 元素
ubFormer      = (maxElemNum / alignFactor) * alignFactor

ubLoopOfFormerBlock = (blockFormer + ubFormer - 1) / ubFormer
ubTailOfFormerBlock = blockFormer - (ubLoopOfFormerBlock - 1) * ubFormer
# 尾 block 同理：blockTail = dim0 - (blockNum-1)*blockFormer → ubLoopOfTailBlock / ubTailOfTailBlock
```

**Kernel 执行模型**区分首/尾 block（循环次数和 tail 可能不同）：

```cpp
bool isLastBlock = (blockIdx == blockNum - 1);
loopNum = isLastBlock ? ubLoopOfTailBlock : ubLoopOfFormerBlock;
tailNum = isLastBlock ? ubTailOfTailBlock : ubTailOfFormerBlock;
for (i = 0; i < loopNum - 1; i++) { ProcessTile(offset, ubFormer); offset += ubFormer; }
ProcessTile(offset, tailNum);   // 尾部不完整 UB 块
```

## 四、升精度分支 UB 预算（FP16/BF16 Add/Sub）

在原 dtype Queue 之外额外引入 **K 份 `ubFormer × sizeof(float)` 的 FP32 中间 Buffer**（K 由 API 别名约束给出，tiling 阶段作参数代入）：

```
# 原直算分支
bufferDivisor = bufferNum * elemBytes

# 升精度分支：bufferNum 份半精度 + K 份 FP32
bufferDivisor = bufferNum * elemBytes + K * sizeof(float)
maxElemNum    = (ubSize * 8) / bufferDivisor
alignFactor   = ALIGN_256 * 8 / elemBytes     # 对齐仍按输入 dtype
ubFormer      = (maxElemNum / alignFactor) * alignFactor
```

> 升精度分支不新增 TilingData 字段，Kernel 侧按 dtype 模板参数静态选择分支。Cast/Add/Sub 调用、RoundMode、别名写法属 API 实现细节。

## 五、TilingData 模板

```cpp
struct TilingData {
    int64_t dim0, blockFormer, blockNum, ubFormer;
    int64_t ubLoopOfFormerBlock, ubTailOfFormerBlock;
    int64_t ubLoopOfTailBlock, ubTailOfTailBlock;
    int32_t coreNum;
};
```

## 六、经验总结

| 经验 | 值 | 代码模式 |
|---|---|---|
| 最小粒度 | 每核 ≥4KB，否则不值得开核 | `MIN_TILING_BITS = 32768` |
| 多核对齐 | 元素数对齐 512 倍数 | `(原始值 + 511) / 512 * 512` |
| UB 对齐 | 256B，Vector 指令效率 | `alignFactor = 256 / elemBytes`（FP32=64） |
| 跨核偏移 | `blockFormer * blockIdx` | `CalcBlockOffset()` |

## 关联
- 方法论主源：`tiling-methodology.md`（T1，四要素）
- Broadcast 场景（输入 shape 不同）：`broadcast-tiling.md`
- 分类总览：`algorithm-categories.md`（T2）
