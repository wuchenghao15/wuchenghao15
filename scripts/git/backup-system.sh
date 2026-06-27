#!/bin/bash

# 系统备份脚本
# 用于创建完整的系统备份，包括所有重要文件和数据

# 配置参数
BACKUP_DIR="${HOME}/MTSCOS_Backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="mtscos_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
LOG_FILE="${BACKUP_DIR}/backup_log.txt"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 记录开始时间
echo "[$(date)] 开始系统备份..." >> "${LOG_FILE}"
echo "备份目标: ${BACKUP_PATH}" >> "${LOG_FILE}"

# 创建备份目录结构
mkdir -p "${BACKUP_PATH}/frontend"
mkdir -p "${BACKUP_PATH}/data"
mkdir -p "${BACKUP_PATH}/docs"
mkdir -p "${BACKUP_PATH}/config"

# 备份前端文件
echo "[$(date)] 备份前端文件..." >> "${LOG_FILE}"
if [ -d "frontend" ]; then
    cp -r "frontend" "${BACKUP_PATH}/"
    echo "[$(date)] 前端文件备份完成" >> "${LOG_FILE}"  
else
    echo "[$(date)] 前端目录不存在，跳过" >> "${LOG_FILE}"
fi

# 备份数据文件
echo "[$(date)] 备份数据文件..." >> "${LOG_FILE}"
if [ -d "data" ]; then
    cp -r "data" "${BACKUP_PATH}/"
    echo "[$(date)] 数据文件备份完成" >> "${LOG_FILE}"
else
    echo "[$(date)] 数据目录不存在，跳过" >> "${LOG_FILE}"
fi

# 备份配置文件
echo "[$(date)] 备份配置文件..." >> "${LOG_FILE}"
for config_file in ".env" ".env.example" "docker-compose.yml" "VERSION"; do
    if [ -f "${config_file}" ]; then
        cp "${config_file}" "${BACKUP_PATH}/config/"
        echo "[$(date)] 备份 ${config_file}" >> "${LOG_FILE}"
    fi
done

# 备份脚本文件
echo "[$(date)] 备份脚本文件..." >> "${LOG_FILE}"
for script_file in "start_server.sh" "backup-script.sh" "deploy.sh"; do
    if [ -f "${script_file}" ]; then
        cp "${script_file}" "${BACKUP_PATH}/config/"
        echo "[$(date)] 备份 ${script_file}" >> "${LOG_FILE}"
    fi
done

# 备份文档
echo "[$(date)] 备份文档..." >> "${LOG_FILE}"
if [ -d "docs" ]; then
    cp -r "docs" "${BACKUP_PATH}/"
    echo "[$(date)] 文档备份完成" >> "${LOG_FILE}"
else
    echo "[$(date)] 文档目录不存在，跳过" >> "${LOG_FILE}"
fi

# 创建备份摘要
cat > "${BACKUP_PATH}/backup_summary.txt" << EOF
MTSCOS 系统备份摘要
备份时间: $(date)
备份路径: ${BACKUP_PATH}

备份内容:
- 前端文件
- 数据文件
- 配置文件
- 脚本文件
- 文档

EOF

# 计算备份大小
BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)
echo "[$(date)] 备份大小: ${BACKUP_SIZE}" >> "${LOG_FILE}"

# 记录完成时间
echo "[$(date)] 系统备份完成!" >> "${LOG_FILE}"
echo "[$(date)] 备份文件保存在: ${BACKUP_PATH}" >> "${LOG_FILE}"
echo "----------------------------------------" >> "${LOG_FILE}"

echo "系统备份已完成!"
echo "备份文件: ${BACKUP_PATH}"
echo "备份大小: ${BACKUP_SIZE}"
echo "详细日志: ${LOG_FILE}"