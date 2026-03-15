# Alpha101 量化交易系统架构设计

## 系统概述

本系统是一个完整的量化交易框架，从数据获取、因子计算、信号生成到回测评估，提供端到端的解决方案。

## 核心理念

**Alpha101 因子不是交易信号，而是预测收益的特征变量。**

- **因子（Factor）**: 描述股票特征的数值指标
- **因子模型（Factor Model）**: 使用多个因子预测股票未来收益
- **交易信号（Trading Signal）**: 基于预测收益生成的买卖决策

## 系统架构

### 五层架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      5. 展示层 (Presentation)                │
│              可视化、报告生成、交互式分析                      │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                    4. 回测层 (Backtesting)                   │
│           历史数据回测、性能评估、风险分析                     │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│              3. 信号层 (Signal Generation)                   │
│        因子模型、机器学习、交易信号生成                        │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                2. 核心计算层 (Computation)                    │
│         因子计算、辅助函数、性能指标                           │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                   1. 数据层 (Data Layer)                     │
│            数据获取、ETL、数据清洗、数据存储                   │
└─────────────────────────────────────────────────────────────┘
```

## 详细架构图

### 1. 数据层 (Data Layer)

```mermaid
graph TB
    subgraph "数据源 Data Sources"
        A1[Baostock API]
        A2[聚宽 JoinQuant]
        A3[本地文件 CSV/HDF5]
        A4[数据库 MySQL/PostgreSQL]
    end
    
    subgraph "数据获取 Data Acquisition"
        B1[数据下载器 DataDownloader]
        B2[数据缓存 DataCache]
        B3[增量更新 IncrementalUpdate]
    end
    
    subgraph "ETL 处理 ETL Pipeline"
        C1[数据清洗 DataCleaning]
        C2[数据验证 DataValidation]
        C3[数据转换 DataTransformation]
        C4[缺失值处理 MissingValueHandler]
        C5[异常值检测 OutlierDetection]
    end
    
    subgraph "数据存储 Data Storage"
        D1[内存缓存 MemoryCache]
        D2[本地存储 LocalStorage]
        D3[数据库 Database]
    end
    
    subgraph "数据接口 Data API"
        E1[get_stock_data]
        E2[get_market_data]
        E3[get_factor_data]
        E4[get_universe]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    
    B1 --> B2
    B2 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5
    
    C5 --> D1
    C5 --> D2
    C5 --> D3
    
    D1 --> E1
    D2 --> E2
    D3 --> E3
    D1 --> E4
    
    style A1 fill:#e3f2fd
    style B1 fill:#fff3e0
    style C1 fill:#f3e5f5
    style D1 fill:#e8f5e9
    style E1 fill:#fce4ec
```

**核心模块：**
- `data/data_loader.py` - 数据加载器基类
- `data/baostock_loader.py` - Baostock 数据源
- `data/data_cleaner.py` - 数据清洗
- `data/data_cache.py` - 数据缓存管理
- `data/data_api.py` - 统一数据接口

### 2. 核心计算层 (Computation Layer)

```mermaid
graph TB
    subgraph "辅助函数 Helper Functions"
        A1[时间序列操作<br/>rank, delay, delta, ts_sum]
        A2[统计函数<br/>correlation, covariance]
        A3[技术指标<br/>MA, EMA, RSI, MACD]
        A4[数学运算<br/>signed_power, scale]
    end
    
    subgraph "因子计算 Factor Calculation"
        B1[Alpha001-Alpha101<br/>101个量化因子]
        B2[自定义因子<br/>Custom Factors]
        B3[因子标准化<br/>Factor Normalization]
        B4[因子中性化<br/>Factor Neutralization]
    end
    
    subgraph "性能指标 Performance Metrics"
        C1[收益指标<br/>Total/Annual Return]
        C2[风险指标<br/>Volatility, Drawdown]
        C3[风险调整收益<br/>Sharpe, Calmar, Sortino]
        C4[其他指标<br/>Win Rate, Turnover]
    end
    
    subgraph "计算接口 Computation API"
        D1[calculate_factors]
        D2[calculate_metrics]
        D3[normalize_factors]
        D4[neutralize_factors]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B2
    A4 --> B1
    
    B1 --> B3
    B2 --> B3
    B3 --> B4
    
    B4 --> D1
    C1 --> D2
    C2 --> D2
    C3 --> D2
    C4 --> D2
    
    style A1 fill:#e3f2fd
    style B1 fill:#fff3e0
    style C1 fill:#f3e5f5
    style D1 fill:#e8f5e9
