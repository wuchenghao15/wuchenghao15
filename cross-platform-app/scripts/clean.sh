#!/bin/bash

# 清理脚本
echo "=========================================="
echo "  清理项目"
echo "=========================================="
echo ""

# 清理Node模块
echo "[1/5] 清理Node模块..."
rm -rf node_modules
echo "✓ node_modules已删除"

# 清理构建产物
echo ""
echo "[2/5] 清理Android构建..."
if [ -d "android" ]; then
    cd android
    ./gradlew clean
    rm -rf .gradle
    rm -rf build
    rm -rf app/build
    cd ..
fi
echo "✓ Android构建已清理"

# 清理缓存
echo ""
echo "[3/5] 清理React Native缓存..."
rm -rf $TMPDIR/react-*
rm -rf $TMPDIR/metro-*
rm -rf $TMPDIR/haste-*
echo "✓ 缓存已清理"

# 清理dist和packages
echo ""
echo "[4/5] 清理输出目录..."
rm -rf dist
rm -rf packages
echo "✓ 输出目录已清理"

# 清理iOS构建
echo ""
echo "[5/5] 清理iOS构建..."
if [ -d "ios" ]; then
    cd ios
    rm -rf build
    rm -rf Pods
    rm -rf Podfile.lock
    cd ..
fi
echo "✓ iOS构建已清理"

echo ""
echo "=========================================="
echo "  清理完成！"
echo "=========================================="
echo ""
echo "接下来请运行：npm install"
echo ""
