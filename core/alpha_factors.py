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
from core.alpha_helpers import decay_linear, scale


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
    weighted_vwap = vwap * 0.728317 + vwap * (1 - 0.728317)  # 实际上就是vwap
    
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

def calculateAlpha061():
    """Alpha #61: 复杂公式，涉及adv180
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha061 尚未实现")

def calculateAlpha062():
    """Alpha #62: 复杂公式，涉及adv20
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha062 尚未实现")

def calculateAlpha063():
    """Alpha #63: 复杂公式，涉及行业中性化
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha063 尚未实现")

def calculateAlpha064():
    """Alpha #64: 复杂公式，涉及adv120
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha064 尚未实现")

def calculateAlpha065():
    """Alpha #65: 复杂公式，涉及adv60
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha065 尚未实现")

def calculateAlpha066():
    """Alpha #66: 复杂公式，涉及decay_linear
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha066 尚未实现")

def calculateAlpha067():
    """Alpha #67: 复杂公式，涉及行业中性化
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha067 尚未实现")

def calculateAlpha068():
    """Alpha #68: 复杂公式，涉及adv15
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha068 尚未实现")

def calculateAlpha069():
    """Alpha #69: 复杂公式，涉及行业中性化
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha069 尚未实现")

def calculateAlpha070():
    """Alpha #70: 复杂公式，涉及行业中性化和adv50
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha070 尚未实现")

def calculateAlpha071():
    """Alpha #71: 复杂公式，涉及max和decay_linear
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha071 尚未实现")

def calculateAlpha072():
    """Alpha #72: 复杂公式，涉及adv40
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha072 尚未实现")

def calculateAlpha073():
    """Alpha #73: 复杂公式，涉及max和decay_linear
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha073 尚未实现")

def calculateAlpha074():
    """Alpha #74: 复杂公式，涉及adv20
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha074 尚未实现")

def calculateAlpha075():
    """Alpha #75: 复杂公式，涉及行业中性化
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha075 尚未实现")

def calculateAlpha076():
    """Alpha #76: 复杂公式，涉及行业中性化
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha076 尚未实现")

def calculateAlpha077():
    """Alpha #77: 复杂公式，涉及adv15
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha077 尚未实现")

def calculateAlpha078():
    """Alpha #78: 复杂公式，涉及行业中性化和adv20
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha078 尚未实现")

def calculateAlpha079():
    """Alpha #79: 复杂公式，涉及行业中性化和adv50
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha079 尚未实现")

def calculateAlpha080():
    """Alpha #80: 复杂公式，涉及min和decay_linear
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha080 尚未实现")

def calculateAlpha081():
    """Alpha #81: 复杂公式，涉及adv40
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha081 尚未实现")

def calculateAlpha082():
    """Alpha #82: 复杂公式，涉及decay_linear
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha082 尚未实现")

def calculateAlpha083():
    """Alpha #83: 复杂公式，涉及adv60
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha083 尚未实现")

def calculateAlpha084():
    """Alpha #84: 复杂公式，涉及adv120
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha084 尚未实现")

def calculateAlpha085():
    """Alpha #85: 复杂公式，涉及行业中性化
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha085 尚未实现")

def calculateAlpha086():
    """Alpha #86: (rank(ts_argmax(close, 10)) - 2 * rank(((((close - low) - (high - close)) / (high - low)) * volume))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha086 尚未实现")

def calculateAlpha087():
    """Alpha #87: 复杂公式，涉及returns
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha087 尚未实现")

def calculateAlpha088():
    """Alpha #88: (rank(volume) - rank(correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha088 尚未实现")

def calculateAlpha089():
    """Alpha #89: (rank((returns * cap)) - rank((sum(returns, 10) / sum(sum(returns, 2), 3)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha089 尚未实现")

def calculateAlpha090():
    """Alpha #90: (rank(ts_argmax(close, 30)) - rank((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha090 尚未实现")

def calculateAlpha091():
    """Alpha #91: (rank(adv180) - rank(correlation(rank(high), rank(adv15), 8.91644)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha091 尚未实现")

def calculateAlpha092():
    """Alpha #92: (rank(adv60) - rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 8.6911), 6.40374)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha092 尚未实现")

def calculateAlpha093():
    """Alpha #93: (rank(adv20) - rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 4.92416)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha093 尚未实现")

def calculateAlpha094():
    """Alpha #94: (rank(adv50) - rank(correlation(IndNeutralize(close, IndClass.industry), adv50, 17.8256)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha094 尚未实现")

def calculateAlpha095():
    """Alpha #95: (rank(adv40) - rank(correlation(((high + low) / 2), adv40, 8.93345)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha095 尚未实现")

def calculateAlpha096():
    """Alpha #96: (rank(adv120) - rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054), sum(adv120, 12.7054), 16.6208)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha096 尚未实现")

def calculateAlpha097():
    """Alpha #97: (rank(volume) - rank(correlation(rank(close), rank(volume), 5)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha097 尚未实现")

def calculateAlpha098():
    """Alpha #98: (rank(volume) - rank(correlation(rank(high), rank(volume), 5)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha098 尚未实现")

def calculateAlpha099():
    """Alpha #99: (rank(volume) - rank(correlation(rank(low), rank(volume), 5)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha099 尚未实现")

def calculateAlpha100():
    """Alpha #100: (rank(volume) - rank(correlation(rank(open), rank(volume), 10)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha100 尚未实现")

def calculateAlpha101():
    """Alpha #101: (rank(volume) - rank(correlation(rank(vwap), rank(volume), 5)))
    TODO: 实现此因子"""
    raise NotImplementedError("Alpha101 尚未实现")
