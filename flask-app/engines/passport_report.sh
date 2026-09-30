#!/bin/bash
# ══════════════════════════════════════════════════════════════
# 仙女座 → AI Passport 一键反馈脚本
# ══════════════════════════════════════════════════════════════
# 用法:
#   ./passport_report.sh              # 自动收集仙女座状态 → 推送
#   ./passport_report.sh "升级完成!"  # 推送一条自定义消息
#   ./passport_report.sh broker       # 只启动 MQTT Broker
#   ./passport_report.sh status       # 查设备 + Broker 状态
#   ./passport_report.sh volume 80    # 调设备音量
#   ./passport_report.sh reboot       # 重启设备
# ══════════════════════════════════════════════════════════════

set -e
cd "$(dirname "$0")"

ACTION="${1:-report}"
MSG="${2:-}"

echo "📡 仙女座 → AI Passport 反馈"
echo "═══════════════════════════════"

# ── 确保 MQTT Broker 跑着 ──
ensure_broker() {
    if lsof -i :1883 -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; then
        echo "  ✅ MQTT Broker 运行中 (*:1883)"
    else
        echo "  ▶️  启动 MQTT Broker..."
        pkill -f mqtt_broker 2>/dev/null || true
        nohup python3 mqtt_broker.py > /tmp/mqtt_broker.log 2>&1 &
        sleep 2
        if lsof -i :1883 -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; then
            echo "  ✅ Broker 已启动 (PID=$!)"
        else
            echo "  ❌ Broker 启动失败!"; exit 1
        fi
    fi
}

# ── 查 USB 设备 ──
check_usb() {
    local PORT
    PORT=$(ls /dev/cu.usbmodem* 2>/dev/null | head -1 || echo "")
    if [ -n "$PORT" ]; then
        echo "  ✅ USB 设备: $PORT"
        echo "  $(python3 -c "
import serial, time
s=serial.Serial('$PORT',115200,timeout=2); time.sleep(1)
s.write(b'AT+CONFIG=?\r\n'); time.sleep(1)
r=s.read(1024).decode(errors='replace').strip(); s.close()
print(r[:200])
" 2>/dev/null)"
    else
        echo "  ❌ 未检测到 USB 设备 → 检查 USB 线 + 通电"
    fi
}

case "$ACTION" in
    broker)
        ensure_broker
        echo "✅ Broker 就绪, Ctrl+C 退出"
        wait
        ;;
    status)
        echo ""
        echo "📋 系统状态"
        echo "──────────"
        ensure_broker
        check_usb
        echo ""
        echo "  📊 仙女座引擎: $(python3 -c "import sqlite3; db=sqlite3.connect('database/app.db'); print(f\"daemon={db.execute(\\\"SELECT COUNT(*) FROM mt_daemon_registry\\\").fetchone()[0]} AI员工={db.execute(\\\"SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE employee_source NOT IN ('eigenflux','arduino_employees.py')\\\").fetchone()[0]}\"); db.close()" 2>/dev/null)"
        ;;
    report)
        ensure_broker
        echo ""
        echo "📤 推送仙女座自动报告..."
        python3 ai_passport_feedback.py andromeda 2>&1 | grep -v Deprecation | grep -v paho | tail -15
        ;;
    feedback)
        ensure_broker
        if [ -z "$MSG" ]; then echo "请传消息: ./passport_report.sh feedback 'xxx'"; exit 1; fi
        echo ""
        echo "📤 推送自定义消息: $MSG"
        python3 ai_passport_feedback.py feedback "$MSG" 2>&1 | grep -v Deprecation | grep -v paho | tail -10
        ;;
    volume)
        check_usb
        if [ -z "$MSG" ]; then MSG=50; fi
        echo ""
        echo "🔊 设音量 $MSG"
        python3 ai_passport_feedback.py volume "$MSG" 2>&1 | tail -5
        ;;
    reboot)
        check_usb
        echo ""
        echo "🔄 重启设备..."
        python3 ai_passport_feedback.py reboot 2>&1 | tail -5
        ;;
    *)
        echo "未知操作: $ACTION"
        echo "用法: passport_report.sh [broker|status|report|feedback 'msg'|volume N|reboot]"
        exit 1
        ;;
esac

echo ""
echo "✅ 完成"
