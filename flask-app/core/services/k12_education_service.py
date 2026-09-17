from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS K12教育综合服务 (v15.1.0) =================================== 针对九年制义务教育（K12）学生的学科资源管理、分层教学、家校互动、 错题本和薄弱点分析等综合服务。  核心能力： 1. 学科资源管理 - 9大学科资源体系（语数英/物化生/政史地） 2. 分层教学 - 按学习能力A/B/C分层，差异化教学 3. 家校互动 - 家长端查看学习情况、教师端反馈 4. 错题本管理 - 智能错题归集和薄弱知识点分析 5. 学习报告 - 周报/月报/学期报告自动生成 6. 知识点体系 - 按年级和学科的知识点树状结构 7. 学习进度追踪 - 按知识点的掌握度追踪 """
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'k12_education_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('K12Education')


# ========== K12 学科体系 ==========

K12_SUBJECTS = {
    '语文': {
        'code': 'chinese',
        'category': 'liberal_arts',
        'grades': '1-12',
        'full_name': '语文',
        'has_listening': False,
        'exam_weight': 1.0
    },
    '数学': {
        'code': 'math',
        'category': 'science',
        'grades': '1-12',
        'full_name': '数学',
        'has_listening': False,
        'exam_weight': 1.2
    },
    '英语': {
        'code': 'english',
        'category': 'language',
        'grades': '3-12',
        'full_name': '英语',
        'has_listening': True,
        'exam_weight': 1.0
    },
    '物理': {
        'code': 'physics',
        'category': 'science',
        'grades': '8-12',
        'full_name': '物理',
        'has_listening': False,
        'exam_weight': 1.0
    },
    '化学': {
        'code': 'chemistry',
        'category': 'science',
        'grades': '9-12',
        'full_name': '化学',
        'has_listening': False,
        'exam_weight': 1.0
    },
    '生物': {
        'code': 'biology',
        'category': 'science',
        'grades': '7-12',
        'full_name': '生物',
        'has_listening': False,
        'exam_weight': 0.8
    },
    '政治': {
        'code': 'politics',
        'category': 'liberal_arts',
        'grades': '7-12',
        'full_name': '道德与法治',
        'has_listening': False,
        'exam_weight': 0.8
    },
    '历史': {
        'code': 'history',
        'category': 'liberal_arts',
        'grades': '7-12',
        'full_name': '历史',
        'has_listening': False,
        'exam_weight': 0.8
    },
    '地理': {
        'code': 'geography',
        'category': 'liberal_arts',
        'grades': '7-12',
        'full_name': '地理',
        'has_listening': False,
        'exam_weight': 0.8
    }
}

# 年级分组
GRADE_GROUPS = {
    'primary': {'name': '小学', 'grades': ['1', '2', '3', '4', '5', '6']},
    'junior': {'name': '初中', 'grades': ['7', '8', '9']},
    'senior': {'name': '高中', 'grades': ['10', '11', '12']}
}

# 分层教学等级
LEARNING_TIERS = {
    'A': {
        'name': '提高层',
        'description': '基础扎实，可挑战拓展题',
        'difficulty_range': (0.7, 1.0),
        'recommended_practice_per_day': 15,
        'focus': '拓展提升'
    },
    'B': {
        'name': '基础层',
        'description': '基础一般，巩固基础题',
        'difficulty_range': (0.4, 0.7),
        'recommended_practice_per_day': 20,
        'focus': '基础巩固'
    },
    'C': {
        'name': '补差层',
        'description': '基础薄弱，需重点辅导',
        'difficulty_range': (0.1, 0.4),
        'recommended_practice_per_day': 10,
        'focus': '基础补差'
    }
}

# 知识点难度等级
DIFFICULTY_LEVELS = {
    1: {'name': '了解', 'description': '知道基本概念'},
    2: {'name': '理解', 'description': '理解概念含义'},
    3: {'name': '掌握', 'description': '能够应用解题'},
    4: {'name': '熟练', 'description': '灵活运用综合题'},
    5: {'name': '精通', 'description': '拓展创新应用'}
}

# 家校互动消息类型
HOME_SCHOOL_MESSAGE_TYPES = {
    'study_report': '学习报告',
    'behavior_feedback': '行为反馈',
    'exam_notice': '考试通知',
    'homework_notice': '作业通知',
    'achievement': '表扬鼓励',
    'concern': '关注提醒',
    'meeting': '家长会通知'
}

# 学习报告类型
REPORT_TYPES = {
    'weekly': {'name': '周报', 'cycle_days': 7},
    'monthly': {'name': '月报', 'cycle_days': 30},
    'term': {'name': '学期报告', 'cycle_days': 120}
}


class K12EducationService:
    """K12 教育综合服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # K12 学生档案表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_student_profiles ( user_id INTEGER PRIMARY KEY, grade TEXT, grade_group TEXT, learning_tier TEXT DEFAULT 'B', subjects TEXT, class_id TEXT, parent_user_id INTEGER, teacher_user_id INTEGER, total_study_hours REAL DEFAULT 0, total_questions_done INTEGER DEFAULT 0, avg_accuracy REAL DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                # 知识点表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_knowledge_points ( point_id TEXT PRIMARY KEY, subject TEXT NOT NULL, grade TEXT NOT NULL, chapter TEXT, point_name TEXT NOT NULL, parent_point_id TEXT, difficulty_level INTEGER DEFAULT 2, description TEXT, created_at TEXT ) ''')
                # 学生知识点掌握度表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_knowledge_mastery ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, point_id TEXT NOT NULL, mastery_level REAL DEFAULT 0, attempts INTEGER DEFAULT 0, correct_count INTEGER DEFAULT 0, last_practiced TEXT, updated_at TEXT, UNIQUE(user_id, point_id) ) ''')
                # 错题本表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_wrong_questions ( wrong_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, subject TEXT NOT NULL, question_id TEXT, point_id TEXT, wrong_type TEXT, wrong_count INTEGER DEFAULT 1, first_wrong_at TEXT, last_wrong_at TEXT, resolved INTEGER DEFAULT 0, resolved_at TEXT, note TEXT ) ''')
                # 家校互动消息表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_home_school_messages ( message_id TEXT PRIMARY KEY, student_user_id INTEGER NOT NULL, sender_id INTEGER NOT NULL, sender_role TEXT, message_type TEXT NOT NULL, title TEXT, content TEXT, read_status INTEGER DEFAULT 0, created_at TEXT, read_at TEXT ) ''')
                # 学习报告表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_study_reports ( report_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, report_type TEXT NOT NULL, period_start TEXT, period_end TEXT, study_hours REAL, questions_done INTEGER, accuracy REAL, subjects_covered TEXT, weak_points TEXT, improvement TEXT, created_at TEXT ) ''')
                # 分层教学分组表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_tier_groups ( group_id TEXT PRIMARY KEY, subject TEXT NOT NULL, grade TEXT NOT NULL, tier TEXT NOT NULL, teacher_id INTEGER, student_count INTEGER DEFAULT 0, description TEXT, created_at TEXT ) ''')
                conn.commit()
                logger.info('K12教育服务数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化数据库失败: {e}')

    # ========== 学生档案管理 ==========

    def create_student_profile(self, user_id: int, grade: str,
                                  subjects: List[str] = None,
                                  parent_user_id: int = None,
                                  class_id: str = None) -> Dict[str, Any]:
        """创建K12学生档案"""
        with self._lock:
            # 确定年级组
            grade_group = self._get_grade_group(grade)
            if not grade_group:
                return {'success': False, 'error': f'未知年级: {grade}'}

            # 默认科目
            if not subjects:
                subjects = self._get_default_subjects(grade_group)

            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    conn.execute(''' INSERT OR REPLACE INTO k12_student_profiles (user_id, grade, grade_group, learning_tier, subjects, class_id, parent_user_id, created_at, updated_at) VALUES (?, ?, ?, 'B', ?, ?, ?, ?, ?) ''', (user_id, grade, grade_group, json.dumps(subjects),
                          class_id, parent_user_id, now, now))
                    conn.commit()
                logger.info(f'创建K12学生档案: user_id={user_id} grade={grade}')
                return {
                    'success': True,
                    'user_id': user_id,
                    'grade': grade,
                    'grade_group': grade_group,
                    'subjects': subjects,
                    'learning_tier': 'B'
                }
            except Exception as e:
                logger.error(f'创建学生档案失败: {e}')
                return {'success': False, 'error': str(e)}

    def _get_grade_group(self, grade: str) -> Optional[str]:
        """根据年级获取年级组"""
        # 标准化年级（提取数字）
        grade_num = ''.join(c for c in grade if c.isdigit())
        for group_key, group_config in GRADE_GROUPS.items():
            if grade_num in group_config['grades']:
                return group_key
        return None

    def _get_default_subjects(self, grade_group: str) -> List[str]:
        """获取默认科目"""
        if grade_group == 'primary':
            return ['语文', '数学', '英语']
        elif grade_group == 'junior':
            return ['语文', '数学', '英语', '物理', '化学', '生物', '政治', '历史', '地理']
        elif grade_group == 'senior':
            return ['语文', '数学', '英语', '物理', '化学', '生物', '政治', '历史', '地理']
        return ['语文', '数学', '英语']

    def update_learning_tier(self, user_id: int, tier: str,
                                subject: str = None) -> Dict[str, Any]:
        """更新学习分层"""
        with self._lock:
            if tier not in LEARNING_TIERS:
                return {'success': False, 'error': f'未知分层: {tier}'}
            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    conn.execute(''' UPDATE k12_student_profiles SET learning_tier = ?, updated_at = ? WHERE user_id = ? ''', (tier, now, user_id))
                    conn.commit()
                logger.info(f'学生 {user_id} 调整为 {tier} 层')
                return {
                    'success': True,
                    'user_id': user_id,
                    'tier': tier,
                    'tier_name': LEARNING_TIERS[tier]['name'],
                    'focus': LEARNING_TIERS[tier]['focus']
                }
            except Exception as e:
                logger.error(f'更新分层失败: {e}')
                return {'success': False, 'error': str(e)}

    def evaluate_tier(self, user_id: int, subject: str = None) -> Dict[str, Any]:
        """根据学习表现评估分层"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' SELECT avg_accuracy, total_questions_done FROM k12_student_profiles WHERE user_id = ? ''', (user_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '学生档案不存在'}
                accuracy = row[0] or 0
                questions_done = row[1] or 0

            # 根据准确率推荐分层
            if accuracy >= 0.85 and questions_done >= 50:
                recommended_tier = 'A'
            elif accuracy >= 0.6:
                recommended_tier = 'B'
            else:
                recommended_tier = 'C'

            return {
                'success': True,
                'user_id': user_id,
                'current_accuracy': accuracy,
                'total_questions': questions_done,
                'recommended_tier': recommended_tier,
                'tier_name': LEARNING_TIERS[recommended_tier]['name'],
                'difficulty_range': LEARNING_TIERS[recommended_tier]['difficulty_range'],
                'recommended_practice_per_day': LEARNING_TIERS[recommended_tier]['recommended_practice_per_day']
            }
        except Exception as e:
            logger.error(f'评估分层失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识点管理 ==========

    def add_knowledge_point(self, subject: str, grade: str, point_name: str,
                              chapter: str = None, difficulty_level: int = 2,
                              parent_point_id: str = None,
                              description: str = '') -> Dict[str, Any]:
        """添加知识点"""
        with self._lock:
            if subject not in K12_SUBJECTS:
                return {'success': False, 'error': f'未知学科: {subject}'}
            if difficulty_level not in DIFFICULTY_LEVELS:
                return {'success': False, 'error': f'未知难度: {difficulty_level}'}

            point_id = f'kp_{subject}_{grade}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    conn.execute(''' INSERT INTO k12_knowledge_points (point_id, subject, grade, chapter, point_name, parent_point_id, difficulty_level, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (point_id, subject, grade, chapter, point_name,
                          parent_point_id, difficulty_level, description, now))
                    conn.commit()
                return {
                    'success': True,
                    'point_id': point_id,
                    'subject': subject,
                    'grade': grade,
                    'point_name': point_name,
                    'difficulty': DIFFICULTY_LEVELS[difficulty_level]['name']
                }
            except Exception as e:
                logger.error(f'添加知识点失败: {e}')
                return {'success': False, 'error': str(e)}

    def get_knowledge_tree(self, subject: str, grade: str) -> Dict[str, Any]:
        """获取知识点树"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' SELECT point_id, chapter, point_name, parent_point_id, difficulty_level, description FROM k12_knowledge_points WHERE subject = ? AND grade = ? ORDER BY chapter, point_name ''', (subject, grade))
                rows = cursor.fetchall()

            points = []
            for row in rows:
                points.append({
                    'point_id': row[0],
                    'chapter': row[1],
                    'point_name': row[2],
                    'parent_point_id': row[3],
                    'difficulty_level': row[4],
                    'difficulty_name': DIFFICULTY_LEVELS.get(row[4], {}).get('name', ''),
                    'description': row[5]
                })

            # 构建树结构
            tree = self._build_tree(points)
            return {
                'success': True,
                'subject': subject,
                'grade': grade,
                'total_points': len(points),
                'tree': tree
            }
        except Exception as e:
            logger.error(f'获取知识点树失败: {e}')
            return {'success': False, 'error': str(e)}

    def _build_tree(self, points: List[Dict], parent_id: str = None) -> List[Dict]:
        """构建树结构"""
        tree = []
        for p in points:
            if p['parent_point_id'] == parent_id:
                children = self._build_tree(points, p['point_id'])
                node = {**p, 'children': children}
                tree.append(node)
        return tree

    # ========== 知识点掌握度 ==========

    def update_mastery(self, user_id: int, point_id: str,
                          is_correct: bool) -> Dict[str, Any]:
        """更新知识点掌握度"""
        with self._lock:
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' SELECT mastery_level, attempts, correct_count FROM k12_knowledge_mastery WHERE user_id = ? AND point_id = ? ''', (user_id, point_id))
                    row = cursor.fetchone()

                    if row:
                        old_mastery, attempts, correct = row
                        new_attempts = attempts + 1
                        new_correct = correct + (1 if is_correct else 0)
                        # 掌握度 = 正确次数/总次数 * 0.7 + 上次掌握度 * 0.3
                        new_mastery = (new_correct / new_attempts) * 0.7 + (old_mastery or 0) * 0.3
                        cursor.execute(''' UPDATE k12_knowledge_mastery SET mastery_level = ?, attempts = ?, correct_count = ?, last_practiced = ?, updated_at = ? WHERE user_id = ? AND point_id = ? ''', (new_mastery, new_attempts, new_correct, now, now,
                              user_id, point_id))
                    else:
                        new_attempts = 1
                        new_correct = 1 if is_correct else 0
                        new_mastery = new_correct / new_attempts
                        cursor.execute(''' INSERT INTO k12_knowledge_mastery (user_id, point_id, mastery_level, attempts, correct_count, last_practiced, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (user_id, point_id, new_mastery, new_attempts,
                              new_correct, now, now))
                    conn.commit()

                return {
                    'success': True,
                    'user_id': user_id,
                    'point_id': point_id,
                    'mastery_level': round(new_mastery, 4),
                    'attempts': new_attempts,
                    'correct_count': new_correct,
                    'mastery_status': self._get_mastery_status(new_mastery)
                }
            except Exception as e:
                logger.error(f'更新掌握度失败: {e}')
                return {'success': False, 'error': str(e)}

    def _get_mastery_status(self, mastery: float) -> str:
        """获取掌握状态"""
        if mastery >= 0.85:
            return '精通'
        elif mastery >= 0.7:
            return '熟练'
        elif mastery >= 0.5:
            return '掌握'
        elif mastery >= 0.3:
            return '理解'
        else:
            return '薄弱'

    def get_weak_points(self, user_id: int, subject: str = None,
                          threshold: float = 0.5) -> Dict[str, Any]:
        """获取薄弱知识点"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if subject:
                    cursor.execute(''' SELECT m.point_id, k.point_name, k.subject, k.grade, k.chapter, k.difficulty_level, m.mastery_level, m.attempts, m.correct_count FROM k12_knowledge_mastery m JOIN k12_knowledge_points k ON m.point_id = k.point_id WHERE m.user_id = ? AND k.subject = ? AND m.mastery_level < ? ORDER BY m.mastery_level ASC ''', (user_id, subject, threshold))
                else:
                    cursor.execute(''' SELECT m.point_id, k.point_name, k.subject, k.grade, k.chapter, k.difficulty_level, m.mastery_level, m.attempts, m.correct_count FROM k12_knowledge_mastery m JOIN k12_knowledge_points k ON m.point_id = k.point_id WHERE m.user_id = ? AND m.mastery_level < ? ORDER BY m.mastery_level ASC ''', (user_id, threshold))
                rows = cursor.fetchall()

            weak_points = []
            for row in rows:
                weak_points.append({
                    'point_id': row[0],
                    'point_name': row[1],
                    'subject': row[2],
                    'grade': row[3],
                    'chapter': row[4],
                    'difficulty': DIFFICULTY_LEVELS.get(row[5], {}).get('name', ''),
                    'mastery_level': round(row[6], 4),
                    'mastery_status': self._get_mastery_status(row[6]),
                    'attempts': row[7],
                    'correct_count': row[8]
                })
            return {
                'success': True,
                'user_id': user_id,
                'subject': subject,
                'threshold': threshold,
                'weak_points': weak_points,
                'count': len(weak_points)
            }
        except Exception as e:
            logger.error(f'获取薄弱知识点失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 错题本 ==========

    def add_wrong_question(self, user_id: int, subject: str,
                              question_id: str, point_id: str = None,
                              wrong_type: str = 'concept_error',
                              note: str = '') -> Dict[str, Any]:
        """添加错题"""
        with self._lock:
            now = datetime.now().isoformat()
            wrong_id = f'wq_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 检查是否已有相同错题
                    cursor.execute(''' SELECT wrong_id, wrong_count FROM k12_wrong_questions WHERE user_id = ? AND question_id = ? AND resolved = 0 ''', (user_id, question_id))
                    existing = cursor.fetchone()
                    if existing:
                        # 更新错题次数
                        cursor.execute(''' UPDATE k12_wrong_questions SET wrong_count = wrong_count + 1, last_wrong_at = ? WHERE wrong_id = ? ''', (now, existing[0]))
                        conn.commit()
                        return {
                            'success': True,
                            'wrong_id': existing[0],
                            'wrong_count': existing[1] + 1,
                            'message': '错题次数已更新'
                        }
                    # 新错题
                    cursor.execute(''' INSERT INTO k12_wrong_questions (wrong_id, user_id, subject, question_id, point_id, wrong_type, wrong_count, first_wrong_at, last_wrong_at, resolved, note) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, 0, ?) ''', (wrong_id, user_id, subject, question_id, point_id,
                          wrong_type, now, now, note))
                    conn.commit()
                logger.info(f'学生 {user_id} 新增错题: {wrong_id} ({subject})')
                return {
                    'success': True,
                    'wrong_id': wrong_id,
                    'subject': subject,
                    'wrong_count': 1
                }
            except Exception as e:
                logger.error(f'添加错题失败: {e}')
                return {'success': False, 'error': str(e)}

    def resolve_wrong_question(self, wrong_id: str) -> Dict[str, Any]:
        """标记错题为已解决"""
        with self._lock:
            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    conn.execute(''' UPDATE k12_wrong_questions SET resolved = 1, resolved_at = ? WHERE wrong_id = ? ''', (now, wrong_id))
                    conn.commit()
                return {'success': True, 'wrong_id': wrong_id, 'resolved_at': now}
            except Exception as e:
                logger.error(f'解决错题失败: {e}')
                return {'success': False, 'error': str(e)}

    def list_wrong_questions(self, user_id: int, subject: str = None,
                                resolved: int = 0) -> Dict[str, Any]:
        """列出错题"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                sql = '''SELECT wrong_id, subject, question_id, point_id, wrong_type, wrong_count, first_wrong_at, last_wrong_at, resolved, note FROM k12_wrong_questions WHERE user_id = ? AND resolved = ?'''
                params = [user_id, resolved]
                if subject:
                    sql += ' AND subject = ?'
                    params.append(subject)
                sql += ' ORDER BY last_wrong_at DESC'
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            wrong_questions = []
            for row in rows:
                wrong_questions.append({
                    'wrong_id': row[0],
                    'subject': row[1],
                    'question_id': row[2],
                    'point_id': row[3],
                    'wrong_type': row[4],
                    'wrong_count': row[5],
                    'first_wrong_at': row[6],
                    'last_wrong_at': row[7],
                    'resolved': bool(row[8]),
                    'note': row[9]
                })
            return {
                'success': True,
                'wrong_questions': wrong_questions,
                'count': len(wrong_questions)
            }
        except Exception as e:
            logger.error(f'列出错题失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 家校互动 ==========

    def send_home_school_message(self, student_user_id: int, sender_id: int,
                                    sender_role: str, message_type: str,
                                    title: str, content: str) -> Dict[str, Any]:
        """发送家校互动消息"""
        with self._lock:
            if message_type not in HOME_SCHOOL_MESSAGE_TYPES:
                return {'success': False, 'error': f'未知消息类型: {message_type}'}
            message_id = f'msg_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    conn.execute(''' INSERT INTO k12_home_school_messages (message_id, student_user_id, sender_id, sender_role, message_type, title, content, read_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?) ''', (message_id, student_user_id, sender_id, sender_role,
                          message_type, title, content, now))
                    conn.commit()
                logger.info(f'发送家校消息: {message_id} -> 学生 {student_user_id}')
                return {
                    'success': True,
                    'message_id': message_id,
                    'message_type': message_type,
                    'message_type_name': HOME_SCHOOL_MESSAGE_TYPES[message_type],
                    'title': title,
                    'created_at': now
                }
            except Exception as e:
                logger.error(f'发送家校消息失败: {e}')
                return {'success': False, 'error': str(e)}

    def get_home_school_messages(self, student_user_id: int,
                                    unread_only: bool = False) -> Dict[str, Any]:
        """获取家校互动消息"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                sql = '''SELECT message_id, sender_id, sender_role, message_type, title, content, read_status, created_at, read_at FROM k12_home_school_messages WHERE student_user_id = ?'''
                params = [student_user_id]
                if unread_only:
                    sql += ' AND read_status = 0'
                sql += ' ORDER BY created_at DESC'
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            messages = []
            for row in rows:
                messages.append({
                    'message_id': row[0],
                    'sender_id': row[1],
                    'sender_role': row[2],
                    'message_type': row[3],
                    'message_type_name': HOME_SCHOOL_MESSAGE_TYPES.get(row[3], row[3]),
                    'title': row[4],
                    'content': row[5],
                    'read_status': bool(row[6]),
                    'created_at': row[7],
                    'read_at': row[8]
                })
            return {
                'success': True,
                'messages': messages,
                'count': len(messages),
                'unread_count': sum(1 for m in messages if not m['read_status'])
            }
        except Exception as e:
            logger.error(f'获取家校消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def mark_message_read(self, message_id: str) -> Dict[str, Any]:
        """标记消息已读"""
        with self._lock:
            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    conn.execute(''' UPDATE k12_home_school_messages SET read_status = 1, read_at = ? WHERE message_id = ? ''', (now, message_id))
                    conn.commit()
                return {'success': True, 'message_id': message_id, 'read_at': now}
            except Exception as e:
                logger.error(f'标记已读失败: {e}')
                return {'success': False, 'error': str(e)}

    # ========== 学习报告 ==========

    def generate_report(self, user_id: int, report_type: str = 'weekly') -> Dict[str, Any]:
        """生成学习报告"""
        with self._lock:
            if report_type not in REPORT_TYPES:
                return {'success': False, 'error': f'未知报告类型: {report_type}'}

            cycle_days = REPORT_TYPES[report_type]['cycle_days']
            now = datetime.now()
            period_start = (now - timedelta(days=cycle_days)).isoformat()
            period_end = now.isoformat()

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 获取学生档案
                    cursor.execute(''' SELECT grade, grade_group, learning_tier, avg_accuracy, total_questions_done, total_study_hours FROM k12_student_profiles WHERE user_id = ? ''', (user_id,))
                    profile = cursor.fetchone()
                    if not profile:
                        return {'success': False, 'error': '学生档案不存在'}

                    # 获取薄弱知识点
                    cursor.execute(''' SELECT k.point_name, k.subject, m.mastery_level FROM k12_knowledge_mastery m JOIN k12_knowledge_points k ON m.point_id = k.point_id WHERE m.user_id = ? AND m.mastery_level < 0.5 ORDER BY m.mastery_level ASC LIMIT 5 ''', (user_id,))
                    weak_points = [{'point_name': r[0], 'subject': r[1],
                                     'mastery': round(r[2], 4)}
                                     for r in cursor.fetchall()]

                    # 获取错题统计
                    cursor.execute(''' SELECT subject, COUNT(*), SUM(wrong_count) FROM k12_wrong_questions WHERE user_id = ? AND resolved = 0 GROUP BY subject ''', (user_id,))
                    wrong_stats = {r[0]: {'count': r[1], 'total_wrong': r[2]}
                                     for r in cursor.fetchall()}

                # 生成改进建议
                improvement = self._generate_improvement_suggestions(
                    profile[3] or 0, weak_points, wrong_stats
                )

                report_id = f'report_{report_type}_{int(now.timestamp())}_{uuid.uuid4().hex[:8]}'
                with self._get_connection() as conn:
                    conn.execute(''' INSERT INTO k12_study_reports (report_id, user_id, report_type, period_start, period_end, study_hours, questions_done, accuracy, subjects_covered, weak_points, improvement, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (report_id, user_id, report_type, period_start, period_end,
                          profile[5] or 0, profile[4] or 0, profile[3] or 0,
                          json.dumps(wrong_stats.keys() and list(wrong_stats.keys()) or []),
                          json.dumps(weak_points, ensure_ascii=False),
                          json.dumps(improvement, ensure_ascii=False),
                          now.isoformat()))
                    conn.commit()

                logger.info(f'生成学习报告: {report_id} (类型: {report_type})')
                return {
                    'success': True,
                    'report_id': report_id,
                    'report_type': report_type,
                    'report_type_name': REPORT_TYPES[report_type]['name'],
                    'period_start': period_start,
                    'period_end': period_end,
                    'grade': profile[0],
                    'learning_tier': profile[2],
                    'avg_accuracy': profile[3] or 0,
                    'total_questions': profile[4] or 0,
                    'study_hours': profile[5] or 0,
                    'weak_points': weak_points,
                    'wrong_question_stats': wrong_stats,
                    'improvement_suggestions': improvement
                }
            except Exception as e:
                logger.error(f'生成报告失败: {e}')
                return {'success': False, 'error': str(e)}

    def _generate_improvement_suggestions(self, accuracy: float,
                                            weak_points: List[Dict],
                                            wrong_stats: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []
        if accuracy < 0.6:
            suggestions.append('整体准确率偏低，建议加强基础知识复习')
        elif accuracy < 0.8:
            suggestions.append('准确率有提升空间，建议针对薄弱知识点专项练习')
        else:
            suggestions.append('学习表现优秀，建议挑战更高难度题目')

        if weak_points:
            subjects_with_weak = set(p['subject'] for p in weak_points)
            for subject in subjects_with_weak:
                suggestions.append(f'{subject}存在薄弱知识点，建议重点突破')

        if wrong_stats:
            for subject, stats in wrong_stats.items():
                if stats['total_wrong'] > 5:
                    suggestions.append(f'{subject}错题较多({stats["total_wrong"]}次)，建议整理错题本')

        if not suggestions:
            suggestions.append('保持良好学习习惯，继续努力')
        return suggestions

    # ========== 统计 ==========

    def get_statistics(self) -> Dict[str, Any]:
        """获取K12教育统计"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM k12_student_profiles')
                total_students = cursor.fetchone()[0]
                cursor.execute('SELECT grade_group, COUNT(*) FROM k12_student_profiles GROUP BY grade_group')
                grade_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT learning_tier, COUNT(*) FROM k12_student_profiles GROUP BY learning_tier')
                tier_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM k12_knowledge_points')
                total_points = cursor.fetchone()[0]
                cursor.execute('SELECT subject, COUNT(*) FROM k12_knowledge_points GROUP BY subject')
                subject_point_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM k12_wrong_questions WHERE resolved = 0')
                unresolved_wrong = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM k12_home_school_messages')
                total_messages = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM k12_home_school_messages WHERE read_status = 0')
                unread_messages = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM k12_study_reports')
                total_reports = cursor.fetchone()[0]

            return {
                'success': True,
                'total_students': total_students,
                'by_grade_group': grade_stats,
                'by_tier': tier_stats,
                'total_knowledge_points': total_points,
                'points_by_subject': subject_point_stats,
                'unresolved_wrong_questions': unresolved_wrong,
                'total_home_school_messages': total_messages,
                'unread_messages': unread_messages,
                'total_reports': total_reports,
                'available_subjects': list(K12_SUBJECTS.keys()),
                'available_tiers': list(LEARNING_TIERS.keys())
            }
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


# ========== 学习游戏化系统 ==========

GAME_LEVELS = {
    1: {'name': '小学士', 'required_points': 0, 'icon': '📚'},
    2: {'name': '秀才', 'required_points': 500, 'icon': '🎓'},
    3: {'name': '举人', 'required_points': 1500, 'icon': '🏆'},
    4: {'name': '贡士', 'required_points': 3000, 'icon': '🌟'},
    5: {'name': '进士', 'required_points': 5000, 'icon': '👑'},
    6: {'name': '榜眼', 'required_points': 8000, 'icon': '💎'},
    7: {'name': '探花', 'required_points': 12000, 'icon': '🏅'},
    8: {'name': '状元', 'required_points': 18000, 'icon': '👑'}
}

ACHIEVEMENTS = {
    'first_study': {'name': '初次学习', 'description': '完成第一次学习', 'points': 10, 'icon': '🎯'},
    'daily_streak_7': {'name': '连续学习7天', 'description': '连续7天每天学习', 'points': 50, 'icon': '🔥'},
    'daily_streak_30': {'name': '连续学习30天', 'description': '连续30天每天学习', 'points': 200, 'icon': '💪'},
    'accuracy_90': {'name': '准确率90%', 'description': '单次练习准确率达到90%以上', 'points': 30, 'icon': '🎯'},
    'perfect_day': {'name': '完美一天', 'description': '一天内完成所有推荐练习', 'points': 50, 'icon': '⭐'},
    'wrong_resolved_10': {'name': '纠错达人', 'description': '解决10道错题', 'points': 50, 'icon': '✅'},
    'master_point_10': {'name': '知识达人', 'description': '掌握10个知识点', 'points': 100, 'icon': '📖'},
    'exam_pass': {'name': '考试通过', 'description': '通过一次正式考试', 'points': 100, 'icon': '🎊'},
    'week_report': {'name': '周报达成', 'description': '连续4周生成学习周报', 'points': 80, 'icon': '📊'}
}

BONUS_POINTS = {
    'daily_login': 5,
    'correct_answer': 2,
    'wrong_resolved': 10,
    'first_correct_in_row': 5,
    'perfect_practice': 20,
    'study_hour': 10
}


class K12GameService:
    """K12学习游戏化服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_game_points ( user_id INTEGER PRIMARY KEY, total_points INTEGER DEFAULT 0, current_level INTEGER DEFAULT 1, daily_streak INTEGER DEFAULT 0, last_login_date TEXT, achievements TEXT DEFAULT '[]', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_point_transactions ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, transaction_type TEXT NOT NULL, points INTEGER NOT NULL, description TEXT, related_activity TEXT, created_at TEXT ) ''')
                conn.commit()
                logger.info('K12游戏化系统数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化游戏化数据库失败: {e}')

    def add_points(self, user_id: int, transaction_type: str, points: int,
                    description: str = '', related_activity: str = '') -> Dict[str, Any]:
        """添加游戏积分"""
        with self._lock:
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT OR REPLACE INTO k12_game_points (user_id, total_points, current_level, daily_streak, last_login_date, achievements, created_at, updated_at) VALUES (?, COALESCE((SELECT total_points FROM k12_game_points WHERE user_id = ?), 0) + ?, COALESCE((SELECT current_level FROM k12_game_points WHERE user_id = ?), 1), COALESCE((SELECT daily_streak FROM k12_game_points WHERE user_id = ?), 0), COALESCE((SELECT last_login_date FROM k12_game_points WHERE user_id = ?), ?), COALESCE((SELECT achievements FROM k12_game_points WHERE user_id = ?), '[]'), COALESCE((SELECT created_at FROM k12_game_points WHERE user_id = ?), ?), ?) ''', (user_id, user_id, points, user_id, user_id, user_id, now,
                          user_id, user_id, now, now))

                    cursor.execute(''' INSERT INTO k12_point_transactions (user_id, transaction_type, points, description, related_activity, created_at) VALUES (?, ?, ?, ?, ?, ?) ''', (user_id, transaction_type, points, description, related_activity, now))

                    conn.commit()

                level_info = self._calculate_level(user_id)
                self._check_achievements(user_id)

                return {
                    'success': True,
                    'user_id': user_id,
                    'points_added': points,
                    'total_points': level_info['total_points'],
                    'current_level': level_info['current_level'],
                    'level_name': level_info['level_name']
                }
            except Exception as e:
                logger.error(f'添加积分失败: {e}')
                return {'success': False, 'error': str(e)}

    def _calculate_level(self, user_id: int) -> Dict[str, Any]:
        """计算用户等级"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT total_points FROM k12_game_points WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                total_points = row[0] if row else 0

            current_level = 1
            for level, config in GAME_LEVELS.items():
                if total_points >= config['required_points']:
                    current_level = level

            with self._get_connection() as conn:
                conn.execute(''' UPDATE k12_game_points SET current_level = ? WHERE user_id = ? ''', (current_level, user_id))
                conn.commit()

            return {
                'total_points': total_points,
                'current_level': current_level,
                'level_name': GAME_LEVELS[current_level]['name'],
                'level_icon': GAME_LEVELS[current_level]['icon']
            }
        except Exception as e:
            logger.error(f'计算等级失败: {e}')
            return {'total_points': 0, 'current_level': 1, 'level_name': '小学士'}

    def _check_achievements(self, user_id: int):
        """检查成就解锁"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT achievements FROM k12_game_points WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                unlocked = json.loads(row[0]) if row and row[0] else []

            for achievement_key, config in ACHIEVEMENTS.items():
                if achievement_key in unlocked:
                    continue

                if self._check_achievement_condition(user_id, achievement_key):
                    unlocked.append(achievement_key)
                    self.add_points(user_id, 'achievement_unlock', config['points'],
                                    f'解锁成就: {config["name"]}', achievement_key)

            if unlocked:
                with self._get_connection() as conn:
                    conn.execute(''' UPDATE k12_game_points SET achievements = ? WHERE user_id = ? ''', (json.dumps(unlocked), user_id))
                    conn.commit()
        except Exception as e:
            logger.error(f'检查成就失败: {e}')

    def _check_achievement_condition(self, user_id: int, achievement_key: str) -> bool:
        """检查成就条件"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if achievement_key == 'first_study':
                    cursor.execute('SELECT COUNT(*) FROM k12_point_transactions WHERE user_id = ?', (user_id,))
                    return cursor.fetchone()[0] >= 1

                elif achievement_key == 'daily_streak_7':
                    cursor.execute('SELECT daily_streak FROM k12_game_points WHERE user_id = ?', (user_id,))
                    row = cursor.fetchone()
                    return row and row[0] >= 7

                elif achievement_key == 'daily_streak_30':
                    cursor.execute('SELECT daily_streak FROM k12_game_points WHERE user_id = ?', (user_id,))
                    row = cursor.fetchone()
                    return row and row[0] >= 30

                elif achievement_key == 'wrong_resolved_10':
                    cursor.execute('SELECT COUNT(*) FROM k12_wrong_questions WHERE user_id = ? AND resolved = 1',
                    (user_id,))
                    return cursor.fetchone()[0] >= 10

                elif achievement_key == 'master_point_10':
                    cursor.execute('SELECT COUNT( *) FROM k12_knowledge_mastery WHERE user_id = ? AND mastery_level >= 0.8', (user_id,))
                    return cursor.fetchone()[0] >= 10

            return False
        except Exception as e:
            logger.error(f'检查成就条件失败: {e}')
            return False

    def get_user_game_status(self, user_id: int) -> Dict[str, Any]:
        """获取用户游戏状态"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' SELECT total_points, current_level, daily_streak, achievements FROM k12_game_points WHERE user_id = ? ''', (user_id,))
                row = cursor.fetchone()

            if not row:
                return {
                    'success': True,
                    'user_id': user_id,
                    'total_points': 0,
                    'current_level': 1,
                    'level_name': '小学士',
                    'level_icon': '📚',
                    'daily_streak': 0,
                    'achievements': [],
                    'next_level_points': 500,
                    'points_to_next_level': 500
                }

            total_points, current_level, daily_streak, achievements = row
            achievements = json.loads(achievements) if achievements else []

            next_level = current_level + 1
            next_level_points = GAME_LEVELS.get(next_level, {}).get('required_points', 0)
            points_to_next = max(0, next_level_points - total_points)

            return {
                'success': True,
                'user_id': user_id,
                'total_points': total_points,
                'current_level': current_level,
                'level_name': GAME_LEVELS[current_level]['name'],
                'level_icon': GAME_LEVELS[current_level]['icon'],
                'daily_streak': daily_streak,
                'achievements': [
                    {**ACHIEVEMENTS[ach], 'achievement_key': ach}
                    for ach in achievements
                ],
                'next_level_points': next_level_points,
                'points_to_next_level': points_to_next,
                'available_achievements': [
                    {**ACHIEVEMENTS[key], 'achievement_key': key}
                    for key in ACHIEVEMENTS if key not in achievements
                ]
            }
        except Exception as e:
            logger.error(f'获取游戏状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def login_check_in(self, user_id: int) -> Dict[str, Any]:
        """每日登录签到"""
        with self._lock:
            now = datetime.now()
            today_str = now.strftime('%Y-%m-%d')

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT last_login_date, daily_streak FROM k12_game_points WHERE user_id = ?',
                    (user_id,))
                    row = cursor.fetchone()

                    new_streak = 1
                    if row and row[0]:
                        last_date = row[0].split('T')[0] if 'T' in row[0] else row[0]
                        last_date_obj = datetime.strptime(last_date, '%Y-%m-%d')
                        days_diff = (now - last_date_obj).days

                        if days_diff == 1:
                            new_streak = row[1] + 1
                        elif days_diff > 1:
                            new_streak = 1
                        else:
                            return {'success': True, 'message': '今日已签到', 'streak_unchanged': True}

                    cursor.execute(''' INSERT OR REPLACE INTO k12_game_points (user_id, total_points, current_level, daily_streak, last_login_date, achievements, created_at, updated_at) VALUES (?, COALESCE((SELECT total_points FROM k12_game_points WHERE user_id = ?), 0) + ?, COALESCE((SELECT current_level FROM k12_game_points WHERE user_id = ?), 1), ?, ?, COALESCE((SELECT achievements FROM k12_game_points WHERE user_id = ?), '[]'), COALESCE((SELECT created_at FROM k12_game_points WHERE user_id = ?), ?), ?) ''', (user_id, user_id, BONUS_POINTS['daily_login'], user_id,
                          new_streak, now.isoformat(), user_id, user_id, now.isoformat(), now.isoformat()))

                    cursor.execute(''' INSERT INTO k12_point_transactions (user_id, transaction_type, points, description, created_at) VALUES (?, 'daily_login', ?, '每日签到', ?) ''', (user_id, BONUS_POINTS['daily_login'], now.isoformat()))

                    conn.commit()

                return {
                    'success': True,
                    'user_id': user_id,
                    'points_added': BONUS_POINTS['daily_login'],
                    'daily_streak': new_streak,
                    'message': f'签到成功！连续学习{new_streak}天'
                }
            except Exception as e:
                logger.error(f'签到失败: {e}')
                return {'success': False, 'error': str(e)}