```

**核心模块：**
- `core/alpha_helpers.py` - 辅助函数库
- `core/alpha_factors.py` - Alpha101 因子实现
- `core/custom_factors.py` - 自定义因子
- `core/factor_processor.py` - 因子处理（标准化、中性化）
- `core/metrics.py` - 性能指标计算

### 3. 信号层 (Signal Generation Layer)

```mermaid
graph TB
    subgraph "因子选择 Factor Selection"
        A1[因子池<br/>Factor Pool]
        A2[因子筛选<br/>Factor Screening]
        A3[因子相关性分析<br/>Correlation Analysis]
        A4[因子有效性检验<br/>Factor Validation]
    end
    
    subgraph "因子模型 Factor Models"
        B1[线性回归<br/>Linear Regression]
        B2[岭回归/Lasso<br/>Ridge/Lasso]
        B3[随机森林<br/>Random Forest]
        B4[XGBoost/LightGBM<br/>Gradient Boosting]
        B5[神经网络<br/>Neural Network]
    end
    
    subgraph "收益预测 Return Prediction"
        C1[预测未来收益<br/>Predict Future Returns]
        C2[预测置信度<br/>Prediction Confidence]
        C3[预测误差分析<br/>Error Analysis]
    end
    
    subgraph "信号生成 Signal Generation"
        D1[排序信号<br/>Ranking Signal]
        D2[阈值信号<br/>Threshold Signal]
        D3[多空信号<br/>Long-Short Signal]
        D4[仓位分配<br/>Position Sizing]
    end
    
    subgraph "信号接口 Signal API"
        E1[train_model]
        E2[predict_returns]
        E3[generate_signals]
        E4[optimize_portfolio]
    end
    
    A1 --> A2
    A2 --> A3
    A3 --> A4
    
    A4 --> B1
    A4 --> B2
    A4 --> B3
    A4 --> B4
    A4 --> B5
    
    B1 --> C1
    B2 --> C1
    B3 --> C1
    B4 --> C1
    B5 --> C1
    
    C1 --> C2
    C2 --> C3
    
    C1 --> D1
    C1 --> D2
    C1 --> D3
    D1 --> D4
    D2 --> D4
    D3 --> D4
    
    D4 --> E1
    D4 --> E2
    D4 --> E3
    D4 --> E4
    
    style A1 fill:#e3f2fd
    style B1 fill:#fff3e0
    style C1 fill:#f3e5f5
    style D1 fill:#e8f5e9
    style E1 fill:#fce4ec
```

**核心模块：**
- `signal/factor_selector.py` - 因子选择器
- `signal/linear_model.py` - 线性因子模型
- `signal/ml_model.py` - 机器学习模型
- `signal/signal_generator.py` - 信号生成器
- `signal/portfolio_optimizer.py` - 组合优化

### 4. 回测层 (Backtesting Layer)

```mermaid
graph TB
    subgraph "回测引擎 Backtest Engine"
        A1[事件驱动引擎<br/>Event-Driven Engine]
        A2[向量化回测<br/>Vectorized Backtest]
        A3[滚动窗口回测<br/>Rolling Window]
    end
    
    subgraph "交易模拟 Trade Simulation"
        B1[订单管理<br/>Order Management]
        B2[成交模拟<br/>Execution Simulation]
        B3[滑点模型<br/>Slippage Model]
        B4[交易成本<br/>Transaction Cost]
    end
    
    subgraph "风险管理 Risk Management"
        C1[仓位控制<br/>Position Control]
        C2[止损止盈<br/>Stop Loss/Profit]
        C3[风险限额<br/>Risk Limits]
        C4[对冲策略<br/>Hedging]
    end
    
    subgraph "性能分析 Performance Analysis"
        D1[收益分析<br/>Return Analysis]
        D2[风险分析<br/>Risk Analysis]
        D3[归因分析<br/>Attribution Analysis]
        D4[敏感性分析<br/>Sensitivity Analysis]
    end
    
    subgraph "回测接口 Backtest API"
        E1[run_backtest]
        E2[calculate_performance]
        E3[analyze_trades]
        E4[generate_report]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    
    B1 --> B2
    B2 --> B3
    B3 --> B4
    
    B4 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    
    C4 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> D4
    
    D4 --> E1
    D4 --> E2
    D4 --> E3
    D4 --> E4
    
    style A1 fill:#e3f2fd
    style B1 fill:#fff3e0
    style C1 fill:#f3e5f5
    style D1 fill:#e8f5e9
    style E1 fill:#fce4ec
