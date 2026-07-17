#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI推荐引擎
提供个性化推荐和协同过滤功能
"""

import os
import sys
import json
import time
import math
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from collections import defaultdict

logger = print


class UserItem:
    """用户-物品交互"""

    def __init__(self, user_id: str, item_id: str, action: str = 'view',
                 rating: float = 0, timestamp: str = None):
        self.user_id = user_id
        self.item_id = item_id
        self.action = action  # view, like, purchase, rate
        self.rating = rating  # 0-5
        self.timestamp = timestamp or datetime.now().isoformat()


class ItemProfile:
    """物品画像"""

    def __init__(self, item_id: str, title: str = '', category: str = '',
                 tags: List[str] = None, description: str = ''):
        self.item_id = item_id
        self.title = title
        self.category = category
        self.tags = tags or []
        self.description = description
        self.view_count = 0
        self.like_count = 0
        self.avg_rating = 0.0
        self.rating_count = 0
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'item_id': self.item_id,
            'title': self.title,
            'category': self.category,
            'tags': self.tags,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'avg_rating': round(self.avg_rating, 2),
            'rating_count': self.rating_count
        }


class AIRecommendationEngine:
    """AI推荐引擎"""

    def __init__(self):
        self.item_profiles: Dict[str, ItemProfile] = {}
        self.user_history: Dict[str, List[UserItem]] = defaultdict(list)
        self.item_users: Dict[str, Set[str]] = defaultdict(set)
        self.is_running = False
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_items()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_rec_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL UNIQUE,
                    title TEXT,
                    category TEXT,
                    tags TEXT,
                    description TEXT,
                    view_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    avg_rating REAL DEFAULT 0,
                    rating_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_rec_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    rating REAL DEFAULT 0,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_rec_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    score REAL DEFAULT 0,
                    strategy TEXT DEFAULT 'hybrid',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_rec_interactions_user ON ai_rec_interactions(user_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_rec_interactions_item ON ai_rec_interactions(item_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[推荐引擎] 初始化数据库失败: {e}")

    def _register_default_items(self):
        """注册默认物品"""
        defaults = [
            ItemProfile('item_course_1', 'Python入门课程', 'course', ['python', '编程', '入门']),
            ItemProfile('item_course_2', 'AI机器学习', 'course', ['ai', 'ml', '进阶']),
            ItemProfile('item_course_3', 'Web开发实战', 'course', ['web', 'flask', '前端']),
            ItemProfile('item_doc_1', '系统使用手册', 'document', ['手册', '系统', '指南']),
            ItemProfile('item_doc_2', 'API开发文档', 'document', ['api', '开发', '接口']),
            ItemProfile('item_doc_3', '部署运维指南', 'document', ['部署', '运维', 'docker']),
            ItemProfile('item_exam_1', 'Python基础测试', 'exam', ['python', '测试', '基础']),
            ItemProfile('item_exam_2', 'AI知识测验', 'exam', ['ai', '测验', '知识']),
        ]

        for item in defaults:
            self.item_profiles[item.item_id] = item
            self._save_item_to_db(item)

    def _save_item_to_db(self, item: ItemProfile):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_rec_items
                (item_id, title, category, tags, description,
                 view_count, like_count, avg_rating, rating_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.item_id, item.title, item.category,
                json.dumps(item.tags), item.description,
                item.view_count, item.like_count,
                item.avg_rating, item.rating_count
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[推荐引擎] 保存物品失败: {e}")

    def _save_interaction_to_db(self, interaction: UserItem):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO ai_rec_interactions
                (user_id, item_id, action, rating, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                interaction.user_id, interaction.item_id,
                interaction.action, interaction.rating,
                interaction.timestamp
            ))

            conn.commit()
            conn.close()
        except:
            pass

    def add_item(self, item_id: str, title: str, category: str = '',
                 tags: List[str] = None, description: str = '') -> str:
        """添加物品"""
        item = ItemProfile(item_id, title, category, tags or [], description)

        with self.lock:
            self.item_profiles[item_id] = item

        self._save_item_to_db(item)
        return item_id

    def record_interaction(self, user_id: str, item_id: str,
                           action: str = 'view', rating: float = 0):
        """记录用户交互"""
        interaction = UserItem(user_id, item_id, action, rating)

        with self.lock:
            self.user_history[user_id].append(interaction)
            self.item_users[item_id].add(user_id)

            item = self.item_profiles.get(item_id)
            if item:
                if action == 'view':
                    item.view_count += 1
                elif action == 'like':
                    item.like_count += 1
                elif action == 'rate' and rating > 0:
                    total = item.avg_rating * item.rating_count + rating
                    item.rating_count += 1
                    item.avg_rating = total / item.rating_count

                self._save_item_to_db(item)

        self._save_interaction_to_db(interaction)

    def recommend(self, user_id: str, top_k: int = 10,
                  strategy: str = 'hybrid') -> List[Dict[str, Any]]:
        """推荐"""
        if strategy == 'collaborative':
            return self._collaborative_filtering(user_id, top_k)
        elif strategy == 'content':
            return self._content_based(user_id, top_k)
        elif strategy == 'popular':
            return self._popular_items(top_k)
        else:  # hybrid
            cf_results = self._collaborative_filtering(user_id, top_k * 2)
            content_results = self._content_based(user_id, top_k * 2)

            # 合并去重
            seen = set()
            merged = []

            for r in cf_results + content_results:
                if r['item_id'] not in seen:
                    seen.add(r['item_id'])
                    merged.append(r)

            return merged[:top_k]

    def _collaborative_filtering(self, user_id: str,
                                 top_k: int) -> List[Dict[str, Any]]:
        """协同过滤"""
        user_items = set(
            ui.item_id for ui in self.user_history.get(user_id, [])
        )

        if not user_items:
            return self._popular_items(top_k)

        # 找相似用户
        similar_users: Dict[str, float] = {}

        for other_user, interactions in self.user_history.items():
            if other_user == user_id:
                continue

            other_items = set(ui.item_id for ui in interactions)

            # Jaccard相似度
            intersection = user_items & other_items
            union = user_items | other_items

            if union:
                similarity = len(intersection) / len(union)
                if similarity > 0:
                    similar_users[other_user] = similarity

        if not similar_users:
            return self._popular_items(top_k)

        # 基于相似用户推荐
        item_scores: Dict[str, float] = defaultdict(float)

        for other_user, similarity in similar_users.items():
            for ui in self.user_history[other_user]:
                if ui.item_id not in user_items:
                    weight = similarity
                    if ui.action == 'like':
                        weight *= 2
                    elif ui.action == 'rate':
                        weight *= ui.rating / 5.0

                    item_scores[ui.item_id] += weight

        results = []
        for item_id, score in sorted(item_scores.items(),
                                     key=lambda x: x[1], reverse=True)[:top_k]:
            item = self.item_profiles.get(item_id)
            if item:
                results.append({
                    'item_id': item_id,
                    'title': item.title,
                    'category': item.category,
                    'score': round(score, 4),
                    'strategy': 'collaborative'
                })

        return results

    def _content_based(self, user_id: str,
                       top_k: int) -> List[Dict[str, Any]]:
        """基于内容的推荐"""
        user_history = self.user_history.get(user_id, [])

        if not user_history:
            return self._popular_items(top_k)

        # 获取用户偏好
        user_categories: Dict[str, int] = defaultdict(int)
        user_tags: Dict[str, int] = defaultdict(int)
        user_items = set()

        for ui in user_history:
            user_items.add(ui.item_id)
            item = self.item_profiles.get(ui.item_id)
            if item:
                user_categories[item.category] += 1
                for tag in item.tags:
                    user_tags[tag] += 1

        # 计算物品分数
        results = []

        for item_id, item in self.item_profiles.items():
            if item_id in user_items:
                continue

            score = 0.0

            # 分类匹配
            if item.category in user_categories:
                score += user_categories[item.category] * 0.3

            # 标签匹配
            for tag in item.tags:
                if tag in user_tags:
                    score += user_tags[tag] * 0.2

            # 热门度
            score += min(item.view_count / 100, 1.0) * 0.1
            score += min(item.like_count / 50, 1.0) * 0.1

            # 评分
            score += item.avg_rating / 5.0 * 0.3

            if score > 0:
                results.append({
                    'item_id': item_id,
                    'title': item.title,
                    'category': item.category,
                    'score': round(score, 4),
                    'strategy': 'content'
                })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def _popular_items(self, top_k: int) -> List[Dict[str, Any]]:
        """热门推荐"""
        items = sorted(self.item_profiles.values(),
                      key=lambda i: (i.view_count + i.like_count * 2 + i.avg_rating * 10),
                      reverse=True)

        return [{
            'item_id': i.item_id,
            'title': i.title,
            'category': i.category,
            'score': round(i.view_count + i.like_count * 2 + i.avg_rating * 10, 4),
            'strategy': 'popular'
        } for i in items[:top_k]]

    def get_items(self, category: str = None) -> List[Dict[str, Any]]:
        with self.lock:
            items = list(self.item_profiles.values())
            if category:
                items = [i for i in items if i.category == category]
            return [i.to_dict() for i in items]

    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        history = self.user_history.get(user_id, [])
        return [{
            'item_id': ui.item_id,
            'action': ui.action,
            'rating': ui.rating,
            'timestamp': ui.timestamp
        } for ui in history]

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total_users = len(self.user_history)
            total_items = len(self.item_profiles)
            total_interactions = sum(len(h) for h in self.user_history.values())

            return {
                'total_users': total_users,
                'total_items': total_items,
                'total_interactions': total_interactions,
                'avg_interactions_per_user': round(total_interactions / max(1, total_users), 2)
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_items': len(self.item_profiles),
            'total_users': len(self.user_history)
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[推荐引擎] 推荐引擎已启动")

    def stop(self):
        self.is_running = False
        logger(f"[推荐引擎] 推荐引擎已停止")


ai_recommendation_engine = AIRecommendationEngine()
