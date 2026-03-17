#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha #1 因子测试 - 使用Baostock数据源
Test Alpha #1 Factor with Baostock Data Source

使用baostock获取真实股票数据，测试Alpha #1因子的计算和有效性
"""

import baostock as bs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================================
# 辅助函数定义
# ============================================================================

def rank(df):
    """横截面排名"""
    return df.rank(axis=1, pct=True)

def tsArgmax(df, window):
    """时间序列最大值索引"""
    return df.rolling(window=int(window)).apply(lambda x: x.argmax(), raw=True)

def signedPower(df, exp):
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
    signed_power_result = signedPower(power_input_df, 2)
    
    # 计算Ts_ArgMax(..., 5)
    ts_argmax_result = tsArgmax(signed_power_result, 5)
    
    # 计算rank并减去0.5
    return rank(ts_argmax_result) - 0.5

# ============================================================================
# 数据获取函数
# ============================================================================

class BaostockDataLoader:
    """Baostock数据加载器"""
    
    def __init__(self):
        """初始化并登录baostock"""
        print("正在连接baostock...")
        login_result = bs.login()
        if login_result.error_code != '0':
            raise Exception(f"baostock登录失败: {login_result.error_msg}")
        print("baostock连接成功")
    
    def __del__(self):
        """析构函数，登出baostock"""
        bs.logout()
    
    def get_stock_list(self, index_code='sz.399300'):
        """
        获取指数成分股列表
        
        Args:
            index_code: 指数代码，默认为沪深300
        
        Returns:
            股票代码列表
        """
        print(f"获取{index_code}成分股...")
        
        # 获取指数成分股
        rs = bs.query_sz50_stocks()
        if index_code == 'sh.000300':  # 沪深300
            rs = bs.query_hs300_stocks()
        elif index_code == 'sz.399006':  # 创业板指
            rs = bs.query_zz500_stocks()
        
        stock_list = []
        while (rs.error_code == '0') & rs.next():
            stock_list.append(rs.get_row_data()[1])  # 获取股票代码
        
        print(f"获取到 {len(stock_list)} 只成分股")
        return stock_list[:50]  # 限制为前50只股票以提高速度
    
    def get_stock_data(self, stock_code, start_date, end_date):
        """
        获取单只股票的历史数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            股票数据DataFrame
        """
        rs = bs.query_history_k_data_plus(
            stock_code,
            "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"  # 后复权
        )
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 数据类型转换
        numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 过滤掉停牌和ST股票的数据
        df = df[df['tradestatus'] == '1']  # 正常交易
        df = df[df['isST'] == '0']  # 非ST股票
        
        return df
    
    def get_multiple_stocks_data(self, stock_list, start_date, end_date, max_stocks=30):
        """
        获取多只股票的历史数据
        
        Args:
            stock_list: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            max_stocks: 最大股票数量
        
        Returns:
            价格数据字典 {字段: DataFrame}
        """
        print(f"开始获取 {min(len(stock_list), max_stocks)} 只股票的历史数据...")
        
        price_data = {'open': {}, 'high': {}, 'low': {}, 'close': {}, 'volume': {}}
        successful_stocks = []
        
        for i, stock_code in enumerate(stock_list[:max_stocks]):
            try:
                print(f"获取 {stock_code} 数据... ({i+1}/{min(len(stock_list), max_stocks)})")
                
                stock_data = self.get_stock_data(stock_code, start_date, end_date)
                
                if len(stock_data) > 50:  # 确保有足够的数据
                    for field in price_data.keys():
                        if field in stock_data.columns:
                            price_data[field][stock_code] = stock_data[field]
                    successful_stocks.append(stock_code)
                else:
                    print(f"  {stock_code} 数据不足，跳过")
                    
            except Exception as e:
                print(f"  获取 {stock_code} 数据失败: {str(e)}")
                continue
        
        print(f"成功获取 {len(successful_stocks)} 只股票的数据")
        
        # 转换为DataFrame
        result = {}
        for field, data_dict in price_data.items():
            if data_dict:
                result[field] = pd.DataFrame(data_dict)
        
        return result, successful_stocks

# ============================================================================
# Alpha #1 因子测试类
# ============================================================================

class Alpha001Tester:
    """Alpha #1 因子测试器"""
    
    def __init__(self, start_date='2023-01-01', end_date='2024-01-01'):
        """
        初始化测试器
        
        Args:
            start_date: 测试开始日期
            end_date: 测试结束日期
        """
        self.start_date = start_date
        self.end_date = end_date
        self.data_loader = BaostockDataLoader()
        self.price_data = None
        self.returns_data = None
        self.factor_values = None
        
    def load_data(self, max_stocks=30):
        """加载股票数据"""
        print("=" * 60)
        print("开始加载数据...")
        
        # 获取股票列表
        stock_list = self.data_loader.get_stock_list('sh.000300')  # 沪深300
        
        # 获取股票数据
        self.price_data, self.successful_stocks = self.data_loader.get_multiple_stocks_data(
            stock_list, self.start_date, self.end_date, max_stocks
        )
        
        if not self.price_data or 'close' not in self.price_data:
            raise Exception("未能获取到有效的价格数据")
        
        # 计算收益率
        close_prices = self.price_data['close']
        self.returns_data = close_prices.pct_change().dropna()
        
        print(f"数据加载完成:")
        print(f"  股票数量: {len(self.successful_stocks)}")
        print(f"  数据日期范围: {self.returns_data.index[0]} 到 {self.returns_data.index[-1]}")
        print(f"  数据维度: {self.returns_data.shape}")
        
    def calculate_factor(self):
        """计算Alpha #1因子"""
        print("\n" + "=" * 60)
        print("开始计算Alpha #1因子...")
        
        if self.returns_data is None:
            raise Exception("请先加载数据")
        
        # 计算Alpha #1因子
        self.factor_values = alpha001(self.returns_data)
        
        print(f"因子计算完成:")
        print(f"  因子数据维度: {self.factor_values.shape}")
        print(f"  有效因子值数量: {self.factor_values.count().sum()}")
        
        # 显示最新因子值统计
        latest_factors = self.factor_values.iloc[-1].dropna()
        if len(latest_factors) > 0:
            print(f"  最新因子值统计:")
            print(f"    均值: {latest_factors.mean():.4f}")
            print(f"    标准差: {latest_factors.std():.4f}")
            print(f"    最小值: {latest_factors.min():.4f}")
            print(f"    最大值: {latest_factors.max():.4f}")
            
            # 显示因子值最高和最低的股票
            top_stocks = latest_factors.nlargest(5)
            bottom_stocks = latest_factors.nsmallest(5)
            
            print(f"  因子值最高的5只股票:")
            for stock, value in top_stocks.items():
                print(f"    {stock}: {value:.4f}")
            
            print(f"  因子值最低的5只股票:")
            for stock, value in bottom_stocks.items():
                print(f"    {stock}: {value:.4f}")
    
    def backtest_strategy(self, top_n=10, rebalance_freq=5):
        """
        回测Alpha #1因子策略
        
        Args:
            top_n: 选择的股票数量
            rebalance_freq: 调仓频率（天）
        """
        print(f"\n" + "=" * 60)
        print(f"开始回测策略 (选股数量: {top_n}, 调仓频率: {rebalance_freq}天)...")
        
        if self.factor_values is None:
            raise Exception("请先计算因子")
        
        # 获取有效的交易日期
        valid_dates = self.factor_values.dropna(how='all').index[25:]  # 确保有足够历史数据
        
        portfolio_returns = []
        positions_history = []
        current_positions = []
        
        for i, date in enumerate(valid_dates):
            # 检查是否需要调仓
            if i % rebalance_freq == 0:
                # 获取当日因子值
                daily_factors = self.factor_values.loc[date].dropna()
                
                if len(daily_factors) >= top_n:
                    # 选择因子值最高的股票
                    top_stocks = daily_factors.nlargest(top_n)
                    current_positions = list(top_stocks.index)
                    positions_history.append((date, current_positions.copy()))
            
            # 计算当日组合收益
            if current_positions and date in self.returns_data.index:
                # 等权重组合收益
                daily_returns = self.returns_data.loc[date, current_positions]
                valid_returns = daily_returns.dropna()
                
                if len(valid_returns) > 0:
                    portfolio_return = valid_returns.mean()
                    portfolio_returns.append(portfolio_return)
                else:
                    portfolio_returns.append(0)
            else:
                portfolio_returns.append(0)
        
        # 计算策略指标
        portfolio_returns = np.array(portfolio_returns)
        
        # 基本指标
        total_return = np.prod(1 + portfolio_returns) - 1
        annual_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        volatility = np.std(portfolio_returns) * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 最大回撤
        cumulative_returns = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # 胜率
        win_rate = np.mean(portfolio_returns > 0)
        
        # 基准收益（等权重所有股票）
        benchmark_returns = self.returns_data.loc[valid_dates].mean(axis=1)
        benchmark_total_return = np.prod(1 + benchmark_returns) - 1
        benchmark_annual_return = (1 + benchmark_total_return) ** (252 / len(benchmark_returns)) - 1
        
        print(f"回测结果:")
        print(f"  总收益率: {total_return:.2%}")
        print(f"  年化收益率: {annual_return:.2%}")
        print(f"  年化波动率: {volatility:.2%}")
        print(f"  夏普比率: {sharpe_ratio:.3f}")
        print(f"  最大回撤: {max_drawdown:.2%}")
        print(f"  胜率: {win_rate:.2%}")
        print(f"  调仓次数: {len(positions_history)}")
        print(f"  基准年化收益率: {benchmark_annual_return:.2%}")
        print(f"  超额收益: {annual_return - benchmark_annual_return:.2%}")
        
        # 保存结果
        self.backtest_results = {
            'dates': valid_dates,
            'portfolio_returns': portfolio_returns,
            'cumulative_returns': cumulative_returns,
            'benchmark_returns': benchmark_returns.values,
            'positions_history': positions_history,
            'metrics': {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'excess_return': annual_return - benchmark_annual_return
            }
        }
        
        return self.backtest_results
    
    def plot_results(self):
        """绘制回测结果"""
        if not hasattr(self, 'backtest_results'):
            print("请先运行回测")
            return
        
        results = self.backtest_results
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 累积收益曲线
        benchmark_cumulative = np.cumprod(1 + results['benchmark_returns'])
        
        ax1.plot(results['dates'], results['cumulative_returns'], 
                label='Alpha #1 策略', linewidth=2, color='red')
        ax1.plot(results['dates'], benchmark_cumulative, 
                label='基准(等权重)', linewidth=2, color='blue', alpha=0.7)
        ax1.set_title('累积收益曲线对比', fontsize=14)
        ax1.set_ylabel('累积收益', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 日收益率分布
        ax2.hist(results['portfolio_returns'], bins=50, alpha=0.7, 
                edgecolor='black', label='策略收益率')
        ax2.hist(results['benchmark_returns'], bins=50, alpha=0.5, 
                edgecolor='black', label='基准收益率')
        ax2.set_title('日收益率分布对比', fontsize=14)
        ax2.set_xlabel('日收益率', fontsize=12)
        ax2.set_ylabel('频数', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 回撤曲线
        running_max = np.maximum.accumulate(results['cumulative_returns'])
        drawdown = (results['cumulative_returns'] - running_max) / running_max
        
        ax3.fill_between(results['dates'], drawdown, 0, alpha=0.3, color='red')
        ax3.plot(results['dates'], drawdown, color='red', linewidth=1)
        ax3.set_title('回撤曲线', fontsize=14)
        ax3.set_ylabel('回撤', fontsize=12)
        ax3.grid(True, alpha=0.3)
        
        # 4. 滚动夏普比率
        window = 60  # 60日滚动窗口
        if len(results['portfolio_returns']) > window:
            rolling_sharpe = []
            for i in range(window, len(results['portfolio_returns'])):
                window_returns = results['portfolio_returns'][i-window:i]
                if np.std(window_returns) > 0:
                    sharpe = np.mean(window_returns) / np.std(window_returns) * np.sqrt(252)
                    rolling_sharpe.append(sharpe)
                else:
                    rolling_sharpe.append(0)
            
            ax4.plot(results['dates'][window:], rolling_sharpe, linewidth=2)
            ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax4.set_title(f'{window}日滚动夏普比率', fontsize=14)
            ax4.set_ylabel('夏普比率', fontsize=12)
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def save_results(self, filename='alpha001_test_results.csv'):
        """保存测试结果"""
        if hasattr(self, 'backtest_results'):
            results_df = pd.DataFrame({
                'date': self.backtest_results['dates'],
                'portfolio_return': self.backtest_results['portfolio_returns'],
                'cumulative_return': self.backtest_results['cumulative_returns'],
                'benchmark_return': self.backtest_results['benchmark_returns']
            })
            results_df.to_csv(filename, index=False)
            print(f"结果已保存到 {filename}")

# ============================================================================
# 主测试函数
# ============================================================================

def main():
    """主测试函数"""
    print("Alpha #1 因子测试 - Baostock数据源")
    print("=" * 60)
    
    try:
        # 创建测试器
        tester = Alpha001Tester(
            start_date='2023-01-01',
            end_date='2024-01-01'
        )
        
        # 加载数据
        tester.load_data(max_stocks=30)
        
        # 计算因子
        tester.calculate_factor()
        
        # 回测策略
        results = tester.backtest_strategy(top_n=10, rebalance_freq=5)
        
        # 绘制结果
        tester.plot_results()
        
        # 保存结果
        tester.save_results()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        
        return tester
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 运行测试
    tester = main()
    
    if tester:
        print("\n使用说明:")
        print("1. 本测试使用baostock获取真实股票数据")
        print("2. 测试了Alpha #1因子在沪深300成分股上的表现")
        print("3. 结果已保存到CSV文件，图表显示了策略表现")
        print("4. 可以调整参数重新测试不同的配置")
        
        # 提供交互式测试选项
        while True:
            print("\n" + "=" * 40)
            print("交互式测试选项:")
            print("1. 重新测试不同参数")
            print("2. 查看详细因子分析")
            print("3. 退出")
            
            choice = input("请选择 (1-3): ").strip()
            
            if choice == '1':
                try:
                    top_n = int(input("请输入选股数量 (默认10): ") or "10")
                    rebalance_freq = int(input("请输入调仓频率/天 (默认5): ") or "5")
                    
                    print(f"\n重新回测 (选股数量: {top_n}, 调仓频率: {rebalance_freq}天)...")
                    tester.backtest_strategy(top_n=top_n, rebalance_freq=rebalance_freq)
                    tester.plot_results()
                    
                except ValueError:
                    print("输入无效，请输入数字")
                except Exception as e:
                    print(f"回测失败: {str(e)}")
            
            elif choice == '2':
                if tester.factor_values is not None:
                    print("\nAlpha #1 因子详细分析:")
                    print("-" * 40)
                    
                    # 因子分布统计
                    all_factors = tester.factor_values.stack().dropna()
                    print(f"因子值总体统计:")
                    print(f"  样本数量: {len(all_factors)}")
                    print(f"  均值: {all_factors.mean():.4f}")
                    print(f"  标准差: {all_factors.std():.4f}")
                    print(f"  偏度: {all_factors.skew():.4f}")
                    print(f"  峰度: {all_factors.kurtosis():.4f}")
                    
                    # 因子稳定性分析
                    monthly_corr = []
                    for i in range(1, len(tester.factor_values)):
                        corr = tester.factor_values.iloc[i-1].corr(tester.factor_values.iloc[i])
                        if not np.isnan(corr):
                            monthly_corr.append(corr)
                    
                    if monthly_corr:
                        print(f"  日间相关性均值: {np.mean(monthly_corr):.4f}")
                        print(f"  日间相关性标准差: {np.std(monthly_corr):.4f}")
                else:
                    print("请先计算因子")
            
            elif choice == '3':
                print("退出测试")
                break
            
            else:
                print("无效选择，请重新输入")