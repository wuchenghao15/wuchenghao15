from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 心理健康服务 (v15.5.0) ==================================== 提供心理咨询预约、心理测评、情绪追踪和心理健康管理等综合服务。  核心能力： 1. 心理咨询 - 咨询师管理、在线预约、咨询记录 2. 心理测评 - 多种量表、自动评分、结果报告 3. 情绪追踪 - 每日情绪记录、情绪趋势 4. 危机干预 - 危机预警、紧急联系 5. 心理档案 - 心理健康档案 6. 团体辅导 - 团体心理活动 7. 成人心理 - 成人教育心理支持 8. K12心理 - 九年制心理健康教育 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mental_health_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MentalHealth')


# ========== 心理健康配置 ==========

# 咨询师资质
COUNSELOR_TITLES = {
    'intern': {'name': '实习咨询师', 'level': 1, 'max_daily': 3},
    'junior': {'name': '初级咨询师', 'level': 2, 'max_daily': 5},
    'middle': {'name': '中级咨询师', 'level': 3, 'max_daily': 6},
    'senior': {'name': '高级咨询师', 'level': 4, 'max_daily': 8},
    'expert': {'name': '专家咨询师', 'level': 5, 'max_daily': 6}
}

# 咨询类型
COUNSELING_TYPES = {
    'general': {'name': '一般心理困扰', 'duration': 50, 'fee': 0},
    'academic': {'name': '学业压力', 'duration': 50, 'fee': 0},
    'emotion': {'name': '情绪管理', 'duration': 50, 'fee': 0},
    'interpersonal': {'name': '人际关系', 'duration': 50, 'fee': 0},
    'family': {'name': '家庭关系', 'duration': 50, 'fee': 0},
    'career': {'name': '职业发展', 'duration': 50, 'fee': 0},
    'crisis': {'name': '危机干预', 'duration': 60, 'fee': 0},
    'group': {'name': '团体辅导', 'duration': 90, 'fee': 0}
}

# 预约状态
APPOINTMENT_STATUS = {
    'pending': {'name': '待确认', 'color': '#faad14'},
    'confirmed': {'name': '已确认', 'color': '#1890ff'},
    'in_progress': {'name': '进行中', 'color': '#722ed1'},
    'completed': {'name': '已完成', 'color': '#52c41a'},
    'cancelled': {'name': '已取消', 'color': '#8c8c8c'},
    'no_show': {'name': '未出席', 'color': '#f5222d'}
}

# 心理测评量表
ASSESSMENT_SCALES = {
    'phq9': {'name': 'PHQ-9抑郁量表', 'questions': 9, 'type': 'mood', 'duration_minutes': 5},
    'gad7': {'name': 'GAD-7焦虑量表', 'questions': 7, 'type': 'mood', 'duration_minutes': 5},
    'pss': {'name': 'PSS压力知觉量表', 'questions': 14, 'type': 'stress', 'duration_minutes': 8},
    'scl90': {'name': 'SCL-90症状自评', 'questions': 90, 'type': 'comprehensive', 'duration_minutes': 25},
    'self_esteem': {'name': '自尊量表', 'questions': 10, 'type': 'self', 'duration_minutes': 5},
    'sleep_quality': {'name': '睡眠质量量表', 'questions': 19, 'type': 'sleep', 'duration_minutes': 10},
    'burnout': {'name': '职业倦怠量表', 'questions': 22, 'type': 'work', 'duration_minutes': 10},
    'learning_burnout': {'name': '学习倦怠量表', 'questions': 16, 'type': 'learning', 'duration_minutes': 8},
    'social_anxiety': {'name': '社交焦虑量表', 'questions': 20, 'type': 'social', 'duration_minutes': 8},
    'test_anxiety': {'name': '考试焦虑量表', 'questions': 37, 'type': 'exam', 'duration_minutes': 10}
}

