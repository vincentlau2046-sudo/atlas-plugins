---
tier: T1
confidence: verified
source-of-truth:
  repo: msprobe
  sha: 6824676473debc2adfe868751fddfd270ce9c9a6
  path: docs/zh/user_guide/dump/atb_data_dump_instruct.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: official-doc
  ref: https://gitcode.com/Ascend/msprobe@6824676
  note: "从 msprobe 官方文档 docs/zh/user_guide/dump/atb_data_dump_instruct.md 抽取 ATB dump 模块加载脚本/config.json/Operation-Kernel-op 概念自撰重写；MulanPSL-2.0，关键命令带 attribution，非逐字 vendor"
license: MulanPSL-2.0
---

# msprobe 推理侧精度数据采集（ATB 场景）

> 本文是 **推理侧精度 dump 的主入口**（T1，msprobe@6824676 官方文档验真）。ATB = Ascend Transformer Boost（专为 Transformer 模型设计的昇腾加速库）。**ATB dump 与训练侧 PrecisionDebugger 形态完全不同** —— 不是 Python import，而是 source 一个 shell 脚本加载 dump 模块。这是"ATB dump 非 msit CLI"订正的依据。

## 一、形态关键：load_atb_probe.sh（非 Python import）

训练侧用 `from msprobe.pytorch import PrecisionDebugger`；**推理侧 ATB dump 用 sourced shell 脚本**（attribution: msprobe@6824676 `atb_data_dump_instruct.md`）：

```bash
# 1. 定位 msprobe 安装路径
pip show mindstudio-probe          # 假设返回 /usr/local/lib/python3.11/site-packages

# 2. source 加载脚本（不是 python -m，不是 msit 子命令）
MSPROBE_HOME_PATH=/usr/local/lib/python3.11/site-packages
source $MSPROBE_HOME_PATH/msprobe/scripts/atb/load_atb_probe.sh \
    --output=$PWD \
    --config=$PWD/config.json

# 3. 跑 ATB 模型（dump 自动生效，数据落 --output/atb_dump_data）
python examples/run_pa.py --model_path /path-to-weights

# 4. 采完卸载 dump 模块
#    （load_atb_probe.sh 提供对应 unload 脚本）
```

> ⚠️ **入口形态验证纪律**：ATB dump 的入口是 `source .../load_atb_probe.sh`，**不是** `msit llm dump`（msit 是 umbrella 仓非 CLI，曾误判）、**不是** `msprobe -m atb_dump`（臆造的模块形式）。验 CLI 调用必查官方文档的命令形态。

## 二、安装（与训练侧不同）

ATB dump 模块**不在** `pip install mindstudio-probe --pre` 的默认包内，需源码安装并显式 include：

```bash
# 源码安装 + 指定 atb_probe 模块
pip install . --include-mod=atb_probe      # 从 msprobe 源码仓装
```

约束：仅支持 **CANN 8.3.RC1 及以上**。

## 三、基本概念

| 概念 | 含义 |
|---|---|
| **ATB** | Ascend Transformer Boost，Transformer 加速库 |
| **Operation** | ATB 原生算子；最外层称 layer 级 Operation（WordEmbedding / Prefill_layer / Decoder_layer / LmHead 等），可嵌套包含其它 Operation |
| **Kernel** | Operation 调用的底层算子，名多以 "Kernel" 结尾（RmsNormKernel / AddBF16Kernel 等） |
| **op** | 广义执行算子 = layer 级 Operation + 非 layer 级 Operation + Kernel |

dump 默认按 op 粒度采集，`save_child` 控制是否递归采子 Operation。

## 四、config.json（ATB 专用 schema）

ATB dump 的 config.json 与训练侧**字段不同**：

```json
{
    "task": "tensor",
    "dump_enable": true,
    "exec_range": "all",
    "ids": "0",
    "op_name": "",
    "save_child": false,
    "device": "",
    "filter_level": 1
}
```

- `task`：通常 `tensor`（采完整 op 输入输出）。
- `dump_enable`：开关。
- `exec_range`：`all` 或指定执行范围。
- `ids`：op id 筛选（`"0"` 起始）。
- `op_name`：空=全采；指定 op 名精确采。
- `save_child`：是否递归采子 Operation。
- `device`：空=当前设备；指定 device id。
- `filter_level`：过滤粒度（1=粗）。

## 五、约束

- dump 涉及 NPU→主机内存拷贝 + 磁盘 IO，**减慢 ATB 模型运行**（影响程度取决于数据量 + 环境 IO）。
- `task="tensor"` 真实数据模式直接存 op 输入输出 tensor，**磁盘占用大**。
- ATB 模型运行环境须先就绪：CANN Toolkit 包 + CANN NNAL 包安装使能。
- 采完须执行 unload 脚本卸载 dump 模块，避免残留 hook 影响后续运行。

## 六、与训练侧 dump 的对照

| 维度 | 训练侧（PyTorch） | 推理侧（ATB） |
|---|---|---|
| 入口 | `PrecisionDebugger` Python API | `source load_atb_probe.sh` |
| 安装 | `pip install mindstudio-probe --pre` | 源码装 `--include-mod=atb_probe` |
| 粒度 | L0 模块 / L1 API / mix | op（Operation/Kernel） |
| config 字段 | task/level/rank/step/statistics... | task/dump_enable/exec_range/ids/op_name/filter_level |
| CANN | 8.0.RC3 基线 | 8.3.RC1+ |

## 关联

- `msprobe-usage.md` — 训练侧 PrecisionDebugger（模型级 dump）
- `msprobe-compare.md` — dump 后比对（ATB 用 `atb_data_compare_instruct`）
- `msprobe-best-practices.md` — 推理精度定位方法论（乱码/重复/语义断裂）
