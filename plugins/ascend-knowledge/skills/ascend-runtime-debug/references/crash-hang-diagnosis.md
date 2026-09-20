---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-crash-debug/{references/crash_workflow.md,references/memcheck/mssanitizer_guide.md,references/memcheck/automated_workflow.md}
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-crash-debug 的 crash_workflow（triage/coredump/挂起/buffer死锁）+ memcheck/mssanitizer_guide + automated_workflow（6类内存异常/命令/报告）抽取事实自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# 卡死/崩溃/内存错误诊断

> 本文是 **程序无法运行完场景的主源**（T1，cannbot@c24e8b5 验真，3 源文件）。面向程序崩溃（Segfault/Abort）、卡死/超时、偶发崩溃/内存越界三类。与 `error-code-taxonomy.md`（返回码非 0）互补：本文处理"跑不完"而非"返回错码"。

## 一、triage 决策树

```
程序无法运行完 / 偶发异常
  │
  ├─ 程序崩溃（Segfault / Abort）？
  │   └─ Coredump 调试 → gdb bt
  │       └─ 堆栈不清晰 → mssanitizer 主动检测（§五）
  │
  ├─ 程序卡死/超时（Kernel 无响应）？
  │   └─ Kernel 挂起调试 → 读 plog 定位（§三）
  │       └─ Buffer 配对检查（§四）
  │
  └─ 偶发崩溃 / 怀疑内存错误？
      └─ mssanitizer 主动检测（§五）
```

## 二、程序崩溃 — Coredump 调试

适用 Segmentation Fault / Abort。

1. **启用 coredump**：`ulimit -c unlimited`
2. **生成 core**：重跑程序，崩溃时落 core 文件
3. **GDB 分析**：
   ```bash
   gdb <executable> <core_file>
   (gdb) bt              # 调用栈
   (gdb) bt full         # 完整栈 + 局部变量
   (gdb) frame N         # 切到第 N 层栈帧
   (gdb) info locals     # 局部变量
   (gdb) p variable      # 打印变量
   ```

**常见崩溃根因**：空指针解引用（检查 tensor nullptr）/ 内存越界（DataCopy 长度、GM/UB 范围）/ 栈溢出（递归过深、Kernel 内大数组）。

> 堆栈不清晰（优化致栈帧缺失）或偶发难复现 → 转 mssanitizer（§五）主动检测。

## 三、程序卡死/超时 — Kernel 挂起

### 取证

```bash
ls ~/ascend/log/debug/plog/plog-pid_*.log    # plog 默认路径
export ASCEND_SLOG_PRINT_TO_STDOUT=1          # 或实时打屏
python3 parse_plog.py <plog_file>             # 解析（见 plog-parsing.md）
```

### plog 信号 → 根因

| plog 信号 | 可能根因 | 检查 |
|---|---|---|
| `timeout` / 长时间无响应 | Buffer 未释放 | 循环内 Alloc 后必须 Free |
| 队列空等/满等 | 死锁 | EnQue/DeQue 配对 |
| 无限循环 | 终止条件错 | 循环边界 |
| 阻塞同步 | 同步点 | CrossCoreWaitFlag ↔ SetFlag |
| `aic error` | DataCopy 长度/GM 地址/UB 越界/非对齐 | size 参数 + offset + 32B 对齐 |

### Kernel 内调试三法

| 方法 | 用途 | 形态 |
|---|---|---|
| `AscendC::PRINTF` | 打印关键变量（blockLength/tileNum） | kernel 内嵌原语 |
| `DumpTensor` | 打印 tensor 内容（前 N 元素） | kernel 内嵌（须 DeQue 后调用） |
| msDebug | 单步调试 | CANN 工具（复杂卡死/越界） |

## 四、Buffer 死锁模式

