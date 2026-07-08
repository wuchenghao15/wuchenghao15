# -*- coding: utf-8 -*-
"""
AI实例管理模块 - AI实例管理
"""

import logging

logger = logging.getLogger(__name__)

class AIInstanceManager:
    def __init__(self):
        self.instances = {}
    
    def get_instance(self, instance_id):
        return self.instances.get(instance_id)
    
    def list_instances(self):
        return list(self.instances.keys())
    
    def create_instance(self, instance_id, config):
        self.instances[instance_id] = config
        return True
    
    def delete_instance(self, instance_id):
        if instance_id in self.instances:
            del self.instances[instance_id]
            return True
        return False

ai_instance_manager = AIInstanceManager()