from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 体育健康管理服务 (v15.6.0) ==================================== 提供体育课程、体质健康、运动赛事和健康档案等综合服务。  核心能力： 1. 体育课程 - 课程管理、考勤记录、成绩评定 2. 体质健康 - 体质测试、健康档案、数据分析 3. 运动赛事 - 赛事组织、报名管理、成绩记录 4. 健康监测 - 日常健康、视力口腔、体检管理 5. 运动处方 - 个性化运动建议、健康干预 6. 体育设施 - 场地管理、预约使用 7. 成人健身 - 成人教育健身管理 8. K12体测 - 学生体质健康标准 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sports_health_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SportsHealth')


# ========== 体育配置 ==========

# 体育课程类型
PE_COURSE_TYPES = {
    'track_field': {'name': '田径', 'icon': 'running'},
    'ball_team': {'name': '球类团队', 'icon': 'basketball'},
    'ball_racket': {'name': '球类隔网', 'icon': 'volleyball'},
    'gymnastics': {'name': '体操', 'icon': 'child'},
    'swimming': {'name': '游泳', 'icon': 'swimmer'},
    'martial_arts': {'name': '武术', 'icon': 'hand-rock'},
    'dance': {'name': '舞蹈', 'icon': 'music'},
    'fitness': {'name': '健身', 'icon': 'dumbbell'},
    'outdoor': {'name': '户外运动', 'icon': 'tree'},
    'ice_snow': {'name': '冰雪运动', 'icon': 'snowflake'}
}

# 体质测试项目（K12国家标准）
FITNESS_TEST_ITEMS = {
    'height': {'name': '身高', 'unit': 'cm', 'type': 'measurement'},
    'weight': {'name': '体重', 'unit': 'kg', 'type': 'measurement'},
    'bmi': {'name': 'BMI', 'unit': '', 'type': 'calculated'},
    'vital_capacity': {'name': '肺活量', 'unit': 'ml', 'type': 'measurement'},
    '50m_run': {'name': '50米跑', 'unit': 's', 'type': 'time', 'lower_better': True},
    'sit_reach': {'name': '坐位体前屈', 'unit': 'cm', 'type': 'measurement'},
    '800m_run': {'name': '800米跑(女)', 'unit': 's', 'type': 'time', 'lower_better': True},
    '1000m_run': {'name': '1000米跑(男)', 'unit': 's', 'type': 'time', 'lower_better': True},
    'sit_ups': {'name': '仰卧起坐', 'unit': '次', 'type': 'count'},
    'pull_ups': {'name': '引体向上(男)', 'unit': '次', 'type': 'count'},
    'rope_skipping': {'name': '跳绳', 'unit': '次', 'type': 'count'},
    'standing_jump': {'name': '立定跳远', 'unit': 'cm', 'type': 'measurement'},
    '50m_shuttle': {'name': '50米往返跑', 'unit': 's', 'type': 'time', 'lower_better': True}
}

# 体质等级
FITNESS_GRADES = {
    'excellent': {'name': '优秀', 'score_range': (90, 100), 'color': '#52c41a'},
    'good': {'name': '良好', 'score_range': (80, 89), 'color': '#1890ff'},
    'pass': {'name': '及格', 'score_range': (60, 79), 'color': '#faad14'},
    'fail': {'name': '不及格', 'score_range': (0, 59), 'color': '#f5222d'}
}

# 赛事类型
EVENT_TYPES = {
    'track_field_meet': {'name': '田径运动会', 'team': False},
    'basketball_league': {'name': '篮球联赛', 'team': True},
    'football_league': {'name': '足球联赛', 'team': True},
    'volleyball_league': {'name': '排球联赛', 'team': True},
    'table_tennis': {'name': '乒乓球赛', 'team': False},
    'badminton': {'name': '羽毛球赛', 'team': False},
    'swimming_gala': {'name': '游泳比赛', 'team': False},
    'rope_skipping': {'name': '跳绳比赛', 'team': False},
    'tug_of_war': {'name': '拔河比赛', 'team': True},
    'fun_sports': {'name': '趣味运动会', 'team': True}
}

