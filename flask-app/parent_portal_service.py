#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 家长端服务 (v15.4.0)
====================================
提供家长查看孩子学习情况、成绩、行为、考勤和家校沟通等综合服务。

核心能力：
1. 家长账户 - 家长注册、绑定子女、多子女管理
2. 学习概览 - 孩子学习数据汇总展示
3. 成绩查询 - 考试成绩、排名、趋势查看
4. 行为查看 - 行为记录、奖惩、品德评定
5. 考勤查看 - 出勤记录、请假管理
6. 家校沟通 - 与教师消息沟通
7. 学习建议 - AI生成的学习建议
8. 成人学员 - 成人教育自我服务端
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parent_portal_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ParentPortal')


# ========== 家长端配置 ==========

# 家长关系类型
PARENT_RELATIONS = {
    'father': {'name': '父亲', 'priority': 1},
    'mother': {'name': '母亲', 'priority': 1},
    'grandfather': {'name': '爷爷', 'priority': 2},
    'grandmother': {'name': '奶奶', 'priority': 2},
    'grandfather_m': {'name': '外公', 'priority': 2},
    'grandmother_m': {'name': '外婆', 'priority': 2},
    'guardian': {'name': '监护人', 'priority': 3},
    'other': {'name': '其他', 'priority': 4}
}

# 通知偏好
NOTIFICATION_PREFERENCES = {
    'score_published': {'name': '成绩发布通知', 'default': True},
    'behavior_record': {'name': '行为记录通知', 'default': True},
    'attendance_abnormal': {'name': '考勤异常通知', 'default': True},
    'homework_assigned': {'name': '作业布置通知', 'default': True},
    'exam_scheduled': {'name': '考试安排通知', 'default': True},
    'teacher_message': {'name': '教师消息通知', 'default': True},
    'school_notice': {'name': '学校公告通知', 'default': True},
    'fee_reminder': {'name': '缴费提醒通知', 'default': True},
    'weekly_report': {'name': '周报推送', 'default': True},
    'monthly_report': {'name': '月报推送', 'default': True}
}

# 请假类型
LEAVE_TYPES = {
    'sick': {'name': '病假', 'requires_cert': True, 'max_days': 30},
    'personal': {'name': '事假', 'requires_cert': False, 'max_days': 7},
    'family': {'name': '家庭事假', 'requires_cert': False, 'max_days': 3},
    'competition': {'name': '竞赛请假', 'requires_cert': True, 'max_days': 5},
    'activity': {'name': '活动请假', 'requires_cert': False, 'max_days': 3},
    'other': {'name': '其他', 'requires_cert': False, 'max_days': 3}
}

# 请假状态
LEAVE_STATUS = {
    'pending': '待审批',
    'approved': '已批准',
    'rejected': '已驳回',
    'cancelled': '已撤销',
    'expired': '已过期'
}

# 报告周期
REPORT_PERIODS = {
    'daily': {'name': '日报', 'description': '每日学习情况汇总'},
    'weekly': {'name': '周报', 'description': '每周学习情况总结'},
    'monthly': {'name': '月报', 'description': '每月学习情况分析'},
    'midterm': {'name': '期中报告', 'description': '期中学习总结报告'},
    'final': {'name': '期末报告', 'description': '期末学习总结报告'},
    'semester': {'name': '学期报告', 'description': '整学期学习总结'}
}

# 家长权限
PARENT_PERMISSIONS = {
    'view_scores': {'name': '查看成绩', 'default': True},
    'view_behavior': {'name': '查看行为', 'default': True},
    'view_attendance': {'name': '查看考勤', 'default': True},
    'view_homework': {'name': '查看作业', 'default': True},
    'view_schedule': {'name': '查看课表', 'default': True},
    'apply_leave': {'name': '申请请假', 'default': True},
    'message_teacher': {'name': '消息沟通', 'default': True},
    'view_report': {'name': '查看报告', 'default': True},
    'pay_fees': {'name': '在线缴费', 'default': True},
    'view_resources': {'name': '查看资源', 'default': False}
}


