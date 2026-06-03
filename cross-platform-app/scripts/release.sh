#!/bin/bash

set -e

APP_NAME="MTSCOS"
VERSION="2.0.0"
BUILD_DIR="build"
OUTPUT_DIR="dist"
PACKAGE_DIR="packages"

echo "=========================================="
echo "  ${APP_NAME} 完整发布流程"
echo "  版本: ${VERSION}"
echo "=========================================="

function print_separator() {
    echo ""
    echo "------------------------------------------"
    echo ""
}

function setup_environment() {
    echo "[环境] 检查构建环境..."
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        echo "错误: 未找到Node.js，请安装Node.js 18+"
        exit 1
    fi
    echo "✓ Node.js: $(node --version)"
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        echo "错误: 未找到npm"
        exit 1
    fi
    echo "✓ npm: $(npm --version)"
    
    # 检查Java
    if ! command -v java &> /dev/null; then
        echo "错误: 未找到Java，请安装JDK 11+"
        exit 1
    fi
    echo "✓ Java: $(java -version 2>&1 | head -n 1)"
    
    # 检查Gradle
    if ! command -v gradle &> /dev/null; then
        echo "警告: 未找到Gradle，将使用Android项目中的gradlew"
    fi
    
    # 检查hpm (HarmonyOS)
    if ! command -v hpm &> /dev/null; then
        echo "警告: 未找到hpm CLI (HarmonyOS构建工具)"
    fi
    
    echo "[环境] 环境检查完成!"
}

function install_dependencies() {
    echo "[依赖] 安装项目依赖..."
    
    # 安装npm依赖
    npm install
    
    # 安装cocoapods (iOS)
    if command -v pod &> /dev/null && [ -d "ios" ]; then
        echo "[依赖] 安装iOS依赖..."
        cd ios && pod install && cd ..
    fi
    
    echo "[依赖] 依赖安装完成!"
}

function build_project() {
    echo "[构建] 开始构建项目..."
    
    # 运行构建脚本
    bash scripts/build.sh --all
    
    echo "[构建] 构建完成!"
}

function package_project() {
    echo "[打包] 开始打包..."
    
    # 运行打包脚本
    bash scripts/package.sh --all
    
    echo "[打包] 打包完成!"
}

function create_distribution() {
    echo "[分发] 创建分发包..."
    
    # 创建分发目录
    DISTRIBUTION_DIR="${PACKAGE_DIR}/distribution"
    mkdir -p ${DISTRIBUTION_DIR}
    
    # 创建压缩包
    echo "[分发] 创建ZIP压缩包..."
    cd ${PACKAGE_DIR}
    zip -r "${APP_NAME}_v${VERSION}_all_platforms.zip" *.apk *.hap checksums.* RELEASE_NOTES.md
    
    # 创建tar.gz压缩包
    echo "[分发] 创建tar.gz压缩包..."
    tar -czvf "${APP_NAME}_v${VERSION}_all_platforms.tar.gz" *.apk *.hap checksums.* RELEASE_NOTES.md
    
    cd ..
    
    echo "[分发] 分发包创建完成!"
}

function show_summary() {
    echo ""
    echo "=========================================="
    echo "  发布完成!"
    echo "=========================================="
    echo ""
    echo "📱 生成的安装包:"
    echo ""
    
    if [ -d "${PACKAGE_DIR}" ]; then
        ls -la "${PACKAGE_DIR}/"*.apk 2>/dev/null || true
        ls -la "${PACKAGE_DIR}/"*.hap 2>/dev/null || true
        ls -la "${PACKAGE_DIR}/"*.zip 2>/dev/null || true
        ls -la "${PACKAGE_DIR}/"*.tar.gz 2>/dev/null || true
    fi
    
    echo ""
    echo "📋 发布说明: ${PACKAGE_DIR}/RELEASE_NOTES.md"
    echo "🔍 校验文件: ${PACKAGE_DIR}/checksums.md5"
    echo "🔍 校验文件: ${PACKAGE_DIR}/checksums.sha256"
    echo ""
    echo "=========================================="
}

function release_all() {
    print_separator
    setup_environment
    
    print_separator
    install_dependencies
    
    print_separator
    build_project
    
    print_separator
    package_project
    
    print_separator
    create_distribution
    
    print_separator
    show_summary
}

function show_help() {
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -e, --env        仅检查环境"
    echo "  -d, --deps       仅安装依赖"
    echo "  -b, --build      仅构建"
    echo "  -p, --package    仅打包"
    echo "  -all, --all      完整发布流程"
    echo "  -h, --help       显示此帮助信息"
    echo ""
}

case "$1" in
    -e|--env)
        setup_environment
        ;;
    -d|--deps)
        install_dependencies
        ;;
    -b|--build)
        build_project
        ;;
    -p|--package)
        package_project
        ;;
    -all|--all)
        release_all
        ;;
    -h|--help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac

exit 0