# ========== 综合素质评价系统 ==========

COMPREHENSIVE_DIMENSIONS = {
    '德': {'name': '品德修养', 'weight': 0.2, 'items': ['思想品德', '行为规范', '责任感', '团队合作']},
    '智': {'name': '学业水平', 'weight': 0.35, 'items': ['学科成绩', '学习能力', '创新思维', '知识应用']},
    '体': {'name': '身心健康', 'weight': 0.15, 'items': ['体育锻炼', '体能达标', '心理健康', '生活习惯']},
    '美': {'name': '艺术素养', 'weight': 0.15, 'items': ['艺术欣赏', '才艺特长', '审美能力', '创新表达']},
    '劳': {'name': '社会实践', 'weight': 0.15, 'items': ['劳动技能', '社会实践', '志愿服务', '职业体验']}
}


class K12ComprehensiveEvaluationService:
    """K12综合素质评价服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_comprehensive_eval ( eval_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, eval_period TEXT, moral_score REAL DEFAULT 0, intellectual_score REAL DEFAULT 0, physical_score REAL DEFAULT 0, aesthetic_score REAL DEFAULT 0, labor_score REAL DEFAULT 0, total_score REAL DEFAULT 0, eval_level TEXT DEFAULT '待评价', comments TEXT, created_by INTEGER, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_eval_items ( id INTEGER PRIMARY KEY AUTOINCREMENT, eval_id TEXT NOT NULL, dimension TEXT NOT NULL, item_name TEXT NOT NULL, score REAL DEFAULT 0, max_score INTEGER DEFAULT 100, comments TEXT, evidence TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_activity_records ( record_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, activity_type TEXT, activity_name TEXT, dimension TEXT, score_contribution REAL DEFAULT 0, description TEXT, evidence TEXT, verified INTEGER DEFAULT 0, created_at TEXT ) ''')
                conn.commit()
                logger.info('K12综合素质评价系统数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化综合素质评价数据库失败: {e}')

    def create_evaluation(self, user_id: int, eval_period: str, created_by: int = None) -> Dict[str, Any]:
        """创建综合素质评价"""
        with self._lock:
            eval_id = f'eval_{user_id}_{eval_period}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO k12_comprehensive_eval (eval_id, user_id, eval_period, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?) ''', (eval_id, user_id, eval_period, created_by, now, now))

                    for dimension, config in COMPREHENSIVE_DIMENSIONS.items():
                        for item in config['items']:
                            cursor.execute(''' INSERT INTO k12_eval_items (eval_id, dimension, item_name, max_score) VALUES (?, ?, ?, ?) ''', (eval_id, dimension, item, 100))

                    conn.commit()

                logger.info(f'创建综合素质评价: {eval_id}')
                return {
                    'success': True,
                    'eval_id': eval_id,
                    'user_id': user_id,
                    'eval_period': eval_period,
                    'dimensions': COMPREHENSIVE_DIMENSIONS
                }
            except Exception as e:
                logger.error(f'创建评价失败: {e}')
                return {'success': False, 'error': str(e)}

    def update_eval_item(self, eval_id: str, dimension: str, item_name: str,
                          score: float, comments: str = '', evidence: str = '') -> Dict[str, Any]:
        """更新评价项"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE k12_eval_items SET score = ?, comments = ?, evidence = ? WHERE eval_id = ? AND dimension = ? AND item_name = ? ''', (score, comments, evidence, eval_id, dimension, item_name))
                    conn.commit()

                self._calculate_total_score(eval_id)

                return {
                    'success': True,
                    'eval_id': eval_id,
                    'dimension': dimension,
                    'item_name': item_name,
                    'score': score
                }
            except Exception as e:
                logger.error(f'更新评价项失败: {e}')
                return {'success': False, 'error': str(e)}

    def _calculate_total_score(self, eval_id: str):
        """计算总分"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' SELECT dimension, AVG(score) FROM k12_eval_items WHERE eval_id = ? GROUP BY dimension ''', (eval_id,))
                dimension_scores = {row[0]: row[1] or 0 for row in cursor.fetchall()}

                total_score = 0
                for dimension, config in COMPREHENSIVE_DIMENSIONS.items():
                    total_score += (dimension_scores.get(dimension, 0) * config['weight'])

                eval_level = '待评价'
                if total_score >= 90:
                    eval_level = '优秀'
                elif total_score >= 80:
                    eval_level = '良好'
                elif total_score >= 60:
                    eval_level = '合格'
                else:
                    eval_level = '待改进'

                cursor.execute(''' UPDATE k12_comprehensive_eval SET moral_score = ?, intellectual_score = ?, physical_score = ?, aesthetic_score = ?, labor_score = ?, total_score = ?, eval_level = ?, updated_at = ? WHERE eval_id = ? ''', (dimension_scores.get('德', 0), dimension_scores.get('智', 0),
                      dimension_scores.get('体', 0), dimension_scores.get('美', 0),
                      dimension_scores.get('劳', 0), round(total_score, 2), eval_level,
                      datetime.now().isoformat(), eval_id))
                conn.commit()
        except Exception as e:
            logger.error(f'计算总分失败: {e}')

    def add_activity_record(self, user_id: int, activity_type: str, activity_name: str,
                             dimension: str, score_contribution: float = 0,
                             description: str = '', evidence: str = '') -> Dict[str, Any]:
        """添加活动记录"""
        record_id = f'act_{user_id}_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO k12_activity_records (record_id, user_id, activity_type, activity_name, dimension, score_contribution, description, evidence, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (record_id, user_id, activity_type, activity_name, dimension,
                      score_contribution, description, evidence, now))
                conn.commit()

            logger.info(f'添加活动记录: {record_id}')
            return {
                'success': True,
                'record_id': record_id,
                'user_id': user_id,
                'activity_name': activity_name,
                'dimension': dimension,
                'dimension_name': COMPREHENSIVE_DIMENSIONS[dimension]['name']
            }
        except Exception as e:
            logger.error(f'添加活动记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation(self, user_id: int, eval_period: str = None) -> Dict[str, Any]:
        """获取评价结果"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if eval_period:
                    cursor.execute(''' SELECT * FROM k12_comprehensive_eval WHERE user_id = ? AND eval_period = ? ''', (user_id, eval_period))
                else:
                    cursor.execute(''' SELECT * FROM k12_comprehensive_eval WHERE user_id = ? ORDER BY created_at DESC LIMIT 1 ''', (user_id,))

                row = cursor.fetchone()
                if not row:
                    return {'success': True, 'evaluations': []}

                eval_id = row[0]
                cursor.execute(''' SELECT dimension, item_name, score, max_score, comments, evidence FROM k12_eval_items WHERE eval_id = ? ''', (eval_id,))

                items = []
                for r in cursor.fetchall():
                    items.append({
                        'dimension': r[0],
                        'dimension_name': COMPREHENSIVE_DIMENSIONS[r[0]]['name'],
                        'item_name': r[1],
                        'score': r[2],
                        'max_score': r[3],
                        'comments': r[4],
                        'evidence': r[5]
                    })

                return {
                    'success': True,
                    'eval_id': row[0],
                    'user_id': row[1],
                    'eval_period': row[2],
                    'moral_score': row[3],
                    'intellectual_score': row[4],
                    'physical_score': row[5],
                    'aesthetic_score': row[6],
                    'labor_score': row[7],
                    'total_score': row[8],
                    'eval_level': row[9],
                    'comments': row[10],
                    'items': items,
                    'dimensions': COMPREHENSIVE_DIMENSIONS
                }
        except Exception as e:
            logger.error(f'获取评价失败: {e}')
            return {'success': False, 'error': str(e)}


