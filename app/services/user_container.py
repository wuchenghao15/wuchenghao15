#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户容器 (User Container) 系统
================================
为每个登录用户生成安全容器，包含：
- user_id: 用户唯一标识
- user_group: 用户组别（super_admin / admin / arduino / teacher / student / parent / guest）
- permission_code: 用户权限识别码（加密生成）
- login_status: 登录状态（online / offline / suspended）
- is_anomaly: 是否异常（0/1）
- is_valid: 是否合法（0/1）
- unique_login_timestamp: 唯一登录时间戳
- login_ip: 登录IP
- login_device: 登录设备
- vikey_verified: vikey验证状态
- fingerprint_verified: 指纹验证状态
- expires_at: 容器过期时间
- session_token: 会话令牌
"""

import os
import json
import time
import uuid
import hashlib
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_CONTAINER_DB = os.path.join(_PROJECT_ROOT, "data", "user_containers.db")

VALID_USER_GROUPS = [
    "super_admin",
    "admin",
    "arduino",
    "teacher",
    "student",
    "parent",
    "guest",
    "ai_employee",
    "system",
]

PERMISSION_LEVELS = {
    "super_admin": 99,
    "admin": 80,
    "arduino": 70,
    "teacher": 60,
    "student": 30,
    "parent": 20,
    "guest": 10,
    "ai_employee": 50,
    "system": 100,
}

_container_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.Lock()


def _ensure_data_dir():
    d = os.path.dirname(USER_CONTAINER_DB)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _init_db():
    _ensure_data_dir()
    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_containers (
                session_token TEXT PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                user_group TEXT,
                permission_code TEXT,
                login_status TEXT DEFAULT 'online',
                is_anomaly INTEGER DEFAULT 0,
                is_valid INTEGER DEFAULT 1,
                unique_login_timestamp TEXT,
                login_ip TEXT,
                login_device TEXT,
                vikey_verified INTEGER DEFAULT 0,
                fingerprint_verified INTEGER DEFAULT 0,
                expires_at TEXT,
                created_at TEXT,
                last_active_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_uc_user_id ON user_containers(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_uc_token ON user_containers(session_token)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_uc_group ON user_containers(user_group)
        """)
        conn.commit()


_init_db()


def generate_permission_code(user_id: int, user_group: str, timestamp: str) -> str:
    raw = f"MTSCOS_PERM::{user_id}::{user_group}::{timestamp}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_user_container(
    user_id: int,
    username: str,
    user_group: str,
    login_ip: str = "",
    login_device: str = "",
    vikey_verified: bool = False,
    fingerprint_verified: bool = False,
    ttl_seconds: int = 7200,
) -> Dict[str, Any]:
    now = datetime.now()
    timestamp = now.isoformat()
    expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat()
    session_token = hashlib.sha256(
        f"{uuid.uuid4().hex}::{user_id}::{timestamp}".encode("utf-8")
    ).hexdigest()
    permission_code = generate_permission_code(user_id, user_group, timestamp)

    container = {
        "session_token": session_token,
        "user_id": user_id,
        "username": username,
        "user_group": user_group,
        "permission_code": permission_code,
        "login_status": "online",
        "is_anomaly": 0,
        "is_valid": 1,
        "unique_login_timestamp": timestamp,
        "login_ip": login_ip,
        "login_device": login_device,
        "vikey_verified": 1 if vikey_verified else 0,
        "fingerprint_verified": 1 if fingerprint_verified else 0,
        "expires_at": expires_at,
        "created_at": timestamp,
        "last_active_at": timestamp,
    }

    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO user_containers
               (session_token, user_id, username, user_group, permission_code,
                login_status, is_anomaly, is_valid, unique_login_timestamp,
                login_ip, login_device, vikey_verified, fingerprint_verified,
                expires_at, created_at, last_active_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                session_token, user_id, username, user_group, permission_code,
                "online", 0, 1, timestamp,
                login_ip, login_device,
                1 if vikey_verified else 0,
                1 if fingerprint_verified else 0,
                expires_at, timestamp, timestamp,
            ),
        )
        conn.commit()

    with _cache_lock:
        _container_cache[session_token] = container

    return container


def validate_user_container(session_token: str) -> Dict[str, Any]:
    now = datetime.now()
    with _cache_lock:
        cached = _container_cache.get(session_token)

    container = None
    if cached:
        exp = cached.get("expires_at", "")
        if exp:
            try:
                exp_dt = datetime.fromisoformat(exp)
                if now > exp_dt:
                    container = cached
                    cached["is_valid"] = 0
                    cached["login_status"] = "expired"
                    return {"valid": False, "reason": "容器已过期", "container": cached}
                container = cached
            except Exception:
                container = cached
    else:
        with sqlite3.connect(USER_CONTAINER_DB) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM user_containers WHERE session_token=?",
                (session_token,),
            ).fetchone()
            if row:
                container = dict(row)
                exp = container.get("expires_at", "")
                try:
                    exp_dt = datetime.fromisoformat(exp)
                    if now > exp_dt:
                        container["is_valid"] = 0
                        container["login_status"] = "expired"
                        return {"valid": False, "reason": "容器已过期", "container": container}
                except Exception:
                    pass

    if not container:
        return {"valid": False, "reason": "容器不存在", "container": None}

    if container.get("is_anomaly", 0):
        return {"valid": False, "reason": "账户异常", "container": container}

    if not container.get("is_valid", 0):
        return {"valid": False, "reason": "容器已失效", "container": container}

    return {"valid": True, "reason": None, "container": container}


