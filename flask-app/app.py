#!/usr/bin/env python3
"""
MTSCOS AI Project Main Application
"""

import os
import sys
import logging
import traceback
import argparse
import sqlite3
import hashlib
import time
import json
import random
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from flask import jsonify, render_template, request, redirect, session, make_response, url_for

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置默认的MODEL_PATH环境变量
if 'MODEL_PATH' not in os.environ:
    os.environ['MODEL_PATH'] = './models'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS
from flask import send_from_directory

# 创建Flask应用
app = Flask(__name__)
# 模板文件夹：项目根目录下的 templates 文件夹
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
# 启用模板自动重载（开发环境）
app.config['TEMPLATES_AUTO_RELOAD'] = True
# 静态文件文件夹
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'html', 'assets')
app.static_url_path = '/assets'
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'mtscos_ai_secret_key_2026'  # 设置session密钥

# 注册Jinja2模板全局函数
def get_role_name(role):
    """获取角色中文名"""
    role_names = {
        'super_admin': '超级管理员',
        'admin': '管理员',
        'hardware_admin': '硬件管理员',
        'hardware_vikey_admin': '硬件维凯管理员',
        'teacher': '教师',
        'student': '学生',
        'researcher': '研究员',
        'designer': '设计师',
        'user': '用户',
        'guest': '访客'
    }
    return role_names.get(role, role)

def get_role_tag_class(role):
    """获取角色标签样式类"""
    tag_classes = {
        'super_admin': 'tag-red',
        'admin': 'tag-purple',
        'hardware_admin': 'tag-blue',
        'hardware_vikey_admin': 'tag-blue',
        'teacher': 'tag-green',
        'student': 'tag-blue',
        'researcher': 'tag-yellow',
        'designer': 'tag-orange',
        'user': 'tag-gray',
        'guest': 'tag-gray'
    }
    return tag_classes.get(role, 'tag-gray')

app.jinja_env.globals['get_role_name'] = get_role_name
app.jinja_env.globals['getRoleName'] = get_role_name
app.jinja_env.globals['get_role_tag_class'] = get_role_tag_class
app.jinja_env.globals['getRoleTagClass'] = get_role_tag_class

# 配置CORS支持
CORS(app, resources={r"/*": {"origins": "*"}})

ASSETS_FOLDER = app.static_folder

@app.route('/assets/<path:filename>')
def custom_static(filename):
    return send_from_directory(ASSETS_FOLDER, filename)

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

# 处理 Font Awesome 字体文件请求（/webfonts/ -> /assets/webfonts/）
@app.route('/webfonts/<path:filename>')
def webfonts(filename):
    webfonts_folder = os.path.join(STATIC_FOLDER, 'webfonts')
    if os.path.exists(os.path.join(webfonts_folder, filename)):
        return send_from_directory(webfonts_folder, filename)
    webfonts_folder_assets = os.path.join(ASSETS_FOLDER, 'webfonts')
    return send_from_directory(webfonts_folder_assets, filename)

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' http://localhost:8888 http://127.0.0.1:8888 http://0.0.0.0:8888 http://192.168.0.0/16; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' http://localhost:8888 http://127.0.0.1:8888 http://0.0.0.0:8888 http://192.168.0.0/16; media-src 'self' data:;"
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# 自动路由发现 - 扫描所有API和路由模块
try:
    from app.routes.auto_discover import init_auto_routes
    route_result = init_auto_routes(app)
    logger.info(f"[路由] 自动路由发现完成: 注册 {route_result['registered']} 个蓝图, "
                f"失败 {route_result['failed']} 个, 总路由数 {route_result['total_routes']}")
except Exception as e:
    logger.error(f"[路由] 自动路由发现失败: {str(e)}")

# 角色路由跳转API(需要特殊处理)
try:
    from app.utils.role_router import role_router_bp, create_role_routes
    app.register_blueprint(role_router_bp)
    app = create_role_routes(app)
    logger.info("[路由] 角色路由跳转API注册成功")
except ImportError:
    logger.warning("[路由] 角色路由跳转API未找到，跳过注册")

# 注册拆分后的系统蓝图
try:
    from app.views.exam_system import exam_system_bp
    app.register_blueprint(exam_system_bp)
    logger.info("[路由] 考试系统蓝图注册成功")
except ImportError:
    logger.warning("[路由] 考试系统蓝图未找到，跳过注册")

try:
    from app.views.test_system import test_system_bp
    app.register_blueprint(test_system_bp)
    logger.info("[路由] 测试系统蓝图注册成功")
except ImportError:
    logger.warning("[路由] 测试系统蓝图未找到，跳过注册")

try:
    from app.views.learning_system import learning_system_bp
    app.register_blueprint(learning_system_bp)
    logger.info("[路由] 学习系统蓝图注册成功")
except ImportError:
    logger.warning("[路由] 学习系统蓝图未找到，跳过注册")

try:
    from app.views.user_system import user_system_bp
    app.register_blueprint(user_system_bp)
    logger.info("[路由] 用户信息管理系统蓝图注册成功")
except ImportError:
    logger.warning("[路由] 用户信息管理系统蓝图未找到，跳过注册")

# 初始化动态路由管理器
try:
    from app.utils.dynamic_route_manager import init_dynamic_routes
    init_dynamic_routes(app)
    logger.info("[动态路由] 动态路由管理器初始化成功")
except ImportError as e:
    logger.warning(f"[动态路由] 动态路由管理器未找到，跳过初始化: {e}")

# 注册AI员工批量修复API
try:
    from app.api.ai_fixer_api import ai_fixer_api
    app.register_blueprint(ai_fixer_api)
    logger.info("[AI员工] AI员工批量修复API注册成功")
except ImportError as e:
    logger.warning(f"[AI员工] AI员工批量修复API未找到，跳过注册: {e}")

# 注册用户信息API
try:
    from app.api.user_info_api import user_info_api
    app.register_blueprint(user_info_api)
    logger.info("[用户API] 用户信息API注册成功")
except ImportError as e:
    logger.warning(f"[用户API] 用户信息API未找到，跳过注册: {e}")

# 注册超级管理员数据API
try:
    from app.api.super_admin_data_api import super_admin_data_api
    app.register_blueprint(super_admin_data_api, url_prefix='/api')
    logger.info("[超级管理员] 超级管理员数据API注册成功")
except ImportError as e:
    logger.warning(f"[超级管理员] 超级管理员数据API未找到，跳过注册: {e}")

# 注册AI员工增强系统API
try:
    from app.api.ai_employee_enhanced_api import ai_employee_enhanced_api, init_enhanced_system
    app.register_blueprint(ai_employee_enhanced_api, url_prefix='/api')
    init_enhanced_system()
    logger.info("[AI员工增强] AI员工增强系统API注册成功")
except ImportError as e:
    logger.warning(f"[AI员工增强] AI员工增强系统API未找到，跳过注册: {e}")

# 注册数据完整性与并发控制API
try:
    from app.api.data_integrity_api import data_integrity_api
    app.register_blueprint(data_integrity_api, url_prefix='/api')
    logger.info("[数据完整性] 数据完整性与并发控制API注册成功")
except ImportError as e:
    logger.warning(f"[数据完整性] 数据完整性与并发控制API未找到，跳过注册: {e}")

# 注册AI员工主动运作系统API
try:
    from app.api.proactive_ai_api import proactive_ai_api
    app.register_blueprint(proactive_ai_api, url_prefix='/api')
    logger.info("[主动AI] AI员工主动运作系统API注册成功")
except ImportError as e:
    logger.warning(f"[主动AI] AI员工主动运作系统API未找到，跳过注册: {e}")

# 注册AI脑库系统API
try:
    from app.api.brain_bank_api import brain_bank_api
    app.register_blueprint(brain_bank_api, url_prefix='/api')
    logger.info("[AI脑库] AI脑库系统API注册成功")
except ImportError as e:
    logger.warning(f"[AI脑库] AI脑库系统API未找到，跳过注册: {e}")

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# 初始化权限管理器和会话管理器
from app.utils.permission_manager import init_permission_manager
from app.utils.session_manager import init_session_manager
from app.utils.rule_manager import init_rule_manager
from app.utils.config_manager import init_config_manager
from app.utils.monitor_manager import init_monitor_manager
from app.utils.backup_manager import init_backup_manager
from app.middlewares.access_control import access_control_middleware

# 导入统一规则配置中心
from app.config.unified_rules import init_unified_rules, check_route_permission, check_permission_by_rule

# 初始化权限管理器
init_permission_manager(DATABASE_PATH)

# 初始化会话管理器(超时时间30分钟)
init_session_manager(DATABASE_PATH, timeout_minutes=30)

# 初始化规则管理器(深度绑定系统规则数据库)
init_rule_manager(DATABASE_PATH)

# 初始化统一规则配置中心
init_unified_rules(DATABASE_PATH)

# 初始化配置管理器(实时配置加载,30秒自动重载)
init_config_manager(DATABASE_PATH, auto_reload_interval=30)

# 初始化监控管理器(10秒检查间隔)
init_monitor_manager(DATABASE_PATH, check_interval=10)

# 初始化备份管理器(实时双备份,5分钟自动备份)
init_backup_manager(DATABASE_PATH, auto_backup_interval=300)

# 导入装饰器
try:
    from app.middlewares.access_control import require_login, require_admin, require_super_admin, require_hardware_admin
except ImportError:
    logger.warning("[中间件] 访问控制装饰器未找到，跳过导入")
    require_login = require_admin = require_super_admin = require_hardware_admin = lambda f: f

# 应用访问控制中间件
try:
    app = access_control_middleware(app)
except Exception:
    logger.warning("[中间件] 访问控制中间件应用失败，跳过")

# 导入并应用全局认证中间件
try:
    from app.middlewares.authentication import authentication_middleware, login_user, logout_user, get_redirect_url
    app = authentication_middleware(app)
except ImportError:
    logger.warning("[中间件] 认证中间件未找到，跳过")
    login_user = logout_user = get_redirect_url = lambda *args, **kwargs: None

def verify_password(stored_password, provided_password):
    """验证密码 - 支持多种哈希方式"""
    import hashlib
    import base64
    
    try:
        # 尝试PBKDF2验证
        stored_bytes = base64.b64decode(stored_password)
        if len(stored_bytes) == 32:
            # 可能是直接的SHA-256哈希
            provided_hash = hashlib.sha256(provided_password.encode()).digest()
            return stored_bytes == provided_hash
        
        # 尝试简单比较(用于测试)
        if stored_password == provided_password:
            return True
            
        # PBKDF2格式:salt + hash
        if len(stored_bytes) > 32:
            salt = stored_bytes[:16]
            stored_hash = stored_bytes[16:]
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
            return stored_hash == provided_hash
            
    except Exception as e:
        logger.error(f"密码验证错误: {e}")
    
    # 默认:直接比较(支持明文密码的用户)
    return stored_password == provided_password

