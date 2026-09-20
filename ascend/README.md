# Atlas × Ascend 域技能总览（atlas-plugins）

> 本目录是 **纯文档** 文件夹：`atlas-plugins` 市场里 Ascend 域技能的分类索引 + 4 层治理说明。
> 它 **不移动** 任何 `plugins/` 下的 skill 目录（那些才是可安装内容），也不影响 L4 / World A / CI
> 解析路径（它们指向 `~/.atlas/plugins/marketplaces/atlas-plugins/plugins/<skill>/skills/<skill>`）。

## 项目定位

**AtlasHarness** 首先是通用 coding agent；Ascend 是挂在恒定基座上的**可插拔领域包**。
本市场（`atlas-plugins`）承载 Ascend 域的全部可安装技能，分两层：

- **我们自研的治理/知识层**（内容归属 = 本市场仓）：6 个 6 域知识技能 + 18 个官方策展 wrapper。
- **运行时工具面**（编译进 AtlasHarness 二进制，不在此市场）：16 个 Ascend 工具 + 5 个运行时技能。

差异化 = **治理 + 集成层**：官方 skill 是纯知识（缺这四层），我们补齐 溯源 / 工具面 / fixture / efficacy 四层。

## 目标用户

FDE 是随客户业务漂移的综合岗。4 业务面（对应 FDE 的 4 个业务领域）：

| 业务面 | 客户画像 | 典型诉求 |
|---|---|---|
| **算子开发** | 传统行业 / 算子岗 | Ascend C / Catlass / Triton / TileLang 算子端到端开发 |
| **问题定位** | 综合 | 故障采集 / 错误分类 / 性能分析 / 环境运维分诊 |
| **性能测试** | SMB / 互联网 | 数据驱动性能优化 / 模型推理优化 |
| **推理部署** | 互联网 | 模型迁移 / 部署 / vLLM 推理服务 |

## 能力清单

### 1. 自研 6 域知识技能（6 个单 skill 插件条目，已预装）

| 插件条目 | 域 | 内容 |
|---|---|---|
| `ascend-tiling-design` | Tiling 设计 | 多核切分/UB切分/Buffer规划/分支覆盖四要素 + 9 算法分类策略 + AISS 指针 |
| `ascend-precision-debug` | 精度调试 | 模型级 msprobe 两层级 / 算子级 DumpTensor 7 步 / PyPTO 二分 + 误差标准 + 判定决策树 |
| `ascend-runtime-debug` | 运行时调试 | 错误码分类 / plog 解析 / 卡死崩溃 triage / Kernel 二进制构建排查 |
| `ascend-perf-optimize` | 性能优化 | 三层管线四步流程 + msprof 采集 + 10 类 bound 定位与定向优化 |
| `ascend-code-review` | 代码检视 | 假设检验驱动逐条检视 + 5 workflow 路由 + 红线问题 + 缺陷修复路由 |
| `ascend-test-design` | 测试设计 | ST/UT/whitebox/golden 四类测试选择 + 设计流程 + 策略决策树 |

静态 SKILL.md + provenance-stamped references，可移植、可免发版更新。
**验真链跟随内容**：L4 eval + World A verifier 经 `ATLAS_ASCEND_KNOWLEDGE_DIR` 解析市场克隆。

### 2. 官方策展 wrapper（18 个单 skill 插件条目，按 4 业务面）

每个 wrapper 把官方 `agent-skills` / `CANNBot` skill 包按 Atlas 4 层治理做策展封装：
**溯源指针**（权威来源，绝不 vendor）+ **工具面**（路由到 Atlas 16 工具）+ **继承 fixture 面**。

**算子开发（10）**
| 策展条目 | 官方 pack | 许可 | 路由工具（节选） |
|---|---|---|---|
| `cannbot-ops-direct-invoke` | CANNBot ops 直调（27） | OSL | SpecParser/TilingPlanner/CodeGen/CompilerBridge/GoldenTest/Diagnoser |
| `cannbot-aiss-tiling-solver` | CANNBot AISS（1） | OSL | TilingPlanner/CodeGen |
| `cannbot-catlass-op` | CANNBot Catlass（3） | OSL | CodeGen/CompilerBridge/GoldenTest/BenchmarkRunner |
| `cannbot-pypto-op-orchestrator` | CANNBot PyPTO（8） | OSL | SpecParser/CodeGen/GoldenTest/BenchmarkRunner |
| `cannbot-triton-op-generator` | CANNBot Triton（6） | OSL | CodeGen/CompilerBridge/GoldenTest/BenchmarkRunner |
| `cannbot-cuda2ascend-simt` | CANNBot CUDA→SIMT（1） | OSL | CodeGen/CompilerBridge/GoldenTest |
| `cannbot-tilelang-op` | CANNBot TileLang（9） | OSL | CodeGen/CompilerBridge/GoldenTest |
| `community-ascendc-op` | 社区 Ascend C 全流程（17） | Apache | 算子开发全链 7 工具 |
| `community-catlass-op` | 社区 Catlass（4） | Apache | CodeGen/CompilerBridge/GoldenTest/BenchmarkRunner |
| `community-triton-op` | 社区 Triton（11） | Apache | CodeGen/CompilerBridge/GoldenTest/BenchmarkRunner |

