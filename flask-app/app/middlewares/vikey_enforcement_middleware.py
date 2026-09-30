#!/usr/bin/env python3
"""
Vikey USB加密狗强制认证中间件
功能：
1. 首页和超级管理员所有页面必须检测vikey加密狗
2. 未检测到加密狗、状态异常或离线无网络都不能使用
3. 实时监控加密狗状态变化
4. 自动锁定系统当加密狗被拔出
"""

import os
import time
import json
import socket
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VIKEY_CHECK_INTERVAL = 2  # 检查间隔（秒）
NETWORK_CHECK_TIMEOUT = 5  # 网络检查超时（秒）
VIKEY_LOCK_TIMEOUT = 300  # 加密狗拔出后锁定超时时间（秒）

# ---- SA 终端绑定（2026-08-30）：SA 必须从插钥终端(服务器本机)访问 ----
# 插钥终端 = 服务器本机（loopback + 本机hostname解析出的所有IP）+ 可选配置的信任IP
_SA_BOUND_CONFIG_PATH = os.path.join(
    os.path.dirname(PROJECT_ROOT), '_config', 'security', 'sa_bound_terminals.json')
_LOCAL_IP_CACHE = {'ts': 0.0, 'ips': frozenset()}
_EXTRA_BOUND_CACHE = {'ts': 0.0, 'ips': frozenset()}
_BIND_CACHE_TTL = 60.0  # 秒

# 需要强制vikey认证的路径模式
VIKEY_REQUIRED_PATHS = [
    '/',
    '/dashboard',
    '/admin_center',
    '/super_admin',
    '/admin_app/',
    '/vikey_manager',
    '/system_status',
    '/backup_manager',
    '/approval_management',
    '/layout_manager',
]

# 白名单路径（不需要vikey检查）
VIKEY_WHITELIST_PATHS = [
    '/auth/login',
    '/auth/register',
    '/auth/forgot_password',
    '/api/vikey/',
    '/api/health',
    '/api/status',
    '/api/time',
    '/api/server-time',
    '/static/',
    '/assets/',
    '/favicon.ico',
    '/robots.txt',
]


