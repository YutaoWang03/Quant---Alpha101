# Quant - Alpha101

## 项目简介

本项目包含了 Alpha 101 因子的完整实现和文档，旨在为量化交易策略开发提供参考。Alpha 101 是一组经典的量化交易因子，由论文《101 Formulaic Alphas》提出，包含了多种基于价格、成交量等市场数据的因子设计。

## 项目架构

```
Alpha101/
├── core/                           # 核心计算代码
│   ├── alpha_factors.py           # Alpha因子核心实现
│   ├── alpha_helpers.py           # 辅助函数和工具
│   ├── alpha101_functions.py      # Alpha101函数库
│   ├── jq_alpha001_strategy.py    # 聚宽Alpha001策略
│   └── jq_alpha1_strategy.py      # 聚宽Alpha1策略
├── test/                          # 测试文件
│   ├── alpha001_local_test.py     # Alpha001本地测试
│   ├── quick_test_alpha001.py     # Alpha001快速测试
│   └── test_alpha001_baostock.py  # Baostock数据测试
├── docs/                          # 文档和学习资料
│   ├── Alpha 101 Learning.md      # Alpha因子详细说明
│   ├── Alpha101 Learning.ipynb    # 代码实现文档
│   ├── README_Alpha101.md         # Alpha101专项说明
│   └── README_Testing.md          # 测试说明文档
├── source/                        # 静态资源和数据
│   ├── Alpha101.pdf              # 原始论文
│   ├── notebook_cells_content.txt # Notebook内容
│   └── pdf_b64_temp.txt          # 临时数据文件
├── requirements.txt               # 项目依赖
└── README.md                     # 项目主说明
```

## 核心模块说明

### core/ - 核心计算代码
- **alpha_factors.py**: Alpha因子的核心实现，包含所有101个因子的计算逻辑
- **alpha_helpers.py**: 提供数据处理、技术指标计算等辅助函数
- **alpha101_functions.py**: Alpha101因子库的完整函数实现
- **jq_alpha001_strategy.py**: 基于聚宽平台的Alpha001策略实现
- **jq_alpha1_strategy.py**: 基于聚宽平台的Alpha1策略实现

### test/ - 测试模块
- **alpha001_local_test.py**: Alpha001因子的本地测试脚本
- **quick_test_alpha001.py**: Alpha001因子的快速验证测试
- **test_alpha001_baostock.py**: 使用Baostock数据源的完整测试

### docs/ - 文档模块
- **Alpha 101 Learning.md**: 所有101个Alpha因子的详细说明和逻辑解读
- **Alpha101 Learning.ipynb**: 交互式代码实现和分析文档
- **README_Alpha101.md**: Alpha101因子的专项技术说明
- **README_Testing.md**: 测试框架和使用说明

### source/ - 资源模块
- **Alpha101.pdf**: 《101 Formulaic Alphas》原始论文
- **notebook_cells_content.txt**: Jupyter Notebook单元格内容备份
- **pdf_b64_temp.txt**: PDF文件的Base64编码临时文件

## 因子类型

Alpha 101 因子涵盖了多种量化交易策略类型：

1. **动量策略**：基于价格趋势的延续性
2. **均值回归策略**：基于价格回归到均值的假设
3. **成交量分析**：基于成交量变化与价格关系
4. **价格模式识别**：基于价格形态和模式
5. **行业中性化**：去除行业因素的影响
6. **时间序列分析**：基于历史数据的时间序列模式
7. **横截面分析**：基于不同资产间的相对表现

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-username/Alpha101.git
cd Alpha101

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 快速测试Alpha001因子
python test/quick_test_alpha001.py

# 完整测试（需要网络连接获取数据）
python test/test_alpha001_baostock.py

# 本地测试
python test/alpha001_local_test.py
```

### 3. 使用核心模块

```python
# 导入Alpha因子
from core.alpha_factors import Alpha001
from core.alpha_helpers import get_stock_data

# 获取数据并计算因子
data = get_stock_data('000001.SZ', '2023-01-01', '2023-12-31')
alpha001_value = Alpha001(data)
```

## 因子类型

Alpha 101 因子涵盖了多种量化交易策略类型：

1. **动量策略**：基于价格趋势的延续性
2. **均值回归策略**：基于价格回归到均值的假设
3. **成交量分析**：基于成交量变化与价格关系
4. **价格模式识别**：基于价格形态和模式
5. **行业中性化**：去除行业因素的影响
6. **时间序列分析**：基于历史数据的时间序列模式
7. **横截面分析**：基于不同资产间的相对表现

## 开发指南

### 添加新因子

1. 在 `core/alpha_factors.py` 中实现因子计算逻辑
2. 在 `test/` 目录下添加对应的测试文件
3. 更新 `docs/` 中的相关文档

### 测试框架

项目使用分层测试策略：
- **单元测试**: 测试单个因子的计算逻辑
- **集成测试**: 测试数据获取和因子计算的完整流程
- **性能测试**: 测试因子计算的效率和准确性

### 数据源支持

- **Baostock**: 免费的A股历史数据
- **聚宽(JoinQuant)**: 专业量化平台数据接口
- **自定义数据源**: 支持CSV、Excel等格式的本地数据

## 性能优化

- 使用向量化计算提高因子计算效率
- 支持多进程并行计算多个因子
- 内存优化的数据处理流程
- 缓存机制减少重复计算

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 参考资料

- [《101 Formulaic Alphas》原始论文](source/Alpha101.pdf)
- [Baostock数据接口文档](http://baostock.com/)
- [聚宽量化平台](https://www.joinquant.com/)
- [量化交易相关资源](docs/README_Alpha101.md)

## 联系方式

- 项目维护者: [Your Name]
- 邮箱: your.email@example.com
- 项目主页: https://github.com/your-username/Alpha101

---

**注意**: 本项目仅供学习和研究使用，不构成投资建议。量化交易存在风险，请谨慎使用。
