# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
AI脑库增强搜索功能
提供更强大的知识搜索和推荐能力
r"""

import json
import sqlite3
from contextlib import contextmanager
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), r'app.db')

class DatabaseManager:
    r"""简单的数据库管理器,避免导入完整的Flask应用r"""

    @staticmethod
    def fetch_all(query, params=None):
        r"""执行查询并返回所有结果r"""
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            return cursor.fetchall()

    @staticmethod
    def fetch_one(query, params=None):
        r"""执行查询并返回单个结果r"""
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            return cursor.fetchone()

    @staticmethod
    def execute(query, params=None):
        r"""执行SQL语句r"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            conn.commit()

class AIBrainKnowledge:
    r"""简化版AI脑库知识模型,避免导入完整的Flask应用r"""

    @staticmethod
    def get_by_id(knowledge_id):
        r"""获取单个知识项r"""
        query = r"SELECT * FROM ai_brain_knowledge WHERE knowledge_id = ?"
        row = DatabaseManager.fetch_one(query, [knowledge_id])
        if row:
            return SimpleKnowledgeItem(dict(row))
        return None

    @staticmethod
    def filter(where_clause=r"1=1", where_params=None, order_by=None, limit=None):
        r"""过滤知识项r"""
        query = fr"SELECT * FROM ai_brain_knowledge WHERE {where_clause}"
        if order_by:
            query += fr" ORDER BY {order_by}"
        if limit:
            query += fr" LIMIT {limit}"

        rows = DatabaseManager.fetch_all(query, where_params)
        return [SimpleKnowledgeItem(dict(row)) for row in rows]

class SimpleKnowledgeItem:
    r"""简化版知识项r"""

    def __init__(self, data):
        self.data = data

    @property
    def tags(self):
        r"""获取标签列表r"""
        tags_str = self.data.get(r'tags')
        if tags_str:
            try:
                return json.loads(tags_str)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def to_dict(self):
        r"""转换为字典r"""
        result = dict(self.data)
        result[r'tags'] = self.tags
        return result

db_manager = DatabaseManager()

class AIBrainSearchEnhancer:
    r"""AI脑库搜索增强器r"""

    @staticmethod
    def advanced_search(keyword, knowledge_type=None, source=None, tags=None, limit=10):
        r"""高级搜索功能r"""
        query = r"SELECT * FROM ai_brain_knowledge WHERE is_active = ? AND (title LIKE ? OR content LIKE ?)"
        params = [True, fr"%{keyword}%", fr"%{keyword}%"]

        if knowledge_type:
            query += r" AND knowledge_type = ?"
            params.append(knowledge_type)

        if source:
            query += r" AND source = ?"
            params.append(source)

        query += r" ORDER BY priority DESC, created_at DESC LIMIT ?"
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
        r"""获取热门知识r"""
        query = r"SELECT * FROM ai_brain_knowledge WHERE is_active = ? ORDER BY priority DESC, created_at DESC LIMIT ?"
        params = [True, limit]
        rows = db_manager.fetch_all(query, params)
        return [SimpleKnowledgeItem(dict(row)) for row in rows]

    @staticmethod
    def get_related(knowledge_id, limit=5):
        r"""获取相关知识r"""
        current_query = r"SELECT * FROM ai_brain_knowledge WHERE knowledge_id = ? AND is_active = ?"
        current_row = db_manager.fetch_one(current_query, [knowledge_id, True])
        if not current_row:
            return []

        current_item = SimpleKnowledgeItem(dict(current_row))

        if not current_item.tags:
            return []

        tag_conditions = r" OR ".join([r"tags LIKE ?" for _ in current_item.tags])
        tag_params = [fr"%{tag}%" for tag in current_item.tags]

        query = fr"SELECT * FROM ai_brain_knowledge WHERE is_active = ? AND knowledge_id != ? AND ({tag_conditions}) ORDER BY priority DESC, created_at DESC LIMIT ?"
        params = [True, knowledge_id] + tag_params + [limit]

        rows = db_manager.fetch_all(query, params)
        return [SimpleKnowledgeItem(dict(row)) for row in rows]

    @staticmethod
    def get_statistics():
        r"""获取知识统计信息r"""
        type_stats = db_manager.fetch_all(
            r"SELECT knowledge_type, COUNT(*) as count FROM ai_brain_knowledge WHERE is_active = ? GROUP BY knowledge_type",
            [True]
        )

        source_stats = db_manager.fetch_all(
            r"SELECT source, COUNT(*) as count FROM ai_brain_knowledge WHERE is_active = ? GROUP BY source",
            [True]
        )

        total = db_manager.fetch_one(
            r"SELECT COUNT(*) as count FROM ai_brain_knowledge WHERE is_active = ?",
            [True]
        )

        recent = db_manager.fetch_one(
            "SELECT COUNT(*) as count FROM ai_brain_knowledge WHERE is_active = ? AND created_at >= datetime(r'now', r'-7 days')",
            [True]
        )

        return {
            r'total_knowledge': total[r'count'] if total else 0,
            r'recent_additions': recent[r'count'] if recent else 0,
            r'type_distribution': {row[r'knowledge_type']: row[r'count'] for row in type_stats} if type_stats else {},
            r'source_distribution': {row[r'source']: row[r'count'] for row in source_stats} if source_stats else {}
        }