def get_user_by_username(username):
    """从数据库获取用户信息"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
        
        if user:
            columns = ['id', 'username', 'email', 'password', 'role', 'created_at', 'updated_at', 'is_active', 'super_admin_approved', 'hardware_admin_approved', 'avatar']
            return dict(zip(columns, user))
        return None
    except Exception as e:
        logger.error(f"查询用户失败: {e}")
        return None

def get_system_settings():
    """获取系统设置"""
    settings = {
        'system_name': 'MTSCOS AI 智能学习评估系统',
        'version': "3.1.0",
        'description': '基于AI的智能学习评估系统,提供个性化学习体验和智能评估功能.',
        'admin_email': 'admin@example.com',
        'maintenance_mode': False,
        'auto_backup': True
    }
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, value FROM system_settings WHERE category = "general"')
            rows = cursor.fetchall()
            for row in rows:
                key, value = row
                if key in settings:
                    if isinstance(settings[key], bool):
                        settings[key] = value.lower() == 'true'
                    elif isinstance(settings[key], int):
                        try:
                            settings[key] = int(value)
                        except Exception:
                            pass
                    else:
                        settings[key] = value
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
    return settings

def get_security_settings():
    """获取安全设置"""
    settings = {
        'max_login_attempts': 5,
        'lockout_duration': 5,
        'session_timeout': 30,
        'password_expiry_days': 90,
        'hardware_auth_enabled': True,
        'two_factor_auth': False,
        'login_logging': True,
        'ip_whitelist': False,
        'sql_protection': True,
        'xss_protection': True
    }
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, value FROM system_settings WHERE category = "security"')
            rows = cursor.fetchall()
            for row in rows:
                key, value = row
                if key in settings:
                    if isinstance(settings[key], bool):
                        settings[key] = value.lower() == 'true'
                    elif isinstance(settings[key], int):
                        try:
                            settings[key] = int(value)
                        except Exception:
                            pass
                    else:
                        settings[key] = value
    except Exception as e:
        logger.error(f"获取安全设置失败: {e}")
    return settings

def get_language_settings():
    """获取语言设置"""
    settings = {
        'language': 'zh-CN',
        'test_language': 'japanese',
        'voice_type': 'standard'
    }
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, value FROM system_settings WHERE category = "language"')
            rows = cursor.fetchall()
            for row in rows:
                key, value = row
                if key in settings:
                    settings[key] = value
    except Exception as e:
        logger.error(f"获取语言设置失败: {e}")
    return settings

# 服务器时间API
@app.route('/api/server-time')
def get_server_time():
    """获取服务器时间"""
    from datetime import datetime
    now = datetime.now()
    
    # 格式化时间
    time_str = now.strftime('%H:%M:%S')
    date_str = now.strftime('%Y年%m月%d日')
    
    # 星期几
    weekday_map = {
        0: '星期一',
        1: '星期二',
        2: '星期三',
        3: '星期四',
        4: '星期五',
        5: '星期六',
        6: '星期日'
    }
    weekday_str = weekday_map.get(now.weekday(), '')
    
    return jsonify({
        'success': True,
        'timestamp': int(now.timestamp() * 1000),
        'time': time_str,
        'date': date_str,
        'weekday': weekday_str
    })

# ============================================================
# HTTPS强制重定向中间件 - 安全配置（仅SSL模式启用）
# ============================================================

@app.before_request
def force_https_redirect():
    """强制HTTPS重定向 - 仅在SSL模式下启用"""
    # 仅在SSL模式下强制HTTPS重定向
    # HTTP模式下跳过此检查
    pass
    
    # 添加安全响应头
    # HSTS - 强制浏览器使用HTTPS
    # CSP - 内容安全策略
    # X-Frame-Options - 防止iframe嵌入
    # X-Content-Type-Options - 防止MIME类型嗅探
    # X-XSS-Protection - XSS过滤器

# 添加安全响应头到所有响应
@app.after_request
def add_security_headers(response):
    """添加安全响应头"""
    # HSTS - 强制HTTPS（仅在SSL模式下）
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # 防止iframe嵌入（点击劫持防护）
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # 防止MIME类型嗅探
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # XSS防护
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # 内容安全策略
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'self';"
    
    # Referrer策略
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # 权限策略
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()'
    
    return response

# Vite客户端请求处理(开发环境)
@app.route('/@vite/client')
def vite_client():
    return '', 204

def is_mobile_device():
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'ipod', 'tablet', 'touch', 'opera mini', 'windows phone']
    desktop_keywords = ['windows nt', 'macintosh', 'linux x86_64']
    
    has_mobile = any(keyword in user_agent for keyword in mobile_keywords)
    has_desktop = any(keyword in user_agent for keyword in desktop_keywords)
    
    if has_desktop and not has_mobile:
        return False
    return has_mobile

@app.route('/mobile')
def mobile_index():
    if 'user_id' not in session:
        return render_template('mobile/login.html')
    return render_template('mobile/home.html')

@app.route('/mobile/login', methods=['GET', 'POST'])
def mobile_login():
    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"success": False, "error": "请输入用户名和密码"}), 400
        
        user = get_user_by_username(username)
        
        if not user:
            return jsonify({"success": False, "error": "用户名或密码错误"}), 401
        
        if not verify_password(user['password'], password):
            return jsonify({"success": False, "error": "用户名或密码错误"}), 401
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute("INSERT INTO login_logs (user_id, login_time, login_ip, user_agent) VALUES (?, ?, ?, ?)",
                          (user['id'], datetime.now().isoformat(), request.remote_addr, request.headers.get('User-Agent', '')))
                conn.commit()
        except Exception:
            pass
        
        return jsonify({"success": True, "redirect": "/mobile/home"})
    
    return render_template('mobile/login.html')

@app.route('/mobile/home')
def mobile_home():
    if 'user_id' not in session:
        return redirect('/mobile/login')
    user = {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    }
    return render_template('mobile/home.html', user=user, current_page='home')

@app.route('/mobile/exam')
def mobile_exam():
    if 'user_id' not in session:
        return redirect('/mobile/login')
    user = {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    }
    return render_template('mobile/exam.html', user=user, current_page='exam')

@app.route('/mobile/training')
def mobile_training():
    if 'user_id' not in session:
        return redirect('/mobile/login')
    user = {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    }
    return render_template('mobile/training.html', user=user, current_page='training')

@app.route('/mobile/profile')
def mobile_profile():
    if 'user_id' not in session:
        return redirect('/mobile/login')
    user = {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    }
    return render_template('mobile/profile.html', user=user, current_page='profile')

@app.route('/mobile/logout')
def mobile_logout():
    session.clear()
    return redirect('/mobile/login')

# ============================================================
# 管理员App路由 - 仅限管理员和超级管理员访问
# ============================================================
def require_admin_app_access():
    """管理员App权限检查"""
    if 'user_id' not in session:
        return False, 'login'
    role = session.get('role', 'guest')
    if role not in ['admin', 'super_admin', 'hardware_admin']:
        return False, 'forbidden'
    return True, None

@app.route('/admin_app')
def admin_app_index():
    """管理员App入口"""
    has_access, redirect_to = require_admin_app_access()
    if not has_access:
        if redirect_to == 'login':
            return redirect('/admin_app/login')
        return "无权访问", 403
    return redirect('/admin_app/dashboard')

@app.route('/admin_app/login', methods=['GET', 'POST'])
def admin_app_login():
    """管理员App登录页面"""
    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"success": False, "error": "请输入用户名和密码"}), 400
        
        user = get_user_by_username(username)
        
        if not user:
            return jsonify({"success": False, "error": "用户名或密码错误"}), 401
        
        if not verify_password(user['password'], password):
            return jsonify({"success": False, "error": "用户名或密码错误"}), 401
        
        if user['role'] not in ['admin', 'super_admin', 'hardware_admin']:
            return jsonify({"success": False, "error": "您没有管理员权限"}), 403
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute("INSERT INTO login_logs (user_id, login_time, login_ip, user_agent) VALUES (?, ?, ?, ?)",
                          (user['id'], datetime.now().isoformat(), request.remote_addr, request.headers.get('User-Agent', '')))
                conn.commit()
        except Exception:
            pass
        
        return jsonify({"success": True, "redirect": "/admin_app/dashboard"})
    
    return render_template('admin_app/login.html')

@app.route('/admin_app/dashboard')
def admin_app_dashboard():
    """管理员App - 数据概览"""
    has_access, redirect_to = require_admin_app_access()
    if not has_access:
        if redirect_to == 'login':
            return redirect('/admin_app/login')
        return "无权访问", 403
    
    user_id = session.get('user_id')
    user = {
        'id': user_id,
        'username': session.get('username'),
        'role': session.get('role')
    }
    
    stats = {}
    notification_count = 0
    activities = []
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            stats['active_users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exams')
            stats['exams_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM questions')
            stats['questions_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exam_papers')
            stats['papers_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exam_results WHERE status = 'completed'")
            stats['completed_exams'] = cursor.fetchone()[0]
            
            # Today's logins (from session_manager or last_login)
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_login >= date('now')")
            stats['today_logins'] = cursor.fetchone()[0]
            
            # Today's registrations
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now')")
            stats['today_registers'] = cursor.fetchone()[0]
            
            # Get unread notifications count
            if user_id:
                cursor.execute('SELECT COUNT(*) FROM notifications WHERE (recipient_id = ? OR recipient_id IS NULL) AND status = ?', (user_id, 'unread'))
                notification_count = cursor.fetchone()[0]
            
            # Get recent activities from multiple sources
            cursor.execute('''
                SELECT 'exam_result' as type, er.user_id as user_id, er.exam_id, er.score, er.completed_at as time, u.username
                FROM exam_results er
                LEFT JOIN users u ON er.user_id = u.id
                ORDER BY er.completed_at DESC LIMIT 5
            ''')
            for row in cursor.fetchall():
                activities.append({
                    'type': 'exam_result',
                    'user': row[5] or f'用户{row[1]}',
                    'action': f'完成考试，得分 {row[3]}分',
                    'time': row[4]
                })
            
            cursor.execute('''
                SELECT 'user_register' as type, u.id, u.username, u.created_at
                FROM users u ORDER BY u.created_at DESC LIMIT 3
            ''')
            for row in cursor.fetchall():
                activities.append({
                    'type': 'user_register',
                    'user': row[2],
                    'action': '新用户注册',
                    'time': row[3]
                })
            
            cursor.execute('''
                SELECT 'exam_paper' as type, ep.user_id, ep.exam_id, ep.status, ep.started_at, u.username
                FROM exam_papers ep
                LEFT JOIN users u ON ep.user_id = u.id
                ORDER BY ep.started_at DESC LIMIT 3
            ''')
            for row in cursor.fetchall():
                if row[3] == 'in_progress':
                    activities.append({
                        'type': 'exam_paper',
                        'user': row[5] or f'用户{row[1]}',
                        'action': '开始考试',
                        'time': row[4]
                    })
            
            # Sort activities by time
            activities.sort(key=lambda x: x['time'] if x['time'] else '', reverse=True)
            activities = activities[:8]
            
            # Get system alerts from error_logs
            alerts = []
            cursor.execute('''
                SELECT id, error_type, error_message, created_at, status
                FROM error_logs
                WHERE status = 'pending'
                ORDER BY created_at DESC LIMIT 5
            ''')
            for row in cursor.fetchall():
                alerts.append({
                    'type': row[1] or 'error',
                    'message': row[2],
                    'time': row[3],
                    'level': '紧急' if 'critical' in str(row[1]).lower() else '警告'
                })
            
            # If no pending errors, show resolved count
            cursor.execute('SELECT COUNT(*) FROM error_logs WHERE status = \'resolved\'')
            resolved_count = cursor.fetchone()[0]
    except Exception as e:
        import logging
        logging.error(f"Dashboard stats error: {e}")
        stats = {'total_users': 0, 'active_users': 0, 'exams_count': 0, 'questions_count': 0, 'papers_count': 0, 'completed_exams': 0, 'today_logins': 0, 'today_registers': 0}
        alerts = []
        resolved_count = 0
    
    return render_template('admin_app/dashboard.html', user=user, stats=stats, notification_count=notification_count, activities=activities, alerts=alerts, resolved_count=resolved_count, current_page='dashboard')

@app.route('/admin_app/users')
def admin_app_users():
    """管理员App - 用户管理"""
    has_access, redirect_to = require_admin_app_access()
    if not has_access:
        if redirect_to == 'login':
            return redirect('/admin_app/login')
        return "无权访问", 403
    
    user_id = session.get('user_id')
    user = {
        'id': user_id,
        'username': session.get('username'),
        'role': session.get('role')
    }
    
    users = []
    notification_count = 0
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users ORDER BY created_at DESC LIMIT 50')
            columns = ['id', 'username', 'email', 'role', 'is_active', 'created_at']
            for row in cursor.fetchall():
                users.append(dict(zip(columns, row)))
            
            if user_id:
                cursor.execute('SELECT COUNT(*) FROM notifications WHERE (recipient_id = ? OR recipient_id IS NULL) AND status = ?', (user_id, 'unread'))
                notification_count = cursor.fetchone()[0]
    except Exception as e:
        import logging
        logging.error(f"Users list error: {e}")
    
    return render_template('admin_app/users.html', user=user, users=users, notification_count=notification_count, current_page='users')

@app.route('/admin_app/exams')
def admin_app_exams():
    """管理员App - 考试管理"""
    has_access, redirect_to = require_admin_app_access()
    if not has_access:
        if redirect_to == 'login':
            return redirect('/admin_app/login')
        return "无权访问", 403
    
    user_id = session.get('user_id')
    user = {
        'id': user_id,
        'username': session.get('username'),
        'role': session.get('role')
    }
    
    exams = []
    notification_count = 0
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, language_level, duration, total_score, status, created_at FROM exams ORDER BY created_at DESC LIMIT 20')
            columns = ['id', 'exam_name', 'exam_type', 'duration', 'total_score', 'status', 'created_at']
            for row in cursor.fetchall():
                exam = dict(zip(columns, row))
                exams.append(exam)
            
            if user_id:
                cursor.execute('SELECT COUNT(*) FROM notifications WHERE (recipient_id = ? OR recipient_id IS NULL) AND status = ?', (user_id, 'unread'))
                notification_count = cursor.fetchone()[0]
    except Exception as e:
        import logging
        logging.error(f"Exams list error: {e}")
    
    return render_template('admin_app/exams.html', user=user, exams=exams, notification_count=notification_count, current_page='exams')

@app.route('/admin_app/monitor')
def admin_app_monitor():
    """管理员App - 系统监控"""
    has_access, redirect_to = require_admin_app_access()
    if not has_access:
        if redirect_to == 'login':
            return redirect('/admin_app/login')
        return "无权访问", 403
    
    user_id = session.get('user_id')
    user = {
        'id': user_id,
        'username': session.get('username'),
        'role': session.get('role')
    }
    
    logs = []
    notification_count = 0
    # System stats
    uptime = '99.9'
    cpu_usage = 0
    memory_usage = 0
    db_size = '170'
    db_queries = 0
    total_users = 0
    total_exams = 0
    total_papers = 0
    total_questions = 0
    completed_exams = 0
    active_users = 0
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            active_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exams')
            total_exams = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM questions')
            total_questions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exam_papers')
            total_papers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exam_results WHERE status = 'completed'")
            completed_exams = cursor.fetchone()[0]
            
            # Try access_logs first, fallback to system_logs
            try:
                cursor.execute('SELECT id, path, username, ip_address, access_time, method FROM access_logs ORDER BY id DESC LIMIT 20')
                columns = ['id', 'path', 'username', 'ip_address', 'access_time', 'method']
            except:
                cursor.execute('SELECT id, action as path, user_id as username, ip_address, created_at as access_time, \'GET\' as method FROM system_operation_logs ORDER BY id DESC LIMIT 20')
                columns = ['id', 'path', 'username', 'ip_address', 'access_time', 'method']
            
            for row in cursor.fetchall():
                log = dict(zip(columns, row))
                logs.append(log)
            
            if user_id:
                cursor.execute('SELECT COUNT(*) FROM notifications WHERE (recipient_id = ? OR recipient_id IS NULL) AND status = ?', (user_id, 'unread'))
                notification_count = cursor.fetchone()[0]
    except Exception as e:
        import logging
        logging.error(f"Monitor logs error: {e}")
    
    return render_template('admin_app/monitor.html', user=user, logs=logs, notification_count=notification_count, 
                          uptime=uptime, cpu_usage=cpu_usage, memory_usage=memory_usage,
                          db_size=db_size, db_queries=db_queries, total_users=total_users,
                          total_exams=total_exams, total_papers=total_papers, 
                          total_questions=total_questions, completed_exams=completed_exams,
                          active_users=active_users, current_page='monitor')

@app.route('/admin_app/settings')
def admin_app_settings():
    """管理员App - 系统设置"""
    has_access, redirect_to = require_admin_app_access()
    if not has_access:
        if redirect_to == 'login':
            return redirect('/admin_app/login')
        return "无权访问", 403
    
    user_id = session.get('user_id')
    user = {
        'id': user_id,
        'username': session.get('username'),
        'role': session.get('role')
    }
    
    notification_count = 0
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('SELECT COUNT(*) FROM notifications WHERE (recipient_id = ? OR recipient_id IS NULL) AND status = ?', (user_id, 'unread'))
                notification_count = cursor.fetchone()[0]
    except Exception as e:
        import logging
        logging.error(f"Settings error: {e}")
    
    return render_template('admin_app/settings.html', user=user, notification_count=notification_count, current_page='settings')

@app.route('/admin_app/logout')
def admin_app_logout():
    """管理员App登出"""
    session.clear()
    return redirect('/admin_app/login')

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 增强版听力测试路由
@app.route('/listen_enhanced')
def listen_enhanced_page():
    from flask import send_file
    template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'listen_enhanced.html')
    return send_file(template_path)

@app.route('/listen_test.html')
def listen_test_page():
    from flask import send_file
    template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'listen_test.html')
    return send_file(template_path)

@app.route('/audio/<path:filename>')
def audio_files(filename):
    from flask import send_from_directory
    audio_dir = os.path.join(os.path.dirname(__file__), 'app', 'static', 'audio')
    response = send_from_directory(audio_dir, filename, mimetype='audio/mpeg')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def detect_direct_access() -> dict:
    """检测用户是否绕过首页直接访问登录页面"""
    result = {
        'is_direct_access': False,
        'risk_level': 'low',
        'message': '',
        'action': 'allow'
    }
    
    # 获取请求来源
    referer = request.headers.get('Referer', '')
    host = request.host
    
    # 检查是否有来源引用
    if not referer:
        result['is_direct_access'] = True
        result['risk_level'] = 'medium'
        result['message'] = '直接访问检测:未检测到来源页面引用'
        logger.warning(f"[安全检测] 直接访问登录页面 - IP: {request.remote_addr}, User-Agent: {request.user_agent.string}")
    else:
        # 检查来源是否为本站
        if host not in referer:
            result['is_direct_access'] = True
            result['risk_level'] = 'high'
            result['message'] = f'直接访问检测:来源非本站 ({referer})'
            logger.warning(f"[安全检测] 外部来源访问登录页面 - IP: {request.remote_addr}, Referer: {referer}, User-Agent: {request.user_agent.string}")
    
    # 检查是否为爬虫或异常请求
    user_agent = request.user_agent.string.lower()
    suspicious_agents = ['curl', 'wget', 'python-requests', 'bot', 'spider', 'scrapy']
    for agent in suspicious_agents:
        if agent in user_agent:
            result['risk_level'] = 'high'
            result['message'] = f'可疑用户代理检测: {user_agent}'
            logger.warning(f"[安全检测] 可疑用户代理访问登录页面 - IP: {request.remote_addr}, User-Agent: {user_agent}")
            break
    
    # 检查请求频率(简单实现)
    request_count = session.get('login_attempts', 0)
    if request_count > 5:
        result['risk_level'] = 'high'
        result['message'] = '登录请求频率过高'
        result['action'] = 'block'
        logger.warning(f"[安全检测] 登录请求频率过高 - IP: {request.remote_addr}, 次数: {request_count}")
    
    session['login_attempts'] = request_count + 1
    
    return result


def handle_login_exception(e: Exception, username: str = None) -> tuple:
    """处理登录异常"""
    error_code = 'UNKNOWN_ERROR'
    error_message = '登录过程中发生未知错误'
    
    if isinstance(e, ValueError):
        error_code = 'VALIDATION_ERROR'
        error_message = str(e)
    elif isinstance(e, ConnectionError):
        error_code = 'CONNECTION_ERROR'
        error_message = '数据库连接失败,请稍后重试'
    elif isinstance(e, Exception):
        error_code = 'INTERNAL_ERROR'
        error_message = '系统内部错误,请联系管理员'
    
    logger.error(f"[登录异常] 代码: {error_code}, 用户: {username}, 错误: {str(e)}")
    
    # 记录错误日志到数据库
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_logs (level, module, message, ip_address)
                VALUES (?, ?, ?, ?)
            ''', ('ERROR', 'login', f"登录异常 - {error_code}: {error_message}", request.remote_addr))
            conn.commit()
    except Exception:
        pass
    
    return jsonify({
        'success': False,
        'error': error_code,
        'message': error_message
    }), 500


def get_redirect_url_by_role(role: str) -> str:
    """根据用户角色返回登录后重定向的URL"""
    role_redirect_map = {
        # 学生角色 - 直接进入考试系统
        'student': '/exam_system',
        'student_vip': '/exam_system',
        
        # 教师角色 - 进入教师管理中心
        'teacher': '/teacher',
        'teacher_admin': '/teacher',
        
        # 管理员角色 - 进入管理中心
        'admin': '/settings',
        'system_admin': '/settings',
        
        # 超级管理员角色 - 进入超级管理面板
        'super_admin': '/super_admin_dashboard',
        
        # 硬件管理员角色
        'hardware_admin': '/hardware/dashboard',
        
        # 考试专家角色 - 进入考试系统
        'exam_expert': '/exam_system',
        
        # 设计师角色 - 进入Arduino设计页面
        'designer': '/arduino',
        
        # 默认角色 - 进入考试系统(普通用户默认进入考试系统)
        'user': '/exam_system',
        'guest': '/',
    }
    
    # 如果角色不在映射中,返回考试系统作为默认
    return role_redirect_map.get(role, '/exam_system')


# 登录路由 - 后台API接口,不直接显示给用户
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            # 安全检测:直接访问检测
            access_detection = detect_direct_access()
            if access_detection['action'] == 'block':
                return jsonify({
                    'success': False,
                    'error': 'ACCESS_BLOCKED',
                    'message': '访问被拒绝:请求频率过高,请稍后重试'
                }), 403
            
            # 尝试从多种来源获取数据
            data = {}
            
            # 1. 尝试JSON格式
            try:
                json_data = request.get_json(force=False, silent=True)
                if json_data:
                    data.update(json_data)
            except Exception as e:
                logger.warning(f"解析JSON失败: {e}")
            
            # 2. 尝试表单格式
            if not data:
                form_data = request.form.to_dict()
                if form_data:
                    data.update(form_data)
            
            # 3. 尝试查询参数
            if not data:
                args_data = request.args.to_dict()
                if args_data:
                    data.update(args_data)
            
            # 4. 尝试原始数据(安全风险,已移除eval)
            if not data and request.data:
                try:
                    import json
                    data = json.loads(request.data.decode('utf-8'))
                except Exception:
                    pass
            
            logger.info(f"登录请求数据: {data}")
            
            if not data:
                return jsonify({'success': False, 'message': '参数错误: 未接收到有效数据'}), 400
            
            if 'username' not in data:
                return jsonify({'success': False, 'message': '参数错误: 缺少用户名'}), 400
            
            if 'password' not in data:
                return jsonify({'success': False, 'message': '参数错误: 缺少密码'}), 400
            
            username = data.get('username')
            password = data.get('password')
            
            # 用户名格式验证
            if not username or len(username.strip()) < 3:
                return jsonify({'success': False, 'message': '用户名格式错误'}), 400
            
            # 密码长度验证
            if not password or len(password) < 6:
                return jsonify({'success': False, 'message': '密码长度不足'}), 400
            
            # 从数据库查询用户
            user = get_user_by_username(username)
            
            if not user:
                logger.warning(f"[登录失败] 用户不存在 - IP: {request.remote_addr}, 用户名: {username}")
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            
            # 验证密码
            if not verify_password(user['password'], password):
                logger.warning(f"[登录失败] 密码错误 - IP: {request.remote_addr}, 用户名: {username}")
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            
            # 检查用户状态
            if user.get('status') == 'locked':
                logger.warning(f"[登录失败] 用户已锁定 - IP: {request.remote_addr}, 用户名: {username}")
                return jsonify({'success': False, 'message': '账户已被锁定,请联系管理员'}), 403
            
            # 检查是否勾选"记住我"
            remember = data.get('remember', False)
            if isinstance(remember, str):
                remember = remember.lower() in ['true', '1', 'yes', 'on']
            
            # 生成会话ID
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user['id']}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
            
            # 设置session
            session['session_id'] = session_id
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['email'] = user['email']
            session['login_time'] = datetime.now().isoformat()
            session['login_ip'] = request.remote_addr
            session['remember_me'] = remember
            
            # 根据"记住我"设置会话有效期
            if remember:
                # 勾选了"记住我"：会话有效期30天
                session.permanent = True
                from datetime import timedelta
                app.permanent_session_lifetime = timedelta(days=30)
                logger.info(f"[记住我] 用户 {username} 登录，会话有效期30天")
            else:
                # 未勾选"记住我"：会话有效期30分钟
                session.permanent = True
                from datetime import timedelta
                app.permanent_session_lifetime = timedelta(minutes=30)
            
            # 重置登录尝试计数
            session['login_attempts'] = 0
            
            # 注册会话到会话管理器
            from app.utils.session_manager import get_session_manager
            sm = get_session_manager()
            sm.create_session(user['id'], username, user['role'], request.remote_addr, request.user_agent.string)
            
            # 根据用户角色确定登录后重定向页面
            redirect_url = get_redirect_url_by_role(user['role'])
            
            logger.info(f"[登录成功] 用户: {username}, 角色: {user['role']}, 重定向: {redirect_url}, IP: {request.remote_addr}, 记住我: {remember}")
            
            # 判断请求类型,决定返回方式
            accept_header = request.headers.get('Accept', '')
            if 'application/json' in accept_header or request.is_json:
                return jsonify({
                    'success': True, 
                    'message': '登录成功', 
                    'session_id': session_id,
                    'remember_me': remember,
                    'session_expires_in': 30 * 24 * 3600 if remember else 30 * 60,  # 秒
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'role': user['role'],
                        'email': user['email']
                    },
                    'redirect': redirect_url
                })
            else:
                return redirect(redirect_url)
        
        # GET请求显示登录页面
        else:
            # 检测直接访问
            access_detection = detect_direct_access()
            
            # 如果是高风险直接访问,记录但允许访问
            if access_detection['risk_level'] == 'high':
                # 可以在这里添加验证码要求或其他安全措施
                pass
            
            # 检查是否已登录
            if session.get('user_id'):
                # 已登录用户访问登录页面,重定向到dashboard
                logger.info(f"[已登录用户访问登录页] 重定向到dashboard - 用户: {session.get('username')}")
                return redirect('/dashboard')
            
            return render_template('login.html', access_warning=access_detection if access_detection['is_direct_access'] else None)
    
    except Exception as e:
        return handle_login_exception(e)

# 登出路由
@app.route('/auth/logout', methods=['GET', 'POST'])
def logout():
    from app.utils.session_manager import get_session_manager
    from app.utils.backup_manager import get_backup_manager
    
    session_id = session.get('session_id')
    user_id = session.get('user_id')
    username = session.get('username')
    role = session.get('role')
    
    logout_actions = []
    
    if session_id:
        try:
            sm = get_session_manager()
            sm.invalidate_session(session_id)
            logout_actions.append('会话已清除')
        except Exception as e:
            logger.error(f"清除会话失败: {e}")
    
    if role == 'hardware_admin':
        hardware_session = session.get('hardware_session_id')
        if hardware_session:
            try:
                from app.utils.permission_manager import get_hardware_auth_manager
                ham = get_hardware_auth_manager()
                ham.invalidate_hardware_session(hardware_session)
                logout_actions.append('硬件管理会话已清除')
            except Exception as e:
                logger.error(f"清除硬件会话失败: {e}")
    
    try:
        backup_manager = get_backup_manager()
        backup_manager.save_current_session_data()
        logout_actions.append('会话数据已备份')
    except Exception as e:
        logger.error(f"备份会话数据失败: {e}")
    
    session.clear()
    
    logger.info(f"用户 {username or '未知用户'} 已退出登录")
    
    return render_template('logout.html', username=username)


# 注册路由 - 后台API接口
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 尝试从多种来源获取数据
        data = {}
        
        try:
            json_data = request.get_json(force=False, silent=True)
            if json_data:
                data.update(json_data)
        except Exception:
            pass
        
        if not data:
            data.update(request.form.to_dict())
        
        if data and 'username' in data and 'password' in data:
            # 创建用户
            import hashlib
            import base64
            hashed_password = base64.b64encode(hashlib.sha256(data['password'].encode()).digest()).decode()
            
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn_cursor = conn.cursor()
                    cursor = conn.cursor()
                    cursor.execute(
                    'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                    (data['username'], f"{data['username']}@example.com", hashed_password, 'user')
                    )
                    conn.commit()
                return jsonify({'success': True, 'message': '注册成功'})
            except Exception as e:
                logger.error(f"注册失败: {e}")
                return jsonify({'success': False, 'message': '注册失败'}), 500
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    # GET请求重定向到主页,注册页面由前端处理
    return redirect('/')

# 导入权限装饰器
from app.middlewares.access_control import require_login, require_admin, require_super_admin, require_role


@app.route('/dashboard')
@require_login
def dashboard():
    """仪表板 - 重定向到设置页面（仪表盘已整合到设置页面中）"""
    return redirect('/settings')


# 超级管理员控制台 - 最高权限管理员专用
@app.route('/super_admin_dashboard')
@require_super_admin
def super_admin_dashboard():
    role = session.get('role', 'guest')
    username = session.get('username', '')
    
    # 获取权限等级
    from app.config.unified_rules import get_role_level
    user_level = get_role_level(role)
    
    return render_template('super_admin_dashboard.html', 
                           user={'username': username, 'role': role},
                           user_level=user_level)

# 管理员控制台 - admin角色专用（只读权限）
@app.route('/admin_dashboard')
@require_login
def admin_dashboard():
    role = session.get('role', 'guest')
    if role != 'admin':
        return redirect('/dashboard')
    return render_template('admin_dashboard.html')

# 硬件管理员仪表盘 - 重定向到超级管理员控制台
@app.route('/hardware/dashboard')
@require_login
def hardware_dashboard():
    role = session.get('role', 'guest')
    # 硬件管理员角色跳转到超级管理员控制台
    if role in ['hardware_admin', 'hardware_vikey_admin', 'super_admin', 'system_admin']:
        return redirect('/super_admin_dashboard')
    return redirect('/dashboard')

# 管理员中心 - 需要登录权限(根据角色显示不同内容)
@app.route('/admin_center')
@require_login
def admin_center():
    from app.utils.permission_manager import get_permission_manager
    from app.containers.user_container import UserContainer
    
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    
    user_container = UserContainer()
    
    access_error = None
    has_access = False
    
    if not user_id:
        access_error = {
            'code': 'Unauthorized',
            'icon': '🔐',
            'title': '未登录',
            'message': '请先登录系统'
        }
        return render_template('admin_center.html', 
                           user=None, 
                           has_access=False,
                           access_error=access_error,
                           users=[],
                           total_users=0,
                           system_settings={},
                           security_settings={},
                           language_settings={})
    
    if role == 'guest':
        access_error = {
            'code': 'GuestAccessDenied',
            'icon': '🚫',
            'title': '访客权限',
            'message': '访客用户无法访问管理中心,请登录管理员账户'
        }
        return render_template('admin_center.html', 
                           user=None, 
                           has_access=False,
                           access_error=access_error,
                           users=[],
                           total_users=0,
                           system_settings={},
                           security_settings={},
                           language_settings={})
    
    pm = get_permission_manager()
    has_access = pm.has_permission(user_id, 'view_profile')
    
    if not has_access:
        access_error = {
            'code': 'PermissionDenied',
            'icon': '🛡️',
            'title': '权限不足',
            'message': '您的账户权限不足以访问此页面.请联系管理员升级权限.'
        }
        return render_template('admin_center.html', 
                           user=None, 
                           has_access=False,
                           access_error=access_error,
                           users=[],
                           total_users=0,
                           system_settings={},
                           security_settings={},
                           language_settings={})
    
    user_info = user_container.get_user(username)
    if not user_info:
        access_error = {
            'code': 'InvalidUser',
            'icon': '⚠️',
            'title': '用户信息无效',
            'message': '无法获取用户信息,请重新登录'
        }
        return render_template('admin_center.html', 
                           user=None, 
                           has_access=False,
                           access_error=access_error,
                           users=[],
                           total_users=0,
                           system_settings={},
                           security_settings={},
                           language_settings={})
    
    users = []
    total_users = 0
    role_display_map = {
        'guest': '访客',
        'student': '学生',
        'designer': '设计师',
        'user': '普通用户',
        'admin': '管理员',
        'super_admin': '超级管理员',
        'hardware_admin': '硬件管理员',
        'hardware_vikey_admin': '硬件管理员'
    }
    
    if role in ['admin', 'super_admin', 'hardware_admin']:
        try:
            import sqlite3
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users')
            user_records = cursor.fetchall()
            conn.close()
            
            total_users = len(user_records)
            users = [{
                'id': ur[0],
                'username': ur[1],
                'email': ur[2],
                'role': ur[3],
                'role_display': role_display_map.get(ur[3], ur[3]),
                'is_active': ur[4],
                'created_at': ur[5]
            } for ur in user_records]
        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            total_users = user_container.stats.get('total_users', 0)
    
    system_settings = get_system_settings()
    security_settings = get_security_settings()
    language_settings = get_language_settings()
    
    user_data = {
        'username': username,
        'role': role,
        'role_display': role_display_map.get(role, role),
        'is_authenticated': True,
        'user_id': user_id
    }
    
    return render_template('admin_center.html', 
                           user=user_data, 
                           has_access=True,
                           access_error=None,
                           users=users,
                           total_users=total_users,
                           system_settings=system_settings,
                           security_settings=security_settings,
                           language_settings=language_settings)

# 智能仪表板(教师) - 需要登录
@app.route('/smart_dashboard')
@require_login
def smart_dashboard():
    return render_template('smart_dashboard.html')

# 健康检查
@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# 用户IP获取API（公开访问）
@app.route('/api/user/ip', methods=['GET'])
def get_user_ip_public():
    """获取用户IP地址"""
    try:
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            ip = request.headers.get('X-Real-IP').strip()
        else:
            ip = request.remote_addr or '127.0.0.1'
        
        if ip in ['127.0.0.1', '::1', 'localhost', '::ffff:127.0.0.1', None, '']:
            ip = '127.0.0.1 (本地开发)'
        
        return jsonify({'success': True, 'ip': ip, 'message': 'IP地址获取成功'})
    except Exception as e:
        logger.error(f"获取IP失败: {e}")
        return jsonify({'success': True, 'ip': '127.0.0.1 (默认)', 'message': '获取失败，使用默认值'})

# 仪表盘统计数据API（公开访问）
@app.route('/api/admin/dashboard_stats', methods=['GET'])
def get_dashboard_stats_public():
    """获取仪表盘统计数据"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        route_count = len([r for r in app.url_map.iter_rules()])
        
        try:
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM access_logs WHERE DATE(access_time) = DATE("now")')
            active_users = cursor.fetchone()[0]
        except:
            active_users = 0
        
        exams_count = 0
        questions_count = 0
        completed_exams = 0
        try:
            cursor.execute('SELECT COUNT(*) FROM exams')
            exams_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM questions')
            questions_count = cursor.fetchone()[0]
            try:
                cursor.execute('SELECT COUNT(*) FROM exam_results WHERE completed = 1')
                completed_exams = cursor.fetchone()[0]
            except:
                completed_exams = 0
        except:
            pass
        
        learning_records = 0
        wrong_questions = 0
        try:
            cursor.execute('SELECT COUNT(*) FROM learning_records')
            learning_records = cursor.fetchone()[0]
        except:
            pass
        try:
            cursor.execute('SELECT COUNT(*) FROM wrong_questions')
            wrong_questions = cursor.fetchone()[0]
        except:
            pass
        
        backup_count = 0
        try:
            cursor.execute('SELECT COUNT(*) FROM backups')
            backup_count = cursor.fetchone()[0]
        except:
            pass
        
        notification_count = 0
        try:
            cursor.execute('SELECT COUNT(*) FROM notifications')
            notification_count = cursor.fetchone()[0]
        except:
            pass
        
        today_logins = 0
        today_registers = 0
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_login) = DATE('now')")
            today_logins = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')")
            today_registers = cursor.fetchone()[0]
        except:
            pass
        
        recent_users = []
        try:
            cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC LIMIT 5')
            for row in cursor.fetchall():
                recent_users.append({
                    'id': row[0],
                    'username': row[1],
                    'role': row[2],
                    'created_at': row[3]
                })
        except:
            pass
        
        recent_logs = []
        try:
            cursor.execute('SELECT id, user_id, username, action, ip_address, created_at FROM system_logs ORDER BY created_at DESC LIMIT 10')
            for row in cursor.fetchall():
                recent_logs.append({
                    'id': row[0],
                    'user_id': row[1],
                    'username': row[2],
                    'action': row[3],
                    'ip_address': row[4],
                    'created_at': row[5]
                })
        except:
            try:
                cursor.execute('SELECT id, user_id, path, ip_address, access_time FROM access_logs ORDER BY access_time DESC LIMIT 10')
                for row in cursor.fetchall():
                    recent_logs.append({
                        'id': row[0],
                        'user_id': row[1],
                        'username': '用户' + str(row[1]),
                        'action': row[2],
                        'ip_address': row[3],
                        'created_at': row[4]
                    })
            except:
                pass
        
        conn.close()
        
        import psutil
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
        except:
            cpu_percent = 0
            memory_percent = 0
            disk_percent = 0
        
        return jsonify({
            'success': True,
            'data': {
                'user_count': user_count,
                'route_count': route_count,
                'system_status': '正常运行',
                'active_users': active_users,
                'exams_count': exams_count,
                'questions_count': questions_count,
                'completed_exams': completed_exams,
                'learning_records': learning_records,
                'wrong_questions': wrong_questions,
                'backup_count': backup_count,
                'notification_count': notification_count,
                'today_logins': today_logins,
                'today_registers': today_registers,
                'recent_users': recent_users,
                'recent_logs': recent_logs,
                'system_resources': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent
                },
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': {'user_count': 0, 'route_count': 0, 'system_status': '获取失败', 'active_users': 0}})

# 系统状态
@app.route('/api/system/status')
def system_status():
    return jsonify({'status': 'running', 'version': "3.1.0", 'timestamp': datetime.now().isoformat()})

# 用户信息API - 改用/api/users/info避免路由冲突
@app.route('/api/users/info/<username>')
def get_user_info_api(username):
    user = get_user_by_username(username)
    if user:
        # 不返回密码
        user.pop('password', None)
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'message': '用户不存在'}), 404

