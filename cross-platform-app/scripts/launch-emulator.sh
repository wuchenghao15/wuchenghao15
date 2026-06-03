#!/bin/bash

# 启动Android模拟器脚本
echo "=========================================="
echo "  启动Android模拟器"
echo "=========================================="
echo ""

# 查找可用的模拟器
echo "[1/3] 查找可用的模拟器..."
AVDS=$(emulator -list-avds 2>/dev/null)

if [ -z "$AVDS" ]; then
    echo "❌ 未找到可用的Android模拟器"
    echo ""
    echo "请通过以下步骤创建模拟器："
    echo "  1. 打开Android Studio"
    echo "  2. 点击 Tools -> Device Manager"
    echo "  3. 点击 Create Device"
    echo "  4. 选择设备和系统镜像"
    echo "  5. 完成创建"
    echo ""
    exit 1
fi

echo "✓ 发现以下模拟器："
echo "$AVDS"
echo ""

# 如果只有一个模拟器，直接启动
AVD_COUNT=$(echo "$AVDS" | wc -l)
if [ "$AVD_COUNT" -eq 1 ]; then
    SELECTED_AVD=$(echo "$AVDS" | head -1)
    echo "[2/3] 自动选择模拟器: $SELECTED_AVD"
else
    # 让用户选择
    echo "[2/3] 请选择要启动的模拟器："
    echo "$AVDS" | nl -w 2 -s '. '
    echo ""
    read -p "输入编号: " AVD_NUM
    SELECTED_AVD=$(echo "$AVDS" | sed -n "${AVD_NUM}p")
    
    if [ -z "$SELECTED_AVD" ]; then
        echo "❌ 无效的选择"
        exit 1
    fi
fi

# 检查模拟器是否已在运行
echo ""
echo "[3/3] 检查模拟器状态..."
RUNNING=$(adb devices 2>/dev/null | grep -v "List of devices" | grep -v "^$" | wc -l)
if [ "$RUNNING" -gt 0 ]; then
    echo "⚠️ 检测到已有设备/模拟器在运行"
    read -p "是否继续启动新的模拟器？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消"
        exit 0
    fi
fi

# 启动模拟器
echo ""
echo "正在启动模拟器: $SELECTED_AVD"
echo "按 Ctrl+C 停止模拟器（这不会关闭正在运行的模拟器）"
echo ""

# 在后台启动模拟器
nohup emulator -avd "$SELECTED_AVD" -no-snapshot-load > emulator.log 2>&1 &
EMULATOR_PID=$!
echo "模拟器PID: $EMULATOR_PID"
echo "日志输出到: emulator.log"

# 等待设备上线
echo ""
echo "等待模拟器启动..."
echo "这可能需要几分钟..."

COUNT=0
MAX_WAIT=300
while [ $COUNT -lt $MAX_WAIT ]; do
    DEVICES=$(adb devices 2>/dev/null | grep -v "List of devices" | grep "device$" | wc -l)
    if [ "$DEVICES" -gt 0 ]; then
        echo ""
        echo "✓ 模拟器已启动！"
        break
    fi
    printf "."
    sleep 2
    COUNT=$((COUNT + 2))
done

if [ $COUNT -ge $MAX_WAIT ]; then
    echo ""
    echo "⚠️ 等待超时，但模拟器可能仍在启动"
fi

echo ""
echo "=========================================="
echo "  模拟器已启动！"
echo "=========================================="
echo ""
echo "接下来可以运行："
echo "  npm run android:debug"
echo ""
echo "查看模拟器日志："
echo "  tail -f emulator.log"
echo ""
