# msprobe config.json 模板

> 自撰模板（AtlasHarness 自有许可，非外部源）。msprobe `PrecisionDebugger` 的 config.json 模板文档，覆盖 L0/L1/mix 三粒度 + 五常用 task 模式。字段定义见 `references/msprobe-usage.md`（msprobe@6824676 官方文档）。按需选一个 task 模式，复制对应 JSON 块为 `config.json`，改 `dump_path`/`rank`/`step`。

## 字段速查

| 字段 | 说明 |
|---|---|
| `task` | 采集模式：`statistics` / `tensor` / `acc_check` / `structure` / `overflow_check` / `nan_check` |
| `dump_path` | 数据落盘根目录 |
| `rank` | 空=所有卡；卡号列表筛选，如 `[0, 1]` |
| `step` | 空=所有 step；step 列表筛选，如 `[0, 1, 2]` |
| `level` | `L0`（模块级）/ `L1`（API 级）/ `mix`（L0+L1） |
| `async_dump` | `false`=同步（可靠、慢）/ `true`=异步（快、可能丢数据） |
| `statistics.scope` / `list` / `tensor_list` | 按 API 名/模块名/tensor 精确控制采集范围（空=全采） |
| `statistics.data_mode` | `["all"]` 或 `["input", "output"]` 筛选 |
| `statistics.summary_mode` | `statistics` / `md5` / `xor` |

## task 模式（选一）

### 1. 初步精度分析（statistics）— 资源占用低，快速

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

### 2. 深度精度分析（tensor）— 采完整 tensor，磁盘占用大

```json
{
    "task": "tensor",
    "dump_path": "/home/data_dump",
    "rank": [],
    "step": [],
    "level": "L1",
    "async_dump": false,
    "extra_info": true,
    "tensor": {
        "scope": [],
        "list": [],
        "data_mode": ["all"],
        "summary_mode": "tensor"
    }
}
```

### 3. 确定性问题分析（statistics + md5）— 采统计量 + CRC-32 校验值

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
        "summary_mode": "md5"
    }
}
```

### 4. 轻量确定性差异定位（statistics + xor）— 仅采 XOR 校验值

> 装 `--include-mod=xor_checksum` 的包可用 C++ 加速算子，数倍提速。

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
        "summary_mode": "xor"
    }
}
```

### 5. NaN/Inf 检测（nan_check）— 寄存器状态检测，不落完整 tensor

```json
{
    "task": "nan_check",
    "dump_path": "/home/data_dump",
    "rank": [],
    "step": [],
    "level": "L1",
    "async_dump": false,
    "extra_info": true
}
```

## level 选型

- **L0**（模块级）：按 `nn.Module` 采集，粒度粗、数据量小 —— 粗定位用。
- **L1**（API 级）：按 `torch.nn.functional` / `torch.Tensor` API 采集，粒度细 —— 精确定位单 API 用。
- **mix**（L0+L1）：同时采两层，信息最全、数据量最大 —— 复杂问题用。

## ATB 推理侧（不同 schema）

ATB 推理侧 dump 用**不同的 config.json**（字段不同，入口是 `source load_atb_probe.sh` 非 PrecisionDebugger），见 `references/msprobe-infer-dump.md`：

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
