#!/bin/bash

# Android开发环境自动配置脚本
echo "=========================================="
echo "  Android开发环境自动配置"
echo "=========================================="
echo ""

# 检查是否为macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ 此脚本仅支持macOS"
    exit 1
fi

SDK_DIR="$HOME/Library/Android/sdk"
CMD_TOOLS_DIR="$SDK_DIR/cmdline-tools/latest"

# 检查是否已有Android SDK
check_sdk() {
    if [ -d "$SDK_DIR" ] && [ -f "$CMD_TOOLS_DIR/bin/sdkmanager" ]; then
        echo "✓ Android SDK已安装"
        return 0
    else
        return 1
    fi
}

# 安装SDK
install_sdk() {
    echo "[1/4] 下载并安装Android SDK..."
    
    # 创建目录
    mkdir -p "$SDK_DIR/cmdline-tools"
    
    # 下载命令行工具（macOS版本）
    SDK_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-mac-10406996_latest.zip"
    TEMP_ZIP=$(mktemp).zip
    
    echo "下载SDK工具..."
    curl -L -o "$TEMP_ZIP" "$SDK_TOOLS_URL"
    
    if [ $? -ne 0 ]; then
        echo "❌ 下载失败"
        rm -f "$TEMP_ZIP"
        exit 1
    fi
    
    echo "解压SDK工具..."
    unzip -q "$TEMP_ZIP" -d "$SDK_DIR/cmdline-tools"
    rm -f "$TEMP_ZIP"
    
    # 重命名目录
    mv "$SDK_DIR/cmdline-tools/cmdline-tools" "$SDK_DIR/cmdline-tools/latest"
    
    echo "✓ SDK安装完成"
}

# 安装必要组件
install_components() {
    echo "[2/4] 安装Android SDK组件..."
    
    # 接受许可
    echo "接受SDK许可..."
    yes | "$CMD_TOOLS_DIR/bin/sdkmanager" --licenses > /dev/null 2>&1
    
    # 安装组件
    echo "安装平台和工具..."
    "$CMD_TOOLS_DIR/bin/sdkmanager" "platforms;android-34" "build-tools;34.0.0" "emulator" "platform-tools" "system-images;android-34;google_apis_playstore;arm64-v8a"
    
    if [ $? -eq 0 ]; then
        echo "✓ 组件安装完成"
    else
        echo "❌ 组件安装失败"
        exit 1
    fi
}

# 配置环境变量
configure_env() {
    echo "[3/4] 配置环境变量..."
    
    # 检测shell类型
    if [ -f "$HOME/.zshrc" ]; then
        RC_FILE="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        RC_FILE="$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        RC_FILE="$HOME/.bash_profile"
    else
        RC_FILE="$HOME/.zshrc"
    fi
    
    # 添加环境变量
    ANDROID_ENV="
# Android SDK Environment
export ANDROID_HOME=$SDK_DIR
export PATH=\$PATH:\$ANDROID_HOME/emulator
export PATH=\$PATH:\$ANDROID_HOME/tools
export PATH=\$PATH:\$ANDROID_HOME/tools/bin
export PATH=\$PATH:\$ANDROID_HOME/platform-tools
"
    
    # 检查是否已存在
    if ! grep -q "ANDROID_HOME=$SDK_DIR" "$RC_FILE" 2>/dev/null; then
        echo "$ANDROID_ENV" >> "$RC_FILE"
        echo "✓ 环境变量已添加到 $RC_FILE"
    else
        echo "✓ 环境变量已存在"
    fi
    
    # 立即生效
    export ANDROID_HOME="$SDK_DIR"
    export PATH="$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/tools:$ANDROID_HOME/tools/bin:$ANDROID_HOME/platform-tools"
}

# 创建模拟器
create_emulator() {
    echo "[4/4] 创建Android模拟器..."
    
    # 检查是否已有模拟器
    EMULATOR_NAME="MTSCOS_Emulator"
    if "$CMD_TOOLS_DIR/bin/avdmanager" list avd | grep -q "$EMULATOR_NAME"; then
        echo "✓ 模拟器 $EMULATOR_NAME 已存在"
        return
    fi
    
    # 创建模拟器
    echo "创建模拟器 $EMULATOR_NAME..."
    "$CMD_TOOLS_DIR/bin/avdmanager" create avd -n "$EMULATOR_NAME" -k "system-images;android-34;google_apis_playstore;arm64-v8a" --device "pixel_6" --force
    
    if [ $? -eq 0 ]; then
        echo "✓ 模拟器创建完成"
    else
        echo "⚠️ 模拟器创建可能失败，您可以通过Android Studio手动创建"
    fi
}

# 主流程
main() {
    if check_sdk; then
        echo "检测到已安装的SDK"
    else
        install_sdk
    fi
    
    install_components
    configure_env
    create_emulator
    
    echo ""
    echo "=========================================="
    echo "  Android环境配置完成！"
    echo "=========================================="
    echo ""
    echo "接下来："
    echo "  1. 重启终端或运行: source $HOME/.zshrc"
    echo "  2. 启动模拟器: npm run emulator"
    echo "  3. 运行应用: npm run android:debug"
    echo ""
    echo "验证安装:"
    echo "  adb devices"
    echo "  emulator -list-avds"
    echo ""
}

# 执行主流程
main