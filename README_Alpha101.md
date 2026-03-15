# Alpha101 因子库

## 文件结构

本项目已重构为模块化结构，便于维护和扩展：

### 1. `alpha_helpers.py` - 辅助函数模块
包含所有基础的时间序列操作和统计函数：

**时间序列操作：**
- `rank()` - 横截面排名
- `delay()` - 时间序列延迟
- `delta()` - 时间序列差分
- `ts_sum()` - 时间序列求和
- `ts_mean()` - 时间序列均值
- `ts_min()` - 时间序列最小值
- `ts_max()` - 时间序列最大值
- `ts_argmax()` - 时间序列最大值索引
- `ts_argmin()` - 时间序列最小值索引
- `ts_rank()` - 时间序列排名

**统计函数：**
- `correlation()` - 时间序列相关性
- `covariance()` - 时间序列协方差
- `scale()` - 缩放函数
- `decay_linear()` - 线性衰减加权移动平均
- `signed_power()` - 带符号的幂运算
- `indneutralize()` - 行业中性化

**基础指标：**
- `high_level()` - 当日价格高开程度
- `momentum_alpha()` - 动量Alpha

### 2. `alpha_factors.py` - 量化因子模块
包含所有101个Alpha因子的实现：
- `alpha001()` - `alpha016()` 已实现
- `alpha017()` - `alpha101()` 待继续添加

### 3. `alpha101_functions.py` - 主入口文件
为保持向后兼容性，此文件重新导出所有函数。
旧代码可以继续使用：
```python
from alpha101_functions import *
```

### 4. 测试文件
- `Alpha101 Learning.ipynb` - Jupyter notebook完整教程和测试
- `jq_alpha001_strategy.py` - 聚宽平台Alpha #1因子策略
- `alpha001_local_test.py` - 本地测试代码

## 使用方法

### 方法1：使用主入口文件（推荐，向后兼容）
```python
from alpha101_functions import *

# 使用辅助函数
result = rank(data)

# 使用Alpha因子
alpha1 = alpha001(returns)
alpha2 = alpha002(open_price, close, volume)
```

### 方法2：直接导入特定模块
```python
# 只导入辅助函数
from alpha_helpers import rank, delta, correlation

# 只导入Alpha因子
from alpha_factors import alpha001, alpha002

# 使用
result = alpha001(returns)
```

### 方法3：在Jupyter Notebook中使用
```python
# 导入所有函数
from alpha101_functions import *

# 或者分别导入
from alpha_helpers import *
from alpha_factors import *
```

## Alpha #1 因子测试

### 本地测试
```bash
python alpha001_local_test.py
```

### 聚宽平台测试
1. 将 `jq_alpha001_strategy.py` 内容复制到聚宽平台
2. 运行策略回测
3. 查看结果和指标

### Jupyter Notebook测试
打开 `Alpha101 Learning.ipynb`，运行相关单元格

## Alpha #1 因子说明

**因子公式：**
```
rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5
```

**因子逻辑：**
1. 当收益率为负时，使用20日收益率标准差
2. 当收益率为正时，使用收益率绝对值
3. 对上述值进行2次幂运算（保持符号）
4. 计算5日滚动窗口内的最大值位置
5. 对结果进行横截面排名并减去0.5

**因子特性：**
- 类型：短期反转因子
- 周期：5日
- 适用：高频交易和短期策略

## 优势

1. **功能分层**：辅助函数和量化因子分离，职责清晰
2. **易于维护**：修改辅助函数不影响因子实现
3. **便于扩展**：添加新因子只需修改 `alpha_factors.py`
4. **故障排查**：问题定位更快速准确
5. **向后兼容**：旧代码无需修改即可使用
6. **完整测试**：提供多种测试方式和示例

## 数据要求

所有函数接受 `pandas.DataFrame` 格式的数据，包括：
- `open_price` - 开盘价
- `close` - 收盘价
- `high` - 最高价
- `low` - 最低价
- `volume` - 成交量
- `vwap` - 成交量加权平均价
- `returns` - 收益率
- `adv20` - 20日平均成交量

## 类型注解

所有函数都包含完整的类型注解（Type Hints），支持IDE自动补全和类型检查。

## 文档

每个函数都包含详细的文档字符串（Docstrings），说明：
- 函数功能
- 参数说明
- 返回值说明

## 风险提示

1. 因子可能存在时效性，需要定期验证
2. 建议与其他因子组合使用
3. 注意控制交易成本和换手率
4. 测试数据为模拟数据，实际使用需要真实数据