# ========== 升学指导系统 ==========

COLLEGE_MAJORS = {
    '理科': ['计算机科学', '软件工程', '电子信息', '自动化', '机械工程', '土木工程', '化学工程', '材料科学'],
    '文科': ['工商管理', '经济学', '法学', '教育学', '新闻传播', '心理学', '历史学', '汉语言文学'],
    '综合': ['医学', '建筑学', '设计学', '金融学', '会计学', '国际商务', '环境工程', '生物工程']
}

CAREER_INTERESTS = {
    '现实型': {'name': '现实型', 'description': '喜欢动手操作，偏好具体事务', 'suggested_majors': ['机械工程', '土木工程', '电子信息', '计算机科学']},
    '研究型': {'name': '研究型', 'description': '喜欢思考分析，偏好学术研究', 'suggested_majors': ['计算机科学', '生物学', '物理学', '化学工程']},
    '艺术型': {'name': '艺术型', 'description': '富有创造力，偏好艺术表达', 'suggested_majors': ['设计学', '建筑学', '新闻传播', '音乐表演']},
    '社会型': {'name': '社会型', 'description': '喜欢与人交往，偏好社会服务', 'suggested_majors': ['教育学', '心理学', '法学', '社会工作']},
    '企业型': {'name': '企业型', 'description': '喜欢领导决策，偏好管理工作', 'suggested_majors': ['工商管理', '金融学', '国际商务', '市场营销']},
    '常规型': {'name': '常规型', 'description': '喜欢秩序规律，偏好事务处理', 'suggested_majors': ['会计学', '财务管理', '图书馆学', '信息管理']}
}


