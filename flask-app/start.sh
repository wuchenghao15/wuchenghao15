#!/bin/bash

# MTSCOS AI Web 应用启动脚本

echo "=========================================="
echo "MTSCOS AI Web 应用启动脚本"
echo "=========================================="

# 检查Python版本
echo "检查Python版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误：Python3未安装，请先安装Python3"
    exit 1
fi

# 创建虚拟环境
echo "\n创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "\n激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "\n安装项目依赖..."
pip install -r requirements.txt

# 检查是否安装成功
if [ $? -ne 0 ]; then
    echo "\n错误：依赖安装失败"
    exit 1
fi

echo "\n依赖安装成功！"

# 启动应用
echo "\n启动应用..."
echo "应用将在 http://localhost:8080 上运行"
echo "按 Ctrl+C 停止应用"
echo "=========================================="

# 运行应用
python app.py
