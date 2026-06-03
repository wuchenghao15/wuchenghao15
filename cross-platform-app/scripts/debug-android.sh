#!/bin/bash

# MTSCOS Android调试脚本
echo "=========================================="
echo "  MTSCOS Android调试"
echo "=========================================="
echo ""

# 检查设备
echo "[1/6] 检查Android设备..."
DEVICES=$(adb devices 2>/dev/null | grep -v "List of devices" | grep -v "^$" | wc -l)
if [ "$DEVICES" -eq 0 ]; then
    echo "❌ 未发现Android设备"
    echo ""
    echo "请执行以下操作之一："
    echo "  1. 启动Android模拟器"
    echo "  2. 连接Android真机并开启USB调试"
    echo ""
    exit 1
fi
echo "✓ 发现 $DEVICES 个设备"
adb devices

# 启动Metro bundler
echo ""
echo "[2/6] 启动Metro打包器..."
if [ -z "$(lsof -ti:8081)" ]; then
    echo "启动Metro..."
    nohup npm start -- --reset-cache > metro.log 2>&1 &
    METRO_PID=$!
    echo "Metro PID: $METRO_PID"
    echo "等待Metro启动..."
    sleep 10
else
    echo "✓ Metro已在运行"
fi

# 检查依赖
echo ""
echo "[3/6] 检查Node依赖..."
if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install
fi
echo "✓ 依赖已就绪"

# 清理旧构建
echo ""
echo "[4/6] 清理旧构建..."
cd android
./gradlew clean
cd ..
echo "✓ 构建已清理"

# 构建并安装
echo ""
echo "[5/6] 构建并安装应用..."
react-native run-android --variant=androidDebug

if [ $? -eq 0 ]; then
    echo "✓ 应用安装成功"
else
    echo "❌ 安装失败"
    exit 1
fi

# 启动应用
echo ""
echo "[6/6] 启动应用..."
adb shell am start -n com.mtscos.app/.MainActivity
echo "✓ 应用已启动"

echo ""
echo "=========================================="
echo "  调试已启动！"
echo "=========================================="
echo ""
echo "调试提示："
echo "  - 按 d 键打开开发者菜单"
echo "  - 按 r 键重新加载JS"
echo "  - 查看日志: adb logcat -s ReactNativeJS:* ReactNative:* '*:E'"
echo "  - 停止Metro: pkill -f 'react-native'"
echo ""
echo "祝您调试愉快！"
echo ""
