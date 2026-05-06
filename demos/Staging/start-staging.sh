#!/bin/bash

# 灰度测试环境启动脚本

set -e
echo "==================================="
echo "启动灰度测试环境..."
echo "==================================="

# 设置环境变量
export NODE_ENV=staging
export BASE_PATH="$(pwd)"

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "错误: Node.js未安装"
    exit 1
fi

# 检查staging-manager.js是否存在
if [ ! -f "staging-manager.js" ]; then
    echo "错误: staging-manager.js不存在"
    exit 1
fi

# 创建日志目录
mkdir -p "Logs"

# 启动环境管理器
echo "启动环境管理器..."
node staging-manager.js > "Logs/startup-$(date +%Y%m%d).log" 2>&1 &

MANAGER_PID=$!
echo "环境管理器已启动，PID: $MANAGER_PID"

# 等待管理器初始化
echo "等待环境初始化..."
sleep 5

# 检查进程是否仍在运行
if ps -p $MANAGER_PID > /dev/null; then
    echo "==================================="
    echo "灰度测试环境启动成功!"
    echo "环境管理器PID: $MANAGER_PID"
    echo "日志文件: Logs/startup-$(date +%Y%m%d).log"
    echo "==================================="
    
    # 保存PID到文件
    echo $MANAGER_PID > .manager-pid
    echo "PID已保存到 .manager-pid"
else
    echo "错误: 环境管理器启动失败"
    echo "请检查日志: Logs/startup-$(date +%Y%m%d).log"
    exit 1
fi
