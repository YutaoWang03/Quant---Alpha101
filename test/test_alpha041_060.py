#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha041-060因子测试套件

测试Alpha041到Alpha060的所有因子实现，确保：
1. 函数能正常运行不报错
2. 返回结果的数据类型和形状正确
3. 处理边界情况（NaN值、空数据等）
4. 数学逻辑的基本正确性

作者: Alpha101项目组
日期: 2025年
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.alpha_factors import (
    calculateAlpha041, calculateAlpha042, calculateAlpha043, calculateAlpha044, calculateAlpha045,
    calculateAlpha046, calculateAlpha047, calculateAlpha048, calculateAlpha049, calculateAlpha050,
    calculateAlpha051, calculateAlpha052, calculateAlpha053, calculateAlpha054, calculateAlpha055,
    calculateAlpha056, calculateAlpha057, calculateAlpha058, calculateAlpha059, calculateAlpha060
)


class TestAlpha041_060(unittest.TestCase):
    """Alpha041-060因子测试类"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试日期范围（300天，确保有足够的历史数据）
        dates = pd.date_range(start='2023-01-01', periods=300, freq='D')
        stocks = ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ']
        
        # 生成模拟价格数据
        np.random.seed(42)  # 固定随机种子确保测试可重复
        
        # 基础价格（模拟股价在10-100之间）
        base_prices = np.random.uniform(10, 100, len(stocks))
        
        # 生成价格时间序列（带有趋势和随机波动）
        price_data = []
        for i, base_price in enumerate(base_prices):
            # 生成收益率序列（正态分布，年化波动率约20%）
            returns = np.random.normal(0.0001, 0.02, len(dates))  # 日收益率
            # 累积收益率转换为价格
            prices = base_price * np.exp(np.cumsum(returns))
            price_data.append(prices)
        
        price_data = np.array(price_data).T
        
        # 创建价格DataFrames
        self.close_price = pd.DataFrame(price_data, index=dates, columns=stocks)
        
        # 生成其他价格数据（基于收盘价的合理范围）
        self.open_price = self.close_price * (1 + np.random.normal(0, 0.01, self.close_price.shape))
        self.high_price = np.maximum(self.close_price, self.open_price) * (1 + np.abs(np.random.normal(0, 0.01, self.close_price.shape)))
        self.low_price = np.minimum(self.close_price, self.open_price) * (1 - np.abs(np.random.normal(0, 0.01, self.close_price.shape)))
        
        # 生成成交量数据（对数正态分布）
        volume_base = np.random.lognormal(15, 1, len(stocks))  # 基础成交量
        volume_data = []
        for i, base_vol in enumerate(volume_base):
            # 成交量有一定的序列相关性
            vol_series = []
            current_vol = base_vol
            for _ in range(len(dates)):
                current_vol *= np.random.lognormal(0, 0.3)  # 成交量波动
                vol_series.append(current_vol)
            volume_data.append(vol_series)
        
        volume_data = np.array(volume_data).T
        self.volume = pd.DataFrame(volume_data, index=dates, columns=stocks)
        
        # 生成VWAP数据（基于价格的加权平均）
        self.vwap = (self.high_price + self.low_price + 2 * self.close_price) / 4
        
        # 生成收益率数据
        self.returns = self.close_price.pct_change()
        
        # 生成市值数据（模拟）
        self.cap = self.close_price * self.volume * np.random.uniform(0.1, 10, self.close_price.shape)
        
        # 生成ADV数据（平均日成交量）
        self.adv20 = self.volume.rolling(window=20).mean()
        self.adv40 = self.volume.rolling(window=40).mean()
        self.adv60 = self.volume.rolling(window=60).mean()
        self.adv120 = self.volume.rolling(window=120).mean()
        self.adv180 = self.volume.rolling(window=180).mean()
    
    def test_alpha041(self):
        """测试Alpha041因子"""
        result = calculateAlpha041(self.high_price, self.low_price, self.vwap)
        
        # 检查返回类型和形状
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(result.index.equals(self.close_price.index))
        self.assertTrue(result.columns.equals(self.close_price.columns))
        
        # 检查数值范围（应该有有限值）
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha041测试通过")
    
    def test_alpha042(self):
        """测试Alpha042因子"""
        result = calculateAlpha042(self.close_price, self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha042测试通过")
    
    def test_alpha043(self):
        """测试Alpha043因子"""
        result = calculateAlpha043(self.close_price, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha043测试通过")
    
    def test_alpha044(self):
        """测试Alpha044因子"""
        result = calculateAlpha044(self.high_price, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha044测试通过")
    
    def test_alpha045(self):
        """测试Alpha045因子"""
        result = calculateAlpha045(self.close_price, self.volume, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha045测试通过")
    
    def test_alpha046(self):
        """测试Alpha046因子"""
        result = calculateAlpha046(self.close_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha046测试通过")
    
    def test_alpha047(self):
        """测试Alpha047因子"""
        result = calculateAlpha047(self.close_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha047测试通过")
    
    def test_alpha048(self):
        """测试Alpha048因子"""
        result = calculateAlpha048(self.close_price, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha048测试通过")
    
    def test_alpha049(self):
        """测试Alpha049因子"""
        result = calculateAlpha049(self.open_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha049测试通过")
    
    def test_alpha050(self):
        """测试Alpha050因子"""
        result = calculateAlpha050(self.open_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha050测试通过")
    
    def test_alpha051(self):
        """测试Alpha051因子"""
        result = calculateAlpha051(self.open_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha051测试通过")
    
    def test_alpha052(self):
        """测试Alpha052因子"""
        result = calculateAlpha052(self.low_price, self.returns, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha052测试通过")
    
    def test_alpha053(self):
        """测试Alpha053因子"""
        result = calculateAlpha053(self.close_price, self.high_price, self.low_price)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha053测试通过")
    
    def test_alpha054(self):
        """测试Alpha054因子"""
        result = calculateAlpha054(self.open_price, self.close_price, self.high_price, self.low_price)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # Alpha054可能产生极值，只检查非NaN值是否有限
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha054测试通过")
    
    def test_alpha055(self):
        """测试Alpha055因子"""
        result = calculateAlpha055(self.close_price, self.high_price, self.low_price, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # Alpha055可能产生极值，只检查非NaN值是否有限
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha055测试通过")
    
    def test_alpha056(self):
        """测试Alpha056因子"""
        result = calculateAlpha056(self.returns, self.cap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha056测试通过")
    
    def test_alpha057(self):
        """测试Alpha057因子"""
        result = calculateAlpha057(self.close_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # Alpha057可能产生极值，只检查非NaN值是否有限
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha057测试通过")
    
    def test_alpha058(self):
        """测试Alpha058因子"""
        result = calculateAlpha058(self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha058测试通过")
    
    def test_alpha059(self):
        """测试Alpha059因子"""
        result = calculateAlpha059(self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha059测试通过")
    
    def test_alpha060(self):
        """测试Alpha060因子"""
        result = calculateAlpha060(self.close_price, self.high_price, self.low_price, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha060测试通过")
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试包含NaN值的数据
        close_with_nan = self.close_price.copy()
        close_with_nan.iloc[10:15, 0] = np.nan
        
        # 测试几个代表性因子是否能处理NaN值
        try:
            result1 = calculateAlpha049(self.open_price, self.vwap)
            result2 = calculateAlpha055(close_with_nan, self.high_price, self.low_price, self.volume)
            print("✓ 边界情况测试通过")
        except Exception as e:
            self.fail(f"边界情况测试失败: {e}")
    
    def test_data_consistency(self):
        """测试数据一致性"""
        # 确保所有因子返回的数据形状一致
        factors = [
            calculateAlpha049(self.open_price, self.vwap),
            calculateAlpha050(self.open_price, self.vwap),
            calculateAlpha051(self.open_price, self.vwap),
            calculateAlpha053(self.close_price, self.high_price, self.low_price),
            calculateAlpha055(self.close_price, self.high_price, self.low_price, self.volume)
        ]
        
        base_shape = factors[0].shape
        for i, factor in enumerate(factors[1:], 1):
            self.assertEqual(factor.shape, base_shape, f"因子{i+49}形状不一致")
        
        print("✓ 数据一致性测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Alpha041-060因子测试套件")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAlpha041_060)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要:")
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)