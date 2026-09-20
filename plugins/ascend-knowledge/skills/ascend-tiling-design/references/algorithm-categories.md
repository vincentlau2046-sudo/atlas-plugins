---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-tiling-design/SKILL.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "草稿来自 cannbot ascendc-tiling-design，9 类分类表经对照 c24e8b5 重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Ascend C 算子 Tiling 分类体系

> 本文档是算子分类总览（T2，cannbot@c24e8b5 验真）。先按算子特征归入下表类别，再查该类专属 tiling 参考。本切片仅含 Reduction 类详细参考（`reduction-tiling.md`）；其余类别参考在全量 Phase C 补。

## 九大算子类别

| 类别 | 特征 | 典型算子 | 专属 tiling 支持 |
|------|------|---------|-----------------|
| **Reduction 归约类** | 沿轴归约（含索引跟踪变体） | ReduceSum, Softmax, LayerNorm, ArgMax | ✅ 完整（见 `reduction-tiling.md`） |
| **Sort 排序类** | 排序、TopK、外部归并 | Sort, ArgSort, TopK | ✅ 完整（两级 mrgsort） |
| **Elementwise 逐元素类** | 输入输出 shape 相同，逐元素独立计算 | Sin, Cos, Abs, Exp | ✅ 完整 |
| **Broadcast 广播类** | 输入 shape 不同，需广播对齐 | Add, Mul, Sub | ✅ 完整 |
| **Conversion 数据转换类** | 改变布局/形状，合并/拆分张量 | Transpose, Concat, Split | ⚠️ 部分（仅 Transpose） |
| **Random 随机类** | 生成随机数，需种子管理 | RandomUniform, Dropout | 📋 规划中 |
| **MatMul 矩阵乘类** | 矩阵乘法，高计算密度，用 Cube 单元 | MatMul, BatchMatMul | ✅ mxfp8+eltwise 融合；其它形态规划中 |
| **Convolution 卷积类** | 空间卷积，滑动窗口计算 | Conv2D, DepthwiseConv | 📋 规划中 |
| **NN 神经网络类** | 神经网络专用，多种操作组合 | FlashAttention, GroupNorm | 📋 规划中 |

## 归类决策

设计 tiling 前先归类：
1. **看计算模式**：沿轴归约 → Reduction；矩阵乘 → MatMul；逐元素独立 → Elementwise；输入 shape 不同 → Broadcast；改变布局 → Conversion。
2. **查专属参考**：归入类别后，读该类 tiling 参考取专属策略（如 Reduction 的场景路由 + Welford/Dichotomy 算法）。
3. **守四要素**：无论哪类，`tiling-methodology.md` 的四要素（多核切分/UB 切分/Buffer 规划/分支覆盖）都必须产出。

## 关联
- 方法论主源：`tiling-methodology.md`（T1，四要素 + 设计原则）
- Reduction 详细：`reduction-tiling.md`（T2，场景路由 + 算法）
- AISS 自动求解：`aiss-solver.md`（T3/external）
