from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育体育健康服务 (v15.25.0) ==================================== 提供体育课程管理、体育活动组织、体质健康监测、运动训练指导、 体育竞赛管理、体育设施管理、体育安全保障和健康教育等综合管理服务。  核心能力：体育课程、体育活动、体质监测、运动训练、体育竞赛、 设施管理、安全保障、健康教育  差异化支持：成人教育、K12教育 """
import os
import uuid
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_physical_health_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationPhysicalHealth')


SPORT_TYPES = {
    'track_field': {'name': '田径', 'sub': ['短跑', '长跑', '跳远', '跳高', '投掷']},
    'ball': {'name': '球类', 'sub': ['篮球', '足球', '排球', '羽毛球', '乒乓球']},
    'gymnastics': {'name': '体操', 'sub': ['艺术体操', '竞技体操', '健美操']},
    'swimming': {'name': '游泳', 'sub': ['自由泳', '蛙泳', '仰泳', '蝶泳']},
    'martial_arts': {'name': '武术', 'sub': ['太极拳', '散打', '跆拳道']},
    'winter_sports': {'name': '冰雪运动', 'sub': ['滑雪', '滑冰', '冰球']},
    'outdoor': {'name': '户外运动', 'sub': ['登山', '骑行', '徒步']},
    'leisure': {'name': '休闲运动', 'sub': ['瑜伽', '普拉提', '健身操']}
}

COURSE_TYPES = {
    'required': {'name': '必修课程', 'hours': 48},
    'elective': {'name': '选修课程', 'hours': 24},
    'extended': {'name': '拓展课程', 'hours': 16},
    'special': {'name': '特色课程', 'hours': 12},
    'school_based': {'name': '校本课程', 'hours': 20},
    'club': {'name': '社团课程', 'hours': 32},
    'training': {'name': '训练课程', 'hours': 60},
    'competition': {'name': '竞赛课程', 'hours': 40}
}

ACTIVITY_TYPES = {
    'sports_meeting': {'name': '运动会', 'min': 100},
    'sports_festival': {'name': '体育节', 'min': 50},
    'sunshine_sports': {'name': '阳光体育', 'min': 200},
    'sports_club': {'name': '体育社团', 'min': 10},
    'sports_tournament': {'name': '体育赛事', 'min': 20},
    'outdoor_activity': {'name': '户外活动', 'min': 15},
    'summer_camp': {'name': '体育夏令营', 'min': 30},
    'winter_camp': {'name': '体育冬令营', 'min': 30}
}

FITNESS_INDICATORS = {
    'height_weight': {'name': '身高体重', 'unit': 'cm/kg', 'k12': True},
    'vital_capacity': {'name': '肺活量', 'unit': 'ml', 'k12': True},
    'endurance': {'name': '耐力素质', 'unit': '分秒', 'k12': True},
    'strength': {'name': '力量素质', 'unit': '次/kg', 'k12': True},
    'speed': {'name': '速度素质', 'unit': '秒', 'k12': True},
    'flexibility': {'name': '柔韧性', 'unit': 'cm', 'k12': True},
    'coordination': {'name': '协调性', 'unit': '评分', 'k12': False},
    'balance': {'name': '平衡性', 'unit': '秒', 'k12': False}
}

TRAINING_METHODS = {
    'physical': {'name': '体能训练', 'focus': '基础素质'},
    'skill': {'name': '技能训练', 'focus': '技术提升'},
    'tactical': {'name': '战术训练', 'focus': '战术配合'},
    'psychological': {'name': '心理训练', 'focus': '心理素质'},
    'rehabilitation': {'name': '康复训练', 'focus': '恢复健康'},
    'specialized': {'name': '专项训练', 'focus': '专项能力'},
    'comprehensive': {'name': '综合训练', 'focus': '全面发展'},
    'personalized': {'name': '个性化训练', 'focus': '因材施教'}
}

COMPETITION_TYPES = {
    'school': {'name': '校级比赛', 'level': 1},
    'city': {'name': '市级比赛', 'level': 2},
    'province': {'name': '省级比赛', 'level': 3},
    'national': {'name': '国家级比赛', 'level': 4},
    'international': {'name': '国际比赛', 'level': 5},
    'league': {'name': '联赛', 'level': 2},
    'championship': {'name': '锦标赛', 'level': 3},
    'friendly': {'name': '友谊赛', 'level': 1}
}

FACILITY_TYPES = {
    'stadium': {'name': '体育场', 'capacity': 5000},
    'gymnasium': {'name': '体育馆', 'capacity': 2000},
    'fitness_center': {'name': '健身房', 'capacity': 100},
    'swimming_pool': {'name': '游泳池', 'capacity': 50},
    'training_field': {'name': '训练场', 'capacity': 80},
    'equipment_room': {'name': '器材室', 'capacity': 0},
    'outdoor_field': {'name': '户外场地', 'capacity': 150},
    'specialized_field': {'name': '专项场地', 'capacity': 60}
}

HEALTH_TOPICS = {
    'sports_health': {'name': '运动健康', 'duration': 60},
    'nutrition_health': {'name': '营养健康', 'duration': 45},
    'mental_health': {'name': '心理健康', 'duration': 50},
    'lifestyle': {'name': '生活方式', 'duration': 40},
    'disease_prevention': {'name': '疾病预防', 'duration': 55},
    'rehabilitation': {'name': '康复保健', 'duration': 50},
    'safety_knowledge': {'name': '安全知识', 'duration': 30},
    'health_management': {'name': '健康管理', 'duration': 45}
}


class EducationPhysicalHealthService:

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS sports_courses ( course_id TEXT PRIMARY KEY, course_name TEXT, sport_type TEXT, course_type TEXT, education_type TEXT, grade_level INTEGER, teacher_id INTEGER, teacher_name TEXT, semester TEXT, weekly_hours INTEGER DEFAULT 2, total_hours INTEGER DEFAULT 0, location TEXT, max_students INTEGER DEFAULT 30, enrolled_count INTEGER DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS course_schedules ( schedule_id TEXT PRIMARY KEY, course_id TEXT, day_of_week INTEGER, start_time TEXT, end_time TEXT, location TEXT, week_range TEXT, status TEXT DEFAULT 'active', created_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS sports_activities ( activity_id TEXT PRIMARY KEY, activity_name TEXT, activity_type TEXT, sport_type TEXT, organizer TEXT, description TEXT, location TEXT, start_date TEXT, end_date TEXT, start_time TEXT DEFAULT '08:00', end_time TEXT DEFAULT '17:00', max_participants INTEGER DEFAULT 100, registered_count INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'scheduled', created_at TEXT, updated_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS activity_records ( record_id TEXT PRIMARY KEY, activity_id TEXT, student_id INTEGER, student_name TEXT, register_time TEXT, attended INTEGER DEFAULT 0, performance TEXT, score REAL)''')
                c.execute('''CREATE TABLE IF NOT EXISTS physical_fitness ( fitness_id TEXT PRIMARY KEY, student_id INTEGER, student_name TEXT, education_type TEXT, grade_level INTEGER, test_date TEXT, height REAL, weight REAL, vital_capacity INTEGER, endurance_score REAL, strength_score REAL, speed_score REAL, flexibility_score REAL, coordination_score REAL, balance_score REAL, overall_score REAL, health_level TEXT, remarks TEXT, created_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS fitness_records ( record_id TEXT PRIMARY KEY, fitness_id TEXT, indicator_type TEXT, value REAL, unit TEXT, standard_value REAL, is_pass INTEGER DEFAULT 0, created_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS sports_training ( training_id TEXT PRIMARY KEY, training_name TEXT, training_method TEXT, sport_type TEXT, education_type TEXT, target_group TEXT, description TEXT, duration INTEGER DEFAULT 60, frequency TEXT DEFAULT '每周3次', coach_id INTEGER, coach_name TEXT, max_participants INTEGER DEFAULT 20, enrolled_count INTEGER DEFAULT 0, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS training_records ( record_id TEXT PRIMARY KEY, training_id TEXT, student_id INTEGER, student_name TEXT, attendance_count INTEGER DEFAULT 0, total_sessions INTEGER DEFAULT 0, progress TEXT DEFAULT '初级', performance_score REAL, feedback TEXT, created_at TEXT, updated_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS sports_competition ( competition_id TEXT PRIMARY KEY, competition_name TEXT, competition_type TEXT, sport_type TEXT, organizer TEXT, location TEXT, start_date TEXT, end_date TEXT, max_teams INTEGER DEFAULT 16, registered_teams INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'registration', created_at TEXT, updated_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS competition_results ( result_id TEXT PRIMARY KEY, competition_id TEXT, team_id INTEGER, team_name TEXT, player_id INTEGER, player_name TEXT, event_name TEXT, rank INTEGER, score REAL, medal TEXT, created_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS sports_facilities ( facility_id TEXT PRIMARY KEY, facility_name TEXT, facility_type TEXT, location TEXT, capacity INTEGER DEFAULT 0, status TEXT DEFAULT 'available', opening_hours TEXT DEFAULT '06:00-22:00', maintenance_status TEXT DEFAULT 'normal', description TEXT, created_at TEXT, updated_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS facility_usage ( usage_id TEXT PRIMARY KEY, facility_id TEXT, user_id INTEGER, user_name TEXT, education_type TEXT, usage_date TEXT, start_time TEXT, end_time TEXT, purpose TEXT, status TEXT DEFAULT 'reserved', created_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS sports_safety ( safety_id TEXT PRIMARY KEY, check_type TEXT, location TEXT, description TEXT, check_date TEXT, check_result TEXT DEFAULT 'passed', issues_found TEXT, rectification_status TEXT DEFAULT 'none', inspector_id INTEGER, inspector_name TEXT, created_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS safety_records ( record_id TEXT PRIMARY KEY, incident_type TEXT, location TEXT, description TEXT, severity TEXT DEFAULT 'minor', injured_person TEXT, emergency_response TEXT, date_time TEXT, status TEXT DEFAULT 'processing', created_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS health_education ( education_id TEXT PRIMARY KEY, topic TEXT, education_type TEXT, title TEXT, description TEXT, content TEXT, duration INTEGER DEFAULT 45, presenter TEXT, target_audience TEXT, status TEXT DEFAULT 'planned', created_at TEXT, updated_at TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS education_records ( record_id TEXT PRIMARY KEY, education_id TEXT, participant_id INTEGER, participant_name TEXT, education_type TEXT, attended INTEGER DEFAULT 0, feedback TEXT, satisfaction_score INTEGER, created_at TEXT)''')
                conn.commit()
                logger.info('教育体育健康服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 体育课程 ==========

    def create_sports_course(self, course_name: str, sport_type: str,
                             course_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"spc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            total_hours = kwargs.get('total_hours', COURSE_TYPES[course_type]['hours'])
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO sports_courses (course_id, course_name, sport_type, course_type, education_type, grade_level, teacher_id, teacher_name, semester, weekly_hours, total_hours, location, max_students, enrolled_count, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)''',
                        (course_id, course_name, sport_type, course_type,
                        kwargs.get('education_type'), kwargs.get('grade_level'),
                        kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                        kwargs.get('semester'), kwargs.get('weekly_hours', 2),
                        total_hours, kwargs.get('location'), kwargs.get('max_students', 30),
                        kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建体育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建体育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_sports_course(self, course_id: str, student_id: int,
                             student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT max_students, enrolled_count, status FROM sports_courses WHERE course_id = ?',
                    (course_id,))
                    course = c.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    c.execute('SELECT course_id FROM course_schedules WHERE course_id = ?', (course_id,))
                    if not c.fetchone():
                        return {'success': False, 'error': '课程尚未安排上课时间'}
                    c.execute('INSERT OR IGNORE INTO activity_records (record_id, activity_id, student_id, student_name, register_time, attended) VALUES (?, ?, ?, ?, ?, 0)',
                             (f"ars_{uuid.uuid4().hex[:12]}", course_id, student_id, student_name, now[:10]))
                    if c.rowcount > 0:
                        c.execute('UPDATE sports_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'体育选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_course_score(self, course_id: str, student_id: int,
                            score: float) -> Dict[str, Any]:
        try:
            level = '优秀' if score >= 90 else ('良好' if score >= 80 else ('及格' if score >= 60 else '不及格'))
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE activity_records SET score = ?, performance = ? WHERE activity_id = ? AND student_id = ?',
                             (score, level, course_id, student_id))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'health_level': level}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录体育成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_course_schedule(self, course_id: str, day_of_week: int,
                            start_time: str, end_time: str, **kwargs) -> Dict[str, Any]:
        try:
            schedule_id = f"sch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT status FROM sports_courses WHERE course_id = ?', (course_id,))
                    if not c.fetchone():
                        return {'success': False, 'error': '课程不存在'}
                    c.execute('''INSERT INTO course_schedules (schedule_id, course_id, day_of_week, start_time, end_time, location, week_range, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)''',
                        (schedule_id, course_id, day_of_week, start_time, end_time,
                        kwargs.get('location'), kwargs.get('week_range', '1-18'), now))
                    conn.commit()
                    logger.info(f'添加课程安排: {course_id} - 周{day_of_week} {start_time}-{end_time}')
                    return {'success': True, 'schedule_id': schedule_id}
        except Exception as e:
            logger.error(f'添加课程安排失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 体育活动 ==========

    def create_sports_activity(self, activity_name: str, activity_type: str,
                               start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"spa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO sports_activities (activity_id, activity_name, activity_type, sport_type, organizer, description, location, start_date, end_date, start_time, end_time, max_participants, registered_count, education_type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'scheduled', ?, ?)''',
                        (activity_id, activity_name, activity_type, kwargs.get('sport_type'),
                        kwargs.get('organizer'), kwargs.get('description'), kwargs.get('location'),
                        start_date, kwargs.get('end_date'), kwargs.get('start_time', '08:00'),
                        kwargs.get('end_time', '17:00'), kwargs.get('max_participants',
                        ACTIVITY_TYPES[activity_type]['min']),
                        kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建体育活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'创建体育活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_activity(self, activity_id: str, student_id: int,
                          student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT max_participants, registered_count, status FROM sports_activities WHERE activity_id = ?', (activity_id,))
                    activity = c.fetchone()
                    if not activity:
                        return {'success': False, 'error': '活动不存在'}
                    if activity[2] != 'scheduled':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if activity[0] and activity[1] >= activity[0]:
                        return {'success': False, 'error': '名额已满'}
                    c.execute('INSERT OR IGNORE INTO activity_records (record_id, activity_id, student_id, student_name, register_time, attended) VALUES (?, ?, ?, ?, ?, 0)',
                             (f"arr_{uuid.uuid4().hex[:12]}", activity_id, student_id, student_name, now))
                    if c.rowcount > 0:
                        c.execute('UPDATE sports_activities SET registered_count = registered_count + 1, updated_at = ? WHERE activity_id = ?', (now, activity_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_activity_attendance(self, activity_id: str, student_id: int,
                                   attended: bool = True) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE activity_records SET attended = ? WHERE activity_id = ? AND student_id = ?',
                             (1 if attended else 0, activity_id, student_id))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录活动出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_activity_stats(self, activity_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT max_participants, registered_count FROM sports_activities WHERE activity_id = ?',
                (activity_id,))
                activity = c.fetchone()
                if not activity:
                    return {'success': False, 'error': '活动不存在'}
                c.execute('SELECT COUNT(*) FROM activity_records WHERE activity_id = ? AND attended = 1', (activity_id,
                ))
                attended = c.fetchone()[0]
                c.execute('SELECT AVG(score) FROM activity_records WHERE activity_id = ? AND score IS NOT NULL',
                (activity_id,))
                avg_score = c.fetchone()[0]
                return {
                    'success': True,
                    'max_participants': activity[0],
                    'registered_count': activity[1],
                    'attended_count': attended,
                    'attendance_rate': round(attended / activity[1] * 100, 1) if activity[1] > 0 else 0,
                    'average_score': round(avg_score, 1) if avg_score else 0
                }
        except Exception as e:
            logger.error(f'获取活动统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 体质监测 ==========

    def create_fitness_test(self, student_id: int, student_name: str,
                            test_date: str, **kwargs) -> Dict[str, Any]:
        try:
            fitness_id = f"fit_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO physical_fitness (fitness_id, student_id, student_name, education_type, grade_level, test_date, height, weight, vital_capacity, endurance_score, strength_score, speed_score, flexibility_score, coordination_score, balance_score, overall_score, health_level, remarks, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (fitness_id, student_id, student_name, kwargs.get('education_type'),
                        kwargs.get('grade_level'), test_date, kwargs.get('height'), kwargs.get('weight'),
                        kwargs.get('vital_capacity'), kwargs.get('endurance_score'),
                        kwargs.get('strength_score'), kwargs.get('speed_score'), kwargs.get('flexibility_score'),
                        kwargs.get('coordination_score'), kwargs.get('balance_score'), kwargs.get('overall_score'),
                        kwargs.get('health_level'), kwargs.get('remarks'), now))
                    conn.commit()
                    logger.info(f'创建体质测试记录: {student_name} ({fitness_id})')
                    return {'success': True, 'fitness_id': fitness_id}
        except Exception as e:
            logger.error(f'创建体质测试记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_fitness_indicator(self, fitness_id: str, indicator_type: str,
                              value: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            config = FITNESS_INDICATORS.get(indicator_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT * FROM physical_fitness WHERE fitness_id = ?', (fitness_id,))
                    if not c.fetchone():
                        return {'success': False, 'error': '体质测试记录不存在'}
                    c.execute('''INSERT INTO fitness_records (record_id, fitness_id, indicator_type, value, unit, standard_value, is_pass, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (f"fir_{uuid.uuid4().hex[:12]}", fitness_id, indicator_type,
                        value, config.get('unit', ''), kwargs.get('standard_value'),
                        1 if kwargs.get('is_pass', False) else 0, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加体质指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_health_report(self, student_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = 'SELECT * FROM physical_fitness WHERE student_id = ?'
                params = [student_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                c.execute(query + ' ORDER BY test_date DESC LIMIT 1', params)
                latest = c.fetchone()
                if not latest:
                    return {'success': False, 'error': '暂无体质测试记录'}
                c.execute('SELECT * FROM fitness_records WHERE fitness_id = ?', (latest['fitness_id'],))
                indicators = [dict(i) for i in c.fetchall()]
                return {
                    'success': True,
                    'report': {
                        'student_id': latest['student_id'],
                        'student_name': latest['student_name'],
                        'test_date': latest['test_date'],
                        'education_type': latest['education_type'],
                        'overall_score': latest['overall_score'],
                        'health_level': latest['health_level'],
                        'indicators': indicators,
                        'suggestions': self._get_suggestions(latest, education_type)
                    }
                }
        except Exception as e:
            logger.error(f'生成健康报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def _get_suggestions(self, fitness, education_type: str) -> List[str]:
        suggestions = []
        if fitness['health_level'] == '不及格':
            suggestions.append('建议增加体育锻炼频率，每周至少3次')
        if education_type == 'k12':
            suggestions.append('按照国家学生体质健康标准进行针对性训练')
        else:
            suggestions.append('建议制定个性化健身计划')
        if fitness['endurance_score'] and fitness['endurance_score'] < 60:
            suggestions.append('耐力素质有待提高，建议进行长跑训练')
        if fitness['strength_score'] and fitness['strength_score'] < 60:
            suggestions.append('力量素质不足，建议增加力量训练')
        return suggestions

    def check_fitness_alerts(self, student_id: int = None, threshold: float = 60) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = 'SELECT * FROM physical_fitness WHERE overall_score < ?'
                params = [threshold]
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                c.execute(query + ' ORDER BY test_date DESC', params)
                alerts = [dict(a) for a in c.fetchall()]
                return {'success': True, 'alerts': alerts, 'count': len(alerts)}
        except Exception as e:
            logger.error(f'检查体质预警失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 运动训练 ==========

    def create_training_program(self, training_name: str, training_method: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"trn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO sports_training (training_id, training_name, training_method, sport_type, education_type, target_group, description, duration, frequency, coach_id, coach_name, max_participants, enrolled_count, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)''',
                        (training_id, training_name, training_method, kwargs.get('sport_type'),
                        kwargs.get('education_type'), kwargs.get('target_group'), kwargs.get('description'),
                        kwargs.get('duration', 60), kwargs.get('frequency', '每周3次'),
                        kwargs.get('coach_id'), kwargs.get('coach_name'), kwargs.get('max_participants', 20),
                        now, now))
                    conn.commit()
                    logger.info(f'创建训练计划: {training_name} ({training_id})')
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建训练计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_training(self, training_id: str, student_id: int,
                        student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT max_participants, enrolled_count, status FROM sports_training WHERE training_id = ?', (training_id,))
                    training = c.fetchone()
                    if not training:
                        return {'success': False, 'error': '训练计划不存在'}
                    if training[2] != 'active':
                        return {'success': False, 'error': '训练计划状态不允许报名'}
                    if training[0] and training[1] >= training[0]:
                        return {'success': False, 'error': '名额已满'}
                    c.execute('INSERT OR IGNORE INTO training_records (record_id, training_id, student_id, student_name, attendance_count, total_sessions, progress, created_at, updated_at) VALUES (?, ?, ?, ?, 0, 0, \'初级\', ?, ?)',
                             (f"trr_{uuid.uuid4().hex[:12]}", training_id, student_id, student_name, now, now))
                    if c.rowcount > 0:
                        c.execute('UPDATE sports_training SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE training_id = ?', (now, training_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该训练'}
        except Exception as e:
            logger.error(f'训练报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_session(self, training_id: str, student_id: int,
                                attended: bool = True) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    if attended:
                        c.execute('UPDATE training_records SET attendance_count = attendance_count + 1, total_sessions = total_sessions + 1, updated_at = ? WHERE training_id = ? AND student_id = ?',
                                 (now, training_id, student_id))
                    else:
                        c.execute('UPDATE training_records SET total_sessions = total_sessions + 1, updated_at = ? WHERE training_id = ? AND student_id = ?',
                                 (now, training_id, student_id))
                    if c.rowcount > 0:
                        c.execute('SELECT attendance_count, total_sessions FROM training_records WHERE training_id = ? AND student_id = ?', (training_id,
                        student_id))
                        record = c.fetchone()
                        rate = record[0] / record[1] * 100
                        progress = '高级' if rate >= 90 else ('中级' if rate >= 70 else '初级')
                        c.execute('UPDATE training_records SET progress = ? WHERE training_id = ? AND student_id = ?',
                        (progress, training_id, student_id))
                        conn.commit()
                        return {'success': True, 'progress': progress, 'attendance_rate': round(rate, 1)}
                    return {'success': False, 'error': '训练记录不存在'}
        except Exception as e:
            logger.error(f'记录训练课时失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_training_effect(self, training_id: str, student_id: int,
                                 score: float, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE training_records SET performance_score = ?, feedback = ?, updated_at = ? WHERE training_id = ? AND student_id = ?',
                             (score, kwargs.get('feedback'), datetime.now().isoformat(), training_id, student_id))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '训练记录不存在'}
        except Exception as e:
            logger.error(f'评估训练效果失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_personalized_training_plan(self, student_id: int, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute(
                'SELECT * FROM physical_fitness WHERE student_id = ? AND education_type = ? ORDER BY test_date DESC  LIMIT 1', (student_id, education_type))
                fitness = c.fetchone()
                plan = {'student_id': student_id, 'education_type': education_type, 'plan_type': 'personalized',
                'recommendations': []}
                if fitness:
                    if fitness['endurance_score'] and fitness['endurance_score'] < 70:
                        plan['recommendations'].append({'method': 'physical', 'focus': '耐力训练',
                        'suggestion': '每周3次，每次30分钟有氧训练'})
                    if fitness['strength_score'] and fitness['strength_score'] < 70:
                        plan['recommendations'].append({'method': 'specialized', 'focus': '力量训练',
                        'suggestion': '每周2次，进行基础力量训练'})
                else:
                    plan['recommendations'].append({'method': 'comprehensive', 'focus': '综合训练',
                    'suggestion': '建议先进行体质测试，再制定个性化计划'})
                return {'success': True, 'plan': plan}
        except Exception as e:
            logger.error(f'获取个性化训练计划失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 体育竞赛 ==========

    def create_competition(self, competition_name: str, competition_type: str,
                           start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            competition_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO sports_competition (competition_id, competition_name, competition_type, sport_type, organizer, location, start_date, end_date, max_teams, registered_teams, education_type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'registration', ?, ?)''',
                        (competition_id, competition_name, competition_type, kwargs.get('sport_type'),
                        kwargs.get('organizer'), kwargs.get('location'), start_date, kwargs.get('end_date'),
                        kwargs.get('max_teams', 16), kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建体育竞赛: {competition_name} ({competition_id})')
                    return {'success': True, 'competition_id': competition_id}
        except Exception as e:
            logger.error(f'创建体育竞赛失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_competition(self, competition_id: str, team_id: int,
                             team_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT max_teams, registered_teams, status FROM sports_competition WHERE competition_id = ?', (competition_id,))
                    comp = c.fetchone()
                    if not comp:
                        return {'success': False, 'error': '竞赛不存在'}
                    if comp[2] != 'registration':
                        return {'success': False, 'error': '报名已截止'}
                    if comp[0] and comp[1] >= comp[0]:
                        return {'success': False, 'error': '名额已满'}
                    c.execute('SELECT team_id FROM competition_results WHERE competition_id = ? AND team_id = ?',
                    (competition_id, team_id))
                    if c.fetchone():
                        return {'success': False, 'error': '该队伍已报名'}
                    c.execute('INSERT INTO competition_results (result_id, competition_id, team_id, team_name) VALUES (?, ?, ?, ?)',
                             (f"cmr_{uuid.uuid4().hex[:12]}", competition_id, team_id, team_name))
                    c.execute('UPDATE sports_competition SET registered_teams = registered_teams + 1, updated_at = ? WHERE competition_id = ?', (now, competition_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'竞赛报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_competition_result(self, competition_id: str, team_id: int,
                                  rank: int, **kwargs) -> Dict[str, Any]:
        try:
            medal = 'gold' if rank == 1 else ('silver' if rank == 2 else ('bronze' if rank == 3 else None))
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE competition_results SET rank = ?, score = ?, medal = ? WHERE competition_id = ? AND team_id = ?',
                             (rank, kwargs.get('score'), medal, competition_id, team_id))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'medal': medal}
                    return {'success': False, 'error': '竞赛报名记录不存在'}
        except Exception as e:
            logger.error(f'记录竞赛成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_competition_ranking(self, competition_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute('SELECT * FROM competition_results WHERE competition_id = ? ORDER BY rank ASC',
                (competition_id,))
                return {'success': True, 'ranking': [dict(r) for r in c.fetchall()]}
        except Exception as e:
            logger.error(f'获取竞赛排名失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 设施管理 ==========

    def register_facility(self, facility_name: str, facility_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            facility_id = f"fac_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = FACILITY_TYPES.get(facility_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO sports_facilities (facility_id, facility_name, facility_type, location, capacity, status, opening_hours, maintenance_status, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'available', ?, 'normal', ?, ?, ?)''',
                        (facility_id, facility_name, facility_type, kwargs.get('location'),
                        kwargs.get('capacity', config.get('capacity', 0)), kwargs.get('opening_hours', '06:00-22:00'),
                        kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'登记体育设施: {facility_name} ({facility_id})')
                    return {'success': True, 'facility_id': facility_id}
        except Exception as e:
            logger.error(f'登记体育设施失败: {e}')
            return {'success': False, 'error': str(e)}

    def reserve_facility(self, facility_id: str, user_id: int, user_name: str,
                         usage_date: str, start_time: str, end_time: str, **kwargs) -> Dict[str, Any]:
        try:
            usage_id = f"fau_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT status FROM sports_facilities WHERE facility_id = ?', (facility_id,))
                    facility = c.fetchone()
                    if not facility:
                        return {'success': False, 'error': '设施不存在'}
                    if facility[0] != 'available':
                        return {'success': False, 'error': '设施不可用'}
                    c.execute('''SELECT COUNT(*) FROM facility_usage WHERE facility_id = ? AND usage_date = ? AND ((start_time < ? AND end_time > ?) OR (start_time < ? AND end_time > ?))''',
                        (facility_id, usage_date, end_time, start_time, end_time, start_time))
                    if c.fetchone()[0] > 0:
                        return {'success': False, 'error': '该时间段已被预约'}
                    c.execute('''INSERT INTO facility_usage (usage_id, facility_id, user_id, user_name, education_type, usage_date, start_time, end_time, purpose, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'reserved', ?)''',
                        (usage_id, facility_id, user_id, user_name, kwargs.get('education_type'),
                        usage_date, start_time, end_time, kwargs.get('purpose', '训练'), datetime.now().isoformat()))
                    conn.commit()
                    return {'success': True, 'usage_id': usage_id}
        except Exception as e:
            logger.error(f'预约设施失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_facility_usage(self, usage_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE facility_usage SET status = ?, purpose = ? WHERE usage_id = ?',
                             ('completed', kwargs.get('purpose', '训练'), usage_id))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预约记录不存在'}
        except Exception as e:
            logger.error(f'记录设施使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_facility_maintenance(self, facility_id: str,
                                    maintenance_status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'available' if maintenance_status == 'normal' else 'maintenance'
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE sports_facilities SET maintenance_status = ?, status = ?, updated_at = ? WHERE facility_id = ?',
                             (maintenance_status, status, now, facility_id))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '设施不存在'}
        except Exception as e:
            logger.error(f'更新设施维护状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全保障 ==========

    def create_safety_check(self, check_type: str, location: str,
                            check_date: str, **kwargs) -> Dict[str, Any]:
        try:
            safety_id = f"sft_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO sports_safety (safety_id, check_type, location, description, check_date, check_result, issues_found, rectification_status, inspector_id, inspector_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (safety_id, check_type, location, kwargs.get('description'),
                        check_date, kwargs.get('check_result', 'passed'), kwargs.get('issues_found'),
                        kwargs.get('rectification_status', 'none'), kwargs.get('inspector_id'),
                        kwargs.get('inspector_name'), datetime.now().isoformat()))
                    conn.commit()
                    logger.info(f'创建安全检查记录: {check_type} ({safety_id})')
                    return {'success': True, 'safety_id': safety_id}
        except Exception as e:
            logger.error(f'创建安全检查记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_safety_incident(self, incident_type: str, location: str,
                               date_time: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"sri_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO safety_records (record_id, incident_type, location, description, severity, injured_person, emergency_response, date_time, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (record_id, incident_type, location, kwargs.get('description'),
                        kwargs.get('severity', 'minor'), kwargs.get('injured_person'),
                        kwargs.get('emergency_response'), date_time,
                        kwargs.get('status', 'processing'), datetime.now().isoformat()))
                    conn.commit()
                    logger.warning(f'记录安全事故: {incident_type} ({record_id})')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录安全事故失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_incident_status(self, record_id: str, status: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE safety_records SET status = ? WHERE record_id = ?', (status, record_id))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '事故记录不存在'}
        except Exception as e:
            logger.error(f'更新事故状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_safety_report(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = 'SELECT * FROM safety_records WHERE 1=1'
                params = []
                if start_date:
                    query += ' AND date_time >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND date_time <= ?'
                    params.append(end_date)
                c.execute(query, params)
                incidents = [dict(i) for i in c.fetchall()]
                c.execute('SELECT COUNT(*) FROM sports_safety WHERE check_result = ?', ('failed',))
                failed_checks = c.fetchone()[0]
                return {'success': True, 'incident_count': len(incidents), 'failed_check_count': failed_checks,
                'incidents': incidents}
        except Exception as e:
            logger.error(f'获取安全报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 健康教育 ==========

    def create_health_course(self, topic: str, title: str, **kwargs) -> Dict[str, Any]:
        try:
            education_id = f"hec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = HEALTH_TOPICS.get(topic, {})
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('''INSERT INTO health_education (education_id, topic, education_type, title, description, content, duration, presenter, target_audience, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?)''',
                        (education_id, topic, kwargs.get('education_type'), title,
                        kwargs.get('description'), kwargs.get('content'),
                        kwargs.get('duration', config.get('duration', 45)), kwargs.get('presenter'),
                        kwargs.get('target_audience'), now, now))
                    conn.commit()
                    logger.info(f'创建健康教育课程: {title} ({education_id})')
                    return {'success': True, 'education_id': education_id}
        except Exception as e:
            logger.error(f'创建健康教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_health_course(self, education_id: str, participant_id: int,
                               participant_name: str = None) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT status FROM health_education WHERE education_id = ?', (education_id,))
                    course = c.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[0] != 'planned':
                        return {'success': False, 'error': '课程状态不允许报名'}
                    c.execute('INSERT OR IGNORE INTO education_records (record_id, education_id, participant_id, participant_name, education_type, attended) VALUES (?, ?, ?, ?, ?, 0)',
                             (f"her_{uuid.uuid4().hex[:12]}", education_id, participant_id, participant_name,
                             kwargs.get('education_type')))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该课程'}
        except Exception as e:
            logger.error(f'健康教育课程报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_health_course_attendance(self, education_id: str, participant_id: int,
                                        attended: bool = True, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE education_records SET attended = ?, feedback = ?, satisfaction_score = ? WHERE education_id = ? AND participant_id = ?',
                             (1 if attended else 0, kwargs.get('feedback'), kwargs.get('satisfaction_score'),
                             education_id, participant_id))
                    if c.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录健康教育出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_health_record(self, participant_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = 'SELECT * FROM education_records WHERE participant_id = ?'
                params = [participant_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                c.execute(query, params)
                records = [dict(r) for r in c.fetchall()]
                return {'success': True, 'records': records, 'count': len(records)}
        except Exception as e:
            logger.error(f'获取健康档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_overall_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                tables = ['sports_courses', 'sports_activities', 'physical_fitness', 'sports_training',
                          'sports_competition', 'sports_facilities', 'safety_records', 'health_education']
                stats = {}
                for table in tables:
                    query = f'SELECT COUNT(*) FROM {table}'
                    params = []
                    if education_type and table not in ['sports_facilities', 'safety_records']:
                        query += ' WHERE education_type = ?'
                        params.append(education_type)
                    c.execute(query, params)
                    stats[table] = c.fetchone()[0]
                return {
                    'success': True,
                    'education_type': education_type,
                    'stats': {
                        'courses': stats['sports_courses'],
                        'activities': stats['sports_activities'],
                        'fitness_tests': stats['physical_fitness'],
                        'training_programs': stats['sports_training'],
                        'competitions': stats['sports_competition'],
                        'facilities': stats['sports_facilities'],
                        'safety_incidents': stats['safety_records'],
                        'health_education': stats['health_education']
                    }
                }
        except Exception as e:
            logger.error(f'获取整体统计失败: {e}')
            return {'success': False, 'error': str(e)}




































































































































