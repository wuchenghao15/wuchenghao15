# -*- coding: utf-8 -*-
"""
角色模型模块
"""

class Role:
    def __init__(self, id=None, name=None, description=None, permissions=None):
        self.id = id
        self.name = name
        self.description = description
        self.permissions = permissions or []
    
    @staticmethod
    def get_all():
        return []
    
    @staticmethod
    def get_by_id(role_id):
        return None
    
    @staticmethod
    def get_by_name(name):
        return Role(id=1, name=name, description=f'{name}角色')
    
    @staticmethod
    def create(data):
        return Role(id=1, **data)