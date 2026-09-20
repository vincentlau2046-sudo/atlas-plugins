---
name: ascend-perf-optimize
description: Ascend 算子/模型性能优化技能。覆盖三层管线（卡间/核间/核内）四步流程（Tiling 理论建模→通算演算→核间流水→单核流水）、msprof 采集与 7 组 aic-metrics 指标、10 类 bound 定位与定向优化（VEC/MTE2/CUBE/SCALAR/核间不均衡/Bank Conflict/DoubleBuffer/流水气泡/L2 Cache/交叉关联）、tiling 修正回溯。触发关键词：性能优化、性能调优、瓶颈定位、bound、msprof、profiling、吞吐、throughput、算力利用率、流水线、DoubleBuffer、Bank Conflict、L2 Cache、ais-bench。
when_to_use: Use when the user asks to optimize the performance of an Ascend operator or model, locate a performance bottleneck, or interpret msprof profiling data. The agent runs the three-layer pipeline flow (card/inter-core/intra-core), collects profiling evidence via T0 tools, reads references on demand, locates the bound type, and produces a tiling-correction + optimization strategy with before/after throughput. No fixed step order.
allowed-tools: AscendProfileAnalyzer, AscendProfileReportParser, AscendBenchmarkRunner, AscendRealHWBridge
---

# Ascend 算子/模型性能优化

Drive a performance optimization for an Ascend operator or model. You run the three-layer pipeline flow (card → inter-core → intra-core), collect profiling evidence via T0 tools (AscendRealHWBridge triggers msprof, AscendProfileReportParser parses the dump, AscendBenchmarkRunner quantifies throughput), read references on demand (progressive disclosure), locate the bound type via msprof metrics, and produce a tiling-correction + optimization strategy backed by before/after throughput. There is no fixed step order — you decide what to read and which tool to call based on which layer is the bottleneck.

## Goal

Produce a performance optimization report: three-layer pipeline analysis + bound classification (with msprof metric evidence) + tiling-correction strategy + before/after throughput quantification.

## Gates（产出须含）

- [ ] **三层管线分析**：指明当前瓶颈在卡间 / 核间 / 核内哪层，附判定依据（通信时序 / 逐核 cycle 差异 / bound 执行单元）。下钻顺序卡间→核间→核内，不跳层.
- [ ] **bound 分类**：对照 `bottleneck-location.md` 10 类 bound，定具体类型（VEC/MTE2/CUBE/SCALAR/核间不均衡/Bank Conflict/DoubleBuffer 未生效/流水气泡/L2 Cache 低/交叉关联），附 msprof 指标值（如 `aiv_vec_ratio > 50%`）.
- [ ] **profiling 证据**：AscendRealHWBridge(profile) 采的 PROF_* dump + AscendProfileReportParser 解析的 op_summary_*.csv 关键字段值；或 AscendProfileAnalyzer(ada-pa) 解析的 GE text dump op-stat 排名；指明取证文件/字段/工具.
- [ ] **tiling 修正建议**：对照 `perf-tiling-recorrection.md` bound→tiling 参数映射，给具体改的参数（blockDim/tile 大小/DoubleBuffer 份数/512B 对齐/L0C 复用/AIC:AIV 比例），回溯 `ascend-tiling-design` skill.
- [ ] **前后吞吐量化**：AscendBenchmarkRunner(ais-bench) 跑优化前/后两轮，对比 throughput + NPU_compute_time。当返 `mocked: true`，须说明是 liveness 信号非真实性能.

## Tool catalog

- **AscendRealHWBridge** (T0 Tool) — `profile` 命令触发 msprof 采集 PROF_* dump；`info`/`query` 命令取设备信息（核数/UB/arch，npu-smi）。性能优化的采数入口 + 平台参数来源。`mocked: true` = liveness.
- **AscendProfileReportParser** (T0 Tool) — `msprof --export=on` 解析 msprof 二进制 dump（PROF_* 目录）→ op_summary_*.csv（per-op 时间 + 利用率比值 aiv_vec_ratio/aiv_mte2_ratio 等）+ trace.json。输入是 PROF_* 目录。`mocked: true` = liveness.
- **AscendProfileAnalyzer** (T0 Tool) — `ada-pa` 解析 GE 文本 profiling dump（GE_PROFILING_TO_STD_OUT=1）→ trace.json + op-stat 排名。**与 ProfileReportParser 输入格式不同**（GE text vs msprof 二进制）。**ada-pa ≠ ada**（ada 是 CI 下载装包工具）。`mocked: true` = liveness.
- **AscendBenchmarkRunner** (T0 Tool) — `python3 -m ais_bench`（IEEE 2937 标准化推理性能测试）benchmark 编译好的 .om → NPU_compute_time(min/max/mean/median/p99) + H2D/D2H latency + throughput + summary.json。输入须是 .om（.onnx/.pb 须先 atc/msame 转）。`mocked: true` = liveness.
- **cannbot 方法论工具** (Shape B，非 shell Tool) — agent 用基座 coding 调用：`msprof_profile_run.sh`（一键采数+warm-up）/ `msprof_perf_summary.py`（归档 round_NNN + summary.txt）/ `perf_summary.py`（perf 汇总）。不包 shell Tool（Shape B 约定）.

**references**（按需读，progressive disclosure）:

- **references/perf-pipeline-methodology.md** (T1) — 三层管线（卡间/核间/核内）+ 四步流程（Tiling 理论建模→通算演算→核间流水→单核流水）+ 每步四件产出（仿真图/profiling 报告/优化策略/tiling 修正）+ 迭代闭环。流程骨架主源。读此定优化流程。(cannbot@c24e8b5, CANN-OSL-2.0, verified)
- **references/msprof-collection.md** (T1) — msprof 采集流程（warm-up N 规避 DVFS）+ 7 组 --aic-metrics 指标（PipeUtilization/ArithmeticUtilization/Memory/MemoryL0/MemoryUB/L2Cache/ResourceConflictRatio）+ 逐核 cycle（sample aicore.db task_cyc 反推，op_summary 无逐核 time/无频率字段）+ 目录结构 + Main Bound 判定优先级。采数主源。读此采数与解读指标。(cannbot@c24e8b5, verified)
- **references/bottleneck-location.md** (T1) — 10 类 bound 判定阈值 + 定向优化方法（VEC UB 融合/MTE2 512B 对齐+DoubleBuffer/CUBE L0C 累加/SCALAR 缩 TilingData/核间均匀尾块/Bank Conflict 调步长/DoubleBuffer bufNum=2/流水气泡增 workspace/L2 SetL2CacheHint）+ 交叉关联诊断 + 4 案例（GroupedMatmul 41%/Matmul 4.75x/FlashAttention fixpipe 80%→55%/MC² 32.7%）。bound 定位主源。读此定 bound 与优化方法。(cannbot@c24e8b5, verified)
- **references/perf-tiling-recorrection.md** (T1) — bound→tiling 参数映射表 + 分层修正（卡间切分粒度/核间 blockDim/核内 tile+Buffer）+ 修正后验证四步（CodeGen 重生成→CompilerBridge 重编译→GoldenTest 正确性门→BenchmarkRunner 量化）+ 何时停止迭代。tiling 回溯主源。读此把 bound 转成 tiling 改法。(cannbot@c24e8b5, verified)
- **references/profiling-tool-routing.md** (T3) — 何时用 AscendRealHWBridge vs AscendProfileReportParser vs AscendProfileAnalyzer vs AscendBenchmarkRunner 决策树 + 3 协作链（硬件采数→解析→定位 / GE text→ada-pa / 纯知识层归档）。**启发式综合**（confidence:heuristic），工具选择参考。读此选工具。(composite, heuristic)

Read references via their relative path in this skill's base directory (the base directory path is injected above). Read on demand — do not load all at once.

## Rules

- **三层下钻不跳层**：卡间→核间→核内。核内 bound 可能是核间不均衡的表象，先解上层再解下层.
- **先采数再判 bound**：AscendRealHWBridge(profile) 采 PROF_* dump → AscendProfileReportParser 解析 op_summary → 读指标判 bound。无 profiling 数据不下优化结论.
- **bound 判定看 PipeUtilization 占比**：按 Main Bound 优先级（MTE2>CUBE>VEC>FIXP>MTE3>SCALAR），占比最大者为主 bound。阈值见 `bottleneck-location.md`.
- **优化前后必须量化**：AscendBenchmarkRunner 跑两轮对比 throughput。无 before/after 数据的优化无依据.
- **正确性是硬门**：每轮 tiling 修正后先 AscendGoldenTest 确认正确性未回归，再看性能。优化破坏正确性是常见坑（增 tile 溢出 UB / 调对齐改语义）.
- **工具返证据非决策**：RealHWBridge/ProfileReportParser/ProfileAnalyzer/BenchmarkRunner 返回 evidence（dump/CSV/排名/timing），不返回 `next_tool`；agent 据证据 + bound 方法论推断优化方向.
- **cannbot 方法论工具是 Shape B**：msprof_profile_run.sh / msprof_perf_summary.py / perf_summary.py —— agent 用基座 coding 调用，不包 shell Tool.
- **当工具返 `mocked: true`**：视作 liveness 信号非真实性能，须在报告说明，不可据 mock 数值下优化结论.
- **msprof 必须 warm-up**：不 warm-up DVFS 致频率不稳 cycle 偏大，误导 bound 判定.
- **许可**：cannbot refs = CANN OSL v2.0（non-sublicensable，引用+溯源不 vendor 文本）；references 均自撰验真文本（抽取事实重写），非逐字 copy.

## Gotchas

- **ada-pa 当 ada**：ada 下载装 CANN 包，ada-pa 才是 profiling 分析。AscendProfileAnalyzer 包 ada-pa.
- **ProfileReportParser 喂 GE text**：ProfileReportParser 解 msprof 二进制（PROF_* 目录），GE text 用 AscendProfileAnalyzer —— 输入格式不同别混.
- **BenchmarkRunner 喂 .onnx**：ais-bench 要 .om，.onnx/.pb 须先 atc/msame 转.
- **跳过 warm-up**：不 warm-up 采的 cycle 偏大，会误判 bound（虚高的 MTE2/VEC）.
- **op_summary 无逐核 time**：逐核 cycle 须 sample aicore.db（task_cyc）反推，op_summary 只有聚合 op 时间.
- **核内 bound 实为核间不均衡**：某核 cycle 异常高拉高整体 vec_ratio —— 先查逐核均衡（Step 3）再查核内 bound（Step 4）.
- **MTE2+MTE3 带宽共享**：高 MTE2 拉高 MTE3，需联合看，勿分别当两个 bound.
- **DoubleBuffer 配对错退化单缓冲**：EnQue 无配对 DeQue → bufNum=2 也退回串行。检查 EnQue/DeQue 严格配对.
- **Bank Conflict 藏在 vec_ratio 后**：高 vec_ratio + 高 aiv_vec_total_cflt_ratio → 先解 bank conflict（调访问步长），vec 占比是假象.
