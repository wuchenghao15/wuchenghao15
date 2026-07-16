#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 成人教育综合服务 (v15.1.0)
====================================
针对成人教育用户的学习特点，提供职业导向学习、碎片化学习计划、
学分证书管理和学习进度追踪等综合服务。

核心能力：
1. 职业导向学习推荐 - 基于职业目标推荐科目和学习路径
2. 碎片化学习计划 - 适配工作日晚上/周末的灵活学习时间
3. 学分管理 - 学习活动累计学分
4. 证书发放 - 达标后自动发放学习证书
5. 成人学情分析 - 针对成人学习模式的分析
6. 学习目标管理 - 短期/中期/长期目标设定与追踪
7. 班级社群 - 成人学习班级和同伴互助
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'adult_education_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AdultEducation')


# ========== 成人教育配置 ==========

# 成人教育职业方向与科目映射
CAREER_PATHS = {
    'foreign_trade': {
        'name': '外贸方向',
        'description': '面向外贸行业的日语/英语能力提升',
        'recommended_subjects': ['日语', '日语听力', '英语', '商务沟通'],
        'target_level': 'N2',
        'estimated_months': 6
    },
    'tourism': {
        'name': '旅游方向',
        'description': '面向旅游行业的语言服务能力',
        'recommended_subjects': ['日语', '日语听力', '英语', '导游知识'],
        'target_level': 'N3',
        'estimated_months': 4
    },
    'it_japan': {
        'name': '对日IT方向',
        'description': '对日软件开发的语言+技术能力',
        'recommended_subjects': ['日语', '日语听力', 'IT专业日语', '技术文档'],
        'target_level': 'N2',
        'estimated_months': 8
    },
    'translation': {
        'name': '翻译方向',
        'description': '专业笔译/口译能力培养',
        'recommended_subjects': ['日语', '日语听力', '翻译技巧', '英语'],
        'target_level': 'N1',
        'estimated_months': 12
    },
    'general_upgrade': {
        'name': '学历提升',
        'description': '成人高考/自考等学历提升',
        'recommended_subjects': ['数学', '英语', '语文'],
        'target_level': '本科',
        'estimated_months': 24
    },
    'interest': {
        'name': '兴趣学习',
        'description': '兴趣导向的自主学习',
        'recommended_subjects': ['日语', '日语听力'],
        'target_level': 'N4',
        'estimated_months': 3
    }
}

# 成人教育科目分类
ADULT_SUBJECTS = {
    '日语': {
        'category': 'language',
        'level_system': 'N5-N1',
        'has_listening': True,
        'credits_per_hour': 1.0
    },
    '日语听力': {
        'category': 'language',
        'level_system': 'N5-N1',
        'has_listening': True,
        'credits_per_hour': 1.2
    },
    '英语': {
        'category': 'language',
        'level_system': 'A1-C2',
        'has_listening': True,
        'credits_per_hour': 1.0
    },
    '数学': {
        'category': 'foundation',
        'level_system': '初中-高中',
        'has_listening': False,
        'credits_per_hour': 1.5
    },
    '语文': {
        'category': 'foundation',
        'level_system': '初中-高中',
        'has_listening': False,
        'credits_per_hour': 1.0
    },
    '商务沟通': {
        'category': 'professional',
        'level_system': '初级-高级',
        'has_listening': False,
        'credits_per_hour': 1.3
    }
}

# 碎片化学习时段
STUDY_TIME_SLOTS = {
    'weekday_morning': {'name': '工作日早晨', 'start': '06:00', 'end': '08:00', 'recommended_minutes': 30},
    'weekday_noon': {'name': '工作日午休', 'start': '12:00', 'end': '13:30', 'recommended_minutes': 20},
    'weekday_evening': {'name': '工作日晚上', 'start': '19:00', 'end': '22:00', 'recommended_minutes': 60},
    'weekend_morning': {'name': '周末上午', 'start': '08:00', 'end': '12:00', 'recommended_minutes': 120},
    'weekend_afternoon': {'name': '周末下午', 'start': '14:00', 'end': '17:00', 'recommended_minutes': 90},
    'weekend_evening': {'name': '周末晚上', 'start': '18:00', 'end': '21:00', 'recommended_minutes': 60}
}

