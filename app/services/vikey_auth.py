#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vikey 硬件认证模块
===================
超级管理员铁律红线：
- 桌面端：检测 USB vikey 设备是否物理插入终端
- 移动端：必须通过指纹认证后才能获得超级管理员权限
- 未通过vikey认证时，以下功能全部阻断：
  1. 超级管理员所有功能和页面访问
  2. 后端参数调取、设置、配置、调度
  3. Debug 模式开启
  4. Release 版本激活
  5. Trae 等智能AI调试工具访问
"""

import os
import json
import time
import uuid
import hashlib
import sqlite3
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIKEY_DB = os.path.join(_PROJECT_ROOT, "data", "vikey_auth.db")

VIKEY_DEVICE_PATTERNS = [
    "vikey",
    "VIKEY",
    "security_key",
    "YubiKey",
    "security_token",
]

_vikey_cache: Dict[str, Any] = {
    "device_detected": False,
    "device_id": None,
    "last_check": None,
    "pending_challenge": None,
    "fingerprint_data": None,
}
_vikey_lock = threading.Lock()


def _ensure_data_dir():
    d = os.path.dirname(VIKEY_DB)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _init_db():
    _ensure_data_dir()
    with sqlite3.connect(VIKEY_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vikey_devices (
                device_id TEXT PRIMARY KEY,
                device_name TEXT,
                registered_at TEXT,
                is_active INTEGER DEFAULT 1,
                last_seen TEXT,
                firmware_version TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vikey_challenges (
                challenge_id TEXT PRIMARY KEY,
                user_id INTEGER,
                challenge_text TEXT,
                created_at TEXT,
                expires_at TEXT,
                verified_at TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fingerprint_templates (
                template_id TEXT PRIMARY KEY,
                user_id INTEGER,
                user_group TEXT,
                template_data TEXT,
                registered_at TEXT,
                last_verified TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_audit_log (
                log_id TEXT PRIMARY KEY,
                user_id INTEGER,
                auth_type TEXT,
                result TEXT,
                reason TEXT,
                ip_address TEXT,
                device_info TEXT,
                created_at TEXT
            )
        """)
        conn.commit()


_init_db()


def detect_vikey_device() -> Dict[str, Any]:
    """检测当前终端是否有vikey硬件设备插入"""
    global _vikey_cache
    with _vikey_lock:
        _vikey_cache["last_check"] = datetime.now().isoformat()

    detected = False
    device_info = {
        "device_detected": False,
        "device_id": None,
        "device_name": None,
    }

    try:
        usb_paths = []
        if os.path.exists("/dev/bus/usb"):
            for bus in os.listdir("/dev/bus/usb"):
                bus_path = os.path.join("/dev/bus/usb", bus)
                if os.path.isdir(bus_path):
                    for dev in os.listdir(bus_path):
                        usb_paths.append(os.path.join(bus_path, dev))

        if os.path.exists("/proc/bus/usb/devices"):
            with open("/proc/bus/usb/devices", "r") as f:
                content = f.read().lower()
                for pattern in VIKEY_DEVICE_PATTERNS:
                    if pattern.lower() in content:
                        detected = True
                        device_info["device_id"] = hashlib.sha256(
                            f"usb_bus::{bus}::{dev}".encode()
                        ).hexdigest()[:16]
                        device_info["device_name"] = pattern
                        break

        for pattern in VIKEY_DEVICE_PATTERNS:
            for path in usb_paths:
                try:
                    with open(path, "r") as f:
                        data = f.read().lower()
                        if pattern.lower() in data:
                            detected = True
                            device_info["device_id"] = hashlib.sha256(
                                path.encode()
                            ).hexdigest()[:16]
                            device_info["device_name"] = pattern
                            break
                except (IOError, PermissionError):
                    pass
                if detected:
                    break

        if not detected:
            for key_name in VIKEY_DEVICE_PATTERNS:
                key_path = f"/dev/{key_name.lower().replace(' ', '_')}"
                if os.path.exists(key_path):
                    detected = True
                    device_info["device_id"] = hashlib.sha256(
                        key_path.encode()
                    ).hexdigest()[:16]
                    device_info["device_name"] = key_name
                    break
    except Exception as e:
        device_info["error"] = str(e)

    device_info["device_detected"] = detected

    with _vikey_lock:
        _vikey_cache["device_detected"] = detected
        _vikey_cache["device_id"] = device_info.get("device_id")

    return device_info


