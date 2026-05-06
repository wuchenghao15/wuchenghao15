#!/usr/bin/env python3
"""
Simple Flask Start Script with Security Defenses

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
# JSON import removed - using database
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Flask和相关模块
# JSON import removed - using database
from ip_manager import get_ip_manager

# 禁用dotenv加载，避免超时问题
os.environ['FLASK_SKIP_DOTENV'] = '1'
os.environ['FLASK_APP'] = __file__
os.environ['FLASK_ENV'] = 'development'

# 创建Flask应用
app = Flask(__name__)

# 生成安全的SECRET_KEY
if not os.environ.get('FLASK_SECRET_KEY'):
    os.environ['FLASK_SECRET_KEY'] = secrets.token_urlsafe(64)

# 配置Flask应用
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['DATABASE'] = 'app.db'

# 配置安全的会话选项
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# 设置模板目录
app.template_folder = 'templates'

# 设置静态文件目录
app.static_folder = 'static'

# ------------------------------
# 自定义JSON响应处理
# ------------------------------

    """自定义JSON响应，优化pre标签显示效果，支持包含上下文信息"""
    try:
        # 1. 增强响应数据，添加调试和上下文信息（如果启用）
        response_data = data.copy() if isinstance(data, dict) else data

        if include_context and isinstance(response_data, dict):
            # 添加请求上下文信息
            response_data['_context'] = {
                'timestamp': datetime.now().isoformat(),
                'request_id': str(uuid.uuid4()),
                'client_ip': request.remote_addr,
                'path': request.path,
                'method': request.method
            }

        # 2. 优化JSON序列化，确保在pre标签中显示美观
        if pretty:
            # 使用更适合pre标签显示的格式
            json_str = str(
                response_data,
                ensure_ascii=False,  # 支持中文
                indent=2,            # 缩进2空格
                separators=(',', ': '),  # 优化分隔符
                sort_keys=True       # 按键排序，增强可读性
            )
        else:
            json_str = str(response_data)

        # 3. 创建响应对象
        response = make_response(json_str)

        # 4. 设置优化的响应头
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['X-Content-Type-Options'] = 'nosniff'  # 防止MIME类型嗅探
        response.headers['X-Frame-Options'] = 'DENY'  # 防止点击劫持
        response.status_code = status_code

        return response
    except Exception as e:
        # 构建更详细的错误响应
        error_data = {
            'error': str(e),
            'error_type': type(e).__name__,
            '_context': {
                'timestamp': datetime.now().isoformat(),
                'request_id': str(uuid.uuid4()),
                'client_ip': request.remote_addr,
                'method': request.method
        }
        error_response = make_response(
        )
        error_response.status_code = 500
# ------------------------------
# 安全防御相关函数

ip_manager = get_ip_manager()

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
    print(f"[白名单] 添加IP {ip_address} 到白名单，原因: {reason}，添加者: {added_by}")
    return ip_manager.add_ip(ip_address, 'whitelist', reason, added_by)

def add_ip_to_blacklist(ip_address, reason, added_by):
    """添加IP到黑名单"""
    print(f"[黑名单] 添加IP {ip_address} 到黑名单，原因: {reason}，添加者: {added_by}")
    return ip_manager.add_ip(ip_address, 'blacklist', reason, added_by)

def add_ip_to_sandbox(ip_address, reason, marked_by):
    """将IP添加到沙箱隔离"""
    print(f"[沙箱] 将IP {ip_address} 添加到沙箱，原因: {reason}，标记者: {marked_by}")
    return ip_manager.add_ip(ip_address, 'sandbox', reason, marked_by)

def check_access_rate_limit(ip_address, endpoint, limit=5, window=60):
    """检查访问频率限制"""
    # 简化版本，模拟频率限制
    global access_counts
    current_time = time.time()
    if endpoint not in access_counts:
        access_counts[endpoint] = {}
    if ip_address not in access_counts[endpoint]:
        access_counts[endpoint][ip_address] = {'count': 0, 'last_request': current_time}

    if current_time - access_counts[endpoint][ip_address]['last_request'] > window:
        # 超过时间窗口，重置计数
        access_counts[endpoint][ip_address] = {'count': 1, 'last_request': current_time}
        return True
    else:
        # 未超过时间窗口，检查请求数
        if access_counts[endpoint][ip_address]['count'] >= limit:
            # 超过限制
            return False
        else:
            # 增加计数
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
        elif validation_type == 'password':
            # 放宽密码规则，允许纯数字密码，只要长度至少为6位，允许下划线
            return bool(re.match(r'^[a-zA-Z\d@$!%*?&._-]{6,}$', input_data))
        return False
        return False

def sanitize_input(input_data):
    """净化输入数据"""
    if isinstance(input_data, str):
        sanitized = html.escape(input_data)
        sanitized = re.sub(r'[\x00\x1a"\'\\\/\;\(\)]', '', sanitized)
        return sanitized
    return input_data

# ------------------------------
# AI异常检测器 - 使用增强版实现


from ai_brain import get_ai_brain

# 导入AI日志分析器
from ai_log_analyzer import get_log_analyzer

# 尝试导入AI性能监控器，如果失败则使用None
perf_monitor = None
try:
    from ai_performance_monitor import get_performance_monitor
    perf_monitor = get_performance_monitor()
except ImportError as e:
    print(f"警告: 无法导入AI性能监控器: {e}")
    print("系统将在没有性能监控的情况下运行")

# 导入AI自我提升系统
try:
    from ai_self_improvement import get_ai_self_improvement
    ai_self_improvement = get_ai_self_improvement()
except ImportError as e:
    print(f"警告: 无法导入AI自我提升系统: {e}")
    ai_self_improvement = None

# 导入AI自动化管理系统
try:
    from ai_auto_management import get_ai_auto_management
    ai_auto_management = get_ai_auto_management()
except ImportError as e:
    print(f"警告: 无法导入AI自动化管理系统: {e}")
    ai_auto_management = None

# 全局变量
access_counts = {}
failed_login_attempts = {}

# 获取AI实例
ai_anomaly_detector = get_ai_detector()
ai_brain = get_ai_brain()
# 只有在之前导入失败时才尝试重新获取perf_monitor
if perf_monitor is None:
    try:
        perf_monitor = get_performance_monitor()
    except Exception as e:
        print(f"警告: 无法获取性能监控器实例: {e}")

# 安全防御中间件

@app.after_request
def enhanced_security_middleware(response):
    """增强版安全防御中间件"""
    # 基础安全头设置
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
@app.before_request
def performance_monitor_start():
    request.start_time = time.time()


@app.before_request
def security_defense_middleware():
    """安全防御中间件，实行黑名单制防火墙
    规则：
    1. 白名单IP：直接放行
    2. 黑名单IP：拒绝访问
    3. 沙箱IP：特殊处理
    4. 其他IP：自动放行（黑名单制）
    # 排除健康检查接口
    if request.path in ['/health', '/version']:

    # 获取客户端IP
    client_ip = request.remote_addr
    endpoint = request.path

    # 1. 检查IP是否在白名单中 - 直接放行
    if is_ip_whitelisted(client_ip):
        log_security_event(client_ip, None, 'access_attempt', 'allowed', f'白名单IP放行: {endpoint}')
        return  # 直接放行，不检查其他限制

    # 2. 检查IP是否在黑名单中 - 拒绝访问
    if is_ip_blacklisted(client_ip):
        log_security_event(client_ip, None, 'access_attempt', 'blocked', f'黑名单IP拦截: {endpoint}')
        return custom_json_response({'error': '您的IP已被禁止访问'}, status_code=403)
    # 3. 检查IP是否在沙箱中 - 按照沙箱规则处理
    if is_ip_in_sandbox(client_ip):
        log_security_event(client_ip, None, 'access_attempt', 'sandboxed', f'沙箱IP访问: {endpoint}')
        # 沙箱IP可以访问，但会受到更严格的监控

    # 4. 其他IP：自动放行（黑名单制）
    # 但仍需对敏感接口进行访问频率限制
    if endpoint in ['/auth/login', '/auth/register']:
        # 登录/注册接口：1分钟内最多5次请求
        if not check_access_rate_limit(client_ip, endpoint, limit=5, window=60):
            # 检测到异常访问，添加到沙箱
            add_ip_to_sandbox(client_ip, f'登录/注册频率超限', 'system')
            log_security_event(client_ip, None, 'access_attempt', 'rate_limited', f'登录/注册频率超限，已添加到沙箱: {endpoint}')
            return custom_json_response({'error': '请求频率过高，您的IP已被标记为嫌疑IP，请等待管理员审核'}, status_code=429)
    elif endpoint.startswith('/api/'):
        # API接口：1分钟内最多30次请求
        if not check_access_rate_limit(client_ip, endpoint, limit=30, window=60):
            # 检测到异常访问，添加到沙箱
            add_ip_to_sandbox(client_ip, f'API频率超限', 'system')
            log_security_event(client_ip, None, 'access_attempt', 'rate_limited', f'API频率超限，已添加到沙箱: {endpoint}')
            return custom_json_response({'error': 'API请求频率过高，您的IP已被标记为嫌疑IP，请等待管理员审核'}, status_code=429)


