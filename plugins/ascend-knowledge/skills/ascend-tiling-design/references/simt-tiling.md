---
tier: T2
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-simt-tiling-design/{SKILL.md,references/guide.md}
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "草稿来自 cannbot ascendc-simt-tiling-design（SKILL.md + references/guide.md 2 文件），本参考抽取 SIMT vs SIMD 差异/核数切分/线程数/DCache-UB 自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# SIMT 类算子 Tiling 设计

> SIMT 算子切分参考（T2，cannbot@c24e8b5 验真，源 ascendc-simt-tiling-design 2 文件）。**SIMT ≠ SIMD**：SIMT 以核数切分 + 线程数设置为核心，不涉及 UB 切分和 Buffer 规划（那是 SIMD/Vector 的范式）。

## 一、SIMT vs SIMD 切分差异

| 要素 | SIMD（Vector） | SIMT |
|---|---|---|
| 多核切分 | 按 UB 单次处理量切分 | 按元素总量切分（`ceil(总量/单核最少元素数)`） |
| 单核并行 | UB Buffer + 向量指令 | 线程数（constexpr 编译期常量） |
| 数据搬运 | 需显式 Load/Store | 支持直接读写 GM |
| UB 使用 | 全量使用 | 仅核内共享场景使用，DCache ≥32KB |
| Buffer 规划 | inQueue/outQueue/tmpBuf | TBuf（仅在需共享内存时用） |

> SIMD 算子 Tiling 设计参考 `tiling-methodology.md` + 各 category reference（broadcast/sort/elewise 等）。本参考仅覆盖 SIMT 范式。

## 二、核数切分策略

```
总核数 = ceil(输出元素总数 / 单核最少处理元素数)
单核最少处理元素数建议 1024，需对 warp(32) 对齐
```

- 通过 tiling 侧 `SetBlockDim` 设置核数。
- 合理设置 `perCoreElements` 避免负载不均。
- **避免总数据量少但启动核数多**的场景（空转浪费）。数据量小导致线程空转过多时，应调整**核数**（`SetBlockDim`）适配，而非减少线程数。

## 三、线程数设置策略

- 默认 **1024**，最大 **2048**，必须是 `constexpr` 编译期常量。
- `LAUNCH_BOUND(N)` 与 `Simt::Dim3(N)` 必须使用**同一个常量**。
- **禁止从 tiling 数据动态获取线程数**（运行时变量）。

**按算子类型选择**：

| 算子类型 | 建议线程数 | 原因 |
|---|---|---|
| 搬运类算子 | 2048 / 1024 | 更多线程隐藏内存延迟 |
| 计算类算子 | 512 / 1024 | 寄存器压力大，需平衡 |

**正确写法**：

```cpp
constexpr uint32_t THREAD_NUM = 512;

__simt_vf__ __aicore__ LAUNCH_BOUND(THREAD_NUM) inline void OpComputeSimt(...);
Simt::VF_CALL<OpComputeSimt<T>>(Simt::Dim3(THREAD_NUM), args...);
```

**错误写法（严禁）**：

```cpp
int32_t threadNum = static_cast<int32_t>(tilingData_->threadNum);  // 运行时变量
Simt::VF_CALL<OpComputeSimt<T>>(Simt::Dim3(threadNum), args...);
```

## 四、DCache 与 UB 空间分配

SIMT 算子不能使用全部 UB 空间，需为 DCache 预留 ≥32KB：

```cpp
constexpr uint64_t DCACHE_SIZE = 128 * 1024;     // DCache 预留
uint64_t ubsize = 256 * 1024;
context->SetLocalMemorySize(ubsize - DCACHE_SIZE);
```

**可用 UB = 256KB − 8KB(预留) − 32KB(DCache 最低) = 216KB**。

- DCache 必须 ≥32KB；通过 tiling 侧 `SetLocalMemorySize` 设置。
- 仅核内线程需共享内存时才用 TBuf 分配 UB；否则线程直接读写 GM。

## 五、设计要点速查

1. 先定**核数**（`SetBlockDim`，按元素总量/warp 对齐）→ 再定**线程数**（constexpr，按算子类型）→ 最后定 **DCache/UB**（`SetLocalMemorySize`，预留 ≥32KB DCache）。
2. 线程数是编译期常量，核数是运行时 tiling 参数——两者解耦，数据量变化调核数不调线程数。
3. SIMT 不做 UB tile 切分（无 ubFormer/ubLoop 概念），单核靠线程并行覆盖 `perCoreElements`。

## 关联
- SIMD 方法论主源：`tiling-methodology.md`（T1，四要素）
- 分类总览：`algorithm-categories.md`（T2，9 类 support status）
- SIMT ≠ SIMD 范式差异详见源 `ascendc-simt-tiling-design` skill
