#!/bin/bash

set -e

APP_NAME="MTSCOS"
VERSION="2.0.0"
BUILD_DIR="build"
OUTPUT_DIR="dist"
PACKAGE_DIR="packages"

echo "=========================================="
echo "  ${APP_NAME} 打包脚本"
echo "  版本: ${VERSION}"
echo "=========================================="

# 创建打包目录
mkdir -p ${PACKAGE_DIR}

function package_apk() {
    echo ""
    echo "[APK] 开始打包APK..."
    
    # 查找APK文件
    APK_FILES=$(find ${OUTPUT_DIR} -name "*.apk" 2>/dev/null)
    
    if [ -z "$APK_FILES" ]; then
        echo "错误: 未找到APK文件，请先运行构建脚本"
        exit 1
    fi
    
    for apk in ${APK_FILES}; do
        filename=$(basename "$apk")
        platform=$(echo "$filename" | sed 's/.*-\([a-z]*\)-release\.apk/\1/')
        
        case "$platform" in
            "hyperos")
                display_name="MTSCOS_HyperOS_v${VERSION}"
                ;;
            "harmonyos")
                display_name="MTSCOS_HarmonyOS_Android_v${VERSION}"
                ;;
            *)
                display_name="MTSCOS_Android_v${VERSION}"
                ;;
        esac
        
        echo "打包: ${display_name}.apk"
        cp "$apk" "${PACKAGE_DIR}/${display_name}.apk"
    done
    
    echo "[APK] APK打包完成!"
}

function package_harmonyos() {
    echo ""
    echo "[HarmonyOS] 开始打包HAP..."
    
    # 查找HAP文件
    HAP_FILES=$(find ${OUTPUT_DIR} -name "*.hap" 2>/dev/null)
    
    if [ -z "$HAP_FILES" ]; then
        echo "警告: 未找到HAP文件"
        return
    fi
    
    for hap in ${HAP_FILES}; do
        filename=$(basename "$hap")
        display_name="MTSCOS_HarmonyOS_v${VERSION}"
        
        echo "打包: ${display_name}.hap"
        cp "$hap" "${PACKAGE_DIR}/${display_name}.hap"
    done
    
    echo "[HarmonyOS] HAP打包完成!"
}

function create_checksum() {
    echo ""
    echo "[校验] 生成校验文件..."
    
    cd ${PACKAGE_DIR}
    
    # 生成MD5校验
    md5sum *.apk *.hap 2>/dev/null > checksums.md5 || true
    
    # 生成SHA256校验
    sha256sum *.apk *.hap 2>/dev/null > checksums.sha256 || true
    
    cd ..
    
    echo "[校验] 校验文件生成完成!"
}

function create_release_note() {
    echo ""
    echo "[文档] 生成发布说明..."
    
    RELEASE_NOTE="${PACKAGE_DIR}/RELEASE_NOTES.md"
    
    cat > ${RELEASE_NOTE} << EOF
# ${APP_NAME} v${VERSION} 发布说明

## 📱 支持平台

| 平台 | 文件 | 说明 |
|------|------|------|
| Android | ${APP_NAME}_Android_v${VERSION}.apk | 通用Android版本 |
| HyperOS | ${APP_NAME}_HyperOS_v${VERSION}.apk | 小米HyperOS专用版 |
| HarmonyOS (Android) | ${APP_NAME}_HarmonyOS_Android_v${VERSION}.apk | HarmonyOS兼容版 |
| HarmonyOS | ${APP_NAME}_HarmonyOS_v${VERSION}.hap | HarmonyOS原生版 |

## ✨ 新增功能

- 深度适配小米HyperOS系统
- 完美适配华为HarmonyOS系统
- 优化Android原生体验
- 支持深色/浅色主题切换
- 新增考试中心模块
- 学习统计数据展示

## 🎨 平台适配

**HyperOS:**
- 深色主题设计
- 紫色主色调 (#6366f1)
- MiSans字体
- 流畅动画效果

**HarmonyOS:**
- 跟随系统主题
- 蓝色主色调 (#007dff)
- HarmonyOS Sans SC字体
- 鸿蒙特性支持

**Android:**
- 浅色主题设计
- 紫色主色调 (#6200ee)
- Roboto字体
- 原生优化

## 🛡️ 安全更新

- 加密存储用户数据
- HTTPS通信加密
- Token安全管理

## 📅 发布日期

$(date +%Y-%m-%d)

---

**MTSCOS AI Project** - 智能教育系统
EOF
    
    echo "[文档] 发布说明生成完成!"
}

function package_all() {
    echo ""
    echo "开始打包所有平台..."
    
    # 清理旧包
    rm -rf ${PACKAGE_DIR}/*
    
    # 打包APK
    package_apk
    
    # 打包HarmonyOS
    package_harmonyos
    
    # 生成校验文件
    create_checksum
    
    # 生成发布说明
    create_release_note
    
    echo ""
    echo "=========================================="
    echo "  打包完成!"
    echo "=========================================="
    echo "输出目录: ${PACKAGE_DIR}/"
    ls -la ${PACKAGE_DIR}/
}

function show_help() {
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -a, --apk        仅打包APK"
    echo "  -hm, --harmonyos 仅打包HarmonyOS"
    echo "  -all, --all      打包所有版本"
    echo "  -h, --help       显示此帮助信息"
    echo ""
}

case "$1" in
    -a|--apk)
        package_apk
        ;;
    -hm|--harmonyos)
        package_harmonyos
        ;;
    -all|--all)
        package_all
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