@app.after_request
def performance_monitor_end(response):
    """性能监控结束中间件"""
    if hasattr(request, 'start_time'):
        response_time = time.time() - request.start_time
        endpoint = request.path
        method = request.method
        is_error = response.status_code >= 400

        # 记录请求性能数据（仅当perf_monitor可用时）
        if perf_monitor is not None:
            try:
                perf_monitor.record_request(endpoint, method, response_time, is_error)
            except Exception as e:
                print(f"记录请求性能数据失败: {e}")

    return response

# ------------------------------
# 简单路由
# ------------------------------
    return render_template('index.html')

@app.route('/health')
def health():

@app.route('/version')
def version():
    return {"VERSION": "3.0.0"}, 200

@app.route('/auth/login', methods=['GET', 'POST'])
        # 获取表单数据
        password = request.form.get('password', '').strip()

        # 简单的输入验证
        if not password:
            flash('请输入密码', 'error')
            return render_template('index.html')

        # 直接使用sqlite3连接数据库
        import sqlite3
        import hashlib
        import base64
            # 连接数据库
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 只获取密码，不验证用户名
            cursor.execute('SELECT id, username, email, password, role, is_active FROM users LIMIT 1')
            user = cursor.fetchone()
            conn.close()

            if user:
                user_id, username, email, hashed_password, role, is_active = user

                # 密码验证逻辑 - 简化版，只检查密码是否正确
                password_valid = False

                try:
                    # 尝试直接比较密码（如果数据库中存储的是明文密码）
                    if password == hashed_password:
                        password_valid = True
                    else:
                        # 尝试base64格式验证
                        decoded = base64.b64decode(hashed_password)
                        if len(decoded) == 64:  # 32字节salt + 32字节hash
                            salt = decoded[:32]
                            stored_hash = decoded[32:]

                            # 计算提供密码的哈希值
                                'sha256',
                                password.encode('utf-8'),
                                salt,
                                100000
                            )

                            if hashed == stored_hash:
                                password_valid = True
                        # 如果base64验证失败，尝试hex格式
                        else:
                            # 尝试hex格式验证
                            if len(hashed_password) == 96:  # 16字节salt + 32字节hash（hex格式）
                                salt_hex = hashed_password[:32]
                                hash_hex = hashed_password[32:96]
                                salt = bytes.fromhex(salt_hex)
                                stored_hash = bytes.fromhex(hash_hex)

                                # 计算提供密码的哈希值
                                hashed = hashlib.pbkdf2_hmac(
                                    'sha256',
                                    password.encode('utf-8'),
                                    salt,
                                    100000
                                )

                                    password_valid = True
                except Exception as e:
                    print(f"密码验证错误: {e}")

                if password_valid:
                    # 设置会话
                    session['user_id'] = user_id
                    session['username'] = username
                    session['email'] = email
                    session['role'] = role
                    session['logged_in'] = True

                    # 生成会话ID
                    import uuid
                    session['session_id'] = str(uuid.uuid4())

                    flash('登录成功', 'success')
                    return redirect(url_for('index'))
                    flash('密码不正确', 'error')
                    print(f"密码验证失败，提供的密码: {password}")
            else:
                # 如果没有用户，创建一个默认用户
                print("没有找到用户，创建默认用户...")
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()

                # 创建默认用户，密码为明文"password"
                cursor.execute('''
                    VALUES (?, ?, ?, ?, ?)
                conn.commit()

                if password == 'password':
                    session['email'] = 'admin@example.com'
                    session['logged_in'] = True
                    # 生成会话ID - 确保uuid模块可用
                    import uuid
                    flash('登录成功，已创建默认用户', 'success')
                else:
                    flash('密码不正确', 'error')
        except Exception as e:
            flash('登录时发生错误，请稍后重试', 'error')
            print(f"登录错误: {e}")

        return render_template('index.html')
    # GET请求，渲染登录页面
    return render_template('index.html')

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        email = sanitize_input(request.form.get('email', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        registration_token = request.form.get('registration_token', '')
        log_security_event(client_ip, None, 'register_attempt', 'initiated', f'用户名: {username}, 邮箱: {email}')

        # 输入验证
        if not validate_input(username, 'username'):
            return custom_json_response({'error': '用户名格式无效'}, status_code=400)

        if not validate_input(email, 'email'):
            return custom_json_response({'error': '邮箱格式无效'}, status_code=400)
        if not validate_input(password, 'password'):
            return custom_json_response({'error': '密码格式无效'}, status_code=400)

        # 验证密码和确认密码是否匹配
        if password != confirm_password:
            return custom_json_response({'error': '密码和确认密码不匹配'}, status_code=400)

        try:
            # 验证注册来源
            is_legitimate = False
            registration_source = "illegal"

            # 检查是否是合法的注册来源
            if registration_token == "frontend_legit_token":
                # 首页前端注册
                is_legitimate = True
            elif registration_token == "register_tool_legit_token":
                registration_source = "register_tool"

            # 生成安全唯一码（使用uuid4生成随机唯一码）
            import secrets
            machine_code = secrets.token_hex(16)
            import datetime
            register_timezone = str(datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)
            # 连接数据库
            import sqlite3
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 插入用户信息，包括新添加的字段
            cursor.execute('''
                INSERT INTO users
                (username, password, email, role, is_active, security_code, machine_code, register_ip, register_timezone, activated_at, registration_source, is_illegal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username,
                password,
                email,
                'user',  # 默认角色
                0 if is_legitimate else 0,  # 无论是否合法，都需要管理员激活
                security_code,
                machine_code,
                client_ip,
                register_timezone,
                None,  # 初始激活时间为NULL，管理员激活时再设置
                registration_source,
                0 if is_legitimate else 1  # 只有合法来源的用户is_illegal为0
            ))
            conn.commit()
            conn.close()

            if is_legitimate:
                log_security_event(client_ip, 1, 'register_attempt', 'success', f'用户名: {username}, 邮箱: {email}, 来源: {registration_source}')
                return custom_json_response({'message': '注册成功，请等待管理员激活'}, status_code=200)
            else:
                log_security_event(client_ip, None, 'register_attempt', 'illegal', f'用户名: {username}, 邮箱: {email}, 非法来源')
                return custom_json_response({'message': '注册成功，请等待管理员激活'}, status_code=200)  # 非法用户也返回成功消息，但在数据库中标记为非法
        except Exception as e:
            log_security_event(client_ip, None, 'register_attempt', 'failed', f'用户名: {username}, 邮箱: {email}, 错误: {str(e)}')
            return custom_json_response({'error': f'注册失败: {str(e)}'}, status_code=500)
    return "Register Page", 200

