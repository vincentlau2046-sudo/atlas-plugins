---
name: ascend-runtime-debug
description: Ascend 算子运行时故障调试技能。覆盖运行时错误码（161xxx 参数/361xxx Runtime/561xxx 内部/507035 向量核异常）、plog 日志解析、程序卡死/崩溃/内存错误 triage（coredump/gdb/mssanitizer）、Kernel 二进制构建排查（SEL/vendor/opParaSize）。触发关键词：运行时错误、错误码、507035、卡死、挂起、超时、崩溃、Segmentation Fault、hang、crash、aic error、内存越界、plog、msaicerr、npucollector、Kernel 查找失败。
when_to_use: Use when the user reports an Ascend operator runtime fault — aclnn returns a non-zero error code (161xxx/361xxx/561xxx/507035), the program hangs/crashes/times out, an intermittent crash is suspected (memory corruption), or a Kernel-lookup/binary-build error occurs. The agent classifies the error code, collects log/dump evidence via T0 tools, reads references on demand, and produces a root-cause hypothesis with evidence. No fixed step order.
allowed-tools: AscendErrorClassifier, AscendFaultCollector, AscendDiagnoser
---

# Ascend 算子运行时故障调试

Drive a runtime-fault root-cause analysis for an Ascend operator. You classify the error code (161xxx/361xxx/561xxx/507035) or symptom (hang/crash/intermittent), collect log/dump evidence via T0 tools or cannbot methodology tools, read references on demand (progressive disclosure), and produce a root-cause hypothesis backed by evidence. There is no fixed step order — you decide what to read and which tool to call based on the error class.

## Goal

Produce a runtime-fault root-cause report: error-code classification (or symptom class) + log/dump evidence + candidate root cause + fix direction.

## Gates（产出须含）

- [ ] **错误码/症状分类**：aclnn 返回码非 0 → 判段（161xxx 参数 / 361xxx Runtime / 561xxx 内部 / 507035 向量核异常）；程序跑不完 → 判类（崩溃 / 卡死 / 偶发内存），附判定依据（返回码值或症状信号）.
- [ ] **现场证据**：AICore 错误码 → AscendFaultCollector 采集 tar.gz + AscendErrorClassifier 解码（bits/PC/CCE line/addr）；卡死/崩溃 → plog 行级证据（parse_plog.py 或 grep）或 coredump gdb bt；指明取证的文件/行/工具.
- [ ] **候选根因**：对照 `error-code-taxonomy.md` 根因分级（507035 高/中/低置信度）或 `crash-hang-diagnosis.md` triage（Buffer 死锁/越界/踩踏），给出候选根因.
- [ ] **修复方向**：对齐 32B / 修 Buffer 配对 / 修 SEL/tiling_key 对齐 / 清缓存重装 / 修环境变量 等具体方向 + 验证方式（重跑/golden/编译）.
- [ ] **工具证据标注**：当 T0 Tool 返 `mocked: true`，须在报告说明是 liveness 信号非正确性证明.

## Tool catalog

- **AscendFaultCollector** (T0 Tool) — npucollector 一键采集故障现场（CANN/driver 日志 + coredump + GE dump graph + op .o + 机器 env）→ tar.gz。故障后跑一次，喂 ErrorClassifier/Diagnoser。部分模块需 root。`mocked: true` = liveness.
- **AscendErrorClassifier** (T0 Tool) — msaicerr 解码 AICore 错误码（561xxx/507035）。消费 FaultCollector 的 tar.gz → 返回解码错误码 + bits + PC/CCE line + addr bounds + 粗类。`mocked: true` = liveness.
- **AscendDiagnoser** (T0 Tool) — 分类 bisheng 编译/golden-test 错误（crash/OOM/alignment/missing-symbol）+ 候选修复。返 evidence 非 `next_tool`。配 trap 表推断根因.
- **cannbot 方法论工具** (Shape B，非 shell Tool) — agent 用基座 coding 调用：`aclGetRecentErrMsg()`（C API 取错误详情）/ `parse_plog.py`（plog 解析）/ `gdb`（coredump 分析）/ `mssanitizer --tool=memcheck`（内存检测）/ `msDebug`（单步）。不包 shell Tool（Shape B 约定）.

**references**（按需读，progressive disclosure）:

- **references/error-code-taxonomy.md** (T1) — aclnn 返回码三大来源分类（161xxx/361xxx/561xxx）+ NPU 硬件码 5xxxxx（507035）+ 507035 根因分级（高=DataCopyPad 32B 对齐 / 中=UB 溢出 / 低=越界）+ 561xxx 子类全表 + 解码工具映射。错误码定向主源。读此判码。(cannbot@c24e8b5, CANN-OSL-2.0, verified)
- **references/plog-parsing.md** (T1) — plog 默认路径 + ASCEND_SLOG_PRINT_TO_STDOUT + parse_plog.py 分类逻辑（ACLNN_ERR_PARAM/RUNTIME/INNER_TILING/INNER_FIND_KERNEL/INNER_OPP）+ plog 信号解读（超时/越界）+ 手动 grep。日志取证主源。读此取运行时证据。(cannbot@c24e8b5, verified)
- **references/crash-hang-diagnosis.md** (T1) — triage 决策树（崩溃→coredump/gdb / 卡死→plog+Buffer / 偶发→mssanitizer）+ Buffer 6 死锁模式 + mssanitizer 6 类内存异常（Illegal R-W/踩踏/非对齐/非法释放/泄漏/未用）+ 命令 + 报告格式。跑不完场景主源。读此做卡死/崩溃诊断。(cannbot@c24e8b5, verified)
- **references/kernel-binary-debug.md** (T1) — 5 流程（修改后输出不变/SEL 不匹配 561003/dtype 缺失 361001/多 vendor 冲突/opParaSize）+ opc kernelList 后缀系统（_0/_1/_27）+ 3 位置对齐（tiling_key.h→tiling.cpp→kernel 入口）。构建系统排查主源。读此做 561003/二进制问题。(cannbot@c24e8b5, verified)
- **references/fault-tool-routing.md** (T3) — 何时用 AscendFaultCollector vs AscendErrorClassifier vs AscendDiagnoser vs cannbot 工具（plog/gdb/mssanitizer）决策树 + 3 协作链（采集→解码 / 编译→分类 / 纯知识层）。**启发式综合**（confidence:heuristic），工具选择参考。读此选工具。(composite, heuristic)

Read references via their relative path in this skill's base directory (the base directory path is injected above). Read on demand — do not load all at once.

## Rules

- **先判码/症状再下手**：返回码非 0 先判段（161/361/561/507035）定向；程序跑不完先判类（崩溃/卡死/偶发）。判码走 `error-code-taxonomy.md`，判类走 `crash-hang-diagnosis.md`，选工具走 `fault-tool-routing.md`.
- **AICore 错误码先采后解**：561xxx/507035 解码需 FaultCollector 的 tar.gz（含 coredump/GE dump/PC 上下文）—— 先 AscendFaultCollector 采现场，再 AscendErrorClassifier 解码，勿跳过采集直接猜码.
- **工具返证据非决策**：AscendFaultCollector/ErrorClassifier/Diagnoser 返回 evidence（现场/解码结果/错误分类），不返回 `next_tool`；agent 据证据 + taxonomy/triage 推断根因.
- **cannbot 方法论工具是 Shape B**：aclGetRecentErrMsg（C API）/ parse_plog.py（脚本）/ gdb（CLI）/ mssanitizer（CLI）/ msDebug（CLI）—— agent 用基座 coding 调用，不包 shell Tool.
- **当工具返 `mocked: true`**：视作 liveness 信号非正确性证明，须在报告说明.
- **507035 勿与 507046 混淆**：507035=向量核异常（DMA 对齐/UB 溢出），507046=流同步超时.
- **mssanitizer 不支持 ATB**：加速库（Ascend Transformer Boost）算子仓不可内存检测；PyTorch 框架内存池管理 GM 须用手动上报接口（SanitizerReportMalloc/Free）.
- **许可**：cannbot refs = CANN OSL v2.0（non-sublicensable，引用+溯源不 vendor 文本，含 parse_plog.py 脚本只引用不 vendor）；references 均自撰验真文本（抽取事实重写），非逐字 copy.

## Gotchas

- **AICore 错误码跳过采集**：msaicerr 解码需 FaultCollector tar.gz，只读返回码会缺 PC/CCE line 上下文 —— 先采后解.
- **卡死误用 ErrorClassifier**：卡死是超时/死锁无 AICore 错误码，ErrorClassifier 无码可解 —— 走 plog + Buffer 配对检查.
- **编译错误用过 ErrorClassifier**：ErrorClassifier 解 AICore 运行时码；编译错误（bisheng stderr）用 AscendDiagnoser 分类.
- **507035 高置信根因**：DataCopyPad 参数非 32B 对齐（blockLen/xRow/chunk）—— 速算 `alignElements = 32/sizeof(dtype)`，先查对齐再查 UB.
- **SEL/tiling_key.h 3 位置对齐**：561003 常因 tiling_key.h 声明 ↔ tiling.cpp 传值 ↔ kernel GET_TILING_KEY 三处 dtype 不一致 —— 用 `ASCENDC_TPL_INPUT(0)` 绑定 input[0] 类型.
- **修改后输出不变**：先 `sha256sum build/**/*.o` 验二进制是否真更新（编译器缓存 `$HOME/atc_data/kernel_cache/` 可能吃改动）—— 勿直接怀疑逻辑.
- **多 vendor 包冲突**：`$ASCEND_OPP_PATH/vendors/` 与 `$ASCEND_HOME_PATH/vendors/` 同装一算子 → 旧配置意外激活 —— 两处全清重建.