class K12CollegeAdmissionService:
    """K12升学指导服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_admission_records ( record_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, exam_type TEXT, target_province TEXT, target_majors TEXT, interest_type TEXT, estimated_score INTEGER, actual_score INTEGER, admission_result TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_major_recommendations ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, major TEXT, match_score REAL, reason TEXT, recommended_colleges TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS k12_subject_selections ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, grade TEXT, selected_subjects TEXT, reason TEXT, suggested_subjects TEXT, created_at TEXT ) ''')
                conn.commit()
                logger.info('K12升学指导系统数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化升学指导数据库失败: {e}')

    def set_admission_plan(self, user_id: int, exam_type: str, target_province: str,
                           estimated_score: int, interest_type: str = None) -> Dict[str, Any]:
        """设置升学计划"""
        record_id = f'adm_{user_id}_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO k12_admission_records (record_id, user_id, exam_type, target_province, interest_type, estimated_score, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (record_id, user_id, exam_type, target_province, interest_type,
                      estimated_score, now, now))
                conn.commit()

            recommendations = self._generate_major_recommendations(user_id, interest_type, estimated_score)

            logger.info(f'设置升学计划: {record_id}')
            return {
                'success': True,
                'record_id': record_id,
                'user_id': user_id,
                'exam_type': exam_type,
                'target_province': target_province,
                'estimated_score': estimated_score,
                'interest_type': interest_type,
                'interest_name': CAREER_INTERESTS.get(interest_type, {}).get('name'),
                'major_recommendations': recommendations
            }
        except Exception as e:
            logger.error(f'设置升学计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_major_recommendations(self, user_id: int, interest_type: str,
                                          estimated_score: int) -> List[Dict]:
        """生成专业推荐"""
        recommendations = []

        if interest_type and interest_type in CAREER_INTERESTS:
            interest_config = CAREER_INTERESTS[interest_type]
            for major in interest_config['suggested_majors'][:5]:
                match_score = self._calculate_major_match(user_id, major, interest_type)
                recommendations.append({
                    'major': major,
                    'match_score': round(match_score, 2),
                    'reason': f'与您的{interest_config["name"]}兴趣匹配',
                    'recommended_colleges': self._get_colleges_for_major(major, estimated_score)
                })

        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        return recommendations[:5]

    def _calculate_major_match(self, user_id: int, major: str, interest_type: str) -> float:
        """计算专业匹配度"""
        score = 50.0

        if interest_type:
            interest_config = CAREER_INTERESTS[interest_type]
            if major in interest_config['suggested_majors']:
                score += 30.0

        if major in COLLEGE_MAJORS['理科']:
            score += 10.0
        elif major in COLLEGE_MAJORS['文科']:
            score += 5.0

        return min(score, 100.0)

    def _get_colleges_for_major(self, major: str, score: int) -> List[str]:
        """获取专业对应的推荐院校"""
        if score >= 650:
            return ['清华大学', '北京大学', '复旦大学', '上海交通大学']
        elif score >= 600:
            return ['浙江大学', '南京大学', '中国人民大学', '武汉大学']
        elif score >= 550:
            return ['华中科技大学', '中山大学', '四川大学', '西安交通大学']
        elif score >= 500:
            return ['吉林大学', '山东大学', '中南大学', '厦门大学']
        else:
            return ['本地重点大学', '省内优秀高校']

    def recommend_subjects(self, user_id: int, grade: str) -> Dict[str, Any]:
        """推荐选科"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT interest_type FROM k12_admission_records WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                interest_type = row[0] if row else None

            grade_num = ''.join(c for c in grade if c.isdigit())
            if grade_num >= '10':
                if interest_type in CAREER_INTERESTS:
                    interest_config = CAREER_INTERESTS[interest_type]
                    if interest_config['name'] in ['现实型', '研究型']:
                        suggested = ['物理', '化学', '生物']
                    elif interest_config['name'] in ['艺术型']:
                        suggested = ['历史', '地理', '政治']
                    elif interest_config['name'] in ['社会型']:
                        suggested = ['历史', '政治', '地理']
                    elif interest_config['name'] in ['企业型']:
                        suggested = ['物理', '历史', '政治']
                    else:
                        suggested = ['物理', '化学', '历史']
                else:
                    suggested = ['物理', '化学', '历史']
            else:
                suggested = ['语文', '数学', '英语']

            record_id = None
            with self._get_connection() as conn:
                cursor = conn.cursor()
                record_id = f'sel_{user_id}_{grade}_{uuid.uuid4().hex[:8]}'
                cursor.execute(''' INSERT INTO k12_subject_selections (id, user_id, grade, selected_subjects, suggested_subjects, created_at) VALUES (NULL, ?, ?, ?, ?, ?) ''', (user_id, grade, json.dumps(suggested), json.dumps(suggested), datetime.now().isoformat()))
                conn.commit()

            return {
                'success': True,
                'user_id': user_id,
                'grade': grade,
                'suggested_subjects': suggested,
                'interest_type': interest_type,
                'interest_name': CAREER_INTERESTS.get(interest_type, {}).get('name'),
                'reason': self._generate_subject_reason(suggested, interest_type)
            }
        except Exception as e:
            logger.error(f'推荐选科失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_subject_reason(self, subjects: List[str], interest_type: str) -> str:
        """生成选科理由"""
        if interest_type:
            interest_config = CAREER_INTERESTS[interest_type]
            return f'基于您的{interest_config["name"]}兴趣倾向，推荐以上选科组合，有助于您未来的专业发展。'
        return '推荐选科组合，覆盖理工科和文史类专业选择范围。'


if __name__ == '__main__':
    service = K12EducationService()
    print('=' * 60)
    print('MTSCOS K12教育综合服务 v15.1.0 测试')
    print('=' * 60)

    print('\n1. 创建学生档案...')
    r = service.create_student_profile(2001, '8', parent_user_id=3001, class_id='class_8_1')
    print(f'   结果: {r["success"]} 年级组: {r.get("grade_group")}')

    print('\n2. 评估分层...')
    r = service.evaluate_tier(2001)
    print(f'   推荐分层: {r.get("recommended_tier")} ({r.get("tier_name")})')

    print('\n3. 添加知识点...')
    r = service.add_knowledge_point('数学', '8', '一元二次方程', '代数', 3)
    print(f'   结果: {r["success"]} 知识点ID: {r.get("point_id")}')
    kp_id = r.get('point_id', '')

    print('\n4. 更新掌握度...')
    r = service.update_mastery(2001, kp_id, True)
    print(f'   掌握度: {r.get("mastery_level")} 状态: {r.get("mastery_status")}')
    r = service.update_mastery(2001, kp_id, False)
    print(f'   掌握度: {r.get("mastery_level")} 状态: {r.get("mastery_status")}')

    print('\n5. 添加错题...')
    r = service.add_wrong_question(2001, '数学', 'q_001', point_id=kp_id,
                                     wrong_type='calculation_error', note='符号搞反')
    print(f'   结果: {r["success"]} 错题ID: {r.get("wrong_id")}')

    print('\n6. 获取薄弱知识点...')
    r = service.get_weak_points(2001, '数学')
    print(f'   薄弱点数: {r.get("count", 0)}')

    print('\n7. 发送家校消息...')
    r = service.send_home_school_message(2001, 3001, 'parent',
                                           'achievement', '本周表扬',
                                           '本周作业完成优秀，继续加油！')
    print(f'   结果: {r["success"]} 消息ID: {r.get("message_id")}')

    print('\n8. 获取家校消息...')
    r = service.get_home_school_messages(2001)
    print(f'   消息数: {r.get("count", 0)} 未读: {r.get("unread_count", 0)}')

    print('\n9. 生成周报...')
    r = service.generate_report(2001, 'weekly')
    print(f'   结果: {r["success"]} 报告ID: {r.get("report_id")}')
    print(f'   改进建议: {r.get("improvement_suggestions")}')

    print('\n10. 统计...')
    stats = service.get_statistics()
    print(f'   总学生: {stats.get("total_students")} 知识点: {stats.get("total_knowledge_points")}')
    print(f'   未解决错题: {stats.get("unresolved_wrong_questions")} 报告数: {stats.get("total_reports")}')
    print('\n' + '=' * 60)
    print('测试完成')
    print('=' * 60)
