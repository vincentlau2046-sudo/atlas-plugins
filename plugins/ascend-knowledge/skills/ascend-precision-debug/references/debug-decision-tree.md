---
tier: T3
confidence: heuristic
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-precision-debug/references/diagnosis-workflow.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: composite
  ref: cannbot@c24e8b5 diagnosis-workflow + msprobe@6824676 best_practices
  note: "综合 cannbot 算子级诊断流程 + msprobe 模型级定位方法论自撰的判定决策树；基础事实可验（两源均已验真：cannbot@c24e8b5 + msprobe@6824676），但模型级 vs 算子级的判定边界是启发式综合，非单一源事实断言"
license: CANN-OSL-2.0
---

# 精度调试判定决策树（模型级 vs 算子级）

> 本文是 **T3 启发式决策参考**（composite：cannbot 算子级诊断 + msprobe 模型级方法论）。**假设来源非事实断言** —— 基础事实（两源）可验，但"何时走模型级、何时走算子级"的判定边界是综合启发式，须结合实际症状取舍。读 `msprobe-best-practices.md`（模型级）+ `ascendc-operator-precision.md`（算子级）后用本文做路径选择。

## 一、第一问：症状在模型级还是算子级？

```
精度问题
  │
  ├─ 整网症状（模型级）？
  │   ├─ 训练：loss NaN/尖刺/不对齐/gradnorm NaN/首step差异/长稳差异
  │   └─ 推理：乱码/重复/语义断裂/输出抖动/评测不达标
  │   → 走模型级（msprobe）
  │
  └─ 单算子症状（算子级）？
      ├─ 单算子 golden 测试 fail
      ├─ FP32 pass / FP16 fail
      └─ msprobe compare 定位到某 API 后转单算子验证 fail
      → 走算子级（DumpTensor / PyPTO 二分）
```

## 二、模型级路径（msprobe）

适用整网症状。链路：

1. **CheckList 排除非算子因素**（`msprobe-best-practices.md` §3.1/§5）：超参/环境变量 → 三方库版本 → 数据读取 → 模型结构/配置 → 权重初始化 → 环境版本。
2. **复现前置**：`seed_all()` + `torch.use_deterministic_algorithms(True)` + `HCCL_DETERMINISTIC=TRUE` + `shuffle=False`。
3. **dump**：训练侧 `PrecisionDebugger`（`msprobe-usage.md` L0/L1/mix）；推理侧 ATB `load_atb_probe.sh`（`msprobe-infer-dump.md`）。
4. **比对**：`msprobe compare -tp <npu> -gp <golden> -da`（`msprobe-compare.md`）定位**首差异** API/层。
5. **转判**：首差异是单算子且单算子验证 fail → 转算子级；否则留模型级按 CheckList 修。

## 三、算子级路径（DumpTensor / PyPTO）

适用单算子症状。链路：

1. **误差模式分析**（`ascendc-operator-precision.md` §六）：系统性/随机/聚集/稀疏大误差 → 推断根因类别。
2. **查 9 陷阱表**（`ascendc-operator-precision.md` §三）：FP16 精度/溢出/减法抵消/Reduce/除零/硬件约束/类型转换/Cast RoundMode/输出全0。
3. **快速定位**（≤7 次）：DumpTensor 7 步法（`dumptensor-7step.md`）—— CopyIn/Compute/CopyOut 关键点 dump + CPU golden 对比 + desc 编号（100-199/200-299/300-399）。
4. **二分定位**（>7 次）：PyPTO 二分定位法（`pypto-binary-search.md`）—— 检查点 tensor 二分找首个出错 op。
5. **判 pass/fail**：按 `precision-standard.md` 阈值（MERE/MARE + dtype/分级）。
6. **修复 + 验证**：实施修复，重跑 golden 测试。

## 四、关键判定信号

| 信号 | 倾向 | 依据 |
|---|---|---|
| loss/gradnorm NaN 或尖刺 | 模型级 | msprobe train_debug_guide 现象分类 |
| 推理乱码/重复 | 模型级（多实践错误） | msprobe infer_debug_guide |
| 单算子 numpy golden fail | 算子级 | cannbot golden test 范式 |
| FP32 pass / FP16 fail | 算子级（FP16 精度/溢出） | cannbot 诊断模式 |
| msprobe compare 首差异=单 API | 转算子级 | msprobe compare `-da` |
| msprobe compare 首差异=结构/超参 | 留模型级 | msprobe CheckList |
| 输出全 0 | 算子级（流水线同步/DataCopy 对齐） | cannbot common-traps #9 |

## 五、常见误判（Gotchas）

- **模型级症状误判为算子级**：loss 不对齐常源于超参/三方库/数据读取（msprobe 统计大部分精度问题源于非算子因素），直接钻单算子会浪费工时 —— 先过 CheckList。
- **算子级症状误判为模型级**：单算子 FP16 溢出也会引发整网 NaN，但根因在算子 —— msprobe compare 定位到首差异 API 后须转单算子验证。
- **数值偏差 ≠ 精度问题**：不同硬件细微数值偏差在容限内属正常（`precision-standard.md` 阈值内 pass），勿过度定位。
- **工具副作用 ≠ 真实问题**：msprobe 的 item 同步/hook 可能略改 loss/gnorm，DumpTensor 改执行流 —— 区分工具副作用与真实精度问题。

## 六、工具对照速查

| 层级 | 工具 | 形态 | 采什么 |
|---|---|---|---|
| 模型级（训练） | msprobe PrecisionDebugger | Python API | L0 模块 / L1 API / mix |
| 模型级（推理） | msprobe load_atb_probe.sh | sourced shell | op（Operation/Kernel） |
| 模型级（比对） | msprobe compare | CLI 子命令 | 逐 API MERE/MARE |
| 算子级（快速） | DumpTensor | kernel 内嵌原语 | 中间 tensor（CopyIn/Compute/CopyOut） |
| 算子级（二分） | PyPTO 二分 | jit + 检查点 tensor | 首个出错 op |
| 算子级（golden） | AscendGoldenTest | T0 Tool | numpy ref vs NPU |

> ⚠️ 本决策树的"层级判定边界"是启发式综合（T3），非单一官方源的事实断言。实际定位时以两源原文（`msprobe-best-practices.md` + `ascendc-operator-precision.md`）为准，本文做路径选择的启发式参考。

## 关联

- `msprobe-best-practices.md` — 模型级定位方法论（本文模型级路径的依据）
- `ascendc-operator-precision.md` — 算子级根因（本文算子级路径的依据）
- `msprobe-usage.md` / `msprobe-infer-dump.md` / `msprobe-compare.md` — 模型级工具链
- `dumptensor-7step.md` / `pypto-binary-search.md` — 算子级工具链
- `precision-standard.md` — pass/fail 判据
