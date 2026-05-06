#!/bin/bash

# MTSCOS AI 项目部署脚本
# 目标服务器: 172.16.0.196
# 功能: 清理、整理、优化、初始化，并重启项目

set -e

echo "🚀 开始部署MTSCOS AI项目到 172.16.0.196..."

# 1. 清理和优化本地项目
echo "🧹 清理和优化本地项目..."
npm run clean || true

# 2. 检查项目结构
echo "📋 检查项目结构..."
ls -la

# 3. 创建部署目录结构
echo "📁 准备部署文件..."

# 4. 传输项目文件到目标服务器
echo "🌐 传输项目文件到目标服务器..."
scp -r ./* 172.16.0.196:/var/www/mtscos-ai-project/ || {
    echo "❌ SCP传输失败，尝试使用其他方式..."
    # 尝试使用rsync
    rsync -avz --exclude 'node_modules' --exclude 'Logs' --exclude 'storage' ./* 172.16.0.196:/var/www/mtscos-ai-project/ || {
        echo "❌ 所有传输方式失败，请检查网络连接和服务器配置"
        exit 1
    }
}

# 5. 连接到目标服务器并初始化项目
echo "🔧 在目标服务器上初始化项目..."
ssh 172.16.0.196 << 'EOF'
    cd /var/www/mtscos-ai-project/
    
    # 安装依赖
    echo "📦 安装项目依赖..."
    npm install --production
    
    # 确保目录存在
    echo "📁 创建必要的目录..."
    mkdir -p Logs storage data
    
    # 修复权限
    echo "🔒 修复文件权限..."
    chmod -R 755 .
    
    # 启动项目
    echo "🚀 启动MTSCOS AI项目服务器..."
    npm start &
    
    # 检查服务状态
    echo "📊 检查服务状态..."
    sleep 5
    curl -s http://localhost:8081/api/health || echo "⚠️  服务可能正在启动中..."
EOF

echo "🎉 部署完成！项目已发布到 http://172.16.0.196:8081"
echo "📋 部署信息:"
echo "   - 目标服务器: 172.16.0.196"
echo "   - 部署路径: /var/www/mtscos-ai-project/"
echo "   - 访问地址: http://172.16.0.196:8081"
echo "   - API端点: http://172.16.0.196:8081/api"
echo "   - 健康检查: http://172.16.0.196:8081/api/health"