#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
从 .env 文件加载配置
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """配置类"""
    
    def __init__(self, env_file: str = '.env'):
        """
        初始化配置
        
        Args:
            env_file: .env 文件路径
        """
        self.env_file = env_file
        self._load_env()
    
    def _load_env(self):
        """加载 .env 文件"""
        env_path = Path(self.env_file)
        
        if not env_path.exists():
            print(f"警告: {self.env_file} 文件不存在，使用默认配置")
            return
        
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 设置环境变量（如果尚未设置）
                    if key not in os.environ:
                        os.environ[key] = value
    
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            配置值
        """
        return os.environ.get(key, default)
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """
        获取整数配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            整数配置值
        """
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        """
        获取浮点数配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            浮点数配置值
        """
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """
        获取布尔配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            布尔配置值
        """
        value = os.environ.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    # Tushare 配置
    @property
    def tushare_token(self) -> str:
        """Tushare API Token"""
        return self.get('TUSHARE_TOKEN', '')
    
    # 数据库配置
    @property
    def db_path(self) -> str:
        """数据库路径"""
        return self.get('DB_PATH', 'data/db/stock_data.db')
    
    @property
    def table_stock_daily(self) -> str:
        """股票日线数据表名"""
        return self.get('TABLE_STOCK_DAILY', 'stock_daily')
    
    @property
    def table_stock_info(self) -> str:
        """股票信息表名"""
        return self.get('TABLE_STOCK_INFO', 'stock_info')
    
    # 下载配置
    @property
    def download_start_date(self) -> str:
        """下载开始日期"""
        return self.get('DOWNLOAD_START_DATE', '20240101')
    
    @property
    def download_mode(self) -> str:
        """下载模式"""
        return self.get('DOWNLOAD_MODE', 'sample')
    
    @property
    def api_delay(self) -> float:
        """API请求延迟（秒）"""
        return self.get_float('API_DELAY', 0.2)


# 创建全局配置实例
config = Config()


# 便捷函数
def get_config() -> Config:
    """获取配置实例"""
    return config


if __name__ == "__main__":
    # 测试配置加载
    print("配置测试:")
    print(f"  Tushare Token: {config.tushare_token[:10]}..." if config.tushare_token else "  Tushare Token: 未设置")
    print(f"  数据库路径: {config.db_path}")
    print(f"  日线数据表: {config.table_stock_daily}")
    print(f"  股票信息表: {config.table_stock_info}")
    print(f"  开始日期: {config.download_start_date}")
    print(f"  下载模式: {config.download_mode}")
    print(f"  API延迟: {config.api_delay} 秒")
