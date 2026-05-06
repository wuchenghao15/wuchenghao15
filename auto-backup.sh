#!/bin/bash

# 自动备份机制
# 用于定期自动备份系统，确保系统数据的安全性

# 配置参数
BACKUP_DIR="${HOME}/MTSCOS_Backup"
LOG_FILE="${BACKUP_DIR}/auto_backup_log.txt"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 记录开始时间
echo "[$(date)] 自动备份开始..." >> "${LOG_FILE}"

# 检查备份脚本是否存在
if [ ! -f "backup-system.sh" ]; then
    echo "错误: 备份脚本不存在!"
    echo "请先创建 backup-system.sh 脚本"
    echo "[$(date)] 备份脚本不存在，自动备份失败" >> "${LOG_FILE}"
    exit 1
fi

# 运行备份脚本
echo "[$(date)] 执行备份脚本..." >> "${LOG_FILE}"
chmod +x "backup-system.sh"
./backup-system.sh >> "${LOG_FILE}" 2>&1

# 检查备份结果
if [ $? -eq 0 ]; then
    echo "[$(date)] 自动备份成功完成" >> "${LOG_FILE}"
else
    echo "[$(date)] 自动备份失败" >> "${LOG_FILE}"
fi

# 清理旧备份（保留最近7个备份）
echo "[$(date)] 清理旧备份..." >> "${LOG_FILE}"
BACKUP_COUNT=$(ls -la "${BACKUP_DIR}/mtscos_backup_"* | wc -l)
MAX_BACKUPS=7

if [ ${BACKUP_COUNT} -gt ${MAX_BACKUPS} ]; then
    # 按时间排序，删除最旧的备份
    OLD_BACKUPS=$(ls -la "${BACKUP_DIR}/mtscos_backup_"* | sort | head -n $((BACKUP_COUNT - MAX_BACKUPS)) | awk '{print $9}')
    
    for backup in ${OLD_BACKUPS}; do
        if [ -d "${backup}" ]; then
            rm -rf "${backup}"
            echo "[$(date)] 删除旧备份: $(basename ${backup})" >> "${LOG_FILE}"
        fi
    done
    
    echo "[$(date)] 旧备份清理完成" >> "${LOG_FILE}"
else
    echo "[$(date)] 备份数量未超过限制，跳过清理" >> "${LOG_FILE}"
fi

# 记录完成时间
echo "[$(date)] 自动备份过程完成" >> "${LOG_FILE}"
echo "----------------------------------------" >> "${LOG_FILE}"

echo "自动备份已完成!"
echo "详细日志: ${LOG_FILE}"