#!/bin/bash

# 设置环境变量
DB_HOST=${DB_HOST:-db-primary}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-mtscos_db}
DB_USER=${DB_USER:-mtscos_user}
DB_PASSWORD=${DB_PASSWORD:-SecurePassword123!}
BACKUP_DIR=${BACKUP_DIR:-/backups}

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

# 设置备份文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql.gz"

# 执行备份
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F c -b -v | gzip > "$BACKUP_FILE"

# 检查备份是否成功
if [ $? -eq 0 ]; then
    echo "$(date +"%Y-%m-%d %H:%M:%S") - 备份成功: $BACKUP_FILE"
    
    # 记录备份日志到数据库
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    INSERT INTO backup_logs (backup_type, backup_path, backup_size, status, error_message) 
    VALUES ('full', '$BACKUP_FILE', $(ls -l "$BACKUP_FILE" | awk '{print $5}'), 'success', NULL)
    "
    
    # 复制备份到备用数据库
    PGPASSWORD="$DB_PASSWORD" pg_restore -h "db-secondary" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v "$BACKUP_FILE"
    
    # 清理7天前的备份文件
    find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -type f -mtime +7 -delete
    
else
    echo "$(date +"%Y-%m-%d %H:%M:%S") - 备份失败"
    
    # 记录备份失败日志到数据库
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    INSERT INTO backup_logs (backup_type, backup_path, backup_size, status, error_message) 
    VALUES ('full', '$BACKUP_FILE', NULL, 'failed', '备份命令执行失败')
    "
    
    exit 1
fi