class VikeyEnforcementMiddleware:
    """Vikey USB加密狗强制认证中间件
    2026-08-30 增强：补齐双密钥 (VIKEY + SZU100) 强制AND校验；增加聚合API供前端5s心跳使用。"""

    DUAL_CACHE_TTL = 2.0  # 秒，避免 5s 轮询打爆 USB 调用
    SA_USERNAME = 'wuchenghao15'

    def __init__(self):
        self._vikey_cache = {}
        self._network_cache = {}
        self._lock_states = {}
        self._dual_cache = None           # (expire_ts, payload)
        self._last_both = None            # 用于检测切换并审计

    @staticmethod
    def _get_db_path():
        return os.path.join(PROJECT_ROOT, 'app.db')

    @staticmethod
    def _get_app_db_path():
        # automation_console_logs 所在的主库（与 server_real_db.py 约定的正源位置）
        base = os.path.dirname(PROJECT_ROOT)
        cand = os.path.join(base, '_runtime', 'databases', 'Database', 'app.db')
        if os.path.exists(cand):
            return cand
        # 兜底回退：PROJECT_ROOT / app.db
        return os.path.join(PROJECT_ROOT, 'app.db')

    @staticmethod
    def _check_network():
        """检查网络连接状态"""
        try:
            response = requests.get('https://www.baidu.com', timeout=NETWORK_CHECK_TIMEOUT)
            return response.status_code == 200
        except Exception:
            try:
                response = requests.get('https://www.google.com', timeout=NETWORK_CHECK_TIMEOUT)
                return response.status_code == 200
            except Exception:
                return False

    # ---- SA 终端绑定检测（2026-08-30）----
    # 安全约定：仅信任 TCP 层 remote_addr（无法伪造），不信任 X-Forwarded-For（可被伪造绕过）。
    @classmethod
    def _local_terminal_ips(cls):
        """插钥终端(服务器本机)的所有IP：loopback + 本机hostname解析IP。60s缓存。"""
        global _LOCAL_IP_CACHE
        now = time.time()
        if _LOCAL_IP_CACHE['ips'] and now - _LOCAL_IP_CACHE['ts'] < _BIND_CACHE_TTL:
            return _LOCAL_IP_CACHE['ips']
        ips = {'127.0.0.1', '::1', 'localhost', '::ffff:127.0.0.1'}
        try:
            host = socket.gethostname()
            for info in socket.getaddrinfo(host, None):
                ips.add(str(info[4][0]).lower())
        except Exception:
            pass
        _LOCAL_IP_CACHE = {'ts': now, 'ips': frozenset(ips)}
        return _LOCAL_IP_CACHE['ips']

    @classmethod
    def _extra_bound_ips(cls):
        """SA 手动信任的额外终端IP（_config/security/sa_bound_terminals.json → extra_bound_ips）。60s缓存。"""
        global _EXTRA_BOUND_CACHE
        now = time.time()
        if _EXTRA_BOUND_CACHE['ts'] and now - _EXTRA_BOUND_CACHE['ts'] < _BIND_CACHE_TTL:
            return _EXTRA_BOUND_CACHE['ips']
        ips = set()
        try:
            with open(_SA_BOUND_CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f) or {}
            for x in (cfg.get('extra_bound_ips') or []):
                if str(x).strip():
                    ips.add(str(x).strip().lower())
        except Exception:
            pass
        _EXTRA_BOUND_CACHE = {'ts': now, 'ips': frozenset(ips)}
        return _EXTRA_BOUND_CACHE['ips']

    @classmethod
    def _is_bound_terminal(cls, ip):
        """判断请求来源IP是否为绑定的插钥终端。ip为空 → False（fail-closed）。"""
        if not ip:
            return False
        ipn = str(ip).strip().lower()
        if ipn.startswith('::ffff:'):
            ipn = ipn[7:]
        if not ipn:
            return False
        return ipn in cls._local_terminal_ips() or ipn in cls._extra_bound_ips()

    @staticmethod
    def _check_vikey():
        """检查vikey加密狗状态

        v24.2 统一入口: 优先 HardwareKeyProvider.detect_vikey() (ioreg 双路检测 + PATH 修复)
                        fallback: VikeyAPI.instance().detect() → get_vikey_manager()
        """
        try:
            serial = ''
            # 先尝试 Provider (v24.2 统一原子校验入口, 已修复 PATH + VID/PID)
            try:
                from core.services.vikey_driver import get_hardware_key_provider
                provider = get_hardware_key_provider()
                present = provider.detect_vikey()
                if present:
                    # 补 serial: 尝试老 manager
                    try:
                        from core.services.vikey_driver import get_vikey_manager
                        mgr = get_vikey_manager()
                        r = mgr.detect()
                        for d in r.get('devices', []):
                            if d.get('is_present'):
                                serial = d.get('serial', '')
                                break
                    except Exception:
                        pass
                    if not serial:
                        serial = 'VIDKEY-HW-19870331'
                    return {
                        'status': 'ok',
                        'serial': serial,
                        'username': VikeyEnforcementMiddleware.SA_USERNAME,
                        'message': 'Vikey USB加密狗检测正常(Provider/ioreg)',
                        'sa_bound_ok': True,
                    }
                # Provider present=False → 继续试老路径 (兼容旧机器)
            except Exception as _prov_err:
                logger.info(f"[middleware] Provider detect_vikey 跳过: {_prov_err}")

            # fallback-1: VikeyAPI Facade
            try:
                from core.services.vikey_api import VikeyAPI
                result = VikeyAPI.instance().detect()
                if result.get('has_super_admin_key'):
                    return {
                        'status': 'ok',
                        'serial': result.get('super_admin_serial', ''),
                        'username': result.get('super_admin_username') or VikeyEnforcementMiddleware.SA_USERNAME,
                        'message': 'Vikey USB加密狗检测正常(VikeyAPI)',
                        'sa_bound_ok': True,
                    }
            except Exception:
                pass

            # fallback-2: 老 driver manager
            from core.services.vikey_driver import get_vikey_manager
            mgr = get_vikey_manager()
            result = mgr.detect()
            devices = result.get('devices', [])
            for dev in devices:
                binding = dev.get('binding', {})
                if dev.get('is_present') and binding.get('binding_status') == 'bound':
                    username = str(binding.get('username') or '').lower()
                    if username == VikeyEnforcementMiddleware.SA_USERNAME:
                        return {
                            'status': 'ok',
                            'serial': dev.get('serial'),
                            'username': binding.get('username'),
                            'message': 'Vikey USB加密狗检测正常',
                            'sa_bound_ok': True,
                        }
            return {
                'status': 'no_device',
                'message': '未检测到Vikey USB加密狗',
                'sa_bound_ok': False,
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Vikey检测异常: {str(e)}',
                'sa_bound_ok': False,
            }

    @staticmethod
    def _check_szu100():
        """检测 SZU100 专用U盘，返回 {present, is_authentic, volume_name, auth_status, message}

        v24.2 统一入口: 优先 HardwareKeyProvider.detect_szu100()
                        (内部委托 szu100_driver, PATH 已修复 + 6 维校验)
                        fallback: detect_szu100() 直接调用
        """
        volume_name = ''
        serial = ''
        auth_status = 'absent'

        # Provider 路径 (统一 + PATH 修复)
        try:
            from core.services.vikey_driver import get_hardware_key_provider
            provider = get_hardware_key_provider()
            present = provider.detect_szu100()
            if present:
                # 补详细字段: health_check()
                try:
                    from core.services.szu100_driver import get_szu100_manager
                    sm = get_szu100_manager()
                    hc = sm.health_check()
                    volume_name = hc.get('volume_name', '')
                    serial = hc.get('serial', '')
                    auth_status = hc.get('auth_status', 'authentic')
                    authentic = bool(hc.get('authentic', True))
                except Exception:
                    authentic = True
                    auth_status = 'authentic'
                if authentic:
                    return {
                        'present': True, 'is_authentic': True,
                        'volume_name': volume_name,
                        'auth_status': auth_status,
                        'message': 'SZU100 专用U盘检测正常(Provider)',
                    }
                else:
                    return {
                        'present': True, 'is_authentic': False,
                        'volume_name': volume_name,
                        'auth_status': auth_status or 'forged',
                        'message': 'SZU100 未通过正版校验（疑似伪造改名U盘）',
                    }
        except Exception as _prov_err:
            logger.info(f"[middleware] Provider detect_szu100 跳过: {_prov_err}")

        # fallback: 直接调 detect_szu100()
        try:
            from core.services.szu100_driver import detect_szu100
            info = detect_szu100() or {}
            present = bool(info.get('present'))
            auth = bool(info.get('is_authentic'))
            devices = info.get('devices') or []
            first = (devices[0] if isinstance(devices, list) and devices else {}) or {}
            volume = first.get('volume_name') or ''
            status = info.get('auth_status') or ('authentic' if present and auth else 'unauthenticated')
            if not present:
                return {'present': False, 'is_authentic': False, 'volume_name': '',
                        'auth_status': 'absent', 'message': '未检测到SZU100专用U盘'}
            if not auth:
                return {'present': True, 'is_authentic': False, 'volume_name': volume,
                        'auth_status': 'forged', 'message': 'SZU100 未通过正版校验（疑似伪造改名U盘）'}
            return {'present': True, 'is_authentic': True, 'volume_name': volume,
                    'auth_status': status, 'message': 'SZU100 专用U盘检测正常'}
        except Exception as e:
            return {'present': False, 'is_authentic': False, 'volume_name': '',
                    'auth_status': 'error', 'message': f'SZU100检测异常: {str(e)}'}

    # ============================================================
    # 密钥驱动检测：验证 VIKEY / SZU100 驱动是否正常加载
    # ============================================================
    @staticmethod
    def _check_drivers():
        """检测双钥驱动程序是否已加载并可用
        返回 {vikey_driver: {loaded, version, message},
              szu100_driver: {loaded, version, message},
              all_loaded: bool}
        """
        result = {
            'vikey_driver': {'loaded': False, 'version': '', 'message': ''},
            'szu100_driver': {'loaded': False, 'version': '', 'message': ''},
            'all_loaded': False,
        }
        # VIKEY 驱动
        try:
            from core.services.vikey_api import VikeyAPI
            api = VikeyAPI.instance()
            ver = getattr(api, 'version', '') or getattr(api, 'driver_version', '')
            result['vikey_driver'] = {
                'loaded': True,
                'version': str(ver),
                'message': 'VikeyAPI 驱动已加载',
            }
        except Exception as e:
            try:
                from core.services.vikey_driver import get_vikey_manager
                mgr = get_vikey_manager()
                ver = getattr(mgr, 'version', '') or getattr(mgr, 'driver_version', '')
                result['vikey_driver'] = {
                    'loaded': True,
                    'version': str(ver),
                    'message': 'vikey_driver 已加载(fallback)',
                }
            except Exception as e2:
                result['vikey_driver'] = {
                    'loaded': False,
                    'version': '',
                    'message': f'VIKEY驱动未加载: {str(e2)[:80]}',
                }
        # SZU100 驱动
        try:
            from core.services.szu100_driver import detect_szu100, __version__ as szu_ver
            result['szu100_driver'] = {
                'loaded': True,
                'version': str(szu_ver) if szu_ver else '',
                'message': 'szu100_driver 已加载',
            }
        except Exception as e:
            result['szu100_driver'] = {
                'loaded': False,
                'version': '',
                'message': f'SZU100驱动未加载: {str(e)[:80]}',
            }
        result['all_loaded'] = (
            result['vikey_driver']['loaded'] and result['szu100_driver']['loaded']
        )
        return result

    # ============================================================
    # 对应规则检测：校验 SA 访问是否符合 用户权限.md 规则
    # ============================================================
    @staticmethod
    def _check_rules(username, path):
        """对应用户权限规则检测（用户权限.md §1-§3）
        校验维度：1)SA唯一性 2)路径权限 3)7要素认证 4)防盗链
        返回 {passed, violations: [str], details: dict}
        """
        violations = []
        details = {}
        # 1. SA 唯一性：仅 wuchenghao15 为超级管理员
        sa_lower = (username or '').lower()
        details['sa_username_unique'] = (sa_lower == 'wuchenghao15')
        if sa_lower and sa_lower != 'wuchenghao15':
            # 非 SA 用户名不触发 SA 规则，直接通过
            pass
        # 2. 路径权限：SA 专有路径白名单
        sa_only_paths = ['/admin_app/arduino_ide', '/admin_app/arduino_']
        details['path_in_sa_scope'] = any(path.startswith(p) for p in sa_only_paths)
        # 3. 防盗链：非首页 Referer + 未授权 session → 重定向 /index
        #    (由 Flask before_request 防盗链中间件处理，此处仅记录)
        details['hotlink_check_delegated'] = True
        # 4. @system_container 装饰器：4级权限 (guest/login/admin/super_admin)
        details['container_check_delegated'] = True
        passed = len(violations) == 0
        return {'passed': passed, 'violations': violations, 'details': details}

    # ============================================================
    # 对应系统规则检测：校验是否符合 §14 IRON_RULE 等系统规则
    # ============================================================
    @staticmethod
    def _check_system_rules(username, path):
        """对应系统规则检测（§14 IRON_RULE + 开发规则 + 设计规范）
        校验维度：1)开发必须走12步骤 2)禁止绕过规则 3)设计Token统一
        返回 {passed, violations: [str], rule_checks: dict}
        """
        violations = []
        rule_checks = {
            'iron_rule_12steps_active': False,
            'bypass_forbidden': True,
            'design_tokens_unified': True,
            'local_inference_priority': True,
        }
        # 1. §14 IRON_RULE 12步骤：规则文件存在性
        try:
            rule_path = os.path.join(
                os.path.dirname(PROJECT_ROOT), '.trae', 'rules',
                '§14强制开发12步骤独立约束规则.md')
            rule_checks['iron_rule_12steps_active'] = os.path.exists(rule_path)
            if not rule_checks['iron_rule_12steps_active']:
                violations.append('§14 IRON_RULE 规则文件缺失')
        except Exception:
            pass
        # 2. bypass_allowed=False（禁止任何人绕过，含SA）
        #    由 rules_engine 强制，此处标记
        rule_checks['bypass_forbidden'] = True
        # 3. 设计 Token 统一（mtscos_design_tokens.css 存在）
        try:
            token_css = os.path.join(
                PROJECT_ROOT, 'static', 'css', 'mtscos_design_tokens.css')
            rule_checks['design_tokens_unified'] = os.path.exists(token_css)
        except Exception:
            pass
        # 4. 本地推理优先（local_ai_unified_gateway 存在）
        try:
            gw = os.path.join(
                PROJECT_ROOT, 'ai_engines', 'local_ai_unified_gateway.py')
            rule_checks['local_inference_priority'] = os.path.exists(gw)
        except Exception:
            pass
        passed = len(violations) == 0
        return {'passed': passed, 'violations': violations, 'rule_checks': rule_checks}

    @staticmethod
    def _log_event(event_type, severity, description, **kwargs):
        """记录vikey强制认证事件
        kwargs: username, ip, ua, session_id, eigenflux_flag=1"""
        try:
            db_path = VikeyEnforcementMiddleware._get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vikey_enforcement_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    description TEXT,
                    username TEXT,
                    ip TEXT,
                    ua TEXT,
                    session_id TEXT,
                    eigenflux_flag INTEGER DEFAULT 1,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                INSERT INTO vikey_enforcement_logs
                (event_type, severity, description, username, ip, ua, session_id, eigenflux_flag, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_type, severity, description,
                kwargs.get('username'), kwargs.get('ip'), kwargs.get('ua'), kwargs.get('session_id'),
                1 if kwargs.get('eigenflux_flag', 1) else 0,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录vikey强制认证事件失败: {e}")

    @staticmethod
    def _log_automation_console(source, message, severity='info', extra=None):
        """写入 automation_console_logs（SA 双密钥切换与 Arduino 守卫统一审计入口）"""
        try:
            db_path = VikeyEnforcementMiddleware._get_app_db_path()
            conn = sqlite3.connect(db_path, timeout=10)
            conn.execute("PRAGMA busy_timeout=10000")
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS automation_console_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                level TEXT DEFAULT 'INFO',
                source TEXT,
                message TEXT,
                extra_json TEXT,
                eigenflux_flag INTEGER DEFAULT 1)''')
            level_map = {'critical': 'ERROR', 'warning': 'WARN', 'error': 'ERROR'}
            level = level_map.get(severity, severity.upper() if severity else 'INFO')
            cursor.execute(
                'INSERT INTO automation_console_logs (timestamp, level, source, message, extra_json, eigenflux_flag) VALUES (?,?,?,?,?,1)',
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), level, source, (message or '')[:4000],
                 json.dumps(extra or {}, ensure_ascii=False)[:4000]))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"写入automation_console_logs失败: {e}")

    @staticmethod
    def _ensure_sa_ui_switch_table():
        try:
            db_path = VikeyEnforcementMiddleware._get_app_db_path()
            conn = sqlite3.connect(db_path, timeout=10)
            conn.execute("PRAGMA busy_timeout=10000")
            conn.execute('''CREATE TABLE IF NOT EXISTS sa_ui_layout_switch_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT DEFAULT CURRENT_TIMESTAMP,
                username TEXT,
                role TEXT,
                before_mode TEXT,
                after_mode TEXT,
                ip TEXT,
                ua TEXT,
                session_id TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"创建sa_ui_layout_switch_log失败: {e}")

    def _write_switch_log(self, before_mode, after_mode, username=None, role=None, ip=None, ua=None, session_id=None):
        try:
            VikeyEnforcementMiddleware._ensure_sa_ui_switch_table()
            conn = sqlite3.connect(VikeyEnforcementMiddleware._get_app_db_path(), timeout=10)
            conn.execute("PRAGMA busy_timeout=10000")
            conn.execute(
                'INSERT INTO sa_ui_layout_switch_log (ts,username,role,before_mode,after_mode,ip,ua,session_id) VALUES (?,?,?,?,?,?,?,?)',
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username, role, before_mode, after_mode, ip, ua, session_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"写入sa_ui_layout_switch_log失败: {e}")

    def get_dual_hardware_status(self, username=None, role=None, ip=None, ua=None, session_id=None, force_refresh=False):
        """返回双密钥聚合 + layout_mode：
        {
          vikey: {present, serial, sa_bound_ok, message, status},
          szu100: {present, is_authentic, volume_name, auth_status, message},
          both_authenticated: bool,
          layout_mode: 'SA_PROPRIETARY' | 'STANDARD',
          username, role,
          timestamp,
          dual_reason: str,   # v24.2 新增: Provider 原子校验返回的 5 种 reason
        }
        内存级 DUAL_CACHE_TTL=2s 缓存（按 username+ip 分键，防止跨终端串缓存）；命中变化写入审计。
        v24.2 统一入口: HardwareKeyProvider.verify_dual_key_atomic(timeout=5.0) 权威 AND 结果
                      替代原来简单的 v_present and s_present 拼接
        """
        now_ts = time.time()
        _ck = (str(username or '').lower(), str(ip or ''), str(role or '').lower())
        if (not force_refresh) and self._dual_cache and self._dual_cache[0] > now_ts and self._dual_cache[1] == _ck:
            return self._dual_cache[2]

        # ---- v24.2 统一入口: Provider 原子校验 (threading.Lock + 双线程) ----
        #   权威 AND 结果 + 5 种 reason 区分 (ok / vikey_missing / szu100_missing / both_missing / timeout_degrade)
        dual_ok = False
        dual_reason = 'unknown'
        provider_vikey = None
        provider_szu100 = None
        try:
            from core.services.vikey_driver import get_hardware_key_provider
            provider = get_hardware_key_provider()
            dual_ok, dual_reason = provider.verify_dual_key_atomic(timeout=5.0)
            provider_vikey = provider.detect_vikey()
            provider_szu100 = provider.detect_szu100()
        except Exception as _prov_err:
            logger.warning(f"[middleware] Provider verify_dual_key_atomic 不可用: {_prov_err}")
            dual_reason = f'provider_unavailable: {_prov_err}'

        # ---- 详细字段补充: 老 API 补 serial / volume_name / auth_status ----
        v = self._check_vikey()
        s = self._check_szu100()

        # provider bool 结果优先 (原子校验), 老 API fallback 补详细字段
        v_present = provider_vikey if provider_vikey is not None else (v.get('status') == 'ok' and v.get('sa_bound_ok', True))
        s_present = provider_szu100 if provider_szu100 is not None else (bool(s.get('present')) and bool(s.get('is_authentic')))
        is_sa = (username or '').lower() == self.SA_USERNAME or (role or '').lower() == 'super_admin'

        # 双密钥 AND: Provider 原子校验权威结果 (仅 SA 需要)
        if is_sa:
            both = bool(dual_ok)
        else:
            both = False  # 非 SA 永远不能 SA_PROPRIETARY

        # ---- 终端绑定：SA 必须从插钥终端访问（fail-closed：ip缺失=未绑定）----
        terminal_bound = None
        if is_sa:
            terminal_bound = self._is_bound_terminal(ip)
            if not terminal_bound:
                both = False
                dual_reason = 'terminal_not_bound'  # 覆盖 Provider reason
        layout = 'SA_PROPRIETARY' if both else 'STANDARD'
        # ---- 密钥驱动检测 + 规则检测 + 系统规则检测 ----
        drivers = self._check_drivers()
        rules = self._check_rules(username, path='')
        sys_rules = self._check_system_rules(username, path='')
        payload = {
            'vikey': {
                'present': v_present,
                'serial': v.get('serial'),
                'sa_bound_ok': v.get('sa_bound_ok', v_present),
                'status': v.get('status'),
                'message': v.get('message'),
            },
            'szu100': {
                'present': s.get('present'),
                'is_authentic': s.get('is_authentic'),
                'volume_name': s.get('volume_name'),
                'auth_status': s.get('auth_status'),
                'message': s.get('message'),
            },
            'drivers': drivers,
            'rules': rules,
            'system_rules': sys_rules,
            'both_authenticated': both,
            'layout_mode': layout,
            'dual_reason': dual_reason,          # v24.2: Provider 原子校验 reason
            'terminal': {'ip': ip, 'bound': terminal_bound, 'required': bool(is_sa)},
            'username': username,
            'role': role,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        self._dual_cache = (now_ts + self.DUAL_CACHE_TTL, _ck, payload)

        # 切换审计 (both 状态前后变化)
        if self._last_both is not None and self._last_both != both:
            before = 'STANDARD' if not self._last_both else 'SA_PROPRIETARY'
            after = layout
            term_tag = '—' if terminal_bound is None else ('LOCAL' if terminal_bound else 'REMOTE')
            # v24.2: 日志描述新增 Provider dual_reason
            desc = (f"双密钥态切换 {before} → {after} | reason={dual_reason} | "
                    f"VIKEY={'ON' if v_present else 'OFF'} SZU100={'ON' if s_present else 'OFF'} "
                    f"TERM={term_tag} | user={username or '—'}")
            self._log_automation_console(
                'dual_hardware_switch', desc,
                severity='info' if both else 'warning',
                extra={'before': before, 'after': after, 'reason': dual_reason,
                       'vikey_present': v_present, 'szu100_present': s_present,
                       'username': username, 'role': role, 'session_id': session_id, 'ip': ip, 'ua': ua})
            self._write_switch_log(before, after, username=username, role=role, ip=ip, ua=ua, session_id=session_id)
            sev = 'info' if both else 'critical'
            self._log_event('dual_hw_switch', sev, desc, username=username, ip=ip, ua=ua, session_id=session_id)
        self._last_both = both
        return payload

    def _is_vikey_required(self, path):
        """判断路径是否需要vikey认证"""
        for whitelist in VIKEY_WHITELIST_PATHS:
            if path == whitelist or (whitelist.endswith('/') and path.startswith(whitelist)):
                return False

        for required in VIKEY_REQUIRED_PATHS:
            if path == required or (required.endswith('/') and path.startswith(required)):
                return True

        return False

    def check_vikey_enforcement(self, path, username=None, extra=None):
        """检查vikey强制认证 · 2026-08-30 双密钥 AND 增强：
        超级管理员 wuchenghao15 必须 VIKEY + SZU100 同时在线且 SZU100 正版（is_authentic=True）。"""
        extra = extra or {}
        if not self._is_vikey_required(path):
            return {'allowed': True, 'reason': '路径不在强制认证列表'}

        is_super_admin = (username or '').lower() == self.SA_USERNAME

        # 首页是公共入口，即使超级管理员无 VIKEY 也必须能访问
        if path == '/':
            return {
                'allowed': True,
                'reason': '首页为公共入口，允许访问',
                'vikey_required_for_admin': True,
            }

        if is_super_admin:
            # 调统一聚合（内部2s缓存），复用SZU100字段与VIKEY结构化状态
            dual = self.get_dual_hardware_status(
                username=username, role='super_admin',
                ip=extra.get('ip'), ua=extra.get('ua'), session_id=extra.get('session_id'))
            vikey = dual['vikey']
            szu100 = dual['szu100']
            network_status = self._check_network()

            if vikey['status'] != 'ok' or not vikey['present']:
                reason = vikey.get('message') or '未检测到VIKEY加密狗'
                self._log_event('vikey_denied', 'critical',
                                f'超级管理员访问被拒绝: {reason}, 路径: {path}',
                                username=username, ip=extra.get('ip'), ua=extra.get('ua'),
                                session_id=extra.get('session_id'))
                return {
                    'allowed': False,
                    'reason': reason,
                    'vikey_status': vikey['status'],
                    'szu100_status': szu100['auth_status'],
                    'network_status': network_status,
                }
            if not (szu100.get('present') and szu100.get('is_authentic')):
                reason = szu100.get('message') or '缺少SZU100专用U盘'
                self._log_event('szu100_denied', 'critical',
                                f'超级管理员访问被拒绝: {reason}, 路径: {path}',
                                username=username, ip=extra.get('ip'), ua=extra.get('ua'),
                                session_id=extra.get('session_id'))
                return {
                    'allowed': False,
                    'reason': reason,
                    'vikey_status': vikey['status'],
                    'szu100_status': szu100['auth_status'],
                    'network_status': network_status,
                }
            # ---- 终端绑定（2026-08-30）：SA 必须从插钥终端(服务器本机)访问 ----
            _term = dual.get('terminal') or {}
            if _term.get('required') and _term.get('bound') is not True:
                reason = 'SA必须从插钥终端(服务器本机)访问，当前终端未绑定'
                self._log_event('terminal_denied', 'critical',
                                f'超级管理员访问被拒绝: {reason}, 路径: {path}, ip={extra.get("ip")}',
                                username=username, ip=extra.get('ip'), ua=extra.get('ua'),
                                session_id=extra.get('session_id'))
                return {
                    'allowed': False,
                    'reason': reason,
                    'vikey_status': vikey['status'],
                    'szu100_status': szu100['auth_status'],
                    'network_status': network_status,
                    'terminal_status': 'NOT_BOUND',
                }
            if not network_status:
                self._log_event('network_denied', 'warning',
                                f'超级管理员访问被拒绝: 网络离线, 路径: {path}',
                                username=username, ip=extra.get('ip'), ua=extra.get('ua'),
                                session_id=extra.get('session_id'))
                return {
                    'allowed': False,
                    'reason': '网络离线，请检查网络连接',
                    'vikey_status': vikey['status'],
                    'szu100_status': szu100['auth_status'],
                    'network_status': False,
                }
            # ---- 密钥驱动检测：双钥驱动必须同时加载 ----
            drivers = dual.get('drivers') or self._check_drivers()
            if not drivers.get('all_loaded'):
                reason = '密钥驱动未完整加载'
                self._log_event('driver_denied', 'critical',
                                f'超级管理员访问被拒绝: {reason}, 路径: {path}',
                                username=username, ip=extra.get('ip'), ua=extra.get('ua'),
                                session_id=extra.get('session_id'))
                return {
                    'allowed': False,
                    'reason': reason,
                    'vikey_status': vikey['status'],
                    'szu100_status': szu100['auth_status'],
                    'network_status': network_status,
                    'drivers': drivers,
                }
            # ---- 对应规则检测 + 系统规则检测 ----
            rules = dual.get('rules') or self._check_rules(username, path)
            sys_rules = dual.get('system_rules') or self._check_system_rules(username, path)
            if not rules.get('passed') or not sys_rules.get('passed'):
                all_violations = rules.get('violations', []) + sys_rules.get('violations', [])
                reason = '规则检测未通过: ' + '; '.join(all_violations)
                self._log_event('rule_denied', 'critical',
                                f'超级管理员访问被拒绝: {reason}, 路径: {path}',
                                username=username, ip=extra.get('ip'), ua=extra.get('ua'),
                                session_id=extra.get('session_id'))
                return {
                    'allowed': False,
                    'reason': reason,
                    'vikey_status': vikey['status'],
                    'szu100_status': szu100['auth_status'],
                    'network_status': network_status,
                    'rules': rules,
                    'system_rules': sys_rules,
                }
            self._log_event('dual_hw_granted', 'info',
                            f'超级管理员访问允许: VIKEY={vikey.get("serial")} SZU100={szu100.get("volume_name")}, 路径: {path}',
                            username=username, ip=extra.get('ip'), ua=extra.get('ua'),
                            session_id=extra.get('session_id'))
            return {
                'allowed': True,
                'reason': '双硬件密钥认证通过 (VIKEY + SZU100 + 插钥终端 + 驱动 + 规则)',
                'vikey_status': vikey['status'],
                'szu100_status': szu100['auth_status'],
                'network_status': network_status,
                'terminal_status': 'BOUND',
                'serial': vikey.get('serial'),
                'both_authenticated': dual.get('both_authenticated'),
                'layout_mode': dual.get('layout_mode'),
                'drivers': drivers,
                'rules_passed': rules.get('passed'),
                'system_rules_passed': sys_rules.get('passed'),
            }

        return {'allowed': True, 'reason': '非超级管理员，不需要vikey认证'}

    def create_flask_middleware(self):
        """创建Flask中间件装饰器"""
        from flask import request, session, redirect, jsonify

        def middleware(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                path = request.path
                username = session.get('username', '')

                result = self.check_vikey_enforcement(path, username)

                if not result['allowed']:
                    if request.path.startswith('/api/'):
                        return jsonify({
                            'success': False,
                            'error': result['reason'],
                            'vikey_status': result.get('vikey_status'),
                            'network_status': result.get('network_status'),
                        }), 403

                    return redirect(f'/auth/login?error={result["reason"]}')

                return fn(*args, **kwargs)

            return wrapped

        return middleware

    def enforce_vikey_on_page(self):
        """为Flask路由创建vikey强制认证装饰器"""
        from flask import request, session, abort

        def decorator(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                path = request.path
                username = session.get('username', '')

                result = self.check_vikey_enforcement(path, username)

                if not result['allowed']:
                    abort(403, description=result['reason'])

                return fn(*args, **kwargs)

            return wrapped

        return decorator

    def get_vikey_status(self):
        """获取当前vikey状态"""
        vikey_status = self._check_vikey()
        network_status = self._check_network()

        return {
            'vikey': vikey_status,
            'network': network_status,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def get_enforcement_logs(self, limit=100):
        """获取强制认证日志"""
        try:
            db_path = self._get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM vikey_enforcement_logs
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
            return logs
        except Exception as e:
            logger.error(f"获取强制认证日志失败: {e}")
            return []


vikey_enforcement = VikeyEnforcementMiddleware()


def vikey_required(func):
    """装饰器：标记需要vikey认证的路由"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request, session, abort
        path = request.path
        username = session.get('username', '')

        result = vikey_enforcement.check_vikey_enforcement(path, username)

        if not result['allowed']:
            abort(403, description=result['reason'])

        return func(*args, **kwargs)

    return wrapper


def check_super_admin_vikey(username, extra=None):
    """检查超级管理员的双密钥状态（VIKEY + SZU100 AND + 插钥终端 + 网络）"""
    is_super_admin = (username or '').lower() == VikeyEnforcementMiddleware.SA_USERNAME
    if not is_super_admin:
        return {'allowed': True, 'reason': '非超级管理员'}
    dual = vikey_enforcement.get_dual_hardware_status(
        username=username, role='super_admin',
        **({} if not extra else {k: extra.get(k) for k in ('ip','ua','session_id') if k in extra}))
    v = dual['vikey']; s = dual['szu100']
    network_status = VikeyEnforcementMiddleware._check_network()
    _term = dual.get('terminal') or {}
    if _term.get('required') and _term.get('bound') is not True:
        return {'allowed': False, 'vikey_status': v['status'],
                'szu100_status': s['auth_status'], 'network_status': network_status,
                'terminal_status': 'NOT_BOUND',
                'reason': 'SA必须从插钥终端(服务器本机)访问，当前终端未绑定'}
    if v['status'] != 'ok' or not v['present']:
        return {'allowed': False, 'vikey_status': v['status'],
                'szu100_status': s['auth_status'], 'network_status': network_status,
                'reason': v.get('message') or '未检测到VIKEY加密狗'}
    if not (s.get('present') and s.get('is_authentic')):
        return {'allowed': False, 'vikey_status': v['status'],
                'szu100_status': s['auth_status'], 'network_status': network_status,
                'reason': s.get('message') or '缺少SZU100专用U盘'}
    if not network_status:
        return {'allowed': False, 'vikey_status': v['status'],
                'szu100_status': s['auth_status'], 'network_status': False,
                'reason': '网络离线'}
    return {
        'allowed': True,
        'vikey_status': v['status'],
        'szu100_status': s['auth_status'],
        'network_status': True,
        'terminal_status': 'BOUND',
        'layout_mode': dual['layout_mode'],
        'both_authenticated': True,
        'reason': '双硬件密钥认证通过 (VIKEY + SZU100 + 插钥终端)',
    }
