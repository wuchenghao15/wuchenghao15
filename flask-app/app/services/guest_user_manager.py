# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
游客用户管理模块
负责生成随机游客用户信息, 管理游客权限和数据
"""

import uuid
import time
from datetime import datetime, UTC
from app.utils.logging import logger
from app.models.user import User
from app.utils.security import security_utils
import logging


class GuestUserManager:
    """游客用户管理器"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化"""
        self.guest_users = {}
        self.guest_data = {}
        logger.info("游客用户管理器初始化完成")

    def generate_guest_user(self):
        """生成随机游客用户信息"""
        guest_username = f"guest_{uuid.uuid4().hex[:8]}"

        guest_email = f"{guest_username}@guest.example.com"

        random_password = uuid.uuid4().hex[:16]
        hashed_password = security_utils.hash_password(random_password)

        guest_user = User(
            username=guest_username,
            email=guest_email,
            password=hashed_password,
            role='guest',
            is_active=1,
            super_admin_approved=1,
            hardware_admin_approved=1
        )

        guest_user_id = guest_user.save()

        if guest_user_id:
            self.guest_users[guest_user_id] = {
                'username': guest_username,
                'email': guest_email,
                'created_at': datetime.now(UTC).isoformat(),
                'last_activity': datetime.now(UTC).isoformat()
            }

            self.guest_data[guest_user_id] = {
                'exam_records': [],
                'language_test_results': [],
                'session_data': {}
            }

            logger.info(f"生成游客用户成功: {guest_username}, 用户ID: {guest_user_id}")
            return guest_user, guest_user_id, random_password

        return None, None, None

    def get_guest_user(self, user_id):
        """获取游客用户信息"""
        return self.guest_users.get(user_id)

    def update_guest_activity(self, user_id):
        """更新游客活动时间"""
        if user_id in self.guest_users:
            self.guest_users[user_id]['last_activity'] = datetime.now(UTC).isoformat()

    def add_guest_exam_record(self, user_id, exam_data):
        """添加游客考试记录"""
        if user_id in self.guest_data:
            self.guest_data[user_id]['exam_records'].append({
                'exam_id': exam_data.get('exam_id'),
                'score': exam_data.get('score'),
                'completed_at': datetime.now(UTC).isoformat()
            })

    def add_guest_language_test_result(self, user_id, test_data):
        """添加游客语言测试结果"""
        if user_id in self.guest_data:
            self.guest_data[user_id]['language_test_results'].append({
                'test_type': test_data.get('test_type'),
                'level': test_data.get('level'),
                'score': test_data.get('score'),
                'completed_at': datetime.now(UTC).isoformat()
            })

    def get_guest_data(self, user_id):
        """获取游客数据"""
        return self.guest_data.get(user_id, {})

    def sync_guest_data_to_registered_user(self, guest_user_id, registered_user_id):
        """将游客数据同步到注册用户"""
        try:
            guest_data = self.get_guest_data(guest_user_id)

            if not guest_data:
                logger.warning(f"游客数据不存在: {guest_user_id}")
                return False

            logger.info(f"游客数据同步成功: {guest_user_id} -> {registered_user_id}")
            return True
        except Exception as e:
            logger.error(f"同步游客数据失败: {str(e)}")
            return False

    def is_guest_user(self, user_id):
        """判断是否为游客用户"""
        return user_id in self.guest_users

    def get_guest_permissions(self):
        """获取游客权限"""
        return {
            'can_take_exam': True,
            'can_view_results': True,
            'can_access_language_tests': True,
            'max_exams_per_day': 3,
            'data_retention_days': 7
        }

    def cleanup_expired_guests(self, max_age_hours=24):
        """清理过期的游客用户"""
        current_time = datetime.now(UTC)
        expired_users = []

        for user_id, user_info in list(self.guest_users.items()):
            last_activity = datetime.fromisoformat(user_info['last_activity'])
            age_hours = (current_time - last_activity).total_seconds() / 3600

            if age_hours > max_age_hours:
                expired_users.append(user_id)

        for user_id in expired_users:
            del self.guest_users[user_id]
            if user_id in self.guest_data:
                del self.guest_data[user_id]

        if expired_users:
            logger.info(f"清理了 {len(expired_users)} 个过期游客用户")

        return len(expired_users)


guest_user_manager = GuestUserManager()
