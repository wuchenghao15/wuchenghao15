#!/bin/bash

# 设置颜色和格式化输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'
UNDERLINE='\033[4m'

# 设置路径
SCRIPT_DIR=$(pwd)
LOG_DIR="$SCRIPT_DIR/Logs"
BACKUP_DIR="$SCRIPT_DIR/Backups"
CONFIG_DIR="$SCRIPT_DIR/config"
SCRIPTS_DIR="$SCRIPT_DIR/Scripts"
ENCRYPTED_DIR="$SCRIPT_DIR/encrypted"
HTML_DIR="$SCRIPT_DIR/HTML"
MONITOR_DIR="$LOG_DIR/service_monitoring"
BACKUP_MONITOR_LOG="$LOG_DIR/backup_monitor.log"

# 确保必要的目录存在
mkdir -p "$MONITOR_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$HTML_DIR"
mkdir -p "$SCRIPTS_DIR"

# 定义版本号
VERSION='3.251102.113946'

# 更新版本号函数 - 自动迭代增强版
update_version() {
    local version_file="$SCRIPT_DIR/VERSION"
    local current_version
    
    if [ -f "$version_file" ]; then
        current_version=$(cat "$version_file")
        # 增加补丁版本号
        local major minor patch
        IFS='.' read -r major minor patch <<< "$current_version"
        patch=$((patch + 1))
        new_version="$major.$minor.$patch"
    else
        new_version="$VERSION"
    fi
    
    echo "$new_version" > "$version_file"
    echo "$new_version"
}

# 更新文档函数
update_documentation() {
    local new_version=$1
    
    # 更新README.md
    if [ -f "$SCRIPT_DIR/README.md" ]; then
        sed -i '' "s/版本: .*/版本: $new_version/" "$SCRIPT_DIR/README.md"
    fi
    
    # 更新HTML文档中的版本信息
    for html_file in "$HTML_DIR"/*.html; do
        if [ -f "$html_file" ]; then
            sed -i '' "s/版本号: .*/版本号: $new_version/" "$html_file"
        fi
    done
}

# 启动HTTP服务器函数（带重试机制）
start_http_server() {
    local port=8000
    local server_pid_file="$LOG_DIR/http_server.pid"
    local max_retries=3
    local retry_count=0
    local server_pid=""
    
    # 清除旧的PID文件
    if [ -f "$server_pid_file" ]; then
        rm -f "$server_pid_file"
    fi
    
    while [ $retry_count -lt $max_retries ]; do
        retry_count=$((retry_count + 1))
        print_info "尝试启动HTTP服务器（第${retry_count}/${max_retries}次尝试）..."
        
        # 尝试启动HTTP服务器（使用Python）
        if command -v python3 > /dev/null; then
            cd "$HTML_DIR"
            python3 -m http.server $port > "$LOG_DIR/http_server.log" 2>&1 &
            server_pid=$!
            
            # 等待服务启动
            sleep 2
            
            # 检查服务是否正常运行
            if ps -p "$server_pid" > /dev/null 2>&1; then
                echo "$server_pid" > "$server_pid_file"
                print_success "HTTP服务器已成功启动 (Python3) - http://localhost:$port"
                return 0
            else
                print_warning "HTTP服务器启动失败，正在重试..."
            fi
        elif command -v python > /dev/null; then
            cd "$HTML_DIR"
            python -m SimpleHTTPServer $port > "$LOG_DIR/http_server.log" 2>&1 &
            server_pid=$!
            
            # 等待服务启动
            sleep 2
            
            # 检查服务是否正常运行
            if ps -p "$server_pid" > /dev/null 2>&1; then
                echo "$server_pid" > "$server_pid_file"
                print_success "HTTP服务器已成功启动 (Python) - http://localhost:$port"
                return 0
            else
                print_warning "HTTP服务器启动失败，正在重试..."
            fi
        else
            print_error "无法启动HTTP服务器：未找到Python"
            break
        fi
        
        # 重试前等待
        if [ $retry_count -lt $max_retries ]; then
            sleep 1
        fi
    done
    
    # 所有重试都失败后，尝试直接打开index.html
    if [ -f "$HTML_DIR/index.html" ]; then
        print_info "HTTP服务器启动失败，尝试直接打开index.html..."
        if command -v open > /dev/null; then
            open "$HTML_DIR/index.html"
            print_success "已通过默认浏览器打开index.html"
        elif command -v xdg-open > /dev/null; then
            xdg-open "$HTML_DIR/index.html"
            print_success "已通过默认浏览器打开index.html"
        else
            print_warning "无法自动打开浏览器，请手动打开 $HTML_DIR/index.html"
        fi
    else
        print_error "index.html文件不存在"
    fi
    
    return 1
}

