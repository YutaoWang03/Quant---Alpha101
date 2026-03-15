#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha #1 因子本地测试代码
Local Test for Alpha #1 Factor

使用模拟数据测试Alpha #1因子的计算和策略逻辑
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================================
# 辅助函数定义
# ============================================================================

def rank(df):
    """横截面排名"""
    return df.rank(axis=1, pct=True)

def ts_argmax(df, window):
    """时间序列最大值索引"""
    return df.rolling(window=int(window)).apply(lambda x: x.argmax(), raw=True)

def signed_power(df, exp):
    """带符号的幂运算"""
    return df.abs() ** exp * np.sign(df)

def alpha001(returns):
    """
    Alpha #1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)
    
    Args:
        returns: 收益率数据框
    
    Returns:
        Alpha #1因子值
    """
    # 计算20日标准差
    stddev_20 = returns.rolling(window=20).std()
    
    # 条件判断：returns < 0 时使用stddev，否则使用returns的绝对值
    condition = returns < 0
    power_input = np.where(condition, stddev_20, returns.abs())
    
    # 转换为DataFrame以保持索引和列名
    power_input_df = pd.DataFrame(power_input, index=returns.index, columns=returns.columns)
    
    # 计算SignedPower(power_input, 2)
    signed_power_result = signed_power(power_input_df, 2)
    
    # 计算Ts_ArgMax(..., 5)
    ts_argmax_result = ts_argmax(signed_power_result, 5)
    
    # 计算rank并减去0.5
    return rank(ts_argmax_result) - 0.5

# ============================================================================
# 数据生成函数
# ============================================================================

