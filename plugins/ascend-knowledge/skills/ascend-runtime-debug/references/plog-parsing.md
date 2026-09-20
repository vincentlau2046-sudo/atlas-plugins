---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-runtime-debug/{references/debug_workflow.md,scripts/parse_plog.py}
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-runtime-debug 的 debug_workflow（plog 路径/打屏/分析要点）+ parse_plog.py（分类逻辑/输出格式）抽取事实自撰重写，不 vendor 脚本源码；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor"
license: CANN-OSL-2.0
---

# plog 日志解析方法论

> 本文是 **运行时日志取证主源**（T1，cannbot@c24e8b5 验真，含 parse_plog.py 脚本行为）。面向"返回码非 0 但信息不清"或"需运行时全量证据"的场景。配合 `error-code-taxonomy.md`（判码）使用。

## 一、plog 是什么

plog 是 Ascend 运行时（CANN/driver）打出的日志，记录算子执行期间的 ERROR/WARN、硬件异常、同步事件。aclnn 返回码只给类别，plog 给上下文（哪一行、哪个 block、什么地址）—— 是运行时错误的核心证据源。

**默认路径**：`~/ascend/log/debug/plog/plog-pid_<PID>.log`（每进程一文件，按 PID 区分）。

## 二、日志获取

| 方式 | 命令 | 场景 |
|---|---|---|
| 直接读文件 | `ls ~/ascend/log/debug/plog/plog-pid_*.log`（取最新 mtime） | 事后取证 |
| 实时打屏 | `export ASCEND_SLOG_PRINT_TO_STDOUT=1` 后重跑 | 复现时实时观察 |

> 打屏模式会略增开销，定位后关闭。事后取证优先读文件（不打扰执行流）。

## 三、parse_plog.py 解析

cannbot 提供 `parse_plog.py`（CANN OSL v2.0 脚本，**引用不 vendor**）—— 扫 plog 行，按正则分类 `[ERROR]` / `[WARN]` 行并汇总。

**用法**：
```bash
python3 parse_plog.py <plog_file>   # 指定文件
python3 parse_plog.py               # 自动取 ~/ascend/log/debug/plog/ 最新 mtime 文件
```

**分类逻辑**（按行内关键字归类）：

| 行内关键字 | 归类 |
|---|---|
| `ACLNN_ERR_PARAM` | 参数错误（对应 161xxx） |
| `ACLNN_ERR_RUNTIME` | Runtime 错误（对应 361xxx） |
| `ACLNN_ERR_INNER_TILING` | Tiling 错误（对应 561002） |
| `ACLNN_ERR_INNER_FIND_KERNEL` | Kernel 查找错误（对应 561003） |
| `ACLNN_ERR_INNER_OPP` | 环境配置错误（对应 561107 等） |
| 其他 `[ERROR]` | 其他错误 |

**输出**：错误总数 / 警告总数 / 错误类型分布（按计数降序）/ 错误详情前 10 条（行号 + 类型 + 截断内容）。退出码：有错误 → 1，无 → 0（可串进 CI）。

> 脚本是 Shape B（Python 脚本，非 shell Tool）—— agent 用基座 coding 调用，或自撰等价解析器（grep `[ERROR]` + 分类）。**不包 shell Tool**（Shape B 约定，同 msprobe）。

## 四、plog 内容解读要点

### 核心超时 / 卡死信号

plog 出现 `timeout` 或程序长时间无响应：

| 信号 | 可能根因 |
|---|---|
| Buffer 未释放 | 循环内 Alloc 后未 Free → 检查 AllocTensor/FreeTensor 配对 |
| 死锁 | EnQue/DeQue 不配对 → 队列空等/满等 |
| 无限循环 | 循环终止条件错 |
| 阻塞同步 | 同步点阻塞 → 检查 CrossCoreWaitFlag 是否有对应 SetFlag |

### 内存越界信号

`aic error` 或长时间无响应：

| 信号 | 可能根因 |
|---|---|
| DataCopy 长度错 | size 参数与实际不符 |
| GM 地址错 | offset 计算 → 超 GM 分配 |
| UB 访问越界 | buffer 大小不足 |
| 非对齐访问 | DMA 地址非 32B 对齐 |

> 越界/踩踏深入排查见 `crash-hang-diagnosis.md`（mssanitizer 6 类内存异常）。

## 五、手动解析（无脚本时）

```bash
# 取所有 ERROR 行 + 行号
grep -n '\[ERROR\]' ~/ascend/log/debug/plog/plog-pid_*.log

# 按错误码过滤
grep -nE '507035|56100[23]|16100[12]|361001' <plog_file>

# 看 vector core 异常上下文
grep -n -A5 -B5 'VECTOR_CORE_EXCEPTION\|507035' <plog_file>
```

关键字段：行号（定位时序）、`[ERROR]`/`[WARN]`（级别）、错误码数值、block/device 索引（aiv(N)/aic(N)，定位是哪个核）、PC 指针（对应 kernel 内指令位置）。

## 六、plog ↔ 工具协作

| 阶段 | 动作 | 工具 |
|---|---|---|
| 取证 | 采集故障现场全量日志 + coredump + GE dump | **AscendFaultCollector**（npucollector，一键 tar.gz） |
| 解码 | 解码 AICore 错误码 → bits + PC/CCE line + addr | **AscendErrorClassifier**（msaicerr，消费 tar.gz） |
| 阅读 | 读 plog 行级细节 | parse_plog.py / 手动 grep |

> AscendFaultCollector 采集的 tar.gz 含 plog（喂 AscendErrorClassifier）；单读 plog 用 parse_plog.py。两者互补：全量现场 vs 行级阅读。

## 关联

- `error-code-taxonomy.md` — 错误码分类（plog 行归类与之对齐）
- `crash-hang-diagnosis.md` — 卡死/崩溃 triage（plog 超时/越界信号的深入）
- `fault-tool-routing.md` — 何时采现场（FaultCollector）vs 只读 plog
