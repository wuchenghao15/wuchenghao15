#!/usr/bin/env python3
"""
系统逻辑管理器
"""

import time
import logging
import datetime
from typing import Dict, List, Any, Optional

from app.utils.db import db_manager
from app.utils.logging import logger
from app.services.user_group_manager import user_group_manager
from app.ai.enhanced_ai_engine import enhanced_ai_engine
from app.models.enhanced_exam import enhanced_exam_system

class SystemLogicManager:
    """系统逻辑管理器"""
    
    def __init__(self):
        """初始化系统逻辑管理器"""
        self.state_machines = {}
        self.business_processes = {}
        logger.info("系统逻辑管理器初始化完成")
    
    def initialize_business_processes(self):
        """初始化业务流程"""
        # 注册业务流程
        self.business_processes = {
            'user_registration': self._process_user_registration,
            'user_login': self._process_user_login,
            'password_reset': self._process_password_reset,
            'exam_taking': self._process_exam_taking,
            'user_group_management': self._process_user_group_management
        }
        logger.info("业务流程初始化完成")
    
    def process_business_flow(self, flow_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理业务流程
        
        Args:
            flow_type: 流程类型
            data: 流程数据
        
        Returns:
            流程结果
        """
        if flow_type not in self.business_processes:
            return {
                'status': 'error',
                'message': f'未知的业务流程类型: {flow_type}'
            }
        
        try:
            logger.info(f"开始处理业务流程: {flow_type}")
            result = self.business_processes[flow_type](data)
            logger.info(f"业务流程 {flow_type} 处理完成")
            return result
        except Exception as e:
            logger.error(f"处理业务流程 {flow_type} 失败: {str(e)}")
            return {
                'status': 'error',
                'message': f'处理业务流程失败: {str(e)}'
            }
    
    def _process_user_registration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户注册流程
        
        Args:
            data: 注册数据
        
        Returns:
            处理结果
        """
        # 1. 验证输入数据
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return {
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }
        
        # 2. 检查用户是否已存在
        existing_user = db_manager.fetch_one(
            'SELECT id FROM user WHERE username = ? OR email = ?',
            (data['username'], data['email'])
        )
        
        if existing_user:
            return {
                'status': 'error',
                'message': '用户名或邮箱已存在'
            }
        
        # 3. 密码强度验证
        if len(data['password']) < 8:
            return {
                'status': 'error',
                'message': '密码长度至少8位'
            }
        
        # 4. 创建用户
        try:
            import bcrypt
            hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            
            result = db_manager.execute(
                '''
                INSERT INTO user (username, email, password, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''',
                (data['username'], data['email'], hashed_password.decode('utf-8'), 1)
            )
            
            user_id = result.lastrowid
            
            # 5. 添加密码历史
            db_manager.execute(
                '''
                INSERT INTO password_history (user_id, password_hash, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ''',
                (user_id, hashed_password.decode('utf-8'))
            )
            
            # 6. 设置密码修改信息
            db_manager.execute(
                '''
                UPDATE user
                SET password_modified_at = CURRENT_TIMESTAMP, password_modified_by = ?
                WHERE id = ?
                ''',
                (data['username'], user_id)
            )
            
            # 7. 分配默认用户组
            user_group_manager.add_user_to_group(user_id, 'user')
            
            # 8. 记录用户行为
            enhanced_ai_engine.analyze_user_behavior(user_id, [{
                'type': 'registration',
                'timestamp': time.time(),
                'details': {'username': data['username'], 'email': data['email']}
            }])
            
            return {
                'status': 'success',
                'message': '注册成功',
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"注册用户失败: {str(e)}")
            return {
                'status': 'error',
                'message': f'注册失败: {str(e)}'
            }
    
    def _process_user_login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户登录流程
        
        Args:
            data: 登录数据
        
        Returns:
            处理结果
        """
        # 1. 验证输入数据
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in data:
                return {
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }
        
        # 2. 检查用户是否存在
        user = db_manager.fetch_one(
            'SELECT id, username, password, is_active FROM user WHERE username = ?',
            (data['username'],)
        )
        
        if not user:
            # 记录登录失败
            db_manager.execute(
                '''
                INSERT INTO login_attempts (username, ip_address, successful, attempt_time)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                (data['username'], data.get('ip', 'unknown'), 0)
            )
            
            return {
                'status': 'error',
                'message': '用户名或密码错误'
            }
        
        # 3. 检查用户是否激活
        is_active = user['is_active'] if isinstance(user, dict) else user[3]
        if not is_active:
            return {
                'status': 'error',
                'message': '账户已被禁用'
            }
        
        # 4. 验证密码
        try:
            import bcrypt
            stored_password = user['password'] if isinstance(user, dict) else user[2]
            if not bcrypt.checkpw(data['password'].encode('utf-8'), stored_password.encode('utf-8')):
                # 记录登录失败
                db_manager.execute(
                    '''
                    INSERT INTO login_attempts (username, ip_address, successful, attempt_time)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ''',
                    (data['username'], data.get('ip', 'unknown'), 0)
                )
                
                return {
                    'status': 'error',
                    'message': '用户名或密码错误'
                }
        except Exception as e:
            logger.error(f"验证密码失败: {str(e)}")
            return {
                'status': 'error',
                'message': '密码验证失败'
            }
        
        # 5. 记录登录成功
        user_id = user['id'] if isinstance(user, dict) else user[0]
        username = user['username'] if isinstance(user, dict) else user[1]
        
        # 记录登录历史
        db_manager.execute(
            '''
            INSERT INTO user_login_history (user_id, ip_address, user_agent, login_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            (user_id, data.get('ip', 'unknown'), data.get('user_agent', 'unknown'))
        )
        
        # 记录登录成功
        db_manager.execute(
            '''
            INSERT INTO login_attempts (username, ip_address, successful, attempt_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            (data['username'], data.get('ip', 'unknown'), 1)
        )
        
        # 6. 记录用户行为
        enhanced_ai_engine.analyze_user_behavior(user_id, [{
            'type': 'login',
            'timestamp': time.time(),
            'ip': data.get('ip', 'unknown'),
            'user_agent': data.get('user_agent', 'unknown')
        }])
        
        # 7. 获取用户组
        user_group = user_group_manager.get_user_group(user_id)
        
        return {
            'status': 'success',
            'message': '登录成功',
            'user_id': user_id,
            'username': username,
            'user_group': user_group
        }
    
    def _process_password_reset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理密码重置流程
        
        Args:
            data: 重置数据
        
        Returns:
            处理结果
        """
        # 1. 验证输入数据
        if 'email' in data:
            # 第一步：请求重置链接
            email = data['email']
            
            # 检查用户是否存在
            user = db_manager.fetch_one(
                'SELECT id, username FROM user WHERE email = ?',
                (email,)
            )
            
            if not user:
                return {
                    'status': 'error',
                    'message': '邮箱不存在'
                }
            
            # 生成重置令牌
            import secrets
            import datetime
            token = secrets.token_urlsafe(32)
            expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            
            # 更新用户表
            user_id = user['id'] if isinstance(user, dict) else user[0]
            username = user['username'] if isinstance(user, dict) else user[1]
            
            db_manager.execute(
                '''
                UPDATE user
                SET reset_token = ?, reset_token_expiry = ?
                WHERE id = ?
                ''',
                (token, expiry.isoformat(), user_id)
            )
            
            # 记录用户行为
            enhanced_ai_engine.analyze_user_behavior(user_id, [{
                'type': 'password_reset_request',
                'timestamp': time.time(),
                'email': email
            }])
            
            return {
                'status': 'success',
                'message': '重置链接已发送',
                'reset_token': token,
                'user_id': user_id
            }
        
        elif 'token' in data and 'new_password' in data:
            # 第二步：重置密码
            token = data['token']
            new_password = data['new_password']
            
            # 验证令牌
            user = db_manager.fetch_one(
                'SELECT id, username FROM user WHERE reset_token = ? AND reset_token_expiry > ?',
                (token, datetime.datetime.utcnow().isoformat())
            )
            
            if not user:
                return {
                    'status': 'error',
                    'message': '无效的重置令牌或令牌已过期'
                }
            
            # 密码强度验证
            if len(new_password) < 8:
                return {
                    'status': 'error',
                    'message': '密码长度至少8位'
                }
            
            # 检查是否与历史密码相同
            user_id = user['id'] if isinstance(user, dict) else user[0]
            password_history = db_manager.fetch_all(
                'SELECT password_hash FROM password_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 3',
                (user_id,)
            )
            
            import bcrypt
            new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            for history in password_history:
                stored_hash = history['password_hash'] if isinstance(history, dict) else history[0]
                if bcrypt.checkpw(new_password.encode('utf-8'), stored_hash.encode('utf-8')):
                    return {
                        'status': 'error',
                        'message': '新密码不能与最近使用的密码相同'
                    }
            
            # 更新密码
            db_manager.execute(
                'UPDATE user SET password = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?',
                (new_password_hash.decode('utf-8'), user_id)
            )
            
            # 添加密码历史
            db_manager.execute(
                'INSERT INTO password_history (user_id, password_hash, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
                (user_id, new_password_hash.decode('utf-8'))
            )
            
            # 更新密码修改信息
            db_manager.execute(
                'UPDATE user SET password_modified_at = CURRENT_TIMESTAMP, password_modified_by = ? WHERE id = ?',
                ('system', user_id)
            )
            
            # 记录用户行为
            enhanced_ai_engine.analyze_user_behavior(user_id, [{
                'type': 'password_reset',
                'timestamp': time.time()
            }])
            
            return {
                'status': 'success',
                'message': '密码重置成功'
            }
        
        else:
            return {
                'status': 'error',
                'message': '缺少必要字段'
            }
    
    def _process_exam_taking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理考试流程
        
        Args:
            data: 考试数据
        
        Returns:
            处理结果
        """
        if 'start' in data:
            # 开始考试
            user_id = data['user_id']
            exam_id = data['exam_id']
            
            # 开始考试
            exam_record_id = enhanced_exam_system.start_exam(user_id, exam_id)
            
            if exam_record_id == -1:
                return {
                    'status': 'error',
                    'message': '开始考试失败'
                }
            
            # 记录用户行为
            enhanced_ai_engine.analyze_user_behavior(user_id, [{
                'type': 'exam_started',
                'timestamp': time.time(),
                'exam_id': exam_id
            }])
            
            return {
                'status': 'success',
                'message': '考试开始',
                'exam_record_id': exam_record_id
            }
        
        elif 'submit' in data:
            # 提交考试
            exam_record_id = data['exam_record_id']
            answers = data['answers']
            
            # 提交考试
            result = enhanced_exam_system.submit_exam(exam_record_id, answers)
            
            if not result:
                return {
                    'status': 'error',
                    'message': '提交考试失败'
                }
            
            # 获取用户ID
            record = db_manager.fetch_one(
                'SELECT user_id, exam_id FROM exam_records WHERE id = ?',
                (exam_record_id,)
            )
            
            if record:
                user_id = record['user_id'] if isinstance(record, dict) else record[0]
                exam_id = record['exam_id'] if isinstance(record, dict) else record[1]
                
                # 记录用户行为
                enhanced_ai_engine.analyze_user_behavior(user_id, [{
                    'type': 'exam_completed',
                    'timestamp': time.time(),
                    'exam_id': exam_id,
                    'score': result['score']
                }])
                
                # 预测用户表现
                prediction = enhanced_ai_engine.predict_user_performance(user_id, exam_id)
                result['prediction'] = prediction
            
            return {
                'status': 'success',
                'message': '考试提交成功',
                'result': result
            }
        
        else:
            return {
                'status': 'error',
                'message': '无效的考试操作'
            }
    
    def _process_user_group_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户组管理流程
        
        Args:
            data: 管理数据
        
        Returns:
            处理结果
        """
        if 'add' in data:
            # 添加用户到组
            user_id = data['user_id']
            group_name = data['group_name']
            
            # 检查用户是否存在
            user = db_manager.fetch_one(
                'SELECT id FROM user WHERE id = ?',
                (user_id,)
            )
            
            if not user:
                return {
                    'status': 'error',
                    'message': '用户不存在'
                }
            
            # 添加用户到组
            success = user_group_manager.add_user_to_group(user_id, group_name)
            
            if not success:
                return {
                    'status': 'error',
                    'message': '添加用户到组失败'
                }
            
            # 记录用户行为
            enhanced_ai_engine.analyze_user_behavior(user_id, [{
                'type': 'group_assigned',
                'timestamp': time.time(),
                'group_name': group_name
            }])
            
            return {
                'status': 'success',
                'message': f'用户已添加到 {group_name} 组'
            }
        
        elif 'remove' in data:
            # 从组中移除用户
            user_id = data['user_id']
            
            # 检查用户是否存在
            user = db_manager.fetch_one(
                'SELECT id FROM user WHERE id = ?',
                (user_id,)
            )
            
            if not user:
                return {
                    'status': 'error',
                    'message': '用户不存在'
                }
            
            # 移除用户从组
            success = user_group_manager.remove_user_from_group(user_id)
            
            if not success:
                return {
                    'status': 'error',
                    'message': '从组中移除用户失败'
                }
            
            # 记录用户行为
            enhanced_ai_engine.analyze_user_behavior(user_id, [{
                'type': 'group_removed',
                'timestamp': time.time()
            }])
            
            return {
                'status': 'success',
                'message': '用户已从组中移除'
            }
        
        elif 'get' in data:
            # 获取用户组
            user_id = data['user_id']
            
            # 检查用户是否存在
            user = db_manager.fetch_one(
                'SELECT id FROM user WHERE id = ?',
                (user_id,)
            )
            
            if not user:
                return {
                    'status': 'error',
                    'message': '用户不存在'
                }
            
            # 获取用户组
            group_name = user_group_manager.get_user_group(user_id)
            
            return {
                'status': 'success',
                'message': '获取用户组成功',
                'group_name': group_name
            }
        
        else:
            return {
                'status': 'error',
                'message': '无效的用户组操作'
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态
        """
        try:
            # 获取用户统计
            user_stats = db_manager.fetch_one(
                'SELECT COUNT(*) as total_users, SUM(is_active) as active_users FROM user'
            )
            
            # 获取考试统计
            exam_stats = db_manager.fetch_one(
                'SELECT COUNT(*) as total_exams, SUM(is_active) as active_exams FROM exams'
            )
            
            # 获取登录统计
            try:
                login_stats = db_manager.fetch_one(
                    '''
                    SELECT 
                        COUNT(*) as total_logins,
                        SUM(successful) as successful_logins
                    FROM login_attempts
                    WHERE attempt_time > datetime('now', '-7 days')
                    '''
                )
            except Exception as e:
                # 如果表结构不匹配，使用默认值
                login_stats = None
            
            # 获取AI洞察
            ai_insights = enhanced_ai_engine.get_ai_insights()
            
            # 处理登录统计为None的情况
            login_stats_data = {
                'total_logins': 0,
                'successful_logins': 0
            }
            if login_stats:
                login_stats_data = {
                    'total_logins': login_stats['total_logins'] if isinstance(login_stats, dict) else login_stats[0],
                    'successful_logins': login_stats['successful_logins'] if isinstance(login_stats, dict) else login_stats[1]
                }
            
            return {
                'status': 'success',
                'system_status': 'running',
                'user_stats': {
                    'total_users': user_stats['total_users'] if isinstance(user_stats, dict) else user_stats[0],
                    'active_users': user_stats['active_users'] if isinstance(user_stats, dict) else user_stats[1]
                },
                'exam_stats': {
                    'total_exams': exam_stats['total_exams'] if isinstance(exam_stats, dict) else exam_stats[0],
                    'active_exams': exam_stats['active_exams'] if isinstance(exam_stats, dict) else exam_stats[1]
                },
                'login_stats': login_stats_data,
                'ai_insights': ai_insights
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {
                'status': 'error',
                'message': f'获取系统状态失败: {str(e)}'
            }

# 创建全局系统逻辑管理器实例
system_logic_manager = SystemLogicManager()
# 初始化业务流程
system_logic_manager.initialize_business_processes()