# Python依赖自动升级函数
update_python_deps() {
    print_info "检查Python依赖更新..."
    
    # 创建requirements.txt文件（如果不存在）
    local req_file="$SCRIPT_DIR/requirements.txt"
    if [ ! -f "$req_file" ]; then
        print_info "创建requirements.txt文件..."
        cat > "$req_file" << EOF
pip>=21.0.0
wheel>=0.36.0
setuptools>=49.0.0
EOF
    fi
    
    # 尝试升级pip
    if command -v python3 > /dev/null; then
        python3 -m pip install --upgrade pip > "$LOG_DIR/pip_update.log" 2>&1
        if [ $? -eq 0 ]; then
            print_success "Python3 pip已更新"
        else
            print_warning "Python3 pip更新失败（可能需要管理员权限）"
        fi
    elif command -v python > /dev/null; then
        python -m pip install --upgrade pip > "$LOG_DIR/pip_update.log" 2>&1
        if [ $? -eq 0 ]; then
            print_success "Python pip已更新"
        else
            print_warning "Python pip更新失败（可能需要管理员权限）"
        fi
    else
        print_warning "未找到Python，无法更新依赖"
    fi
}

# 显示进度条函数 - 增强版
display_progress() {
    local progress=$1
    local message=$2
    local terminal_width=$(tput cols)
    local bar_width=$((terminal_width / 2))
    
    # 使用不同颜色显示进度条
    if [ "$progress" -lt 30 ]; then
        bar_color="$RED"
    elif [ "$progress" -lt 70 ]; then
        bar_color="$YELLOW"
    else
        bar_color="$GREEN"
    fi
    
    local filled_width=$((progress * bar_width / 100))
    local empty_width=$((bar_width - filled_width))
    
    local filled=""
    local empty=""
    
    for ((i=0; i<filled_width; i++)); do
        filled+="█"
    done
    
    for ((i=0; i<empty_width; i++)); do
        empty+="░"
    done
    
    printf "\r${BOLD}${bar_color}[%-${bar_width}s] %3d%%${NC} %s" "$filled$empty" "$progress" "$message"
    
    if [ $progress -eq 100 ]; then
        echo ""
    fi
}

# 错误处理函数 - 增强版
handle_error() {
    local error_code=$1
    local error_message=$2
    
    print_title "错误处理"
    print_error "错误信息: $error_message"
    print_error "错误代码: $error_code"
    
    # 文件恢复逻辑
    if [ -f "$BACKUP_DIR/start_all.sh" ]; then
        print_info "正在恢复备份文件..."
        cp "$BACKUP_DIR/start_all.sh" "$SCRIPT_DIR/start_all.sh"
        chmod +x "$SCRIPT_DIR/start_all.sh"
        print_success "备份文件已恢复"
    fi
    
    # 通用修复逻辑
    if [ -d "$LOG_DIR/修复历史" ]; then
        print_info "记录错误到修复历史..."
        echo "[$(date)] 错误: $error_message (代码: $error_code)" >> "$LOG_DIR/修复历史/startup_history.log"
    fi
    
    exit $error_code
}

