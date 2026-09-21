#!/bin/bash
# ════════════════════════════════════════════════════════════════
# MTSCOS AI Flask Launchd 守护化 · 一键安装
# ════════════════════════════════════════════════════════════════
# 解决 Flask "无声死亡" 问题 (nohup + & 被 SIGHUP 杀掉)
# 运行方式:
#   cd ~/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project
#   bash install_flask_launchd.sh
# ════════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$HOME/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
PLIST="$HOME/Library/LaunchAgents/com.mtscos.server8888.plist"
LAUNCHER="$PROJECT_ROOT/launch_mtscos_flask.sh"
LABEL="com.mtscos.server8888"
UID_GUID="gui/$(id -u)"

echo "═══════════════════════════════════════════"
echo "  MTSCOS Flask Launchd 守护化 一键安装"
echo "═══════════════════════════════════════════"

# 1. 杀掉可能残留的 Flask 进程
echo ""
echo "[1/5] 清理残留 Flask 进程..."
pkill -9 -f "python.*modular_start" 2>/dev/null || true
pkill -9 -f "python.*server_real_db" 2>/dev/null || true
sleep 2
echo "  ✅ 已清理"

# 2. launcher 脚本 + plist 就绪检查
echo ""
echo "[2/5] 检查 launcher + plist..."
[ -x "$LAUNCHER" ] && echo "  ✅ launcher 脚本 (可执行)" || { echo "  ❌ launcher 不存在"; exit 1; }
[ -f "$PLIST" ] && echo "  ✅ plist 文件存在" || { echo "  ❌ plist 不存在"; exit 1; }
plutil -lint "$PLIST" >/dev/null 2>&1 && echo "  ✅ plist XML 语法 OK" || { echo "  ❌ plist XML 错误"; exit 1; }

# 3. Ollama 健康 (launchd 已在守护 com.mtscos.ollama-native)
echo ""
echo "[3/5] Ollama 预检 (launchd 已托管)..."
for i in 1 2 3; do
    if curl -s --max-time 3 http://localhost:11435/api/tags >/dev/null 2>&1; then
        echo "  ✅ Ollama 11435 在线"
        break
    fi
    echo "  ⏳ 等 Ollama ($i/3)..."
    sleep 3
done

# 4. 卸载旧 plist (如果有) + 加载新的
echo ""
echo "[4/5] launchctl load..."
launchctl bootout "$UID_GUID" "$PLIST" 2>/dev/null || echo "  (bootout: 可能没加载过, 跳过)"
launchctl bootstrap "$UID_GUID" "$PLIST" || { echo "  ❌ bootstrap 失败"; exit 1; }
launchctl enable "$UID_GUID/$LABEL" 2>/dev/null || true
echo "  ✅ launchctl bootstrap 成功"

# 5. 等 Flask 启动 + HTTP 验证
echo ""
echo "[5/5] 等 Flask 启动 (最多 50s)..."
for i in $(seq 1 10); do
    sleep 5
    HTTP=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8888/ 2>/dev/null)
    echo "  [$((i*5))s] HTTP=$HTTP"
    [ "$HTTP" != "000" ] && break
done

# 最终状态
echo ""
echo "═══════════════════════════════════════════"
if [ "$HTTP" != "000" ]; then
    echo "  ✅ 安装完成! Flask 由 launchd 守护"
    echo "  - 开机用户登录后自动启动 (RunAtLoad)"
    echo "  - 崩溃自动重启 (KeepAlive, ThrottleInterval=10s)"
    echo "  - HTTP 8888 OK"
    echo "  - 查看状态: launchctl list | grep server8888"
    echo "  - 重启 Flask: launchctl kickstart -k $UID_GUID/$LABEL"
else
    echo "  ⚠️ Flask 没起来, 看日志:"
    echo "     tail -20 $PROJECT_ROOT/_runtime/logs/launchd_server8888.stderr.log"
fi
echo "═══════════════════════════════════════════"
