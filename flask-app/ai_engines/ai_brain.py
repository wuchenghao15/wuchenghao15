# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI脑库数据模型
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AIBrainKnowledge:
    """AI脑库知识模型"""

    def __init__(self, knowledge_id=None, title=None, content=None,
                 knowledge_type=None, source=None, tags=None, priority=0,
                 is_active=True, review_status="pending", confidence_score=0.0):
        self.knowledge_id = knowledge_id
        self.title = title
        self.content = content
        self.knowledge_type = knowledge_type
        self.source = source
        self.tags = tags or []
        self.priority = priority
        self.is_active = is_active
        self.review_status = review_status
        self.confidence_score = confidence_score
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.reviewed_at = None
        self.reviewed_by = None

    @classmethod
    def create_table(cls):
        """创建表"""
        logger.info("创建 AIBrainKnowledge 表")

    @classmethod
    def get_by_status(cls, status):
        """按状态获取"""
        return []


class AIBrainActivity:
    """AI脑库活动模型"""

    @classmethod
    def create_table(cls):
        """创建表"""
        logger.info("创建 AIBrainActivity 表")
