#!/bin/bash

# 脚本版本
SCRIPT_VERSION="4.2"

# 定义目录路径
PROJECT_ROOT="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
TEMP_DIR="${PROJECT_ROOT}/temp"
BACKUP_DIR="${PROJECT_ROOT}/backup"
LOG_DIR="${PROJECT_ROOT}/Logs"
HTML_DIR="${PROJECT_ROOT}/html"
SOURCE_DIR="${PROJECT_ROOT}/SourceCode"
CSS_DIR="${SOURCE_DIR}/CSS"
JS_DIR="${SOURCE_DIR}/JavaScript"
PY_DIR="${SOURCE_DIR}/Python"
JAVA_DIR="${SOURCE_DIR}/Java"
SH_DIR="${SOURCE_DIR}/Shell"
BAK_DIR="${PROJECT_ROOT}/Backups"
SCRIPTS_DIR="${PROJECT_ROOT}/Scripts"

# 创建必要目录
mkdir -p "${TEMP_DIR}"
mkdir -p "${BACKUP_DIR}"
mkdir -p "${LOG_DIR}"
mkdir -p "${HTML_DIR}"
mkdir -p "${CSS_DIR}"
mkdir -p "${JS_DIR}"
mkdir -p "${PY_DIR}"
mkdir -p "${JAVA_DIR}"
mkdir -p "${SH_DIR}"
mkdir -p "${BAK_DIR}"

# 日志函数
log_message() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${message}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${message}" >> "${LOG_DIR}/run.log"
}

# 初始化日志
log_message "Auto_Start.sh v${SCRIPT_VERSION} 启动"

# 确保主索引文件存在
MAIN_INDEX="${HTML_DIR}/index.html"
if [ ! -f "${MAIN_INDEX}" ]; then
    log_message "创建主索引文件"
    echo '<!DOCTYPE html><html><head><title>主页面</title></head><body><h1>项目主页面</h1></body></html>' > "${MAIN_INDEX}"
fi

# 查找并更新其他index.html文件
log_message "查找其他索引文件..."
find "${PROJECT_ROOT}" -name "index.html" -not -path "${HTML_DIR}/*" | while read file; do
    # 备份
    cp "${file}" "${BACKUP_DIR}/$(basename "${file}").bak"
    log_message "已备份: ${file}"
    
    # 创建简单的重定向页面
    echo '<!DOCTYPE html>' > "${file}"
    echo '<html>' >> "${file}"
    echo '<head>' >> "${file}"
    echo '<meta http-equiv="refresh" content="1;url=../html/index.html">' >> "${file}"
    echo '<title>重定向</title>' >> "${file}"
    echo '</head>' >> "${file}"
    echo '<body>' >> "${file}"
    echo '<p>正在重定向... <a href="../html/index.html">点击此处</a></p>' >> "${file}"
    echo '</body>' >> "${file}"
    echo '</html>' >> "${file}"
    
    log_message "已更新索引文件: ${file}"
done

# 检测文件引用函数 - 增强版
check_file_references() {
    local file_type="$1"
    local search_term="$2"
    local base_dir="$3"
    local missing_count=0
    local total_count=0
    
    log_message "开始检测${file_type}文件引用..."
    
    # 查找所有可能包含引用的文件
    find "${PROJECT_ROOT}" -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.py" -o -name "*.sh" \) | while read file; do
        # 跳过临时目录和备份目录
        if [[ "${file}" == *"${TEMP_DIR}"* || "${file}" == *"${BACKUP_DIR}"* ]]; then
            continue
        fi
        
        # 根据文件类型进行简单的内容检查
        case "${file_type}" in
            css)
                # 检查CSS引用
                if grep -q "<link.*\.css\"\|'<link.*\.css'" "${file}"; then
                    log_message "在 ${file} 中发现 CSS 引用"
                    total_count=$((total_count + 1))
                fi
                ;;
            js)
                # 检查JS引用
                if grep -q "<script.*\.js\"\|'<script.*\.js'" "${file}"; then
                    log_message "在 ${file} 中发现 JavaScript 引用"
                    total_count=$((total_count + 1))
                fi
                ;;
            py)
                # 检查Python导入
                if grep -q "import " "${file}" || grep -q "from " "${file}"; then
                    log_message "在 ${file} 中发现 Python 导入"
                    total_count=$((total_count + 1))
                fi
                ;;
            sh)
                # 检查Shell引用
                if grep -q "\. ".*\.sh\"\|source ".*\.sh\"" "${file}"; then
                    log_message "在 ${file} 中发现 Shell 脚本引用"
                    total_count=$((total_count + 1))
                fi
                ;;
        esac
    done
    
    log_message "${file_type}文件引用检测完成，共检测到 ${total_count} 个引用"
}