# 情绪类型
EMOTION_TYPES = {
    'happy': {'name': '开心', 'color': '#52c41a', 'level': 5},
    'calm': {'name': '平静', 'color': '#1890ff', 'level': 4},
    'neutral': {'name': '一般', 'color': '#8c8c8c', 'level': 3},
    'tired': {'name': '疲惫', 'color': '#faad14', 'level': 2},
    'sad': {'name': '低落', 'color': '#722ed1', 'level': 2},
    'anxious': {'name': '焦虑', 'color': '#fa8c16', 'level': 2},
    'angry': {'name': '生气', 'color': '#f5222d', 'level': 1},
    'stressed': {'name': '压力大', 'color': '#eb2f96', 'level': 1}
}

# 危机等级
CRISIS_LEVELS = {
    0: {'name': '正常', 'color': '#52c41a', 'action': '正常关注'},
    1: {'name': '轻度关注', 'color': '#faad14', 'action': '定期回访'},
    2: {'name': '中度预警', 'color': '#f5222d', 'action': '主动联系评估'},
    3: {'name': '高度预警', 'color': '#f5222d', 'action': '紧急干预'}
}

# 咨询方式
COUNSELING_METHODS = {
    'face_to_face': {'name': '面对面咨询', 'location': '心理咨询室'},
    'online_video': {'name': '视频咨询', 'location': '线上视频'},
    'online_chat': {'name': '文字咨询', 'location': '线上文字'},
    'phone': {'name': '电话咨询', 'location': '电话'},
    'group': {'name': '团体辅导', 'location': '团体活动室'}
}


