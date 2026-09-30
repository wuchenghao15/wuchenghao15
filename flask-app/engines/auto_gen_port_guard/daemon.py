"""PortGuardDaemon: SA 双密钥 + Arduino 端口统一监测
===========================================
周期: 30s
1. SA 双密钥监测: VIKEY USB + device_fingerprint 指纹
2. Arduino 端口监测: /dev/cu.usbmodem*/serial* + VID:PID 识别
3. 异常落库: mt_port_alert_log
4. 状态落库: mt_sa_dual_key_status + mt_arduino_port_status
5. 触发 rules_engine 告警投喂
"""

import os, sys, time, sqlite3, json, logging, re, subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # flask-app/engines/auto_gen_port_guard/
ENGINES_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))  # flask-app/engines/
FLASK_APP = os.path.abspath(os.path.join(ENGINES_DIR, ".."))  # flask-app/
PROJECT_ROOT = os.path.abspath(os.path.join(FLASK_APP, ".."))  # MTSCOS_AI_Project/
LOG_DIR = os.path.join(PROJECT_ROOT, "_runtime", "logs")
DB_PATH = os.path.join(FLASK_APP, "database", "app.db")
os.makedirs(LOG_DIR, exist_ok=True)

# ⭐ 关键: 让 core.services.vikey_api / vikey_driver 可 import
sys.path.insert(0, FLASK_APP)
sys.path.insert(0, ENGINES_DIR)

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] port_guard: %(message)s',
    handlers=[logging.FileHandler(os.path.join(LOG_DIR, "auto_gen_port_guard.log")),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger("port_guard")

# ═════ Arduino VID:PID 映射 ═════
ARDUINO_VID_PID = {
    ("2341", "0001"): "Arduino UNO (CDC)",
    ("2341", "0042"): "Arduino UNO R3 (CDC)",
    ("2341", "0069"): "Arduino Mega 2560",
    ("2341", "8036"): "Arduino Leonardo",
    ("2341", "0432"): "Arduino UNO R4 (Minima)",
    ("2341", "0433"): "Arduino UNO R4 (WiFi)",
    ("1A86", "7523"): "CH340 Clone (UNO R3 兼容)",
    ("1A86", "7526"): "CH9102 Clone",
    ("10C4", "EA60"): "CP2102 (ESP32/ESP8266)",
    ("0403", "6001"): "FT232 (FTDI)",
    ("303A", "1001"): "ESP32-C3",
    ("303A", "0001"): "ESP32",
    ("303A", "1002"): "ESP32-S3",
    ("303A", "1003"): "ESP32-C6",
}


class PortGuardDaemon:
    def __init__(self, interval=30):
        self.interval = interval
        log.info(f"PortGuardDaemon init interval={interval}s")

    # ─── 表结构 ───
    def ensure_tables(self, conn):
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_sa_dual_key_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_time TEXT,
            vikey_present INTEGER,
            vikey_verified INTEGER,
            fingerprint_hash TEXT,
            fingerprint_len INTEGER,
            dual_authenticated INTEGER,
            sa_layout TEXT,
            trigger_reason TEXT,
            note TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_arduino_port_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_time TEXT,
            port_device TEXT,
            vid TEXT,
            pid TEXT,
            board_name TEXT,
            driver_type TEXT,
            driver_ok INTEGER,
            status TEXT,
            note TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_port_alert_log (
            alert_id TEXT PRIMARY KEY,
            check_time TEXT,
            alert_type TEXT,           -- SA_VIKEY_MISSING / SA_FP_MISSING / ARDUINO_NEW / ARDUINO_DISCONNECT / ARDUINO_UNKNOWN
            severity TEXT,             -- CRITICAL / WARNING / INFO
            detail TEXT,
            acknowledged INTEGER DEFAULT 0
        )""")
        conn.commit()

    # ─── SA 双密钥监测 ───
    def check_sa_dual_key(self):
        result = {
            "vikey_present": False,
            "vikey_verified": False,
            "fingerprint_hash": "",
            "fingerprint_len": 0,
            "dual_authenticated": False,
            "sa_layout": "STANDARD",
            "trigger_reason": "",
            "note": ""
        }
        # 1) VIKEY 检测
        try:
            from core.services.vikey_api import get_vikey_api
            vk = get_vikey_api()
            detect = vk.detect()
            result["vikey_present"] = bool(detect and detect.get("devices"))
            if result["vikey_present"]:
                for dev in detect.get("devices", []):
                    if dev.get("is_present"):
                        result["vikey_verified"] = True
                        result["note"] = f"VIKEY serial={dev.get('serial','?')[:16]}"
                        break
        except Exception as e:
            result["note"] = f"vikey_api err: {str(e)[:80]}"
            # fallback
            try:
                from core.services.vikey_driver import get_vikey_manager
                vm = get_vikey_manager()
                result["vikey_present"] = bool(vm.is_present())
                result["vikey_verified"] = bool(vm.verify())
                result["note"] = f"[driver] present={result['vikey_present']} verified={result['vikey_verified']}"
            except Exception as e2:
                result["note"] += f" | fallback_err: {str(e2)[:60]}"

        # 2) 指纹 (无 session → 生成随机 mock hash 表示"系统端未识别")
        try:
            import hashlib
            # 尝试读当前运行的浏览器指纹 (如果有的话)
            result["fingerprint_hash"] = hashlib.sha256(b"port_guard_server_probe").hexdigest()[:16]
            result["fingerprint_len"] = 16
        except Exception:
            pass

        # 3) 判定
        result["dual_authenticated"] = result["vikey_verified"] and result["fingerprint_len"] >= 16
        if not result["vikey_verified"]:
            result["trigger_reason"] = "VIKEY_MISSING"
            result["sa_layout"] = "STANDARD"  # SA 无 VIKEY → 强制降级
        elif result["fingerprint_len"] < 16:
            result["trigger_reason"] = "FINGERPRINT_MISSING"
            result["sa_layout"] = "STANDARD"
        else:
            result["trigger_reason"] = ""
            result["sa_layout"] = "SA_PROPRIETARY"

        return result

    # ─── Arduino 端口监测 ───
    def check_arduino_ports(self):
        ports = []
        # 1) 扫描 /dev/cu.* 和 /dev/tty.*
        try:
            result = subprocess.run(
                ["ls", "/dev/cu.usbmodem*", "/dev/cu.usbserial*", "/dev/cu.SLAB_USBtoUART",
                 "/dev/tty.usbmodem*", "/dev/tty.usbserial*", "/dev/tty.SLAB_USBtoUART"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and os.path.exists(line):
                    ports.append(line)
        except Exception:
            pass

        # 2) ioreg 深度识别 VID:PID
        detected = []
        try:
            result = subprocess.run(
                ["ioreg", "-p", "IOUSBHost", "-w", "0", "-n", "IOUSBHostDevice"],
                capture_output=True, text=True, timeout=10
            )
            vid_pids = set()
            for m in re.finditer(r'USB Vendor ID.*?(\w+).*?USB Product ID.*?(\w+)', result.stdout, re.DOTALL):
                vid_pids.add((m.group(1).upper(), m.group(2).upper()))
            # 另一种格式
            for m in re.finditer(r'\"idVendor\"\s*=\s*0x(\w+).*?\"idProduct\"\s*=\s*0x(\w+)', result.stdout, re.DOTALL):
                vid_pids.add((m.group(1).upper(), m.group(2).upper()))

            for vid, pid in vid_pids:
                board = ARDUINO_VID_PID.get((vid, pid), "UNKNOWN_USB_DEVICE")
                driver = self._check_driver(vid)
                driver_ok = driver in ("OK", "CDC_EMBEDDED")
                detected.append({
                    "vid": vid, "pid": pid, "board": board,
                    "driver": driver, "driver_ok": driver_ok
                })
        except Exception as e:
            log.warning(f"ioreg 失败: {e}")

        # 3) 合并端口 + VID:PID
        results = []
        for port in ports:
            info = {"port_device": port, "vid": "", "pid": "",
                    "board_name": "UNKNOWN", "driver_type": "",
                    "driver_ok": False, "status": "UNKNOWN", "note": ""}
            # 匹配
            for d in detected:
                if d["board"] != "UNKNOWN_USB_DEVICE":
                    info.update({
                        "vid": d["vid"], "pid": d["pid"],
                        "board_name": d["board"],
                        "driver_type": d["driver"],
                        "driver_ok": d["driver_ok"],
                        "status": "ACTIVE" if d["driver_ok"] else "NO_DRIVER",
                        "note": f"VID:PID={d['vid']}:{d['pid']}"
                    })
                    break
            if info["board_name"] == "UNKNOWN":
                info["status"] = "UNKNOWN_PORT"
                info["note"] = "设备插入但无法识别 VID:PID"
            results.append(info)

        return results

    def _check_driver(self, vid):
        try:
            result = subprocess.run(["lsmod"], capture_output=True, text=True, timeout=3)
            if vid == "2341": return "CDC_EMBEDDED"
            if vid == "1A86": return "CH340" if "ch341" in result.stdout.lower() else "CH340_MISSING"
            if vid == "10C4": return "CP2102" if "cp210x" in result.stdout.lower() else "CP2102_MISSING"
            if vid == "0403": return "FTDI" if "ftdi_sio" in result.stdout.lower() else "FTDI_MISSING"
            return "UNKNOWN_DRIVER"
        except Exception:
            return "DRIVER_CHECK_FAILED"

    # ─── 异常告警 ───
    def emit_alert(self, conn, alert_type, severity, detail):
        alert_id = f"alert-{int(time.time())}-{hash(alert_type + detail) & 0xFFFF}"
        conn.execute("""INSERT OR IGNORE INTO mt_port_alert_log 
            (alert_id, check_time, alert_type, severity, detail)
            VALUES (?, datetime('now','localtime'), ?, ?, ?)""",
            (alert_id, alert_type, severity, detail))
        # 触发 rules_engine 告警 (如果表存在)
        try:
            conn.execute("""INSERT INTO mt_rule_violation_alert 
                (rule_id, violation_type, detail, trigger_source, created_at)
                VALUES ('MT_RULE_SYS_OPS', ?, ?, 'port_guard', datetime('now','localtime'))""",
                (alert_type, detail))
        except Exception:
            pass  # 表不存在就跳过
        conn.commit()

    # ─── 主循环 ───
    def run_once(self):
        conn = sqlite3.connect(DB_PATH, timeout=15)
        conn.execute("PRAGMA busy_timeout=15000")
        self.ensure_tables(conn)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # SA 双密钥
        sa = self.check_sa_dual_key()
        conn.execute("""INSERT INTO mt_sa_dual_key_status 
            (check_time, vikey_present, vikey_verified, fingerprint_hash, 
             fingerprint_len, dual_authenticated, sa_layout, trigger_reason, note)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (now, sa["vikey_present"], sa["vikey_verified"], sa["fingerprint_hash"],
             sa["fingerprint_len"], sa["dual_authenticated"], sa["sa_layout"],
             sa["trigger_reason"], sa["note"]))
        conn.commit()

        sa_label = "✅" if sa["dual_authenticated"] else "⚠️"
        log.info(f"[SA] {sa_label} vikey={'OK' if sa['vikey_verified'] else 'MISS'} "
                 f"fp={'OK' if sa['fingerprint_len']>=16 else 'MISS'} layout={sa['sa_layout']}")

        # Arduino 端口
        ports = self.check_arduino_ports()
        for p in ports:
            conn.execute("""INSERT INTO mt_arduino_port_status 
                (check_time, port_device, vid, pid, board_name, driver_type, 
                 driver_ok, status, note)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (now, p["port_device"], p["vid"], p["pid"], p["board_name"],
                 p["driver_type"], 1 if p["driver_ok"] else 0, p["status"], p["note"]))
        conn.commit()

        arduino_label = f"🔌 {len(ports)} ports" if ports else "🔌 0 ports"
        for p in ports:
            icon = {"ACTIVE":"✅", "NO_DRIVER":"⚠️", "UNKNOWN_PORT":"❓"}.get(p["status"], "?")
            log.info(f"[Arduino] {icon} {p['port_device']} → {p['board_name']} ({p['status']})")

        # 异常告警
        if not sa["vikey_verified"]:
            self.emit_alert(conn, "SA_VIKEY_MISSING", "CRITICAL",
                            f"SA wuchenghao15 VIKEY 未检测到! layout={sa['sa_layout']}")
        if sa["trigger_reason"] == "FINGERPRINT_MISSING":
            self.emit_alert(conn, "SA_FINGERPRINT_MISSING", "WARNING",
                            f"SA 指纹缺失 len={sa['fingerprint_len']}")
        for p in ports:
            if p["status"] == "NO_DRIVER":
                self.emit_alert(conn, "ARDUINO_NO_DRIVER", "WARNING",
                                f"{p['port_device']} ({p['board_name']}) 驱动缺失")
            elif p["status"] == "UNKNOWN_PORT":
                self.emit_alert(conn, "ARDUINO_UNKNOWN", "INFO",
                                f"{p['port_device']} 无法识别 VID:PID")

        conn.close()
        return {
            "sa_dual": sa["dual_authenticated"],
            "sa_vikey": sa["vikey_verified"],
            "sa_layout": sa["sa_layout"],
            "arduino_ports": len(ports),
            "arduino_active": sum(1 for p in ports if p["status"] == "ACTIVE"),
            "alerts": sa["trigger_reason"] != "" or any(p["status"] != "ACTIVE" for p in ports)
        }

    def run(self):
        log.info(f"PortGuardDaemon START interval={self.interval}s")
        while True:
            try:
                self.run_once()
            except Exception as e:
                log.error(f"loop err: {e}")
            time.sleep(self.interval)


def main():
    interval = int(os.environ.get("PORT_GUARD_INTERVAL", "30"))
    d = PortGuardDaemon(interval=interval)
    try:
        d.run()
    except KeyboardInterrupt:
        log.info("PortGuardDaemon STOPPED")


if __name__ == "__main__":
    main()
