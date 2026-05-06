
#!/bin/bash

# 系统初始化检查脚本

# 日志目录
LOG_DIR="logs"
mkdir -p $LOG_DIR

# 检查时间
CHECK_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$CHECK_TIME] 开始系统初始化检查..." >> $LOG_DIR/init_check.log

# 检查目录结构
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查目录结构..." >> $LOG_DIR/init_check.log
required_dirs=("app" "app/ai" "app/models" "app/utils" "app/templates" "app/static" "logs" "data")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] 目录 $dir 存在" >> $LOG_DIR/init_check.log
    else
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] 警告: 目录 $dir 不存在，正在创建..." >> $LOG_DIR/init_check.log
        mkdir -p $dir
    fi
done

# 检查数据库文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查数据库文件..." >> $LOG_DIR/init_check.log
if [ -f "app/data/mtscos_ai_project.db" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 数据库文件存在" >> $LOG_DIR/init_check.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 警告: 数据库文件不存在" >> $LOG_DIR/init_check.log
fi

# 检查配置文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查配置文件..." >> $LOG_DIR/init_check.log
if [ -f "app/config.py" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 配置文件存在" >> $LOG_DIR/init_check.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 警告: 配置文件不存在" >> $LOG_DIR/init_check.log
fi

# 检查完成
END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$END_TIME] 系统初始化检查完成" >> $LOG_DIR/init_check.log
            