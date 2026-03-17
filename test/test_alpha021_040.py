#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Alpha021-Alpha040 因子实现
"""

import sys
import os
import pandas as pd
import numpy as np

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.alpha_factors import (
    calculateAlpha021, calculateAlpha022, calculateAlpha023, calculateAlpha024,
    calculateAlpha025, calculateAlpha026, calculateAlpha027, calculateAlpha028,
    calculateAlpha029, calculateAlpha030, calculateAlpha031, calculateAlpha032,
    calculateAlpha033, calculateAlpha034, calculateAlpha035, calculateAlpha036,
    calculateAlpha037, calculateAlpha038, calculateAlpha039, calculateAlpha040
)


def create_test_data(n_days=30, n_stocks=5):
    """创建测试数据"""
    dates = pd.date_range('2024-01-01', periods=n_days)
    stocks = [f'stock_{i}' for i in range(n_stocks)]
    
    np.random.seed(42)
    
    # 创建基础价格数据
    base_price = 50
    open_prices = np.random.rand(n_days, n_stocks) * 20 + base_price
    high_prices = open_prices + np.random.rand(n_days, n_stocks) * 10
    low_prices = open_prices - np.random.rand(n_days, n_stocks) * 10
    close_prices = open_prices + (np.random.rand(n_days, n_stocks) - 0.5) * 10
    volumes = np.random.rand(n_days, n_stocks) * 1000000
    
    # 计算VWAP (简化版本)
    vwap_prices = (high_prices + low_prices + close_prices) / 3
    
    data = {
        'open': pd.DataFrame(open_prices, index=dates, columns=stocks),
        'high': pd.DataFrame(high_prices, index=dates, columns=stocks),
        'low': pd.DataFrame(low_prices, index=dates, columns=stocks),
        'close': pd.DataFrame(close_prices, index=dates, columns=stocks),
        'volume': pd.DataFrame(volumes, index=dates, columns=stocks),
        'vwap': pd.DataFrame(vwap_prices, index=dates, columns=stocks),
    }
    
    return data


def test_alpha_factor(alpha_func, data, **kwargs):
    """测试单个Alpha因子"""
    try:
        result = alpha_func(**kwargs)
        print(f"✓ {alpha_func.__name__} 测试通过")
        print(f"  - 结果形状: {result.shape}")
        print(f"  - 非空值数量: {result.notna().sum().sum()}")
        if result.notna().sum().sum() > 0:
            print(f"  - 值范围: [{result.min().min():.4f}, {result.max().max():.4f}]")
        return True
    except Exception as e:
        print(f"✗ {alpha_func.__name__} 测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("Alpha021-Alpha040 因子测试")
    print("=" * 60)
    
    # 创建测试数据
    print("\n创建测试数据...")
    data = create_test_data(n_days=30, n_stocks=5)
    print(f"✓ 测试数据创建完成: {data['close'].shape[0]} 天, {data['close'].shape[1]} 只股票")
    
    # 测试各个因子
    test_cases = [
        (calculateAlpha021, {'open_price': data['open'], 'close_price': data['close']}),
        (calculateAlpha022, {'open_price': data['open']}),
        (calculateAlpha023, {'open_price': data['open'], 'close_price': data['close']}),
        (calculateAlpha024, {'open_price': data['open']}),
        (calculateAlpha025, {'high_price': data['high'], 'low_price': data['low']}),
        (calculateAlpha026, {'high_price': data['high'], 'low_price': data['low']}),
        (calculateAlpha027, {'high_price': data['high'], 'low_price': data['low']}),
        (calculateAlpha028, {'high_price': data['high'], 'low_price': data['low']}),
        (calculateAlpha029, {'close_price': data['close'], 'volume': data['volume']}),
        (calculateAlpha030, {'close_price': data['close']}),
        (calculateAlpha031, {'close_price': data['close'], 'volume': data['volume']}),
        (calculateAlpha032, {'close_price': data['close']}),
        (calculateAlpha033, {'vwap': data['vwap'], 'volume': data['volume']}),
        (calculateAlpha034, {'vwap': data['vwap']}),
        (calculateAlpha035, {'vwap': data['vwap'], 'volume': data['volume']}),
        (calculateAlpha036, {'vwap': data['vwap']}),
        (calculateAlpha037, {'close_price': data['close'], 'vwap': data['vwap']}),
        (calculateAlpha038, {'close_price': data['close'], 'vwap': data['vwap']}),
        (calculateAlpha039, {'close_price': data['close'], 'vwap': data['vwap']}),
        (calculateAlpha040, {'close_price': data['close'], 'vwap': data['vwap']}),
    ]
    
    print("\n" + "=" * 60)
    print("开始测试因子...")
    print("=" * 60 + "\n")
    
    passed = 0
    failed = 0
    
    for alpha_func, kwargs in test_cases:
        if test_alpha_factor(alpha_func, data, **kwargs):
            passed += 1
        else:
            failed += 1
        print()
    
    # 输出测试总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总计: {passed + failed} 个因子")
    print(f"✓ 通过: {passed} 个")
    print(f"✗ 失败: {failed} 个")
    print(f"成功率: {passed / (passed + failed) * 100:.1f}%")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)