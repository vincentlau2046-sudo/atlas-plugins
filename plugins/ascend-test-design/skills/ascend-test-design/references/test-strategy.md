---
tier: T3
confidence: heuristic
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-st-design/SKILL.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: composite
  ref: cannbot@c24e8b5 st-design + ut-develop + whitebox-design + AtlasHarness T0 工具契约（AscendGoldenTest）
  note: "综合 cannbot 三测试 skill（ST/UT/whitebox）方法论 + AtlasHarness AscendGoldenTest 契约自撰的测试策略选择决策树；基础事实可验（cannbot@c24e8b5 + 工具契约均已验真），但'何时用 ST vs UT vs whitebox vs golden'的判定边界是启发式综合，非单一源事实断言"
license: CANN-OSL-2.0
---

# 测试策略选择决策树（ST vs UT vs whitebox vs golden）

> 本文是 **T3 启发式决策参考**（composite：cannbot 三测试 skill + AtlasHarness AscendGoldenTest 契约）。**假设来源非事实断言** —— 基础事实（cannbot 测试方法论 + T0 工具契约）可验，但"何时用哪种测试"的边界是综合启发式，须结合测试目标取舍。读 `st-design.md` / `ut-develop.md` / `whitebox-design.md` 后用本文选测试类型。

## 一、四类测试

| 测试类型 | 范围 | 目标 | 方法论 | AtlasHarness 工具 |
|---|---|---|---|---|
| **ST**（系统测试） | aclnn 接口级 | 功能/精度/性能参数组合覆盖 | `st-design.md`（L0/L1/L2） | 基座 coding 调 cannbot 脚本 |
| **UT**（单元测试） | 模块级（opapi/ophost/opkernel） | 覆盖率增强 + 定位未覆盖代码 | `ut-develop.md`（Step 1-5） | 基座 coding 调 cannbot 脚本 |
| **whitebox**（白盒） | 源码路径级 | 分支路径覆盖 + TilingKey 覆盖 | `whitebox-design.md`（6+TTK） | 基座 coding 调 cannbot 脚本 |
| **golden**（金标准） | 算子正确性 | numpy ref vs NPU 输出对比 | `AscendGoldenTest`（T0 Tool） | AscendGoldenTest（ais-bench 无关，np.allclose） |

> ST/UT/whitebox 的脚本是 cannbot 源（CANN OSL v2.0）—— AtlasHarness **引用不 vendor**：agent 用基座 coding 调用。golden 是 AtlasHarness T0 Tool（AscendGoldenTest，np.allclose 正确性门）。

## 二、路由决策树

```
要测什么？
  │
  ├─ 接口级功能/精度/性能（参数组合覆盖）？
  │   └─ ST（st-design.md）
  │       ├─ L0 门槛（核心功能直通，≤200）
  │       ├─ L1 功能/精度/性能（参数 BC 组合，500~700）
  │       └─ L2 异常（dtype/dim 异常，≤20）
  │
  ├─ 模块级覆盖率增强（定位未覆盖代码）？
  │   └─ UT（ut-develop.md）
  │       ├─ opapi（API 接口层）/ ophost（host 逻辑）/ opkernel（kernel 计算）
  │       └─ Step 1-5：空白分析→生成 UT→定位未覆盖→增强→报告
  │
  ├─ 分支路径覆盖（源码路径枚举）？
  │   └─ whitebox（whitebox-design.md）
  │       ├─ 全量（路径覆盖+网络用例）
  │       ├─ 低覆盖（采样+网络，~25）
  │       └─ TilingKey 覆盖率（诊断指标）
  │
  └─ 算子正确性验证（numpy ref vs NPU）？
      └─ golden（AscendGoldenTest，T0 Tool）
          └─ np.allclose(rtol, atol) — 正确性门（非覆盖率，非参数组合）
```

## 三、测试协作链

### 链 A：开发期正确性门（golden）

```
AscendCodeGen 生成算子 → AscendCompilerBridge 编译
        ↓
AscendGoldenTest                ← numpy ref vs NPU，np.allclose 正确性门
        ↓ pass
进 ST/UT/whitebox 覆盖率增强
```

> golden 是**正确性门**（算不算对），ST/UT/whitebox 是**覆盖度增强**（测得全不全）。先过 golden 再做覆盖。

### 链 B：接口级覆盖（ST）

```
aclnn 接口文档 → st-design.md 9 步
        ↓ 参数定义 + 因子 + 约束 + 求解
L0/L1/L2 用例 CSV
        ↓ 下游执行
接口级功能/精度/性能验证
```

### 链 C：模块级覆盖（UT）+ 路径级覆盖（whitebox）

```
UT（ut-develop.md）              ← 模块级覆盖率增强
        ↓ 定位未覆盖代码
whitebox（whitebox-design.md）   ← 路径级分支覆盖（更深）
        ↓ TilingKey 覆盖率
覆盖率报告
```

## 四、关键判定信号

| 信号 | 测试类型 | 依据 |
|---|---|---|
| 接口级参数组合 | ST | aclnn 接口 L0/L1/L2 参数 BC 组合 |
| 模块覆盖率不足 | UT | opapi/ophost/opkernel 未覆盖代码 |
| 分支路径未覆盖 | whitebox | 源码路径枚举 + TilingKey |
| 算子正确性验证 | golden | numpy ref vs NPU（正确性门） |
| 开发期持续集成门 | golden | AscendGoldenTest 快速正确性验证 |
| 性能基准 | （非测试 skill，走 ascend-perf-optimize） | ais-bench benchmark |

## 五、常见误判

- **golden 当覆盖率测试**：golden 是正确性门（算不算对），不是覆盖度（测得全不全）—— 覆盖走 ST/UT/whitebox。
- **ST 当模块测试**：ST 是 aclnn 接口级，模块级（opapi/ophost/opkernel）走 UT。
- **UT 当路径覆盖**：UT 是模块级覆盖率增强，路径级分支覆盖走 whitebox。
- **跳过 golden 直接做覆盖**：覆盖率测试前提是算子正确——先 golden 过正确性门再做覆盖。
- **mocked:true 当正确性**：AscendGoldenTest 在 mock 模式返 `mocked: true` 是 liveness 信号非正确性证明——须真硬件验证。
- **改 rtol/atol 放宽精度**：whitebox pytest 中 rtol/atol 阈值禁止手动修改（质量最后门槛）—— 不达标标 XFAIL，勿改阈值。

> ⚠️ 本文路由边界是启发式综合（T3），非单一官方源事实断言。实际测试以 `st-design.md` / `ut-develop.md` / `whitebox-design.md` 方法论为准，本文做测试类型选择参考。

## 关联

- `st-design.md` — ST 系统测试设计（aclnn L0/L1/L2）
- `ut-develop.md` — UT 单元测试与覆盖率增强
- `whitebox-design.md` — 白盒用例生成（路径覆盖 + TilingKey）
- `ascend-perf-optimize` skill — 性能测试（非本 skill 范围，ais-bench benchmark）
