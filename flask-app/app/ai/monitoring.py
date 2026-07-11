# -*- coding: utf-8 -*-
"""
AI监控模块 - 系统监控和错误统计
"""

import logging

logger = logging.getLogger(__name__)

class AIMonitor:
    def __init__(self):
        self.error_count = 0
        self.errors = []
        self.error_by_type = {}
        self.error_by_component = {}
    
    def get_error_stats(self):
        return {
            'total_errors': self.error_count,
            'recent_errors': self.errors[-10:] if self.errors else [],
            'errors_by_type': self.error_by_type,
            'errors_by_component': self.error_by_component
        }
    
    def log_error(self, error_type=None, error_message=None, component=None, error_stack=None):
        self.error_count += 1
        if error_type:
            self.error_by_type[error_type] = self.error_by_type.get(error_type, 0) + 1
        if component:
            self.error_by_component[component] = self.error_by_component.get(component, 0) + 1
        
        error_info = {
            'timestamp': __import__('time').time(),
            'error_type': error_type,
            'error_message': error_message,
            'component': component,
            'error_stack': error_stack
        }
        self.errors.append(error_info)
        logger.error(f"[AI监控] [{component or 'unknown'}] [{error_type or 'unknown'}] {error_message}")

ai_monitor = AIMonitor()