**问题定位（2）**
| 策展条目 | 官方 pack | 许可 | 路由工具 |
|---|---|---|---|
| `cannbot-infra-skills` | CANNBot infra（5） | OSL | FaultCollector/ErrorClassifier/ProfileAnalyzer |
| `common-infra-skills` | 社区通用基础设施（6） | Apache | RealHWBridge |

**性能测试（2）**
| 策展条目 | 官方 pack | 许可 | 路由工具 |
|---|---|---|---|
| `mindstudio-ascendc-perf-optim` | MindStudio 性能优化（1） | Apache | BenchmarkRunner/ProfileReportParser/TilingPlanner |
| `cannbot-model-infer` | CANNBot 模型推理（11） | OSL | BenchmarkRunner/ProfileReportParser/Diagnoser |

**推理部署（4）**
| 策展条目 | 官方 pack | 许可 | 路由工具 |
|---|---|---|---|
| `vllm-ascend` | vLLM-Ascend（3） | Apache | InferValidator/ModelConverter/RealHWBridge |
| `mindspeed-drivingsdk` | MindSpeed 自驾 SDK（14） | Apache | ModelConverter/InferValidator |
| `common-deploy` | 社区通用部署（3） | Apache | ModelConverter/OnnxOptimizer/InferValidator/DataPrepTool |
| `common-migration` | 社区通用迁移（5） | Apache | ModelConverter/InferValidator |

### 3. 运行时面（编译进二进制，不在此市场；`--skills` = 5）

5 个运行时 `.ts` 技能（`ascend-generate / validate / debug / optimize / model-adapt`，工具链占位符渲染 + 离线可用）
+ **16 个 Ascend 工具**（4 业务面：算子开发 7 / 问题定位 3 / 性能测试 2 / 推理部署 4）。

## 4 层治理（差异化核心）

官方 skill 是**纯知识**——缺以下四层；Atlas 补齐它们：

| 层 | 含义 | 归属 | 本市场如何承载 |
|---|---|---|---|
| **L1 工具执行面** | 把知识路由到可执行工具 | 二进制 `src/tools/ascend/*.ts`（16 工具） | wrapper 的 `allowed-tools` + Tool catalog |
| **L2 fixture 面** | scenario-aware 非 tautology mock | 二进制 `src/core/executor/ascendMockFixtures.ts` | **继承**：wrapper 路由到的 16 工具已带 fixture |
| **L4 efficacy 面** | with/without A/B 效力断言 | 二进制 `src/plugins/ascend/evals/` + 集成评测 | 6 知识技能已做；18 wrapper 的 L4 为后续跨仓增强（deferred） |
| **溯源面（World A）** | provenance stamp → 可达性验真 | 二进制 `scripts/verify-ascend-knowledge.ts` + manifest | wrapper 的 `references/provenance.md` 溯源块（OSL 仅指针） |

**原则**：官方知识 = *method*（走溯源指针读权威源）；Atlas 工具 = *evidence*（返证据非决策）。
工具返 `mocked: true` 只是存活信号，非正确性证明。

## 许可边界（务必遵守）

| 来源 | 许可 | 边界 |
|---|---|---|
| `CANNBot` 子模块（gitcode.com/cann/cannbot-skills） | **CANN OSL v2.0**（非可再许可，字段限华为 AI 处理器） | **引用 + 溯源，绝不 vendor** 其文本 |
| `agent-skills` 父仓（gitcode.com/Ascend/agent-skills） | **Apache-2.0（代码）+ CC-BY-SA-4.0（文档）** | 代码可 vendor；**文档引用须署名 + 分享相同许可** |

> 市场仓 `atlas-plugins` 必须保持 **公开**（客户 TUI 启动时匿名克隆预装；私有会破坏所有预装）。
> git 凭证走系统，不做 token 注入。

## 快速开始

```bash
# 预装（客户 TUI 启动自动 materialize atlas-plugins，含本市场全部 skill）
# 手动刷新本地市场克隆（publish 新内容后，刷新 resolvedSha 才能搜到/验真新技能）：
bun run src/launcher.ts plugin marketplace update atlas-plugins
# 按域选装（安装粒度 = plugin，非 skill）：
#   /plugin → atlas-plugins → 选 6 域知识 skill 或 18 官方策展 wrapper 之一
# 跨市场 skill 搜索（cache-only）：
bun run src/launcher.ts plugin skills ascend
```

**验真链（跟随内容，CI 用 `ATLAS_ASCEND_KNOWLEDGE_DIR` 指向 CI 克隆的市场根）：**
- L4 eval：`tests/integration/ascend-*-skill-eval.test.ts`（6 域，with/without A/B）
- World A：`bun run verify:ascend`（溯源 stamp → 上游可达性 + freshness）
- World B：`bun run verify:ascend-official`（官方 skill 装后 integrity/pin/drift/submodule）
