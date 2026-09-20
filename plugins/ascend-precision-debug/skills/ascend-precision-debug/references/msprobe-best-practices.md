---
tier: T2
confidence: verified
source-of-truth:
  repo: msprobe
  sha: 6824676473debc2adfe868751fddfd270ce9c9a6
  path: docs/zh/best_practices/{train_debug_guide,infer_debug_guide}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: official-doc
  ref: https://gitcode.com/Ascend/msprobe@6824676
  note: "从 msprobe 官方 best_practices/train_debug_guide.md(1771L)+infer_debug_guide.md 抽取训练/推理精度问题分类/现象/CheckList/复现前置方法论自撰重写；MulanPSL-2.0，方法论提炼非逐字 vendor"
license: MulanPSL-2.0
---

# 大模型精度定位方法论（训练 + 推理）

> 本文是 **模型级精度定位的方法论主源**（T2，msprobe@6824676 best_practices 验真）。覆盖训练侧（loss/NaN/尖刺）与推理侧（乱码/重复/语义断裂）的统一定位思路。配合 `msprobe-usage.md`（dump）+ `msprobe-compare.md`（比对）使用。

## 一、精度问题二分（训练 + 推理通用）

精度问题分两大类，成因与处置策略不同（attribution: msprobe@6824676 train/infer_debug_guide）：

| 类别 | 性质 | 成因 | 影响 |
|---|---|---|---|
| **模型精度问题** | 结构性偏差 | 数据加载异常 / 超参配置失误 / 网络结构实现错误 / 框架设计缺陷 | 对收敛/输出有决定性影响，须逐环节排查 |
| **数值精度问题** | 计算性偏差 | 浮点有限字长 / 计算序与通信序差异 / 数学表达式近似 | 不必然导致收敛失败，容限内属正常 |

> **关键认知**：不同硬件（GPU vs CPU、GPU 各版本）同样计算逻辑产生细微数值偏差是**正常**的，只要控制在合理容限内不影响最终收敛。先区分"正常计算差异"与"异常精度问题"，再定位根因。

## 二、训练侧：常见问题现象

迁移场景（NPU vs 标杆 GPU/NPU）下，不对齐现象分 5 类：

1. **溢出 / NaN**：相较标杆更频繁出现 Loss 或 Grad Norm 溢出、NaN。
2. **首 Step Loss 差异**：第 0 步或前几步 Loss 与标杆差异 > 1%。
3. **长稳 Loss 差异**：前期拟合，后期与标杆差异渐大，平均误差 > 1%。
4. **尖刺**：相较标杆更频繁出现 Loss/Grad Norm 陡增又快速跌落。
5. **Loss 小但下游任务差**：Loss 与标杆差异小，但下游任务效果变差。

> 同一现象根因复杂各异，须按 CheckList 逐项排除。

## 三、训练侧：定位步骤

### 3.1 CheckList（排除非算子因素）

定位前先排除非算子因素干扰（大部分精度问题源于此）：

- **训练超参 + 环境变量比对**：Beyond Compare 或脚本比对工具比对双方启动脚本/日志的超参与环境变量。
- **三方库版本比对**：`git` 分支查 MindSpeed-LLM/Megatron/DeepSpeed 版本对齐；`pip list` 查 PyTorch/TorchNPU 版本对齐。
- **数据读取检查**：精度工具采最开始输入数据，或 forward 时打印传入 tensor。
- **模型结构检查**：双方直接打印模型结构比对。
- **权重初始化对齐**：确认加载同一预训练模型或同随机种子（`seed_all`）。
- **环境版本更新**：条件允许可升 CANN/驱动/TorchNPU 最新版（很多问题旧版已修）。

### 3.2 问题复现前置（固定随机性 + 确定性）

排除非算子因素后，复现问题、缩变量：

- **固定随机种子**：`np.random.seed` / `torch.manual_seed` / `torch_npu.npu.manual_seed`；关闭 Dropout；`shuffle=False`。
- **工具固定**：`msprobe.seed_all()` 一次性固定所有随机种子 + Dropout + 算子/通信确定性（除 shuffle）。
- **算子计算确定性**：`torch.use_deterministic_algorithms(True)`。
- **通信确定性**：`export HCCL_DETERMINISTIC=TRUE`。
- ⚠️ 不是所有算子都支持确定性计算，特殊算子参考算子确定性问题单独定位。

### 3.3 dump + 比对

复现后用 `PrecisionDebugger`（`msprobe-usage.md`）采 NPU + 标杆 dump → `msprobe compare -da`（`msprobe-compare.md`）定位首差异层 → 转算子级或结构排查。

## 四、推理侧：常见问题现象

推理精度问题体现在输出不符合预期，5 类现象：

1. **乱码**：输出大量 `�` / `<unk>` / `â€™` 异常符号或插入他语言字符。
2. **重复**：局部卡住，不断重复相同/相似文本。
3. **语义断裂**：局部通顺但整体逻辑不连贯、推理链中断。
4. **不一致/抖动**：多次请求输出差异巨大。
5. **评测不达标**：数据集评测正确率相较标杆下降。

推理部署中精度问题**以实践错误为主**。

## 五、推理侧：实践错误 5 类

1. **模型配置**：权重错误（影响 WordEmbedding/Linear/LayerNorm/LmHead）；参数配置（padding 方式、`pad_token_id`/`eos_token_id`/max_seq 等，对齐 config 规避）。
2. **模型结构错误**（代码实现错误）：一般导致明显精度错误，输出无序英文/胡言乱语/无法输出。
3. **算子传参错误**：attention mask 传错（不输出无序英文，但输出大量空格、不对齐 GPU）；RoPE 旋转系数传错（一般直接无序输出）。
4. **算子实现**：后处理算子问题（greedy 正常但采样策略后不对）；模型侧算子问题（单算子正常但模型异常 → 多算子内存踩踏/寄存器未复位，开确定性后多次问同一问题结果不一致可佐证）。
5. **环境版本缺陷/差异**：某类机器正常、换机器/换 CANN 异常（如 x86→arm）；对齐环境依赖版本解决。

## 六、推理侧：定位思路

有标杆对照（NPU vs GPU，或 NPU vs 历史基线）场景，泛化为"问题场景 vs 标杆场景"对照：

- CheckList：推理超参/环境变量比对 → 三方库版本（MindIE/vLLM/Transformers + PyTorch/torch_npu）→ 数据读取检查 → 模型配置检查。
- 问题复现前置：随机固定 + 确定性计算（同训练侧）。
- dump + 比对：ATB 侧用 `msprobe-infer-dump.md` 的 load_atb_probe.sh 采，`atb_data_compare` 比对。

## 七、模型级 → 算子级 转判

msprobe 比对定位到首差异 API/层后，判断是否转算子级：

- 首差异是**单算子**且单算子 golden 测试 fail → 转 `ascendc-operator-precision.md` + `dumptensor-7step.md` / `pypto-binary-search.md` 做算子级根因。
- 首差异是**模型结构/超参/传参** → 留在模型级按 CheckList 修。
- 判定决策树见 `debug-decision-tree.md`。

## 关联

- `msprobe-usage.md` / `msprobe-infer-dump.md` — dump 采集（训练/推理）
- `msprobe-compare.md` — 比对定位首差异
- `ascendc-operator-precision.md` — 算子级精度根因（转判目标）
- `debug-decision-tree.md` — 模型级 vs 算子级判定