| 模式 | 表现 | 修复 |
|---|---|---|
| Alloc/Free 不配对 | 循环对同 buffer 多 Alloc 不 Free → 核心挂起 | 循环内 Alloc 后必 Free |
| EnQue/DeQue 不配对 | 队列空等或满等 | 配对调用 |
| 多核同步缺失 | CrossCoreWaitFlag 无对应 SetFlag → AIV 卡死 | 补 SetFlag |
| PipeBarrier 滥用 | 全流水线停顿 | 减少不必要 PipeBarrier |
| VECIN 用于输出 | 输出 == 输入 | 输出须用 VECOUT 队列 |
| Double Buffer 漏算 | 阈值错误 | 计算阈值时 ×2 |

> drain 卡死特例：AIV→AIC flag 未发送 → 检查 flag 发送链路。

## 五、mssanitizer 内存检测

适用：偶发崩溃无法复现 / aic error 代码逻辑复杂 / coredump 堆栈不清晰 / 怀疑内存错误。

### 6 类内存异常

| 异常 | 级别 | 含义 | 地址空间 |
|---|---|---|---|
| Illegal Read/Write | ERROR | 访问未分配内存 | GM, UB, L0{A,B,C}, L1 |
| Multi-core Overwrite（多核踩踏） | WARNING | 多核访问重叠 GM 且至少一核写入 | GM |
| Misaligned Access（非对齐） | ERROR | DMA 地址不满足 32B 对齐 | GM, UB, L0{A,B,C}, L1 |
| Illegal Free（非法释放） | ERROR | 释放未分配/已释放地址 | GM |
| Memory Leak（泄漏） | ERROR | 申请未释放（须 `--leak-check=yes`） | GM |
| Unused Memory（分配未用） | WARNING | 分配后从未访问（须 `--check-unused-memory=yes`） | GM |

### 命令

```bash
mssanitizer --tool=memcheck <application>                          # 基础（非法读写+踩踏+非对齐+非法释放）
mssanitizer --tool=memcheck --leak-check=yes <application>         # +泄漏
mssanitizer --tool=memcheck --check-unused-memory=yes <application># +未用
```

> ⚠️ mssanitizer **不支持**加速库（ATB）算子仓内存检测。PyTorch 等框架内存池管理 GM 时，须用手动上报接口（`SanitizerReportMalloc` / `SanitizerReportFree`）确保检测准确。

### 报告格式

每条异常：`====== ERROR/WARNING : <类型> of size <N>` + `at 0x... on <GM/UB>` + `in block aiv(N) on device 0` + `code in pc current 0x... (serialNo: N)` + 调用栈（`#0..#3 <源文件>:<行>`）。

> 编译时加 `-g` 才有完整调用栈，否则只有 PC 指针。多核踩踏报告里 `aiv(N)` 是 vector 核 block 索引 —— 定位是哪个核踩踏。

### 工作流（cannbot 自动化脚本，引用不 vendor）

cannbot 提供 `run_memcheck_pre.sh` + `memcheck_input.json.template`（CANN OSL 脚本）：填配置 → 执行 → `grep "====== ERROR:" memcheck_output/.../ascendc_memcheck_report_raw.txt` 分析。agent 亦可用基座 coding 自撰等价流程。

## 六、工具协作

| 症状 | 首选 | AtlasHarness Tool |
|---|---|---|
| 故障已发生，需全量现场 | 采集 tar.gz（含 coredump/plog/GE dump） | **AscendFaultCollector**（npucollector） |
| AICore 错误码需解码 | 消费 tar.gz → bits + PC/CCE line | **AscendErrorClassifier**（msaicerr） |
| 编译/golden-test 错误分类 | 分类 crash/OOM/alignment/missing-symbol | **AscendDiagnoser** |
| 卡死定位 | 读 plog | parse_plog.py / grep |
| 崩溃定位 | gdb core | 基座 coding |
| 内存越界/踩踏 | mssanitizer | 基座 coding |

> 工具路由细节见 `fault-tool-routing.md`（T3 启发式综合）。

## 关联

- `error-code-taxonomy.md` — 返回码非 0 场景（507035 越界根因分级）
- `plog-parsing.md` — plog 取证方法论（本文 §三 的依据）
- `fault-tool-routing.md` — 何时用哪个 T0 工具
