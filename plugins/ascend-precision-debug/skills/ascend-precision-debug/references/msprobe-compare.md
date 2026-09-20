---
tier: T1
confidence: verified
source-of-truth:
  repo: msprobe
  sha: 6824676473debc2adfe868751fddfd270ce9c9a6
  path: docs/zh/user_guide/accuracy_compare/pytorch_accuracy_compare_instruct.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: official-doc
  ref: https://gitcode.com/Ascend/msprobe@6824676
  note: "从 msprobe 官方文档 docs/zh/user_guide/accuracy_compare/pytorch_accuracy_compare_instruct.md 抽取 compare 子命令/参数/API 匹配规则自撰重写；MulanPSL-2.0，CLI 命令形态带 attribution，非逐字 vendor"
license: MulanPSL-2.0
---

# msprobe 精度比对（compare）

> 本文是 **dump 后精度比对的主入口**（T1，msprobe@6824676 官方文档验真）。采集到 NPU 与 CPU/GPU 的 dump 数据后，用 `msprobe compare` 子命令逐层/逐 API 比对，定位首差异节点。

## 一、CLI 形态（compare 子命令）

`msprobe` 是一个带子命令的 CLI，比对用 `compare` 子命令（attribution: msprobe@6824676 `pytorch_accuracy_compare_instruct.md`）：

```shell
msprobe compare -tp <target_path> -gp <golden_path> [options]
```

- `-tp / --target_path`（必选）：**NPU** 侧 dump.json 路径（单卡）或 dump 目录（多卡）。
- `-gp / --golden_path`（必选）：**CPU/GPU/NPU** 侧 dump.json 路径（单卡）或 dump 目录（多卡）。

> ⚠️ **入口形态验证纪律**：正确形态是 `msprobe compare -tp ... -gp ...`（**子命令**）。`msprobe -m compare`（模块形式）是未验入口的臆造 —— 二者只差一个 `-m`，但 `-m compare` 不存在。验 CLI 必查官方文档命令形态。

## 二、可选参数

| 参数 | 说明 |
|---|---|
| `-o / --output_path` | 比对结果存盘目录，默认当前目录建 `output/`；默认输出 csv `compare_result_{timestamp}.csv` |
| `--xlsx` | 输出 xlsx 格式（默认 csv） |
| `-fm / --fuzzy_match` | 模糊匹配：同层级同名仅调用次数不同的 API 可匹配比对 |
| `-dm / --data_mapping` | 自定义映射（指定 `*.yaml`），用于 API/模块无法自动匹配场景，仅逐卡 |
| `-cm / --cell_mapping` | 不同平台/不同配置的模块比对（可指定 yaml） |
| `-da / --diff_analyze` | **自动识别首差异节点**，支持 md5/统计量 dump，单卡/多卡 |
| `-tensor_log / --is_print_compare_log` | 单模块/API 日志打印（仅 tensor 数据） |
| `--consistent_check` | verl 训推一致性比对 |
| `--backend` | verl 一致性比对训练后端 `fsdp` / `megatron`（须先 `--consistent_check`） |
| `--config` | tensor 后处理 yaml（量化场景 matmul 校准），仅 PyTorch |

## 三、API 匹配条件

比对前需判断两侧 API 是否可比对，须同时满足：

1. **API 名称相同** —— 命名规则：`{api_type}.{api_name}.{api调用次数}.{前向反向}.{输入输出}.{index}`，如 `Functional.conv2d.1.backward.input.0`。
2. **输入输出 Tensor 数量相同**。

满足则视为同一 API，进入指标计算；不满足则跳过。

## 四、使用场景

1. **移植精度下降**：同模型从 CPU/GPU 移植到 NPU 存在精度下降 → 比对 NPU 与 CPU/GPU 的 API 数值。
2. **迭代版本精度下降**：模型/框架升级或硬件升级前后精度下降 → 比对迭代前后版本 API 数值。
3. **无法自动匹配**：NPU 自研 API 在 CPU/GPU 无对应（不比对）；调用次数不同致无法匹配（忽略，不影响运行）。

## 五、性能与约束

- 比对速度：单份文件 < 10 GB 时 ~0.1 GB/s；> 10 GB 时 ~0.3 GB/s（速度 = 两份文件大小 / 耗时）。
- 推荐环境：独占、CPU 192 核、固态硬盘（SSD > 500 MB/s；机械盘 60–170 MB/s 会拖慢）。
- **误差累积**：NPU 与 CPU/GPU 计算误差随模型执行累积，后期同一 API 可能因输入差异大而无法比对 —— 属正常，定位时聚焦**首差异节点**（`-da`）。
- 仅支持 PyTorch 场景比对（ATB 侧用 `atb_data_compare_instruct`）。

## 六、典型链路

```
CPU/GPU 采 dump  ──┐
                   ├─→  msprobe compare -tp <npu_dump> -gp <golden_dump> -da
NPU 采 dump  ──────┘         │
                             ▼
                   compare_result_{ts}.csv  ──→  首差异 API/层  ──→  转算子级定位
```

`-da`（diff_analyze）自动识别首差异节点，是定位效率的关键 —— 找到第一个偏离的 API 后，若该 API 是单算子，转 `ascendc-operator-precision.md` + `dumptensor-7step.md` 做算子级根因；若是模型结构/超参，转 `msprobe-best-practices.md` 的 CheckList。

## 关联

- `msprobe-usage.md` — 训练侧 dump（比对的前置采集）
- `msprobe-infer-dump.md` — 推理侧 ATB dump
- `msprobe-best-practices.md` — 比对结果解读 + 定位方法论
- `precision-standard.md` — 比对通过阈值（MERE/MARE/分级）
