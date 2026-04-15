#!/bin/bash

# MTSCOS AI 项目统一启动脚本
# 管理所有服务的启动和配置

echo "🚀 MTSCOS AI 项目启动脚本"
echo "================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python 3 未安装"
    exit 1
fi

# 显示服务配置
echo "📋 服务配置:"
echo "--------------------------------"
echo "主服务器: http://localhost:8080"
echo "Python服务器: http://localhost:8082"
echo "监控服务: http://localhost:8083"
echo ""

# 显示统一入口
echo "🔗 统一入口:"
echo "--------------------------------"
echo "维护入口: http://localhost:8080/api/health"
echo "后台入口: http://localhost:8082/python/dashboard"
echo "检测入口: http://localhost:8083/api/health"
echo "调试入口: http://localhost:8080/api/health"
echo "API接入入口: http://localhost:8080/api/auth"
echo "AI入口: http://localhost:8082/python/api/ai"
echo ""

# 启动主启动器
echo "🚀 启动 MTSCOS AI 多线程后台启动器..."

# 进入项目根目录
cd "$(dirname "$0")"

# 启动 Python 启动器
nohup python3 mtscos_ai_launcher.py > Logs/mtscos_ai_launcher.log 2>&1 &

# 保存 PID
echo $! > .mtscos_ai_launcher.pid

sleep 3

echo ""
echo "✅ MTSCOS AI 多线程后台启动器已启动!"
echo ""
echo "� 系统状态检查:"
echo "--------------------------------"
echo "启动器日志: Logs/mtscos_ai_launcher.log"
echo ""
echo "🎯 访问入口:"
echo "--------------------------------"
echo "首页: http://localhost:8080/html/index.html"
echo "后台管理: http://localhost:8082/python/dashboard"
echo "监控面板: http://localhost:8083/api/monitor/clients"
echo ""
echo "💡 提示: 使用 'kill -9 $(cat .mtscos_ai_launcher.pid)' 停止启动器"
echo "         或使用 './stop-all.sh' 停止所有服务"
