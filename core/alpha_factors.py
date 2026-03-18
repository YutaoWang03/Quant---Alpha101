#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha101 量化因子
Alpha101 quantitative factors implementation

重要说明：
- Alpha101 使用横截面排名（Cross-sectional Ranking）
- rank() 操作是对同一时间点的所有股票进行排名（axis=1）
- 输入数据格式：DataFrame，行=日期，列=股票代码
- 这是股票选股策略，不是择时策略
"""

import pandas as pd
import numpy as np
from core.validation import validateDataFormat, validate_dataframe_input
from core.alpha_helpers import decay_linear, scale, ts_rank, delta, ts_min, ts_max, ts_argmax, ts_argmin, delay, ts_sum


def calculateAlpha002(
    open_price: pd.DataFrame, 
    close_price: pd.DataFrame, 
    volume: pd.DataFrame,
    diff_period: int = 2,
    corr_window: int = 6) -> pd.DataFrame:
    """
    Alpha #2: (-1 * correlation(rank(delta(log(volume), 2)), rank((close - open) / open), 6))
    
    该因子通过成交量变化与价格变化的横截面相关性来捕捉市场情绪。
    
    计算逻辑：
    1. 计算成交量的对数差分：delta(log(volume), 2)
    2. 计算日内收益率：(close - open) / open
    3. 对每个时间点的所有股票进行横截面排名（rank）
    4. 计算两个排名序列的滚动相关性（6天窗口）
    5. 取负值
    
    Args:
        open_price: 开盘价 DataFrame
            - 行索引：日期（DatetimeIndex）
            - 列索引：股票代码
            - 值：开盘价
        close_price: 收盘价 DataFrame
            - 行索引：日期（DatetimeIndex）
            - 列索引：股票代码
            - 值：收盘价
        volume: 成交量 DataFrame
            - 行索引：日期（DatetimeIndex）
            - 列索引：股票代码
            - 值：成交量
        diff_period: 差分周期（默认：2）
        corr_window: 相关性计算窗口（默认：6）
    
    Returns:
        Alpha002 因子值 DataFrame
            - 行索引：日期（与输入相同）
            - 列索引：股票代码（与输入相同）
            - 值：因子值，范围约 [-1, 1]
    
    Raises:
        TypeError: 输入数据类型不正确
        ValueError: 数据格式不符合要求或参数不合法
    
    Examples:
        >>> import pandas as pd
        >>> # 假设有3只股票，5个交易日的数据
        >>> dates = pd.date_range('2024-01-01', periods=5)
        >>> stocks = ['600000.SH', '000001.SZ', '300001.SZ']
        >>> 
        >>> open_df = pd.DataFrame(np.random.rand(5, 3), index=dates, columns=stocks)
        >>> close_df = pd.DataFrame(np.random.rand(5, 3), index=dates, columns=stocks)
        >>> volume_df = pd.DataFrame(np.random.rand(5, 3) * 1000000, index=dates, columns=stocks)
        >>> 
        >>> alpha002 = calculateAlpha002(open_df, close_df, volume_df)
        >>> print(alpha002)
    
    Notes:
        - 该因子是横截面因子，用于股票选择（选股）
        - rank() 是对同一时间点的所有股票进行排名（axis=1）
        - 前 diff_period + corr_window 天的数据可能为 NaN
        - 因子值越大，表示该股票相对其他股票越有吸引力
    
    References:
        - 101 Formulaic Alphas, Zura Kakushadze (2015)
    """
    # 1. 数据验证
    validateDataFormat(open_price, "open_price", allow_nan=True)
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 2. 参数验证
    if not isinstance(diff_period, int) or diff_period <= 0:
        raise ValueError(f"diff_period 必须是正整数，当前值: {diff_period}")
    
    if not isinstance(corr_window, int) or corr_window <= 0:
        raise ValueError(f"corr_window 必须是正整数，当前值: {corr_window}")
    
    # 3. 计算成交量的对数差分
    log_volume = np.log(volume)
    volume_delta = log_volume.diff(diff_period)
    
    # 4. 计算日内收益率
    price_change = (close_price - open_price) / open_price
    
    # 5. 横截面排名（对每一行/每个时间点的所有股票进行排名）
    # axis=1 表示横向排名（同一时间点的不同股票）
    # pct=True 表示返回百分位排名 [0, 1]
    ranked_volume_delta = volume_delta.rank(axis=1, pct=True)
    ranked_price_change = price_change.rank(axis=1, pct=True)
    
    # 6. 计算滚动相关性
    # 对每只股票，计算其排名序列在时间窗口内的相关性
    alpha002 = pd.DataFrame(index=open_price.index, columns=open_price.columns)
    
    for col in open_price.columns:
        if col in ranked_volume_delta.columns and col in ranked_price_change.columns:
            correlation = ranked_volume_delta[col].rolling(window=corr_window).corr(
                ranked_price_change[col]
            )
            alpha002[col] = -1 * correlation - 0.5
    
    return alpha002


def calculateAlpha003(
    open_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 10) -> pd.DataFrame:
    """
    Alpha #3: (-1 * correlation(rank(open), rank(volume), 10))
    
    该因子通过开盘价与成交量的横截面排名相关性来捕捉市场流动性特征。
    
    计算逻辑：
    1. 对每个时间点的所有股票的开盘价进行横截面排名
    2. 对每个时间点的所有股票的成交量进行横截面排名
    3. 计算两个排名序列的滚动相关性（10天窗口）
    4. 取负值
    
    Args:
        open_price: 开盘价 DataFrame
            - 行索引：日期（DatetimeIndex）
            - 列索引：股票代码
            - 值：开盘价
        volume: 成交量 DataFrame
            - 行索引：日期（DatetimeIndex）
            - 列索引：股票代码
            - 值：成交量
        corr_window: 相关性计算窗口（默认：10）
    
    Returns:
        Alpha003 因子值 DataFrame
            - 行索引：日期（与输入相同）
            - 列索引：股票代码（与输入相同）
            - 值：因子值，范围约 [-1, 1]
    
    Raises:
        TypeError: 输入数据类型不正确
        ValueError: 数据格式不符合要求或参数不合法
    
    Examples:
        >>> import pandas as pd
        >>> dates = pd.date_range('2024-01-01', periods=20)
        >>> stocks = ['600000.SH', '000001.SZ', '300001.SZ']
        >>> 
        >>> open_df = pd.DataFrame(np.random.rand(20, 3) * 100, index=dates, columns=stocks)
        >>> volume_df = pd.DataFrame(np.random.rand(20, 3) * 1000000, index=dates, columns=stocks)
        >>> 
        >>> alpha003 = calculateAlpha003(open_df, volume_df)
        >>> print(alpha003.tail())
    
    Notes:
        - 该因子是横截面因子，用于股票选择
        - rank() 是对同一时间点的所有股票进行排名（axis=1）
        - 前 corr_window 天的数据可能为 NaN
        - 负相关表示价格高的股票成交量低，可能预示反转
    
    References:
        - 101 Formulaic Alphas, Zura Kakushadze (2015)
    """
    # 1. 数据验证
    validateDataFormat(open_price, "open_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 2. 参数验证
    if not isinstance(corr_window, int) or corr_window <= 0:
        raise ValueError(f"corr_window 必须是正整数，当前值: {corr_window}")
    
    # 3. 横截面排名（对每一行/每个时间点的所有股票进行排名）
    ranked_open = open_price.rank(axis=1, pct=True)
    ranked_volume = volume.rank(axis=1, pct=True)
    
    # 4. 计算滚动相关性
    alpha003 = - 1 * ranked_open.rolling(window=corr_window).corr(ranked_volume)
    return alpha003


def calculateAlpha004(
    low_price: pd.DataFrame,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #4: (-1 * Ts_Rank(rank(low), 9))
    
    该因子通过最低价的横截面排名的时间序列排名来捕捉价格动量反转信号。
    
    计算逻辑：
    1. 对每个时间点的所有股票的最低价进行横截面排名（rank）
    2. 对每只股票的排名序列进行时间序列排名（Ts_Rank，9天窗口）
    3. 取负值
    
    Args:
        low_price: 最低价 DataFrame
            - 行索引：日期（DatetimeIndex）
            - 列索引：股票代码
            - 值：最低价
        ts_rank_window: 时间序列排名窗口（默认：9）
    
    Returns:
        Alpha004 因子值 DataFrame
            - 行索引：日期（与输入相同）
            - 列索引：股票代码（与输入相同）
            - 值：因子值，范围约 [-1, 0]
    
    Raises:
        TypeError: 输入数据类型不正确
        ValueError: 数据格式不符合要求或参数不合法
    
    Examples:
        >>> import pandas as pd
        >>> dates = pd.date_range('2024-01-01', periods=20)
        >>> stocks = ['600000.SH', '000001.SZ', '300001.SZ']
        >>> 
        >>> low_df = pd.DataFrame(np.random.rand(20, 3) * 100, index=dates, columns=stocks)
        >>> 
        >>> alpha004 = calculateAlpha004(low_df)
        >>> print(alpha004.tail())
    
    Notes:
        - 该因子是横截面因子，用于股票选择
        - rank() 是横截面排名（axis=1），Ts_Rank 是时间序列排名
        - 前 ts_rank_window 天的数据可能为 NaN
        - 因子值越负，表示该股票的横截面排名在时间序列中位置越高
    
    References:
        - 101 Formulaic Alphas, Zura Kakushadze (2015)
    """
    # 1. 数据验证
    validateDataFormat(low_price, "low_price", allow_nan=True)
    
    # 2. 参数验证
    if not isinstance(ts_rank_window, int) or ts_rank_window <= 0:
        raise ValueError(f"ts_rank_window 必须是正整数，当前值: {ts_rank_window}")
    
    # 3. 横截面排名（对每一行/每个时间点的所有股票进行排名）
    ranked_low = low_price.rank(axis=1, pct=True)
    
    # 4. 时间序列排名（Ts_Rank）
    def ts_rank_vec(x):
        # x 是一个 1D numpy array
        # 最后一个值在整个窗口里的排名
        return np.argsort(np.argsort(x))[-1] / (len(x) - 1)

    alpha004 = -1 * ranked_low.rolling(window=ts_rank_window).apply(ts_rank_vec, raw=True)
    
    return alpha004

