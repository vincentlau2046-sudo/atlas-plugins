---
tier: T1
confidence: verified
source-of-truth:
  repo: cannbot-skills
  sha: c24e8b5bc53e190504d8b09359fe5d5fa4ef3a4c
  path: ops/pypto-precision-compare/{SKILL,precision-binary-search/SKILL}.md
  cann_version: 8.0.RC3
  verified_date: 2026-09-19
source-of-text:
  origin: cannbot
  ref: https://gitcode.com/cann/cannbot-skills@c24e8b5
  note: "从 cannbot pypto-precision-compare 的 SKILL + precision-binary-search/SKILL 抽取二分定位法 6 步流程/检查点 tensor 原理/关键技巧自撰重写；CANN OSL v2.0 non-sublicensable，引用+溯源不 vendor 文本"
license: CANN-OSL-2.0
---

# PyPTO 二分定位法（算子级中间结果隔离定位）

> 本文是 **算子级二分定位的主源**（T1，cannbot@c24e8b5 验真）。PyPTO（Python PyTorch Operator）是算子上板框架，用 `@pypto.frontend.jit()` 装饰器。当 DumpTensor 快速方法（`dumptensor-7step.md`）超过 7 次仍未定位时，切二分对比隔离 —— 在 kernel 添加检查点 tensor 作输入参数，二分找首个出错的 op。

## 一、核心原理

二分定位法通过 **检查点 tensor 作为 kernel 输入参数** 实现原地修改 + 中间结果对比：

1. **检查点 tensor 作输入参数**：在 kernel 函数定义中添加检查点 tensor 为输入参数（声明 shape + dtype），支持原地修改。
2. **与 golden 对应位置对比**：算子 kernel 与 golden 函数的检查点必须完全一致（数量/shape/dtype/顺序/计算逻辑）。
3. **二分定位**：从单个关键计算点开始，逐次添加检查点二分对比，直到找到精度不对的 op。

> 关键：检查点必须在**同一计算节点的相同状态**对比 —— 若 golden 中某变量被后续操作修改，kernel 对应检查点也须是修改后版本。

## 二、6 步工作流

### 步骤 1：分析代码结构，确定检查点

分析 kernel 和 golden 代码，确定关键计算节点。选计算节点**之后**的位置（结果有明确含义），优先选有明显边界的位置（如 matmul、softmax 之后）。

### 步骤 2：修改 kernel 函数，添加检查点 tensor

在 kernel 函数定义中添加检查点 tensor 作输入参数：

```python
@pypto.frontend.jit()
def your_kernel(input0, input1, out, checkpoint_tensor):  # 检查点作输入参数
    # ... 计算 ...
    pypto.assemble(checkpoint_tensor, intermediate_result)  # 原地写入检查点
    # 不 return，输出经 out 参数（out.move() 或 pypto.assemble）
```

**重要原则**：
- 检查点 tensor 作输入参数直接在 kernel 函数声明（不是返回值）。
- 测试函数中用 `torch.empty()` 初始化检查点 tensor。
- kernel 内部不 return，输出 tensor 经 out 参数传入，用 `out.move()` 或 `pypto.assemble` 写入。
- 算子与 golden 的检查点完全一致（shape/dtype/数量/顺序）。
- 循环内变量：循环外建大 tensor，循环内用 `view` / `pypto.assemble` 赋值切片。
- 多层循环复杂算子且算子与 golden 实现一致时，可比循环内临时变量而非 assemble 后大 tensor（注意非对齐尾块带脏数据致 assert 误判，选第一块对比）。

**shape 推导方法**：
- 从变量定义推导（赋值语句右边的 shape 变换）。
- 从权重/输入 tensor shape 推导（按 matmul/view 规则）。
- 从循环 tile 推导（循环内变量第一维 = tile_batch，追溯到原始输入 shape）。

### 步骤 3：修改 golden 函数，增加返回值

golden 函数返回检查点对应 tensor（与 kernel 检查点数量/意义/顺序一致）：

```python
def golden(input0, input1) -> Tuple[Tensor, Tensor]:  # 返回检查点
    # ... 计算 ...
    return output, intermediate_checkpoint
```

修改返回类型注解，增加检查点对应 tensor 类型。若 golden 有多个子函数调用，确保每个子函数返回值数量与意义匹配。

### 步骤 4：修改测试函数，对比所有结果

```python
checkpoint_tensor = torch.empty(...)  # 创建检查点
pypto_output = your_kernel(input0, input1, out, checkpoint_tensor)  # kernel 原地写检查点
golden_output, golden_checkpoint = golden(input0, input1)            # golden 返回检查点
# 对比最终结果 + 所有检查点
```

> device 输出为 0 可能是卡冲突或检查点添加有误；结果相差过大或 shape 不匹配 → 重查检查点代码。

### 步骤 5：运行测试并分析结果

定位第一个精度不匹配的检查点 → 问题在该检查点**之前或该检查点的计算中**。

### 步骤 6：二分定位精度问题

从个别关键计算点开始，每次添加一个检查点，二分对比，直到找到精度不对的具体 op。

## 三、关键技巧

| 技巧 | 说明 |
|---|---|
| **循环输出** | 检查点在循环内时用切片或 `view` / `pypto.assemble` 赋值 |
| **shape 对齐** | 确保 jit 和 golden 输出 shape 一致 |
| **dtype 转换** | 不一致时统一转 float32 对比（如 golden float32 / jit bf16） |
| **assemble 变量名** | `pypto.assemble` 输入输出变量名**不能相同**（否则报 "mix assemble and common operation"） |
| **assemble dtype 一致** | `pypto.assemble` 要求输入输出 dtype 一致（否则 "Source dtype must be same with dst dtype"），用 cast 转换 |
| **检查点 shape 理解** | 准确理解检查点变量实际 shape（kernel 与 golden 必须一致才能对比） |

## 四、另一条路：文件保存方法（verify 模式）

除二分外，PyPTO 还提供文件保存方法（`pass_verify_save` + `torch.save`）和 tensor_graph 校验：

```python
verify_options = {
    "enable_pass_verify": True,
    "pass_verify_save_tensor": True,   # 保存中间 tensor
    "pass_verify_pass_filter": []
}
@pypto.frontend.jit(verify_options=verify_options)
def your_kernel(...): ...

# 须严格按 计算 golden → 设置 golden → 执行算子 顺序
torch_output = torch.add(input0, input1)
pypto.set_verify_golden_data(goldens=[None, None, torch_output.cpu()])
pypto_output = your_kernel(input0, input1)
```

编译：`python3 -m pip install . --verbose`（PyPTO 算子实现文件须先编译安装）。

> 选型：明确知问题所在用文件保存（verify）；定位首个出错 op 用二分（binary）；Pass 级校验用 precision-pass。未指定 mode 走 tensor_graph 校验全自动决策树。

## 关联

- `ascendc-operator-precision.md` — 调试计数规则（>7 次切二分）+ 9 陷阱表
- `dumptensor-7step.md` — DumpTensor 快速方法（二分的前置，≤7 次先用）
- `precision-standard.md` — 比对通过阈值