# 调试路由
@app.route('/debug/routes')
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'rule': str(rule),
            'endpoint': rule.endpoint,
            'methods': list(rule.methods)
        })
    return jsonify(routes)

# 在线考试页面路由
@app.route('/exam')
def exam_page():
    role = session.get('role', 'guest')
    if role not in ['student', 'teacher', 'researcher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
        return redirect('/')
    response = make_response(render_template('exam_page.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/exam/start/<exam_id>')
def exam_start_page(exam_id):
    """开始考试页面"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/auth/login')
    
    role = session.get('role')
    if role not in ['student', 'teacher', 'researcher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
        return redirect('/')
    
    # 获取考试信息
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
            exam = cursor.fetchone()
            
            if not exam:
                return "考试不存在", 404
            
            exam_dict = dict(exam)
    except Exception as e:
        logger.error(f"获取考试信息失败: {e}")
        return "考试加载失败", 500
    
    response = make_response(render_template('exam_page.html', exam_id=exam_id))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

def get_user_education_type(user_id: int) -> str:
    """获取用户教育类型：九年义务教育、成人教育、或通用"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT grade, education_level, student_type FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                grade, education_level, student_type = row
                
                # 优先使用 education_level 判断
                if education_level:
                    if '义务' in education_level or '初中' in education_level or '高中' in education_level:
                        return 'nine_year'
                    elif '成人' in education_level or '继续教育' in education_level:
                        return 'adult'
                
                # 使用 grade 判断
                if grade:
                    if grade.startswith('小学') or grade.startswith('初中') or grade.startswith('高中'):
                        return 'nine_year'
                    elif grade.startswith('成人'):
                        return 'adult'
                    elif '雅思' in grade or '托福' in grade:
                        return 'adult'
                
                # 使用 student_type 判断
                if student_type:
                    if '义务' in student_type:
                        return 'nine_year'
                    elif '成人' in student_type:
                        return 'adult'
    except Exception as e:
        logger.error(f"获取用户教育类型失败: {e}")
    
    return 'general'

# 考试系统路由 - 学生仪表盘
@app.route('/exam_system')
def exam_system():
    ALLOWED_EXAM_ROLES = ['student']
    
    user_id = session.get('user_id')
    
    # 未登录用户，显示美化的登录提示页面
    if not user_id:
        return render_template('login_required.html', request_path='/exam_system'), 401
    
    # 检查角色权限
    role = session.get('role')
    if role not in ALLOWED_EXAM_ROLES:
        return render_template('403.html', current_role=role, required_role='student', request_path='/exam_system'), 403
    
    # 获取用户信息
    user_info = get_user_info(user_id)
    if not user_info:
        return render_template('login_required.html', request_path='/exam_system'), 401
    
    # 获取教育类型
    education_type = get_user_education_type(user_id)
    education_type_label = {
        'nine_year': '九年制义务教育',
        'adult': '成人教育',
        'general': '通用学习'
    }.get(education_type, '通用学习')
    
    # 获取用户统计数据
    stats = get_user_stats(user_id)
    
    # 获取即将开始的考试（最近的3个）
    upcoming_exams = get_upcoming_exams(education_type, limit=3)
    
    # 获取错题（最近的5个）
    wrong_questions = get_user_wrong_questions(user_id, limit=5)
    
    # 获取推荐考试
    recommended_exams = get_recommended_exams(education_type, limit=6)
    
    return render_template('student_dashboard.html',
                         user=user_info,
                         education_type=education_type,
                         education_type_label=education_type_label,
                         stats=stats,
                         upcoming_exams=upcoming_exams,
                         wrong_questions=wrong_questions,
                         recommended_exams=recommended_exams)


def get_user_info(user_id):
    """获取用户详细信息"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
    return {
        'id': user_id,
        'username': '用户',
        'grade': '',
        'student_type': '学生',
        'education_level': ''
    }


def get_user_stats(user_id):
    """获取用户学习统计数据"""
    stats = {
        'total_exams': 0,
        'average_score': 0,
        'wrong_questions': 0,
        'points': 0,
        'streak_days': 1,
        'daily_chances': 3,
        'overall_progress': 35,
        'weekly_progress': 60
    }
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 已完成考试数
            cursor.execute('SELECT COUNT(*) FROM exam_sessions WHERE user_id = ? AND status = "completed"', (user_id,))
            stats['total_exams'] = cursor.fetchone()[0] or 0
            
            # 平均正确率
            cursor.execute('SELECT AVG(score) FROM exam_sessions WHERE user_id = ? AND status = "completed"', (user_id,))
            avg = cursor.fetchone()[0]
            stats['average_score'] = int(avg) if avg else 0
            
            # 错题数
            try:
                cursor.execute('SELECT COUNT(*) FROM wrong_questions WHERE user_id = ?', (user_id,))
                stats['wrong_questions'] = cursor.fetchone()[0] or 0
            except Exception:
                pass
            
            # 学习积分
            try:
                cursor.execute('SELECT points FROM user_points WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                stats['points'] = result[0] if result else 100
            except Exception:
                stats['points'] = 100
                
    except Exception as e:
        logger.error(f"获取用户统计数据失败: {e}")
    
    return stats


def get_upcoming_exams(education_type='general', limit=3):
    """获取即将开始的考试"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM exams WHERE status = "active"'
            params = []
            
            if education_type == 'nine_year':
                query += ' AND (title LIKE ? OR description LIKE ? OR level LIKE ?)'
                params.extend(['%小学%', '%初中%', '%初级'])
            elif education_type == 'adult':
                query += ' AND (language = ? OR title LIKE ? OR level LIKE ?)'
                params.extend(['japanese', '%成人%', '%中级'])
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"获取即将开始的考试失败: {e}")
    
    # 返回默认测试数据
    return [
        {
            'id': 'default_1',
            'title': '综合能力测试',
            'description': '测试您的综合学习能力',
            'duration': 60,
            'question_count': 20,
            'total_points': 100,
            'language': '综合',
            'level': '初级'
        }
    ]


def get_user_wrong_questions(user_id, limit=5):
    """获取用户错题列表"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT wq.*, q.subject, q.type, q.question_text 
                FROM wrong_questions wq 
                LEFT JOIN questions q ON wq.question_id = q.id
                WHERE wq.user_id = ? 
                ORDER BY wq.wrong_count DESC 
                LIMIT ?
            ''', (user_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"获取用户错题失败: {e}")
    
    return []


def get_recommended_exams(education_type='general', limit=6):
    """获取推荐考试"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exams WHERE status = "active" ORDER BY question_count LIMIT ?', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"获取推荐考试失败: {e}")
    
    return []


# 随机有奖测试页面
@app.route('/exam/random_challenge')
def random_challenge():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/auth/login')
    
    # 生成随机题目
    question = generate_random_question()
    
    return render_template('random_challenge.html', 
                         question=question,
                         user=get_user_info(user_id))


def generate_random_question():
    """生成随机测试题"""
    import random
    
    questions = [
        {
            'type': 'single',
            'subject': '综合知识',
            'question': '以下哪个是Python的关键字？',
            'options': ['function', 'def', 'func', 'define'],
            'answer': 1,
            'points': 10
        },
        {
            'type': 'single',
            'subject': '逻辑推理',
            'question': '1, 4, 9, 16, 25, ? 下一个数字是？',
            'options': ['30', '36', '49', '64'],
            'answer': 1,
            'points': 15
        },
        {
            'type': 'single',
            'subject': '常识',
            'question': '一年有多少个月？',
            'options': ['10', '11', '12', '13'],
            'answer': 2,
            'points': 5
        },
        {
            'type': 'single',
            'subject': '数学',
            'question': '2的8次方等于多少？',
            'options': ['64', '128', '256', '512'],
            'answer': 2,
            'points': 10
        },
        {
            'type': 'single',
            'subject': '语言',
            'question': '"Hello" 的中文意思是？',
            'options': ['再见', '你好', '谢谢', '对不起'],
            'answer': 1,
            'points': 5
        }
    ]
    
    return random.choice(questions)


# 提交随机测试答案
@app.route('/api/exam/random_challenge/submit', methods=['POST'])
def submit_random_challenge():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        data = request.get_json()
        user_answer = data.get('answer')
        correct_answer = data.get('correct_answer')
        points = data.get('points', 10)
        
        is_correct = user_answer == correct_answer
        
        if is_correct:
            # 答对了，奖励积分
            earned_points = points
            result = {
                'success': True,
                'correct': True,
                'points': earned_points,
                'message': f'恭喜！答对了，获得 {earned_points} 积分！'
            }
        else:
            result = {
                'success': True,
                'correct': False,
                'points': 0,
                'message': '很遗憾，答错了，继续加油！'
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"提交随机测试失败: {e}")
        return jsonify({'success': False, 'message': '服务器错误'}), 500


# 错题本页面
@app.route('/exam/wrong_book')
def wrong_book():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/auth/login')
    
    wrong_questions = get_user_wrong_questions(user_id, limit=20)
    
    return render_template('wrong_book.html',
                         user=get_user_info(user_id),
                         wrong_questions=wrong_questions)


# 错题练习页面
@app.route('/exam/wrong_book/practice')
def wrong_book_practice():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/auth/login')
    
    return redirect('/exam/wrong_book')


# Arduino设计页面路由
@app.route('/arduino')
def arduino_page():
    role = session.get('role', 'guest')
    if role != 'designer':
        from app.utils.role_router import get_role_router
        return redirect(get_role_router().get_redirect_path(role))
    return app.send_static_file('html/arduino.html')

# 教师管理后台路由
@app.route('/teacher')
def teacher_page():
    role = session.get('role', 'guest')
    if role != 'teacher':
        from app.utils.role_router import get_role_router
        return redirect(get_role_router().get_redirect_path(role))
    return app.send_static_file('html/teacher.html')

# 教研员专属页面路由
@app.route('/researcher')
def researcher_page():
    role = session.get('role', 'guest')
    if role != 'researcher':
        from app.utils.role_router import get_role_router
        return redirect(get_role_router().get_redirect_path(role))
    return app.send_static_file('html/researcher.html')

# Dashboard重定向到角色页面
@app.route('/dashboard')
def dashboard_page():
    role = session.get('role', 'guest')
    from app.utils.role_router import get_role_router
    router = get_role_router()
    return redirect(router.get_redirect_path(role))

def check_exam_permission():
    """检查考试系统访问权限"""
    ALLOWED_EXAM_ROLES = ['student']
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    role = session.get('role')
    if role not in ALLOWED_EXAM_ROLES:
        return jsonify({'success': False, 'error': '没有权限访问考试系统'}), 403
    return None

# 获取考试列表API
@app.route('/api/exams', methods=['GET'])
def get_exams():
    result = check_exam_permission()
    if result:
        return result
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM exams WHERE status = "active" ORDER BY title')
        exams = cursor.fetchall()
        
        exam_list = []
        for exam in exams:
            exam_type = exam.get('exam_type', 'simulation')
            exam_list.append({
                'id': exam['id'],
                'name': exam['title'],
                'description': exam['description'],
                'duration': exam['duration'],
                'total_questions': exam['question_count'],
                'passing_score': exam['passing_score'],
                'language': exam['language'],
                'difficulty_level': exam['level'],
                'exam_type': exam_type,
                'exam_type_label': '历年真题' if exam_type == 'real' else '拟真试题',
                'audio_type': None
            })
    
    return jsonify({'success': True, 'data': exam_list})

# 删除考试API
@app.route('/api/exams/<exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
        exam = cursor.fetchone()
        
        if not exam:
            return jsonify({'success': False, 'message': '考试不存在'}), 404
        
        try:
            cursor.execute('DELETE FROM exams WHERE id = ?', (exam_id,))
            cursor.execute('DELETE FROM ai_generated_questions WHERE exam_id = ?', (exam_id,))
            cursor.execute('DELETE FROM exam_sessions WHERE exam_id = ?', (exam_id,))
            
            conn.commit()
            return jsonify({'success': True, 'message': '考试删除成功'})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

def generate_test_questions(language, difficulty, count):
    """生成测试题目"""
    questions = []
    
    base_questions = {
        'japanese': {
            'beginner': [
                {'content': '「りんご」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '梨'}, {'key': 'B', 'text': '苹果'}, {'key': 'C', 'text': '香蕉'}, {'key': 'D', 'text': '葡萄'}]},
                {'content': '「ありがとう」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '对不起'}, {'key': 'B', 'text': '谢谢'}, {'key': 'C', 'text': '你好'}, {'key': 'D', 'text': '再见'}]},
                {'content': '日本の首都はどこですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '大阪'}, {'key': 'B', 'text': '京都'}, {'key': 'C', 'text': '东京'}, {'key': 'D', 'text': '横滨'}]},
                {'content': '「水」の読み方は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'みず'}, {'key': 'B', 'text': 'すい'}, {'key': 'C', 'text': 'くみ'}, {'key': 'D', 'text': 'おと'}]},
                {'content': '「学校」の読み方は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'がっこう'}, {'key': 'B', 'text': 'えんきょう'}, {'key': 'C', 'text': 'じゅく'}, {'key': 'D', 'text': 'ほうこう'}]},
            ],
            'intermediate': [
                {'content': '「勉強」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '工作'}, {'key': 'B', 'text': '学习'}, {'key': 'C', 'text': '休息'}, {'key': 'D', 'text': '玩耍'}]},
                {'content': '「今日はとても暑いですね」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '今天很冷'}, {'key': 'B', 'text': '今天很热'}, {'key': 'C', 'text': '今天很凉快'}, {'key': 'D', 'text': '今天很舒服'}]},
                {'content': '「友達と遊びに行きます」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '和朋友一起去玩'}, {'key': 'B', 'text': '和朋友一起工作'}, {'key': 'C', 'text': '和朋友一起学习'}, {'key': 'D', 'text': '和朋友一起吃饭'}]},
                {'content': '「明日は雨が降るそうです」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '明天会晴天'}, {'key': 'B', 'text': '明天会下雨'}, {'key': 'C', 'text': '明天会下雪'}, {'key': 'D', 'text': '明天会刮风'}]},
                {'content': '「いつもありがとうございます」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '谢谢'}, {'key': 'B', 'text': '一直以来谢谢你'}, {'key': 'C', 'text': '对不起'}, {'key': 'D', 'text': '请多关照'}]},
            ],
            'advanced': [
                {'content': '「相談する」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '回答'}, {'key': 'B', 'text': '商量'}, {'key': 'C', 'text': '拒绝'}, {'key': 'D', 'text': '接受'}]},
                {'content': '「問題を解決する」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '提出问题'}, {'key': 'B', 'text': '解决问题'}, {'key': 'C', 'text': '忽略问题'}, {'key': 'D', 'text': '发现问题'}]},
                {'content': '「契約を結ぶ」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '签订合同'}, {'key': 'B', 'text': '解除合同'}, {'key': 'C', 'text': '修改合同'}, {'key': 'D', 'text': '阅读合同'}]},
                {'content': '「責任を負う」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '推卸责任'}, {'key': 'B', 'text': '承担责任'}, {'key': 'C', 'text': '放弃责任'}, {'key': 'D', 'text': '逃避责任'}]},
                {'content': '「経験を積む」の意味は何ですか？', 'type': '单选题', 'options': [{'key': 'A', 'text': '积累经验'}, {'key': 'B', 'text': '失去经验'}, {'key': 'C', 'text': '忘记经验'}, {'key': 'D', 'text': '分享经验'}]},
            ]
        },
        'english': {
            'beginner': [
                {'content': 'What is the meaning of "apple"?', 'type': '单选题', 'options': [{'key': 'A', 'text': '香蕉'}, {'key': 'B', 'text': '苹果'}, {'key': 'C', 'text': '橙子'}, {'key': 'D', 'text': '葡萄'}]},
                {'content': 'What is the capital of the United States?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'New York'}, {'key': 'B', 'text': 'Los Angeles'}, {'key': 'C', 'text': 'Washington D.C.'}, {'key': 'D', 'text': 'Chicago'}]},
                {'content': 'How do you say "thank you" in English?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Sorry'}, {'key': 'B', 'text': 'Thank you'}, {'key': 'C', 'text': 'Hello'}, {'key': 'D', 'text': 'Goodbye'}]},
                {'content': 'What is 2 + 2?', 'type': '单选题', 'options': [{'key': 'A', 'text': '3'}, {'key': 'B', 'text': '4'}, {'key': 'C', 'text': '5'}, {'key': 'D', 'text': '6'}]},
                {'content': 'What color is the sky?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Green'}, {'key': 'B', 'text': 'Blue'}, {'key': 'C', 'text': 'Red'}, {'key': 'D', 'text': 'Yellow'}]},
            ],
            'intermediate': [
                {'content': 'What does "accomplish" mean?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Start'}, {'key': 'B', 'text': 'Complete'}, {'key': 'C', 'text': 'Delay'}, {'key': 'D', 'text': 'Cancel'}]},
                {'content': 'Choose the correct sentence: "She ___ to school every day."', 'type': '单选题', 'options': [{'key': 'A', 'text': 'go'}, {'key': 'B', 'text': 'goes'}, {'key': 'C', 'text': 'going'}, {'key': 'D', 'text': 'went'}]},
                {'content': 'What does "environment" mean?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Technology'}, {'key': 'B', 'text': 'Surroundings'}, {'key': 'C', 'text': 'Economy'}, {'key': 'D', 'text': 'Politics'}]},
                {'content': 'Which word is a synonym for "happy"?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Sad'}, {'key': 'B', 'text': 'Angry'}, {'key': 'C', 'text': 'Joyful'}, {'key': 'D', 'text': 'Tired'}]},
                {'content': 'What is the past tense of "eat"?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Eated'}, {'key': 'B', 'text': 'Ate'}, {'key': 'C', 'text': 'Eaten'}, {'key': 'D', 'text': 'Eating'}]},
            ],
            'advanced': [
                {'content': 'What does "comprehensive" mean?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Limited'}, {'key': 'B', 'text': 'Thorough'}, {'key': 'C', 'text': 'Superficial'}, {'key': 'D', 'text': 'Narrow'}]},
                {'content': 'Choose the correct word: "The research findings are ___ significant."', 'type': '单选题', 'options': [{'key': 'A', 'text': 'highly'}, {'key': 'B', 'text': 'height'}, {'key': 'C', 'text': 'high'}, {'key': 'D', 'text': 'higher'}]},
                {'content': 'What does "perspective" mean?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Distance'}, {'key': 'B', 'text': 'Opinion'}, {'key': 'C', 'text': 'Speed'}, {'key': 'D', 'text': 'Weight'}]},
                {'content': 'Which sentence is grammatically correct?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'He don\'t like coffee.'}, {'key': 'B', 'text': 'He doesn\'t likes coffee.'}, {'key': 'C', 'text': 'He doesn\'t like coffee.'}, {'key': 'D', 'text': 'He not like coffee.'}]},
                {'content': 'What does "substantial" mean?', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Small'}, {'key': 'B', 'text': 'Insignificant'}, {'key': 'C', 'text': 'Considerable'}, {'key': 'D', 'text': 'Minimal'}]},
            ]
        },
        'chinese': {
            'beginner': [
                {'content': '"苹果"的英文是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Banana'}, {'key': 'B', 'text': 'Apple'}, {'key': 'C', 'text': 'Orange'}, {'key': 'D', 'text': 'Grape'}]},
                {'content': '中国的首都是哪里？', 'type': '单选题', 'options': [{'key': 'A', 'text': '上海'}, {'key': 'B', 'text': '北京'}, {'key': 'C', 'text': '广州'}, {'key': 'D', 'text': '深圳'}]},
                {'content': '"谢谢"的英文是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Sorry'}, {'key': 'B', 'text': 'Hello'}, {'key': 'C', 'text': 'Thank you'}, {'key': 'D', 'text': 'Goodbye'}]},
                {'content': '"水"的拼音是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'shui'}, {'key': 'B', 'text': 'sui'}, {'key': 'C', 'text': 'shou'}, {'key': 'D', 'text': 'sou'}]},
                {'content': '"学校"的拼音是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'xuexiao'}, {'key': 'B', 'text': 'xiaoxue'}, {'key': 'C', 'text': 'xueyao'}, {'key': 'D', 'text': 'xiaoyao'}]},
            ],
            'intermediate': [
                {'content': '"学习"的近义词是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': '玩耍'}, {'key': 'B', 'text': '工作'}, {'key': 'C', 'text': '研读'}, {'key': 'D', 'text': '休息'}]},
                {'content': '"今天天气很好"的英文翻译是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Today is bad weather.'}, {'key': 'B', 'text': 'Today is good weather.'}, {'key': 'C', 'text': 'Today is nice weather.'}, {'key': 'D', 'text': 'The weather is good today.'}]},
                {'content': '"朋友"的英文是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Enemy'}, {'key': 'B', 'text': 'Friend'}, {'key': 'C', 'text': 'Family'}, {'key': 'D', 'text': 'Stranger'}]},
                {'content': '"明天会下雨"的英文翻译是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'It will rain tomorrow.'}, {'key': 'B', 'text': 'Tomorrow rain.'}, {'key': 'C', 'text': 'Rain tomorrow.'}, {'key': 'D', 'text': 'Will rain tomorrow.'}]},
                {'content': '"谢谢"的日文是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'すみません'}, {'key': 'B', 'text': 'ありがとう'}, {'key': 'C', 'text': 'こんにちは'}, {'key': 'D', 'text': 'さようなら'}]},
            ],
            'advanced': [
                {'content': '"解决"的近义词是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': '提出'}, {'key': 'B', 'text': '解决'}, {'key': 'C', 'text': '忽略'}, {'key': 'D', 'text': '发现'}]},
                {'content': '"承担责任"的英文翻译是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Take responsibility'}, {'key': 'B', 'text': 'Avoid responsibility'}, {'key': 'C', 'text': 'Share responsibility'}, {'key': 'D', 'text': 'Ignore responsibility'}]},
                {'content': '"积累经验"的英文翻译是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Lose experience'}, {'key': 'B', 'text': 'Gain experience'}, {'key': 'C', 'text': 'Forget experience'}, {'key': 'D', 'text': 'Share experience'}]},
                {'content': '"签订合同"的英文翻译是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Break a contract'}, {'key': 'B', 'text': 'Sign a contract'}, {'key': 'C', 'text': 'Read a contract'}, {'key': 'D', 'text': 'Modify a contract'}]},
                {'content': '"商量"的英文翻译是什么？', 'type': '单选题', 'options': [{'key': 'A', 'text': 'Answer'}, {'key': 'B', 'text': 'Discuss'}, {'key': 'C', 'text': 'Refuse'}, {'key': 'D', 'text': 'Accept'}]},
            ]
        }
    }
    
    lang_key = language.lower() if language else 'japanese'
    diff_key = difficulty.lower() if difficulty else 'intermediate'
    
    if lang_key not in base_questions:
        lang_key = 'japanese'
    if diff_key not in base_questions[lang_key]:
        diff_key = 'intermediate'
    
    available_questions = base_questions[lang_key][diff_key]
    
    for i in range(count):
        base_q = available_questions[i % len(available_questions)]
        questions.append({
            'id': i + 1,
            'content': base_q['content'],
            'type': base_q['type'],
            'options': base_q['options'],
            'audio_available': True,
            'audio_url': None
        })
    
    return questions