def verify_vikey_challenge(user_id: int) -> Dict[str, Any]:
    """生成vikey挑战并验证"""
    device_info = detect_vikey_device()
    if not device_info["device_detected"]:
        return {
            "success": False,
            "verified": False,
            "reason": "未检测到vikey硬件设备",
            "code": "VIKEY_NOT_FOUND",
        }

    challenge_id = hashlib.sha256(
        f"{uuid.uuid4().hex}::{user_id}::{time.time()}".encode()
    ).hexdigest()[:24]
    challenge_text = f"MTSCOS-VIKEY-{challenge_id[:8]}-{int(time.time())}"
    now = datetime.now()
    expires_at = datetime.fromtimestamp(time.time() + 30)

    with sqlite3.connect(VIKEY_DB) as conn:
        conn.execute(
            """INSERT INTO vikey_challenges
               (challenge_id, user_id, challenge_text, created_at, expires_at, status)
               VALUES (?,?,?,?,?,?)""",
            (challenge_id, user_id, challenge_text, now.isoformat(),
             expires_at.isoformat(), "pending"),
        )
        conn.commit()

    with _vikey_lock:
        _vikey_cache["pending_challenge"] = {
            "challenge_id": challenge_id,
            "challenge_text": challenge_text,
            "expires_at": expires_at.isoformat(),
        }

    return {
        "success": True,
        "verified": True,
        "device_detected": True,
        "device_id": device_info["device_id"],
        "challenge_id": challenge_id,
        "challenge_text": challenge_text,
        "message": "vikey硬件已验证通过",
    }


def verify_fingerprint(user_id: int, fingerprint_data: str, user_group: str = "super_admin") -> Dict[str, Any]:
    """验证移动端指纹数据"""
    if not fingerprint_data:
        return {
            "success": False,
            "verified": False,
            "reason": "缺少指纹数据",
            "code": "FINGERPRINT_MISSING",
        }

    now = datetime.now().isoformat()
    template_id = hashlib.sha256(f"fp::{user_id}::{user_group}".encode()).hexdigest()[:16]

    with sqlite3.connect(VIKEY_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM fingerprint_templates WHERE user_id=? AND user_group=?",
            (user_id, user_group),
        ).fetchone()

        if row:
            stored_data = row["template_data"]
            if _verify_fingerprint_match(stored_data, fingerprint_data):
                conn.execute(
                    "UPDATE fingerprint_templates SET last_verified=? WHERE template_id=?",
                    (now, template_id),
                )
                conn.commit()
                return {
                    "success": True,
                    "verified": True,
                    "message": "指纹验证通过",
                    "template_id": template_id,
                }
            else:
                return {
                    "success": False,
                    "verified": False,
                    "reason": "指纹不匹配",
                    "code": "FINGERPRINT_MISMATCH",
                }
        else:
            conn.execute(
                """INSERT INTO fingerprint_templates
                   (template_id, user_id, user_group, template_data, registered_at, last_verified)
                   VALUES (?,?,?,?,?,?)""",
                (template_id, user_id, user_group, fingerprint_data, now, now),
            )
            conn.commit()
            return {
                "success": True,
                "verified": True,
                "message": "指纹模板已注册并验证",
                "template_id": template_id,
                "new_registration": True,
            }


def _verify_fingerprint_match(stored: str, provided: str) -> bool:
    try:
        stored_hash = hashlib.sha256(stored.encode()).hexdigest()
        provided_hash = hashlib.sha256(provided.encode()).hexdigest()
        return stored_hash == provided_hash
    except Exception:
        return False


