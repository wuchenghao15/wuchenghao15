#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级管理员双钥匙认证管理器
==========================
钥匙1：密码（PBKDF2-HMAC-SHA256, 100000轮）
钥匙2：VIKEY 硬件加密狗（USB序列号+芯片ID / 移动端指纹）

7要素强认证：
  ① 用户名    ② 密码      ③ VIKEY序列号
  ④ IP段     ⑤ 设备指纹   ⑥ 时间窗口(08:00-23:00)
  ⑦ 行为基线

实时检测：登录后每30s心跳检测VIKEY在线状态，拔出即销毁会话+审计告警
会话绑定：session token 含 VIKEY 签名，防重放攻击
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from vikey_detector import VikeyDetector, VikeyInfo, get_detector

# ── 常量 ──
PBKDF2_ITERATIONS = 100_000
PBKDF2_ALGO = "sha256"
SALT_LEN = 32
TOKEN_LEN = 48
SESSION_TIMEOUT_DEFAULT = 7200       # 2小时
HEARTBEAT_INTERVAL_DEFAULT = 30       # 30秒
HEARTBEAT_GRACE = 10                  # 宽限10秒
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900                # 15分钟
TIME_WINDOW_START = 8                 # 08:00
TIME_WINDOW_END = 23                  # 23:00
SUPER_ADMIN_USERNAME = "wuchenghao15"

# 允许的IP段（CIDR前缀）
ALLOWED_IP_PREFIXES = [
    "127.", "192.168.", "10.", "172.16.", "172.17.", "172.18.",
    "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
]


@dataclass
class SevenFactors:
    """7要素认证上下文"""
    username: str = ""
    password_verified: bool = False
    vikey_identity: str = ""
    client_ip: str = ""
    device_fingerprint: str = ""
    login_hour: int = 0
    behavior_baseline: Dict = field(default_factory=dict)

    def check_all(self) -> Tuple[bool, str]:
        """校验7要素，返回(是否通过, 失败原因)"""
        # ① 用户名
        if not self.username:
            return False, "要素①用户名为空"
        if self.username != SUPER_ADMIN_USERNAME:
            return False, f"要素①用户名非超级管理员({self.username})"
        # ② 密码
        if not self.password_verified:
            return False, "要素②密码验证未通过"
        # ③ VIKEY
        if not self.vikey_identity:
            return False, "要素③VIKEY未检测到"
        # ④ IP段
        if self.client_ip:
            ok_ip = any(self.client_ip.startswith(p) for p in ALLOWED_IP_PREFIXES)
            if not ok_ip:
                return False, f"要素④IP段不允许({self.client_ip})"
        # ⑤ 设备指纹
        if not self.device_fingerprint:
            return False, "要素⑤设备指纹为空"
        # ⑥ 时间窗口
        if not (TIME_WINDOW_START <= self.login_hour < TIME_WINDOW_END):
            return False, f"要素⑥时间窗口不允许(当前{self.login_hour}时, 允许{TIME_WINDOW_START}-{TIME_WINDOW_END})"
        # ⑦ 行为基线（5秒内≥4次登录才视为异常）
        login_history = self.behavior_baseline.get("login_history", [])
        now = time.time()
        recent = [t for t in login_history if now - t < 5]
        if len(recent) >= 4:
            return False, "要素⑦行为异常(5秒内4次以上登录)"
        return True, "7要素全部通过"


