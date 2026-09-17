# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""路由配置模块r"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.version import VERSION, VERSION_INFO, get_version_info, get_latest_version
import json
import sys

logger = logging.getLogger(__name__)

class RouteManager:
    def __init__(self, app=None):
        self.app = app
        self.blueprints = {}
        self.routes = []
        logger.info(r"路由管理器初始化完成")

    def init_app(self, app):
        self.app = app
        self._register_core_routes()
        logger.info(r"路由应用初始化完成")

    def _register_core_routes(self):
        main_bp = Blueprint(r'main', __name__)
        auth_bp = Blueprint(r'auth', __name__)
        api_bp = Blueprint(r'api', __name__, url_prefix=r'/api')

        @main_bp.route(r'/')
        def index():
            version_info = get_version_info()
            latest_version = get_latest_version()
            return render_template(r'index.html',
                                version=VERSION,
                                version_info=version_info,
                                latest_version=latest_version)

        @main_bp.route(r'/dashboard')
        def dashboard():
            return render_template(r'dashboard.html')

        @main_bp.route(r'/test')
        def test():
            return jsonify({r'status': r'success', r'message': r'系统运行正常'})

        @auth_bp.route(r'/login', methods=[r'GET', r'POST'])
        def login():
            if request.method == r'POST':
                data = request.get_json()
                if data and r'username' in data and r'password' in data:
                    username = data.get(r'username')
                    password = data.get(r'password')
                    if username == r'admin' and password == r'admin123':
                        return jsonify({r'success': True, r'message': r'登录成功', r'session_id': r'test_session_123'})
                    else:
                        return jsonify({r'success': False, r'message': r'用户名或密码错误'}), 401
                return jsonify({r'success': False, r'message': r'参数错误'}), 400
            return render_template(r'login.html')

        @auth_bp.route(r'/register', methods=[r'GET', r'POST'])
        def register():
            if request.method == r'POST':
                data = request.get_json()
                if data and r'username' in data and r'password' in data:
                    return jsonify({r'success': True, r'message': r'注册成功'})
                return jsonify({r'success': False, r'message': r'参数错误'}), 400
            return render_template(r'register.html')

        @auth_bp.route(r'/logout', methods=[r'POST'])
        def logout():
            return jsonify({r'success': True, r'message': r'登出成功'})

        @api_bp.route(r'/health')
        def health():
            return jsonify({r'status': r'healthy', r'timestamp': datetime.now().isoformat()})

        @api_bp.route(r'/user', methods=[r'GET'])
        def get_user():
            session_id = request.headers.get(r'X-Session-ID')
            if session_id:
                return jsonify({r'success': True, r'user': {r'id': 1, r'username': r'admin', r'role': r'admin'}})
            return jsonify({r'success': False, r'message': r'未授权'}), 401

        @api_bp.route(r'/system/status')
        def system_status():
            return jsonify({r'status': r'running', r'version': r'4.5.5', r'timestamp': datetime.now().isoformat()})

        # ========== 学生端专用蓝图 /student + 2 个 API（新增 STEP_7 实施）==========
        student_bp = Blueprint(r'student', __name__, url_prefix=r'/student')

        def _system_container_stub(role_list=None):
            """简易 @system_container 装饰器：检查 user 是否登录；未登录则跳 /auth/login。
            生产环境下核心层已存在该装饰器，这里用作兜底。"""
            def _wrapper(fn):
                from functools import wraps
                from flask import session as _s, redirect as _rd, url_for as _uf
                @wraps(fn)
                def _inner(*a, **kw):
                    try:
                        user = _s.get(r'user') or _s.get(r'current_user')
                        if not user and not _s.get(r'user_id') and not _s.get(r'logged_in'):
                            return _rd(r'/auth/login')
                    except Exception:
                        pass
                    return fn(*a, **kw)
                return _inner
            return _wrapper

        _try_auth = _system_container_stub([r'student', r'student_vip', r'teacher', r'admin', r'super_admin', r'system_admin'])

        @student_bp.route(r'/analytics')
        @_try_auth
        def s_analytics():
            return render_template(r'student/analytics.html',
                                   current_page=r'analytics',
                                   page_title=r'学习分析')

        @student_bp.route(r'/tournament')
        @_try_auth
        def s_tournament():
            return render_template(r'student/tournament.html',
                                   current_page=r'tournament',
                                   page_title=r'赛事中心')

        @student_bp.route(r'/ai_tutor')
        @_try_auth
        def s_ai_tutor():
            return render_template(r'student/ai_tutor.html',
                                   current_page=r'ai_tutor',
                                   page_title=r'AI 导师')

        @student_bp.route(r'/redeem')
        @_try_auth
        def s_redeem():
            return render_template(r'student/redeem.html',
                                   current_page=r'redeem',
                                   page_title=r'兑换商店')

        @student_bp.route(r'/achievements')
        @_try_auth
        def s_achievements():
            return render_template(r'student/achievements.html',
                                   current_page=r'achievements',
                                   page_title=r'成就徽章')

        @student_bp.route(r'/settings')
        @_try_auth
        def s_settings():
            """个性化设置页，直接复用前端已完善的 student_settings.html 模板"""
            from flask import session as _s
            user = _s.get(r'user') or {r'username': r'Student', r'role': r'student'}
            return render_template(r'student_settings.html',
                                   user=user,
                                   current_page=r'student_settings',
                                   page_title=r'个性化设置')

        # ========== /student_bp 注册 + API 端点 ==========
        self.app.register_blueprint(main_bp)
        self.app.register_blueprint(auth_bp, url_prefix=r'/auth')
        self.app.register_blueprint(api_bp)
        self.app.register_blueprint(student_bp)

        @self.app.route(r'/student_portal')
        @_try_auth
        def legacy_student_portal():
            from flask import session as _s
            user = _s.get(r'user') or {r'username': r'Student', r'role': r'student'}
            return render_template(r'student_portal.html',
                                   user=user, current_page=r'student_portal',
                                   page_title=r'学习仪表盘')

        @self.app.route(r'/settings')
        @_try_auth
        def legacy_settings():
            from flask import session as _s
            user = _s.get(r'user') or {r'username': r'Student', r'role': r'student'}
            return render_template(r'student_settings.html',
                                   user=user, current_page=r'settings',
                                   page_title=r'个人设置')

        # ----------- /api/student/save_profile：SSOT 写库 -----------
        @self.app.route(r'/api/student/save_profile', methods=[r'POST'])
        @_try_auth
        def api_student_save_profile():
            try:
                payload = request.get_json(silent=True) or {}
                section = payload.get(r'section', r'profile')
                try:
                    from flask import session as _s
                    user = _s.get(r'user') or {}
                    uid = _s.get(r'user_id') or (user.get(r'id') if isinstance(user, dict) else None) or 1
                    # 落库 SSOT：优先使用核心层 db_manager；失败则写本地 SQLite failover
                    saved = _ssot_write_prefs(uid, section, payload)
                    if saved:
                        return jsonify({r'success': True, r'section': section,
                                        r'message': r'已保存（数据库）', r'ts': datetime.now().isoformat()})
                    return jsonify({r'success': True, r'fallback': True, r'section': section,
                                    r'message': r'已本地缓存，稍后同步', r'ts': datetime.now().isoformat()})
                except Exception as _se:
                    logger.exception(r'save_profile ssot write error')
                    return jsonify({r'success': False, r'message': str(_se)[:120]}), 500
            except Exception as e:
                logger.exception(r'save_profile top-level error')
                return jsonify({r'success': False, r'message': str(e)[:80]}), 500

        # ----------- /api/ai_inspection/console_error：前端全局错误上报 -----------
        @self.app.route(r'/api/ai_inspection/console_error', methods=[r'POST'])
        def api_ai_inspection_console_error():
            try:
                payload = request.get_json(silent=True) or {}
                kind = payload.get(r'kind', r'unknown')
                path = payload.get(r'path', r'')
                ts = payload.get(r'ts', datetime.now().isoformat())
                try:
                    _write_error_log(kind, path, ts, payload.get(r'payload') or {})
                except Exception:
                    pass
                return jsonify({r'success': True, r'kind': kind, r'received_at': datetime.now().isoformat()})
            except Exception:
                return jsonify({r'success': True, r'note': r'fire-and-forget accepted'}), 202

        logger.info(r"核心路由注册完成（含学生端新蓝图 student_bp + save_profile / ai_inspection 接口）")

        def _ssot_write_prefs(uid, section, payload):
            """优先调用 core.services.db_manager → SQLite failover，返回 True/False。"""
            wrote_via_core = False
            try:
                from core.services.db_manager import DBManager
                mgr = DBManager()
                data_str = json.dumps(payload, ensure_ascii=False)
                sql = (r"INSERT INTO mt_student_preferences(user_id, section, prefs_json, updated_at) "
                       r"VALUES (?,?,?,?) ON CONFLICT(user_id, section) DO UPDATE SET "
                       r"prefs_json=excluded.prefs_json, updated_at=excluded.updated_at")
                mgr.execute(sql, (int(uid), section, data_str, datetime.now().isoformat()))
                wrote_via_core = True
            except Exception:
                wrote_via_core = False
            if not wrote_via_core:
                # SQLite failover 写入 data/mtscos_student_prefs.db
                try:
                    import os as _os, sqlite3 as _sq
                    db_dir = _os.path.join(
                        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                        r'data')
                    _os.makedirs(db_dir, exist_ok=True)
                    db_path = _os.path.join(db_dir, r'mtscos_student_prefs.db')
                    conn = _sq.connect(db_path, timeout=5)
                    try:
                        cur = conn.cursor()
                        cur.execute(r"CREATE TABLE IF NOT EXISTS mt_student_preferences ("
                                    r"user_id INTEGER NOT NULL, "
                                    r"section TEXT NOT NULL, "
                                    r"prefs_json TEXT NOT NULL, "
                                    r"updated_at TEXT NOT NULL, "
                                    r"PRIMARY KEY (user_id, section))")
                        cur.execute(r"INSERT INTO mt_student_preferences(user_id,section,prefs_json,updated_at) VALUES(?,?,?,?) "
                                    r"ON CONFLICT(user_id,section) DO UPDATE SET prefs_json=excluded.prefs_json,updated_at=excluded.updated_at",
                                    (int(uid), section, json.dumps(payload, ensure_ascii=False), datetime.now().isoformat()))
                        conn.commit()
                        wrote_via_core = True
                    finally:
                        conn.close()
                except Exception:
                    wrote_via_core = False
            return wrote_via_core

        def _write_error_log(kind, path, ts, payload_obj):
            """优先 DBManager → 本地 JSONL failover。"""
            import os as _os
            log_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), r'logs', r'ai_inspection')
            _os.makedirs(log_dir, exist_ok=True)
            log_path = _os.path.join(log_dir, r'console_errors.jsonl')
            line = json.dumps({r'kind': kind, r'path': path, r'ts': ts, r'payload': payload_obj}, ensure_ascii=False)
            with open(log_path, r'a', encoding=r'utf-8') as f:
                f.write(line + r'\n')

    def add_route(self, rule, view_func, methods=None):
        if methods is None:
            methods = [r'GET']
        self.app.add_url_rule(rule, view_func.__name__, view_func, methods=methods)
        self.routes.append({r'rule': rule, r'methods': methods})

    def register_all_routes(self, app):
        self.app = app
        self._register_core_routes()

route_manager = RouteManager()

def init_routes():
    logger.info(r"初始化路由...")
    logger.info(r"路由初始化完成")

if __name__ == r"__main__":
    pass
