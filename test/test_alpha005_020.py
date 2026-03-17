#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Alpha005-Alpha020 因子实现
"""

import sys
import os
import pandas as pd
import numpy as np

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.alpha_factors import (
    calculateAlpha005, calculateAlpha006, calculateAlpha007, calculateAlpha008,
    calculateAlpha009, calculateAlpha010, calculateAlpha011, calculateAlpha012,
    calculateAlpha013, calculateAlpha014, calculateAlpha015, calculateAlpha016,
    calculateAlpha017, calculateAlpha018, calculateAlpha019, calculateAlpha020
)


def create_test_data(n_days=30, n_stocks=5):
    """创建测试数据"""
    dates = pd.date_range('2024-01-01', periods=n_days)
    stocks = [f'stock_{i}' for i in range(n_stocks)]
    
    np.random.seed(42)
    
    data = {
        'open': pd.DataFrame(np.random.rand(n_days, n_stocks) * 100 + 50, 
                            index=dates, columns=stocks),
        'high': pd.DataFrame(np.random.rand(n_days, n_stocks) * 100 + 60, 
                            index=dates, columns=stocks),
        'low': pd.DataFrame(np.random.rand(n_days, n_stocks) * 100 + 40, 
                           index=dates, columns=stocks),
        'close': pd.DataFrame(np.random.rand(n_days, n_stocks) * 100 + 50, 
                             index=dates, columns=stocks),
        'volume': pd.DataFrame(np.random.rand(n_days, n_stocks) * 1000000, 
                              index=dates, columns=stocks),
    }
    
    return data


def test_alpha_factor(alpha_func, data, **kwargs):
    """测试单个Alpha因子"""
    try:
        result = alpha_func(**kwargs)
        print(f"✓ {alpha_func.__name__} 测试通过")
        print(f"  - 结果形状: {result.shape}")
        print(f"  - 非空值数量: {result.notna().sum().sum()}")
        print(f"  - 值范围: [{result.min().min():.4f}, {result.max().max():.4f}]")
        return True
    except Exception as e:
        print(f"✗ {alpha_func.__name__} 测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("Alpha005-Alpha020 因子测试")
    print("=" * 60)
    
    # 创建测试数据
    print("\n创建测试数据...")
    data = create_test_data(n_days=30, n_stocks=5)
    print(f"✓ 测试数据创建完成: {data['close'].shape[0]} 天, {data['close'].shape[1]} 只股票")
    
    # 测试各个因子
    test_cases = [
        (calculateAlpha005, {'open_price': data['open'], 'close_price': data['close']}),
        (calculateAlpha006, {'close_price': data['close']}),
        (calculateAlpha007, {'close_price': data['close'], 'volume': data['volume']}),
        (calculateAlpha008, {'volume': data['volume']}),
        (calculateAlpha009, {'close_price': data['close'], 'volume': data['volume']}),
        (calculateAlpha010, {'close_price': data['close']}),
        (calculateAlpha011, {'close_price': data['close'], 'volume': data['volume']}),
        (calculateAlpha012, {'volume': data['volume']}),
        (calculateAlpha013, {'high_price': data['high'], 'volume': data['volume']}),
        (calculateAlpha014, {'high_price': data['high']}),
        (calculateAlpha015, {'high_price': data['high'], 'volume': data['volume']}),
        (calculateAlpha016, {'high_price': data['high']}),
        (calculateAlpha017, {'low_price': data['low'], 'volume': data['volume']}),
        (calculateAlpha018, {'low_price': data['low']}),
        (calculateAlpha019, {'low_price': data['low'], 'volume': data['volume']}),
        (calculateAlpha020, {'low_price': data['low']}),
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
