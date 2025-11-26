#!/bin/bash

# 依赖项升级脚本
# 用途: 更新测试环境的依赖项并检查兼容性

echo "================================="
echo "开始执行依赖项升级..."
echo "================================="

# 检查是否在正确的目录
if [ ! -f "../config/staging-environment.json" ]; then
    echo "错误: 请在项目根目录下执行此脚本"
    exit 1
fi

# 设置环境变量
export NODE_ENV=staging

# 创建备份
echo "创建依赖项备份..."
if [ -f "package.json" ]; then
    cp package.json package.json.bak
    echo "✓ 已备份 package.json"
fi

if [ -f "package-lock.json" ]; then
    cp package-lock.json package-lock.json.bak
    echo "✓ 已备份 package-lock.json"
fi

# 安装npm-check-updates工具（如果不存在）
echo "检查更新工具..."
npm list -g npm-check-updates > /dev/null 2>&1 || npm install -g npm-check-updates

# 检查可用更新
echo "\n检查可用更新..."
ncu --format group > update-report.md
echo "✓ 已生成更新报告: update-report.md"

# 显示更新摘要
head -20 update-report.md

# 询问是否继续
read -p "\n是否继续执行更新？(y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消更新操作"
    exit 0
fi

# 执行更新
echo "\n开始执行更新..."
ncu -u --upgrade

# 安装更新的依赖
echo "\n安装更新的依赖项..."
npm install

# 运行测试（如果有）
if [ -f "test.js" ] || [ -d "tests" ]; then
    echo "\n运行测试以验证更新..."
    if command -v npm test > /dev/null; then
        npm test || echo "警告: 测试失败，但更新已完成"
    else
        echo "注意: 未找到npm test命令，跳过测试"
    fi
fi

# 清理备份
echo "\n清理旧备份文件..."
find . -name "package.json.bak.*" -delete
find . -name "package-lock.json.bak.*" -delete

# 重命名当前备份
if [ -f "package.json.bak" ]; then
    mv package.json.bak "package.json.bak.$(date +%Y%m%d)"
fi
if [ -f "package-lock.json.bak" ]; then
    mv package-lock.json.bak "package-lock.json.bak.$(date +%Y%m%d)"
fi

echo "\n================================="
echo "依赖项升级完成!"
echo "报告文件: update-report.md"
echo "================================="
