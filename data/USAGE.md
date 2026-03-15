# 数据下载和使用指南

## 第一步：下载历史数据

运行数据下载脚本，将历史数据保存到本地 SQLite 数据库：

```bash
cd /Applications/obsidian\ repo/Obsidian\ Repo/Finance/Investment/Alpha101
python data/download_historical_data.py
```

### 下载内容

脚本将自动下载以下股票和指数的**全部历史数据**（自发行以来）：

| 代码 | 名称 | 类型 |
|------|------|------|
| sh.000300 | 沪深300指数 | 指数 |
| sz.399006 | 创业板指数 | 指数 |
| sh.000905 | 中证500指数 | 指数 |
| sh.000852 | 中证1000指数 | 指数 |
| sh.600919 | 江苏银行 | 股票 |
| sh.601398 | 工商银行 | 股票 |
| sh.601288 | 农业银行 | 股票 |
| sh.601939 | 建设银行 | 股票 |

### 预期输出

```
============================================================
历史数据下载脚本
============================================================
正在连接 Baostock...
✓ Baostock 连接成功

✓ 连接数据库: data/db/stock_data.db

✓ 数据表创建完成

开始下载 8 只股票/指数的历史数据...

============================================================
处理: 沪深300指数 (sh.000300)
============================================================
  股票名称: 沪深300
  上市日期: 2005-04-08
  下载 sh.000300 数据 (2005-04-08 → 2024-01-15)... ✓ 获取 4567 条记录
  保存数据到数据库... ✓ 完成

  数据统计:
    记录数: 4567
    日期范围: 2005-04-08 → 2024-01-15
    收盘价范围: 998.52 → 5930.91

...（其他股票类似）

============================================================
数据库统计信息
============================================================
股票数量: 8
总记录数: 35,234
日期范围: 2005-04-08 → 2024-01-15

各股票记录数:
  sh.000300    沪深300      4,567 条  (2005-04-08 → 2024-01-15)
  sz.399006    创业板指      3,234 条  (2010-06-01 → 2024-01-15)
  ...

数据库大小: 12.34 MB
数据库路径: data/db/stock_data.db

============================================================
✓ 所有数据下载完成！
============================================================
```

## 第二步：查询数据

### 方式1：使用查询工具

```bash
python data/query_database.py
```

这将显示数据库摘要和示例查询。

### 方式2：在代码中使用

```python
from data import StockDatabase

# 使用上下文管理器
with StockDatabase() as db:
    # 1. 查看数据库摘要
    db.print_summary()
    
    # 2. 获取单只股票数据
    icbc_data = db.get_stock_data(
        code='sh.601398',
        start_date='2023-01-01',
        end_date='2024-01-01',
        fields=['date', 'open', 'high', 'low', 'close', 'volume']
    )
    print(icbc_data.head())
    
    # 3. 获取多只股票数据
    banks = ['sh.601398', 'sh.601288', 'sh.601939', 'sh.600919']
    banks_data = db.get_stock_data(
        code=banks,
        start_date='2023-01-01'
    )
    
    # 4. 获取面板数据（透视表格式）
    # 行=日期，列=股票代码
    close_panel = db.get_panel_data(
        codes=banks,
        start_date='2023-01-01',
        field='close'
    )
    print(close_panel.head())
    
    # 5. 计算收益率
    returns = close_panel.pct_change()
    
    # 6. 获取股票列表
    stock_list = db.get_stock_list()
    print(stock_list)
```

## 第三步：在因子计算中使用

```python
from data import StockDatabase
from core.alpha_factors import alpha001

# 从数据库获取数据
with StockDatabase() as db:
    # 获取沪深300成分股的收盘价
    codes = ['sh.601398', 'sh.601288', 'sh.601939', 'sh.600919']
    close_df = db.get_panel_data(
        codes=codes,
        start_date='2023-01-01',
        end_date='2024-01-01',
        field='close'
    )
    
    # 计算收益率
    returns_df = close_df.pct_change().dropna()
    
    # 计算Alpha001因子
    factor_values = alpha001(returns_df)
    
    print("Alpha001因子值:")
    print(factor_values.tail())
```

## 数据库结构

### 表：stock_info（股票信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| code | TEXT | 股票代码（主键） |
| name | TEXT | 股票名称 |
| type | TEXT | 类型（股票/指数） |
| start_date | TEXT | 上市日期 |
| end_date | TEXT | 最后更新日期 |
| last_update | TIMESTAMP | 最后更新时间 |

### 表：stock_daily（日线数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增主键 |
| code | TEXT | 股票代码 |
| date | TEXT | 日期 |
| open | REAL | 开盘价 |
| high | REAL | 最高价 |
| low | REAL | 最低价 |
| close | REAL | 收盘价 |
| preclose | REAL | 前收盘价 |
| volume | REAL | 成交量 |
| amount | REAL | 成交额 |
| adjustflag | TEXT | 复权类型 |
| turn | REAL | 换手率 |
| tradestatus | TEXT | 交易状态 |
| pctChg | REAL | 涨跌幅 |
| isST | TEXT | 是否ST |
| created_at | TIMESTAMP | 创建时间 |

**索引**:
- `idx_stock_daily_code`: 按股票代码索引
- `idx_stock_daily_date`: 按日期索引
- `idx_stock_daily_code_date`: 按股票代码和日期联合索引
- `UNIQUE(code, date)`: 唯一约束，防止重复数据

## 常见问题

### Q1: 如何更新数据？

再次运行下载脚本即可，数据库有唯一约束，不会重复插入：

```bash
python data/download_historical_data.py
```

### Q2: 如何添加更多股票？

编辑 `data/download_historical_data.py`，在 `stocks_to_download` 列表中添加：

```python
stocks_to_download = [
    # 现有的...
    
    # 添加新股票
    ('sh.600036', '招商银行', '1990-01-01'),
    ('sz.000001', '平安银行', '1990-01-01'),
]
```

### Q3: 数据库文件在哪里？

```
data/db/stock_data.db
```

这个文件已加入 `.gitignore`，不会上传到 GitHub。

### Q4: 如何清空数据库重新下载？

删除数据库文件后重新运行下载脚本：

```bash
rm data/db/stock_data.db
python data/download_historical_data.py
```

### Q5: 数据库太大怎么办？

可以只下载需要的日期范围，修改下载脚本中的 `start_date` 参数：

```python
('sh.601398', '工商银行', '2020-01-01'),  # 只下载2020年以后的数据
```

## 性能优化建议

1. **使用索引**: 数据库已自动创建索引，查询时尽量使用 `code` 和 `date` 字段
2. **批量查询**: 一次查询多只股票，而不是循环单独查询
3. **限制日期范围**: 只查询需要的日期范围
4. **选择必要字段**: 只查询需要的字段，减少数据传输

## 下一步

数据准备完成后，可以：

1. 计算 Alpha 因子
2. 训练因子模型
3. 生成交易信号
4. 执行回测

参考 [ARCHITECTURE.md](../docs/ARCHITECTURE.md) 了解完整的量化交易流程。
