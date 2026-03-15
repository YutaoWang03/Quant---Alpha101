"""
Alpha101 辅助函数
Helper functions for Alpha101 factor calculations
"""

import pandas as pd
import numpy as np
from typing import Union


# ============================================================================
# 时间序列操作函数（Time Series Operations）
# ============================================================================

def rank(df: pd.DataFrame) -> pd.DataFrame:
    """
    横截面排名（Cross-sectional rank）
    
    Args:
        df: 输入数据框
    
    Returns:
        排名后的数据框，值在[0,1]之间
    """
    return df.rank(axis=1, pct=True)


def delay(df: pd.DataFrame, period: Union[int, float]) -> pd.DataFrame:
    """
    时间序列延迟（Time series delay）
    
    Args:
        df: 输入数据框
        period: 延迟的周期数
    
    Returns:
        延迟后的数据框
    """
    return df.shift(int(period))


def delta(df: pd.DataFrame, period: Union[int, float]) -> pd.DataFrame:
    """
    时间序列差分（Time series delta）
    
    Args:
        df: 输入数据框
        period: 差分的周期数
    
    Returns:
        差分后的数据框
    """
    return df.diff(int(period))


def ts_sum(df: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列求和（Time series sum）
    
    Args:
        df: 输入数据框
        window: 窗口大小
    
    Returns:
        滚动求和后的数据框
    """
    return df.rolling(window=int(window)).sum()


def ts_mean(df: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列均值（Time series mean）
    
    Args:
        df: 输入数据框
        window: 窗口大小
    
    Returns:
        滚动均值后的数据框
    """
    return df.rolling(window=int(window)).mean()


def ts_min(df: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列最小值（Time series minimum）
    
    Args:
        df: 输入数据框
        window: 窗口大小
    
    Returns:
        滚动最小值后的数据框
    """
    return df.rolling(window=int(window)).min()


def ts_max(df: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列最大值（Time series maximum）
    
    Args:
        df: 输入数据框
        window: 窗口大小
    
    Returns:
        滚动最大值后的数据框
    """
    return df.rolling(window=int(window)).max()


def ts_argmax(df: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列最大值索引（Time series argmax）
    
    Args:
        df: 输入数据框
        window: 窗口大小
    
    Returns:
        滚动窗口内最大值的索引位置
    """
    return df.rolling(window=int(window)).apply(lambda x: x.argmax(), raw=True)


def ts_argmin(df: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列最小值索引（Time series argmin）
    
    Args:
        df: 输入数据框
        window: 窗口大小
    
    Returns:
        滚动窗口内最小值的索引位置
    """
    return df.rolling(window=int(window)).apply(lambda x: x.argmin(), raw=True)


def ts_rank(df: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列排名（Time series rank）
    
    Args:
        df: 输入数据框
        window: 窗口大小
    
    Returns:
        滚动窗口内的排名
    """
    return df.rolling(window=int(window)).apply(lambda x: x.rank(pct=True).iloc[-1], raw=False)


# ============================================================================
# 统计函数（Statistical Functions）
# ============================================================================

def correlation(x: pd.DataFrame, y: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列相关性（Time series correlation）
    
    Args:
        x: 第一个数据框
        y: 第二个数据框
        window: 窗口大小
    
    Returns:
        滚动相关系数
    """
    return x.rolling(window=int(window)).corr(y)


def covariance(x: pd.DataFrame, y: pd.DataFrame, window: Union[int, float]) -> pd.DataFrame:
    """
    时间序列协方差（Time series covariance）
    
    Args:
        x: 第一个数据框
        y: 第二个数据框
        window: 窗口大小
    
    Returns:
        滚动协方差
    """
    return x.rolling(window=int(window)).cov(y)


def scale(df: pd.DataFrame, k: float = 1.0) -> pd.DataFrame:
    """
    缩放到总和为k（Scale to sum k）
    
    Args:
        df: 输入数据框
        k: 缩放目标总和
    
    Returns:
        缩放后的数据框
    """
    return df.div(df.abs().sum(axis=1), axis=0) * k


def decay_linear(df: pd.DataFrame, period: Union[int, float]) -> pd.DataFrame:
    """
    线性衰减加权移动平均（Linear decay weighted moving average）
    
    Args:
        df: 输入数据框
        period: 衰减周期
    
    Returns:
        线性衰减加权后的数据框
    """
    period = int(period)
    weights = np.arange(1, period + 1)
    weights = weights / weights.sum()
    return df.rolling(window=period).apply(lambda x: (x * weights).sum(), raw=True)


def signed_power(df: pd.DataFrame, exp: Union[int, float]) -> pd.DataFrame:
    """
    带符号的幂运算（Signed power）
    
    Args:
        df: 输入数据框
        exp: 指数
    
    Returns:
        保留符号的幂运算结果
    """
    return df.abs() ** exp * np.sign(df)


def indneutralize(df: pd.DataFrame, industry: pd.DataFrame) -> pd.DataFrame:
    """
    行业中性化（Industry neutralize）
    
    Args:
        df: 输入数据框
        industry: 行业分类数据框
    
    Returns:
        行业中性化后的数据框
    """
    return df.sub(df.groupby(industry).transform('mean'))


# ============================================================================
# 基础指标函数（Basic Indicators）
# ============================================================================

def high_level(open_price: pd.DataFrame, close_price: pd.DataFrame) -> pd.DataFrame:
    """
    当日价格高开程度
    
    Args:
        open_price: 开盘价数据框
        close_price: 收盘价数据框
    
    Returns:
        高开程度指标
    """
    return np.log(open_price / close_price.shift(1))


def momentum_alpha(close_price: pd.DataFrame, open_price: pd.DataFrame, d: int) -> pd.DataFrame:
    """
    动量Alpha
    
    Args:
        close_price: 收盘价数据框
        open_price: 开盘价数据框
        d: 天数
    
    Returns:
        动量Alpha指标
    """
    return np.log(close_price.shift(-d) / open_price)
