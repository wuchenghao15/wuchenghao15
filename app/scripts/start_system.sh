
#!/bin/bash

# 系统启动脚本

# 日志目录
LOG_DIR="logs"
mkdir -p $LOG_DIR

# 启动时间
START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$START_TIME] 开始启动系统..." >> $LOG_DIR/startup.log

# 检查Python环境
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查Python环境..." >> $LOG_DIR/startup.log
if command -v python3 &> /dev/null; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] Python 3 已安装" >> $LOG_DIR/startup.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 错误: Python 3 未安装" >> $LOG_DIR/startup.log
    exit 1
fi

# 检查依赖
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查依赖..." >> $LOG_DIR/startup.log
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt >> $LOG_DIR/startup.log 2>&1
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 依赖安装完成" >> $LOG_DIR/startup.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 警告: requirements.txt 未找到" >> $LOG_DIR/startup.log
fi

# 启动Flask应用
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 启动Flask应用..." >> $LOG_DIR/startup.log
cd flask-app
python3 -m flask run --host=0.0.0.0 --port=5000 >> $LOG_DIR/startup.log 2>&1

# 结束时间
END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$END_TIME] 系统启动完成" >> $LOG_DIR/startup.log
            