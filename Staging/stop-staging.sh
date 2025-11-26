#!/bin/bash

# 灰度测试环境停止脚本

echo "==================================="
echo "停止灰度测试环境..."
echo "==================================="

# 检查PID文件
if [ ! -f ".manager-pid" ]; then
    echo "警告: .manager-pid文件不存在，尝试查找进程..."
    
    # 尝试通过进程名查找
    MANAGER_PID=$(ps aux | grep "[s]taging-manager.js" | awk '{print $2}')
    
    if [ -z "$MANAGER_PID" ]; then
        echo "错误: 未找到运行中的环境管理器进程"
        exit 1
    fi
else
    MANAGER_PID=$(cat .manager-pid)
fi

echo "找到环境管理器进程，PID: $MANAGER_PID"

# 尝试优雅停止
if ps -p $MANAGER_PID > /dev/null; then
    echo "发送终止信号..."
    kill $MANAGER_PID
    
    # 等待进程终止
    echo "等待进程终止..."
    for i in {1..10}; do
        if ! ps -p $MANAGER_PID > /dev/null; then
            echo "进程已终止"
            break
        fi
        sleep 1
    done
    
    # 如果进程仍在运行，强制终止
    if ps -p $MANAGER_PID > /dev/null; then
        echo "进程未正常终止，尝试强制终止..."
        kill -9 $MANAGER_PID
    fi
else
    echo "进程已不存在"
fi

# 清理PID文件
if [ -f ".manager-pid" ]; then
    rm .manager-pid
    echo "已清理PID文件"
fi

echo "==================================="
echo "灰度测试环境停止完成!"
echo "==================================="