```

**核心模块：**
- `backtest/backtest_engine.py` - 回测引擎
- `backtest/order_manager.py` - 订单管理
- `backtest/execution.py` - 成交模拟
- `backtest/risk_manager.py` - 风险管理
- `backtest/performance.py` - 性能分析

### 5. 展示层 (Presentation Layer)

```mermaid
graph TB
    subgraph "数据可视化 Data Visualization"
        A1[净值曲线<br/>Equity Curve]
        A2[回撤曲线<br/>Drawdown Curve]
        A3[收益分布<br/>Return Distribution]
        A4[因子分析图<br/>Factor Analysis]
    end
    
    subgraph "报告生成 Report Generation"
        B1[HTML报告<br/>HTML Report]
        B2[PDF报告<br/>PDF Report]
        B3[Excel报告<br/>Excel Report]
        B4[交互式仪表板<br/>Interactive Dashboard]
    end
    
    subgraph "交互分析 Interactive Analysis"
        C1[参数调优<br/>Parameter Tuning]
        C2[情景分析<br/>Scenario Analysis]
        C3[实时监控<br/>Real-time Monitoring]
        C4[预警系统<br/>Alert System]
    end
    
    subgraph "展示接口 Presentation API"
        D1[plot_results]
        D2[generate_report]
        D3[create_dashboard]
        D4[export_data]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B2
    A4 --> B2
    
    B1 --> C1
    B2 --> C1
    B3 --> C2
    B4 --> C2
    
    C1 --> D1
    C2 --> D2
    C3 --> D3
    C4 --> D4
    
    style A1 fill:#e3f2fd
    style B1 fill:#fff3e0
    style C1 fill:#f3e5f5
    style D1 fill:#e8f5e9
```

**核心模块：**
- `visualization/plotter.py` - 图表绘制
- `visualization/report_generator.py` - 报告生成
- `visualization/dashboard.py` - 交互式仪表板
- `visualization/exporter.py` - 数据导出

## 完整数据流程图

```mermaid
sequenceDiagram
    participant User as 用户
    participant Data as 数据层
    participant Compute as 计算层
    participant Signal as 信号层
    participant Backtest as 回测层
    participant Visual as 展示层
    
    User->>Data: 1. 请求股票数据
    Data->>Data: 数据获取与ETL
    Data-->>Compute: 2. 返回清洗后数据
    
    Compute->>Compute: 3. 计算Alpha因子
    Compute-->>Signal: 4. 返回因子矩阵
    
    Signal->>Signal: 5. 因子选择
    Signal->>Signal: 6. 训练因子模型
    Signal->>Signal: 7. 预测收益
    Signal->>Signal: 8. 生成交易信号
    Signal-->>Backtest: 9. 返回信号序列
    
    Backtest->>Backtest: 10. 执行回测
    Backtest->>Backtest: 11. 风险管理
    Backtest->>Compute: 12. 请求性能指标
    Compute-->>Backtest: 13. 返回指标
    Backtest-->>Visual: 14. 返回回测结果
    
    Visual->>Visual: 15. 生成图表
    Visual->>Visual: 16. 生成报告
    Visual-->>User: 17. 展示结果
```

## 模块调用关系图

```mermaid
graph LR
    subgraph "用户层"
        U[用户脚本/Notebook]
    end
    
    subgraph "数据层"
        D1[DataLoader]
        D2[DataCleaner]
        D3[DataAPI]
    end
    
    subgraph "计算层"
        C1[AlphaHelpers]
        C2[AlphaFactors]
        C3[Metrics]
    end
    
    subgraph "信号层"
        S1[FactorSelector]
        S2[FactorModel]
        S3[SignalGenerator]
    end
    
    subgraph "回测层"
        B1[BacktestEngine]
        B2[RiskManager]
        B3[Performance]
    end
    
    subgraph "展示层"
        V1[Plotter]
        V2[ReportGenerator]
    end
    
    U --> D3
    U --> S3
    U --> B1
    U --> V2
    
    D3 --> D1
    D3 --> D2
    
    S1 --> C2
    S2 --> C2
    S3 --> S2
    
    B1 --> S3
    B1 --> B2
    B1 --> B3
    
    B3 --> C3
    
    V1 --> B3
    V2 --> B3
    V2 --> V1
    
    C2 --> C1
    
    style U fill:#fce4ec
    style D3 fill:#e3f2fd
    style C2 fill:#fff3e0
    style S3 fill:#f3e5f5
    style B1 fill:#e8f5e9
    style V2 fill:#fff9c4
