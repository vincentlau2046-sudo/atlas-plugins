---
tier: T3
confidence: heuristic
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-code-review/core/methodology.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: composite
  ref: cannbot@c24e8b5 methodology + AtlasHarness T0 工具契约（AscendCodeGen/CompilerBridge/GoldenTest）
  note: "综合 cannbot 检视方法论（缺陷分类 + 修复建议）+ AtlasHarness T0 工具（AscendCodeGen 重生成/CompilerBridge 重编译/GoldenTest 验证）契约自撰的修复路由决策树；基础事实可验（cannbot@c24e8b5 + 工具契约均已验真），但'审完发现走哪个修复工具'的判定边界是启发式综合，非单一源事实断言"
license: CANN-OSL-2.0
---

# 检视发现 → 修复路由决策树

> 本文是 **T3 启发式决策参考**（composite：cannbot 检视方法论 + AtlasHarness T0 工具契约）。**假设来源非事实断言** —— 基础事实（cannbot 缺陷分类 + T0 工具契约）可验，但"审完发现走哪个修复工具"的边界是综合启发式，须结合缺陷类型取舍。读 `review-redlines-defects.md`（缺陷模式）后用本文选修复路径。

## 一、修复工具分层

| 层 | 工具 | 形态 | 用途 |
|---|---|---|---|
| **T0 Tool（AtlasHarness 包裹）** | AscendCodeGen | Shape A CLI → Tool | 结构性缺陷 → 重生成四件套 |
| **基座 coding 工具** | Read / Edit / Write / Grep | base coding | 参数级缺陷 → 定点改 |
| **T0 Tool** | AscendCompilerBridge | Shape A CLI → Tool | 改后重编译（python3 setup.py build_ext） |
| **T0 Tool** | AscendGoldenTest | Shape A CLI → Tool | 改后正确性验证（numpy ref vs NPU） |

> AscendCodeGen 是 AtlasHarness 的**工具执行层**差异化（cannbot 检视只给修复建议，无 CLI 重生成）；基座 Read/Edit 是参数级修复。

## 二、路由决策树

```
检视发现缺陷
  │
  ├─ 缺陷类型？
  │   ├─ Host 红线违规（除零/越界/溢出/指针/初始化/资源匹配）
  │   │   ├─ 参数级（加校验/assert/边界判断）→ Read/Edit 定点改 tiling 代码
  │   │   └─ 结构性（资源管理重构）→ AscendCodeGen 重生成
  │   │       ↓
  │   │   AscendCompilerBridge 重编译 → AscendGoldenTest 正确性门
  │   │
  │   ├─ Kernel 缺陷（API 用法/性能/精度）
  │   │   ├─ 参数级（tile 大小/Buffer 配置）→ Read/Edit 定点改 kernel
  │   │   └─ 结构性（kernel 逻辑重写）→ AscendCodeGen 重生成
  │   │       ↓
  │   │   AscendCompilerBridge 重编译 → AscendGoldenTest
  │   │
  │   ├─ SIMT 转换问题（API 未转 C 风格/UintDiv 误转/变量名冲突/头文件位置）
  │   │   └─ Read/Edit 修 SIMT API 转换 → AscendCompilerBridge 编译验证（Kernel §5 强制）
  │   │
  │   └─ 设计一致性偏离（实现 ≠ DESIGN.md）
  │      └─ 对照设计文档 → AscendCodeGen 重生成（大偏离）或 Read/Edit（小偏离）
  │
  └─ 修复后必走验证链
      AscendCompilerBridge（重编译）→ AscendGoldenTest（正确性门）→ 重检视（确认缺陷消失）
```

## 三、修复协作链

### 链 A：参数级修复（Read/Edit）

```
检视发现（review-redlines-defects.md）  ← 缺陷模式 + 行号
        ↓
Read 缺陷代码 → Edit 加校验/修参数       ← 基座 coding 定点改
        ↓
AscendCompilerBridge                    ← python3 setup.py build_ext 重编译
        ↓
AscendGoldenTest                        ← numpy ref vs NPU 正确性门
```

### 链 B：结构性重生成（AscendCodeGen）

```
检视发现结构性缺陷                       ← kernel/tiling 逻辑需重写
        ↓
AscendCodeGen                           ← 重生成四件套（kernel .asc + pybind + setup.py + test）
        ↓ 填 placeholder
AscendCompilerBridge → AscendGoldenTest ← 重编译 + 正确性门
```

### 链 C：SIMT 编译验证

```
SIMT 转换问题                            ← API 未转 C 风格 / UintDiv 误转
        ↓
Read/Edit 修 simt_api 转换               ← C++ API → C 风格 API
        ↓
AscendCompilerBridge                    ← 编译验证（Kernel §5 强制，转换后必须编译通过）
```

## 四、关键判定信号

| 缺陷信号 | 修复工具 | 依据 |
|---|---|---|
| 加一行 assert/边界判断即可 | Read/Edit | 参数级修复，无需重生成 |
| kernel 逻辑需重写 | AscendCodeGen | 结构性缺陷，重生成四件套 |
| SIMT API 转换问题 | Read/Edit + 编译验证 | Kernel §5 强制编译验证 |
| 资源管理重构 | AscendCodeGen | 结构性，重生成 |
| 改后须验证正确性 | AscendGoldenTest | 修复不能破坏正确性（硬门） |
| 改后须重编译 | AscendCompilerBridge | bisheng 重编译 |

## 五、常见误判

- **参数级缺陷用 AscendCodeGen 重生成**：加一个 assert 就能修的缺陷，重生成四件套是过度——Read/Edit 定点改即可。
- **结构性缺陷用 Read/Edit 硬改**：kernel 逻辑需重写时，硬改易引入新缺陷——AscendCodeGen 重生成更可靠。
- **改后跳过 GoldenTest**：修复可能破坏正确性（加校验改语义/重生成引入新 bug）——**改后必跑 AscendGoldenTest**。
- **SIMT 转换不编译验证**：Kernel §5 红线——转换后必须 AscendCompilerBridge 编译通过。
- **mocked:true 当正确性**：GoldenTest 在 mock 模式返 `mocked: true` 是 liveness 信号非正确性证明——须在真硬件验证。

> ⚠️ 本文路由边界是启发式综合（T3），非单一官方源事实断言。实际修复以 `review-redlines-defects.md`（缺陷模式）+ 检视输出的修复建议为准，本文做工具选择参考。

## 关联

- `review-methodology.md` — 假设检验（缺陷发现的判定方法）
- `review-redlines-defects.md` — 红线 + 常见缺陷模式（本文路由的输入）
- `review-workflow-routing.md` — 检视 workflow 路由（本文是检视后的修复路由）
