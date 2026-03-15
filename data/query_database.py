#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库查询工具
提供便捷的数据库查询接口
"""

import sqlite3
import pandas as pd
import os
from typing import List, Optional, Union
from datetime import datetime


class StockDatabase:
    """股票数据库查询类"""
    
    def __init__(self, db_path: str = 'data/db/stock_data.db'):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库路径
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        print(f"✓ 连接数据库: {db_path}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("✓ 数据库连接已关闭")
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取所有股票列表
        
        Returns:
            股票信息 DataFrame
        """
        query = "SELECT * FROM stock_info ORDER BY code"
        return pd.read_sql_query(query, self.conn)
    
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
            start_date: 开始日期
            end_date: 结束日期
            fields: 字段列表
        
        Returns:
            股票数据 DataFrame
        """
        if fields is None:
            fields = ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount']
        
        fields_str = ', '.join(fields)
        
        # 构建查询条件
        conditions = []
        params = []
        
        if isinstance(code, str):
            conditions.append("code = ?")
            params.append(code)
        elif isinstance(code, list):
            placeholders = ','.join(['?'] * len(code))
            conditions.append(f"code IN ({placeholders})")
            params.extend(code)
        
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT {fields_str}
            FROM stock_daily
            WHERE {where_clause}
            ORDER BY date, code
        """
        
        df = pd.read_sql_query(query, self.conn, params=params)
        df['date'] = pd.to_datetime(df['date'])
        
        return df
    
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
            start_date: 开始日期
            end_date: 结束日期
            field: 字段名
        
        Returns:
            面板数据 DataFrame（行=日期，列=股票代码）
        """
        df = self.get_stock_data(codes, start_date, end_date, fields=['date', 'code', field])
        
        if df.empty:
            return pd.DataFrame()
        
        # 透视表
        panel = df.pivot(index='date', columns='code', values=field)
        return panel
    
    def get_date_range(self, code: str) -> tuple:
        """
        获取股票的日期范围
        
        Args:
            code: 股票代码
        
        Returns:
            (最早日期, 最晚日期)
        """
        query = """
            SELECT MIN(date), MAX(date)
            FROM stock_daily
            WHERE code = ?
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (code,))
        return cursor.fetchone()
    
    def get_statistics(self) -> dict:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        cursor = self.conn.cursor()
        
        # 股票数量
        cursor.execute("SELECT COUNT(DISTINCT code) FROM stock_daily")
        stock_count = cursor.fetchone()[0]
        
        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM stock_daily")
        total_records = cursor.fetchone()[0]
        
        # 日期范围
        cursor.execute("SELECT MIN(date), MAX(date) FROM stock_daily")
        date_range = cursor.fetchone()
        
        # 数据库大小
        db_size = os.path.getsize(self.db_path) / (1024 * 1024)
        
        return {
            'stock_count': stock_count,
            'total_records': total_records,
            'date_range': date_range,
            'db_size_mb': db_size,
            'db_path': self.db_path
        }
    
    def print_summary(self):
        """打印数据库摘要信息"""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("数据库摘要")
        print("="*60)
        print(f"股票数量: {stats['stock_count']}")
        print(f"总记录数: {stats['total_records']:,}")
        print(f"日期范围: {stats['date_range'][0]} → {stats['date_range'][1]}")
        print(f"数据库大小: {stats['db_size_mb']:.2f} MB")
        print(f"数据库路径: {stats['db_path']}")
        
        # 显示股票列表
        print("\n股票列表:")
        stocks = self.get_stock_list()
        for _, row in stocks.iterrows():
            date_range = self.get_date_range(row['code'])
            print(f"  {row['code']:12} {row['name']:10} "
                  f"({date_range[0]} → {date_range[1]})")


# 使用示例
if __name__ == "__main__":
    with StockDatabase() as db:
        # 打印摘要
        db.print_summary()
        
        # 获取单只股票数据
        print("\n" + "="*60)
        print("示例：获取工商银行最近10天数据")
        print("="*60)
        icbc_data = db.get_stock_data('sh.601398', fields=['date', 'close', 'volume'])
        print(icbc_data.tail(10))
        
        # 获取面板数据
        print("\n" + "="*60)
        print("示例：获取四大行收盘价面板数据（最近5天）")
        print("="*60)
        banks = ['sh.601398', 'sh.601288', 'sh.601939', 'sh.600919']
        panel = db.get_panel_data(banks, field='close')
        print(panel.tail(5))