```

## 新项目目录结构

```
Alpha101/
├── data/                          # 数据层
│   ├── __init__.py
│   ├── data_loader.py            # 数据加载器基类
│   ├── baostock_loader.py        # Baostock数据源
│   ├── joinquant_loader.py       # 聚宽数据源
│   ├── data_cleaner.py           # 数据清洗
│   ├── data_cache.py             # 数据缓存
│   └── data_api.py               # 统一数据接口
│
├── core/                          # 核心计算层
│   ├── __init__.py
│   ├── alpha_helpers.py          # 辅助函数
│   ├── alpha_factors.py          # Alpha101因子
│   ├── custom_factors.py         # 自定义因子
│   ├── factor_processor.py       # 因子处理
│   └── metrics.py                # 性能指标
│
├── signal/                        # 信号层
│   ├── __init__.py
│   ├── factor_selector.py        # 因子选择
│   ├── linear_model.py           # 线性模型
│   ├── ml_model.py               # 机器学习模型
│   ├── signal_generator.py       # 信号生成
│   └── portfolio_optimizer.py    # 组合优化
│
├── backtest/                      # 回测层
│   ├── __init__.py
│   ├── backtest_engine.py        # 回测引擎
│   ├── order_manager.py          # 订单管理
│   ├── execution.py              # 成交模拟
│   ├── risk_manager.py           # 风险管理
│   └── performance.py            # 性能分析
│
├── visualization/                 # 展示层
│   ├── __init__.py
│   ├── plotter.py                # 图表绘制
│   ├── report_generator.py       # 报告生成
│   ├── dashboard.py              # 交互式仪表板
│   └── exporter.py               # 数据导出
│
├── test/                          # 测试
│   ├── test_data_layer.py
│   ├── test_factors.py
│   ├── test_signals.py
│   └── test_backtest.py
│
├── examples/                      # 示例
│   ├── example_factor_analysis.py
│   ├── example_signal_generation.py
│   ├── example_backtest.py
│   └── example_full_pipeline.py
│
├── docs/                          # 文档
│   ├── ARCHITECTURE.md           # 架构文档
│   ├── API_REFERENCE.md          # API参考
│   ├── USER_GUIDE.md             # 用户指南
│   └── DEVELOPMENT.md            # 开发指南
│
├── config/                        # 配置
│   ├── data_config.yaml          # 数据配置
│   ├── factor_config.yaml        # 因子配置
│   ├── model_config.yaml         # 模型配置
│   └── backtest_config.yaml      # 回测配置
│
├── requirements.txt               # 依赖
├── setup.py                       # 安装脚本
└── README.md                      # 项目说明
```

## 使用示例

### 完整流程示例

```python
from data.data_api import DataAPI
from core.alpha_factors import calculate_all_factors
from signal.ml_model import XGBoostFactorModel
from signal.signal_generator import SignalGenerator
from backtest.backtest_engine import BacktestEngine
from visualization.report_generator import ReportGenerator

# 1. 数据层：获取数据
data_api = DataAPI(source='baostock')
stock_data = data_api.get_stock_data(
    symbols=['000001.SZ', '000002.SZ'],
    start_date='2023-01-01',
    end_date='2024-01-01'
)

# 2. 计算层：计算因子
factors = calculate_all_factors(stock_data, factor_list=['alpha001', 'alpha002', 'alpha003'])

# 3. 信号层：训练模型并生成信号
model = XGBoostFactorModel()
model.train(factors, target='future_return_5d')

signal_gen = SignalGenerator(model)
signals = signal_gen.generate_signals(factors, method='ranking', top_n=10)

# 4. 回测层：执行回测
engine = BacktestEngine(
    initial_capital=1000000,
    commission=0.0003,
    slippage=0.001
)
results = engine.run(stock_data, signals)

# 5. 展示层：生成报告
report = ReportGenerator()
report.generate(results, output='backtest_report.html')
report.plot_equity_curve(results)
```

## 关键设计原则

1. **模块化**: 每层独立，接口清晰
2. **可扩展**: 易于添加新因子、新模型、新数据源
3. **可配置**: 通过配置文件管理参数
4. **可测试**: 每个模块都有单元测试
5. **高性能**: 向量化计算，支持并行处理
6. **易用性**: 提供简洁的API和丰富的示例

## 下一步行动

1. 重构现有代码到新架构
2. 实现数据层的统一接口
3. 完善核心计算层的性能指标
4. 实现信号层的因子模型
5. 构建完整的回测引擎
6. 开发可视化和报告系统
