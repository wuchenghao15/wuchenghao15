#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS VIKEY 统一对外封装 API  [v1.0.0]
==========================================
**设计目标**：
  把 vikey_driver.py / vikey_api Blueprint / vikey_enforcement_middleware.py
  / server_real_db.py 中零散的 VIKEY 方法、逻辑、方案、思路、参数、
  底层后端、厂商驱动、锁定/绑定/审计、超级管理员 7 要素强认证等信息全部
  打包封装成一个面向业务、无 Flask 依赖、可独立导入、便于 MTSCOS 统一维护
  且支持被其他项目直接调用的高层 API。

**架构**（Facade 模式，内部委托给 vikey_driver.VikeyDriverManager）：

  ┌────────────────────────────────────────────────────┐
  │                  VikeyAPI (本模块)                  │
  │   设备管理 · 认证 · 密钥 · 运算 · 绑定 · 锁定       │
  │   · 审计日志 · 7 要素强认证 · 业务便捷方法          │
  └───────────────────────┬────────────────────────────┘
                          │ 委托
  ┌───────────────────────▼────────────────────────────┐
  │         VikeyDriverManager / VikeyDevice            │  (vikey_driver.py)
  │   底层 3 大后端：NativeHID / Simulation / USBDrive  │
  └────────────────────────────────────────────────────┘

**对外暴露方式**：
  方式 A：类实例 API
      from core.services.vikey_api import VikeyAPI
      vk = VikeyAPI()
      devices = vk.list_devices()

  方式 B：模块级单例 + 便捷函数（推荐，向后兼容）
      from core.services.vikey_api import (
          get_vikey_api,
          vikey_list_devices, vikey_detect, vikey_is_present,
          vikey_login, vikey_sign, VikeyError, ...
      )
      api = get_vikey_api()

  方式 C：与 vikey_driver.py 同名的兼容函数（无需改老代码）
      from core.services.vikey_api import VikeyFind, VikeyIsPresent, VikeyGetStatus

  方式 D：超级管理员 7 要素强认证（登录/鉴权统一入口）
      from core.services.vikey_api import vikey_super_admin_login_7factor
      result = vikey_super_admin_login_7factor({
          'username': 'wuchenghao15',
          'password': 'xxxx',
          'challenge_code': 'A3F9Z2',
          'usbkey_serial': 'VIDKEY-...',
          'usbkey_pin':   '12345678',
          'ssl_fingerprint': 'sha256:...',
          'hardware_binding': 'machine-...',
          'ip':  request.remote_addr,
          'ua':  request.headers.get('User-Agent'),
      })

**使用示例**（快速上手）：
  # 1. 初始化 & 基础检测
  api = VikeyAPI()
  print(api.get_version_info())
  print(api.health_check())

  # 2. 列设备 + 登录
  devs = api.list_devices()
  if devs:
      token = api.login(devs[0]['serial'], pin='12345678')
      print('session token:', token)

  # 3. 硬件签名
  sig = api.sign(devs[0]['serial'], 'SM2_SIG_01', b'hello')
  ok  = api.verify(devs[0]['serial'], 'SM2_SIG_01',
                   b'hello', sig['signature_b64'])
  print('verify valid:', ok['valid'])

  # 4. 锁定（超级管理员拔出后自动锁定）
  api.lock_system(required_serial=devs[0]['serial'],
                  by_username='wuchenghao15', timeout_sec=300)

**无 Flask 依赖**：
  本模块所有核心 API 均可脱离 Flask 运行；
  只有在 server_real_db.py / Blueprint 中需要用到 session / DB 时，
  才会按需 import 对应数据库路径。
