#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""登录逻辑模块"""
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
logger = logging.getLogger(__name__)

class LoginLogic:
    def __init__(self):
        self.sessions = {}
        self.users = {}
        self.max_login_attempts = 5
        self.login_attempts = {}
        self.session_timeout = 3600
        logger.info("登录逻辑处理器初始化完成")

    def register_user(self, username: str, password: str, email: str = ""):
        if username in self.users:
            return {'success': False, 'message': '用户名已存在'}
        hashed_password = self._hash_password(password)
        self.users[username] = {
            'password': hashed_password,
            'email': email,
            'created_at': datetime.now().isoformat(),
            'role': 'user',
            'active': True
        }
        logger.info(f"用户注册成功: {username}")
        return {'success': True, 'message': '注册成功'}

    def login(self, username: str, password: str) -> Dict[str, any]:
        if self.login_attempts.get(username, 0) >= self.max_login_attempts:
            return {'success': False, 'message': '登录尝试次数过多'}
        if username not in self.users:
            self._record_login_attempt(username)
            return {'success': False, 'message': '用户名或密码错误'}
        user = self.users[username]
        if not user.get('active', True):
            return {'success': False, 'message': '用户已被禁用'}
        if self._hash_password(password) != user['password']:
            return {'success': False, 'message': '用户名或密码错误'}
            del self.login_attempts[username]
        session_id = self._create_session(username)
        logger.info(f"用户登录成功: {username}")
        return {
            'success': True, 'message': '登录成功',
            'session_id': session_id,
            'user': {'username': username, 'role': user['role'], 'email': user['email']}

    def logout(self, session_id: str) -> Dict[str, any]:
        if session_id in self.sessions:
            username = self.sessions[session_id]['username']
            del self.sessions[session_id]
            logger.info(f"用户登出: {username}")
            return {'success': True, 'message': '登出成功'}
        return {'success': False, 'message': '无效的会话'}

    def validate_session(self, session_id: str) -> Optional[Dict[str, any]]:
        if session_id not in self.sessions:
            return None
        session = self.sessions[session_id]
        if datetime.now() > session['expires_at']:
            del self.sessions[session_id]
            return None
        session['expires_at'] = datetime.now() + timedelta(seconds=self.session_timeout)

        return hashlib.sha256(password.encode()).hexdigest()

    def _create_session(self, username: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'username': username,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=self.session_timeout),
            'last_activity': datetime.now()
        return session_id

    def _record_login_attempt(self, username: str):
        self.login_attempts[username] = self.login_attempts.get(username, 0) + 1
        logger.warning(f"登录尝试失败: {username}")

    def get_user_by_session(self, session_id: str) -> Optional[Dict[str, any]]:
        session = self.validate_session(session_id)
        if session:
            return self.users.get(session['username'])
        return None

login_logic = LoginLogic()

def init_login_logic():
    if 'admin' not in login_logic.users:
        login_logic.register_user('admin', 'admin123', 'admin@example.com')
        login_logic.users['admin']['role'] = 'admin'
    logger.info("登录逻辑初始化完成")

if __name__ == "__main__":
    init_login_logic()
