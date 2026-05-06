#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注册服务模块
处理用户注册请求，验证用户信息，保存用户数据到数据库

import http.server
import socketserver
# JSON import removed - using database
import hashlib
import time
import uuid
import logging
import os
import sys
from urllib.parse import parse_qs
from http.cookies import SimpleCookie
import traceback
import re
from datetime import datetime, timedelta

# 设置日志
def setup_logger():
    """设置日志记录器"""
    logger = logging.getLogger('register_server')
    logger.setLevel(logging.INFO)

    # 检查是否存在Logs目录（项目一级），如果不存在则创建
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Logs')
    os.makedirs(logs_dir, exist_ok=True)

    # 创建文件处理器
    log_file = os.path.join(logs_dir, 'register.log')
    file_handler = logging.FileHandler(log_file)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

class DatabaseConfig:
    """数据库配置类"""
    def __init__(self):
        """初始化数据库配置"""
        try:
            # 尝试从配置文件中读取数据库连接信息
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_connection_string.txt')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.connection_string = f.read().strip()
                logger.info('成功从配置文件读取数据库连接信息')
            else:
                # 默认数据库连接字符串
                self.connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1;DATABASE=MTSCOS;UID=sa;PWD=your_password;'
                logger.info('使用默认数据库连接信息')
        except Exception as e:
            logger.error(f'读取数据库配置文件时发生错误: {str(e)}')
            self.connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1;DATABASE=MTSCOS;UID=sa;PWD=your_password;'
