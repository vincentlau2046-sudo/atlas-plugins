---
name: ascend-test-design
description: Ascend C 算子测试设计技能。覆盖四类测试选择（ST 系统测试 aclnn L0/L1/L2 / UT 单元测试 opapi-ophost-opkernel 覆盖率增强 / whitebox 白盒路径覆盖+TilingKey / golden 正确性门）、ST 9 步设计流程（3 大类 6 种参数 + 9 约束类型 + 6 脚本）、UT Step 1-5、whitebox 6+TTK 步、测试策略决策树。触发关键词：测试设计、测试用例、ST、系统测试、UT、单元测试、覆盖率、白盒、whitebox、路径覆盖、TilingKey、golden、金标准、L0/L1/L2、aclnn。
when_to_use: Use when the user asks to design tests for an Ascend operator — ST system test cases (aclnn L0/L1/L2), UT unit tests with coverage enhancement, whitebox path-coverage cases, or a correctness gate. The agent selects the test type via the strategy decision tree, reads the applicable methodology references, designs cases, and runs the correctness gate via AscendGoldenTest. No fixed step order.
allowed-tools: AscendGoldenTest
---

# Ascend C 算子测试设计

Drive a test-design for an Ascend C operator. You select the test type via the strategy decision tree (ST system test / UT unit test / whitebox path-coverage / golden correctness gate), read the applicable methodology references on demand (progressive disclosure), design test cases following the cannbot methodology (ST 9-step / UT Step 1-5 / whitebox 6+TTK), and run the correctness gate via AscendGoldenTest (numpy ref vs NPU). There is no fixed step order — you decide which test type and methodology apply based on the test goal.

## Goal

Produce a test-design report: test-type selection (with rationale) + case-design methodology + coverage strategy + correctness-gate result (for golden).

## Gates（产出须含）

- [ ] **测试类型路由**：据测试目标选 ST（接口级参数组合）/ UT（模块级覆盖率）/ whitebox（路径覆盖）/ golden（正确性门），附 `test-strategy.md` 判定依据。不混用（golden 是正确性非覆盖度）.
- [ ] **用例设计方法论**：据所选类型读对应 reference（ST→`st-design.md` 9 步 / UT→`ut-develop.md` Step 1-5 / whitebox→`whitebox-design.md` 6+TTK），附设计产物（参数定义/因子/约束/路径枚举）.
- [ ] **覆盖率策略**：ST 标 L0/L1/L2 分级（≤200/500-700/≤20）+ 空tensor派生；UT 标 opapi/ophost/opkernel 模块 + 未覆盖代码定位；whitebox 标全量/低覆盖 + TilingKey 覆盖率.
- [ ] **正确性门**（当涉及 golden）：AscendGoldenTest 跑 numpy ref vs NPU，np.allclose(rtol, atol)，附 pass/fail + mismatch 证据。当返 `mocked: true`，须说明是 liveness 信号非正确性证明.
- [ ] **精度标准锁定**：rtol/atol 阈值禁止手动修改（质量最后门槛），不达标标 XFAIL 勿改阈值放宽.

## Tool catalog

- **AscendGoldenTest** (T0 Tool) — 正确性门：跑 golden-test 脚本（numpy ref vs NPU 输出，np.allclose(rtol, atol)）。提供 test_file 路径 + 可选 cwd/tolerance。返 exit code + stdout/stderr + mismatch 证据。这是**正确性门**（非覆盖率测试）。`mocked: true` = liveness.
- **cannbot 测试脚本** (Shape B，非 shell Tool) — agent 用基座 coding 调用：ST 6 脚本（generate_test_factors/implicit_constraints/solver_config/factor_values/test_cases/empty_tensor_derive）/ UT Step 1-5 / whitebox S2P0-S2P3 + S5_mapper + S6 pytest。不包 shell Tool（Shape B 约定，CANN OSL 引用不 vendor）.
- **基座 coding 工具** (Shape B) — agent 用基座 Read/Edit/Write 执行测试脚本 + 读 aclnn 接口文档 + 生成用例 CSV.

**references**（按需读，progressive disclosure）:

- **references/st-design.md** (T1) — ST 系统测试 9 步流程（输入校准→参数定义 3 大类 6 种→测试因子→约束分析 9 类型→隐式约束 6 规则→依赖图拓扑排序→求解→L0/L1/L2 生成→总结）+ L0 ≤200/L1 500-700/L2 ≤20 分级 + 6 自动化脚本 + 输出目录结构。ST 设计主源。读此设计接口级用例。(cannbot@c24e8b5, CANN-OSL-2.0, verified)
- **references/ut-develop.md** (T1) — UT 入口参数（op_name/repo_type/soc_type/test_model opapi-ophost-opkernel/interactive_mode）+ 强制前置（问卷/TODO/tmp 目录）+ Step 1-5 主流程（空白分析→生成 UT→定位未覆盖→增强→报告）+ 执行规则（严格顺序/禁提前阅读/即时更新）。UT 覆盖增强主源。读此做模块级覆盖率。(cannbot@c24e8b5, verified)
- **references/whitebox-design.md** (T1) — 白盒 6+TTK 步（参数收集→源码侦察 S2P0-S2P3→交叉验证→安全闸门→映射 S5→pytest+TilingKey 覆盖率→TTK 可选）+ 路径覆盖（全量/低覆盖~25）+ S2P0 侦察产物 + TilingKey 覆盖率 + 关键行为（自动重试/精度兜底 XFAIL/无 NPU 兼容 SKIPPED/精度标准锁定）。白盒用例生成主源。读此做路径覆盖。(cannbot@c24e8b5, verified)
- **references/test-strategy.md** (T3) — ST vs UT vs whitebox vs golden 选择决策树 + 4 协作链（开发期正确性门 golden / 接口级覆盖 ST / 模块+路径覆盖 UT+whitebox）+ 关键判定信号。**启发式综合**（confidence:heuristic），测试类型选择参考。读此选测试类型。(composite, heuristic)

Read references via their relative path in this skill's base directory (the base directory path is injected above). Read on demand — do not load all at once.

## Rules

- **先选测试类型再设计**：据测试目标走 `test-strategy.md` 决策树选 ST/UT/whitebox/golden。golden 是正确性门（算不算对），ST/UT/whitebox 是覆盖度（测得全不全）—— 不混用.
- **覆盖率测试前提是正确性**：先 AscendGoldenTest 过正确性门，再做 ST/UT/whitebox 覆盖率增强。未过 golden 的算子做覆盖率无意义.
- **ST 走 9 步流程**：参数定义→因子→约束→求解→L0/L1/L2。用 cannbot 6 脚本（基座 coding 调用，引用不 vendor）.
- **UT 走 Step 1-5**：先做强制前置（问卷/TODO/tmp），再模块级覆盖率增强.
- **whitebox 走 6+TTK**：源码侦察 S2P0-S2P3→映射 S5→pytest+TilingKey。路径覆盖 + TilingKey 覆盖率.
- **精度标准锁定**：rtol/atol 阈值禁止手动修改。不达标标 XFAIL（保留偏差），勿改阈值放宽.
- **工具返证据非决策**：AscendGoldenTest 返回正确性证据（pass/fail + mismatch），不返回 `next_tool`；agent 据证据 + 测试方法论推断下一步.
- **cannbot 测试脚本是 Shape B**：ST 6 脚本 / UT Step 1-5 / whitebox S2P0-S2P3 + S5 + S6 —— agent 用基座 coding 调用，不包 shell Tool.
- **当工具返 `mocked: true`**：视作 liveness 信号非正确性证明，须在报告说明.
- **许可**：cannbot refs = CANN OSL v2.0（non-sublicensable，引用+溯源不 vendor 文本，含测试脚本只引用不 vendor）；references 均自撰验真文本（抽取事实重写），非逐字 copy.

## Gotchas

- **golden 当覆盖率测试**：golden 是正确性门（np.allclose 算不算对），不是覆盖度——覆盖走 ST/UT/whitebox.
- **ST 当模块测试**：ST 是 aclnn 接口级，模块级（opapi/ophost/opkernel）走 UT.
- **UT 当路径覆盖**：UT 是模块级覆盖率，路径级分支覆盖走 whitebox.
- **跳过 golden 直接覆盖**：覆盖率测试前提是算子正确——先 golden 过门.
- **改 rtol/atol 放宽精度**：whitebox pytest 中 rtol/atol 禁改（质量最后门槛）—— 不达标标 XFAIL.
- **L0/L1/L2 用例数超规**：L0 ≤200 / L1 500-700 / L2 ≤20，超规用 `--max-cases`/`--target-count` 控制.
- **dimensions 范围错**：通用最小 1 最大 8，须结合接口文档约束调整（如「3 维」取 [3]，「不超过 8 维」取 [1..8]）.
- **数据类型遗漏**：参数定义须从原始资料完整复制所有数据类型，不允许遗漏.
- **约束 sources 为空**：`sources` 不可为 `[]`；固定取值范围无需定义约束；需自引用时 `sources` 包含 `target` 自身.
- **mocked:true 当正确性**：GoldenTest mock 模式返 `mocked: true` 是 liveness 信号非正确性——须真硬件验证.
