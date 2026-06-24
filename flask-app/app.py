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
from contextlib import contextmanager
from datetime import datetime
from flask import jsonify, render_template, request, redirect, session, make_response

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

# 配置CORS支持
CORS(app, resources={r"/*": {"origins": "*"}})

ASSETS_FOLDER = app.static_folder

@app.route('/assets/<path:filename>')
def custom_static(filename):
    return send_from_directory(ASSETS_FOLDER, filename)

# 处理 Font Awesome 字体文件请求（/webfonts/ -> /assets/webfonts/）
@app.route('/webfonts/<path:filename>')
def webfonts(filename):
    webfonts_folder = os.path.join(ASSETS_FOLDER, 'webfonts')
    return send_from_directory(webfonts_folder, filename)

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

# 导入并注册硬件管理路由蓝图
try:
    from app.routes.hardware_routes import hardware_bp
    app.register_blueprint(hardware_bp)
except ImportError:
    logger.warning("[路由] 硬件管理路由蓝图未找到，跳过注册")

# 导入并注册认证API路由蓝图
try:
    from app.api.auth_api import auth_api
    app.register_blueprint(auth_api)
    logger.info("[路由] 认证API路由蓝图注册成功")
except ImportError:
    logger.warning("[路由] 认证API路由蓝图未找到，跳过注册")

# 导入并注册OAuth路由蓝图
try:
    from app.routes.oauth_routes import oauth_bp
    app.register_blueprint(oauth_bp)
except ImportError:
    logger.warning("[路由] OAuth路由蓝图未找到，跳过注册")

# 导入并注册设置路由蓝图
try:
    from app.routes.settings_routes import settings_bp
    app.register_blueprint(settings_bp)
except ImportError:
    logger.warning("[路由] 设置路由蓝图未找到，跳过注册")

# 导入并注册管理员API路由蓝图
try:
    from app.routes.admin_api import admin_api_bp
    app.register_blueprint(admin_api_bp)
except ImportError:
    logger.warning("[路由] 管理员API路由蓝图未找到，跳过注册")

# 导入并注册摸底测试API路由蓝图
try:
    from app.blueprints.placement_test_api import placement_test_api
    app.register_blueprint(placement_test_api)
except ImportError:
    logger.warning("[路由] 摸底测试API路由蓝图未找到，跳过注册")

# 导入并注册配置API路由蓝图
try:
    from app.api.config_api import config_api_bp
    app.register_blueprint(config_api_bp)
except ImportError:
    logger.warning("[路由] 配置API路由蓝图未找到，跳过注册")

# 导入并注册数学公式API路由蓝图
try:
    from app.api.formula_api import formula_api_bp
    app.register_blueprint(formula_api_bp)
except ImportError:
    logger.warning("[路由] 数学公式API路由蓝图未找到，跳过注册")

# 导入并注册监考API路由蓝图
try:
    from app.blueprints.proctor_api import proctor_api
    app.register_blueprint(proctor_api)
except ImportError:
    logger.warning("[路由] 监考API路由蓝图未找到，跳过注册")

# 导入并注册音频API路由蓝图
try:
    from app.blueprints.audio_api import audio_api
    app.register_blueprint(audio_api)
except ImportError:
    logger.warning("[路由] 音频API路由蓝图未找到，跳过注册")

# 导入并注册音频字库API路由蓝图
try:
    from app.blueprints.pronunciation_api import pronunciation_api
    app.register_blueprint(pronunciation_api)
except ImportError:
    logger.warning("[路由] 音频字库API路由蓝图未找到，跳过注册")

# 导入并注册矩阵题库API路由蓝图
try:
    from app.blueprints.matrix_bp import matrix_bp
    app.register_blueprint(matrix_bp)
except ImportError:
    logger.warning("[路由] 矩阵题库API路由蓝图未找到，跳过注册")

# 导入并注册审批API路由蓝图
try:
    from app.blueprints.approval_api import approval_api
    app.register_blueprint(approval_api)
except ImportError:
    logger.warning("[路由] 审批API路由蓝图未找到，跳过注册")

# 导入并注册通知API路由蓝图
try:
    from app.blueprints.notification_api import notification_api
    app.register_blueprint(notification_api)
except ImportError:
    logger.warning("[路由] 通知API路由蓝图未找到，跳过注册")

# 导入并注册学生行为管理API路由蓝图
try:
    from app.routes.student_behavior_api import student_behavior_bp
    app.register_blueprint(student_behavior_bp)
