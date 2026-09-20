---
tier: T3
confidence: heuristic
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ops-profiling/references/msprof-guide.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: composite
  ref: cannbot@c24e8b5 msprof-guide + AtlasHarness T0 工具契约（AscendProfileAnalyzer/ProfileReportParser/BenchmarkRunner/RealHWBridge）
  note: "综合 cannbot profiling 方法论 + AtlasHarness T0 工具（ada-pa/msprof/ais-bench/npu-smi）契约自撰的路由决策树；基础事实可验（cannbot@c24e8b5 + 工具契约均已验真），但'何时用哪个 profile/bench 工具'的判定边界是启发式综合，非单一源事实断言"
license: CANN-OSL-2.0
---

# 性能工具路由决策树

> 本文是 **T3 启发式决策参考**（composite：cannbot profiling 方法论 + AtlasHarness T0 工具契约）。**假设来源非事实断言** —— 基础事实（cannbot 工具用法 + T0 工具契约）可验，但"何时用哪个工具"的边界是综合启发式，须结合实际场景取舍。读 `msprof-collection.md` + `bottleneck-location.md` 后用本文选工具。

## 一、两类工具

AtlasHarness 把 Ascend 性能工具分两层：

| 层 | 工具 | 形态 | 返回 |
|---|---|---|---|
| **T0 Tool（AtlasHarness 包裹）** | AscendRealHWBridge / AscendProfileReportParser / AscendProfileAnalyzer / AscendBenchmarkRunner | Shape A CLI → Tool | evidence（非 `next_tool`） |
| **cannbot 方法论工具（基座 coding 调用）** | msprof_profile_run.sh / msprof_perf_summary.py / perf_summary.py | 脚本 | 归档/summary |

> T0 Tool 是 AtlasHarness 的**工具执行层**差异化（官方 skill 无 CLI 包装成 Tool）；cannbot 脚本是**知识层归档**（agent 用基座 coding 调用，不包 shell Tool）。

## 二、路由决策树

```
要测性能
  │
  ├─ 先要什么？
  │   ├─ 吞吐 baseline（优化前后对比）→ AscendBenchmarkRunner（ais-bench）
  │   │   └─ 输入是编译好的 .om；返 NPU_compute_time/throughput + summary.json
  │   │
  │   ├─ 瓶颈定位（op 级利用率）→ 须先采 profiling dump
  │   │   ├─ 有 NPU 硬件 → AscendRealHWBridge（profile 命令）触发 msprof 采 PROF_* dump
  │   │   │   └─ dump 是 msprof 二进制 → AscendProfileReportParser（msprof --export）解析
  │   │   └─ 无 NPU / 已有 GE text dump → AscendProfileAnalyzer（ada-pa）解析 GE text
  │   │
  │   └─ 设备状态（核数/UB/arch）→ AscendRealHWBridge（info/query 命令，npu-smi）
  │
  └─ dump 格式决定解析工具
      ├─ PROF_* 目录（msprof 二进制）→ AscendProfileReportParser
      └─ GE_PROFILING_TO_STD_OUT=1 文本 → AscendProfileAnalyzer（ada-pa）
```

## 三、工具协作链

### 链 A：硬件采数 → 解析 → 定位（有 NPU）

```
AscendRealHWBridge (profile)        ← 触发 msprof 采 PROF_* dump
        ↓ PROF_* 目录
AscendProfileReportParser (msprof)  ← --export 解析 → op_summary_*.csv
        ↓ CSV 指标
agent + bottleneck-location.md      ← Main Bound 判定 + 定向优化
        ↓ 优化后
AscendBenchmarkRunner (ais-bench)   ← 前后吞吐对比
```

### 链 B：GE 文本 dump 解析（无 NPU / GE 级）

```
GE_PROFILING_TO_STD_OUT=1 跑模型    ← GE 文本 profiling dump
        ↓ stdout 文本
AscendProfileAnalyzer (ada-pa)      ← 解析 → trace.json + op-stat 排名
        ↓ 排名
agent + bottleneck-location.md      ← 定位瓶颈 op/stage
```

> **ada-pa ≠ ada**：ada 是 CI 下载装包工具，ada-pa 是 profiling 分析工具。AscendProfileAnalyzer 包的是 ada-pa。

### 链 C：纯知识层（无 T0 Tool）

归档（msprof_perf_summary.py 生成 round_NNN/ + summary.txt）、一键采数（msprof_profile_run.sh --warm-up）—— cannbot 方法论工具，agent 用基座 coding 调用。**不包 shell Tool**（Shape B 约定）。

## 四、关键判定信号

| 信号 | 倾向 | 依据 |
|---|---|---|
| 要量化吞吐 | AscendBenchmarkRunner | ais-bench 返 throughput + summary.json |
| 有 NPU + 要 op 利用率 | RealHWBridge(profile) → ProfileReportParser | msprof 二进制 dump 路径 |
| 无 NPU / GE 级 text dump | AscendProfileAnalyzer | ada-pa 处理 GE text |
| 要核数/UB/arch | AscendRealHWBridge(info) | npu-smi 设备信息 |
| 优化前后对比 | BenchmarkRunner 跑两轮 | before/after throughput |

## 五、常见误判

- **ada-pa 当 ada**：ada 下载装 CANN 包，ada-pa 才是 profiling 分析。AscendProfileAnalyzer 包 ada-pa。
- **ProfileReportParser 喂 GE text**：ProfileReportParser 解 msprof 二进制（PROF_* 目录），GE text 用 AscendProfileAnalyzer——输入格式不同。
- **BenchmarkRunner 喂 .onnx**：ais-bench 要编译好的 .om，.onnx/.pb 须先 atc/msame 转 .om。
- **跳过 warm-up 采数**：不 warm-up DVFS 致频率不稳，cycle 偏大误导 bound 判定。
- **mocked:true 当真实性能**：T0 Tool 在 mock 模式返 `mocked: true` 是 liveness 信号非真实性能——不可据 mock 数值下优化结论。

> ⚠️ 本文路由边界是启发式综合（T3），非单一官方源事实断言。实际定位以 `msprof-collection.md`（采集）+ `bottleneck-location.md`（bound 判定）为准，本文做工具选择参考。

## 关联

- `msprof-collection.md` — msprof 采集 + 7 组指标（本文链 A 的采集层）
- `bottleneck-location.md` — bound 判定（本文链 A/B 的解析后层）
- `perf-pipeline-methodology.md` — 三层管线流程（本文工具服务于该流程）
- `perf-tiling-recorrection.md` — bound 定位后回溯 tiling
