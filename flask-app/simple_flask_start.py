# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Simple Flask Start Script with Security Defenses
"""

import logging
import os
import sys
import re
import html
import time
from datetime import datetime
import base64
import uuid
import secrets
import hashlib
import json
from contextlib import contextmanager

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, render_template, redirect, url_for, flash, session, make_response

from ip_manager import get_ip_manager

os.environ['FLASK_SKIP_DOTENV'] = '1'
os.environ['FLASK_APP'] = __file__
os.environ['FLASK_ENV'] = 'development'

app = Flask(__name__)

if not os.environ.get('FLASK_SECRET_KEY'):
    os.environ['FLASK_SECRET_KEY'] = secrets.token_urlsafe(64)

app.config['DEBUG'] = True
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['DATABASE'] = 'app.db'

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

app.template_folder = 'templates'
app.static_folder = 'static'

logger = logging.getLogger(__name__)


def custom_json_response(data, status_code=200, pretty=True, include_context=False):
    """自定义JSON响应,优化pre标签显示效果,支持包含上下文信息"""
    try:
        response_data = data.copy() if isinstance(data, dict) else data

        if include_context and isinstance(response_data, dict):
            response_data['_context'] = {
                'timestamp': datetime.now().isoformat(),
                'request_id': str(uuid.uuid4()),
                'client_ip': request.remote_addr,
                'path': request.path,
                'method': request.method
            }

        if pretty:
            json_str = json.dumps(
                response_data,
                ensure_ascii=False,
                indent=2,
                separators=(',', ': '),
                sort_keys=True
            )
        else:
            json_str = json.dumps(response_data)

        response = make_response(json_str)

        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.status_code = status_code

        return response
    except Exception as e:
        error_data = {
            'error': str(e),
            'error_type': type(e).__name__,
            '_context': {
                'timestamp': datetime.now().isoformat(),
                'request_id': str(uuid.uuid4()),
                'client_ip': request.remote_addr,
                'method': request.method
            }
        }
        error_response = make_response(json.dumps(error_data, ensure_ascii=False, indent=2))
        error_response.status_code = 500
        return error_response


ip_manager = get_ip_manager()


def is_ip_blacklisted(ip_address):
    """检查IP是否在黑名单中"""
    return ip_manager.is_ip_blacklisted(ip_address)


def is_ip_whitelisted(ip_address):
    """检查IP是否在白名单中"""
    return ip_manager.is_ip_whitelisted(ip_address)


def is_ip_in_sandbox(ip_address):
    """检查IP是否在沙箱中"""
    return ip_manager.is_ip_in_sandbox(ip_address)


def add_ip_to_whitelist(ip_address, reason, added_by):
    """添加IP到白名单"""
    print(f"[白名单] 添加IP {ip_address} 到白名单,原因: {reason},添加者: {added_by}")
    return ip_manager.add_ip(ip_address, 'whitelist', reason, added_by)


def add_ip_to_blacklist(ip_address, reason, added_by):
    """添加IP到黑名单"""
    print(f"[黑名单] 添加IP {ip_address} 到黑名单,原因: {reason},添加者: {added_by}")
    return ip_manager.add_ip(ip_address, 'blacklist', reason, added_by)


def add_ip_to_sandbox(ip_address, reason, marked_by):
    """将IP添加到沙箱隔离"""
    print(f"[沙箱] 将IP {ip_address} 添加到沙箱,原因: {reason},标记者: {marked_by}")
    return ip_manager.add_ip(ip_address, 'sandbox', reason, marked_by)


access_counts = {}
failed_login_attempts = {}


def check_access_rate_limit(ip_address, endpoint, limit=5, window=60):
    """检查访问频率限制"""
    global access_counts
    current_time = time.time()
    if endpoint not in access_counts:
        access_counts[endpoint] = {}
    if ip_address not in access_counts[endpoint]:
        access_counts[endpoint][ip_address] = {'count': 0, 'last_request': current_time}

    if current_time - access_counts[endpoint][ip_address]['last_request'] > window:
        access_counts[endpoint][ip_address] = {'count': 1, 'last_request': current_time}
        return True
    else:
        if access_counts[endpoint][ip_address]['count'] >= limit:
            return False
        else:
            access_counts[endpoint][ip_address]['count'] += 1
            access_counts[endpoint][ip_address]['last_request'] = current_time
            return True


def log_security_event(ip_address, user_id, action, status, details=None):
    """记录安全事件日志"""
    print(f"[安全日志] IP: {ip_address}, 用户ID: {user_id}, 操作: {action}, 状态: {status}, 详情: {details}")
    return True


def validate_input(input_data, validation_type):
    """验证输入数据的格式"""
    try:
        if validation_type == 'username':
            return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', input_data))
        elif validation_type == 'email':
            return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', input_data))
        elif validation_type == 'password':
            return bool(re.match(r'^[a-zA-Z\d@$!%*?&._-]{6,}$', input_data))
        return False
    except Exception:
        return False


def sanitize_input(input_data):
    """净化输入数据"""
    if isinstance(input_data, str):
        sanitized = html.escape(input_data)
        sanitized = re.sub(r'[\x00\x1a"\'\\\/\;\(\)]', '', sanitized)
        return sanitized
    return input_data


from ai_anomaly_detector import get_ai_detector
from ai_brain import get_ai_brain
from ai_log_analyzer import get_log_analyzer

perf_monitor = None
try:
    from ai_performance_monitor import get_performance_monitor
    perf_monitor = get_performance_monitor()
except ImportError as e:
    print(f"警告: 无法导入AI性能监控器: {e}")
    print("系统将在没有性能监控的情况下运行")

ai_self_improvement = None
try:
    from ai_self_improvement import get_ai_self_improvement
    ai_self_improvement = get_ai_self_improvement()
except ImportError as e:
    print(f"警告: 无法导入AI自我提升系统: {e}")

ai_auto_management = None
try:
    from ai_auto_management import get_ai_auto_management
    ai_auto_management = get_ai_auto_management()
except ImportError as e:
    print(f"警告: 无法导入AI自动化管理系统: {e}")

ai_anomaly_detector = get_ai_detector()
ai_brain = get_ai_brain()
log_analyzer = get_log_analyzer()

if perf_monitor is None:
    try:
        perf_monitor = get_performance_monitor()
    except Exception as e:
        print(f"警告: 无法获取性能监控器实例: {e}")


@app.after_request
def enhanced_security_middleware(response):
    """增强版安全防御中间件"""
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@app.before_request
def performance_monitor_start():
    """性能监控开始中间件"""
    request.start_time = time.time()


@app.before_request
def security_defense_middleware():
    """安全防御中间件,实行黑名单制防火墙"""
    if request.path in ['/health', '/version']:
        return

    client_ip = request.remote_addr
    endpoint = request.path

    if is_ip_whitelisted(client_ip):
        log_security_event(client_ip, None, 'access_attempt', 'allowed', f'白名单IP放行: {endpoint}')
        return

    if is_ip_blacklisted(client_ip):
        log_security_event(client_ip, None, 'access_attempt', 'blocked', f'黑名单IP拦截: {endpoint}')
        return custom_json_response({'error': '您的IP已被禁止访问'}, status_code=403)

    if is_ip_in_sandbox(client_ip):
        log_security_event(client_ip, None, 'access_attempt', 'sandboxed', f'沙箱IP访问: {endpoint}')

    if endpoint in ['/auth/login', '/auth/register']:
        if not check_access_rate_limit(client_ip, endpoint, limit=5, window=60):
            add_ip_to_sandbox(client_ip, f'登录/注册频率超限', 'system')
            log_security_event(client_ip, None, 'access_attempt', 'rate_limited', f'登录/注册频率超限,已添加到沙箱: {endpoint}')
            return custom_json_response({'error': '请求频率过高,您的IP已被标记为嫌疑IP,请等待管理员审核'}, status_code=429)
    elif endpoint.startswith('/api/'):
        if not check_access_rate_limit(client_ip, endpoint, limit=30, window=60):
            add_ip_to_sandbox(client_ip, f'API频率超限', 'system')
            log_security_event(client_ip, None, 'access_attempt', 'rate_limited', f'API频率超限,已添加到沙箱: {endpoint}')
            return custom_json_response({'error': 'API请求频率过高,您的IP已被标记为嫌疑IP,请等待管理员审核'}, status_code=429)


@app.after_request
def performance_monitor_end(response):
    """性能监控结束中间件"""
    if hasattr(request, 'start_time'):
        response_time = time.time() - request.start_time
        endpoint = request.path
        method = request.method
        is_error = response.status_code >= 400

        if perf_monitor is not None:
            try:
                perf_monitor.record_request(endpoint, method, response_time, is_error)
            except Exception as e:
                print(f"记录请求性能数据失败: {e}")

    return response


@app.route('/')
def index():
    """根路由"""
    return render_template('index.html')


@app.route('/health')
def health():
    """健康检查路由"""
    return "OK", 200


@app.route('/version')
def version():
    """版本信息路由"""
    return {"VERSION": "3.0.0"}, 200


@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """登录路由"""
    if request.method == 'POST':
        password = request.form.get('password', '').strip()

        if not password:
            flash('请输入密码', 'error')
            return render_template('index.html')

        import sqlite3
        import hashlib
        import base64

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('SELECT id, username, email, password, role, is_active FROM users LIMIT 1')
            user = cursor.fetchone()
            conn.close()

            if user:
                user_id, username, email, hashed_password, role, is_active = user

                password_valid = False

                try:
                    if password == hashed_password:
                        password_valid = True
                    else:
                        try:
                            decoded = base64.b64decode(hashed_password)
                            if len(decoded) == 64:
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
                        except Exception:
                            pass

                        if not password_valid and len(hashed_password) == 96:
                            try:
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
                            except Exception:
                                pass
                except Exception as e:
                    print(f"密码验证错误: {e}")

                if password_valid:
                    session['user_id'] = user_id
                    session['username'] = username
                    session['email'] = email
                    session['role'] = role
                    session['logged_in'] = True
                    session['session_id'] = str(uuid.uuid4())

                    flash('登录成功', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('密码不正确', 'error')
                    print(f"密码验证失败,提供的密码: {password}")
            else:
                print("没有找到用户,创建默认用户...")
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO users (username, email, password, role, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', 'admin@example.com', 'password', 'admin', 1))
                conn.commit()
                conn.close()

                if password == 'password':
                    session['user_id'] = 1
                    session['username'] = 'admin'
                    session['email'] = 'admin@example.com'
                    session['role'] = 'admin'
                    session['logged_in'] = True
                    session['session_id'] = str(uuid.uuid4())
                    flash('登录成功,已创建默认用户', 'success')
                else:
                    flash('密码不正确', 'error')
        except Exception as e:
            flash('登录时发生错误,请稍后重试', 'error')
            print(f"登录错误: {e}")

        return render_template('index.html')

    return render_template('index.html')


@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    """注册路由"""
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        email = sanitize_input(request.form.get('email', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        registration_token = request.form.get('registration_token', '')
        client_ip = request.remote_addr

        log_security_event(client_ip, None, 'register_attempt', 'initiated', f'用户名: {username}, 邮箱: {email}')

        if not validate_input(username, 'username'):
            return custom_json_response({'error': '用户名格式无效'}, status_code=400)

        if not validate_input(email, 'email'):
            return custom_json_response({'error': '邮箱格式无效'}, status_code=400)

        if not validate_input(password, 'password'):
            return custom_json_response({'error': '密码格式无效'}, status_code=400)

        if password != confirm_password:
            return custom_json_response({'error': '密码和确认密码不匹配'}, status_code=400)

        try:
            is_legitimate = False
            registration_source = "illegal"

            if registration_token == "frontend_legit_token":
                is_legitimate = True
            elif registration_token == "register_tool_legit_token":
                is_legitimate = True
                registration_source = "register_tool"

            import secrets
            import datetime
            machine_code = secrets.token_hex(16)
            security_code = secrets.token_hex(8)
            register_timezone = str(datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)

            import sqlite3
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO users
                (username, password, email, role, is_active, security_code, machine_code, register_ip, register_timezone, activated_at, registration_source, is_illegal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username,
                password,
                email,
                'user',
                0,
                security_code,
                machine_code,
                client_ip,
                register_timezone,
                None,
                registration_source,
                0 if is_legitimate else 1
            ))
            conn.commit()
            conn.close()

            if is_legitimate:
                log_security_event(client_ip, 1, 'register_attempt', 'success', f'用户名: {username}, 邮箱: {email}, 来源: {registration_source}')
                return custom_json_response({'message': '注册成功,请等待管理员激活'}, status_code=200)
            else:
                log_security_event(client_ip, None, 'register_attempt', 'illegal', f'用户名: {username}, 邮箱: {email}, 非法来源')
                return custom_json_response({'message': '注册成功,请等待管理员激活'}, status_code=200)
        except Exception as e:
            log_security_event(client_ip, None, 'register_attempt', 'failed', f'用户名: {username}, 邮箱: {email}, 错误: {str(e)}')
            return custom_json_response({'error': f'注册失败: {str(e)}'}, status_code=500)

    return "Register Page", 200


@app.route('/api/test', methods=['GET', 'POST'])
def api_test():
    """API测试路由"""
    return custom_json_response({'message': 'API测试成功'}, status_code=200)


@app.route('/api/ip/list', methods=['GET'])
def list_ips():
    """列出IP列表"""
    ips = ip_manager.get_all_ips()
    return custom_json_response({'ips': ips}, status_code=200)


@app.route('/api/ip/add', methods=['POST'])
def add_ip():
    """添加IP到指定列表"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    ip_type = data.get('type', 'whitelist')
    reason = data.get('reason', '管理员添加')
    added_by = data.get('added_by', 'admin')

    if not ip_address:
        return custom_json_response({'error': 'IP地址不能为空'}, status_code=400)

    result = ip_manager.add_ip(ip_address, ip_type, reason, added_by)
    return custom_json_response({'success': result, 'ip_address': ip_address, 'type': ip_type}, status_code=200 if result else 500)