except ImportError:
    logger.warning("[路由] 学生行为管理API路由蓝图未找到，跳过注册")

# 导入并注册超时锁定API路由蓝图
try:
    from app.api.timeout_lock_api import timeout_lock_api
    app.register_blueprint(timeout_lock_api)
except ImportError:
    logger.warning("[路由] 超时锁定API路由蓝图未找到，跳过注册")

# 导入并注册锦标赛API路由蓝图
try:
    from app.routes.tournament_api import tournament_bp
    app.register_blueprint(tournament_bp)
except ImportError:
    logger.warning("[路由] 锦标赛API路由蓝图未找到，跳过注册")

# 导入并注册版本管理API路由蓝图
try:
    from app.api.version_api import version_api
    app.register_blueprint(version_api)
except ImportError:
    logger.warning("[路由] 版本管理API路由蓝图未找到，跳过注册")

# 导入并注册考试判断API路由蓝图
try:
    from app.api.exam_judge_api import exam_judge_api
    app.register_blueprint(exam_judge_api)
except ImportError:
    logger.warning("[路由] 考试判断API路由蓝图未找到，跳过注册")

# 导入并注册高危敏感设置路由蓝图
try:
    from app.routes.sensitive_settings_routes import sensitive_settings_bp
    app.register_blueprint(sensitive_settings_bp)
except ImportError:
    logger.warning("[路由] 高危敏感设置路由蓝图未找到，跳过注册")

# 导入并注册客户端监控API路由蓝图
try:
    from app.routes.monitor_routes import monitor_bp
    app.register_blueprint(monitor_bp)
    logger.info("[路由] 客户端监控API路由蓝图注册成功")
except ImportError:
    logger.warning("[路由] 客户端监控API路由蓝图未找到，跳过注册")

# 导入并注册代码修复API路由蓝图
try:
    from app.routes.code_repair_routes import repair_bp
    app.register_blueprint(repair_bp)
    logger.info("[路由] 代码修复API路由蓝图注册成功")
except ImportError:
    logger.warning("[路由] 代码修复API路由蓝图未找到，跳过注册")

# 导入并注册端口监控API路由蓝图
try:
    from app.routes.port_monitor_routes import port_monitor_bp
    app.register_blueprint(port_monitor_bp)
    logger.info("[路由] 端口监控API路由蓝图注册成功")
except ImportError:
    logger.warning("[路由] 端口监控API路由蓝图未找到，跳过注册")

# 导入并注册用户行为监控API路由蓝图
try:
    from app.routes.user_behavior_routes import behavior_bp
    app.register_blueprint(behavior_bp)
    logger.info("[路由] 用户行为监控API路由蓝图注册成功")
except ImportError:
    logger.warning("[路由] 用户行为监控API路由蓝图未找到，跳过注册")

# 导入并注册系统优化API路由蓝图
try:
    from app.routes.system_optimization_routes import optimizer_bp
    app.register_blueprint(optimizer_bp)
    logger.info("[路由] 系统优化API路由蓝图注册成功")
except ImportError:
    logger.warning("[路由] 系统优化API路由蓝图未找到，跳过注册")

# 导入并注册智能仪表盘API路由蓝图
try:
    from app.routes.intelligent_dashboard_api import intelligent_dashboard_bp
    app.register_blueprint(intelligent_dashboard_bp)
    logger.info("[路由] 智能仪表盘API路由蓝图注册成功")
except ImportError:
    logger.warning("[路由] 智能仪表盘API路由蓝图未找到，跳过注册")

# 导入并注册设置页面数据API路由蓝图
try:
    from app.api.settings_data_api import settings_data_bp
    app.register_blueprint(settings_data_bp)
    logger.info("[路由] 设置页面数据API路由蓝图注册成功")
except ImportError:
    logger.warning("[路由] 设置页面数据API路由蓝图未找到，跳过注册")

# 导入并注册路由约束引擎API
try:
    from app.api.route_constraint_api import constraint_api_bp
    app.register_blueprint(constraint_api_bp)
    logger.info("[路由] 路由约束引擎API注册成功")
except ImportError:
    logger.warning("[路由] 路由约束引擎API未找到，跳过注册")

# 导入并注册角色路由跳转API
try:
    from app.utils.role_router import role_router_bp, create_role_routes
    app.register_blueprint(role_router_bp)
    app = create_role_routes(app)
    logger.info("[路由] 角色路由跳转API注册成功")
except ImportError:
    logger.warning("[路由] 角色路由跳转API未找到，跳过注册")

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

