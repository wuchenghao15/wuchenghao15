#!/usr/bin/env python3
"""
仙女座 → AI Passport 反馈引擎 (BLE 主通道版)
================================================

双通道架构 (重构后):
  1. BLE GATT   — 主通道 (扫描/连接/发送命令/蜂鸣/文本/音频通道预留)
                  → folotoy_bridge.py
  2. USB AT     — 辅通道 (volume / reboot / CONFIG 硬控)
                  → pyserial + AT 命令
  3. MQTT       — 保留给未来云连接 (FoloToy WiFi 联网推送)

硬件 (已发现):
  · BLE Service: 54524145-4341-5244-0000-000000000000 ("TRAECARD")
  · USB /dev/cu.usbmodem101 @ 115200 (ESP32-C3, fallback)
  · FoloToy fw=trae_card v1.0.0, audio=ES8311

用法 (保持原 CLI 兼容 + 新增 BLE action):
  python3 ai_passport_feedback.py scan           # 扫描 BLE + USB
  python3 ai_passport_feedback.py ble-status     # BLE 读 0x12/0x13
  python3 ai_passport_feedback.py beep           # BLE 蜂鸣
  python3 ai_passport_feedback.py feedback "xxx" # BLE 推文本 + 蜂鸣
  python3 ai_passport_feedback.py andromeda       # 自动收集 + BLE 推送
  python3 ai_passport_feedback.py status          # USB 读 CONFIG
  python3 ai_passport_feedback.py volume 80       # USB 调音量
  python3 ai_passport_feedback.py reboot          # USB 重启
"""
from __future__ import annotations
import json, os, sys, time, argparse, threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ═══════════════════════════════════════════════════════════
# USB AT 辅通道 (保留原实现, volume/reboot 硬控还得靠这个)
# ═══════════════════════════════════════════════════════════
USB_BAUD = 115200
USB_PORTS = [
    "/dev/cu.usbmodem101",
    "/dev/cu.usbserial-14210",
    "/dev/cu.SLAB_USBtoUART",
    "/dev/cu.usbserial",
    "/dev/tty.usbmodem101",
]

# MQTT — 保留, 未来云连接用
MQTT_BROKER = os.environ.get("PASSPORT_MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.environ.get("PASSPORT_MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("PASSPORT_MQTT_TOPIC", "folotoy/command")


def find_usb_port() -> str | None:
    """扫描 /dev/cu.* 找 FoloToy 设备"""
    try:
        import serial
    except ImportError:
        return None
    for p in USB_PORTS:
        if Path(p).exists():
            try:
                s = serial.Serial(p, USB_BAUD, timeout=2)
                time.sleep(0.5)
                s.reset_input_buffer()
                s.write(b'AT+CONFIG=?\r\n')
                time.sleep(1)
                resp = s.read(2048).decode(errors="replace")
                s.close()
                if "CONFIG:" in resp or "sn=" in resp or "FoloToy" in resp:
                    return p
            except Exception:
                continue
    import glob
    for p in sorted(glob.glob("/dev/cu.usb*")):
        try:
            s = serial.Serial(p, USB_BAUD, timeout=2)
            time.sleep(0.5)
            s.reset_input_buffer()
            s.write(b'AT\r\n')
            time.sleep(1)
            resp = s.read(1024).decode(errors="replace")
            s.close()
            if "+ERR" in resp or "+OK" in resp or "CONFIG:" in resp:
                return p
        except Exception:
            continue
    return None


def usb_at(cmd: str, timeout: float = 2.5) -> str:
    """发一条 AT 命令, 返回响应"""
    try:
        import serial
    except ImportError:
        return "[USB] pyserial 未装, pip3 install pyserial --break-system-packages"

    port = find_usb_port() or os.environ.get("PASSPORT_USB_PORT")
    if not port or not Path(port).exists():
        return "[USB] 未找到 AI Passport 设备 (USB)"

    try:
        s = serial.Serial(port, USB_BAUD, timeout=timeout)
        time.sleep(0.8)
        s.reset_input_buffer()
        boot = s.read(2048).decode(errors="replace")
        s.reset_input_buffer()

        full_cmd = cmd.encode() + b'\r\n'
        s.write(full_cmd)
        time.sleep(timeout)
        resp = s.read(4096).decode(errors="replace")
        s.close()

        lines = [l for l in resp.split('\n') if l.strip()
                 and not l.startswith('I (') and not l.startswith('Build:')
                 and not l.startswith('ESP-ROM:') and not l.startswith('rst:')
                 and not l.startswith('boot:') and not l.startswith('SPIWP:')]
        return '\n'.join(lines).strip() or "(no response)"
    except Exception as e:
        return f"[USB Error] {type(e).__name__}: {e}"


# ═══════════════════════════════════════════════════════════
# MQTT 通道 (保留, 未来云连接)
# ═══════════════════════════════════════════════════════════
def mqtt_publish(topic: str, payload: str | dict) -> bool:
    try:
        import paho.mqtt.publish as mqtt_pub
    except ImportError:
        return False
    if isinstance(payload, dict):
        payload = json.dumps(payload, ensure_ascii=False)
    try:
        mqtt_pub.single(topic, payload, hostname=MQTT_BROKER, port=MQTT_PORT, keepalive=5)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# BLE 主通道 (通过 folotoy_bridge)
# ═══════════════════════════════════════════════════════════
def _ble_available() -> bool:
    try:
        import folotoy_bridge
        return True
    except ImportError:
        return False


def ble_scan(timeout: float = 8.0) -> list[dict]:
    import folotoy_bridge
    return folotoy_bridge.ble_scan_sync(timeout)


def ble_status() -> dict:
    import folotoy_bridge
    return folotoy_bridge.ble_status_sync()


def ble_beep(pattern: str = "report_ok") -> dict:
    import folotoy_bridge
    return folotoy_bridge.ble_send_command_sync(pattern)


def ble_send_text(text: str) -> dict:
    import folotoy_bridge
    async def _do():
        if not folotoy_bridge._ble_client or not folotoy_bridge._ble_client.is_connected:
            await folotoy_bridge.connect()
        return await folotoy_bridge.send_text(text)
    return folotoy_bridge.run_sync(_do())


def ble_report(message: str | None = None) -> dict:
    import folotoy_bridge
    return folotoy_bridge.ble_report_sync(message)


# ═══════════════════════════════════════════════════════════
# 仙女座报告收集 (复用逻辑)
# ═══════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "app.db"


def collect_andromeda_report() -> dict:
    import sqlite3
    info = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "items": []}
    if not DB_PATH.exists():
        info["db"] = "not found"
        return info
    db = sqlite3.connect(str(DB_PATH))
    try:
        try:
            rows = db.execute(
                "SELECT process_name, status FROM mt_daemon_registry WHERE status='RUNNING' ORDER BY process_name"
            ).fetchall()
            info["daemon_running"] = len(rows)
            info["daemon_total"] = db.execute("SELECT COUNT(*) FROM mt_daemon_registry").fetchone()[0]
        except Exception: pass
        try:
            rows = db.execute(
                "SELECT rule_id, to_version, change_type, created_at FROM mt_rule_changelog ORDER BY created_at DESC LIMIT 3"
            ).fetchall()
            info["rule_changes"] = [f"{r[0]}→{r[1]} {r[2]}" for r in rows]
        except Exception: pass
        try:
            info["ai_employees_andromeda"] = db.execute(
                "SELECT COUNT(*) FROM mt_andromeda_employee_registry "
                "WHERE employee_source NOT IN ('eigenflux','arduino_employees.py')"
            ).fetchone()[0]
        except Exception: pass
    finally:
        db.close()
    return info


