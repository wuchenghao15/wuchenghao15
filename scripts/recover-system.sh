#!/bin/bash

# 系统恢复脚本
# 用于从备份中恢复系统，确保系统崩溃时能够彻底恢复

# 配置参数
BACKUP_DIR="${HOME}/MTSCOS_Backup"
LOG_FILE="${BACKUP_DIR}/recovery_log.txt"

# 检查备份目录
if [ ! -d "${BACKUP_DIR}" ]; then
    echo "错误: 备份目录不存在!"
    echo "请先运行 backup-system.sh 创建备份"
    exit 1
fi

# 显示可用备份
echo "可用的系统备份:"
echo "----------------------------------------"
ls -la "${BACKUP_DIR}/" | grep "mtscos_backup_"
echo "----------------------------------------"

# 让用户选择备份
read -p "请输入要恢复的备份名称: " BACKUP_NAME
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# 检查备份是否存在
if [ ! -d "${BACKUP_PATH}" ]; then
    echo "错误: 选择的备份不存在!"
    exit 1
fi

# 记录开始时间
echo "[$(date)] 开始系统恢复..." >> "${LOG_FILE}"
echo "恢复备份: ${BACKUP_PATH}" >> "${LOG_FILE}"

# 停止服务器（如果正在运行）
echo "[$(date)] 停止服务器..." >> "${LOG_FILE}"
if pgrep -f "python3 -m http.server 8888" > /dev/null; then
    pkill -f "python3 -m http.server 8888"
    echo "[$(date)] 服务器已停止" >> "${LOG_FILE}"
else
    echo "[$(date)] 服务器未运行，跳过停止步骤" >> "${LOG_FILE}"
fi

# 备份当前系统（以防万一）
CURRENT_BACKUP="${BACKUP_DIR}/current_system_$(date +"%Y%m%d_%H%M%S")"
echo "[$(date)] 创建当前系统的临时备份..." >> "${LOG_FILE}"
mkdir -p "${CURRENT_BACKUP}"

if [ -d "frontend" ]; then
    cp -r "frontend" "${CURRENT_BACKUP}/"
fi

if [ -d "data" ]; then
    cp -r "data" "${CURRENT_BACKUP}/"
fi

for config_file in ".env" ".env.example" "docker-compose.yml" "VERSION"; do
    if [ -f "${config_file}" ]; then
        cp "${config_file}" "${CURRENT_BACKUP}/"
    fi
done

echo "[$(date)] 当前系统备份完成: ${CURRENT_BACKUP}" >> "${LOG_FILE}"

# 恢复前端文件
echo "[$(date)] 恢复前端文件..." >> "${LOG_FILE}"
if [ -d "${BACKUP_PATH}/frontend" ]; then
    rm -rf "frontend" 2>/dev/null
    cp -r "${BACKUP_PATH}/frontend" "./"
    echo "[$(date)] 前端文件恢复完成" >> "${LOG_FILE}"
else
    echo "[$(date)] 备份中没有前端文件，跳过" >> "${LOG_FILE}"
fi

# 恢复数据文件
echo "[$(date)] 恢复数据文件..." >> "${LOG_FILE}"
if [ -d "${BACKUP_PATH}/data" ]; then
    rm -rf "data" 2>/dev/null
    cp -r "${BACKUP_PATH}/data" "./"
    echo "[$(date)] 数据文件恢复完成" >> "${LOG_FILE}"
else
    echo "[$(date)] 备份中没有数据文件，跳过" >> "${LOG_FILE}"
fi

# 恢复配置文件
echo "[$(date)] 恢复配置文件..." >> "${LOG_FILE}"
if [ -d "${BACKUP_PATH}/config" ]; then
    for config_file in "${BACKUP_PATH}/config"/*; do
        if [ -f "${config_file}" ]; then
            filename=$(basename "${config_file}")
            cp "${config_file}" "./"
            echo "[$(date)] 恢复 ${filename}" >> "${LOG_FILE}"
        fi
    done
    echo "[$(date)] 配置文件恢复完成" >> "${LOG_FILE}"
else
    echo "[$(date)] 备份中没有配置文件，跳过" >> "${LOG_FILE}"
fi

# 恢复文档
echo "[$(date)] 恢复文档..." >> "${LOG_FILE}"
if [ -d "${BACKUP_PATH}/docs" ]; then
    rm -rf "docs" 2>/dev/null
    cp -r "${BACKUP_PATH}/docs" "./"
    echo "[$(date)] 文档恢复完成" >> "${LOG_FILE}"
else
    echo "[$(date)] 备份中没有文档，跳过" >> "${LOG_FILE}"
fi

# 重启服务器
echo "[$(date)] 重启服务器..." >> "${LOG_FILE}"
if [ -f "start_server.sh" ]; then
    chmod +x "start_server.sh"
    ./start_server.sh &
    echo "[$(date)] 服务器已重启" >> "${LOG_FILE}"
else
    echo "[$(date)] 启动脚本不存在，手动启动服务器" >> "${LOG_FILE}"
    echo "请运行: python3 -m http.server 8888" >> "${LOG_FILE}"
fi

# 记录完成时间
echo "[$(date)] 系统恢复完成!" >> "${LOG_FILE}"
echo "[$(date)] 恢复备份: ${BACKUP_PATH}" >> "${LOG_FILE}"
echo "[$(date)] 当前系统备份: ${CURRENT_BACKUP}" >> "${LOG_FILE}"
echo "----------------------------------------" >> "${LOG_FILE}"

echo "系统恢复已完成!"
echo "恢复备份: ${BACKUP_PATH}"
echo "当前系统备份: ${CURRENT_BACKUP}"
echo "详细日志: ${LOG_FILE}"
echo ""
echo "服务器已重新启动，请访问 http://localhost:8888 检查系统状态"