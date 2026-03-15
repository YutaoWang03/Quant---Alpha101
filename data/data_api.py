#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据接口 (Data API)
提供对本地数据库的统一访问接口
"""

import pandas as pd
from typing import List, Optional, Union
from .query_database import StockDatabase


class DataAPI:
    """
    统一数据访问接口
    所有数据访问都通过本地SQLite数据库
    """
    
    def __init__(self, db_path: str = 'data/db/stock_data.db'):
        """
        初始化数据接口
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.db = None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.db = StockDatabase(self.db_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.db:
            self.db.close()
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取所有股票列表
        
        Returns:
            股票信息 DataFrame，包含 code 和 name 列
        """
        if self.db is None:
            raise RuntimeError("请使用 with 语句或先调用 __enter__")
        return self.db.get_stock_list()
    
    def get_stock_data(
        self,
        code: Union[str, List[str]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        获取股票数据
        
        Args:
            code: 股票代码或代码列表
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            fields: 字段列表，默认为 ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount']
        
        Returns:
            股票数据 DataFrame
        """
        if self.db is None:
            raise RuntimeError("请使用 with 语句或先调用 __enter__")
        return self.db.get_stock_data(code, start_date, end_date, fields)
    
    def get_panel_data(
        self,
        codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        field: str = 'close'
    ) -> pd.DataFrame:
        """
        获取面板数据（透视表格式）
        
        Args:
            codes: 股票代码列表
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            field: 字段名 ('open', 'high', 'low', 'close', 'volume', 'amount')
        
        Returns:
            面板数据 DataFrame（行=日期，列=股票代码）
        """
        if self.db is None:
            raise RuntimeError("请使用 with 语句或先调用 __enter__")
        return self.db.get_panel_data(codes, start_date, end_date, field)
    
    def get_date_range(self, code: str) -> tuple:
        """
        获取股票的日期范围
        
        Args:
            code: 股票代码
        
        Returns:
            (最早日期, 最晚日期)
        """
        if self.db is None:
            raise RuntimeError("请使用 with 语句或先调用 __enter__")
        return self.db.get_date_range(code)
    
    def get_statistics(self) -> dict:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        if self.db is None:
            raise RuntimeError("请使用 with 语句或先调用 __enter__")
        return self.db.get_statistics()
    
    def print_summary(self):
        """打印数据库摘要信息"""
        if self.db is None:
            raise RuntimeError("请使用 with 语句或先调用 __enter__")
        self.db.print_summary()


# 使用示例
if __name__ == "__main__":
    # 使用统一接口访问数据
    with DataAPI() as api:
        # 打印数据库摘要
        api.print_summary()
        
        # 获取股票列表
        print("\n" + "="*60)
        print("获取股票列表")
        print("="*60)
        stocks = api.get_stock_list()
        print(stocks)
        
        # 获取单只股票数据
        print("\n" + "="*60)
        print("获取工商银行数据")
        print("="*60)
        icbc_data = api.get_stock_data('sh.601398', start_date='2023-01-01')
        print(icbc_data.tail(10))
        
        # 获取面板数据
        print("\n" + "="*60)
        print("获取四大行收盘价面板数据")
        print("="*60)
        banks = ['sh.601398', 'sh.601288', 'sh.601939', 'sh.600919']
        panel = api.get_panel_data(banks, field='close')
        print(panel.tail(5))