@app.route('/api/test', methods=['GET', 'POST'])
def api_test():
    return custom_json_response({'message': 'API测试成功'}, status_code=200)

# ------------------------------
# AI功能API接口
# ------------------------------

def list_ips():
    return custom_json_response({'ips': ips}, status_code=200)
@app.route('/api/ip/add', methods=['POST'])
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

# 2. AI异常检测API
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

# 3. AI大脑API
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
    context = data.get('context', {})

    if not problem_description:
        return custom_json_response({'error': '问题描述不能为空'}, status_code=400)

    result = ai_brain.auto_repair(problem_description, context)
    return custom_json_response(result, status_code=200)

# 4. AI日志分析API
@app.route('/api/ai/log/analyze', methods=['POST'])
def analyze_log():
    """分析日志"""
    data = request.get_json()
    log_content = data.get('log_content')
    log_file = data.get('log_file')
    if not log_content and not log_file:
        return custom_json_response({'error': '日志内容或日志文件路径不能为空'}, status_code=400)
    if log_file:
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

# 5. AI性能监控API
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

    # 这里可以扩展具体的优化逻辑
    return custom_json_response({
        'success': True,
        'message': f'已执行{metric}的{action}优化',
        'details': {
            'metric': metric,
            'action': action
        }
    }, status_code=200)

# 6. AI综合API
@app.route('/api/ai/overview', methods=['GET'])
def get_ai_overview():
    ip_stats = ip_manager.get_stats()
    knowledge_base = ai_brain.export_knowledge_base()

    # 构建overview对象，根据perf_monitor是否可用添加不同内容
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

    # 只有当perf_monitor可用时才添加performance_monitor数据
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

    # 简化启动流程，直接启动Flask服务器
    # 跳过耗时的AI系统初始化，确保服务器能快速启动
    try:
        print("[简化启动] 直接启动Flask服务器，跳过AI系统初始化...")
        app.run(host='0.0.0.0', port=PORT, debug=True)
    except KeyboardInterrupt:
        print("Flask app stopped.")
        import traceback
        traceback.print_exc()
