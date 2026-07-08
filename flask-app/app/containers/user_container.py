# -*- coding: utf-8 -*-
"""
用户容器模块 - 用户数据管理
"""

class UserContainer:
    def __init__(self):
        self.users = {}
        self.stats = {
            'total_users': 0,
            'active_users': 0,
            'guest_users': 0
        }
    
    def get_user(self, user_id):
        return self.users.get(user_id)
    
    def add_user(self, user_id, user_data):
        self.users[user_id] = user_data
    
    def remove_user(self, user_id):
        if user_id in self.users:
            del self.users[user_id]
    
    def get_all_users(self):
        return list(self.users.values())