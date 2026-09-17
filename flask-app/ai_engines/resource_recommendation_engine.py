# -*- coding: utf-8 -*-
"""
学习资源推荐引擎
基于学习画像的个性化学习资源推荐，包含协同过滤、内容匹配、知识图谱路径推荐
推荐策略：内容匹配(40%) + 协同过滤(35%) + 知识路径(15%) + 热度补充(10%)
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resource_recommendation_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ResourceRecommendationEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 资源类型
RESOURCE_TYPES = {
    'video': '视频',
    'article': '文章',
    'book': '图书',
    'exercise': '练习题',
    'course': '课程',
    'document': '文档',
    'audio': '音频',
    'interactive': '交互式'
}

# 难度等级
DIFFICULTY_LEVELS = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}


class ResourceRecommendationEngine:
    """学习资源推荐引擎 - 多策略个性化推荐"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._init_database()
        self._initialized = True
        logger.info("ResourceRecommendationEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 资源池主表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_resources (
                        resource_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        resource_type TEXT NOT NULL,
                        subject TEXT,
                        grade TEXT,
                        topic TEXT,
                        difficulty TEXT DEFAULT 'intermediate',
                        duration_minutes INTEGER DEFAULT 30,
                        url TEXT,
                        thumbnail_url TEXT,
                        author TEXT,
                        publisher TEXT,
                        language TEXT DEFAULT 'zh-CN',
                        tags TEXT DEFAULT '[]',
                        keywords TEXT,
                        content_vector TEXT,
                        quality_score REAL DEFAULT 0,
                        popularity_score REAL DEFAULT 0,
                        rating_avg REAL DEFAULT 0,
                        rating_count INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. 用户-资源交互表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_interactions (
                        interaction_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        interaction_type TEXT,
                        rating REAL DEFAULT 0,
                        duration_spent INTEGER DEFAULT 0,
                        progress REAL DEFAULT 0,
                        completed BOOLEAN DEFAULT 0,
                        bookmarked BOOLEAN DEFAULT 0,
                        feedback TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (resource_id) REFERENCES learning_resources(resource_id)
                    )
                ''')

                # 3. 推荐结果表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recommendations (
                        recommendation_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        strategy TEXT,
                        score REAL DEFAULT 0,
                        reason TEXT,
                        status TEXT DEFAULT 'pending',
                        clicked BOOLEAN DEFAULT 0,
                        clicked_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (resource_id) REFERENCES learning_resources(resource_id)
                    )
                ''')

                # 4. 资源评价表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_reviews (
                        review_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        rating REAL NOT NULL,
                        review_text TEXT,
                        helpful_count INTEGER DEFAULT 0,
                        reported BOOLEAN DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (resource_id) REFERENCES learning_resources(resource_id)
                    )
                ''')

                # 5. 推荐策略配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recommendation_config (
                        config_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        strategy_weights TEXT DEFAULT '{"content":0.4,"collaborative":0.35,"knowledge_path":0.15,"popularity":0.10}',
                        preferred_types TEXT DEFAULT '[]',
                        preferred_difficulty TEXT,
                        max_recommendations INTEGER DEFAULT 10,
                        enable_diversity BOOLEAN DEFAULT 1,
                        enable_explanation BOOLEAN DEFAULT 1,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_lr_subject ON learning_resources(subject)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_lr_topic ON learning_resources(topic)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ri_user ON resource_interactions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ri_resource ON resource_interactions(resource_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rec_user ON recommendations(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rr_resource ON resource_reviews(resource_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化资源推荐数据库失败: {e}")

    # ==================== 资源管理 ====================

    def add_resource(self, resource_id: str, title: str, resource_type: str,
                     subject: str = None, grade: str = None, topic: str = None,
                     difficulty: str = 'intermediate', duration_minutes: int = 30,
                     url: str = None, description: str = None, author: str = None,
                     publisher: str = None, tags: List[str] = None,
                     keywords: str = None, thumbnail_url: str = None) -> Dict[str, Any]:
        """添加学习资源"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO learning_resources
                        (resource_id, title, description, resource_type, subject, grade,
                         topic, difficulty, duration_minutes, url, thumbnail_url,
                         author, publisher, tags, keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (resource_id, title, description, resource_type, subject, grade,
                          topic, difficulty, duration_minutes, url, thumbnail_url,
                          author, publisher,
                          json.dumps(tags or [], ensure_ascii=False), keywords))
                    conn.commit()

                return {'success': True, 'resource_id': resource_id, 'message': '资源已添加'}
            except Exception as e:
                logger.error(f"添加资源失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """获取资源详情"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_resources WHERE resource_id = ?',
                               (resource_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '资源不存在'}

                cols = ['resource_id', 'title', 'description', 'resource_type', 'subject',
                        'grade', 'topic', 'difficulty', 'duration_minutes', 'url',
                        'thumbnail_url', 'author', 'publisher', 'language', 'tags',
                        'keywords', 'content_vector', 'quality_score', 'popularity_score',
                        'rating_avg', 'rating_count', 'view_count', 'like_count',
                        'status', 'created_at', 'updated_at']
                result = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}

                # 解析 tags
                if result.get('tags'):
                    try:
                        result['tags'] = json.loads(result['tags'])
                    except Exception:
                        result['tags'] = []

                # 更新浏览次数
                cursor.execute('UPDATE learning_resources SET view_count = view_count + 1 WHERE resource_id = ?',
                               (resource_id,))
                conn.commit()

                return {'success': True, 'resource': result}
        except Exception as e:
            logger.error(f"获取资源失败: {e}")
            return {'success': False, 'error': str(e)}

    def record_interaction(self, user_id: str, resource_id: str,
                           interaction_type: str, rating: float = 0,
                           duration_spent: int = 0, progress: float = 0,
                           completed: bool = False, bookmarked: bool = False,
                           feedback: str = None) -> Dict[str, Any]:
        """记录用户与资源的交互"""
        with self._lock:
            try:
                interaction_id = f"int_{int(time.time() * 1000)}_{user_id}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO resource_interactions
                        (interaction_id, user_id, resource_id, interaction_type,
                         rating, duration_spent, progress, completed, bookmarked, feedback)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (interaction_id, user_id, resource_id, interaction_type,
                          rating, duration_spent, progress, 1 if completed else 0,
                          1 if bookmarked else 0, feedback))
                    conn.commit()

                    # 异步更新资源评分和热度
                    self._update_resource_stats(cursor, conn, resource_id)

                return {'success': True, 'interaction_id': interaction_id, 'message': '交互已记录'}
            except Exception as e:
                logger.error(f"记录交互失败: {e}")
                return {'success': False, 'error': str(e)}

    def _update_resource_stats(self, cursor, conn, resource_id: str):
        """更新资源评分和热度"""
        try:
            cursor.execute('''
                SELECT AVG(rating), COUNT(*) FROM resource_interactions
                WHERE resource_id = ? AND rating > 0
            ''', (resource_id,))
            row = cursor.fetchone()
            if row and row[1] > 0:
                avg_rating = row[0]
                count = row[1]
                cursor.execute('''
                    UPDATE learning_resources
                    SET rating_avg = ?, rating_count = ?,
                        popularity_score = ? * 0.7 + view_count * 0.001 + like_count * 0.05
                    WHERE resource_id = ?
                ''', (avg_rating, count, avg_rating, resource_id))
                conn.commit()
        except Exception as e:
            logger.error(f"更新资源统计失败: {e}")

    # ==================== 推荐核心 ====================

    def recommend(self, user_id: str, subject: str = None, limit: int = 10,
                  strategy: str = 'hybrid') -> Dict[str, Any]:
        """生成个性化推荐（核心方法）"""
        with self._lock:
            try:
                # 1. 获取用户配置
                config = self._get_user_config(user_id)
                weights = config.get('strategy_weights', {
                    'content': 0.4, 'collaborative': 0.35,
                    'knowledge_path': 0.15, 'popularity': 0.10
                })

                # 2. 获取候选资源（已过滤用户已交互的）
                candidates = self._get_candidate_resources(user_id, subject, limit * 5)
                if not candidates:
                    return {'success': True, 'user_id': user_id, 'recommendations': [],
                            'message': '暂无可用资源'}

                # 3. 多策略打分
                scores = defaultdict(lambda: {'score': 0.0, 'reasons': []})

                if strategy in ('hybrid', 'content'):
                    content_scores = self._content_based_score(user_id, candidates)
                    for rid, sc in content_scores.items():
                        scores[rid]['score'] += sc * weights.get('content', 0.4)
                        if sc > 0:
                            scores[rid]['reasons'].append(f"内容匹配({round(sc, 2)})")

                if strategy in ('hybrid', 'collaborative'):
                    collab_scores = self._collaborative_filter_score(user_id, candidates)
                    for rid, sc in collab_scores.items():
                        scores[rid]['score'] += sc * weights.get('collaborative', 0.35)
                        if sc > 0:
                            scores[rid]['reasons'].append(f"相似用户推荐({round(sc, 2)})")

                if strategy in ('hybrid', 'knowledge_path'):
                    path_scores = self._knowledge_path_score(user_id, candidates)
                    for rid, sc in path_scores.items():
                        scores[rid]['score'] += sc * weights.get('knowledge_path', 0.15)
                        if sc > 0:
                            scores[rid]['reasons'].append(f"学习路径匹配({round(sc, 2)})")

                if strategy in ('hybrid', 'popularity'):
                    pop_scores = self._popularity_score(candidates)
                    for rid, sc in pop_scores.items():
                        scores[rid]['score'] += sc * weights.get('popularity', 0.10)
                        if sc > 0:
                            scores[rid]['reasons'].append(f"热门资源({round(sc, 2)})")

                # 4. 排序并取 Top-N
                sorted_recs = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
                top_recs = sorted_recs[:limit]

                # 5. 多样性优化（不同类型/主题分散）
                if config.get('enable_diversity', True):
                    top_recs = self._diversify(top_recs, candidates, limit)

                # 6. 保存推荐结果
                recommendations = []
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    for rid, score_info in top_recs:
                        reason = '; '.join(score_info['reasons']) or '综合推荐'
                        rec_id = f"rec_{int(time.time() * 1000)}_{rid[:8]}"
                        cursor.execute('''
                            INSERT INTO recommendations
                            (recommendation_id, user_id, resource_id, strategy, score, reason)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (rec_id, user_id, rid, strategy, round(score_info['score'], 4), reason))

                        # 获取资源详情
                        cursor.execute('SELECT title, resource_type, subject, topic, difficulty, duration_minutes, thumbnail_url FROM learning_resources WHERE resource_id = ?',
                                       (rid,))
                        r = cursor.fetchone()
                        if r:
                            recommendations.append({
                                'resource_id': rid,
                                'title': r[0],
                                'resource_type': r[1],
                                'subject': r[2],
                                'topic': r[3],
                                'difficulty': r[4],
                                'duration_minutes': r[5],
                                'thumbnail_url': r[6],
                                'score': round(score_info['score'], 4),
                                'reason': reason
                            })
                    conn.commit()

                return {
                    'success': True,
                    'user_id': user_id,
                    'strategy': strategy,
                    'recommendations': recommendations,
                    'count': len(recommendations)
                }
            except Exception as e:
                logger.error(f"生成推荐失败: {e}")
                return {'success': False, 'error': str(e)}

    def _get_user_config(self, user_id: str) -> Dict[str, Any]:
        """获取用户推荐配置"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM recommendation_config WHERE user_id = ? OR user_id IS NULL ORDER BY user_id IS NULL LIMIT 1',
                               (user_id,))
                row = cursor.fetchone()
                if row:
                    cols = ['config_id', 'user_id', 'strategy_weights', 'preferred_types',
                            'preferred_difficulty', 'max_recommendations', 'enable_diversity',
                            'enable_explanation', 'updated_at']
                    result = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
                    try:
                        result['strategy_weights'] = json.loads(result.get('strategy_weights') or '{}')
                    except Exception:
                        result['strategy_weights'] = {}
                    try:
                        result['preferred_types'] = json.loads(result.get('preferred_types') or '[]')
                    except Exception:
                        result['preferred_types'] = []
                    return result
        except Exception:
            pass
        return {}

    def _get_candidate_resources(self, user_id: str, subject: str, limit: int) -> List[Dict]:
        """获取候选资源（排除已交互的）"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''
                    SELECT resource_id, title, resource_type, subject, grade, topic,
                           difficulty, duration_minutes, tags, keywords,
                           rating_avg, popularity_score, view_count, like_count
                    FROM learning_resources
                    WHERE status = 'active' AND resource_id NOT IN (
                        SELECT resource_id FROM resource_interactions WHERE user_id = ?
                    )
                '''
                params = [user_id]
                if subject:
                    sql += ' AND subject = ?'
                    params.append(subject)
                sql += ' LIMIT ?'
                params.append(limit)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                candidates = []
                for r in rows:
                    try:
                        tags = json.loads(r[8]) if r[8] else []
                    except Exception:
                        tags = []
                    candidates.append({
                        'resource_id': r[0], 'title': r[1], 'resource_type': r[2],
                        'subject': r[3], 'grade': r[4], 'topic': r[5],
                        'difficulty': r[6], 'duration_minutes': r[7],
                        'tags': tags, 'keywords': r[9] or '',
                        'rating_avg': r[10] or 0, 'popularity_score': r[11] or 0,
                        'view_count': r[12] or 0, 'like_count': r[13] or 0
                    })
                return candidates
        except Exception as e:
            logger.error(f"获取候选资源失败: {e}")
            return []

    def _content_based_score(self, user_id: str, candidates: List[Dict]) -> Dict[str, float]:
        """基于内容的推荐打分（标签/主题/关键词匹配）"""
        scores = {}
        try:
            # 获取用户偏好画像
            user_profile = self._get_user_profile(user_id)
            preferred_tags = set(user_profile.get('preferred_tags', []))
            preferred_subjects = set(user_profile.get('preferred_subjects', []))
            preferred_topics = set(user_profile.get('preferred_topics', []))
            preferred_difficulty = user_profile.get('preferred_difficulty')

            for c in candidates:
                score = 0.0
                # 标签匹配（权重0.4）
                c_tags = set(c.get('tags', []))
                if preferred_tags and c_tags:
                    overlap = len(preferred_tags & c_tags)
                    score += (overlap / max(len(preferred_tags), 1)) * 0.4

                # 主题匹配（权重0.3）
                if c.get('subject') in preferred_subjects:
                    score += 0.3
                elif c.get('topic') in preferred_topics:
                    score += 0.2

                # 难度匹配（权重0.2）
                if preferred_difficulty and c.get('difficulty') == preferred_difficulty:
                    score += 0.2

                # 关键词匹配（权重0.1）
                if c.get('keywords'):
                    user_keywords = user_profile.get('keywords', '')
                    if user_keywords:
                        kw_overlap = sum(1 for k in user_keywords.split(',') if k.strip() in c['keywords'])
                        score += min(0.1, kw_overlap * 0.02)

                scores[c['resource_id']] = min(1.0, score)
        except Exception as e:
            logger.error(f"内容匹配打分失败: {e}")
        return scores

    def _collaborative_filter_score(self, user_id: str, candidates: List[Dict]) -> Dict[str, float]:
        """基于协同过滤的推荐打分（用户-用户相似度）"""
        scores = {}
        try:
            candidate_ids = [c['resource_id'] for c in candidates]
            if not candidate_ids:
                return scores

            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 获取当前用户的高分资源（>=4分）
                cursor.execute('''
                    SELECT resource_id, rating FROM resource_interactions
                    WHERE user_id = ? AND rating >= 4
                ''', (user_id,))
                user_liked = cursor.fetchall()
                user_liked_ids = set([r[0] for r in user_liked])

                if not user_liked_ids:
                    return scores

                # 2. 找相似用户（共同喜欢相同资源）
                placeholders = ','.join('?' * len(user_liked_ids))
                cursor.execute(f'''
                    SELECT user_id, COUNT(*) as common
                    FROM resource_interactions
                    WHERE resource_id IN ({placeholders}) AND rating >= 4 AND user_id != ?
                    GROUP BY user_id
                    ORDER BY common DESC
                    LIMIT 20
                ''', list(user_liked_ids) + [user_id])
                similar_users = cursor.fetchall()

                if not similar_users:
                    return scores

                # 3. 聚合相似用户对候选资源的评分
                similar_user_ids = [r[0] for r in similar_users]
                placeholders = ','.join('?' * len(similar_user_ids))
                candidate_placeholders = ','.join('?' * len(candidate_ids))

                cursor.execute(f'''
                    SELECT resource_id, AVG(rating) as avg_rating, COUNT(*) as cnt
                    FROM resource_interactions
                    WHERE user_id IN ({placeholders}) AND resource_id IN ({candidate_placeholders}) AND rating > 0
                    GROUP BY resource_id
                ''', similar_user_ids + candidate_ids)

                for row in cursor.fetchall():
                    rid, avg, cnt = row[0], row[1], row[2]
                    # 加权：评分越高 + 评价人数越多 → 越可信
                    confidence = min(1.0, cnt / 5.0)
                    scores[rid] = (avg / 5.0) * confidence
        except Exception as e:
            logger.error(f"协同过滤打分失败: {e}")
        return scores

    def _knowledge_path_score(self, user_id: str, candidates: List[Dict]) -> Dict[str, float]:
        """基于学习路径的推荐打分（前置知识已掌握则推荐进阶）"""
        scores = {}
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                # 获取用户已完成资源
                cursor.execute('''
                    SELECT resource_id, completed FROM resource_interactions
                    WHERE user_id = ? AND completed = 1
                ''', (user_id,))
                completed_ids = set([r[0] for r in cursor.fetchall()])

                # 简化版：对每个候选资源，根据其难度与用户当前学习进度匹配
                cursor.execute('''
                    SELECT AVG(progress) FROM resource_interactions WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                avg_progress = (row[0] if row and row[0] else 0) / 100.0

                for c in candidates:
                    diff = DIFFICULTY_LEVELS.get(c.get('difficulty', 'intermediate'), 2)
                    # 用户进度越高，越推荐高难度
                    expected_difficulty = 1 + avg_progress * 3
                    diff_match = 1.0 - abs(diff - expected_difficulty) / 4.0
                    scores[c['resource_id']] = max(0, diff_match)
        except Exception as e:
            logger.error(f"知识路径打分失败: {e}")
        return scores

    def _popularity_score(self, candidates: List[Dict]) -> Dict[str, float]:
        """基于热度的推荐打分"""
        scores = {}
        try:
            if not candidates:
                return scores
            max_views = max((c.get('view_count', 0) or 0) for c in candidates) or 1
            max_likes = max((c.get('like_count', 0) or 0) for c in candidates) or 1
            max_rating = max((c.get('rating_avg', 0) or 0) for c in candidates) or 5

            for c in candidates:
                view_score = (c.get('view_count', 0) or 0) / max_views
                like_score = (c.get('like_count', 0) or 0) / max_likes
                rating_score = (c.get('rating_avg', 0) or 0) / max_rating if max_rating > 0 else 0
                # 归一化到 0-1
                scores[c['resource_id']] = min(1.0, (view_score * 0.3 + like_score * 0.3 + rating_score * 0.4))
        except Exception as e:
            logger.error(f"热度打分失败: {e}")
        return scores

    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """从用户交互历史推断偏好画像"""
        profile = {
            'preferred_tags': [],
            'preferred_subjects': [],
            'preferred_topics': [],
            'preferred_difficulty': None,
            'keywords': ''
        }
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.resource_type, r.subject, r.topic, r.difficulty, r.tags, r.keywords
                    FROM resource_interactions ri
                    JOIN learning_resources r ON ri.resource_id = r.resource_id
                    WHERE ri.user_id = ? AND ri.rating >= 3
                ''', (user_id,))
                rows = cursor.fetchall()

                tags_count = defaultdict(int)
                subjects_count = defaultdict(int)
                topics_count = defaultdict(int)
                difficulty_count = defaultdict(int)
                keywords_set = set()

                for r in rows:
                    if r[0]: profile.setdefault('_types', defaultdict(int))[r[0]] += 0  # noop placeholder
                    if r[1]: subjects_count[r[1]] += 1
                    if r[2]: topics_count[r[2]] += 1
                    if r[3]: difficulty_count[r[3]] += 1
                    if r[4]:
                        try:
                            for t in json.loads(r[4]):
                                tags_count[t] += 1
                        except Exception:
                            pass
                    if r[5]:
                        for k in r[5].split(','):
                            kw = k.strip()
                            if kw:
                                keywords_set.add(kw)

                profile['preferred_tags'] = [t for t, _ in sorted(tags_count.items(), key=lambda x: -x[1])[:10]]
                profile['preferred_subjects'] = [s for s, _ in sorted(subjects_count.items(), key=lambda x: -x[1])[:5]]
                profile['preferred_topics'] = [t for t, _ in sorted(topics_count.items(), key=lambda x: -x[1])[:10]]
                profile['preferred_difficulty'] = max(difficulty_count.items(), key=lambda x: x[1])[0] if difficulty_count else None
                profile['keywords'] = ','.join(list(keywords_set)[:20])
        except Exception as e:
            logger.error(f"获取用户画像失败: {e}")
        return profile

    def _diversify(self, top_recs: List, candidates: List[Dict], limit: int) -> List:
        """多样性优化：同一类型不超过 40%"""
        try:
            if not top_recs:
                return top_recs

            result = []
            type_count = defaultdict(int)
            max_per_type = max(2, int(limit * 0.4))

            # 第一轮：每个类型最多 max_per_type
            for rid, score_info in top_recs:
                candidate = next((c for c in candidates if c['resource_id'] == rid), None)
                if not candidate:
                    continue
                rtype = candidate.get('resource_type', 'unknown')
                if type_count[rtype] < max_per_type:
                    result.append((rid, score_info))
                    type_count[rtype] += 1
                if len(result) >= limit:
                    break

            # 第二轮：填满剩余名额
            if len(result) < limit:
                for rid, score_info in top_recs:
                    if rid not in [r[0] for r in result]:
                        result.append((rid, score_info))
                        if len(result) >= limit:
                            break

            return result[:limit]
        except Exception:
            return top_recs[:limit]

    # ==================== 评价与统计 ====================

    def add_review(self, resource_id: str, user_id: str, rating: float,
                   review_text: str = None) -> Dict[str, Any]:
        """添加资源评价"""
        with self._lock:
            try:
                review_id = f"rev_{int(time.time() * 1000)}_{user_id}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO resource_reviews
                        (review_id, resource_id, user_id, rating, review_text)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (review_id, resource_id, user_id, rating, review_text))

                    # 更新资源评分
                    cursor.execute('SELECT AVG(rating), COUNT(*) FROM resource_reviews WHERE resource_id = ?',
                                   (resource_id,))
                    row = cursor.fetchone()
                    if row and row[1] > 0:
                        cursor.execute('UPDATE learning_resources SET rating_avg = ?, rating_count = ? WHERE resource_id = ?',
                                       (row[0], row[1], resource_id))
                    conn.commit()

                return {'success': True, 'review_id': review_id, 'message': '评价已添加'}
            except Exception as e:
                logger.error(f"添加评价失败: {e}")
                return {'success': False, 'error': str(e)}

    def mark_clicked(self, recommendation_id: str) -> Dict[str, Any]:
        """标记推荐为已点击"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE recommendations
                        SET clicked = 1, clicked_at = ?, status = 'clicked'
                        WHERE recommendation_id = ?
                    ''', (datetime.now().isoformat(), recommendation_id))
                    conn.commit()

                return {'success': True, 'message': '推荐已标记为已点击'}
            except Exception as e:
                logger.error(f"标记推荐点击失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_user_recommendations(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """获取用户历史推荐"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.recommendation_id, r.resource_id, lr.title,
                           r.strategy, r.score, r.reason, r.status, r.clicked, r.created_at
                    FROM recommendations r
                    LEFT JOIN learning_resources lr ON r.resource_id = lr.resource_id
                    WHERE r.user_id = ?
                    ORDER BY r.created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
                rows = cursor.fetchall()

                recs = [{
                    'recommendation_id': r[0], 'resource_id': r[1], 'title': r[2],
                    'strategy': r[3], 'score': r[4], 'reason': r[5],
                    'status': r[6], 'clicked': bool(r[7]), 'created_at': r[8]
                } for r in rows]

                return {
                    'success': True,
                    'user_id': user_id,
                    'recommendations': recs,
                    'count': len(recs)
                }
        except Exception as e:
            logger.error(f"获取用户推荐失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM learning_resources')
                resource_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM resource_interactions')
                interaction_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM recommendations')
                rec_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM recommendations WHERE clicked = 1')
                clicked_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM resource_reviews')
                review_count = cursor.fetchone()[0]

                cursor.execute('SELECT AVG(rating_avg) FROM learning_resources WHERE rating_count > 0')
                avg_rating_row = cursor.fetchone()
                avg_rating = avg_rating_row[0] if avg_rating_row and avg_rating_row[0] else 0

                # 推荐点击率
                ctr = (clicked_count / rec_count * 100) if rec_count > 0 else 0

                return {
                    'success': True,
                    'resources': resource_count,
                    'interactions': interaction_count,
                    'recommendations': rec_count,
                    'clicked': clicked_count,
                    'click_through_rate': round(ctr, 2),
                    'reviews': review_count,
                    'avg_rating': round(avg_rating, 2)
                }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}


# 单例实例
resource_recommendation_engine = ResourceRecommendationEngine()
