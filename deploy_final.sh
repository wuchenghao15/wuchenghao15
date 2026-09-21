#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║  MTSCOS AI v23.0.0-Andromeda-Nova 一键部署              ║
# ║  目标: 192.168.31.9 (Linux)                            ║
# ║  源:  http://192.168.31.203:8080/ (本机 macOS HTTP)    ║
# ╚══════════════════════════════════════════════════════════╝
set -e

D=${DEPLOY_DIR:-/opt/mtscos}
S=http://192.168.31.203:8080

echo ""
echo "📦 MTSCOS AI v23.0.0-Andromeda-Nova 部署"
echo "════════════════════════════════════════════════"
echo "部署目录: $D"
echo "下载源:   $S"
echo ""

# ===== 1. 检查依赖 =====
echo "[0/5] 检查依赖..."
command -v python3 >/dev/null 2>&1 || { echo "❌ 需要 python3"; exit 1; }
command -v wget >/dev/null 2>&1 || { echo "❌ 需要 wget: apt install wget"; exit 1; }
echo "  ✅ python3=$(python3 --version 2>&1 | awk '{print $2}') wget=$(wget --version 2>&1 | head -1 | awk '{print $3}')"

# ===== 2. 创建目录 =====
echo "[1/5] 准备目录..."
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
         "$D/flask-app/test_reports" \
         "$D/flask-app/deploy"

cd "$D"

# ===== 3. 下载 flask-app (递归 wget, 排除大目录) =====
echo "[2/5] 下载 flask-app 源码 (排除 migrations/data/venv/logs/__pycache__)..."
cd "$D/flask-app"
# 用 wget 递归, 排除大目录
wget -q \
  --recursive --no-parent --level=inf \
  --reject "*migrations*,*data*,*venv*,*logs*,*__pycache__,*.pyc,*.pyo" \
  --exclude-directories=migrations,data,venv,logs,__pycache__ \
  -nd --no-host-directories --cut-dirs=1 \
  -N \
  "$S/flask-app/" 2>&1 | tail -5
echo "  ✅ 源码下载完成: $(find . -type f | wc -l) 个文件"

# ===== 4. 下载数据库 =====
echo "[3/5] 下载 mtscos.db (5GB+)..."
cd "$D/_runtime/databases/Database"
wget -q --show-progress -c "$S/_runtime/databases/Database/mtscos.db"
echo "  ✅ mtscos.db: $(ls -lh mtscos.db | awk '{print $5}')"

# ===== 5. .trae 规则 =====
echo "[4/5] 下载 .trae 规则..."
cd "$D/.trae"
wget -q -r -np -nd --exclude-directories=rules_backup -A "*.md" "$S/.trae/rules/" 2>/dev/null || true
# 重命名: wget 下载的文件名可能带前缀
ls rules_backup 2>/dev/null && rm -rf rules_backup
# 修复目录结构 (wget 可能生成 rules/ 子目录)
if [ -d rules ]; then mv rules rules.trae; mv rules.trae/* . 2>/dev/null; rmdir rules.trae; fi 2>/dev/null
echo "  ✅ .trae 规则: $(find . -name '*.md' | wc -l) 篇"

# ===== 6. 安装依赖 + 启动 =====
echo "[5/5] 安装 Python 依赖 + 启动 Flask..."
cd "$D/flask-app"
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip -q 2>/dev/null
pip install flask flask-cors flask-sqlalchemy sqlalchemy flask-login flask-bcrypt \
            pyyaml requests pillow 2>/dev/null | tail -1
if [ -f requirements.txt ]; then
    pip install -r requirements.txt 2>/dev/null | tail -1 || true
fi
echo "  ✅ venv + 依赖安装完成"

# 启动
export MTSCOS_SKIP_EF_STARTUP_SCAN=1
nohup python3 server_real_db.py > /tmp/mtscos.log 2>&1 &
SERVER_PID=$!
sleep 5

# 验证
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8888/ 2>/dev/null || echo '000')
echo ""
echo "════════════════════════════════════════════════"
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "192.168.31.9")
    echo "🎉  部署成功! 服务已启动"
    echo ""
    echo "🌐  访问:   http://$HOST_IP:8888/"
    echo "📄  日志:   tail -f /tmp/mtscos.log"
    echo "🔧  PID:    $SERVER_PID"
    echo "🛑  停止:   kill $SERVER_PID"
else
    echo "⚠️   服务可能未启动成功 (HTTP $HTTP_CODE)"
    echo "📄  查看日志: tail -50 /tmp/mtscos.log"
    echo "🔧  手动启动: cd $D/flask-app && source venv/bin/activate && MTSCOS_SKIP_EF_STARTUP_SCAN=1 python3 server_real_db.py"
fi
echo "════════════════════════════════════════════════"