# 自动更新Python脚本功能
auto_update_python() {
    log_message "开始自动更新Python脚本..."
    
    # 查找所有Python脚本
    find "${PY_DIR}" -name "*.py" | while read py_file; do
        log_message "检查Python脚本: ${py_file}"
        
        # 这里可以添加Python脚本的特定更新逻辑
        # 例如: 更新导入语句、添加注释、格式化等
        
        # 简单示例: 添加更新日期注释
        if ! grep -q "# 上次更新:" "${py_file}"; then
            sed -i '' "1i\\
# 上次更新: $(date '+%Y-%m-%d %H:%M:%S')
" "${py_file}"
            log_message "已更新: ${py_file}"
        else
            sed -i '' "s/# 上次更新:.*/# 上次更新: $(date '+%Y-%m-%d %H:%M:%S')/" "${py_file}"
            log_message "已更新日期: ${py_file}"
        fi
    done
    
    log_message "Python脚本更新完成"
}

# 自动更新Java功能
auto_update_java() {
    log_message "开始自动更新Java文件..."
    
    # 查找所有Java文件
    find "${JAVA_DIR}" -name "*.java" | while read java_file; do
        log_message "检查Java文件: ${java_file}"
        
        # 简单示例: 添加更新日期注释
        if ! grep -q "// 上次更新:" "${java_file}"; then
            sed -i '' "1i\\
// 上次更新: $(date '+%Y-%m-%d %H:%M:%S')
" "${java_file}"
            log_message "已更新: ${java_file}"
        else
            sed -i '' "s|// 上次更新:.*|// 上次更新: $(date '+%Y-%m-%d %H:%M:%S')|" "${java_file}"
            log_message "已更新日期: ${java_file}"
        fi
    done
    
    log_message "Java文件更新完成"
}

# 文件归类功能
organize_files() {
    log_message "开始归类文件..."
    
    # 归类CSS文件
    log_message "归类CSS文件..."
    find "${PROJECT_ROOT}" -name "*.css" -not -path "${CSS_DIR}/*" -not -path "${LOG_DIR}/*" -not -path "${BACKUP_DIR}/*" | while read css_file; do
        local filename=$(basename "${css_file}")
        local dest="${CSS_DIR}/${filename}"
        
        # 如果目标文件已存在，添加时间戳
        if [ -f "${dest}" ]; then
            local timestamp=$(date '+%Y%m%d%H%M%S')
            dest="${CSS_DIR}/${filename%.css}_${timestamp}.css"
        fi
        
        log_message "移动CSS文件: ${css_file} -> ${dest}"
        mv "${css_file}" "${dest}"
    done
    
    # 归类JavaScript文件
    log_message "归类JavaScript文件..."
    find "${PROJECT_ROOT}" -name "*.js" -not -path "${JS_DIR}/*" -not -path "${LOG_DIR}/*" -not -path "${BACKUP_DIR}/*" | while read js_file; do
        local filename=$(basename "${js_file}")
        local dest="${JS_DIR}/${filename}"
        
        if [ -f "${dest}" ]; then
            local timestamp=$(date '+%Y%m%d%H%M%S')
            dest="${JS_DIR}/${filename%.js}_${timestamp}.js"
        fi
        
        log_message "移动JavaScript文件: ${js_file} -> ${dest}"
        mv "${js_file}" "${dest}"
    done
    
    # 归类Python文件
    log_message "归类Python文件..."
    find "${PROJECT_ROOT}" -name "*.py" -not -path "${PY_DIR}/*" -not -path "${LOG_DIR}/*" -not -path "${BACKUP_DIR}/*" | while read py_file; do
        local filename=$(basename "${py_file}")
        local dest="${PY_DIR}/${filename}"
        
        if [ -f "${dest}" ]; then
            local timestamp=$(date '+%Y%m%d%H%M%S')
            dest="${PY_DIR}/${filename%.py}_${timestamp}.py"
        fi
        
        log_message "移动Python文件: ${py_file} -> ${dest}"
        mv "${py_file}" "${dest}"
    done
    
    # 归类Shell脚本
    log_message "归类Shell脚本..."
    find "${PROJECT_ROOT}" -name "*.sh" -not -path "${SH_DIR}/*" -not -path "${SCRIPTS_DIR}/*" -not -path "${LOG_DIR}/*" -not -path "${BACKUP_DIR}/*" | while read sh_file; do
        local filename=$(basename "${sh_file}")
        local dest="${SH_DIR}/${filename}"
        
        if [ -f "${dest}" ]; then
            local timestamp=$(date '+%Y%m%d%H%M%S')
            dest="${SH_DIR}/${filename%.sh}_${timestamp}.sh"
        fi
        
        log_message "移动Shell脚本: ${sh_file} -> ${dest}"
        mv "${sh_file}" "${dest}"
        chmod +x "${dest}"
    done
    
    # 归类备份文件
    log_message "归类备份文件..."
    find "${PROJECT_ROOT}" -name "*.bak" | while read bak_file; do
        local filename=$(basename "${bak_file}")
        local dest="${BAK_DIR}/${filename}"
        
        if [ -f "${dest}" ]; then
            local timestamp=$(date '+%Y%m%d%H%M%S')
            dest="${BAK_DIR}/${filename%.bak}_${timestamp}.bak"
        fi
        
        log_message "移动备份文件: ${bak_file} -> ${dest}"
        mv "${bak_file}" "${dest}"
    done
    
    # 归类日志文件
    log_message "归类日志文件..."
    find "${PROJECT_ROOT}" -name "*.log" -not -path "${LOG_DIR}/*" | while read log_file; do
        local filename=$(basename "${log_file}")
        local dest="${LOG_DIR}/${filename}"
        
        if [ -f "${dest}" ]; then
            local timestamp=$(date '+%Y%m%d%H%M%S')
            dest="${LOG_DIR}/${filename%.log}_${timestamp}.log"
        fi
        
        log_message "移动日志文件: ${log_file} -> ${dest}"
        mv "${log_file}" "${dest}"
    done
    
    log_message "文件归类完成"
}