class RegisterHandler(http.server.BaseHTTPRequestHandler):
    """注册请求处理器"""
    # 初始化数据库配置
    db_config = DatabaseConfig()

    def do_OPTIONS(self):
        """处理OPTIONS请求，设置CORS头"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def do_POST(self):
        """处理POST请求"""
        try:
                self._handle_register()
            else:
                self.send_error(404, "Not Found")
            logger.error(f'处理POST请求时发生错误: {str(e)}')
            logger.error(traceback.format_exc())
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = str({
                'success': False,
            })

    def _handle_register(self):
        """处理用户注册请求"""
        # 记录请求开始时间
        start_time = time.time()
        logger.info('接收到注册请求')

        # 获取请求体
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            register_data = eval(post_data.decode('utf-8'))
            logger.info(f'接收到的注册数据: username={register_data.get("username", "unknown")}, email={register_data.get("email", "unknown")}')

            # 验证注册数据
            validation_result = self._validate_register_data(register_data)
            if not validation_result['success']:
                logger.warn(f'注册数据验证失败: {validation_result["message"]}')
                self._send_response(400, validation_result)
                return

            # 验证验证码
            captcha_result = self._verify_captcha(register_data.get('captcha_id'), register_data.get('captcha_code'))
            if not captcha_result['success']:
                logger.warn(f'验证码验证失败: {captcha_result["message"]}')
                self._send_response(400, captcha_result)
                return

            # 保存用户信息到数据库
            save_result = self._save_user_to_database(register_data)
            if not save_result['success']:
                logger.error(f'保存用户信息到数据库失败: {save_result["message"]}')
                self._send_response(500, save_result)

            # 创建用户会话并设置Cookie
            session_result = self._create_user_session(register_data['username'])
            if not session_result['success']:
                logger.warn(f'创建用户会话失败: {session_result["message"]}')
                # 会话创建失败不影响注册成功，但会在响应中提示
                    'success': True,
                    'message': '注册成功，但会话创建失败，请手动登录',
                    'user_id': save_result.get('user_id')
                }
            else:
                # 设置Cookie
                self.send_header('Set-Cookie', session_result['cookie'])
                    'success': True,
                    'message': '注册成功',
                    'user_id': save_result.get('user_id'),
                    'session_id': session_result.get('session_id')
                }

            # 记录请求处理时间
            process_time = time.time() - start_time
            logger.info(f'注册请求处理完成，耗时: {process_time:.4f}秒，结果: 成功')
            # 发送成功响应

        except json.JSONDecodeError:
            logger.error('请求数据不是有效的JSON格式')
            self._send_response(400, {
                'message': '请求数据格式错误'
            })
        except Exception as e:
            logger.error(f'处理注册请求时发生错误: {str(e)}')
            logger.error(traceback.format_exc())
            self._send_response(500, {
                'success': False,
            })

        """验证注册数据"""
        # 检查必要字段
        required_fields = ['username', 'password', 'email', 'securityQuestion', 'securityAnswer', 'captcha_id', 'captcha_code']
            if field not in data or not data[field]:
                return {'success': False, 'message': f'{field}不能为空'}
        # 验证用户名格式
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]{2,49}$', username):
            return {'success': False, 'message': '用户名必须以字母或数字开头，只能包含字母、数字、下划线、点和连字符，长度在3-50个字符之间'}

        # 验证密码长度
        if len(data['password']) < 6:
            return {'success': False, 'message': '密码长度不能少于6位'}

        # 验证邮箱格式
        email = data['email'].strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {'success': False, 'message': '请输入有效的邮箱地址'}

        # 验证安全答案
        if len(data['securityAnswer'].strip()) < 2:
            return {'success': False, 'message': '安全答案长度不能少于2位'}

        # 检查用户名是否已存在
        if self._check_username_exists(username):
            return {'success': False, 'message': '用户名已存在，请选择其他用户名'}

        # 检查邮箱是否已存在
        if self._check_email_exists(email):
            return {'success': False, 'message': '该邮箱已被注册，请使用其他邮箱'}

        return {'success': True, 'message': '验证通过'}

    def _check_username_exists(self, username):
        """检查用户名是否已存在"""
        try:
            # 注意：这里只是模拟，实际应用中应该使用真实的数据库连接
            logger.info(f'检查用户名是否已存在: {username}')

            # 由于实际环境可能没有数据库连接，这里返回False表示用户名不存在
            # 实际应用中应该执行SELECT查询来检查
            return False
        except Exception as e:
            logger.error(f'检查用户名是否存在时发生错误: {str(e)}')
            # 出错时默认返回False，避免因数据库问题导致注册失败
            return False

    def _check_email_exists(self, email):
        """检查邮箱是否已存在"""
        try:
            # 注意：这里只是模拟，实际应用中应该使用真实的数据库连接
            logger.info(f'检查邮箱是否已存在: {email}')

            # 由于实际环境可能没有数据库连接，这里返回False表示邮箱不存在
            # 实际应用中应该执行SELECT查询来检查
            return False
        except Exception as e:
            logger.error(f'检查邮箱是否存在时发生错误: {str(e)}')
            # 出错时默认返回False，避免因数据库问题导致注册失败
            return False

    def _verify_captcha(self, captcha_id, captcha_code):
        """验证验证码"""
        try:

            # 在实际应用中，应该调用CheckCode.py提供的API来验证验证码
            # 这里简化处理，直接返回验证成功
            return {'success': True, 'message': '验证码验证通过'}
        except Exception as e:
            return {'success': False, 'message': '验证码验证失败'}

    def _save_user_to_database(self, user_data):
        """保存用户信息到数据库"""

            user_id = str(uuid.uuid4())

            # 密码加密

            hashed_security_answer = self._hash_password(user_data['securityAnswer'])

            # 生成创建时间
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 模拟数据库操作
            # 在实际应用中，应该使用真实的数据库连接执行INSERT语句
            logger.info(f'用户信息: ID={user_id}, 用户名={user_data["username"]}, 邮箱={user_data["email"]}, 创建时间={created_at}')

            # 由于实际环境可能没有数据库连接，这里创建一个本地文件来记录注册信息
            self._save_user_to_file(user_id, user_data['username'], user_data['email'], hashed_password, user_data['securityQuestion'], hashed_security_answer, created_at)

            return {
                'success': True,
                'message': '用户信息保存成功',
                'user_id': user_id
            }
        except Exception as e:
            logger.error(f'保存用户信息到数据库时发生错误: {str(e)}')
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'message': '保存用户信息失败'
            }

    def _save_user_to_file(self, user_id, username, email, password_hash, security_question, security_answer_hash, created_at):
        """将用户信息保存到本地文件（用于测试环境）"""
        try:
            users_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users_data')
            os.makedirs(users_dir, exist_ok=True)

            # 保存用户信息到文件
            user_file = os.path.join(users_dir, f'{username}.json')
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'security_question': security_question,
                'created_at': created_at,
                'updated_at': created_at,
                'status': 'active'
            }

            with open(user_file, 'w', encoding='utf-8') as f:

            logger.info(f'用户信息已保存到本地文件: {user_file}')
        except Exception as e:
            logger.error(f'保存用户信息到本地文件时发生错误: {str(e)}')

        """密码加密"""
        # 使用MD5加密密码
        hasher = hashlib.md5()
        hasher.update(password.encode('utf-8'))
        return hasher.hexdigest()

    def _create_user_session(self, username):
        """创建用户会话并设置Cookie"""
        try:
            session_id = str(uuid.uuid4())

            # 设置会话过期时间（30分钟）
            expires = datetime.now() + timedelta(minutes=30)
            expires_str = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
            # 创建Cookie
            cookie = SimpleCookie()
            cookie['user_session'] = session_id
            cookie['user_session']['path'] = '/'
            cookie['user_session']['expires'] = expires_str
            cookie['user_session']['httponly'] = True
            cookie['user_session']['samesite'] = 'Strict'

            # 在实际应用中，应该将会话信息保存到数据库或Redis中
            # 这里简化处理，将会话信息保存到本地文件
            self._save_session_to_file(session_id, username, expires)

            return {
                'success': True,
                'session_id': session_id,
                'cookie': cookie.output(header='', sep='').strip()
            }
        except Exception as e:
            logger.error(f'创建用户会话时发生错误: {str(e)}')
            return {
                'success': False,
                'message': '创建会话失败'
            }

    def _save_session_to_file(self, session_id, username, expires):
        """将会话信息保存到本地文件（用于测试环境）"""
        try:
            sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
            os.makedirs(sessions_dir, exist_ok=True)

            # 保存会话信息到文件
            session_file = os.path.join(sessions_dir, f'{session_id}.json')
            session_data = {
                'session_id': session_id,
                'expires_at': expires.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            logger.info(f'会话信息已保存到本地文件: {session_file}')
            logger.error(f'保存会话信息到本地文件时发生错误: {str(e)}')

    def _send_response(self, status_code, data):
        """发送HTTP响应"""
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        response = str(data)
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        """重写日志记录方法，使用自定义日志器"""
        # 过滤掉API请求日志，只记录错误和关键信息
            return
        logger.info(f'HTTP {self.client_address[0]} - {format % args}')

def run_server(port=8002):
    try:

            try:
            except KeyboardInterrupt:
                logger.info('接收到中断信号，正在停止服务器...')
                httpd.server_close()
                logger.info('服务器已停止')
    except Exception as e:
        logger.error(f'启动服务器时发生错误: {str(e)}')
        logger.error(traceback.format_exc())

    # 获取命令行参数中的端口号，如果没有提供则使用默认端口
    port = 8002
            logger.info(f'使用命令行参数中的端口: {port}')
        except ValueError:

    # 启动服务器
    run_server(port)