def update_container_activity(session_token: str) -> bool:
    now = datetime.now().isoformat()
    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        conn.execute(
            "UPDATE user_containers SET last_active_at=? WHERE session_token=?",
            (now, session_token),
        )
        conn.commit()
    with _cache_lock:
        if session_token in _container_cache:
            _container_cache[session_token]["last_active_at"] = now
    return True


def invalidate_container(session_token: str, reason: str = "logout") -> bool:
    now = datetime.now().isoformat()
    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        conn.execute(
            """UPDATE user_containers
               SET is_valid=0, login_status='logged_out', last_active_at=?
               WHERE session_token=?""",
            (now, session_token),
        )
        conn.commit()
    with _cache_lock:
        if session_token in _container_cache:
            del _container_cache[session_token]
    return True


def mark_container_anomaly(session_token: str, reason: str) -> bool:
    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        conn.execute(
            """UPDATE user_containers
               SET is_anomaly=1, login_status='suspended'
               WHERE session_token=?""",
            (session_token,),
        )
        conn.commit()
    with _cache_lock:
        if session_token in _container_cache:
            _container_cache[session_token]["is_anomaly"] = 1
            _container_cache[session_token]["login_status"] = "suspended"
    return True


def get_user_containers(user_id: int) -> List[Dict[str, Any]]:
    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM user_containers WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_containers_by_group(user_group: str) -> List[Dict[str, Any]]:
    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM user_containers WHERE user_group=? AND is_valid=1",
            (user_group,),
        ).fetchall()
        return [dict(r) for r in rows]


def verify_permission_code(session_token: str, expected_group: str = None) -> Dict[str, Any]:
    result = validate_user_container(session_token)
    if not result["valid"]:
        return {"valid": False, "reason": result["reason"]}
    container = result["container"]
    if expected_group and container.get("user_group") != expected_group:
        return {
            "valid": False,
            "reason": f"权限不足：需要{expected_group}，实际{container.get('user_group')}",
        }
    perm_code = generate_permission_code(
        container["user_id"], container["user_group"], container["unique_login_timestamp"]
    )
    if perm_code != container.get("permission_code"):
        return {"valid": False, "reason": "权限码不匹配"}
    return {"valid": True, "container": container}


def require_group(session_token: str, allowed_groups: List[str]) -> Dict[str, Any]:
    result = validate_user_container(session_token)
    if not result["valid"]:
        return {"allowed": False, "reason": result["reason"]}
    container = result["container"]
    user_group = container.get("user_group", "")
    if user_group not in allowed_groups:
        return {
            "allowed": False,
            "reason": f"权限不足：需要 {allowed_groups}，实际 {user_group}",
            "container": container,
        }
    return {"allowed": True, "container": container}


def check_super_admin_access(session_token: str) -> Dict[str, Any]:
    result = require_group(session_token, ["super_admin"])
    if not result.get("allowed"):
        return result
    container = result["container"]
    if not container.get("vikey_verified", 0):
        return {"allowed": False, "reason": "需要vikey硬件认证", "container": container}
    return result


def cleanup_expired_containers():
    now = datetime.now().isoformat()
    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        conn.execute(
            "UPDATE user_containers SET is_valid=0 WHERE expires_at < ? AND is_valid=1",
            (now,),
        )
        conn.commit()


def get_container_stats() -> Dict[str, Any]:
    with sqlite3.connect(USER_CONTAINER_DB) as conn:
        active = conn.execute(
            "SELECT COUNT(*) FROM user_containers WHERE is_valid=1"
        ).fetchone()[0]
        total = conn.execute(
            "SELECT COUNT(*) FROM user_containers"
        ).fetchone()[0]
        anomaly = conn.execute(
            "SELECT COUNT(*) FROM user_containers WHERE is_anomaly=1"
        ).fetchone()[0]
        super_admin = conn.execute(
            "SELECT COUNT(*) FROM user_containers WHERE user_group='super_admin' AND is_valid=1"
        ).fetchone()[0]
        vikey_verified = conn.execute(
            "SELECT COUNT(*) FROM user_containers WHERE vikey_verified=1 AND is_valid=1"
        ).fetchone()[0]
    return {
        "active_containers": active,
        "total_containers": total,
        "anomaly_containers": anomaly,
        "super_admin_sessions": super_admin,
        "vikey_verified_sessions": vikey_verified,
    }
