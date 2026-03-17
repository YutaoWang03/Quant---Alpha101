#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据格式是否符合 core 模块要求
Test if data format meets core module requirements
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
from data import DataAPI

# 直接从 validation 模块导入，避免通过 __init__.py
import core.validation as validation
validateDataFormat = validation.validateDataFormat

def test_data_format():
    """测试从数据库获取的数据是否符合 core 模块的格式要求"""
    
    print("="*60)
    print("测试数据格式验证")
    print("="*60)
    
    with DataAPI() as api:
        # 获取四大行的收盘价
        banks = ['sh.601398', 'sh.601288', 'sh.601939', 'sh.600919']
        panel = api.get_panel_data(banks, start_date='2026-01-01', field='close')
        
        print("\n1. 数据基本信息:")
        print(f"   数据类型: {type(panel)}")
        print(f"   索引类型: {type(panel.index)}")
        print(f"   数据形状: {panel.shape}")
        print(f"   列名: {list(panel.columns)}")
        
        print("\n2. 数据预览:")
        print(panel.head())
        
        print("\n3. 验证数据格式:")
        try:
            validateDataFormat(panel, "panel")
            print("   ✓ 数据格式验证通过！")
        except Exception as e:
            print(f"   ✗ 数据格式验证失败: {e}")
            return False
        
        print("\n4. 计算收益率并验证:")
        returns = panel.pct_change().dropna()
        try:
            validateDataFormat(returns, "returns")
            print("   ✓ 收益率数据格式验证通过！")
        except Exception as e:
            print(f"   ✗ 收益率数据格式验证失败: {e}")
            return False
        
        print("\n5. 收益率数据预览:")
        print(returns.tail())
        
        print("\n" + "="*60)
        print("✓ 所有测试通过！数据格式符合 core 模块要求")
        print("="*60)
        
        return True

if __name__ == "__main__":
    success = test_data_format()
    sys.exit(0 if success else 1)
