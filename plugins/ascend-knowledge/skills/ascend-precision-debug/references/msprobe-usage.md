---
tier: T1
confidence: verified
source-of-truth:
  repo: msprobe
  sha: 6824676473debc2adfe868751fddfd270ce9c9a6
  path: docs/zh/user_guide/dump/pytorch_data_dump_instruct.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: official-doc
  ref: https://gitcode.com/Ascend/msprobe@6824676
  note: "从 msprobe 官方文档 docs/zh/user_guide/dump/pytorch_data_dump_instruct.md 抽取 PrecisionDebugger API/config.json schema/L0-L1-mix 粒度/task 模式事实自撰重写；MulanPSL-2.0 宽松许可，关键 API 签名带 attribution，非逐字 vendor"
license: MulanPSL-2.0
---

# msprobe 模型级精度数据采集（PyTorch 训练侧）

> 本文是 **模型级精度调试的主工具入口**（T1，msprobe@6824676 官方文档验真）。msprobe 是 MindStudio 工具族中独立的精度调试 Python 库（Shape B），`pip install mindstudio-probe --pre` 安装，通过在训练脚本插入 `PrecisionDebugger` 采集运行时精度数据。区别于算子级 DumpTensor（见 `dumptensor-7step.md`）——msprobe 采的是 **模块/API 级** 数据，面向"模型 loss 不对齐/NaN"这类整网问题。

## 一、核心 API（PrecisionDebugger）

msprobe 的训练侧数据采集通过原型函数 `PrecisionDebugger` 完成（attribution: msprobe@6824676 `pytorch_data_dump_instruct.md`）：

```python
from msprobe.pytorch import PrecisionDebugger, seed_all

seed_all()                                          # 固定随机种子/Dropout/算子+通信确定性
debugger = PrecisionDebugger(config_path="./config.json")  # 训练开始前实例化
debugger.start(model=model)                         # 开启 dump
# ... 训练 forward/backward ...
debugger.stop()                                     # 关闭 dump（可再 start，记同一 step）
debugger.step()                                     # 结束本 step（后续 dump 记下一 step）
```

- `seed_all()`：一次性固定网络所有随机种子 + 关闭 Dropout + 打开算子计算/通信确定性；仍需手动 `shuffle=False`（数据加载顺序不在 seed_all 范围）。
- `start(model=model)`：以一个 `nn.Module` 为锚点挂 hook，开始采集。
- `stop()` / `step()`：stop 暂停（同 step 内可重启），step 推进采集窗口。dump 数据落在 `config.json` 的 `dump_path`。

## 二、采集粒度（level）

| level | 粒度 | 说明 |
|---|---|---|
| **L0** | 模块级（nn.Module） | 按 `nn.Module` 前向/反向输入输出采集，粒度粗、数据量小 |
| **L1** | API 级（torch.api） | 按 `torch.nn.functional` / `torch.Tensor` 等 API 采集，粒度细、定位准 |
| **mix** | L0 + L1 | 同时采两层，数据量大但信息最全 |

> 选型：粗定位用 L0，精确定位单 API 用 L1，复杂问题用 mix。

## 三、采集模式（task）

config.json 的 `task` 字段决定采什么：

| 调试需求 | task 配置 | 特点 |
|---|---|---|
| 初步精度分析 | `task="statistics"` | 资源占用低，采统计量（max/min/mean/var 等），快速 |
| 深度精度分析 | `task="tensor"` | 采完整 tensor 数据，磁盘占用大，支持详细分析 |
| 确定性问题分析 | `task="statistics"` + `summary_mode="md5"` | 采统计量 + CRC-32 校验值，快速判确定性 |
| 轻量确定性差异定位 | `task="statistics"` + `summary_mode="xor"` | 仅采 XOR 校验值；装 `--include-mod=xor_checksum` 的包可用 C++ 加速算子，数倍提速 |
| NaN/Inf 检测 | `task="nan_check"` | 通过寄存器状态检测 API 运行中的 NaN/Inf，不落完整 tensor |
| 精度闭环校验 | `task="acc_check"` | 采集同时做精度校验 |
| 结构检查 | `task="structure"` | 采集网络结构信息 |
| 溢出检查 | `task="overflow_check"` | 溢出检测 |

## 四、config.json schema

```json
{
    "task": "statistics",
    "dump_path": "/home/data_dump",
    "rank": [],
    "step": [],
    "level": "L1",
    "async_dump": false,
    "extra_info": true,
    "statistics": {
        "scope": [],
        "list": [],
        "tensor_list": [],
        "data_mode": ["all"],
        "summary_mode": "statistics"
    }
}
```

关键字段：
- `task`：采集模式（见上表）。
- `dump_path`：数据落盘根目录。
- `rank`：空=所有卡；指定卡号列表筛选。
- `step`：空=所有 step；指定 step 列表筛选。
- `level`：`L0` / `L1` / `mix`。
- `async_dump`：`false`=同步（数据可靠、慢），`true`=异步（快、可能丢数据）。
- `statistics.scope` / `list` / `tensor_list`：按 API 名/模块名/tensor 精确控制采集范围（空=全采）。
- `statistics.data_mode`：`["all"]` 或 `["input","output"]` 筛选前向/反向、输入/输出。
- `statistics.summary_mode`：`statistics`（统计量）/ `md5` / `xor`。

> 完整模板见 `assets/msprobe-config-template.json`。

## 五、约束与陷阱

- **仅支持 PyTorch**，暂不支持 PyTorch 2.7+ 的 dynamo 场景。
- **原地操作反向数据缺失**：因 PyTorch 自动微分机制，dump 数据中可能缺原地操作模块/API 及其上一个模块/API 的反向数据。
- **工具改变 loss/gnorm**：msprobe 的 `item` 操作引入同步 + PyTorch hook 机制，可能使 loss/gnorm 略变 —— 排查时区分"工具副作用"与"真实精度问题"（详见 msprobe FAQ）。
- **statistics 模式不落完整 tensor**，需逐 tensor 比对时切 `task="tensor"`（磁盘代价大）。

## 六、与比对工具的衔接

采集到的 dump 数据（`dump_path` 下的 `dump.json` + tensor 文件）可直接喂给 `msprobe compare`（见 `msprobe-compare.md`）做 CPU/GPU vs NPU 逐层/逐 API 比对。典型链路：`PrecisionDebugger` 采 NPU dump → 同模型 CPU/GPU 采 golden dump → `msprobe compare -tp <npu> -gp <golden>` 定位首差异层。

## 关联

- `msprobe-compare.md` — dump 后的精度比对（CLI + 匹配规则）
- `msprobe-infer-dump.md` — 推理侧 ATB dump（非 PrecisionDebugger，是 load_atb_probe.sh）
- `msprobe-best-practices.md` — 训练/推理精度定位方法论（NAN/gradnorm/loss 不对齐）
- `debug-decision-tree.md` — 模型级 vs 算子级判定决策树
