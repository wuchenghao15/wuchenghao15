# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
学习分析模型,用于分析学生的学习方向和兴趣
"""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.utils.db import db_manager
from app.utils.logging import logger
from app.utils.table_encryption import table_encryption
import logging
import json


class LearningAnalysisManager:
    """学习分析管理器"""

    def __init__(self):
        """初始化学习分析管理器"""
        self._create_tables()

    def _create_tables(self):
        """创建必要的表"""
        try:
            learning_analyses_table = table_encryption.encrypt_table_name('learning_analyses')
            learning_interests_table = table_encryption.encrypt_table_name('learning_interests')
            learning_directions_table = table_encryption.encrypt_table_name('learning_directions')
            learning_activities_table = table_encryption.encrypt_table_name('learning_activities')
            user_table = table_encryption.encrypt_table_name('user')

            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_analyses_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    analysis_type TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')

            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_interests_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    interest_level INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')

            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_directions_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')

            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_activities_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    activity_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            logger.info("学习分析表结构创建成功")
        except Exception as e:
            logger.error(f"创建学习分析表结构失败: {str(e)}")

    def analyze_learning_interest(self, user_id: int) -> Dict[str, Any]:
        """
        分析学习兴趣

        Args:
            user_id: 用户ID

        Returns:
            兴趣分析结果
        """
        try:
            learning_activities_table = table_encryption.encrypt_table_name('learning_activities')
            learning_interests_table = table_encryption.encrypt_table_name('learning_interests')

            activities = db_manager.fetch_all(
                f'SELECT activity_type, activity_data FROM {learning_activities_table} WHERE user_id = ? ORDER BY created_at DESC LIMIT 100',
                (user_id,)
            )

            interest_scores = self._analyze_activities(activities)

            history_interests = db_manager.fetch_all(
                f'SELECT subject, interest_level FROM {learning_interests_table} WHERE user_id = ?',
                (user_id,)
            )

            for interest in history_interests:
                subject = interest['subject'] if isinstance(interest, dict) else interest[0]
                level = interest['interest_level'] if isinstance(interest, dict) else interest[1]
                if subject not in interest_scores:
                    interest_scores[subject] = level

            comprehensive_interest = self._calculate_comprehensive_interest(interest_scores)

            analysis = {
                "user_id": user_id,
                "analysis_type": "interest",
                "interest_scores": interest_scores,
                "comprehensive_interest": comprehensive_interest,
                "recommended_subjects": self._get_recommended_subjects(interest_scores),
                "generated_at": datetime.now().isoformat()
            }

            self._save_analysis(user_id, "interest", analysis)

            for subject, level in interest_scores.items():
                self._update_learning_interest(user_id, subject, level)

            return analysis
        except Exception as e:
            logger.error(f"分析学习兴趣失败: {str(e)}")
            return {}

    def _analyze_activities(self, activities: List) -> Dict[str, int]:
        """分析活动数据"""
        interest_scores = {}
        for activity in activities:
            activity_type = activity['activity_type'] if isinstance(activity, dict) else activity[0]
            if activity_type not in interest_scores:
                interest_scores[activity_type] = 0
            interest_scores[activity_type] += 1
        return interest_scores

    def _calculate_comprehensive_interest(self, interest_scores: Dict[str, int]) -> str:
        """计算综合兴趣"""
        if not interest_scores:
            return "未确定"
        max_subject = max(interest_scores, key=interest_scores.get)
        return max_subject

    def _get_recommended_subjects(self, interest_scores: Dict[str, int]) -> List[str]:
        """获取推荐科目"""
        if not interest_scores:
            return []
        sorted_subjects = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)
        return [subject for subject, _ in sorted_subjects[:3]]

    def _identify_strengths_weaknesses(self, error_stats: Dict[str, Any], exam_records: List[Dict[str, Any]]) -> tuple:
        """
        识别优势和劣势

        Args:
            error_stats: 错题统计
            exam_records: 考试记录

        Returns:
            (优势列表, 劣势列表)
        """
        strengths = []
        weaknesses = []

        error_types = error_stats.get('error_types', {})
        for error_type, count in error_types.items():
            if count > 5:
                weaknesses.append(f"{error_type}错误较多")

        if exam_records:
            recent_scores = [record['score'] for record in exam_records[:5]]
            avg_score = sum(recent_scores) / len(recent_scores)

            if avg_score >= 80:
                strengths.append("整体成绩优秀")
            elif avg_score >= 60:
                strengths.append("基础掌握良好")

            strengths.append("学习态度认真")

        if not strengths:
            strengths.append("有学习潜力")
        if not weaknesses:
            weaknesses.append("需要进一步提高")

        return strengths, weaknesses

    def _save_analysis(self, user_id: int, analysis_type: str, analysis_data: Dict[str, Any]):
        """
        保存分析结果

        Args:
            user_id: 用户ID
            analysis_type: 分析类型
            analysis_data: 分析数据
        """
        try:
            learning_analyses_table = table_encryption.encrypt_table_name('learning_analyses')

            analysis_data_json = str(analysis_data)
            db_manager.execute(
                f'''
                INSERT INTO {learning_analyses_table} (user_id, analysis_type, analysis_data)
                VALUES (?, ?, ?)
                ''',
                (user_id, analysis_type, analysis_data_json)
            )
        except Exception as e:
            logger.error(f"保存分析结果失败: {str(e)}")

    def _update_learning_interest(self, user_id: int, subject: str, interest_level: int):
        """
        更新学习兴趣

        Args:
            user_id: 用户ID
            subject: 科目
            interest_level: 兴趣水平
        """
        try:
            learning_interests_table = table_encryption.encrypt_table_name('learning_interests')

            existing = db_manager.fetch_one(
                f'SELECT id FROM {learning_interests_table} WHERE user_id = ? AND subject = ?',
                (user_id, subject)
            )

            if existing:
                db_manager.execute(
                    f'''
                    UPDATE {learning_interests_table}
                    SET interest_level = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND subject = ?
                    ''',
                    (interest_level, user_id, subject)
                )
            else:
                db_manager.execute(
                    f'''
                    INSERT INTO {learning_interests_table} (user_id, subject, interest_level)
                    VALUES (?, ?, ?)
                    ''',
                    (user_id, subject, interest_level)
                )
        except Exception as e:
            logger.error(f"更新学习兴趣失败: {str(e)}")

    def _update_learning_direction(self, user_id: int, direction: str, priority: int):
        """
        更新学习方向

        Args:
            user_id: 用户ID
            direction: 方向
            priority: 优先级
        """
        try:
            learning_directions_table = table_encryption.encrypt_table_name('learning_directions')

            existing = db_manager.fetch_one(
                f'SELECT id FROM {learning_directions_table} WHERE user_id = ? AND direction = ?',
                (user_id, direction)
            )

            if existing:
                db_manager.execute(
                    f'''
                    UPDATE {learning_directions_table}
                    SET priority = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND direction = ?
                    ''',
                    (priority, user_id, direction)
                )
            else:
                db_manager.execute(
                    f'''
                    INSERT INTO {learning_directions_table} (user_id, direction, priority)
                    VALUES (?, ?, ?)
                    ''',
                    (user_id, direction, priority)
                )
        except Exception as e:
            logger.error(f"更新学习方向失败: {str(e)}")

    def _analyze_learning_style(self, user_id: int) -> Dict[str, Any]:
        """
        分析学习风格

        Args:
            user_id: 用户ID

        Returns:
            学习风格分析
        """
        try:
            learning_activities_table = table_encryption.encrypt_table_name('learning_activities')

            activities = db_manager.fetch_all(
                f'SELECT activity_type, duration FROM {learning_activities_table} WHERE user_id = ? ORDER BY created_at DESC LIMIT 50',
                (user_id,)
            )

            style_scores = {
                "visual": 0,
                "auditory": 0,
                "kinesthetic": 0,
                "reading/writing": 0
            }

            for activity in activities:
                activity_type = activity['activity_type'] if isinstance(activity, dict) else activity[0]
                duration = activity['duration'] if isinstance(activity, dict) else activity[1]

                if activity_type == 'resource_view':
                    style_scores["visual"] += duration or 1
                elif activity_type == 'review':
                    style_scores["reading/writing"] += duration or 1
                elif activity_type == 'practice':
                    style_scores["kinesthetic"] += duration or 1
                elif activity_type == 'exam':
                    style_scores["reading/writing"] += duration or 1

            dominant_style = max(style_scores, key=style_scores.get)

            style_descriptions = {
                "visual": "你倾向于通过视觉方式学习,如图表、图片和视频",
                "auditory": "你倾向于通过听觉方式学习,如听讲、讨论和音频材料",
                "kinesthetic": "你倾向于通过动手实践学习,如实验、操作和角色扮演",
                "reading/writing": "你倾向于通过阅读和写作学习,如笔记、文章和书籍"
            }

            return {
                "dominant_style": dominant_style,
                "style_scores": style_scores,
                "description": style_descriptions.get(dominant_style, "")
            }
        except Exception as e:
            logger.error(f"分析学习风格失败: {str(e)}")
            return {}
