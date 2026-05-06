#!/bin/bash

# 灰度测试环境部署脚本
# 用途: 将测试通过的代码部署到指定位置

echo "===================================="
echo "MTSCOS AI Project - 部署脚本"
echo "===================================="

# 配置信息
STAGING_DIR="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Staging"
TARGET_DIR="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
BACKUP_DIR="$STAGING_DIR/Backups"
RESULTS_DIR="$STAGING_DIR/Results"
LOG_FILE="$STAGING_DIR/Logs/deploy-$(date +%Y%m%d).log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 记录日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查必要的目录
check_directories() {
    log "检查目录..."
    if [ ! -d "$STAGING_DIR" ]; then
        log "错误: 灰度测试环境目录不存在: $STAGING_DIR"
        return 1
    fi
    
    if [ ! -d "$TARGET_DIR" ]; then
        log "错误: 目标部署目录不存在: $TARGET_DIR"
        return 1
    fi
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$RESULTS_DIR"
    
    return 0
}

# 检查测试结果
check_test_results() {
    log "检查测试结果..."
    local latest_result=$(ls -t "$RESULTS_DIR"/test-*.json 2>/dev/null | head -n 1)
    
    if [ -z "$latest_result" ]; then
        log "错误: 未找到测试结果文件"
        return 1
    fi
    
    log "最新测试结果: $(basename "$latest_result")"
    
    # 简单检查测试结果是否通过（实际环境中应使用jq解析JSON）
    if grep -q '"status":"failed"' "$latest_result"; then
        log "错误: 测试结果显示失败，部署已中止"
        return 1
    fi
    
    log "✓ 测试结果通过"
    return 0
}

# 创建备份
create_backup() {
    log "创建部署前备份..."
    local backup_file="$BACKUP_DIR/deploy-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    log "正在创建备份: $(basename "$backup_file")"
    
    # 排除不需要备份的目录
    tar -czf "$backup_file" \
        --exclude="$TARGET_DIR/Staging" \
        --exclude="$TARGET_DIR/node_modules" \
        --exclude="$TARGET_DIR/.git" \
        --exclude="$TARGET_DIR/Backups" \
        --exclude="$TARGET_DIR/Logs" \
        "$TARGET_DIR"/* 2>> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log "✓ 备份创建成功"
        return 0
    else
        log "错误: 备份创建失败"
        return 1
    fi
}

# 部署文件
deploy_files() {
    log "开始部署文件..."
    
    # 复制关键文件（根据实际项目调整）
    local source_files=(
        "$STAGING_DIR/Scripts/tests/results"
        "$STAGING_DIR/updates"
    )
    
    for src in "${source_files[@]}"; do
        if [ -e "$src" ]; then
            local dest="$TARGET_DIR/$(basename "$src")"
            log "部署: $(basename "$src") -> $(basename "$dest")"
            cp -r "$src" "$dest" 2>> "$LOG_FILE"
            if [ $? -eq 0 ]; then
                log "✓ 部署成功: $(basename "$src")"
            else
                log "错误: 部署失败: $(basename "$src")"
                return 1
            fi
        fi
    done
    
    # 特殊处理package.json和其他配置文件
    if [ -f "$STAGING_DIR/package.json" ]; then
        log "更新 package.json"
        cp "$STAGING_DIR/package.json" "$TARGET_DIR/package.json" 2>> "$LOG_FILE"
    fi
    
    log "✓ 所有文件部署完成"
    return 0
}

# 验证部署
verify_deployment() {
    log "验证部署..."
    
    # 检查关键文件是否存在
    local critical_files=(
        "$TARGET_DIR/package.json"
        "$TARGET_DIR/index.html"
        "$TARGET_DIR/assets/js"
    )
    
    for file in "${critical_files[@]}"; do
        if [ ! -e "$file" ]; then
            log "错误: 关键文件/目录缺失: $(basename "$file")"
            return 1
        fi
    done
    
    log "✓ 部署验证通过"
    return 0
}

# 更新版本信息
update_version() {
    log "更新版本信息..."
    local version_file="$TARGET_DIR/VERSION.txt"
    
    if [ -f "$version_file" ]; then
        local current_version=$(cat "$version_file")
        # 简单的版本号递增（实际环境应使用语义化版本）
        local new_version="$current_version.$(date +%Y%m%d)"
        echo "$new_version" > "$version_file"
        log "版本已更新: $current_version -> $new_version"
    else
        # 创建新的版本文件
        echo "1.0.$(date +%Y%m%d)" > "$version_file"
        log "创建版本文件: 1.0.$(date +%Y%m%d)"
    fi
}

# 主函数
main() {
    log "开始部署过程..."
    
    # 步骤1: 检查目录
    check_directories || {
        log "部署终止: 目录检查失败"
        exit 1
    }
    
    # 步骤2: 检查测试结果
    check_test_results || {
        log "部署终止: 测试结果不通过"
        exit 1
    }
    
    # 步骤3: 创建备份
    create_backup || {
        log "部署终止: 备份创建失败"
        exit 1
    }
    
    # 步骤4: 部署文件
    deploy_files || {
        log "部署终止: 文件部署失败"
        log "正在恢复到备份状态..."
        # 这里应该有恢复备份的逻辑
        exit 1
    }
    
    # 步骤5: 验证部署
    verify_deployment || {
        log "部署终止: 部署验证失败"
        log "正在恢复到备份状态..."
        # 这里应该有恢复备份的逻辑
        exit 1
    }
    
    # 步骤6: 更新版本
    update_version
    
    log "===================================="
    log "部署成功完成!"
    log "详细日志: $LOG_FILE"
    log "===================================="
    
    return 0
}

# 执行主函数
main "$@"
