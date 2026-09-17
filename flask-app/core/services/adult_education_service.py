from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 成人教育综合服务 (v15.1.0) ==================================== 针对成人教育用户的学习特点，提供职业导向学习、碎片化学习计划、 学分证书管理和学习进度追踪等综合服务。  核心能力： 1. 职业导向学习推荐 - 基于职业目标推荐科目和学习路径 2. 碎片化学习计划 - 适配工作日晚上/周末的灵活学习时间 3. 学分管理 - 学习活动累计学分 4. 证书发放 - 达标后自动发放学习证书 5. 成人学情分析 - 针对成人学习模式的分析 6. 学习目标管理 - 短期/中期/长期目标设定与追踪 7. 班级社群 - 成人学习班级和同伴互助 """
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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS adult_education_profiles ( user_id INTEGER PRIMARY KEY, career_path TEXT, study_goal TEXT, target_level TEXT, available_time_slots TEXT, current_level TEXT, total_credits REAL DEFAULT 0, study_streak_days INTEGER DEFAULT 0, last_study_date TEXT, created_at TEXT, updated_at TEXT ) ''')
                # 学分记录表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS adult_credit_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, credit_type TEXT NOT NULL, activity_id TEXT, subject TEXT, credits REAL NOT NULL, study_duration_minutes INTEGER DEFAULT 0, created_at TEXT ) ''')
                # 学习计划表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS adult_study_plans ( plan_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, plan_name TEXT, subject TEXT, target_level TEXT, start_date TEXT, end_date TEXT, weekly_hours INTEGER, time_slots TEXT, status TEXT DEFAULT 'active', progress REAL DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                # 证书表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS adult_certificates ( certificate_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, certificate_type TEXT NOT NULL, subject TEXT, level TEXT, credits_achieved REAL, accuracy_achieved REAL, issued_at TEXT, valid_until TEXT, status TEXT DEFAULT 'issued' ) ''')
                # 学习目标表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS adult_study_goals ( goal_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, goal_type TEXT, title TEXT, description TEXT, target_value REAL, current_value REAL DEFAULT 0, deadline TEXT, status TEXT DEFAULT 'in_progress', created_at TEXT, completed_at TEXT ) ''')
                # 班级社群表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS adult_study_groups ( group_id TEXT PRIMARY KEY, group_name TEXT, career_path TEXT, subject TEXT, leader_id INTEGER, member_count INTEGER DEFAULT 0, max_members INTEGER DEFAULT 30, description TEXT, created_at TEXT ) ''')
                # 班级成员表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS adult_study_group_members ( id INTEGER PRIMARY KEY AUTOINCREMENT, group_id TEXT NOT NULL, user_id INTEGER NOT NULL, role TEXT DEFAULT 'member', joined_at TEXT, UNIQUE(group_id, user_id) ) ''')
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
                    cursor.execute(''' INSERT OR REPLACE INTO adult_education_profiles (user_id, career_path, target_level, updated_at, created_at) VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM adult_education_profiles WHERE user_id = ?), ?)) ''', (user_id, career_path, target, now, user_id, now))
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
                cursor.execute(''' SELECT career_path, current_level, total_credits FROM adult_education_profiles WHERE user_id = ? ''', (user_id,))
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
                    cursor.execute(''' INSERT INTO adult_study_plans (plan_id, user_id, plan_name, subject, target_level, start_date, end_date, weekly_hours, time_slots, status, progress, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, ?, ?) ''', (plan_id, user_id,
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
                    cursor.execute(''' SELECT plan_id, subject, target_level, start_date, end_date, weekly_hours, time_slots, progress, status FROM adult_study_plans WHERE user_id = ? AND plan_id = ? ''', (user_id, plan_id))
                else:
                    cursor.execute(''' SELECT plan_id, subject, target_level, start_date, end_date, weekly_hours, time_slots, progress, status FROM adult_study_plans WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC ''', (user_id,))
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
                    conn.execute(''' UPDATE adult_study_plans SET progress = ?, status = ?, updated_at = ? WHERE plan_id = ? ''', (progress, status, now, plan_id))
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
                    cursor.execute(''' SELECT SUM(credits) FROM adult_credit_records WHERE user_id = ? AND credit_type = ? AND date(created_at) = ? ''', (user_id, credit_type, today))
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
                    cursor.execute(''' INSERT INTO adult_credit_records (user_id, credit_type, activity_id, subject, credits, study_duration_minutes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (user_id, credit_type, activity_id, subject, credits, duration_minutes, now))

                    # 更新用户总学分
                    cursor.execute(''' INSERT INTO adult_education_profiles (user_id, total_credits, updated_at, created_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET total_credits = total_credits + ?, updated_at = ? ''', (user_id, credits, now, now, credits, now))

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
        cursor.execute(''' SELECT study_streak_days, last_study_date FROM adult_education_profiles WHERE user_id = ? ''', (user_id,))
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
            conn.execute(''' UPDATE adult_education_profiles SET study_streak_days = ?, last_study_date = ? WHERE user_id = ? ''', (new_streak, today, user_id))

    def get_credit_summary(self, user_id: int) -> Dict[str, Any]:
        """获取学分汇总"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 总学分
                cursor.execute(''' SELECT total_credits, study_streak_days, last_study_date FROM adult_education_profiles WHERE user_id = ? ''', (user_id,))
                profile = cursor.fetchone()

                # 按类型统计
                cursor.execute(''' SELECT credit_type, SUM(credits) as total, COUNT(*) as count FROM adult_credit_records WHERE user_id = ? GROUP BY credit_type ''', (user_id,))
                type_stats = {row[0]: {'total': row[1], 'count': row[2]}
                                for row in cursor.fetchall()}

                # 本周学分
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute(''' SELECT SUM(credits) FROM adult_credit_records WHERE user_id = ? AND created_at >= ? ''', (user_id, week_ago))
                week_credits = cursor.fetchone()[0] or 0

                # 按科目统计
                cursor.execute(''' SELECT subject, SUM(credits) FROM adult_credit_records WHERE user_id = ? AND subject IS NOT NULL GROUP BY subject ''', (user_id,))
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
                    cursor.execute(''' SELECT total_credits FROM adult_education_profiles WHERE user_id = ? ''', (user_id,))
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
                    conn.execute(''' INSERT INTO adult_certificates (certificate_id, user_id, certificate_type, subject, level, credits_achieved, accuracy_achieved, issued_at, valid_until, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued') ''', (certificate_id, user_id, certificate_type, subject, level,
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
                cursor.execute(''' SELECT certificate_id, certificate_type, subject, level, credits_achieved, accuracy_achieved, issued_at, valid_until, status FROM adult_certificates WHERE user_id = ? ORDER BY issued_at DESC ''', (user_id,))
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
                    conn.execute(''' INSERT INTO adult_study_goals (goal_id, user_id, goal_type, title, description, target_value, current_value, deadline, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'in_progress', ?) ''', (goal_id, user_id, goal_type, title, description,
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
                    cursor.execute(''' UPDATE adult_study_goals SET current_value = ?, status = ?, completed_at = COALESCE(?, completed_at) WHERE goal_id = ? ''', (current_value, status, completed_at, goal_id))
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
                    cursor.execute(''' INSERT INTO adult_study_groups (group_id, group_name, career_path, subject, leader_id, member_count, max_members, description, created_at) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?) ''', (group_id, group_name, career_path, subject, leader_id,
                          max_members, description, now))
                    # 班长加入班级
                    cursor.execute(''' INSERT INTO adult_study_group_members (group_id, user_id, role, joined_at) VALUES (?, ?, 'leader', ?) ''', (group_id, leader_id, now))
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
                    cursor.execute(''' SELECT member_count, max_members FROM adult_study_groups WHERE group_id = ? ''', (group_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '班级不存在'}
                    if row[0] >= row[1]:
                        return {'success': False, 'error': '班级已满员'}
                    cursor.execute(''' INSERT OR IGNORE INTO adult_study_group_members (group_id, user_id, role, joined_at) VALUES (?, ?, 'member', ?) ''', (group_id, user_id, now))
                    if cursor.rowcount > 0:
                        cursor.execute(''' UPDATE adult_study_groups SET member_count = member_count + 1 WHERE group_id = ? ''', (group_id,))
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


# ========== 企业培训系统 ==========

CORPORATE_TRAINING_TYPES = {
    'onboarding': {'name': '新员工入职培训', 'description': '公司文化、制度规范、岗位技能入门'},
    'skill_upgrade': {'name': '技能提升培训', 'description': '专业技能、管理能力、软技能提升'},
    'compliance': {'name': '合规培训', 'description': '法律法规、行业规范、公司政策培训'},
    'product': {'name': '产品培训', 'description': '新产品知识、技术原理、销售话术'},
    'leadership': {'name': '领导力培训', 'description': '团队管理、战略思维、决策能力'},
    'safety': {'name': '安全培训', 'description': '安全生产、消防安全、应急处理'}
}

CORPORATE_ROLES = {
    'ceo': {'name': 'CEO', 'description': '首席执行官'},
    'cto': {'name': 'CTO', 'description': '首席技术官'},
    'manager': {'name': '部门经理', 'description': '部门负责人'},
    'team_lead': {'name': '团队负责人', 'description': '项目/团队负责人'},
    'employee': {'name': '普通员工', 'description': '基层员工'},
    'intern': {'name': '实习生', 'description': '实习人员'}
}


class CorporateTrainingService:
    """企业培训服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS corporate_training_programs ( program_id TEXT PRIMARY KEY, company_id TEXT, program_name TEXT, training_type TEXT, target_role TEXT, duration_hours REAL, required_credits REAL, description TEXT, status TEXT DEFAULT 'active', created_by INTEGER, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS corporate_training_modules ( module_id TEXT PRIMARY KEY, program_id TEXT NOT NULL, module_name TEXT, module_order INTEGER, duration_hours REAL, description TEXT, required_score REAL DEFAULT 0.8, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS corporate_employee_training ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, program_id TEXT NOT NULL, company_id TEXT, employee_role TEXT, enrollment_date TEXT, completion_date TEXT, progress REAL DEFAULT 0, status TEXT DEFAULT 'in_progress', total_score REAL DEFAULT 0, completed_modules TEXT DEFAULT '[]', certificate_issued INTEGER DEFAULT 0, created_at TEXT, UNIQUE(user_id, program_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS corporate_companies ( company_id TEXT PRIMARY KEY, company_name TEXT, industry TEXT, employee_count INTEGER, contact_email TEXT, created_at TEXT ) ''')
                conn.commit()
                logger.info('企业培训系统数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化企业培训数据库失败: {e}')

    def create_company(self, company_id: str, company_name: str, industry: str,
                        employee_count: int = 0, contact_email: str = '') -> Dict[str, Any]:
        """创建企业"""
        now = datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT OR REPLACE INTO corporate_companies (company_id, company_name, industry, employee_count, contact_email, created_at) VALUES (?, ?, ?, ?, ?, ?) ''', (company_id, company_name, industry, employee_count, contact_email, now))
                conn.commit()
            logger.info(f'创建企业: {company_id}')
            return {'success': True, 'company_id': company_id, 'company_name': company_name}
        except Exception as e:
            logger.error(f'创建企业失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_training_program(self, company_id: str, program_name: str, training_type: str,
                                 target_role: str, duration_hours: float,
                                 required_credits: float = 0, description: str = '',
                                 created_by: int = None) -> Dict[str, Any]:
        """创建培训项目"""
        if training_type not in CORPORATE_TRAINING_TYPES:
            return {'success': False, 'error': f'未知培训类型: {training_type}'}

        program_id = f'prog_{company_id}_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO corporate_training_programs (program_id, company_id, program_name, training_type, target_role, duration_hours, required_credits, description, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (program_id, company_id, program_name, training_type, target_role,
                      duration_hours, required_credits, description, created_by, now, now))
                conn.commit()

            logger.info(f'创建培训项目: {program_id}')
            return {
                'success': True,
                'program_id': program_id,
                'program_name': program_name,
                'training_type': training_type,
                'training_type_name': CORPORATE_TRAINING_TYPES[training_type]['name'],
                'target_role': target_role,
                'duration_hours': duration_hours,
                'required_credits': required_credits
            }
        except Exception as e:
            logger.error(f'创建培训项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_training_module(self, program_id: str, module_name: str, module_order: int,
                             duration_hours: float, description: str = '',
                             required_score: float = 0.8) -> Dict[str, Any]:
        """添加培训模块"""
        module_id = f'mod_{program_id}_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO corporate_training_modules (module_id, program_id, module_name, module_order, duration_hours, description, required_score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (module_id, program_id, module_name, module_order, duration_hours,
                      description, required_score, now))
                conn.commit()

            logger.info(f'添加培训模块: {module_id}')
            return {
                'success': True,
                'module_id': module_id,
                'program_id': program_id,
                'module_name': module_name,
                'module_order': module_order
            }
        except Exception as e:
            logger.error(f'添加培训模块失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_employee(self, user_id: int, program_id: str, company_id: str,
                         employee_role: str = 'employee') -> Dict[str, Any]:
        """员工报名培训"""
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT OR IGNORE INTO corporate_employee_training (user_id, program_id, company_id, employee_role, enrollment_date, status, created_at) VALUES (?, ?, ?, ?, ?, 'in_progress', ?) ''', (user_id, program_id, company_id, employee_role, now, now))

                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f'员工 {user_id} 报名培训 {program_id}')
                    return {'success': True, 'user_id': user_id, 'program_id': program_id}
                return {'success': False, 'error': '已报名该培训'}
        except Exception as e:
            logger.error(f'报名培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_module(self, user_id: int, program_id: str, module_id: str,
                         score: float) -> Dict[str, Any]:
        """完成培训模块"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT required_score FROM corporate_training_modules WHERE module_id = ?',
                    (module_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '模块不存在'}

                    required_score = row[0]
                    status = 'passed' if score >= required_score else 'failed'

                    cursor.execute('SELECT completed_modules, progress FROM corporate_employee_training WHERE user_id = ? AND program_id = ?', (user_id,
                    program_id))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '未报名该培训'}

                    completed_modules = json.loads(row[0]) if row[0] else []
                    if module_id not in completed_modules:
                        completed_modules.append(module_id)

                    cursor.execute('SELECT COUNT(*) FROM corporate_training_modules WHERE program_id = ?', (program_id,
                    ))
                    total_modules = cursor.fetchone()[0]
                    new_progress = len(completed_modules) / total_modules * 100

                    cursor.execute(''' UPDATE corporate_employee_training SET completed_modules = ?, progress = ?, total_score = (total_score + ?) / 2, status = ?, updated_at = ? WHERE user_id = ? AND program_id = ? ''', (json.dumps(completed_modules), round(new_progress, 2), score,
                          'completed' if new_progress >= 100 else 'in_progress',
                          datetime.now().isoformat(), user_id, program_id))
                    conn.commit()

                return {
                    'success': True,
                    'user_id': user_id,
                    'program_id': program_id,
                    'module_id': module_id,
                    'score': score,
                    'status': status,
                    'progress': round(new_progress, 2)
                }
            except Exception as e:
                logger.error(f'完成模块失败: {e}')
                return {'success': False, 'error': str(e)}

    def get_employee_training_status(self, user_id: int) -> Dict[str, Any]:
        """获取员工培训状态"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' SELECT et.program_id, et.company_id, et.employee_role, et.progress, et.status, et.total_score, et.enrollment_date, et.completion_date, tp.program_name, tp.training_type, tp.duration_hours, tp.required_credits FROM corporate_employee_training et JOIN corporate_training_programs tp ON et.program_id = tp.program_id WHERE et.user_id = ? ''', (user_id,))

                trainings = []
                for row in cursor.fetchall():
                    trainings.append({
                        'program_id': row[0],
                        'company_id': row[1],
                        'employee_role': row[2],
                        'progress': row[3],
                        'status': row[4],
                        'total_score': row[5],
                        'enrollment_date': row[6],
                        'completion_date': row[7],
                        'program_name': row[8],
                        'training_type': row[9],
                        'training_type_name': CORPORATE_TRAINING_TYPES.get(row[9], {}).get('name'),
                        'duration_hours': row[10],
                        'required_credits': row[11]
                    })

            return {'success': True, 'trainings': trainings}
        except Exception as e:
            logger.error(f'获取培训状态失败: {e}')
            return {'success': False, 'error': str(e)}


# ========== 在线考试认证系统 ==========

EXAM_TYPES = {
    'certification': {'name': '资格认证考试', 'description': '行业资格认证、职业技能认证'},
    'proficiency': {'name': '能力水平考试', 'description': '语言能力、专业技能水平测试'},
    'assessment': {'name': '学习评估考试', 'description': '课程学习效果评估、阶段性测试'},
    'placement': {'name': '入学分级考试', 'description': '新生入学分级、水平摸底测试'}
}

EXAM_STATUS = {
    'draft': '草稿',
    'published': '发布',
    'ongoing': '进行中',
    'ended': '已结束'
}


class OnlineExamService:
    """在线考试认证服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS online_exams ( exam_id TEXT PRIMARY KEY, exam_name TEXT, exam_type TEXT, subject TEXT, duration_minutes INTEGER, total_score REAL, passing_score REAL, question_count INTEGER, allowed_attempts INTEGER DEFAULT 3, start_time TEXT, end_time TEXT, status TEXT DEFAULT 'draft', created_by INTEGER, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS online_exam_questions ( id INTEGER PRIMARY KEY AUTOINCREMENT, exam_id TEXT NOT NULL, question_id TEXT, question_text TEXT, question_type TEXT, options TEXT, correct_answer TEXT, score REAL, question_order INTEGER ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS online_exam_records ( record_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, exam_id TEXT NOT NULL, attempt_number INTEGER DEFAULT 1, start_time TEXT, end_time TEXT, duration_minutes REAL, score REAL DEFAULT 0, max_score REAL, passing_score REAL, passed INTEGER DEFAULT 0, answers TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS online_certifications ( cert_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, exam_id TEXT NOT NULL, certification_name TEXT, level TEXT, score REAL, issue_date TEXT, valid_until TEXT, status TEXT DEFAULT 'active', created_at TEXT ) ''')
                conn.commit()
                logger.info('在线考试认证系统数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化在线考试数据库失败: {e}')

    def create_exam(self, exam_name: str, exam_type: str, subject: str,
                     duration_minutes: int, total_score: float, passing_score: float,
                     question_count: int, created_by: int = None) -> Dict[str, Any]:
        """创建考试"""
        if exam_type not in EXAM_TYPES:
            return {'success': False, 'error': f'未知考试类型: {exam_type}'}

        exam_id = f'exam_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO online_exams (exam_id, exam_name, exam_type, subject, duration_minutes, total_score, passing_score, question_count, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (exam_id, exam_name, exam_type, subject, duration_minutes,
                      total_score, passing_score, question_count, created_by, now, now))
                conn.commit()

            logger.info(f'创建考试: {exam_id}')
            return {
                'success': True,
                'exam_id': exam_id,
                'exam_name': exam_name,
                'exam_type': exam_type,
                'exam_type_name': EXAM_TYPES[exam_type]['name'],
                'subject': subject,
                'duration_minutes': duration_minutes,
                'total_score': total_score,
                'passing_score': passing_score
            }
        except Exception as e:
            logger.error(f'创建考试失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_exam_question(self, exam_id: str, question_text: str, question_type: str,
                           options: List[str], correct_answer: str, score: float,
                           question_order: int) -> Dict[str, Any]:
        """添加考试题"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO online_exam_questions (exam_id, question_id, question_text, question_type, options, correct_answer, score, question_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (exam_id, f'q_{uuid.uuid4().hex[:8]}', question_text, question_type,
                      json.dumps(options), correct_answer, score, question_order))
                conn.commit()

            return {
                'success': True,
                'exam_id': exam_id,
                'question_text': question_text[:50],
                'question_type': question_type,
                'score': score
            }
        except Exception as e:
            logger.error(f'添加考试题失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_exam(self, user_id: int, exam_id: str) -> Dict[str, Any]:
        """开始考试"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, allowed_attempts, duration_minutes, total_score, passing_score FROM online_exams WHERE exam_id = ?', (exam_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '考试不存在'}
                    if row[0] != 'published':
                        return {'success': False, 'error': '考试未发布'}

                    cursor.execute('SELECT COUNT(*) FROM online_exam_records WHERE user_id = ? AND exam_id = ?',
                    (user_id, exam_id))
                    attempts = cursor.fetchone()[0]
                    if attempts >= row[1]:
                        return {'success': False, 'error': '已达到最大尝试次数'}

                    cursor.execute('SELECT * FROM online_exam_questions WHERE exam_id = ? ORDER BY question_order',
                    (exam_id,))
                    questions = []
                    for q in cursor.fetchall():
                        questions.append({
                            'id': q[0],
                            'question_text': q[3],
                            'question_type': q[4],
                            'options': json.loads(q[5]),
                            'score': q[7]
                        })

                    record_id = f'rec_{user_id}_{exam_id}_{attempts + 1}_{uuid.uuid4().hex[:8]}'
                    now = datetime.now().isoformat()
                    cursor.execute(''' INSERT INTO online_exam_records (record_id, user_id, exam_id, attempt_number, start_time, max_score, passing_score) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (record_id, user_id, exam_id, attempts + 1, now, row[3], row[4]))
                    conn.commit()

                return {
                    'success': True,
                    'record_id': record_id,
                    'exam_id': exam_id,
                    'attempt_number': attempts + 1,
                    'duration_minutes': row[2],
                    'questions': questions,
                    'start_time': now
                }
            except Exception as e:
                logger.error(f'开始考试失败: {e}')
                return {'success': False, 'error': str(e)}

    def submit_exam(self, record_id: str, answers: Dict) -> Dict[str, Any]:
        """提交考试"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id, exam_id, max_score, passing_score, start_time FROM online_exam_records WHERE record_id = ?', (record_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '考试记录不存在'}

                    user_id, exam_id, max_score, passing_score, start_time = row

                    cursor.execute('SELECT id, correct_answer, score FROM online_exam_questions WHERE exam_id = ?',
                    (exam_id,))
                    question_info = {r[0]: {'correct': r[1], 'score': r[2]} for r in cursor.fetchall()}

                    total_score = 0
                    for q_id, user_answer in answers.items():
                        q_id_int = int(q_id)
                        if q_id_int in question_info:
                            if str(user_answer) == str(question_info[q_id_int]['correct']):
                                total_score += question_info[q_id_int]['score']

                    passed = 1 if total_score >= passing_score else 0
                    end_time = datetime.now().isoformat()
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    duration = (end_dt - start_dt).total_seconds() / 60

                    cursor.execute(''' UPDATE online_exam_records SET end_time = ?, duration_minutes = ?, score = ?, passed = ?, answers = ? WHERE record_id = ? ''', (end_time, round(duration, 2), round(total_score, 2), passed,
                          json.dumps(answers), record_id))

                    if passed:
                        cert_id = f'cert_{user_id}_{exam_id}_{uuid.uuid4().hex[:8]}'
                        cursor.execute('SELECT exam_name FROM online_exams WHERE exam_id = ?', (exam_id,))
                        exam_name = cursor.fetchone()[0]
                        cursor.execute(''' INSERT INTO online_certifications (cert_id, user_id, exam_id, certification_name, level, score, issue_date, valid_until) VALUES (?, ?, ?, ?, '通过', ?, ?, ?) ''', (cert_id, user_id, exam_id, exam_name, round(total_score, 2),
                              end_time, (end_dt + timedelta(days=365)).isoformat()))

                    conn.commit()

                return {
                    'success': True,
                    'record_id': record_id,
                    'score': round(total_score, 2),
                    'max_score': max_score,
                    'passing_score': passing_score,
                    'passed': passed,
                    'duration_minutes': round(duration, 2),
                    'message': '考试通过，证书已发放' if passed else '考试未通过，请继续努力'
                }
            except Exception as e:
                logger.error(f'提交考试失败: {e}')
                return {'success': False, 'error': str(e)}

    def get_user_certifications(self, user_id: int) -> Dict[str, Any]:
        """获取用户证书"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' SELECT oc.cert_id, oc.certification_name, oc.level, oc.score, oc.issue_date, oc.valid_until, oc.status, oe.exam_type, oe.subject FROM online_certifications oc JOIN online_exams oe ON oc.exam_id = oe.exam_id WHERE oc.user_id = ? ''', (user_id,))

                certifications = []
                for row in cursor.fetchall():
                    certifications.append({
                        'cert_id': row[0],
                        'certification_name': row[1],
                        'level': row[2],
                        'score': row[3],
                        'issue_date': row[4],
                        'valid_until': row[5],
                        'status': row[6],
                        'exam_type': row[7],
                        'exam_type_name': EXAM_TYPES.get(row[7], {}).get('name'),
                        'subject': row[8]
                    })

            return {'success': True, 'certifications': certifications}
        except Exception as e:
            logger.error(f'获取证书失败: {e}')
            return {'success': False, 'error': str(e)}


# ========== 学习社群增强功能 ==========

COMMUNITY_ROLES = {
    'admin': {'name': '管理员', 'description': '社群最高权限'},
    'moderator': {'name': '版主', 'description': '内容管理、用户管理'},
    'instructor': {'name': '讲师', 'description': '提供教学指导'},
    'member': {'name': '普通成员', 'description': '参与讨论学习'}
}

COMMUNITY_ACTIVITIES = {
    'discussion': {'name': '话题讨论', 'description': '发起或参与话题讨论'},
    'resource_share': {'name': '资源分享', 'description': '分享学习资源'},
    'help_request': {'name': '求助提问', 'description': '提出问题寻求帮助'},
    'help_response': {'name': '解答帮助', 'description': '帮助解答他人问题'},
    'study_group': {'name': '小组学习', 'description': '参与学习小组'},
    'event_participation': {'name': '活动参与', 'description': '参与社群活动'}
}


class LearningCommunityService:
    """学习社群服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS community_groups ( group_id TEXT PRIMARY KEY, group_name TEXT, category TEXT, description TEXT, member_count INTEGER DEFAULT 0, max_members INTEGER DEFAULT 500, privacy TEXT DEFAULT 'public', created_by INTEGER, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS community_members ( id INTEGER PRIMARY KEY AUTOINCREMENT, group_id TEXT NOT NULL, user_id INTEGER NOT NULL, role TEXT DEFAULT 'member', joined_at TEXT, last_active_at TEXT, contribution_points INTEGER DEFAULT 0, UNIQUE(group_id, user_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS community_topics ( topic_id TEXT PRIMARY KEY, group_id TEXT NOT NULL, user_id INTEGER NOT NULL, title TEXT, content TEXT, topic_type TEXT, tags TEXT, views INTEGER DEFAULT 0, replies INTEGER DEFAULT 0, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS community_replies ( reply_id TEXT PRIMARY KEY, topic_id TEXT NOT NULL, user_id INTEGER NOT NULL, content TEXT, likes INTEGER DEFAULT 0, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS community_events ( event_id TEXT PRIMARY KEY, group_id TEXT NOT NULL, event_name TEXT, event_type TEXT, description TEXT, start_time TEXT, end_time TEXT, location TEXT, max_participants INTEGER DEFAULT 100, participant_count INTEGER DEFAULT 0, created_by INTEGER, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS community_event_participants ( id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL, user_id INTEGER NOT NULL, status TEXT DEFAULT 'registered', registered_at TEXT, UNIQUE(event_id, user_id) ) ''')
                conn.commit()
                logger.info('学习社群系统数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化学习社群数据库失败: {e}')

    def create_community(self, group_name: str, category: str, description: str = '',
                          max_members: int = 500, privacy: str = 'public',
                          created_by: int = None) -> Dict[str, Any]:
        """创建社群"""
        group_id = f'comm_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO community_groups (group_id, group_name, category, description, max_members, privacy, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (group_id, group_name, category, description, max_members,
                      privacy, created_by, now))

                if created_by:
                    cursor.execute(''' INSERT INTO community_members (group_id, user_id, role, joined_at, last_active_at) VALUES (?, ?, 'admin', ?, ?) ''', (group_id, created_by, now, now))
                    cursor.execute('UPDATE community_groups SET member_count = 1 WHERE group_id = ?', (group_id,))

                conn.commit()

            logger.info(f'创建社群: {group_id}')
            return {
                'success': True,
                'group_id': group_id,
                'group_name': group_name,
                'category': category,
                'privacy': privacy
            }
        except Exception as e:
            logger.error(f'创建社群失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_community(self, group_id: str, user_id: int) -> Dict[str, Any]:
        """加入社群"""
        with self._lock:
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT member_count, max_members, privacy FROM community_groups WHERE group_id = ?',
                    (group_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '社群不存在'}
                    if row[0] >= row[1]:
                        return {'success': False, 'error': '社群已满员'}

                    cursor.execute(''' INSERT OR IGNORE INTO community_members (group_id, user_id, role, joined_at, last_active_at) VALUES (?, ?, 'member', ?, ?) ''', (group_id, user_id, now, now))

                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE community_groups SET member_count = member_count + 1 WHERE group_id = ?',
                        (group_id,))
                        conn.commit()
                        logger.info(f'用户 {user_id} 加入社群 {group_id}')
                        return {'success': True, 'group_id': group_id, 'user_id': user_id}
                    return {'success': False, 'error': '已加入该社群'}
            except Exception as e:
                logger.error(f'加入社群失败: {e}')
                return {'success': False, 'error': str(e)}

    def create_topic(self, group_id: str, user_id: int, title: str, content: str,
                      topic_type: str = 'discussion', tags: List[str] = None) -> Dict[str, Any]:
        """创建话题"""
        topic_id = f'topic_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()
        tags = tags or []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO community_topics (topic_id, group_id, user_id, title, content, topic_type, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (topic_id, group_id, user_id, title, content, topic_type,
                      json.dumps(tags), now, now))
                conn.commit()

            logger.info(f'创建话题: {topic_id}')
            return {
                'success': True,
                'topic_id': topic_id,
                'title': title,
                'topic_type': topic_type,
                'tags': tags
            }
        except Exception as e:
            logger.error(f'创建话题失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_reply(self, topic_id: str, user_id: int, content: str) -> Dict[str, Any]:
        """回复话题"""
        reply_id = f'reply_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO community_replies (reply_id, topic_id, user_id, content, created_at) VALUES (?, ?, ?, ?, ?) ''', (reply_id, topic_id, user_id, content, now))

                cursor.execute(''' UPDATE community_topics SET replies = replies + 1, updated_at = ? WHERE topic_id = ? ''', (now, topic_id))

                conn.commit()

            logger.info(f'回复话题: {reply_id}')
            return {
                'success': True,
                'reply_id': reply_id,
                'topic_id': topic_id
            }
        except Exception as e:
            logger.error(f'回复话题失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_event(self, group_id: str, event_name: str, event_type: str,
                     description: str = '', start_time: str = '', end_time: str = '',
                     location: str = '', max_participants: int = 100,
                     created_by: int = None) -> Dict[str, Any]:
        """创建活动"""
        event_id = f'event_{uuid.uuid4().hex[:8]}'
        now = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO community_events (event_id, group_id, event_name, event_type, description, start_time, end_time, location, max_participants, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (event_id, group_id, event_name, event_type, description,
                      start_time, end_time, location, max_participants, created_by, now))
                conn.commit()

            logger.info(f'创建活动: {event_id}')
            return {
                'success': True,
                'event_id': event_id,
                'event_name': event_name,
                'event_type': event_type,
                'max_participants': max_participants
            }
        except Exception as e:
            logger.error(f'创建活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_event(self, event_id: str, user_id: int) -> Dict[str, Any]:
        """报名活动"""
        with self._lock:
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT participant_count, max_participants FROM community_events WHERE event_id = ?', (event_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '活动不存在'}
                    if row[0] >= row[1]:
                        return {'success': False, 'error': '活动已满员'}

                    cursor.execute(''' INSERT OR IGNORE INTO community_event_participants (event_id, user_id, status, registered_at) VALUES (?, ?, 'registered', ?) ''', (event_id, user_id, now))

                    if cursor.rowcount > 0:
                        cursor.execute(
                        'UPDATE community_events SET participant_count = participant_count + 1 WHERE event_id = ?',
                        (event_id,))
                        conn.commit()
                        logger.info(f'用户 {user_id} 报名活动 {event_id}')
                        return {'success': True, 'event_id': event_id, 'user_id': user_id}
                    return {'success': False, 'error': '已报名该活动'}
            except Exception as e:
                logger.error(f'报名活动失败: {e}')
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
