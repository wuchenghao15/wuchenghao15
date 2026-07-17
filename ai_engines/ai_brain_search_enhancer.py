# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI脑库增强搜索功能
提供更强大的知识搜索和推荐能力
"""

import json
import sqlite3
from contextlib import contextmanager
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

class DatabaseManager:
    """简单的数据库管理器,避免导入完整的Flask应用"""

    @staticmethod
    def fetch_all(query, params=None):
        """执行查询并返回所有结果"""
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            return cursor.fetchall()

    @staticmethod
    def fetch_one(query, params=None):
        """执行查询并返回单个结果"""
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            return cursor.fetchone()

    @staticmethod
    def execute(query, params=None):
        """执行SQL语句"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            conn.commit()

class AIBrainKnowledge:
    """简化版AI脑库知识模型,避免导入完整的Flask应用"""
    
    @staticmethod
    def get_by_id(knowledge_id):
        """获取单个知识项"""
        query = "SELECT * FROM ai_brain_knowledge WHERE knowledge_id = ?"
        row = DatabaseManager.fetch_one(query, [knowledge_id])
        if row:
            return SimpleKnowledgeItem(dict(row))
        return None

    @staticmethod
    def filter(where_clause="1=1", where_params=None, order_by=None, limit=None):
        """过滤知识项"""
        query = f"SELECT * FROM ai_brain_knowledge WHERE {where_clause}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"

        rows = DatabaseManager.fetch_all(query, where_params)
        return [SimpleKnowledgeItem(dict(row)) for row in rows]

class SimpleKnowledgeItem:
    """简化版知识项"""

    def __init__(self, data):
        self.data = data

    @property
    def tags(self):
        """获取标签列表"""
        tags_str = self.data.get('tags')
        if tags_str:
            try:
                return json.loads(tags_str)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def to_dict(self):
        """转换为字典"""
        result = dict(self.data)
        result['tags'] = self.tags
        return result

db_manager = DatabaseManager()

class AIBrainSearchEnhancer:
    """AI脑库搜索增强器"""
    
    @staticmethod
    def advanced_search(keyword, knowledge_type=None, source=None, tags=None, limit=10):
        """高级搜索功能"""
        query = "SELECT * FROM ai_brain_knowledge WHERE is_active = ? AND (title LIKE ? OR content LIKE ?)"
        params = [True, f"%{keyword}%", f"%{keyword}%"]

        if knowledge_type:
            query += " AND knowledge_type = ?"
            params.append(knowledge_type)

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
        params.append(limit)

        rows = db_manager.fetch_all(query, params)
        knowledge_items = [SimpleKnowledgeItem(dict(row)) for row in rows]

        if tags:
            filtered_items = []
            for item in knowledge_items:
                if any(tag in item.tags for tag in tags):
                    filtered_items.append(item)
            knowledge_items = filtered_items

        return knowledge_items

    @staticmethod
    def get_popular(limit=10):
        """获取热门知识"""
        query = "SELECT * FROM ai_brain_knowledge WHERE is_active = ? ORDER BY priority DESC, created_at DESC LIMIT ?"
        params = [True, limit]
        rows = db_manager.fetch_all(query, params)
        return [SimpleKnowledgeItem(dict(row)) for row in rows]

    @staticmethod
    def get_related(knowledge_id, limit=5):
        """获取相关知识"""
        current_query = "SELECT * FROM ai_brain_knowledge WHERE knowledge_id = ? AND is_active = ?"
        current_row = db_manager.fetch_one(current_query, [knowledge_id, True])
        if not current_row:
            return []

        current_item = SimpleKnowledgeItem(dict(current_row))

        if not current_item.tags:
            return []

        tag_conditions = " OR ".join(["tags LIKE ?" for _ in current_item.tags])
        tag_params = [f"%{tag}%" for tag in current_item.tags]

        query = f"SELECT * FROM ai_brain_knowledge WHERE is_active = ? AND knowledge_id != ? AND ({tag_conditions}) ORDER BY priority DESC, created_at DESC LIMIT ?"
        params = [True, knowledge_id] + tag_params + [limit]

        rows = db_manager.fetch_all(query, params)
        return [SimpleKnowledgeItem(dict(row)) for row in rows]

    @staticmethod
    def get_statistics():
        """获取知识统计信息"""
        type_stats = db_manager.fetch_all(
            "SELECT knowledge_type, COUNT(*) as count FROM ai_brain_knowledge WHERE is_active = ? GROUP BY knowledge_type",
            [True]
        )

        source_stats = db_manager.fetch_all(
            "SELECT source, COUNT(*) as count FROM ai_brain_knowledge WHERE is_active = ? GROUP BY source",
            [True]
        )

        total = db_manager.fetch_one(
            "SELECT COUNT(*) as count FROM ai_brain_knowledge WHERE is_active = ?",
            [True]
        )

        recent = db_manager.fetch_one(
            "SELECT COUNT(*) as count FROM ai_brain_knowledge WHERE is_active = ? AND created_at >= datetime('now', '-7 days')",
            [True]
        )

        return {
            'total_knowledge': total['count'] if total else 0,
            'recent_additions': recent['count'] if recent else 0,
            'type_distribution': {row['knowledge_type']: row['count'] for row in type_stats} if type_stats else {},
            'source_distribution': {row['source']: row['count'] for row in source_stats} if source_stats else {}
        }