# 学分类型
CREDIT_TYPES = {
    'course_learning': {'name': '课程学习', 'credit_per_hour': 1.0, 'max_daily': 8},
    'exercise_practice': {'name': '练习做题', 'credit_per_hour': 1.5, 'max_daily': 6},
    'exam_pass': {'name': '考试通过', 'credit_per_exam': 5.0, 'max_daily': 20},
    'homework_submit': {'name': '作业提交', 'credit_per_homework': 2.0, 'max_daily': 10},
    'listening_practice': {'name': '听力训练', 'credit_per_hour': 1.2, 'max_daily': 4}
}

# 证书类型
CERTIFICATE_TYPES = {
    'subject_completion': {
        'name': '科目结业证书',
        'required_credits': 60,
        'required_accuracy': 0.7,
        'description': '完成单科目学习并达到要求'
    },
    'level_certification': {
        'name': '等级认证证书',
        'required_credits': 100,
        'required_accuracy': 0.8,
        'description': '达到指定等级能力认证'
    },
    'career_path': {
        'name': '职业方向证书',
        'required_credits': 200,
        'required_accuracy': 0.75,
        'description': '完成职业方向全部推荐科目'
    },
    'outstanding_learner': {
        'name': '优秀学员证书',
        'required_credits': 300,
        'required_accuracy': 0.85,
        'description': '累计学分和准确率均达到优秀标准'
    }
}


