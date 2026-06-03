#!/bin/bash

set -e

APP_NAME="MTSCOS"
VERSION="2.0.0"
BUILD_DIR="build"
OUTPUT_DIR="dist"

echo "=========================================="
echo "  ${APP_NAME} 构建脚本"
echo "  版本: ${VERSION}"
echo "=========================================="

# 创建输出目录
mkdir -p ${OUTPUT_DIR}

function build_android() {
    echo ""
    echo "[Android] 开始构建..."
    
    cd android
    
    # 清理构建
    ./gradlew clean
    
    # 构建发布版本
    echo "[Android] 构建普通版..."
    ./gradlew assembleRelease
    
    # 构建HyperOS版本
    echo "[Android] 构建HyperOS版..."
    ./gradlew assembleHyperosRelease
    
    # 构建HarmonyOS版本
    echo "[Android] 构建HarmonyOS版..."
    ./gradlew assembleHarmonyosRelease
    
    # 复制APK到输出目录
    cp app/build/outputs/apk/release/*.apk ../${OUTPUT_DIR}/
    cp app/build/outputs/apk/hyperos/release/*.apk ../${OUTPUT_DIR}/
    cp app/build/outputs/apk/harmonyos/release/*.apk ../${OUTPUT_DIR}/
    
    cd ..
    
    echo "[Android] 构建完成!"
}

function build_harmonyos() {
    echo ""
    echo "[HarmonyOS] 开始构建..."
    
    cd harmonyos
    
    # 安装依赖
    hpm install
    
    # 构建调试版
    echo "[HarmonyOS] 构建调试版..."
    ohos build --mode debug
    
    # 构建发布版
    echo "[HarmonyOS] 构建发布版..."
    ohos build --mode release
    
    # 签名
    echo "[HarmonyOS] 签名..."
    ohos sign
    
    # 复制HAP到输出目录
    cp build/default/outputs/default/*.hap ../${OUTPUT_DIR}/
    
    cd ..
    
    echo "[HarmonyOS] 构建完成!"
}

function build_all() {
    echo ""
    echo "开始构建所有平台..."
    
    # 清理旧构建
    rm -rf ${OUTPUT_DIR}/*
    
    # 构建Android
    build_android
    
    # 构建HarmonyOS
    build_harmonyos
    
    echo ""
    echo "=========================================="
    echo "  构建完成!"
    echo "=========================================="
    echo "输出目录: ${OUTPUT_DIR}/"
    ls -la ${OUTPUT_DIR}/
}

function show_help() {
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -a, --android    仅构建Android版本"
    echo "  -h, --harmonyos  仅构建HarmonyOS版本"
    echo "  -a11, --all      构建所有版本"
    echo "  -h, --help       显示此帮助信息"
    echo ""
}

case "$1" in
    -a|--android)
        build_android
        ;;
    -hm|--harmonyos)
        build_harmonyos
        ;;
    -all|--all)
        build_all
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