# -*- coding: utf-8 -*-
"""
权限模型模块
"""

class Permission:
    def __init__(self, id=None, name=None, description=None, resource=None, action=None):
        self.id = id
        self.name = name
        self.description = description
        self.resource = resource
        self.action = action
    
    @staticmethod
    def get_all():
        return []
    
    @staticmethod
    def get_by_id(permission_id):
        return None
    
    @staticmethod
    def create(data):
        return Permission(id=1, **data)