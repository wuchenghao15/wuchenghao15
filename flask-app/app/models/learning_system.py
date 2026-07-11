# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
新学习系统核心模型
包含学习记录管理、进度追踪、学习统计等功能
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from app.utils.logging import logger
import logging

# 数据库路径配置
DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'


class LearningSystem:
    """学习系统主类"""
    
    def __init__(self):
        self.courses = []
        self.user_progress = {}
        self._init_database()
        logger.info("学习系统初始化完成")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # 创建学习记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        subject TEXT NOT NULL,
                        content TEXT,
                        duration INTEGER DEFAULT 0,
                        knowledge_points TEXT,
                        difficulty_level INTEGER DEFAULT 1,
                        mastery_level INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建学习进度表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        subject TEXT NOT NULL,
                        total_duration INTEGER DEFAULT 0,
                        sessions_count INTEGER DEFAULT 0,
                        average_score REAL DEFAULT 0,
                        mastery_level INTEGER DEFAULT 0,
                        last_study_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, subject)
                    )
                ''')
                
                # 创建学习目标表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_goals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        goal_type TEXT NOT NULL,
                        goal_content TEXT NOT NULL,
                        target_date TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        progress REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建学习统计表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        total_duration INTEGER DEFAULT 0,
                        subjects_count INTEGER DEFAULT 0,
                        questions_completed INTEGER DEFAULT 0,
                        correct_rate REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, date)
                    )
                ''')
                
                logger.info("学习系统数据库表初始化完成")
        except Exception as e:
            logger.error(f"学习系统数据库初始化失败: {str(e)}")
    
    def get_courses(self):
        return self.courses
    
    def get_progress(self, user_id):
        return self.user_progress.get(user_id, {})
    
    def add_learning_record(self, user_id: int, subject: str, content: str = None,
                           duration: int = 0, knowledge_points: str = None,
                           difficulty_level: int = 1, mastery_level: int = 0,
                           notes: str = None) -> Dict[str, Any]:
        """
        添加学习记录
        
        Args:
            user_id: 用户ID
            subject: 学习科目
            content: 学习内容
            duration: 学习时长（分钟）
            knowledge_points: 涉及知识点
            difficulty_level: 难度等级
            mastery_level: 掌握程度
            notes: 学习笔记
        
        Returns:
            操作结果
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # 添加学习记录
                cursor.execute('''
                    INSERT INTO learning_records 
                    (user_id, subject, content, duration, knowledge_points, 
                     difficulty_level, mastery_level, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, subject, content, duration, knowledge_points,
                      difficulty_level, mastery_level, notes))
                
                record_id = cursor.lastrowid
                
                # 更新学习进度
                self._update_learning_progress(conn, user_id, subject, duration)
                
                # 更新学习统计
                self._update_daily_statistics(conn, user_id, duration, subject)
                
                return {
                    'success': True,
                    'record_id': record_id,
                    'message': '学习记录已添加'
                }
        except Exception as e:
            logger.error(f"添加学习记录失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _update_learning_progress(self, conn, user_id: int, subject: str, duration: int):
        """更新学习进度"""
        cursor = conn.cursor()
        
        # 检查是否已有进度记录
        cursor.execute('''
            SELECT id, total_duration, sessions_count FROM learning_progress
            WHERE user_id = ? AND subject = ?
        ''', (user_id, subject))
        
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有记录
            new_duration = existing[1] + duration
            new_sessions = existing[2] + 1
            
            cursor.execute('''
                UPDATE learning_progress
                SET total_duration = ?, sessions_count = ?, last_study_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND subject = ?
            ''', (new_duration, new_sessions, user_id, subject))
        else:
            # 创建新记录
            cursor.execute('''
                INSERT INTO learning_progress
                (user_id, subject, total_duration, sessions_count, last_study_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, subject, duration, 1))
    
    def _update_daily_statistics(self, conn, user_id: int, duration: int, subject: str):
        """更新每日学习统计"""
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 检查今日是否已有统计
        cursor.execute('''
            SELECT id, total_duration, subjects_count FROM learning_statistics
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        existing = cursor.fetchone()
        
        if existing:
            # 更新今日统计
            new_duration = existing[1] + duration
            new_subjects = existing[2] + 1 if subject not in self._get_today_subjects(conn, user_id, today) else existing[2]
            
            cursor.execute('''
                UPDATE learning_statistics
                SET total_duration = ?, subjects_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND date = ?
            ''', (new_duration, new_subjects, user_id, today))
        else:
            # 创建今日统计
            cursor.execute('''
                INSERT INTO learning_statistics
                (user_id, date, total_duration, subjects_count)
                VALUES (?, ?, ?, ?)
            ''', (user_id, today, duration, 1))
    
    def _get_today_subjects(self, conn, user_id: int, date: str) -> List[str]:
        """获取今日学习的科目"""
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT subject FROM learning_records
            WHERE user_id = ? AND DATE(created_at) = ?
        ''', (user_id, date))
        
        return [row[0] for row in cursor.fetchall()]
    
    def get_user_learning_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取用户学习摘要
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            学习摘要数据
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取总学习时长
                cursor.execute('''
                    SELECT SUM(total_duration) as total_duration, 
                           SUM(sessions_count) as total_sessions,
                           COUNT(*) as subjects_count
                    FROM learning_progress WHERE user_id = ?
                ''', (user_id,))
                progress_summary = cursor.fetchone()
                
                # 获取最近学习记录
                cursor.execute('''
                    SELECT subject, duration, created_at, mastery_level
                    FROM learning_records
                    WHERE user_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (user_id, 10))
                recent_records = [dict(row) for row in cursor.fetchall()]
                
                # 获取学习统计趋势
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT date, total_duration, subjects_count
                    FROM learning_statistics
                    WHERE user_id = ? AND date >= ?
                    ORDER BY date DESC
                ''', (user_id, start_date))
                daily_stats = [dict(row) for row in cursor.fetchall()]
                
                # 计算学习频率
                study_frequency = len(daily_stats) / days if days > 0 else 0
                
                return {
                    'user_id': user_id,
                    'total_duration': progress_summary['total_duration'] or 0,
                    'total_sessions': progress_summary['total_sessions'] or 0,
                    'subjects_count': progress_summary['subjects_count'] or 0,
                    'recent_records': recent_records,
                    'daily_stats': daily_stats,
                    'study_frequency': round(study_frequency * 100, 1),
                    'period_days': days,
                    'generated_at': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"获取学习摘要失败: {str(e)}")
            return {}
    
    def set_learning_goal(self, user_id: int, goal_type: str, goal_content: str,
                         target_date: str = None) -> Dict[str, Any]:
        """
        设置学习目标
        
        Args:
            user_id: 用户ID
            goal_type: 目标类型（短期/中期/长期）
            goal_content: 目标内容
            target_date: 目标日期
        
        Returns:
            操作结果
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO learning_goals
                    (user_id, goal_type, goal_content, target_date)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, goal_type, goal_content, target_date))
                
                goal_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'goal_id': goal_id,
                    'message': '学习目标已设置'
                }
        except Exception as e:
            logger.error(f"设置学习目标失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_learning_goals(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户学习目标
        
        Args:
            user_id: 用户ID
        
        Returns:
            学习目标列表
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, goal_type, goal_content, target_date, status, progress
                    FROM learning_goals
                    WHERE user_id = ? AND status != 'completed'
                    ORDER BY target_date ASC
                ''', (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取学习目标失败: {str(e)}")
            return []
    
    def update_goal_progress(self, goal_id: int, progress: float) -> Dict[str, Any]:
        """
        更新目标进度
        
        Args:
            goal_id: 目标ID
            progress: 进度值（0-100）
        
        Returns:
            操作结果
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                status = 'completed' if progress >= 100 else 'active'
                
                cursor.execute('''
                    UPDATE learning_goals
                    SET progress = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (progress, status, goal_id))
                
                return {
                    'success': True,
                    'goal_id': goal_id,
                    'progress': progress,
                    'status': status,
                    'message': '目标进度已更新'
                }
        except Exception as e:
            logger.error(f"更新目标进度失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_subject_analysis(self, user_id: int) -> Dict[str, Any]:
        """
        获取科目学习分析
        
        Args:
            user_id: 用户ID
        
        Returns:
            科目分析数据
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取各科目学习时长分布
                cursor.execute('''
                    SELECT subject, total_duration, sessions_count, mastery_level, last_study_at
                    FROM learning_progress
                    WHERE user_id = ?
                    ORDER BY total_duration DESC
                ''', (user_id,))
                
                subjects_data = [dict(row) for row in cursor.fetchall()]
                
                # 计算学习时长占比
                total_duration = sum(s['total_duration'] for s in subjects_data)
                
                for subject in subjects_data:
                    if total_duration > 0:
                        subject['duration_percentage'] = round(
                            subject['total_duration'] / total_duration * 100, 1
                        )
                    else:
                        subject['duration_percentage'] = 0
                
                # 找出优势和劣势科目
                sorted_by_mastery = sorted(subjects_data, key=lambda x: x.get('mastery_level', 0), reverse=True)
                
                strengths = sorted_by_mastery[:3] if len(sorted_by_mastery) >= 3 else sorted_by_mastery
                weaknesses = sorted_by_mastery[-3:] if len(sorted_by_mastery) >= 3 else []
                
                return {
                    'user_id': user_id,
                    'subjects_analysis': subjects_data,
                    'strengths': strengths,
                    'weaknesses': weaknesses,
                    'total_subjects': len(subjects_data),
                    'total_duration': total_duration,
                    'recommendation': self._generate_subject_recommendation(subjects_data),
                    'generated_at': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"获取科目分析失败: {str(e)}")
            return {}
    
    def _generate_subject_recommendation(self, subjects_data: List[Dict]) -> str:
        """生成科目学习建议"""
        if not subjects_data:
            return "建议开始选择一门科目进行系统学习"
        
        # 找出学习时间最少的科目
        min_duration_subject = min(subjects_data, key=lambda x: x['total_duration'])
        
        if min_duration_subject['total_duration'] < 60:
            return f"建议增加对{min_duration_subject['subject']}的学习时间，每日至少30分钟"
        
        # 找出掌握程度最低的科目
        min_mastery_subject = min(subjects_data, key=lambda x: x.get('mastery_level', 0))
        
        if min_mastery_subject.get('mastery_level', 50) < 60:
            return f"建议加强对{min_mastery_subject['subject']}的深入学习和练习"
        
        return "各科目学习进度均衡，建议继续保持并挑战更高难度"


class LearningRecordManager:
    """学习记录管理器"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def get_records_by_date(self, user_id: int, date: str) -> List[Dict[str, Any]]:
        """
        按日期获取学习记录
        
        Args:
            user_id: 用户ID
            date: 日期（YYYY-MM-DD）
        
        Returns:
            学习记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM learning_records
                    WHERE user_id = ? AND DATE(created_at) = ?
                    ORDER BY created_at DESC
                ''', (user_id, date))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取日期学习记录失败: {str(e)}")
            return []
    
    def get_records_by_subject(self, user_id: int, subject: str) -> List[Dict[str, Any]]:
        """
        按科目获取学习记录
        
        Args:
            user_id: 用户ID
            subject: 科目名称
        
        Returns:
            学习记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM learning_records
                    WHERE user_id = ? AND subject = ?
                    ORDER BY created_at DESC
                ''', (user_id, subject))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取科目学习记录失败: {str(e)}")
            return []
    
    def delete_record(self, record_id: int, user_id: int) -> Dict[str, Any]:
        """
        删除学习记录
        
        Args:
            record_id: 记录ID
            user_id: 用户ID（用于验证权限）
        
        Returns:
            操作结果
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 验证记录归属
                cursor.execute('''
                    SELECT id FROM learning_records WHERE id = ? AND user_id = ?
                ''', (record_id, user_id))
                
                if not cursor.fetchone():
                    return {'success': False, 'error': '记录不存在或无权限'}
                
                cursor.execute('DELETE FROM learning_records WHERE id = ?', (record_id,))
                
                return {'success': True, 'message': '学习记录已删除'}
        except Exception as e:
            logger.error(f"删除学习记录失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_record(self, record_id: int, user_id: int, 
                     updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新学习记录
        
        Args:
            record_id: 记录ID
            user_id: 用户ID
            updates: 更新字段
        
        Returns:
            操作结果
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 验证记录归属
                cursor.execute('''
                    SELECT id FROM learning_records WHERE id = ? AND user_id = ?
                ''', (record_id, user_id))
                
                if not cursor.fetchone():
                    return {'success': False, 'error': '记录不存在或无权限'}
                
                # 构建更新SQL
                update_fields = []
                update_values = []
                
                allowed_fields = ['content', 'duration', 'knowledge_points', 
                                 'difficulty_level', 'mastery_level', 'notes']
                
                for field, value in updates.items():
                    if field in allowed_fields:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                
                if not update_fields:
                    return {'success': False, 'error': '无有效更新字段'}
                
                update_values.append(record_id)
                
                cursor.execute('''
                    UPDATE learning_records
                    SET {}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                '''.format(', '.join(update_fields)), update_values)
                
                return {'success': True, 'message': '学习记录已更新'}
        except Exception as e:
            logger.error(f"更新学习记录失败: {str(e)}")
            return {'success': False, 'error': str(e)}


# 创建全局实例
learning_system = LearningSystem()
learning_record_manager = LearningRecordManager()
