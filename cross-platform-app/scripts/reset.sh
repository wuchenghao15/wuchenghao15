#!/bin/bash

# 完整重置脚本
echo "=========================================="
echo "  完整重置项目"
echo "=========================================="
echo ""

read -p "这将删除所有本地数据，确定要继续吗？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消"
    exit 0
fi

# 执行清理
bash scripts/clean.sh

# 重新安装依赖
echo ""
echo "重新安装依赖..."
npm install

# 安装iOS pods
if [ -d "ios" ]; then
    cd ios
    pod install
    cd ..
fi

echo ""
echo "=========================================="
echo "  重置完成！"
echo "=========================================="
echo ""
