# -*- coding: utf-8 -*-
"""
智能日程规划引擎
提供AI学习日程规划、考试倒计时、最优学习时间推荐、任务优先级排序、日程提醒
基于用户历史活跃时段智能推荐最佳学习时间
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_schedule_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SmartScheduleEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 任务优先级权重
PRIORITY_WEIGHTS = {
    'exam_preparation': 10,   # 考试备考（最高）
    'homework': 8,            # 作业
    'weak_subject_review': 7, # 薄弱科目复习
    'wrong_question_review': 6, # 错题复习
    'daily_practice': 5,      # 日常练习
    'knowledge_expansion': 3, # 知识拓展
    'collaboration': 2,       # 协作学习
    'rest': 1,                # 休息
}


class SmartScheduleEngine:
    """智能日程规划引擎 - AI驱动的学习时间管理"""

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
        logger.info("SmartScheduleEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 学习日程
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        task_type TEXT DEFAULT 'daily_practice',
                        subject TEXT,
                        priority INTEGER DEFAULT 5,
                        scheduled_start TEXT NOT NULL,
                        scheduled_end TEXT NOT NULL,
                        duration_minutes INTEGER,
                        status TEXT DEFAULT 'pending',
                        completed_at TEXT,
                        ai_recommended INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 考试倒计时
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_countdowns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        exam_id TEXT,
                        exam_name TEXT NOT NULL,
                        exam_subject TEXT,
                        exam_date TEXT NOT NULL,
                        target_score REAL DEFAULT 90,
                        importance INTEGER DEFAULT 5,
                        preparation_status TEXT DEFAULT 'not_started',
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, exam_name, exam_date)
                    )
                ''')

                # 用户活跃时段统计（按小时聚合）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_activity_hours (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        hour_of_day INTEGER NOT NULL,
                        activity_count INTEGER DEFAULT 0,
                        avg_performance REAL DEFAULT 0,
                        last_updated TEXT,
                        UNIQUE(user_id, hour_of_day)
                    )
                ''')

                # 学习时段推荐
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_time_recommendations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        recommended_date TEXT NOT NULL,
                        recommended_start TEXT NOT NULL,
                        recommended_end TEXT NOT NULL,
                        expected_performance REAL,
                        reason TEXT,
                        utilized INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 日程提醒
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS schedule_reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        schedule_id TEXT,
                        reminder_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT,
                        remind_at TEXT NOT NULL,
                        sent INTEGER DEFAULT 0,
                        ack INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ss_user ON study_schedules(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ss_date ON study_schedules(scheduled_start)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ec_user ON exam_countdowns(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ec_date ON exam_countdowns(exam_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_uah_user ON user_activity_hours(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sr_user ON schedule_reminders(user_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化日程引擎数据库失败: {e}")

    # ==================== 日程管理 ====================

    def create_schedule(self, user_id: str, title: str, scheduled_start: str,
                        scheduled_end: str, task_type: str = 'daily_practice',
                        subject: str = None, priority: int = None,
                        notes: str = None) -> Dict[str, Any]:
        """创建学习日程"""
        with self._lock:
            try:
                # 计算时长
                fmt = '%Y-%m-%dT%H:%M'
                try:
                    start_dt = datetime.strptime(scheduled_start[:16], fmt)
                    end_dt = datetime.strptime(scheduled_end[:16], fmt)
                    duration = int((end_dt - start_dt).total_seconds() / 60)
                except Exception:
                    duration = 60

                # 默认优先级按类型
                if priority is None:
                    priority = PRIORITY_WEIGHTS.get(task_type, 5)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO study_schedules
                        (user_id, title, task_type, subject, priority,
                         scheduled_start, scheduled_end, duration_minutes, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, title, task_type, subject, priority,
                          scheduled_start, scheduled_end, duration, notes))
                    sched_id = cursor.lastrowid
                    conn.commit()

                # 自动创建提醒
                self._create_reminder(user_id, str(sched_id), 'schedule',
                                      title, f'日程即将开始: {title}',
                                      scheduled_start, minutes_before=15)

                return {
                    'success': True,
                    'schedule_id': sched_id,
                    'message': '日程已创建',
                    'duration_minutes': duration
                }
            except Exception as e:
                logger.error(f"创建日程失败: {e}")
                return {'success': False, 'error': str(e)}

    def complete_schedule(self, schedule_id: int, performance: float = None) -> Dict[str, Any]:
        """完成日程"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE study_schedules
                        SET status = 'completed', completed_at = ?
                        WHERE id = ? AND status = 'pending'
                    ''', (datetime.now().isoformat(), schedule_id))

                    # 记录活跃时段
                    cursor.execute('''
                        SELECT user_id, scheduled_start FROM study_schedules WHERE id = ?
                    ''', (schedule_id,))
                    row = cursor.fetchone()
                    if row:
                        user_id, start_time = row
                        self._record_activity_hour(user_id, start_time, performance)
                    conn.commit()
                return {'success': True, 'schedule_id': schedule_id, 'message': '日程已完成'}
            except Exception as e:
                logger.error(f"完成日程失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_user_schedule(self, user_id: str, date: str = None,
                           status: str = None) -> Dict[str, Any]:
        """获取用户日程"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = 'SELECT id, title, task_type, subject, priority, scheduled_start, scheduled_end, duration_minutes, status, completed_at, ai_recommended, notes FROM study_schedules WHERE user_id = ?'
                params = [user_id]
                if date:
                    sql += ' AND date(scheduled_start) = ?'
                    params.append(date)
                if status:
                    sql += ' AND status = ?'
                    params.append(status)
                sql += ' ORDER BY scheduled_start ASC'
                cursor.execute(sql, params)
                schedules = [{
                    'id': r[0], 'title': r[1], 'task_type': r[2], 'subject': r[3],
                    'priority': r[4], 'start': r[5], 'end': r[6],
                    'duration': r[7], 'status': r[8], 'completed_at': r[9],
                    'ai_recommended': bool(r[10]), 'notes': r[11]
                } for r in cursor.fetchall()]
            return {'success': True, 'schedules': schedules, 'total': len(schedules)}
        except Exception as e:
            logger.error(f"获取日程失败: {e}")
            return {'success': False, 'error': str(e)}

    def delete_schedule(self, schedule_id: int) -> Dict[str, Any]:
        """删除日程"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM study_schedules WHERE id = ?', (schedule_id,))
                conn.commit()
            return {'success': True, 'message': '日程已删除'}
        except Exception as e:
            logger.error(f"删除日程失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 考试倒计时 ====================

    def add_exam_countdown(self, user_id: str, exam_name: str, exam_date: str,
                           exam_subject: str = None, exam_id: str = None,
                           target_score: float = 90, importance: int = 5,
                           notes: str = None) -> Dict[str, Any]:
        """添加考试倒计时"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO exam_countdowns
                    (user_id, exam_id, exam_name, exam_subject, exam_date,
                     target_score, importance, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, exam_id, exam_name, exam_subject, exam_date,
                      target_score, importance, notes))
                cd_id = cursor.lastrowid
                conn.commit()

            days_left = self._days_until(exam_date)
            return {
                'success': True,
                'countdown_id': cd_id,
                'days_left': days_left,
                'message': f'考试「{exam_name}」倒计时已添加，距今 {days_left} 天'
            }
        except Exception as e:
            logger.error(f"添加倒计时失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_exam_countdowns(self, user_id: str) -> Dict[str, Any]:
        """获取用户考试倒计时"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, exam_id, exam_name, exam_subject, exam_date,
                           target_score, importance, preparation_status, notes, created_at
                    FROM exam_countdowns WHERE user_id = ?
                    ORDER BY exam_date ASC
                ''', (user_id,))
                items = []
                now = datetime.now()
                for r in cursor.fetchall():
                    days_left = self._days_until(r[4])
                    items.append({
                        'id': r[0], 'exam_id': r[1], 'exam_name': r[2],
                        'subject': r[3], 'exam_date': r[4], 'target_score': r[5],
                        'importance': r[6], 'preparation_status': r[7],
                        'notes': r[8], 'created_at': r[9],
                        'days_left': days_left,
                        'is_upcoming': days_left >= 0,
                        'urgency': 'critical' if 0 <= days_left <= 3
                                  else ('high' if days_left <= 7
                                  else ('medium' if days_left <= 30 else 'low'))
                    })
            return {
                'success': True,
                'countdowns': items,
                'total': len(items),
                'upcoming': sum(1 for i in items if i['is_upcoming'])
            }
        except Exception as e:
            logger.error(f"获取倒计时失败: {e}")
            return {'success': False, 'error': str(e)}

    def update_preparation_status(self, countdown_id: int, status: str) -> Dict[str, Any]:
        """更新备考状态"""
        valid = ['not_started', 'in_progress', 'intensive', 'final_sprint', 'ready']
        if status not in valid:
            return {'success': False, 'message': f'状态无效，可选: {", ".join(valid)}'}
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE exam_countdowns SET preparation_status = ? WHERE id = ?
                ''', (status, countdown_id))
                conn.commit()
            return {'success': True, 'message': f'备考状态已更新为: {status}'}
        except Exception as e:
            logger.error(f"更新备考状态失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== AI智能推荐 ====================

    def generate_ai_schedule(self, user_id: str, date: str = None) -> Dict[str, Any]:
        """AI生成每日学习日程（基于历史活跃时段+考试倒计时+薄弱科目）"""
        with self._lock:
            try:
                target_date = date or datetime.now().strftime('%Y-%m-%d')

                # 1. 获取最佳学习时段
                best_hours = self._get_best_study_hours(user_id)

                # 2. 获取即将到来的考试
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT exam_name, exam_subject, exam_date, importance
                        FROM exam_countdowns WHERE user_id = ? AND exam_date >= ?
                        ORDER BY exam_date ASC LIMIT 3
                    ''', (user_id, target_date))
                    upcoming_exams = [{
                        'name': r[0], 'subject': r[1], 'date': r[2], 'importance': r[3],
                        'days_left': self._days_until(r[2])
                    } for r in cursor.fetchall()]

                # 3. 获取薄弱科目（从学习分析引擎）
                weak_subjects = self._get_weak_subjects(user_id)

                # 4. 生成日程
                schedules = []
                for hour_slot in best_hours[:4]:  # 推荐4个时段
                    hour = hour_slot['hour']
                    perf = hour_slot['performance']
                    start = f"{target_date}T{hour:02d}:00"
                    end = f"{target_date}T{hour:02d}:50"

                    # 根据时段性能和紧急度选择任务类型
                    if upcoming_exams and upcoming_exams[0]['days_left'] <= 7:
                        task_type = 'exam_preparation'
                        subj = upcoming_exams[0]['subject']
                        title = f"备考: {upcoming_exams[0]['name']}"
                    elif weak_subjects:
                        task_type = 'weak_subject_review'
                        subj = weak_subjects[0]
                        title = f"薄弱科目复习: {subj}"
                    else:
                        task_type = 'daily_practice'
                        subj = None
                        title = '日常练习'

                    priority = PRIORITY_WEIGHTS.get(task_type, 5)
                    reason = f"该时段历史表现 {perf:.1f}/100"

                    # 创建AI推荐日程
                    sched = self.create_schedule(
                        user_id, title, start, end, task_type, subj, priority
                    )
                    if sched.get('success'):
                        sched_id = sched['schedule_id']
                        # 标记为AI推荐
                        with sqlite3.connect(DATABASE_PATH) as conn:
                            cursor = conn.cursor()
                            cursor.execute('UPDATE study_schedules SET ai_recommended = 1 WHERE id = ?',
                                           (sched_id,))
                            # 记录推荐
                            cursor.execute('''
                                INSERT INTO study_time_recommendations
                                (user_id, recommended_date, recommended_start, recommended_end,
                                 expected_performance, reason)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (user_id, target_date, start, end, perf, reason))
                            conn.commit()
                        schedules.append({
                            'schedule_id': sched_id,
                            'title': title,
                            'start': start, 'end': end,
                            'task_type': task_type, 'subject': subj,
                            'priority': priority,
                            'expected_performance': round(perf, 1),
                            'reason': reason
                        })

                return {
                    'success': True,
                    'user_id': user_id,
                    'date': target_date,
                    'generated_schedules': schedules,
                    'upcoming_exams': upcoming_exams,
                    'weak_subjects': weak_subjects,
                    'best_hours': best_hours[:4],
                    'message': f'已生成 {len(schedules)} 个AI推荐日程'
                }
            except Exception as e:
                logger.error(f"生成AI日程失败: {e}")
                return {'success': False, 'error': str(e)}

    def _get_best_study_hours(self, user_id: str) -> List[Dict]:
        """获取用户最佳学习时段（基于历史数据）"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT hour_of_day, activity_count, avg_performance
                    FROM user_activity_hours WHERE user_id = ?
                    ORDER BY avg_performance DESC, activity_count DESC
                ''', (user_id,))
                rows = cursor.fetchall()

            if rows:
                return [{'hour': r[0], 'activity': r[1], 'performance': r[2] or 50}
                        for r in rows[:6]]
            # 无历史数据，返回默认最佳时段
            return [
                {'hour': 9, 'activity': 0, 'performance': 75},
                {'hour': 14, 'activity': 0, 'performance': 70},
                {'hour': 19, 'activity': 0, 'performance': 80},
                {'hour': 20, 'activity': 0, 'performance': 78},
                {'hour': 21, 'activity': 0, 'performance': 72},
                {'hour': 10, 'activity': 0, 'performance': 73},
            ]
        except Exception as e:
            logger.error(f"获取最佳时段失败: {e}")
            return [{'hour': 9, 'activity': 0, 'performance': 70}]

    def _get_weak_subjects(self, user_id: str) -> List[str]:
        """获取用户薄弱科目"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT subject FROM subject_proficiency
                    WHERE user_id = ? AND proficiency_score < 60
                    ORDER BY proficiency_score ASC LIMIT 3
                ''', (user_id,))
                return [r[0] for r in cursor.fetchall()]
        except Exception:
            return []

    def _record_activity_hour(self, user_id: str, time_str: str, performance: float = None):
        """记录活跃时段"""
        try:
            hour = datetime.fromisoformat(time_str).hour
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT activity_count, avg_performance FROM user_activity_hours
                    WHERE user_id = ? AND hour_of_day = ?
                ''', (user_id, hour))
                row = cursor.fetchone()
                now = datetime.now().isoformat()
                if row:
                    old_count, old_perf = row
                    new_count = old_count + 1
                    new_perf = ((old_perf or 50) * old_count + (performance or 70)) / new_count
                    cursor.execute('''
                        UPDATE user_activity_hours
                        SET activity_count = ?, avg_performance = ?, last_updated = ?
                        WHERE user_id = ? AND hour_of_day = ?
                    ''', (new_count, new_perf, now, user_id, hour))
                else:
                    cursor.execute('''
                        INSERT INTO user_activity_hours
                        (user_id, hour_of_day, activity_count, avg_performance, last_updated)
                        VALUES (?, ?, 1, ?, ?)
                    ''', (user_id, hour, performance or 70, now))
                conn.commit()
        except Exception as e:
            logger.error(f"记录活跃时段失败: {e}")

    # ==================== 日程提醒 ====================

    def _create_reminder(self, user_id: str, schedule_id: str, reminder_type: str,
                         title: str, message: str, remind_at: str,
                         minutes_before: int = 15):
        """创建提醒"""
        try:
            # 提前 minutes_before 分钟提醒
            dt = datetime.fromisoformat(remind_at[:19])
            remind_time = dt - timedelta(minutes=minutes_before)
            if remind_time < datetime.now():
                remind_time = datetime.now() + timedelta(seconds=5)

            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO schedule_reminders
                    (user_id, schedule_id, reminder_type, title, message, remind_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, schedule_id, reminder_type, title, message,
                      remind_time.isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"创建提醒失败: {e}")

    def get_pending_reminders(self, user_id: str = None) -> Dict[str, Any]:
        """获取待发送的提醒"""
        try:
            now = datetime.now().isoformat()
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = 'SELECT id, user_id, schedule_id, reminder_type, title, message, remind_at FROM schedule_reminders WHERE sent = 0 AND remind_at <= ?'
                params = [now]
                if user_id:
                    sql += ' AND user_id = ?'
                    params.append(user_id)
                sql += ' ORDER BY remind_at ASC LIMIT 50'
                cursor.execute(sql, params)
                reminders = [{
                    'id': r[0], 'user_id': r[1], 'schedule_id': r[2],
                    'type': r[3], 'title': r[4], 'message': r[5], 'remind_at': r[6]
                } for r in cursor.fetchall()]
            return {'success': True, 'reminders': reminders, 'total': len(reminders)}
        except Exception as e:
            logger.error(f"获取提醒失败: {e}")
            return {'success': False, 'error': str(e)}

    def mark_reminder_sent(self, reminder_id: int) -> Dict[str, Any]:
        """标记提醒已发送"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE schedule_reminders SET sent = 1 WHERE id = ?', (reminder_id,))
                conn.commit()
            return {'success': True, 'reminder_id': reminder_id}
        except Exception as e:
            logger.error(f"标记提醒失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 辅助方法 ====================

    def _days_until(self, date_str: str) -> int:
        """计算距离某天的天数"""
        try:
            target = datetime.strptime(date_str[:10], '%Y-%m-%d')
            now = datetime.now()
            return (target - now.replace(hour=0, minute=0, second=0, microsecond=0)).days
        except Exception:
            return 0

    # ==================== 统计 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """获取日程引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM study_schedules')
                total_schedules = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM study_schedules WHERE status='completed'")
                completed = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM study_schedules WHERE ai_recommended=1")
                ai_recommended = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM exam_countdowns')
                total_countdowns = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM exam_countdowns WHERE exam_date >= date('now')")
                upcoming_exams = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM user_activity_hours')
                activity_records = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM schedule_reminders WHERE sent=0')
                pending_reminders = cursor.fetchone()[0]

                # 完成率
                completion_rate = (completed / total_schedules * 100) if total_schedules > 0 else 0

            return {
                'success': True,
                'total_schedules': total_schedules,
                'completed_schedules': completed,
                'ai_recommended_schedules': ai_recommended,
                'completion_rate': round(completion_rate, 1),
                'total_countdowns': total_countdowns,
                'upcoming_exams': upcoming_exams,
                'activity_records': activity_records,
                'pending_reminders': pending_reminders
            }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}


smart_schedule_engine = SmartScheduleEngine()
