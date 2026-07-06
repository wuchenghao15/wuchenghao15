#!/usr/bin/env python3
"""
功能模块加载器 - 按阶段加载系统功能模块
阶段1: 认证与基础路由
阶段2: API接口模块
阶段3: 蓝图模块
阶段4: 服务模块
阶段5: AI引擎模块
阶段6: 中间件模块
"""

import os
import sys
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ModuleLoader:
    """功能模块加载器"""

    def __init__(self, app):
        self.app = app
        self.loaded_modules = {}
        self.failed_modules = {}
        self.loading_order = []

    def _import_safe(self, module_path: str, attribute: str = None):
        """安全导入模块"""
        try:
            module = __import__(module_path, fromlist=['*'])
            if attribute:
                return getattr(module, attribute, None)
            return module
        except Exception as e:
            logger.warning(f"导入模块失败 {module_path}: {e}")
            return None

    def _register_module(self, name: str, status: str, details: str = None):
        """注册模块状态"""
        self.loading_order.append(name)
        self.loaded_modules[name] = {
            'status': status,
            'details': details,
            'loaded_at': datetime.now().isoformat()
        }

    # ==================== 阶段1: 认证与基础路由 ====================
    def load_auth_and_base_routes(self) -> bool:
        """阶段1: 加载认证与基础路由"""
        logger.info("=" * 60)
        logger.info("[模块 1/6] 加载认证与基础路由...")
        logger.info("=" * 60)

        loaded = 0
        failed = 0

        # 导入基础工具
        try:
            from functools import wraps
            from flask import jsonify, render_template, request, redirect, session, url_for, make_response

            # ================ 认证装饰器 ================
            def require_login(f):
                @wraps(f)
                def decorated_function(*args, **kwargs):
                    if 'user_id' not in session:
                        if request.path.startswith('/api/'):
                            return jsonify({'success': False, 'message': '请先登录', 'code': 401}), 401
                        return redirect(url_for('login_page'))
                    return f(*args, **kwargs)
                return decorated_function

            def require_admin(f):
                @wraps(f)
                def decorated_function(*args, **kwargs):
                    if 'user_id' not in session:
                        if request.path.startswith('/api/'):
                            return jsonify({'success': False, 'message': '请先登录', 'code': 401}), 401
                        return redirect(url_for('login_page'))
                    role = session.get('role', 'user')
                    if role not in ['admin', 'super_admin']:
                        if request.path.startswith('/api/'):
                            return jsonify({'success': False, 'message': '权限不足', 'code': 403}), 403
                        return render_template('error/403.html'), 403
                    return f(*args, **kwargs)
                return decorated_function

            def require_super_admin(f):
                @wraps(f)
                def decorated_function(*args, **kwargs):
                    if 'user_id' not in session:
                        if request.path.startswith('/api/'):
                            return jsonify({'success': False, 'message': '请先登录', 'code': 401}), 401
                        return redirect(url_for('login_page'))
                    role = session.get('role', 'user')
                    if role != 'super_admin':
                        if request.path.startswith('/api/'):
                            return jsonify({'success': False, 'message': '需要超级管理员权限', 'code': 403}), 403
                        return render_template('error/403.html'), 403
                    return f(*args, **kwargs)
                return decorated_function

            self.app.require_login = require_login
            self.app.require_admin = require_admin
            self.app.require_super_admin = require_super_admin

            # 设置全局可用
            import __main__
            __main__.require_login = require_login
            __main__.require_admin = require_admin

            self._register_module('auth_decorators', 'success', '认证装饰器加载成功')
            loaded += 1

        except Exception as e:
            logger.error(f"加载认证装饰器失败: {e}")
            failed += 1

        # ================ 页面路由 ================
        try:
            app = self.app
            from flask import render_template, redirect, session, url_for
            import sqlite3

            SPLIT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases')

            def _get_index_template_vars():
                """获取首页模板所需的变量"""
                vars = {
                    'version': '7.0.0',
                'system_status': '运行中',
                'system_notice': '欢迎使用 MTSCOS AI 智能考试系统 v7.0.0 (Intelligent Modular Edition)',
                    'user_count': 0,
                    'exam_count': 0,
                    'online_users': 0,
                    'latest_version': {'title': 'Intelligent Modular Edition'},
                    'version_info': {
                        'release_date': '2026-07-07',
                        'build_number': '7000',
                        'codename': 'Intelligent Modular Edition'
                    }
                }

                # 尝试从数据库获取真实数据
                try:
                    auth_db = os.path.join(SPLIT_DB_DIR, 'auth.db')
                    if os.path.exists(auth_db):
                        conn = sqlite3.connect(auth_db, timeout=3)
                        cursor = conn.cursor()
                        cursor.execute('SELECT COUNT(*) FROM users')
                        vars['user_count'] = cursor.fetchone()[0]
                        conn.close()
                except Exception:
                    pass

                try:
                    exam_db = os.path.join(SPLIT_DB_DIR, 'exam.db')
                    if os.path.exists(exam_db):
                        conn = sqlite3.connect(exam_db, timeout=3)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exams'")
                        if cursor.fetchone():
                            cursor.execute('SELECT COUNT(*) FROM exams')
                            vars['exam_count'] = cursor.fetchone()[0]
                        conn.close()
                except Exception:
                    pass

                return vars

            @app.route('/')
            def index_page():
                return render_template('index.html', **_get_index_template_vars())

            @app.route('/login')
            def login_page():
                return render_template('login.html')

            @app.route('/register')
            def register_page():
                return render_template('register.html')

            @app.route('/terms')
            def terms_page():
                return render_template('terms.html')

            @app.route('/privacy')
            def privacy_page():
                return render_template('privacy.html')

            @app.route('/logout')
            def logout_page():
                session.clear()
                return redirect('/login')

            self._register_module('base_pages', 'success', '基础页面路由加载成功')
            loaded += 1

        except Exception as e:
            logger.error(f"加载基础页面路由失败: {e}")
            failed += 1

        # ================ 认证API ================
        try:
            app = self.app
            import hashlib
            import sqlite3
            import json
            import random
            from datetime import datetime
            from flask import request, session, jsonify

            SPLIT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases')

            def get_auth_db():
                auth_db = os.path.join(SPLIT_DB_DIR, 'auth.db')
                conn = sqlite3.connect(auth_db, timeout=10)
                conn.row_factory = sqlite3.Row
                return conn

            @app.route('/auth/login', methods=['POST'])
            def api_login():
                try:
                    data = request.get_json() or {}
                    username = data.get('username', '').strip()
                    password = data.get('password', '')

                    if not username or not password:
                        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400

                    conn = get_auth_db()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, username, password, role, is_active FROM users WHERE username = ? LIMIT 1",
                        (username,)
                    )
                    user = cursor.fetchone()
                    conn.close()

                    if not user:
                        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

                    # 支持多种密码格式
                    password_sha256 = hashlib.sha256(password.encode()).hexdigest()
                    password_b64 = __import__('base64').b64encode(
                        hashlib.sha256(password.encode()).digest()
                    ).decode()

                    if user['password'] != password_sha256 and user['password'] != password_b64:
                        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

                    if not user['is_active']:
                        return jsonify({'success': False, 'message': '账号已被禁用'}), 403

                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['login_time'] = datetime.now().isoformat()

                    return jsonify({
                        'success': True,
                        'message': '登录成功',
                        'data': {
                            'user_id': user['id'],
                            'username': user['username'],
                            'role': user['role']
                        }
                    })

                except Exception as e:
                    logger.error(f"登录失败: {e}")
                    return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500

            @app.route('/auth/register', methods=['POST'])
            def api_register():
                try:
                    data = request.get_json() or {}
                    username = data.get('username', '').strip()
                    password = data.get('password', '')
                    email = data.get('email', '').strip()

                    if not username or not password:
                        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400

                    if len(password) < 6:
                        return jsonify({'success': False, 'message': '密码长度不能少于6位'}), 400

                    conn = get_auth_db()
                    cursor = conn.cursor()

                    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                    if cursor.fetchone():
                        conn.close()
                        return jsonify({'success': False, 'message': '用户名已存在'}), 400

                    password_hash = hashlib.sha256(password.encode()).hexdigest()

                    cursor.execute(
                        "INSERT INTO users (username, password, email, role, is_active, created_at, updated_at) VALUES (?, ?, ?, 'user', 1, ?, ?)",
                        (username, password_hash, email, datetime.now().isoformat(), datetime.now().isoformat())
                    )
                    conn.commit()
                    user_id = cursor.lastrowid
                    conn.close()

                    return jsonify({
                        'success': True,
                        'message': '注册成功',
                        'data': {'user_id': user_id, 'username': username}
                    })

                except Exception as e:
                    logger.error(f"注册失败: {e}")
                    return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

            @app.route('/auth/logout', methods=['GET', 'POST'])
            def api_logout():
                session.clear()
                # GET 请求重定向到登录页，POST 请求返回 JSON
                from flask import request as flask_request
                if flask_request.method == 'GET':
                    return redirect('/login')
                return jsonify({'success': True, 'message': '已退出登录'})

            @app.route('/auth/check')
            def api_auth_check():
                if 'user_id' in session:
                    return jsonify({
                        'success': True,
                        'data': {
                            'user_id': session.get('user_id'),
                            'username': session.get('username'),
                            'role': session.get('role')
                        }
                    })
                return jsonify({'success': False, 'message': '未登录'}), 401

            self._register_module('auth_api', 'success', '认证API加载成功')
            loaded += 1

        except Exception as e:
            logger.error(f"加载认证API失败: {e}")
            failed += 1

        logger.info(f"认证与基础路由加载完成: 成功 {loaded} 个, 失败 {failed} 个")
        return failed == 0

    # ==================== 阶段2: API接口模块 ====================
    def load_api_modules(self) -> bool:
        """阶段2: 加载API接口模块（后台线程加载大量API）"""
        logger.info("=" * 60)
        logger.info("[模块 2/6] 加载API接口模块...")
        logger.info("=" * 60)

        app = self.app
        app.api_loading_status = {'loading': True, 'loaded': 0, 'failed': 0}

        def _load_apis_background():
            """后台加载API模块"""
            loaded = 0
            failed = 0

            api_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'api')
            if not os.path.exists(api_dir):
                app.api_loading_status['loading'] = False
                return

            api_files = [f for f in os.listdir(api_dir)
                         if f.endswith('.py') and not f.startswith('__') and f != 'middleware.py']
            logger.info(f"发现 {len(api_files)} 个API模块文件 (后台加载中...)")

            for api_file in sorted(api_files):
                module_name = api_file.replace('.py', '')
                try:
                    module_path = f'app.api.{module_name}'
                    module = __import__(module_path, fromlist=['bp', 'blueprint'])
                    bp = getattr(module, 'bp', None) or getattr(module, 'blueprint', None)

                    if bp and hasattr(bp, 'name'):
                        url_prefix = getattr(bp, 'url_prefix', None) or f'/api/{module_name.replace("_api", "")}'
                        app.register_blueprint(bp, url_prefix=url_prefix)
                        loaded += 1
                        self._register_module(f'api_{module_name}', 'success', f'蓝图注册: {url_prefix}')
                    else:
                        logger.debug(f"  - API模块无蓝图: {module_name}")

                except Exception as e:
                    logger.debug(f"  ✗ API模块加载失败 {module_name}: {e}")
                    self.failed_modules[f'api_{module_name}'] = str(e)
                    failed += 1

                # 每加载10个记录一次进度
                if (loaded + failed) % 10 == 0:
                    logger.info(f"  API加载进度: {loaded + failed}/{len(api_files)}")

            app.api_loading_status['loading'] = False
            app.api_loading_status['loaded'] = loaded
            app.api_loading_status['failed'] = failed
            logger.info(f"API接口模块后台加载完成: 成功 {loaded} 个, 失败 {failed} 个")

        # 后台线程加载大量API
        threading.Thread(target=_load_apis_background, daemon=True).start()

        self._register_module('api_modules', 'background', 'API模块后台加载中')
        logger.info("API接口模块已启动后台加载（不阻塞主启动流程）")
        return True

    # ==================== 阶段3: 蓝图模块 ====================
    def load_blueprint_modules(self) -> bool:
        """阶段3: 加载蓝图模块（后台线程）"""
        logger.info("=" * 60)
        logger.info("[模块 3/6] 加载蓝图模块...")
        logger.info("=" * 60)

        app = self.app
        app.bp_loading_status = {'loading': True, 'loaded': 0, 'failed': 0}

        def _load_blueprints_background():
            """后台加载蓝图模块"""
            loaded = 0
            failed = 0

            bp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'blueprints')
            if not os.path.exists(bp_dir):
                app.bp_loading_status['loading'] = False
                return

            bp_files = [f for f in os.listdir(bp_dir)
                        if f.endswith('.py') and not f.startswith('__')]
            logger.info(f"发现 {len(bp_files)} 个蓝图文件 (后台加载中...)")

            for bp_file in sorted(bp_files):
                module_name = bp_file.replace('.py', '')
                try:
                    module_path = f'app.blueprints.{module_name}'
                    module = __import__(module_path, fromlist=['bp', 'blueprint'])
                    bp = getattr(module, 'bp', None) or getattr(module, 'blueprint', None)

                    if bp and hasattr(bp, 'name'):
                        url_prefix = getattr(bp, 'url_prefix', None) or f'/{module_name.replace("_bp", "")}'
                        app.register_blueprint(bp, url_prefix=url_prefix)
                        loaded += 1
                        self._register_module(f'blueprint_{module_name}', 'success', f'蓝图注册: {url_prefix}')
                    else:
                        logger.debug(f"  - 蓝图无注册: {module_name}")

                except Exception as e:
                    logger.debug(f"  ✗ 蓝图加载失败 {module_name}: {e}")
                    self.failed_modules[f'blueprint_{module_name}'] = str(e)
                    failed += 1

            app.bp_loading_status['loading'] = False
            app.bp_loading_status['loaded'] = loaded
            app.bp_loading_status['failed'] = failed
            logger.info(f"蓝图模块后台加载完成: 成功 {loaded} 个, 失败 {failed} 个")

        threading.Thread(target=_load_blueprints_background, daemon=True).start()

        self._register_module('blueprint_modules', 'background', '蓝图模块后台加载中')
        logger.info("蓝图模块已启动后台加载（不阻塞主启动流程）")
        return True

    # ==================== 阶段4: 服务模块 ====================
    def load_service_modules(self) -> bool:
        """阶段4: 加载服务模块（后台初始化）"""
        logger.info("=" * 60)
        logger.info("[模块 4/6] 加载服务模块...")
        logger.info("=" * 60)

        loaded = 0
        failed = 0
        app = self.app

        # 在app上存储服务管理器引用
        app.services = {}

        # 尝试加载关键服务
        services_to_load = [
            ('cache_service', '缓存服务'),
            ('log_manager', '日志管理'),
            ('notification_service', '通知服务'),
        ]

        for svc_name, svc_desc in services_to_load:
            try:
                module_path = f'app.services.{svc_name}'
                module = __import__(module_path, fromlist=['*'])
                app.services[svc_name] = module
                loaded += 1
                self._register_module(f'service_{svc_name}', 'success', svc_desc)
                logger.info(f"  ✓ 服务: {svc_name} - {svc_desc}")
            except Exception as e:
                logger.debug(f"  - 服务不可用: {svc_name}: {e}")
                failed += 1

        logger.info(f"服务模块加载完成: 成功 {loaded} 个, 失败 {failed} 个")
        return True

    # ==================== 阶段5: AI引擎模块 ====================
    def load_ai_engine_modules(self) -> bool:
        """阶段5: 加载AI引擎模块（后台线程）"""
        logger.info("=" * 60)
        logger.info("[模块 5/6] 加载AI引擎模块（后台线程）...")
        logger.info("=" * 60)

        app = self.app
        app.ai_status = {'initializing': True}

        def _load_ai_in_background():
            """后台加载AI引擎"""
            loaded_count = 0
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                sys.path.insert(0, base_dir)

                # AI员工加载器
                try:
                    from ai_engines.all_ai_employees_loader import load_all_ai_employees, get_all_ai_employees_status
                    ai_status = load_all_ai_employees()
                    app.ai_status['employees'] = ai_status
                    loaded_count += 1
                    logger.info("[AI] AI员工加载完成")
                except Exception as e:
                    logger.warning(f"[AI] AI员工加载失败: {e}")

                # 检索模型
                try:
                    from ai_engines.ai_search_query_model import init_search_models
                    init_search_models()
                    loaded_count += 1
                    logger.info("[AI] 检索模型加载完成")
                except Exception as e:
                    logger.warning(f"[AI] 检索模型加载失败: {e}")

                # API数据库管理器
                try:
                    from ai_engines.ai_api_database_manager import init_api_db_manager, scan_and_register_apis
                    init_api_db_manager()
                    scan_and_register_apis(app)
                    loaded_count += 1
                    logger.info("[AI] API数据库管理器加载完成")
                except Exception as e:
                    logger.warning(f"[AI] API数据库管理器加载失败: {e}")

                # 路由数据库管理器
                try:
                    from ai_engines.ai_routes_database_manager import init_routes_db_manager, scan_and_register_routes
                    init_routes_db_manager()
                    scan_and_register_routes(app)
                    loaded_count += 1
                    logger.info("[AI] 路由数据库管理器加载完成")
                except Exception as e:
                    logger.warning(f"[AI] 路由数据库管理器加载失败: {e}")

            except Exception as e:
                logger.error(f"[AI] 后台加载失败: {e}")
            finally:
                app.ai_status['initializing'] = False
                app.ai_status['loaded'] = loaded_count
                logger.info(f"[AI] AI引擎加载完成: {loaded_count} 个模块")

        # 后台线程加载
        threading.Thread(target=_load_ai_in_background, daemon=True).start()
        self._register_module('ai_engine', 'background', 'AI引擎后台加载中')

        logger.info("AI引擎模块已启动后台加载")
        return True

    # ==================== 阶段6: 中间件模块 ====================
    def load_middleware_modules(self) -> bool:
        """阶段6: 加载中间件模块"""
        logger.info("=" * 60)
        logger.info("[模块 6/6] 加载中间件模块...")
        logger.info("=" * 60)

        loaded = 0
        failed = 0
        app = self.app

        # 导入Flask请求对象
        from flask import request as flask_request

        # 注册请求计时中间件
        try:
            import time

            @app.before_request
            def before_request_timer():
                flask_request._start_time = time.time()

            @app.after_request
            def after_request_timer(response):
                if hasattr(flask_request, '_start_time'):
                    duration = time.time() - flask_request._start_time
                    response.headers['X-Response-Time'] = f'{duration:.3f}s'
                return response

            loaded += 1
            self._register_module('middleware_timer', 'success', '请求计时中间件')
        except Exception as e:
            logger.warning(f"计时中间件加载失败: {e}")
            failed += 1

        # 注册安全头中间件
        try:
            @app.after_request
            def security_headers_mw(response):
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                return response

            loaded += 1
            self._register_module('middleware_security', 'success', '安全头中间件')
        except Exception as e:
            logger.warning(f"安全头中间件加载失败: {e}")
            failed += 1

        # 尝试加载app/middlewares下的中间件
        mw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'middlewares')
        if os.path.exists(mw_dir):
            mw_files = [f for f in os.listdir(mw_dir)
                        if f.endswith('.py') and not f.startswith('__')]
            for mw_file in sorted(mw_files)[:10]:
                try:
                    module_name = mw_file.replace('.py', '')
                    module_path = f'app.middlewares.{module_name}'
                    module = __import__(module_path, fromlist=['*'])

                    # 查找init_middleware函数
                    init_func = getattr(module, 'init_middleware', None) or getattr(module, 'register', None)
                    if init_func:
                        init_func(app)
                        loaded += 1
                        logger.info(f"  ✓ 中间件: {module_name}")
                except Exception as e:
                    logger.debug(f"  - 中间件加载失败 {mw_file}: {e}")
                    failed += 1

        logger.info(f"中间件模块加载完成: 成功 {loaded} 个, 失败 {failed} 个")
        return True

    # ==================== 完整加载流程 ====================
    def load_all_modules(self) -> Dict[str, Any]:
        """加载所有功能模块（6个阶段）"""
        logger.info("开始加载所有功能模块...")
        start_time = datetime.now()

        results = {
            'total_stages': 6,
            'completed_stages': 0,
            'loaded_modules': 0,
            'failed_modules': 0,
            'stages': []
        }

        # 阶段1: 认证与基础路由
        stage1_ok = self.load_auth_and_base_routes()
        results['stages'].append({'stage': 1, 'name': '认证与基础路由', 'success': stage1_ok})
        results['completed_stages'] += 1

        # 阶段2: API接口模块
        stage2_ok = self.load_api_modules()
        results['stages'].append({'stage': 2, 'name': 'API接口模块', 'success': stage2_ok})
        results['completed_stages'] += 1

        # 阶段3: 蓝图模块
        stage3_ok = self.load_blueprint_modules()
        results['stages'].append({'stage': 3, 'name': '蓝图模块', 'success': stage3_ok})
        results['completed_stages'] += 1

        # 阶段4: 服务模块
        stage4_ok = self.load_service_modules()
        results['stages'].append({'stage': 4, 'name': '服务模块', 'success': stage4_ok})
        results['completed_stages'] += 1

        # 阶段5: AI引擎模块
        stage5_ok = self.load_ai_engine_modules()
        results['stages'].append({'stage': 5, 'name': 'AI引擎模块', 'success': stage5_ok})
        results['completed_stages'] += 1

        # 阶段6: 中间件模块
        stage6_ok = self.load_middleware_modules()
        results['stages'].append({'stage': 6, 'name': '中间件模块', 'success': stage6_ok})
        results['completed_stages'] += 1

        # 统计
        results['loaded_modules'] = len([m for m in self.loaded_modules.values() if m['status'] == 'success'])
        results['failed_modules'] = len(self.failed_modules)
        results['elapsed_seconds'] = (datetime.now() - start_time).total_seconds()
        results['module_list'] = list(self.loaded_modules.keys())
        results['failed_list'] = list(self.failed_modules.keys())

        logger.info("=" * 60)
        logger.info(f"功能模块加载完成！")
        logger.info(f"  完成阶段: {results['completed_stages']}/{results['total_stages']}")
        logger.info(f"  成功模块: {results['loaded_modules']}")
        logger.info(f"  失败模块: {results['failed_modules']}")
        logger.info(f"  加载耗时: {results['elapsed_seconds']:.2f}秒")
        logger.info("=" * 60)

        return results


def load_all_modules(app):
    """加载所有功能模块（便捷函数）"""
    loader = ModuleLoader(app)
    results = loader.load_all_modules()
    return loader, results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'
    loader, results = load_all_modules(app)
    print(f"\n加载结果: {results}")
