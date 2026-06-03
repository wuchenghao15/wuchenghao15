# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
新学习系统核心模型
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from app.utils.logging import logger
import logging

class LearningSystem:
    """学习系统主类"""
    
    def __init__(self):
        self.courses = []
        self.user_progress = {}
        logger.info("学习系统初始化完成")
    
    def get_courses(self):
        return self.courses
    
    def get_progress(self, user_id):
        return self.user_progress.get(user_id, {})
