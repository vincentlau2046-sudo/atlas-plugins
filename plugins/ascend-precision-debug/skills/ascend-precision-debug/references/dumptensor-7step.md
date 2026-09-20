---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-precision-debug/references/ascendc-dumptensor.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-precision-debug/references/ascendc-dumptensor.md 抽取 DumpTensor 7 步法/desc 编号规范/使用陷阱自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# DumpTensor 7 步法（Ascend C 算子级中间结果采集）

> 本文是 **算子级快速调试的主操作参考**（T2，cannbot@c24e8b5 验真）。DumpTensor 是 Ascend C kernel 内嵌的中间 tensor 采集原语，在 CopyIn/Compute/CopyOut 关键点 dump 数据 + CPU golden 打印对比。是 ≤7 次快速方法的首选；超过 7 次切 `pypto-binary-search.md` 二分。

## 一、7 步法

### 步骤 1：在关键点添加 DumpTensor

在 kernel 的三个关键阶段插入 DumpTensor（attribution: cannbot@c24e8b5 `ascendc-dumptensor.md`）：

- **CopyIn**（搬入）后 —— 验证输入是否正确。
- **Compute**（计算）中/后 —— 逐段验证中间结果。
- **CopyOut**（搬出）前 —— 验证输出。

### 步骤 2：systematic desc 编号

dump 的 tensor 用**系统化编号 desc** 标识，便于定位：

| 编号段 | 含义 |
|---|---|
| `100–199` | 输入 tensor（CopyIn 阶段） |
| `200–299` | 中间 tensor（Compute 阶段） |
| `300–399` | 输出 tensor（CopyOut 阶段） |

> 编号要连续、不重，配合日志快速定位"第几个 dump 出错"。

### 步骤 3：CPU golden 打印

同一编号位置，CPU golden 实现打印对应 tensor，与 NPU dump 逐点对比。

### 步骤 4：先验输入

**先验证输入正确再查计算** —— 若输入就错，后续全错无意义。CopyIn dump 与 golden 输入比对，确认输入一致后再往下查 Compute。

### 步骤 5：分段验证

按 CopyIn → Compute → CopyOut 顺序逐段比对，定位首个偏差段。Compute 内若有多步，按计算顺序逐中间 tensor 推进。

### 步骤 6：误差模式分析

分析偏差 tensor 的误差模式（系统性/随机/聚集/稀疏大误差，见 `ascendc-operator-precision.md` §六），结合 9 陷阱表推断根因。

### 步骤 7：应用修复

据根因实施修复（升精度/改算法/修同步等），重跑 golden 测试验证 pass。调试完成后**移除所有 DumpTensor 代码**（见陷阱）。

## 二、使用陷阱

| 陷阱 | 说明 |
|---|---|
| **必须 DeQue 后 Dump** | DumpTensor 须在 `DeQue`（出队拿到 tensor）之后调用，**不能**在 `AllocTensor`（分配）后立即 dump —— 此时数据未填充 |
| **多核 blockIdx 编 desc** | 多核场景按 `blockIdx` 区分各核 dump，desc 编号须带核标识，避免不同核 dump 混淆 |
| **dumpSize ≤ 32** | 单次 dump 元素数建议 ≤ 32（打印可读），大数据截取首/尾/异常段 dump |
| **调试完移除** | DumpTensor 有性能开销 + 改变执行流，验证完成后必须移除全部 dump 代码，避免残留影响生产 |

## 三、调试方法选择（效率纪律）

```
精度问题
  │
  ├─ ≤7 次 → DumpTensor 7 步法（本文，快速）
  │           │
  │           └─ 定位到 → 修复 → 验证
  │
  └─ >7 次仍未定位 → PyPTO 二分定位法（pypto-binary-search.md）
                     │
                     └─ 检查点 tensor 二分找首个出错 op
```

> 快速方法够用就别上二分（二分要改 kernel 签名 + golden 返回值，成本高）。

## 四、与模型级 dump 的边界

DumpTensor 是**算子级**（单 kernel 内中间 tensor），面向单算子 golden fail。
- 模型级（整网 loss/NaN/不对齐）→ msprobe（`msprobe-usage.md` 的 L0/L1 dump）。
- 判定走模型级还是算子级 → `debug-decision-tree.md`。

## 关联

- `ascendc-operator-precision.md` — 9 陷阱表 + 7 步诊断流程 + 调试计数规则
- `pypto-binary-search.md` — 二分定位法（>7 次切此）
- `debug-decision-tree.md` — 模型级 vs 算子级判定
