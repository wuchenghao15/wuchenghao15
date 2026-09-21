#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║  MTSCOS AI v23.0.0-Andromeda-Nova 一键部署              ║
# ║  目标: 192.168.31.9 (Linux)                            ║
# ║  源:  http://192.168.31.203:8080/ (本机 macOS HTTP)    ║
# ║  自动探测 curl/wget + auto-install                      ║
# ╚══════════════════════════════════════════════════════════╝
set -e

# 自动选部署目录: 优先 $DEPLOY_DIR, 尝试 /opt/mtscos(需 root), 否则 ~/mtscos
if [ -n "$DEPLOY_DIR" ]; then
    D="$DEPLOY_DIR"
elif [ "$(id -u)" = "0" ] && [ -w /opt ]; then
    D=/opt/mtscos
elif [ -w /opt ]; then
    D=/opt/mtscos
else
    D=$HOME/mtscos
fi
S=http://192.168.31.203:8080

echo ""
echo "📦 MTSCOS AI v23.0.0-Andromeda-Nova 一键部署"
echo "════════════════════════════════════════════════"
echo "部署目录: $D"
echo "下载源:   $S"
echo ""

# ===== 0. 自动安装缺失依赖 =====
echo "[0/5] 检查/自动安装依赖..."

install_pkg() {
    local pkg=$1
    echo "  安装 $pkg ..."
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq 2>/dev/null || true
        apt-get install -y -qq "$pkg" 2>/dev/null
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y "$pkg" 2>/dev/null
    elif command -v yum >/dev/null 2>&1; then
        yum install -y "$pkg" 2>/dev/null
    elif command -v apk >/dev/null 2>&1; then
        apk add --no-cache "$pkg" 2>/dev/null
    fi
}

# curl (递归下载用)
if ! command -v curl >/dev/null 2>&1; then
    install_pkg curl
fi
command -v curl >/dev/null 2>&1 || { echo "❌ 无法安装 curl, 请手动装: apt install curl"; exit 1; }
echo "  ✅ curl=$(curl --version 2>&1 | head -1 | awk '{print $3}')"

# python3
if ! command -v python3 >/dev/null 2>&1; then
    install_pkg python3
fi
command -v python3 >/dev/null 2>&1 || { echo "❌ 无法安装 python3"; exit 1; }

# python3-venv
if ! python3 -c "import venv" >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then install_pkg python3-venv; fi
fi

# ===== 1. 创建目录 =====
echo "[1/5] 准备目录 ($D)..."
mkdir -p "$D" 2>/dev/null || {
    echo "  /opt 无写权限, 尝试 sudo..."
    if command -v sudo >/dev/null 2>&1; then
        DEPLOY_DIR=/opt/mtscos sudo -E bash -c "mkdir -p /opt/mtscos && curl -sL http://192.168.31.203:8080/deploy.sh | bash"
        exit $?
    fi
    # 最后 fallback 到 home
    D=$HOME/mtscos
    echo "  自动改用: $D"
    mkdir -p "$D"
}
mkdir -p "$D/flask-app" "$D/.trae" \
         "$D/_runtime/databases/Database" \
         "$D/flask-app/engines" \
         "$D/flask-app/core" \
         "$D/flask-app/routes" \
         "$D/flask-app/ai_engines" \
         "$D/flask-app/templates" \
         "$D/flask-app/static" \
         "$D/flask-app/scripts" \
         "$D/flask-app/services" \
         "$D/flask-app/app" \
         "$D/flask-app/db" \
         "$D/flask-app/config" \
         "$D/flask-app/split_databases" \
         "$D/flask-app/tests" \
         "$D/flask-app/deploy" \
         "$D/flask-app/layout_ai"

cd "$D"

# ===== curl 递归下载函数 =====
# curl -r 没有 --recursive, 用 Python 脚本递归下载 (自带 curl)
curl_recursive() {
    local src="$1"        # http://host/path/
    local dest="$2"       # 本地目录
    shift 2
    local excludes=("$@") # 要排除的 dir 名称
    
    python3 - "$src" "$dest" "${excludes[@]}" <<'PYEOF'
import sys, os, urllib.request, urllib.parse, html, re

base_url = sys.argv[1].rstrip('/')
base_dir = sys.argv[2]
excludes = set(sys.argv[3:])

visited = set()

def fetch_dir(url, local_dir):
    url = url.rstrip('/') + '/'
    if url in visited: return
    visited.add(url)
    
    os.makedirs(local_dir, exist_ok=True)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MTSCOS-deploy/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                # 是文件
                filename = os.path.basename(url.rstrip('/'))
                if filename:
                    local_path = os.path.join(local_dir, filename)
                    if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
                        data = resp.read()
                        with open(local_path, 'wb') as f: f.write(data)
                        print(f'  📄 {url} → {local_path}')
                return
            # HTML 目录 listing — 解析 <a href="...">
            html_content = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f'  ⚠️  {url}: {e}')
        return
    
    # 从 HTML 提取链接
    links = re.findall(r'href="([^"]+)"', html_content)
    for link in links:
        if link.startswith('?') or link.startswith('/') or link.startswith('.'):
            continue
        if '..' in link: continue
        # URL decode
        link_decoded = urllib.parse.unquote(link)
        
        # 跳过已知排除项
        skip = False
        for ex in excludes:
            if link_decoded.startswith(ex) or link_decoded == ex or f'/{ex}/' in '/' + link_decoded:
                skip = True; break
        if skip: continue
        
        child_url = url + link
        child_local = os.path.join(local_dir, link_decoded.rstrip('/'))
        
        if link.endswith('/'):
            fetch_dir(child_url, child_local)
        else:
            # 文件
            if not os.path.exists(child_local) or os.path.getsize(child_local) == 0:
                try:
                    req2 = urllib.request.Request(child_url, headers={'User-Agent': 'MTSCOS-deploy/1.0'})
                    with urllib.request.urlopen(req2, timeout=120) as r2:
                        data = r2.read()
                        os.makedirs(os.path.dirname(child_local), exist_ok=True)
                        with open(child_local, 'wb') as f: f.write(data)
                except Exception as e:
                    print(f'  ⚠️  {child_url}: {e}')

