# 数据层 (Data Layer)

提供统一的数据获取、处理和存储接口。

## 模块说明

### 核心模块

- `data_api.py` - 统一数据接口，支持多种数据源
- `baostock_loader.py` - Baostock 数据源实现
- `joinquant_loader.py` - 聚宽数据源实现（待实现）
- `data_cleaner.py` - 数据清洗模块（待实现）
- `data_cache.py` - 数据缓存管理（待实现）

### 目录结构

```
data/
├── __init__.py              # 模块初始化
├── README.md                # 本文档
├── data_api.py              # 统一数据接口 ✅
├── baostock_loader.py       # Baostock数据源 ✅
├── joinquant_loader.py      # 聚宽数据源 🚧
├── data_cleaner.py          # 数据清洗 🚧
├── data_cache.py            # 缓存管理 🚧
└── db/                      # 本地数据存储
    └── README.md            # 存储说明
```

## 快速开始

### 1. 使用统一接口

```python
from data import DataAPI

# 创建数据接口（默认使用 Baostock）
with DataAPI(source='baostock') as api:
    # 获取沪深300成分股
    stocks = api.get_stock_list('hs300')
    
    # 获取市场数据
    market_data = api.get_market_data(
        universe='hs300',
        start_date='2023-01-01',
        end_date='2024-01-01',
        max_stocks=30
    )
    
    # 保存到缓存
    api.save_cache(market_data, 'hs300_2023', format='hdf5')
```

### 2. 直接使用 Baostock

```python
from data import BaostockLoader

with BaostockLoader() as loader:
    # 获取单只股票数据
    stock_data = loader.get_stock_data(
        'sh.600000',
        '2023-01-01',
        '2024-01-01'
    )
    
    # 获取面板数据
    panel_data = loader.get_panel_data(
        stock_list=['sh.600000', 'sz.000001'],
        start_date='2023-01-01',
        end_date='2024-01-01'
    )
```

## 数据源支持

### Baostock ✅

- 免费的A股历史数据
- 支持日/周/月频率
- 支持前复权/后复权/不复权
- 提供指数成分股查询

**使用示例**:
```python
api = DataAPI(source='baostock')
```

### 聚宽 (JoinQuant) 🚧

- 专业量化平台
- 需要API密钥
- 数据质量高

**使用示例**:
```python
api = DataAPI(source='joinquant', api_key='your_key')
```

### 本地数据 🚧

- 支持CSV/Excel/HDF5
- 适合离线使用

**使用示例**:
```python
api = DataAPI(source='local', data_dir='path/to/data')
```

## 数据缓存

### 支持的格式

1. **Parquet** (推荐)
   - 压缩率高
   - 读取速度快
   - 支持列式存储

2. **HDF5**
   - 适合大型面板数据
   - 支持多个数据集
   - 高效的随机访问

3. **CSV**
   - 通用格式
   - 易于查看和编辑
   - 文件较大

### 缓存管理

```python
# 保存到缓存
api.save_cache(data, 'cache_name', format='parquet')

# 从缓存加载
cached_data = api.load_cache('cache_name', format='parquet')
```

## API 参考

### DataAPI

#### `__init__(source, cache_dir)`
初始化数据接口

**参数**:
- `source`: 数据源类型 ('baostock', 'joinquant', 'local')
- `cache_dir`: 缓存目录路径

#### `get_stock_list(index, date)`
获取股票列表

**参数**:
- `index`: 指数名称 ('hs300', 'sz50', 'zz500', 'cyb')
- `date`: 指定日期（可选）

**返回**: 股票代码列表

#### `get_stock_data(symbols, start_date, end_date, fields, adjust)`
获取股票数据

**参数**:
- `symbols`: 股票代码或代码列表
- `start_date`: 开始日期
- `end_date`: 结束日期
- `fields`: 字段列表
- `adjust`: 复权方式 ('qfq', 'hfq', 'none')

**返回**: DataFrame 或字典

#### `get_market_data(universe, start_date, end_date, fields, max_stocks)`
获取市场面板数据

**参数**:
- `universe`: 股票池（指数名称或股票列表）
- `start_date`: 开始日期
- `end_date`: 结束日期
- `fields`: 字段列表
- `max_stocks`: 最大股票数量

**返回**: 面板数据字典

## 最佳实践

1. **使用上下文管理器**
   ```python
   with DataAPI(source='baostock') as api:
       data = api.get_market_data(...)
   ```

2. **合理使用缓存**
   ```python
   # 先尝试从缓存加载
   data = api.load_cache('cache_name')
   if data is None:
       # 缓存不存在，从数据源获取
       data = api.get_market_data(...)
       api.save_cache(data, 'cache_name')
   ```

3. **批量获取数据**
   ```python
   # 一次获取多只股票，而不是循环单独获取
   data = api.get_market_data(universe=stock_list, ...)
   ```

4. **选择合适的数据格式**
   - 小数据集: CSV
   - 中等数据集: Parquet
   - 大型面板数据: HDF5

## 注意事项

1. Baostock 有访问频率限制，建议使用缓存
2. 数据缓存目录 `data/db/` 不会上传到 Git
3. 定期清理过期的缓存文件
4. 使用前复权数据进行因子计算

## 待实现功能

- [ ] 聚宽数据源
- [ ] 本地数据源
- [ ] 数据清洗模块
- [ ] 智能缓存管理
- [ ] 增量数据更新
- [ ] 数据质量检查
- [ ] 并行数据下载
