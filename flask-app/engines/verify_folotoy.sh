#!/bin/bash
# ══════════════════════════════════════════════════════════════
# FoloToy AI Passport 配网后验证脚本
# ══════════════════════════════════════════════════════════════
# 用法: bash verify_folotoy.sh
# 三个维度: WiFi 上线 · MQTT 连 Broker · 消息可收发
# ══════════════════════════════════════════════════════════════

cd "$(dirname "$0")"

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║  🎯 FoloToy AI Passport 配网后验证              ║"
echo "╚═══════════════════════════════════════════════╝"

MY_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "192.168.11.192")

# ══════════════════════════════════════════════════════════════
# 维度 1: Broker 存活
# ══════════════════════════════════════════════════════════════
echo ""
echo "【1/3】MQTT Broker 状态"
echo "───────────────────────────────────"
if lsof -i :1883 -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; then
  BROKER_PID=$(lsof -i :1883 -sTCP:LISTEN -t 2>/dev/null | head -1)
  echo "  ✅ Broker 运行中 (PID=$BROKER_PID, $MY_IP:1883)"
else
  echo "  ❌ Broker 没跑 — 启动..."
  nohup python3 mqtt_broker.py > /tmp/mqtt_v2.log 2>&1 &
  sleep 2
  if lsof -i :1883 -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; then
    echo "  ✅ Broker 已启动 (PID=$!)"
  else
    echo "  ❌ 启动失败!"; exit 1
  fi
fi

# ══════════════════════════════════════════════════════════════
# 维度 2: 设备 WiFi 上线 (ARP 里找 ESP32)
# ══════════════════════════════════════════════════════════════
echo ""
echo "【2/3】设备 WiFi 上线? (扫描 ARP)"
echo "───────────────────────────────────"

ESP32_FOUND=""
for ip in $(seq 2 254); do
  (ping -c 1 -W 0.3 192.168.11.$ip >/dev/null 2>&1 &)
done 2>/dev/null
wait
sleep 1

FOUND=$(arp -a 2>/dev/null | grep -v incomplete | grep -v "192.168.11.192" | grep -v "192.168.11.1 ")

if [ -z "$FOUND" ]; then
  echo "  ❌ ARP 里没有在线设备 — 设备 WiFi 没连上"
  echo "     → 检查: 是 2.4GHz 不是 5GHz?"
  echo "     → 路由器 DHCP 开了吗?"
else
  echo "  在线设备 (非 Mac 自己)："
  ESP32_OUIS="24:6F:28 3C:71:BF 40:F5:20 54:43:B2 80:7D:3A 84:0D:8E 84:CC:A8 88:19:A6 94:B5:55 A4:CF:12 A8:42:A1 AC:67:B2 B4:E6:2D C4:4F:33 E8:9F:6D EC:DA:3B F4:CF:A2 70:03:9F 24:0A:C4"
  echo "$FOUND" | while read line; do
    ip=$(echo "$line" | awk '{print $2}' | tr -d '()')
    mac=$(echo "$line" | awk '{print $4}')
    mac_up=$(echo "$mac" | tr 'a-f' 'A-F')
    found_esp32=""
    for oui in $ESP32_OUIS; do
      if echo "$mac_up" | grep -qi "${oui//:/}"; then
        found_esp32="🎯🎯🎯"
        break
      fi
    done
    echo "    $found_esp32 $ip  $mac"
    if [ -n "$found_esp32" ]; then
      ESP32_FOUND="$ip"
    fi
  done
  
  if [ -n "$ESP32_FOUND" ]; then
    echo ""
    echo "  🎯 找到 ESP32/FoloToy: $ESP32_FOUND"
    echo "     下一步: 让它连 Broker..."
  else
    echo ""
    echo "  ⚠️  没找到 ESP32 MAC — 设备可能还没上 WiFi"
    echo "     按一下设备的唤醒键, 等 30 秒再试"
  fi
fi

# ══════════════════════════════════════════════════════════════
# 维度 3: Broker 连接日志 (关键!)
# ══════════════════════════════════════════════════════════════
echo ""
echo "【3/3】Broker 收到设备连接? (实时监听 10s)"
echo "───────────────────────────────────"

BROKER_LOG=/tmp/mqtt_v2.log
cp "$BROKER_LOG" "${BROKER_LOG}.before" 2>/dev/null
CONN_BEFORE=$(grep -c "🟢 NEW" "${BROKER_LOG}.before" 2>/dev/null || echo 0)

echo "  等 10s 让设备尝试连 Broker..."
sleep 10

CONN_AFTER=$(grep -c "🟢 NEW" "$BROKER_LOG" 2>/dev/null || echo 0)
DIFF=$((CONN_AFTER - CONN_BEFORE))

if [ "$DIFF" -gt 0 ]; then
  echo ""
  echo "  🎉🎉🎉 成功! Broker 收到 $DIFF 个新连接!"
  echo "  日志尾部:"
  tail -20 "$BROKER_LOG" | grep -E "🟢|🔗|📥|📤|🔴"
else
  echo "  ❌ 10s 内没有新设备连 Broker"
  echo ""
  echo "  检查清单:"
  echo "    ✅ 设备和 MacBook 在同一个 WiFi?"
  echo "    ✅ App 里 Broker Host 填的是 $MY_IP ?"
  echo "    ✅ Broker Port 填的是 1883 ?"
  echo "    ✅ 设备重连/重启过了吗?"
  echo ""
  echo "  当前 Broker 全部连接:"
  tail -30 "$BROKER_LOG" | head -20
fi

# ══════════════════════════════════════════════════════════════
# 如果上面都通了 → 推一条测试消息
# ══════════════════════════════════════════════════════════════
if [ "$DIFF" -gt 0 ]; then
  echo ""
  echo "════════════════════════════════════════"
  echo "🚀 推一条仙女座报告测试..."
  echo "════════════════════════════════════════"
  timeout 15 python3 ai_passport_feedback.py feedback \
    "仙女座→AI Passport 全链路打通! 配置网成功, 语音应该响了!" 2>&1 | tail -5
  echo ""
  echo "✅ 完成! 去听设备有没有说话 📢"
fi
