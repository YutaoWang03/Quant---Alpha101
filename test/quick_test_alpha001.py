#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha #1 因子快速测试
Quick Test for Alpha #1 Factor with Baostock

简化版测试，快速验证Alpha #1因子的计算和基本表现
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
# Alpha #1 因子实现
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
    Alpha #1 因子实现
    """
    # 计算20日标准差
    stddev_20 = returns.rolling(window=20).std()
    
    # 条件判断：returns < 0 时使用stddev，否则使用returns的绝对值
    condition = returns < 0
    power_input = np.where(condition, stddev_20, returns.abs())
    
    # 转换为DataFrame
    power_input_df = pd.DataFrame(power_input, index=returns.index, columns=returns.columns)
    
    # 计算SignedPower(power_input, 2)
    signed_power_result = signed_power(power_input_df, 2)
    
    # 计算Ts_ArgMax(..., 5)
    ts_argmax_result = ts_argmax(signed_power_result, 5)
    
    # 计算rank并减去0.5
    return rank(ts_argmax_result) - 0.5

# ============================================================================
# 数据获取函数
# ============================================================================

def get_stock_data(stock_codes, start_date, end_date):
    """
    获取股票数据
    
    Args:
        stock_codes: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        价格数据DataFrame
    """
    print("正在连接baostock...")
    login_result = bs.login()
    if login_result.error_code != '0':
        print(f"baostock登录失败: {login_result.error_msg}")
        return None
    
    print("baostock连接成功")
    
    all_data = {}
    successful_stocks = []
    
    for i, stock_code in enumerate(stock_codes):
        try:
            print(f"获取 {stock_code} 数据... ({i+1}/{len(stock_codes)})")
            
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,close,pctChg,tradestatus,isST",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"  # 后复权
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if data_list:
                df = pd.DataFrame(data_list, columns=rs.fields)
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 过滤停牌和ST股票
                df = df[df['tradestatus'] == '1']
                df = df[df['isST'] == '0']
                
                if len(df) > 50:  # 确保有足够数据
                    all_data[stock_code] = df['close']
                    successful_stocks.append(stock_code)
                    
        except Exception as e:
            print(f"  获取 {stock_code} 数据失败: {str(e)}")
            continue
    
    bs.logout()
    
    if all_data:
        price_df = pd.DataFrame(all_data)
        print(f"成功获取 {len(successful_stocks)} 只股票的数据")
        return price_df, successful_stocks
    else:
        print("未能获取到任何有效数据")
        return None, []

# ============================================================================
# 快速测试函数
# ============================================================================

def quick_test():
    """快速测试Alpha #1因子"""
    print("Alpha #1 因子快速测试")
    print("=" * 50)
    
    # 测试股票列表（选择一些知名股票）
    test_stocks = [
        'sz.000001',  # 平安银行
        'sz.000002',  # 万科A
        'sh.600000',  # 浦发银行
        'sh.600036',  # 招商银行
        'sh.600519',  # 贵州茅台
        'sz.000858',  # 五粮液
        'sh.600276',  # 恒瑞医药
        'sz.002415',  # 海康威视
        'sh.601318',  # 中国平安
        'sh.600887',  # 伊利股份
    ]
    
    # 设置测试期间
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    print(f"测试期间: {start_date} 到 {end_date}")
    print(f"测试股票: {len(test_stocks)} 只")
    
    # 获取数据
    price_data, successful_stocks = get_stock_data(test_stocks, start_date, end_date)
    
    if price_data is None or len(successful_stocks) == 0:
        print("数据获取失败，无法进行测试")
        return None
    
    print(f"数据维度: {price_data.shape}")
    
    # 计算收益率
    returns_data = price_data.pct_change().dropna()
    print(f"收益率数据维度: {returns_data.shape}")
    
    # 计算Alpha #1因子
    print("\n计算Alpha #1因子...")
    try:
        factor_values = alpha001(returns_data)
        print(f"因子计算成功，维度: {factor_values.shape}")
        
        # 分析因子值
        latest_factors = factor_values.iloc[-1].dropna()
        if len(latest_factors) > 0:
            print(f"\n最新因子值统计:")
            print(f"  均值: {latest_factors.mean():.4f}")
            print(f"  标准差: {latest_factors.std():.4f}")
            print(f"  最小值: {latest_factors.min():.4f}")
            print(f"  最大值: {latest_factors.max():.4f}")
            
            print(f"\n因子值排名:")
            sorted_factors = latest_factors.sort_values(ascending=False)
            for i, (stock, value) in enumerate(sorted_factors.items()):
                print(f"  {i+1}. {stock}: {value:.4f}")
        
        # 简单回测
        print(f"\n简单回测测试...")
        backtest_results = simple_backtest(returns_data, factor_values, top_n=5)
        
        # 绘制结果
        plot_simple_results(factor_values, backtest_results)
        
        return {
            'price_data': price_data,
            'returns_data': returns_data,
            'factor_values': factor_values,
            'backtest_results': backtest_results,
            'successful_stocks': successful_stocks
        }
        
    except Exception as e:
        print(f"因子计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def simple_backtest(returns_data, factor_values, top_n=5, rebalance_freq=10):
    """
    简单回测
    
    Args:
        returns_data: 收益率数据
        factor_values: 因子值数据
        top_n: 选择股票数量
        rebalance_freq: 调仓频率
    
    Returns:
        回测结果
    """
    valid_dates = factor_values.dropna(how='all').index[25:]  # 确保有足够历史数据
    
    portfolio_returns = []
    current_positions = []
    
    for i, date in enumerate(valid_dates):
        # 调仓
        if i % rebalance_freq == 0:
            daily_factors = factor_values.loc[date].dropna()
            if len(daily_factors) >= top_n:
                top_stocks = daily_factors.nlargest(top_n)
                current_positions = list(top_stocks.index)
        
        # 计算收益
        if current_positions and date in returns_data.index:
            daily_returns = returns_data.loc[date, current_positions]
            valid_returns = daily_returns.dropna()
            if len(valid_returns) > 0:
                portfolio_return = valid_returns.mean()
                portfolio_returns.append(portfolio_return)
            else:
                portfolio_returns.append(0)
        else:
            portfolio_returns.append(0)
    
    # 计算指标
    portfolio_returns = np.array(portfolio_returns)
    cumulative_returns = np.cumprod(1 + portfolio_returns)
    
    total_return = cumulative_returns[-1] - 1
    annual_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
    volatility = np.std(portfolio_returns) * np.sqrt(252)
    sharpe_ratio = annual_return / volatility if volatility > 0 else 0
    
    # 基准收益
    benchmark_returns = returns_data.loc[valid_dates].mean(axis=1)
    benchmark_cumulative = np.cumprod(1 + benchmark_returns)
    benchmark_total_return = benchmark_cumulative.iloc[-1] - 1
    benchmark_annual_return = (1 + benchmark_total_return) ** (252 / len(benchmark_returns)) - 1
    
    print(f"回测结果 (选股数量: {top_n}, 调仓频率: {rebalance_freq}天):")
    print(f"  策略年化收益率: {annual_return:.2%}")
    print(f"  策略年化波动率: {volatility:.2%}")
    print(f"  策略夏普比率: {sharpe_ratio:.3f}")
    print(f"  基准年化收益率: {benchmark_annual_return:.2%}")
    print(f"  超额收益: {annual_return - benchmark_annual_return:.2%}")
    
    return {
        'dates': valid_dates,
        'portfolio_returns': portfolio_returns,
        'cumulative_returns': cumulative_returns,
        'benchmark_returns': benchmark_returns.values,
        'benchmark_cumulative': benchmark_cumulative.values,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'excess_return': annual_return - benchmark_annual_return
    }

def plot_simple_results(factor_values, backtest_results):
    """绘制简单结果"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 因子值时间序列
    factor_mean = factor_values.mean(axis=1)
    ax1.plot(factor_mean.index, factor_mean.values, linewidth=1.5)
    ax1.set_title('Alpha #1 因子均值时间序列', fontsize=12)
    ax1.set_ylabel('因子均值', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 2. 最新因子值分布
    latest_factors = factor_values.iloc[-1].dropna()
    ax2.hist(latest_factors.values, bins=20, alpha=0.7, edgecolor='black')
    ax2.set_title('最新因子值分布', fontsize=12)
    ax2.set_xlabel('因子值', fontsize=10)
    ax2.set_ylabel('频数', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # 3. 累积收益对比
    ax3.plot(backtest_results['dates'], backtest_results['cumulative_returns'], 
             label='Alpha #1 策略', linewidth=2, color='red')
    ax3.plot(backtest_results['dates'], backtest_results['benchmark_cumulative'], 
             label='基准(等权重)', linewidth=2, color='blue', alpha=0.7)
    ax3.set_title('累积收益对比', fontsize=12)
    ax3.set_ylabel('累积收益', fontsize=10)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 日收益率对比
    ax4.scatter(backtest_results['benchmark_returns'], backtest_results['portfolio_returns'], 
               alpha=0.6, s=20)
    ax4.plot([-0.1, 0.1], [-0.1, 0.1], 'r--', alpha=0.5)  # 对角线
    ax4.set_title('策略 vs 基准日收益率', fontsize=12)
    ax4.set_xlabel('基准收益率', fontsize=10)
    ax4.set_ylabel('策略收益率', fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    print("开始Alpha #1因子快速测试...")
    
    try:
        results = quick_test()
        
        if results:
            print("\n" + "=" * 50)
            print("测试完成！")
            print("\n主要发现:")
            print(f"1. 成功获取 {len(results['successful_stocks'])} 只股票的数据")
            print(f"2. Alpha #1 因子计算正常")
            print(f"3. 策略年化收益率: {results['backtest_results']['annual_return']:.2%}")
            print(f"4. 策略夏普比率: {results['backtest_results']['sharpe_ratio']:.3f}")
            print(f"5. 超额收益: {results['backtest_results']['excess_return']:.2%}")
            
            # 保存结果
            factor_df = results['factor_values']
            factor_df.to_csv('alpha001_factor_values.csv')
            print(f"\n因子值已保存到 alpha001_factor_values.csv")
            
        else:
            print("测试失败，请检查网络连接和数据源")
            
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n测试结束")