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
                        # 携带 next 参数，登录后返回原页面
                        next_url = request.full_path.rstrip('?') if request.full_path else request.path
                        return redirect(url_for('login_page', next=next_url))
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
                    'version': '7.2.0',
                    'system_status': '运行中',
                    'system_notice': '',
                    'user_count': 0,
                    'exam_count': 0,
                    'online_users': 0,
                    'latest_version': {'title': 'Intelligent Modular Enhanced Edition'},
                    'version_info': {
                        'release_date': '2026-07-07',
                        'build_number': '7100',
                        'codename': 'Intelligent Modular Enhanced Edition'
                    }
                }

                try:
                    notice_db = os.path.join(SPLIT_DB_DIR, 'system.db')
                    if os.path.exists(notice_db):
                        conn = sqlite3.connect(notice_db, timeout=3)
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT content FROM system_notices 
                            WHERE status = 'active' 
                            ORDER BY priority DESC, created_at DESC 
                            LIMIT 1
                        """)
                        notice = cursor.fetchone()
                        if notice:
                            vars['system_notice'] = notice['content']
                        conn.close()
                except Exception:
                    pass

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

            # 根据角色获取重定向地址
            def _get_role_redirect(role):
                redirect_map = {
                    'student': '/exam_system',
                    'student_vip': '/exam_system',
                    'designer': '/arduino',
                    'teacher': '/teacher',
                    'admin': '/settings',
                    'super_admin': '/super_admin_dashboard',
                    'hardware_admin': '/super_admin_dashboard',
                    'hardware_vikey_admin': '/super_admin_dashboard',
                }
                return redirect_map.get(role, '/dashboard')

            @app.route('/')
            def index_page():
                # 已登录用户重定向到对应仪表板
                if 'user_id' in session:
                    return redirect(_get_role_redirect(session.get('role', 'user')))
                return render_template('index.html', **_get_index_template_vars())

            @app.route('/login')
            def login_page():
                # 已登录用户重定向到对应仪表板
                if 'user_id' in session:
                    return redirect(_get_role_redirect(session.get('role', 'user')))
                return render_template('login.html')

            @app.route('/register')
            def register_page():
                return render_template('register.html')

            # ================ 角色重定向路由（确保登录后能正确跳转） ================
            @app.route('/exam_system')
            @require_login
            def exam_system_page():
                return render_template('exam_system.html')

            @app.route('/exam_system/exams')
            @require_login
            def exam_system_exams_page():
                return render_template('exam_center.html')

            @app.route('/exam_system/tests')
            @require_login
            def exam_system_tests_page():
                return render_template('test_center.html')

            @app.route('/teacher')
            @require_login
            def teacher_page():
                return render_template('teacher.html')

            @app.route('/settings')
            @require_login
            def settings_page():
                return render_template('settings.html')

            @app.route('/super_admin_dashboard')
            @require_login
            def super_admin_dashboard_page():
                return render_template('super_admin_dashboard.html')

            @app.route('/arduino')
            @require_login
            def arduino_page():
                return render_template('arduino.html')

            @app.route('/ai-chat')
            @require_login
            def ai_chat_page():
                return render_template('ai_chat.html')

            @app.route('/k12')
            def k12_page():
                return render_template('k12_education.html')
            
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

                    # 根据角色确定重定向地址 (复用页面路由中定义的函数)
                    role = user['role']
                    try:
                        redirect_url = _get_role_redirect(role)
                    except NameError:
                        # 后备重定向映射
                        redirect_map = {
                            'student': '/exam_system', 'student_vip': '/exam_system',
                            'designer': '/arduino', 'teacher': '/teacher',
                            'admin': '/settings', 'super_admin': '/super_admin_dashboard',
                            'hardware_admin': '/super_admin_dashboard',
                        }
                        redirect_url = redirect_map.get(role, '/dashboard')

                    return jsonify({
                        'success': True,
                        'message': '登录成功',
                        'redirect': redirect_url,
                        'data': {
                            'user_id': user['id'],
                            'username': user['username'],
                            'role': role,
                            'redirect': redirect_url
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

            # ================ 跑马灯通知管理API ================
            def _get_notice_db():
                db_path = os.path.join(SPLIT_DB_DIR, 'system.db')
                conn = sqlite3.connect(db_path, timeout=3)
                conn.row_factory = sqlite3.Row
                return conn

            @app.route('/api/system/notices/marquee/toggle', methods=['POST'])
            def toggle_marquee():
                try:
                    data = request.get_json()
                    enabled = data.get('enabled', False)
                    
                    conn = _get_notice_db()
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT id FROM system_notices WHERE status = 'active' LIMIT 1")
                    active_notice = cursor.fetchone()
                    
                    if enabled:
                        if not active_notice:
                            cursor.execute("SELECT id FROM system_notices WHERE status = 'inactive' LIMIT 1")
                            inactive_notice = cursor.fetchone()
                            if inactive_notice:
                                cursor.execute("UPDATE system_notices SET status = 'active' WHERE id = ?", 
                                              (inactive_notice[0],))
                            else:
                                conn.close()
                                return jsonify({'success': False, 'message': '请先设置通知内容'}), 400
                    else:
                        if active_notice:
                            cursor.execute("UPDATE system_notices SET status = 'inactive' WHERE status = 'active'")
                    
                    conn.commit()
                    conn.close()
                
                    return jsonify({'success': True, 'message': '操作成功'})
                except Exception as e:
                    logger.error(f"Toggle marquee error: {e}")
                    return jsonify({'success': False, 'message': '操作失败'}), 500

            @app.route('/api/system/notices/marquee/update', methods=['POST'])
            def update_marquee():
                try:
                    data = request.get_json()
                    content = data.get('content', '').strip()
                    
                    if not content:
                        return jsonify({'success': False, 'message': '通知内容不能为空'}), 400
                    
                    conn = _get_notice_db()
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT id FROM system_notices WHERE status = 'active' LIMIT 1")
                    active_notice = cursor.fetchone()
                    
                    if active_notice:
                        cursor.execute("UPDATE system_notices SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                                      (content, active_notice[0]))
                    else:
                        cursor.execute("""
                            INSERT INTO system_notices (content, status, priority, created_at, updated_at)
                            VALUES (?, 'inactive', 10, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (content,))
                    
                    conn.commit()
                    conn.close()
                
                    return jsonify({'success': True, 'message': '保存成功，需手动开启显示'})
                except Exception as e:
                    logger.error(f"Update marquee error: {e}")
                    return jsonify({'success': False, 'message': '保存失败'}), 500

            @app.route('/api/system/notices/marquee/generate', methods=['POST'])
            def generate_marquee():
                try:
                    import time
                    current_time = time.strftime("%Y年%m月%d日 %H:%M", time.localtime())
                    data = request.get_json()
                    auto_enable = data.get('auto_enable', False)
                    
                    suggestions = [
                        f"📢 系统维护通知：{current_time}系统正常运行中，欢迎使用！",
                        f"🎉 新版本发布：v7.1.0智能模块化增强版已上线！",
                        f"💡 使用提示：新增AI员工管理功能，可自动扩展智能服务！",
                        f"🔔 重要提醒：请及时备份数据，确保数据安全！",
                        f"🌟 功能更新：学生门户页面全新改版，体验升级！",
                        f"⚡ 性能优化：数据库查询速度提升50%，响应更快！"
                    ]
                    
                    content = suggestions[hash(current_time) % len(suggestions)]
                    status = 'active' if auto_enable else 'inactive'
                    
                    conn = _get_notice_db()
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT id FROM system_notices WHERE status = 'active' LIMIT 1")
                    active_notice = cursor.fetchone()
                    
                    if active_notice:
                        cursor.execute("UPDATE system_notices SET content = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                                      (content, status, active_notice[0]))
                    else:
                        cursor.execute("""
                            INSERT INTO system_notices (content, status, priority, created_at, updated_at)
                            VALUES (?, ?, 10, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (content, status))
                    
                    conn.commit()
                    conn.close()
                
                    return jsonify({'success': True, 'message': '生成成功' + ('，已自动开启显示' if auto_enable else '，需手动开启显示'), 'content': content})
                except Exception as e:
                    logger.error(f"Generate marquee error: {e}")
                    return jsonify({'success': False, 'message': '生成失败'}), 500

            @app.route('/api/system/notices/marquee/push', methods=['POST'])
            def push_marquee():
                try:
                    data = request.get_json()
                    content = data.get('content', '').strip()
                    priority = data.get('priority', 10)
                    
                    if not content:
                        return jsonify({'success': False, 'message': '消息内容不能为空'}), 400
                    
                    conn = _get_notice_db()
                    cursor = conn.cursor()
                    
                    cursor.execute("UPDATE system_notices SET status = 'inactive' WHERE status = 'active'")
                    
                    cursor.execute("""
                        INSERT INTO system_notices (content, status, priority, created_at, updated_at)
                        VALUES (?, 'active', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (content, priority))
                    
                    conn.commit()
                    conn.close()
                
                    return jsonify({'success': True, 'message': '消息已推送，跑马灯已自动打开', 'content': content})
                except Exception as e:
                    logger.error(f"Push marquee error: {e}")
                    return jsonify({'success': False, 'message': '推送失败'}), 500

            # ================ 移动端管理API ================
            @app.route('/api/mobile/detect', methods=['GET'])
            def mobile_detect():
                user_agent = request.headers.get('User-Agent', '')
                is_mobile = any(keyword in user_agent.lower() for keyword in ['mobile', 'android', 'iphone', 'ipad', 'tablet', 'touch'])
                is_ios = any(keyword in user_agent.lower() for keyword in ['iphone', 'ipad', 'ios'])
                is_android = 'android' in user_agent.lower()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'is_mobile': is_mobile,
                        'is_ios': is_ios,
                        'is_android': is_android,
                        'user_agent': user_agent[:200],
                        'recommended_view': 'mobile' if is_mobile else 'desktop'
                    }
                })

            @app.route('/api/mobile/config', methods=['GET'])
            def mobile_config():
                try:
                    conn = _get_notice_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT config_key, config_value, description FROM mobile_config")
                    configs = {}
                    for row in cursor.fetchall():
                        configs[row['config_key']] = {
                            'value': row['config_value'],
                            'description': row['description']
                        }
                    conn.close()
                    return jsonify({'success': True, 'data': configs})
                except Exception as e:
                    logger.error(f"Mobile config error: {e}")
                    return jsonify({'success': False, 'message': '获取配置失败'}), 500

            @app.route('/api/mobile/device/register', methods=['POST'])
            def register_device():
                try:
                    data = request.get_json()
                    device_id = data.get('device_id', '')
                    device_type = data.get('device_type', 'mobile')
                    device_name = data.get('device_name', '')
                    os_type = data.get('os_type', '')
                    os_version = data.get('os_version', '')
                    app_version = data.get('app_version', '')
                    push_token = data.get('push_token', '')
                    
                    if not device_id:
                        return jsonify({'success': False, 'message': '设备ID不能为空'}), 400
                    
                    user_id = session.get('user_id') if 'user_id' in session else None
                    
                    conn = _get_notice_db()
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT id FROM user_devices WHERE device_id = ?", (device_id,))
                    if cursor.fetchone():
                        cursor.execute("""
                            UPDATE user_devices SET device_type=?, device_name=?, os_type=?, os_version=?, 
                            app_version=?, push_token=?, last_active_at=CURRENT_TIMESTAMP, is_active=1, updated_at=CURRENT_TIMESTAMP
                            WHERE device_id = ?
                        """, (device_type, device_name, os_type, os_version, app_version, push_token, device_id))
                    else:
                        cursor.execute("""
                            INSERT INTO user_devices (user_id, device_id, device_type, device_name, os_type, 
                            os_version, app_version, push_token, last_active_at, is_active)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                        """, (user_id, device_id, device_type, device_name, os_type, os_version, app_version, push_token))
                    
                    conn.commit()
                    conn.close()
                    return jsonify({'success': True, 'message': '设备注册成功'})
                except Exception as e:
                    logger.error(f"Register device error: {e}")
                    return jsonify({'success': False, 'message': '设备注册失败'}), 500

            # ================ 通知推送API ================
            @app.route('/api/notification/send', methods=['POST'])
            def send_notification():
                try:
                    data = request.get_json()
                    recipient_id = data.get('recipient_id')
                    title = data.get('title', '')
                    content = data.get('content', '')
                    priority = data.get('priority', 10)
                    push_type = data.get('push_type', 'system')
                    
                    if not title or not content:
                        return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
                    
                    conn = _get_notice_db()
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO notification_queue (recipient_id, recipient_type, title, content, 
                        priority, status, push_type)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    """, (recipient_id, 'user' if recipient_id else 'broadcast', title, content, priority, push_type))
                    
                    conn.commit()
                    conn.close()
                    return jsonify({'success': True, 'message': '通知已加入推送队列'})
                except Exception as e:
                    logger.error(f"Send notification error: {e}")
                    return jsonify({'success': False, 'message': '发送失败'}), 500

            @app.route('/api/notification/queue', methods=['GET'])
            def get_notification_queue():
                try:
                    conn = _get_notice_db()
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, recipient_id, title, content, priority, status, push_type, 
                        sent_at, retry_count, created_at 
                        FROM notification_queue 
                        ORDER BY priority DESC, created_at DESC 
                        LIMIT 50
                    """)
                    queue = []
                    for row in cursor.fetchall():
                        queue.append({
                            'id': row['id'],
                            'recipient_id': row['recipient_id'],
                            'title': row['title'],
                            'content': row['content'],
                            'priority': row['priority'],
                            'status': row['status'],
                            'push_type': row['push_type'],
                            'sent_at': row['sent_at'],
                            'retry_count': row['retry_count'],
                            'created_at': row['created_at']
                        })
                    conn.close()
                    return jsonify({'success': True, 'data': queue})
                except Exception as e:
                    logger.error(f"Get notification queue error: {e}")
                    return jsonify({'success': False, 'message': '获取队列失败'}), 500

            # ================ 题库拓展API ================
            @app.route('/api/questions/categories', methods=['GET'])
            def get_question_categories():
                try:
                    db_path = os.path.join(SPLIT_DB_DIR, 'question.db')
                    conn = sqlite3.connect(db_path, timeout=3)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    stage = request.args.get('stage', '')
                    subject = request.args.get('subject', '')
                    
                    query = "SELECT * FROM question_categories_ext WHERE is_active = 1"
                    params = []
                    if stage:
                        query += " AND education_stage = ?"
                        params.append(stage)
                    if subject:
                        query += " AND subject = ?"
                        params.append(subject)
                    query += " ORDER BY sort_order, category_name"
                    
                    cursor.execute(query, params)
                    categories = []
                    for row in cursor.fetchall():
                        categories.append({
                            'id': row['id'],
                            'category_name': row['category_name'],
                            'parent_id': row['parent_id'],
                            'level': row['level'],
                            'subject': row['subject'],
                            'education_stage': row['education_stage'],
                            'grade': row['grade'],
                            'semester': row['semester'],
                            'total_questions': row['total_questions']
                        })
                    conn.close()
                    return jsonify({'success': True, 'data': categories})
                except Exception as e:
                    logger.error(f"Get categories error: {e}")
                    return jsonify({'success': False, 'message': '获取分类失败'}), 500

            @app.route('/api/questions/tags', methods=['GET'])
            def get_question_tags():
                try:
                    db_path = os.path.join(SPLIT_DB_DIR, 'question.db')
                    conn = sqlite3.connect(db_path, timeout=3)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM question_tags ORDER BY usage_count DESC")
                    tags = []
                    for row in cursor.fetchall():
                        tags.append({
                            'id': row['id'],
                            'tag_name': row['tag_name'],
                            'tag_color': row['tag_color'],
                            'usage_count': row['usage_count']
                        })
                    conn.close()
                    return jsonify({'success': True, 'data': tags})
                except Exception as e:
                    logger.error(f"Get tags error: {e}")
                    return jsonify({'success': False, 'message': '获取标签失败'}), 500

            # ================ AI模型库API ================
            @app.route('/api/ai/models', methods=['GET'])
            def get_ai_models():
                try:
                    db_path = os.path.join(SPLIT_DB_DIR, 'ai.db')
                    conn = sqlite3.connect(db_path, timeout=3)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM ai_model_performance ORDER BY performance_score DESC")
                    models = []
                    for row in cursor.fetchall():
                        models.append({
                            'model_id': row['model_id'],
                            'model_name': row['model_name'],
                            'provider': row['provider'],
                            'model_type': row['model_type'],
                            'performance_score': row['performance_score'],
                            'response_time_ms': row['response_time_ms'],
                            'success_rate': row['success_rate'],
                            'total_requests': row['total_requests'],
                            'status': row['status']
                        })
                    conn.close()
                    return jsonify({'success': True, 'data': models})
                except Exception as e:
                    logger.error(f"Get AI models error: {e}")
                    return jsonify({'success': False, 'message': '获取模型失败'}), 500

            @app.route('/api/ai/nodes', methods=['GET'])
            def get_ai_nodes():
                try:
                    db_path = os.path.join(SPLIT_DB_DIR, 'ai.db')
                    conn = sqlite3.connect(db_path, timeout=3)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM ai_node_status ORDER BY node_type, status")
                    nodes = []
                    for row in cursor.fetchall():
                        nodes.append({
                            'node_id': row['node_id'],
                            'node_name': row['node_name'],
                            'node_type': row['node_type'],
                            'address': row['address'],
                            'status': row['status'],
                            'load': row['load'],
                            'capacity': row['capacity'],
                            'active_tasks': row['active_tasks'],
                            'last_heartbeat': row['last_heartbeat']
                        })
                    conn.close()
                    return jsonify({'success': True, 'data': nodes})
                except Exception as e:
                    logger.error(f"Get AI nodes error: {e}")
                    return jsonify({'success': False, 'message': '获取节点失败'}), 500

            # ================ 系统状态API ================
            @app.route('/api/system/status/extended', methods=['GET'])
            def system_status_extended():
                try:
                    import psutil
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    network = psutil.net_io_counters()
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'cpu': {
                                'percent': cpu_percent,
                                'cores': psutil.cpu_count(),
                                'threads': psutil.cpu_count(logical=True)
                            },
                            'memory': {
                                'total': memory.total,
                                'used': memory.used,
                                'available': memory.available,
                                'percent': memory.percent
                            },
                            'disk': {
                                'total': disk.total,
                                'used': disk.used,
                                'free': disk.free,
                                'percent': disk.percent
                            },
                            'network': {
                                'bytes_sent': network.bytes_sent,
                                'bytes_recv': network.bytes_recv,
                                'packets_sent': network.packets_sent,
                                'packets_recv': network.packets_recv
                            },
                            'process': {
                                'count': len(psutil.pids()),
                                'pid': os.getpid()
                            }
                        }
                    })
                except Exception as e:
                    logger.error(f"System status error: {e}")
                    return jsonify({'success': False, 'message': '获取状态失败'}), 500

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
