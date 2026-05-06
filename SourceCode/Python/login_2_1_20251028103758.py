# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:08
#!/usr/bin/env python3

import http.server
import socketserver
import webbrowser
import os
import sys
# JSON import removed - using database
import cgi
import logging
import datetime
import urllib.parse
from threading import Timer

# pyodbc将在需要时动态导入

# 设置端口号
PORT = 8000

# 配置日志记录
LOG_DIR = './Logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f'login_{datetime.date.today().strftime("%Y-%m-%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('login_server')

# 获取脚本所在目录的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))

# 数据库连接配置
class DatabaseConfig:
    def __init__(self):
        self.conn_str = ""
        self.load_connection_string()

    def load_connection_string(self):
        try:
            # 从项目根目录加载连接字符串，而不是从脚本目录
            project_root = os.path.dirname(script_dir)
            config_file = os.path.join(project_root, 'MyData', 'db_connection_string.txt')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if not line.startswith('#') and line:
                            # 寻找包含服务器信息的连接字符串
                            if 'Server=' in line or 'SERVER=' in line:
                                self.conn_str = line.split('=', 1)[1] if '=' in line else line
                                break
                logger.info('成功从配置文件读取数据库连接信息')
            else:
                self.conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=wuchenghao15.xicp.net,33693;DATABASE=MyData;UID=sa;PWD=LoginMe15;"
                logger.info('使用默认数据库连接信息')
        except Exception as e:
            logger.error(f'加载数据库连接字符串失败: {str(e)}')
            # 使用默认连接字符串作为后备
            self.conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=wuchenghao15.xicp.net,33693;DATABASE=MyData;UID=sa;PWD=LoginMe15;"
# 自定义请求处理器
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db_config = DatabaseConfig()
        # 设置服务器目录为项目根目录，而不是脚本目录
        project_root = os.path.dirname(script_dir)

    # 处理POST请求
    def do_POST(self):
        if self.path == '/api/login':
            self.handle_login()
        else:
            super().do_POST()
    # 处理登录请求
    def handle_login(self):
        try:
            content_type = self.headers.get('content-type')
            if not content_type or 'application/json' not in content_type:
                self.send_error(400, "Content type must be application/json")
                return

            # 读取请求体
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            login_data = eval(post_data)

            username = login_data.get('username', '').strip()
            password = login_data.get('password', '')
            remember = login_data.get('remember', False)
            captcha_id = login_data.get('captcha_id', '')
            captcha_code = login_data.get('captcha_code', '')

            logger.info(f'用户登录尝试: username={username}, remember={remember}')

            # 验证输入
            if not username or not password:
                logger.warn(f'登录失败: {username}, 原因: 用户名或密码为空')
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str({
                    'success': False,
                    'message': '请输入用户名和密码'
                }).encode())
                return

            # 验证验证码
            captcha_valid, captcha_msg = self.validate_captcha(captcha_id, captcha_code)
            if not captcha_valid:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str({
                    'success': False,
                    'message': captcha_msg
                return
            # 验证用户凭据


                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                # 设置cookie
                user_info = auth_result['user']
                session_data = str(user_info)
                cookie_expires = self.get_cookie_expires(remember)
                self.send_header('Set-Cookie', f'mtscos_user_cookie={urllib.parse.quote(session_data)}; Path=/; HttpOnly; SameSite=Strict; {cookie_expires}')

                self.wfile.write(str(auth_result).encode())
            else:
                logger.error(f'登录失败: {username}, 原因: {auth_result.get("message", "用户名或密码错误")}')
                self.send_response(401)
                self.end_headers()
                self.wfile.write(str(auth_result).encode())

        except Exception as e:
            logger.error(f'处理登录请求时发生错误: {str(e)}')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
                'message': '服务器内部错误'
            }).encode())

    def validate_user_credentials(self, username, password):
        try:
            # 首先尝试从本地文件验证（用于测试环境或当数据库不可用）
            import hashlib
            import traceback
            users_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users_data')
            if os.path.exists(user_file):
                logger.info(f'从本地文件加载用户信息: {user_file}')
                with open(user_file, 'r', encoding='utf-8') as f:

                # 计算密码哈希并比较

                if user_data['password_hash'] == hashed_password:
                    logger.info(f'用户验证成功（本地文件）: {username}')
                        'success': True,
                        'user': {
                            'username': user_data['username'],
                            'displayName': user_data.get('displayName', user_data['username'])
                        }
                    }
                else:
                    logger.warn(f'密码不匹配（本地文件）: {username}')

            # 尝试连接到数据库
                conn = pyodbc.connect(self.db_config.conn_str)
                cursor = conn.cursor()

                # 查询用户信息
                cursor.execute("SELECT username, role, displayName, password_hash FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()

                # 关闭连接
                cursor.close()
                conn.close()

                if row:
                    # 计算密码哈希并比较
                    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

                    if row.password_hash == hashed_password:
                        logger.info(f'用户验证成功（数据库）: {username}')
                        return {
                            'success': True,
                            'user': {
                                'username': row.username,
                                'role': row.role or 'user',
                            }
                        }
                    else:
                        logger.warn(f'密码不匹配（数据库）: {username}')
                else:
                    logger.warn(f'用户不存在（数据库）: {username}')
            except ImportError:
            except Exception as e:
        except Exception as e:
            logger.error(f'验证用户凭据时发生错误: {str(e)}')
            logger.error(traceback.format_exc())

        # 如果所有验证方式都失败，返回认证失败
        logger.warn(f'所有验证方式均失败: {username}')
        return {
            'success': False,
            'message': '用户名或密码错误'

        """验证验证码是否正确"""
            # JSON import removed - using database
            verify_url = "http://localhost:8001/api/verify-captcha"
            headers = {'Content-Type': 'application/json'}
            payload = str({
                'captcha_code': captcha_code

            result = response.json()

            if result.get('success'):
                logger.info(f'验证码验证成功')
                logger.warn(f'验证码验证失败: {result.get("message", "未知错误")}')
                return False, result.get("message", "验证码错误")
        except ImportError:
            logger.warn('requests模块不可用，无法验证验证码')
            return True, "开发环境跳过验证码验证"
            logger.error(f'验证验证码时发生错误: {str(e)}')
            return False, f'验证码验证失败: {str(e)}'

    # 获取cookie过期时间
    def get_cookie_expires(self, remember):
        if remember:
        else:
            # 不记住我，会话结束时过期
            return ''
        return f'Expires={expires.strftime("%a, %d %b %Y %H:%M:%S GMT")};'

    def log_message(self, format, *args):
            # 只记录非API请求
            logger.info("%s - - [%s] %s" % (
                self.client_address[0],
                self.log_date_time_string(),
                format % args))

# 启动服务器
def run_server():
    try:
        # 创建TCP服务器 - 注意：地址需要是元组形式
            logger.info(f"服务器已启动，访问地址: http://localhost:{PORT}/MyPages/index.html")
            logger.info("按Ctrl+C停止服务器")

            # 在浏览器中打开页面
            def open_browser():
                webbrowser.open_new_tab(f"http://localhost:{PORT}/MyPages/index.html")

            # 延迟一秒打开浏览器，确保服务器已经启动
            Timer(1, open_browser).start()

            # 启动服务器
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
        sys.exit(0)

def main():
    # 运行服务器

if __name__ == "__main__":
    main()
