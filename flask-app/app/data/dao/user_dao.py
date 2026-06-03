# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据访问对象
"""

from typing import Dict, Optional, Any

from app.data.dao.base_dao import BaseDAO


class UserDAO(BaseDAO):
    """用户数据访问对象"""
    
    _table_name = 'users'
    _primary_key = 'id'
    
    @classmethod
    def find_by_username(cls, username: str) -> Optional[Dict]:
        """通过用户名查找用户"""
        try:
            query = "SELECT * FROM users WHERE username = ?"
            result = cls.get_db().fetch_one(query, (username,))
            return result
        except Exception as e:
            import logging
            logging.error(f"查找用户失败: {str(e)}")
            return None
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional[Dict]:
        """通过邮箱查找用户"""
        try:
            query = "SELECT * FROM users WHERE email = ?"
            result = cls.get_db().fetch_one(query, (email,))
            return result
        except Exception as e:
            import logging
            logging.error(f"查找用户失败: {str(e)}")
            return None
    
    @classmethod
    def list_active_users(cls, page: int = 1, page_size: int = 20) -> Dict:
        """列出活跃用户"""
        return cls.list({'status': 'active'}, page, page_size)
    
    @classmethod
    def list_by_role(cls, role: str, page: int = 1, page_size: int = 20) -> Dict:
        """按角色列出用户"""
        return cls.list({'role': role}, page, page_size)
    
    @classmethod
    def count_by_role(cls, role: str) -> int:
        """按角色统计用户数"""
        return cls.count({'role': role})
