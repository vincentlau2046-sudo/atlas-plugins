---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-runtime-debug/{references/error_codes,references/debug_workflow}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-runtime-debug 的 error_codes + debug_workflow 抽取错误码分类/状态码表/507035 根因分级/解码工具事实自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Ascend C 算子运行时错误码体系

> 本文是 **运行时错误码主源**（T1，cannbot@c24e8b5 验真，2 源文件）。面向 `aclnn` API 返回非 0 状态码的场景。先读本文做错误码分类与定向，再按具体码进 `plog-parsing.md`（取日志证据）或 `fault-tool-routing.md`（选工具）。

## 一、三大来源分类

aclnn API 返回码按来源分三段，定位时先判段再判码：

| 段 | 类别 | 产生层 | 典型代表 |
|---|---|---|---|
| 161xxx | 参数错误 | Host 侧参数校验 | 161001 nullptr / 161002 invalid |
| 361xxx | Runtime 错误 | NPU runtime 接口 | 361001 runtime 异常 |
| 5xxxxx | NPU 硬件/驱动 | 硬件层（非 aclnn 框架码） | 507035 向量核异常 |
| 561xxx | 内部异常 | aclnn 框架内部 | 561002 tiling / 561003 find-kernel |

> 5xxxxx 不是 aclnn 框架错误码，由 NPU 硬件/驱动产生，经 `aclrtStreamSynchronize()` 上报，须查 plog 日志或 `aclGetRecentErrMsg()` 取详情。

## 二、基本状态码

| 状态码 | 值 | 含义 | 定向 |
|---|---|---|---|
| ACLNN_SUCCESS | 0 | 成功 | — |
| ACLNN_ERR_PARAM_NULLPTR | 161001 | 参数含非法 nullptr | 检查入参指针 |
| ACLNN_ERR_PARAM_INVALID | 161002 | 参数校验失败（dtype/shape/属性/format 不满足推导关系） | 检查 dtype/shape/属性值/format |
| ACLNN_ERR_RUNTIME_ERROR | 361001 | API 内部调用 npu runtime 接口异常 | `aclGetRecentErrMsg()` 取详情 + 查 plog |

## 三、NPU 硬件错误码（5xxxxx）

| 错误码 | 信息 | 触发机制 |
|---|---|---|
| 507035 | 向量核异常 (vector core exception) | 向量核执行期间硬件异常，经 `aclrtStreamSynchronize()` 报告 Host |

> ⚠️ 507035 勿与 507046（ACL_ERROR_RT_STREAM_SYNC_TIMEOUT，流同步超时）混淆。

### 507035 根因分级（置信度由高到低）

| 置信度 | 根因 | 排查 |
|---|---|---|
| 高 | DataCopyPad 参数非 32B 对齐 | blockLen / xRow 偏移 / 动态 chunk 大小 → 向上对齐到 32 字节倍数 |
| 中 | UB 溢出 / Buffer 冲突 | tmpBuf 用官方 API（`GetReduceMaxMaxMinTmpSize`）勿手估；验 `allBufSize < UB_LIMIT`；查 AllocTensor/FreeTensor 配对 |
| 低 | DataCopyPad 读取越界 | srcStride / xRow 超 GM 范围；高维 offset 超 GM 分配 |
| 极低 | 其他 DMA 异常 | 多核并发写冲突 / 硬件资源耗尽 / 编译优化问题 |

**32B 对齐速算**：`alignElements = 32 / sizeof(dtype)`（FP16/BF16=16，FP32=8），`alignedBlockLen = ((n + alignElements - 1) / alignElements) * alignElements`。

**507035 内置清单**：① DataCopyPad blockLen 是 32B 倍数？② UB 子张量 `Get(offset)` 的 `offset*sizeof(T)` 是 32B 倍数？③ 动态 chunk 对齐计算在 Host 侧做了？④ tmpBuf 用官方 API 而非手估？⑤ 总 UB < 容量限制？

## 四、内部异常（561xxx）

### 核心错误

