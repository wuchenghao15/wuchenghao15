# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户管理服务模块
负责用户管理和自动填充拓展功能
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UserManagerService:
    """用户管理服务类"""

    def __init__(self, db_path="app.db"):
        """初始化用户管理服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

        self.auto_fill_config = {
            "enabled": True,
            "fields": ["name", "email", "phone", "address", "company", "job_title"],
            "sync_with_browser": True,
            "auto_save": True
        }

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def get_user_profile(self, user_id):
        """获取用户个人信息"""
        if not self.connect():
            return None
        try:
            self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return None
        finally:
            self.close()

    def update_user_profile(self, user_id, profile_data):
        """更新用户个人信息"""
        if not self.connect():
            return False
        try:
            self.cursor.execute(
                "UPDATE users SET name = ?, email = ?, phone = ? WHERE id = ?",
                (profile_data.get('name'), profile_data.get('email'), profile_data.get('phone'), user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return False
        finally:
            self.close()

    def get_auto_fill_data(self, user_id, field_name=None):
        """获取自动填充数据"""
        if not self.connect():
            return []
        try:
            if field_name:
                self.cursor.execute(
                    "SELECT * FROM auto_fill_data WHERE user_id = ? AND field_name = ?",
                    (user_id, field_name)
                )
            else:
                self.cursor.execute("SELECT * FROM auto_fill_data WHERE user_id = ?", (user_id,))
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"获取自动填充数据失败: {str(e)}")
            return []
        finally:
            self.close()

    def set_user_preference(self, user_id, preference_key, preference_value, category=None):
        """设置用户偏好设置"""
        if not self.connect():
            return False
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value, category) VALUES (?, ?, ?, ?)",
                (user_id, preference_key, preference_value, category)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"设置用户偏好失败: {str(e)}")
            return False
        finally:
            self.close()

    def record_user_behavior(self, user_id, action_type, action_data=None, ip_address=None, user_agent=None):
        """记录用户行为"""
        if not self.connect():
            return False
        try:
            self.cursor.execute(
                "INSERT INTO user_behaviors (user_id, action_type, action_data, ip_address, user_agent, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, action_type, str(action_data), ip_address, user_agent, datetime.now().isoformat())
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"记录用户行为失败: {str(e)}")
            return False
        finally:
            self.close()

    def get_user_behavior(self, user_id, limit=50, offset=0):
        """获取用户行为记录"""
        if not self.connect():
            return []
        try:
            self.cursor.execute(
                "SELECT * FROM user_behaviors WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset)
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"获取用户行为记录失败: {str(e)}")
            return []
        finally:
            self.close()

    def get_auto_fill_suggestions(self, user_id, field_name, context=None):
        """获取自动填充建议"""
        if not self.connect():
            return []
        try:
            self.cursor.execute(
                "SELECT field_value FROM auto_fill_data WHERE user_id = ? AND field_name = ?",
                (user_id, field_name)
            )
            results = self.cursor.fetchall()
            return [r[0] for r in results]
        except Exception as e:
            logger.error(f"获取自动填充建议失败: {str(e)}")
            return []
        finally:
            self.close()

    def sync_with_browser(self, user_id, browser_data):
        """与浏览器同步自动填充数据"""
        if not self.auto_fill_config["sync_with_browser"]:
            return False
        if not self.connect():
            return False
        try:
            for field_name, field_value in browser_data.items():
                self.cursor.execute(
                    "INSERT OR REPLACE INTO auto_fill_data (user_id, field_name, field_value) VALUES (?, ?, ?)",
                    (user_id, field_name, field_value)
                )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"同步浏览器数据失败: {str(e)}")
            return False
        finally:
            self.close()
