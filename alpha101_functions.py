"""
Alpha101 因子实现 - 主入口文件
Implementation of 101 Alpha factors with type annotations

本文件为向后兼容保留，实际实现已拆分为：
- alpha_helpers.py: 辅助函数
- alpha_factors.py: 量化因子

This file is kept for backward compatibility.
Actual implementation is split into:
- alpha_helpers.py: Helper functions
- alpha_factors.py: Alpha factors
"""

# 导入所有辅助函数
from alpha_helpers import (
    # 时间序列操作
    rank, delay, delta, ts_sum, ts_mean, ts_min, ts_max,
    ts_argmax, ts_argmin, ts_rank,
    # 统计函数
    correlation, covariance, scale, decay_linear, signed_power,
    indneutralize,
    # 基础指标
    high_level, momentum_alpha
)

# 导入所有Alpha因子
from alpha_factors import (
    alpha001, alpha002, alpha003, alpha004, alpha005,
    alpha006, alpha007, alpha008, alpha009, alpha010,
    alpha011, alpha012, alpha013, alpha014, alpha015,
    alpha016
)

# 导出所有函数
__all__ = [
    # 辅助函数
    'rank', 'delay', 'delta', 'ts_sum', 'ts_mean', 'ts_min', 'ts_max',
    'ts_argmax', 'ts_argmin', 'ts_rank', 'correlation', 'covariance',
    'scale', 'decay_linear', 'signed_power', 'indneutralize',
    'high_level', 'momentum_alpha',
    # Alpha因子
    'alpha001', 'alpha002', 'alpha003', 'alpha004', 'alpha005',
    'alpha006', 'alpha007', 'alpha008', 'alpha009', 'alpha010',
    'alpha011', 'alpha012', 'alpha013', 'alpha014', 'alpha015',
    'alpha016'
]
