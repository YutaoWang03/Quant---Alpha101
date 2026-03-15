"""
数据层 (Data Layer)
提供统一的数据访问接口，所有数据访问都通过本地SQLite数据库
"""

from .data_api import DataAPI
from .query_database import StockDatabase

# BaostockLoader 仅用于数据下载，不在常规使用中导入
# 如需使用，请直接导入: from data.baostock_loader import BaostockLoader

__all__ = ['DataAPI', 'StockDatabase']