| 值 | 名称 | 含义 |
|---|---|---|
| 561000 | ACLNN_ERR_INNER | API 内部异常 |
| 561001 | …INFERSHAPE_ERROR | 输出 shape 推导错误 |
| 561002 | …INNER_TILING_ERROR | Tiling 时异常 |
| 561003 | …INNER_FIND_KERNEL_ERROR | 查找 npu kernel 异常（可能算子二进制包未安装） |

### 执行器 / 属性 / 配置

| 值 | 含义 |
|---|---|
| 561101 | 创建 aclOpExecutor 失败（OS 异常） |
| 561102 | 未调用 uniqueExecutor ReleaseTo |
| 561103 | 出现 nullptr |
| 561104 / 561114 / 561115 | 算子属性个数异常 / 超 json 指定 / 少于 json 指定 |
| 561105 | kernel 匹配 hash key 冲突 |
| 561106 | 算子实现模式参数错误 |
| 561107 | 未检测到 `ASCEND_OPP_PATH` 环境变量 |

### JSON / 二进制包

| 值 | 含义 |
|---|---|
| 561108–561111 | 加载 json 失败 / 字段缺失 / format 非法 / dtype 非法 |
| 561112 | 未加载算子二进制 kernel 库 |
| 561113 | 加载 json 字段异常 |
| 561116 / 561117 | 输入个数超 32 / json 信息缺失 |
| 561118 / 561119 | 静态二进制 json 中 workspace / 核数信息异常 |

## 五、高频错误码定向

| 错误码 | 类型 | 排查方向 | 进阶参考 |
|---|---|---|---|
| 507035 | 向量核异常 | DataCopyPad 32B 对齐 / UB 溢出 | 本文 §三 |
| 161xxx | 参数错误 | dtype / shape / nullptr | UT（`ascendc-ut-develop`）Host 层快速定位 |
| 561002 | Tiling 错误 | TilingFunc 实现（分支是否全设 TilingKey / 除零 / 越界）+ 输入参数（shape 元素个数 / 参数组合） | UT 验 Tiling 逻辑 |
| 561003 | Kernel 未找到 | TilingKey/SEL 匹配 / 算子安装 / vendor_name / SOC / 环境变量 | `kernel-binary-debug.md` |
| 561107 | 环境变量缺失 | `ASCEND_OPP_PATH` / `LD_LIBRARY_PATH` | `ascendc-env-check` |

## 六、错误码解码工具

| 工具 | 形态 | 用途 | 对应 AtlasHarness Tool |
|---|---|---|---|
| `aclGetRecentErrMsg()` | C API | 返回码非 0 时取错误详情字符串 | 基座 coding 调用 |
| plog 日志 | 文件 | 运行时全量日志（ERROR/WARN/卡死/越界信号） | 见 `plog-parsing.md` |
| `ASCEND_SLOG_PRINT_TO_STDOUT=1` | env | plog 实时打屏 | — |
| msaicerr | CANN CLI | 解码 AICore 错误码（561xxx/507035）→ bits + PC/CCE line + addr | **AscendErrorClassifier**（T0 Tool，返证据） |
| npucollector | CANN CLI | 一键采集故障现场（CANN/driver 日志 + coredump + GE dump + op .o + 机器 env）→ tar.gz | **AscendFaultCollector**（T0 Tool，采集后喂 msaicerr） |

> **工具返证据非决策**：AscendErrorClassifier / AscendFaultCollector 返回解码结果 + 采集现场，不返回 `next_tool`；agent 据证据 + 本错误码体系推断根因。

## 七、未知错误码兜底

速查表未列时：① `aclGetRecentErrMsg()` 取详情 → ② 开 `ASCEND_SLOG_PRINT_TO_STDOUT=1` 或读 `~/ascend/log/debug/plog/` → ③ 搜官方文档（错误码值 + 信息关键字）→ ④ 搜社区（CANN Issue / 昇腾论坛）。

## 关联

- `plog-parsing.md` — plog 结构 + parse_plog.py 解析方法论（取日志证据）
- `crash-hang-diagnosis.md` — 卡死/崩溃/内存错误 triage（507035 越界/多核踩踏深入）
- `kernel-binary-debug.md` — 561003 Kernel 查找失败的二进制/SEL/vendor 排查
- `fault-tool-routing.md` — 何时用 AscendFaultCollector vs AscendErrorClassifier vs AscendDiagnoser
