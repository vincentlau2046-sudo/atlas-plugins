#!/usr/bin/env python3
# precision-verify-template.py
# 自撰模板（AtlasHarness 自有许可，非外部源）。
# numpy golden vs NPU 输出的 rtol/atol 比对模板 —— 算子级精度验证的速查工具。
# 正式交付分级（L0/L1/L2 + MERE/MARE 阈值）用 references/precision-standard.md 的标准，
# 本模板是调试期快速判 pass/fail 的轻量脚本。
#
# 用法：
#   python3 precision-verify-template.py --golden golden.npy --actual npu_out.npy \
#       --dtype float16 --rtol 1e-3 --atol 1e-4
# 默认阈值（调试期速查，参考 ascendc-operator-precision.md）：
#   FP16: rtol=1e-3, atol=1e-4 ; FP32: rtol=1e-5, atol=1e-6 ; INT8/BF16 见下

import argparse
import numpy as np

# 调试期默认阈值（速查，非正式标准；正式标准见 precision-standard.md）
DEFAULT_THRESH = {
    "float16":  (1e-3, 1e-4),
    "bfloat16": (5e-3, 1e-3),
    "float32":  (1e-5, 1e-6),
    "int8":     (0.0, 0.0),     # 整型精确匹配
}


def mere(actual: np.ndarray, golden: np.ndarray) -> float:
    """平均相对误差 MERE（同 precision-standard.md 定义，+1e-7 防除零）."""
    denom = np.abs(golden) + 1e-7
    return float(np.mean(np.abs(actual - golden) / denom))


def mare(actual: np.ndarray, golden: np.ndarray) -> float:
    """最大相对误差 MARE."""
    denom = np.abs(golden) + 1e-7
    return float(np.max(np.abs(actual - golden) / denom))


def main() -> int:
    ap = argparse.ArgumentParser(description="numpy golden vs NPU output 精度比对（调试期速查）")
    ap.add_argument("--golden", required=True, help="golden .npy 路径（CPU 参考实现输出）")
    ap.add_argument("--actual", required=True, help="actual .npy 路径（NPU 算子输出）")
    ap.add_argument("--dtype", default="float16", choices=list(DEFAULT_THRESH),
                    help="dtype（决定默认阈值）")
    ap.add_argument("--rtol", type=float, default=None, help="覆盖默认 rtol")
    ap.add_argument("--atol", type=float, default=None, help="覆盖默认 atol")
    args = ap.parse_args()

    golden = np.load(args.golden)
    actual = np.load(args.actual)

    if golden.shape != actual.shape:
        print(f"FAIL: shape 不匹配 golden={golden.shape} actual={actual.shape}")
        return 1

    rtol, atol = DEFAULT_THRESH[args.dtype]
    rtol = args.rtol if args.rtol is not None else rtol
    atol = args.atol if args.atol is not None else atol

    # numpy allclose（rtol/atol 判据）
    ac_pass = np.allclose(actual, golden, rtol=rtol, atol=atol, equal_nan=False)

    # 生态标准判据（precision-standard.md：MERE<Threshold && MARE<10*Threshold）
    mere_v = mere(actual, golden)
    mare_v = mare(actual, golden)
    std_pass = (mere_v < rtol) and (mare_v < 10 * rtol)

    nan_count = int(np.isnan(actual).sum()) + int(np.isnan(golden).sum())
    inf_count = int(np.isinf(actual).sum()) + int(np.isinf(golden).sum())

    print(f"dtype={args.dtype} shape={golden.shape}")
    print(f"  rtol={rtol} atol={atol}")
    print(f"  MERE={mere_v:.3e}  MARE={mare_v:.3e}")
    print(f"  NaN={nan_count}  Inf={inf_count}")
    print(f"  allclose(rtol,atol): {'PASS' if ac_pass else 'FAIL'}")
    print(f"  std(MERE<rtol && MARE<10*rtol): {'PASS' if std_pass else 'FAIL'}")
    return 0 if (ac_pass and std_pass and nan_count == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