# 获取考试题目API
@app.route('/api/exams/<exam_id>/questions', methods=['GET'])
def get_exam_questions(exam_id):
    result = check_exam_permission()
    if result:
        return result
    
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        questions = exam_service.get_questions(exam_id)
        
        if not questions:
            return jsonify({'success': False, 'message': '考试不存在或没有题目'}), 404
        
        return jsonify({'success': True, 'data': questions})
    except Exception as e:
        logger.error(f"获取考试题目失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 获取单个考试详情API
@app.route('/api/exams/<exam_id>', methods=['GET'])
def get_exam(exam_id):
    result = check_exam_permission()
    if result:
        return result
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
        exam = cursor.fetchone()
    
    if exam:
        exam_data = {
            'id': exam['id'],
            'name': exam['title'],
            'description': exam['description'],
            'duration': exam['duration'],
            'total_questions': exam['question_count'],
            'passing_score': exam['passing_score'],
            'language': exam['language'],
            'difficulty_level': exam['level'],
            'exam_type': 'standard',
            'audio_type': None
        }
        return jsonify({'success': True, 'data': exam_data})
    else:
        return jsonify({'success': False, 'message': '考试不存在'}), 404

# 创建考试API
@app.route('/api/exams', methods=['POST'])
def create_exam():
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'success': False, 'message': '缺少考试名称'}), 400
    
    import uuid
    exam_id = str(uuid.uuid4())
    exam_type = data.get('exam_type', 'simulation')
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO exams 
        (id, title, description, duration, question_count, total_points, passing_score, status, language, level, shuffle_questions, shuffle_options, allow_retake, max_retakes, created_by, created_at, updated_at, exam_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
        exam_id,
        data.get('name'),
        data.get('description', ''),
        data.get('duration', 60),
        data.get('total_questions', 50),
        data.get('total_points', 100.0),
        data.get('passing_score', 60.0),
        'active',
        data.get('language', 'japanese'),
        data.get('difficulty_level', 'intermediate'),
        1,
        1,
        1,
        3,
        'admin',
        int(time.time()),
        int(time.time()),
        exam_type
        ))
        
        conn.commit()
    
    return jsonify({'success': True, 'message': '考试创建成功', 'exam_id': exam_id})

