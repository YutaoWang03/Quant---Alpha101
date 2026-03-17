#!/bin/bash
# 安装项目依赖脚本

echo "正在安装 Alpha101 项目依赖..."

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    echo "检测到虚拟环境 .venv，正在激活..."
    source .venv/bin/activate
fi

# 安装依赖
echo "安装 requirements.txt 中的依赖..."
pip install -r requirements.txt

echo ""
echo "✓ 依赖安装完成！"
echo ""
echo "已安装的关键包："
pip list | grep -E "baostock|akshare|pandas|numpy"
