# Core 模块函数命名与编写规范

## 目录

1. [命名规范](#命名规范)
2. [数据格式规范](#数据格式规范)
3. [函数编写规范](#函数编写规范)
4. [文档规范](#文档规范)
5. [示例代码](#示例代码)

---

## 1. 命名规范

### 1.1 函数命名

**规则：所有函数使用小驼峰命名法（camelCase）**

```python
# ✅ 正确示例
def calculateAlpha001(returns: pd.DataFrame) -> pd.DataFrame:
    pass

def getTsRank(data: pd.DataFrame, window: int) -> pd.DataFrame:
    pass

def computeMovingAverage(prices: pd.DataFrame, period: int) -> pd.DataFrame:
    pass

# ❌ 错误示例
def calculate_alpha_001(returns):  # 不使用下划线命名
    pass

def GetTsRank(data, window):  # 不使用大驼峰命名
    pass
```

### 1.2 变量命名

**规则：变量使用小驼峰命名法，常量使用全大写**

```python
# ✅ 正确示例
closePrice = df['close']
movingAverage = calculateMovingAverage(closePrice, 20)
MAX_WINDOW_SIZE = 252

# ❌ 错误示例
close_price = df['close']  # 不使用下划线
MovingAverage = calculate_moving_average(close_price, 20)  # 不使用大驼峰
```

### 1.3 参数命名

**规则：参数名称要清晰明确，避免缩写**

```python
# ✅ 正确示例
def calculateCorrelation(
    firstSeries: pd.DataFrame,
    secondSeries: pd.DataFrame,
    window: int
) -> pd.DataFrame:
    pass

# ❌ 错误示例
def calculateCorrelation(x, y, w):  # 参数名不清晰
    pass
```

---

## 2. 数据格式规范

### 2.1 输入数据格式

**规则：所有函数输入必须是 pandas DataFrame 或 Series，索引为日期格式**

**标准数据格式：**

```python
# DataFrame 格式（面板数据）
# 索引：日期（pd.DatetimeIndex）
# 列：股票代码
# 值：价格/成交量/因子值等

import pandas as pd

# ✅ 正确的数据格式
data = pd.DataFrame({
    'sh.601398': [10.5, 10.6, 10.7],
    'sh.601288': [5.2, 5.3, 5.4]
}, index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']))

print(data.index)  # DatetimeIndex(['2023-01-01', '2023-01-02', '2023-01-03'])
print(type(data.index))  # <class 'pandas.core.indexes.datetimes.DatetimeIndex'>

# ❌ 错误的数据格式
data_wrong = pd.DataFrame({
    'sh.601398': [10.5, 10.6, 10.7],
    'sh.601288': [5.2, 5.3, 5.4]
}, index=[0, 1, 2])  # 索引不是日期格式
```

### 2.2 数据验证

**规则：函数开始时必须验证输入数据格式**

```python
def validateDataFormat(data: pd.DataFrame, paramName: str = "data") -> None:
    """
    验证数据格式是否符合要求
    
    Args:
        data: 待验证的数据框
        paramName: 参数名称（用于错误提示）
    
    Raises:
        TypeError: 数据类型不正确
        ValueError: 数据格式不符合要求
    """
    # 检查是否为 DataFrame
    if not isinstance(data, pd.DataFrame):
        raise TypeError(f"{paramName} 必须是 pandas DataFrame，当前类型: {type(data)}")
    
    # 检查索引是否为日期格式
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError(f"{paramName} 的索引必须是 DatetimeIndex，当前类型: {type(data.index)}")
    
    # 检查是否有空值
    if data.isnull().any().any():
        raise ValueError(f"{paramName} 包含空值，请先处理缺失数据")
    
    # 检查是否为空
    if data.empty:
        raise ValueError(f"{paramName} 为空数据框")
```

### 2.3 使用数据验证

```python
def calculateAlpha001(returns: pd.DataFrame) -> pd.DataFrame:
    """
    计算 Alpha001 因子
    
    Args:
        returns: 收益率数据框（索引为日期，列为股票代码）
    
    Returns:
        Alpha001 因子值
    """
    # 第一步：验证数据格式
    validateDataFormat(returns, "returns")
    
    # 第二步：执行计算
    result = rank(tsArgmax(signedPower(returns, 2), 5)) - 0.5
    
    return result
```

---

## 3. 函数编写规范

### 3.1 函数结构

**标准函数结构：**

```python
def functionName(
    param1: pd.DataFrame,
    param2: int,
    param3: float = 1.0
) -> pd.DataFrame:
    """
    函数功能简述（一句话）
    
    详细说明（可选）：
    - 说明1
    - 说明2
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        param3: 参数3说明（默认值：1.0）
    
    Returns:
        返回值说明
    
    Raises:
        TypeError: 类型错误说明
        ValueError: 值错误说明
    
    Examples:
        >>> data = pd.DataFrame(...)
        >>> result = functionName(data, 10)
    """
    # 1. 数据验证
    validateDataFormat(param1, "param1")
    
    # 2. 参数验证
    if param2 <= 0:
        raise ValueError("param2 必须大于 0")
    
    # 3. 执行计算
    result = ...
    
    # 4. 返回结果
    return result
```

### 3.2 类型注解

**规则：所有函数必须包含完整的类型注解**

```python
from typing import Union, Optional, List, Tuple

# ✅ 正确示例
def calculateMovingAverage(
    data: pd.DataFrame,
    window: int,
    minPeriods: Optional[int] = None
) -> pd.DataFrame:
    pass

def getRankPercentile(
    data: pd.DataFrame,
    axis: int = 1
) -> pd.DataFrame:
    pass

def computeMultipleFactors(
    closePrice: pd.DataFrame,
    volume: pd.DataFrame,
    windows: List[int]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    pass

# ❌ 错误示例
def calculateMovingAverage(data, window, minPeriods=None):  # 缺少类型注解
    pass
```

### 3.3 错误处理

**规则：使用明确的异常类型和清晰的错误信息**

```python
def calculateRollingCorrelation(
    x: pd.DataFrame,
    y: pd.DataFrame,
    window: int
) -> pd.DataFrame:
    """计算滚动相关系数"""
    
    # 验证数据格式
    validateDataFormat(x, "x")
    validateDataFormat(y, "y")
    
    # 验证参数
    if window <= 0:
        raise ValueError(f"window 必须大于 0，当前值: {window}")
    
    if window > len(x):
        raise ValueError(f"window ({window}) 不能大于数据长度 ({len(x)})")
    
    # 验证数据形状
    if x.shape != y.shape:
        raise ValueError(f"x 和 y 的形状必须相同，x: {x.shape}, y: {y.shape}")
    
    # 执行计算
    try:
        result = x.rolling(window=window).corr(y)
    except Exception as e:
        raise RuntimeError(f"计算滚动相关系数时出错: {str(e)}")
    
    return result
```

### 3.4 性能优化

**规则：优先使用向量化操作，避免循环**

```python
# ✅ 正确示例（向量化）
def calculateReturns(prices: pd.DataFrame) -> pd.DataFrame:
    """计算收益率"""
    validateDataFormat(prices, "prices")
    return prices.pct_change()

# ❌ 错误示例（循环）
def calculateReturns(prices: pd.DataFrame) -> pd.DataFrame:
    """计算收益率"""
    validateDataFormat(prices, "prices")
    result = pd.DataFrame(index=prices.index, columns=prices.columns)
    for col in prices.columns:
        for i in range(1, len(prices)):
            result.iloc[i, result.columns.get_loc(col)] = \
                (prices.iloc[i, prices.columns.get_loc(col)] - 
                 prices.iloc[i-1, prices.columns.get_loc(col)]) / \
                prices.iloc[i-1, prices.columns.get_loc(col)]
    return result
```

---

## 4. 文档规范

### 4.1 Docstring 格式

**规则：使用 Google 风格的 docstring**

```python
def calculateAlpha001(
    returns: pd.DataFrame,
    window: int = 5
) -> pd.DataFrame:
    """
    计算 Alpha001 因子
    
    Alpha001 公式：
    rank(Ts_ArgMax(SignedPower(returns, 2), window)) - 0.5
    
    该因子捕捉价格动量的非线性特征，通过对收益率进行幂运算
    并在时间窗口内寻找最大值位置来识别趋势强度。
    
    Args:
        returns: 收益率数据框
            - 索引：日期（DatetimeIndex）
            - 列：股票代码
            - 值：日收益率
        window: 时间窗口大小（默认：5）
            - 必须大于 0
            - 建议范围：3-20
    
    Returns:
        Alpha001 因子值数据框
            - 索引：日期（与输入相同）
            - 列：股票代码（与输入相同）
            - 值：因子值，范围 [-0.5, 0.5]
    
    Raises:
        TypeError: 输入数据类型不正确
        ValueError: 参数值不合法或数据格式不符合要求
    
    Examples:
        >>> from data import DataAPI
        >>> with DataAPI() as api:
        ...     prices = api.get_panel_data(['sh.601398', 'sh.601288'], field='close')
        ...     returns = prices.pct_change()
        ...     alpha001 = calculateAlpha001(returns, window=5)
        >>> print(alpha001.head())
    
    Notes:
        - 该因子对异常值敏感，建议先进行数据清洗
        - 窗口期越长，因子越平滑但滞后性越强
        - 建议与其他因子组合使用
    
    References:
        - 101 Formulaic Alphas, Zura Kakushadze (2015)
    """
    # 实现代码...
    pass
```

### 4.2 注释规范

**规则：关键步骤必须添加注释**

```python
def calculateComplexFactor(
    closePrice: pd.DataFrame,
    volume: pd.DataFrame,
    window: int = 20
) -> pd.DataFrame:
    """计算复杂因子"""
    
    # 1. 数据验证
    validateDataFormat(closePrice, "closePrice")
    validateDataFormat(volume, "volume")
    
    # 2. 计算价格动量
    # 使用对数收益率以保持数值稳定性
    logReturns = np.log(closePrice / closePrice.shift(1))
    
    # 3. 计算成交量变化率
    # 标准化成交量以消除量纲影响
    volumeChange = volume.pct_change()
    normalizedVolume = (volumeChange - volumeChange.mean()) / volumeChange.std()
    
    # 4. 计算滚动相关性
    # 窗口期内价格动量与成交量的相关性
    correlation = logReturns.rolling(window=window).corr(normalizedVolume)
    
    # 5. 横截面标准化
    # 每个时间点对所有股票进行排名
    rankedFactor = correlation.rank(axis=1, pct=True)
    
    # 6. 中心化处理
    # 减去 0.5 使因子值中心为 0
    finalFactor = rankedFactor - 0.5
    
    return finalFactor
```

---

## 5. 示例代码

### 5.1 完整的辅助函数示例

```python
def tsRank(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    时间序列排名
    
    计算滚动窗口内每个值的百分位排名。
    
    Args:
        data: 输入数据框
            - 索引：日期（DatetimeIndex）
            - 列：股票代码
            - 值：待排名的数值
        window: 滚动窗口大小
            - 必须大于 0
            - 必须小于等于数据长度
    
    Returns:
        排名结果数据框
            - 索引：日期（与输入相同）
            - 列：股票代码（与输入相同）
            - 值：百分位排名，范围 [0, 1]
    
    Raises:
        TypeError: 输入数据类型不正确
        ValueError: 参数值不合法
    
    Examples:
        >>> data = pd.DataFrame({
        ...     'stock1': [1, 2, 3, 4, 5],
        ...     'stock2': [5, 4, 3, 2, 1]
        ... }, index=pd.date_range('2023-01-01', periods=5))
        >>> result = tsRank(data, window=3)
        >>> print(result)
    """
    # 1. 数据验证
    validateDataFormat(data, "data")
    
    # 2. 参数验证
    if not isinstance(window, int):
        raise TypeError(f"window 必须是整数，当前类型: {type(window)}")
    
    if window <= 0:
        raise ValueError(f"window 必须大于 0，当前值: {window}")
    
    if window > len(data):
        raise ValueError(
            f"window ({window}) 不能大于数据长度 ({len(data)})"
        )
    
    # 3. 执行计算
    # 使用 rolling + apply 计算滚动窗口内的排名
    result = data.rolling(window=window).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1],
        raw=False
    )
    
    return result
```

### 5.2 完整的因子函数示例

```python
def calculateAlpha002(
    openPrice: pd.DataFrame,
    closePrice: pd.DataFrame,
    volume: pd.DataFrame
) -> pd.DataFrame:
    """
    计算 Alpha002 因子
    
    Alpha002 公式：
    -1 * correlation(rank(delta(log(volume), 2)), rank((close - open) / open), 6)
    
    该因子通过成交量变化与价格变化的相关性来捕捉市场情绪。
    
    Args:
        openPrice: 开盘价数据框
            - 索引：日期（DatetimeIndex）
            - 列：股票代码
            - 值：开盘价
        closePrice: 收盘价数据框
            - 索引：日期（DatetimeIndex）
            - 列：股票代码
            - 值：收盘价
        volume: 成交量数据框
            - 索引：日期（DatetimeIndex）
            - 列：股票代码
            - 值：成交量
    
    Returns:
        Alpha002 因子值数据框
            - 索引：日期（与输入相同）
            - 列：股票代码（与输入相同）
            - 值：因子值，范围 [-1, 1]
    
    Raises:
        TypeError: 输入数据类型不正确
        ValueError: 数据格式不符合要求
    
    Examples:
        >>> from data import DataAPI
        >>> with DataAPI() as api:
        ...     codes = ['sh.601398', 'sh.601288']
        ...     openPrice = api.get_panel_data(codes, field='open')
        ...     closePrice = api.get_panel_data(codes, field='close')
        ...     volume = api.get_panel_data(codes, field='volume')
        ...     alpha002 = calculateAlpha002(openPrice, closePrice, volume)
    """
    # 1. 数据验证
    validateDataFormat(openPrice, "openPrice")
    validateDataFormat(closePrice, "closePrice")
    validateDataFormat(volume, "volume")
    
    # 2. 验证数据形状一致性
    if not (openPrice.shape == closePrice.shape == volume.shape):
        raise ValueError(
            f"所有输入数据的形状必须相同\n"
            f"openPrice: {openPrice.shape}\n"
            f"closePrice: {closePrice.shape}\n"
            f"volume: {volume.shape}"
        )
    
    # 3. 计算成交量变化
    # 使用对数差分计算成交量变化率
    logVolume = np.log(volume)
    volumeDelta = delta(logVolume, 2)
    
    # 4. 计算价格变化率
    # 计算日内收益率（收盘价相对开盘价的变化）
    priceChange = (closePrice - openPrice) / openPrice
    
    # 5. 横截面排名
    # 对每个时间点的所有股票进行排名
    rankedVolumeDelta = rank(volumeDelta)
    rankedPriceChange = rank(priceChange)
    
    # 6. 计算滚动相关性
    # 6天窗口内的相关系数
    corr = correlation(rankedVolumeDelta, rankedPriceChange, 6)
    
    # 7. 取负值
    # 负相关表示反向关系
    alpha002 = -1 * corr
    
    return alpha002
```

### 5.3 数据验证工具函数

```python
"""
数据验证工具模块
提供统一的数据格式验证功能
"""

import pandas as pd
import numpy as np
from typing import Optional, List


def validateDataFormat(
    data: pd.DataFrame,
    paramName: str = "data",
    allowNaN: bool = False,
    minLength: Optional[int] = None
) -> None:
    """
    验证数据格式是否符合要求
    
    Args:
        data: 待验证的数据框
        paramName: 参数名称（用于错误提示）
        allowNaN: 是否允许空值（默认：False）
        minLength: 最小数据长度（可选）
    
    Raises:
        TypeError: 数据类型不正确
        ValueError: 数据格式不符合要求
    """
    # 检查是否为 DataFrame
    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            f"{paramName} 必须是 pandas DataFrame\n"
            f"当前类型: {type(data)}"
        )
    
    # 检查索引是否为日期格式
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError(
            f"{paramName} 的索引必须是 DatetimeIndex\n"
            f"当前类型: {type(data.index)}\n"
            f"提示: 使用 pd.to_datetime() 转换索引"
        )
    
    # 检查是否为空
    if data.empty:
        raise ValueError(f"{paramName} 为空数据框")
    
    # 检查最小长度
    if minLength is not None and len(data) < minLength:
        raise ValueError(
            f"{paramName} 的长度 ({len(data)}) 小于最小要求 ({minLength})"
        )
    
    # 检查是否有空值
    if not allowNaN and data.isnull().any().any():
        nanCount = data.isnull().sum().sum()
        raise ValueError(
            f"{paramName} 包含 {nanCount} 个空值\n"
            f"提示: 使用 fillna() 或 dropna() 处理缺失数据"
        )


def validateWindow(
    window: int,
    dataLength: int,
    paramName: str = "window"
) -> None:
    """
    验证窗口参数是否合法
    
    Args:
        window: 窗口大小
        dataLength: 数据长度
        paramName: 参数名称（用于错误提示）
    
    Raises:
        TypeError: 参数类型不正确
        ValueError: 参数值不合法
    """
    if not isinstance(window, int):
        raise TypeError(
            f"{paramName} 必须是整数\n"
            f"当前类型: {type(window)}"
        )
    
    if window <= 0:
        raise ValueError(
            f"{paramName} 必须大于 0\n"
            f"当前值: {window}"
        )
    
    if window > dataLength:
        raise ValueError(
            f"{paramName} ({window}) 不能大于数据长度 ({dataLength})"
        )


def validateShapeConsistency(
    dataList: List[pd.DataFrame],
    nameList: List[str]
) -> None:
    """
    验证多个数据框的形状是否一致
    
    Args:
        dataList: 数据框列表
        nameList: 数据框名称列表
    
    Raises:
        ValueError: 数据框形状不一致
    """
    if len(dataList) != len(nameList):
        raise ValueError("dataList 和 nameList 的长度必须相同")
    
    if len(dataList) < 2:
        return  # 少于2个数据框，无需验证
    
    # 获取第一个数据框的形状作为参考
    referenceShape = dataList[0].shape
    referenceName = nameList[0]
    
    # 检查其他数据框的形状
    for data, name in zip(dataList[1:], nameList[1:]):
        if data.shape != referenceShape:
            errorMsg = f"数据框形状不一致:\n"
            for d, n in zip(dataList, nameList):
                errorMsg += f"  {n}: {d.shape}\n"
            raise ValueError(errorMsg)
```

---

## 6. 最佳实践

### 6.1 函数设计原则

1. **单一职责原则**：每个函数只做一件事
2. **输入验证**：始终验证输入数据的格式和参数的合法性
3. **向量化优先**：优先使用 pandas/numpy 的向量化操作
4. **清晰命名**：函数名和变量名要清晰表达其含义
5. **完整文档**：提供完整的 docstring 和类型注解

### 6.2 代码组织

```python
# 文件结构示例
"""
core/
├── __init__.py              # 模块初始化
├── functions_rule.md        # 本规范文档
├── validation.py            # 数据验证工具
├── alpha_helpers.py         # 辅助函数
├── alpha_factors.py         # Alpha 因子
└── alpha101_functions.py    # 主入口（向后兼容）
```

### 6.3 导入规范

```python
# ✅ 正确的导入方式
import pandas as pd
import numpy as np
from typing import Union, Optional, List, Tuple

from .validation import validateDataFormat, validateWindow
from .alpha_helpers import rank, delay, delta, tsSum

# ❌ 错误的导入方式
from pandas import *  # 不使用 * 导入
import pandas  # 不省略别名
```

### 6.4 测试规范

**每个函数都应该有对应的单元测试**

```python
# test/test_alpha_helpers.py
import pytest
import pandas as pd
import numpy as np
from core.alpha_helpers import tsRank

def test_tsRank_basic():
    """测试 tsRank 基本功能"""
    # 准备测试数据
    data = pd.DataFrame({
        'stock1': [1, 2, 3, 4, 5],
        'stock2': [5, 4, 3, 2, 1]
    }, index=pd.date_range('2023-01-01', periods=5))
    
    # 执行函数
    result = tsRank(data, window=3)
    
    # 验证结果
    assert isinstance(result, pd.DataFrame)
    assert result.shape == data.shape
    assert isinstance(result.index, pd.DatetimeIndex)

def test_tsRank_invalid_input():
    """测试 tsRank 异常处理"""
    # 测试非 DataFrame 输入
    with pytest.raises(TypeError):
        tsRank([1, 2, 3], window=2)
    
    # 测试无效窗口
    data = pd.DataFrame({'a': [1, 2, 3]}, 
                       index=pd.date_range('2023-01-01', periods=3))
    with pytest.raises(ValueError):
        tsRank(data, window=0)
```

---

## 7. 常见错误与解决方案

### 7.1 索引不是日期格式

```python
# ❌ 错误
data = pd.DataFrame({'price': [100, 101, 102]})
result = calculateAlpha001(data)  # 报错：索引不是 DatetimeIndex

# ✅ 正确
data = pd.DataFrame(
    {'price': [100, 101, 102]},
    index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])
)
result = calculateAlpha001(data)
```

### 7.2 数据包含空值

```python
# ❌ 错误
data = pd.DataFrame({'price': [100, np.nan, 102]}, 
                   index=pd.date_range('2023-01-01', periods=3))
result = calculateAlpha001(data)  # 报错：包含空值

# ✅ 正确
data = pd.DataFrame({'price': [100, np.nan, 102]}, 
                   index=pd.date_range('2023-01-01', periods=3))
data = data.fillna(method='ffill')  # 前向填充
result = calculateAlpha001(data)
```

### 7.3 窗口期过大

```python
# ❌ 错误
data = pd.DataFrame({'price': [100, 101, 102]}, 
                   index=pd.date_range('2023-01-01', periods=3))
result = tsRank(data, window=10)  # 报错：窗口大于数据长度

# ✅ 正确
data = pd.DataFrame({'price': [100, 101, 102]}, 
                   index=pd.date_range('2023-01-01', periods=3))
result = tsRank(data, window=2)  # 使用合适的窗口
```

---

## 8. 版本历史

- v1.0.0 (2026-03-15): 初始版本
  - 定义基本命名规范
  - 定义数据格式规范
  - 定义函数编写规范
  - 提供完整示例代码

---

## 9. 参考资料

- [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [NumPy Documentation](https://numpy.org/doc/)
- 101 Formulaic Alphas, Zura Kakushadze (2015)

---

**注意**：本规范是强制性的，所有 core 模块的代码都必须遵循此规范。