# 测试路由
@app.route('/test')
def test():
    return jsonify({'status': 'success', 'message': '系统运行正常'})

# 矩阵题库管理页面
@app.route('/matrix_management')
def matrix_management():
    return render_template('matrix_management.html')

# 审批管理页面
@app.route('/approval_management')
def approval_management():
    return render_template('approval_management.html')

# 通知中心页面
@app.route('/notification_center')
def notification_center():
    return render_template('notification_center.html')

# 通知管理页面(管理员)
@app.route('/notification_admin')
def notification_admin():
    return render_template('notification_admin.html')

# 学生行为管理页面
@app.route('/admin/student_behavior')
@require_admin
def student_behavior_management():
    return render_template('admin/student_behavior.html')

# 锦标赛管理页面
@app.route('/admin/tournament')
@require_admin
def tournament_management():
    return render_template('admin/tournament.html')

# 学生端锦标赛页面
@app.route('/student/tournament')
@require_login
def student_tournament():
    return render_template('student/tournament.html')

# 用户信息栏页面
@app.route('/user_info')
def user_info():
    return render_template('user_info_bar.html')

# ============================================
# 备份管理API
# ============================================
# 文件整理页面路由
@app.route('/file_organizer')
def file_organizer():
    return render_template('file_organizer.html')