# 健康检查类型
HEALTH_CHECK_TYPES = {
    'physical_exam': {'name': '常规体检', 'frequency': 'annual'},
    'vision': {'name': '视力检查', 'frequency': 'semiannual'},
    'dental': {'name': '口腔检查', 'frequency': 'annual'},
    'hearing': {'name': '听力检查', 'frequency': 'annual'},
    'spine': {'name': '脊柱检查', 'frequency': 'annual'},
    'nutrition': {'name': '营养评估', 'frequency': 'semiannual'},
    'mental_health': {'name': '心理健康筛查', 'frequency': 'semiannual'}
}

# 运动处方类型
EXERCISE_PRESCRIPTION_TYPES = {
    'weight_loss': {'name': '减脂塑形', 'intensity': 'medium', 'frequency': '4-5次/周'},
    'muscle_gain': {'name': '增肌健体', 'intensity': 'high', 'frequency': '4-6次/周'},
    'endurance': {'name': '耐力提升', 'intensity': 'medium', 'frequency': '3-5次/周'},
    'flexibility': {'name': '柔韧改善', 'intensity': 'low', 'frequency': '5-7次/周'},
    'rehabilitation': {'name': '康复训练', 'intensity': 'low', 'frequency': '3-4次/周'},
    'stress_relief': {'name': '减压放松', 'intensity': 'low', 'frequency': '3-5次/周'}
}

# BMI等级
BMI_CATEGORIES = {
    'underweight': {'name': '偏瘦', 'range': (0, 18.5), 'color': '#1890ff'},
    'normal': {'name': '正常', 'range': (18.5, 24), 'color': '#52c41a'},
    'overweight': {'name': '超重', 'range': (24, 28), 'color': '#faad14'},
    'obese': {'name': '肥胖', 'range': (28, 100), 'color': '#f5222d'}
}


