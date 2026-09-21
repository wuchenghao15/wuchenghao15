#!/usr/bin/env bash
set -euo pipefail

BOLD='\033[1m'; GREEN='\033[32m'; RED='\033[31m'; CYAN='\033[36m'; YEL='\033[33m'; NC='\033[0m'
say(){ echo -e "${BOLD}${CYAN}▸${NC} $*"; }
ok(){ echo -e "  ${GREEN}✓${NC} $*"; }
warn(){ echo -e "  ${YEL}⚠${NC} $*"; }
fail(){ echo -e "  ${RED}✗${NC} $*"; }

DEPLOY="${DEPLOY_DIR:-$HOME/mtscos}"
FLASK="$DEPLOY/flask-app"
SRC="${SRC_HOST:-192.168.31.203}"
PORT="${SRC_PORT:-8080}"
PKG="flask_app_essentials.tar.gz"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  MTSCOS Andromeda · 一键修复脚本              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 停 Flask ──
say "[1/7] 停止 Flask"
cd "$DEPLOY"
if [ -x ./mtscos.sh ]; then ./mtscos.sh stop 2>/dev/null || true; fi
pkill -f "server_real_db.*run" 2>/dev/null || true
sleep 2
ok "已停止"

# ── 下载资源包 ──
say "[2/7] 下载资源包 (templates+static+routes)"
curl -sL -C - "http://${SRC}:${PORT}/${PKG}" -o "$PKG"
if [ ! -s "$PKG" ]; then fail "下载失败 — ${SRC}:${PORT} 在线吗?"; exit 1; fi
ok "下载完成: $(ls -lh $PKG | awk '{print $5}')"

# ── 备份旧文件 ──
say "[3/7] 备份旧模板 → .bak"
TS=$(date +%Y%m%d%H%M%S)
if [ -d "$FLASK/templates" ]; then cp -R "$FLASK/templates" "$FLASK/templates.bak.$TS"; fi
ok "templates 已备份"

# ── 解压覆盖 ──
say "[4/7] 解压覆盖"
tar -xzf "$PKG" -C "$FLASK/"
find "$FLASK/" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$FLASK/" -name "*.pyc" -delete 2>/dev/null || true
ok "解压完成"

# ── 修复静态资源权限 ──
say "[5/7] 修复静态资源权限"
chmod -R u+rwX "$FLASK/static/" 2>/dev/null || true
chmod -R u+rwX "$FLASK/templates/" 2>/dev/null || true
chmod -R u+rwX "$FLASK/routes/" 2>/dev/null || true
ok "权限已修复"

# ── 诊断：关键文件在不在 ──
say "[6/7] 诊断关键文件"
DIAG_OK=true
for f in \
    "templates/index.html" \
    "static/assets/css/mtscos-design-system.css" \
    "static/assets/font-awesome/css/all.min.css" \
    "static/css/_theme_tokens_source.css" \
    "routes/__init__.py"; do
    if [ -f "$FLASK/$f" ]; then
        sz=$(wc -c < "$FLASK/$f")
        ok "$f ($sz bytes)"
    else
        fail "$f 缺失!"
        DIAG_OK=false
    fi
done
# index.html 里有没有仙女座（不是 fallback 极简白卡）
if grep -q "仙女座" "$FLASK/templates/index.html" 2>/dev/null; then
    ok "index.html 含仙女座内容 (不是 fallback)"
else
    fail "index.html 可能是 fallback 白卡!"
    DIAG_OK=false
fi

# ── 重启 Flask + 验证 ──
say "[7/7] 重启 Flask + 验证"
if [ -x ./mtscos.sh ]; then
    ./mtscos.sh restart
else
    cd "$FLASK"
    export MTSCOS_SKIP_EF_STARTUP_SCAN=1
    nohup python3 -c "import server_real_db as srd; srd.app.run(host='0.0.0.0', port=8888, threaded=True)" > /tmp/mtscos.log 2>&1 &
fi
sleep 10

echo ""
echo "════════════════════════════════════════════════"
echo "  等待 Flask 就绪..."
echo "════════════════════════════════════════════════"

# 等 Flask 起来
for i in 1 2 3 4 5 6 7 8 9 10; do
    CODE=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://127.0.0.1:8888/ 2>/dev/null || echo "000")
    if [ "$CODE" != "000" ]; then break; fi
    echo -n "  ."; sleep 2
done
echo ""

echo ""
echo "  ${BOLD}直连 Flask :8888${NC}"
C_INDEX=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8888/index 2>/dev/null || echo "000")
C_CSS=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8888/assets/css/mtscos-design-system.css 2>/dev/null || echo "000")
C_FA=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8888/assets/font-awesome/css/all.min.css 2>/dev/null || echo "000")
C_TOK=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8888/static/css/_theme_tokens_source.css 2>/dev/null || echo "000")
C_APACHE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ 2>/dev/null || echo "000")

printf "  /index:                          HTTP %s %s\n" "$C_INDEX"   $([ "$C_INDEX" = "200" ] && echo "✅" || [ "$C_INDEX" = "302" ] && echo "✅" || echo "❌")
printf "  /assets/css/mtscos-design-system: HTTP %s %s\n" "$C_CSS"     $([ "$C_CSS" = "200" ] && echo "✅" || echo "❌")
printf "  /assets/font-awesome/all.min:     HTTP %s %s\n" "$C_FA"      $([ "$C_FA" = "200" ] && echo "✅" || echo "❌")
printf "  /static/css/_theme_tokens_source: HTTP %s %s\n" "$C_TOK"     $([ "$C_TOK" = "200" ] && echo "✅" || echo "❌")
printf "  Apache :80 /:                    HTTP %s %s\n" "$C_APACHE"  $([ "$C_APACHE" = "200" ] || [ "$C_APACHE" = "302" ] && echo "✅" || echo "❌")

# 如果 /index 是 200/302 但 body 有 fallback 标记
if [ "$C_INDEX" = "200" ] || [ "$C_INDEX" = "302" ]; then
    BODY_HAS_FALLBACK=$(curl -s http://127.0.0.1:8888/index 2>/dev/null | grep -c "前往登录页.*font-family:sans-serif" || echo "0")
    if [ "$BODY_HAS_FALLBACK" -gt 0 ]; then
        warn "⚠ 模板渲染走了 except fallback！极简白卡。"
        echo "  → 看日志: tail -50 /tmp/mtscos.log | grep -i error"
    else
        ok "模板渲染成功 (仙女座页面, 不是 fallback)"
    fi
fi

LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "192.168.31.9")
echo ""
echo "════════════════════════════════════════════════"
echo -e "  ${BOLD}🌐  访问地址:${NC}"
echo "    http://${LAN_IP}/            (Apache 反代)"
echo "    http://${LAN_IP}:8888/       (直连 Flask)"
echo "════════════════════════════════════════════════"
