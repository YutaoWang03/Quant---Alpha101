#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha101 辅助函数
Helper functions for Alpha101 factors implementation
"""

import pandas as pd
import numpy as np


def ts_rank(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    时间序列排名（Ts_Rank）
    计算每只股票在过去window天内的时间序列排名
    
    Args:
        df: 输入数据 DataFrame
        window: 时间窗口
    
    Returns:
        时间序列排名 DataFrame
    """
    def rank_last(x):
        """计算最后一个值在窗口内的排名"""
        if len(x) < 2:
            return np.nan
        return (x.rank(pct=True).iloc[-1])
    
    return df.rolling(window=window).apply(rank_last, raw=False)


def ts_argmax(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    时间序列最大值索引（Ts_ArgMax）
    返回过去window天内最大值出现的位置（从0开始）
    
    Args:
        df: 输入数据 DataFrame
        window: 时间窗口
    
    Returns:
        最大值索引 DataFrame
    """
    return df.rolling(window=window).apply(lambda x: x.argmax(), raw=True)


def ts_argmin(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    时间序列最小值索引（Ts_ArgMin）
    返回过去window天内最小值出现的位置（从0开始）
    
    Args:
        df: 输入数据 DataFrame
        window: 时间窗口
    
    Returns:
        最小值索引 DataFrame
    """
    return df.rolling(window=window).apply(lambda x: x.argmin(), raw=True)


def ts_min(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    时间序列最小值（ts_min）
    
    Args:
        df: 输入数据 DataFrame
        window: 时间窗口
    
    Returns:
        滚动最小值 DataFrame
    """
    return df.rolling(window=window).min()


def ts_max(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    时间序列最大值（ts_max）
    
    Args:
        df: 输入数据 DataFrame
        window: 时间窗口
    
    Returns:
        滚动最大值 DataFrame
    """
    return df.rolling(window=window).max()


def delta(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """
    差分（delta）
    计算当前值与period天前的差值
    
    Args:
        df: 输入数据 DataFrame
        period: 差分周期
    
    Returns:
        差分结果 DataFrame
    """
    return df.diff(period)


def delay(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """
    延迟（delay）
    返回period天前的值
    
    Args:
        df: 输入数据 DataFrame
        period: 延迟周期
    
    Returns:
        延迟结果 DataFrame
    """
    return df.shift(period)


def decay_linear(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    线性衰减加权移动平均（decay_linear）
    权重从1到window线性递减
    
    Args:
        df: 输入数据 DataFrame
        window: 时间窗口
    
    Returns:
        线性衰减加权移动平均 DataFrame
    """
    weights = np.arange(1, window + 1)
    weights = weights / weights.sum()
    
    def weighted_mean(x):
        if len(x) < window:
            return np.nan
        return np.sum(weights * x)
    
    return df.rolling(window=window).apply(weighted_mean, raw=True)


def scale(df: pd.DataFrame, constant: float = 1.0) -> pd.DataFrame:
    """
    缩放（scale）
    对每一行进行缩放，使得绝对值之和等于constant
    
    Args:
        df: 输入数据 DataFrame
        constant: 缩放常数（默认1.0）
    
    Returns:
        缩放后的 DataFrame
    """
    return df.div(df.abs().sum(axis=1), axis=0) * constant


def signed_power(df: pd.DataFrame, power: float) -> pd.DataFrame:
    """
    带符号的幂运算（SignedPower）
    保持符号的幂运算
    
    Args:
        df: 输入数据 DataFrame
        power: 幂次
    
    Returns:
        带符号的幂运算结果 DataFrame
    """
    return np.sign(df) * (np.abs(df) ** power)
