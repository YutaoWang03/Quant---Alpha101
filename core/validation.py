"""
数据验证工具模块
提供统一的数据格式验证功能
"""

import pandas as pd
import numpy as np
from typing import Optional, List


def validateDataFormat(
    data: pd.DataFrame,
    param_name: str = "data",
    allow_nan: bool = False,
    min_length: Optional[int] = None
) -> None:
    """
    验证数据格式是否符合要求
    
    Args:
        data: 待验证的数据框
        param_name: 参数名称（用于错误提示）
        allow_nan: 是否允许空值（默认：False）
        min_length: 最小数据长度（可选）
    
    Raises:
        TypeError: 数据类型不正确
        ValueError: 数据格式不符合要求
    """
    # 检查是否为 DataFrame
    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            f"{param_name} 必须是 pandas DataFrame\n"
            f"当前类型: {type(data)}"
        )
    
    # 检查索引是否为日期格式
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError(
            f"{param_name} 的索引必须是 DatetimeIndex\n"
            f"当前类型: {type(data.index)}\n"
            f"提示: 使用 pd.to_datetime() 转换索引"
        )
    
    # 检查是否为空
    if data.empty:
        raise ValueError(f"{param_name} 为空数据框")
    
    # 检查最小长度
    if min_length is not None and len(data) < min_length:
        raise ValueError(
            f"{param_name} 的长度 ({len(data)}) 小于最小要求 ({min_length})"
        )
    
    # 检查是否有空值
    if not allow_nan and data.isnull().any().any():
        nan_count = data.isnull().sum().sum()
        raise ValueError(
            f"{param_name} 包含 {nan_count} 个空值\n"
            f"提示: 使用 fillna() 或 dropna() 处理缺失数据"
        )


def validateWindow(
    window: int,
    data_length: int,
    param_name: str = "window"
) -> None:
    """
    验证窗口参数是否合法
    
    Args:
        window: 窗口大小
        data_length: 数据长度
        param_name: 参数名称（用于错误提示）
    
    Raises:
        TypeError: 参数类型不正确
        ValueError: 参数值不合法
    """
    if not isinstance(window, int):
        raise TypeError(
            f"{param_name} 必须是整数\n"
            f"当前类型: {type(window)}"
        )
    
    if window <= 0:
        raise ValueError(
            f"{param_name} 必须大于 0\n"
            f"当前值: {window}"
        )
    
    if window > data_length:
        raise ValueError(
            f"{param_name} ({window}) 不能大于数据长度 ({data_length})"
        )


def validateShapeConsistency(
    data_list: List[pd.DataFrame],
    name_list: List[str]
) -> None:
    """
    验证多个数据框的形状是否一致
    
    Args:
        data_list: 数据框列表
        name_list: 数据框名称列表
    
    Raises:
        ValueError: 数据框形状不一致
    """
    if len(data_list) != len(name_list):
        raise ValueError("data_list 和 name_list 的长度必须相同")
    
    if len(data_list) < 2:
        return  # 少于2个数据框，无需验证
    
    # 获取第一个数据框的形状作为参考
    reference_shape = data_list[0].shape
    reference_name = name_list[0]
    
    # 检查其他数据框的形状
    for data, name in zip(data_list[1:], name_list[1:]):
        if data.shape != reference_shape:
            error_msg = f"数据框形状不一致:\n"
            for d, n in zip(data_list, name_list):
                error_msg += f"  {n}: {d.shape}\n"
            raise ValueError(error_msg)