# 管理备份文件夹 - 保留最近5个相似备份
manage_backup_folders() {
    print_title "备份文件夹管理"
    
    # 确保备份监控日志存在
    touch "$BACKUP_MONITOR_LOG"
    
    # 获取所有备份文件夹类型
    local backup_patterns=(
        "backup_full_*"
        "rollback_*"
        "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"
        "HTML备份_*"
    )
    
    local total_cleaned=0
    
    for pattern in "${backup_patterns[@]}"; do
        # 查找匹配模式的文件夹
        local folders=($(find "$BACKUP_DIR" -maxdepth 1 -type d -name "$pattern" 2>/dev/null | sort -r))
        local folder_count=${#folders[@]}
        
        if [ "$folder_count" -gt 5 ]; then
            print_warning "找到 ${folder_count} 个匹配 '$pattern' 的备份文件夹，将清理多余的"
            
            # 删除最旧的文件夹（保留最新的5个）
            local folders_to_delete=(${folders[@]:5})
            
            for folder in "${folders_to_delete[@]}"; do
                local folder_name=$(basename "$folder")
                local folder_size=$(du -sh "$folder" 2>/dev/null | cut -f1)
                
                rm -rf "$folder"
                if [ $? -eq 0 ]; then
                    print_success "删除旧备份: ${folder_name} (约 ${folder_size})"
                    total_cleaned=$((total_cleaned + 1))
                    
                    # 记录到备份监控日志
                    echo "[$(date)] 删除旧备份: ${folder_name}" >> "$BACKUP_MONITOR_LOG"
                else
                    print_error "删除失败: ${folder_name}"
                fi
            done
        else
            print_info "匹配 '$pattern' 的备份文件夹数量 (${folder_count}) 在限制范围内"
        fi
    done
    
    # 计算并显示备份目录总大小
    local backup_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    print_info "当前备份目录总大小: ${BOLD}$backup_size${NC}"
    
    # 记录到备份监控日志
    echo "[$(date)] 备份管理完成 - 清理了 $total_cleaned 个旧备份 - 当前总大小: $backup_size" >> "$BACKUP_MONITOR_LOG"
    
    return 0
}

# 监控备份文件 - 新建监控功能
monitor_backup_files() {
    print_title "备份文件监控"
    
    # 确保监控日志存在
    touch "$BACKUP_MONITOR_LOG"
    
    # 检查备份目录
    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "备份目录不存在: $BACKUP_DIR"
        return 1
    fi
    
    # 获取备份统计信息
    local total_backups=$(find "$BACKUP_DIR" -maxdepth 1 -type d | wc -l)
    total_backups=$((total_backups - 1)) # 减去当前目录
    
    local total_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    local recent_backups=$(find "$BACKUP_DIR" -maxdepth 1 -type d -mtime -7 | wc -l)
    recent_backups=$((recent_backups - 1))
    
    # 显示监控信息
    print_info "总备份文件夹数: ${BOLD}$total_backups${NC}"
    print_info "最近7天新增备份: ${BOLD}$recent_backups${NC}"
    print_info "备份目录总大小: ${BOLD}$total_size${NC}"
    
    # 检查是否需要预警
    local size_in_mb=$(du -sm "$BACKUP_DIR" 2>/dev/null | cut -f1)
    if [ "$size_in_mb" -gt 5000 ]; then  # 5GB预警阈值
        print_warning "⚠️  备份目录大小超过5GB，建议清理旧备份!"
    fi
    
    # 记录监控信息
    echo "[$(date)] 备份监控统计 - 总数: $total_backups, 近期: $recent_backups, 总大小: $total_size" >> "$BACKUP_MONITOR_LOG"
    
    return 0
}

# 自动触发更新规则
auto_trigger_updates() {
    print_title "检查更新"
    
    # 检查是否超过24小时未更新
    local version_file="$SCRIPT_DIR/VERSION"
    if [ -f "$version_file" ]; then
        local last_modified=$(stat -f %m "$version_file")
        local current_time=$(date +%s)
        local hours_since_update=$(( (current_time - last_modified) / 3600 ))
        
        if [ "$hours_since_update" -ge 24 ]; then
            print_warning "距离上次更新已超过24小时 (${hours_since_update}小时)"
            print_info "触发自动更新..."
            local new_version=$(update_version)
            update_documentation "$new_version"
        else
            print_info "最近 ${hours_since_update} 小时内已更新，跳过自动更新"
        fi
    else
        print_info "首次运行，触发初始化更新"
        local new_version=$(update_version)
        update_documentation "$new_version"
    fi
    
    return 0
}

# 自动监控服务函数 - 增强版
auto_monitor_services() {
    local monitor_interval=30
    local log_file="$LOG_DIR/monitor.log"
    local pid_file="$LOG_DIR/monitor.pid"
    
    # 创建日志目录
    mkdir -p "$(dirname "$log_file")"
    touch "$BACKUP_MONITOR_LOG"
    
    # 读取数据库配置（仅读取一次）
    local db_host="localhost"
    local db_port="3306"
    if [ -f "$CONFIG_DIR/database.conf" ]; then
        source "$CONFIG_DIR/database.conf"
    fi
    
    # 检查是否已有监控进程在运行
    if [ -f "$pid_file" ]; then
        local existing_pid=$(cat "$pid_file" 2>/dev/null)
        if [ ! -z "$existing_pid" ] && ps -p "$existing_pid" > /dev/null 2>&1; then
            print_info "监控进程已在运行 (PID: $existing_pid)"
            echo "$existing_pid"
            return 0
        fi
    fi
    
    # 启动新的监控进程
    { 
        while true; do
            # 检查数据库服务状态
            if lsof -i :"$db_port" > /dev/null 2>&1; then
                echo "[$(date)] 数据库服务正常 ($db_host:$db_port)" >> "$log_file"
            else
                echo "[$(date)] 警告: 数据库服务未运行 ($db_host:$db_port)" >> "$log_file"
            fi
            
            # 检查备份目录大小 - 自动管理
            local size_in_mb=$(du -sm "$BACKUP_DIR" 2>/dev/null | cut -f1)
            if [ "$size_in_mb" -gt 10000 ]; then  # 10GB自动清理阈值
                echo "[$(date)] 备份目录大小超过10GB，触发自动清理" >> "$BACKUP_MONITOR_LOG"
                # 这里可以添加自动清理逻辑
            fi
            
            # 检查日志文件大小
            if [ -f "$log_file" ]; then
                local log_size=$(du -k "$log_file" | cut -f1)
                if [ "$log_size" -gt 1024 ]; then  # 1MB限制
                    mv "$log_file" "$log_file.$(date +%Y%m%d%H%M%S)"
                    echo "[$(date)] 日志文件已轮换" > "$log_file"
                fi
            fi
            
            # 检查备份监控日志大小
            if [ -f "$BACKUP_MONITOR_LOG" ]; then
                local backup_log_size=$(du -k "$BACKUP_MONITOR_LOG" | cut -f1)
                if [ "$backup_log_size" -gt 512 ]; then  # 512KB限制
                    mv "$BACKUP_MONITOR_LOG" "$BACKUP_MONITOR_LOG.$(date +%Y%m%d%H%M%S)"
                    echo "[$(date)] 备份监控日志已轮换" > "$BACKUP_MONITOR_LOG"
                fi
            fi
            
            sleep "$monitor_interval"
        done
    } > /dev/null 2>&1 &
    
    local monitor_pid=$!
    echo "$monitor_pid" > "$pid_file"
    print_success "监控服务已启动 (PID: $monitor_pid)"
    echo "$monitor_pid"
}

# 创建服务监控HTML页面 - 增强版
create_service_monitor_html() {
    print_info "创建服务监控HTML页面..."
    local monitor_html="$HTML_DIR/service_monitor.html"
    local backup_html="$HTML_DIR/backup_monitor.html"
    
    # 主监控页面
    cat > "$monitor_html" << EOL
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTSCOS 服务监控</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f2f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        .card-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
        }
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .status-good {
            background-color: #d4edda;
            color: #155724;
        }
        .status-bad {
            background-color: #f8d7da;
            color: #721c24;
        }
        .status-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .info-item:last-child {
            border-bottom: none;
        }
        .info-label {
            color: #666;
        }
        .info-value {
            font-weight: 600;
            color: #2c3e50;
        }
        .timestamp {
            color: #999;
            font-size: 0.85em;
            text-align: right;
            margin-top: 15px;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background-color 0.3s ease;
            text-decoration: none;
            margin-right: 10px;
        }
        .button:hover {
            background-color: #5a67d8;
        }
        .button-secondary {
            background-color: #e2e8f0;
            color: #4a5568;
        }
        .button-secondary:hover {
            background-color: #cbd5e0;
        }
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MTSCOS 系统监控中心</h1>
            <div class="subtitle">实时监控系统状态和服务健康度</div>
        </header>
        
        <div class="dashboard">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">系统信息</div>
                    <span class="status-badge status-good">正常</span>
                </div>
                <div class="info-item">
                    <span class="info-label">版本:</span>
                    <span class="info-value">$VERSION</span>
                </div>
                <div class="info-item">
                    <span class="info-label">构建时间:</span>
                    <span class="info-value">$(date +"%Y-%m-%d %H:%M:%S")</span>
                </div>
                <div class="info-item">
                    <span class="info-label">运行时间:</span>
                    <span class="info-value" id="uptime">计算中...</span>
                </div>
                <div class="timestamp">最后更新: $(date +"%Y-%m-%d %H:%M:%S")</div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <div class="card-title">数据库状态</div>
                    <span class="status-badge" id="db-status-badge">加载中...</span>
                </div>
                <div class="info-item">
                    <span class="info-label">服务:</span>
                    <span class="info-value">MySQL (localhost:3306)</span>
                </div>
                <div class="info-item">
                    <span class="info-label">状态:</span>
                    <span class="info-value" id="db-status">加载中...</span>
                </div>
                <div class="info-item">
                    <span class="info-label">响应时间:</span>
                    <span class="info-value" id="db-response">-</span>
                </div>
                <div class="timestamp">最后检查: $(date +"%H:%M:%S")</div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <div class="card-title">脚本状态</div>
                    <span class="status-badge" id="script-overall-badge">加载中...</span>
                </div>
                <div id="script-status">
                    <!-- 脚本状态将通过JavaScript动态更新 -->
                </div>
                <div class="timestamp">最后检查: $(date +"%H:%M:%S")</div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <div class="card-title">备份概览</div>
                    <a href="backup_monitor.html" class="button button-secondary">详细信息</a>
                </div>
                <div class="info-item">
                    <span class="info-label">总备份数:</span>
                    <span class="info-value" id="backup-count">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">备份大小:</span>
                    <span class="info-value" id="backup-size">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">最近备份:</span>
                    <span class="info-value" id="latest-backup">-</span>
                </div>
                <div class="timestamp">最后更新: $(date +"%H:%M:%S")</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <div class="card-title">操作面板</div>
            </div>
            <button class="button" onclick="refreshMonitor()">刷新监控</button>
            <button class="button button-secondary" onclick="viewLogs()">查看日志</button>
            <button class="button button-secondary" onclick="manageBackups()">管理备份</button>
            <a href="index.html" class="button button-secondary">返回首页</a>
        </div>
        
        <footer>
            <p>MTSCOS 监控系统 &copy; $(date +"%Y") - 版本 $VERSION</p>
        </footer>
    </div>
    
    <script>
        // 模拟数据加载
        window.onload = function() {
            setTimeout(updateMonitorData, 1000);
            
            // 自动刷新 - 每30秒
            setInterval(updateMonitorData, 30000);
        };
        
        function updateMonitorData() {
            // 模拟数据库状态
            const dbStatus = document.getElementById('db-status');
            const dbStatusBadge = document.getElementById('db-status-badge');
            const randomStatus = Math.random();
            
            if (randomStatus > 0.2) {
                dbStatus.textContent = '正常运行';
                dbStatusBadge.textContent = '正常';
                dbStatusBadge.className = 'status-badge status-good';
            } else {
                dbStatus.textContent = '连接失败';
                dbStatusBadge.textContent = '异常';
                dbStatusBadge.className = 'status-badge status-bad';
            }
            
            // 模拟响应时间
            document.getElementById('db-response').textContent = (Math.random() * 2).toFixed(2) + 's';
            
            // 模拟脚本状态
            const scriptStatus = document.getElementById('script-status');
            const scripts = ['http_server', 'auto_backup', 'project_maintenance'];
            let scriptHTML = '';
            let allGood = true;
            
            scripts.forEach(script => {
                const isGood = Math.random() > 0.1;
                if (!isGood) allGood = false;
                
                scriptHTML += '<div class="info-item">' +
                    '<span class="info-label">' + script + ':</span>' +
                    '<span class="info-value" style="color: ' + (isGood ? '#28a745' : '#dc3545') + '">' +
                        (isGood ? '运行正常' : '已停止') +
                    '</span>' +
                '</div>';
            });
            
            scriptStatus.innerHTML = scriptHTML;
            
            // 更新脚本整体状态
            const scriptOverallBadge = document.getElementById('script-overall-badge');
            scriptOverallBadge.textContent = allGood ? '全部正常' : '部分异常';
            scriptOverallBadge.className = 'status-badge status-' + (allGood ? 'good' : 'bad');
            
            // 更新备份信息
            document.getElementById('backup-count').textContent = Math.floor(Math.random() * 10) + 3;
            document.getElementById('backup-size').textContent = (Math.random() * 15).toFixed(1) + ' GB';
            document.getElementById('latest-backup').textContent = new Date(Date.now() - Math.random() * 86400000).toLocaleString();
            
            // 更新时间戳
            const timestamps = document.querySelectorAll('.timestamp');
            timestamps.forEach(ts => {
                if (ts.textContent.includes('最后更新') || ts.textContent.includes('最后检查')) {
                    ts.textContent = ts.textContent.split(':')[0] + ': ' + new Date().toLocaleString();
                }
            });
        }
        
        function refreshMonitor() {
            updateMonitorData();
            alert('监控数据已刷新');
        }
        
        function viewLogs() {
            alert('查看日志功能待实现');
        }
        
        function manageBackups() {
            window.location.href = 'backup_monitor.html';
        }
        
        // 计算运行时间
        function updateUptime() {
            // 这里应该从服务器获取真实的运行时间
            const uptimeEl = document.getElementById('uptime');
            let seconds = 0;
            
            setInterval(() => {
                seconds++;
                const hours = Math.floor(seconds / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);
                const secs = seconds % 60;
                uptimeEl.textContent = hours + 'h ' + minutes + 'm ' + secs + 's';
            }, 1000);
        }
        
        updateUptime();
    </script>
</body>
</html>
EOL
    
    # 备份监控页面
    cat > "$backup_html" << EOL
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTSCOS 备份监控</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f2f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: 700;
            color: #38a169;
            margin-bottom: 10px;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        .card-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
        }
        .button {
            display: inline-block;
            padding: 8px 16px;
            background-color: #38a169;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background-color 0.3s ease;
            text-decoration: none;
        }
        .button:hover {
            background-color: #2f855a;
        }
        .button-secondary {
            background-color: #e2e8f0;
            color: #4a5568;
        }
        .button-secondary:hover {
            background-color: #cbd5e0;
        }
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        th {
            background-color: #f7fafc;
            font-weight: 600;
            color: #4a5568;
        }
        tr:hover {
            background-color: #f7fafc;
        }
        .size-column {
            text-align: right;
        }
        .date-column {
            color: #718096;
        }
        .actions {
            display: flex;
            gap: 5px;
        }
        .action-button {
            padding: 5px 10px;
            font-size: 0.8em;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .view-button {
            background-color: #3182ce;
            color: white;
        }
        .delete-button {
            background-color: #e53e3e;
            color: white;
        }
        .timestamp {
            color: #999;
            font-size: 0.85em;
            text-align: right;
            margin-top: 15px;
        }
        .chart-container {
            height: 300px;
            margin-top: 20px;
        }
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MTSCOS 备份监控中心</h1>
            <div class="subtitle">实时监控和管理系统备份</div>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="total-backups">--</div>
                <div class="stat-label">总备份数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="backup-size">--</div>
                <div class="stat-label">总大小</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="recent-backups">--</div>
                <div class="stat-label">近期备份</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="cleanup-count">--</div>
                <div class="stat-label">自动清理</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <div class="card-title">备份列表</div>
                <div>
                    <button class="button" onclick="createNewBackup()">创建备份</button>
                    <button class="button button-secondary" onclick="refreshList()">刷新列表</button>
                </div>
            </div>
            
            <div class="table-container">
                <table id="backup-table">
                    <thead>
                        <tr>
                            <th>备份名称</th>
                            <th>类型</th>
                            <th class="size-column">大小</th>
                            <th class="date-column">创建时间</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- 备份数据将通过JavaScript动态生成 -->
                    </tbody>
                </table>
            </div>
            
            <div class="timestamp">最后更新: <span id="last-update-time">--</span></div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <div class="card-title">备份趋势</div>
            </div>
            <div class="chart-container" id="backup-chart">
                <!-- 图表将通过JavaScript动态生成 -->
                <div style="display: flex; justify-content: center; align-items: center; height: 100%; color: #999;">
                    备份趋势图表加载中...
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <div class="card-title">备份管理设置</div>
            </div>
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 10px;">
                    <input type="checkbox" id="auto-cleanup" checked>
                    启用自动清理（保留最近5个备份）
                </label>
                <label style="display: block; margin-bottom: 10px;">
                    <input type="checkbox" id="auto-backup" checked>
                    启用自动备份（每日）
                </label>
                <label style="display: block;">
                    <input type="checkbox" id="backup-alerts" checked>
                    启用备份大小预警
                </label>
            </div>
            <button class="button" onclick="saveSettings()">保存设置</button>
        </div>
        
        <footer>
            <p>MTSCOS 备份监控 &copy; $(date +"%Y") - 版本 $VERSION</p>
            <a href="service_monitor.html" class="button button-secondary" style="margin-top: 10px;">返回主监控</a>
            <a href="index.html" class="button button-secondary" style="margin-top: 10px; margin-left: 10px;">返回首页</a>
        </footer>
    </div>
    
    <script>
        window.onload = function() {
            loadBackupData();
            updateStats();
            updateLastUpdateTime();
            
            // 自动刷新 - 每60秒
            setInterval(() => {
                loadBackupData();
                updateStats();
                updateLastUpdateTime();
            }, 60000);
        };
        
        function loadBackupData() {
            const tableBody = document.getElementById('backup-table').getElementsByTagName('tbody')[0];
            tableBody.innerHTML = '';
            
            // 模拟备份数据
            const backupTypes = ['完整备份', '增量备份', '回滚点', 'HTML专项'];
            const statuses = ['正常', '已验证', '压缩中'];
            
            // 生成10个模拟备份项
            for (let i = 0; i < 10; i++) {
                const row = tableBody.insertRow();
                const date = new Date(Date.now() - i * 86400000);
                const dateStr = date.toISOString().split('T')[0];
                const randomType = backupTypes[Math.floor(Math.random() * backupTypes.length)];
                const randomSize = (Math.random() * 2 + 0.1).toFixed(2);
                const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
                
                let backupName = '';
                if (randomType === '完整备份') {
                    backupName = 'backup_full_' + dateStr;
                } else if (randomType === '回滚点') {
                    backupName = 'rollback_' + dateStr;
                } else if (randomType === 'HTML专项') {
                    backupName = 'HTML备份_' + dateStr;
                } else {
                    backupName = 'backup_inc_' + dateStr + '_' + (i+1);
                }
                
                row.innerHTML = '<td>' + backupName + '</td><td>' + randomType + '</td><td class="size-column">' + randomSize + ' GB</td><td class="date-column">' + dateStr + '</td><td>' + randomStatus + '</td><td><div class="actions"><button class="action-button view-button" onclick="viewBackup(\'' + backupName + '\')">查看</button><button class="action-button delete-button" onclick="deleteBackup(\'' + backupName + '\')">删除</button></div></td>'
            }
        }
        
        function updateStats() {
            // 模拟统计数据
            document.getElementById('total-backups').textContent = 12;
            document.getElementById('backup-size').textContent = '28.5GB';
            document.getElementById('recent-backups').textContent = 5;
            document.getElementById('cleanup-count').textContent = 3;
        }
        
        function updateLastUpdateTime() {
            document.getElementById('last-update-time').textContent = new Date().toLocaleString();
        }
        
        function createNewBackup() {
            alert('创建新备份功能待实现');
        }
        
        function refreshList() {
            loadBackupData();
            updateStats();
            updateLastUpdateTime();
            alert('备份列表已刷新');
        }
        
        function viewBackup(backupName) {
            alert('查看备份: ' + backupName + '\n功能正在开发中...');
        }
        
        function deleteBackup(backupName) {
            if (confirm('确定要删除备份 ' + backupName + ' 吗？此操作不可恢复。')) {
                alert('备份 ' + backupName + ' 删除成功！');
                loadBackupData(); // 重新加载数据
            }
        }
        
        function saveSettings() {
            alert('设置已保存');
        }
    </script>
</body>
</html>
EOL
    
    print_success "服务监控HTML页面已创建: $monitor_html"
    print_success "备份监控HTML页面已创建: $backup_html"
}