@app.route('/backup_manager')
def backup_manager():
    import os
    from datetime import datetime
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backup_root = os.path.join(project_root, 'backups')
    iso_directory = os.path.join(backup_root, 'iso')
    db_backup_directory = os.path.join(backup_root, 'database')
    config_backup_directory = os.path.join(backup_root, 'config')
    
    os.makedirs(backup_root, exist_ok=True)
    os.makedirs(iso_directory, exist_ok=True)
    os.makedirs(db_backup_directory, exist_ok=True)
    os.makedirs(config_backup_directory, exist_ok=True)
    
    iso_files = []
    if os.path.exists(iso_directory):
        for f in os.listdir(iso_directory):
            if f.endswith('.iso'):
                filepath = os.path.join(iso_directory, f)
                filesize = os.path.getsize(filepath)
                size_str = f"{filesize / (1024 * 1024):.2f} MB"
                iso_files.append({'name': f, 'path': filepath, 'size': size_str})
    
    last_backup_time = '从未备份'
    backup_files = []
    if os.path.exists(backup_root):
        for root, dirs, files in os.walk(backup_root):
            for f in files:
                filepath = os.path.join(root, f)
                mtime = os.path.getmtime(filepath)
                backup_files.append((mtime, filepath))
        
        if backup_files:
            latest_mtime = max(f[0] for f in backup_files)
            last_backup_time = datetime.fromtimestamp(latest_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    total_backups = sum(len(files) for _, _, files in os.walk(backup_root))
    db_backups = len([f for f in os.listdir(db_backup_directory) if os.path.isfile(os.path.join(db_backup_directory, f))]) if os.path.exists(db_backup_directory) else 0
    
    total_size = 0
    for root, dirs, files in os.walk(backup_root):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
    
    if total_size < 1024:
        size_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        size_str = f"{total_size / 1024:.2f} KB"
    else:
        size_str = f"{total_size / (1024 * 1024):.2f} MB"
    
    backup_paths = {
        'backup_root': backup_root,
        'iso_directory': iso_directory,
        'db_backup_directory': db_backup_directory,
        'config_backup_directory': config_backup_directory,
        'project_root': project_root,
        'last_backup_time': last_backup_time
    }
    
    stats = {
        'total_backups': total_backups,
        'iso_count': len(iso_files),
        'total_size': size_str,
        'db_backups': db_backups
    }
    
    return render_template('backup_manager.html', 
                           backup_paths=backup_paths,
                           iso_files=iso_files,
                           stats=stats)

@app.route('/api/backup/create', methods=['GET'])
def create_backup():
    import os
    import shutil
    from datetime import datetime
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backup_root = os.path.join(project_root, 'backups')
    db_backup_directory = os.path.join(backup_root, 'database')
    config_backup_directory = os.path.join(backup_root, 'config')
    
    os.makedirs(db_backup_directory, exist_ok=True)
    os.makedirs(config_backup_directory, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    db_source = os.path.join(project_root, 'flask-app', 'mtscos.db')
    db_dest = os.path.join(db_backup_directory, f'mtscos_{timestamp}.db')
    if os.path.exists(db_source):
        shutil.copy2(db_source, db_dest)
    
    config_source = os.path.join(project_root, 'flask-app', 'config.py')
    config_dest = os.path.join(config_backup_directory, f'config_{timestamp}.py')
    if os.path.exists(config_source):
        shutil.copy2(config_source, config_dest)
    
    return jsonify({'success': True, 'message': '备份创建成功', 'timestamp': timestamp})

@app.route('/api/backup/create-iso', methods=['GET'])
def create_iso():
    return jsonify({'success': True, 'message': 'ISO镜像生成功能已预留,可通过工具如mkisofs实现'})

@app.route('/api/backup/clean', methods=['GET'])
def clean_backups():
    import os
    from datetime import datetime, timedelta
    
    backup_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    cutoff_date = datetime.now() - timedelta(days=30)
    deleted_count = 0
    
    for root, dirs, files in os.walk(backup_root):
        for f in files:
            filepath = os.path.join(root, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff_date:
                os.remove(filepath)
                deleted_count += 1
    
    return jsonify({'success': True, 'message': f'清理完成,共删除 {deleted_count} 个旧备份文件'})

# ============================================
# 文件整理和路径修复API
# ============================================
@app.route('/api/file/organize')
def organize_files():
    import subprocess
    result = subprocess.run(
        ['python3', 'file_organizer.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True,
        timeout=300
    )
    response = jsonify({
        'success': True,
        'message': '文件整理完成',
        'output': result.stdout
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/file/fix-paths')
def fix_paths():
    import subprocess
    result = subprocess.run(
        ['python3', 'path_fixer.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True
    )
    return jsonify({
        'success': True,
        'message': '路径修复完成',
        'output': result.stdout
    })

@app.route('/api/file/recommendations')
def get_fix_recommendations():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn_cursor = conn.cursor()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT type, description, action, priority, file_path, details, status
        FROM file_organization_log
        WHERE status = 'pending'
        ORDER BY
        CASE priority
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
        END,
        id DESC
        LIMIT 100
        ''')
        
        rows = cursor.fetchall()
    
    recommendations = []
    for row in rows:
        try:
            details = json.loads(row['details']) if row['details'] else {}
        except Exception:
            details = {'raw': row['details']}
        recommendations.append({
            'type': row['type'],
            'description': row['description'],
            'action': row['action'],
            'priority': row['priority'],
            'file_path': row['file_path'],
            'details': details,
            'status': row['status']
        })
    
    return jsonify({
        'success': True,
        'count': len(recommendations),
        'recommendations': recommendations
    })

@app.route('/api/file/categories')
def get_file_categories():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn_cursor = conn.cursor()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT category, COUNT(*) as count, SUM(file_size) as total_size
        FROM file_category_index
        WHERE status = 'active'
        GROUP BY category
        ORDER BY count DESC
        ''')
        
        rows = cursor.fetchall()
    
    categories = []
    for row in rows:
        total_size = row['total_size'] or 0
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.2f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.2f} MB"
        
        categories.append({
            'name': row['category'],
            'file_count': row['count'],
            'total_size': size_str
        })
    
    return jsonify({
        'success': True,
        'categories': categories
    })

# ============================================
# AI考试系统API
# ============================================

# 摸底测试页面 - 学生必须先完成摸底测试才能参加正式考试
@app.route('/exam/placement_test')
@require_login
def placement_test_page():
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    
    # 验证用户角色
    student_roles = ['student', 'student_vip', 'exam_expert']
    if role not in student_roles:
        return redirect('/dashboard')
    
    # 检查是否已经完成过摸底测试
    has_completed = False
    current_level = None
    try:
        from app.services.placement_test_service import get_placement_test_service
        placement_service = get_placement_test_service()
        reports = placement_service.get_user_reports(user_id, limit=1)
        if reports:
            has_completed = True
            current_level = reports[0].get('overall_level')
    except Exception as e:
        logger.error(f"检查摸底测试状态失败: {e}")
    
    test_info = {
        'title': '智能摸底测试',
        'description': '通过综合测试评估您的知识水平，为您推荐合适的学习路径',
        'duration': '30分钟',
        'questions': '30道',
        'subjects': ['数学', '物理', '英语', '化学']
    }
    
    return render_template('placement_test.html', 
                           username=username, 
                           role=role,
                           user_id=user_id,
                           has_completed=has_completed,
                           current_level=current_level,
                           test_info=test_info)

# 摸底测试答题页面
@app.route('/exam/placement_test/take/<test_id>')
@require_login
def take_placement_test(test_id):
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    
    # 验证用户角色
    student_roles = ['student', 'student_vip', 'exam_expert']
    if role not in student_roles:
        return redirect('/dashboard')
    
    # 验证测试是否属于当前用户
    try:
        from app.services.placement_test_service import get_placement_test_service
        placement_service = get_placement_test_service()
        test = placement_service.get_placement_test(test_id)
        if not test or test['user_id'] != user_id:
            return redirect('/exam/placement_test')
    except Exception as e:
        logger.error(f"验证测试失败: {e}")
        return redirect('/exam/placement_test')
    
    return render_template('placement_test_take.html', 
                           username=username,
                           test_id=test_id)

# 年级设置页面
@app.route('/exam/set_grade', methods=['GET', 'POST'])
@require_login
def set_grade():
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    error = None
    
    # 初始化题库信息
    grade_bank_info = {}
    grade_bank_data = {}
    
    student_roles = ['student', 'student_vip', 'exam_expert']
    if role not in student_roles:
        return redirect('/dashboard')
    
    # 预定义所有年级
    all_grades = [
        '小学1年级', '小学2年级', '小学3年级', '小学4年级', '小学5年级', '小学6年级',
        '初中1年级', '初中2年级', '初中3年级',
        '高中1年级', '高中2年级', '高中3年级',
        '大学1年级', '大学2年级', '大学3年级', '大学4年级', '研究生', '博士生',
        '成人大学', '成人日语N5', '成人日语N4', '成人日语N3', '成人日语N2', '成人日语N1',
        '雅思4.0', '雅思5.0', '雅思5.5', '雅思6.0', '雅思6.5', '雅思7.0+',
        '托福60分', '托福70分', '托福80分', '托福90分', '托福100分', '托福110+',
        'AMC8入门', 'AMC8进阶', 'AMC8冲刺', '华罗庚小学组', '华罗庚初中组', '华罗庚高中组'
    ]
    
    # 获取题库信息
    try:
        from app.services.grade_bank_service import get_grade_bank_service
        grade_bank_service = get_grade_bank_service()
        
        for grade in all_grades:
            summary = grade_bank_service.get_grade_bank_summary(grade)
            grade_bank_info[grade] = {
                'total_banks': summary['total_banks'],
                'total_questions': summary['total_questions']
            }
            grade_bank_data[grade] = summary
    except Exception as e:
        logger.error(f"获取题库信息失败: {e}")
    
    try:
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        grade_manager.init_database()
        
        if request.method == 'POST':
            grade = request.form.get('grade')
            if grade_manager.set_user_grade(user_id, grade):
                logger.info(f"用户 {username} 设置年级为: {grade}")
                try:
                    from app.services.grade_bank_service import get_grade_bank_service
                    banks = get_grade_bank_service().get_banks_for_grade(grade)
                    logger.info(f"年级 {grade} 绑定了 {len(banks)} 个题库")
                except Exception:
                    pass
                return redirect('/exam/placement_test')
            else:
                error = '无效的年级选择'
    
    except Exception as e:
        logger.error(f"设置年级失败: {e}")
        error = '设置年级失败'
    
    return render_template('set_grade.html', 
                           username=username,
                           grade_bank_info=grade_bank_info,
                           grade_bank_data=grade_bank_data,
                           error=error)

# 专业摸底测试页面
@app.route('/exam/major_placement_test', methods=['GET', 'POST'])
@require_login
def major_placement_test():
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    
    student_roles = ['student', 'student_vip', 'exam_expert']
    if role not in student_roles:
        return redirect('/dashboard')
    
    try:
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        
        user_grade = grade_manager.get_user_grade(user_id)
        if not user_grade or not grade_manager.is_college_level(user_grade):
            return redirect('/exam/exam_center')
        
        if request.method == 'POST':
            major = request.form.get('major')
            if major:
                result = grade_manager.create_major_placement_test(user_id, major)
                return redirect(f'/exam/placement_test/take/{result["test_id"]}')
        
        majors = ['计算机科学', '人工智能', '软件工程', '数据科学', '数学', '物理学', '化学', '生物学', '经济学', '管理学']
        
        return render_template('major_placement_test.html', 
                           username=username,
                           grade=user_grade,
                           majors=majors)
    except Exception as e:
        logger.error(f"专业摸底测试失败: {e}")
        return redirect('/exam/exam_center')

# 成人教育摸底测试页面
@app.route('/exam/adult_placement_test', methods=['GET', 'POST'])
@require_login
def adult_placement_test():
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    
    student_roles = ['student', 'student_vip', 'exam_expert']
    if role not in student_roles:
        return redirect('/dashboard')
    
    try:
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        
        user_grade = grade_manager.get_user_grade(user_id)
        if not user_grade or not grade_manager.is_adult_education(user_grade):
            return redirect('/exam/exam_center')
        
        if request.method == 'POST':
            subject = request.form.get('subject')
            if subject:
                result = grade_manager.create_adult_placement_test(user_id, subject)
                return redirect(f'/exam/placement_test/take/{result["test_id"]}')
        
    except Exception as e:
        logger.error(f"成人教育摸底测试失败: {e}")
        return redirect('/exam/exam_center')
    
    return render_template('adult_placement_test.html', 
                           username=username,
                           grade=user_grade)

# 考试中心页面 - 学生登录后直接进入
@app.route('/exam/exam_center')
@require_login
def exam_center():
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    
    # 验证用户角色
    student_roles = ['student', 'student_vip', 'exam_expert']
    if role not in student_roles:
        # 非学生角色重定向到dashboard
        return redirect('/dashboard')
    
    logger.info(f"考试中心访问 - 用户: {username}, 角色: {role}, 用户ID: {user_id}")
    
    # 获取用户年级
    user_grade = None
    try:
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        user_grade = grade_manager.get_user_grade(user_id)
    except Exception as e:
        logger.warning(f"获取用户年级失败: {e}")
    
    # 如果未设置年级,重定向到年级设置页面
    if not user_grade:
        logger.info(f"用户 {username} 未设置年级,重定向到年级设置页面")
        return redirect('/exam/set_grade')
    
    # 检查是否需要完成综合摸底测试
    has_completed_placement = True
    reports = []
    
    # 成人教育需要特殊处理 - 先选择科目再进行摸底测试
    if grade_manager.is_adult_education(user_grade):
        # 检查是否已完成成人教育科目摸底测试
        if not grade_manager.has_completed_major_test(user_id):
            logger.info(f"用户 {username} 为成人教育,未完成科目摸底测试")
            return redirect('/exam/adult_placement_test')
    
    # 对于雅思、托福、数学竞赛,跳过摸底测试
    elif not (grade_manager.is_ielts(user_grade) or 
              grade_manager.is_toefl(user_grade) or 
              grade_manager.is_math_competition(user_grade)):
        try:
            from app.services.placement_test_service import get_placement_test_service
            placement_service = get_placement_test_service()
            reports = placement_service.get_user_reports(user_id, limit=10)
            has_completed_placement = len(reports) > 0
        except Exception as e:
            logger.warning(f"检查摸底测试状态失败: {e}")
        
        # 如果未完成摸底测试,重定向到摸底测试页面
        if not has_completed_placement:
            logger.info(f"用户 {username} 未完成摸底测试,重定向到摸底测试页面")
            return redirect('/exam/placement_test')
    
    # 检查大学级别用户是否已完成专业摸底测试
    if grade_manager.is_college_level(user_grade):
        if not grade_manager.has_completed_major_test(user_id):
            logger.info(f"用户 {username} 为大学级别,未完成专业摸底测试")
            return redirect('/exam/major_placement_test')
    
    # 自动更新题库
    try:
        from app.utils.question_auto_updater import auto_update_on_access
        update_result = auto_update_on_access()
        if update_result:
            if update_result.get('success'):
                logger.info(f"题库自动更新成功,添加了 {update_result.get('added')} 道新题目")
            else:
                logger.warning(f"题库自动更新失败: {update_result.get('message')}")
    except Exception as e:
        logger.warning(f"题库自动更新模块加载失败: {e}")
    
    # 获取可用考试列表(使用ExamManager)
    exams_list = []
    categories = []
    try:
        from app.services.exam_manager import exam_manager
        
        # 获取所有考试分类
        categories = exam_manager.get_all_categories()
        
        # 根据年级获取匹配的考试
        exams = exam_manager.get_exams_by_grade(user_grade)
        
        # 如果没有年级匹配的考试,获取所有考试
        if not exams:
            exams = exam_manager.get_exams_by_category()
        
        # 转换为字典列表
        exams_list = exams
        
    except Exception as e:
        logger.error(f"获取考试列表失败: {e}")
    
    # 获取用户当前水平
    current_level = None
    if reports:
        current_level = reports[0].get('overall_level')
    
    return render_template('exam_center.html', 
                           username=username, 
                           role=role,
                           user_id=user_id,
                           exams=exams_list,
                           categories=categories,
                           current_level=current_level)

# ============================================

# 开始考试会话
@app.route('/api/exam/start', methods=['POST'])
def start_exam_api():
    data = request.get_json()
    exam_id = data.get('exam_id')
    user_id = data.get('user_id', 1)  # 默认用户ID
    
    if not exam_id:
        return jsonify({'success': False, 'message': '缺少考试ID'}), 400
    
    try:
        from app.ai.exam_system_integrator import exam_system_integrator
        result = exam_system_integrator.start_exam_session(exam_id, user_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'开始考试失败: {str(e)}'}), 500

# 提交答题
@app.route('/api/exam/answer', methods=['POST'])
def submit_answer_api():
    data = request.get_json()
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    user_answer = data.get('user_answer')
    correct_answer = data.get('correct_answer')
    
    if not session_id or question_id is None or user_answer is None:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    try:
        from app.ai.exam_system_integrator import exam_system_integrator
        result = exam_system_integrator.submit_exam_answer(
            session_id, question_id, user_answer, correct_answer
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'提交答案失败: {str(e)}'}), 500

# 结束考试并获取AI分析
@app.route('/api/exam/finish', methods=['POST'])
def finish_exam_api():
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'message': '缺少会话ID'}), 400
    
    try:
        from app.ai.exam_system_integrator import exam_system_integrator
        result = exam_system_integrator.finish_exam_session(session_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'结束考试失败: {str(e)}'}), 500