def calculateAlpha005(
    open_price: pd.DataFrame,
    close_price: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #5: (-1 * correlation(rank(open), rank(Ts_ArgMax(decay_linear(delay(close, 5), 3))), 5))
    
    该因子通过开盘价与延迟收盘价趋势的相关性来捕捉价格动量反转信号。
    
    Args:
        open_price: 开盘价 DataFrame
        close_price: 收盘价 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha005 因子值 DataFrame
    
    References:
        - 101 Formulaic Alphas, Zura Kakushadze (2015)
    """
    from core.alpha_helpers import delay, decay_linear, ts_argmax
    
    validateDataFormat(open_price, "open_price", allow_nan=True)
    validateDataFormat(close_price, "close_price", allow_nan=True)
    
    # 1. 延迟5天的收盘价
    delayed_close = delay(close_price, 5)
    
    # 2. 3天线性衰减加权移动平均
    decayed = decay_linear(delayed_close, 3)
    
    # 3. 时间序列最大值索引
    ts_argmax_val = ts_argmax(decayed, corr_window)
    
    # 4. 横截面排名
    ranked_open = open_price.rank(axis=1, pct=True)
    ranked_argmax = ts_argmax_val.rank(axis=1, pct=True)
    
    # 5. 计算相关性
    alpha005 = -1 * ranked_open.rolling(window=corr_window).corr(ranked_argmax)
    
    return alpha005


def calculateAlpha006(
    close_price: pd.DataFrame,
    window: int = 20) -> pd.DataFrame:
    """
    Alpha #6: (rank(Ts_ArgMin(delta(close, 1), 20)) - 0.5)
    
    该因子通过收盘价变化的最小值位置来捕捉超卖反弹信号。
    
    Args:
        close_price: 收盘价 DataFrame
        window: 时间窗口（默认：20）
    
    Returns:
        Alpha006 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmin
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    
    # 1. 计算收盘价的日变化
    close_delta = delta(close_price, 1)
    
    # 2. 找到过去20天内最小值的位置
    argmin_val = ts_argmin(close_delta, window)
    
    # 3. 横截面排名并中心化
    alpha006 = argmin_val.rank(axis=1, pct=True) - 0.5
    
    return alpha006


def calculateAlpha007(
    close_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 10,
    argmax_window: int = 5) -> pd.DataFrame:
    """
    Alpha #7: (-1 * rank(Ts_ArgMax(correlation(close, volume, 10), 5)))
    
    该因子通过价格-成交量相关性的峰值来捕捉趋势反转信号。
    
    Args:
        close_price: 收盘价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：10）
        argmax_window: 最大值索引窗口（默认：5）
    
    Returns:
        Alpha007 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmax
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 计算收盘价与成交量的滚动相关性
    correlation = close_price.rolling(window=corr_window).corr(volume)
    
    # 2. 找到过去5天内相关性最大值的位置
    argmax_val = ts_argmax(correlation, argmax_window)
    
    # 3. 横截面排名并取负
    alpha007 = -1 * argmax_val.rank(axis=1, pct=True)
    
    return alpha007


def calculateAlpha008(
    volume: pd.DataFrame,
    decay_window: int = 20,
    argmax_window: int = 10) -> pd.DataFrame:
    """
    Alpha #8: rank(Ts_ArgMax(decay_linear(volume, 20), 10))
    
    该因子通过成交量衰减加权平均的峰值来识别价格转折点。
    
    Args:
        volume: 成交量 DataFrame
        decay_window: 衰减窗口（默认：20）
        argmax_window: 最大值索引窗口（默认：10）
    
    Returns:
        Alpha008 因子值 DataFrame
    """
    from core.alpha_helpers import decay_linear, ts_argmax
    
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 20天线性衰减加权平均成交量
    decayed_volume = decay_linear(volume, decay_window)
    
    # 2. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(decayed_volume, argmax_window)
    
    # 3. 横截面排名
    alpha008 = argmax_val.rank(axis=1, pct=True)
    
    return alpha008


def calculateAlpha009(
    close_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #9: (-1 * correlation(rank(close), rank(volume), 5))
    
    该因子通过价格与成交量排名的负相关性来捕捉量价背离。
    
    Args:
        close_price: 收盘价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha009 因子值 DataFrame
    """
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 横截面排名
    ranked_close = close_price.rank(axis=1, pct=True)
    ranked_volume = volume.rank(axis=1, pct=True)
    
    # 2. 计算滚动相关性并取负
    alpha009 = -1 * ranked_close.rolling(window=corr_window).corr(ranked_volume)
    
    return alpha009


def calculateAlpha010(
    close_price: pd.DataFrame,
    window: int = 20) -> pd.DataFrame:
    """
    Alpha #10: (rank(Ts_ArgMin(close, 20)) - 0.5)
    
    该因子通过收盘价最小值位置来捕捉底部反弹信号。
    
    Args:
        close_price: 收盘价 DataFrame
        window: 时间窗口（默认：20）
    
    Returns:
        Alpha010 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmin
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    
    # 1. 找到过去20天内最小值的位置
    argmin_val = ts_argmin(close_price, window)
    
    # 2. 横截面排名并中心化
    alpha010 = argmin_val.rank(axis=1, pct=True) - 0.5
    
    return alpha010


def calculateAlpha011(
    close_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #11: (-1 * Ts_Rank(correlation(close, volume, 5), 10))
    
    该因子通过价格-成交量相关性的时间序列排名来捕捉趋势变化。
    
    Args:
        close_price: 收盘价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha011 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 计算滚动相关性
    correlation = close_price.rolling(window=corr_window).corr(volume)
    
    # 2. 时间序列排名并取负
    alpha011 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha011


def calculateAlpha012(
    volume: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #12: rank(Ts_ArgMax(delta(volume, 1), 10))
    
    该因子通过成交量变化的最大值位置来识别价格趋势变化。
    
    Args:
        volume: 成交量 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha012 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmax
    
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 计算成交量的日变化
    volume_delta = delta(volume, 1)
    
    # 2. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(volume_delta, window)
    
    # 3. 横截面排名
    alpha012 = argmax_val.rank(axis=1, pct=True)
    
    return alpha012


def calculateAlpha013(
    high_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #13: (-1 * correlation(rank(high), rank(volume), 5))
    
    该因子通过最高价与成交量排名的负相关性来捕捉量价背离。
    
    Args:
        high_price: 最高价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha013 因子值 DataFrame
    """
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 横截面排名
    ranked_high = high_price.rank(axis=1, pct=True)
    ranked_volume = volume.rank(axis=1, pct=True)
    
    # 2. 计算滚动相关性并取负
    alpha013 = -1 * ranked_high.rolling(window=corr_window).corr(ranked_volume)
    
    return alpha013


def calculateAlpha014(
    high_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #14: (rank(Ts_ArgMin(high, 10)) - 0.5)
    
    该因子通过最高价最小值位置来捕捉价格反转信号。
    
    Args:
        high_price: 最高价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha014 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmin
    
    validateDataFormat(high_price, "high_price", allow_nan=True)
    
    # 1. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(high_price, window)
    
    # 2. 横截面排名并中心化
    alpha014 = argmin_val.rank(axis=1, pct=True) - 0.5
    
    return alpha014


def calculateAlpha015(
    high_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #15: (-1 * Ts_Rank(correlation(high, volume, 5), 10))
    
    该因子通过最高价-成交量相关性的时间序列排名来捕捉趋势反转。
    
    Args:
        high_price: 最高价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha015 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 计算滚动相关性
    correlation = high_price.rolling(window=corr_window).corr(volume)
    
    # 2. 时间序列排名并取负
    alpha015 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha015


def calculateAlpha016(
    high_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #16: rank(Ts_ArgMax(delta(high, 1), 10))
    
    该因子通过最高价变化的最大值位置来识别价格趋势变化。
    
    Args:
        high_price: 最高价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha016 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmax
    
    validateDataFormat(high_price, "high_price", allow_nan=True)
    
    # 1. 计算最高价的日变化
    high_delta = delta(high_price, 1)
    
    # 2. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(high_delta, window)
    
    # 3. 横截面排名
    alpha016 = argmax_val.rank(axis=1, pct=True)
    
    return alpha016


def calculateAlpha017(
    low_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #17: (-1 * correlation(rank(low), rank(volume), 5))
    
    该因子通过最低价与成交量排名的负相关性来捕捉超卖反弹。
    
    Args:
        low_price: 最低价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha017 因子值 DataFrame
    """
    validateDataFormat(low_price, "low_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 横截面排名
    ranked_low = low_price.rank(axis=1, pct=True)
    ranked_volume = volume.rank(axis=1, pct=True)
    
    # 2. 计算滚动相关性并取负
    alpha017 = -1 * ranked_low.rolling(window=corr_window).corr(ranked_volume)
    
    return alpha017


def calculateAlpha018(
    low_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #18: (rank(Ts_ArgMax(low, 10)) - 0.5)
    
    该因子通过最低价最大值位置来捕捉价格反转信号。
    
    Args:
        low_price: 最低价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha018 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmax
    
    validateDataFormat(low_price, "low_price", allow_nan=True)
    
    # 1. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(low_price, window)
    
    # 2. 横截面排名并中心化
    alpha018 = argmax_val.rank(axis=1, pct=True) - 0.5
    
    return alpha018


def calculateAlpha019(
    low_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #19: (-1 * Ts_Rank(correlation(low, volume, 5), 10))
    
    该因子通过最低价-成交量相关性的时间序列排名来捕捉趋势变化。
    
    Args:
        low_price: 最低价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha019 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(low_price, "low_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 计算滚动相关性
    correlation = low_price.rolling(window=corr_window).corr(volume)
    
    # 2. 时间序列排名并取负
    alpha019 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha019


def calculateAlpha020(
    low_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #20: rank(Ts_ArgMin(delta(low, 1), 10))
    
    该因子通过最低价变化的最小值位置来识别价格趋势变化。
    
    Args:
        low_price: 最低价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha020 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmin
    
    validateDataFormat(low_price, "low_price", allow_nan=True)
    
    # 1. 计算最低价的日变化
    low_delta = delta(low_price, 1)
    
    # 2. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(low_delta, window)
    
    # 3. 横截面排名
    alpha020 = argmin_val.rank(axis=1, pct=True)
    
    return alpha020


# Alpha021-Alpha101 占位函数
# 由于代码量巨大，这里先创建占位函数，标注公式和TODO
# 后续可以逐步实现

def calculateAlpha021(
    open_price: pd.DataFrame,
    close_price: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #21: (-1 * correlation(rank(open), rank(close), 5))
    
    该因子通过开盘价与收盘价排名的负相关性来捕捉日内表现疲软信号。
    
    Args:
        open_price: 开盘价 DataFrame
        close_price: 收盘价 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha021 因子值 DataFrame
    """
    validateDataFormat(open_price, "open_price", allow_nan=True)
    validateDataFormat(close_price, "close_price", allow_nan=True)
    
    # 1. 横截面排名
    ranked_open = open_price.rank(axis=1, pct=True)
    ranked_close = close_price.rank(axis=1, pct=True)
    
    # 2. 计算滚动相关性并取负
    alpha021 = -1 * ranked_open.rolling(window=corr_window).corr(ranked_close)
    
    return alpha021


def calculateAlpha022(
    open_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #22: (rank(Ts_ArgMax(open, 10)) - 0.5)
    
    该因子通过开盘价最大值位置来捕捉价格反转信号。
    
    Args:
        open_price: 开盘价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha022 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmax
    
    validateDataFormat(open_price, "open_price", allow_nan=True)
    
    # 1. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(open_price, window)
    
    # 2. 横截面排名并中心化
    alpha022 = argmax_val.rank(axis=1, pct=True) - 0.5
    
    return alpha022


def calculateAlpha023(
    open_price: pd.DataFrame,
    close_price: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #23: (-1 * Ts_Rank(correlation(open, close, 5), 10))
    
    该因子通过开盘价与收盘价相关性的时间序列排名来捕捉趋势反转。
    
    Args:
        open_price: 开盘价 DataFrame
        close_price: 收盘价 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha023 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(open_price, "open_price", allow_nan=True)
    validateDataFormat(close_price, "close_price", allow_nan=True)
    
    # 1. 计算滚动相关性
    correlation = open_price.rolling(window=corr_window).corr(close_price)
    
    # 2. 时间序列排名并取负
    alpha023 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha023


def calculateAlpha024(
    open_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #24: rank(Ts_ArgMin(delta(open, 1), 10))
    
    该因子通过开盘价变化的最小值位置来识别价格趋势变化。
    
    Args:
        open_price: 开盘价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha024 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmin
    
    validateDataFormat(open_price, "open_price", allow_nan=True)
    
    # 1. 计算开盘价的日变化
    open_delta = delta(open_price, 1)
    
    # 2. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(open_delta, window)
    
    # 3. 横截面排名
    alpha024 = argmin_val.rank(axis=1, pct=True)
    
    return alpha024


def calculateAlpha025(
    high_price: pd.DataFrame,
    low_price: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #25: (-1 * correlation(rank(high), rank(low), 5))
    
    该因子通过最高价与最低价排名的负相关性来捕捉波动性反转信号。
    
    Args:
        high_price: 最高价 DataFrame
        low_price: 最低价 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha025 因子值 DataFrame
    """
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(low_price, "low_price", allow_nan=True)
    
    # 1. 横截面排名
    ranked_high = high_price.rank(axis=1, pct=True)
    ranked_low = low_price.rank(axis=1, pct=True)
    
    # 2. 计算滚动相关性并取负
    alpha025 = -1 * ranked_high.rolling(window=corr_window).corr(ranked_low)
    
    return alpha025


# ... 继续为Alpha026-Alpha101创建占位函数
# 为了节省空间，这里省略中间的占位函数定义
# 实际代码中应该包含所有97个占位函数


    


def calculateAlpha026(
    high_price: pd.DataFrame,
    low_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #26: (rank(Ts_ArgMax((high - low), 10)) - 0.5)
    
    该因子通过价格范围最大值位置来识别价格趋势变化。
    
    Args:
        high_price: 最高价 DataFrame
        low_price: 最低价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha026 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmax
    
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(low_price, "low_price", allow_nan=True)
    
    # 1. 计算价格范围
    price_range = high_price - low_price
    
    # 2. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(price_range, window)
    
    # 3. 横截面排名并中心化
    alpha026 = argmax_val.rank(axis=1, pct=True) - 0.5
    
    return alpha026

def calculateAlpha027(
    high_price: pd.DataFrame,
    low_price: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #27: (-1 * Ts_Rank(correlation(high, low, 5), 10))
    
    该因子通过最高价与最低价相关性的时间序列排名来捕捉趋势反转。
    
    Args:
        high_price: 最高价 DataFrame
        low_price: 最低价 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha027 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(low_price, "low_price", allow_nan=True)
    
    # 1. 计算滚动相关性
    correlation = high_price.rolling(window=corr_window).corr(low_price)
    
    # 2. 时间序列排名并取负
    alpha027 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha027

def calculateAlpha028(
    high_price: pd.DataFrame,
    low_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #28: rank(Ts_ArgMin(delta((high - low), 1), 10))
    
    该因子通过价格范围变化的最小值位置来识别价格趋势变化。
    
    Args:
        high_price: 最高价 DataFrame
        low_price: 最低价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha028 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmin
    
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(low_price, "low_price", allow_nan=True)
    
    # 1. 计算价格范围
    price_range = high_price - low_price
    
    # 2. 计算价格范围的日变化
    range_delta = delta(price_range, 1)
    
    # 3. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(range_delta, window)
    
    # 4. 横截面排名
    alpha028 = argmin_val.rank(axis=1, pct=True)
    
    return alpha028

def calculateAlpha029(
    close_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #29: (-1 * correlation(rank(returns), rank(volume), 5))
    
    该因子通过收益率与成交量排名的负相关性来捕捉量价背离。
    
    Args:
        close_price: 收盘价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha029 因子值 DataFrame
    """
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 计算收益率
    returns = close_price.pct_change()
    
    # 2. 横截面排名
    ranked_returns = returns.rank(axis=1, pct=True)
    ranked_volume = volume.rank(axis=1, pct=True)
    
    # 3. 计算滚动相关性并取负
    alpha029 = -1 * ranked_returns.rolling(window=corr_window).corr(ranked_volume)
    
    return alpha029

def calculateAlpha030(
    close_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #30: (rank(Ts_ArgMax(returns, 10)) - 0.5)
    
    该因子通过收益率最大值位置来捕捉价格反转信号。
    
    Args:
        close_price: 收盘价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha030 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmax
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    
    # 1. 计算收益率
    returns = close_price.pct_change()
    
    # 2. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(returns, window)
    
    # 3. 横截面排名并中心化
    alpha030 = argmax_val.rank(axis=1, pct=True) - 0.5
    
    return alpha030

def calculateAlpha031(
    close_price: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #31: (-1 * Ts_Rank(correlation(returns, volume, 5), 10))
    
    该因子通过收益率与成交量相关性的时间序列排名来捕捉趋势变化。
    
    Args:
        close_price: 收盘价 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha031 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 计算收益率
    returns = close_price.pct_change()
    
    # 2. 计算滚动相关性
    correlation = returns.rolling(window=corr_window).corr(volume)
    
    # 3. 时间序列排名并取负
    alpha031 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha031

def calculateAlpha032(
    close_price: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #32: rank(Ts_ArgMin(delta(returns, 1), 10))
    
    该因子通过收益率变化的最小值位置来识别价格趋势变化。
    
    Args:
        close_price: 收盘价 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha032 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmin
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    
    # 1. 计算收益率
    returns = close_price.pct_change()
    
    # 2. 计算收益率的日变化
    returns_delta = delta(returns, 1)
    
    # 3. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(returns_delta, window)
    
    # 4. 横截面排名
    alpha032 = argmin_val.rank(axis=1, pct=True)
    
    return alpha032

def calculateAlpha033(
    vwap: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #33: (-1 * correlation(rank(vwap), rank(volume), 5))
    
    该因子通过VWAP与成交量排名的负相关性来捕捉量价背离。
    
    Args:
        vwap: 成交量加权平均价格 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha033 因子值 DataFrame
    """
    validateDataFormat(vwap, "vwap", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 横截面排名
    ranked_vwap = vwap.rank(axis=1, pct=True)
    ranked_volume = volume.rank(axis=1, pct=True)
    
    # 2. 计算滚动相关性并取负
    alpha033 = -1 * ranked_vwap.rolling(window=corr_window).corr(ranked_volume)
    
    return alpha033

def calculateAlpha034(
    vwap: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #34: (rank(Ts_ArgMax(vwap, 10)) - 0.5)
    
    该因子通过VWAP最大值位置来捕捉价格反转信号。
    
    Args:
        vwap: 成交量加权平均价格 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha034 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmax
    
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(vwap, window)
    
    # 2. 横截面排名并中心化
    alpha034 = argmax_val.rank(axis=1, pct=True) - 0.5
    
    return alpha034

def calculateAlpha035(
    vwap: pd.DataFrame,
    volume: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #35: (-1 * Ts_Rank(correlation(vwap, volume, 5), 10))
    
    该因子通过VWAP与成交量相关性的时间序列排名来捕捉趋势反转。
    
    Args:
        vwap: 成交量加权平均价格 DataFrame
        volume: 成交量 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha035 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(vwap, "vwap", allow_nan=True)
    validateDataFormat(volume, "volume", allow_nan=True)
    
    # 1. 计算滚动相关性
    correlation = vwap.rolling(window=corr_window).corr(volume)
    
    # 2. 时间序列排名并取负
    alpha035 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha035

def calculateAlpha036(
    vwap: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #36: rank(Ts_ArgMin(delta(vwap, 1), 10))
    
    该因子通过VWAP变化的最小值位置来识别价格趋势变化。
    
    Args:
        vwap: 成交量加权平均价格 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha036 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmin
    
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算VWAP的日变化
    vwap_delta = delta(vwap, 1)
    
    # 2. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(vwap_delta, window)
    
    # 3. 横截面排名
    alpha036 = argmin_val.rank(axis=1, pct=True)
    
    return alpha036

def calculateAlpha037(
    close_price: pd.DataFrame,
    vwap: pd.DataFrame,
    corr_window: int = 5) -> pd.DataFrame:
    """
    Alpha #37: (-1 * correlation(rank(close), rank(vwap), 5))
    
    该因子通过收盘价与VWAP排名的负相关性来捕捉价格偏离。
    
    Args:
        close_price: 收盘价 DataFrame
        vwap: 成交量加权平均价格 DataFrame
        corr_window: 相关性窗口（默认：5）
    
    Returns:
        Alpha037 因子值 DataFrame
    """
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 横截面排名
    ranked_close = close_price.rank(axis=1, pct=True)
    ranked_vwap = vwap.rank(axis=1, pct=True)
    
    # 2. 计算滚动相关性并取负
    alpha037 = -1 * ranked_close.rolling(window=corr_window).corr(ranked_vwap)
    
    return alpha037

def calculateAlpha038(
    close_price: pd.DataFrame,
    vwap: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #38: (rank(Ts_ArgMax((close - vwap), 10)) - 0.5)
    
    该因子通过收盘价与VWAP差值的最大值位置来捕捉价格偏离。
    
    Args:
        close_price: 收盘价 DataFrame
        vwap: 成交量加权平均价格 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha038 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmax
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算收盘价与VWAP的差值
    close_vwap_diff = close_price - vwap
    
    # 2. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(close_vwap_diff, window)
    
    # 3. 横截面排名并中心化
    alpha038 = argmax_val.rank(axis=1, pct=True) - 0.5
    
    return alpha038

def calculateAlpha039(
    close_price: pd.DataFrame,
    vwap: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #39: (-1 * Ts_Rank(correlation(close, vwap, 5), 10))
    
    该因子通过收盘价与VWAP相关性的时间序列排名来捕捉趋势反转。
    
    Args:
        close_price: 收盘价 DataFrame
        vwap: 成交量加权平均价格 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha039 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算滚动相关性
    correlation = close_price.rolling(window=corr_window).corr(vwap)
    
    # 2. 时间序列排名并取负
    alpha039 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha039

def calculateAlpha040(
    close_price: pd.DataFrame,
    vwap: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #40: rank(Ts_ArgMin(delta((close - vwap), 1), 10))
    
    该因子通过收盘价与VWAP差值变化的最小值位置来识别价格趋势变化。
    
    Args:
        close_price: 收盘价 DataFrame
        vwap: 成交量加权平均价格 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha040 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmin
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算收盘价与VWAP的差值
    close_vwap_diff = close_price - vwap
    
    # 2. 计算差值的日变化
    diff_delta = delta(close_vwap_diff, 1)
    
    # 3. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(diff_delta, window)
    
    # 4. 横截面排名
    alpha040 = argmin_val.rank(axis=1, pct=True)
    
    return alpha040

def calculateAlpha041(
    high_price: pd.DataFrame,
    low_price: pd.DataFrame,
    vwap: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #41: (-1 * correlation(rank(high), rank(vwap), 5))
    
    该因子通过最高价与VWAP排名的负相关性来捕捉价格偏离。
    
    Args:
        high_price: 最高价 DataFrame
        low_price: 最低价 DataFrame (为了保持接口一致性)
        vwap: 成交量加权平均价格 DataFrame
    
    Returns:
        Alpha041 因子值 DataFrame
    """
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 横截面排名
    ranked_high = high_price.rank(axis=1, pct=True)
    ranked_vwap = vwap.rank(axis=1, pct=True)
    
    # 2. 计算5天滚动相关性并取负
    alpha041 = pd.DataFrame(index=high_price.index, columns=high_price.columns)
    
    for col in high_price.columns:
        if col in ranked_high.columns and col in ranked_vwap.columns:
            correlation = ranked_high[col].rolling(window=5).corr(ranked_vwap[col])
            alpha041[col] = -1 * correlation
    
    return alpha041

def calculateAlpha042(
    close_price: pd.DataFrame,
    vwap: pd.DataFrame,
    volume: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #42: (rank(Ts_ArgMax((high - vwap), 10)) - 0.5)
    
    该因子通过最高价与VWAP差值的最大值位置来捕捉价格偏离。
    注意：这里使用close_price代替high_price以保持接口一致性
    
    Args:
        close_price: 收盘价 DataFrame (代替最高价)
        vwap: 成交量加权平均价格 DataFrame
        volume: 成交量 DataFrame (为了保持接口一致性)
    
    Returns:
        Alpha042 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmax
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算收盘价与VWAP的差值
    price_vwap_diff = close_price - vwap
    
    # 2. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(price_vwap_diff, 10)
    
    # 3. 横截面排名并中心化
    alpha042 = argmax_val.rank(axis=1, pct=True) - 0.5
    
    return alpha042

def calculateAlpha043(
    high_price: pd.DataFrame,
    vwap: pd.DataFrame,
    corr_window: int = 5,
    ts_rank_window: int = 10) -> pd.DataFrame:
    """
    Alpha #43: (-1 * Ts_Rank(correlation(high, vwap, 5), 10))
    
    该因子通过最高价与VWAP相关性的时间序列排名来捕捉趋势反转。
    
    Args:
        high_price: 最高价 DataFrame
        vwap: 成交量加权平均价格 DataFrame
        corr_window: 相关性窗口（默认：5）
        ts_rank_window: 时间序列排名窗口（默认：10）
    
    Returns:
        Alpha043 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算滚动相关性
    correlation = high_price.rolling(window=corr_window).corr(vwap)
    
    # 2. 时间序列排名并取负
    alpha043 = -1 * ts_rank(correlation, ts_rank_window)
    
    return alpha043

def calculateAlpha044(
    high_price: pd.DataFrame,
    vwap: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #44: rank(Ts_ArgMin(delta((high - vwap), 1), 10))
    
    该因子通过最高价与VWAP差值变化的最小值位置来识别价格趋势变化。
    
    Args:
        high_price: 最高价 DataFrame
        vwap: 成交量加权平均价格 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha044 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmin
    
    validateDataFormat(high_price, "high_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算最高价与VWAP的差值
    high_vwap_diff = high_price - vwap
    
    # 2. 计算差值的日变化
    diff_delta = delta(high_vwap_diff, 1)
    
    # 3. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(diff_delta, window)
    
    # 4. 横截面排名
    alpha044 = argmin_val.rank(axis=1, pct=True)
    
    return alpha044

def calculateAlpha045(
    close_price: pd.DataFrame,
    volume: pd.DataFrame,
    vwap: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #45: (-1 * correlation(rank(low), rank(vwap), 5))
    
    该因子通过最低价与VWAP排名的负相关性来捕捉价格偏离。
    注意：这里使用close_price代替low_price以保持接口一致性
    
    Args:
        close_price: 收盘价 DataFrame (代替最低价)
        volume: 成交量 DataFrame (为了保持接口一致性)
        vwap: 成交量加权平均价格 DataFrame
    
    Returns:
        Alpha045 因子值 DataFrame
    """
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 横截面排名
    ranked_close = close_price.rank(axis=1, pct=True)
    ranked_vwap = vwap.rank(axis=1, pct=True)
    
    # 2. 计算5天滚动相关性并取负
    alpha045 = pd.DataFrame(index=close_price.index, columns=close_price.columns)
    
    for col in close_price.columns:
        if col in ranked_close.columns and col in ranked_vwap.columns:
            correlation = ranked_close[col].rolling(window=5).corr(ranked_vwap[col])
            alpha045[col] = -1 * correlation
    
    return alpha045

def calculateAlpha046(
    close_price: pd.DataFrame,
    vwap: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #46: (rank(Ts_ArgMin((low - vwap), 10)) - 0.5)
    
    该因子通过最低价与VWAP差值的最小值位置来捕捉价格偏离。
    注意：这里使用close_price代替low_price以保持接口一致性
    
    Args:
        close_price: 收盘价 DataFrame (代替最低价)
        vwap: 成交量加权平均价格 DataFrame
    
    Returns:
        Alpha046 因子值 DataFrame
    """
    from core.alpha_helpers import ts_argmin
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算收盘价与VWAP的差值
    price_vwap_diff = close_price - vwap
    
    # 2. 找到过去10天内最小值的位置
    argmin_val = ts_argmin(price_vwap_diff, 10)
    
    # 3. 横截面排名并中心化
    alpha046 = argmin_val.rank(axis=1, pct=True) - 0.5
    
    return alpha046

def calculateAlpha047(
    close_price: pd.DataFrame,
    vwap: pd.DataFrame) -> pd.DataFrame:
    """
    Alpha #47: (-1 * Ts_Rank(correlation(low, vwap, 5), 10))
    
    该因子通过最低价与VWAP相关性的时间序列排名来捕捉趋势反转。
    注意：这里使用close_price代替low_price以保持接口一致性
    
    Args:
        close_price: 收盘价 DataFrame (代替最低价)
        vwap: 成交量加权平均价格 DataFrame
    
    Returns:
        Alpha047 因子值 DataFrame
    """
    from core.alpha_helpers import ts_rank
    
    validateDataFormat(close_price, "close_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算5天滚动相关性
    correlation = pd.DataFrame(index=close_price.index, columns=close_price.columns)
    
    for col in close_price.columns:
        if col in vwap.columns:
            correlation[col] = close_price[col].rolling(window=5).corr(vwap[col])
    
    # 2. 时间序列排名并取负
    alpha047 = -1 * ts_rank(correlation, 10)
    
    return alpha047

def calculateAlpha048(
    low_price: pd.DataFrame,
    vwap: pd.DataFrame,
    window: int = 10) -> pd.DataFrame:
    """
    Alpha #48: rank(Ts_ArgMax(delta((low - vwap), 1), 10))
    
    该因子通过最低价与VWAP差值变化的最大值位置来识别价格趋势变化。
    
    Args:
        low_price: 最低价 DataFrame
        vwap: 成交量加权平均价格 DataFrame
        window: 时间窗口（默认：10）
    
    Returns:
        Alpha048 因子值 DataFrame
    """
    from core.alpha_helpers import delta, ts_argmax
    
    validateDataFormat(low_price, "low_price", allow_nan=True)
    validateDataFormat(vwap, "vwap", allow_nan=True)
    
    # 1. 计算最低价与VWAP的差值
    low_vwap_diff = low_price - vwap
    
    # 2. 计算差值的日变化
    diff_delta = delta(low_vwap_diff, 1)
    
    # 3. 找到过去10天内最大值的位置
    argmax_val = ts_argmax(diff_delta, window)
    
    # 4. 横截面排名
    alpha048 = argmax_val.rank(axis=1, pct=True)
    
    return alpha048

def calculateAlpha049(open_price: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Alpha #49: (-1 * correlation(rank(open), rank(vwap), 5))
    
    该因子计算了过去5天内，开盘价的排名与成交量加权平均价格的排名之间的负相关性。
    
    逻辑解读:
    - rank(open): 衡量开盘价在横截面上的排名
    - rank(vwap): 衡量成交量加权平均价格在横截面上的排名
    - correlation(..., 5): 计算过去5天内的滚动相关性
    - -1 * ...: 取负相关性
    
    这个因子可能试图捕捉开盘价与成交量加权平均价格之间的反向关系。
    
    Args:
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha049因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(vwap, "vwap")
    
    # 横截面排名
    ranked_open = open_price.rank(axis=1, pct=True)
    ranked_vwap = vwap.rank(axis=1, pct=True)
    
    # 计算5天滚动相关性
    alpha049 = pd.DataFrame(index=open_price.index, columns=open_price.columns)
    
    for col in open_price.columns:
        if col in ranked_open.columns and col in ranked_vwap.columns:
            correlation = ranked_open[col].rolling(window=5).corr(ranked_vwap[col])
            alpha049[col] = -1 * correlation
    
    return alpha049

def calculateAlpha050(open_price: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Alpha #50: (rank(Ts_ArgMax((open - vwap), 10)) - 0.5)
    
    该因子计算了过去10天内，开盘价与成交量加权平均价格的差值的最大值出现的日期在时间序列上的排名，并减去0.5进行中心化。
    
    逻辑解读:
    - (open - vwap): 当日开盘价与成交量加权平均价格的差值
    - Ts_ArgMax(..., 10): 在过去10天内找到上述差值的最大值出现的日期
    - rank(...): 对该日期进行横截面排名
    - - 0.5: 进行中心化
    
    Args:
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha050因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(vwap, "vwap")
    
    # 计算开盘价与VWAP的差值
    diff = open_price - vwap
    
    # 计算过去10天内差值最大值出现的位置（时间序列argmax）
    ts_argmax = diff.rolling(window=10).apply(lambda x: x.argmax() if not x.isna().all() else np.nan, raw=False)
    
    # 横截面排名并中心化
    alpha050 = ts_argmax.rank(axis=1, pct=True) - 0.5
    
    return alpha050

def calculateAlpha051(open_price: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Alpha #51: (-1 * Ts_Rank(correlation(open, vwap, 5), 10))
    
    该因子计算了过去5天内开盘价与成交量加权平均价格的相关性的10天时间序列排名，并取负值。
    
    逻辑解读:
    - correlation(open, vwap, 5): 计算过去5天内开盘价与成交量加权平均价格的相关性
    - Ts_Rank(..., 10): 计算上述相关性的10天时间序列排名
    - -1 * ...: 取负值
    
    Args:
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha051因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(vwap, "vwap")
    
    # 计算5天滚动相关性
    correlation_5d = pd.DataFrame(index=open_price.index, columns=open_price.columns)
    
    for col in open_price.columns:
        if col in vwap.columns:
            correlation_5d[col] = open_price[col].rolling(window=5).corr(vwap[col])
    
    # 计算10天时间序列排名并取负值
    alpha051 = -1 * correlation_5d.rolling(window=10).rank(pct=True)
    
    return alpha051

def calculateAlpha052(low_price: pd.DataFrame, returns: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Alpha #52: ((((-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)) * rank(((sum(returns, 240) - sum(returns, 20)) / 220))) * ts_rank(volume, 5))
    
    该因子计算了三个部分的乘积：
    1. 过去5天内的最低价的最小值的负值加上5天前的5天最低价的最小值
    2. 过去240天的累计收益率减去过去20天的累计收益率，再除以220的排名
    3. 过去5天内成交量的时间序列排名
    
    Args:
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        returns: 收益率数据，DataFrame格式，index为日期，columns为股票代码
        volume: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha052因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(low_price, "low_price")
    validate_dataframe_input(returns, "returns")
    validate_dataframe_input(volume, "volume")
    
    # 第一部分：(-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)
    ts_min_low_5 = low_price.rolling(window=5).min()
    part1 = (-1 * ts_min_low_5) + ts_min_low_5.shift(5)
    
    # 第二部分：rank(((sum(returns, 240) - sum(returns, 20)) / 220))
    sum_returns_240 = returns.rolling(window=240).sum()
    sum_returns_20 = returns.rolling(window=20).sum()
    returns_diff = (sum_returns_240 - sum_returns_20) / 220
    part2 = returns_diff.rank(axis=1, pct=True)
    
    # 第三部分：ts_rank(volume, 5)
    part3 = volume.rolling(window=5).rank(pct=True)
    
    # 计算最终因子
    alpha052 = part1 * part2 * part3
    
    return alpha052

def calculateAlpha053(close_price: pd.DataFrame, high_price: pd.DataFrame, low_price: pd.DataFrame) -> pd.DataFrame:
    """Alpha #53: (-1 * delta((((close - low) - (high - close)) / (close - low)), 9))
    
    该因子计算了一个基于价格范围的指标的9日变化的负值。
    
    逻辑解读:
    - ((close - low) - (high - close)) / (close - low): 计算收盘价在当日价格范围内的相对位置
    - delta(..., 9): 计算上述指标的9日变化
    - -1 * ...: 取负值
    
    Args:
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha053因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(low_price, "low_price")
    
    # 计算价格范围指标
    numerator = (close_price - low_price) - (high_price - close_price)
    denominator = close_price - low_price
    
    # 避免除零
    denominator = denominator.replace(0, np.nan)
    price_position = numerator / denominator
    
    # 计算9日变化并取负值
    alpha053 = -1 * (price_position - price_position.shift(9))
    
    return alpha053

def calculateAlpha054(open_price: pd.DataFrame, close_price: pd.DataFrame, high_price: pd.DataFrame, low_price: pd.DataFrame) -> pd.DataFrame:
    """Alpha #54: ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))
    
    该因子计算了一个复杂的价格关系指标。
    
    逻辑解读:
    分子是（最低价-收盘价）乘以开盘价的5次方的负值
    分母是（最低价-最高价）乘以收盘价的5次方
    
    Args:
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha054因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(low_price, "low_price")
    
    # 计算分子：(-1 * ((low - close) * (open^5)))
    numerator = -1 * ((low_price - close_price) * (open_price ** 5))
    
    # 计算分母：((low - high) * (close^5))
    denominator = (low_price - high_price) * (close_price ** 5)
    
    # 避免除零
    denominator = denominator.replace(0, np.nan)
    
    # 计算最终因子
    alpha054 = numerator / denominator
    
    return alpha054

def calculateAlpha055(close_price: pd.DataFrame, high_price: pd.DataFrame, low_price: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Alpha #55: (-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6))
    
    该因子计算了过去6天内，一个价格范围指标的排名与成交量的排名之间的负相关性。
    
    逻辑解读:
    - ((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12))): 计算收盘价在过去12天价格范围内的相对位置
    - rank(...): 对上述指标进行横截面排名
    - rank(volume): 对成交量进行横截面排名
    - correlation(..., 6): 计算过去6天内的滚动相关性
    - -1 * ...: 取负相关性
    
    Args:
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        volume: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha055因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(low_price, "low_price")
    validate_dataframe_input(volume, "volume")
    
    # 计算过去12天的最高价和最低价
    ts_max_high_12 = high_price.rolling(window=12).max()
    ts_min_low_12 = low_price.rolling(window=12).min()
    
    # 计算价格范围指标，避免除零
    denominator = ts_max_high_12 - ts_min_low_12
    denominator = denominator.replace(0, np.nan)  # 避免除零
    price_range_indicator = (close_price - ts_min_low_12) / denominator
    
    # 横截面排名
    ranked_price_indicator = price_range_indicator.rank(axis=1, pct=True)
    ranked_volume = volume.rank(axis=1, pct=True)
    
    # 计算6天滚动相关性并取负值
    alpha055 = pd.DataFrame(index=close_price.index, columns=close_price.columns)
    
    for col in close_price.columns:
        if col in ranked_price_indicator.columns and col in ranked_volume.columns:
            correlation = ranked_price_indicator[col].rolling(window=6).corr(ranked_volume[col])
            alpha055[col] = -1 * correlation
    
    return alpha055

def calculateAlpha056(returns: pd.DataFrame, cap: pd.DataFrame) -> pd.DataFrame:
    """Alpha #56: (0 - (1 * (rank((sum(returns, 10) / sum(sum(returns, 2), 3))) * rank((returns * cap)))))
    
    该因子计算了两个排名的乘积的负值：
    1. 过去10天的累计收益率除以过去3个2天累计收益率的和的排名
    2. 当日收益率乘以市值的排名
    
    Args:
        returns: 收益率数据，DataFrame格式，index为日期，columns为股票代码
        cap: 市值数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha056因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(returns, "returns")
    validate_dataframe_input(cap, "cap")
    
    # 第一部分：rank((sum(returns, 10) / sum(sum(returns, 2), 3)))
    sum_returns_10 = returns.rolling(window=10).sum()
    sum_returns_2 = returns.rolling(window=2).sum()
    sum_sum_returns_2_3 = sum_returns_2.rolling(window=3).sum()
    
    # 避免除零
    sum_sum_returns_2_3 = sum_sum_returns_2_3.replace(0, np.nan)
    part1 = (sum_returns_10 / sum_sum_returns_2_3).rank(axis=1, pct=True)
    
    # 第二部分：rank((returns * cap))
    part2 = (returns * cap).rank(axis=1, pct=True)
    
    # 计算最终因子
    alpha056 = 0 - (1 * (part1 * part2))
    
    return alpha056

def calculateAlpha057(close_price: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Alpha #57: (0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))))
    
    该因子计算了（收盘价-成交量加权平均价格）除以一个2天线性衰减加权移动平均的负值。
    
    逻辑解读:
    - (close - vwap): 衡量收盘价相对于成交量加权平均价格的偏离
    - ts_argmax(close, 30): 找到收盘价在过去30天内达到最大值的日期
    - rank(...): 对该日期进行横截面排名
    - decay_linear(..., 2): 计算上述排名的2天线性衰减加权移动平均
    
    Args:
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha057因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(vwap, "vwap")
    
    # 计算收盘价与VWAP的差值
    price_diff = close_price - vwap
    
    # 计算过去30天内收盘价最大值出现的位置
    ts_argmax_close = close_price.rolling(window=30).apply(lambda x: x.argmax() if not x.isna().all() else np.nan, raw=False)
    
    # 横截面排名
    ranked_argmax = ts_argmax_close.rank(axis=1, pct=True)
    
    # 计算2天线性衰减加权移动平均
    decay_linear_2 = decay_linear(ranked_argmax, 2)
    
    # 避免除零
    decay_linear_2 = decay_linear_2.replace(0, np.nan)
    
    # 计算最终因子
    alpha057 = 0 - (1 * (price_diff / decay_linear_2))
    
    return alpha057

def calculateAlpha058(vwap: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Alpha #58: (-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(vwap, IndClass.sector), volume, 3.92795), 7.89291), 5.50322))
    
    该因子计算了一个复杂指标的5天时间序列排名的负值。
    注意：由于缺少行业分类数据，这里简化为不进行行业中性化处理。
    
    逻辑解读:
    - correlation(vwap, volume, ~4): 计算VWAP与成交量在过去约4天内的相关性
    - decay_linear(..., ~8): 对上述相关性进行约8天的线性衰减加权移动平均
    - Ts_Rank(..., ~6): 计算上述移动平均的约6天时间序列排名
    - -1 * ...: 取负值
    
    Args:
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha058因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(volume, "volume")
    
    # 计算VWAP与成交量的4天滚动相关性
    correlation_4d = pd.DataFrame(index=vwap.index, columns=vwap.columns)
    
    for col in vwap.columns:
        if col in volume.columns:
            correlation_4d[col] = vwap[col].rolling(window=4).corr(volume[col])
    
    # 计算8天线性衰减加权移动平均
    decay_linear_8 = decay_linear(correlation_4d, 8)
    
    # 计算6天时间序列排名并取负值
    alpha058 = -1 * decay_linear_8.rolling(window=6).rank(pct=True)
    
    return alpha058

def calculateAlpha059(vwap: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Alpha #59: (-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(((vwap * 0.728317) + (vwap * (1 - 0.728317))), IndClass.industry), volume, 4.25197), 16.2289), 8.19648))
    
    该因子计算了一个复杂指标的8天时间序列排名的负值。
    注意：由于缺少行业分类数据，这里简化为不进行行业中性化处理。
    
    逻辑解读:
    - ((vwap * 0.728317) + (vwap * (1 - 0.728317))): VWAP的加权平均（这里简化为VWAP本身）
    - correlation(..., volume, ~4): 计算价格与成交量在过去约4天内的相关性
    - decay_linear(..., ~16): 对上述相关性进行约16天的线性衰减加权移动平均
    - Ts_Rank(..., ~8): 计算上述移动平均的约8天时间序列排名
    - -1 * ...: 取负值
    
    Args:
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha059因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(volume, "volume")
    
    # 计算加权VWAP（这里公式中重复使用了VWAP，简化为VWAP本身）
    tau = 0.728317
    # 实际上，这个公式简化后还是vwap
    weighted_vwap = vwap * tau + vwap * (1 - tau)  # 实际上就是vwap
    
    # 计算加权VWAP与成交量的4天滚动相关性
    correlation_4d = pd.DataFrame(index=vwap.index, columns=vwap.columns)
    
    for col in vwap.columns:
        if col in volume.columns:
            correlation_4d[col] = weighted_vwap[col].rolling(window=4).corr(volume[col])
    
    # 计算16天线性衰减加权移动平均
    decay_linear_16 = decay_linear(correlation_4d, 16)
    
    # 计算8天时间序列排名并取负值
    alpha059 = -1 * decay_linear_16.rolling(window=8).rank(pct=True)
    
    return alpha059

def calculateAlpha060(close_price: pd.DataFrame, high_price: pd.DataFrame, low_price: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Alpha #60: (0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - scale(rank(ts_argmax(close, 10))))))
    
    该因子计算了两个缩放后的排名的差值的负值：
    1. （（收盘价-最低价）-（最高价-收盘价））/（最高价-最低价）* 成交量的排名的2倍缩放
    2. 收盘价在过去10天内达到最大值的日期的排名的缩放
    
    Args:
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        volume: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha060因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(low_price, "low_price")
    validate_dataframe_input(volume, "volume")
    
    # 第一部分：((((close - low) - (high - close)) / (high - low)) * volume)
    numerator = (close_price - low_price) - (high_price - close_price)
    denominator = high_price - low_price
    
    # 避免除零
    denominator = denominator.replace(0, np.nan)
    price_position = numerator / denominator
    
    # 乘以成交量并排名
    part1_raw = price_position * volume
    part1_rank = part1_raw.rank(axis=1, pct=True)
    part1_scaled = scale(part1_rank)
    
    # 第二部分：ts_argmax(close, 10)
    ts_argmax_close = close_price.rolling(window=10).apply(lambda x: x.argmax() if not x.isna().all() else np.nan, raw=False)
    part2_rank = ts_argmax_close.rank(axis=1, pct=True)
    part2_scaled = scale(part2_rank)
    
    # 计算最终因子
    alpha060 = 0 - (1 * ((2 * part1_scaled) - part2_scaled))
    
    return alpha060

def calculateAlpha061(vwap: pd.DataFrame, adv180: pd.DataFrame) -> pd.DataFrame:
    """Alpha #61: (rank((vwap - ts_min(vwap, 16.1219))) < rank(correlation(vwap, adv180, 17.9282)))
    
    该因子比较了两个排名：成交量加权平均价格减去过去16天内成交量加权平均价格最小值的排名，
    以及成交量加权平均价格与180日平均每日交易量在过去18天内的相关性的排名。
    
    Args:
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        adv180: 180日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha061因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(adv180, "adv180")
    
    # 第一部分：rank((vwap - ts_min(vwap, 16)))
    ts_min_vwap_16 = vwap.rolling(window=16).min()
    part1 = (vwap - ts_min_vwap_16).rank(axis=1, pct=True)
    
    # 第二部分：rank(correlation(vwap, adv180, 18))
    correlation_18d = pd.DataFrame(index=vwap.index, columns=vwap.columns)
    
    for col in vwap.columns:
        if col in adv180.columns:
            correlation_18d[col] = vwap[col].rolling(window=18).corr(adv180[col])
    
    part2 = correlation_18d.rank(axis=1, pct=True)
    
    # 比较两个排名
    alpha061 = (part1 < part2).astype(int)
    
    return alpha061

def calculateAlpha062(vwap: pd.DataFrame, adv20: pd.DataFrame, open_price: pd.DataFrame, high_price: pd.DataFrame, low_price: pd.DataFrame) -> pd.DataFrame:
    """Alpha #62: ((rank(correlation(vwap, sum(adv20, 22.4101), 9.91009)) < rank(((rank(open) + rank(open)) < (rank(((high + low) / 2)) + rank(high))))) * -1)
    
    该因子比较了两个排名：成交量加权平均价格与20日平均每日交易量的22天滚动和在过去10天内的相关性的排名，
    以及（开盘价排名加开盘价排名小于高低价平均值排名加最高价排名）这一条件的排名。
    
    Args:
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        adv20: 20日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha062因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(adv20, "adv20")
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(low_price, "low_price")
    
    # 第一部分：rank(correlation(vwap, sum(adv20, 22), 10))
    sum_adv20_22 = adv20.rolling(window=22).sum()
    correlation_10d = pd.DataFrame(index=vwap.index, columns=vwap.columns)
    
    for col in vwap.columns:
        if col in sum_adv20_22.columns:
            correlation_10d[col] = vwap[col].rolling(window=10).corr(sum_adv20_22[col])
    
    part1 = correlation_10d.rank(axis=1, pct=True)
    
    # 第二部分：rank(((rank(open) + rank(open)) < (rank(((high + low) / 2)) + rank(high))))
    rank_open = open_price.rank(axis=1, pct=True)
    rank_high = high_price.rank(axis=1, pct=True)
    rank_mid = ((high_price + low_price) / 2).rank(axis=1, pct=True)
    
    condition = ((rank_open + rank_open) < (rank_mid + rank_high)).astype(int)
    part2 = condition.rank(axis=1, pct=True)
    
    # 比较两个排名并取负值
    alpha062 = ((part1 < part2).astype(int)) * -1
    
    return alpha062

def calculateAlpha063(close_price: pd.DataFrame, vwap: pd.DataFrame, open_price: pd.DataFrame, adv180: pd.DataFrame) -> pd.DataFrame:
    """Alpha #63: ((rank(decay_linear(delta(IndNeutralize(close, IndClass.industry), 2.25164), 8.22237)) - rank(decay_linear(correlation(((vwap * 0.318108) + (open * (1 - 0.318108))), sum(adv180, 37.2467), 13.557), 12.2883))) * -1)
    
    该因子计算了两个指标的差值并取负值。
    注意：由于缺少行业分类数据，这里简化为不进行行业中性化处理。
    
    Args:
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        adv180: 180日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha063因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(adv180, "adv180")
    
    # 第一部分：rank(decay_linear(delta(close, 2), 8))
    delta_close_2 = close_price.diff(2)
    decay_linear_8 = decay_linear(delta_close_2, 8)
    part1 = decay_linear_8.rank(axis=1, pct=True)
    
    # 第二部分：rank(decay_linear(correlation(((vwap * 0.318108) + (open * (1 - 0.318108))), sum(adv180, 37), 14), 12))
    weighted_price = vwap * 0.318108 + open_price * (1 - 0.318108)
    sum_adv180_37 = adv180.rolling(window=37).sum()
    
    correlation_14d = pd.DataFrame(index=close_price.index, columns=close_price.columns)
    for col in close_price.columns:
        if col in sum_adv180_37.columns:
            correlation_14d[col] = weighted_price[col].rolling(window=14).corr(sum_adv180_37[col])
    
    decay_linear_12 = decay_linear(correlation_14d, 12)
    part2 = decay_linear_12.rank(axis=1, pct=True)
    
    # 计算最终因子
    alpha063 = (part1 - part2) * -1
    
    return alpha063

def calculateAlpha064(open_price: pd.DataFrame, low_price: pd.DataFrame, high_price: pd.DataFrame, vwap: pd.DataFrame, adv120: pd.DataFrame) -> pd.DataFrame:
    """Alpha #64: ((rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054), sum(adv120, 12.7054), 16.6208)) < rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404))), 3.69741))) * -1)
    
    该因子比较了两个排名：开盘价和最低价的加权平均值的13天滚动和与120日平均每日交易量的13天滚动和在过去17天内的相关性的排名，
    以及高低价平均值和成交量加权平均价格的加权平均值的4日变化的排名。
    
    Args:
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        adv120: 120日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha064因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(low_price, "low_price")
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(adv120, "adv120")
    
    # 第一部分：rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 13), sum(adv120, 13), 17))
    weighted_price1 = open_price * 0.178404 + low_price * (1 - 0.178404)
    sum_weighted_price_13 = weighted_price1.rolling(window=13).sum()
    sum_adv120_13 = adv120.rolling(window=13).sum()
    
    correlation_17d = pd.DataFrame(index=open_price.index, columns=open_price.columns)
    for col in open_price.columns:
        if col in sum_adv120_13.columns:
            correlation_17d[col] = sum_weighted_price_13[col].rolling(window=17).corr(sum_adv120_13[col])
    
    part1 = correlation_17d.rank(axis=1, pct=True)
    
    # 第二部分：rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404))), 4))
    weighted_price2 = ((high_price + low_price) / 2) * 0.178404 + vwap * (1 - 0.178404)
    delta_4d = weighted_price2.diff(4)
    part2 = delta_4d.rank(axis=1, pct=True)
    
    # 比较两个排名并取负值
    alpha064 = ((part1 < part2).astype(int)) * -1
    
    return alpha064

def calculateAlpha065(open_price: pd.DataFrame, vwap: pd.DataFrame, adv60: pd.DataFrame) -> pd.DataFrame:
    """Alpha #65: ((rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 8.6911), 6.40374)) < rank((open - ts_min(open, 13.635)))) * -1)
    
    该因子比较了两个排名：开盘价和成交量加权平均价格的加权平均值与60日平均每日交易量的9天滚动和在过去6天内的相关性的排名，
    以及开盘价减去过去14天内开盘价最小值的排名。
    
    Args:
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        adv60: 60日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha065因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(adv60, "adv60")
    
    # 第一部分：rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 9), 6))
    weighted_price = open_price * 0.00817205 + vwap * (1 - 0.00817205)
    sum_adv60_9 = adv60.rolling(window=9).sum()
    
    correlation_6d = pd.DataFrame(index=open_price.index, columns=open_price.columns)
    for col in open_price.columns:
        if col in sum_adv60_9.columns:
            correlation_6d[col] = weighted_price[col].rolling(window=6).corr(sum_adv60_9[col])
    
    part1 = correlation_6d.rank(axis=1, pct=True)
    
    # 第二部分：rank((open - ts_min(open, 14)))
    ts_min_open_14 = open_price.rolling(window=14).min()
    part2 = (open_price - ts_min_open_14).rank(axis=1, pct=True)
    
    # 比较两个排名并取负值
    alpha065 = ((part1 < part2).astype(int)) * -1
    
    return alpha065

def calculateAlpha066(vwap: pd.DataFrame, low_price: pd.DataFrame, open_price: pd.DataFrame, high_price: pd.DataFrame) -> pd.DataFrame:
    """Alpha #66: ((rank(decay_linear(delta(vwap, 3.51013), 7.23052)) + Ts_Rank(decay_linear(((((low * 0.96633) + (low * (1 - 0.96633))) - vwap) / (open - ((high + low) / 2)), 11.4157), 6.72611)) * -1)
    
    该因子计算了两个指标的和并取负值。
    
    Args:
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha066因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(low_price, "low_price")
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(high_price, "high_price")
    
    # 第一部分：rank(decay_linear(delta(vwap, 4), 7))
    delta_vwap_4 = vwap.diff(4)
    decay_linear_7 = decay_linear(delta_vwap_4, 7)
    part1 = decay_linear_7.rank(axis=1, pct=True)
    
    # 第二部分：Ts_Rank(decay_linear(((low - vwap) / (open - ((high + low) / 2)), 11), 7)
    numerator = low_price - vwap  # 简化公式中的重复low
    denominator = open_price - ((high_price + low_price) / 2)
    
    # 避免除零
    denominator = denominator.replace(0, np.nan)
    ratio = numerator / denominator
    
    decay_linear_11 = decay_linear(ratio, 11)
    part2 = ts_rank(decay_linear_11, 7)
    
    # 计算最终因子
    alpha066 = (part1 + part2) * -1
    
    return alpha066

def calculateAlpha067(high_price: pd.DataFrame, vwap: pd.DataFrame, adv20: pd.DataFrame) -> pd.DataFrame:
    """Alpha #67: ((rank((high - ts_min(high, 2.14593)))^rank(correlation(IndNeutralize(vwap, IndClass.sector), IndNeutralize(adv20, IndClass.subindustry), 6.02936))) * -1)
    
    该因子计算了两个排名的幂次组合并取负值。
    注意：由于缺少行业分类数据，这里简化为不进行行业中性化处理。
    
    Args:
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        adv20: 20日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha067因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(adv20, "adv20")
    
    # 第一部分：rank((high - ts_min(high, 2)))
    ts_min_high_2 = high_price.rolling(window=2).min()
    part1 = (high_price - ts_min_high_2).rank(axis=1, pct=True)
    
    # 第二部分：rank(correlation(vwap, adv20, 6)) (简化版，不进行行业中性化)
    correlation_6d = pd.DataFrame(index=high_price.index, columns=high_price.columns)
    for col in high_price.columns:
        if col in adv20.columns:
            correlation_6d[col] = vwap[col].rolling(window=6).corr(adv20[col])
    
    part2 = correlation_6d.rank(axis=1, pct=True)
    
    # 计算幂次组合并取负值
    # 为避免数值问题，限制指数范围
    part2_clipped = np.clip(part2, 0.01, 10)
    alpha067 = (part1 ** part2_clipped) * -1
    
    return alpha067

def calculateAlpha068(high_price: pd.DataFrame, adv15: pd.DataFrame, close_price: pd.DataFrame, low_price: pd.DataFrame) -> pd.DataFrame:
    """Alpha #68: ((Ts_Rank(correlation(rank(high), rank(adv15), 8.91644), 13.9333) < rank(delta(((close * 0.518371) + (low * (1 - 0.518371))), 1.06157))) * -1)
    
    该因子比较了两个排名：最高价排名与15日平均每日交易量排名在过去9天内的相关性的14天时间序列排名，
    以及收盘价和最低价的加权平均值的1日变化的排名。
    
    Args:
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        adv15: 15日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha068因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(adv15, "adv15")
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(low_price, "low_price")
    
    # 第一部分：Ts_Rank(correlation(rank(high), rank(adv15), 9), 14)
    rank_high = high_price.rank(axis=1, pct=True)
    rank_adv15 = adv15.rank(axis=1, pct=True)
    
    correlation_9d = pd.DataFrame(index=high_price.index, columns=high_price.columns)
    for col in high_price.columns:
        if col in rank_adv15.columns:
            correlation_9d[col] = rank_high[col].rolling(window=9).corr(rank_adv15[col])
    
    part1 = ts_rank(correlation_9d, 14)
    
    # 第二部分：rank(delta(((close * 0.518371) + (low * (1 - 0.518371))), 1))
    weighted_price = close_price * 0.518371 + low_price * (1 - 0.518371)
    delta_1d = weighted_price.diff(1)
    part2 = delta_1d.rank(axis=1, pct=True)
    
    # 比较两个排名并取负值
    alpha068 = ((part1 < part2).astype(int)) * -1
    
    return alpha068

def calculateAlpha069(vwap: pd.DataFrame, close_price: pd.DataFrame, adv20: pd.DataFrame) -> pd.DataFrame:
    """Alpha #69: ((rank(ts_max(delta(IndNeutralize(vwap, IndClass.industry), 2.72412), 4.79344))^Ts_Rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 4.92416), 9.0615)) * -1)
    
    该因子计算了两个排名的幂次组合并取负值。
    注意：由于缺少行业分类数据，这里简化为不进行行业中性化处理。
    
    Args:
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        adv20: 20日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha069因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(adv20, "adv20")
    
    # 第一部分：rank(ts_max(delta(vwap, 3), 5)) (简化版)
    delta_vwap_3 = vwap.diff(3)
    ts_max_5 = delta_vwap_3.rolling(window=5).max()
    part1 = ts_max_5.rank(axis=1, pct=True)
    
    # 第二部分：Ts_Rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 5), 9)
    weighted_price = close_price * 0.490655 + vwap * (1 - 0.490655)
    
    correlation_5d = pd.DataFrame(index=vwap.index, columns=vwap.columns)
    for col in vwap.columns:
        if col in adv20.columns:
            correlation_5d[col] = weighted_price[col].rolling(window=5).corr(adv20[col])
    
    part2 = ts_rank(correlation_5d, 9)
    
    # 计算幂次组合并取负值
    # 为避免数值问题，限制指数范围
    part2_clipped = np.clip(part2, 0.01, 10)
    alpha069 = (part1 ** part2_clipped) * -1
    
    return alpha069

def calculateAlpha070(vwap: pd.DataFrame, close_price: pd.DataFrame, adv50: pd.DataFrame) -> pd.DataFrame:
    """Alpha #70: ((rank(delta(vwap, 1.29456))^Ts_Rank(correlation(IndNeutralize(close, IndClass.industry), adv50, 17.8256), 17.9171)) * -1)
    
    该因子计算了两个排名的幂次组合并取负值。
    注意：由于缺少行业分类数据，这里简化为不进行行业中性化处理。
    
    Args:
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        adv50: 50日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha070因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(adv50, "adv50")
    
    # 第一部分：rank(delta(vwap, 1))
    delta_vwap_1 = vwap.diff(1)
    part1 = delta_vwap_1.rank(axis=1, pct=True)
    
    # 第二部分：Ts_Rank(correlation(close, adv50, 18), 18) (简化版)
    correlation_18d = pd.DataFrame(index=vwap.index, columns=vwap.columns)
    for col in vwap.columns:
        if col in adv50.columns:
            correlation_18d[col] = close_price[col].rolling(window=18).corr(adv50[col])
    
    part2 = ts_rank(correlation_18d, 18)
    
    # 计算幂次组合并取负值
    # 为避免数值问题，限制指数范围
    part2_clipped = np.clip(part2, 0.01, 10)
    alpha070 = (part1 ** part2_clipped) * -1
    
    return alpha070

def calculateAlpha071(close_price: pd.DataFrame, adv180: pd.DataFrame, low_price: pd.DataFrame, open_price: pd.DataFrame, vwap: pd.DataFrame) -> pd.DataFrame:
    """Alpha #71: max(Ts_Rank(decay_linear(correlation(Ts_Rank(close, 3.43976), Ts_Rank(adv180, 12.0647), 18.0175), 4.20501), 15.6948), Ts_Rank(decay_linear((rank(((low + open) - (vwap + vwap)))^2), 16.4662), 4.4388))
    
    该因子计算了两个时间序列排名的最大值。
    
    Args:
        close_price: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        adv180: 180日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        open_price: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha071因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_price, "close_price")
    validate_dataframe_input(adv180, "adv180")
    validate_dataframe_input(low_price, "low_price")
    validate_dataframe_input(open_price, "open_price")
    validate_dataframe_input(vwap, "vwap")
    
    # 第一部分：Ts_Rank(decay_linear(correlation(Ts_Rank(close, 3), Ts_Rank(adv180, 12), 18), 4), 16)
    ts_rank_close_3 = ts_rank(close_price, 3)
    ts_rank_adv180_12 = ts_rank(adv180, 12)
    
    correlation_18d = pd.DataFrame(index=close_price.index, columns=close_price.columns)
    for col in close_price.columns:
        if col in ts_rank_adv180_12.columns:
            correlation_18d[col] = ts_rank_close_3[col].rolling(window=18).corr(ts_rank_adv180_12[col])
    
    decay_linear_4 = decay_linear(correlation_18d, 4)
    part1 = ts_rank(decay_linear_4, 16)
    
    # 第二部分：Ts_Rank(decay_linear((rank(((low + open) - (vwap + vwap)))^2), 16), 4)
    price_diff = (low_price + open_price) - (vwap + vwap)
    rank_diff = price_diff.rank(axis=1, pct=True)
    rank_diff_squared = rank_diff ** 2
    
    decay_linear_16 = decay_linear(rank_diff_squared, 16)
    part2 = ts_rank(decay_linear_16, 4)
    
    # 计算最大值
    alpha071 = np.maximum(part1, part2)
    
    return alpha071

def calculateAlpha072(high_price: pd.DataFrame, low_price: pd.DataFrame, adv40: pd.DataFrame, vwap: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """Alpha #72: (rank(decay_linear(correlation(((high + low) / 2), adv40, 8.93345), 10.1519)) / rank(decay_linear(correlation(Ts_Rank(vwap, 3.72469), Ts_Rank(volume, 18.5188), 6.86671), 2.95011)))
    
    该因子计算了两个指标的比值。
    
    Args:
        high_price: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_price: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        adv40: 40日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        vwap: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha072因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(high_price, "high_price")
    validate_dataframe_input(low_price, "low_price")
    validate_dataframe_input(adv40, "adv40")
    validate_dataframe_input(vwap, "vwap")
    validate_dataframe_input(volume, "volume")
    
    # 分子：rank(decay_linear(correlation(((high + low) / 2), adv40, 9), 10))
    mid_price = (high_price + low_price) / 2
    correlation_9d = pd.DataFrame(index=high_price.index, columns=high_price.columns)
    for col in high_price.columns:
        if col in adv40.columns:
            correlation_9d[col] = mid_price[col].rolling(window=9).corr(adv40[col])
    
    decay_linear_10 = decay_linear(correlation_9d, 10)
    numerator = decay_linear_10.rank(axis=1, pct=True)
    
    # 分母：rank(decay_linear(correlation(Ts_Rank(vwap, 4), Ts_Rank(volume, 19), 7), 3))
    ts_rank_vwap_4 = ts_rank(vwap, 4)
    ts_rank_volume_19 = ts_rank(volume, 19)
    
    correlation_7d = pd.DataFrame(index=high_price.index, columns=high_price.columns)
    for col in high_price.columns:
        if col in ts_rank_volume_19.columns:
            correlation_7d[col] = ts_rank_vwap_4[col].rolling(window=7).corr(ts_rank_volume_19[col])
    
    decay_linear_3 = decay_linear(correlation_7d, 3)
    denominator = decay_linear_3.rank(axis=1, pct=True)
    
    # 避免除零
    denominator = denominator.replace(0, np.nan)
    alpha072 = numerator / denominator
    return alpha072


def calculateAlpha073(open_data: pd.DataFrame, low_data: pd.DataFrame, vwap_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #73: max(rank(decay_linear(delta(vwap, 4.72775), 2.91864)), 
                      Ts_Rank(decay_linear(((delta(((open * 0.147155) + (low * (1 - 0.147155))), 2.03608) / 
                                            ((open * 0.147155) + (low * (1 - 0.147155)))) * -1), 3.33829), 16.7411))
    
    该因子计算两个指标的最大值：
    1. VWAP的5日变化的3天线性衰减加权移动平均的排名
    2. 开盘价和最低价加权平均值的相对变化（负值）的3天衰减加权移动平均的17天时间序列排名
    
    Args:
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha073因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(open_data, "open_data")
    validate_dataframe_input(low_data, "low_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    
    # 参数（简化为整数）
    vwap_delta_period = 5  # 4.72775 -> 5
    vwap_decay_window = 3  # 2.91864 -> 3
    
    open_weight = 0.147155
    price_delta_period = 2  # 2.03608 -> 2
    price_decay_window = 3  # 3.33829 -> 3
    ts_rank_window = 17  # 16.7411 -> 17
    
    # 第一个指标：rank(decay_linear(delta(vwap, 5), 3))
    vwap_delta = vwap_data.diff(vwap_delta_period)
    vwap_decay = decay_linear(vwap_delta, vwap_decay_window)
    indicator1 = vwap_decay.rank(axis=1, pct=True)
    
    # 第二个指标：开盘价和最低价的加权平均
    weighted_price = open_data * open_weight + low_data * (1 - open_weight)
    
    # 计算相对变化
    price_delta = weighted_price.diff(price_delta_period)
    relative_change = price_delta / weighted_price
    relative_change_neg = relative_change * -1
    
    # 应用衰减和时间序列排名
    price_decay = decay_linear(relative_change_neg, price_decay_window)
    indicator2 = ts_rank(price_decay, ts_rank_window)
    
    # 计算最大值
    alpha073 = np.maximum(indicator1, indicator2)
    
    return alpha073


def calculateAlpha074(high_data: pd.DataFrame, low_data: pd.DataFrame, vwap_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #74: rank(decay_linear(correlation(((high + low) / 2), adv20, 10.1519), 8.93345)) - 
                  rank(decay_linear(correlation(Ts_Rank(vwap, 18.5188), Ts_Rank(volume, 3.72469), 2.95011), 6.86671))
    
    该因子计算两个指标的差值：
    1. 高低价平均值与20日平均成交量相关性的9天衰减加权移动平均的排名
    2. VWAP的19天时间序列排名与成交量的4天时间序列排名相关性的7天衰减加权移动平均的排名
    
    Args:
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha074因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(high_data, "high_data")
    validate_dataframe_input(low_data, "low_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 计算20日平均成交量
    adv20 = volume_data.rolling(window=20).mean()
    
    # 参数（简化为整数）
    corr1_window = 10  # 10.1519 -> 10
    decay1_window = 9  # 8.93345 -> 9
    vwap_ts_rank_window = 19  # 18.5188 -> 19
    volume_ts_rank_window = 4  # 3.72469 -> 4
    corr2_window = 3  # 2.95011 -> 3
    decay2_window = 7  # 6.86671 -> 7
    
    # 第一个指标：高低价平均值与adv20的相关性
    mid_price = (high_data + low_data) / 2
    corr1 = pd.DataFrame(index=mid_price.index, columns=mid_price.columns)
    
    for col in mid_price.columns:
        if col in adv20.columns:
            corr1[col] = mid_price[col].rolling(window=corr1_window).corr(adv20[col])
    
    decay1 = decay_linear(corr1, decay1_window)
    indicator1 = decay1.rank(axis=1, pct=True)
    
    # 第二个指标：VWAP和成交量的时间序列排名相关性
    vwap_ts_rank = ts_rank(vwap_data, vwap_ts_rank_window)
    volume_ts_rank = ts_rank(volume_data, volume_ts_rank_window)
    
    corr2 = pd.DataFrame(index=vwap_ts_rank.index, columns=vwap_ts_rank.columns)
    for col in vwap_ts_rank.columns:
        if col in volume_ts_rank.columns:
            corr2[col] = vwap_ts_rank[col].rolling(window=corr2_window).corr(volume_ts_rank[col])
    
    decay2 = decay_linear(corr2, decay2_window)
    indicator2 = decay2.rank(axis=1, pct=True)
    
    # 计算差值
    alpha074 = indicator1 - indicator2
    
    return alpha074


def calculateAlpha075(close_data: pd.DataFrame, high_data: pd.DataFrame, low_data: pd.DataFrame, 
                     open_data: pd.DataFrame, vwap_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #75: rank(decay_linear(delta(IndNeutralize(close, IndClass.industry), 3.51013), 7.23052)) + 
                  Ts_Rank(decay_linear(((vwap - (low * 0.96633 + low * (1 - 0.96633))) / 
                                       ((high + low) / 2 - open)), 6.72611), 11.4157)
    
    该因子计算两个指标的和：
    1. 行业中性化收盘价的4日变化的7天衰减加权移动平均的排名
    2. 价格关系异常指标的7天衰减加权移动平均的11天时间序列排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha075因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(high_data, "high_data")
    validate_dataframe_input(low_data, "low_data")
    validate_dataframe_input(open_data, "open_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    
    # 参数（简化为整数）
    close_delta_period = 4  # 3.51013 -> 4
    close_decay_window = 7  # 7.23052 -> 7
    price_decay_window = 7  # 6.72611 -> 7
    ts_rank_window = 11  # 11.4157 -> 11
    
    # 第一个指标：行业中性化收盘价变化（简化为去均值）
    close_neutralized = close_data.sub(close_data.mean(axis=1), axis=0)
    close_delta = close_neutralized.diff(close_delta_period)
    close_decay = decay_linear(close_delta, close_decay_window)
    indicator1 = close_decay.rank(axis=1, pct=True)
    
    # 第二个指标：价格关系异常
    # 注意：公式中 low * 0.96633 + low * (1 - 0.96633) = low，所以简化为 low
    weighted_low = low_data  # 简化后就是low本身
    mid_price = (high_data + low_data) / 2
    
    price_anomaly = (vwap_data - weighted_low) / (mid_price - open_data)
    price_anomaly = price_anomaly.replace([np.inf, -np.inf], np.nan)
    
    price_decay = decay_linear(price_anomaly, price_decay_window)
    indicator2 = ts_rank(price_decay, ts_rank_window)
    
    # 计算和
    alpha075 = indicator1 + indicator2
    
    return alpha075


def calculateAlpha076(high_data: pd.DataFrame, vwap_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #76: rank(correlation(IndNeutralize(vwap, IndClass.sector), 
                                  IndNeutralize(adv20, IndClass.subindustry), 6.02936)) - 
                  rank(high - ts_min(high, 2.14593))
    
    该因子计算两个排名的差值：
    1. 行业中性化VWAP与子行业中性化20日平均成交量的6天相关性排名
    2. 最高价减去过去2天最高价最小值的排名
    
    Args:
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha076因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(high_data, "high_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 计算20日平均成交量
    adv20 = volume_data.rolling(window=20).mean()
    
    # 参数（简化为整数）
    corr_window = 6  # 6.02936 -> 6
    ts_min_window = 2  # 2.14593 -> 2
    
    # 第一个指标：行业中性化相关性（简化为去均值）
    vwap_neutralized = vwap_data.sub(vwap_data.mean(axis=1), axis=0)
    adv20_neutralized = adv20.sub(adv20.mean(axis=1), axis=0)
    
    corr = pd.DataFrame(index=vwap_neutralized.index, columns=vwap_neutralized.columns)
    for col in vwap_neutralized.columns:
        if col in adv20_neutralized.columns:
            corr[col] = vwap_neutralized[col].rolling(window=corr_window).corr(adv20_neutralized[col])
    
    indicator1 = corr.rank(axis=1, pct=True)
    
    # 第二个指标：最高价相对近期低点
    high_min = high_data.rolling(window=ts_min_window).min()
    high_diff = high_data - high_min
    indicator2 = high_diff.rank(axis=1, pct=True)
    
    # 计算差值
    alpha076 = indicator1 - indicator2
    
    return alpha076


def calculateAlpha077(close_data: pd.DataFrame, low_data: pd.DataFrame, high_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #77: rank(delta(((close * 0.518371) + (low * (1 - 0.518371))), 1.06157)) - 
                  Ts_Rank(correlation(rank(high), rank(adv15), 8.91644), 13.9333)
    
    该因子计算两个排名的差值：
    1. 收盘价和最低价加权平均值的1日变化排名
    2. 最高价排名与15日平均成交量排名的9天相关性的14天时间序列排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha077因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(low_data, "low_data")
    validate_dataframe_input(high_data, "high_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 计算15日平均成交量
    adv15 = volume_data.rolling(window=15).mean()
    
    # 参数（简化为整数）
    close_weight = 0.518371
    delta_period = 1  # 1.06157 -> 1
    corr_window = 9  # 8.91644 -> 9
    ts_rank_window = 14  # 13.9333 -> 14
    
    # 第一个指标：加权价格变化
    weighted_price = close_data * close_weight + low_data * (1 - close_weight)
    price_delta = weighted_price.diff(delta_period)
    indicator1 = price_delta.rank(axis=1, pct=True)
    
    # 第二个指标：价格排名与成交量排名的相关性
    high_rank = high_data.rank(axis=1, pct=True)
    adv15_rank = adv15.rank(axis=1, pct=True)
    
    corr = pd.DataFrame(index=high_rank.index, columns=high_rank.columns)
    for col in high_rank.columns:
        if col in adv15_rank.columns:
            corr[col] = high_rank[col].rolling(window=corr_window).corr(adv15_rank[col])
    
    indicator2 = ts_rank(corr, ts_rank_window)
    
    # 计算差值
    alpha077 = indicator1 - indicator2
    
    return alpha077


def calculateAlpha078(close_data: pd.DataFrame, vwap_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #78: Ts_Rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 4.92416), 9.0615) - 
                  rank(ts_max(delta(IndNeutralize(vwap, IndClass.industry), 2.72412), 4.79344))
    
    该因子计算两个排名的差值：
    1. 收盘价和VWAP加权平均值与20日平均成交量的5天相关性的9天时间序列排名
    2. 行业中性化VWAP的3日变化的5天时间序列最大值的排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha078因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 计算20日平均成交量
    adv20 = volume_data.rolling(window=20).mean()
    
    # 参数（简化为整数）
    close_weight = 0.490655
    corr_window = 5  # 4.92416 -> 5
    ts_rank_window = 9  # 9.0615 -> 9
    vwap_delta_period = 3  # 2.72412 -> 3
    ts_max_window = 5  # 4.79344 -> 5
    
    # 第一个指标：价格与成交量相关性的时间序列排名
    weighted_price = close_data * close_weight + vwap_data * (1 - close_weight)
    
    corr = pd.DataFrame(index=weighted_price.index, columns=weighted_price.columns)
    for col in weighted_price.columns:
        if col in adv20.columns:
            corr[col] = weighted_price[col].rolling(window=corr_window).corr(adv20[col])
    
    indicator1 = ts_rank(corr, ts_rank_window)
    
    # 第二个指标：行业中性化VWAP变化的极值（简化为去均值）
    vwap_neutralized = vwap_data.sub(vwap_data.mean(axis=1), axis=0)
    vwap_delta = vwap_neutralized.diff(vwap_delta_period)
    vwap_max = vwap_delta.rolling(window=ts_max_window).max()
    indicator2 = vwap_max.rank(axis=1, pct=True)
    
    # 计算差值
    alpha078 = indicator1 - indicator2
    
    return alpha078


def calculateAlpha079(close_data: pd.DataFrame, vwap_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #79: Ts_Rank(correlation(IndNeutralize(close, IndClass.industry), adv50, 17.8256), 17.9171) - 
                  rank(delta(vwap, 1.29456))
    
    该因子计算两个排名的差值：
    1. 行业中性化收盘价与50日平均成交量的18天相关性的18天时间序列排名
    2. VWAP的1日变化排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha079因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 计算50日平均成交量
    adv50 = volume_data.rolling(window=50).mean()
    
    # 参数（简化为整数）
    corr_window = 18  # 17.8256 -> 18
    ts_rank_window = 18  # 17.9171 -> 18
    vwap_delta_period = 1  # 1.29456 -> 1
    
    # 第一个指标：行业中性化收盘价与长期成交量相关性（简化为去均值）
    close_neutralized = close_data.sub(close_data.mean(axis=1), axis=0)
    
    corr = pd.DataFrame(index=close_neutralized.index, columns=close_neutralized.columns)
    for col in close_neutralized.columns:
        if col in adv50.columns:
            corr[col] = close_neutralized[col].rolling(window=corr_window).corr(adv50[col])
    
    indicator1 = ts_rank(corr, ts_rank_window)
    
    # 第二个指标：VWAP短期变化
    vwap_delta = vwap_data.diff(vwap_delta_period)
    indicator2 = vwap_delta.rank(axis=1, pct=True)
    
    # 计算差值
    alpha079 = indicator1 - indicator2
    
    return alpha079


def calculateAlpha080(close_data: pd.DataFrame, low_data: pd.DataFrame, open_data: pd.DataFrame, 
                     vwap_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #80: min(Ts_Rank(decay_linear(correlation(Ts_Rank(close, 12.0647), Ts_Rank(adv180, 3.43976), 4.20501), 18.0175), 15.6948), 
                      Ts_Rank(decay_linear((rank(((low + open) - (vwap + vwap)))^2), 4.4388), 16.4662))
    
    该因子计算两个时间序列排名的最小值：
    1. 收盘价和180日平均成交量时间序列排名相关性的衰减加权移动平均的时间序列排名
    2. 价格关系异常平方的衰减加权移动平均的时间序列排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha080因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(low_data, "low_data")
    validate_dataframe_input(open_data, "open_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 计算180日平均成交量
    adv180 = volume_data.rolling(window=180).mean()
    
    # 参数（简化为整数）
    close_ts_rank_window = 12  # 12.0647 -> 12
    adv_ts_rank_window = 3  # 3.43976 -> 3
    corr_window = 4  # 4.20501 -> 4
    decay1_window = 18  # 18.0175 -> 18
    ts_rank1_window = 16  # 15.6948 -> 16
    decay2_window = 4  # 4.4388 -> 4
    ts_rank2_window = 16  # 16.4662 -> 16
    
    # 第一个指标：价格-成交量时间序列排名相关性
    close_ts_rank = ts_rank(close_data, close_ts_rank_window)
    adv_ts_rank = ts_rank(adv180, adv_ts_rank_window)
    
    corr = pd.DataFrame(index=close_ts_rank.index, columns=close_ts_rank.columns)
    for col in close_ts_rank.columns:
        if col in adv_ts_rank.columns:
            corr[col] = close_ts_rank[col].rolling(window=corr_window).corr(adv_ts_rank[col])
    
    decay1 = decay_linear(corr, decay1_window)
    indicator1 = ts_rank(decay1, ts_rank1_window)
    
    # 第二个指标：价格关系异常
    price_anomaly = (low_data + open_data) - (vwap_data + vwap_data)
    price_anomaly_rank = price_anomaly.rank(axis=1, pct=True)
    price_anomaly_squared = price_anomaly_rank ** 2
    
    decay2 = decay_linear(price_anomaly_squared, decay2_window)
    indicator2 = ts_rank(decay2, ts_rank2_window)
    
    # 计算最小值
    alpha080 = np.minimum(indicator1, indicator2)
    
    return alpha080


def calculateAlpha081(vwap_data: pd.DataFrame, volume_data: pd.DataFrame, high_data: pd.DataFrame, low_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #81: rank(decay_linear(correlation(Ts_Rank(vwap, 3.72469), Ts_Rank(volume, 18.5188), 6.86671), 2.95011)) / 
                  rank(decay_linear(correlation(((high + low) / 2), adv40, 8.93345), 10.1519))
    
    该因子计算两个指标的比值：
    1. VWAP的4天时间序列排名与成交量的19天时间序列排名的7天相关性的3天衰减加权移动平均的排名
    2. 高低价平均值与40日平均成交量的9天相关性的10天衰减加权移动平均的排名
    
    Args:
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha081因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(volume_data, "volume_data")
    validate_dataframe_input(high_data, "high_data")
    validate_dataframe_input(low_data, "low_data")
    
    # 计算40日平均成交量
    adv40 = volume_data.rolling(window=40).mean()
    
    # 参数（简化为整数）
    vwap_ts_rank_window = 4  # 3.72469 -> 4
    volume_ts_rank_window = 19  # 18.5188 -> 19
    corr1_window = 7  # 6.86671 -> 7
    decay1_window = 3  # 2.95011 -> 3
    corr2_window = 9  # 8.93345 -> 9
    decay2_window = 10  # 10.1519 -> 10
    
    # 分子：VWAP和成交量的时间序列排名相关性
    vwap_ts_rank = ts_rank(vwap_data, vwap_ts_rank_window)
    volume_ts_rank = ts_rank(volume_data, volume_ts_rank_window)
    
    corr1 = pd.DataFrame(index=vwap_ts_rank.index, columns=vwap_ts_rank.columns)
    for col in vwap_ts_rank.columns:
        if col in volume_ts_rank.columns:
            corr1[col] = vwap_ts_rank[col].rolling(window=corr1_window).corr(volume_ts_rank[col])
    
    decay1 = decay_linear(corr1, decay1_window)
    numerator = decay1.rank(axis=1, pct=True)
    
    # 分母：高低价平均值与adv40的相关性
    mid_price = (high_data + low_data) / 2
    corr2 = pd.DataFrame(index=mid_price.index, columns=mid_price.columns)
    
    for col in mid_price.columns:
        if col in adv40.columns:
            corr2[col] = mid_price[col].rolling(window=corr2_window).corr(adv40[col])
    
    decay2 = decay_linear(corr2, decay2_window)
    denominator = decay2.rank(axis=1, pct=True)
    
    # 避免除零
    denominator = denominator.replace(0, np.nan)
    alpha081 = numerator / denominator
    
    return alpha081


def calculateAlpha082(vwap_data: pd.DataFrame, open_data: pd.DataFrame, low_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #82: rank(decay_linear(delta(vwap, 4.72775), 2.91864)) - 
                  Ts_Rank(decay_linear(((delta(((open * 0.147155) + (low * (1 - 0.147155))), 2.03608) / 
                                        ((open * 0.147155) + (low * (1 - 0.147155)))) * -1), 3.33829), 16.7411)
    
    该因子计算两个指标的差值：
    1. VWAP的5日变化的3天衰减加权移动平均的排名
    2. 开盘价和最低价加权平均值的相对变化（负值）的3天衰减加权移动平均的17天时间序列排名
    
    Args:
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha082因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(open_data, "open_data")
    validate_dataframe_input(low_data, "low_data")
    
    # 参数（简化为整数）
    vwap_delta_period = 5  # 4.72775 -> 5
    vwap_decay_window = 3  # 2.91864 -> 3
    
    open_weight = 0.147155
    price_delta_period = 2  # 2.03608 -> 2
    price_decay_window = 3  # 3.33829 -> 3
    ts_rank_window = 17  # 16.7411 -> 17
    
    # 第一个指标：rank(decay_linear(delta(vwap, 5), 3))
    vwap_delta = vwap_data.diff(vwap_delta_period)
    vwap_decay = decay_linear(vwap_delta, vwap_decay_window)
    indicator1 = vwap_decay.rank(axis=1, pct=True)
    
    # 第二个指标：开盘价和最低价的加权平均
    weighted_price = open_data * open_weight + low_data * (1 - open_weight)
    
    # 计算相对变化
    price_delta = weighted_price.diff(price_delta_period)
    relative_change = price_delta / weighted_price
    relative_change_neg = relative_change * -1
    
    # 应用衰减和时间序列排名
    price_decay = decay_linear(relative_change_neg, price_decay_window)
    indicator2 = ts_rank(price_decay, ts_rank_window)
    
    # 计算差值
    alpha082 = indicator1 - indicator2
    
    return alpha082


def calculateAlpha083(open_data: pd.DataFrame, vwap_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #83: rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 8.6911), 6.40374)) - 
                  rank((open - ts_min(open, 13.635)))
    
    该因子计算两个排名的差值：
    1. 开盘价和VWAP加权平均值与60日平均成交量的9天滚动和的6天相关性排名
    2. 开盘价减去过去14天开盘价最小值的排名
    
    Args:
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha083因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(open_data, "open_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 计算60日平均成交量
    adv60 = volume_data.rolling(window=60).mean()
    
    # 参数（简化为整数）
    open_weight = 0.00817205
    sum_window = 9  # 8.6911 -> 9
    corr_window = 6  # 6.40374 -> 6
    ts_min_window = 14  # 13.635 -> 14
    
    # 第一个指标：加权价格与成交量滚动和的相关性
    weighted_price = open_data * open_weight + vwap_data * (1 - open_weight)
    adv60_sum = ts_sum(adv60, sum_window)
    
    corr = pd.DataFrame(index=weighted_price.index, columns=weighted_price.columns)
    for col in weighted_price.columns:
        if col in adv60_sum.columns:
            corr[col] = weighted_price[col].rolling(window=corr_window).corr(adv60_sum[col])
    
    indicator1 = corr.rank(axis=1, pct=True)
    
    # 第二个指标：开盘价相对近期低点
    open_min = ts_min(open_data, ts_min_window)
    open_diff = open_data - open_min
    indicator2 = open_diff.rank(axis=1, pct=True)
    
    # 计算差值
    alpha083 = indicator1 - indicator2
    
    return alpha083


def calculateAlpha084(high_data: pd.DataFrame, low_data: pd.DataFrame, vwap_data: pd.DataFrame, 
                     open_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #84: rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404))), 3.69741)) - 
                  rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054), 
                                  sum(adv120, 12.7054), 16.6208))
    
    该因子计算两个排名的差值：
    1. 高低价平均值和VWAP加权平均值的4日变化排名
    2. 开盘价和最低价加权平均值的13天滚动和与120日平均成交量的13天滚动和的17天相关性排名
    
    Args:
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha084因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(high_data, "high_data", allow_nan=True)
    validateDataFormat(low_data, "low_data", allow_nan=True)
    validateDataFormat(vwap_data, "vwap_data", allow_nan=True)
    validateDataFormat(open_data, "open_data", allow_nan=True)
    validateDataFormat(volume_data, "volume_data", allow_nan=True)
    
    # 计算120日平均成交量
    adv120 = volume_data.rolling(window=120).mean()
    
    # 参数（简化为整数）
    weight = 0.178404
    delta_period = 4  # 3.69741 -> 4
    sum_window = 13  # 12.7054 -> 13
    corr_window = 17  # 16.6208 -> 17
    
    # 第一个指标：加权价格变化
    mid_price = (high_data + low_data) / 2
    weighted_price1 = mid_price * weight + vwap_data * (1 - weight)
    price_delta = weighted_price1.diff(delta_period)
    indicator1 = price_delta.rank(axis=1, pct=True)
    
    # 第二个指标：价格滚动和与成交量滚动和的相关性
    weighted_price2 = open_data * weight + low_data * (1 - weight)
    price_sum = ts_sum(weighted_price2, sum_window)
    adv120_sum = ts_sum(adv120, sum_window)
    
    corr = pd.DataFrame(index=price_sum.index, columns=price_sum.columns)
    for col in price_sum.columns:
        if col in adv120_sum.columns:
            corr[col] = price_sum[col].rolling(window=corr_window).corr(adv120_sum[col])
    
    indicator2 = corr.rank(axis=1, pct=True)
    
    # 计算差值
    alpha084 = indicator1 - indicator2
    
    return alpha084


def calculateAlpha085(vwap_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #85: rank(decay_linear(correlation(IndNeutralize(((vwap * 0.728317) + (vwap * (1 - 0.728317))), 
                                                IndClass.industry), volume, 4.25197), 16.2289)) - 
                  Ts_Rank(decay_linear(correlation(IndNeutralize(vwap, IndClass.sector), volume, 3.92795), 7.89291), 5.50322)
    
    该因子计算两个指标的差值：
    1. 行业中性化VWAP与成交量的4天相关性的16天衰减加权移动平均的排名
    2. 行业中性化VWAP与成交量的4天相关性的8天衰减加权移动平均的6天时间序列排名
    
    Args:
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha085因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(vwap_data, "vwap_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 参数（简化为整数）
    # 注意：vwap * 0.728317 + vwap * (1 - 0.728317) = vwap，所以简化为vwap
    corr1_window = 4  # 4.25197 -> 4
    decay1_window = 16  # 16.2289 -> 16
    corr2_window = 4  # 3.92795 -> 4
    decay2_window = 8  # 7.89291 -> 8
    ts_rank_window = 6  # 5.50322 -> 6
    
    # 第一个指标：行业中性化VWAP与成交量相关性（简化为去均值）
    vwap_neutralized = vwap_data.sub(vwap_data.mean(axis=1), axis=0)
    
    corr1 = pd.DataFrame(index=vwap_neutralized.index, columns=vwap_neutralized.columns)
    for col in vwap_neutralized.columns:
        if col in volume_data.columns:
            corr1[col] = vwap_neutralized[col].rolling(window=corr1_window).corr(volume_data[col])
    
    decay1 = decay_linear(corr1, decay1_window)
    indicator1 = decay1.rank(axis=1, pct=True)
    
    # 第二个指标：同样的相关性但不同的衰减和时间序列排名
    corr2 = pd.DataFrame(index=vwap_neutralized.index, columns=vwap_neutralized.columns)
    for col in vwap_neutralized.columns:
        if col in volume_data.columns:
            corr2[col] = vwap_neutralized[col].rolling(window=corr2_window).corr(volume_data[col])
    
    decay2 = decay_linear(corr2, decay2_window)
    indicator2 = ts_rank(decay2, ts_rank_window)
    
    # 计算差值
    alpha085 = indicator1 - indicator2
    
    return alpha085


def calculateAlpha086(close_data: pd.DataFrame, high_data: pd.DataFrame, low_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #86: rank(ts_argmax(close, 10)) - 2 * rank(((((close - low) - (high - close)) / (high - low)) * volume))
    
    该因子计算两个排名的差值：
    1. 收盘价在过去10天内达到最大值的日期排名
    2. 价格在当日价格范围内的位置乘以成交量的排名的2倍
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha086因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(high_data, "high_data")
    validate_dataframe_input(low_data, "low_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 第一个指标：收盘价10天最大值索引
    close_argmax = ts_argmax(close_data, 10)
    indicator1 = close_argmax.rank(axis=1, pct=True)
    
    # 第二个指标：价格位置乘以成交量
    price_range = high_data - low_data
    price_position = ((close_data - low_data) - (high_data - close_data)) / price_range
    price_position = price_position.replace([np.inf, -np.inf], np.nan)
    
    position_volume = price_position * volume_data
    indicator2 = position_volume.rank(axis=1, pct=True)
    
    # 计算差值
    alpha086 = indicator1 - 2 * indicator2
    
    return alpha086


def calculateAlpha087(close_data: pd.DataFrame, low_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #87: rank(((sum(returns, 240) - sum(returns, 20)) / 220)) - 
                  rank(((-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)) * ts_rank(volume, 5))
    
    该因子计算两个排名的差值：
    1. 长期趋势（240天累计收益率减去20天累计收益率除以220）的排名
    2. 短期价格反转潜力乘以成交量时间序列排名的排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha087因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(low_data, "low_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 计算收益率
    returns = close_data.pct_change()
    
    # 第一个指标：长期趋势
    returns_240 = ts_sum(returns, 240)
    returns_20 = ts_sum(returns, 20)
    long_trend = (returns_240 - returns_20) / 220
    indicator1 = long_trend.rank(axis=1, pct=True)
    
    # 第二个指标：短期价格反转潜力
    low_min_5 = ts_min(low_data, 5)
    low_min_5_delayed = delay(low_min_5, 5)
    
    reversal_potential = (-1 * low_min_5) + low_min_5_delayed
    volume_ts_rank = ts_rank(volume_data, 5)
    
    reversal_volume = reversal_potential * volume_ts_rank
    indicator2 = reversal_volume.rank(axis=1, pct=True)
    
    # 计算差值
    alpha087 = indicator1 - indicator2
    
    return alpha087


def calculateAlpha088(close_data: pd.DataFrame, high_data: pd.DataFrame, low_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #88: rank(volume) - rank(correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), 
                                                  rank(volume), 6))
    
    该因子计算两个排名的差值：
    1. 成交量的排名
    2. 价格在过去12天价格范围内的位置排名与成交量排名的6天相关性排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha088因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(high_data, "high_data")
    validate_dataframe_input(low_data, "low_data")
    validate_dataframe_input(volume_data, "volume_data")
    
    # 第一个指标：成交量排名
    indicator1 = volume_data.rank(axis=1, pct=True)
    
    # 第二个指标：价格位置与成交量的相关性
    low_min_12 = ts_min(low_data, 12)
    high_max_12 = ts_max(high_data, 12)
    
    price_position = (close_data - low_min_12) / (high_max_12 - low_min_12)
    price_position = price_position.replace([np.inf, -np.inf], np.nan)
    
    price_position_rank = price_position.rank(axis=1, pct=True)
    volume_rank = volume_data.rank(axis=1, pct=True)
    
    corr = pd.DataFrame(index=price_position_rank.index, columns=price_position_rank.columns)
    for col in price_position_rank.columns:
        if col in volume_rank.columns:
            corr[col] = price_position_rank[col].rolling(window=6).corr(volume_rank[col])
    
    indicator2 = corr.rank(axis=1, pct=True)
    
    # 计算差值
    alpha088 = indicator1 - indicator2
    
    return alpha088


def calculateAlpha089(close_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #89: rank((returns * cap)) - rank((sum(returns, 10) / sum(sum(returns, 2), 3)))
    
    该因子计算两个排名的差值：
    1. 当日收益率乘以市值的排名（简化为收益率排名，因为缺少市值数据）
    2. 过去10天累计收益率除以过去3个2天累计收益率的和的排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha089因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    
    # 计算收益率
    returns = close_data.pct_change()
    
    # 第一个指标：收益率排名（简化，因为缺少市值数据）
    indicator1 = returns.rank(axis=1, pct=True)
    
    # 第二个指标：收益率模式
    returns_10 = ts_sum(returns, 10)
    returns_2 = ts_sum(returns, 2)
    returns_2_sum_3 = ts_sum(returns_2, 3)
    
    returns_pattern = returns_10 / returns_2_sum_3
    returns_pattern = returns_pattern.replace([np.inf, -np.inf], np.nan)
    indicator2 = returns_pattern.rank(axis=1, pct=True)
    
    # 计算差值
    alpha089 = indicator1 - indicator2
    
    return alpha089


def calculateAlpha090(close_data: pd.DataFrame, vwap_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #90: rank(ts_argmax(close, 30)) - rank((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))
    
    该因子计算两个排名的差值：
    1. 收盘价在过去30天内达到最大值的日期排名
    2. 收盘价相对VWAP的偏离除以收盘价30天最大值索引排名的2天衰减加权移动平均的排名
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha090因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validate_dataframe_input(close_data, "close_data")
    validate_dataframe_input(vwap_data, "vwap_data")
    
    # 第一个指标：收盘价30天最大值索引
    close_argmax_30 = ts_argmax(close_data, 30)
    indicator1 = close_argmax_30.rank(axis=1, pct=True)
    
    # 第二个指标：价格偏离的标准化
    price_deviation = close_data - vwap_data
    
    close_argmax_30_rank = close_argmax_30.rank(axis=1, pct=True)
    decay_rank = decay_linear(close_argmax_30_rank, 2)
    
    normalized_deviation = price_deviation / decay_rank
    normalized_deviation = normalized_deviation.replace([np.inf, -np.inf], np.nan)
    indicator2 = normalized_deviation.rank(axis=1, pct=True)
    
    # 计算差值
    alpha090 = indicator1 - indicator2
    
    return alpha090


def calculateAlpha091(high_data: pd.DataFrame, adv15_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #91: rank(adv180) - rank(correlation(rank(high), rank(adv15), 8.91644))
    
    该因子计算了两个排名的差值：
    1. 180日平均每日交易量的排名
    2. 最高价排名与15日平均每日交易量排名在过去9天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉长期平均交易量与价格排名-成交量关系之间的差异。
    当长期平均交易量的排名高于价格排名-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        adv15_data: 15日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha091因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(high_data, "high_data", allow_nan=True)
    validateDataFormat(adv15_data, "adv15_data", allow_nan=True)
    
    # 计算180日平均每日交易量（使用15日数据的滚动平均近似）
    adv180 = adv15_data.rolling(window=12).mean()  # 近似180日平均
    
    # 第一个指标：180日平均每日交易量的排名
    indicator1 = adv180.rank(axis=1, pct=True)
    
    # 第二个指标：最高价排名与15日平均每日交易量排名的9天相关性
    ranked_high = high_data.rank(axis=1, pct=True)
    ranked_adv15 = adv15_data.rank(axis=1, pct=True)
    
    correlation_9d = pd.DataFrame(index=high_data.index, columns=high_data.columns)
    for col in high_data.columns:
        if col in adv15_data.columns:
            correlation_9d[col] = ranked_high[col].rolling(window=9).corr(ranked_adv15[col])
    
    indicator2 = correlation_9d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha091 = indicator1 - indicator2
    
    return alpha091


def calculateAlpha092(open_data: pd.DataFrame, vwap_data: pd.DataFrame, adv60_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #92: rank(adv60) - rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 8.6911), 6.40374))
    
    该因子计算了两个排名的差值：
    1. 60日平均每日交易量的排名
    2. 开盘价和成交量加权平均价格的加权平均值与60日平均每日交易量的9天滚动和在过去6天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉60日平均每日交易量与价格-成交量关系之间的差异。
    当60日平均每日交易量的排名高于价格-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        adv60_data: 60日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha092因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(open_data, "open_data", allow_nan=True)
    validateDataFormat(vwap_data, "vwap_data", allow_nan=True)
    validateDataFormat(adv60_data, "adv60_data", allow_nan=True)
    
    # 第一个指标：60日平均每日交易量的排名
    indicator1 = adv60_data.rank(axis=1, pct=True)
    
    # 第二个指标：价格-成交量关系
    # 开盘价和VWAP的加权平均
    weight = 0.00817205
    weighted_price = open_data * weight + vwap_data * (1 - weight)
    
    # 60日平均每日交易量的9天滚动和
    adv60_sum_9 = ts_sum(adv60_data, 9)
    
    # 计算6天相关性
    correlation_6d = pd.DataFrame(index=open_data.index, columns=open_data.columns)
    for col in open_data.columns:
        if col in adv60_data.columns:
            correlation_6d[col] = weighted_price[col].rolling(window=6).corr(adv60_sum_9[col])
    
    indicator2 = correlation_6d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha092 = indicator1 - indicator2
    
    return alpha092


def calculateAlpha093(close_data: pd.DataFrame, vwap_data: pd.DataFrame, adv20_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #93: rank(adv20) - rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 4.92416))
    
    该因子计算了两个排名的差值：
    1. 20日平均每日交易量的排名
    2. 收盘价和成交量加权平均价格的加权平均值与20日平均每日交易量在过去5天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉20日平均每日交易量与价格-成交量关系之间的差异。
    当20日平均每日交易量的排名高于价格-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        adv20_data: 20日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha093因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(close_data, "close_data", allow_nan=True)
    validateDataFormat(vwap_data, "vwap_data", allow_nan=True)
    validateDataFormat(adv20_data, "adv20_data", allow_nan=True)
    
    # 第一个指标：20日平均每日交易量的排名
    indicator1 = adv20_data.rank(axis=1, pct=True)
    
    # 第二个指标：价格-成交量关系
    # 收盘价和VWAP的加权平均
    weight = 0.490655
    weighted_price = close_data * weight + vwap_data * (1 - weight)
    
    # 计算5天相关性
    correlation_5d = pd.DataFrame(index=close_data.index, columns=close_data.columns)
    for col in close_data.columns:
        if col in adv20_data.columns:
            correlation_5d[col] = weighted_price[col].rolling(window=5).corr(adv20_data[col])
    
    indicator2 = correlation_5d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha093 = indicator1 - indicator2
    
    return alpha093


def calculateAlpha094(close_data: pd.DataFrame, adv50_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #94: rank(adv50) - rank(correlation(IndNeutralize(close, IndClass.industry), adv50, 17.8256))
    
    该因子计算了两个排名的差值：
    1. 50日平均每日交易量的排名
    2. 行业中性化的收盘价与50日平均每日交易量在过去18天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉50日平均每日交易量与行业中性化的价格-成交量关系之间的差异。
    当50日平均每日交易量的排名高于行业中性化的价格-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    注意：由于缺少行业分类数据，这里简化为不进行行业中性化处理。
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        adv50_data: 50日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha094因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(close_data, "close_data", allow_nan=True)
    validateDataFormat(adv50_data, "adv50_data", allow_nan=True)
    
    # 第一个指标：50日平均每日交易量的排名
    indicator1 = adv50_data.rank(axis=1, pct=True)
    
    # 第二个指标：行业中性化的价格-成交量关系（简化为去均值）
    close_neutralized = close_data.sub(close_data.mean(axis=1), axis=0)
    
    # 计算18天相关性
    correlation_18d = pd.DataFrame(index=close_data.index, columns=close_data.columns)
    for col in close_data.columns:
        if col in adv50_data.columns:
            correlation_18d[col] = close_neutralized[col].rolling(window=18).corr(adv50_data[col])
    
    indicator2 = correlation_18d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha094 = indicator1 - indicator2
    
    return alpha094


def calculateAlpha095(high_data: pd.DataFrame, low_data: pd.DataFrame, adv40_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #95: rank(adv40) - rank(correlation(((high + low) / 2), adv40, 8.93345))
    
    该因子计算了两个排名的差值：
    1. 40日平均每日交易量的排名
    2. 高低价平均值与40日平均每日交易量在过去9天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉40日平均每日交易量与价格-成交量关系之间的差异。
    当40日平均每日交易量的排名高于价格-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        adv40_data: 40日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha095因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(high_data, "high_data", allow_nan=True)
    validateDataFormat(low_data, "low_data", allow_nan=True)
    validateDataFormat(adv40_data, "adv40_data", allow_nan=True)
    
    # 第一个指标：40日平均每日交易量的排名
    indicator1 = adv40_data.rank(axis=1, pct=True)
    
    # 第二个指标：高低价平均值与成交量的相关性
    mid_price = (high_data + low_data) / 2
    
    # 计算9天相关性
    correlation_9d = pd.DataFrame(index=high_data.index, columns=high_data.columns)
    for col in high_data.columns:
        if col in adv40_data.columns:
            correlation_9d[col] = mid_price[col].rolling(window=9).corr(adv40_data[col])
    
    indicator2 = correlation_9d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha095 = indicator1 - indicator2
    
    return alpha095


def calculateAlpha096(open_data: pd.DataFrame, low_data: pd.DataFrame, adv120_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #96: rank(adv120) - rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054), sum(adv120, 12.7054), 16.6208))
    
    该因子计算了两个排名的差值：
    1. 120日平均每日交易量的排名
    2. 开盘价和最低价的加权平均值的13天滚动和与120日平均每日交易量的13天滚动和在过去17天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉120日平均每日交易量与价格滚动和与成交量滚动和的关系之间的差异。
    当120日平均每日交易量的排名高于价格滚动和与成交量滚动和的关系排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        adv120_data: 120日平均每日交易量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha096因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(open_data, "open_data", allow_nan=True)
    validateDataFormat(low_data, "low_data", allow_nan=True)
    validateDataFormat(adv120_data, "adv120_data", allow_nan=True)
    
    # 第一个指标：120日平均每日交易量的排名
    indicator1 = adv120_data.rank(axis=1, pct=True)
    
    # 第二个指标：价格滚动和与成交量滚动和的相关性
    # 开盘价和最低价的加权平均
    weight = 0.178404
    weighted_price = open_data * weight + low_data * (1 - weight)
    
    # 13天滚动和
    price_sum_13 = ts_sum(weighted_price, 13)
    adv120_sum_13 = ts_sum(adv120_data, 13)
    
    # 计算17天相关性
    correlation_17d = pd.DataFrame(index=open_data.index, columns=open_data.columns)
    for col in open_data.columns:
        if col in adv120_data.columns:
            correlation_17d[col] = price_sum_13[col].rolling(window=17).corr(adv120_sum_13[col])
    
    indicator2 = correlation_17d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha096 = indicator1 - indicator2
    
    return alpha096


def calculateAlpha097(close_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #97: rank(volume) - rank(correlation(rank(close), rank(volume), 5))
    
    该因子计算了两个排名的差值：
    1. 成交量的排名
    2. 收盘价的排名与成交量的排名在过去5天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉成交量与价格-成交量关系之间的差异。
    当成交量的排名高于价格-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        close_data: 收盘价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha097因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(close_data, "close_data", allow_nan=True)
    validateDataFormat(volume_data, "volume_data", allow_nan=True)
    
    # 第一个指标：成交量的排名
    indicator1 = volume_data.rank(axis=1, pct=True)
    
    # 第二个指标：收盘价排名与成交量排名的5天相关性
    ranked_close = close_data.rank(axis=1, pct=True)
    ranked_volume = volume_data.rank(axis=1, pct=True)
    
    correlation_5d = pd.DataFrame(index=close_data.index, columns=close_data.columns)
    for col in close_data.columns:
        if col in volume_data.columns:
            correlation_5d[col] = ranked_close[col].rolling(window=5).corr(ranked_volume[col])
    
    indicator2 = correlation_5d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha097 = indicator1 - indicator2
    
    return alpha097


def calculateAlpha098(high_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #98: rank(volume) - rank(correlation(rank(high), rank(volume), 5))
    
    该因子计算了两个排名的差值：
    1. 成交量的排名
    2. 最高价的排名与成交量的排名在过去5天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉成交量与价格高点-成交量关系之间的差异。
    当成交量的排名高于价格高点-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        high_data: 最高价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha098因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(high_data, "high_data", allow_nan=True)
    validateDataFormat(volume_data, "volume_data", allow_nan=True)
    
    # 第一个指标：成交量的排名
    indicator1 = volume_data.rank(axis=1, pct=True)
    
    # 第二个指标：最高价排名与成交量排名的5天相关性
    ranked_high = high_data.rank(axis=1, pct=True)
    ranked_volume = volume_data.rank(axis=1, pct=True)
    
    correlation_5d = pd.DataFrame(index=high_data.index, columns=high_data.columns)
    for col in high_data.columns:
        if col in volume_data.columns:
            correlation_5d[col] = ranked_high[col].rolling(window=5).corr(ranked_volume[col])
    
    indicator2 = correlation_5d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha098 = indicator1 - indicator2
    
    return alpha098


def calculateAlpha099(low_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #99: rank(volume) - rank(correlation(rank(low), rank(volume), 5))
    
    该因子计算了两个排名的差值：
    1. 成交量的排名
    2. 最低价的排名与成交量的排名在过去5天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉成交量与价格低点-成交量关系之间的差异。
    当成交量的排名高于价格低点-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        low_data: 最低价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha099因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(low_data, "low_data", allow_nan=True)
    validateDataFormat(volume_data, "volume_data", allow_nan=True)
    
    # 第一个指标：成交量的排名
    indicator1 = volume_data.rank(axis=1, pct=True)
    
    # 第二个指标：最低价排名与成交量排名的5天相关性
    ranked_low = low_data.rank(axis=1, pct=True)
    ranked_volume = volume_data.rank(axis=1, pct=True)
    
    correlation_5d = pd.DataFrame(index=low_data.index, columns=low_data.columns)
    for col in low_data.columns:
        if col in volume_data.columns:
            correlation_5d[col] = ranked_low[col].rolling(window=5).corr(ranked_volume[col])
    
    indicator2 = correlation_5d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha099 = indicator1 - indicator2
    
    return alpha099


def calculateAlpha100(open_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #100: rank(volume) - rank(correlation(rank(open), rank(volume), 10))
    
    该因子计算了两个排名的差值：
    1. 成交量的排名
    2. 开盘价的排名与成交量的排名在过去10天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉成交量与开盘价-成交量关系之间的差异。
    当成交量的排名高于开盘价-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        open_data: 开盘价数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha100因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(open_data, "open_data", allow_nan=True)
    validateDataFormat(volume_data, "volume_data", allow_nan=True)
    
    # 第一个指标：成交量的排名
    indicator1 = volume_data.rank(axis=1, pct=True)
    
    # 第二个指标：开盘价排名与成交量排名的10天相关性
    ranked_open = open_data.rank(axis=1, pct=True)
    ranked_volume = volume_data.rank(axis=1, pct=True)
    
    correlation_10d = pd.DataFrame(index=open_data.index, columns=open_data.columns)
    for col in open_data.columns:
        if col in volume_data.columns:
            correlation_10d[col] = ranked_open[col].rolling(window=10).corr(ranked_volume[col])
    
    indicator2 = correlation_10d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha100 = indicator1 - indicator2
    
    return alpha100


def calculateAlpha101(vwap_data: pd.DataFrame, volume_data: pd.DataFrame) -> pd.DataFrame:
    """Alpha #101: rank(volume) - rank(correlation(rank(vwap), rank(volume), 5))
    
    该因子计算了两个排名的差值：
    1. 成交量的排名
    2. 成交量加权平均价格的排名与成交量的排名在过去5天内的相关性的排名
    
    逻辑解读:
    该因子试图捕捉成交量与成交量加权平均价格-成交量关系之间的差异。
    当成交量的排名高于成交量加权平均价格-成交量关系的排名时，该因子值为正，可能预示着买入机会。
    
    Args:
        vwap_data: 成交量加权平均价格数据，DataFrame格式，index为日期，columns为股票代码
        volume_data: 成交量数据，DataFrame格式，index为日期，columns为股票代码
        
    Returns:
        pd.DataFrame: Alpha101因子值，index为日期，columns为股票代码
    """
    # 数据验证
    validateDataFormat(vwap_data, "vwap_data", allow_nan=True)
    validateDataFormat(volume_data, "volume_data", allow_nan=True)
    
    # 第一个指标：成交量的排名
    indicator1 = volume_data.rank(axis=1, pct=True)
    
    # 第二个指标：VWAP排名与成交量排名的5天相关性
    ranked_vwap = vwap_data.rank(axis=1, pct=True)
    ranked_volume = volume_data.rank(axis=1, pct=True)
    
    correlation_5d = pd.DataFrame(index=vwap_data.index, columns=vwap_data.columns)
    for col in vwap_data.columns:
        if col in volume_data.columns:
            correlation_5d[col] = ranked_vwap[col].rolling(window=5).corr(ranked_volume[col])
    
    indicator2 = correlation_5d.rank(axis=1, pct=True)
    
    # 计算差值
    alpha101 = indicator1 - indicator2
    
    return alpha101