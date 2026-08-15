#!/bin/bash
# MTSCOS AI 灰度发布自动化部署脚本
# 支持：自动构建、灰度发布、健康检查、自动回滚、全量发布

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"
FLASK_PORT=${FLASK_PORT:-8888}
RELEASE_VERSION=""
RELEASE_DESC=""
COMMIT_HASH=""
GRAY_STEPS="${GRAY_STEPS:-10,30,50,100}"
STEP_DURATION="${STEP_DURATION:-60}"

usage() {
    echo "MTSCOS AI 灰度发布自动化部署脚本"
    echo ""
    echo "用法: $0 [选项] <命令>"
    echo ""
    echo "命令:"
    echo "  create     创建发布计划"
    echo "  start      开始发布"
    echo "  gray       设置灰度比例"
    echo "  full       全量发布"
    echo "  complete   完成发布"
    echo "  rollback   回滚发布"
    echo "  auto       自动灰度发布流程"
    echo "  status     查看发布状态"
    echo "  health     检查健康状态"
    echo ""
    echo "选项:"
    echo "  -v, --version <版本>    设置版本号"
    echo "  -d, --desc <描述>       设置发布描述"
    echo "  -c, --commit <哈希>     设置提交哈希"
    echo "  -r, --release <ID>      指定发布ID"
    echo "  -p, --percentage <%>    设置灰度比例"
    echo "  -s, --steps <步骤>      自动发布步骤(逗号分隔)"
    echo "  -t, --time <秒>         每步等待时间"
    echo ""
    echo "示例:"
    echo "  $0 -v 1.9.0 -d '新功能发布' create"
    echo "  $0 -r release_xxx start"
    echo "  $0 -r release_xxx -p 10 gray"
    echo "  $0 -v 1.9.0 -d '自动发布测试' auto"
}

api_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local url="http://localhost:${FLASK_PORT}/api/release${endpoint}"
    
    if [ "$method" = "GET" ]; then
        curl -s "$url"
    else
        curl -s -X "$method" -H "Content-Type: application/json" -d "$data" "$url"
    fi
}

cmd_create() {
    if [ -z "$RELEASE_VERSION" ]; then
        echo "错误: 版本号不能为空"
        exit 1
    fi
    
    local data="{\"version\":\"${RELEASE_VERSION}\",\"description\":\"${RELEASE_DESC}\",\"commit_hash\":\"${COMMIT_HASH}\"}"
    echo "创建发布计划..."
    local result=$(api_request POST "/plan" "$data")
    echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
    
    RELEASE_ID=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('release_id',''))" 2>/dev/null)
    if [ -n "$RELEASE_ID" ]; then
        echo "发布ID: $RELEASE_ID"
        echo "请使用: $0 -r $RELEASE_ID start"
    fi
}

cmd_start() {
    if [ -z "$RELEASE_ID" ]; then
        echo "错误: 发布ID不能为空"
        exit 1
    fi
    
    echo "开始发布: $RELEASE_ID..."
    local result=$(api_request POST "/start/${RELEASE_ID}" "{}")
    echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
}

cmd_gray() {
    if [ -z "$RELEASE_ID" ]; then
        echo "错误: 发布ID不能为空"
        exit 1
    fi
    
    if [ -z "$GRAY_PERCENTAGE" ]; then
        echo "错误: 灰度比例不能为空"
        exit 1
    fi
    
    local data="{\"percentage\":${GRAY_PERCENTAGE}}"
    echo "设置灰度比例: ${RELEASE_ID} -> ${GRAY_PERCENTAGE}%"
    local result=$(api_request POST "/gray/${RELEASE_ID}" "$data")
    echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
}

cmd_full() {
    if [ -z "$RELEASE_ID" ]; then
        echo "错误: 发布ID不能为空"
        exit 1
    fi
    
    echo "全量发布: $RELEASE_ID..."
    local result=$(api_request POST "/full/${RELEASE_ID}" "{}")
    echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
}