class ParentPortalService:
    """家长端服务"""

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
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_accounts (
                        parent_id TEXT PRIMARY KEY,
                        user_id INTEGER UNIQUE,
                        phone TEXT,
        email TEXT,
                        real_name TEXT,
                        id_number TEXT,
                        relation_type TEXT,
                        is_verified INTEGER DEFAULT 0,
                        verified_at TEXT,
                        notification_prefs TEXT,
                        permissions TEXT,
                        avatar_url TEXT,
                        last_login TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_student_relations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        relation_type TEXT DEFAULT 'father',
                        is_primary INTEGER DEFAULT 0,
                        can_pickup INTEGER DEFAULT 1,
                        emergency_contact INTEGER DEFAULT 1,
                        created_at TEXT,
                        UNIQUE(parent_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leave_requests (
                        leave_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        parent_id TEXT,
                        leave_type TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        total_days REAL,
                        reason TEXT NOT NULL,
                        attachment_url TEXT,
                        status TEXT DEFAULT 'pending',
                        approved_by INTEGER,
                        approved_by_name TEXT,
                        approved_at TEXT,
                        reject_reason TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_reports (
                        report_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        parent_id TEXT,
                        period TEXT NOT NULL,
                        period_start TEXT,
                        period_end TEXT,
                        title TEXT,
                        summary TEXT,
                        academic_data TEXT,
                        behavior_data TEXT,
                        attendance_data TEXT,
                        suggestions TEXT,
                        teacher_comment TEXT,
                        generated_at TEXT,
                        is_read INTEGER DEFAULT 0,
                        read_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_consents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        parent_id TEXT,
                        consent_type TEXT NOT NULL,
                        consent_value TEXT,
                        is_agreed INTEGER DEFAULT 0,
                        agreed_at TEXT,
                        expires_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_view_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        view_type TEXT,
                        view_content TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('家长端服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def register_parent(self, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            parent_id = f"prt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            prefs = json.dumps(NOTIFICATION_PREFERENCES, ensure_ascii=False)
            perms = json.dumps(PARENT_PERMISSIONS, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT parent_id FROM parent_accounts WHERE user_id = ?', (user_id,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该用户已注册为家长'}
                    cursor.execute('''
                        INSERT INTO parent_accounts (
                            parent_id, user_id, phone, email, real_name, id_number,
                            relation_type, is_verified, notification_prefs, permissions,
                            avatar_url, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'active', ?, ?)
                    ''', (parent_id, user_id, kwargs.get('phone'), kwargs.get('email'),
                          kwargs.get('real_name'), kwargs.get('id_number'),
                          kwargs.get('relation_type', 'father'),
                          prefs, perms, kwargs.get('avatar_url'), now, now))
                    conn.commit()
                    logger.info(f'注册家长账户: {parent_id}')
                    return {'success': True, 'parent_id': parent_id}
        except Exception as e:
            logger.error(f'注册家长失败: {e}')
            return {'success': False, 'error': str(e)}

    def bind_student(self, parent_id: str, student_id: int,
                      relation_type: str = 'father', is_primary: bool = False) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT parent_id FROM parent_accounts WHERE parent_id = ?', (parent_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '家长账户不存在'}
                    cursor.execute('SELECT id FROM parent_student_relations WHERE parent_id = ? AND student_id = ?', (parent_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该学生已绑定'}
                    if is_primary:
                        cursor.execute('UPDATE parent_student_relations SET is_primary = 0 WHERE parent_id = ?', (parent_id,))
                    cursor.execute('''
                        INSERT INTO parent_student_relations (parent_id, student_id, relation_type, is_primary, can_pickup, emergency_contact, created_at)
                        VALUES (?, ?, ?, ?, 1, 1, ?)
                    ''', (parent_id, student_id, relation_type, 1 if is_primary else 0, now))
                    conn.commit()
                    logger.info(f'绑定学生: 家长{parent_id} -> 学生{student_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'绑定学生失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_parent_children(self, parent_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT psr.*, pa.real_name as parent_name
                    FROM parent_student_relations psr
                    JOIN parent_accounts pa ON psr.parent_id = pa.parent_id
                    WHERE psr.parent_id = ?
                    ORDER BY psr.is_primary DESC, psr.created_at
                ''', (parent_id,))
                children = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'children': children, 'count': len(children)}
        except Exception as e:
            logger.error(f'获取家长子女失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_overview(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                overview = {'student_id': student_id}
                try:
                    cursor.execute('SELECT student_no, grade_level, current_class_id, status FROM student_profiles WHERE user_id = ?', (student_id,))
                    row = cursor.fetchone()
                    overview['profile'] = dict(row) if row else None
                except:
                    overview['profile'] = None
                try:
                    cursor.execute('''
                        SELECT class_id FROM class_students
                        WHERE student_id = ? AND enrollment_status = 'enrolled'
                    ''', (student_id,))
                    overview['class_id'] = cursor.fetchone()
                except:
                    overview['class_id'] = None
                try:
                    cursor.execute('''
                        SELECT AVG(score) as avg_score, COUNT(*) as exam_count,
                               MAX(score) as best_score, MIN(score) as lowest_score
                        FROM exam_scores WHERE student_id = ? AND is_absent = 0
                    ''', (student_id,))
                    row = cursor.fetchone()
                    overview['academic'] = dict(row) if row else None
                except:
                    overview['academic'] = None
                try:
                    cursor.execute('''
                        SELECT behavior_type, COUNT(*) as cnt
                        FROM behavior_records WHERE student_id = ?
                        GROUP BY behavior_type
                    ''', (student_id,))
                    overview['behavior'] = {r[0]: r[1] for r in cursor.fetchall()}
                except:
                    overview['behavior'] = {}
                try:
                    cursor.execute('''
                        SELECT status, COUNT(*) as cnt FROM attendance_records
                        WHERE student_id = ? AND record_date >= ?
                        GROUP BY status
                    ''', (student_id, (datetime.now() - timedelta(days=30)).isoformat()[:10]))
                    overview['attendance_30days'] = {r[0]: r[1] for r in cursor.fetchall()}
                except:
                    overview['attendance_30days'] = {}
                try:
                    cursor.execute('''
                        SELECT COUNT(*) as unread FROM messages
                        WHERE receiver_id = ? AND is_read = 0
                    ''', (student_id,))
                    overview['unread_messages'] = cursor.fetchone()[0]
                except:
                    overview['unread_messages'] = 0
                overview['generated_at'] = datetime.now().isoformat()
                return {'success': True, 'overview': overview}
        except Exception as e:
            logger.error(f'获取学生概览失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_leave(self, student_id: int, leave_type: str,
                     start_date: str, end_date: str, reason: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            leave_id = f"lv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            try:
                d1 = datetime.strptime(start_date, '%Y-%m-%d')
                d2 = datetime.strptime(end_date, '%Y-%m-%d')
                total_days = (d2 - d1).days + 1
            except:
                total_days = 1
            leave_config = LEAVE_TYPES.get(leave_type, {})
            if total_days > leave_config.get('max_days', 7):
                return {'success': False, 'error': f'{leave_config.get("name", "")}最多{leave_config.get("max_days", 7)}天'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO leave_requests (
                            leave_id, student_id, parent_id, leave_type,
                            start_date, end_date, total_days, reason,
                            attachment_url, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (leave_id, student_id, kwargs.get('parent_id'),
                          leave_type, start_date, end_date, total_days, reason,
                          kwargs.get('attachment_url'), now, now))
                    conn.commit()
                    logger.info(f'申请请假: {leave_id}')
                    return {'success': True, 'leave_id': leave_id, 'total_days': total_days}
        except Exception as e:
            logger.error(f'申请请假失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_leave(self, leave_id: str, approved_by: int,
                       approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE leave_requests SET
                            status = ?, approved_by = ?, approved_by_name = ?,
                            approved_at = ?, reject_reason = ?, updated_at = ?
                        WHERE leave_id = ? AND status = 'pending'
                    ''', (status, approved_by, kwargs.get('approved_by_name'),
                          now, kwargs.get('reject_reason'), now, leave_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审批请假: {leave_id} -> {status}')
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '请假申请不存在或已处理'}
        except Exception as e:
            logger.error(f'审批请假失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_leave_requests(self, student_id: int = None, parent_id: str = None,
                            status: str = None, page: int = 1,
                            page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM leave_requests WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if parent_id:
                    query += ' AND parent_id = ?'
                    params.append(parent_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                leaves = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'leaves': leaves, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取请假记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_scores(self, student_id: int, semester: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT es.*, e.exam_name, e.exam_type, e.exam_date, e.full_score
                    FROM exam_scores es
                    JOIN exams e ON es.exam_id = e.exam_id
                    WHERE es.student_id = ? AND es.is_absent = 0
                '''
                params = [student_id]
                if semester:
                    query += ' AND e.exam_date LIKE ?'
                    params.append(f'{semester}%')
                query += ' ORDER BY e.exam_date DESC'
                cursor.execute(query, params)
                scores = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'scores': scores, 'count': len(scores)}
        except Exception as e:
            logger.error(f'获取学生成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_behavior(self, student_id: int, days: int = 30) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                start_date = (datetime.now() - timedelta(days=days)).isoformat()[:10]
                cursor.execute('''
                    SELECT * FROM behavior_records
                    WHERE student_id = ? AND record_date >= ?
                    ORDER BY created_at DESC
                ''', (student_id, start_date))
                records = [dict(r) for r in cursor.fetchall()]
                positive = sum(1 for r in records if r['behavior_type'] == 'positive')
                negative = sum(1 for r in records if r['behavior_type'] == 'negative')
                total_score = sum(r.get('score_change', 0) for r in records)
                return {
                    'success': True,
                    'records': records,
                    'summary': {
                        'total': len(records),
                        'positive': positive,
                        'negative': negative,
                        'score_change': total_score
                    }
                }
        except Exception as e:
            logger.error(f'获取学生行为失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_attendance(self, student_id: int, days: int = 30) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                start_date = (datetime.now() - timedelta(days=days)).isoformat()[:10]
                cursor.execute('''
                    SELECT * FROM attendance_records
                    WHERE student_id = ? AND record_date >= ?
                    ORDER BY record_date DESC
                ''', (student_id, start_date))
                records = [dict(r) for r in cursor.fetchall()]
                stats = {}
                for r in records:
                    stats[r['status']] = stats.get(r['status'], 0) + 1
                total = len(records)
                present = stats.get('present', 0)
                return {
                    'success': True,
                    'records': records,
                    'stats': stats,
                    'attendance_rate': round(present / total * 100, 2) if total > 0 else 0,
                    'total_days': total
                }
        except Exception as e:
            logger.error(f'获取学生考勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_report(self, student_id: int, period: str,
                         parent_id: str = None, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            period_config = REPORT_PERIODS.get(period, {})
            if period == 'weekly':
                period_start = (datetime.now() - timedelta(days=7)).isoformat()[:10]
                period_end = datetime.now().isoformat()[:10]
            elif period == 'monthly':
                period_start = (datetime.now() - timedelta(days=30)).isoformat()[:10]
                period_end = datetime.now().isoformat()[:10]
            else:
                period_start = kwargs.get('period_start')
                period_end = kwargs.get('period_end')
            scores_data = self.get_student_scores(student_id)
            behavior_data = self.get_student_behavior(student_id)
            attendance_data = self.get_student_attendance(student_id)
            academic_data = json.dumps({
                'scores': scores_data.get('scores', [])[:10],
                'score_count': scores_data.get('count', 0)
            }, ensure_ascii=False)
            behavior_json = json.dumps({
                'records': behavior_data.get('records', [])[:10],
                'summary': behavior_data.get('summary', {})
            }, ensure_ascii=False)
            attendance_json = json.dumps({
                'stats': attendance_data.get('stats', {}),
                'attendance_rate': attendance_data.get('attendance_rate', 0)
            }, ensure_ascii=False)
            suggestions = self._generate_suggestions(scores_data, behavior_data, attendance_data)
            summary = self._generate_summary(period, scores_data, behavior_data, attendance_data)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO parent_reports (
                            report_id, student_id, parent_id, period,
                            period_start, period_end, title, summary,
                            academic_data, behavior_data, attendance_data,
                            suggestions, teacher_comment, generated_at, is_read
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    ''', (report_id, student_id, parent_id, period,
                          period_start, period_end,
                          f'{period_config.get("name", period)}学习报告',
                          summary, academic_data, behavior_json, attendance_json,
                          json.dumps(suggestions, ensure_ascii=False),
                          kwargs.get('teacher_comment'), now))
                    conn.commit()
                    logger.info(f'生成家长报告: {report_id}')
                    return {
                        'success': True,
                        'report_id': report_id,
                        'summary': summary,
                        'suggestions': suggestions
                    }
        except Exception as e:
            logger.error(f'生成报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_summary(self, period: str, scores: dict, behavior: dict, attendance: dict) -> str:
        parts = []
        score_count = scores.get('count', 0)
        if score_count > 0:
            avg_scores = [s.get('score', 0) for s in scores.get('scores', [])]
            if avg_scores:
                avg = sum(avg_scores) / len(avg_scores)
                parts.append(f'本期共参加{score_count}次考试，平均分{avg:.1f}分')
        behavior_summary = behavior.get('summary', {})
        pos = behavior_summary.get('positive', 0)
        neg = behavior_summary.get('negative', 0)
        if pos or neg:
            parts.append(f'行为记录：正面{pos}条，负面{neg}条')
        att_rate = attendance.get('attendance_rate', 0)
        if att_rate > 0:
            parts.append(f'出勤率{att_rate}%')
        if not parts:
            parts.append('本期暂无数据记录')
        return '。'.join(parts) + '。'

    def _generate_suggestions(self, scores: dict, behavior: dict, attendance: dict) -> list:
        suggestions = []
        score_list = scores.get('scores', [])
        if score_list:
            avg_score = sum(s.get('score', 0) for s in score_list) / len(score_list)
            if avg_score >= 90:
                suggestions.append('成绩优异，继续保持良好学习状态')
            elif avg_score >= 75:
                suggestions.append('成绩良好，建议加强薄弱科目练习')
            elif avg_score >= 60:
                suggestions.append('成绩及格，需要更多关注和辅导')
            else:
                suggestions.append('成绩不理想，建议与老师沟通制定提升计划')
        behavior_summary = behavior.get('summary', {})
        if behavior_summary.get('negative', 0) > behavior_summary.get('positive', 0):
            suggestions.append('近期负面行为较多，建议关注行为习惯培养')
        att_rate = attendance.get('attendance_rate', 100)
        if att_rate < 90:
            suggestions.append('出勤率偏低，请关注孩子到校情况')
        if not suggestions:
            suggestions.append('整体表现良好，继续保持')
        return suggestions

    def get_reports(self, student_id: int, parent_id: str = None,
                     period: str = None, page: int = 1,
                     page_size: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM parent_reports WHERE student_id = ?'
                params = [student_id]
                if parent_id:
                    query += ' AND parent_id = ?'
                    params.append(parent_id)
                if period:
                    query += ' AND period = ?'
                    params.append(period)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY generated_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                reports = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reports': reports, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取报告列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def read_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE parent_reports SET is_read = 1, read_at = ? WHERE report_id = ?', (now, report_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'标记报告已读失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_notification_prefs(self, parent_id: str, prefs: dict) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE parent_accounts SET notification_prefs = ?, updated_at = ? WHERE parent_id = ?',
                                 (json.dumps(prefs, ensure_ascii=False), now, parent_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新通知偏好失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_notification_prefs(self, parent_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT notification_prefs FROM parent_accounts WHERE parent_id = ?', (parent_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    return {'success': True, 'prefs': json.loads(row[0])}
                return {'success': True, 'prefs': NOTIFICATION_PREFERENCES}
        except Exception as e:
            logger.error(f'获取通知偏好失败: {e}')
            return {'success': False, 'error': str(e)}

    def log_parent_view(self, parent_id: str, student_id: int,
                         view_type: str, view_content: str = None,
                         ip_address: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO parent_view_logs (parent_id, student_id, view_type, view_content, ip_address, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (parent_id, student_id, view_type, view_content, ip_address, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录家长查看失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_parent(self, parent_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE parent_accounts SET is_verified = 1, verified_at = ? WHERE parent_id = ?', (now, parent_id))
                    conn.commit()
                    logger.info(f'验证家长: {parent_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'验证家长失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_parent_info(self, parent_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM parent_accounts WHERE parent_id = ?', (parent_id,))
                row = cursor.fetchone()
                if row:
                    parent = dict(row)
                    if parent.get('notification_prefs'):
                        parent['notification_prefs'] = json.loads(parent['notification_prefs'])
                    if parent.get('permissions'):
                        parent['permissions'] = json.loads(parent['permissions'])
                    return parent
                return None
        except Exception as e:
            logger.error(f'获取家长信息失败: {e}')
            return None