fetch_dir(base_url, base_dir)
PYEOF
}

# ===== 2. 下载 flask-app (curl 递归, 排除大目录) =====
echo "[2/5] 下载 flask-app 源码 (排除 migrations/data/venv/logs/__pycache__)..."
curl_recursive "$S/flask-app/" "$D/flask-app" \
    "migrations" "data" "venv" "logs" "__pycache__" \
    "test_reports" ".git_disabled" ".scheduler_heartbeat" ".scheduler_pid"
echo "  ✅ 源码下载完成: $(find "$D/flask-app" -type f | wc -l) 个文件"

# ===== 3. 下载数据库 (curl 直接链, 支持断点续传) =====
echo "[3/5] 下载 mtscos.db..."
cd "$D/_runtime/databases/Database"
# 先看远端文件大小
REMOTE_SIZE=$(curl -sI "$S/_runtime/databases/Database/mtscos.db" 2>/dev/null | grep -i content-length | awk '{print $2}' | tr -d '\r\n')
REMOTE_MB=$(( REMOTE_SIZE / 1024 / 1024 ))
echo "  远端大小: ${REMOTE_MB}MB"

# 断点续传
if [ -f mtscos.db ]; then
    LOCAL_SIZE=$(stat -c%s mtscos.db 2>/dev/null || stat -f%z mtscos.db 2>/dev/null || echo 0)
    if [ "$LOCAL_SIZE" -lt "$REMOTE_SIZE" ]; then
        echo "  继续下载 (已下载 $((LOCAL_SIZE / 1024 / 1024))MB / ${REMOTE_MB}MB)..."
        curl -L -C - -o mtscos.db "$S/_runtime/databases/Database/mtscos.db"
    else
        echo "  已完整 (${REMOTE_MB}MB)"
    fi
else
    curl -L -o mtscos.db "$S/_runtime/databases/Database/mtscos.db"
fi
echo "  ✅ mtscos.db: $(ls -lh mtscos.db | awk '{print $5}')"

# ===== 4. .trae 规则 =====
echo "[4/5] 下载 .trae 规则..."
mkdir -p "$D/.trae"
curl_recursive "$S/.trae/rules/" "$D/.trae" "rules_backup" "rules_generated"
# 如果规则在 $D/.trae/rules/ 子目录里, 挪上来
if [ -d "$D/.trae/rules" ]; then
    mv "$D/.trae/rules/"*.md "$D/.trae/" 2>/dev/null || true
    rmdir "$D/.trae/rules" 2>/dev/null || true
fi
echo "  ✅ .trae 规则: $(find "$D/.trae" -name '*.md' | wc -l) 篇"

# ===== 5. 安装依赖 + 启动 =====
echo "[5/5] 安装 Python 依赖 + 启动 Flask..."
cd "$D/flask-app"

if ! [ -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip -q 2>/dev/null
pip install flask flask-cors flask-sqlalchemy sqlalchemy flask-login flask-bcrypt \
            pyyaml requests pillow 2>/dev/null | tail -1
if [ -f requirements.txt ]; then
    pip install -r requirements.txt 2>/dev/null | tail -1 || true
fi
echo "  ✅ venv + 依赖安装完成"

# 启动 (强制 host=0.0.0.0 — Linux 上 host='::' 只监听 IPv6, IPv4 不通!)
export MTSCOS_SKIP_EF_STARTUP_SCAN=1
nohup python3 -c "
import server_real_db as srd
srd.app.run(host='0.0.0.0', port=8888, threaded=True)
" > /tmp/mtscos.log 2>&1 &
SERVER_PID=$!
sleep 6

# 验证
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8888/ 2>/dev/null || echo '000')
echo ""
echo "════════════════════════════════════════════════"
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || hostname -s || echo "192.168.31.9")
    echo "🎉  部署成功! 服务已启动 (HTTP $HTTP_CODE)"
    echo ""
    echo "🌐  访问:   http://$HOST_IP:8888/"
    echo "📄  日志:   tail -f /tmp/mtscos.log"
    echo "🔧  PID:    $SERVER_PID"
    echo "🛑  停止:   kill $SERVER_PID"
else
    echo "⚠️   服务可能未启动 (HTTP $HTTP_CODE)"
    echo "📄  查看日志: tail -50 /tmp/mtscos.log"
    echo "🔧  手动启动: cd $D/flask-app && source venv/bin/activate && MTSCOS_SKIP_EF_STARTUP_SCAN=1 python3 server_real_db.py"
fi
echo "════════════════════════════════════════════════"