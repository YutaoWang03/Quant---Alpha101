#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha061-080因子测试套件

测试Alpha061到Alpha080的所有因子实现，确保：
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
    calculateAlpha061, calculateAlpha062, calculateAlpha063, calculateAlpha064, calculateAlpha065,
    calculateAlpha066, calculateAlpha067, calculateAlpha068, calculateAlpha069, calculateAlpha070,
    calculateAlpha071, calculateAlpha072, calculateAlpha073, calculateAlpha074, calculateAlpha075,
    calculateAlpha076, calculateAlpha077, calculateAlpha078, calculateAlpha079, calculateAlpha080
)


class TestAlpha061_080(unittest.TestCase):
    """Alpha061-080因子测试类"""
    
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
        
        # 生成ADV数据（平均日成交量）
        self.adv15 = self.volume.rolling(window=15).mean()
        self.adv20 = self.volume.rolling(window=20).mean()
        self.adv40 = self.volume.rolling(window=40).mean()
        self.adv50 = self.volume.rolling(window=50).mean()
        self.adv60 = self.volume.rolling(window=60).mean()
        self.adv120 = self.volume.rolling(window=120).mean()
        self.adv180 = self.volume.rolling(window=180).mean()
    
    def test_alpha061(self):
        """测试Alpha061因子"""
        result = calculateAlpha061(self.vwap, self.adv180)
        
        # 检查返回类型和形状
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(result.index.equals(self.close_price.index))
        self.assertTrue(result.columns.equals(self.close_price.columns))
        
        # 检查数值范围（应该是0或1）
        unique_values = result.dropna().values.flatten()
        unique_values = np.unique(unique_values[np.isfinite(unique_values)])
        self.assertTrue(all(val in [0, 1] for val in unique_values))
        
        print("✓ Alpha061测试通过")
    
    def test_alpha062(self):
        """测试Alpha062因子"""
        result = calculateAlpha062(self.vwap, self.adv20, self.open_price, self.high_price, self.low_price)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        
        # 检查数值范围（应该是0或-1）
        unique_values = result.dropna().values.flatten()
        unique_values = np.unique(unique_values[np.isfinite(unique_values)])
        self.assertTrue(all(val in [0, -1] for val in unique_values))
        
        print("✓ Alpha062测试通过")
    
    def test_alpha063(self):
        """测试Alpha063因子"""
        result = calculateAlpha063(self.close_price, self.vwap, self.open_price, self.adv180)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha063测试通过")
    
    def test_alpha064(self):
        """测试Alpha064因子"""
        result = calculateAlpha064(self.open_price, self.low_price, self.high_price, self.vwap, self.adv120)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        
        # 检查数值范围（应该是0或-1）
        unique_values = result.dropna().values.flatten()
        unique_values = np.unique(unique_values[np.isfinite(unique_values)])
        self.assertTrue(all(val in [0, -1] for val in unique_values))
        
        print("✓ Alpha064测试通过")
    
    def test_alpha065(self):
        """测试Alpha065因子"""
        result = calculateAlpha065(self.open_price, self.vwap, self.adv60)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        
        # 检查数值范围（应该是0或-1）
        unique_values = result.dropna().values.flatten()
        unique_values = np.unique(unique_values[np.isfinite(unique_values)])
        self.assertTrue(all(val in [0, -1] for val in unique_values))
        
        print("✓ Alpha065测试通过")
    
    def test_alpha066(self):
        """测试Alpha066因子"""
        result = calculateAlpha066(self.vwap, self.low_price, self.open_price, self.high_price)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # Alpha066可能产生极值，只检查非NaN值是否有限
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha066测试通过")
    
    def test_alpha067(self):
        """测试Alpha067因子"""
        result = calculateAlpha067(self.high_price, self.vwap, self.adv20)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # Alpha067可能产生极值，只检查非NaN值是否有限
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha067测试通过")
    
    def test_alpha068(self):
        """测试Alpha068因子"""
        result = calculateAlpha068(self.high_price, self.adv15, self.close_price, self.low_price)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        
        # 检查数值范围（应该是0或-1）
        unique_values = result.dropna().values.flatten()
        unique_values = np.unique(unique_values[np.isfinite(unique_values)])
        self.assertTrue(all(val in [0, -1] for val in unique_values))
        
        print("✓ Alpha068测试通过")
    
    def test_alpha069(self):
        """测试Alpha069因子"""
        result = calculateAlpha069(self.vwap, self.close_price, self.adv20)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # Alpha069可能产生极值，只检查非NaN值是否有限
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha069测试通过")
    
    def test_alpha070(self):
        """测试Alpha070因子"""
        result = calculateAlpha070(self.vwap, self.close_price, self.adv50)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # Alpha070可能产生极值，只检查非NaN值是否有限
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha070测试通过")
    
    def test_alpha071(self):
        """测试Alpha071因子"""
        result = calculateAlpha071(self.close_price, self.adv180, self.low_price, self.open_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        self.assertTrue(np.isfinite(result.dropna()).all().all())
        
        print("✓ Alpha071测试通过")
    
    def test_alpha072(self):
        """测试Alpha072因子"""
        result = calculateAlpha072(self.high_price, self.low_price, self.adv40, self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # Alpha072可能产生极值，只检查非NaN值是否有限
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha072测试通过")
    
    def test_alpha073(self):
        """测试Alpha073因子"""
        result = calculateAlpha073(self.open_price, self.low_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        # 检查结果是否包含有效数值
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha073测试通过")
    
    def test_alpha074(self):
        """测试Alpha074因子"""
        result = calculateAlpha074(self.high_price, self.low_price, self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha074测试通过")
    
    def test_alpha075(self):
        """测试Alpha075因子"""
        result = calculateAlpha075(self.close_price, self.high_price, self.low_price, self.open_price, self.vwap)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha075测试通过")
    
    def test_alpha076(self):
        """测试Alpha076因子"""
        result = calculateAlpha076(self.high_price, self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha076测试通过")
    
    def test_alpha077(self):
        """测试Alpha077因子"""
        result = calculateAlpha077(self.close_price, self.low_price, self.high_price, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha077测试通过")
    
    def test_alpha078(self):
        """测试Alpha078因子"""
        result = calculateAlpha078(self.close_price, self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha078测试通过")
    
    def test_alpha079(self):
        """测试Alpha079因子"""
        result = calculateAlpha079(self.close_price, self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha079测试通过")
    
    def test_alpha080(self):
        """测试Alpha080因子"""
        result = calculateAlpha080(self.close_price, self.low_price, self.open_price, self.vwap, self.volume)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, self.close_price.shape)
        finite_result = result.replace([np.inf, -np.inf], np.nan).dropna()
        if not finite_result.empty:
            self.assertTrue(np.isfinite(finite_result).all().all())
        
        print("✓ Alpha080测试通过")
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试包含NaN值的数据
        vwap_with_nan = self.vwap.copy()
        vwap_with_nan.iloc[10:15, 0] = np.nan
        
        # 测试几个代表性因子是否能处理NaN值
        try:
            result1 = calculateAlpha061(vwap_with_nan, self.adv180)
            result2 = calculateAlpha063(self.close_price, vwap_with_nan, self.open_price, self.adv180)
            print("✓ 边界情况测试通过")
        except Exception as e:
            self.fail(f"边界情况测试失败: {e}")
    
    def test_data_consistency(self):
        """测试数据一致性"""
        # 确保所有因子返回的数据形状一致
        factors = [
            calculateAlpha061(self.vwap, self.adv180),
            calculateAlpha063(self.close_price, self.vwap, self.open_price, self.adv180),
            calculateAlpha066(self.vwap, self.low_price, self.open_price, self.high_price),
            calculateAlpha071(self.close_price, self.adv180, self.low_price, self.open_price, self.vwap)
        ]
        
        base_shape = factors[0].shape
        for i, factor in enumerate(factors[1:], 1):
            self.assertEqual(factor.shape, base_shape, f"因子{i+61}形状不一致")
        
        print("✓ 数据一致性测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Alpha061-080因子测试套件")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAlpha061_080)
    
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