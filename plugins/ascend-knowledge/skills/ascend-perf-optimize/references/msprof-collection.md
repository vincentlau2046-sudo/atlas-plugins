---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ops-profiling/references/msprof-guide.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ops-profiling msprof-guide.md 抽取 msprof 采集流程、7 组 aic-metrics、逐核 cycle 反推、归档结构与 Main Bound 判定自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# msprof 采集与指标解读

> msprof 是 CANN 二进制 profiling 工具（非 GitHub 仓库工具），采集算子/模型在 NPU 上的执行 trace。本文聚焦**采集流程 + 7 组 --aic-metrics 指标 + 逐核 cycle 反推 + Main Bound 判定**。瓶颈定向优化见 `bottleneck-location.md`。AtlasHarness 用 AscendRealHWBridge（profile 命令）触发 msprof 采集，用 AscendProfileReportParser（msprof --export）解析 dump。

## 一、采集流程

### 1. warm-up（强制）

**必须先 warm-up N 次再采**——NPU 有 DVFS（动态调频），冷启动前几轮频率不稳，采到的 cycle 偏大。warm-up 让频率稳定后再采真值。

```bash
# 一键脚本（cannbot）：--warm-up=3 规避 DVFS
msprof_profile_run.sh --warm-up=3 --output ./prof_out -- ./demo
```

### 2. 7 组 --aic-metrics

msprof `--aic-metrics` 采集 AICore 利用率，共 7 组指标：

| 组 | 指标前缀 | 看什么 |
|---|---|---|
| PipeUtilization | `ai*_vec_ratio` / `ai*_mte2_ratio` / `ai*_cube_ratio` / `ai*_scalar_ratio` / `ai*_fixp_ratio` / `ai*_mte3_ratio` | 各执行单元占比——**Main Bound 判定的主依据** |
| ArithmeticUtilization | `aiv_vec_*` | 向量算力利用率（指令类型分布） |
| Memory | `ai*_mte2_*` / `ai*_mte3_*` | 搬入/搬出带宽 |
| MemoryL0 | L0A/L0B/L0C | Cube 侧 L0 利用 |
| MemoryUB | UB 读写带宽 | 向量侧 UB 带宽 |
| L2Cache | `hit_rate` | L2 缓存命中率 |
| ResourceConflictRatio | `aiv_vec_total_cflt_ratio` | Bank/资源冲突占比 |

### 3. 逐核 cycle（sample-based）

op_summary_*.csv **没有逐核 time 字段**，也**没有 Current Freq / Rated Freq**。要逐核 cycle 须采 sample-based aicore.db：

- 路径：`PROF_Sample/.../device_0/sqlite/aicore.db`（表 `task_cyc`）。
- 用 `aicore_time / max_cycles` 反推主频（频率字段缺失，只能反推）。

> 逐核 cycle 用于核间负载均衡判定（Step 3）：各核 cycle 差异 > 10% → 不均衡。

## 二、目录结构

```
PROF_GROUP_*/
└── PROF_<Metric>/
    └── mindstudio_profiler_output/
        ├── op_summary_*.csv          ← per-op 时间 + 利用率比值（瓶颈定位主表）
        └── ...
└── PROF_Sample/
    └── .../device_0/sqlite/aicore.db ← 逐核 task_cyc（负载均衡判定）
```

> AscendProfileReportParser 解析的 `op_summary_*.csv` 在 `PROF_<Metric>/mindstudio_profiler_output/` 下。Glob `op_summary_*.csv` 找确切文件名。

## 三、Main Bound 判定

按优先级定位瓶颈执行单元（占比最高者）：

| 优先级 | Bound | 判定 |
|---|---|---|
| 1 | MTE2 Bound | `ai*_mte2_ratio` > 80% 或占比最大且 > 70% |
| 2 | CUBE Bound | `aic_cube_ratio` 占比最大 |
| 3 | VEC Bound | `aiv_vec_ratio` 占比最大（PUSHQ 类） |
| 4 | FIXP Bound | `ai*_fixp_ratio` 占比最大 |
| 5 | MTE3 Bound | `ai*_mte3_ratio` 占比最大 |
| 6 | SCALAR Bound | `ai*_scalar_ratio` > 30% |
| — | 无 bound | 多单元 30-50% 无明显主导（流水气泡） |

> 定向优化见 `bottleneck-location.md`（每类 bound 的判定阈值 + 优化方法）。

## 四、归档

每轮 profiling 归档到算子目录：

```
operators/{op}/docs/perf/round_NNN/
├── summary.txt                    ← 本轮关键指标 + Main Bound
├── op_summary_*.csv               ← 原始 per-op 表
└── 逐核负载均衡段                  ← 各核 cycle 差异
```

cannbot `msprof_perf_summary.py` 一键生成归档 + summary.txt + 逐核负载均衡段。

## 五、采数注意

- **必须 warm-up**：不 warm-up 前几轮频率不稳，cycle 偏大误导瓶颈判定。
- **无频率字段**：op_summary 无 Current/Rated Freq，逐核 cycle 须 sample aicore.db 反推。
- **MTE2 + MTE3 带宽共享**：两者共享搬运带宽，高 MTE2 可能拉高 MTE3，需联合看。
- **小数据量头开销**：数据量小时 launch/头开销占比大，cycle 不反映真实算力 bound。
- **多核同地址串行化**：多核写同地址会串行化（硬件保序），采数时避免多核写同址。

## 关联

- `bottleneck-location.md` — 10 类 bound 的判定阈值 + 定向优化方法
- `perf-pipeline-methodology.md` — 三层管线流程（本文是 Step 4 采集层）
- `profiling-tool-routing.md` — msprof vs ada-pa vs ais-bench 工具选择
