#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史数据下载脚本
从 Baostock 下载指定股票和指数的历史数据并保存到 SQLite 数据库
"""

import baostock as bs
import pandas as pd
import sqlite3
import os
from datetime import datetime
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')


class HistoricalDataDownloader:
    """历史数据下载器"""
    
    def __init__(self, db_path: str = 'data/db/stock_data.db'):
        """
        初始化下载器
        
        Args:
            db_path: SQLite 数据库路径
        """
        self.db_path = db_path
        self.conn = None
        self.is_logged_in = False
        
        # 确保数据库目录存在
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"✓ 创建数据库目录: {db_dir}")
    
    def login_baostock(self):
        """登录 Baostock"""
        if not self.is_logged_in:
            print("正在连接 Baostock...")
            result = bs.login()
            if result.error_code != '0':
                raise Exception(f"Baostock 登录失败: {result.error_msg}")
            self.is_logged_in = True
            print("✓ Baostock 连接成功\n")
    
    def logout_baostock(self):
        """登出 Baostock"""
        if self.is_logged_in:
            bs.logout()
            self.is_logged_in = False
            print("\n✓ Baostock 已断开连接")
    
    def connect_db(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        print(f"✓ 连接数据库: {self.db_path}\n")
    
    def close_db(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("\n✓ 数据库连接已关闭")
    
    def create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()
        
        # 创建股票日线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                preclose REAL,
                volume REAL,
                amount REAL,
                adjustflag TEXT,
                turn REAL,
                tradestatus TEXT,
                pctChg REAL,
                isST TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, date)
            )
        ''')
        
        # 创建股票信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                code TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                start_date TEXT,
                end_date TEXT,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_daily_code 
            ON stock_daily(code)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_daily_date 
            ON stock_daily(date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_daily_code_date 
            ON stock_daily(code, date)
        ''')
        
        self.conn.commit()
        print("✓ 数据表创建完成")
    
    def get_stock_info(self, code: str) -> Dict:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
        
        Returns:
            股票信息字典
        """
        # 查询股票基本信息
        rs = bs.query_stock_basic(code=code)
        
        if rs.error_code != '0':
            print(f"  ✗ 获取 {code} 信息失败: {rs.error_msg}")
            return None
        
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return None
        
        # 解析数据
        fields = rs.fields
        data = dict(zip(fields, data_list[0]))
        
        return {
            'code': data.get('code', code),
            'name': data.get('code_name', ''),
            'type': data.get('type', ''),
            'start_date': data.get('ipoDate', '1990-01-01'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def download_stock_data(
        self,
        code: str,
        start_date: str = '1990-01-01',
        end_date: str = None,
        frequency: str = 'd',
        adjustflag: str = '3'
    ) -> pd.DataFrame:
        """
        下载单只股票的历史数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 频率，'d'=日，'w'=周，'m'=月
            adjustflag: 复权类型，'1'=前复权，'2'=后复权，'3'=不复权
        
        Returns:
            股票数据 DataFrame
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"  下载 {code} 数据 ({start_date} → {end_date})...", end=' ')
        
        # 查询历史数据
        rs = bs.query_history_k_data_plus(
            code,
            "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag=adjustflag
        )
        
        if rs.error_code != '0':
            print(f"✗ 失败: {rs.error_msg}")
            return pd.DataFrame()
        
        # 收集数据
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            print("✗ 无数据")
            return pd.DataFrame()
        
        # 转换为 DataFrame
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 数据类型转换
        numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 
                          'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"✓ 获取 {len(df)} 条记录")
        return df
    
    def save_stock_info(self, stock_info: Dict):
        """保存股票信息到数据库"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO stock_info 
            (code, name, type, start_date, end_date, last_update)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            stock_info['code'],
            stock_info['name'],
            stock_info['type'],
            stock_info['start_date'],
            stock_info['end_date']
        ))
        
        self.conn.commit()
    
    def save_stock_data(self, df: pd.DataFrame):
        """保存股票数据到数据库"""
        if df.empty:
            return
        
        # 使用 pandas 的 to_sql 方法
        df.to_sql('stock_daily', self.conn, if_exists='append', index=False)
        self.conn.commit()
    
    def download_and_save(
        self,
        code: str,
        name: str = '',
        start_date: str = '1990-01-01'
    ):
        """
        下载并保存股票数据
        
        Args:
            code: 股票代码
            name: 股票名称（用于显示）
            start_date: 开始日期
        """
        print(f"\n{'='*60}")
        print(f"处理: {name} ({code})")
        print(f"{'='*60}")
        
        # 获取股票信息
        stock_info = self.get_stock_info(code)
        if stock_info:
            print(f"  股票名称: {stock_info['name']}")
            print(f"  上市日期: {stock_info['start_date']}")
            
            # 使用上市日期作为起始日期
            actual_start = max(start_date, stock_info['start_date'])
            
            # 保存股票信息
            self.save_stock_info(stock_info)
        else:
            actual_start = start_date
            print(f"  使用默认起始日期: {actual_start}")
        
        # 下载数据
        df = self.download_stock_data(code, start_date=actual_start)
        
        if not df.empty:
            # 保存数据
            print(f"  保存数据到数据库...", end=' ')
            self.save_stock_data(df)
            print(f"✓ 完成")
            
            # 显示统计信息
            print(f"\n  数据统计:")
            print(f"    记录数: {len(df)}")
            print(f"    日期范围: {df['date'].min()} → {df['date'].max()}")
            if 'close' in df.columns:
                print(f"    收盘价范围: {df['close'].min():.2f} → {df['close'].max():.2f}")
        else:
            print(f"  ✗ 未获取到数据")
    
    def get_data_summary(self):
        """获取数据库统计信息"""
        cursor = self.conn.cursor()
        
        print(f"\n{'='*60}")
        print("数据库统计信息")
        print(f"{'='*60}")
        
        # 股票数量
        cursor.execute("SELECT COUNT(DISTINCT code) FROM stock_daily")
        stock_count = cursor.fetchone()[0]
        print(f"股票数量: {stock_count}")
        
        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM stock_daily")
        total_records = cursor.fetchone()[0]
        print(f"总记录数: {total_records:,}")
        
        # 日期范围
        cursor.execute("SELECT MIN(date), MAX(date) FROM stock_daily")
        date_range = cursor.fetchone()
        print(f"日期范围: {date_range[0]} → {date_range[1]}")
        
        # 每只股票的记录数
        print(f"\n各股票记录数:")
        cursor.execute('''
            SELECT s.code, s.name, COUNT(d.id) as count,
                   MIN(d.date) as start_date, MAX(d.date) as end_date
            FROM stock_info s
            LEFT JOIN stock_daily d ON s.code = d.code
            GROUP BY s.code, s.name
            ORDER BY count DESC
        ''')
        
        for row in cursor.fetchall():
            code, name, count, start, end = row
            print(f"  {code:12} {name:10} {count:6,} 条  ({start} → {end})")
        
        # 数据库文件大小
        db_size = os.path.getsize(self.db_path) / (1024 * 1024)
        print(f"\n数据库大小: {db_size:.2f} MB")
        print(f"数据库路径: {self.db_path}")