def format_feedback(report: dict, subsystem: str | None = None) -> str:
    lines = [f"仙女座报告 {report['time']}"]
    if report.get("daemon_running") is not None:
        lines.append(f"运行中 {report['daemon_running']}/{report.get('daemon_total','?')}")
    if report.get("ai_employees_andromeda"):
        lines.append(f"AI员工 {report['ai_employees_andromeda']}")
    if report.get("rule_changes"):
        lines.append(f"规则变更: {', '.join(report['rule_changes'][:2])}")
    if subsystem:
        lines.append(f"{subsystem} 升级完成")
    return " | ".join(lines)


# ═══════════════════════════════════════════════════════════
# 主入口 — PassportFeedback (重构后 BLE-first)
# ═══════════════════════════════════════════════════════════
class PassportFeedback:
    def __init__(self):
        self._ble_ok = _ble_available()
        self._mqtt_ok = False
        try:
            import paho.mqtt.client as mqtt
            ok = False
            def on_connect(c, ud, fl, rc, prop=None):
                nonlocal ok
                ok = (rc == 0); c.disconnect()
            c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            c.on_connect = on_connect
            c.connect(MQTT_BROKER, MQTT_PORT, 5)
            c.loop_start(); time.sleep(1.5); c.loop_stop()
            self._mqtt_ok = ok
        except Exception:
            pass

        print(f"\n📡 AI Passport 反馈引擎 (BLE 主通道)")
        print(f"   BLE  桥接: {'✅ folotoy_bridge 可用' if self._ble_ok else '⚠️  不可用 (pip3 install bleak --break-system-packages)'}")
        print(f"   MQTT:   {'✅ 可达' if self._mqtt_ok else '❌ 不可达 (保留备用)'}")

    # ── 扫描 (BLE + USB) ──
    def scan(self) -> dict:
        info: dict = {}
        print(f"\n🔍 扫描设备...")
        # BLE
        if self._ble_ok:
            try:
                hits = ble_scan(timeout=6.0)
                info["ble"] = hits
            except Exception as e:
                info["ble_error"] = str(e)
                print(f"   BLE 扫描失败: {e}")
        # USB
        port = find_usb_port()
        info["usb_port"] = port
        if port:
            cfg = usb_at("AT+CONFIG=?")
            info["usb_config"] = cfg
        return info

    # ── BLE 状态 ──
    def ble_status(self) -> dict:
        if not self._ble_ok:
            print("⚠️  BLE 桥接不可用")
            return {"error": "ble not available"}
        res = ble_status()
        print(f"\n📋 BLE 设备身份 (0x12):")
        for k, v in res.get("identity", {}).items():
            print(f"   {k}: {v}")
        print(f"\n📋 BLE 运行状态 (0x13):")
        for k, v in res.get("state", {}).items():
            print(f"   {k}: {v}")
        return res

    # ── USB 状态 (保留原 action 兼容) ──
    def status(self) -> str:
        cfg = usb_at("AT+CONFIG=?")
        cmd = usb_at("AT+COMMAND=?")
        print(f"\n📋 USB CONFIG: {cfg}")
        print(f"📋 USB COMMANDS: {cmd}")
        return cfg

    # ── USB 音量 ──
    def volume(self, level: int):
        level = max(0, min(100, level))
        resp = usb_at(f"AT+CONFIG=common,volume,{level}")
        print(f"🔊 USB 音量 → {level} → {resp}")

    # ── USB 重启 ──
    def reboot(self):
        resp = usb_at("AT+REBOOT")
        print(f"🔄 USB 重启 → {resp}")

    # ── 蜂鸣 (BLE) ──
    def beep(self, pattern: str = "report_ok"):
        if not self._ble_ok:
            print("⚠️  BLE 桥接不可用")
            return
        res = ble_beep(pattern)
        print(f"🔔 BLE {pattern}: ok={res.get('ok')} ack={res.get('ack_desc', res.get('ack'))}")
        return res

    # ── 推送反馈 (BLE 为主, 一次连接完成蜂鸣+文本) ──
    def feedback(self, message: str, via: str = "auto"):
        print(f"\n📤 推送: {message[:100]}")
        pushed = False

        # BLE 主通道 — 一次连接搞定蜂鸣 + 文本 (避免跨 event loop 问题)
        if via in ("auto", "ble") and self._ble_ok:
            import folotoy_bridge as fb
            async def _ble_flow():
                await fb.connect()
                beep_res = await fb.send_command("report_ok")
                text_res = await fb.send_text(message)
                await fb.disconnect()
                return beep_res, text_res
            try:
                import asyncio
                beep_res, text_res = asyncio.run(_ble_flow())
                pushed = beep_res.get("ok") or text_res.get("ok")
                print(f"   [BLE] 蜂鸣={'✅' if beep_res.get('ok') else '⚠️'}  文本={'✅' if text_res.get('ok') else '⚠️'}")
                print(f"          ack={beep_res.get('ack_desc', beep_res.get('ack'))}")
            except Exception as e:
                print(f"   [BLE] 推送失败: {e}")

        # USB 辅通道 — 设备离线兜底
        if via in ("auto", "usb") and not pushed:
            port = find_usb_port()
            if port:
                cfg = usb_at("AT+CONFIG=?")
                print(f"   [USB] 设备在线 ({port}) cfg={cfg[:100]}")
                pushed = True

        # MQTT 备用
        if via in ("auto", "mqtt") and self._mqtt_ok and not pushed:
            payload = json.dumps({
                "type": "feedback", "from": "仙女座",
                "time": datetime.now().isoformat(), "message": message,
            }, ensure_ascii=False)
            if mqtt_publish(MQTT_TOPIC, payload):
                pushed = True
                print(f"   [MQTT] ✅ 已发布")

        if not pushed:
            print("   ⚠️  所有通道都没推送成功 — 设备可能离线")
        return pushed

    # ── 仙女座自动报告 ──
    def andromeda_report(self):
        print("\n📊 收集仙女座最新状态...")
        report = collect_andromeda_report()
        msg = format_feedback(report)
        print(f"\n📋 报告: {msg}")
        self.feedback(msg)
        return report