class SportsHealthService:
    """体育健康管理服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS pe_courses ( course_id TEXT PRIMARY KEY, course_name TEXT NOT NULL, course_type TEXT NOT NULL, teacher_id INTEGER, teacher_name TEXT, education_type TEXT, grade_level INTEGER, semester TEXT, weekly_hours INTEGER DEFAULT 2, location TEXT, max_students INTEGER DEFAULT 40, enrolled_count INTEGER DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS pe_enrollments ( id INTEGER PRIMARY KEY AUTOINCREMENT, course_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, enroll_date TEXT, attendance_count INTEGER DEFAULT 0, absence_count INTEGER DEFAULT 0, final_score REAL, grade TEXT, UNIQUE(course_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS fitness_tests ( test_id TEXT PRIMARY KEY, test_name TEXT NOT NULL, academic_year TEXT, semester TEXT, grade_level INTEGER, education_type TEXT, test_date TEXT, location TEXT, organizer TEXT, total_participants INTEGER DEFAULT 0, completed_count INTEGER DEFAULT 0, status TEXT DEFAULT 'scheduled', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS fitness_test_records ( record_id TEXT PRIMARY KEY, test_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, gender TEXT, age INTEGER, grade_level INTEGER, height REAL, weight REAL, bmi REAL, vital_capacity INTEGER, run_50m REAL, sit_reach REAL, run_800m REAL, run_1000m REAL, sit_ups INTEGER, pull_ups INTEGER, rope_skipping INTEGER, standing_jump REAL, shuttle_50m REAL, total_score REAL, grade TEXT, tested_at TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS sports_events ( event_id TEXT PRIMARY KEY, event_name TEXT NOT NULL, event_type TEXT, education_type TEXT, organizer TEXT, start_date TEXT, end_date TEXT, location TEXT, description TEXT, max_participants INTEGER DEFAULT 100, registered_count INTEGER DEFAULT 0, is_team_event INTEGER DEFAULT 0, team_size INTEGER, status TEXT DEFAULT 'scheduled', cover_image TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS event_registrations ( id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, team_name TEXT, register_date TEXT, result TEXT, ranking INTEGER, score REAL, award TEXT, UNIQUE(event_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS health_records ( record_id TEXT PRIMARY KEY, student_id INTEGER NOT NULL, student_name TEXT, check_type TEXT NOT NULL, check_date TEXT, checker TEXT, result TEXT, result_summary TEXT, recommendation TEXT, is_normal INTEGER DEFAULT 1, abnormal_items TEXT, follow_up TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS exercise_prescriptions ( prescription_id TEXT PRIMARY KEY, student_id INTEGER NOT NULL, student_name TEXT, prescription_type TEXT, target TEXT, intensity TEXT, frequency TEXT, duration_minutes INTEGER, exercises TEXT, precautions TEXT, valid_from TEXT, valid_to TEXT, prescribed_by TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS sports_facilities ( facility_id TEXT PRIMARY KEY, facility_name TEXT NOT NULL, facility_type TEXT, location TEXT, capacity INTEGER, is_available INTEGER DEFAULT 1, open_time TEXT, close_time TEXT, description TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS facility_reservations ( reservation_id TEXT PRIMARY KEY, facility_id TEXT NOT NULL, facility_name TEXT, reserved_by INTEGER, reserved_by_name TEXT, reserve_date TEXT, start_time TEXT, end_time TEXT, purpose TEXT, status TEXT DEFAULT 'pending', created_at TEXT ) ''')
                conn.commit()
                logger.info('体育健康管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 体育课程 ==========

    def create_pe_course(self, course_name: str, course_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"pec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO pe_courses ( course_id, course_name, course_type, teacher_id, teacher_name, education_type, grade_level, semester, weekly_hours, location, max_students, enrolled_count, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?) ''', (course_id, course_name, course_type,
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('semester'), kwargs.get('weekly_hours', 2),
                          kwargs.get('location'), kwargs.get('max_students', 40),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建体育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建体育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_pe_course(self, course_id: str, student_id: int,
                          student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM pe_courses WHERE course_id = ?',
                    (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute(''' INSERT OR IGNORE INTO pe_enrollments (course_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?) ''', (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE pe_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_pe_score(self, course_id: str, student_id: int,
                         score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            grade = self._score_to_grade(score)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE pe_enrollments SET final_score = ?, grade = ? WHERE course_id = ? AND student_id = ? ''', (score, grade, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录体育成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def _score_to_grade(self, score: float) -> str:
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 60:
            return 'pass'
        else:
            return 'fail'

    # ========== 体质测试 ==========

    def create_fitness_test(self, test_name: str, test_date: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            test_id = f"fts_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO fitness_tests ( test_id, test_name, academic_year, semester, grade_level, education_type, test_date, location, organizer, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?) ''', (test_id, test_name, kwargs.get('academic_year'),
                          kwargs.get('semester'), kwargs.get('grade_level'),
                          kwargs.get('education_type'), test_date,
                          kwargs.get('location'), kwargs.get('organizer'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建体质测试: {test_name} ({test_id})')
                    return {'success': True, 'test_id': test_id}
        except Exception as e:
            logger.error(f'创建体质测试失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_fitness_test(self, test_id: str, student_id: int,
                             **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"ftr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            height = kwargs.get('height', 0)
            weight = kwargs.get('weight', 0)
            bmi = round(weight / (height / 100) ** 2, 1) if height and weight else 0
            total_score = self._calculate_fitness_score(kwargs)
            grade = self._score_to_grade(total_score)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO fitness_test_records ( record_id, test_id, student_id, student_name, gender, age, grade_level, height, weight, bmi, vital_capacity, run_50m, sit_reach, run_800m, run_1000m, sit_ups, pull_ups, rope_skipping, standing_jump, shuttle_50m, total_score, grade, tested_at, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (record_id, test_id, student_id,
                          kwargs.get('student_name'), kwargs.get('gender'),
                          kwargs.get('age'), kwargs.get('grade_level'),
                          height, weight, bmi,
                          kwargs.get('vital_capacity'),
                          kwargs.get('run_50m'), kwargs.get('sit_reach'),
                          kwargs.get('run_800m'), kwargs.get('run_1000m'),
                          kwargs.get('sit_ups'), kwargs.get('pull_ups'),
                          kwargs.get('rope_skipping'),
                          kwargs.get('standing_jump'),
                          kwargs.get('shuttle_50m'),
                          total_score, grade, now[:10], now))
                    cursor.execute('UPDATE fitness_tests SET completed_count = completed_count + 1, updated_at = ? WHERE test_id = ?', (now, test_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id,
                            'total_score': total_score, 'grade': grade, 'bmi': bmi}
        except Exception as e:
            logger.error(f'记录体质测试失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_fitness_score(self, data: Dict) -> float:
        scores = []
        if data.get('vital_capacity'):
            scores.append(min(100, data['vital_capacity'] / 50))
        if data.get('run_50m'):
            scores.append(max(0, 100 - (data['run_50m'] - 7) * 20))
        if data.get('sit_reach'):
            scores.append(min(100, max(0, (data['sit_reach'] + 10) * 5)))
        if data.get('sit_ups'):
            scores.append(min(100, data['sit_ups'] * 2))
        if data.get('standing_jump'):
            scores.append(min(100, data['standing_jump'] / 2))
        if data.get('rope_skipping'):
            scores.append(min(100, data['rope_skipping'] / 1.5))
        return round(sum(scores) / len(scores), 1) if scores else 0

    def get_student_fitness_records(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM fitness_test_records WHERE student_id = ? ORDER BY tested_at DESC',
                (student_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取学生体测记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_fitness_statistics(self, test_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*), AVG(total_score), AVG(bmi) FROM fitness_test_records WHERE test_id = ?', (test_id,))
                row = cursor.fetchone()
                cursor.execute('SELECT grade, COUNT(*) FROM fitness_test_records WHERE test_id = ? GROUP BY grade',
                (test_id,))
                by_grade = {r[0]: r[1] for r in cursor.fetchall()}
                total = row[0] or 0
                return {
                    'success': True,
                    'stats': {
                        'total_tested': total,
                        'average_score': round(row[1], 1) if row[1] else 0,
                        'average_bmi': round(row[2], 1) if row[2] else 0,
                        'grade_distribution': by_grade
                    }
                }
        except Exception as e:
            logger.error(f'获取体测统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 运动赛事 ==========

    def create_sports_event(self, event_name: str, event_type: str,
                             start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            event_id = f"sev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EVENT_TYPES.get(event_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO sports_events ( event_id, event_name, event_type, education_type, organizer, start_date, end_date, location, description, max_participants, registered_count, is_team_event, team_size, status, cover_image, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'scheduled', ?, ?, ?) ''', (event_id, event_name, event_type,
                          kwargs.get('education_type'), kwargs.get('organizer'),
                          start_date, kwargs.get('end_date'),
                          kwargs.get('location'), kwargs.get('description'),
                          kwargs.get('max_participants', 100),
                          1 if config.get('team') else 0,
                          kwargs.get('team_size'), kwargs.get('cover_image'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建运动赛事: {event_name} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'创建运动赛事失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_event(self, event_id: str, student_id: int,
                        student_name: str = None, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM sports_events WHERE event_id = ?', (event_id,))
                    event = cursor.fetchone()
                    if not event:
                        return {'success': False, 'error': '赛事不存在'}
                    if event[2] != 'scheduled':
                        return {'success': False, 'error': '赛事状态不允许报名'}
                    if event[0] and event[1] >= event[0]:
                        return {'success': False, 'error': '赛事名额已满'}
                    cursor.execute(''' INSERT OR IGNORE INTO event_registrations (event_id, student_id, student_name, team_name, register_date) VALUES (?, ?, ?, ?, ?) ''', (event_id, student_id, student_name, kwargs.get('team_name'), now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE sports_events SET registered_count = registered_count + 1, updated_at = ? WHERE event_id = ?', (now, event_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该赛事'}
        except Exception as e:
            logger.error(f'赛事报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_event_result(self, event_id: str, student_id: int,
                             **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE event_registrations SET result = ?, ranking = ?, score = ?, award = ? WHERE event_id = ? AND student_id = ? ''', (kwargs.get('result'), kwargs.get('ranking'),
                          kwargs.get('score'), kwargs.get('award'),
                          event_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录赛事成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 健康档案 ==========

    def create_health_record(self, student_id: int, check_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"hlr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            abnormal_items = json.dumps(kwargs.get('abnormal_items'),
            ensure_ascii=False) if kwargs.get('abnormal_items') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO health_records ( record_id, student_id, student_name, check_type, check_date, checker, result, result_summary, recommendation, is_normal, abnormal_items, follow_up, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (record_id, student_id, kwargs.get('student_name'),
                          check_type, kwargs.get('check_date', now[:10]),
                          kwargs.get('checker'), kwargs.get('result'),
                          kwargs.get('result_summary'),
                          kwargs.get('recommendation'),
                          kwargs.get('is_normal', 1), abnormal_items,
                          kwargs.get('follow_up'), now))
                    conn.commit()
                    logger.info(f'创建健康记录: {record_id}')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'创建健康记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_health_records(self, student_id: int,
                                     check_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM health_records WHERE student_id = ?'
                params = [student_id]
                if check_type:
                    query += ' AND check_type = ?'
                    params.append(check_type)
                query += ' ORDER BY check_date DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取健康记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 运动处方 ==========

    def create_exercise_prescription(self, student_id: int,
                                       prescription_type: str,
                                       **kwargs) -> Dict[str, Any]:
        try:
            prescription_id = f"exp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EXERCISE_PRESCRIPTION_TYPES.get(prescription_type, {})
            exercises = json.dumps(kwargs.get('exercises'), ensure_ascii=False) if kwargs.get('exercises') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO exercise_prescriptions ( prescription_id, student_id, student_name, prescription_type, target, intensity, frequency, duration_minutes, exercises, precautions, valid_from, valid_to, prescribed_by, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (prescription_id, student_id, kwargs.get('student_name'),
                          prescription_type, kwargs.get('target'),
                          kwargs.get('intensity', config.get('intensity', 'medium')),
                          kwargs.get('frequency', config.get('frequency', '3-5次/周')),
                          kwargs.get('duration_minutes', 45),
                          exercises, kwargs.get('precautions'),
                          kwargs.get('valid_from', now[:10]),
                          kwargs.get('valid_to', (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')),
                          kwargs.get('prescribed_by'), now, now))
                    conn.commit()
                    logger.info(f'创建运动处方: {prescription_id}')
                    return {'success': True, 'prescription_id': prescription_id}
        except Exception as e:
            logger.error(f'创建运动处方失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 体育设施 ==========

    def create_facility(self, facility_name: str, facility_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            facility_id = f"fac_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO sports_facilities ( facility_id, facility_name, facility_type, location, capacity, is_available, open_time, close_time, description, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?) ''', (facility_id, facility_name, facility_type,
                          kwargs.get('location'), kwargs.get('capacity'),
                          kwargs.get('open_time', '08:00'),
                          kwargs.get('close_time', '22:00'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    return {'success': True, 'facility_id': facility_id}
        except Exception as e:
            logger.error(f'创建体育设施失败: {e}')
            return {'success': False, 'error': str(e)}

    def reserve_facility(self, facility_id: str, reserved_by: int,
                          reserve_date: str, start_time: str,
                          end_time: str, **kwargs) -> Dict[str, Any]:
        try:
            reservation_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT facility_name, is_available FROM sports_facilities WHERE facility_id = ?',
                    (facility_id,))
                    facility = cursor.fetchone()
                    if not facility:
                        return {'success': False, 'error': '设施不存在'}
                    if not facility[1]:
                        return {'success': False, 'error': '设施不可用'}
                    cursor.execute(''' SELECT COUNT(*) FROM facility_reservations WHERE facility_id = ? AND reserve_date = ? AND ((start_time < ? AND end_time > ?) OR (start_time < ? AND end_time > ?)) AND status != 'rejected' ''', (facility_id, reserve_date, end_time, start_time, end_time, start_time))
                    if cursor.fetchone()[0] > 0:
                        return {'success': False, 'error': '该时段已被预约'}
                    cursor.execute(''' INSERT INTO facility_reservations ( reservation_id, facility_id, facility_name, reserved_by, reserved_by_name, reserve_date, start_time, end_time, purpose, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?) ''', (reservation_id, facility_id, facility[0],
                          reserved_by, kwargs.get('reserved_by_name'),
                          reserve_date, start_time, end_time,
                          kwargs.get('purpose'), now))
                    conn.commit()
                    return {'success': True, 'reservation_id': reservation_id}
        except Exception as e:
            logger.error(f'预约设施失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_facility_reservations(self, facility_id: str,
                                    reserve_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM facility_reservations WHERE facility_id = ?'
                params = [facility_id]
                if reserve_date:
                    query += ' AND reserve_date = ?'
                    params.append(reserve_date)
                query += ' ORDER BY start_time'
                cursor.execute(query, params)
                reservations = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reservations': reservations}
        except Exception as e:
            logger.error(f'获取预约列表失败: {e}')
            return {'success': False, 'error': str(e)}