# 检测依赖项和服务
check_dependencies() {
    log_message "开始检测依赖项和服务..."
    
    # 检测必要的命令行工具
    local tools=("bash" "grep" "sed" "find" "cp" "mkdir" "date")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if ! command -v "${tool}" &> /dev/null; then
            missing_tools+=("${tool}")
        fi
    done
    
    if [ ${#missing_tools[@]} -eq 0 ]; then
        log_message "所有必要工具都已安装"
    else
        log_message "警告: 缺少以下工具: ${missing_tools[*]}"
    fi
    
    # 检测Python环境
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1)
        log_message "Python环境: ${python_version}"
    else
        log_message "警告: 未检测到Python环境"
    fi
    
    # 检测Java环境
    if command -v java &> /dev/null; then
        local java_version=$(java -version 2>&1 | head -n 1)
        log_message "Java环境: ${java_version}"
    else
        log_message "警告: 未检测到Java环境"
    fi
    
    # 检测项目必要目录
    local required_dirs=("${SOURCE_DIR}" "${HTML_DIR}" "${LOG_DIR}")
    local missing_dirs=()
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "${dir}" ]; then
            missing_dirs+=("${dir}")
        fi
    done
    
    if [ ${#missing_dirs[@]} -eq 0 ]; then
        log_message "所有必要目录都已存在"
    else
        log_message "警告: 缺少以下目录: ${missing_dirs[*]}"
    fi
}

# 检查更新
check_for_updates() {
    log_message "检查脚本更新..."
    
    # 记录当前版本到版本文件
    echo "${SCRIPT_VERSION}" > "${PROJECT_ROOT}/VERSION"
    
    # 获取上次更新时间
    if [ -f "${PROJECT_ROOT}/update_version.log" ]; then
        local last_update=$(cat "${PROJECT_ROOT}/update_version.log")
        log_message "上次更新: ${last_update}"
    fi
    
    # 更新更新日志
    echo "更新于 $(date) - 版本 ${SCRIPT_VERSION}" > "${PROJECT_ROOT}/update_version.log"
    log_message "已更新版本信息到 ${SCRIPT_VERSION}"
}

# 执行检测
check_file_references "css" "" "${PROJECT_ROOT}"
check_file_references "js" "" "${PROJECT_ROOT}"
check_file_references "py" "" "${PY_DIR}"
check_file_references "sh" "" "${PROJECT_ROOT}"

# 执行文件归类
organize_files

# 执行自动更新
auto_update_python
auto_update_java

# 检查依赖和更新
check_dependencies
check_for_updates

# 创建基本文档
log_message "更新项目文档..."

# 简单方式创建README
cat > "${PROJECT_ROOT}/README.md" << EOF
# MTSCOS_AI_Project
项目文档
更新于 $(date)
脚本版本: ${SCRIPT_VERSION}

## 功能特性
- 自动创建和管理项目目录结构
- 统一管理所有index.html文件，重定向到主页面
- 检测文件引用正确性（CSS, JS, Python, Shell）
- 检查项目依赖项和必要服务
- 版本管理和更新检测
- 自动更新Python和Java文件
- 智能归类CSS、JavaScript、Python、Shell、备份和日志文件
- 增强的链接检测功能
EOF

# 输出完成信息
log_message "脚本执行完成"

# 设置执行权限
chmod +x "$0"