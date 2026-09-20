---
tier: T3
confidence: heuristic
source-of-truth:
  repo: aiss-tiling-solver
  sha: null
  url: https://gitcode.com/HIT1920/TilingSolver
  note: "第三方/学术/preview，代码未全开源，仅 url 可达验；不作 T1 source-of-truth"
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5:ops/aiss-tiling-solver/SKILL.md
  note: "AISS 用法来自 cannbot aiss-tiling-solver skill；工具本身 external；CANN OSL v2.0 引用+溯源不 vendor"
license: external-preview
---

# AISS-TilingSolver 自动求解器（T3/external）

> 本文档是 **T3 启发式参考**——AISS 是第三方/学术/preview 工具（gitcode.com/HIT1920/TilingSolver），代码未全开源，无法 pin SHA 验真。作启发式参考 + 指针，**不作事实断言来源**。agent 用时须配证据（实际运行结果），启发式知识只作假设来源非事实断言。

## 工具定位

`AISS-TilingSolver` CLI 为 Ascend C 算子自动求解最优 tiling 参数（MatMul / Vector 两类型），免上机实测。位于 gitcode.com/HIT1920/TilingSolver（哈工大第三方，非 Ascend 官方 org）。

**核心原则**：引导用户正确调用工具并解读输出，**不要自己手动计算 tiling**。

## 获取工具

```bash
# aarch64
curl -LO https://gitcode.com/HIT1920/TilingSolver/releases/download/latest/tiling_solver_aarch64
curl -LO https://gitcode.com/HIT1920/TilingSolver/releases/download/latest/platform_info_aarch64
mv tiling_solver_aarch64 tiling_solver
mv platform_info_aarch64 platform_info

# x86_64
curl -LO https://gitcode.com/HIT1920/TilingSolver/releases/download/latest/tiling_solver_x86_64
curl -LO https://gitcode.com/HIT1920/TilingSolver/releases/download/latest/platform_info_x86_64
mv tiling_solver_x86_64 tiling_solver
mv platform_info_x86_64 platform_info

chmod +x tiling_solver platform_info
```

环境要求：aarch64 或 x86_64，glibc ≥ 2.38。

## 使用流程（3 步）

1. **采集硬件参数**：`./platform_info` → 输出核心数/各级缓存容量/带宽。
2. **构造输入 JSON**：硬件参数 + 算子 shape/dtype 填入 JSON。
3. **运行求解**：`./tiling_solver input.json` → 输出 JSON 含最优 tiling 参数。

## 算子类型

### MatMul（矩阵乘法）
必填：`type`, `M`, `N`, `K`（其余有默认值，硬件参数从 platform_info 获取）。
输出字段：`base_m`/`base_n`/`base_k`（内层切块）、`single_core_m`/`single_core_n`（每核范围）、`step_ka`/`step_kb`（K 方向 L1 步长）、`depth_a1`/`depth_b1`（L1 缓冲深度）、`db_l0a`/`db_l0b`/`db_l0c`（L0 双缓冲 1 或 2）、`iterate_order`（0=M 优先/1=N 优先）、`solve_time_ms`、`status`。

### Vector（逐元素算子，如 Add/LeakyReLU）
必填：`type`, `total_length`。
输出字段：`block_dim`（核数）、`tile_num`（每核 tile 数）、`buf_num`（缓冲数）、`tile_length`（每 tile 元素数）、`solve_time_ms`、`status`。

## 可选参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `optimize` | bool | true | 是否用 cost model 搜索最优解 |
| `timeout_ms` | int | 10000 | Z3 求解超时（毫秒） |

支持 dtype：float16/float32/bfloat16/int8/int16/int32/int64/uint8/uint16/uint32/uint64/bool（及别名 fp16/fp32/bf16/half/float/double 等）。

## 结果解读

- `status: "ok"` — 求解成功，参数可直接应用。
- `status: "unsat"` — 约束不可满足，当前 shape/dtype 在此硬件无可行解（缩小维度确认）。
- `status: "timeout"` — Z3 超时（增大 timeout_ms 或设 optimize:false）。
- `status: "error"` — 输入非法或内部异常。

## 故障排查

- "cannot execute binary file" → 下载了错误架构，`uname -m` 确认（aarch64/x86_64）。
- "GLIBC_2.38 not found" → glibc 过旧，升级系统或用容器。
- 返回 unsat → 缩小维度确认可行解，再逐步放大。
- 返回 timeout → 增大 timeout_ms（如 30000）或 `"optimize": false` 取可行解。

## ⚠️ Gotcha

**AISS 曾被误判虚构**：因只在 github grep（命中 faiss 误中），没查 gitcode。真实在 gitcode.com/HIT1920/TilingSolver。但因代码未全开源（preview），判 T3/external，不作 T1 事实来源——参数须以实际运行输出为准。

## 关联
- 方法论主源（T1，手动设计四要素）：`tiling-methodology.md`
- 分类总览：`algorithm-categories.md`