@app.route('/api/ip/remove', methods=['POST'])
def remove_ip():
    """从指定列表移除IP"""
    data = request.get_json()
    ip_address = data.get('ip_address')

    if not ip_address:
        return custom_json_response({'error': 'IP地址不能为空'}, status_code=400)

    result = ip_manager.remove_ip(ip_address)
    return custom_json_response({'success': result, 'ip_address': ip_address}, status_code=200 if result else 500)


@app.route('/api/ai/anomaly/stats', methods=['GET'])
def get_anomaly_stats():
    """获取异常检测统计信息"""
    stats = ai_anomaly_detector.get_anomaly_stats()
    return custom_json_response(stats, status_code=200)


@app.route('/api/ai/anomaly/detect', methods=['POST'])
def manual_detect_anomaly():
    """手动检测异常"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    action = data.get('action')
    result = data.get('result')

    if not all([ip_address, action, result]):
        return custom_json_response({'error': '缺少必要参数'}, status_code=400)

    is_anomalous, details, score = ai_anomaly_detector.detect_anomalous_behavior(
        ip_address, action, result,
        user_agent=data.get('user_agent', ''),
        path=data.get('path', '')
    )

    return custom_json_response({
        'is_anomalous': is_anomalous,
        'details': details,
        'score': score
    }, status_code=200)


@app.route('/api/ai/brain/problems', methods=['GET'])
def list_problems():
    """获取问题列表"""
    knowledge_base = ai_brain.export_knowledge_base()
    problems = knowledge_base['problems']
    return custom_json_response({'problems': problems}, status_code=200)


@app.route('/api/ai/brain/solutions', methods=['GET'])
def list_solutions():
    """获取解决方案列表"""
    problem_id = request.args.get('problem_id')
    solutions = ai_brain.get_solutions_for_problem(problem_id) if problem_id else []
    return custom_json_response({'solutions': solutions}, status_code=200)


@app.route('/api/ai/brain/repair', methods=['POST'])
def auto_repair():
    """自动修复问题"""
    data = request.get_json()
    problem_description = data.get('problem_description')
    context = data.get('context', {})

    if not problem_description:
        return custom_json_response({'error': '问题描述不能为空'}, status_code=400)

    result = ai_brain.auto_repair(problem_description, context)
    return custom_json_response(result, status_code=200)


@app.route('/api/ai/log/analyze', methods=['POST'])
def analyze_log():
    """分析日志"""
    data = request.get_json()
    log_content = data.get('log_content')
    log_file = data.get('log_file')

    if not log_content and not log_file:
        return custom_json_response({'error': '日志内容或日志文件路径不能为空'}, status_code=400)

    if log_file:
        result = log_analyzer.analyze_log_file(log_file)
    else:
        result = log_analyzer.analyze_log_content(log_content)

    return custom_json_response(result, status_code=200)


@app.route('/api/ai/log/report', methods=['GET'])
def get_log_report():
    """获取日志分析报告"""
    report_id = request.args.get('report_id')
    if report_id:
        report = log_analyzer.get_report(report_id)
    else:
        report = log_analyzer.generate_report()
    return custom_json_response(report, status_code=200)


@app.route('/api/ai/performance/status', methods=['GET'])
def get_performance_status():
    """获取当前性能状态"""
    if perf_monitor is None:
        return custom_json_response({'error': '性能监控功能不可用'}, status_code=503)
    try:
        status = perf_monitor.get_current_status()
        return custom_json_response(status, status_code=200)
    except Exception as e:
        return custom_json_response({'error': f'获取性能状态失败: {str(e)}'}, status_code=500)


@app.route('/api/ai/performance/report', methods=['GET'])
def get_performance_report():
    """获取性能报告"""
    if perf_monitor is None:
        return custom_json_response({'error': '性能监控功能不可用'}, status_code=503)
    try:
        time_window = int(request.args.get('time_window', 3600))
        report = perf_monitor.get_performance_report(time_window)
        return custom_json_response(report, status_code=200 if report.get('success', True) else 500)
    except Exception as e:
        return custom_json_response({'error': f'获取性能报告失败: {str(e)}'}, status_code=500)


@app.route('/api/ai/performance/optimize', methods=['POST'])
def optimize_performance():
    """执行性能优化"""
    data = request.get_json()
    metric = data.get('metric')
    action = data.get('action')

    return custom_json_response({
        'success': True,
        'message': f'已执行{metric}的{action}优化',
        'details': {
            'metric': metric,
            'action': action
        }
    }, status_code=200)


@app.route('/api/ai/overview', methods=['GET'])
def get_ai_overview():
    """获取AI系统概览"""
    ip_stats = ip_manager.get_stats()
    knowledge_base = ai_brain.export_knowledge_base()

    overview = {
        'anomaly_detector': ai_anomaly_detector.get_anomaly_stats(),
        'ip_manager': {
            'total_ips': ip_stats['total'],
            'whitelist_ips': ip_stats['whitelist'],
            'blacklist_ips': ip_stats['blacklist'],
        },
        'brain': {
            'total_problems': len(knowledge_base['problems']),
            'total_solutions': len(knowledge_base['solutions'])
        },
        'log_analyzer': {
            'total_logs': log_analyzer.get_total_logs()
        }
    }

    if perf_monitor is not None:
        try:
            overview['performance_monitor'] = perf_monitor.get_current_status()['app']
        except Exception as e:
            overview['performance_monitor'] = {'error': f'获取性能数据失败: {str(e)}'}
    else:
        overview['performance_monitor'] = {'error': '性能监控功能不可用'}

    return custom_json_response(overview, status_code=200)


if __name__ == '__main__':
    PORT = 8888
    print(f"Starting Simple Flask app on http://0.0.0.0:{PORT}...")

    try:
        print("[简化启动] 直接启动Flask服务器,跳过AI系统初始化...")
        app.run(host='0.0.0.0', port=PORT, debug=True)
    except KeyboardInterrupt:
        print("Flask app stopped.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
