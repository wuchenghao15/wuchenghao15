#!/usr/bin/env python3
"""
游客用户管理模块
负责生成随机游客用户信息、管理游客权限和数据

import uuid
import time
from datetime import datetime, UTC
from app.utils.logging import logger
from app.models.user import User
from app.utils.security import security_utils

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
        self.guest_users = {}  # 内存中的游客用户信息，用于快速访问
        self.guest_data = {}   # 游客临时数据
        logger.info("游客用户管理器初始化完成")

    def generate_guest_user(self):
        """生成随机游客用户信息"""
        # 生成随机游客用户名
        guest_username = f"guest_{uuid.uuid4().hex[:8]}"

        # 为游客生成随机邮箱（游客专用格式）
        guest_email = f"{guest_username}@guest.example.com"

        # 为游客生成随机密码
        random_password = uuid.uuid4().hex[:16]
        hashed_password = security_utils.hash_password(random_password)

        # 创建游客用户记录
        guest_user = User(
            username=guest_username,
            email=guest_email,
            password=hashed_password,
            role='guest',  # 游客角色
            is_active=1,  # 自动激活
            super_admin_approved=1,  # 自动批准
            hardware_admin_approved=1  # 自动批准
        )

        # 保存游客用户到数据库
        guest_user_id = guest_user.save()

        if guest_user_id:
            # 将游客添加到内存中
            self.guest_users[guest_user_id] = {
                'username': guest_username,
                'email': guest_email,
                'created_at': datetime.now(UTC).isoformat(),
                'last_activity': datetime.now(UTC).isoformat()
            }

            # 初始化游客临时数据
            self.guest_data[guest_user_id] = {
                'exam_records': [],
                'language_test_results': [],
                'session_data': {}
            }

            logger.info(f"生成游客用户成功: {guest_username}, 用户ID: {guest_user_id}")
            return guest_user, guest_user_id, random_password
        else:
            logger.error("生成游客用户失败")
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
                'test_type': test_data.get('test_type'),
                'level': test_data.get('level'),
                'score': test_data.get('score'),
                'completed_at': datetime.now(UTC).isoformat()
            })
    def get_guest_data(self, user_id):
        return self.guest_data.get(user_id, {})

    def sync_guest_data_to_registered_user(self, guest_user_id, registered_user_id):
        """将游客数据同步到注册用户"""
        try:
            # 获取游客数据
            guest_data = self.get_guest_data(guest_user_id)

            if not guest_data:
                logger.warning(f"游客数据不存在: {guest_user_id}")
                return False

            # 同步考试记录
            if 'exam_records' in guest_data:
                for exam_record in guest_data['exam_records']:
                    try:
                        from app.utils.db import db_manager
                        # 检查记录是否已存在
                        existing = db_manager.fetch_one(
                            (registered_user_id, exam_record['exam_id'])
                        )
                            # 插入考试记录
                            db_manager.execute(
                                'INSERT INTO exam_records (user_id, exam_id, score, completed_at) VALUES (?, ?, ?, ?)',
                                (registered_user_id, exam_record['exam_id'], exam_record['score'], exam_record['completed_at'])
                            )
                    except Exception as exam_error:
                        logger.error(f"同步游客考试记录失败: {str(exam_error)}")

            # 同步语言测试结果
            if 'language_test_results' in guest_data:
                for test_result in guest_data['language_test_results']:
                    try:
                        from app.utils.db import db_manager
                        # 检查记录是否已存在
                        existing = db_manager.fetch_one(
                            'SELECT id FROM language_test_results WHERE user_id = ? AND test_type = ?',
                            (registered_user_id, test_result['test_type'])
                            # 插入语言测试结果
                            db_manager.execute(
                                (registered_user_id, test_result['test_type'], test_result['level'], test_result['score'], test_result['completed_at'])
                    except Exception as test_error:

            logger.info(f"游客数据同步到注册用户成功: 游客ID={guest_user_id}, 注册用户ID={registered_user_id}")
            return True
        except Exception as e:
            return False

        """清理游客用户数据"""
        try:
            # 从内存中删除游客信息
            if user_id in self.guest_users:
                del self.guest_users[user_id]

            if user_id in self.guest_data:
            # 从数据库中删除游客用户
            if user:
                logger.info(f"清理游客用户成功: {user_id}")

            return True
        except Exception as e:
            logger.error(f"清理游客用户失败: {str(e)}")
            return False

    def is_guest_user(self, user_id):
        """判断是否为游客用户"""
        return user_id in self.guest_users

    def get_guest_permissions(self):
        """获取游客权限"""
        return {
            'can_take_exams': True,  # 可以参加考试
            'can_take_language_test': True,  # 可以参加语言等级测试
            'can_access_dashboard': False,  # 不能访问仪表盘
            'can_manage_account': False,  # 不能管理账户
        }

# 创建游客用户管理器实例
