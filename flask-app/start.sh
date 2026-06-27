#!/bin/bash
# MTSCOS AI 系统启动脚本

cd "$(dirname "$0")"

PYTHON_PATH="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"

echo "启动MTSCOS AI系统..."
$PYTHON_PATH app.py

# 如果上面的路径不存在，尝试python3
if [ $? -ne 0 ]; then
    echo "尝试使用python3启动..."
    python3 app.py
fi