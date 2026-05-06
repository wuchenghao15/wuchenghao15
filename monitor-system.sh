#!/bin/bash

# 系统状态监控脚本
# 用于监控系统的运行状态，及时发现问题

# 配置参数
LOG_FILE="${HOME}/MTSCOS_Backup/system_monitor_log.txt"
ALERT_FILE="${HOME}/MTSCOS_Backup/system_alert.txt"

# 创建日志目录
mkdir -p "${HOME}/MTSCOS_Backup"

# 记录开始时间
echo "[$(date)] 系统状态监控开始..." >> "${LOG_FILE}"

# 检查服务器状态
echo "[$(date)] 检查服务器状态..." >> "${LOG_FILE}"
SERVER_STATUS="离线"
if pgrep -f "python3 -m http.server 8888" > /dev/null; then
    SERVER_STATUS="在线"
    echo "[$(date)] 服务器状态: 在线" >> "${LOG_FILE}"
else
    echo "[$(date)] 服务器状态: 离线" >> "${LOG_FILE}"
    echo "[$(date)] 警告: 服务器未运行!" >> "${ALERT_FILE}"
fi

# 检查前端文件
echo "[$(date)] 检查前端文件..." >> "${LOG_FILE}"
if [ -d "frontend" ]; then
    FRONTEND_FILES=$(find "frontend" -type f | wc -l)
    echo "[$(date)] 前端文件数量: ${FRONTEND_FILES}" >> "${LOG_FILE}"
else
    echo "[$(date)] 错误: 前端目录不存在!" >> "${LOG_FILE}"
    echo "[$(date)] 严重警告: 前端目录不存在!" >> "${ALERT_FILE}"
fi

# 检查数据文件
echo "[$(date)] 检查数据文件..." >> "${LOG_FILE}"
if [ -d "data" ]; then
    DATA_FILES=$(find "data" -type f | wc -l)
    echo "[$(date)] 数据文件数量: ${DATA_FILES}" >> "${LOG_FILE}"
else
    echo "[$(date)] 警告: 数据目录不存在!" >> "${LOG_FILE}"
    echo "[$(date)] 警告: 数据目录不存在!" >> "${ALERT_FILE}"
fi

# 检查配置文件
echo "[$(date)] 检查配置文件..." >> "${LOG_FILE}"
CONFIG_FILES=".env .env.example docker-compose.yml VERSION"
for config_file in ${CONFIG_FILES}; do
    if [ -f "${config_file}" ]; then
        echo "[$(date)] 配置文件 ${config_file}: 存在" >> "${LOG_FILE}"
    else
        echo "[$(date)] 警告: 配置文件 ${config_file} 不存在!" >> "${LOG_FILE}"
        echo "[$(date)] 警告: 配置文件 ${config_file} 不存在!" >> "${ALERT_FILE}"
    fi
done

# 检查备份状态
echo "[$(date)] 检查备份状态..." >> "${LOG_FILE}"
BACKUP_DIR="${HOME}/MTSCOS_Backup"
if [ -d "${BACKUP_DIR}" ]; then
    BACKUP_COUNT=$(ls -la "${BACKUP_DIR}/mtscos_backup_"* | wc -l)
    echo "[$(date)] 备份数量: ${BACKUP_COUNT}" >> "${LOG_FILE}"
    
    if [ ${BACKUP_COUNT} -eq 0 ]; then
        echo "[$(date)] 警告: 没有备份文件!" >> "${LOG_FILE}"
        echo "[$(date)] 警告: 没有备份文件!" >> "${ALERT_FILE}"
    else
        # 检查最近备份的时间
        LATEST_BACKUP=$(ls -la "${BACKUP_DIR}/mtscos_backup_"* | sort -r | head -n 1 | awk '{print $9}')
        BACKUP_TIME=$(stat -f "%Sm" "${LATEST_BACKUP}")
        echo "[$(date)] 最近备份: $(basename ${LATEST_BACKUP})" >> "${LOG_FILE}"
        echo "[$(date)] 备份时间: ${BACKUP_TIME}" >> "${LOG_FILE}"
    fi
else
    echo "[$(date)] 错误: 备份目录不存在!" >> "${LOG_FILE}"
    echo "[$(date)] 严重警告: 备份目录不存在!" >> "${ALERT_FILE}"
fi

# 检查磁盘空间
echo "[$(date)] 检查磁盘空间..." >> "${LOG_FILE}"
DISK_USAGE=$(df -h . | tail -n 1 | awk '{print $5}' | sed 's/%//')
echo "[$(date)] 磁盘使用率: ${DISK_USAGE}%" >> "${LOG_FILE}"

if [ ${DISK_USAGE} -gt 90 ]; then
    echo "[$(date)] 警告: 磁盘空间不足!" >> "${LOG_FILE}"
    echo "[$(date)] 警告: 磁盘空间不足 (${DISK_USAGE}%)!" >> "${ALERT_FILE}"
fi

# 生成系统状态报告
cat > "${HOME}/MTSCOS_Backup/system_status_report.txt" << EOF
MTSCOS 系统状态报告
生成时间: $(date)

服务器状态: ${SERVER_STATUS}
前端文件数量: ${FRONTEND_FILES:-0}
数据文件数量: ${DATA_FILES:-0}
备份数量: ${BACKUP_COUNT:-0}
磁盘使用率: ${DISK_USAGE}%

详细日志请查看: ${LOG_FILE}
警告信息请查看: ${ALERT_FILE}
EOF

# 记录完成时间
echo "[$(date)] 系统状态监控完成" >> "${LOG_FILE}"
echo "----------------------------------------" >> "${LOG_FILE}"

echo "系统状态监控已完成!"
echo "状态报告: ${HOME}/MTSCOS_Backup/system_status_report.txt"
echo "详细日志: ${LOG_FILE}"
echo "警告信息: ${ALERT_FILE}"