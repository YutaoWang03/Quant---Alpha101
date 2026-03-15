#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha #1 因子测试 - 从 core/ 调用计算函数，数据实时从 baostock 获取
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

import baostock as bs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# 从 core 模块导入所有计算函数
from alpha_helpers import rank, ts_argmax, signed_power, ts_min, ts_max, delta
from alpha_factors import alpha001

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================================
# Baostock 数据获取
# ============================================================================

class BaostockDataLoader:
    """Baostock 数据加载器"""

    def __init__(self):
        print("正在连接 baostock...")
        result = bs.login()
        if result.error_code != '0':
            raise Exception(f"baostock 登录失败: {result.error_msg}")
        print("baostock 连接成功")

    def __del__(self):
        bs.logout()

    def get_stock_list(self, index_code='sh.000300'):
        """获取指数成分股列表"""
        print(f"获取 {index_code} 成分股...")
        if index_code == 'sh.000300':
            rs = bs.query_hs300_stocks()
        elif index_code == 'sh.000016':
            rs = bs.query_sz50_stocks()
        else:
            rs = bs.query_zz500_stocks()

        stock_list = []
        while (rs.error_code == '0') and rs.next():
            stock_list.append(rs.get_row_data()[1])

        print(f"获取到 {len(stock_list)} 只成分股")
        return stock_list[:50]

    def get_stock_data(self, stock_code, start_date, end_date):
        """获取单只股票历史数据"""
        rs = bs.query_history_k_data_plus(
            stock_code,
            "date,open,high,low,close,volume,tradestatus,isST",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"
        )
        rows = []
        while (rs.error_code == '0') and rs.next():
            rows.append(rs.get_row_data())

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=rs.fields)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # 过滤停牌和ST
        df = df[(df['tradestatus'] == '1') & (df['isST'] == '0')]
        return df

    def get_panel_data(self, stock_list, start_date, end_date, max_stocks=30):
        """获取多只股票的面板数据"""
        print(f"获取 {min(len(stock_list), max_stocks)} 只股票数据...")
        close_dict, volume_dict = {}, {}

        for i, code in enumerate(stock_list[:max_stocks]):
            try:
                print(f"  [{i+1}/{min(len(stock_list), max_stocks)}] {code}")
                df = self.get_stock_data(code, start_date, end_date)
                if len(df) > 50:
                    close_dict[code] = df['close']
                    volume_dict[code] = df['volume']
            except Exception as e:
                print(f"  {code} 获取失败: {e}")

        close_df = pd.DataFrame(close_dict).sort_index()
        volume_df = pd.DataFrame(volume_dict).sort_index()
        print(f"成功获取 {len(close_dict)} 只股票数据")
        return close_df, volume_df

# ============================================================================
# 策略回测
# ============================================================================

class Alpha001Strategy:
    """Alpha #1 因子策略回测"""

    def __init__(self, returns_df, top_n=10, rebalance_freq=5):
        self.returns_df = returns_df
        self.top_n = top_n
        self.rebalance_freq = rebalance_freq

    def run(self):
        """执行回测，返回结果 DataFrame"""
        # 计算因子（调用 core/alpha_factors.py）
        factor_df = alpha001(self.returns_df)

        valid_dates = factor_df.dropna(how='all').index[25:]
        portfolio_returns = []
        current_positions = []

        for i, date in enumerate(valid_dates):
            if i % self.rebalance_freq == 0:
                daily_factors = factor_df.loc[date].dropna()
                if len(daily_factors) >= self.top_n:
                    current_positions = list(daily_factors.nlargest(self.top_n).index)

            if current_positions and date in self.returns_df.index:
                ret = self.returns_df.loc[date, current_positions].dropna().mean()
                portfolio_returns.append(ret if not np.isnan(ret) else 0)
            else:
                portfolio_returns.append(0)

        portfolio_returns = np.array(portfolio_returns)
        cumulative = np.cumprod(1 + portfolio_returns)

        self.results = pd.DataFrame({
            'date': valid_dates,
            'portfolio_return': portfolio_returns,
            'cumulative_return': cumulative
        })
        return self.results

    def metrics(self):
        """计算策略指标"""
        r = self.results['portfolio_return'].values
        total = self.results['cumulative_return'].iloc[-1] - 1
        annual = (1 + total) ** (252 / len(r)) - 1
        vol = np.std(r) * np.sqrt(252)
        sharpe = annual / vol if vol > 0 else 0

        cum = self.results['cumulative_return']
        max_dd = ((cum - cum.expanding().max()) / cum.expanding().max()).min()

        return {
            '总收益率': f'{total:.2%}',
            '年化收益率': f'{annual:.2%}',
            '年化波动率': f'{vol:.2%}',
            '夏普比率': f'{sharpe:.3f}',
            '最大回撤': f'{max_dd:.2%}',
            '胜率': f'{np.mean(r > 0):.2%}'
        }

    def plot(self, benchmark_returns=None):
        """绘制回测结果"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        ax1.plot(self.results['date'], self.results['cumulative_return'],
                 label='Alpha #1 策略', linewidth=2, color='red')
        if benchmark_returns is not None:
            bench_cum = np.cumprod(1 + benchmark_returns.values)
            ax1.plot(self.results['date'], bench_cum[:len(self.results)],
                     label='基准(等权重)', linewidth=2, color='blue', alpha=0.7)
        ax1.set_title('Alpha #1 累积收益曲线', fontsize=14)
        ax1.set_ylabel('累积收益')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.hist(self.results['portfolio_return'], bins=50, alpha=0.7, edgecolor='black')
        ax2.set_title('日收益率分布', fontsize=14)
        ax2.set_xlabel('日收益率')
        ax2.set_ylabel('频数')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

# ============================================================================
# 主函数
# ============================================================================

def main():
    print("Alpha #1 因子测试（baostock 实时数据 + core/ 计算模块）")
    print("=" * 60)

    START_DATE = '2023-01-01'
    END_DATE   = '2024-01-01'
    MAX_STOCKS = 30
    TOP_N      = 10
    REBALANCE  = 5

    # 1. 获取数据
    loader = BaostockDataLoader()
    stock_list = loader.get_stock_list('sh.000300')
    close_df, volume_df = loader.get_panel_data(stock_list, START_DATE, END_DATE, MAX_STOCKS)

    returns_df = close_df.pct_change().dropna()
    print(f"\n数据维度: {returns_df.shape}")
    print(f"日期范围: {returns_df.index[0].date()} → {returns_df.index[-1].date()}")

    # 2. 回测
    strategy = Alpha001Strategy(returns_df, top_n=TOP_N, rebalance_freq=REBALANCE)
    strategy.run()

    # 3. 指标
    print("\n策略表现:")
    for k, v in strategy.metrics().items():
        print(f"  {k}: {v}")

    # 4. 基准
    benchmark = returns_df.mean(axis=1).loc[strategy.results['date']]

    # 5. 绘图
    strategy.plot(benchmark_returns=benchmark)

    # 6. 保存
    strategy.results.to_csv('alpha001_backtest_results.csv', index=False)
    print("\n结果已保存到 alpha001_backtest_results.csv")

if __name__ == "__main__":
    main()
