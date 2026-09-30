#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Arduino设备自动检测+驱动适配引擎
================================================================
flow_id: flow_arduino_detect_20260819_001

功能:
  1. 自动扫描已插入的Arduino设备(USB串口检测)
  2. 通过VID:PID识别板卡型号(UNO/Mega/Nano/Micro/ESP32/ESP8266等)
  3. 自动检测/安装驱动(CH340/CP2102/FT232/原生CDC)
  4. 自动配置IDE参数(板卡型号/端口/波特率/上传协议)
  5. 检测结果落库, 实时保持最新
  6. 设备热插拔感知(周期巡检)

macOS检测原理:
  - 原生CDC (ATmega32U4/UNO R4): /dev/cu.usbmodem* (VID:2341 PID:00xx)
  - CH340芯片 (UNO R3兼容版): /dev/cu.usbserial-* (VID:1A86 PID:7523)
  - CP2102芯片: /dev/cu.SLAB_USBtoUART (VID:10C4 PID:EA60)
  - FT232芯片: /dev/cu.usbserial-* (VID:0403 PID:6001)
  - ESP32: /dev/cu.SLAB_USBtoUART 或 /dev/cu.usbserial-* (VID:303A PID:0001)
  - ESP8266: /dev/cu.SLAB_USBtoUART (VID:10C4 PID:EA60)

CLI:
  python3 ai_arduino_detect_engine.py scan    扫描设备
  python3 ai_arduino_detect_engine.py status  查看状态
  python3 ai_arduino_detect_engine.py start   守护模式(周期巡检)