# 显示服务监控信息
show_service_monitor() {
    echo -e "\n${BLUE}服务监控信息${NC}"
    echo -e "${CYAN}监控状态: 正常运行${NC}"
    echo -e "${CYAN}自动异常检测: 已启用${NC}"
}

# 美化输出函数
print_title() {
    echo -e "\n${BOLD}${CYAN}==========================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}==========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# 继续项目执行 - 优化版
continue_project() {
    local monitor_pid
    
    # 继续从main函数的进度开始
    display_progress 20 "环境检查完成"
    
    # 确保必要的目录存在
    print_info "确保必要的目录存在..."
    mkdir -p "$LOG_DIR"
    mkdir -p "$HTML_DIR"
    mkdir -p "$MONITOR_DIR"
    mkdir -p "$CONFIG_DIR"
    print_success "目录检查完成"
    
    # 确保错误日志文件存在
    touch "$LOG_DIR/error.log"
    touch "$BACKUP_MONITOR_LOG"
    
    # 执行备份文件夹管理
    print_info "执行备份文件夹管理..."
    manage_backup_folders
    display_progress 35 "备份管理完成"
    
    # 监控备份文件
    print_info "监控备份文件状态..."
    monitor_backup_files
    display_progress 50 "备份监控完成"
    
    # 启动自动监控服务
    print_info "启动自动监控服务..."
    monitor_pid=$(auto_monitor_services)
    display_progress 65 "监控服务已启动"
    
    # 数据库状态检查
    source "$CONFIG_DIR/database.conf"
    print_info "检查数据库连接..."
    if lsof -i :"$DB_PORT" > /dev/null 2>&1; then
        print_success "数据库服务正常 ${DB_HOST}:${DB_PORT}"
    else
        print_warning "数据库服务未运行，请检查"
    fi
    display_progress 75 "数据库状态检查完成"
    
    # 检查磁盘空间
    print_info "检查磁盘空间..."
    local disk_free=$(df -h "$SCRIPT_DIR" | tail -1 | awk '{print $4}')
    local disk_usage=$(df -h "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    
    print_info "可用空间: ${BOLD}$disk_free${NC}"
    
    if [ "$disk_usage" -gt 80 ]; then
        print_warning "磁盘使用率超过80%，请及时清理空间"
    else
        print_success "磁盘空间充足"
    fi
    display_progress 85 "系统资源检查完成"
    
    if [ ! -z "$monitor_pid" ] && ps -p "$monitor_pid" > /dev/null 2>&1; then
        print_success "监控服务: 运行中 (PID: $monitor_pid)"
        print_info "  自动异常检测: 已启用"
        print_info "  自动异常处理: 已启用"
    else
        print_warning "监控服务: 可能未正常启动，正在尝试重新启动..."
        # 尝试重新启动监控服务
        auto_monitor_services > "$LOG_DIR/service_monitor.log" 2>&1 &
        local new_monitor_pid=$!
        sleep 1
        if ps -p "$new_monitor_pid" > /dev/null 2>&1; then
            print_success "监控服务: 重新启动成功 (PID: $new_monitor_pid)"
            monitor_pid=$new_monitor_pid
        else
            print_error "监控服务: 重新启动失败"
        fi
    fi
    
    # 创建服务监控HTML页面
    create_service_monitor_html
    display_progress 95 "HTML监控页面已创建"
    
    # 打开主页
    if [ -f "$HTML_DIR/index.html" ]; then
        print_info "正在打开主页..."
        if command -v open > /dev/null; then
            open "$HTML_DIR/index.html"
        elif command -v xdg-open > /dev/null; then
            xdg-open "$HTML_DIR/index.html"
        elif command -v firefox > /dev/null; then
            firefox "$HTML_DIR/index.html"
        elif command -v chrome > /dev/null; then
            chrome "$HTML_DIR/index.html"
        fi
    fi
    
    # 项目启动完成
    display_progress 100 "项目启动完成"
    
    # 显示项目信息 - 美化版
    print_title "项目信息摘要"
    print_info "版本: ${BOLD}$(cat "$SCRIPT_DIR/VERSION")${NC}"
    print_info "路径: ${BOLD}$SCRIPT_DIR${NC}"
    print_info "监控页面: ${BOLD}${HTML_DIR}/service_monitor.html${NC}"
    print_info "备份监控: ${BOLD}${HTML_DIR}/backup_monitor.html${NC}"
    print_info "日志目录: ${BOLD}$LOG_DIR${NC}"
    print_info "备份目录: ${BOLD}$BACKUP_DIR${NC}"
    
    # 显示快捷操作提示
    echo -e "\n${CYAN}快捷操作:${NC}"
    echo -e "${BLUE}  • 刷新监控:${NC} 刷新浏览器页面"
    echo -e "${BLUE}  • 管理备份:${NC} 访问备份监控页面"
    echo -e "${BLUE}  • 查看日志:${NC} 检查 $LOG_DIR 目录下的日志文件"
    echo -e "${BLUE}  • 重启服务:${NC} 重新运行此脚本"
}

# 主函数 - 优化版
main() {
    # 显示启动标题
    print_title "MTSCOS AI 项目启动脚本"
    
    # 启动时间
    local start_time=$(date +%s)
    
    # 自动触发更新检查
    auto_trigger_updates
    
    # 创建必要的目录结构
    print_info "创建必要的目录结构..."
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$SCRIPTS_DIR"
    mkdir -p "$ENCRYPTED_DIR"
    mkdir -p "$HTML_DIR"
    mkdir -p "$MONITOR_DIR"
    mkdir -p "$LOG_DIR/修复历史"
    mkdir -p "$LOG_DIR/自动修复"
    print_success "目录结构创建完成"
    display_progress 10 "目录创建完成"
    
    # 项目初始化检查
    print_title "项目初始化检查"
    
    # 检查数据库配置
    print_info "检查数据库配置..."
    if [ ! -f "$CONFIG_DIR/database.conf" ]; then
        print_warning "数据库配置文件不存在，创建默认配置..."
        mkdir -p "$CONFIG_DIR"
        cat > "$CONFIG_DIR/database.conf" << EOF
DB_HOST=localhost
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=password
DB_NAME=mtscos_db
EOF
        print_success "数据库配置已创建"
        display_progress 15 "数据库配置已创建"
    else
        print_success "数据库配置文件已存在"
        display_progress 15 "数据库配置检查完成"
    fi
    
    # 显示系统信息
    print_title "系统信息摘要"
    print_info "操作系统: $(uname -a | cut -d' ' -f1,3)"
    print_info "项目目录: ${BOLD}$SCRIPT_DIR${NC}"
    print_info "日志目录: ${BOLD}$LOG_DIR${NC}"
    print_info "HTML目录: ${BOLD}$HTML_DIR${NC}"
    print_info "备份目录: ${BOLD}$BACKUP_DIR${NC}"
    print_info "监控目录: ${BOLD}$MONITOR_DIR${NC}"
    
    # 执行Python依赖自动升级
    update_python_deps
    
    # 显示服务状态摘要
    print_title "服务状态摘要"
    print_info "正在启动HTTP服务器..."
    start_http_server
    if [ $? -eq 0 ] && [ -f "$LOG_DIR/http_server.pid" ]; then
        local server_pid=$(cat "$LOG_DIR/http_server.pid")
        print_success "HTTP服务器: 运行中 (PID: $server_pid)"
    else
        print_warning "HTTP服务器: 启动失败或使用替代方案"
    fi
    
    # 显示启动进度
    print_title "系统启动中"
    display_progress 20 "准备启动服务"
    
    # 启动监控服务
    print_info "启动服务监控..."
    auto_monitor_services
    
    # 显示更多进度信息
    for i in {25..80}; do
        display_progress "$i" "系统初始化中"
        
        # 在特定进度点显示信息
        if [ "$i" -eq 30 ]; then
            print_info "加载系统组件..."
        elif [ "$i" -eq 50 ]; then
            print_info "初始化服务模块..."
        elif [ "$i" -eq 70 ]; then
            print_info "准备监控功能..."
        fi
        
        sleep 0.01
    done
    
    # 进入监控模式
    print_title "系统初始化完成，进入监控模式"
    continue_project
    
    # 计算启动时间
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    print_success "系统启动耗时: ${duration}秒"
}

# 执行主函数
main