def main():
    ap = argparse.ArgumentParser(description="📡 AI Passport 反馈引擎 (BLE 主通道)")
    ap.add_argument("action", nargs="?", default="scan",
                    choices=["scan", "ble-status", "status", "feedback", "andromeda",
                             "beep", "beep-long", "beep-sos", "beep-chime",
                             "volume", "reboot"])
    ap.add_argument("message", nargs="?", help="feedback 消息 / volume 音量值")
    ap.add_argument("--via", choices=["ble", "usb", "mqtt", "auto"], default="auto")
    args = ap.parse_args()

    f = PassportFeedback()

    if args.action == "scan":
        f.scan()
    elif args.action == "ble-status":
        f.ble_status()
    elif args.action == "status":
        f.status()
    elif args.action == "feedback":
        if not args.message:
            print("请提供消息: feedback '你好'")
        else:
            f.feedback(args.message, via=args.via)
    elif args.action == "andromeda":
        f.andromeda_report()
    elif args.action == "beep":
        f.beep("report_ok")
    elif args.action == "beep-long":
        f.beep("beep_long")
    elif args.action == "beep-sos":
        f.beep("beep_sos")
    elif args.action == "beep-chime":
        f.beep("beep_chime")
    elif args.action == "volume":
        try:
            f.volume(int(args.message or 50))
        except ValueError:
            print("音量应该是数字 0-100")
    elif args.action == "reboot":
        f.reboot()


if __name__ == "__main__":
    main()
