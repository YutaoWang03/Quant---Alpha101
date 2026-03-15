#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baostock 数据加载器
提供从 Baostock 获取股票数据的功能
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import os
import warnings
warnings.filterwarnings('ignore')


class BaostockLoader:
    """Baostock 数据加载器"""
    
    def __init__(self, cache_dir: str = 'data/db'):
        """
        初始化 Baostock 数据加载器
        
        Args:
            cache_dir: 本地缓存目录
        """
        self.cache_dir = cache_dir
        self.is_logged_in = False
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            print(f"创建缓存目录: {self.cache_dir}")
    
    def login(self):
        """登录 Baostock"""
        if not self.is_logged_in:
            print("正在连接 Baostock...")
            result = bs.login()
            if result.error_code != '0':
                raise Exception(f"Baostock 登录失败: {result.error_msg}")
            self.is_logged_in = True
            print("✓ Baostock 连接成功")
    
    def logout(self):
        """登出 Baostock"""
        if self.is_logged_in:
            bs.logout()
            self.is_logged_in = False
            print("✓ Baostock 已断开连接")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.login()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.logout()
    
    def get_index_stocks(self, index_code: str = 'sh.000300') -> List[str]:
        """
        获取指数成分股列表
        
        Args:
            index_code: 指数代码
                - 'sh.000300': 沪深300
                - 'sh.000016': 上证50
                - 'sz.399006': 创业板指
                - 'sz.399005': 中小板指
                - 'sz.399001': 深证成指
        
        Returns:
            股票代码列表
        """
        self.login()
        
        print(f"获取 {index_code} 成分股...")
        
        # 根据指数代码选择查询方法
        if index_code == 'sh.000300':
            rs = bs.query_hs300_stocks()
        elif index_code == 'sh.000016':
            rs = bs.query_sz50_stocks()
        elif index_code == 'sz.399006':
            rs = bs.query_zz500_stocks()
        else:
            # 默认使用沪深300
            rs = bs.query_hs300_stocks()
        
        stock_list = []
        while (rs.error_code == '0') and rs.next():
            stock_list.append(rs.get_row_data()[1])
        
        print(f"✓ 获取到 {len(stock_list)} 只成分股")
        return stock_list
    
    def get_stock_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        frequency: str = 'd',
        adjustflag: str = '3'
    ) -> pd.DataFrame:
        """
        获取单只股票的历史数据
        
        Args:
            stock_code: 股票代码，如 'sh.600000'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            fields: 字段列表，默认为常用字段
            frequency: 数据频率，'d'=日，'w'=周，'m'=月
            adjustflag: 复权类型，'1'=前复权，'2'=后复权，'3'=不复权
        
        Returns:
            股票数据 DataFrame
        """
        self.login()
        
        if fields is None:
            fields = [
                'date', 'code', 'open', 'high', 'low', 'close', 
                'preclose', 'volume', 'amount', 'adjustflag',
                'turn', 'tradestatus', 'pctChg', 'isST'
            ]
        
        fields_str = ','.join(fields)
        
        rs = bs.query_history_k_data_plus(
            stock_code,
            fields_str,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag=adjustflag
        )
        
        rows = []
        while (rs.error_code == '0') and rs.next():
            rows.append(rs.get_row_data())
        
        if not rows:
            return pd.DataFrame()
        
        # 转换为 DataFrame
        df = pd.DataFrame(rows, columns=rs.fields)
        
        # 数据类型转换
        numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 
                          'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 过滤停牌和ST股票
        if 'tradestatus' in df.columns:
            df = df[df['tradestatus'] == '1']  # 正常交易
        if 'isST' in df.columns:
            df = df[df['isST'] == '0']  # 非ST股票
        
        return df
    
    def get_panel_data(
        self,
        stock_list: List[str],
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        max_stocks: Optional[int] = None,
        min_data_points: int = 50
    ) -> Dict[str, pd.DataFrame]:
        """
        获取多只股票的面板数据
        
        Args:
            stock_list: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            fields: 需要的字段列表，默认 ['close', 'open', 'high', 'low', 'volume']
            max_stocks: 最大股票数量限制
            min_data_points: 最小数据点数量，少于此数量的股票将被过滤
        
        Returns:
            字典，key为字段名，value为DataFrame（行=日期，列=股票代码）
        """
        self.login()
        
        if fields is None:
            fields = ['close', 'open', 'high', 'low', 'volume']
        
        if max_stocks:
            stock_list = stock_list[:max_stocks]
        
        print(f"开始获取 {len(stock_list)} 只股票的面板数据...")
        print(f"日期范围: {start_date} → {end_date}")
        
        # 初始化数据字典
        panel_data = {field: {} for field in fields}
        successful_stocks = []
        
        for i, stock_code in enumerate(stock_list):
            try:
                print(f"  [{i+1}/{len(stock_list)}] {stock_code}", end=' ')
                
                # 获取股票数据
                df = self.get_stock_data(stock_code, start_date, end_date)
                
                if len(df) >= min_data_points:
                    # 提取需要的字段
                    for field in fields:
                        if field in df.columns:
                            panel_data[field][stock_code] = df[field]
                    
                    successful_stocks.append(stock_code)
                    print(f"✓ ({len(df)} 条)")
                else:
                    print(f"✗ 数据不足 ({len(df)} < {min_data_points})")
                    
            except Exception as e:
                print(f"✗ 失败: {str(e)}")
                continue
        
        print(f"\n✓ 成功获取 {len(successful_stocks)} 只股票的数据")
        
        # 转换为 DataFrame
        result = {}
        for field, data_dict in panel_data.items():
            if data_dict:
                df = pd.DataFrame(data_dict)
                df = df.sort_index()  # 按日期排序
                result[field] = df
                print(f"  {field}: {df.shape}")
        
        return result
    
    def save_to_cache(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        filename: str,
        format: str = 'parquet'
    ):
        """
        保存数据到本地缓存
        
        Args:
            data: 要保存的数据
            filename: 文件名（不含扩展名）
            format: 保存格式，'parquet', 'hdf5', 'csv'
        """
        filepath = os.path.join(self.cache_dir, f"{filename}.{format}")
        
        if isinstance(data, pd.DataFrame):
            if format == 'parquet':
                data.to_parquet(filepath)
            elif format == 'hdf5':
                data.to_hdf(filepath, key='data', mode='w')
            elif format == 'csv':
                data.to_csv(filepath)
            print(f"✓ 数据已保存到: {filepath}")
        
        elif isinstance(data, dict):
            if format == 'hdf5':
                with pd.HDFStore(filepath, mode='w') as store:
                    for key, df in data.items():
                        store[key] = df
                print(f"✓ 面板数据已保存到: {filepath}")
            else:
                # 对于字典，分别保存每个DataFrame
                for key, df in data.items():
                    key_filepath = os.path.join(
                        self.cache_dir, 
                        f"{filename}_{key}.{format}"
                    )
                    if format == 'parquet':
                        df.to_parquet(key_filepath)
                    elif format == 'csv':
                        df.to_csv(key_filepath)
                print(f"✓ 面板数据已保存到: {self.cache_dir}/{filename}_*.{format}")
    
    def load_from_cache(
        self,
        filename: str,
        format: str = 'parquet'
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame], None]:
        """
        从本地缓存加载数据
        
        Args:
            filename: 文件名（不含扩展名）
            format: 文件格式
        
        Returns:
            加载的数据，如果文件不存在返回 None
        """
        filepath = os.path.join(self.cache_dir, f"{filename}.{format}")
        
        if not os.path.exists(filepath):
            print(f"✗ 缓存文件不存在: {filepath}")
            return None
        
        try:
            if format == 'parquet':
                data = pd.read_parquet(filepath)
            elif format == 'hdf5':
                # 尝试读取单个DataFrame或多个
                with pd.HDFStore(filepath, mode='r') as store:
                    keys = store.keys()
                    if len(keys) == 1:
                        data = store[keys[0]]
                    else:
                        data = {key.strip('/'): store[key] for key in keys}
            elif format == 'csv':
                data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            print(f"✓ 从缓存加载数据: {filepath}")
            return data
        
        except Exception as e:
            print(f"✗ 加载缓存失败: {str(e)}")
            return None


# 使用示例
if __name__ == "__main__":
    # 使用上下文管理器自动登录登出
    with BaostockLoader() as loader:
        # 获取沪深300成分股
        stocks = loader.get_index_stocks('sh.000300')
        print(f"沪深300成分股数量: {len(stocks)}")
        
        # 获取面板数据
        panel_data = loader.get_panel_data(
            stock_list=stocks[:10],  # 只获取前10只
            start_date='2023-01-01',
            end_date='2024-01-01',
            max_stocks=10
        )
        
        # 保存到缓存
        loader.save_to_cache(panel_data, 'hs300_sample', format='hdf5')
        
        # 从缓存加载
        cached_data = loader.load_from_cache('hs300_sample', format='hdf5')
        
        if cached_data:
            print("\n缓存数据加载成功:")
            for key, df in cached_data.items():
                print(f"  {key}: {df.shape}")
