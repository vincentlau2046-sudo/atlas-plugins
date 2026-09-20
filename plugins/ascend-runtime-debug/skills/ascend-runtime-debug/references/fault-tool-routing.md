---
tier: T3
confidence: heuristic
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-crash-debug/references/crash_workflow.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: composite
  ref: cannbot@c24e8b5 crash_workflow + AtlasHarness T0 工具契约（AscendFaultCollector/ErrorClassifier/Diagnoser）
  note: "综合 cannbot 故障调试工具方法论 + AtlasHarness T0 工具（npucollector/msaicerr/Diagnoser）契约自撰的路由决策树；基础事实可验（cannbot@c24e8b5 + 工具契约均已验真），但'何时用哪个 T0 工具'的判定边界是启发式综合，非单一源事实断言"
license: CANN-OSL-2.0
---

# 故障工具路由决策树

> 本文是 **T3 启发式决策参考**（composite：cannbot 故障方法论 + AtlasHarness T0 工具契约）。**假设来源非事实断言** —— 基础事实（cannbot 工具用法 + T0 工具契约）可验，但"何时用哪个 T0 工具"的边界是综合启发式，须结合实际症状取舍。读 `error-code-taxonomy.md` + `crash-hang-diagnosis.md` 后用本文选工具。

## 一、两类工具

AtlasHarness 把 Ascend 故障工具分两层：

| 层 | 工具 | 形态 | 返回 |
|---|---|---|---|
| **T0 Tool（AtlasHarness 包裹）** | AscendFaultCollector / AscendErrorClassifier / AscendDiagnoser | Shape A CLI → Tool | evidence（非 `next_tool`） |
| **cannbot 方法论工具（基座 coding 调用）** | aclGetRecentErrMsg / parse_plog.py / gdb / mssanitizer / msDebug | C API / 脚本 / CLI | 日志/栈/内存报告 |

> T0 Tool 是 AtlasHarness 的**工具执行层**差异化（官方 skill 无 CLI 包装成 Tool）；cannbot 工具是**知识层方法**（agent 用基座 coding 调用，不包 shell Tool）。

## 二、路由决策树

```
故障发生
  │
  ├─ 返回码非 0（aclnn status）？
  │   ├─ 561xxx / 507035（AICore 错误码）→ AscendErrorClassifier（msaicerr 解码）
  │   │   └─ 先 AscendFaultCollector 采现场 tar.gz（若需 PC/CCE line + addr）
  │   ├─ 161xxx / 361xxx（参数/Runtime）→ aclGetRecentErrMsg() 取详情 + 读 plog
  │   └─ 561003（Kernel 查找）→ 手工排查（kernel-binary-debug.md）或 AscendDiagnoser
  │
  ├─ 程序崩溃（Segfault/Abort）？
  │   └─ ulimit -c unlimited → gdb core（bt/bt full）
  │       └─ 堆栈不清晰 / 偶发 → mssanitizer（crash-hang-diagnosis.md §五）
  │
  ├─ 程序卡死/超时？
  │   └─ 读 plog（parse_plog.py）→ Buffer 配对检查
  │       └─ 疑越界/踩踏 → mssanitizer
  │
  ├─ 编译错误（bisheng）/ golden-test 失败？
  │   └─ AscendDiagnoser（分类 crash/OOM/alignment/missing-symbol + 候选修复）
  │
  └─ 需全量现场（不知从何下手）？
      └─ AscendFaultCollector 一键采（CANN/driver 日志 + coredump + GE dump + op .o + env）→ tar.gz
          └─ 喂 AscendErrorClassifier 解码 / 喂 AscendDiagnoser 分类
```

## 三、工具协作链

### 链 A：现场采集 → 错误码解码

```
AscendFaultCollector (npucollector)        ← 故障时跑一次，采全量 tar.gz
        ↓ tar.gz
AscendErrorClassifier (msaicerr)           ← 解码 AICore 错误码 → bits + PC/CCE line + addr bounds
        ↓ 解码结果
agent + error-code-taxonomy.md             ← 据码 + 根因分级推断
```

### 链 B：编译/golden 错误分类

```
AscendCompilerBridge / AscendGoldenTest    ← 跑出错误（stderr/exit）
        ↓ 错误日志
AscendDiagnoser                            ← 分类 crash/OOM/alignment/missing-symbol + 候选修复
        ↓ 分类
agent + crash-hang-diagnosis.md            ← 据类深入（OOM→内存/alignment→32B/missing-symbol→安装）
```

### 链 C：纯知识层（无 T0 Tool）

卡死（读 plog）/ 崩溃（gdb core）/ 内存越界（mssanitizer）—— cannbot 方法论工具，agent 用基座 coding 调用。**这些不包 shell Tool**（Shape B 约定：脚本/CLI 的知识层用法走 base coding）。

## 四、关键判定信号

| 信号 | 倾向 | 依据 |
|---|---|---|
| aclnn 返回 561xxx / 507035 | AscendErrorClassifier | AICore 错误码可解码 |
| "不知从何下手" / 需 PC+addr | 先 AscendFaultCollector | 全量现场含 coredump+plog+GE dump |
| bisheng 编译失败 / golden-test fail | AscendDiagnoser | 编译/golden 错误可分类 |
| 程序跑不完（卡死/崩溃） | 知识层工具（plog/gdb/mssanitizer） | 非 AICore 错误码场景 |
| 偶发崩溃难复现 | mssanitizer | 主动检测内存错误 |
| 561003 Kernel 查找 | 手工（kernel-binary-debug.md） | 构建/SEL 问题非运行时错误 |

## 五、常见误判

- **AICore 错误码跳过采集直接解码**：msaicerr 解码需 FaultCollector 的 tar.gz（含 coredump/GE dump）—— 只读返回码会缺 PC/CCE line 上下文。先采后解。
- **卡死误用 ErrorClassifier**：卡死无 AICore 错误码（是超时/死锁），ErrorClassifier 无码可解 —— 走 plog + Buffer 检查。
- **编译错误用过 ErrorClassifier**：ErrorClassifier 解 AICore 运行时码，编译错误（bisheng stderr）用 AscendDiagnoser。
- **mocked:true 当正确性**：T0 Tool 在 mock 模式返 `mocked: true` 是 liveness 信号非正确性证明 —— 须在报告说明。

> ⚠️ 本文路由边界是启发式综合（T3），非单一官方源事实断言。实际定位以 `error-code-taxonomy.md`（错误码）+ `crash-hang-diagnosis.md`（症状 triage）为准，本文做工具选择参考。

## 关联

- `error-code-taxonomy.md` — 错误码分类（本文路由的判定依据）
- `crash-hang-diagnosis.md` — 卡死/崩溃/内存 triage（本文链 C 的依据）
- `plog-parsing.md` — plog 取证（卡死路由的执行层）
- `kernel-binary-debug.md` — 561003 深入（本文路由的构建系统分支）
