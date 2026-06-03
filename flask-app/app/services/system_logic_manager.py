# -*- coding: utf-8 -*-
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
import sys


class SystemLogicManager:
    """系统逻辑管理器"""

    def __init__(self):
        """初始化系统逻辑管理器"""
        self.state_machines = {}
        self.business_processes = {}
        logger.info("系统逻辑管理器初始化完成")

    def initialize_business_processes(self):
        """初始化业务流程"""
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
            return {'success': False, 'error': f'未知的流程类型: {flow_type}'}

        try:
            result = self.business_processes[flow_type](data)
            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f"处理业务流程失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _process_user_registration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户注册流程"""
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not username or not password:
            return {'success': False, 'error': '用户名和密码不能为空'}

        try:
            existing = db_manager.fetch_one(
                'SELECT id FROM users WHERE username = ?',
                (username,)
            )
            if existing:
                return {'success': False, 'error': '用户名已存在'}

            db_manager.execute(
                'INSERT INTO users (username, password, email, created_at) VALUES (?, ?, ?, ?)',
                (username, password, email, datetime.datetime.now().isoformat())
            )

            return {'success': True, 'message': '注册成功'}
        except Exception as e:
            logger.error(f"用户注册失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _process_user_login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户登录流程"""
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'success': False, 'error': '用户名和密码不能为空'}

        try:
            user = db_manager.fetch_one(
                'SELECT id, username, password FROM users WHERE username = ?',
                (username,)
            )

            if not user:
                return {'success': False, 'error': '用户不存在'}

            if isinstance(user, dict):
                stored_password = user['password']
                user_id = user['id']
            else:
                stored_password = user[2]
                user_id = user[0]

            if stored_password != password:
                return {'success': False, 'error': '密码错误'}

            return {'success': True, 'user_id': user_id, 'username': username}
        except Exception as e:
            logger.error(f"用户登录失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _process_password_reset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理密码重置流程"""
        email = data.get('email')
        new_password = data.get('new_password')

        if not email or not new_password:
            return {'success': False, 'error': '邮箱和新密码不能为空'}

        try:
            user = db_manager.fetch_one(
                'SELECT id FROM users WHERE email = ?',
                (email,)
            )

            if not user:
                return {'success': False, 'error': '邮箱未注册'}

            db_manager.execute(
                'UPDATE users SET password = ?, updated_at = ? WHERE email = ?',
                (new_password, datetime.datetime.now().isoformat(), email)
            )

            return {'success': True, 'message': '密码重置成功'}
        except Exception as e:
            logger.error(f"密码重置失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _process_exam_taking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理考试流程"""
        user_id = data.get('user_id')
        exam_id = data.get('exam_id')
        answers = data.get('answers', [])

        if not user_id or not exam_id:
            return {'success': False, 'error': '缺少必要参数'}

        try:
            correct_count = 0
            total_count = len(answers)

            for answer in answers:
                question_id = answer.get('question_id')
                user_answer = answer.get('answer')

                question = db_manager.fetch_one(
                    'SELECT correct_answer FROM questions WHERE id = ?',
                    (question_id,)
                )

                if question:
                    correct_answer = question['correct_answer'] if isinstance(question, dict) else question[0]
                    is_correct = (user_answer == correct_answer)
                    if is_correct:
                        correct_count += 1

                    db_manager.execute(
                        'INSERT INTO exam_results (user_id, exam_id, question_id, user_answer, is_correct, created_at) VALUES (?, ?, ?, ?, ?, ?',
                        (user_id, exam_id, question_id, user_answer, is_correct, datetime.datetime.now().isoformat())
                    )

            score = (correct_count / total_count * 100) if total_count > 0 else 0

            return {
                'success': True,
                'score': score,
                'correct_count': correct_count,
                'total_count': total_count
            }
        except Exception as e:
            logger.error(f"考试处理失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _process_user_group_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户组管理流程"""
        action = data.get('action')
        user_id = data.get('user_id')
        group_name = data.get('group_name')

        if action == 'add':
            return {'success': user_group_manager.add_user_to_group(user_id, group_name)}
        elif action == 'remove':
            return {'success': user_group_manager.remove_user_from_group(user_id)}
        elif action == 'get':
            group = user_group_manager.get_user_group(user_id)
            return {'success': True, 'group': group}
        else:
            return {'success': False, 'error': f'未知的操作: {action}'}

    def register_state_machine(self, name: str, state_machine):
        """注册状态机"""
        self.state_machines[name] = state_machine
        logger.info(f"状态机 {name} 已注册")

    def get_state_machine(self, name: str):
        """获取状态机"""
        return self.state_machines.get(name)

    def execute_state_transition(self, machine_name: str, transition: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行状态转换"""
        machine = self.get_state_machine(machine_name)
        if not machine:
            return {'success': False, 'error': f'状态机 {machine_name} 不存在'}

        try:
            result = machine.transition(transition, data or {})
            return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f"状态转换失败: {str(e)}")
            return {'success': False, 'error': str(e)}


system_logic_manager = SystemLogicManager()