# 初始化权限管理器
init_permission_manager(DATABASE_PATH)

# 初始化会话管理器(超时时间30分钟)
init_session_manager(DATABASE_PATH, timeout_minutes=30)

# 初始化规则管理器(深度绑定系统规则数据库)
init_rule_manager(DATABASE_PATH)

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
        'version': "1.4.0",
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
                        except:
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
                        except:
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

# Vite客户端请求处理(开发环境)
@app.route('/@vite/client')
def vite_client():
    return '', 204

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

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
    except:
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
        'student': '/exam/exam_center',
        'student_vip': '/exam/exam_center',
        
        # 教师角色 - 进入教师管理中心
        'teacher': '/teacher/dashboard',
        'teacher_admin': '/teacher/dashboard',
        
        # 管理员角色 - 进入管理中心
        'admin': '/admin_center',
        'system_admin': '/admin_center',
        
        # 超级管理员角色 - 进入超级管理面板
        'super_admin': '/super_admin_dashboard',
        
        # 硬件管理员角色
        'hardware_admin': '/hardware/dashboard',
        
        # 考试专家角色 - 进入考试系统
        'exam_expert': '/exam/exam_center',
        
        # 默认角色 - 进入考试系统(普通用户默认进入考试系统)
        'user': '/exam/exam_center',
        'guest': '/',
    }
    
    # 如果角色不在映射中,返回考试系统作为默认
    return role_redirect_map.get(role, '/exam/exam_center')


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
                except:
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
        except:
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


# 超级管理员仪表板 - 需要超级管理员权限
@app.route('/super_admin_dashboard')
@require_super_admin
def super_admin_dashboard():
    return render_template('super_admin_dashboard.html')

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

# 系统状态
@app.route('/api/system/status')
def system_status():
    return jsonify({'status': 'running', 'version': "1.3.0", 'timestamp': datetime.now().isoformat()})

# 用户信息API
@app.route('/api/user/<username>')
def get_user(username):
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
    user_id = session.get('user_id')
    
    # 未登录用户，跳转到登录页
    if not user_id:
        return redirect('/auth/login')
    
    # 获取用户信息
    user_info = get_user_info(user_id)
    if not user_info:
        return redirect('/auth/login')
    
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
            except:
                pass
            
            # 学习积分
            try:
                cursor.execute('SELECT points FROM user_points WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                stats['points'] = result[0] if result else 100
            except:
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

# 获取考试列表API
@app.route('/api/exams', methods=['GET'])
def get_exams():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM exams WHERE status = "active" ORDER BY title')
        exams = cursor.fetchall()
        
        exam_list = []
        for exam in exams:
            exam_list.append({
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
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
        exam = cursor.fetchone()
    
    if not exam:
        return jsonify({'success': False, 'message': '考试不存在'}), 404
    
    language = exam['language'] if exam['language'] else 'japanese'
    difficulty = exam['level'] if exam['level'] else 'intermediate'
    exam_type = 'standard'
    total_questions = exam['question_count'] if exam['question_count'] else 10
    voice_type = 'standard'
    
    questions = generate_test_questions(language, difficulty, total_questions)
    
    return jsonify({'success': True, 'data': questions})

# 获取单个考试详情API
@app.route('/api/exams/<exam_id>', methods=['GET'])
def get_exam(exam_id):
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
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO exams 
        (id, title, description, duration, question_count, total_points, passing_score, status, language, level, shuffle_questions, shuffle_options, allow_retake, max_retakes, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        int(time.time())
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
        except:
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
    
    return render_template('placement_test.html', 
                           username=username, 
                           role=role,
                           user_id=user_id,
                           has_completed=has_completed,
                           current_level=current_level)

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
                except:
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
    parser.add_argument('--ssl-port', type=int, default=8443, help='SSL端口号')
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
            print(f"[INFO] 服务器运行在 https://0.0.0.0:{args.ssl_port}")
            app.run(host='0.0.0.0', port=args.ssl_port, debug=False, use_reloader=False, ssl_context=(args.ssl_cert, args.ssl_key))
        else:
            print(f"[ERROR] SSL证书或密钥文件不存在")
            print(f"[ERROR] 证书: {args.ssl_cert}")
            print(f"[ERROR] 密钥: {args.ssl_key}")
            print(f"[INFO] 回退到HTTP模式")
            print(f"[INFO] 服务器运行在 http://0.0.0.0:{args.port}")
            app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)
    else:
        print(f"[INFO] 服务器运行在 http://0.0.0.0:{args.port}")
        app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)