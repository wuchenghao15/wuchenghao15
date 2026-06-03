#!/bin/bash

# MTSCOS 跨平台应用完整初始化脚本
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_DIR=$(pwd)
PROJECT_NAME="MTSCOS 智能学习系统"
VERSION="2.0.0"

print_title() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}  $PROJECT_NAME 初始化${NC}"
    echo -e "${BLUE}  版本: $VERSION${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo ""
}

print_step() {
    local step=$1
    local total=$2
    local desc=$3
    echo -e "${YELLOW}[$step/$total]${NC} $desc"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. 检查Node.js版本
check_nodejs() {
    print_step 1 10 "检查Node.js版本..."
    if ! command -v node &> /dev/null; then
        print_error "Node.js未安装"
        echo "请从 https://nodejs.org 安装最新版本（需要18.x或更高）"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js版本过低，需要18.x或更高，当前: $(node -v)"
        echo "请从 https://nodejs.org 安装最新版本"
        exit 1
    fi
    print_success "Node.js $(node -v)"
}

# 2. 检查npm
check_npm() {
    echo ""
    print_step 2 10 "检查npm..."
    if ! command -v npm &> /dev/null; then
        print_error "npm未安装"
        exit 1
    fi
    print_success "npm $(npm -v)"
}

# 3. 检查package.json
check_package() {
    echo ""
    print_step 3 10 "检查项目配置文件..."
    if [ ! -f "package.json" ]; then
        print_error "package.json文件不存在"
        exit 1
    fi
    print_success "package.json已找到"
}

# 4. 清理旧的依赖
clean_dependencies() {
    echo ""
    print_step 4 10 "清理旧的依赖文件..."
    if [ -d "node_modules" ]; then
        echo "正在删除node_modules..."
        rm -rf node_modules
    fi
    if [ -f "package-lock.json" ]; then
        rm -f package-lock.json
    fi
    print_success "旧依赖清理完成"
}

# 5. 安装依赖
install_dependencies() {
    echo ""
    print_step 5 10 "安装项目依赖..."
    npm install --legacy-peer-deps
    
    if [ $? -ne 0 ]; then
        print_error "依赖安装失败，尝试使用npm install --force"
        npm install --force --legacy-peer-deps
        if [ $? -ne 0 ]; then
            print_error "依赖安装失败"
            exit 1
        fi
    fi
    print_success "依赖安装完成"
}

# 6. 检查Android环境
check_android() {
    echo ""
    print_step 6 10 "检查Android开发环境..."
    ANDROID_OK=true
    
    if command -v adb &> /dev/null; then
        print_success "adb已安装"
    else
        print_warning "adb未安装，请安装Android SDK"
        ANDROID_OK=false
    fi
    
    if [ -n "$ANDROID_HOME" ] && [ -d "$ANDROID_HOME" ]; then
        print_success "ANDROID_HOME已设置: $ANDROID_HOME"
    elif [ -d "$HOME/Library/Android/sdk" ]; then
        print_success "Android SDK已找到 (macOS)"
        export ANDROID_HOME=$HOME/Library/Android/sdk
    elif [ -d "$HOME/Android/Sdk" ]; then
        print_success "Android SDK已找到 (Linux)"
        export ANDROID_HOME=$HOME/Android/Sdk
    else
        print_warning "未找到Android SDK"
        ANDROID_OK=false
    fi
    
    if [ "$ANDROID_OK" = false ]; then
        echo ""
        echo "Android开发环境配置建议："
        echo "1. 从 https://developer.android.com/studio 下载Android Studio"
        echo "2. 安装Android SDK (API 33+)"
        echo "3. 配置环境变量："
        echo "   export ANDROID_HOME=\$HOME/Library/Android/sdk"
        echo "   export PATH=\$PATH:\$ANDROID_HOME/emulator:\$ANDROID_HOME/tools:\$ANDROID_HOME/tools/bin:\$ANDROID_HOME/platform-tools"
    fi
}

# 7. 创建必要目录
create_directories() {
    echo ""
    print_step 7 10 "创建必要目录..."
    mkdir -p android/app/src/main/assets
    mkdir -p android/app/src/main/java/com/mtscos/app
    mkdir -p android/app/src/main/res/values
    mkdir -p android/app/src/main/res/drawable
    mkdir -p android/app/src/main/res/mipmap-hdpi
    mkdir -p android/app/src/main/res/mipmap-mdpi
    mkdir -p android/app/src/main/res/mipmap-xhdpi
    mkdir -p android/app/src/main/res/mipmap-xxhdpi
    mkdir -p android/app/src/main/res/mipmap-xxxhdpi
    mkdir -p packages
    mkdir -p dist
    mkdir -p src/config
    mkdir -p src/services
    mkdir -p src/screens
    print_success "目录创建完成"
}

# 8. 生成Android配置
generate_android_config() {
    echo ""
    print_step 8 10 "生成Android配置..."
    
    if [ ! -f "android/local.properties" ]; then
        if [ -n "$ANDROID_HOME" ] && [ -d "$ANDROID_HOME" ]; then
            echo "sdk.dir=$ANDROID_HOME" > android/local.properties
            print_success "从ANDROID_HOME生成local.properties"
        elif [ -d "$HOME/Library/Android/sdk" ]; then
            echo "sdk.dir=$HOME/Library/Android/sdk" > android/local.properties
            print_success "生成local.properties (macOS)"
        elif [ -d "$HOME/Android/Sdk" ]; then
            echo "sdk.dir=$HOME/Android/Sdk" > android/local.properties
            print_success "生成local.properties (Linux)"
        fi
    else
        print_success "local.properties已存在"
    fi
    
    if [ ! -f "android/gradle.properties" ]; then
        cat > android/gradle.properties << EOF
org.gradle.jvmargs=-Xmx2048m -XX:MaxMetaspaceSize=512m -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.configureondemand=true
android.useAndroidX=true
android.enableJetifier=true
reactNativeArchitectures=armeabi-v7a,arm64-v8a,x86,x86_64
newArchEnabled=false
EOF
        print_success "gradle.properties已生成"
    fi
}

# 9. 初始化配置文件
init_config() {
    echo ""
    print_step 9 10 "初始化配置文件..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# MTSCOS 环境配置
ENVIRONMENT=development
API_URL=http://localhost:8890
APP_VERSION=2.0.0
DEBUG=true
LOG_LEVEL=info
EOF
        print_success ".env文件已创建"
    fi
    
    if [ ! -f "src/config/system.config.js" ]; then
        bash scripts/configure-system.sh 2>/dev/null || true
        print_success "系统配置已生成"
    fi
    
    if [ ! -f "src/config/database.config.js" ]; then
        bash scripts/configure-database.sh 2>/dev/null || true
        print_success "数据库配置已生成"
    fi
    
    if [ ! -f "src/config/rules.config.js" ]; then
        bash scripts/configure-rules.sh 2>/dev/null || true
        print_success "规则配置已生成"
    fi
}

# 10. 检查设备状态
check_devices() {
    echo ""
    print_step 10 10 "检查设备状态..."
    
    if command -v adb &> /dev/null; then
        DEVICES=$(adb devices 2>/dev/null | grep -v "List of devices" | grep -v "^$" | wc -l)
        if [ "$DEVICES" -gt 0 ]; then
            print_success "发现 $DEVICES 个已连接的Android设备"
            adb devices 2>/dev/null
        else
            print_warning "未发现Android设备，请连接设备或启动模拟器"
        fi
    else
        print_warning "adb不可用，跳过设备检查"
    fi
}

# 主函数
main() {
    print_title
    
    echo -e "${BLUE}开始初始化...${NC}"
    echo ""
    
    check_nodejs
    check_npm
    check_package
    clean_dependencies
    install_dependencies
    check_android
    create_directories
    generate_android_config
    init_config
    check_devices
    
    echo ""
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}  初始化完成！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    
    echo -e "${BLUE}项目信息：${NC}"
    echo "  项目名称: $PROJECT_NAME"
    echo "  版本: $VERSION"
    echo "  Node.js: $(node -v)"
    echo "  工作目录: $PROJECT_DIR"
    echo ""
    
    echo -e "${BLUE}下一步操作：${NC}"
    echo "  1. 启动Android模拟器: npm run emulator"
    echo "  2. 运行Android调试: npm run android:debug"
    echo "  3. 启动开发服务器: npm start"
    echo "  4. 完整构建发布: npm run release"
    echo ""
    
    echo -e "${YELLOW}提示：${NC}"
    echo "  - 如果遇到依赖问题，运行: npm run reset"
    echo "  - 需要Android SDK和模拟器才能测试移动应用"
    echo ""
}

# 执行主函数
main "$@"