"""
import hashlib
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_ENGINES_DIR = os.path.join(ROOT, "ai_engines")
# v2.0 修复: 不再指向 flask-app/ai_engines/app.db（不存在），使用 core.db_path 解析到 _runtime/databases/Database/app.db
try:
    import sys as _sys_eng
    _sys_eng.path.insert(0, ROOT)
    from core.db_path import get_db_path as _gdbp
    APP_DB = _gdbp('app.db')
except Exception as _ex_appdb:
    # fallback: 与 _runtime 路径结构对齐
    RUNTIME_DIR_FB = os.path.join(ROOT, "..", "_runtime")
    APP_DB = os.path.join(RUNTIME_DIR_FB, "databases", "Database", "app.db")
    _appdb_fallback_warning = f"[WARN] ai_arduino_detect_engine app.db fallback: {APP_DB} ({_ex_appdb})"
    # 注意：RUNTIME_DIR 稍后再次定义，优先使用全局值
RUNTIME_DIR = os.path.join(ROOT, "..", "_runtime")
LOG_DIR = os.path.join(RUNTIME_DIR, "logs")
PID_DIR = os.path.join(RUNTIME_DIR, "pids")
PID_FILE = os.path.join(PID_DIR, "ai_arduino_detect_engine.pid")
LOG_FILE = os.path.join(LOG_DIR, "ai_arduino_detect_engine.log")

for _d in [LOG_DIR, PID_DIR]:
    os.makedirs(_d, exist_ok=True)

_LOCK = threading.Lock()
SCAN_INTERVAL = 30  # 30秒巡检一次

# ============================================================
# VID:PID → 板卡映射表
# ============================================================
USB_ID_MAP = {
    # Arduino官方 (VID=0x2341)
    (0x2341, 0x0001): ("Arduino Uno", "atmega328p", "stk500v1", "115200"),
    (0x2341, 0x0010): ("Arduino Mega2560", "atmega2560", "stk500v2", "115200"),
    (0x2341, 0x0023): ("Arduino Micro", "atmega32u4", "avr109", "115200"),
    (0x2341, 0x003B): ("Arduino Uno R4", "ra4m1", "stk500v1", "115200"),
    (0x2341, 0x0043): ("Arduino Uno R3", "atmega328p", "stk500v1", "115200"),
    (0x2341, 0x0044): ("Arduino Mega2560 R3", "atmega2560", "stk500v2", "115200"),
    (0x2341, 0x0243): ("Arduino Due", "sam3x8e", "arduino", "115200"),
    # CH340芯片 (VID=0x1A86 PID=0x7523) — 最常见的UNO兼容版
    (0x1A86, 0x7523): ("Arduino Uno (CH340)", "atmega328p", "stk500v1", "115200"),
    # CP2102芯片 (VID=0x10C4 PID=0xEA60) — ESP8266/ESP32常用
    (0x10C4, 0xEA60): ("ESP32/ESP8266 (CP2102)", "esp32", "esptool", "115200"),
    # FT232芯片 (VID=0x0403 PID=0x6001)
    (0x0403, 0x6001): ("Arduino (FT232)", "atmega328p", "stk500v1", "115200"),
    # ESP32原生USB (VID=0x303A)
    (0x303A, 0x0001): ("ESP32 DevKit (Native USB)", "esp32", "esptool", "115200"),
    # Adafruit
    (0x239A, 0x0011): ("Adafruit Feather 32U4", "atmega32u4", "avr109", "115200"),
}

# 驱动状态
DRIVER_STATUS = {
    "ch340": {"name": "CH340/CH341", "vendor": "WCH", "macos_driver": "_builtin_",
              "install_url": "https://www.wch.cn/downloads/CH34XSER_MAC_ZIP.html",
              "note": "macOS 11+内置驱动,旧版需手动安装"},
    "cp2102": {"name": "CP2102", "vendor": "Silicon Labs", "macos_driver": "builtin_since_10_15",
               "install_url": "https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers",
               "note": "macOS Catalina+内置,旧版需安装SiLabs VCP驱动"},
    "ft232": {"name": "FT232", "vendor": "FTDI", "macos_driver": "builtin",
              "install_url": "https://ftdichip.com/drivers/vcp-drivers/",
              "note": "macOS内置FTDI驱动"},
    "cdc": {"name": "USB CDC (Native)", "vendor": "Arduino", "macos_driver": "builtin",
            "install_url": "", "note": "原生USB CDC,无需额外驱动"},
}


def _now() -> str:
    return datetime.now().isoformat()


def _log(msg: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{_now()}] {msg}\n")


# ============================================================
# 1. 建表
# ============================================================
def ensure_detect_tables():
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_detected_devices (
            device_id       TEXT PRIMARY KEY,
            serial_port     TEXT NOT NULL,
            board_name      TEXT NOT NULL,
            chip            TEXT,
            upload_protocol TEXT,
            baud_rate       TEXT,
            vid             TEXT,
            pid             TEXT,
            manufacturer    TEXT,
            product_str     TEXT,
            serial_number   TEXT,
            driver_type     TEXT,
            driver_status   TEXT DEFAULT 'OK',
            ide_config_json  TEXT,
            detected_at     TEXT NOT NULL,
            last_seen       TEXT NOT NULL,
            is_connected    INTEGER DEFAULT 1,
            UNIQUE(serial_port)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_driver_log (
            log_id          TEXT PRIMARY KEY,
            driver_type     TEXT NOT NULL,
            action          TEXT NOT NULL,
            result          TEXT,
            details         TEXT,
            logged_at       TEXT NOT NULL
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_detect_log (
            scan_id         TEXT PRIMARY KEY,
            ports_scanned   INTEGER DEFAULT 0,
            devices_found   INTEGER DEFAULT 0,
            new_devices     INTEGER DEFAULT 0,
            removed_devices INTEGER DEFAULT 0,
            details_json    TEXT,
            scan_status     TEXT DEFAULT 'SUCCESS',
            scanned_at      TEXT NOT NULL
        )""")

        # v1.3.0 新增: Arduino用户会话表 (规则§13.7)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_user_sessions (
            session_id      TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL,
            username        TEXT NOT NULL,
            device_vid_pid  TEXT NOT NULL,
            board_model     TEXT,
            code_content    TEXT,
            code_language   TEXT DEFAULT 'cpp',
            config_json     TEXT DEFAULT '{}',
            usage_trace_json TEXT DEFAULT '[]',
            edit_history_json TEXT DEFAULT '[]',
            session_start   TEXT NOT NULL,
            session_end     TEXT,
            auto_saved      INTEGER DEFAULT 0,
            is_resumed      INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_user_device ON mt_arduino_user_sessions(user_id, device_vid_pid)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_user_recent ON mt_arduino_user_sessions(user_id, session_end DESC)")

        # v1.3.0 新增: 设备事件队列表 (规则§13.8 on_insert/on_remove回调载体)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_device_events (
            event_id        TEXT PRIMARY KEY,
            event_type      TEXT NOT NULL,
            device_vid_pid  TEXT NOT NULL,
            board_model     TEXT,
            serial_port     TEXT,
            payload_json    TEXT,
            created_at      TEXT NOT NULL,
            delivered       INTEGER DEFAULT 0,
            delivered_at    TEXT,
            acked           INTEGER DEFAULT 0,
            acked_at        TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_events_pending ON mt_arduino_device_events(delivered, acked, created_at)")

        # v2.0 新增: Arduino 用户专仓 (tasks_v2.md T00a)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_user_vault (
            vault_id            TEXT PRIMARY KEY,
            bound_user_id       INTEGER NOT NULL,
            session_id          TEXT,
            snapshot_version    INTEGER NOT NULL DEFAULT 1,
            label               TEXT DEFAULT '拔出自动保存',
            payload_json        TEXT NOT NULL,
            acl_json            TEXT NOT NULL DEFAULT '{"owner":0,"readers":[]}',
            size_bytes          INTEGER NOT NULL DEFAULT 0,
            committed_at        TEXT NOT NULL,
            json_backup_path    TEXT,
            git_tag             TEXT,
            git_commit_sha      TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_vault_user ON mt_arduino_user_vault(bound_user_id, committed_at DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_vault_created_at_desc ON mt_arduino_user_vault(committed_at DESC)")

        # v2.0 新增: Arduino 管理员设置多版 (T00b)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_admin_settings (
            setting_version     TEXT PRIMARY KEY,
            scope               TEXT NOT NULL DEFAULT 'global',
            key_name            TEXT NOT NULL,
            value_json          TEXT NOT NULL,
            changed_by          INTEGER NOT NULL,
            changed_at          TEXT NOT NULL,
            active_flag         INTEGER NOT NULL DEFAULT 1,
            ai_suggestion_ref   TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_settings_active ON mt_arduino_admin_settings(key_name, active_flag DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_settings_created_at_desc ON mt_arduino_admin_settings(changed_at DESC)")

        # v2.0 新增: Arduino 锁定/解锁审计 (T00c)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_lock_log (
            lock_id             TEXT PRIMARY KEY,
            user_id             INTEGER NOT NULL,
            session_id          TEXT,
            lock_trigger        TEXT NOT NULL,
            lock_reason         TEXT,
            released_by         TEXT,
            released_at         TEXT,
            committed_vault_id  TEXT,
            eigenflux_panel_ref TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_lock_user ON mt_arduino_lock_log(user_id, released_at DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_lock_created_at_desc ON mt_arduino_lock_log(COALESCE(released_at, substr(lock_id,8,8)) DESC)")

        # v2.0 新增: AI 介入审计 (T00d)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_ai_intervention_log (
            intervention_id     TEXT PRIMARY KEY,
            ai_group_type       TEXT NOT NULL,
            ai_employee_id      TEXT,
            action_type         TEXT NOT NULL,
            action_detail       TEXT,
            ai_confidence       REAL DEFAULT 0,
            eigenflux_consensus REAL,
            expert_reviewer_list TEXT,
            created_at          TEXT NOT NULL,
            applied_flag        INTEGER NOT NULL DEFAULT 0
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_aiinter_group ON mt_arduino_ai_intervention_log(ai_group_type, created_at DESC)")

        # v2.0 新增: 重写路由建议审计 (T00e)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_route_override_log (
            override_id         TEXT PRIMARY KEY,
            user_role           TEXT NOT NULL,
            source_path         TEXT NOT NULL,
            rewritten_path      TEXT NOT NULL,
            rule_reason         TEXT,
            ai_agent_id         TEXT,
            eigenflux_panel_ref TEXT,
            created_at          TEXT NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_arduino_route_role_created ON mt_arduino_route_override_log(user_role, created_at DESC)")

        conn.commit()
        conn.close()


# ============================================================
# 2. USB设备扫描
# ============================================================
def _scan_serial_ports() -> List[Dict]:
    """扫描 /dev/cu.* 串口设备"""
    ports = []
    # 方法1: 直接扫描/dev/cu.* 文件
    try:
        result = subprocess.run(["ls", "/dev/"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("cu."):
                port = "/dev/" + line
                ports.append({"port": port, "source": "fs"})
    except Exception:
        pass

    # 方法2: 使用 system_profiler SPUSBDataType 获取USB设备详情
    try:
        result = subprocess.run(
            ["system_profiler", "SPUSBDataType", "-json"],
            capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout:
            usb_data = json.loads(result.stdout)
            _extract_usb_devices(usb_data, ports)
    except Exception as e:
        _log(f"[SCAN] system_profiler error: {e}")

    # 方法3: 使用 ioreg 获取VID/PID (更精确)
    try:
        result = subprocess.run(
            ["ioreg", "-p", "IOUSB", "-l", "-w", "0"],
            capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            _parse_ioreg(result.stdout, ports)
    except Exception as e:
        _log(f"[SCAN] ioreg error: {e}")

    return ports


def _extract_usb_devices(usb_data: Dict, ports: List[Dict]):
    """从system_profiler JSON提取USB设备"""
    def _walk(obj, path=""):
        if isinstance(obj, dict):
            # 检查是否是USB设备
            name = obj.get("_name", "")
            vid = obj.get("idVendor", "")
            pid = obj.get("idProduct", "")
            serial = obj.get("USB Serial Number", "")
            manufacturer = obj.get("manufacturer", "")
            if vid and pid:
                for p in ports:
                    if not p.get("vid"):
                        p["vid"] = str(vid)
                        p["pid"] = str(pid)
                        p["manufacturer"] = manufacturer
                        p["product_str"] = name
                        p["serial_number"] = serial
            for k, v in obj.items():
                _walk(v, path + "/" + str(k))
        elif isinstance(obj, list):
            for item in obj:
                _walk(item, path)

    _walk(usb_data)


def _parse_ioreg(ioreg_output: str, ports: List[Dict]):
    """从ioreg输出解析VID:PID"""
    current_vid = None
    current_pid = None
    current_product = None
    current_serial = None

    for line in ioreg_output.split("\n"):
        line = line.strip()
        if "idVendor" in line:
            m = re.search(r"idVendor\s*=\s*(\d+)", line)
            if m:
                current_vid = int(m.group(1))
        if "idProduct" in line:
            m = re.search(r"idProduct\s*=\s*(\d+)", line)
            if m:
                current_pid = int(m.group(1))
        if "USB Product Name" in line:
            m = re.search(r'"USB Product Name"\s*=\s*"([^"]*)"', line)
            if m:
                current_product = m.group(1)
        if "USB Serial Number" in line:
            m = re.search(r'"USB Serial Number"\s*=\s*"([^"]*)"', line)
            if m:
                current_serial = m.group(1)

        # 如果同时有VID和PID,尝试匹配端口
        if current_vid and current_pid:
            for p in ports:
                if not p.get("vid"):
                    p["vid"] = str(current_vid)
                    p["pid"] = str(current_pid)
                    p["product_str"] = current_product or ""
                    p["serial_number"] = current_serial or ""


def _identify_board(vid: str, pid: str) -> Dict:
    """通过VID:PID识别板卡型号"""
    try:
        v = int(vid, 0) if vid else 0
        p = int(pid, 0) if pid else 0
    except (ValueError, TypeError):
        v, p = 0, 0

    # 查表
    info = USB_ID_MAP.get((v, p))
    if info:
        board_name, chip, protocol, baud = info
        return {
            "board_name": board_name,
            "chip": chip,
            "upload_protocol": protocol,
            "baud_rate": baud,
            "vid": str(v),
            "pid": str(p),
        }

    # 模糊匹配
    if v == 0x2341:
        return {"board_name": "Arduino (Unknown Model)", "chip": "unknown",
                "upload_protocol": "stk500v1", "baud_rate": "115200",
                "vid": str(v), "pid": str(p)}
    if v == 0x1A86:
        return {"board_name": "Arduino (CH340 Compatible)", "chip": "atmega328p",
                "upload_protocol": "stk500v1", "baud_rate": "115200",
                "vid": str(v), "pid": str(p)}
    if v == 0x10C4:
        return {"board_name": "ESP/Arduino (CP2102)", "chip": "esp32",
                "upload_protocol": "esptool", "baud_rate": "115200",
                "vid": str(v), "pid": str(p)}

    return {"board_name": "Unknown USB Serial Device", "chip": "unknown",
            "upload_protocol": "unknown", "baud_rate": "115200",
            "vid": str(v), "pid": str(p)}


def _detect_driver_type(vid: str) -> str:
    """根据VID判断驱动类型"""
    try:
        v = int(vid, 0) if vid else 0
    except (ValueError, TypeError):
        v = 0
    if v == 0x1A86:
        return "ch340"
    if v == 0x10C4:
        return "cp2102"
    if v == 0x0403:
        return "ft232"
    if v in (0x2341, 0x239A, 0x303A):
        return "cdc"
    return "unknown"


def _check_driver_status(driver_type: str) -> Dict:
    """检查驱动状态"""
    info = DRIVER_STATUS.get(driver_type, {"name": "Unknown", "note": ""})
    # macOS: 检查kext是否加载
    if driver_type == "ch340":
        try:
            r = subprocess.run(["kextstat", "-b", "com.wch.ch34x"],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                return {"status": "OK", "driver": info["name"], "note": "kext loaded"}
            # macOS 11+内置, 检查/dev/cu.usbserial*是否存在
            r2 = subprocess.run(["ls", "/dev/cu.usbserial*"],
                                capture_output=True, text=True, timeout=5)
            if r2.returncode == 0:
                return {"status": "OK", "driver": info["name"], "note": "builtin driver active"}
            return {"status": "NEED_INSTALL", "driver": info["name"],
                    "note": info.get("note", ""), "url": info.get("install_url", "")}
        except Exception:
            return {"status": "UNKNOWN", "driver": info["name"]}
    elif driver_type == "cp2102":
        try:
            r = subprocess.run(["ls", "/dev/cu.SLAB_USBtoUART"],
                                capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return {"status": "OK", "driver": info["name"], "note": "builtin driver active"}
            return {"status": "NEED_INSTALL", "driver": info["name"],
                    "note": info.get("note", ""), "url": info.get("install_url", "")}
        except Exception:
            return {"status": "UNKNOWN", "driver": info["name"]}
    elif driver_type in ("ft232", "cdc"):
        return {"status": "OK", "driver": info["name"], "note": "macOS builtin"}
    return {"status": "OK", "driver": info.get("name", "Unknown")}


def _generate_ide_config(board_name: str, chip: str, port: str,
                         protocol: str, baud: str) -> Dict:
    """生成IDE配置JSON"""
    return {
        "board": board_name,
        "chip": chip,
        "port": port,
        "upload_protocol": protocol,
        "upload_speed": baud,
        "monitor_speed": baud,
        "ide_settings": {
            "compiler_warnings": "Default",
            "optimize": "Default",
            "board_parts": "",
            "configuration": "",
        },
        "auto_detected": True,
        "detected_at": _now(),
    }


# ============================================================
# 3. 同步逻辑
# ============================================================
def _emit_device_event(c, event_type: str, vid: str, pid: str,
                       board_model: str, serial_port: str, ts: str):
    """v1.3.0 §13.8: 写入设备事件到 mt_arduino_device_events 队列
    作为 on_insert/on_remove 回调的持久化载体, 前端通过 /api/arduino/events/poll 拉取
    """
    event_id = "ARD-EVT-%s" % uuid.uuid4().hex[:12]
    vid_pid = "%s:%s" % (str(vid), str(pid))
    payload = {
        "event_type": event_type,
        "device_vid_pid": vid_pid,
        "board_model": board_model,
        "serial_port": serial_port,
        "timestamp": ts,
    }
    c.execute("""INSERT INTO mt_arduino_device_events
        (event_id, event_type, device_vid_pid, board_model, serial_port,
         payload_json, created_at, delivered, acked)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (event_id, event_type, vid_pid, board_model, serial_port,
         json.dumps(payload, ensure_ascii=False), ts, 0, 0))
    _log(f"[EVENT] {event_type} vid_pid={vid_pid} board={board_model} port={serial_port}")


def get_pending_events(limit: int = 10) -> List[Dict]:
    """v1.3.0: 拉取未投递的设备事件 (前端轮询调用)"""
    ensure_detect_tables()
    now = _now()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("""SELECT * FROM mt_arduino_device_events
            WHERE delivered=0 ORDER BY created_at ASC LIMIT ?""", (limit,)).fetchall()
        events = []
        for row in rows:
            ev = dict(row)
            try:
                ev["payload"] = json.loads(row["payload_json"]) if row["payload_json"] else {}
            except Exception:
                ev["payload"] = {}
            events.append(ev)
            c.execute("""UPDATE mt_arduino_device_events
                SET delivered=1, delivered_at=? WHERE event_id=?""", (now, row["event_id"]))
        conn.commit()
        conn.close()
    return events


def ack_event(event_id: str) -> bool:
    """v1.3.0: 确认事件已处理 (前端处理完跳转/退出后调用)"""
    ensure_detect_tables()
    now = _now()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        c.execute("""UPDATE mt_arduino_device_events
            SET acked=1, acked_at=? WHERE event_id=?""", (now, event_id))
        conn.commit()
        ok = c.rowcount > 0
        conn.close()
    return ok


def scan_devices() -> Dict:
    """执行一次设备扫描"""
    ensure_detect_tables()
    now = _now()
    ports = _scan_serial_ports()

    # 筛选Arduino相关端口 (v2.0: 扩展关键词覆盖 CH343/CH9102/CP2105 等)
    arduino_ports = []
    for p in ports:
        port_name = p.get("port", "")
        if any(kw in port_name for kw in [
            "usbmodem", "usbserial", "SLAB_USB", "wchusbserial",
            "usbmod", "usbser",  # 简化匹配 (cu.usbmodem*, cu.usbserial*)
            "CH343", "CH9102", "CP210",  # 芯片名直接匹配
        ]):
            arduino_ports.append(p)

    results = {"ports_scanned": len(ports), "arduino_ports": len(arduino_ports),
               "devices_found": 0, "new_devices": 0, "updated": 0, "removed": 0,
               "devices": []}

    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # v1.3.0: 扫描前快照已连接设备(用于事件回调对比)
        prev_connected = {}
        for row in c.execute(
            "SELECT serial_port, vid, pid, board_name FROM mt_arduino_detected_devices WHERE is_connected=1"
        ).fetchall():
            prev_connected[row["serial_port"]] = dict(row)

        # 标记所有现有设备为离线
        c.execute("UPDATE mt_arduino_detected_devices SET is_connected=0")

        current_ports_set = set()

        for p in arduino_ports:
            port = p.get("port", "")
            vid = p.get("vid", "0")
            pid = p.get("pid", "0")
            current_ports_set.add(port)

            # 识别板卡
            board_info = _identify_board(vid, pid)
            board_name = board_info["board_name"]
            chip = board_info["chip"]
            protocol = board_info["upload_protocol"]
            baud = board_info["baud_rate"]

            # 驱动检测
            driver_type = _detect_driver_type(vid)
            driver_result = _check_driver_status(driver_type)

            # 生成IDE配置
            ide_config = _generate_ide_config(board_name, chip, port, protocol, baud)

            device_id = "ARD-DEV-%s" % uuid.uuid4().hex[:10]

            # 检查是否已存在(按serial_port)
            existing = c.execute(
                "SELECT device_id FROM mt_arduino_detected_devices WHERE serial_port=?",
                (port,)).fetchone()

            if existing:
                c.execute("""UPDATE mt_arduino_detected_devices SET
                    board_name=?, chip=?, upload_protocol=?, baud_rate=?,
                    vid=?, pid=?, manufacturer=?, product_str=?, serial_number=?,
                    driver_type=?, driver_status=?, ide_config_json=?,
                    last_seen=?, is_connected=1 WHERE serial_port=?""",
                    (board_name, chip, protocol, baud,
                     str(vid), str(pid), p.get("manufacturer", ""),
                     p.get("product_str", ""), p.get("serial_number", ""),
                     driver_type, driver_result["status"],
                     json.dumps(ide_config, ensure_ascii=False),
                     now, port))
                results["updated"] += 1
            else:
                c.execute("""INSERT INTO mt_arduino_detected_devices
                    (device_id, serial_port, board_name, chip, upload_protocol,
                     baud_rate, vid, pid, manufacturer, product_str, serial_number,
                     driver_type, driver_status, ide_config_json,
                     detected_at, last_seen, is_connected)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (device_id, port, board_name, chip, protocol, baud,
                     str(vid), str(pid), p.get("manufacturer", ""),
                     p.get("product_str", ""), p.get("serial_number", ""),
                     driver_type, driver_result["status"],
                     json.dumps(ide_config, ensure_ascii=False),
                     now, now, 1))
                results["new_devices"] += 1

            # v1.3.0: on_insert 回调 — 新插入设备(prev_connected 中不存在)
            if port not in prev_connected:
                _emit_device_event(c, "insert", vid, pid, board_name, port, now)

            # 如果驱动需要安装,记录日志
            if driver_result["status"] == "NEED_INSTALL":
                log_id = "DRV-LOG-%s" % uuid.uuid4().hex[:10]
                c.execute("""INSERT INTO mt_arduino_driver_log
                    (log_id, driver_type, action, result, details, logged_at)
                    VALUES(?,?,?,?,?,?)""",
                    (log_id, driver_type, "AUTO_DETECT", "NEED_INSTALL",
                     json.dumps(driver_result, ensure_ascii=False), now))

            results["devices_found"] += 1
            results["devices"].append({
                "port": port,
                "board": board_name,
                "chip": chip,
                "driver": driver_type,
                "driver_status": driver_result["status"],
                "ide_config": ide_config,
            })

        # v1.3.0: on_remove 回调 — 拔出设备(prev_connected 中存在但本次未扫到)
        for port, info in prev_connected.items():
            if port not in current_ports_set:
                _emit_device_event(c, "remove", info.get("vid", "0"),
                                   info.get("pid", "0"),
                                   info.get("board_name", "Unknown"),
                                   port, now)

        # 统计离线设备
        offline = c.execute(
            "SELECT COUNT(*) FROM mt_arduino_detected_devices WHERE is_connected=0").fetchone()[0]
        results["removed_devices"] = offline

        # 写扫描日志
        scan_id = "ARD-SCAN-%s" % uuid.uuid4().hex[:10]
        c.execute("""INSERT INTO mt_arduino_detect_log
            (scan_id, ports_scanned, devices_found, new_devices, removed_devices,
             details_json, scan_status, scanned_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (scan_id, results["ports_scanned"], results["devices_found"],
             results["new_devices"], results["removed_devices"],
             json.dumps(results, ensure_ascii=False)[:2000],
             "SUCCESS", now))

        conn.commit()
        conn.close()

    _log(f"[SCAN] ports={results['ports_scanned']} arduino={results['devices_found']} "
         f"new={results['new_devices']} updated={results['updated']} offline={offline}")
    return results


def get_status() -> Dict:
    ensure_detect_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        total = c.execute("SELECT COUNT(*) FROM mt_arduino_detected_devices").fetchone()[0]
        connected = c.execute(
            "SELECT COUNT(*) FROM mt_arduino_detected_devices WHERE is_connected=1").fetchone()[0]
        offline = c.execute(
            "SELECT COUNT(*) FROM mt_arduino_detected_devices WHERE is_connected=0").fetchone()[0]
        scans = c.execute("SELECT COUNT(*) FROM mt_arduino_detect_log").fetchone()[0]
        driver_issues = c.execute(
            "SELECT COUNT(*) FROM mt_arduino_driver_log WHERE result='NEED_INSTALL'").fetchone()[0]

        devices = []
        for row in c.execute(
            "SELECT * FROM mt_arduino_detected_devices WHERE is_connected=1 ORDER BY last_seen DESC").fetchall():
            devices.append(dict(row))

        last_scan = c.execute(
            "SELECT * FROM mt_arduino_detect_log ORDER BY scanned_at DESC LIMIT 1").fetchone()
        conn.close()

    # v2.0: 构建 connected_vid_pids 列表（从 devices 的 vid:pid 组合）
    connected_vid_pids = []
    for d in devices:
        dv = str(d.get("vid") or "")
        dp = str(d.get("pid") or "")
        if dv and dp and dv != "0" and dp != "0":
            connected_vid_pids.append("%s:%s" % (dv, dp))
        elif dv and dp:
            # vid:pid 为 0:0 时也加入（设备已连接但 VID:PID 未获取到）
            connected_vid_pids.append("%s:%s" % (dv, dp))

    return {"total_devices": total, "connected": connected,
            "offline": offline, "scan_count": scans,
            "driver_issues": driver_issues,
            "devices": devices,
            "connected_vid_pids": connected_vid_pids,
            "last_scan": dict(last_scan) if last_scan else None}


# ============================================================
# 4. 用户会话 DAO (规则§13.5/§13.6/§13.7)
# ============================================================
def save_user_session(user_id: str, username: str, device_vid_pid: str,
                      board_model: str, code_content: str = "",
                      code_language: str = "cpp", config_json: str = "{}",
                      usage_trace_json: str = "[]", edit_history_json: str = "[]",
                      auto_saved: int = 0, session_id: str = None) -> str:
    """v1.3.0 §13.5: 保存/更新用户Arduino编译会话 (写穿机制)"""
    ensure_detect_tables()
    now = _now()
    sid = session_id or ("ARD-SES-%s" % uuid.uuid4().hex[:12])
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        existing = c.execute(
            "SELECT session_id FROM mt_arduino_user_sessions WHERE session_id=?", (sid,)).fetchone()
        if existing:
            c.execute("""UPDATE mt_arduino_user_sessions SET
                user_id=?, username=?, device_vid_pid=?, board_model=?, code_content=?,
                code_language=?, config_json=?, usage_trace_json=?, edit_history_json=?,
                auto_saved=?, updated_at=?, session_end=?
                WHERE session_id=?""",
                (user_id, username, device_vid_pid, board_model, code_content,
                 code_language, config_json, usage_trace_json, edit_history_json,
                 auto_saved, now, now, sid))
        else:
            c.execute("""INSERT INTO mt_arduino_user_sessions
                (session_id, user_id, username, device_vid_pid, board_model,
                 code_content, code_language, config_json, usage_trace_json,
                 edit_history_json, session_start, session_end, auto_saved,
                 is_resumed, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (sid, user_id, username, device_vid_pid, board_model,
                 code_content, code_language, config_json, usage_trace_json,
                 edit_history_json, now, now, auto_saved, 0, now, now))
        conn.commit()
        conn.close()
    _log(f"[SESSION] saved sid={sid} user={username} device={device_vid_pid}")
    return sid


def load_user_session(user_id: str, device_vid_pid: str = None) -> Optional[Dict]:
    """v1.3.0 §13.6: 载入用户上次会话 (按 device_vid_pid 精确匹配, 无则取最近一条)"""
    ensure_detect_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if device_vid_pid:
            row = c.execute("""SELECT * FROM mt_arduino_user_sessions
                WHERE user_id=? AND device_vid_pid=?
                ORDER BY updated_at DESC LIMIT 1""", (user_id, device_vid_pid)).fetchone()
        else:
            row = c.execute("""SELECT * FROM mt_arduino_user_sessions
                WHERE user_id=? ORDER BY updated_at DESC LIMIT 1""", (user_id,)).fetchone()
        result = dict(row) if row else None
        if result:
            # 标记为已恢复载入
            c.execute("""UPDATE mt_arduino_user_sessions SET is_resumed=1, updated_at=?
                WHERE session_id=?""", (_now(), result["session_id"]))
            conn.commit()
        conn.close()
    if result:
        _log(f"[SESSION] loaded sid={result['session_id']} user={result['username']}")
    return result


def append_usage_trace(session_id: str, trace_entry: Dict) -> bool:
    """v1.3.0 §13.5: 追加使用痕迹记录 (操作序列)"""
    ensure_detect_tables()
    now = _now()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        row = c.execute(
            "SELECT usage_trace_json FROM mt_arduino_user_sessions WHERE session_id=?",
            (session_id,)).fetchone()
        if not row:
            conn.close()
            return False
        try:
            traces = json.loads(row[0]) if row[0] else []
        except Exception:
            traces = []
        traces.append(trace_entry)
        c.execute("""UPDATE mt_arduino_user_sessions SET usage_trace_json=?, updated_at=?
            WHERE session_id=?""", (json.dumps(traces, ensure_ascii=False), now, session_id))
        conn.commit()
        conn.close()
    return True


def end_user_session(session_id: str) -> bool:
    """v1.3.0 §13.3: 结束会话 (设备拔出时调用)"""
    ensure_detect_tables()
    now = _now()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        c.execute("""UPDATE mt_arduino_user_sessions SET session_end=?, updated_at=?
            WHERE session_id=?""", (now, now, session_id))
        conn.commit()
        ok = c.rowcount > 0
        conn.close()
    return ok


# ============================================================
# v2.0 T04a 管理员设置 DAO (save_admin_setting + load_active_settings_dict)
# ============================================================
def save_admin_setting(key_name: str, value_json: str, changed_by: int,
                       ai_suggestion_ref: str = None, scope: str = 'global') -> str:
    """保存一个管理员设置：旧版 active_flag=0，插入新版。返回 setting_version。"""
    ensure_detect_tables()
    now = _now()
    version = f"ARD-SET-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        # 旧版失效
        c.execute("""UPDATE mt_arduino_admin_settings
            SET active_flag=0 WHERE key_name=? AND active_flag=1""", (key_name,))
        # 新版插入
        c.execute("""INSERT INTO mt_arduino_admin_settings
            (setting_version, scope, key_name, value_json, changed_by,
             changed_at, active_flag, ai_suggestion_ref)
            VALUES(?,?,?,?,?,?,1,?)""",
            (version, scope, key_name, value_json, int(changed_by), now, ai_suggestion_ref))
        conn.commit()
        conn.close()
    _log(f"[SETTINGS] saved key={key_name} by={changed_by} ver={version}")
    return version


def load_active_settings_dict() -> Dict[str, Any]:
    """加载所有 active_flag=1 的设置，返回 {key: parsed_value} 字典。"""
    ensure_detect_tables()
    result: Dict[str, Any] = {}
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("""SELECT key_name, value_json
            FROM mt_arduino_admin_settings WHERE active_flag=1""").fetchall()
        for row in rows:
            try:
                result[row['key_name']] = json.loads(row['value_json'])
            except Exception:
                result[row['key_name']] = row['value_json']
        conn.close()
    # 默认设置兜底（避免前端空字段）
    defaults = {
        'board_whitelist': ['arduino_uno', 'arduino_mega2560', 'arduino_nano',
                             'arduino_micro', 'esp32_devkit', 'esp8266'],
        'toolchain_path': '',
        'default_upload_port': '',
        'default_baud_rate': '115200',
        'autosave_interval_sec': 60,
        'require_device_for_save': True,
        'vault_quota_mb': 100,
        'variant_template_defaults': {
            'default_board': 'arduino_uno',
            'default_libraries': ['Wire', 'SPI'],
        },
        'lock_behavior_on_remove': 'prompt_save',
        'admin_setup_note': '',
    }
    for k, v in defaults.items():
        if k not in result:
            result[k] = v
    return result


# ============================================================
# v2.0 T10a / T10b  用户专仓 commit (三重永久化: SQLite + JSON + Git)
# ============================================================
_VAULT_RUNTIME = os.path.join(ROOT, "..", "_runtime", "arduino_vault")
_VAULT_GIT_REPO = os.path.join(ROOT, "..", "_runtime", "arduino_vault_repo")


def _vault_ensure_dirs():
    os.makedirs(_VAULT_RUNTIME, exist_ok=True)
    os.makedirs(_VAULT_GIT_REPO, exist_ok=True)


def commit_to_user_vault(user_id: int, session_id: Optional[str],
                         code_content: str, variant_actions: List,
                         variant_params: Dict, usage_trace: List = None,
                         edit_history: List = None,
                         label: str = '拔出自动保存') -> Dict[str, Any]:
    """T10a: 写入 SQLite 行 + 物理 JSON 备份。返回 vault_row 信息。"""
    ensure_detect_tables()
    _vault_ensure_dirs()
    now = _now()
    ts_str = datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        uid_hash = hashlib.sha1(str(user_id).encode()).hexdigest()[:8]
    except Exception:
        uid_hash = '00000000'
    vault_id = f"ARD-VLT-{uid_hash}-{ts_str}-{uuid.uuid4().hex[:6]}"

    device_snap = {}
    try:
        st = get_status()
        device_snap = {
            'connected': st.get('connected'),
            'devices': [{'port': d.get('serial_port'), 'vid': d.get('vid'),
                         'pid': d.get('pid'), 'board': d.get('board_name')}
                        for d in (st.get('devices') or [])],
        }
    except Exception:
        pass

    payload = {
        'code_content': code_content or '',
        'variant_actions': variant_actions or [],
        'variant_params': variant_params or {},
        'usage_trace': usage_trace or [],
        'edit_history': edit_history or [],
        'device_snapshot': device_snap,
        'committed_at': now,
        'vault_id': vault_id,
    }
    payload_json = json.dumps(payload, ensure_ascii=False)
    size_bytes = len(payload_json.encode('utf-8'))

    acl = json.dumps({'owner': int(user_id), 'readers': []})

    # 1) SQLite 行
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        # 获取最大 snapshot_version + 1
        try:
            max_v = c.execute("""SELECT MAX(snapshot_version) FROM mt_arduino_user_vault
                WHERE bound_user_id=?""", (int(user_id),)).fetchone()[0] or 0
        except Exception:
            max_v = 0
        snap_ver = int(max_v) + 1
        c.execute("""INSERT INTO mt_arduino_user_vault
            (vault_id, bound_user_id, session_id, snapshot_version, label,
             payload_json, acl_json, size_bytes, committed_at)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (vault_id, int(user_id), session_id, snap_ver, label,
             payload_json, acl, size_bytes, now))
        conn.commit()
        conn.close()

    # 2) 物理 JSON 备份
    user_dir = os.path.join(_VAULT_RUNTIME, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    json_path = os.path.join(user_dir, f"{vault_id}.json")
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(payload_json)
    except Exception as e:
        _log(f"[VAULT] JSON write failed: {e}")
        json_path = None

    return {
        'vault_id': vault_id,
        'snapshot_version': snap_ver,
        'bound_user_id': int(user_id),
        'session_id': session_id,
        'size_bytes': size_bytes,
        'committed_at': now,
        'json_backup_path': json_path,
        'label': label,
    }


def _git_tag_vault(vault_id: str, username: str, json_path: Optional[str]) -> tuple:
    """T10b: Git 仓归档（失败自动降级为 FAILED_DEGRADED）。返回 (tag_or_status, commit_sha_or_None)。"""
    if not json_path or not os.path.exists(json_path):
        return ('FAILED_DEGRADED', None)
    _vault_ensure_dirs()
    repo_dir = os.path.abspath(_VAULT_GIT_REPO)
    try:
        # 首次 init
        if not os.path.isdir(os.path.join(repo_dir, '.git')):
            subprocess.run(['git', 'init'], cwd=repo_dir,
                           capture_output=True, timeout=10, check=False)
            gi = os.path.join(repo_dir, '.gitignore')
            if not os.path.exists(gi):
                try:
                    with open(gi, 'w') as f:
                        f.write("*.tmp\n*.swp\n.DS_Store\n__pycache__/\n")
                except Exception:
                    pass
            subprocess.run(['git', 'config', 'user.email', 'arduino-vault@mtscos.local'],
                           cwd=repo_dir, capture_output=True, timeout=10, check=False)
            subprocess.run(['git', 'config', 'user.name', 'ArduinoVaultBot'],
                           cwd=repo_dir, capture_output=True, timeout=10, check=False)

        # 复制文件
        import shutil
        uid = os.path.basename(os.path.dirname(json_path))
        target_dir = os.path.join(repo_dir, 'users', uid)
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, f"{vault_id}.json")
        shutil.copy2(json_path, target_file)

        # commit
        subprocess.run(['git', 'add', '-A'], cwd=repo_dir,
                       capture_output=True, timeout=30, check=False)
        r = subprocess.run(
            ['git', 'commit', '-m', f"vault: {vault_id} by {username}"],
            cwd=repo_dir, capture_output=True, timeout=30, check=False)
        if r.returncode != 0:
            # nothing to commit
            return ('FAILED_DEGRADED', None)
        sha_r = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo_dir,
                              capture_output=True, text=True, timeout=10, check=False)
        commit_sha = (sha_r.stdout or '').strip()[:12] or None

        # tag
        tag = f"vault/{vault_id}"
        subprocess.run(['git', 'tag', tag], cwd=repo_dir,
                       capture_output=True, timeout=10, check=False)
        return (tag, commit_sha)
    except Exception as e:
        _log(f"[VAULT-GIT] error: {e}")
        return ('FAILED_DEGRADED', None)


def update_vault_git_refs(vault_id: str, git_tag: str, git_commit_sha: str,
                          json_backup_path: str) -> bool:
    """T10d 步骤5: 更新 vault 行的 git 字段与 json_backup_path。"""
    ensure_detect_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        c.execute("""UPDATE mt_arduino_user_vault
            SET git_tag=?, git_commit_sha=?, json_backup_path=? WHERE vault_id=?""",
            (git_tag, git_commit_sha, json_backup_path, vault_id))
        ok = c.rowcount > 0
        conn.commit()
        conn.close()
    return ok


# ============================================================
# v2.0 T10c 更新会话 variant_* 字段 + committed + vault_id
# ============================================================
def update_session_variants_and_commit(session_id: str, variant_actions_json: str,
                                       variant_params_json: str, locked_reason: Optional[str],
                                       vault_id: str) -> bool:
    ensure_detect_tables()
    now = _now()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        c.execute("""UPDATE mt_arduino_user_sessions SET
            variant_actions_json=?, variant_params_json=?,
            locked_reason=?, committed=1, committed_at=?, vault_id=?
            WHERE session_id=?""",
            (variant_actions_json or '[]', variant_params_json or '{}',
             locked_reason, now, vault_id, session_id))
        # 兼容：如果表还没有 variant_actions_json 等列，降级跳过（通过 ALTER TABLE 再 UPDATE）
        ok = c.rowcount > 0
        conn.commit()
        conn.close()
    if not ok:
        # 尝试加列并重试
        try:
            with _LOCK:
                conn = sqlite3.connect(APP_DB, timeout=30)
                c = conn.cursor()
                for col, defval in [('variant_actions_json', "'[]'"),
                                    ('variant_params_json', "'{}'"),
                                    ('locked_reason', 'NULL'),
                                    ('committed', '0'),
                                    ('committed_at', 'NULL'),
                                    ('vault_id', 'NULL')]:
                    try:
                        c.execute(f"ALTER TABLE mt_arduino_user_sessions ADD COLUMN {col}")
                    except Exception:
                        pass
                conn.commit()
                conn.close()
            return update_session_variants_and_commit(
                session_id, variant_actions_json, variant_params_json,
                locked_reason, vault_id)
        except Exception:
            return False
    return True


# ============================================================
# v2.0 T11a  用户专仓分页查询（本人 / SA as_user 过滤）
# ============================================================
def list_user_vault(current_user_id: int, is_sa: bool = False,
                    as_user: int = None, page: int = 1, size: int = 10) -> List[Dict]:
    ensure_detect_tables()
    target_uid = int(as_user) if (is_sa and as_user) else int(current_user_id)
    offset = (max(1, int(page)) - 1) * max(1, int(size))
    limit = max(1, min(100, int(size)))
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("""SELECT vault_id, bound_user_id, session_id, snapshot_version,
            label, size_bytes, committed_at, json_backup_path, git_tag, git_commit_sha
            FROM mt_arduino_user_vault WHERE bound_user_id=?
            ORDER BY committed_at DESC LIMIT ? OFFSET ?""",
            (target_uid, limit, offset)).fetchall()
        result = [dict(r) for r in rows]
        conn.close()
    return result


def get_vault_by_id(vault_id: str) -> Optional[Dict]:
    ensure_detect_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        row = c.execute("SELECT * FROM mt_arduino_user_vault WHERE vault_id=?",
                        (vault_id,)).fetchone()
        result = dict(row) if row else None
        conn.close()
    return result


# ============================================================
# v2.0 T13a  专仓配额统计 GROUP BY user
# ============================================================
def list_vault_usage_summary() -> List[Dict]:
    ensure_detect_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("""
            SELECT v.bound_user_id AS user_id,
                   COUNT(*) AS commit_count,
                   SUM(v.size_bytes) AS total_bytes,
                   MAX(v.committed_at) AS last_commit_at,
                   u.username AS username
            FROM mt_arduino_user_vault v
            LEFT JOIN users u ON u.id = v.bound_user_id
            GROUP BY v.bound_user_id
            ORDER BY total_bytes DESC
            LIMIT 200
        """).fetchall()
        result = []
        for r in rows:
            total_bytes = int(r['total_bytes'] or 0)
            uid = r['user_id']
            result.append({
                'user_id': uid,
                'bound_user_id': uid,  # 双写别名，兼容模板里的 .get('bound_user_id')
                'username': r['username'] or f'uid_{uid}',
                'commit_count': int(r['commit_count'] or 0),
                'total_bytes': total_bytes,
                'total_mb': round(total_bytes / 1048576, 2),
                'last_commit_at': r['last_commit_at'],
            })
        conn.close()
    return result


# ============================================================
# v2.0 锁定日志写入 (T06a / T08b)
# ============================================================
def write_lock_log(lock_id: str, user_id: int, session_id: Optional[str],
                   lock_trigger: str, lock_reason: Optional[str] = None,
                   eigenflux_panel_ref: Optional[str] = None) -> bool:
    ensure_detect_tables()
    with _LOCK:
        try:
            conn = sqlite3.connect(APP_DB, timeout=30)
            c = conn.cursor()
            c.execute("""INSERT INTO mt_arduino_lock_log
                (lock_id, user_id, session_id, lock_trigger, lock_reason,
                 released_by, released_at, committed_vault_id, eigenflux_panel_ref)
                VALUES(?,?,?,?,?,NULL,NULL,NULL,?)""",
                (lock_id, int(user_id), session_id, lock_trigger, lock_reason,
                 eigenflux_panel_ref))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False


def release_lock_log(lock_id: str, released_by: str,
                     committed_vault_id: Optional[str] = None) -> bool:
    ensure_detect_tables()
    now = _now()
    with _LOCK:
        try:
            conn = sqlite3.connect(APP_DB, timeout=30)
            c = conn.cursor()
            if committed_vault_id:
                c.execute("""UPDATE mt_arduino_lock_log SET released_by=?,
                    released_at=?, committed_vault_id=? WHERE lock_id=?""",
                    (released_by, now, committed_vault_id, lock_id))
            else:
                c.execute("""UPDATE mt_arduino_lock_log SET released_by=?,
                    released_at=? WHERE lock_id=?""",
                    (released_by, now, lock_id))
            ok = c.rowcount > 0
            conn.commit()
            conn.close()
            return ok
        except Exception:
            return False


# ============================================================
# v2.0 AI 干预审计写入 (T23/T24/T25/T26)
# ============================================================
def write_ai_intervention(ai_group_type: str, action_type: str,
                          action_detail: Optional[str] = None,
                          ai_confidence: float = 0,
                          eigenflux_consensus: Optional[float] = None,
                          expert_reviewer_list: Optional[List] = None,
                          ai_employee_id: Optional[str] = None,
                          applied_flag: int = 0) -> str:
    ensure_detect_tables()
    iid = f"ARD-AII-{uuid.uuid4().hex[:12]}"
    now = _now()
    with _LOCK:
        try:
            conn = sqlite3.connect(APP_DB, timeout=30)
            c = conn.cursor()
            experts_json = None
            if expert_reviewer_list:
                experts_json = json.dumps(expert_reviewer_list, ensure_ascii=False)
            c.execute("""INSERT INTO mt_arduino_ai_intervention_log
                (intervention_id, ai_group_type, ai_employee_id, action_type,
                 action_detail, ai_confidence, eigenflux_consensus,
                 expert_reviewer_list, created_at, applied_flag)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (iid, ai_group_type, ai_employee_id, action_type,
                 action_detail, float(ai_confidence or 0), eigenflux_consensus,
                 experts_json, now, int(applied_flag or 0)))
            conn.commit()
            conn.close()
        except Exception:
            pass
    return iid


# ============================================================
# 5. CLI守护
# ============================================================
class DetectDaemon:
    @staticmethod
    def read_pid():
        if not os.path.exists(PID_FILE):
            return None
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            return None

    @staticmethod
    def clear_pid():
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    @staticmethod
    def start():
        existing = DetectDaemon.read_pid()
        if existing:
            print(f"[STATUS] RUNNING pid={existing}")
            return
        ensure_detect_tables()
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        def _term(signum, frame):
            _log("[DAEMON] SIGTERM")
            DetectDaemon.clear_pid()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _term)
        signal.signal(signal.SIGINT, _term)
        _log(f"[DAEMON] START pid={os.getpid()} interval={SCAN_INTERVAL}s")
        scan_devices()
        while True:
            time.sleep(SCAN_INTERVAL)
            try:
                scan_devices()
            except Exception as e:
                _log(f"[DAEMON] ERROR: {e}")

    @staticmethod
    def stop():
        pid = DetectDaemon.read_pid()
        if not pid:
            print("[STATUS] STOPPED")
            return
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        DetectDaemon.clear_pid()
        print("[STATUS] STOPPED")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "start":
        DetectDaemon.start()
    elif cmd == "stop":
        DetectDaemon.stop()
    elif cmd == "scan":
        r = scan_devices()
        print(f"{'='*60}")
        print(f"  Arduino Device Detection Result")
        print(f"{'='*60}")
        print(f"  Ports scanned:    {r['ports_scanned']}")
        print(f"  Arduino ports:     {r['arduino_ports']}")
        print(f"  Devices found:     {r['devices_found']}")
        print(f"  New devices:       {r['new_devices']}")
        print(f"  Updated:           {r['updated']}")
        print(f"  Offline:           {r['removed_devices']}")
        if r["devices"]:
            print(f"{'='*60}")
            print(f"  Connected Devices:")
            for d in r["devices"]:
                print(f"    Port:    {d['port']}")
                print(f"    Board:   {d['board']}")
                print(f"    Chip:    {d['chip']}")
                print(f"    Driver:  {d['driver']} ({d['driver_status']})")
                print(f"    Config:  {d['ide_config']['upload_protocol']} @ {d['ide_config']['upload_speed']}")
                print()
    elif cmd == "status":
        s = get_status()
        print(f"{'='*60}")
        print(f"  Arduino Device Detection Engine")
        print(f"{'='*60}")
        pid = DetectDaemon.read_pid()
        print(f"  Daemon:      {'RUNNING' if pid else 'STOPPED'}  pid={pid or '-'}")
        print(f"  Scan Count:  {s['scan_count']}")
        print(f"  Total:       {s['total_devices']} (connected={s['connected']} offline={s['offline']})")
        print(f"  Driver Issues: {s['driver_issues']}")
        if s["devices"]:
            print(f"{'='*60}")
            print(f"  Connected Devices:")
            for d in s["devices"]:
                print(f"    {d['serial_port']:30s} {d['board_name']:25s} driver={d['driver_type']}({d['driver_status']})")
        if s["last_scan"]:
            ls = s["last_scan"]
            print(f"{'='*60}")
            print(f"  Last Scan: {ls['scanned_at']}")
            print(f"  Ports={ls['ports_scanned']} Found={ls['devices_found']} New={ls['new_devices']}")
    else:
        print(f"  未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
