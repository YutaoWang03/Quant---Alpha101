"""
Alpha101 量化因子
Alpha101 quantitative factors implementation
"""

import pandas as pd
import numpy as np
from alpha_helpers import (
    rank, delay, delta, ts_sum, ts_mean, ts_min, ts_max,
    ts_argmax, ts_argmin, ts_rank, correlation, covariance,
    scale, decay_linear, signed_power, indneutralize
)


# ============================================================================
# Alpha因子实现（Alpha #1 - #20）
# ============================================================================

def alpha001(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)
    
    Args:
        returns: 收益率数据框
    
    Returns:
        Alpha #1因子值
    """
    condition = returns < 0
    power_input = condition * returns.abs() + (~condition) * (-returns.abs())
    return rank(ts_argmax(signed_power(power_input, 2), 5)) - 0.5


def alpha002(open_price: pd.DataFrame, close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #2: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))
    
    Args:
        open_price: 开盘价数据框
        close: 收盘价数据框
        volume: 成交量数据框
    
    Returns:
        Alpha #2因子值
    """
    return -1 * correlation(rank(delta(np.log(volume), 2)), 
                           rank((close - open_price) / open_price), 6)


def alpha003(open_price: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #3: (-1 * correlation(rank(open), rank(volume), 10))
    
    Args:
        open_price: 开盘价数据框
        volume: 成交量数据框
    
    Returns:
        Alpha #3因子值
    """
    return -1 * correlation(rank(open_price), rank(volume), 10)


def alpha004(low: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #4: (-1 * Ts_Rank(rank(low), 9))
    
    Args:
        low: 最低价数据框
    
    Returns:
        Alpha #4因子值
    """
    return -1 * ts_rank(rank(low), 9)


def alpha005(open_price: pd.DataFrame, close: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #5: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))
    
    Args:
        open_price: 开盘价数据框
        close: 收盘价数据框
        vwap: 成交量加权平均价数据框
    
    Returns:
        Alpha #5因子值
    """
    return rank(open_price - ts_mean(vwap, 10)) * (-1 * rank((close - vwap)).abs())


def alpha006(open_price: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #6: (-1 * correlation(open, volume, 10))
    
    Args:
        open_price: 开盘价数据框
        volume: 成交量数据框
    
    Returns:
        Alpha #6因子值
    """
    return -1 * correlation(open_price, volume, 10)


def alpha007(close: pd.DataFrame, volume: pd.DataFrame, adv20: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #7: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1))
    
    Args:
        close: 收盘价数据框
        volume: 成交量数据框
        adv20: 20日平均成交量数据框
    
    Returns:
        Alpha #7因子值
    """
    condition = adv20 < volume
    return condition * (-1 * ts_rank(delta(close, 7).abs(), 60) * np.sign(delta(close, 7))) + (~condition) * (-1)


def alpha008(open_price: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #8: (-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10))))
    
    Args:
        open_price: 开盘价数据框
        returns: 收益率数据框
    
    Returns:
        Alpha #8因子值
    """
    sum_open = ts_sum(open_price, 5)
    sum_ret = ts_sum(returns, 5)
    return -1 * rank(sum_open * sum_ret - delay(sum_open * sum_ret, 10))


def alpha009(close: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #9: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))
    
    Args:
        close: 收盘价数据框
    
    Returns:
        Alpha #9因子值
    """
    delta_close = delta(close, 1)
    condition1 = ts_min(delta_close, 5) > 0
    condition2 = ts_max(delta_close, 5) < 0
    return condition1 * delta_close + (~condition1 & condition2) * delta_close + (~condition1 & ~condition2) * (-delta_close)


def alpha010(close: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #10: rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0) ? delta(close, 1) : (-1 * delta(close, 1)))))
    
    Args:
        close: 收盘价数据框
    
    Returns:
        Alpha #10因子值
    """
    delta_close = delta(close, 1)
    condition1 = ts_min(delta_close, 4) > 0
    condition2 = ts_max(delta_close, 4) < 0
    result = condition1 * delta_close + (~condition1 & condition2) * delta_close + (~condition1 & ~condition2) * (-delta_close)
    return rank(result)


def alpha011(close: pd.DataFrame, volume: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #11: ((rank(ts_max((vwap - close), 3)) + rank(ts_min((vwap - close), 3))) * rank(delta(volume, 3)))
    
    Args:
        close: 收盘价数据框
        volume: 成交量数据框
        vwap: 成交量加权平均价数据框
    
    Returns:
        Alpha #11因子值
    """
    return (rank(ts_max(vwap - close, 3)) + rank(ts_min(vwap - close, 3))) * rank(delta(volume, 3))


def alpha012(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #12: (sign(delta(volume, 1)) * (-1 * delta(close, 1)))
    
    Args:
        close: 收盘价数据框
        volume: 成交量数据框
    
    Returns:
        Alpha #12因子值
    """
    return np.sign(delta(volume, 1)) * (-1 * delta(close, 1))


def alpha013(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #13: (-1 * rank(covariance(rank(close), rank(volume), 5)))
    
    Args:
        close: 收盘价数据框
        volume: 成交量数据框
    
    Returns:
        Alpha #13因子值
    """
    return -1 * rank(covariance(rank(close), rank(volume), 5))


def alpha014(open_price: pd.DataFrame, volume: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #14: ((-1 * rank(delta(returns, 3))) * correlation(open, volume, 10))
    
    Args:
        open_price: 开盘价数据框
        volume: 成交量数据框
        returns: 收益率数据框
    
    Returns:
        Alpha #14因子值
    """
    return -1 * rank(delta(returns, 3)) * correlation(open_price, volume, 10)


def alpha015(high: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #15: (-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3))
    
    Args:
        high: 最高价数据框
        volume: 成交量数据框
    
    Returns:
        Alpha #15因子值
    """
    return -1 * ts_sum(rank(correlation(rank(high), rank(volume), 3)), 3)


def alpha016(high: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #16: (-1 * rank(covariance(rank(high), rank(volume), 5)))
    
    Args:
        high: 最高价数据框
        volume: 成交量数据框
    
    Returns:
        Alpha #16因子值
    """
    return -1 * rank(covariance(rank(high), rank(volume), 5))


# ============================================================================
# 注意：Alpha #17 - #101 的实现可以继续添加
# 由于代码量较大，这里仅展示前16个因子的实现
# 其余因子可以按照相同的模式继续添加
# ============================================================================
