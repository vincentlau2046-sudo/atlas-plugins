---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/ascendc-runtime-debug/references/kernel_binary_debug.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-20
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot ascendc-runtime-debug 的 kernel_binary_debug 抽取 5 流程（编译缓存/SEL匹配/dtype缺失/vendor冲突/opParaSize）+ opc kernelList 后缀系统事实自撰重写；CANN OSL v2.0 non-sublicensable field-limited 华为 AI 处理器，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# Kernel 二进制与构建系统调试

> 本文是 **算子二进制/安装/SEL 排查主源**（T1，cannbot@c24e8b5 验真）。面向 561003（Kernel 查找失败）、361001（特定 dtype）、修改后输出不变等构建系统问题。与 `error-code-taxonomy.md`（§四 561xxx）配合。

## 一、症状-根因速查

| 症状 | 最可能根因 | 进阶 |
|---|---|---|
| 修改 Kernel 后输出不变 | 二进制缓存未清 / 旧包未卸 | §二 |
| 561003 FIND_KERNEL_ERROR | TilingKey 与 SEL 声明不匹配 | §三 |
| 特定 dtype 返回 361001 | SEL 缺该 dtype 条目 | §四 |
| 多版本 vendor 包冲突 | `vendors/` 与 `opp/vendors/` 同存 | §五 |
| opParaSize 不匹配 | TilingData struct 大小 ≠ JSON opParaSize | §六 |

## 二、修改后输出不变

4 检查点（按序）：

1. **编译缓存**：`rm -rf build/`；opc 编译器独立缓存 `$HOME/atc_data/kernel_cache/`（存在则删对应条目）；完全清理后重建。
2. **二进制是否更新**：`sha256sum build/op_kernel/*.o`（或 `build/out/*/op_kernel/lib/*.so`）对比编辑前后 —— 不变=编译器缓存问题（回 §1）；变但结果不变=§3。
3. **安装是否正确**：查 install 脚本实际安装路径（`grep -n "cp\|install\|mv" build.sh`）；`sha256sum $ASCEND_OPP_PATH/vendors/<vendor>/op_impl/ai_core/tbe/op_kernel/lib/*.so` 对比构建产物 —— 不一致=install 脚本问题。
4. **旧包清理**：`rm -rf $ASCEND_OPP_PATH/vendors/<vendor>/` + `$ASCEND_HOME_PATH/vendors/<vendor>/` → 重建。

## 三、TilingKey / SEL 不匹配（561003）

### 核心机制

opc 编译器将每个 `(DTYPE, AXIS_MODE, LOAD_MODE)` 组合编译为**独立 kernel 二进制变体**，用 kernelList 后缀区分：

| suffix | dtype 值 | 类型 |
|---|---|---|
| `_0` | C_DT_FLOAT (0) | float32 |
| `_1` | C_DT_FLOAT16 (1) | float16 |
| `_27` | C_DT_BF16 (27) | bfloat16 |

运行时框架按实际 dtype 查匹配后缀 —— 找不到 → 361001（或 561003）。

### 3 位置必须对齐

```
tiling_key.h  — SEL 声明（ASCENDC_TPL_DATATYPE_DECL）
       ↓
tiling.cpp    — Host 侧传 Dtype 值（ASCENDC_TPL_SEL_PARAM）
       ↓
kernel 入口   — GET_TILING_KEY 取值
       ↓
opc 自动生成 kernelList 后缀
```

### 常见错误

- **SEL 缺 dtype**：只声明 `C_DT_FLOAT` → fp16/bf16 调用 361001。须声明全 dtype 并用 `ASCENDC_TPL_INPUT(0)` 绑定 input[0] 实际类型。
- **Host 硬编码 dtype**：`static_cast<uint32_t>(ge::DT_FLOAT)` 写死 → 须用实际输入 `dataType`。`ge::DT_FLOAT=0 / DT_FLOAT16=1 / DT_BF16=27`（须与 `C_DT_*` 一致）。
- **缺某 TilingKey 组合的 SEL 条目**：每个 TilingKey 须为所有 dtype 加 `ASCENDC_TPL_ARGS_SEL(... ASCENDC_TPL_DATATYPE_SEL(DTYPE, C_DT_...) ...)`。

### 验证

```bash
cat build/op_kernel/<op>_<arch>.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
for k in d.get('kernelList', []):
    print(f'  suffix={k[\"suffix\"]}, paraSize={k.get(\"opParaSize\", \"?\")}')"
# 应见 _0, _1, _27（若支持 3 种 dtype）
```

## 四、SEL dtype 条目缺失（特定 dtype 361001）

症状：某 dtype + axis 组合 361001，其他正常。排查：① `tiling_key.h` 该 TilingKey 是否有对应 dtype 的 `ASCENDC_TPL_ARGS_SEL` 条目；② `tiling.cpp` 的 `ASCENDC_TPL_SEL_PARAM` 传的 dtype 值是否与 SEL 一致；③ 构建后 JSON 是否含对应 kernelList 后缀。

## 五、多版本 vendor 包冲突

CANN 按以下顺序查找算子包：
1. `$ASCEND_OPP_PATH/vendors/<vendor>/`（opp 优先级高）
2. `$ASCEND_HOME_PATH/vendors/<vendor>/`（home 兜底）

两位置都装同一算子 → opp 版本优先加载，home 旧配置可能被意外激活。

**排查**：`find $ASCEND_OPP_PATH/vendors/ $ASCEND_HOME_PATH/vendors/ -name "<vendor>" -type d`，对比各位置 JSON 的 `opFile`/`kernelList`/`dtype` 差异。

**修复**：两位置全清 → 重建 → 验证只剩一处。

## 六、opParaSize 不匹配

`opParaSize`（JSON 字段）由 opc 自动计算，可能与 `sizeof(TilingData)` 不同（编译器加对齐 padding）。

**排查**：`printf("sizeof(TilingData) = %zu\n", sizeof(TilingData))` 对比 JSON `opParaSize`（`grep '"opParaSize"' build/op_kernel/*.json`）。

- 小幅差异 → 对齐 padding，通常不影响功能。
- 大幅差异 → struct 成员遗漏/多余。
- 须强制匹配 → `#pragma pack` 或调成员顺序。

## 调试命令速查

| 命令 | 用途 |
|---|---|
| `sha256sum build/**/*.o` | 验二进制是否更新 |
| `cat build/op_kernel/*.json \| grep kernelList` | 查生成的 kernel 变体 |
| `find $ASCEND_OPP_PATH/vendors -name "*.so"` | 查已安装二进制（opp） |
| `find $ASCEND_HOME_PATH/vendors -name "*.so"` | 查兜底位置（home） |
| `rm -rf $HOME/atc_data/kernel_cache/` | 清 opc 编译器缓存 |
| `rm -rf build/` | 清构建产物 |

## 关联

- `error-code-taxonomy.md` — 561003/561112/361001 错误码定义
- `fault-tool-routing.md` — 561003 路由到 Diagnoser 还是手工排查