# 获取AI教师反馈
@app.route('/api/exam/teacher-feedback', methods=['POST'])
def get_teacher_feedback_api():
    data = request.get_json()
    user_id = data.get('user_id', 1)
    exam_id = data.get('exam_id')
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'message': '缺少会话ID'}), 400
    
    try:
        from app.ai.smart_teacher_ai import smart_teacher
        result = smart_teacher.generate_personalized_feedback(user_id, exam_id, session_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取反馈失败: {str(e)}'}), 500

# 获取用户考试历史
@app.route('/api/exam/history/<int:user_id>', methods=['GET'])
def get_exam_history_api(user_id):
    try:
        from app.ai.exam_system_integrator import exam_system_integrator
        result = exam_system_integrator.get_user_exam_history(user_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取历史失败: {str(e)}'}), 500

# ============================================
# 考试页面需要的API (exam_page.html)
# ============================================

@app.route('/api/exam/exams/<exam_id>', methods=['GET'])
def get_exam_detail(exam_id):
    """获取考试详情"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
            exam = cursor.fetchone()
            
            if not exam:
                return jsonify({'success': False, 'error': '考试不存在'}), 404
            
            exam_data = dict(exam)
            exam_type = exam_data.get('exam_type', 'simulation')
            exam_data['exam_type_label'] = '历年真题' if exam_type == 'real' else '拟真试题'
            
            return jsonify({'success': True, 'data': exam_data})
    except Exception as e:
        logger.error(f"获取考试详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/exam/exams/<exam_id>/questions', methods=['GET'])
def get_exam_questions_v2(exam_id):
    """获取考试题目"""
    try:
        import json
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM questions WHERE exam_id = ?', (exam_id,))
            questions = cursor.fetchall()
            
            result = []
            for q in questions:
                q_dict = dict(q)
                # 解析 options JSON 字符串
                if isinstance(q_dict.get('options'), str):
                    try:
                        q_dict['options'] = json.loads(q_dict['options'])
                    except:
                        q_dict['options'] = []
                # 解析 tags JSON 字符串
                if isinstance(q_dict.get('tags'), str):
                    try:
                        q_dict['tags'] = json.loads(q_dict['tags'])
                    except:
                        q_dict['tags'] = []
                result.append(q_dict)
            
            return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"获取题目失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/exam/exams/<exam_id>/papers', methods=['POST'])
def create_exam_paper(exam_id):
    """创建考试试卷"""
    try:
        user_id = session.get('user_id', 1)
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 检查考试是否存在
            cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
            exam = cursor.fetchone()
            
            if not exam:
                return jsonify({'success': False, 'error': '考试不存在'}), 404
            
            # 获取题目
            cursor.execute('SELECT * FROM questions WHERE exam_id = ?', (exam_id,))
            questions = cursor.fetchall()
            
            if not questions:
                return jsonify({'success': False, 'error': '考试没有题目'}), 400
            
            # 创建试卷记录
            import uuid
            paper_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO exam_papers (id, exam_id, user_id, status, created_at, updated_at)
                VALUES (?, ?, ?, 'in_progress', datetime('now'), datetime('now'))
            ''', (paper_id, exam_id, user_id))
            conn.commit()
            
            return jsonify({'success': True, 'paper_id': paper_id})
    except Exception as e:
        logger.error(f"创建试卷失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/exam/papers/<paper_id>/questions', methods=['GET'])
def get_paper_questions(paper_id):
    """获取试卷题目"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取试卷信息
            cursor.execute('SELECT exam_id FROM exam_papers WHERE id = ?', (paper_id,))
            paper = cursor.fetchone()
            
            if not paper:
                return jsonify({'success': False, 'error': '试卷不存在'}), 404
            
            # 获取题目
            cursor.execute('SELECT * FROM questions WHERE exam_id = ?', (paper['exam_id'],))
            questions = cursor.fetchall()
            
            return jsonify({'success': True, 'data': [dict(q) for q in questions]})
    except Exception as e:
        logger.error(f"获取试卷题目失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/exam/papers/<paper_id>/start', methods=['POST'])
def start_exam_paper(paper_id):
    """开始考试"""
    try:
        user_id = session.get('user_id', 1)
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 更新试卷状态
            cursor.execute('''
                UPDATE exam_papers 
                SET status = 'in_progress', start_time = datetime('now')
                WHERE id = ? AND user_id = ?
            ''', (paper_id, user_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'error': '试卷不存在'}), 404
            
            return jsonify({'success': True, 'message': '考试已开始'})
    except Exception as e:
        logger.error(f"开始考试失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/exam/papers/<paper_id>/answer', methods=['POST'])
def save_exam_answer(paper_id):
    """保存答题答案"""
    try:
        user_id = session.get('user_id', 1)
        data = request.get_json()
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        if not question_id:
            return jsonify({'success': False, 'error': '缺少题目ID'}), 400
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取现有答案
            cursor.execute('SELECT answers FROM exam_papers WHERE id = ? AND user_id = ?', (paper_id, user_id))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'success': False, 'error': '试卷不存在'}), 404
            
            answers = json.loads(row[0]) if row[0] else {}
            answers[question_id] = answer
            
            cursor.execute('UPDATE exam_papers SET answers = ? WHERE id = ?', (json.dumps(answers), paper_id))
            conn.commit()
            
            return jsonify({'success': True})
    except Exception as e:
        logger.error(f"保存答案失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/exam/papers/<paper_id>/submit', methods=['POST'])
def submit_exam_paper(paper_id):
    """提交试卷"""
    try:
        user_id = session.get('user_id', 1)
        data = request.get_json(silent=True) or {}
        answers = data.get('answers', {})
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取试卷信息
            cursor.execute('SELECT exam_id FROM exam_papers WHERE id = ? AND user_id = ?', (paper_id, user_id))
            paper = cursor.fetchone()
            
            if not paper:
                return jsonify({'success': False, 'error': '试卷不存在'}), 404
            
            # 计算分数
            exam_id = paper[0]
            cursor.execute('SELECT id, correct_answer, points FROM questions WHERE exam_id = ?', (exam_id,))
            questions = cursor.fetchall()
            
            total_score = 0
            total_points = 0
            
            for q in questions:
                q_id, correct, pts = q
                total_points += pts
                if q_id in answers and answers[q_id] == correct:
                    total_score += pts
            
            # 更新试卷
            cursor.execute('''
                UPDATE exam_papers 
                SET status = 'completed', 
                    answers = ?, 
                    scores = ?,
                    end_time = datetime('now'),
                    submitted_at = datetime('now')
                WHERE id = ?
            ''', (json.dumps(answers), json.dumps({'total': total_score, 'max': total_points}), paper_id))
            conn.commit()
            
            accuracy = (total_score / total_points * 100) if total_points > 0 else 0
            
            return jsonify({
                'success': True, 
                'data': {
                    'total_score': total_score,
                    'max_score': total_points,
                    'accuracy': accuracy / 100,
                    'time_taken': 0
                }
            })
    except Exception as e:
        logger.error(f"提交试卷失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# AI生成题目测试
@app.route('/api/test-ai-questions', methods=['GET'])
def test_ai_questions_api():
    language = request.args.get('language', '日语')
    difficulty = request.args.get('difficulty', '初级')
    exam_type = request.args.get('type', 'standard')
    count = int(request.args.get('count', 5))
    
    try:
        from app.ai.exam_expert_generator import enhanced_exam_generator
        questions = enhanced_exam_generator.generate_questions(
            language, difficulty, exam_type, count
        )
        
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成题目失败: {str(e)}'}), 500

# 音频文件访问路由
@app.route('/audio/<language>/<accent>/<voice>/<filename>')
def serve_audio(language, accent, voice, filename):
    from flask import send_from_directory
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio', language, accent, voice)
    return send_from_directory(audio_dir, filename)

# 音频测试页面路由
@app.route('/test/audio')
def audio_test():
    return render_template('audio_test.html')

@app.route('/api/exam/submit', methods=['POST'])
def submit_exam():
    """提交考试结果（增强版听力测试）"""
    try:
        user_id = session.get('user_id', 1)
        data = request.get_json()
        answers = data.get('answers', {})
        score = data.get('score', 0)
        correct = data.get('correct', 0)
        total = data.get('total', 0)
        speed = data.get('speed', 1.0)
        voice = data.get('voice', 'aria')
        topic = data.get('topic', 'daily')
        difficulty = data.get('difficulty', '中级')
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        import uuid
        exam_paper_id = str(uuid.uuid4())
        exam_id = f"listen_test_{int(time.time())}"
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exam_results (exam_paper_id, exam_id, user_id, total_score, correct_count, total_count, 
                                        accuracy, analysis, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (exam_paper_id, exam_id, str(user_id), score, correct, total, accuracy, 
                  json.dumps({'answers': answers, 'speed': speed, 'voice': voice, 
                             'topic': topic, 'difficulty': difficulty})))
            conn.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'score': score,
                'correct': correct,
                'total': total,
                'accuracy': accuracy / 100,
                'difficulty': difficulty,
                'speed': speed
            },
            'message': '提交成功'
        })
    except Exception as e:
        logger.error(f"提交考试失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 前端API路由补充 - 用户数据相关
# ============================================================

@app.route('/api/user/data/get', methods=['POST'])
def api_user_data_get():
    try:
        data = request.get_json() or {}
        username = data.get('username') or session.get('username')
        collection = data.get('collection')
        
        if not username:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        with get_db_connection() as conn:
            if collection:
                cursor = conn.execute('SELECT * FROM data_records WHERE collection = ?', (collection,))
            else:
                cursor = conn.execute('SELECT * FROM data_records')
            records = cursor.fetchall()
            
        return jsonify({
            'success': True,
            'data': [dict(r) for r in records]
        })
    except Exception as e:
        logger.error(f"API /api/user/data/get error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/data/store', methods=['POST'])
def api_user_data_store():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '数据为空'}), 400
        
        collection = data.get('collection', 'default')
        payload = data.get('data', {})
        
        with get_db_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO data_records (collection, data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (collection, json.dumps(payload), int(time.time()), int(time.time())))
            conn.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        logger.error(f"API /api/user/data/store error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/data/delete', methods=['POST'])
def api_user_data_delete():
    try:
        data = request.get_json()
        record_id = data.get('id')
        
        if not record_id:
            return jsonify({'success': False, 'error': '缺少ID'}), 400
        
        with get_db_connection() as conn:
            conn.execute('DELETE FROM data_records WHERE id = ?', (record_id,))
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"API /api/user/data/delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# 前端API路由补充 - AI相关
# ============================================================

@app.route('/api/ai/status', methods=['GET'])
def api_ai_status():
    try:
        return jsonify({
            'success': True,
            'status': 'online',
            'model': 'local',
            'version': '4.4.0'
        })
    except Exception as e:
        logger.error(f"API /api/ai/status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/instances', methods=['GET'])
def api_ai_instances():
    try:
        with get_db_connection() as conn:
            cursor = conn.execute('SELECT * FROM ai_employees')
            employees = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': [dict(e) for e in employees]
        })
    except Exception as e:
        logger.error(f"API /api/ai/instances error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/tasks', methods=['GET'])
def api_ai_tasks():
    try:
        return jsonify({
            'success': True,
            'data': []
        })
    except Exception as e:
        logger.error(f"API /api/ai/tasks error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/history', methods=['GET'])
def api_ai_history():
    try:
        return jsonify({
            'success': True,
            'data': []
        })
    except Exception as e:
        logger.error(f"API /api/ai/history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/add-instance', methods=['POST'])
def api_ai_add_instance():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '数据为空'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.execute('''
                INSERT OR IGNORE INTO ai_employees (employee_id, name, title, description, category,
                                        capabilities, efficiency, workload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('employee_id', f"emp_{int(time.time())}"),
                data.get('name', ''),
                data.get('title', ''),
                data.get('description', ''),
                data.get('category', 'general'),
                json.dumps(data.get('capabilities', [])),
                data.get('efficiency', 100),
                data.get('workload', 0),
                int(time.time()),
                int(time.time())
            ))
            conn.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        logger.error(f"API /api/ai/add-instance error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/generate-tasks', methods=['POST'])
def api_ai_generate_tasks():
    try:
        return jsonify({
            'success': True,
            'tasks': []
        })
    except Exception as e:
        logger.error(f"API /api/ai/generate-tasks error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# 前端API路由补充 - 题库相关
# ============================================================

@app.route('/api/banks', methods=['GET', 'POST'])
def api_banks():
    try:
        if request.method == 'GET':
            with get_db_connection() as conn:
                cursor = conn.execute('SELECT * FROM question_banks LIMIT 20')
                banks = cursor.fetchall()
            return jsonify({'success': True, 'data': [dict(b) for b in banks]})
        else:
            return jsonify({'success': True, 'message': '题库更新成功'})
    except Exception as e:
        logger.error(f"API /api/banks error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data', methods=['GET'])
def api_data():
    try:
        return jsonify({
            'success': True,
            'version': '4.4.0',
            'timestamp': int(time.time())
        })
    except Exception as e:
        logger.error(f"API /api/data error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# 前端API路由补充 - 认证相关
# ============================================================

@app.route('/api/auth/user', methods=['GET'])
def api_auth_user():
    try:
        username = session.get('username')
        if username:
            return jsonify({'success': True, 'user': {'username': username, 'role': session.get('role', 'user')}})
        return jsonify({'success': False, 'error': '未登录'}), 401
    except Exception as e:
        logger.error(f"API /api/auth/user error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/check-permission', methods=['POST'])
def api_auth_check_permission():
    try:
        data = request.get_json()
        permission = data.get('permission', '')
        role = session.get('role', 'user')
        
        permissions = {
            'admin': ['all'],
            'teacher': ['exam', 'manage'],
            'user': ['view']
        }
        
        has_permission = role == 'admin' or permission in permissions.get(role, [])
        return jsonify({'success': True, 'hasPermission': has_permission})
    except Exception as e:
        logger.error(f"API /api/auth/check-permission error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/unlock', methods=['POST'])
def api_auth_unlock():
    try:
        return jsonify({'success': True, 'message': '解锁成功'})
    except Exception as e:
        logger.error(f"API /api/auth/unlock error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/security/event', methods=['POST'])
def api_security_event():
    try:
        data = request.get_json()
        logger.info(f"安全事件: {data}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"API /api/security/event error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# 前端API路由补充 - 绑定管理相关
# ============================================================

@app.route('/api/binding/config/all', methods=['GET'])
def api_binding_config_all():
    try:
        return jsonify({'success': True, 'data': []})
    except Exception as e:
        logger.error(f"API /api/binding/config/all error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/config/get', methods=['POST'])
def api_binding_config_get():
    try:
        return jsonify({'success': True, 'data': {}})
    except Exception as e:
        logger.error(f"API /api/binding/config/get error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/config/update', methods=['POST'])
def api_binding_config_update():
    try:
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"API /api/binding/config/update error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/pages/scan', methods=['GET'])
def api_binding_pages_scan():
    try:
        return jsonify({'success': True, 'pages': []})
    except Exception as e:
        logger.error(f"API /api/binding/pages/scan error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/page/get', methods=['POST'])
def api_binding_page_get():
    try:
        return jsonify({'success': True, 'data': {}})
    except Exception as e:
        logger.error(f"API /api/binding/page/get error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/page/bind', methods=['POST'])
def api_binding_page_bind():
    try:
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"API /api/binding/page/bind error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/page/bind-all', methods=['POST'])
def api_binding_page_bind_all():
    try:
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"API /api/binding/page/bind-all error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/usage/stats', methods=['GET'])
def api_binding_usage_stats():
    try:
        return jsonify({'success': True, 'stats': {}})
    except Exception as e:
        logger.error(f"API /api/binding/usage/stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/usage/record', methods=['POST'])
def api_binding_usage_record():
    try:
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"API /api/binding/usage/record error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/binding/auto-bind', methods=['POST'])
def api_binding_auto_bind():
    try:
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"API /api/binding/auto-bind error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# 前端API路由补充 - 日语考试相关
# ============================================================

@app.route('/api/jptest/questions', methods=['GET'])
def api_jptest_questions():
    try:
        return jsonify({'success': True, 'questions': []})
    except Exception as e:
        logger.error(f"API /api/jptest/questions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 听力训练系统API
# ============================================================

def require_listening_access(f):
    """听力训练访问装饰器 - 必须登录且是成人制教育学生"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查登录状态
        if 'user_id' not in session:
            logger.warning(f"[听力训练] 未登录用户尝试访问")
            return jsonify({'success': False, 'error': '请先登录', 'require_login': True}), 401
        
        # 检查是否是学生角色
        user_role = session.get('role', '')
        if user_role != 'student':
            logger.warning(f"[听力训练] 非学生用户尝试访问: role={user_role}")
            return jsonify({'success': False, 'error': '只有学生用户才能使用听力训练'}), 403
        
        # 检查是否是成人制教育学生
        user_id = session.get('user_id')
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT education_system FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return jsonify({'success': False, 'error': '用户不存在'}), 404
                
                education_system = result[0] if result[0] else 'regular'
                if education_system != 'adult':
                    logger.warning(f"[听力训练] 非成人制学生尝试访问: user_id={user_id}, education_system={education_system}")
                    return jsonify({'success': False, 'error': '听力训练仅对成人制教育学生开放'}), 403
        except Exception as e:
            logger.error(f"[听力训练] 权限验证失败: {e}")
            return jsonify({'success': False, 'error': '权限验证失败'}), 500
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/listening_training')
def listening_training_page():
    """听力训练页面 - 需要登录且是成人制教育学生"""
    # 检查登录状态
    if 'user_id' not in session:
        return redirect('/auth/login?redirect=/listening_training')
    
    # 检查是否是学生角色
    user_role = session.get('role', '')
    if user_role != 'student':
        return "听力训练仅对学生开放", 403
    
    # 检查是否是成人制教育学生
    user_id = session.get('user_id')
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT education_system FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if not result:
                return redirect('/auth/login?redirect=/listening_training')
            
            education_system = result[0] if result[0] else 'regular'
            if education_system != 'adult':
                return "听力训练仅对成人制教育学生开放", 403
    except Exception as e:
        logger.error(f"[听力训练] 权限验证失败: {e}")
        return "权限验证失败", 500
    
    try:
        # app.py在flask-app根目录，模板在app/templates
        template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates', 'listening_training.html')
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            logger.error(f"模板文件不存在: {template_file}")
            return "模板文件不存在", 404
    except Exception as e:
        logger.error(f"加载听力训练页面失败: {e}")
        return f"页面加载失败: {str(e)}", 500

@app.route('/api/listening/questions', methods=['GET'])
@require_listening_access
def get_listening_questions():
    """获取听力题列表 - 智能调取：先查数据库，不足则AI生成并入库"""
    try:
        language = request.args.get('language', 'all')
        difficulty = request.args.get('difficulty', 'all')
        topic = request.args.get('topic', 'all')
        limit = int(request.args.get('limit', 20))

        logger.info(f"[听力训练] 获取题目 - language={language}, difficulty={difficulty}, topic={topic}, limit={limit}")

        try:
            from ai_engines.listening_question_generator import get_listening_question_generator
            generator = get_listening_question_generator(DATABASE_PATH)
            result = generator.get_or_generate_questions(
                language=language,
                difficulty=difficulty,
                topic=topic,
                limit=limit
            )
            if result.get('success'):
                logger.info(f"[听力训练] 返回{result['total']}题（来自数据库:{result['from_db']}, AI生成:{result['generated']}）")
                return jsonify({
                    'success': True,
                    'data': result['data'],
                    'total': result['total'],
                    'from_db': result['from_db'],
                    'generated': result['generated']
                })
        except Exception as gen_e:
            logger.warning(f"[听力训练] AI生成器调用失败，回退到纯数据库查询: {gen_e}")

        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM listening_questions WHERE 1=1"
            params = []

            if language != 'all':
                query += " AND language = ?"
                params.append(language)
            if difficulty != 'all':
                query += " AND difficulty = ?"
                params.append(int(difficulty))
            if topic != 'all':
                query += " AND topic = ?"
                params.append(topic)

            query += f" ORDER BY difficulty ASC LIMIT {limit}"

            cursor.execute(query, tuple(params))
            questions = cursor.fetchall()

            result = []
            for q in questions:
                result.append({
                    'id': q['id'],
                    'language': q['language'],
                    'difficulty': q['difficulty'],
                    'topic': q['topic'],
                    'accent': q['accent'],
                    'content': q['content'],
                    'options': json.loads(q['options']) if q['options'] else [],
                    'correct_answer': q['correct_answer'],
                    'audio_url': q['audio_url'],
                    'transcript': q['transcript'],
                    'explanation': q['explanation'],
                    'duration': q['duration']
                })

            return jsonify({'success': True, 'data': result, 'total': len(result), 'from_db': len(result), 'generated': 0})
    except Exception as e:
        logger.error(f"获取听力题失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/listening/question/<question_id>', methods=['GET'])
@require_listening_access
def get_listening_question(question_id):
    """获取单个听力题详情"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM listening_questions WHERE id = ?", (question_id,))
            q = cursor.fetchone()
            
            if not q:
                return jsonify({'success': False, 'error': '题目不存在'}), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'id': q['id'],
                    'language': q['language'],
                    'difficulty': q['difficulty'],
                    'topic': q['topic'],
                    'accent': q['accent'],
                    'content': q['content'],
                    'options': json.loads(q['options']) if q['options'] else [],
                    'correct_answer': q['correct_answer'],
                    'audio_url': q['audio_url'],
                    'transcript': q['transcript'],
                    'explanation': q['explanation'],
                    'duration': q['duration']
                }
            })
    except Exception as e:
        logger.error(f"获取听力题详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/listening/submit', methods=['POST'])
@require_listening_access
def submit_listening_answer():
    """提交听力答案"""
    try:
        user_id = session.get('user_id', 'guest')
        data = request.get_json()
        question_id = data.get('question_id')
        answer = data.get('answer')
        time_spent = data.get('time_spent', 0)
        speed_used = data.get('speed_used', 1.0)
        voice_used = data.get('voice_used', 'aria')
        
        import uuid
        record_id = str(uuid.uuid4())
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取正确答案
            cursor.execute("SELECT correct_answer FROM listening_questions WHERE id = ?", (question_id,))
            q = cursor.fetchone()
            
            if not q:
                return jsonify({'success': False, 'error': '题目不存在'}), 404
            
            is_correct = 1 if answer == q['correct_answer'] else 0
            
            # 记录答题
            cursor.execute("""
                INSERT INTO listening_training_records 
                (id, user_id, question_id, is_correct, time_spent, speed_used, voice_used, attempts, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
            """, (record_id, str(user_id), question_id, is_correct, time_spent, speed_used, voice_used))
            
            # 更新统计
            cursor.execute("""
                INSERT INTO listening_training_stats (user_id, total_questions, correct_count, total_time, avg_speed, preferred_voice, last_training, updated_at)
                VALUES (?, 1, ?, ?, ?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    total_questions = total_questions + 1,
                    correct_count = correct_count + ?,
                    total_time = total_time + ?,
                    avg_speed = (avg_speed * total_questions + ?) / (total_questions + 1),
                    last_training = datetime('now'),
                    updated_at = datetime('now')
            """, (str(user_id), is_correct, time_spent, speed_used, voice_used, is_correct, time_spent, speed_used))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'is_correct': is_correct,
                'correct_answer': q['correct_answer']
            },
            'message': '答案提交成功'
        })
    except Exception as e:
        logger.error(f"提交听力答案失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/listening/stats', methods=['GET'])
@require_listening_access
def get_listening_stats():
    """获取听力训练统计"""
    try:
        user_id = request.args.get('user_id') or session.get('user_id', 'guest')
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM listening_training_stats WHERE user_id = ?", (str(user_id),))
            stats = cursor.fetchone()
            
            if not stats:
                return jsonify({
                    'success': True,
                    'data': {
                        'total_questions': 0,
                        'correct_count': 0,
                        'accuracy': 0,
                        'total_time': 0,
                        'avg_speed': 1.0,
                        'preferred_voice': 'aria'
                    }
                })
            
            accuracy = (stats['correct_count'] / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
            
            return jsonify({
                'success': True,
                'data': {
                    'total_questions': stats['total_questions'],
                    'correct_count': stats['correct_count'],
                    'accuracy': accuracy,
                    'total_time': stats['total_time'],
                    'avg_speed': stats['avg_speed'],
                    'preferred_voice': stats['preferred_voice'],
                    'last_training': stats['last_training']
                }
            })
    except Exception as e:
        logger.error(f"获取听力统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/listening/history', methods=['GET'])
@require_listening_access
def get_listening_history():
    """获取听力训练历史"""
    try:
        user_id = request.args.get('user_id') or session.get('user_id', 'guest')
        limit = int(request.args.get('limit', 50))
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT r.*, q.content, q.language, q.difficulty, q.topic
                FROM listening_training_records r
                LEFT JOIN listening_questions q ON r.question_id = q.id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (str(user_id), limit))
            
            records = cursor.fetchall()
            
            result = []
            for r in records:
                result.append({
                    'id': r['id'],
                    'question_id': r['question_id'],
                    'content': r['content'],
                    'language': r['language'],
                    'difficulty': r['difficulty'],
                    'topic': r['topic'],
                    'is_correct': r['is_correct'],
                    'time_spent': r['time_spent'],
                    'speed_used': r['speed_used'],
                    'voice_used': r['voice_used'],
                    'created_at': r['created_at']
                })
            
            return jsonify({'success': True, 'data': result, 'total': len(result)})
    except Exception as e:
        logger.error(f"获取听力历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 数学模型与解题系统API
# ============================================================

def _get_math_service():
    """获取数学模型服务实例"""
    from app.services.problem_solving_service import get_math_model_service
    return get_math_model_service(DATABASE_PATH)

def _get_math_generator():
    """获取数学题生成器实例"""
    from ai_engines.math_solver_engine import get_math_problem_generator
    return get_math_problem_generator(DATABASE_PATH)

def _get_math_solver():
    """获取数学解题引擎实例"""
    from ai_engines.math_solver_engine import get_math_solver
    return get_math_solver()

# ============================================================
# 数学模型与解题系统API - 访问权限控制
# ============================================================

def require_math_training_access(f):
    """数学训练访问装饰器 - 必须登录且是成人制教育学生"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查登录状态
        if 'user_id' not in session:
            logger.warning(f"[数学训练] 未登录用户尝试访问")
            return jsonify({'success': False, 'error': '请先登录', 'require_login': True}), 401
        
        # 检查是否是学生角色
        user_role = session.get('role', '')
        if user_role != 'student':
            logger.warning(f"[数学训练] 非学生用户尝试访问: role={user_role}")
            return jsonify({'success': False, 'error': '只有学生用户才能使用数学训练'}), 403
        
        # 检查是否是成人制教育学生
        user_id = session.get('user_id')
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT education_system FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return jsonify({'success': False, 'error': '用户不存在'}), 404
                
                education_system = result[0] if result[0] else 'regular'
                if education_system != 'adult':
                    logger.warning(f"[数学训练] 非成人制学生尝试访问: user_id={user_id}, education_system={education_system}")
                    return jsonify({'success': False, 'error': '数学训练仅对成人制教育学生开放'}), 403
        except Exception as e:
            logger.error(f"[数学训练] 权限验证失败: {e}")
            return jsonify({'success': False, 'error': '权限验证失败'}), 500
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/math_training')
def math_training_page():
    """数学训练页面 - 需要登录且是成人制教育学生"""
    # 检查登录状态
    if 'user_id' not in session:
        return redirect('/auth/login?redirect=/math_training')
    
    # 检查是否是学生角色
    user_role = session.get('role', '')
    if user_role != 'student':
        return "数学训练仅对学生开放", 403
    
    # 检查是否是成人制教育学生
    user_id = session.get('user_id')
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT education_system FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if not result:
                return redirect('/auth/login?redirect=/math_training')
            
            education_system = result[0] if result[0] else 'regular'
            if education_system != 'adult':
                return "数学训练仅对成人制教育学生开放", 403
    except Exception as e:
        logger.error(f"[数学训练] 权限验证失败: {e}")
        return "权限验证失败", 500
    
    try:
        template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates', 'math_training.html')
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            logger.error(f"数学训练模板文件不存在: {template_file}")
            return "页面开发中...", 404
    except Exception as e:
        logger.error(f"加载数学训练页面失败: {e}")
        return f"页面加载失败: {str(e)}", 500

@app.route('/api/math/stats', methods=['GET'])
@require_math_training_access
def math_get_stats():
    """获取数学系统统计"""
    try:
        user_id = session.get('user_id', '')
        service = _get_math_service()
        result = service.get_stats(user_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取数学统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/categories', methods=['GET'])
@require_math_training_access
def math_get_categories():
    """获取数学分类"""
    try:
        service = _get_math_service()
        result = service.get_categories()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取数学分类失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/concepts', methods=['GET'])
@require_math_training_access
def math_get_concepts():
    """获取数学概念列表"""
    try:
        category = request.args.get('category', '')
        difficulty = request.args.get('difficulty')
        keyword = request.args.get('keyword', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        service = _get_math_service()
        result = service.get_concepts(
            category=category,
            difficulty=int(difficulty) if difficulty else None,
            keyword=keyword,
            limit=limit,
            offset=offset
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取数学概念失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/methods', methods=['GET'])
@require_math_training_access
def math_get_methods():
    """获取解题方法列表"""
    try:
        category = request.args.get('category', '')
        method_type = request.args.get('method_type', '')
        keyword = request.args.get('keyword', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        service = _get_math_service()
        result = service.get_solution_methods(
            category=category,
            method_type=method_type,
            keyword=keyword,
            limit=limit,
            offset=offset
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取解题方法失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/problems', methods=['GET'])
@require_math_training_access
def math_get_problems():
    """获取数学题目列表 - 优先调取数据库，不足时AI生成补充"""
    try:
        category = request.args.get('category', 'all')
        difficulty = request.args.get('difficulty')
        problem_type = request.args.get('problem_type', '')
        keyword = request.args.get('keyword', '')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        auto_generate = request.args.get('auto_generate', 'true').lower() == 'true'

        service = _get_math_service()

        if category == 'all':
            categories = ['algebra', 'geometry', 'probability']
            db_problems = []
            total_from_db = 0
            per_cat = max(1, limit // len(categories))
            for cat in categories:
                result = service.get_problems(
                    category=cat,
                    difficulty=int(difficulty) if difficulty else None,
                    problem_type=problem_type,
                    keyword=keyword,
                    limit=per_cat,
                    offset=0
                )
                if result['success']:
                    db_problems.extend(result['data'])
                    total_from_db += result['total']
            db_problems = db_problems[:limit]
        else:
            result = service.get_problems(
                category=category,
                difficulty=int(difficulty) if difficulty else None,
                problem_type=problem_type,
                keyword=keyword,
                limit=limit,
                offset=offset
            )
            db_problems = result['data'] if result['success'] else []
            total_from_db = result.get('total', 0)

        generated_count = 0
        if auto_generate and len(db_problems) < limit:
            need = limit - len(db_problems)
            gen_category = category if category != 'all' else random.choice(['algebra', 'geometry', 'probability'])
            gen_difficulty = int(difficulty) if difficulty else 2

            generator = _get_math_generator()
            generated = generator.generate_problems(need, gen_category, gen_difficulty)

            for prob in generated:
                service.add_problem(prob)
                generated_count += 1

            db_problems.extend(generated)
            db_problems = db_problems[:limit]

        return jsonify({
            'success': True,
            'data': db_problems,
            'total': total_from_db + generated_count,
            'from_db': len(db_problems) - generated_count,
            'generated': generated_count
        })
    except Exception as e:
        logger.error(f"获取数学题目失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/problems/<problem_id>', methods=['GET'])
@require_math_training_access
def math_get_problem_detail(problem_id):
    """获取题目详情"""
    try:
        service = _get_math_service()
        problem = service.get_problem(problem_id)
        if problem:
            return jsonify({'success': True, 'data': problem})
        else:
            return jsonify({'success': False, 'error': '题目不存在'}), 404
    except Exception as e:
        logger.error(f"获取题目详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/solve', methods=['POST'])
@require_math_training_access
def math_solve_problem():
    """AI解题"""
    try:
        data = request.get_json(silent=True) or {}
        problem = data.get('problem', {})
        problem_id = data.get('problem_id', '')

        service = _get_math_service()
        if problem_id:
            problem_data = service.get_problem(problem_id)
            if problem_data:
                problem = problem_data

        if not problem:
            return jsonify({'success': False, 'error': '请提供题目'}), 400

        solver = _get_math_solver()
        result = solver.solve(problem)

        return jsonify(result)
    except Exception as e:
        logger.error(f"解题失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/submit', methods=['POST'])
@require_math_training_access
def math_submit_answer():
    """提交答案并记录"""
    try:
        data = request.get_json(silent=True) or {}
        problem_id = data.get('problem_id', '')
        user_answer = data.get('user_answer', '')
        time_spent = float(data.get('time_spent', 0))
        attempts = int(data.get('attempts', 1))
        hint_used = int(data.get('hint_used', 0))

        service = _get_math_service()
        problem = service.get_problem(problem_id)

        if not problem:
            return jsonify({'success': False, 'error': '题目不存在'}), 404

        correct_answer = problem.get('correct_answer', '')
        is_correct = str(user_answer).strip() == str(correct_answer).strip() or \
                     str(correct_answer).strip() in str(user_answer).strip()

        user_id = session.get('user_id', '')
        solution_data = {
            'problem_id': problem_id,
            'problem_content': problem.get('content', ''),
            'problem_type': problem.get('problem_type', ''),
            'difficulty': problem.get('difficulty', 1),
            'final_answer': str(user_answer),
            'is_correct': is_correct,
            'user_id': user_id,
            'time_spent': time_spent,
            'attempts': attempts,
            'hint_used': hint_used,
            'related_concepts': problem.get('related_concepts', []),
            'related_formulas': problem.get('related_formulas', [])
        }
        service.save_solution(solution_data)

        return jsonify({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'explanation': problem.get('answer_explanation', ''),
            'solution_steps': problem.get('solution_steps', [])
        })
    except Exception as e:
        logger.error(f"提交答案失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/generate', methods=['POST'])
@require_math_training_access
def math_generate_problems():
    """生成数学题目并入库"""
    try:
        data = request.get_json(silent=True) or {}
        count = int(data.get('count', 5))
        category = data.get('category', 'algebra')
        difficulty = int(data.get('difficulty', 2))
        save_to_db = data.get('save_to_db', True)

        generator = _get_math_generator()
        problems = generator.generate_problems(count, category, difficulty)

        if save_to_db:
            service = _get_math_service()
            for prob in problems:
                service.add_problem(prob)

        return jsonify({
            'success': True,
            'data': problems,
            'count': len(problems),
            'saved': save_to_db
        })
    except Exception as e:
        logger.error(f"生成题目失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/math/user/history', methods=['GET'])
@require_math_training_access
def math_user_history():
    """获取用户解题历史"""
    try:
        user_id = session.get('user_id', '')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401

        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        service = _get_math_service()
        result = service.get_user_solutions(user_id, limit, offset)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取解题历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 友好错误页面处理
# ============================================

@app.errorhandler(400)
def handle_400_error(e):
    """处理400错误 - 请求格式错误"""
    logger.warning(f"[错误页面] 400错误: {e}")
    return render_template('400.html'), 400

@app.errorhandler(401)
def handle_401_error(e):
    """处理401错误 - 需要登录"""
    logger.warning(f"[错误页面] 401错误: {e}")
    return render_template('401.html'), 401

@app.errorhandler(403)
def handle_403_error(e):
    """处理403错误 - 权限不足"""
    logger.warning(f"[错误页面] 403错误: {e}")
    return render_template('403.html', 
                          current_role=session.get('role', '未登录'),
                          request_path=request.path), 403

@app.errorhandler(404)
def handle_404_error(e):
    """处理404错误 - 页面未找到"""
    logger.warning(f"[错误页面] 404错误: {request.path}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def handle_500_error(e):
    """处理500错误 - 服务器内部错误"""
    logger.error(f"[错误页面] 500错误: {e}")
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_generic_error(e):
    """处理所有未捕获的异常"""
    logger.error(f"[错误页面] 未捕获异常: {type(e).__name__}: {e}")
    # 如果是API请求，返回JSON错误
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'message': str(e),
            'status': 'error'
        }), 500
    # 否则返回友好的错误页面
    return render_template('error.html',
                          error_code=500,
                          error_title='服务器内部错误',
                          error_message='抱歉，服务器遇到了一些问题，请稍后再试',
                          error_suggestion='如果问题持续存在，请联系管理员或提交反馈',
                          error_id=str(uuid.uuid4()),
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')), 500


if __name__ == '__main__':
    try:
        from app.services.client_monitor_service import init_monitor_tables, create_monitor_employee
        init_monitor_tables()
        create_monitor_employee()
        print("[INFO] 客户端监控服务初始化完成")
    except Exception as e:
        print(f"[WARNING] 客户端监控服务初始化失败: {e}")
    
    try:
        from app.middleware.monitor_middleware import ClientMonitorMiddleware
        monitor_middleware = ClientMonitorMiddleware(app)
        print("[INFO] 客户端监控中间件注册成功")
    except Exception as e:
        print(f"[WARNING] 客户端监控中间件注册失败: {e}")
    
    try:
        from app.services.code_repair_service import init_repair_tables, create_repair_employee
        init_repair_tables()
        create_repair_employee()
        print("[INFO] 代码修复服务初始化完成")
    except Exception as e:
        print(f"[WARNING] 代码修复服务初始化失败: {e}")
    
    try:
        from app.services.port_monitor_service import init_port_monitor
        init_port_monitor()
        print("[INFO] 端口监控服务初始化完成")
    except Exception as e:
        print(f"[WARNING] 端口监控服务初始化失败: {e}")
    
    try:
        from app.services.user_behavior_service import init_behavior_monitor
        init_behavior_monitor()
        print("[INFO] 用户行为监控服务初始化完成")
    except Exception as e:
        print(f"[WARNING] 用户行为监控服务初始化失败: {e}")
    
    try:
        from app.services.system_optimization_service import init_system_optimizer
        init_system_optimizer()
        print("[INFO] 系统优化服务初始化完成")
    except Exception as e:
        print(f"[WARNING] 系统优化服务初始化失败: {e}")
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8888, help='端口号')
    parser.add_argument('--ssl', action='store_true', help='启用SSL/TLS加密')
    parser.add_argument('--ssl-port', type=int, default=8888, help='SSL端口号')
    parser.add_argument('--ssl-cert', type=str, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl', 'mtscos.crt'), help='SSL证书路径')
    parser.add_argument('--ssl-key', type=str, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl', 'mtscos.key'), help='SSL密钥路径')
    args = parser.parse_args()

    print(f"[INFO] 启动MTSCOS AI应用...")
    print(f"[INFO] 数据库路径: {DATABASE_PATH}")

    if args.ssl:
        if os.path.exists(args.ssl_cert) and os.path.exists(args.ssl_key):
            print(f"[INFO] 🔒 启用SSL/TLS加密")
            print(f"[INFO] SSL证书: {args.ssl_cert}")
            print(f"[INFO] SSL密钥: {args.ssl_key}")
            print(f"[INFO] HTTPS服务器运行在 https://0.0.0.0:{args.ssl_port}")
            
            http_port = args.port
            if http_port == args.ssl_port:
                http_port = 8080
            
            import threading
            
            def start_http_redirect_server():
                from flask import Flask, request, redirect
                redirect_app = Flask('redirect_server')
                
                @redirect_app.route('/', defaults={'path': ''})
                @redirect_app.route('/<path:path>')
                def http_to_https_redirect(path):
                    host = request.host.split(':')[0]
                    https_url = f"https://{host}:{args.ssl_port}/{path}"
                    return redirect(https_url, code=301)
                
                print(f"[INFO] HTTP重定向服务器运行在 http://0.0.0.0:{http_port}")
                redirect_app.run(host='::', port=http_port, debug=False, use_reloader=False)
            
            http_thread = threading.Thread(target=start_http_redirect_server, daemon=True)
            http_thread.start()
            
            app.run(host='::', port=args.ssl_port, debug=False, use_reloader=False, ssl_context=(args.ssl_cert, args.ssl_key))
        else:
            print(f"[ERROR] SSL证书或密钥文件不存在")
            print(f"[ERROR] 证书: {args.ssl_cert}")
            print(f"[ERROR] 密钥: {args.ssl_key}")
            print(f"[INFO] 回退到HTTP模式")
            print(f"[INFO] 服务器运行在 http://0.0.0.0:{args.port}")
            app.run(host='::', port=args.port, debug=False, use_reloader=False)
    else:
        print(f"[INFO] 服务器运行在 http://0.0.0.0:{args.port}")
        app.run(host='::', port=args.port, debug=False, use_reloader=False)