class MentalHealthService:
    """心理健康服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS counselors ( counselor_id TEXT PRIMARY KEY, user_id INTEGER UNIQUE, name TEXT NOT NULL, gender TEXT, title TEXT, specialties TEXT, introduction TEXT, qualifications TEXT, max_daily INTEGER DEFAULT 5, is_active INTEGER DEFAULT 1, total_sessions INTEGER DEFAULT 0, rating REAL DEFAULT 0, rating_count INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS counselor_schedules ( id INTEGER PRIMARY KEY AUTOINCREMENT, counselor_id TEXT NOT NULL, weekday INTEGER NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL, is_available INTEGER DEFAULT 1, UNIQUE(counselor_id, weekday, start_time) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS counseling_appointments ( appointment_id TEXT PRIMARY KEY, counselor_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, counseling_type TEXT NOT NULL, counseling_method TEXT DEFAULT 'face_to_face', appointment_date TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL, status TEXT DEFAULT 'pending', location TEXT, issue_description TEXT, counselor_notes TEXT, diagnosis TEXT, treatment_plan TEXT, rating INTEGER, feedback TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS assessment_tests ( test_id TEXT PRIMARY KEY, scale_code TEXT NOT NULL, user_id INTEGER NOT NULL, user_name TEXT, answers TEXT, total_score REAL, dimension_scores TEXT, result_level TEXT, result_description TEXT, recommendations TEXT, completed_at TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS emotion_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, record_date TEXT NOT NULL, emotion_type TEXT NOT NULL, intensity INTEGER DEFAULT 3, note TEXT, triggers TEXT, sleep_quality INTEGER, sleep_hours REAL, stress_level INTEGER, created_at TEXT, UNIQUE(user_id, record_date) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS mental_health_profiles ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE NOT NULL, crisis_level INTEGER DEFAULT 0, risk_factors TEXT, total_counseling_count INTEGER DEFAULT 0, total_assessment_count INTEGER DEFAULT 0, last_counseling_date TEXT, last_assessment_date TEXT, assigned_counselor TEXT, notes TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS group_counseling ( group_id TEXT PRIMARY KEY, group_name TEXT NOT NULL, counselor_id TEXT NOT NULL, group_type TEXT, max_members INTEGER DEFAULT 10, current_members INTEGER DEFAULT 0, description TEXT, start_date TEXT, end_date TEXT, schedule TEXT, location TEXT, status TEXT DEFAULT 'recruiting', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS group_counseling_members ( id INTEGER PRIMARY KEY AUTOINCREMENT, group_id TEXT NOT NULL, user_id INTEGER NOT NULL, joined_at TEXT, status TEXT DEFAULT 'active', UNIQUE(group_id, user_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS crisis_alerts ( alert_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, crisis_level INTEGER NOT NULL, trigger_source TEXT, description TEXT, handler_id INTEGER, handler_name TEXT, status TEXT DEFAULT 'pending', handled_at TEXT, handling_notes TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS relaxation_resources ( resource_id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT, content_type TEXT, content TEXT, tags TEXT, views INTEGER DEFAULT 0, is_published INTEGER DEFAULT 1, created_at TEXT ) ''')
                conn.commit()
                logger.info('心理健康服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 咨询师管理 ==========

    def register_counselor(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            counselor_id = f"csl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            specialties = json.dumps(kwargs.get('specialties'),
            ensure_ascii=False) if kwargs.get('specialties') else None
            qualifications = json.dumps(kwargs.get('qualifications'),
            ensure_ascii=False) if kwargs.get('qualifications') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO counselors ( counselor_id, user_id, name, gender, title, specialties, introduction, qualifications, max_daily, is_active, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?) ''', (counselor_id, kwargs.get('user_id'), name,
                          kwargs.get('gender'), kwargs.get('title', 'junior'),
                          specialties, kwargs.get('introduction'),
                          qualifications, kwargs.get('max_daily', 5),
                          now, now))
                    conn.commit()
                    logger.info(f'注册咨询师: {name} ({counselor_id})')
                    return {'success': True, 'counselor_id': counselor_id}
        except Exception as e:
            logger.error(f'注册咨询师失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_counselor(self, counselor_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM counselors WHERE counselor_id = ?', (counselor_id,))
                row = cursor.fetchone()
                if row:
                    c = dict(row)
                    if c.get('specialties'):
                        c['specialties'] = json.loads(c['specialties'])
                    if c.get('qualifications'):
                        c['qualifications'] = json.loads(c['qualifications'])
                    return c
                return None
        except Exception as e:
            logger.error(f'获取咨询师失败: {e}')
            return None

    def list_counselors(self, title: str = None, is_active: int = 1,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM counselors WHERE is_active = ?'
                params = [is_active]
                if title:
                    query += ' AND title = ?'
                    params.append(title)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY rating DESC, total_sessions DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                counselors = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'counselors': counselors, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取咨询师列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def set_counselor_schedule(self, counselor_id: str, schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM counselor_schedules WHERE counselor_id = ?', (counselor_id,))
                    for s in schedules:
                        cursor.execute(''' INSERT OR IGNORE INTO counselor_schedules (counselor_id, weekday, start_time, end_time, is_available) VALUES (?, ?, ?, ?, 1) ''', (counselor_id, s['weekday'], s['start_time'], s['end_time']))
                    conn.commit()
                    return {'success': True, 'count': len(schedules)}
        except Exception as e:
            logger.error(f'设置咨询师排班失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 咨询预约 ==========

    def book_appointment(self, counselor_id: str, student_id: int,
                          counseling_type: str, appointment_date: str,
                          start_time: str, **kwargs) -> Dict[str, Any]:
        try:
            appointment_id = f"apt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            type_config = COUNSELING_TYPES.get(counseling_type, {})
            duration = type_config.get('duration', 50)
            start_dt = datetime.strptime(start_time, '%H:%M')
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.strftime('%H:%M')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active, max_daily FROM counselors WHERE counselor_id = ?', (counselor_id,
                    ))
                    counselor = cursor.fetchone()
                    if not counselor or not counselor[0]:
                        return {'success': False, 'error': '咨询师不可用'}
                    cursor.execute(''' SELECT COUNT(*) FROM counseling_appointments WHERE counselor_id = ? AND appointment_date = ? AND status IN (?, ?) ''', (counselor_id, appointment_date, 'pending', 'confirmed'))
                    today_count = cursor.fetchone()[0]
                    if today_count >= counselor[1]:
                        return {'success': False, 'error': '该咨询师当日预约已满'}
                    cursor.execute(''' SELECT appointment_id FROM counseling_appointments WHERE counselor_id = ? AND appointment_date = ? AND status IN (?, ?) AND ((start_time < ? AND end_time > ?) ''', (counselor_id, appointment_date, 'pending', 'confirmed', end_time, start_time))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该时段已被预约'}
                    method_config = COUNSELING_METHODS.get(kwargs.get('counseling_method', 'face_to_face'), {})
                    location = kwargs.get('location', method_config.get('location', ''))
                    cursor.execute(''' INSERT INTO counseling_appointments ( appointment_id, counselor_id, student_id, student_name, counseling_type, counseling_method, appointment_date, start_time, end_time, status, location, issue_description, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?) ''', (appointment_id, counselor_id, student_id,
                          kwargs.get('student_name'), counseling_type,
                          kwargs.get('counseling_method', 'face_to_face'),
                          appointment_date, start_time, end_time,
                          location, kwargs.get('issue_description'), now, now))
                    self._ensure_profile(cursor, student_id)
                    conn.commit()
                    logger.info(f'预约咨询: {appointment_id}')
                    return {'success': True, 'appointment_id': appointment_id, 'end_time': end_time}
        except Exception as e:
            logger.error(f'预约咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def _ensure_profile(self, cursor, user_id: int):
        now = datetime.now().isoformat()
        cursor.execute('SELECT id FROM mental_health_profiles WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute(''' INSERT INTO mental_health_profiles (user_id, crisis_level, created_at, updated_at) VALUES (?, 0, ?, ?) ''', (user_id, now, now))

    def confirm_appointment(self, appointment_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE counseling_appointments SET status = ?, updated_at = ? WHERE appointment_id = ? AND status = ? ''', ('confirmed', now, appointment_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预约不存在或状态不允许确认'}
        except Exception as e:
            logger.error(f'确认预约失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_appointment(self, appointment_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE counseling_appointments SET status = 'completed', counselor_notes = ?, diagnosis = ?, treatment_plan = ?, updated_at = ? WHERE appointment_id = ? AND status IN (?, ?) ''', (kwargs.get('counselor_notes'), kwargs.get('diagnosis'),
                          kwargs.get('treatment_plan'), now, appointment_id,
                          'confirmed', 'in_progress'))
                    if cursor.rowcount > 0:
                        cursor.execute('SELECT counselor_id, student_id FROM counseling_appointments WHERE appointment_id = ?', (appointment_id,))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute('UPDATE counselors SET total_sessions = total_sessions + 1, updated_at = ? WHERE counselor_id = ?', (now, row[0]))
                            cursor.execute(''' UPDATE mental_health_profiles SET total_counseling_count = total_counseling_count + 1, last_counseling_date = ?, updated_at = ? WHERE user_id = ? ''', (now[:10], now, row[1]))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预约不存在或状态不允许完成'}
        except Exception as e:
            logger.error(f'完成预约失败: {e}')
            return {'success': False, 'error': str(e)}

    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE counseling_appointments SET status = 'cancelled', updated_at = ? WHERE appointment_id = ? AND status IN (?, ?) ''', (now, appointment_id, 'pending', 'confirmed'))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'取消预约失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_appointments(self, user_id: int = None, counselor_id: str = None,
                          status: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM counseling_appointments WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND student_id = ?'
                    params.append(user_id)
                if counselor_id:
                    query += ' AND counselor_id = ?'
                    params.append(counselor_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY appointment_date DESC, start_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                appointments = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'appointments': appointments, 'total': total, 'page': page,
                'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预约列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def rate_appointment(self, appointment_id: str, rating: int, feedback: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE counseling_appointments SET rating = ?, feedback = ? WHERE appointment_id = ? AND status = ? ''', (rating, feedback, appointment_id, 'completed'))
                    if cursor.rowcount > 0:
                        cursor.execute('SELECT counselor_id FROM counseling_appointments WHERE appointment_id = ?',
                        (appointment_id,))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute(''' UPDATE counselors SET rating = (rating * rating_count + ?) / (rating_count + 1), rating_count = rating_count + 1, updated_at = ? WHERE counselor_id = ? ''', (rating, now, row[0]))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预约不存在或未完成'}
        except Exception as e:
            logger.error(f'评价预约失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理测评 ==========

    def take_assessment(self, user_id: int, scale_code: str,
                         answers: List[int], **kwargs) -> Dict[str, Any]:
        try:
            test_id = f"tst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            scale = ASSESSMENT_SCALES.get(scale_code)
            if not scale:
                return {'success': False, 'error': '量表不存在'}
            total_score = sum(answers)
            result = self._calculate_assessment_result(scale_code, total_score, answers)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO assessment_tests ( test_id, scale_code, user_id, user_name, answers, total_score, dimension_scores, result_level, result_description, recommendations, completed_at, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (test_id, scale_code, user_id, kwargs.get('user_name'),
                          json.dumps(answers), total_score,
                          json.dumps(result.get('dimensions', {}), ensure_ascii=False),
                          result.get('level'), result.get('description'),
                          json.dumps(result.get('recommendations', []), ensure_ascii=False),
                          now, now))
                    self._ensure_profile(cursor, user_id)
                    cursor.execute(''' UPDATE mental_health_profiles SET total_assessment_count = total_assessment_count + 1, last_assessment_date = ?, updated_at = ? WHERE user_id = ? ''', (now[:10], now, user_id))
                    self._check_crisis(cursor, user_id, scale_code, total_score, result.get('level', ''))
                    conn.commit()
                    logger.info(f'完成测评: {test_id} ({scale_code})')
                    return {
                        'success': True,
                        'test_id': test_id,
                        'total_score': total_score,
                        'result_level': result.get('level'),
                        'result_description': result.get('description'),
                        'recommendations': result.get('recommendations', [])
                    }
        except Exception as e:
            logger.error(f'完成测评失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_assessment_result(self, scale_code: str, total_score: float, answers: List[int]) -> Dict[str, Any]:
        result = {'level': 'normal', 'description': '', 'recommendations': [], 'dimensions': {}}
        if scale_code == 'phq9':
            if total_score <= 4:
                result['level'] = 'minimal'
                result['description'] = '极轻微抑郁症状'
            elif total_score <= 9:
                result['level'] = 'mild'
                result['description'] = '轻度抑郁'
                result['recommendations'].append('建议关注情绪变化，适当运动')
            elif total_score <= 14:
                result['level'] = 'moderate'
                result['description'] = '中度抑郁'
                result['recommendations'].append('建议寻求专业心理咨询')
            elif total_score <= 19:
                result['level'] = 'moderately_severe'
                result['description'] = '中重度抑郁'
                result['recommendations'].append('强烈建议寻求专业帮助')
            else:
                result['level'] = 'severe'
                result['description'] = '重度抑郁'
                result['recommendations'].append('请立即寻求专业心理治疗')
        elif scale_code == 'gad7':
            if total_score <= 4:
                result['level'] = 'minimal'
                result['description'] = '极轻微焦虑'
            elif total_score <= 9:
                result['level'] = 'mild'
                result['description'] = '轻度焦虑'
                result['recommendations'].append('建议学习放松技巧')
            elif total_score <= 14:
                result['level'] = 'moderate'
                result['description'] = '中度焦虑'
                result['recommendations'].append('建议寻求专业评估')
            else:
                result['level'] = 'severe'
                result['description'] = '重度焦虑'
                result['recommendations'].append('强烈建议专业治疗')
        else:
            result['description'] = f'总分{total_score}分'
        return result

    def _check_crisis(self, cursor, user_id: int, scale_code: str, score: float, level: str):
        crisis_level = 0
        if level in ('moderate', 'moderately_severe', 'severe'):
            crisis_level = 2 if level == 'severe' else 1
            alert_id = f"crs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            cursor.execute(''' INSERT INTO crisis_alerts ( alert_id, user_id, crisis_level, trigger_source, description, status, created_at ) VALUES (?, ?, ?, 'assessment', ?, '?', 'pending', ?) ''', (alert_id, user_id, crisis_level, f'{scale_code}测评结果{level}', now))
            cursor.execute(''' UPDATE mental_health_profiles SET crisis_level = MAX(crisis_level, ?), updated_at = ? WHERE user_id = ? ''', (crisis_level, now, user_id))

    def get_assessment_history(self, user_id: int, scale_code: str = None,
                                 page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM assessment_tests WHERE user_id = ?'
                params = [user_id]
                if scale_code:
                    query += ' AND scale_code = ?'
                    params.append(scale_code)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY completed_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tests = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tests': tests, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取测评历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 情绪追踪 ==========

    def record_emotion(self, user_id: int, emotion_type: str,
                        record_date: str = None, **kwargs) -> Dict[str, Any]:
        try:
            record_date = record_date or datetime.now().strftime('%Y-%m-%d')
            now = datetime.now().isoformat()
            triggers = json.dumps(kwargs.get('triggers'), ensure_ascii=False) if kwargs.get('triggers') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO emotion_records ( user_id, record_date, emotion_type, intensity, note, triggers, sleep_quality, sleep_hours, stress_level, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(user_id, record_date) DO UPDATE SET emotion_type = excluded.emotion_type, intensity = excluded.intensity, note = excluded.note, triggers = excluded.triggers, sleep_quality = excluded.sleep_quality, sleep_hours = excluded.sleep_hours, stress_level = excluded.stress_level ''', (user_id, record_date, emotion_type,
                          kwargs.get('intensity', 3), kwargs.get('note'),
                          triggers, kwargs.get('sleep_quality'),
                          kwargs.get('sleep_hours'), kwargs.get('stress_level'),
                          now))
                    conn.commit()
                    return {'success': True, 'record_date': record_date}
        except Exception as e:
            logger.error(f'记录情绪失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_emotion_history(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                cursor.execute(''' SELECT * FROM emotion_records WHERE user_id = ? AND record_date >= ? ORDER BY record_date DESC ''', (user_id, start_date))
                records = [dict(r) for r in cursor.fetchall()]
                emotion_counts = {}
                for r in records:
                    et = r['emotion_type']
                    emotion_counts[et] = emotion_counts.get(et, 0) + 1
                avg = sum(EMOTION_TYPES.get(r['emotion_type'], {}).get('level',
                3) for r in records) / len(records) if records else 0
                return {
                    'success': True,
                    'records': records,
                    'emotion_distribution': emotion_counts,
                    'average_mood': round(avg, 2),
                    'total_days': len(records)
                }
        except Exception as e:
            logger.error(f'获取情绪历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理档案 ==========

    def get_mental_health_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM mental_health_profiles WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    profile = dict(row)
                    if profile.get('risk_factors'):
                        profile['risk_factors'] = json.loads(profile['risk_factors'])
                    return profile
                return None
        except Exception as e:
            logger.error(f'获取心理档案失败: {e}')
            return None

    # ========== 团体辅导 ==========

    def create_group_counseling(self, group_name: str, counselor_id: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            group_id = f"grp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            schedule = json.dumps(kwargs.get('schedule'), ensure_ascii=False) if kwargs.get('schedule') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO group_counseling ( group_id, group_name, counselor_id, group_type, max_members, description, start_date, end_date, schedule, location, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'recruiting', ?, ?) ''', (group_id, group_name, counselor_id,
                          kwargs.get('group_type'), kwargs.get('max_members', 10),
                          kwargs.get('description'), kwargs.get('start_date'),
                          kwargs.get('end_date'), schedule, kwargs.get('location'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建团体辅导: {group_name} ({group_id})')
                    return {'success': True, 'group_id': group_id}
        except Exception as e:
            logger.error(f'创建团体辅导失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_group_counseling(self, group_id: str, user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_members, current_members, status FROM group_counseling WHERE group_id = ?', (group_id,))
                    group = cursor.fetchone()
                    if not group:
                        return {'success': False, 'error': '团体不存在'}
                    if group[2] != 'recruiting':
                        return {'success': False, 'error': f'团体状态不允许加入: {group[2]}'}
                    if group[1] >= group[0]:
                        return {'success': False, 'error': '团体已满'}
                    cursor.execute(''' INSERT OR IGNORE INTO group_counseling_members (group_id, user_id, joined_at, status) VALUES (?, ?, ?, 'active') ''', (group_id, user_id, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE group_counseling SET current_members = current_members + 1, updated_at = ? WHERE group_id = ?', (now, group_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'加入团体辅导失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_crisis_alerts(self, status: str = 'pending', page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM crisis_alerts WHERE status = ?'
                params = [status]
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY crisis_level DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取危机预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def handle_crisis_alert(self, alert_id: str, handler_id: int,
                            handling_notes: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE crisis_alerts SET status = 'handled', handler_id = ?, handler_name = ?, handled_at = ?, handling_notes = ? WHERE alert_id = ? AND status = 'pending' ''', (handler_id, '', now, handling_notes, alert_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'处理危机预警失败: {e}')
            return {'success': False, 'error': str(e)}
