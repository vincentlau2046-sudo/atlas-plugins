---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-whitebox-design/SKILL.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-whitebox-design SKILL.md 抽取 6+TTK 步流程、源码侦察产物体系、路径覆盖与 TilingKey 覆盖率方法论自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# 白盒测试用例生成方法论（路径覆盖 + TilingKey 覆盖率）

> Ascend C 算子白盒测试用例生成系统：分析算子源码提取参数维度，自动枚举参数组合，生成可执行白盒用例。两套输出：全量（路径覆盖+网络用例）与低覆盖（采样+网络用例）。本文是白盒方法论骨架；ST 见 `st-design.md`，UT 见 `ut-develop.md`，测试策略选择见 `test-strategy.md`。

## 一、6+TTK 步流程

| 步骤 | 目标 | 主要产物 |
|---|---|---|
| Step 1 | 收集参数 + 定位算子路径 | 输入摘要 |
| Step 2 | 源码侦察、接口建模、参数推导 | S2P0/S2P1/S2P2/S2P3 产物 |
| Step 3 | 交叉验证测试设计 | S3_verification_report.json |
| Step 4 | 人工闸门确认 | 用户确认记录 |
| Step 5 | 映射抽象用例到 tensor 配置 | S5_mapped_cases_low/high.json |
| Step 6 | 生成并执行 pytest/ST 证据 | S6 pytest、结果、覆盖率 |
| TTK | 可选转换为 TTK CSV 并执行 | ttk_*.csv、golden_plugin.py |

预计用例规模：全量覆盖（路径覆盖+网络用例），低覆盖约 25 个（随机采样+网络用例）。单 pytest 文件通过 `--cases-file` 切换数据源，两套 JSON 始终同时产出。

## 二、Step 2 源码侦察产物体系

| 产物 | 阶段 | 说明 |
|---|---|---|
| S2P0_scout_t.md | Phase 0 | tiling 侦察报告（分支可达性 + 平台标注） |
| S2P0_scout_k.md | Phase 0 | kernel 侦察报告（dispatch 模式 + key 数量） |
| S2P0_file_manifest.json | Phase 0 | 源码文件侦察清单（tiling/kernel 优先级 + dispatch + key 计数） |
| S2P1_path_list.json | Step 2 | 代码路径清单 + 分支树 |
| S2P2_param_def.json | Step 2 | 参数定义 + 约束 + 分组 + `tiling_keys`（供 Step 6c 覆盖率计算） |
| S2P1_operator_model.json | Step 2 | 算子输入输出模型（dtype/shape/presence 规则）+ shape_mapping（Step 5 消费） |
| S2P3_test_design.md | Step 2-3 | 测试设计文档，Step 4 闸门确认依据 |

## 三、路径覆盖方法论

- **分析算子源码**（tiling + kernel + 接口），提取分支路径和参数维度。
- **自动枚举参数组合**，生成白盒测试用例。
- **两套输出**：
  - 全量（high）：路径覆盖 + 网络用例，data_range 扩展（one-hot + 全统一）。
  - 低覆盖（low）：随机采样 + 网络用例，约 25 个。

## 四、TilingKey 覆盖率

Step 6c 自动从 plog 提取所有用例命中的 tiling key 值，与 `S2P2_param_def.json` 顶层 `tiling_keys` 期望集合对比，生成 `S6_tilingkey_coverage.json`（含全局与 per_group 覆盖率）。

- 覆盖率为诊断指标（非通过/失败门）。
- 路径 B `tilingkey_single.py` 提供单用例调试入口。
- 产物：`tilingkey_logs/{op}_full.log`（全量 plog 副本）+ `tilingkey_logs/{op}_{case_id}.log`（单用例 plog 副本）。

## 五、关键行为

- **自动重试**：Step 3 交叉验证失败时，自动回退 Step 2 重新分析，最多 3 轮，无需人工干预。
- **精度兜底**：Step 6 中精度不达标的用例自动标记为 XFAIL（保留偏差信息），而非删除或阻塞交付。
- **无 NPU 兼容**：Step 6 在无 NPU 环境下自动跳过硬件执行，标记为 SKIPPED，不报错。
- **精度标准锁定**：pytest 中 rtol/atol 阈值禁止手动修改（质量保证最后门槛）。
- **TTK CSV 可选**：TTK 模块默认不执行，仅用户选择时于 Step 6 完成后生成 TTK CSV。

## 六、执行约束

- **禁止跳步**：必须按 Step 编号顺序执行。
- **禁止抢跑**：前置条件未满足时禁止启动该步骤任何操作。
- **子 agent 规则传递**：所有行为规范/约束/步骤必须由子 agent 通过 Read 直接从源文件读取，禁止主 agent 转述/摘要/改写后传入。
- **子 agent 按需读取**：禁止提前 Read 后续步骤文件（上下文隔离）。
- **Step 4 安全闸门**：完成 Step 3 后必须停下展示摘要等用户确认，不得自动进入 Step 5。

## 七、TTK 模块（可选）

启用时（用户选择「生成」）：
- 需安装 `numpy`，项目需含 `ops-test-kit/` 目录。
- TTK kernel 执行命令须在 `ops-test-kit/` 目录下运行。
- 算子目录需能定位 aclnn API 文档（`docs/aclnn{Op}.md`），用于生成 `golden_plugin.py` 参考实现。
- 需支持 CSV kernel 模式、`--plugin` 加载和当前 golden 函数签名的 TTK 版本。

产物：`ttk_extract_case_info.py` + `ttk_{op}_cases_low.csv` + `ttk_{op}_cases_full.csv` + `golden_plugin.py`。

## 关联

- `st-design.md` — ST 系统测试设计（aclnn L0/L1/L2）
- `ut-develop.md` — UT 单元测试与覆盖率增强
- `test-strategy.md` — ST vs UT vs whitebox vs golden 选择决策树