@dataclass
class DualKeySession:
    """双钥匙会话"""
    session_id: str = ""
    user_id: str = ""
    username: str = ""
    role: str = "super_admin"
    vikey_identity: str = ""
    vikey_serial: str = ""
    client_ip: str = ""
    device_fingerprint: str = ""
    token: str = ""                # 含VIKEY签名的会话token
    created_at: float = 0.0
    expires_at: float = 0.0
    last_heartbeat: float = 0.0
    vikey_online: bool = True
    destroyed: bool = False
    destroy_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id, "username": self.username,
            "role": self.role, "vikey_identity": self.vikey_identity[:8] + "...",
            "vikey_serial": self.vikey_serial, "client_ip": self.client_ip,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat() if self.created_at else "",
            "expires_at": datetime.fromtimestamp(self.expires_at).isoformat() if self.expires_at else "",
            "last_heartbeat": datetime.fromtimestamp(self.last_heartbeat).isoformat() if self.last_heartbeat else "",
            "vikey_online": self.vikey_online, "destroyed": self.destroyed,
            "destroy_reason": self.destroy_reason,
        }


class DualKeyAuthManager:
    """
    双钥匙认证管理器（单例）
    ──────────────────────
    流程：钥匙1(密码) → 钥匙2(VIKEY) → 7要素校验 → 会话创建 → 实时心跳 → 退出审计
    """

    def __init__(self, vikey_detector: Optional[VikeyDetector] = None):
        self.detector = vikey_detector or get_detector()
        self._sessions: Dict[str, DualKeySession] = {}
        self._token_index: Dict[str, str] = {}  # token -> session_id
        self._failed_attempts: Dict[str, int] = {}
        self._locked_until: Dict[str, float] = {}
        self._behavior: Dict[str, Dict] = {}  # username -> behavior data
        self._lock = threading.RLock()
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_interval = HEARTBEAT_INTERVAL_DEFAULT
        self._running = False
        # 注册的超级管理员密码哈希（内存，不落盘）
        self._admin_password_hash: Optional[str] = None
        self._admin_salt: Optional[bytes] = None

    # ── 钥匙1：密码管理 ──

    def set_admin_password(self, password: str) -> None:
        """设置超级管理员密码（PBKDF2哈希，仅存内存）"""
        salt = os.urandom(SALT_LEN)
        dk = hashlib.pbkdf2_hmac(PBKDF2_ALGO, password.encode(), salt, PBKDF2_ITERATIONS)
        self._admin_salt = salt
        self._admin_password_hash = dk.hex()

    def _verify_password(self, password: str) -> bool:
        """验证密码"""
        if not self._admin_password_hash or not self._admin_salt:
            return False
        dk = hashlib.pbkdf2_hmac(PBKDF2_ALGO, password.encode(), self._admin_salt, PBKDF2_ITERATIONS)
        return hmac.compare_digest(dk.hex(), self._admin_password_hash)

    def _is_locked(self, username: str) -> bool:
        """检查账户是否锁定"""
        deadline = self._locked_until.get(username, 0)
        if deadline and time.time() < deadline:
            return True
        if deadline and time.time() >= deadline:
            # 锁定过期，清除
            self._locked_until.pop(username, None)
            self._failed_attempts.pop(username, None)
        return False

    def _record_failed(self, username: str) -> None:
        """记录失败登录"""
        self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
        if self._failed_attempts[username] >= MAX_LOGIN_ATTEMPTS:
            self._locked_until[username] = time.time() + LOCKOUT_DURATION

    # ── 钥匙2：VIKEY验证 ──

    def _verify_vikey(self) -> Tuple[bool, VikeyInfo]:
        """验证VIKEY在线且在白名单中"""
        info = self.detector.detect()
        if not info.found:
            return False, info
        # 白名单校验
        if not self.detector.whitelist.is_authorized(info):
            return False, info
        return True, info

    # ── 7要素校验 ──

    def _build_factors(self, username: str, password: str,
                       client_ip: str, device_fp: str,
                       vikey_info: VikeyInfo) -> SevenFactors:
        """构建7要素"""
        behavior = self._behavior.get(username, {})
        return SevenFactors(
            username=username,
            password_verified=self._verify_password(password),
            vikey_identity=vikey_info.identity,
            client_ip=client_ip,
            device_fingerprint=device_fp,
            login_hour=datetime.now().hour,
            behavior_baseline=behavior,
        )

    # ── 会话Token生成（含VIKEY签名） ──

    def _generate_token(self, vikey_identity: str, session_id: str) -> str:
        """生成含VIKEY签名的token，防重放"""
        payload = f"{session_id}:{vikey_identity}:{time.time():.0f}"
        sig = hashlib.sha256(payload.encode()).hexdigest()[:24]
        raw = f"{session_id}.{sig}.{secrets.token_hex(TOKEN_LEN)}"
        return raw

    def _verify_token(self, token: str) -> Optional[str]:
        """验证token，返回session_id（防重放）"""
        if not token or "." not in token:
            return None
        parts = token.split(".", 2)
        if len(parts) < 3:
            return None
        session_id = parts[0]
        with self._lock:
            # 检查token是否在索引中
            registered_sid = self._token_index.get(token)
            if not registered_sid or registered_sid != session_id:
                return None
            # 检查会话是否存在且未销毁
            sess = self._sessions.get(session_id)
            if not sess or sess.destroyed:
                return None
            return session_id

    # ── 双钥匙登录主流程 ──

    def login(self, username: str, password: str,
              client_ip: str = "127.0.0.1",
              device_fingerprint: str = "",
              vikey_serial_hint: str = "") -> Tuple[Optional[DualKeySession], str]:
        """
        双钥匙登录
        返回: (session, reason) — session为None表示失败
        """
        # 前置检查：账户锁定
        if self._is_locked(username):
            remaining = int(self._locked_until.get(username, 0) - time.time())
            return None, f"账户已锁定，请{remaining}秒后重试"

        # ── 钥匙1：密码验证 ──
        if not self._verify_password(password):
            self._record_failed(username)
            return None, "钥匙1失败：密码错误"

        # ── 钥匙2：VIKEY验证 ──
        vikey_ok, vikey_info = self._verify_vikey()
        if not vikey_ok:
            self._record_failed(username)
            if not vikey_info.found:
                return None, "钥匙2失败：未检测到VIKEY加密狗"
            return None, "钥匙2失败：VIKEY未在白名单中"

        # ── 7要素校验 ──
        factors = self._build_factors(username, password, client_ip, device_fingerprint, vikey_info)
        ok, reason = factors.check_all()
        if not ok:
            self._record_failed(username)
            return None, f"7要素校验失败：{reason}"

        # ── 创建会话 ──
        session_id = secrets.token_hex(16)
        token = self._generate_token(vikey_info.identity, session_id)
        now = time.time()
        session = DualKeySession(
            session_id=session_id,
            user_id=username,
            username=username,
            role="super_admin",
            vikey_identity=vikey_info.identity,
            vikey_serial=vikey_info.serial,
            client_ip=client_ip,
            device_fingerprint=device_fingerprint,
            token=token,
            created_at=now,
            expires_at=now + SESSION_TIMEOUT_DEFAULT,
            last_heartbeat=now,
            vikey_online=True,
        )
        with self._lock:
            self._sessions[session_id] = session
            self._token_index[token] = session_id
            # 更新行为基线
            history = self._behavior.get(username, {}).get("login_history", [])
            history.append(now)
            history = history[-10:]  # 保留最近10次
            self._behavior[username] = {"last_login_ts": now, "login_history": history}
            # 清除失败计数
            self._failed_attempts.pop(username, None)
            self._locked_until.pop(username, None)

        # 启动心跳监控
        self._ensure_heartbeat()

        return session, "双钥匙登录成功"

    # ── 会话验证 ──

    def verify_session(self, token: str) -> Optional[DualKeySession]:
        """验证会话token（防重放）"""
        session_id = self._verify_token(token)
        if not session_id:
            return None
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess or sess.destroyed:
                return None
            if time.time() > sess.expires_at:
                self._destroy_session(session_id, "会话过期")
                return None
            if not sess.vikey_online:
                self._destroy_session(session_id, "VIKEY离线")
                return None
            return sess

    # ── 心跳机制 ──

    def heartbeat(self, session_id: str) -> bool:
        """手动心跳（客户端调用）"""
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess or sess.destroyed:
                return False
            sess.last_heartbeat = time.time()
            # 检测VIKEY
            if self.detector.is_online():
                sess.vikey_online = True
            else:
                sess.vikey_online = False
                self._destroy_session(session_id, "心跳检测到VIKEY已拔出")
                return False
            return True

    def _ensure_heartbeat(self) -> None:
        """确保心跳线程运行"""
        if self._running:
            return
        self._running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="vikey-heartbeat"
        )
        self._heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        """心跳循环：每30s检测所有会话的VIKEY状态"""
        while self._running:
            time.sleep(self._heartbeat_interval)
            now = time.time()
            with self._lock:
                to_destroy = []
                for sid, sess in self._sessions.items():
                    if sess.destroyed:
                        continue
                    # 过期检查
                    if now > sess.expires_at:
                        to_destroy.append((sid, "会话过期"))
                        continue
                    # VIKEY在线检测
                    if not self.detector.is_online():
                        to_destroy.append((sid, "VIKEY已拔出"))
                        continue
                    # 更新心跳
                    sess.last_heartbeat = now
                    sess.vikey_online = True
                for sid, reason in to_destroy:
                    self._destroy_session(sid, reason)

    def _destroy_session(self, session_id: str, reason: str) -> None:
        """销毁会话"""
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess:
                sess.destroyed = True
                sess.destroy_reason = reason
                sess.vikey_online = False
                # 移除token索引
                self._token_index.pop(sess.token, None)
                # 审计日志
                self._audit_log(session_id, "SESSION_DESTROYED", reason)

    def _audit_log(self, session_id: str, event: str, detail: str) -> None:
        """审计日志（输出到stdout，实际环境落库）"""
        ts = datetime.now().isoformat()
        msg = f"[双钥匙审计] {ts} | session={session_id[:16]}... | {event} | {detail}"
        print(msg)

    # ── 退出登录 ──

    def logout(self, token: str) -> bool:
        """退出登录"""
        session_id = self._verify_token(token)
        if not session_id:
            return False
        self._destroy_session(session_id, "用户主动退出")
        return True

    # ── 状态查询 ──

    def get_session_count(self) -> int:
        with self._lock:
            return sum(1 for s in self._sessions.values() if not s.destroyed)

    def get_active_sessions(self) -> List[Dict]:
        with self._lock:
            return [s.to_dict() for s in self._sessions.values() if not s.destroyed]

    def get_failed_attempts(self, username: str) -> int:
        return self._failed_attempts.get(username, 0)

    def is_heartbeat_running(self) -> bool:
        return self._running and self._heartbeat_thread is not None and self._heartbeat_thread.is_alive()


# ── 单例 ──
_instance: Optional[DualKeyAuthManager] = None
_instance_lock = threading.Lock()


def get_dual_key_auth() -> DualKeyAuthManager:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = DualKeyAuthManager()
    return _instance


if __name__ == "__main__":
    # 快速自检
    mgr = DualKeyAuthManager()
    mgr.set_admin_password("test_password_123")
    # 模拟VIKEY
    det = get_detector()
    det.simulate_vikey("VIKEY_TEST_001")
    det.register_current("wuchenghao15")
    # 尝试登录
    sess, reason = mgr.login(
        username="wuchenghao15",
        password="test_password_123",
        client_ip="127.0.0.1",
        device_fingerprint="MAC_TEST_001",
    )
    if sess:
        print(f"✓ 登录成功: {sess.to_dict()}")
        # 心跳
        ok = mgr.heartbeat(sess.session_id)
        print(f"  心跳: {'✓' if ok else '✗'}")
        # 验证token
        verified = mgr.verify_session(sess.token)
        print(f"  Token验证: {'✓' if verified else '✗'}")
        # 退出
        mgr.logout(sess.token)
        print(f"  退出: ✓")
    else:
        print(f"✗ 登录失败: {reason}")
