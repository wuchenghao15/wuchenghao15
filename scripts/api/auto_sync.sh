#!/bin/bash

# MTSCOS 自动同步主脚本
# 协调所有自动任务：Git同步、备份、恢复点、沙盒、影子节点、回滚记录

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
CONFIG_FILE="$PROJECT_DIR/sync_config.json"
LOG_DIR="${HOME}/MTSCOS_Sync_Logs"
LOG_FILE="${LOG_DIR}/auto_sync_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" | tee -a "$LOG_FILE"
}

ensure_python() {
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        PYTHON_CMD="python"
    else
        error "Python 未安装"
        exit 1
    fi
}

ensure_python

log "========== MTSCOS 自动同步系统启动 =========="

# 1. 创建同步前回滚点
log "步骤1: 创建同步前回滚点"
if "$PYTHON_CMD" "$PROJECT_DIR/rollback_manager.py" --create 2>&1 | grep -q "成功"; then
    success "回滚点创建成功"
else
    error "回滚点创建失败"
fi

# 2. Git/GitHub自动同步
log "步骤2: Git/GitHub自动同步"
if "$PYTHON_CMD" "$PROJECT_DIR/git_sync.py" --sync 2>&1 | grep -q "成功"; then
    success "Git同步成功"
else
    error "Git同步失败"
fi

# 3. 自动备份
log "步骤3: 自动备份"
if "$PYTHON_CMD" "$PROJECT_DIR/backup_manager.py" --backup 2>&1 | grep -q "成功"; then
    success "备份成功"
else
    error "备份失败"
fi

# 4. 创建备份后回滚点
log "步骤4: 创建备份后回滚点"
if "$PYTHON_CMD" "$PROJECT_DIR/rollback_manager.py" --create 2>&1 | grep -q "成功"; then
    success "备份后回滚点创建成功"
else
    error "备份后回滚点创建失败"
fi

# 5. 创建恢复镜像
log "步骤5: 创建恢复镜像"
if "$PYTHON_CMD" "$PROJECT_DIR/backup_manager.py" --image 2>&1 | grep -q "成功"; then
    success "恢复镜像创建成功"
else
    error "恢复镜像创建失败"
fi

# 6. 影子节点同步（如果启用）
log "步骤6: 影子节点同步"
if "$PYTHON_CMD" "$PROJECT_DIR/shadow_node.py" --sync 2>&1 | grep -q "成功"; then
    success "影子节点同步成功"
else
    error "影子节点同步失败或未启用"
fi

# 7. 沙盒清理（如果启用）
log "步骤7: 沙盒清理"
if "$PYTHON_CMD" "$PROJECT_DIR/sandbox_manager.py" --cleanup 2>&1 | grep -q "成功"; then
    success "沙盒清理成功"
else
    error "沙盒清理失败或未启用"
fi

log "========== MTSCOS 自动同步系统完成 =========="

exit 0