def generate_mock_data(n_stocks=50, n_days=100, start_date='2023-01-01'):
    """
    生成模拟股票数据
    
    Args:
        n_stocks: 股票数量
        n_days: 交易日数量
        start_date: 开始日期
    
    Returns:
        price_df: 价格数据框
        returns_df: 收益率数据框
    """
    # 生成日期序列
    dates = pd.date_range(start=start_date, periods=n_days, freq='D')
    
    # 生成股票代码
    stocks = [f'Stock_{i:03d}' for i in range(1, n_stocks + 1)]
    
    # 设置随机种子以便复现
    np.random.seed(42)
    
    # 生成价格数据
    price_data = {}
    for stock in stocks:
        # 初始价格
        base_price = np.random.uniform(10, 100)
        
        # 生成收益率序列（带有一定的自相关性）
        returns = []
        prev_return = 0
        
        for i in range(n_days):
            # 添加一些自相关性和异方差性
            volatility = 0.015 + 0.01 * abs(prev_return)  # 波动率聚集
            new_return = 0.7 * prev_return + np.random.normal(0, volatility)  # AR(1)过程
            returns.append(new_return)
            prev_return = new_return
        
        # 转换为价格序列
        prices = [base_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        price_data[stock] = prices
    
    # 创建DataFrame
    price_df = pd.DataFrame(price_data, index=dates)
    returns_df = price_df.pct_change().dropna()
    
    return price_df, returns_df

# ============================================================================
# 策略回测类
# ============================================================================

class Alpha001Strategy:
    """Alpha #1 因子策略回测"""
    
    def __init__(self, returns_df, top_n=10, rebalance_freq=5):
        """
        初始化策略
        
        Args:
            returns_df: 收益率数据框
            top_n: 选择的股票数量
            rebalance_freq: 调仓频率（天）
        """
        self.returns_df = returns_df
        self.top_n = top_n
        self.rebalance_freq = rebalance_freq
        self.portfolio_returns = []
        self.positions = {}
        self.trade_dates = []
        
    def calculate_factor(self, end_date):
        """计算指定日期的因子值"""
        # 获取截止到end_date的数据
        data_slice = self.returns_df.loc[:end_date]
        
        if len(data_slice) < 25:  # 需要足够的历史数据
            return None
        
        # 计算Alpha #1因子
        factor_values = alpha001(data_slice)
        
        if factor_values.empty:
            return None
        
        # 返回最新的因子值
        return factor_values.iloc[-1].dropna()
    
    def select_stocks(self, factor_values):
        """根据因子值选择股票"""
        if factor_values is None or len(factor_values) == 0:
            return []
        
        # 选择因子值最高的前N只股票
        top_stocks = factor_values.nlargest(self.top_n)
        return list(top_stocks.index)
    
    def backtest(self):
        """执行回测"""
        dates = self.returns_df.index[25:]  # 从第25天开始（确保有足够历史数据）
        
        current_positions = []
        portfolio_value = 1.0
        
        for i, date in enumerate(dates):
            # 检查是否需要调仓
            if i % self.rebalance_freq == 0:
                # 计算因子值
                factor_values = self.calculate_factor(date)
                
                # 选择股票
                new_positions = self.select_stocks(factor_values)
                
                if new_positions:
                    current_positions = new_positions
                    self.trade_dates.append(date)
                    print(f'{date.strftime("%Y-%m-%d")}: 调仓，选择 {len(current_positions)} 只股票')
            
            # 计算当日组合收益
            if current_positions:
                # 等权重组合
                daily_returns = self.returns_df.loc[date, current_positions]
                portfolio_return = daily_returns.mean()
                portfolio_value *= (1 + portfolio_return)
                self.portfolio_returns.append(portfolio_return)
            else:
                self.portfolio_returns.append(0)
        
        # 创建结果DataFrame
        self.results = pd.DataFrame({
            'date': dates,
            'portfolio_return': self.portfolio_returns,
            'cumulative_return': np.cumprod(1 + np.array(self.portfolio_returns))
        })
        
        return self.results
    
    def calculate_metrics(self):
        """计算策略指标"""
        if not hasattr(self, 'results'):
            print("请先运行回测")
            return None
        
        returns = np.array(self.portfolio_returns)
        
        # 基本指标
        total_return = self.results['cumulative_return'].iloc[-1] - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 最大回撤
        cumulative = self.results['cumulative_return']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 胜率
        win_rate = (returns > 0).mean()
        
        metrics = {
            '总收益率': f'{total_return:.2%}',
            '年化收益率': f'{annual_return:.2%}',
            '年化波动率': f'{volatility:.2%}',
            '夏普比率': f'{sharpe_ratio:.3f}',
            '最大回撤': f'{max_drawdown:.2%}',
            '胜率': f'{win_rate:.2%}',
            '交易次数': len(self.trade_dates)
        }
        
        return metrics
    
    def plot_results(self):
        """绘制回测结果"""
        if not hasattr(self, 'results'):
            print("请先运行回测")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 累积收益曲线
        ax1.plot(self.results['date'], self.results['cumulative_return'], 
                label='Alpha #1 策略', linewidth=2)
        ax1.set_title('Alpha #1 因子策略累积收益曲线', fontsize=14)
        ax1.set_ylabel('累积收益', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 日收益率分布
        ax2.hist(self.portfolio_returns, bins=50, alpha=0.7, edgecolor='black')
        ax2.set_title('日收益率分布', fontsize=14)
        ax2.set_xlabel('日收益率', fontsize=12)
        ax2.set_ylabel('频数', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()

# ============================================================================
# 主测试函数
# ============================================================================

def main():
    """主测试函数"""
    print("Alpha #1 因子本地测试")
    print("=" * 50)
    
    # 生成模拟数据
    print("1. 生成模拟数据...")
    price_df, returns_df = generate_mock_data(n_stocks=50, n_days=200)
    print(f"   数据维度: {returns_df.shape}")
    print(f"   日期范围: {returns_df.index[0]} 到 {returns_df.index[-1]}")
    
    # 测试因子计算
    print("\n2. 测试Alpha #1因子计算...")
    alpha1_values = alpha001(returns_df)
    print(f"   因子计算完成，结果维度: {alpha1_values.shape}")
    print(f"   最新因子值统计:")
    latest_factors = alpha1_values.iloc[-1].dropna()
    print(f"   - 均值: {latest_factors.mean():.4f}")
    print(f"   - 标准差: {latest_factors.std():.4f}")
    print(f"   - 最小值: {latest_factors.min():.4f}")
    print(f"   - 最大值: {latest_factors.max():.4f}")
    
    # 策略回测
    print("\n3. 执行策略回测...")
    strategy = Alpha001Strategy(returns_df, top_n=10, rebalance_freq=5)
    results = strategy.backtest()
    
    # 计算指标
    print("\n4. 策略表现指标:")
    metrics = strategy.calculate_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    # 绘制结果
    print("\n5. 绘制回测结果...")
    strategy.plot_results()
    
    # 因子分析
    print("\n6. 因子特性分析:")
    print("   - 因子类型: 短期反转因子")
    print("   - 调仓频率: 5个交易日")
    print("   - 选股数量: 10只股票")
    print("   - 权重分配: 等权重")
    
    # 保存结果
    results.to_csv('alpha001_backtest_results.csv', index=False)
    print("\n7. 回测结果已保存到 'alpha001_backtest_results.csv'")
    
    return strategy, results

if __name__ == "__main__":
    # 运行测试
    strategy, results = main()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n使用说明:")
    print("1. 本测试使用模拟数据，实际使用时请替换为真实股票数据")
    print("2. 在聚宽平台使用时，请参考 'jq_alpha001_strategy.py' 文件")
    print("3. 建议结合其他因子和风险管理措施使用")
    print("4. 定期验证因子有效性，必要时调整参数")