class AdultEducationService:
    """成人教育综合服务"""

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
                # 成人教育学情表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS adult_education_profiles (
                        user_id INTEGER PRIMARY KEY,
                        career_path TEXT,
                        study_goal TEXT,
                        target_level TEXT,
                        available_time_slots TEXT,
                        current_level TEXT,
                        total_credits REAL DEFAULT 0,
                        study_streak_days INTEGER DEFAULT 0,
                        last_study_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 学分记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS adult_credit_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        credit_type TEXT NOT NULL,
                        activity_id TEXT,
                        subject TEXT,
                        credits REAL NOT NULL,
                        study_duration_minutes INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                # 学习计划表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS adult_study_plans (
                        plan_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        plan_name TEXT,
                        subject TEXT,
                        target_level TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        weekly_hours INTEGER,
                        time_slots TEXT,
                        status TEXT DEFAULT 'active',
                        progress REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 证书表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS adult_certificates (
                        certificate_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        certificate_type TEXT NOT NULL,
                        subject TEXT,
                        level TEXT,
                        credits_achieved REAL,
                        accuracy_achieved REAL,
                        issued_at TEXT,
                        valid_until TEXT,
                        status TEXT DEFAULT 'issued'
                    )
                ''')
                # 学习目标表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS adult_study_goals (
                        goal_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        goal_type TEXT,
                        title TEXT,
                        description TEXT,
                        target_value REAL,
                        current_value REAL DEFAULT 0,
                        deadline TEXT,
                        status TEXT DEFAULT 'in_progress',
                        created_at TEXT,
                        completed_at TEXT
                    )
                ''')
                # 班级社群表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS adult_study_groups (
                        group_id TEXT PRIMARY KEY,
                        group_name TEXT,
                        career_path TEXT,
                        subject TEXT,
                        leader_id INTEGER,
                        member_count INTEGER DEFAULT 0,
                        max_members INTEGER DEFAULT 30,
                        description TEXT,
                        created_at TEXT
                    )
                ''')
                # 班级成员表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS adult_study_group_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        role TEXT DEFAULT 'member',
                        joined_at TEXT,
                        UNIQUE(group_id, user_id)
                    )
                ''')
                conn.commit()
                logger.info('成人教育服务数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化数据库失败: {e}')

    # ========== 职业导向学习 ==========

    def set_career_path(self, user_id: int, career_path: str,
                          target_level: str = None) -> Dict[str, Any]:
        """设置用户职业方向"""
        with self._lock:
            if career_path not in CAREER_PATHS:
                return {'success': False, 'error': f'未知职业方向: {career_path}'}

            path_config = CAREER_PATHS[career_path]
            target = target_level or path_config['target_level']
            now = datetime.now().isoformat()

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO adult_education_profiles
                        (user_id, career_path, target_level, updated_at, created_at)
                        VALUES (?, ?, ?, ?,
                            COALESCE((SELECT created_at FROM adult_education_profiles WHERE user_id = ?), ?))
                    ''', (user_id, career_path, target, now, user_id, now))
                    conn.commit()

                logger.info(f'用户 {user_id} 设置职业方向: {career_path} (目标: {target})')
                return {
                    'success': True,
                    'user_id': user_id,
                    'career_path': career_path,
                    'career_name': path_config['name'],
                    'target_level': target,
                    'recommended_subjects': path_config['recommended_subjects'],
                    'estimated_months': path_config['estimated_months']
                }
            except Exception as e:
                logger.error(f'设置职业方向失败: {e}')
                return {'success': False, 'error': str(e)}

    def get_career_recommendation(self, user_id: int) -> Dict[str, Any]:
        """获取职业方向推荐"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT career_path, current_level, total_credits FROM adult_education_profiles
                    WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()

            current_path = row[0] if row else None
            current_level = row[1] if row else 'N5'
            total_credits = row[2] if row else 0

            recommendations = []
            for path_key, path_config in CAREER_PATHS.items():
                match_score = self._calculate_career_match_score(
                    path_key, current_path, current_level, total_credits
                )
                recommendations.append({
                    'career_path': path_key,
                    'name': path_config['name'],
                    'description': path_config['description'],
                    'recommended_subjects': path_config['recommended_subjects'],
                    'target_level': path_config['target_level'],
                    'estimated_months': path_config['estimated_months'],
                    'match_score': match_score,
                    'is_current': path_key == current_path
                })

            recommendations.sort(key=lambda x: x['match_score'], reverse=True)
            return {
                'success': True,
                'recommendations': recommendations,
                'current_path': current_path,
                'current_level': current_level
            }
        except Exception as e:
            logger.error(f'获取职业推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_career_match_score(self, path_key: str, current_path: str,
                                         current_level: str, credits: float) -> float:
        score = 50.0
        if path_key == current_path:
            score += 30.0
        if credits > 100:
            score += 10.0
        if credits > 200:
            score += 10.0
        # 通用方向对初学者更友好
        if path_key == 'interest' and current_level in ('N5', 'N4', None):
            score += 15.0
        if path_key == 'general_upgrade' and credits < 50:
            score += 5.0
        return min(score, 100.0)

    # ========== 碎片化学习计划 ==========

    def create_study_plan(self, user_id: int, subject: str,
                            target_level: str, weekly_hours: int,
                            time_slots: List[str],
                            plan_name: str = None) -> Dict[str, Any]:
        """创建碎片化学习计划"""
        with self._lock:
            if subject not in ADULT_SUBJECTS:
                return {'success': False, 'error': f'未知科目: {subject}'}

            # 验证时段
            valid_slots = [s for s in time_slots if s in STUDY_TIME_SLOTS]
            if not valid_slots:
                return {'success': False, 'error': '未提供有效学习时段'}

            plan_id = f'plan_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()
            start_date = datetime.now().strftime('%Y-%m-%d')
            # 根据目标等级估算结束日期
            weeks_needed = self._estimate_weeks_to_target(subject, target_level, weekly_hours)
            end_date = (datetime.now() + timedelta(weeks=weeks_needed)).strftime('%Y-%m-%d')

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO adult_study_plans
                        (plan_id, user_id, plan_name, subject, target_level,
                         start_date, end_date, weekly_hours, time_slots, status, progress,
                         created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, ?, ?)
                    ''', (plan_id, user_id,
                          plan_name or f'{subject}学习计划-{target_level}',
                          subject, target_level,
                          start_date, end_date, weekly_hours,
                          json.dumps(valid_slots),
                          now, now))
                    conn.commit()

                logger.info(f'用户 {user_id} 创建学习计划: {plan_id} ({subject} -> {target_level})')
                return {
                    'success': True,
                    'plan_id': plan_id,
                    'subject': subject,
                    'target_level': target_level,
                    'start_date': start_date,
                    'end_date': end_date,
                    'weekly_hours': weekly_hours,
                    'time_slots': valid_slots,
                    'estimated_weeks': weeks_needed
                }
            except Exception as e:
                logger.error(f'创建学习计划失败: {e}')
                return {'success': False, 'error': str(e)}

    def _estimate_weeks_to_target(self, subject: str, target_level: str,
                                    weekly_hours: int) -> int:
        """估算达到目标等级所需周数"""
        # 基础估算：每个等级约需100小时学习
        level_hours = {
            'N5': 100, 'N4': 200, 'N3': 400, 'N2': 700, 'N1': 1000,
            '初中': 150, '高中': 300, '本科': 600,
            '初级': 100, '中级': 250, '高级': 450
        }
        needed_hours = level_hours.get(target_level, 200)
        if weekly_hours <= 0:
            weekly_hours = 5
        return max(needed_hours // weekly_hours, 4)

    def get_study_schedule(self, user_id: int, plan_id: str = None) -> Dict[str, Any]:
        """获取学习时间表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if plan_id:
                    cursor.execute('''
                        SELECT plan_id, subject, target_level, start_date, end_date,
                               weekly_hours, time_slots, progress, status
                        FROM adult_study_plans
                        WHERE user_id = ? AND plan_id = ?
                    ''', (user_id, plan_id))
                else:
                    cursor.execute('''
                        SELECT plan_id, subject, target_level, start_date, end_date,
                               weekly_hours, time_slots, progress, status
                        FROM adult_study_plans
                        WHERE user_id = ? AND status = 'active'
                        ORDER BY created_at DESC
                    ''', (user_id,))
                rows = cursor.fetchall()

            if not rows:
                return {'success': True, 'schedules': [], 'message': '无活跃学习计划'}

            schedules = []
            today = datetime.now().strftime('%Y-%m-%d')
            today_weekday = datetime.now().weekday()  # 0=周一, 6=周日

            for row in rows:
                plan_id_db, subject, target_level, start_date, end_date, \
                    weekly_hours, time_slots_json, progress, status = row
                time_slots = json.loads(time_slots_json) if time_slots_json else []

                # 生成今日推荐时段
                today_recommendations = []
                for slot_key in time_slots:
                    slot = STUDY_TIME_SLOTS.get(slot_key)
                    if slot:
                        today_recommendations.append({
                            'slot': slot_key,
                            'name': slot['name'],
                            'time_range': f'{slot["start"]}-{slot["end"]}',
                            'recommended_minutes': slot['recommended_minutes']
                        })

                # 判断今日是否为推荐学习日
                is_weekend = today_weekday >= 5
                weekend_slots = [s for s in time_slots if 'weekend' in s]
                weekday_slots = [s for s in time_slots if 'weekday' in s]
                today_slots = weekend_slots if is_weekend else weekday_slots

                schedules.append({
                    'plan_id': plan_id_db,
                    'subject': subject,
                    'target_level': target_level,
                    'start_date': start_date,
                    'end_date': end_date,
                    'weekly_hours': weekly_hours,
                    'progress': progress,
                    'status': status,
                    'today_date': today,
                    'is_study_day': len(today_slots) > 0,
                    'today_recommendations': today_recommendations,
                    'today_total_minutes': sum(STUDY_TIME_SLOTS[s]['recommended_minutes']
                                                 for s in today_slots if s in STUDY_TIME_SLOTS)
                })

            return {'success': True, 'schedules': schedules, 'count': len(schedules)}
        except Exception as e:
            logger.error(f'获取学习时间表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_plan_progress(self, plan_id: str, progress: float) -> Dict[str, Any]:
        """更新学习计划进度"""
        with self._lock:
            try:
                now = datetime.now().isoformat()
                progress = max(0.0, min(1.0, progress))
                status = 'completed' if progress >= 1.0 else 'active'
                with self._get_connection() as conn:
                    conn.execute('''
                        UPDATE adult_study_plans
                        SET progress = ?, status = ?, updated_at = ?
                        WHERE plan_id = ?
                    ''', (progress, status, now, plan_id))
                    conn.commit()
                return {'success': True, 'plan_id': plan_id, 'progress': progress, 'status': status}
            except Exception as e:
                logger.error(f'更新计划进度失败: {e}')
                return {'success': False, 'error': str(e)}

    # ========== 学分管理 ==========

    def add_credits(self, user_id: int, credit_type: str, credits: float,
                      subject: str = None, activity_id: str = None,
                      duration_minutes: int = 0) -> Dict[str, Any]:
        """增加学分"""
        with self._lock:
            if credit_type not in CREDIT_TYPES:
                return {'success': False, 'error': f'未知学分类型: {credit_type}'}

            config = CREDIT_TYPES[credit_type]
            now = datetime.now().isoformat()
            today = datetime.now().strftime('%Y-%m-%d')

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 检查今日该类型学分是否超限
                    cursor.execute('''
                        SELECT SUM(credits) FROM adult_credit_records
                        WHERE user_id = ? AND credit_type = ?
                          AND date(created_at) = ?
                    ''', (user_id, credit_type, today))
                    row = cursor.fetchone()
                    today_credits = row[0] if row and row[0] else 0

                    if today_credits + credits > config['max_daily']:
                        allowed = max(0, config['max_daily'] - today_credits)
                        return {
                            'success': False,
                            'error': f'今日{config["name"]}学分已达上限',
                            'today_credits': today_credits,
                            'max_daily': config['max_daily'],
                            'allowed_remaining': allowed
                        }

                    # 记录学分
                    cursor.execute('''
                        INSERT INTO adult_credit_records
                        (user_id, credit_type, activity_id, subject, credits, study_duration_minutes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, credit_type, activity_id, subject, credits, duration_minutes, now))

                    # 更新用户总学分
                    cursor.execute('''
                        INSERT INTO adult_education_profiles (user_id, total_credits, updated_at, created_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            total_credits = total_credits + ?,
                            updated_at = ?
                    ''', (user_id, credits, now, now, credits, now))

                    # 更新连续学习天数
                    self._update_study_streak(conn, user_id, today)

                    conn.commit()

                logger.info(f'用户 {user_id} 获得 {credits} 学分 ({credit_type})')
                return {
                    'success': True,
                    'user_id': user_id,
                    'credits_added': credits,
                    'credit_type': credit_type,
                    'subject': subject
                }
            except Exception as e:
                logger.error(f'增加学分失败: {e}')
                return {'success': False, 'error': str(e)}

    def _update_study_streak(self, conn, user_id: int, today: str):
        """更新连续学习天数"""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT study_streak_days, last_study_date FROM adult_education_profiles
            WHERE user_id = ?
        ''', (user_id,))
        row = cursor.fetchone()
        if row:
            streak, last_date = row
            if last_date == today:
                return  # 今日已更新
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            if last_date == yesterday:
                new_streak = (streak or 0) + 1
            else:
                new_streak = 1
            conn.execute('''
                UPDATE adult_education_profiles
                SET study_streak_days = ?, last_study_date = ?
                WHERE user_id = ?
            ''', (new_streak, today, user_id))

    def get_credit_summary(self, user_id: int) -> Dict[str, Any]:
        """获取学分汇总"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 总学分
                cursor.execute('''
                    SELECT total_credits, study_streak_days, last_study_date
                    FROM adult_education_profiles WHERE user_id = ?
                ''', (user_id,))
                profile = cursor.fetchone()

                # 按类型统计
                cursor.execute('''
                    SELECT credit_type, SUM(credits) as total, COUNT(*) as count
                    FROM adult_credit_records
                    WHERE user_id = ?
                    GROUP BY credit_type
                ''', (user_id,))
                type_stats = {row[0]: {'total': row[1], 'count': row[2]}
                                for row in cursor.fetchall()}

                # 本周学分
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute('''
                    SELECT SUM(credits) FROM adult_credit_records
                    WHERE user_id = ? AND created_at >= ?
                ''', (user_id, week_ago))
                week_credits = cursor.fetchone()[0] or 0

                # 按科目统计
                cursor.execute('''
                    SELECT subject, SUM(credits) FROM adult_credit_records
                    WHERE user_id = ? AND subject IS NOT NULL
                    GROUP BY subject
                ''', (user_id,))
                subject_stats = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'success': True,
                'user_id': user_id,
                'total_credits': profile[0] if profile else 0,
                'study_streak_days': profile[1] if profile else 0,
                'last_study_date': profile[2] if profile else None,
                'weekly_credits': week_credits,
                'by_type': {k: {'name': CREDIT_TYPES[k]['name'], **v}
                              for k, v in type_stats.items() if k in CREDIT_TYPES},
                'by_subject': subject_stats
            }
        except Exception as e:
            logger.error(f'获取学分汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证书管理 ==========

    def issue_certificate(self, user_id: int, certificate_type: str,
                            subject: str = None, level: str = None,
                            accuracy: float = 0.0) -> Dict[str, Any]:
        """发放证书"""
        with self._lock:
            if certificate_type not in CERTIFICATE_TYPES:
                return {'success': False, 'error': f'未知证书类型: {certificate_type}'}

            config = CERTIFICATE_TYPES[certificate_type]
            now = datetime.now().isoformat()

            try:
                # 获取用户学分
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT total_credits FROM adult_education_profiles WHERE user_id = ?
                    ''', (user_id,))
                    row = cursor.fetchone()
                    total_credits = row[0] if row else 0

                # 验证是否达标
                if total_credits < config['required_credits']:
                    return {
                        'success': False,
                        'error': '学分不足',
                        'required': config['required_credits'],
                        'current': total_credits,
                        'shortfall': config['required_credits'] - total_credits
                    }
                if accuracy < config['required_accuracy']:
                    return {
                        'success': False,
                        'error': '准确率不足',
                        'required': config['required_accuracy'],
                        'current': accuracy
                    }

                certificate_id = f'cert_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
                valid_until = (datetime.now() + timedelta(days=365 * 3)).isoformat()

                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO adult_certificates
                        (certificate_id, user_id, certificate_type, subject, level,
                         credits_achieved, accuracy_achieved, issued_at, valid_until, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued')
                    ''', (certificate_id, user_id, certificate_type, subject, level,
                          total_credits, accuracy, now, valid_until))
                    conn.commit()

                logger.info(f'用户 {user_id} 获得证书: {certificate_id} ({config["name"]})')
                return {
                    'success': True,
                    'certificate_id': certificate_id,
                    'certificate_name': config['name'],
                    'certificate_type': certificate_type,
                    'subject': subject,
                    'level': level,
                    'issued_at': now,
                    'valid_until': valid_until
                }
            except Exception as e:
                logger.error(f'发放证书失败: {e}')
                return {'success': False, 'error': str(e)}

    def list_certificates(self, user_id: int) -> Dict[str, Any]:
        """列出用户证书"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT certificate_id, certificate_type, subject, level,
                           credits_achieved, accuracy_achieved, issued_at, valid_until, status
                    FROM adult_certificates
                    WHERE user_id = ?
                    ORDER BY issued_at DESC
                ''', (user_id,))
                rows = cursor.fetchall()

            certificates = []
            for row in rows:
                cert_type = row[1]
                config = CERTIFICATE_TYPES.get(cert_type, {})
                certificates.append({
                    'certificate_id': row[0],
                    'certificate_type': cert_type,
                    'certificate_name': config.get('name', cert_type),
                    'subject': row[2],
                    'level': row[3],
                    'credits_achieved': row[4],
                    'accuracy_achieved': row[5],
                    'issued_at': row[6],
                    'valid_until': row[7],
                    'status': row[8]
                })
            return {'success': True, 'certificates': certificates, 'count': len(certificates)}
        except Exception as e:
            logger.error(f'列出证书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习目标管理 ==========

    def set_study_goal(self, user_id: int, goal_type: str, title: str,
                         target_value: float, deadline: str,
                         description: str = '') -> Dict[str, Any]:
        """设置学习目标"""
        with self._lock:
            goal_id = f'goal_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO adult_study_goals
                        (goal_id, user_id, goal_type, title, description, target_value,
                         current_value, deadline, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'in_progress', ?)
                    ''', (goal_id, user_id, goal_type, title, description,
                          target_value, deadline, now))
                    conn.commit()
                logger.info(f'用户 {user_id} 设置学习目标: {goal_id} ({title})')
                return {
                    'success': True, 'goal_id': goal_id, 'title': title,
                    'target_value': target_value, 'deadline': deadline
                }
            except Exception as e:
                logger.error(f'设置学习目标失败: {e}')
                return {'success': False, 'error': str(e)}

    def update_goal_progress(self, goal_id: str, current_value: float) -> Dict[str, Any]:
        """更新目标进度"""
        with self._lock:
            try:
                now = datetime.now().isoformat()
                status = 'completed' if current_value >= 1.0 else 'in_progress'
                completed_at = now if status == 'completed' else None
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT target_value FROM adult_study_goals WHERE goal_id = ?', (goal_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '目标不存在'}
                    target = row[0]
                    progress = current_value / target if target > 0 else 0
                    cursor.execute('''
                        UPDATE adult_study_goals
                        SET current_value = ?, status = ?, completed_at = COALESCE(?, completed_at)
                        WHERE goal_id = ?
                    ''', (current_value, status, completed_at, goal_id))
                    conn.commit()
                return {
                    'success': True, 'goal_id': goal_id,
                    'current_value': current_value, 'target_value': target,
                    'progress': round(progress, 4), 'status': status
                }
            except Exception as e:
                logger.error(f'更新目标进度失败: {e}')
                return {'success': False, 'error': str(e)}

    # ========== 班级社群 ==========

    def create_study_group(self, group_name: str, career_path: str,
                             leader_id: int, subject: str = None,
                             description: str = '', max_members: int = 30) -> Dict[str, Any]:
        """创建学习班级"""
        with self._lock:
            group_id = f'group_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO adult_study_groups
                        (group_id, group_name, career_path, subject, leader_id,
                         member_count, max_members, description, created_at)
                        VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (group_id, group_name, career_path, subject, leader_id,
                          max_members, description, now))
                    # 班长加入班级
                    cursor.execute('''
                        INSERT INTO adult_study_group_members
                        (group_id, user_id, role, joined_at)
                        VALUES (?, ?, 'leader', ?)
                    ''', (group_id, leader_id, now))
                    conn.commit()
                logger.info(f'创建学习班级: {group_id} ({group_name})')
                return {
                    'success': True, 'group_id': group_id, 'group_name': group_name,
                    'leader_id': leader_id, 'career_path': career_path
                }
            except Exception as e:
                logger.error(f'创建班级失败: {e}')
                return {'success': False, 'error': str(e)}

    def join_study_group(self, group_id: str, user_id: int) -> Dict[str, Any]:
        """加入班级"""
        with self._lock:
            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT member_count, max_members FROM adult_study_groups WHERE group_id = ?
                    ''', (group_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '班级不存在'}
                    if row[0] >= row[1]:
                        return {'success': False, 'error': '班级已满员'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO adult_study_group_members
                        (group_id, user_id, role, joined_at)
                        VALUES (?, ?, 'member', ?)
                    ''', (group_id, user_id, now))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            UPDATE adult_study_groups
                            SET member_count = member_count + 1
                            WHERE group_id = ?
                        ''', (group_id,))
                        conn.commit()
                        logger.info(f'用户 {user_id} 加入班级 {group_id}')
                        return {'success': True, 'group_id': group_id, 'user_id': user_id}
                    return {'success': False, 'error': '已加入该班级'}
            except Exception as e:
                logger.error(f'加入班级失败: {e}')
                return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self) -> Dict[str, Any]:
        """获取成人教育统计"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM adult_education_profiles')
                total_users = cursor.fetchone()[0]
                cursor.execute('SELECT career_path, COUNT(*) FROM adult_education_profiles GROUP BY career_path')
                career_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM adult_study_plans WHERE status = "active"')
                active_plans = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM adult_certificates')
                total_certs = cursor.fetchone()[0]
                cursor.execute('SELECT certificate_type, COUNT(*) FROM adult_certificates GROUP BY certificate_type')
                cert_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM adult_study_groups')
                total_groups = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(total_credits) FROM adult_education_profiles')
                total_credits = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM adult_study_goals WHERE status = "in_progress"')
                active_goals = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM adult_study_goals WHERE status = "completed"')
                completed_goals = cursor.fetchone()[0]

            return {
                'success': True,
                'total_users': total_users,
                'by_career_path': career_stats,
                'active_plans': active_plans,
                'total_certificates': total_certs,
                'by_certificate_type': cert_stats,
                'total_study_groups': total_groups,
                'total_credits_issued': total_credits,
                'active_goals': active_goals,
                'completed_goals': completed_goals,
                'available_career_paths': list(CAREER_PATHS.keys()),
                'available_subjects': list(ADULT_SUBJECTS.keys()),
                'available_time_slots': list(STUDY_TIME_SLOTS.keys())
            }
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = AdultEducationService()
    print('=' * 60)
    print('MTSCOS 成人教育综合服务 v15.1.0 测试')
    print('=' * 60)

    print('\n1. 设置职业方向...')
    r = service.set_career_path(1001, 'foreign_trade', 'N2')
    print(f'   结果: {r["success"]} 方向: {r.get("career_name")}')

    print('\n2. 获取职业推荐...')
    r = service.get_career_recommendation(1001)
    print(f'   推荐数: {len(r.get("recommendations", []))}')
    for rec in r.get('recommendations', [])[:3]:
        print(f'   - {rec["name"]} (匹配度: {rec["match_score"]})')

    print('\n3. 创建学习计划...')
    r = service.create_study_plan(1001, '日语', 'N3', 10,
                                    ['weekday_evening', 'weekend_morning'])
    print(f'   结果: {r["success"]} 计划ID: {r.get("plan_id")}')

    print('\n4. 获取学习时间表...')
    r = service.get_study_schedule(1001)
    print(f'   计划数: {r.get("count", 0)}')
    for s in r.get('schedules', []):
        print(f'   - {s["subject"]} 今日推荐: {s["today_total_minutes"]}分钟')

    print('\n5. 增加学分...')
    r = service.add_credits(1001, 'course_learning', 3.0, subject='日语', duration_minutes=120)
    print(f'   结果: {r["success"]} 学分: {r.get("credits_added")}')
    r = service.add_credits(1001, 'exercise_practice', 2.0, subject='日语听力')
    print(f'   结果: {r["success"]} 学分: {r.get("credits_added")}')

    print('\n6. 学分汇总...')
    r = service.get_credit_summary(1001)
    print(f'   总学分: {r.get("total_credits")} 连续学习: {r.get("study_streak_days")}天')

    print('\n7. 设置学习目标...')
    r = service.set_study_goal(1001, 'level', '达到N3水平', 100, '2026-12-31', '通过N3考试')
    print(f'   结果: {r["success"]} 目标ID: {r.get("goal_id")}')

    print('\n8. 发放证书...')
    r = service.issue_certificate(1001, 'subject_completion', subject='日语', level='N5', accuracy=0.85)
    print(f'   结果: {r["success"]} {r.get("certificate_name", r.get("error"))}')

    print('\n9. 创建班级...')
    r = service.create_study_group('日语N2冲刺班', 'foreign_trade', 1001, '日语', '一起冲刺N2')
    print(f'   结果: {r["success"]} 班级ID: {r.get("group_id")}')

    print('\n10. 统计...')
    stats = service.get_statistics()
    print(f'   总用户: {stats.get("total_users")} 总学分: {stats.get("total_credits_issued")}')
    print(f'   活跃计划: {stats.get("active_plans")} 证书总数: {stats.get("total_certificates")}')
    print('\n' + '=' * 60)
    print('测试完成')
    print('=' * 60)
