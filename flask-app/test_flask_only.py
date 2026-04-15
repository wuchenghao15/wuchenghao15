#!/usr/bin/env python3
"""
只测试Flask应用核心功能的脚本，包括AI员工系统集成
"""

import os
import sys
import sqlite3
import hashlib
import base64
import uuid

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Flask和相关模块
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify

# 导入AI员工系统
from ai_employee_system import get_ai_route_system

# 导入路由管理系统
from route_manager import get_route_manager

# 导入OTA服务器系统
from ota_system import get_ota_server

# 创建Flask应用
app = Flask(__name__)

# 配置Flask应用
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['DATABASE'] = 'app.db'

# 配置会话
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境下使用False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# 设置模板目录
app.template_folder = 'templates'

# 设置静态文件目录
app.static_folder = 'static'

# 统一语言测试系统路由
@app.route('/test-system')
def test_system():
    """统一语言测试系统主页"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_role = session.get('role', '')
    # 只有学生可以参加考试
    if user_role != 'student':
        flash('只有学生可以参加语言测试', 'error')
        return redirect(url_for('dashboard'))
    
    # 检查用户是否需要进行等级评估测试
    user_id = session.get('user_id')
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 获取用户的语言等级
        cursor.execute('SELECT japanese_level, english_level FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            japanese_level, english_level = user
            # 如果日语和英语等级都为null，则判定为初次进入，跳转到等级评估测试
            if japanese_level is None and english_level is None:
                flash('欢迎初次使用测试系统，请先进行等级评估测试以确定您的语言水平', 'info')
                return redirect(url_for('level_assessment'))
    except Exception as e:
        print(f"查询用户等级时发生错误: {e}")
    
    return render_template('test_system.html', logged_in=True, username=session.get('username'))

# 等级评估测试路由
@app.route('/level-assessment')
def level_assessment():
    """等级评估测试页面"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_role = session.get('role', '')
    if user_role != 'student':
        flash('只有学生可以参加等级评估测试', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('level_assessment.html', logged_in=True, username=session.get('username'))

# 日语测试页面路由
@app.route('/test-system/japanese')
def japanese_test():
    """日语测试页面"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_role = session.get('role', '')
    # 只有学生可以参加考试
    if user_role != 'student':
        flash('只有学生可以参加语言测试', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('japanese_test.html', logged_in=True, username=session.get('username'))

# 英语测试页面路由
@app.route('/test-system/english')
def english_test():
    """英语测试页面"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_role = session.get('role', '')
    # 只有学生可以参加考试
    if user_role != 'student':
        flash('只有学生可以参加语言测试', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('english_test.html', logged_in=True, username=session.get('username'))

# 双语测试页面路由
@app.route('/test-system/bilingual')
def bilingual_test():
    """双语测试页面"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_role = session.get('role', '')
    # 只有学生可以参加考试
    if user_role != 'student':
        flash('只有学生可以参加语言测试', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('bilingual_test.html', logged_in=True, username=session.get('username'))

# 旧语言测试路由（保留用于兼容性）
@app.route('/language-test')
def language_test():
    """语言测试系统页面"""
    # 重定向到统一测试系统主页
    return redirect(url_for('test_system'))

# AI测试内容生成API
@app.route('/api/generate-test-content', methods=['POST'])
def generate_test_content():
    """使用AI员工生成测试内容"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 获取请求参数
    language = request.json.get('language', 'japanese')
    test_type = request.json.get('test_type', 'assessment')
    user_id = session.get('user_id')
    
    # 获取AI路由系统实例
    ai_route_system = get_ai_route_system()
    
    # 准备请求数据
    request_data = {
        "type": "generate_test_content",
        "data": {
            "language": language,
            "user_id": user_id,
            "test_type": test_type
        }
    }
    
    # 找到测试系统AI员工
    test_system_employee = None
    for employee in ai_route_system.ai_employees.values():
        if employee.type == "test_system":
            test_system_employee = employee
            break
    
    if not test_system_employee:
        return jsonify({'success': False, 'message': '测试系统AI员工未找到'}), 500
    
    # 调用AI员工生成测试内容
    result = test_system_employee.process(request_data)
    
    return jsonify(result), 200 if result.get('success') else 500

# AI测试页面配置API
@app.route('/api/test-page-config/<language>', methods=['GET'])
def get_test_page_config(language):
    """获取测试页面配置"""
    # 获取AI路由系统实例
    ai_route_system = get_ai_route_system()
    
    # 找到测试系统AI员工
    test_system_employee = None
    for employee in ai_route_system.ai_employees.values():
        if employee.type == "test_system":
            test_system_employee = employee
            break
    
    if not test_system_employee:
        return jsonify({'success': False, 'message': '测试系统AI员工未找到'}), 500
    
    # 准备请求数据
    request_data = {
        "type": "get_test_page_config",
        "data": {
            "language": language
        }
    }
    
    # 调用AI员工获取页面配置
    result = test_system_employee.process(request_data)
    
    return jsonify(result), 200 if result.get('success') else 500

# AI测试页面优化API
@app.route('/api/optimize-test-page', methods=['POST'])
def optimize_test_page():
    """优化测试页面"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 获取请求参数
    language = request.json.get('language', 'japanese')
    page_type = request.json.get('page_type', 'assessment')
    user_feedback = request.json.get('user_feedback', {})
    test_results = request.json.get('test_results', {})
    
    # 获取AI路由系统实例
    ai_route_system = get_ai_route_system()
    
    # 找到测试系统AI员工
    test_system_employee = None
    for employee in ai_route_system.ai_employees.values():
        if employee.type == "test_system":
            test_system_employee = employee
            break
    
    if not test_system_employee:
        return jsonify({'success': False, 'message': '测试系统AI员工未找到'}), 500
    
    # 准备请求数据
    request_data = {
        "type": "optimize_test_page",
        "data": {
            "language": language,
            "page_type": page_type,
            "user_feedback": user_feedback,
            "test_results": test_results
        }
    }
    
    # 调用AI员工优化页面
    result = test_system_employee.process(request_data)
    
    return jsonify(result), 200 if result.get('success') else 500

# 测试结果提交API
@app.route('/api/submit-test-results', methods=['POST'])
def submit_test_results():
    """提交测试结果"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 获取请求参数
    test_id = request.json.get('test_id')
    test_results = request.json.get('test_results', {})
    test_type = request.json.get('test_type', 'assessment')
    language = request.json.get('language', 'japanese')
    user_id = session.get('user_id')
    
    # 获取AI路由系统实例
    ai_route_system = get_ai_route_system()
    
    # 找到测试系统AI员工
    test_system_employee = None
    for employee in ai_route_system.ai_employees.values():
        if employee.type == "test_system":
            test_system_employee = employee
            break
    
    if not test_system_employee:
        return jsonify({'success': False, 'message': '测试系统AI员工未找到'}), 500
    
    # 准备请求数据
    request_data = {
        "type": "analyze_test_results",
        "data": {
            "test_id": test_id,
            "user_id": user_id,
            "test_results": test_results,
            "test_type": test_type,
            "language": language
        }
    }
    
    # 调用AI员工分析测试结果
    result = test_system_employee.process(request_data)
    
    return jsonify(result), 200 if result.get('success') else 500

# AI生成测试页面路由
@app.route('/ai-generated-test')
def ai_generated_test():
    """AI生成的测试页面"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # 获取测试ID
    test_id = request.args.get('test_id')
    
    # 从localStorage获取测试内容
    # 注意：这里在实际应用中应该从服务器端获取测试内容，而不是依赖localStorage
    # 这里只是为了演示方便
    return render_template('ai_generated_test.html', 
                         logged_in=True, 
                         username=session.get('username'),
                         test_id=test_id)

# 导入json模块

@app.route('/dashboard')
def dashboard():
    """系统仪表盘页面"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_role = session.get('role', '')
    return render_template('dashboard.html', logged_in=True, username=session.get('username'), role=user_role)

# 简单路由
@app.route('/')
def index():
    # 清除所有flash消息，防止在index页面显示登录错误
    from flask import get_flashed_messages
    # 调用get_flashed_messages()来清除所有消息
    messages = get_flashed_messages(with_categories=True)
    # 检查用户是否已登录
    if session.get('logged_in'):
        user_role = session.get('role', '')
        # 学生直接跳转统一语言测试系统
        if user_role == 'student':
            return redirect(url_for('test_system'))
        # 管理员、超级管理员、硬件管理员跳转仪表盘
        elif user_role in ['admin', 'super_admin', 'hardware_admin']:
            return redirect(url_for('dashboard'))
        # 普通用户跳转仪表盘
        else:
            return render_template('index.html', logged_in=True, username=session.get('username'))
    return render_template('index.html', logged_in=False)

@app.route('/health')
def health():
    return "OK", 200

@app.route('/version')
def version():
    return {"VERSION": "3.0.0"}, 200

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # 获取AI路由系统实例
        ai_route_system = get_ai_route_system()
        
        # 准备请求数据
        request_data = {
            "type": "login",
            "data": {
                "username": username,
                "password": password,
                "action": "login"
            }
        }
        
        # 使用AI员工系统处理请求
        result = ai_route_system.process_request("/auth/login", request_data)
        
        # 获取验证结果
        validation_result = result.get("validation_result")
        
        # 如果验证失败，返回登录页面并显示错误信息
        if not validation_result or not validation_result["success"]:
            error_msg = validation_result.get("message", "用户名或密码格式不正确") if validation_result else "验证失败"
            flash(error_msg, 'error')
            return render_template('index.html')
        
        # 验证成功，继续进行数据库验证
        try:
            # 连接数据库
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            # 获取用户信息
            cursor.execute('SELECT id, username, email, password, role, is_active FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()
            
            # 硬编码登录逻辑，方便测试
            if username == 'admin' and password == 'password':
                # 登录成功，设置会话
                session['user_id'] = 1
                session['username'] = 'admin'
                session['email'] = 'admin@example.com'
                session['role'] = 'admin'
                session['logged_in'] = True
                session['session_id'] = str(uuid.uuid4())
                
                flash('登录成功', 'success')
                
                # 更新AI员工系统的路由请求，包含用户角色
                request_data['user_role'] = 'admin'
            elif user:
                user_id, db_username, email, hashed_password, role, is_active = user
                
                # 密码验证逻辑
                password_valid = False
                
                try:
                    # 尝试直接比较密码
                    if password == hashed_password:
                        password_valid = True
                    else:
                        # 尝试base64格式验证
                        decoded = base64.b64decode(hashed_password)
                        if len(decoded) == 64:  # 32字节salt + 32字节hash
                            salt = decoded[:32]
                            stored_hash = decoded[32:]
                            hashed = hashlib.pbkdf2_hmac(
                                'sha256',
                                password.encode('utf-8'),
                                salt,
                                100000
                            )
                            if hashed == stored_hash:
                                password_valid = True
                        else:
                            # 尝试hex格式验证
                            if len(hashed_password) == 96:
                                salt_hex = hashed_password[:32]
                                hash_hex = hashed_password[32:96]
                                salt = bytes.fromhex(salt_hex)
                                stored_hash = bytes.fromhex(hash_hex)
                                hashed = hashlib.pbkdf2_hmac(
                                    'sha256',
                                    password.encode('utf-8'),
                                    salt,
                                    100000
                                )
                                if hashed == stored_hash:
                                    password_valid = True
                except Exception as e:
                    print(f"密码验证错误: {e}")
                
                if password_valid:
                    # 登录成功，设置会话
                    session['user_id'] = user_id
                    session['username'] = db_username
                    session['email'] = email
                    session['role'] = role
                    session['logged_in'] = True
                    session['session_id'] = str(uuid.uuid4())
                    
                    flash('登录成功', 'success')
                    
                    # 更新AI员工系统的路由请求，包含用户角色
                    request_data['user_role'] = role
                else:
                    # 密码错误，更新验证结果为失败
                    result["validation_result"]["success"] = False
                    result["validation_result"]["message"] = "用户名或密码不正确"
                    flash('用户名或密码不正确', 'error')
                    
                    # 重新处理路由决策
                    routing_request = {
                        "type": "determine",
                        "data": {
                            "action": "login",
                            "result": "failure",
                            "request_path": "/auth/login",
                            "user_role": "guest"
                        }
                    }
                    ai_routing_employee = list(ai_route_system.ai_employees.values())[1]  # 假设第二个是路由AI
                    result["routing_result"] = ai_routing_employee.process(routing_request)
            else:
                # 用户不存在，更新验证结果为失败
                result["validation_result"]["success"] = False
                result["validation_result"]["message"] = "用户名或密码不正确"
                flash('用户名或密码不正确', 'error')
                
                # 重新处理路由决策
                routing_request = {
                    "type": "determine",
                    "data": {
                        "action": "login",
                        "result": "failure",
                        "request_path": "/auth/login",
                        "user_role": "guest"
                    }
                }
                ai_routing_employee = list(ai_route_system.ai_employees.values())[1]  # 假设第二个是路由AI
                result["routing_result"] = ai_routing_employee.process(routing_request)
        except Exception as e:
            flash('登录时发生错误，请稍后重试', 'error')
            print(f"登录错误: {e}")
            
            # 错误处理，更新路由决策
            routing_request = {
                "type": "determine",
                "data": {
                    "action": "login",
                    "result": "failure",
                    "request_path": "/auth/login",
                    "user_role": "guest"
                }
            }
            ai_routing_employee = list(ai_route_system.ai_employees.values())[1]  # 假设第二个是路由AI
            result["routing_result"] = ai_routing_employee.process(routing_request)
        
        # 获取路由结果
        routing_result = result.get("routing_result")
        
        # 根据路由结果进行跳转
        if routing_result and routing_result["success"]:
            redirect_to = routing_result.get("redirect_to", "/")
            return redirect(redirect_to)
        
        # 默认返回登录页面
        return render_template('index.html')
    
    # GET请求，渲染登录页面
    return render_template('index.html')

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    return render_template('index.html')

@app.route('/auth/logout', methods=['GET', 'POST'])
def logout():
    # 清除会话
    session.clear()
    # 重定向到登录页面
    flash('您已成功退出登录', 'success')
    return redirect(url_for('index'))

@app.route('/api/routes', methods=['GET'])
def get_routes():
    """获取所有路由规则"""
    # 检查用户是否登录
    if not session.get('logged_in'):
        return {
            'success': False,
            'message': '请先登录'
        }, 401
    
    # 检查用户角色，只有管理员、超级管理员、硬件管理员可以访问
    user_role = session.get('role', '')
    if user_role not in ['admin', 'super_admin', 'hardware_admin']:
        return {
            'success': False,
            'message': '权限不足'
        }, 403
    
    route_manager = get_route_manager()
    routes = route_manager.get_all_routes()
    return {
        'success': True,
        'total_routes': len(routes),
        'routes': routes
    }, 200

@app.route('/api/routes/sync', methods=['POST'])
def sync_routes():
    """同步路由规则到数据库"""
    # 检查用户是否登录
    if not session.get('logged_in'):
        return {
            'success': False,
            'message': '请先登录'
        }, 401
    
    # 检查用户角色，只有管理员、超级管理员、硬件管理员可以访问
    user_role = session.get('role', '')
    if user_role not in ['admin', 'super_admin', 'hardware_admin']:
        return {
            'success': False,
            'message': '权限不足'
        }, 403
    
    route_manager = get_route_manager(app)
    scanned_routes, saved_routes = route_manager.sync_routes()
    return {
        'success': True,
        'scanned_routes': scanned_routes,
        'saved_routes': saved_routes
    }, 200

@app.route('/api/routes/add', methods=['POST'])
def add_route():
    """添加新的路由规则"""
    # 检查用户是否登录
    if not session.get('logged_in'):
        return {
            'success': False,
            'message': '请先登录'
        }, 401
    
    # 检查用户角色，只有管理员、超级管理员、硬件管理员可以访问
    user_role = session.get('role', '')
    if user_role not in ['admin', 'super_admin', 'hardware_admin']:
        return {
            'success': False,
            'message': '权限不足'
        }, 403
    
    data = request.get_json()
    if not data or 'route_path' not in data or 'handler_name' not in data:
        return {
            'success': False,
            'message': '缺少必要参数'
        }, 400
    
    route_manager = get_route_manager()
    success = route_manager.add_route_rule(
        route_path=data['route_path'],
        handler_name=data['handler_name'],
        methods=data.get('methods', ['GET']),
        validation_employee_id=data.get('validation_employee_id'),
        routing_employee_id=data.get('routing_employee_id'),
        requires_auth=data.get('requires_auth', 0),
        priority=data.get('priority', 0)
    )
    
    return {
        'success': success,
        'message': '路由添加成功' if success else '路由已存在或添加失败'
    }, 200 if success else 400

# OTA API 路由

# 获取最新固件版本
@app.route('/api/ota/latest-firmware', methods=['GET'])
def get_latest_firmware():
    """获取最新固件版本"""
    device_type = request.args.get('type', 'ai_employee')
    device_subtype = request.args.get('subtype')
    
    ota_server = get_ota_server()
    result = ota_server.get_latest_firmware(device_type, device_subtype)
    
    return jsonify(result), 200 if result.get('success') else 500

# 添加新固件版本
@app.route('/api/ota/add-firmware', methods=['POST'])
def add_firmware():
    """添加新固件版本"""
    # 检查用户是否登录
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查用户角色，只有管理员可以添加固件
    user_role = session.get('role', '')
    if user_role not in ['admin', 'super_admin']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取固件数据
    firmware_data = request.get_json()
    if not firmware_data or 'version' not in firmware_data or 'type' not in firmware_data or 'file_path' not in firmware_data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    ota_server = get_ota_server()
    result = ota_server.add_firmware_version(firmware_data)
    
    return jsonify(result), 200 if result.get('success') else 500

# 开始设备更新
@app.route('/api/ota/start-update', methods=['POST'])
def start_device_update():
    """开始设备更新"""
    device_data = request.get_json()
    if not device_data or 'device_id' not in device_data or 'device_type' not in device_data or 'current_version' not in device_data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    ota_server = get_ota_server()
    result = ota_server.start_device_update(device_data)
    
    return jsonify(result), 200 if result.get('success') else 500

# 更新设备更新状态
@app.route('/api/ota/update-status', methods=['POST'])
def update_device_status():
    """更新设备更新状态"""
    update_data = request.get_json()
    if not update_data or 'update_id' not in update_data or 'update_status' not in update_data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    ota_server = get_ota_server()
    result = ota_server.update_device_status(update_data)
    
    return jsonify(result), 200 if result.get('success') else 500

# 添加更新日志
@app.route('/api/ota/add-log', methods=['POST'])
def add_update_log():
    """添加更新日志"""
    log_data = request.get_json()
    if not log_data or 'update_id' not in log_data or 'log_message' not in log_data or 'log_level' not in log_data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    ota_server = get_ota_server()
    result = ota_server.add_update_log(log_data)
    
    return jsonify(result), 200 if result.get('success') else 500

# 获取设备更新历史
@app.route('/api/ota/update-history/<device_id>', methods=['GET'])
def get_device_update_history(device_id):
    """获取设备更新历史"""
    limit = request.args.get('limit', 10, type=int)
    
    ota_server = get_ota_server()
    result = ota_server.get_device_update_history(device_id, limit)
    
    return jsonify(result), 200 if result.get('success') else 500

# 获取更新日志
@app.route('/api/ota/update-logs/<int:update_id>', methods=['GET'])
def get_update_logs(update_id):
    """获取更新日志"""
    limit = request.args.get('limit', 50, type=int)
    
    ota_server = get_ota_server()
    result = ota_server.get_update_logs(update_id, limit)
    
    return jsonify(result), 200 if result.get('success') else 500

if __name__ == '__main__':
    PORT = 8890
    print(f"Starting Flask app on http://0.0.0.0:{PORT}...")
    
    # 初始化路由管理器并同步路由规则到数据库
    print("\n[路由管理] 初始化路由管理器...")
    route_manager = get_route_manager(app)
    print("[路由管理] 同步路由规则到数据库...")
    scanned_routes, saved_routes = route_manager.sync_routes()
    print(f"[路由管理] 扫描到 {scanned_routes} 条路由，保存了 {saved_routes} 条到数据库")
    
    # 绑定AI员工到路由
    ai_route_system = get_ai_route_system()
    # 获取AI员工列表
    ai_employees = list(ai_route_system.ai_employees.values())
    if len(ai_employees) >= 2:
        validation_employee_id = ai_employees[0].employee_id
        routing_employee_id = ai_employees[1].employee_id
        
        # 绑定AI员工到认证路由
        route_manager.bind_ai_employees("/auth/login", validation_employee_id, routing_employee_id)
        route_manager.bind_ai_employees("/auth/register", validation_employee_id, routing_employee_id)
        print(f"[路由管理] 已绑定AI员工到认证路由")
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=True)
    except KeyboardInterrupt:
        print("Flask app stopped.")
    except Exception as e:
        print(f"Error starting Flask app: {str(e)}")
        import traceback
        traceback.print_exc()