def main():
    """主函数"""
    print("="*60)
    print("历史数据下载脚本")
    print("="*60)
    
    # 定义要下载的股票和指数
    stocks_to_download = [
        # 指数
        ('sh.000300', '沪深300指数', '1990-01-01'),
        ('sz.399006', '创业板指数', '1990-01-01'),
        ('sh.000905', '中证500指数', '1990-01-01'),
        ('sh.000852', '中证1000指数', '1990-01-01'),
        
        # 银行股
        ('sh.600919', '江苏银行', '1990-01-01'),
        ('sh.601398', '工商银行', '1990-01-01'),
        ('sh.601288', '农业银行', '1990-01-01'),
        ('sh.601939', '建设银行', '1990-01-01'),
    ]
    
    # 创建下载器
    downloader = HistoricalDataDownloader(db_path='data/db/stock_data.db')
    
    try:
        # 连接服务
        downloader.login_baostock()
        downloader.connect_db()
        
        # 创建表
        downloader.create_tables()
        
        # 下载数据
        print(f"\n开始下载 {len(stocks_to_download)} 只股票/指数的历史数据...")
        
        for code, name, start_date in stocks_to_download:
            try:
                downloader.download_and_save(code, name, start_date)
            except Exception as e:
                print(f"\n✗ 下载 {name} ({code}) 失败: {str(e)}")
                continue
        
        # 显示统计信息
        downloader.get_data_summary()
        
        print(f"\n{'='*60}")
        print("✓ 所有数据下载完成！")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n✗ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        downloader.close_db()
        downloader.logout_baostock()


if __name__ == "__main__":
    main()
