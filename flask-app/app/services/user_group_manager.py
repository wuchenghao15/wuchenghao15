# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户组管理服务
"""

from app.utils.db import db_manager
from app.utils.logging import logger
import logging


class UserGroupManager:
    """用户组管理服务"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def add_user_to_group(self, user_id, group_name):
        """
        添加用户到组别,实现所有组的唯一性和排他性

        Args:
            user_id: 用户ID
            group_name: 组别名称

        Returns:
            bool: 是否添加成功
        """
        try:
            existing = db_manager.fetch_one(
                'SELECT id FROM user_groups WHERE user_id = ?',
                (user_id,)
            )

            if existing:
                db_manager.execute(
                    'UPDATE user_groups SET group_name = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                    (group_name, user_id)
                )
            else:
                db_manager.execute(
                    'INSERT INTO user_groups (user_id, group_name) VALUES (?, ?)',
                    (user_id, group_name)
                )

            logger.info(f"用户 {user_id} 已添加到组别 {group_name}")
            return True
        except Exception as e:
            logger.error(f"添加用户到组别失败: {str(e)}")
            return False

    def remove_user_from_group(self, user_id):
        """
        从组别中移除用户(删除用户的组记录)

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否移除成功
        """
        try:
            db_manager.execute(
                'DELETE FROM user_groups WHERE user_id = ?',
                (user_id,)
            )
            logger.info(f"用户 {user_id} 已从所有组别中移除")
            return True
        except Exception as e:
            logger.error(f"从组别移除用户失败: {str(e)}")
            return False

    def get_user_group(self, user_id):
        """
        获取用户所属组别

        Args:
            user_id: 用户ID

        Returns:
            str: 组别名称,如果用户不在任何组则返回None
        """
        try:
            result = db_manager.fetch_one(
                'SELECT group_name FROM user_groups WHERE user_id = ?',
                (user_id,)
            )
            if result:
                if isinstance(result, dict):
                    return result['group_name']
                else:
                    return result[0]
            return None
        except Exception as e:
            logger.error(f"获取用户组别失败: {str(e)}")
            return None

    def get_group_users(self, group_name):
        """
        获取组别中的所有用户

        Args:
            group_name: 组别名称

        Returns:
            list: 用户ID列表
        """
        try:
            users = db_manager.fetch_all(
                'SELECT user_id FROM user_groups WHERE group_name = ?',
                (group_name,)
            )

            if isinstance(users, list):
                if users and isinstance(users[0], dict):
                    return [user['user_id'] for user in users]
                else:
                    return [user[0] for user in users]
            return []
        except Exception as e:
            logger.error(f"获取组别用户失败: {str(e)}")
            return []

    def get_user_group_stats(self):
        """
        获取用户组别统计信息

        Returns:
            dict: 组别统计信息
        """
        try:
            stats = db_manager.fetch_all(
                'SELECT group_name, COUNT(*) as user_count FROM user_groups GROUP BY group_name'
            )

            result = {}
            if isinstance(stats, list):
                for item in stats:
                    if isinstance(item, dict):
                        result[item['group_name']] = item['user_count']
                    else:
                        result[item[0]] = item[1]
            return result
        except Exception as e:
            logger.error(f"获取组别统计失败: {str(e)}")
            return {}

    def get_all_groups(self):
        """
        获取所有组别

        Returns:
            list: 组别名称列表
        """
        try:
            groups = db_manager.fetch_all(
                'SELECT DISTINCT group_name FROM user_groups'
            )

            if isinstance(groups, list):
                if groups and isinstance(groups[0], dict):
                    return [group['group_name'] for group in groups]
                else:
                    return [group[0] for group in groups]
            return []
        except Exception as e:
            logger.error(f"获取所有组别失败: {str(e)}")
            return []

    def clear_group(self, group_name):
        """
        清空指定组别的所有用户

        Args:
            group_name: 组别名称

        Returns:
            bool: 是否清空成功
        """
        try:
            db_manager.execute(
                'DELETE FROM user_groups WHERE group_name = ?',
                (group_name,)
            )
            logger.info(f"组别 {group_name} 已清空")
            return True
        except Exception as e:
            logger.error(f"清空组别失败: {str(e)}")
            return False


user_group_manager = UserGroupManager()