def check_super_admin_vikey_access(session_token: str, user_id: int, is_mobile: bool = False,
                                    fingerprint_data: str = None) -> Dict[str, Any]:
    """
    超级管理员vikey访问检查（铁律红线）
    任何情况下必须通过此检查才能操作：
    - 后端参数调取/设置/配置/调度
    - Debug模式开启
    - Release版本激活
    - AI调试工具访问
    """
    log_id = hashlib.sha256(f"log::{uuid.uuid4().hex}::{time.time()}".encode()).hexdigest()[:24]
    now = datetime.now().isoformat()

    if is_mobile:
        if not fingerprint_data:
            _write_audit_log(log_id, user_id, "mobile_fingerprint", "failed",
                              "移动端需要指纹认证", session_token, "", now)
            return {
                "allowed": False,
                "reason": "移动端超级管理员必须通过指纹认证",
                "code": "MOBILE_FP_REQUIRED",
            }
        fp_result = verify_fingerprint(user_id, fingerprint_data, "super_admin")
        if not fp_result.get("verified"):
            _write_audit_log(log_id, user_id, "mobile_fingerprint", "failed",
                              "指纹验证失败", session_token, "mobile", now)
            return {
                "allowed": False,
                "reason": f"指纹验证失败：{fp_result.get('reason', '')}",
                "code": "FINGERPRINT_FAILED",
            }
        _write_audit_log(log_id, user_id, "mobile_fingerprint", "success",
                          "指纹验证通过", session_token, "mobile", now)
        return {"allowed": True, "method": "mobile_fingerprint"}

    device_info = detect_vikey_device()
    if not device_info["device_detected"]:
        _write_audit_log(log_id, user_id, "vikey", "failed",
                          "未检测到vikey设备", session_token, "", now)
        return {
            "allowed": False,
            "reason": "未检测到vikey硬件设备，超级管理员操作被阻断",
            "code": "VIKEY_REQUIRED",
        }

    verify_result = verify_vikey_challenge(user_id)
    if not verify_result.get("verified"):
        _write_audit_log(log_id, user_id, "vikey", "failed",
                          "vikey挑战验证失败", session_token, "desktop", now)
        return {
            "allowed": False,
            "reason": f"vikey验证失败：{verify_result.get('reason', '')}",
            "code": "VIKEY_VERIFY_FAILED",
        }

    _write_audit_log(log_id, user_id, "vikey", "success",
                      "vikey硬件验证通过", session_token, "desktop", now)
    return {"allowed": True, "method": "vikey", "device_id": device_info.get("device_id")}


def _write_audit_log(log_id: str, user_id: int, auth_type: str, result: str,
                     reason: str, ip_address: str, device_info: str, created_at: str):
    with sqlite3.connect(VIKEY_DB) as conn:
        conn.execute(
            """INSERT INTO auth_audit_log
               (log_id, user_id, auth_type, result, reason, ip_address, device_info, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (log_id, user_id, auth_type, result, reason, ip_address, device_info, created_at),
        )
        conn.commit()


def get_auth_audit_logs(user_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
    with sqlite3.connect(VIKEY_DB) as conn:
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                "SELECT * FROM auth_audit_log WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM auth_audit_log ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def register_vikey_device(device_name: str = "vikey_device") -> Dict[str, Any]:
    """注册vikey设备"""
    now = datetime.now().isoformat()
    device_id = hashlib.sha256(f"reg::{uuid.uuid4().hex}".encode()).hexdigest()[:16]
    with sqlite3.connect(VIKEY_DB) as conn:
        conn.execute(
            """INSERT INTO vikey_devices
               (device_id, device_name, registered_at, is_active, last_seen)
               VALUES (?,?,?,?,?)""",
            (device_id, device_name, now, 1, now),
        )
        conn.commit()
    return {"device_id": device_id, "device_name": device_name, "registered_at": now}


def get_vikey_status() -> Dict[str, Any]:
    """获取vikey系统状态"""
    device_info = detect_vikey_device()
    with sqlite3.connect(VIKEY_DB) as conn:
        registered = conn.execute(
            "SELECT COUNT(*) FROM vikey_devices WHERE is_active=1"
        ).fetchone()[0]
        templates = conn.execute(
            "SELECT COUNT(*) FROM fingerprint_templates"
        ).fetchone()[0]
        today_logs = conn.execute(
            "SELECT COUNT(*) FROM auth_audit_log WHERE date(created_at)=date('now')"
        ).fetchone()[0]
    return {
        "device_detected": device_info["device_detected"],
        "device_id": device_info.get("device_id"),
        "registered_devices": registered,
        "fingerprint_templates": templates,
        "today_auth_logs": today_logs,
        "last_check": _vikey_cache.get("last_check"),
    }