cmd_complete() {
    if [ -z "$RELEASE_ID" ]; then
        echo "错误: 发布ID不能为空"
        exit 1
    fi
    
    echo "完成发布: $RELEASE_ID..."
    local result=$(api_request POST "/complete/${RELEASE_ID}" "{}")
    echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
}

cmd_rollback() {
    if [ -z "$RELEASE_ID" ]; then
        echo "错误: 发布ID不能为空"
        exit 1
    fi
    
    local reason="${RELEASE_DESC:-手动回滚}"
    local data="{\"reason\":\"${reason}\"}"
    echo "回滚发布: $RELEASE_ID, 原因: $reason"
    local result=$(api_request POST "/rollback/${RELEASE_ID}" "$data")
    echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
}

cmd_auto() {
    if [ -z "$RELEASE_VERSION" ]; then
        echo "错误: 版本号不能为空"
        exit 1
    fi
    
    local steps_array=(${GRAY_STEPS//,/ })
    local steps_json="["
    local first=true
    for step in "${steps_array[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            steps_json="$steps_json,"
        fi
        steps_json="$steps_json{\"percentage\":${step},\"duration\":${STEP_DURATION}}"
    done
    steps_json="$steps_json]"
    
    local data="{\"version\":\"${RELEASE_VERSION}\",\"description\":\"${RELEASE_DESC}\",\"steps\":${steps_json}}"
    echo "启动自动灰度发布..."
    echo "版本: $RELEASE_VERSION"
    echo "步骤: ${GRAY_STEPS}% (每步等待${STEP_DURATION}秒)"
    local result=$(api_request POST "/auto-release" "$data")
    echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
    
    RELEASE_ID=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('release_id',''))" 2>/dev/null)
    if [ -n "$RELEASE_ID" ]; then
        echo ""
        echo "自动发布已启动！"
        echo "发布ID: $RELEASE_ID"
        echo "可使用以下命令查看进度:"
        echo "  $0 -r $RELEASE_ID status"
        echo "  $0 health"
        echo "如需紧急回滚:"
        echo "  $0 -r $RELEASE_ID rollback"
    fi
}

cmd_status() {
    if [ -n "$RELEASE_ID" ]; then
        echo "发布状态: $RELEASE_ID"
        local result=$(api_request GET "/plan/${RELEASE_ID}" "")
        echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
    else
        echo "所有发布计划:"
        local result=$(api_request GET "/plans" "")
        echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
    fi
}

cmd_health() {
    echo "健康状态检查:"
    local result=$(api_request GET "/health" "")
    echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
    
    echo ""
    echo "当前灰度比例:"
    local gray_result=$(api_request GET "/gray/percentage" "")
    echo "$gray_result" | python3 -m json.tool 2>/dev/null || echo "$gray_result"
    
    echo ""
    echo "当前发布:"
    local current_result=$(api_request GET "/current" "")
    echo "$current_result" | python3 -m json.tool 2>/dev/null || echo "$current_result"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version)
            RELEASE_VERSION="$2"
            shift 2
            ;;
        -d|--desc)
            RELEASE_DESC="$2"
            shift 2
            ;;
        -c|--commit)
            COMMIT_HASH="$2"
            shift 2
            ;;
        -r|--release)
            RELEASE_ID="$2"
            shift 2
            ;;
        -p|--percentage)
            GRAY_PERCENTAGE="$2"
            shift 2
            ;;
        -s|--steps)
            GRAY_STEPS="$2"
            shift 2
            ;;
        -t|--time)
            STEP_DURATION="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            COMMAND="$1"
            shift
            ;;
    esac
done

if [ -z "$COMMAND" ]; then
    usage
    exit 1
fi

case "$COMMAND" in
    create)
        cmd_create
        ;;
    start)
        cmd_start
        ;;
    gray)
        cmd_gray
        ;;
    full)
        cmd_full
        ;;
    complete)
        cmd_complete
        ;;
    rollback)
        cmd_rollback
        ;;
    auto)
        cmd_auto
        ;;
    status)
        cmd_status
        ;;
    health)
        cmd_health
        ;;
    *)
        echo "未知命令: $COMMAND"
        usage
        exit 1
        ;;
esac