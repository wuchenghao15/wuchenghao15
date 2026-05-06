# HTTP服务器状态检查和修复函数
check_and_fix_http_server() {
    local http_status="not_running"
    local http_port=""
    local http_pid=""
    
    # 记录日志
    echo "[$(date)] 开始HTTP服务器状态检查" >> "$LOG_DIR/http_monitor.log"
    
    # 检查HTTP服务器进程
    if pgrep -f "python3 -m http.server" > /dev/null; then
        http_status="running"
        http_pid=$(pgrep -f "python3 -m http.server")
        http_port=$(lsof -i | grep -i "python" | grep -i "http" | grep LISTEN | awk '{print $9}' | sed 's/.*://')
        
        # 写入状态文件
        echo "RUNNING" > "$MONITOR_DIR/http_status.txt"
        echo "PID=$http_pid" >> "$MONITOR_DIR/http_status.txt"
        echo "PORT=$http_port" >> "$MONITOR_DIR/http_status.txt"
        echo "TIMESTAMP=$(date)" >> "$MONITOR_DIR/http_status.txt"
        
        # 检查服务器响应
        if command -v curl > /dev/null; then
            local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$http_port/ 2>/dev/null)
            echo "RESPONSE_CODE=$response" >> "$MONITOR_DIR/http_status.txt"
        fi
        
        echo "[$(date)] HTTP服务器运行正常，PID: $http_pid, 端口: $http_port" >> "$LOG_DIR/http_monitor.log"
        return 0
    else
        # 服务器未运行，尝试修复
        echo "[$(date)] HTTP服务器未运行，尝试自动修复" >> "$LOG_DIR/http_monitor.log"
        
        # 写入状态文件
        echo "STOPPED" > "$MONITOR_DIR/http_status.txt"
        echo "TIMESTAMP=$(date)" >> "$MONITOR_DIR/http_status.txt"
        
        # 清理旧PID文件
        if [ -f "$LOG_DIR/http_server.pid" ]; then
            rm -f "$LOG_DIR/http_server.pid"
        fi
        
        # 使用统一的启动函数启动HTTP服务器
        if [ -f "$SCRIPTS_DIR/http_server.sh" ]; then
            start_http_server
            
            # 验证启动是否成功
            local new_pid=$(pgrep -f "python3 -m http.server")
            if [ ! -z "$new_pid" ]; then
                local new_port=$(lsof -i | grep -i "python" | grep -i "http" | grep LISTEN | awk '{print $9}' | sed 's/.*://')
                echo "[$(date)] HTTP服务器修复成功，PID: $new_pid, 端口: $new_port" >> "$LOG_DIR/http_monitor.log"
                return 0
            else
                echo "[$(date)] HTTP服务器修复失败" >> "$LOG_DIR/http_monitor.log"
                return 1
            fi
        else
            echo "[$(date)] HTTP服务器脚本不存在" >> "$LOG_DIR/http_monitor.log"
            return 1
        fi
    fi
}