"""

from __future__ import annotations

import os
import sys
import re
import json
import time
import hmac
import base64
import sqlite3
import hashlib
import secrets
import logging
import threading
import traceback
from datetime import datetime, timedelta
from typing import (
    Any, Callable, Dict, Iterable, List, Optional, Tuple, Union,
)

# ============================================================
#  0. 路径准备：确保能正确 import 到 vikey_driver
# ============================================================
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CORE_DIR = os.path.dirname(_THIS_DIR)
_PROJECT_ROOT = os.path.dirname(_CORE_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.services.vikey_driver import (  # noqa: E402  二次封装层复用 vikey_driver
    VikeyBackendInterface,
    VikeyError,
    VikeyDevice,
    VikeyDriverManager,
    auto_select_backend,
    get_vikey_manager as _raw_get_vikey_manager,
    VIKEY_DRIVER_VERSION,
    VIKEY_MANUFACTURER,
    VIKEY_SUPPORT_ALGOS,
    _base64url_encode,
    _base64url_decode,
)

logger = logging.getLogger("vikey_api")

# ============================================================
#  1. 业务层新增常量 & 默认配置（方便其他项目直接引用）
# ============================================================
VIKEY_API_VERSION = "1.0.0"

VIKEY_DEFAULT_PIN = "12345678"
VIKEY_DEFAULT_PUK_SUPER = "88880000"
VIKEY_DEFAULT_PUK_AUDITOR = "00008888"

VIKEY_SUPER_ADMIN_USERNAME = "wuchenghao15"
VIKEY_SUPER_ADMIN_ROLE_HINT = "super_admin"
VIKEY_HW_ADMIN_ROLE_HINT = "hardware_vikey_admin"

# 锁定 & 强认证 默认参数
VIKEY_DEFAULT_LOCK_TIMEOUT = 300  # 秒
VIKEY_FORCE_CHECK_ENABLED_DEFAULT = True
VIKEY_SUPER_ADMIN_REQUIRED_DEFAULT = True
VIKEY_CHECK_INTERVAL_DEFAULT = 2.0  # 秒

# 7 要素认证字段
SEVEN_FACTOR_FIELDS = (
    "username",          # 1. 用户名
    "password",          # 2. 密码
    "challenge_code",    # 3. 随机挑战码
    "usbkey_serial",     # 4. USB Key 序列号
    "usbkey_pin",        # 5. USB Key PIN
    "ssl_fingerprint",   # 6. SSL 指纹
    "hardware_binding",  # 7. 硬件绑定校验
)

# 绑定状态常量
BINDING_STATUS_UNBOUND = "unbound"
BINDING_STATUS_BOUND = "bound"
BINDING_STATUS_REVOKED = "revoked"

# 审计事件类型（统一规范，之前散落各处的 operation 字符串集合）
OP_LOGIN = "login"
OP_LOGOUT = "logout"
OP_LOGIN_7F = "login_7factor"
OP_VERIFY_PIN = "verify_pin"
OP_CHANGE_PIN = "change_pin"
OP_UNBLOCK_PIN = "unblock_pin"
OP_SIGN = "sign"
OP_VERIFY = "verify"
OP_ENCRYPT = "encrypt"
OP_DECRYPT = "decrypt"
OP_HASH = "hash"
OP_HMAC = "hmac"
OP_RANDOM = "random"
OP_BIND = "bind"
OP_UNBIND = "unbind"
OP_UPDATE_BINDING = "update_binding"
OP_LOCK = "lock_system"
OP_UNLOCK = "unlock_system"
OP_GEN_KEYPAIR = "generate_keypair"
OP_IMPORT_CERT = "import_certificate"
OP_EXPORT_CERT = "export_certificate"
OP_DETECT = "detect"
OP_RESET_DEVICE = "reset_device"
OP_SNAPSHOT_SAVE = "snapshot_save"
OP_SNAPSHOT_RESTORE = "snapshot_restore"
OP_SNAPSHOT_RELEASE = "snapshot_release"
OP_CREATE_USB_DONGLE = "create_usb_dongle"


# ============================================================
#  2. 异常增强（业务层语义化异常）
# ============================================================
class VikeySevenFactorError(VikeyError):
    """超级管理员 7 要素强认证失败。"""

    CODE_AUTH_GENERAL = 0xA0000001
    CODE_USERNAME_MISMATCH = 0xA0000002
    CODE_PASSWORD_WRONG = 0xA0000003
    CODE_CHALLENGE_EXPIRED = 0xA0000004
    CODE_CHALLENGE_WRONG = 0xA0000005
    CODE_USBKEY_MISSING = 0xA0000006
    CODE_USBKEY_PIN_WRONG = 0xA0000007
    CODE_SSL_FP_MISMATCH = 0xA0000008
    CODE_HW_BIND_MISMATCH = 0xA0000009
    CODE_USBKEY_NOT_BOUND = 0xA000000A

    ERR_TABLE_EXTRA = {
        CODE_AUTH_GENERAL: "7 要素认证失败",
        CODE_USERNAME_MISMATCH: "用户名不匹配（非超级管理员）",
        CODE_PASSWORD_WRONG: "账号密码错误",
        CODE_CHALLENGE_EXPIRED: "挑战码已过期",
        CODE_CHALLENGE_WRONG: "挑战码错误",
        CODE_USBKEY_MISSING: "USBKey 未插入或未绑定",
        CODE_USBKEY_PIN_WRONG: "USBKey PIN 错误或已锁定",
        CODE_SSL_FP_MISMATCH: "SSL 指纹校验失败",
        CODE_HW_BIND_MISMATCH: "硬件绑定校验失败（更换机器）",
        CODE_USBKEY_NOT_BOUND: "该 USBKey 未绑定到此超级管理员用户",
    }

    def __init__(self, code: int, message: str = "", vendor_code: int = 0):
        base = VikeySevenFactorError.ERR_TABLE_EXTRA.get(code, "未知 7F 错误")
        full = base + (f": {message}" if message else "")
        VikeyError.__init__(self, code, full, vendor_code)


class VikeyBindingError(VikeyError):
    """设备绑定/解绑相关错误。"""
    CODE_ALREADY_BOUND = 0xB0000001
    CODE_NOT_BOUND = 0xB0000002
    CODE_REVOKED = 0xB0000003


class VikeyLockError(VikeyError):
    """系统锁定相关错误。"""
    CODE_ALREADY_LOCKED = 0xC0000001
    CODE_NOT_LOCKED = 0xC0000002
    CODE_TIMEOUT = 0xC0000003


# ============================================================
#  3. 业务 DB 辅助：admin.db / app.db 路径（按需懒加载，避免无 Flask 环境依赖）
# ============================================================
def _resolve_db_path(name: str) -> str:
    """解析数据库路径；优先使用 core.db_path.get_db_path，失败则回退默认路径。"""
    try:
        from core.db_path import get_db_path
        return get_db_path(name)
    except Exception:
        return os.path.join(_PROJECT_ROOT, "data", "databases", name)


def _app_db_path() -> str:
    return _resolve_db_path("app.db")


def _admin_db_path() -> str:
    return _resolve_db_path("admin.db")


def _auth_db_path() -> str:
    return os.path.join(_PROJECT_ROOT, "split_databases", "auth.db")


# ============================================================
#  4. Facade：VikeyAPI —— 统一封装的入口类
# ============================================================
class VikeyAPI:
    """
    Vikey 统一对外 API 封装类（Facade）。

    对外屏蔽：
      - 后端差异（NativeHID / Simulation / USBDrive）
      - VikeyDriverManager / VikeyDevice 之间的切换
      - 数据库（vikey_device_bindings / vikey_operations_log / vikey_device_certs）细节
      - 绑定/锁定/审计/7 要素认证 的具体 SQL 与算法
    """

    # 单例（内部使用）
    _instance: Optional["VikeyAPI"] = None
    _instance_lock = threading.RLock()

    def __init__(
        self,
        backend: Optional[VikeyBackendInterface] = None,
        admin_db: Optional[str] = None,
        app_db: Optional[str] = None,
    ):
        """
        :param backend:   可选自定义后端；None 则走 auto_select_backend()
        :param admin_db:  可选自定义 admin.db 路径；None 则走 core.db_path
        :param app_db:    可选自定义 app.db 路径；None 则走 core.db_path
        """
        self.admin_db = admin_db or _admin_db_path()
        self.app_db = app_db or _app_db_path()

        # 底层驱动管理器（委托所有硬件调用）
        self._mgr: VikeyDriverManager = VikeyDriverManager(
            backend=backend, admin_db=self.admin_db
        )

        # 挑战码内存缓存：{challenge_code: (created_at_ts, expire_at_ts, owner)}
        self._challenge_cache: Dict[str, Tuple[float, float, str]] = {}
        self._challenge_ttl = 60  # 秒，挑战码默认有效期

        # 快照存储：{snapshot_id: {timestamp, data, owner, ...}}
        self._snapshot_store: Dict[str, Dict[str, Any]] = {}

        # 审计写入缓存锁
        self._log_lock = threading.RLock()

    # ------------------------------------------------------------
    #  4.1 单例工厂
    # ------------------------------------------------------------
    @classmethod
    def instance(cls, **kwargs) -> "VikeyAPI":
        """单例入口（全局共享 1 份 VikeyAPI，所有模块统一维护同一实例）。"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """仅用于测试/清理。"""
        with cls._instance_lock:
            cls._instance = None

    # ------------------------------------------------------------
    #  4.2 元数据 / 健康检查
    # ------------------------------------------------------------
    def get_version_info(self) -> Dict[str, Any]:
        """返回版本/厂商/支持算法/当前后端等元数据，便于对外展示或告警。"""
        return {
            "api_version": VIKEY_API_VERSION,
            "driver_version": VIKEY_DRIVER_VERSION,
            "manufacturer": VIKEY_MANUFACTURER,
            "support_algos": list(VIKEY_SUPPORT_ALGOS),
            "backend": getattr(self._mgr.backend, "NAME", type(self._mgr.backend).__name__),
            "project_root": _PROJECT_ROOT,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def health_check(self) -> Dict[str, Any]:
        """
        一键健康体检：驱动是否 OK、有无设备、是否存在超级管理员绑定、系统是否锁定。
        其他项目可以每秒轮询一次作为心跳。
        """
        try:
            devs = self.list_devices(with_binding=True)
            has_sa_key = any(
                (d.get("binding") or {}).get("role_hint") == VIKEY_SUPER_ADMIN_ROLE_HINT
                and d.get("is_present")
                for d in devs
            )
            sa_serial = next(
                (
                    d.get("serial")
                    for d in devs
                    if (d.get("binding") or {}).get("role_hint") == VIKEY_SUPER_ADMIN_ROLE_HINT
                    and d.get("is_present")
                ),
                None,
            )
            return {
                "ok": True,
                "driver_ok": True,
                "device_count": len(devs),
                "devices": devs,
                "has_super_admin_key": has_sa_key,
                "super_admin_serial": sa_serial,
                "lock_state": self.get_lock_state(),
                "version": self.get_version_info(),
            }
        except Exception as e:
            return {
                "ok": False,
                "driver_ok": False,
                "device_count": 0,
                "error": str(e),
                "error_tb": traceback.format_exc(limit=2),
                "lock_state": self._mgr.get_lock_state() if hasattr(self._mgr, "get_lock_state") else None,
                "version": self.get_version_info(),
            }

    # ------------------------------------------------------------
    #  4.3 设备管理
    # ------------------------------------------------------------
    def list_devices(
        self,
        with_binding: bool = True,
        with_keys: bool = False,
        with_certs: bool = False,
        with_status: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        列出所有 USBKey 设备（合并底层枚举 + 绑定 + 状态）。

        :param with_binding: 是否同时查出 vikey_device_bindings 中的绑定信息
        :param with_keys:    是否附带每把 Key 内部密钥列表（需要已登录或支持匿名列表）
        :param with_certs:   是否附带证书列表
        :param with_status:  是否附带登录状态 / PIN 剩余重试 / 存储信息
        :return: List[DeviceDict]，每个字典至少包含 serial/label/manufacturer/is_present 等字段。
        """
        raw = self._mgr.enumerate_devices()
        result: List[Dict[str, Any]] = []
        for d in raw:
            info = dict(d)
            if with_binding:
                info["binding"] = self.get_binding(info.get("serial"))  # type: ignore[arg-type]
            if with_status:
                info["logged_in"] = bool(
                    self._mgr.sessions and any(
                        dev.serial == info.get("serial")
                        for dev in self._mgr.sessions.values()
                    )
                ) or self._mgr.backend.is_logged_in(str(info.get("serial")))
            if with_keys:
                try:
                    info["keys"] = self.list_keys(info["serial"])
                except Exception as e:
                    info["keys_error"] = str(e)
            if with_certs:
                try:
                    info["certificates"] = self.list_certificates(info["serial"])
                except Exception as e:
                    info["certs_error"] = str(e)
            result.append(info)
        return result

    def detect(self) -> Dict[str, Any]:
        """
        对外检测接口：返回设备列表、数量、是否存在超级管理员绑定 Key 等信息。
        等价于 list_devices(with_binding=True) 的精简版。
        """
        devs = self.list_devices(with_binding=True)
        sa_info = next(
            (
                d
                for d in devs
                if d.get("is_present")
                and (d.get("binding") or {}).get("binding_status") == BINDING_STATUS_BOUND
                and (d.get("binding") or {}).get("role_hint") == VIKEY_SUPER_ADMIN_ROLE_HINT
            ),
            None,
        )
        hw_info = next(
            (
                d
                for d in devs
                if d.get("is_present")
                and (d.get("binding") or {}).get("binding_status") == BINDING_STATUS_BOUND
                and (d.get("binding") or {}).get("role_hint") == VIKEY_HW_ADMIN_ROLE_HINT
            ),
            None,
        )
        return {
            "ok": True,
            "count": len(devs),
            "devices": devs,
            "has_super_admin_key": sa_info is not None,
            "super_admin_serial": sa_info["serial"] if sa_info else None,
            "super_admin_username": (sa_info.get("binding") or {}).get("username") if sa_info else None,
            "has_hw_admin_key": hw_info is not None,
            "hw_admin_serial": hw_info["serial"] if hw_info else None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def is_present(self, serial: Optional[str] = None) -> bool:
        """
        便捷判断：
          is_present()          → 任意 VIKEY 插入返回 True
          is_present('XXX')     → 指定序列号设备插入返回 True
        """
        devs = self._mgr.enumerate_devices()
        if serial:
            return any(d["serial"] == serial and d.get("is_present", True) for d in devs)
        return bool(devs)

    def get_device(self, serial: str) -> Optional[Dict[str, Any]]:
        """按序列号取单个设备完整信息。"""
        for d in self.list_devices(with_binding=True, with_status=True):
            if d.get("serial") == serial:
                return d
        return None

    def open(self, serial: str) -> None:
        """打开设备句柄（通常 list_devices 会自动触发；显式用于预热/测试）。"""
        self._mgr.open(serial)

    def close(self, serial: str) -> None:
        self._mgr.close(serial)

    def reset_device(self, serial: str) -> None:
        """软重置：清空登录态 / PIN 计数器。"""
        self._mgr.reset_device(serial)
        self._write_log(serial=serial, operation=OP_RESET_DEVICE, success=1)

    def register_hotplug_handler(self, handler: Callable[[str, str], None]) -> None:
        """
        注册热插拔回调：handler(event_type, serial)
          event_type ∈ {'added', 'removed'}
        """
        self._mgr.register_hotplug_handler(handler)

    def unregister_hotplug_handler(self, handler: Callable[[str, str], None]) -> None:
        self._mgr.unregister_hotplug_handler(handler)

    # ------------------------------------------------------------
    #  4.4 PIN / 认证 / 会话
    # ------------------------------------------------------------
    def login(
        self,
        serial: str,
        pin: str,
        user_type: str = "user",
        ip: Optional[str] = None,
        ua: Optional[str] = None,
        username: Optional[str] = None,
    ) -> str:
        """
        PIN 登录 → 返回 32 字节 session_token（TTL 1800s）。
        成功 / 失败都会写入审计日志。
        """
        try:
            dev = self._mgr.open_session(serial, pin=pin, user_type=user_type)
            tok = dev.session_token or ""
            self._write_log(
                serial=serial, operation=OP_LOGIN, success=1,
                client_ip=ip, user_agent=ua, username=username,
                session_token=tok,
            )
            return tok
        except VikeyError as e:
            self._write_log(
                serial=serial, operation=OP_LOGIN, success=0,
                error_code=e.code, error_message=str(e),
                client_ip=ip, user_agent=ua, username=username,
            )
            raise

    def login_auto_internal(
        self,
        serial: str,
        user_type: str = "user",
        ip: Optional[str] = None,
        ua: Optional[str] = None,
        username: Optional[str] = None,
    ) -> str:
        """自动读取 Key 内部 PIN 登录（仅限受信任场景，如超级管理员硬件登录）。"""
        try:
            dev = self._mgr.open_session_auto(serial, user_type=user_type)
            tok = dev.session_token or ""
            self._write_log(
                serial=serial, operation=OP_LOGIN, success=1,
                client_ip=ip, user_agent=ua, username=username,
                session_token=tok,
                request_json=json.dumps({"auto_internal": True}, ensure_ascii=False),
            )
            return tok
        except VikeyError as e:
            self._write_log(
                serial=serial, operation=OP_LOGIN, success=0,
                error_code=e.code, error_message=str(e),
                client_ip=ip, user_agent=ua, username=username,
            )
            raise

    def ensure_session(self, token: str, serial: Optional[str] = None) -> bool:
        """检查 token 是否仍然有效。"""
        return self._mgr.ensure_session(token, serial) is not None

    def logout(self, token_or_serial: str, ip: Optional[str] = None, ua: Optional[str] = None) -> None:
        """
        退出登录：token 或 serial 任一均可。
        """
        try:
            self._mgr.close_session(token_or_serial)
        except Exception:
            # 可能 token 无效，尝试按 serial 关
            try:
                self._mgr.backend.logout(token_or_serial)
            except Exception:
                pass
        self._write_log(
            serial=token_or_serial if self.is_present(token_or_serial) else "",
            operation=OP_LOGOUT, success=1, session_token=token_or_serial,
            client_ip=ip, user_agent=ua,
        )

    def change_pin(
        self,
        serial: str,
        old_pin: str,
        new_pin: str,
        ip: Optional[str] = None,
        ua: Optional[str] = None,
    ) -> bool:
        try:
            ok = self._mgr.change_pin(serial, old_pin, new_pin)
            self._write_log(serial=serial, operation=OP_CHANGE_PIN, success=1 if ok else 0, client_ip=ip, user_agent=ua)
            return bool(ok)
        except VikeyError as e:
            self._write_log(
                serial=serial, operation=OP_CHANGE_PIN, success=0,
                error_code=e.code, error_message=str(e), client_ip=ip, user_agent=ua,
            )
            raise

    def unblock_pin(
        self,
        serial: str,
        puk: str,
        new_pin: str,
        ip: Optional[str] = None,
        ua: Optional[str] = None,
    ) -> bool:
        try:
            ok = self._mgr.unblock_pin(serial, puk, new_pin)
            self._write_log(serial=serial, operation=OP_UNBLOCK_PIN, success=1 if ok else 0, client_ip=ip, user_agent=ua)
            return bool(ok)
        except VikeyError as e:
            self._write_log(
                serial=serial, operation=OP_UNBLOCK_PIN, success=0,
                error_code=e.code, error_message=str(e), client_ip=ip, user_agent=ua,
            )
            raise

    def is_logged_in(self, serial_or_token: str) -> bool:
        try:
            if self.is_present(serial_or_token):
                return bool(self._mgr.backend.is_logged_in(serial_or_token))
            # 当作 token 查
            dev = self._mgr.sessions.get(serial_or_token)
            return bool(dev and self._mgr.backend.is_logged_in(dev.serial))
        except Exception:
            return False

    # ------------------------------------------------------------
    #  4.5 密钥 / 证书
    # ------------------------------------------------------------
    def list_keys(self, serial: str) -> List[Dict[str, Any]]:
        return self._mgr.list_keys(serial)

    def list_certificates(self, serial: str) -> List[Dict[str, Any]]:
        return self._mgr.list_certificates(serial)

    def export_certificate(self, serial: str, cert_id: str) -> str:
        pem = self._mgr.export_certificate(serial, cert_id)
        self._write_log(serial=serial, operation=OP_EXPORT_CERT, success=1, request_json=json.dumps({"cert_id": cert_id}))
        return pem

    def import_certificate(
        self,
        serial: str,
        cert_id: str,
        pem: str,
        meta: Optional[Dict[str, Any]] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        导入证书：写底层 Key（模拟/真实后端）+ 同步写入 admin.vikey_device_certs 表。
        meta: {subject, issuer, not_before, not_after, algo, fingerprint_sm3}
        """
        meta = meta or {}
        fp = meta.get("fingerprint_sm3") or hashlib.sha256(pem.encode()).hexdigest()
        # 写 DB 表
        try:
            with self._conn_admin() as c:
                c.execute(
                    """
                    INSERT INTO vikey_device_certs
                        (serial, cert_id, cert_pem, fingerprint_sm3, subject, issuer, not_before, not_after, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(serial, cert_id) DO UPDATE SET
                        cert_pem=excluded.cert_pem,
                        fingerprint_sm3=excluded.fingerprint_sm3,
                        subject=excluded.subject,
                        issuer=excluded.issuer,
                        not_before=excluded.not_before,
                        not_after=excluded.not_after,
                        imported_at=excluded.imported_at
                    """,
                    (
                        serial, cert_id, pem, fp,
                        meta.get("subject", ""), meta.get("issuer", ""),
                        meta.get("not_before", ""), meta.get("not_after", ""),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                c.commit()
        except Exception as e:
            logger.warning(f"[vikey_api] import cert db: {e}")
        self._write_log(
            serial=serial, operation=OP_IMPORT_CERT, success=1,
            username=username, request_json=json.dumps({"cert_id": cert_id, "fingerprint": fp}, ensure_ascii=False),
        )
        return {
            "ok": True,
            "serial": serial,
            "cert_id": cert_id,
            "fingerprint_sm3": fp,
            "imported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def generate_keypair(
        self,
        serial: str,
        key_id: str,
        algo: str,
        label: str = "",
        session_token: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        if session_token:
            self._mgr.ensure_session(session_token, serial)
        res = self._mgr.generate_keypair(serial, key_id=key_id, algo=algo, label=label)
        self._write_log(
            serial=serial, operation=OP_GEN_KEYPAIR, success=1,
            key_id=key_id, algo=algo, username=username,
            session_token=session_token,
        )
        return res

    # ------------------------------------------------------------
    #  4.6 密码运算（hash/sign/verify/encrypt/decrypt/hmac/random）
    # ------------------------------------------------------------
    def hash(self, data: bytes, algo: str = "SM3") -> bytes:
        return self._mgr.hash(data, algo)

    def hash_b64(self, data: bytes, algo: str = "SM3") -> str:
        return _base64url_encode(self.hash(data, algo))

    def sign(
        self,
        serial: str,
        key_id: str,
        data: Union[bytes, str],
        hash_algo: str = "SM3",
        session_token: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        if session_token:
            self._mgr.ensure_session(session_token, serial)
        b_data = data.encode("utf-8") if isinstance(data, str) else data
        res = self._mgr.sign(serial=serial, key_id=key_id, data=b_data, hash_algo=hash_algo)
        self._write_log(
            serial=serial, operation=OP_SIGN, success=1,
            key_id=key_id, algo=res.get("algo"), username=username,
            session_token=session_token,
            request_json=json.dumps({"hash_algo": hash_algo, "data_len": len(b_data)}, ensure_ascii=False),
            response_snippet=res.get("signature_b64", "")[:48],
        )
        return res

    def verify(
        self,
        serial: str,
        key_id: str,
        data: Union[bytes, str],
        signature_b64: str,
        hash_algo: str = "SM3",
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        b_data = data.encode("utf-8") if isinstance(data, str) else data
        res = self._mgr.verify(
            serial=serial, key_id=key_id, data=b_data,
            signature_b64=signature_b64, hash_algo=hash_algo,
        )
        self._write_log(
            serial=serial, operation=OP_VERIFY, success=1 if res.get("valid") else 0,
            key_id=key_id, algo=res.get("algo"), username=username,
            request_json=json.dumps({"valid": res.get("valid"), "hash_algo": hash_algo}, ensure_ascii=False),
        )
        return res

    def encrypt(
        self,
        serial: str,
        key_id: str,
        plaintext: Union[bytes, str],
        session_token: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        if session_token:
            self._mgr.ensure_session(session_token, serial)
        b_pt = plaintext.encode("utf-8") if isinstance(plaintext, str) else plaintext
        res = self._mgr.encrypt(serial, key_id, b_pt)
        self._write_log(
            serial=serial, operation=OP_ENCRYPT, success=1,
            key_id=key_id, algo=res.get("algo"), username=username,
            session_token=session_token,
            request_json=json.dumps({"data_len": len(b_pt)}, ensure_ascii=False),
        )
        return res

    def decrypt(
        self,
        serial: str,
        key_id: str,
        nonce_b64: str,
        ciphertext_b64: str,
        session_token: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        if session_token:
            self._mgr.ensure_session(session_token, serial)
        res = self._mgr.decrypt(serial, key_id, nonce_b64, ciphertext_b64)
        self._write_log(
            serial=serial, operation=OP_DECRYPT, success=1,
            key_id=key_id, algo=res.get("algo"), username=username,
            session_token=session_token,
        )
        return res

    def hmac(
        self,
        serial: str,
        key_id: str,
        data: Union[bytes, str],
        hash_algo: str = "SHA256",
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        b_data = data.encode("utf-8") if isinstance(data, str) else data
        res = self._mgr.hmac_mac(serial, key_id, b_data, hash_algo)
        self._write_log(
            serial=serial, operation=OP_HMAC, success=1,
            key_id=key_id, algo=res.get("hash_algo"), username=username,
            request_json=json.dumps({"data_len": len(b_data)}, ensure_ascii=False),
        )
        return res

    def random(
        self,
        serial: str,
        length_bytes: int = 32,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        res = self._mgr.generate_random(serial, length_bytes)
        self._write_log(
            serial=serial, operation=OP_RANDOM, success=1,
            request_json=json.dumps({"length_bytes": length_bytes}, ensure_ascii=False),
            username=username,
        )
        return res

    # ------------------------------------------------------------
    #  4.7 设备-用户绑定
    # ------------------------------------------------------------
    def bind_device(
        self,
        serial: str,
        user_id: Optional[int],
        username: str,
        role_hint: str = "user",
        allowed_operations: Optional[Iterable[str]] = None,
        label: Optional[str] = None,
        remark: Optional[str] = None,
        auth_token: Optional[str] = None,
        op_ip: Optional[str] = None,
        op_ua: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        绑定用户 ↔ USBKey。超级管理员可绑定 role_hint='super_admin'，
        硬件审计员绑定 role_hint='hardware_vikey_admin'，普通用户绑定 'user'。
        """
        allowed_ops = list(allowed_operations) if allowed_operations else ["*"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._conn_admin() as c:
            c.execute(
                """
                INSERT INTO vikey_device_bindings
                    (serial, user_id, username, role_hint, label, binding_status,
                     bound_at, allowed_operations, last_used_at, remark)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(serial) DO UPDATE SET
                    user_id=excluded.user_id,
                    username=excluded.username,
                    role_hint=excluded.role_hint,
                    label=excluded.label,
                    binding_status=excluded.binding_status,
                    bound_at=excluded.bound_at,
                    allowed_operations=excluded.allowed_operations,
                    remark=excluded.remark
                """,
                (
                    serial, user_id, username, role_hint, label or serial,
                    BINDING_STATUS_BOUND, now,
                    json.dumps(allowed_ops, ensure_ascii=False),
                    now, remark or "",
                ),
            )
            # 如果有 auth_token，写进同一张表的字段（server_real_db 逻辑复用）
            try:
                c.execute("ALTER TABLE vikey_device_bindings ADD COLUMN auth_token TEXT DEFAULT ''")
            except Exception:
                pass
            if auth_token:
                c.execute(
                    "UPDATE vikey_device_bindings SET auth_token=? WHERE serial=?",
                    (auth_token, serial),
                )
            c.commit()
        self._write_log(
            serial=serial, operation=OP_BIND, success=1,
            username=username,
            client_ip=op_ip, user_agent=op_ua,
            request_json=json.dumps(
                {"user_id": user_id, "role_hint": role_hint, "label": label},
                ensure_ascii=False,
            ),
        )
        return {
            "ok": True,
            "serial": serial,
            "username": username,
            "role_hint": role_hint,
            "binding_status": BINDING_STATUS_BOUND,
            "bound_at": now,
            "allowed_operations": allowed_ops,
        }

    def unbind_device(
        self,
        serial: str,
        remark: Optional[str] = None,
        op_ip: Optional[str] = None,
        op_ua: Optional[str] = None,
        op_username: Optional[str] = None,
    ) -> bool:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._conn_admin() as c:
            c.execute(
                """UPDATE vikey_device_bindings
                   SET binding_status=?, unbound_at=?, remark=?, auth_token=''
                   WHERE serial=?""",
                (BINDING_STATUS_REVOKED, now, remark or "", serial),
            )
            c.commit()
            changed = c.total_changes > 0
        self._write_log(
            serial=serial, operation=OP_UNBIND, success=1 if changed else 0,
            username=op_username, client_ip=op_ip, user_agent=op_ua,
        )
        return changed

    def get_binding(self, serial: str) -> Optional[Dict[str, Any]]:
        try:
            with self._conn_admin() as c:
                row = c.execute(
                    "SELECT * FROM vikey_device_bindings WHERE serial=? ORDER BY id DESC LIMIT 1",
                    (serial,),
                ).fetchone()
                if not row:
                    return None
                d = dict(row)
                # 解析 JSON
                for k in ("allowed_operations",):
                    v = d.get(k)
                    if isinstance(v, str):
                        try:
                            d[k] = json.loads(v)
                        except Exception:
                            d[k] = ["*"]
                return d
        except Exception:
            return None

    def get_bindings(
        self,
        username: Optional[str] = None,
        role_hint: Optional[str] = None,
        status: Optional[str] = BINDING_STATUS_BOUND,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM vikey_device_bindings WHERE 1=1"
        args: List[Any] = []
        if username:
            sql += " AND username=?"
            args.append(username)
        if role_hint:
            sql += " AND role_hint=?"
            args.append(role_hint)
        if status:
            sql += " AND binding_status=?"
            args.append(status)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(int(limit))
        try:
            with self._conn_admin() as c:
                rows = c.execute(sql, args).fetchall()
                out = []
                for r in rows:
                    d = dict(r)
                    if isinstance(d.get("allowed_operations"), str):
                        try:
                            d["allowed_operations"] = json.loads(d["allowed_operations"])
                        except Exception:
                            d["allowed_operations"] = ["*"]
                    out.append(d)
                return out
        except Exception as e:
            logger.warning(f"[vikey_api] get_bindings: {e}")
            return []

    def update_binding(
        self,
        serial: str,
        op_username: Optional[str] = None,
        op_ip: Optional[str] = None,
        op_ua: Optional[str] = None,
        **fields,
    ) -> Optional[Dict[str, Any]]:
        """
        更新绑定字段，支持字段：
          username, user_id, role_hint, label, remark, allowed_operations, auth_token, last_used_at
        """
        if not fields:
            return self.get_binding(serial)
        cols, vals = [], []
        for k, v in fields.items():
            cols.append(f"{k}=?")
            if k == "allowed_operations" and isinstance(v, (list, tuple, dict)):
                vals.append(json.dumps(v, ensure_ascii=False))
            else:
                vals.append(v)
        sql = f"UPDATE vikey_device_bindings SET {', '.join(cols)} WHERE serial=?"
        vals.append(serial)
        try:
            with self._conn_admin() as c:
                c.execute(sql, vals)
                c.commit()
        except Exception as e:
            logger.warning(f"[vikey_api] update_binding: {e}")
        self._write_log(
            serial=serial, operation=OP_UPDATE_BINDING, success=1,
            username=op_username, client_ip=op_ip, user_agent=op_ua,
            request_json=json.dumps({"fields": list(fields.keys())}, ensure_ascii=False),
        )
        return self.get_binding(serial)

    def touch_binding(self, serial: str) -> None:
        """更新 last_used_at 为当前时间（每次通过校验调用一次）。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._conn_admin() as c:
                c.execute(
                    "UPDATE vikey_device_bindings SET last_used_at=? WHERE serial=?",
                    (now, serial),
                )
                c.commit()
        except Exception:
            pass

    # ------------------------------------------------------------
    #  4.8 系统锁定（超级管理员拔出后自动锁定）
    # ------------------------------------------------------------
    def get_lock_state(self) -> Dict[str, Any]:
        try:
            return dict(self._mgr.get_lock_state())
        except Exception:
            return {
                "locked": False,
                "locked_at": None,
                "required_serial": None,
                "locked_by": None,
                "lock_timeout_seconds": VIKEY_DEFAULT_LOCK_TIMEOUT,
            }

    def lock_system(
        self,
        required_serial: Optional[str] = None,
        by_username: Optional[str] = None,
        timeout_sec: Optional[int] = None,
        snapshot: Optional[Dict[str, Any]] = None,
        op_ip: Optional[str] = None,
        op_ua: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        业务层显式锁定；required_serial 指定只有重新插入该 Key 才能解锁。
        """
        state = self.get_lock_state()
        if state.get("locked"):
            raise VikeyLockError(VikeyLockError.CODE_ALREADY_LOCKED, str(state.get("locked_at")))
        timeout = int(timeout_sec or VIKEY_DEFAULT_LOCK_TIMEOUT)
        try:
            self._mgr.set_lock_timeout(timeout)
            locked = self._mgr.lock_system(
                required_serial=required_serial,
                by_username=by_username or VIKEY_SUPER_ADMIN_USERNAME,
                snapshot_data=snapshot,
            )
        except Exception as e:
            logger.warning(f"[vikey_api] lock_system fallback: {e}")
            # 某些模拟后端没有 lock_system：本地维护一份 lock_state
            self._mgr._lock_state = {
                "locked": True,
                "locked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "required_serial": required_serial,
                "locked_by": by_username or VIKEY_SUPER_ADMIN_USERNAME,
                "lock_timeout_seconds": timeout,
                "snapshot_data": snapshot,
            }
            locked = True
        self._write_log(
            serial=required_serial or "", operation=OP_LOCK, success=1 if locked else 0,
            username=by_username, client_ip=op_ip, user_agent=op_ua,
            request_json=json.dumps({"timeout_sec": timeout}, ensure_ascii=False),
        )
        return self.get_lock_state()

    def unlock_system(
        self,
        serial: Optional[str] = None,
        op_ip: Optional[str] = None,
        op_ua: Optional[str] = None,
        op_username: Optional[str] = None,
    ) -> Dict[str, Any]:
        state = self.get_lock_state()
        if not state.get("locked"):
            raise VikeyLockError(VikeyLockError.CODE_NOT_LOCKED)
        required = state.get("required_serial")
        if required and serial and required != serial:
            raise VikeyLockError(
                VikeyLockError.CODE_NOT_LOCKED,
                f"系统由 Key={required} 锁定，请插入对应 Key",
            )
        try:
            unlocked = self._mgr.unlock_system(serial)
        except Exception as e:
            logger.warning(f"[vikey_api] unlock fallback: {e}")
            self._mgr._lock_state["locked"] = False
            unlocked = True
        self._write_log(
            serial=serial or required or "", operation=OP_UNLOCK, success=1 if unlocked else 0,
            username=op_username, client_ip=op_ip, user_agent=op_ua,
        )
        return self.get_lock_state()

    def set_lock_timeout(self, seconds: int) -> None:
        self._mgr.set_lock_timeout(int(seconds))

    # ------------------------------------------------------------
    #  4.9 快照（锁定前保存会话状态，解锁后恢复）
    # ------------------------------------------------------------
    def save_snapshot(
        self,
        data: Dict[str, Any],
        owner: Optional[str] = None,
        ttl_seconds: int = 3600,
        op_ip: Optional[str] = None,
        op_ua: Optional[str] = None,
    ) -> str:
        snap_id = _base64url_encode(secrets.token_bytes(16))
        self._snapshot_store[snap_id] = {
            "id": snap_id,
            "created_at": time.time(),
            "expire_at": time.time() + ttl_seconds,
            "owner": owner or VIKEY_SUPER_ADMIN_USERNAME,
            "data": dict(data),
        }
        self._write_log(
            serial="", operation=OP_SNAPSHOT_SAVE, success=1,
            username=owner, client_ip=op_ip, user_agent=op_ua,
            request_json=json.dumps({"snapshot_id": snap_id, "ttl": ttl_seconds}, ensure_ascii=False),
        )
        return snap_id

    def restore_snapshot(self, snap_id: str) -> Optional[Dict[str, Any]]:
        s = self._snapshot_store.get(snap_id)
        if not s:
            return None
        if s["expire_at"] < time.time():
            self._snapshot_store.pop(snap_id, None)
            return None
        self._write_log(serial="", operation=OP_SNAPSHOT_RESTORE, success=1,
                        username=s.get("owner"),
                        request_json=json.dumps({"snapshot_id": snap_id}, ensure_ascii=False))
        return s.get("data")

    def release_snapshot(self, snap_id: str) -> bool:
        ok = self._snapshot_store.pop(snap_id, None) is not None
        self._write_log(
            serial="", operation=OP_SNAPSHOT_RELEASE, success=1 if ok else 0,
            request_json=json.dumps({"snapshot_id": snap_id}, ensure_ascii=False),
        )
        return ok

    # ------------------------------------------------------------
    #  4.10 审计 & 日志
    # ------------------------------------------------------------
    def _conn_admin(self):
        os.makedirs(os.path.dirname(self.admin_db), exist_ok=True)
        c = sqlite3.connect(self.admin_db)
        c.row_factory = sqlite3.Row
        return c

    def _write_log(
        self,
        serial: str,
        operation: str,
        success: int = 1,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        session_token: Optional[str] = None,
        key_id: Optional[str] = None,
        algo: Optional[str] = None,
        error_code: Optional[int] = None,
        error_message: Optional[str] = None,
        request_json: Optional[str] = None,
        response_snippet: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[int]:
        """统一下沉写审计日志；其他项目无需关心表结构。"""
        try:
            with self._log_lock, self._conn_admin() as c:
                c.execute(
                    """
                    INSERT INTO vikey_operations_log
                        (timestamp, serial, user_id, username, session_token, operation,
                         key_id, algo, success, error_code, error_message,
                         request_json, response_snippet, client_ip, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        serial, user_id, username, session_token, operation,
                        key_id, algo, int(success), error_code,
                        (error_message or "")[:500],
                        (request_json or "")[:4000],
                        (response_snippet or "")[:512],
                        (client_ip or "")[:64],
                        (user_agent or "")[:255],
                    ),
                )
                c.commit()
                return c.execute("SELECT last_insert_rowid()").fetchone()[0]
        except Exception as e:
            logger.warning(f"[vikey_api] write_log: {e}")
            return None

    def query_logs(
        self,
        serial: Optional[str] = None,
        username: Optional[str] = None,
        operation: Optional[str] = None,
        start: Optional[str] = None,  # 'YYYY-MM-DD HH:MM:SS'
        end: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM vikey_operations_log WHERE 1=1"
        args: List[Any] = []
        if serial:
            sql += " AND serial=?"
            args.append(serial)
        if username:
            sql += " AND username=?"
            args.append(username)
        if operation:
            sql += " AND operation=?"
            args.append(operation)
        if start:
            sql += " AND timestamp>=?"
            args.append(start)
        if end:
            sql += " AND timestamp<=?"
            args.append(end)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(int(limit))
        try:
            with self._conn_admin() as c:
                return [dict(r) for r in c.execute(sql, args).fetchall()]
        except Exception as e:
            logger.warning(f"[vikey_api] query_logs: {e}")
            return []

    def get_stats(
        self,
        period: str = "today",
    ) -> Dict[str, Any]:
        """
        审计统计：period ∈ {today, last_7d, last_30d, all}
        """
        now = datetime.now()
        if period == "today":
            start = now.strftime("%Y-%m-%d 00:00:00")
        elif period == "last_7d":
            start = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        elif period == "last_30d":
            start = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
        else:
            start = None
        sql = "SELECT operation, success, COUNT(*) as cnt FROM vikey_operations_log"
        args: List[Any] = []
        if start:
            sql += " WHERE timestamp>=?"
            args.append(start)
        sql += " GROUP BY operation, success"
        data: Dict[str, Any] = {
            "period": period,
            "total": 0,
            "success": 0,
            "fail": 0,
            "by_operation": {},
        }
        try:
            with self._conn_admin() as c:
                rows = c.execute(sql, args).fetchall()
                for r in rows:
                    op = r["operation"]
                    cnt = r["cnt"] or 0
                    data["total"] += cnt
                    if r["success"]:
                        data["success"] += cnt
                    else:
                        data["fail"] += cnt
                    data["by_operation"].setdefault(op, {"total": 0, "success": 0, "fail": 0})
                    if r["success"]:
                        data["by_operation"][op]["success"] += cnt
                    else:
                        data["by_operation"][op]["fail"] += cnt
                    data["by_operation"][op]["total"] += cnt
        except Exception as e:
            logger.warning(f"[vikey_api] get_stats: {e}")
        return data

    def cleanup_logs(self, days: int = 90) -> int:
        """清理 N 天前的旧日志（运维接口）。"""
        cutoff = (datetime.now() - timedelta(days=max(1, int(days)))).strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._conn_admin() as c:
                c.execute("DELETE FROM vikey_operations_log WHERE timestamp<?", (cutoff,))
                c.commit()
                return c.total_changes or 0
        except Exception as e:
            logger.warning(f"[vikey_api] cleanup_logs: {e}")
            return 0

    # ------------------------------------------------------------
    #  4.11 挑战码（7 要素强认证要素 #3）
    # ------------------------------------------------------------
    def generate_challenge_code(
        self,
        owner: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        length: int = 6,
    ) -> str:
        """
        生成随机挑战码（数字+大写字母，默认 6 位）。
        内存 TTL：默认 60s；返回生成的挑战码字符串。
        """
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(max(4, int(length))))
            if code not in self._challenge_cache:
                break
        ttl = int(ttl_seconds or self._challenge_ttl)
        now = time.time()
        self._challenge_cache[code] = (now, now + ttl, owner or "")
        return code

    def verify_challenge_code(
        self,
        code: str,
        owner: Optional[str] = None,
        consume: bool = True,
    ) -> Tuple[bool, str]:
        """
        校验挑战码。返回 (ok, reason)
        """
        code = (code or "").strip().upper()
        if not code or code not in self._challenge_cache:
            return False, "challenge_not_found"
        created_at, expire_at, cached_owner = self._challenge_cache[code]
        if time.time() > expire_at:
            self._challenge_cache.pop(code, None)
            return False, "challenge_expired"
        if owner and cached_owner and str(cached_owner).lower() != str(owner).lower():
            return False, "challenge_owner_mismatch"
        if consume:
            self._challenge_cache.pop(code, None)
        return True, "ok"

    # ------------------------------------------------------------
    #  4.12 SSL 指纹 & 硬件绑定（7 要素 #6、#7 计算与校验）
    # ------------------------------------------------------------
    @staticmethod
    def compute_ssl_fingerprint(
        pem_or_cert: Optional[Union[str, bytes]] = None,
        algo: str = "sha256",
    ) -> str:
        """
        计算 SSL 证书指纹。若未传证书，计算本机服务端 SSL 配置指纹（通常生产由 Nginx/Flask
        运行时注入；这里默认用项目根目录的标识性内容作为替代指纹的默认算法）。
        """
        fn = hashlib.sha256 if algo.lower() in ("sha256", "sha-256") else hashlib.sha1
        if pem_or_cert:
            raw = pem_or_cert.encode() if isinstance(pem_or_cert, str) else pem_or_cert
            h = fn(raw).hexdigest()
        else:
            # 兜底：项目版本文件 + VERSION 文件内容哈希作为"环境指纹"
            mix = _PROJECT_ROOT.encode() + b"|" + VIKEY_DRIVER_VERSION.encode()
            try:
                vf = os.path.join(_PROJECT_ROOT, "VERSION")
                if os.path.exists(vf):
                    with open(vf, "rb") as f:
                        mix += b"|" + f.read()
            except Exception:
                pass
            h = fn(mix).hexdigest()
        return f"{algo.lower()}:{h}"

    @staticmethod
    def compute_hardware_binding_hash(
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        计算硬件绑定指纹：组合 MAC + 机器名 + CPU 信息 + 项目根路径哈希。
        相同硬件多次计算结果一致；换机器则不同。
        """
        parts: List[str] = []
        try:
            import uuid
            parts.append(str(uuid.getnode()))  # MAC（第一个网卡的）
        except Exception:
            parts.append("no-mac")
        try:
            import socket
            parts.append(socket.gethostname())
        except Exception:
            parts.append("no-hostname")
        try:
            import platform
            parts.append(platform.platform())
            parts.append(platform.machine())
            parts.append(platform.processor())
        except Exception:
            pass
        parts.append(_PROJECT_ROOT)
        if extra:
            parts.append(json.dumps(extra, sort_keys=True, ensure_ascii=False))
        raw = "|".join(parts).encode("utf-8")
        return "machine-" + hashlib.sha256(raw).hexdigest()[:32]

    # ------------------------------------------------------------
    #  4.13 核心：超级管理员 7 要素强认证
    # ------------------------------------------------------------
    def verify_super_admin_7factor(
        self,
        auth: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        超级管理员 7 要素强认证（项目级统一入口）。

        :param auth: dict，字段：
            username         (1) 必填 'wuchenghao15'
            password         (2) 必填：用户密码（原文或 bcrypt/sha256 哈希；内部会查 split_databases/auth.db.users.password）
            challenge_code   (3) 必填：随机挑战码（已由 generate_challenge_code 生成）
            usbkey_serial    (4) 必填：USBKey 序列号
            usbkey_pin       (5) 必填：USBKey PIN
            ssl_fingerprint  (6) 必填：客户端 SSL 指纹（由 compute_ssl_fingerprint 计算得到）
            hardware_binding (7) 必填：硬件绑定指纹（由 compute_hardware_binding_hash 计算得到）
            ip               审计用
            ua               审计用
            consume_challenge=True  是否一次性消耗挑战码（默认 True）
            skip_password_check=False 仅在特殊受信任内部场景可设为 True（其他项目调用不建议）
        :return: dict{ok:bool, reason:str, session_token:str, device_info:dict, login_at:str}

        所有失败均抛出 VikeySevenFactorError，便于外层区分处理。
        """
        ip = str(auth.get("ip") or "")[:64]
        ua = str(auth.get("ua") or "")[:255]
        username = str(auth.get("username") or "").strip()
        password = str(auth.get("password") or "")
        challenge = str(auth.get("challenge_code") or "").strip()
        serial = str(auth.get("usbkey_serial") or "").strip()
        pin = str(auth.get("usbkey_pin") or "")
        ssl_fp = str(auth.get("ssl_fingerprint") or "").strip()
        hw_bind = str(auth.get("hardware_binding") or "").strip()

        def _log_fail(code: int, msg: str) -> Dict[str, Any]:
            self._write_log(
                serial=serial, operation=OP_LOGIN_7F, success=0,
                error_code=code, error_message=msg,
                username=username, client_ip=ip, user_agent=ua,
            )
            raise VikeySevenFactorError(code, msg)

        # 要素 1：用户名必须是超级管理员
        if username.lower() != VIKEY_SUPER_ADMIN_USERNAME.lower():
            return _log_fail(
                VikeySevenFactorError.CODE_USERNAME_MISMATCH,
                f"got username={username!r}",
            )

        # 要素 2：密码校验（查 split_databases/auth.db → users）
        if not auth.get("skip_password_check"):
            pw_ok = self._verify_user_password(username, password)
            if not pw_ok:
                return _log_fail(
                    VikeySevenFactorError.CODE_PASSWORD_WRONG,
                    "password mismatch (auth.db/users)",
                )

        # 要素 3：挑战码校验
        consume = bool(auth.get("consume_challenge", True))
        c_ok, c_reason = self.verify_challenge_code(
            challenge, owner=username, consume=consume,
        )
        if not c_ok:
            code = (
                VikeySevenFactorError.CODE_CHALLENGE_EXPIRED
                if c_reason == "challenge_expired"
                else VikeySevenFactorError.CODE_CHALLENGE_WRONG
            )
            return _log_fail(code, c_reason)

        # 要素 4：USBKey 真实插入
        if not self.is_present(serial):
            return _log_fail(
                VikeySevenFactorError.CODE_USBKEY_MISSING,
                f"serial={serial!r} not present",
            )

        # 要素 4.5：该 USBKey 必须已绑定到此超级管理员
        binding = self.get_binding(serial)
        if (
            not binding
            or binding.get("binding_status") != BINDING_STATUS_BOUND
            or str(binding.get("username") or "").lower() != username.lower()
            or (binding.get("role_hint") or "") not in (
                VIKEY_SUPER_ADMIN_ROLE_HINT,
                VIKEY_HW_ADMIN_ROLE_HINT,
            )
        ):
            return _log_fail(
                VikeySevenFactorError.CODE_USBKEY_NOT_BOUND,
                f"binding={binding!r}",
            )

        # 要素 5：PIN 登录（同时生成 session_token）
        try:
            session_token = self.login(
                serial=serial, pin=pin, user_type="admin",
                ip=ip, ua=ua, username=username,
            )
        except VikeyError as e:
            return _log_fail(
                VikeySevenFactorError.CODE_USBKEY_PIN_WRONG,
                f"pin verify failed: {e.code:08X}",
            )

        # 要素 6：SSL 指纹
        expected_ssl = self.compute_ssl_fingerprint()
        if ssl_fp and ssl_fp != expected_ssl:
            # 允许客户端传 None（纯 HTTP 调试时），但非空则必须严格匹配
            return _log_fail(
                VikeySevenFactorError.CODE_SSL_FP_MISMATCH,
                f"expected={expected_ssl[:32]}... got={ssl_fp[:32]}...",
            )

        # 要素 7：硬件绑定
        expected_hw = self.compute_hardware_binding_hash()
        if hw_bind and hw_bind != expected_hw:
            return _log_fail(
                VikeySevenFactorError.CODE_HW_BIND_MISMATCH,
                f"expected={expected_hw[:16]}... got={hw_bind[:16]}...",
            )

        # 7 要素全部通过：写入审计、更新 last_used_at、返回 session
        self.touch_binding(serial)
        # 更新绑定表 auth_token，方便 server_real_db 复用
        self.update_binding(serial, auth_token=session_token,
                            op_username=username, op_ip=ip, op_ua=ua)
        device_info = self.get_device(serial) or {}
        self._write_log(
            serial=serial, operation=OP_LOGIN_7F, success=1,
            username=username, client_ip=ip, user_agent=ua,
            session_token=session_token,
            request_json=json.dumps(
                {"challenge_code_len": len(challenge),
                 "ssl_fp_match": bool(not ssl_fp or ssl_fp == expected_ssl),
                 "hw_match": bool(not hw_bind or hw_bind == expected_hw)},
                ensure_ascii=False,
            ),
        )
        return {
            "ok": True,
            "reason": "ok",
            "session_token": session_token,
            "device_info": device_info,
            "binding_info": binding,
            "login_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ssl_fingerprint": expected_ssl,
            "hardware_binding": expected_hw,
        }

    # ------------------------------------------------------------
    #  4.14 内部辅助：账号密码校验（查 auth.db/users，兼容老哈希方式）
    # ------------------------------------------------------------
    def _verify_user_password(self, username: str, password: str) -> bool:
        """
        校验账号密码；兼容 server_real_db.py 中多种密码存储方式：
          - bcrypt    $2b$ / $2a$ 开头
          - pbkdf2    pbkdf2_sha256$... 开头
          - 双 SHA-256 盐（MTSCOS 历史遗留）sha256$salt$hash
          - 纯 sha256 无盐
          - 明文 fallback（仅在数据库中未存哈希时兜底对比）
        """
        if not username or not password:
            return False
        auth_db = _auth_db_path()
        row = None
        try:
            if os.path.exists(auth_db):
                with sqlite3.connect(auth_db) as c:
                    c.row_factory = sqlite3.Row
                    row = c.execute(
                        "SELECT * FROM users WHERE username=? OR LOWER(username)=? LIMIT 1",
                        (username, username.lower()),
                    ).fetchone()
        except Exception:
            row = None
        if row is None:
            # 回退 app.db
            try:
                with sqlite3.connect(self.app_db) as c:
                    c.row_factory = sqlite3.Row
                    row = c.execute(
                        "SELECT * FROM users WHERE username=? OR LOWER(username)=? LIMIT 1",
                        (username, username.lower()),
                    ).fetchone()
            except Exception:
                return False
        if not row:
            return False
        stored = str(dict(row).get("password") or "")
        # bcrypt
        if stored.startswith(("$2b$", "$2a$", "$2y$")):
            try:
                import bcrypt  # type: ignore
                return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
            except Exception:
                return False
        # pbkdf2
        if stored.startswith("pbkdf2"):
            try:
                parts = stored.split("$")
                _name, _iter, salt, digest = parts[0], int(parts[1]), parts[2], parts[3]
                actual = hashlib.pbkdf2_hmac(
                    "sha256", password.encode(), salt.encode("ascii"), _iter,
                    dklen=len(base64.b64decode(digest + "==")),
                )
                return hmac.compare_digest(base64.b64encode(actual).rstrip(b"=").decode(), digest)
            except Exception:
                return False
        # sha256$salt$hash
        if stored.count("$") == 2 and stored.startswith("sha256$"):
            try:
                _prefix, salt, expected = stored.split("$", 2)
                actual = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
                return hmac.compare_digest(actual, expected)
            except Exception:
                return False
        # 纯 sha256（64 位 hex）
        if re.fullmatch(r"[0-9a-fA-F]{64}", stored):
            return hmac.compare_digest(
                hashlib.sha256(password.encode("utf-8")).hexdigest(), stored.lower(),
            )
        # 明文兜底（仅在没有哈希结构时使用；历史上 admin123 等）
        return stored == password

    # ------------------------------------------------------------
    #  4.15 U盘制作 & 兼容：直接暴露底层 USB 后端
    # ------------------------------------------------------------
    def create_usb_dongle(
        self,
        drive_path: str,
        role_hint: str = "user",
        pin: str = VIKEY_DEFAULT_PIN,
        puk: str = VIKEY_DEFAULT_PUK_SUPER,
        label: Optional[str] = None,
        storage_kb: int = 128,
        op_username: Optional[str] = None,
        op_ip: Optional[str] = None,
        op_ua: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        把普通 U 盘制作成 VIKEY 加密狗。
        委托给底层 VikeyUSBDriveBackend.create_usb_dongle()。
        """
        from core.services.vikey_driver import VikeyUSBDriveBackend
        be = VikeyUSBDriveBackend()
        res = be.create_usb_dongle(
            drive_path=drive_path, role_hint=role_hint,
            pin=pin, puk=puk, label=label, storage_kb=storage_kb,
        )
        serial = res.get("serial") or ""
        self._write_log(
            serial=serial, operation=OP_CREATE_USB_DONGLE, success=1,
            username=op_username, client_ip=op_ip, user_agent=op_ua,
            request_json=json.dumps(
                {"drive": drive_path, "role_hint": role_hint, "storage_kb": storage_kb},
                ensure_ascii=False,
            ),
        )
        return res

    # ------------------------------------------------------------
    #  4.16 与 vikey_driver 兼容的便捷属性
    # ------------------------------------------------------------
    @property
    def backend_name(self) -> str:
        return getattr(self._mgr.backend, "NAME", type(self._mgr.backend).__name__)

    @property
    def manager(self) -> VikeyDriverManager:
        """
        向后兼容：暴露底层 VikeyDriverManager。
        ⚠️ 其他项目调用时，优先使用 VikeyAPI 上的方法；
           仅在需要热插拔高级配置等场景再访问 manager。
        """
        return self._mgr


# ============================================================
#  5. 模块级单例 & 便捷函数（推荐所有项目直接用这些入口）
# ============================================================
_global_api: Optional[VikeyAPI] = None
_global_api_lock = threading.RLock()


def get_vikey_api(**kwargs) -> VikeyAPI:
    """
    全局单例入口（项目内所有模块统一维护同一个 VikeyAPI 实例，避免 DB/锁冲突）。
    """
    global _global_api
    if _global_api is None:
        with _global_api_lock:
            if _global_api is None:
                _global_api = VikeyAPI(**kwargs)
    return _global_api


def reset_vikey_api_instance() -> None:
    global _global_api
    with _global_api_lock:
        _global_api = None


# 全部便捷函数（对应 VikeyAPI 的方法，一一映射）
def vikey_get_version_info() -> Dict[str, Any]:
    return get_vikey_api().get_version_info()


def vikey_health_check() -> Dict[str, Any]:
    return get_vikey_api().health_check()


def vikey_list_devices(**kwargs) -> List[Dict[str, Any]]:
    return get_vikey_api().list_devices(**kwargs)


def vikey_detect() -> Dict[str, Any]:
    return get_vikey_api().detect()


def vikey_is_present(serial: Optional[str] = None) -> bool:
    return get_vikey_api().is_present(serial)


def vikey_get_device(serial: str) -> Optional[Dict[str, Any]]:
    return get_vikey_api().get_device(serial)


def vikey_login(serial: str, pin: str, **kwargs) -> str:
    return get_vikey_api().login(serial=serial, pin=pin, **kwargs)


def vikey_login_auto_internal(serial: str, **kwargs) -> str:
    return get_vikey_api().login_auto_internal(serial=serial, **kwargs)


def vikey_ensure_session(token: str, serial: Optional[str] = None) -> bool:
    return get_vikey_api().ensure_session(token, serial)


def vikey_logout(token_or_serial: str, **kwargs) -> None:
    get_vikey_api().logout(token_or_serial, **kwargs)


def vikey_change_pin(serial: str, old_pin: str, new_pin: str, **kwargs) -> bool:
    return get_vikey_api().change_pin(serial, old_pin, new_pin, **kwargs)


def vikey_unblock_pin(serial: str, puk: str, new_pin: str, **kwargs) -> bool:
    return get_vikey_api().unblock_pin(serial, puk, new_pin, **kwargs)


def vikey_is_logged_in(serial_or_token: str) -> bool:
    return get_vikey_api().is_logged_in(serial_or_token)


def vikey_list_keys(serial: str) -> List[Dict[str, Any]]:
    return get_vikey_api().list_keys(serial)


def vikey_list_certificates(serial: str) -> List[Dict[str, Any]]:
    return get_vikey_api().list_certificates(serial)


def vikey_export_certificate(serial: str, cert_id: str) -> str:
    return get_vikey_api().export_certificate(serial, cert_id)


def vikey_import_certificate(serial: str, cert_id: str, pem: str, **kwargs) -> Dict[str, Any]:
    return get_vikey_api().import_certificate(serial, cert_id, pem, **kwargs)


def vikey_generate_keypair(serial: str, key_id: str, algo: str, **kwargs) -> Dict[str, Any]:
    return get_vikey_api().generate_keypair(serial, key_id=key_id, algo=algo, **kwargs)


def vikey_hash(data: bytes, algo: str = "SM3") -> bytes:
    return get_vikey_api().hash(data, algo)


def vikey_hash_b64(data: bytes, algo: str = "SM3") -> str:
    return get_vikey_api().hash_b64(data, algo)


def vikey_sign(serial: str, key_id: str, data: Union[bytes, str], **kwargs) -> Dict[str, Any]:
    return get_vikey_api().sign(serial=serial, key_id=key_id, data=data, **kwargs)


def vikey_verify(serial: str, key_id: str, data: Union[bytes, str], signature_b64: str, **kwargs) -> Dict[str, Any]:
    return get_vikey_api().verify(serial=serial, key_id=key_id, data=data, signature_b64=signature_b64, **kwargs)


def vikey_encrypt(serial: str, key_id: str, plaintext: Union[bytes, str], **kwargs) -> Dict[str, Any]:
    return get_vikey_api().encrypt(serial=serial, key_id=key_id, plaintext=plaintext, **kwargs)


def vikey_decrypt(serial: str, key_id: str, nonce_b64: str, ciphertext_b64: str, **kwargs) -> Dict[str, Any]:
    return get_vikey_api().decrypt(serial=serial, key_id=key_id, nonce_b64=nonce_b64, ciphertext_b64=ciphertext_b64, **kwargs)


def vikey_hmac(serial: str, key_id: str, data: Union[bytes, str], **kwargs) -> Dict[str, Any]:
    return get_vikey_api().hmac(serial=serial, key_id=key_id, data=data, **kwargs)


def vikey_random(serial: str, length_bytes: int = 32, **kwargs) -> Dict[str, Any]:
    return get_vikey_api().random(serial=serial, length_bytes=length_bytes, **kwargs)


def vikey_bind_device(serial: str, **kwargs) -> Dict[str, Any]:
    return get_vikey_api().bind_device(serial=serial, **kwargs)


def vikey_unbind_device(serial: str, **kwargs) -> bool:
    return get_vikey_api().unbind_device(serial=serial, **kwargs)


def vikey_get_binding(serial: str) -> Optional[Dict[str, Any]]:
    return get_vikey_api().get_binding(serial)


def vikey_get_bindings(**kwargs) -> List[Dict[str, Any]]:
    return get_vikey_api().get_bindings(**kwargs)


def vikey_update_binding(serial: str, **kwargs) -> Optional[Dict[str, Any]]:
    return get_vikey_api().update_binding(serial=serial, **kwargs)


def vikey_lock_system(**kwargs) -> Dict[str, Any]:
    return get_vikey_api().lock_system(**kwargs)


def vikey_unlock_system(**kwargs) -> Dict[str, Any]:
    return get_vikey_api().unlock_system(**kwargs)


def vikey_get_lock_state() -> Dict[str, Any]:
    return get_vikey_api().get_lock_state()


def vikey_set_lock_timeout(seconds: int) -> None:
    get_vikey_api().set_lock_timeout(seconds)


def vikey_save_snapshot(data: Dict[str, Any], **kwargs) -> str:
    return get_vikey_api().save_snapshot(data=data, **kwargs)


def vikey_restore_snapshot(snap_id: str) -> Optional[Dict[str, Any]]:
    return get_vikey_api().restore_snapshot(snap_id)


def vikey_release_snapshot(snap_id: str) -> bool:
    return get_vikey_api().release_snapshot(snap_id)


def vikey_generate_challenge(**kwargs) -> str:
    return get_vikey_api().generate_challenge_code(**kwargs)


def vikey_verify_challenge(code: str, **kwargs) -> Tuple[bool, str]:
    return get_vikey_api().verify_challenge_code(code=code, **kwargs)


def vikey_compute_ssl_fingerprint(*args, **kwargs) -> str:
    return VikeyAPI.compute_ssl_fingerprint(*args, **kwargs)


def vikey_compute_hardware_binding(*args, **kwargs) -> str:
    return VikeyAPI.compute_hardware_binding_hash(*args, **kwargs)


def vikey_super_admin_login_7factor(auth: Dict[str, Any]) -> Dict[str, Any]:
    """统一 7 要素强认证入口（推荐直接调用这一个）。"""
    return get_vikey_api().verify_super_admin_7factor(auth)


def vikey_query_logs(**kwargs) -> List[Dict[str, Any]]:
    return get_vikey_api().query_logs(**kwargs)


def vikey_get_stats(**kwargs) -> Dict[str, Any]:
    return get_vikey_api().get_stats(**kwargs)


def vikey_cleanup_logs(days: int = 90) -> int:
    return get_vikey_api().cleanup_logs(days)


def vikey_create_usb_dongle(drive_path: str, **kwargs) -> Dict[str, Any]:
    return get_vikey_api().create_usb_dongle(drive_path=drive_path, **kwargs)


def vikey_register_hotplug_handler(handler: Callable[[str, str], None]) -> None:
    get_vikey_api().register_hotplug_handler(handler)


def vikey_unregister_hotplug_handler(handler: Callable[[str, str], None]) -> None:
    get_vikey_api().unregister_hotplug_handler(handler)


# ============================================================
#  6. 与 vikey_driver.py 完全同名的兼容函数（老代码零修改替换）
#     VikeyFind / VikeyIsPresent / VikeyGetStatus
# ============================================================
def VikeyFind() -> int:
    """兼容旧 API：返回当前插入的设备数量。"""
    try:
        return len(get_vikey_api().list_devices())
    except Exception:
        return 0


def VikeyIsPresent() -> bool:
    return get_vikey_api().is_present()


def VikeyGetStatus() -> Dict[str, Any]:
    """
    兼容旧 API：返回 {present/count/has_super_admin_key/super_admin_serial/.../driver_version}
    """
    try:
        r = get_vikey_api().detect()
        return {
            "present": r["count"] > 0,
            "count": r["count"],
            "devices": r["devices"],
            "has_super_admin_key": r["has_super_admin_key"],
            "super_admin_serial": r["super_admin_serial"],
            "has_hw_admin_key": r["has_hw_admin_key"],
            "hw_admin_serial": r["hw_admin_serial"],
            "driver_version": VIKEY_DRIVER_VERSION,
            "manufacturer": VIKEY_MANUFACTURER,
            "support_algos": list(VIKEY_SUPPORT_ALGOS),
            "timestamp": r["timestamp"],
        }
    except Exception as e:
        return {
            "present": False,
            "count": 0,
            "devices": [],
            "has_super_admin_key": False,
            "super_admin_serial": None,
            "error": str(e),
            "driver_version": VIKEY_DRIVER_VERSION,
            "manufacturer": VIKEY_MANUFACTURER,
            "support_algos": list(VIKEY_SUPPORT_ALGOS),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


# ============================================================
#  7. 单元测试占位（其他项目可直接 import vikey_api_tests 运行）
# ============================================================
def _run_self_tests() -> Dict[str, Any]:
    """
    本地自检：在 Simulation Backend 下跑一套最小 API 覆盖，
    验证所有 Facade 方法都能正常调用，无参数签名错误 / 异常未兜底等问题。
    其他项目可以在启动时跑一次，确认版本兼容。
    """
    # 临时切换到 sim 后端，避免依赖真实硬件
    os.environ["VIKEY_BACKEND"] = "sim"
    reset_vikey_api_instance()
    try:
        from core.services.vikey_driver import VikeySimulationBackend
        api = VikeyAPI(backend=VikeySimulationBackend())
    except Exception:
        api = get_vikey_api()
    report: Dict[str, Any] = {"ok": True, "passed": [], "failed": []}
    cases = [
        ("version", lambda: bool(api.get_version_info())),
        ("health", lambda: api.health_check().get("ok")),
        ("list_devices", lambda: isinstance(api.list_devices(), list)),
        ("detect", lambda: "devices" in api.detect()),
        ("challenge", lambda: len(api.generate_challenge_code()) == 6),
        ("verify_challenge_ok",
         lambda: api.verify_challenge_code(api.generate_challenge_code(), consume=True)[0]),
        ("ssl_fp", lambda: api.compute_ssl_fingerprint().startswith("sha256:")),
        ("hw_bind", lambda: api.compute_hardware_binding_hash().startswith("machine-")),
        ("get_lock_state", lambda: isinstance(api.get_lock_state(), dict)),
        ("get_stats", lambda: isinstance(api.get_stats(period="all"), dict)),
        ("query_logs", lambda: isinstance(api.query_logs(limit=5), list)),
    ]
    for name, fn in cases:
        try:
            ok = bool(fn())
            (report["passed"] if ok else report["failed"]).append(name)
            if not ok:
                report["ok"] = False
        except Exception as e:
            report["failed"].append(f"{name}: {e}")
            report["ok"] = False
    reset_vikey_api_instance()
    os.environ.pop("VIKEY_BACKEND", None)
    return report


# ============================================================
#  8. __all__ 导出清单（明确对外 API 范围）
# ============================================================
__all__ = [
    # 常量
    "VIKEY_API_VERSION",
    "VIKEY_DRIVER_VERSION",
    "VIKEY_MANUFACTURER",
    "VIKEY_SUPPORT_ALGOS",
    "VIKEY_DEFAULT_PIN",
    "VIKEY_DEFAULT_PUK_SUPER",
    "VIKEY_DEFAULT_PUK_AUDITOR",
    "VIKEY_SUPER_ADMIN_USERNAME",
    "VIKEY_SUPER_ADMIN_ROLE_HINT",
    "VIKEY_HW_ADMIN_ROLE_HINT",
    "VIKEY_DEFAULT_LOCK_TIMEOUT",
    "VIKEY_FORCE_CHECK_ENABLED_DEFAULT",
    "VIKEY_SUPER_ADMIN_REQUIRED_DEFAULT",
    "VIKEY_CHECK_INTERVAL_DEFAULT",
    "SEVEN_FACTOR_FIELDS",
    "BINDING_STATUS_UNBOUND",
    "BINDING_STATUS_BOUND",
    "BINDING_STATUS_REVOKED",
    # 异常
    "VikeyError",
    "VikeySevenFactorError",
    "VikeyBindingError",
    "VikeyLockError",
    # 底层（可选直接 import）
    "VikeyBackendInterface",
    "VikeyDevice",
    "VikeyDriverManager",
    # Facade 类 & 单例
    "VikeyAPI",
    "get_vikey_api",
    "reset_vikey_api_instance",
    # 编码辅助
    "_base64url_encode",
    "_base64url_decode",
    # 模块级便捷函数：元数据/检测
    "vikey_get_version_info",
    "vikey_health_check",
    "vikey_list_devices",
    "vikey_detect",
    "vikey_is_present",
    "vikey_get_device",
    # 便捷函数：认证/会话
    "vikey_login",
    "vikey_login_auto_internal",
    "vikey_ensure_session",
    "vikey_logout",
    "vikey_change_pin",
    "vikey_unblock_pin",
    "vikey_is_logged_in",
    # 便捷函数：密钥/证书
    "vikey_list_keys",
    "vikey_list_certificates",
    "vikey_export_certificate",
    "vikey_import_certificate",
    "vikey_generate_keypair",
    # 便捷函数：密码运算
    "vikey_hash",
    "vikey_hash_b64",
    "vikey_sign",
    "vikey_verify",
    "vikey_encrypt",
    "vikey_decrypt",
    "vikey_hmac",
    "vikey_random",
    # 便捷函数：绑定
    "vikey_bind_device",
    "vikey_unbind_device",
    "vikey_get_binding",
    "vikey_get_bindings",
    "vikey_update_binding",
    # 便捷函数：系统锁定/快照
    "vikey_lock_system",
    "vikey_unlock_system",
    "vikey_get_lock_state",
    "vikey_set_lock_timeout",
    "vikey_save_snapshot",
    "vikey_restore_snapshot",
    "vikey_release_snapshot",
    # 便捷函数：7 要素
    "vikey_generate_challenge",
    "vikey_verify_challenge",
    "vikey_compute_ssl_fingerprint",
    "vikey_compute_hardware_binding",
    "vikey_super_admin_login_7factor",
    # 便捷函数：审计日志
    "vikey_query_logs",
    "vikey_get_stats",
    "vikey_cleanup_logs",
    # 便捷函数：U盘 & 热插拔
    "vikey_create_usb_dongle",
    "vikey_register_hotplug_handler",
    "vikey_unregister_hotplug_handler",
    # 兼容 vikey_driver 的同名函数
    "VikeyFind",
    "VikeyIsPresent",
    "VikeyGetStatus",
    # 自测
    "_run_self_tests",
]


# ============================================================
#  9. 直接执行：python -m core.services.vikey_api  触发自检
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    print("Running VikeyAPI self tests ...")
    r = _run_self_tests()
    print(json.dumps(r, indent=2, ensure_ascii=False, default=str))
    sys.exit(0 if r["ok"] else 1)
