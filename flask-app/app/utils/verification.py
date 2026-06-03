# -*- coding: utf-8 -*-
import os
import base64
import random
import string
from datetime import datetime, timedelta
from flask import request
from app.utils.logging import logger
from app.utils.db import db_manager

class VerificationUtils:
    """多因素验证工具类: 用于实现滚码,唯一码,防伪码等验证逻辑"""

    @staticmethod
    def generate_roll_code(user_id, username, length=6):
        """生成滚码 - 动态验证码"""
        try:
            # 生成随机滚码
            roll_code = ''.join(random.choices(string.digits, k=length))

            # 计算有效期(30秒)
            expires_at = (datetime.now() + timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S')

            # 保存到数据库
            db_manager.execute(
                'INSERT INTO verification_codes (code, code_type, user_id, username, expires_at) VALUES (?, ?, ?, ?, ?)',
                (roll_code, 'roll_code', user_id, username, expires_at)
            )

            logger.info(f"生成滚码: {roll_code},用户: {username},有效期: {expires_at}")
            return roll_code
        except Exception as e:
            logger.error(f"生成滚码失败: {str(e)}")
            return None

    @staticmethod
    def generate_unique_code(user_id, username, length=8):
        """生成唯一码 - 一次性验证码"""
        try:
            unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

            # 计算有效期(24小时)
            expires_at = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

            # 保存到数据库
            db_manager.execute(
                'INSERT INTO verification_codes (code, code_type, user_id, username, expires_at) VALUES (?, ?, ?, ?, ?)',
                (unique_code, 'unique_code', user_id, username, expires_at)
            )

            logger.info(f"生成唯一码: {unique_code},用户: {username}")
            return unique_code
        except Exception as e:
            logger.error(f"生成唯一码失败: {str(e)}")
            return None

    @staticmethod
    def generate_anti_fake_code(user_id, username, length=16):
        """生成防伪码 - 用于硬件设备验证"""
        try:
            # 生成随机防伪码
            anti_fake_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

            # 计算有效期(永久)
            expires_at = (datetime.now() + timedelta(days=3650)).strftime('%Y-%m-%d %H:%M:%S')  # 10年

            # 保存到数据库
            db_manager.execute(
                'INSERT INTO verification_codes (code, code_type, user_id, username, expires_at) VALUES (?, ?, ?, ?, ?)',
                (anti_fake_code, 'anti_fake_code', user_id, username, expires_at)
            )

            logger.info(f"生成防伪码: {anti_fake_code},用户: {username}")
            return anti_fake_code
        except Exception as e:
            logger.error(f"生成防伪码失败: {str(e)}")
            return None

    @staticmethod
    def generate_whitelist_token(user_id=None, username=None, expires_at=None, description=None):
        """生成白名单 token"""
        try:
            # 生成随机 token
            token = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
            # 准备参数
            params = [token, user_id, username]
            query = 'INSERT INTO whitelist_tokens (token, user_id, username'

            # 添加可选参数
            if expires_at:
                query += ', expires_at'
                params.append(expires_at.strftime('%Y-%m-%d %H:%M:%S'))
            if description:
                query += ', description'
                params.append(description)

            # 完成查询
            query += ') VALUES (' + ', '.join(['?'] * len(params)) + ')'

            # 保存到数据库
            db_manager.execute(query, params)

            logger.info(f"生成白名单 token: {token[:10]}...,用户: {username}")
            return token
        except Exception as e:
            logger.error(f"生成白名单 token 失败: {str(e)}")
            return None

    @staticmethod
    def verify_whitelist_token(token, user_id=None, username=None):
        """验证白名单 token"""
        try:
            # 构建查询条件
            query = 'SELECT user_id, username, is_active, expires_at FROM whitelist_tokens WHERE token = ?'
            params = [token]
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            if username:
                query += ' AND username = ?'
                params.append(username)

            token_data = db_manager.fetch_one(query, params)

            if not token_data:
                logger.warning(f"白名单 token 不存在: {token[:10]}...")
                return False, "白名单 token 不存在"

            # 检查是否激活
            if not token_data.get('is_active'):
                logger.warning(f"白名单 token 未激活: {token[:10]}...")
                return False, "白名单 token 未激活"

            # 检查是否过期
            if token_data.get('expires_at'):
                expires_at = datetime.strptime(token_data['expires_at'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() > expires_at:
                    logger.warning(f"白名单 token 已过期: {token[:10]}...")
                    return False, "白名单 token 已过期"

            return True, "验证成功"
        except Exception as e:
            logger.error(f"验证白名单 token 失败: {str(e)}")
            return False, f"验证失败: {str(e)}"

    @staticmethod
    def deactivate_whitelist_token(token):
        """停用白名单 token"""
        try:
            db_manager.execute(
                'UPDATE whitelist_tokens SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE token = ?',
                (token,)
            )
            logger.info(f"停用白名单 token: {token[:10]}...")
            return True
        except Exception as e:
            logger.error(f"停用白名单 token 失败: {str(e)}")
            return False

    @staticmethod
    def verify_roll_code(code, user_id=None, username=None):
        """验证滚码"""
        return VerificationUtils._verify_code(code, 'roll_code', user_id, username)

    @staticmethod
    def verify_unique_code(code, user_id=None, username=None):
        """验证唯一码"""
        return VerificationUtils._verify_code(code, 'unique_code', user_id, username)

    @staticmethod
    def verify_anti_fake_code(code, user_id=None, username=None):
        """验证防伪码"""
        return VerificationUtils._verify_code(code, 'anti_fake_code', user_id, username)

    @staticmethod
    def _verify_code(code, code_type, user_id=None, username=None):
        """通用验证码验证逻辑"""
        try:
            # 构建查询条件
            query = 'SELECT id, user_id, username, is_used, expires_at FROM verification_codes WHERE code = ? AND code_type = ?'
            params = [code, code_type]

            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            if username:
                query += ' AND username = ?'
                params.append(username)

            # 查询验证码
            code_data = db_manager.fetch_one(query, params)

            if not code_data:
                logger.warning(f"验证码不存在: {code},类型: {code_type}")
                return False, "验证码不存在"

            # 检查是否已使用
            if code_data.get('is_used'):
                logger.warning(f"验证码已使用: {code}")
                return False, "验证码已使用"

            # 检查是否过期
            if code_data.get('expires_at'):
                expires_at = datetime.strptime(code_data['expires_at'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() > expires_at:
                    logger.warning(f"验证码已过期: {code}")
                    return False, "验证码已过期"

            # 标记为已使用
            db_manager.execute(
                'UPDATE verification_codes SET is_used = 1 WHERE id = ?',
                (code_data['id'],)
            )

            return True, "验证成功"
        except Exception as e:
            logger.error(f"验证码验证失败: {str(e)}")
            return False, f"验证失败: {str(e)}"

    @staticmethod
    def verify_password(user_id, username, password):
        """验证密码 - 调用现有密码验证逻辑"""
        try:
            from app.utils.security import SecurityUtils

            # 查询用户密码
            user_data = db_manager.fetch_one(
                'SELECT password FROM user WHERE id = ? AND username = ?',
                (user_id, username)
            )

            if not user_data:
                logger.warning(f"用户不存在: {username},ID: {user_id}")
                return False, "用户不存在"

            if SecurityUtils.verify_password(user_data[0], password):
                logger.info(f"密码验证成功: {username}")
                return True, "验证成功"
            else:
                logger.warning(f"密码验证失败: {username}")
                return False, "密码错误"
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False, f"验证失败: {str(e)}"

    @staticmethod
    def verify_vikey_hardware(hardware_id, is_admin=False):
        """验证Vikey硬件码 - 验证Vikey硬件设备"""
        try:
            # 查询硬件信息
            hardware_data = db_manager.fetch_one(
                'SELECT user_id, username, is_active, is_admin FROM vikey_hardware WHERE hardware_id = ?',
                (hardware_id,)
            )

            if not hardware_data:
                logger.warning(f"Vikey硬件不存在: {hardware_id}")
                return False, "Vikey硬件不存在"

            user_id, username, is_active, db_is_admin = hardware_data[0], hardware_data[1], hardware_data[2], hardware_data[3]

            # 检查是否激活
            if not is_active:
                logger.warning(f"Vikey硬件未激活: {hardware_id}")
                return False, "Vikey硬件未激活"

            # 检查管理员权限
            if is_admin and not db_is_admin:
                logger.warning(f"Vikey硬件无管理员权限: {hardware_id}")
                return False, "Vikey硬件无管理员权限"

            return True, "验证成功"
        except Exception as e:
            logger.error(f"Vikey硬件验证失败: {str(e)}")
            return False, f"验证失败: {str(e)}"

    @staticmethod
    def log_verification(username, verification_type, verification_value, is_successful, error_message=None, client_ip=None):
        """记录验证日志"""
        try:
            ip_address = client_ip or (request.remote_addr if request else 'unknown')

            # 获取用户代理
            user_agent = request.user_agent.string if request else 'unknown'

            # 保存日志
            db_manager.execute(
                'INSERT INTO verification_logs (username, verification_type, verification_value, is_successful, error_message, ip_address, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (username, verification_type, verification_value, 1 if is_successful else 0, error_message, ip_address, user_agent)
            )

            logger.info(f"记录验证日志: {username}, 类型: {verification_type}, 结果: {'成功' if is_successful else '失败'}")
        except Exception as e:
            logger.error(f"记录验证日志失败: {str(e)}")

    @staticmethod
    def verify_all_factors(username, password, roll_code=None, unique_code=None, anti_fake_code=None, db_id=None, vikey_hardware_id=None, whitelist_token=None):
        """验证所有因素"""
        try:
            client_ip = request.remote_addr if request else 'unknown'

            # 1. 检查登录尝试次数
            login_attempts = db_manager.fetch_one(
                'SELECT COUNT(*) FROM login_attempts WHERE username = ? AND ip_address = ? AND attempt_time > datetime("now", "-5 minutes")',
                (username, client_ip)
            )

            if login_attempts and login_attempts[0] >= 5:
                logger.warning(f"登录尝试次数过多: {username},IP: {client_ip}")
                VerificationUtils.log_verification(username, 'rate_limit', '', False, "登录尝试次数过多,请5分钟后再试")
                return False, "登录尝试次数过多,请5分钟后再试"

            # 2. 验证密码
            password_result, password_msg = VerificationUtils.verify_password(None, username, password)
            if not password_result:
                VerificationUtils.log_verification(username, 'password', '', False, password_msg)
                return False, password_msg

            # 3. 验证其他因素(如果提供)
            if roll_code:
                roll_result, roll_msg = VerificationUtils.verify_roll_code(roll_code, username=username)
                if not roll_result:
                    VerificationUtils.log_verification(username, 'roll_code', roll_code, False, roll_msg)
                    return False, roll_msg

            if unique_code:
                unique_result, unique_msg = VerificationUtils.verify_unique_code(unique_code, username=username)
                if not unique_result:
                    VerificationUtils.log_verification(username, 'unique_code', unique_code, False, unique_msg)
                    return False, unique_msg

            if anti_fake_code:
                anti_fake_result, anti_fake_msg = VerificationUtils.verify_anti_fake_code(anti_fake_code, username=username)
                if not anti_fake_result:
                    VerificationUtils.log_verification(username, 'anti_fake_code', anti_fake_code, False, anti_fake_msg)
                    return False, anti_fake_msg

            if whitelist_token:
                token_result, token_msg = VerificationUtils.verify_whitelist_token(whitelist_token, username=username)
                if not token_result:
                    VerificationUtils.log_verification(username, 'whitelist_token', whitelist_token[:10], False, token_msg)
                    return False, token_msg

            # 所有验证通过
            VerificationUtils.log_verification(username, 'all_factors', '', True)
            return True, "验证成功"
        except Exception as e:
            logger.error(f"多因素验证失败: {str(e)}")
            return False, f"验证失败: {str(e)}"
