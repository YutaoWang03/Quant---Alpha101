#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据接口 (Data API)
提供统一的数据访问接口，支持多种数据源
"""

import pandas as pd
from typing import List, Dict, Optional, Union
from datetime import datetime
from .baostock_loader import BaostockLoader


class DataAPI:
    """
    统一数据接口
    支持多种数据源，提供一致的API
    """
    
    def __init__(self, source: str = 'baostock', cache_dir: str = 'data/db'):
        """
        初始化数据接口
        
        Args:
            source: 数据源类型，'baostock', 'joinquant', 'local'
            cache_dir: 缓存目录
        """
        self.source = source
        self.cache_dir = cache_dir
        self._loader = None
        
        # 初始化数据加载器
        if source == 'baostock':
            self._loader = BaostockLoader(cache_dir=cache_dir)
        elif source == 'joinquant':
            # TODO: 实现聚宽数据源
            raise NotImplementedError("聚宽数据源尚未实现")
        elif source == 'local':
            # TODO: 实现本地数据源
            raise NotImplementedError("本地数据源尚未实现")
        else:
            raise ValueError(f"不支持的数据源: {source}")
    
    def __enter__(self):
        """上下文管理器入口"""
        if hasattr(self._loader, '__enter__'):
            self._loader.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if hasattr(self._loader, '__exit__'):
            self._loader.__exit__(exc_type, exc_val, exc_tb)
    
    def get_stock_list(
        self,
        index: str = 'hs300',
        date: Optional[str] = None
    ) -> List[str]:
        """
        获取股票列表
        
        Args:
            index: 指数名称
                - 'hs300': 沪深300
                - 'sz50': 上证50
                - 'zz500': 中证500
                - 'cyb': 创业板指
            date: 指定日期（可选）
        
        Returns:
            股票代码列表
        """
        # 映射指数名称到代码
        index_map = {
            'hs300': 'sh.000300',
            'sz50': 'sh.000016',
            'zz500': 'sz.399006',
            'cyb': 'sz.399006'
        }
        
        index_code = index_map.get(index, 'sh.000300')
        
        if self.source == 'baostock':
            return self._loader.get_index_stocks(index_code)
        else:
            raise NotImplementedError(f"{self.source} 数据源尚未实现")
    
    def get_stock_data(
        self,
        symbols: Union[str, List[str]],
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        adjust: str = 'hfq'
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        获取股票数据
        
        Args:
            symbols: 股票代码或代码列表
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            fields: 字段列表，默认 ['open', 'high', 'low', 'close', 'volume']
            adjust: 复权方式，'qfq'=前复权，'hfq'=后复权，'none'=不复权
        
        Returns:
            单只股票返回 DataFrame，多只股票返回字典
        """
        if fields is None:
            fields = ['open', 'high', 'low', 'close', 'volume']
        
        # 复权方式映射
        adjust_map = {
            'qfq': '1',  # 前复权
            'hfq': '2',  # 后复权
            'none': '3'  # 不复权
        }
        adjustflag = adjust_map.get(adjust, '3')
        
        if isinstance(symbols, str):
            # 单只股票
            if self.source == 'baostock':
                return self._loader.get_stock_data(
                    symbols, start_date, end_date, 
                    fields=fields, adjustflag=adjustflag
                )
        else:
            # 多只股票
            if self.source == 'baostock':
                return self._loader.get_panel_data(
                    symbols, start_date, end_date, fields=fields
                )
        
        raise NotImplementedError(f"{self.source} 数据源尚未实现")
    
    def get_market_data(
        self,
        universe: Union[str, List[str]],
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        max_stocks: Optional[int] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        获取市场数据（面板数据）
        
        Args:
            universe: 股票池，可以是指数名称或股票列表
            start_date: 开始日期
            end_date: 结束日期
            fields: 字段列表
            max_stocks: 最大股票数量
        
        Returns:
            面板数据字典 {field: DataFrame}
        """
        # 如果是指数名称，先获取成分股
        if isinstance(universe, str):
            stock_list = self.get_stock_list(universe)
        else:
            stock_list = universe
        
        if self.source == 'baostock':
            return self._loader.get_panel_data(
                stock_list, start_date, end_date,
                fields=fields, max_stocks=max_stocks
            )
        
        raise NotImplementedError(f"{self.source} 数据源尚未实现")
    
    def save_cache(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        name: str,
        format: str = 'parquet'
    ):
        """
        保存数据到缓存
        
        Args:
            data: 要保存的数据
            name: 缓存名称
            format: 保存格式
        """
        if self.source == 'baostock':
            self._loader.save_to_cache(data, name, format)
        else:
            raise NotImplementedError(f"{self.source} 数据源尚未实现")
    
    def load_cache(
        self,
        name: str,
        format: str = 'parquet'
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame], None]:
        """
        从缓存加载数据
        
        Args:
            name: 缓存名称
            format: 文件格式
        
        Returns:
            加载的数据
        """
        if self.source == 'baostock':
            return self._loader.load_from_cache(name, format)
        else:
            raise NotImplementedError(f"{self.source} 数据源尚未实现")


# 使用示例
if __name__ == "__main__":
    # 使用统一接口
    with DataAPI(source='baostock') as api:
        # 获取沪深300成分股
        stocks = api.get_stock_list('hs300')
        print(f"沪深300成分股: {len(stocks)} 只")
        
        # 获取单只股票数据
        stock_data = api.get_stock_data(
            'sh.600000',
            '2023-01-01',
            '2024-01-01'
        )
        print(f"\n单只股票数据: {stock_data.shape}")
        
        # 获取市场面板数据
        market_data = api.get_market_data(
            universe='hs300',
            start_date='2023-01-01',
            end_date='2024-01-01',
            max_stocks=10
        )
        print(f"\n市场面板数据:")
        for field, df in market_data.items():
            print(f"  {field}: {df.shape}")
        
        # 保存到缓存
        api.save_cache(market_data, 'hs300_2023', format='hdf5')
        
        # 从缓存加载
        cached = api.load_cache('hs300_2023', format='hdf5')
        print(f"\n从缓存加载成功: {len(cached)} 个字段")
