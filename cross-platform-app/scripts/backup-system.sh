#!/bin/bash

# MTSCOS 系统完整备份脚本
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="MTSCOS"
VERSION="2.0"
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${PROJECT_NAME}_v${VERSION}_${TIMESTAMP}.tar.gz"
BACKUP_FILE_ZIP="${PROJECT_NAME}_v${VERSION}_${TIMESTAMP}.zip"

print_title() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}  MTSCOS 系统完整备份 v${VERSION}${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo ""
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

# 主函数
main() {
    print_title
    
    # 检查是否在正确目录
    if [ ! -f "package.json" ]; then
        print_error "package.json文件不存在"
        print_error "请确保在项目根目录运行此脚本"
        exit 1
    fi
    
    # 创建备份目录
    echo -e "${YELLOW}[1/6]${NC} 创建备份目录..."
    mkdir -p "$BACKUP_DIR"
    print_success "备份目录: $BACKUP_DIR"
    
    # 列出要备份的文件和目录
    echo -e "\n${YELLOW}[2/6]${NC} 准备备份文件列表..."
    
    BACKUP_CONTENTS="
src/
scripts/
android/
harmonyos/
package.json
package-lock.json
.env
README.md
SYSTEM_SUMMARY.md
"
    
    echo "备份内容:"
    echo "$BACKUP_CONTENTS"
    print_success "已准备备份内容列表"
    
    # 创建tar.gz备份
    echo -e "\n${YELLOW}[3/6]${NC} 创建压缩备份..."
    tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
        src/ \
        scripts/ \
        android/ \
        harmonyos/ \
        package.json \
        package-lock.json \
        .env \
        README.md \
        SYSTEM_SUMMARY.md 2>/dev/null
    
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        FILE_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
        print_success "已创建备份: $BACKUP_FILE ($FILE_SIZE)"
    else
        print_error "备份创建失败"
        exit 1
    fi
    
    # 创建zip备份（兼容Windows）
    echo -e "\n${YELLOW}[4/6]${NC} 创建ZIP备份（兼容Windows）..."
    zip -r "$BACKUP_DIR/$BACKUP_FILE_ZIP" \
        src/ \
        scripts/ \
        android/ \
        harmonyos/ \
        package.json \
        package-lock.json \
        .env \
        README.md \
        SYSTEM_SUMMARY.md 2>/dev/null
    
    if [ -f "$BACKUP_DIR/$BACKUP_FILE_ZIP" ]; then
        FILE_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE_ZIP" | cut -f1)
        print_success "已创建ZIP备份: $BACKUP_FILE_ZIP ($FILE_SIZE)"
    else
        print_warning "ZIP备份创建失败（可能需要安装zip工具）"
    fi
    
    # 验证备份完整性
    echo -e "\n${YELLOW}[5/6]${NC} 验证备份完整性..."
    TAR_CONTENTS=$(tar -tzf "$BACKUP_DIR/$BACKUP_FILE" | head -5 | wc -l)
    if [ "$TAR_CONTENTS" -gt 0 ]; then
        print_success "备份验证通过"
    else
        print_error "备份验证失败"
        exit 1
    fi
    
    # 显示备份信息
    echo -e "\n${YELLOW}[6/6]${NC} 备份完成..."
    echo ""
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}  备份完成！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    
    echo -e "${BLUE}备份信息：${NC}"
    echo "  项目名称: $PROJECT_NAME"
    echo "  版本: v${VERSION}"
    echo "  备份时间: $(date "+%Y年%m月%d日 %H:%M:%S")"
    echo ""
    
    echo -e "${BLUE}备份文件：${NC}"
    echo "  📦 TAR格式: $BACKUP_DIR/$BACKUP_FILE"
    if [ -f "$BACKUP_DIR/$BACKUP_FILE_ZIP" ]; then
        echo "  📦 ZIP格式: $BACKUP_DIR/$BACKUP_FILE_ZIP"
    fi
    echo ""
    
    echo -e "${BLUE}备份内容：${NC}"
    echo "  • src/          - 源代码目录"
    echo "  • scripts/      - 脚本工具目录"
    echo "  • android/      - Android项目"
    echo "  • harmonyos/    - HarmonyOS项目"
    echo "  • package.json  - 依赖配置"
    echo "  • .env          - 环境配置"
    echo "  • README.md     - 项目说明"
    echo ""
    
    echo -e "${YELLOW}提示：${NC}"
    echo "  - 备份文件位于: $(pwd)/$BACKUP_DIR/"
    echo "  - 建议将备份文件复制到安全位置"
    echo "  - 定期备份以防止数据丢失"
    echo ""
    
    # 列出最近的备份
    echo -e "${BLUE}最近备份：${NC}"
    ls -la "$BACKUP_DIR/" | head -10
}

# 执行主函数
main "$@"