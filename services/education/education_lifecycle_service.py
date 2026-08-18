from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育全生命周期服务 (v15.23.0) ====================================== 提供学前教育、基础教育、高等教育、继续教育、终身学习、职业教育、特殊教育和老年教育的综合管理服务。  核心能力： 1. 学前教育 - 托儿所、幼儿园、早教中心管理 2. 基础教育 - 小学、初中、高中课程与评估 3. 高等教育 - 本科、研究生、成人高等教育管理 4. 继续教育 - 成人教育、在职培训、职业资格培训 5. 终身学习 - 学习型社会、社区教育、在线教育 6. 职业教育 - 中职、高职、技工教育、产教融合 7. 特殊教育 - 特殊儿童、融合教育、康复教育 8. 老年教育 - 老年大学、社区老年课程 9. 全生命周期跟踪 - 学习轨迹、进度监控、预警系统 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_lifecycle_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationLifecycle')


# ========== 教育配置 ==========

EDUCATION_STAGES = {
    'preschool': {'name': '学前教育', 'age_range': '0-6', 'duration': '3-4年'},
    'primary': {'name': '小学教育', 'age_range': '6-12', 'duration': '6年'},
    'junior_high': {'name': '初中教育', 'age_range': '12-15', 'duration': '3年'},
    'senior_high': {'name': '高中教育', 'age_range': '15-18', 'duration': '3年'},
    'higher': {'name': '高等教育', 'age_range': '18+', 'duration': '3-6年'},
    'vocational': {'name': '职业教育', 'age_range': '15+', 'duration': '2-5年'},
    'continuing': {'name': '继续教育', 'age_range': '18+', 'duration': '灵活'},
    'lifelong': {'name': '终身学习', 'age_range': '全年龄段', 'duration': '终身'}
}

PRESCHOOL_TYPES = {
    'nursery': {'name': '托儿所', 'age_range': '0-3', 'capacity': 50},
    'kindergarten': {'name': '幼儿园', 'age_range': '3-6', 'capacity': 300},
    'early_education': {'name': '早教中心', 'age_range': '0-3', 'capacity': 100},
    'parent_child': {'name': '亲子教育', 'age_range': '0-6', 'capacity': 80},
    'child_care': {'name': '幼儿托管', 'age_range': '3-6', 'capacity': 60},
    'preschool_institution': {'name': '幼教机构', 'age_range': '0-6', 'capacity': 200},
    'preschool_service': {'name': '学前教育服务', 'age_range': '0-6', 'capacity': 150},
    'kindergarten_management': {'name': '幼儿园管理', 'age_range': '3-6', 'capacity': 400}
}

BASIC_EDUCATION = {
    'primary_school': {'name': '小学', 'grade_level': '1-6', 'type': 'compulsory'},
    'junior_high': {'name': '初中', 'grade_level': '7-9', 'type': 'compulsory'},
    'senior_high': {'name': '高中', 'grade_level': '10-12', 'type': 'general'},
    'compulsory': {'name': '义务教育', 'grade_level': '1-9', 'type': 'compulsory'},
    'general': {'name': '普通教育', 'grade_level': '1-12', 'type': 'general'},
    'curriculum': {'name': '基础教育课程', 'subjects': ['语文', '数学', '英语', '科学', '艺术']},
    'assessment': {'name': '基础教育评估', 'methods': ['考试', '测验', '作业', '表现']},
    'management': {'name': '基础教育管理', 'areas': ['学籍', '教务', '师资', '安全']}
}

HIGHER_EDUCATION = {
    'undergraduate': {'name': '本科教育', 'duration': '4年', 'degree': '学士'},
    'graduate': {'name': '研究生教育', 'duration': '2-3年', 'degree': '硕士/博士'},
    'adult_higher': {'name': '成人高等教育', 'duration': '2.5-5年', 'degree': '学士/专科'},
    'higher_vocational': {'name': '高等职业教育', 'duration': '3年', 'degree': '专科'},
    'sino_foreign': {'name': '中外合作办学', 'duration': '3-4年', 'degree': '双学位'},
    'assessment': {'name': '高等教育评估', 'types': ['教学评估', '学科评估', '认证']},
    'degree': {'name': '学位管理', 'levels': ['学士', '硕士', '博士']},
    'university': {'name': '高校管理', 'areas': ['招生', '教学', '科研', '后勤']}
}

CONTINUING_EDUCATION = {
    'adult_education': {'name': '成人教育', 'target': '在职人员', 'form': '业余'},
    'on_job_training': {'name': '在职培训', 'target': '企业员工', 'form': '集中'},
    'position_training': {'name': '岗位培训', 'target': '特定岗位', 'form': '专项'},
    'qualification': {'name': '职业资格培训', 'target': '考证人员', 'form': '考前'},
    'degree_upgrade': {'name': '学历提升', 'target': '在职人员', 'form': '业余'},
    'skill_training': {'name': '技能培训', 'target': '技能提升者', 'form': '短期'},
    'online_learning': {'name': '在线学习', 'target': '全体', 'form': '网络'},
    'community_education': {'name': '社区教育', 'target': '社区居民', 'form': '灵活'}
}

LIFELONG_LEARNING = {
    'learning_society': {'name': '学习型社会', 'scope': '全社会', 'goal': '终身学习'},
    'lifelong_system': {'name': '终身教育体系', 'scope': '全年龄段', 'goal': '持续发展'},
    'community_learning': {'name': '社区教育', 'scope': '社区', 'goal': '居民素质提升'},
    'senior_learning': {'name': '老年教育', 'scope': '老年人', 'goal': '健康快乐'},
    'career_development': {'name': '职业发展', 'scope': '职场人士', 'goal': '能力提升'},
    'personal_growth': {'name': '个人提升', 'scope': '全体', 'goal': '自我实现'},
    'corporate_training': {'name': '企业培训', 'scope': '企业员工', 'goal': '绩效提升'},
    'online_edu': {'name': '在线教育', 'scope': '全体', 'goal': '便捷学习'}
}

VOCATIONAL_EDUCATION = {
    'secondary_vocational': {'name': '中等职业教育', 'duration': '3年', 'level': '中职'},
    'higher_vocational': {'name': '高等职业教育', 'duration': '3年', 'level': '高职'},
    'technical_education': {'name': '技工教育', 'duration': '2-4年', 'level': '技工'},
    'vocational_training': {'name': '职业培训', 'duration': '短期', 'level': '专项'},
    'skill_assessment': {'name': '技能鉴定', 'types': ['初级', '中级', '高级', '技师']},
    'school_enterprise': {'name': '校企合作', 'model': '订单班/实训基地'},
    'industry_education': {'name': '产教融合', 'model': '产业学院/实训中心'},
    'vocational_guidance': {'name': '职业指导', 'services': ['咨询', '测评', '规划']}
}

SPECIAL_EDUCATION = {
    'special_child': {'name': '特殊儿童教育', 'target': '特殊需要儿童', 'approach': '个别化'},
    'inclusive_education': {'name': '融合教育', 'target': '特殊儿童', 'approach': '随班就读'},
    'rehabilitation': {'name': '康复教育', 'target': '有康复需求者', 'approach': '康复训练'},
    'special_institution': {'name': '特教机构', 'type': ['学校', '康复中心', '培训机构']},
    'special_resources': {'name': '特教资源', 'types': ['教材', '教具', '辅助技术']},
    'special_teacher': {'name': '特教教师', 'specialty': ['教育', '康复', '心理']},
    'individualized': {'name': '个别化教育', 'plan': 'IEP', 'review': '年度'},
    'special_assessment': {'name': '特教评估', 'types': ['入学评估', '进展评估', '毕业评估']}
}


class EducationLifecycleService:
    """教育全生命周期服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS education_stages ( stage_id TEXT PRIMARY KEY, stage_name TEXT NOT NULL, stage_code TEXT NOT NULL, age_range TEXT, duration TEXT, education_type TEXT, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS stage_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, student_name TEXT, stage_code TEXT NOT NULL, start_date TEXT, end_date TEXT, institution_id TEXT, institution_name TEXT, education_type TEXT, status TEXT DEFAULT 'in_progress', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS preschool_education ( preschool_id TEXT PRIMARY KEY, name TEXT NOT NULL, preschool_type TEXT, address TEXT, phone TEXT, capacity INTEGER DEFAULT 100, enrolled_count INTEGER DEFAULT 0, director TEXT, teacher_count INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS preschool_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, preschool_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, child_name TEXT, guardian_name TEXT, guardian_phone TEXT, enrollment_date TEXT, expected_graduation TEXT, education_type TEXT, status TEXT DEFAULT 'enrolled', created_at TEXT, UNIQUE(preschool_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS basic_education ( school_id TEXT PRIMARY KEY, school_name TEXT NOT NULL, school_type TEXT, address TEXT, phone TEXT, grade_level TEXT, student_count INTEGER DEFAULT 0, teacher_count INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS basic_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, school_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, grade TEXT, class_name TEXT, enrollment_date TEXT, expected_graduation TEXT, education_type TEXT, status TEXT DEFAULT 'enrolled', created_at TEXT, UNIQUE(school_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS higher_education ( university_id TEXT PRIMARY KEY, university_name TEXT NOT NULL, university_type TEXT, address TEXT, phone TEXT, level TEXT, department_count INTEGER DEFAULT 0, student_count INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS higher_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, university_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, department TEXT, major TEXT, degree TEXT, enrollment_date TEXT, expected_graduation TEXT, education_type TEXT, status TEXT DEFAULT 'enrolled', created_at TEXT, UNIQUE(university_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS continuing_education ( course_id TEXT PRIMARY KEY, course_name TEXT NOT NULL, course_type TEXT, provider TEXT, duration TEXT, credit INTEGER DEFAULT 0, price REAL DEFAULT 0, max_participants INTEGER DEFAULT 50, enrolled_count INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS continuing_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, course_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, enrollment_date TEXT, completion_date TEXT, score REAL, certificate_no TEXT, education_type TEXT, status TEXT DEFAULT 'in_progress', created_at TEXT, UNIQUE(course_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS lifelong_learning ( program_id TEXT PRIMARY KEY, program_name TEXT NOT NULL, program_type TEXT, provider TEXT, description TEXT, duration TEXT, max_participants INTEGER DEFAULT 100, enrolled_count INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, program_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, enrollment_date TEXT, completion_date TEXT, progress INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'in_progress', created_at TEXT, UNIQUE(program_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS vocational_education ( school_id TEXT PRIMARY KEY, school_name TEXT NOT NULL, school_type TEXT, address TEXT, phone TEXT, specialty TEXT, skill_level TEXT, student_count INTEGER DEFAULT 0, teacher_count INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS vocational_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, school_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, specialty TEXT, skill_level TEXT, enrollment_date TEXT, expected_graduation TEXT, education_type TEXT, status TEXT DEFAULT 'enrolled', created_at TEXT, UNIQUE(school_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS special_education ( institution_id TEXT PRIMARY KEY, institution_name TEXT NOT NULL, institution_type TEXT, address TEXT, phone TEXT, service_type TEXT, capacity INTEGER DEFAULT 50, enrolled_count INTEGER DEFAULT 0, staff_count INTEGER DEFAULT 0, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS special_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, institution_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, disability_type TEXT, iep_plan TEXT, enrollment_date TEXT, expected_graduation TEXT, education_type TEXT, status TEXT DEFAULT 'enrolled', created_at TEXT, UNIQUE(institution_id, student_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS lifecycle_tracking ( tracking_id TEXT PRIMARY KEY, student_id INTEGER NOT NULL, student_name TEXT, current_stage TEXT, education_type TEXT, total_learning_hours INTEGER DEFAULT 0, total_courses INTEGER DEFAULT 0, milestone_count INTEGER DEFAULT 0, status TEXT DEFAULT 'tracking', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS tracking_data ( id INTEGER PRIMARY KEY AUTOINCREMENT, tracking_id TEXT NOT NULL, stage_code TEXT, activity_type TEXT, activity_name TEXT, duration_hours INTEGER DEFAULT 0, completed INTEGER DEFAULT 0, timestamp TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS lifecycle_alerts ( alert_id TEXT PRIMARY KEY, student_id INTEGER NOT NULL, student_name TEXT, alert_type TEXT, alert_level TEXT, message TEXT, status TEXT DEFAULT 'active', created_at TEXT, resolved_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS alert_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, alert_id TEXT NOT NULL, student_id INTEGER NOT NULL, alert_type TEXT, message TEXT, resolved_by TEXT, resolved_at TEXT, resolution TEXT, created_at TEXT ) ''')
                conn.commit()
                logger.info('教育全生命周期服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 学前教育 ==========

    def create_preschool(self, name: str, preschool_type: str, **kwargs) -> Dict[str, Any]:
        try:
            preschool_id = f"ps_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PRESCHOOL_TYPES.get(preschool_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO preschool_education ( preschool_id, name, preschool_type, address, phone, capacity, enrolled_count, director, teacher_count, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'active', ?, ?) ''', (preschool_id, name, preschool_type,
                          kwargs.get('address'), kwargs.get('phone'),
                          kwargs.get('capacity', config.get('capacity', 100)),
                          kwargs.get('director'), kwargs.get('teacher_count', 0),
                          kwargs.get('education_type', 'K12'), now, now))
                    conn.commit()
                    logger.info(f'创建学前教育机构: {name} ({preschool_id})')
                    return {'success': True, 'preschool_id': preschool_id}
        except Exception as e:
            logger.error(f'创建学前教育机构失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_preschool(self, preschool_id: str, student_id: int,
                         child_name: str, guardian_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT capacity, enrolled_count, status FROM preschool_education WHERE preschool_id = ?', (preschool_id,))
                    preschool = cursor.fetchone()
                    if not preschool:
                        return {'success': False, 'error': '学前教育机构不存在'}
                    if preschool[2] != 'active':
                        return {'success': False, 'error': '机构状态不允许招生'}
                    if preschool[0] and preschool[1] >= preschool[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO preschool_records (preschool_id, student_id, student_name, child_name, guardian_name, guardian_phone, enrollment_date, expected_graduation, education_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (preschool_id, student_id, kwargs.get('student_name'),
                                  child_name, guardian_name, kwargs.get('guardian_phone'),
                                  now[:10], kwargs.get('expected_graduation'),
                                  kwargs.get('education_type', 'K12'), 'enrolled'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE preschool_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE preschool_id = ?', (now, preschool_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已在该机构就读'}
        except Exception as e:
            logger.error(f'学前教育报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_preschool_record(self, preschool_id: str, student_id: int,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_values = []
                    if 'child_name' in kwargs:
                        update_fields.append('child_name = ?')
                        update_values.append(kwargs['child_name'])
                    if 'guardian_name' in kwargs:
                        update_fields.append('guardian_name = ?')
                        update_values.append(kwargs['guardian_name'])
                    if 'guardian_phone' in kwargs:
                        update_fields.append('guardian_phone = ?')
                        update_values.append(kwargs['guardian_phone'])
                    if 'expected_graduation' in kwargs:
                        update_fields.append('expected_graduation = ?')
                        update_values.append(kwargs['expected_graduation'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if not update_fields:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    update_values.extend([preschool_id, student_id])
                    query = f'UPDATE preschool_records SET {", ".join(update_fields)} WHERE preschool_id = ? AND student_id = ?'
                    cursor.execute(query, update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新学前教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_preschool_records(self, preschool_id: str = None,
                               status: str = None, page: int = 1,
                               page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM preschool_records WHERE 1=1'
                params = []
                if preschool_id:
                    query += ' AND preschool_id = ?'
                    params.append(preschool_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY enrollment_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学前教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 基础教育 ==========

    def create_school(self, school_name: str, school_type: str, **kwargs) -> Dict[str, Any]:
        try:
            school_id = f"sch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = BASIC_EDUCATION.get(school_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO basic_education ( school_id, school_name, school_type, address, phone, grade_level, student_count, teacher_count, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?) ''', (school_id, school_name, school_type,
                          kwargs.get('address'), kwargs.get('phone'),
                          kwargs.get('grade_level', config.get('grade_level', '')),
                          kwargs.get('teacher_count', 0),
                          kwargs.get('education_type', 'K12'), now, now))
                    conn.commit()
                    logger.info(f'创建基础教育学校: {school_name} ({school_id})')
                    return {'success': True, 'school_id': school_id}
        except Exception as e:
            logger.error(f'创建基础教育学校失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_basic_education(self, school_id: str, student_id: int,
                               student_name: str, grade: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM basic_education WHERE school_id = ?', (school_id,))
                    school = cursor.fetchone()
                    if not school:
                        return {'success': False, 'error': '学校不存在'}
                    if school[0] != 'active':
                        return {'success': False, 'error': '学校状态不允许招生'}
                    cursor.execute('INSERT OR IGNORE INTO basic_records (school_id, student_id, student_name, grade, class_name, enrollment_date, expected_graduation, education_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (school_id, student_id, student_name, grade,
                                  kwargs.get('class_name'), now[:10],
                                  kwargs.get('expected_graduation'),
                                  kwargs.get('education_type', 'K12'), 'enrolled'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE basic_education SET student_count = student_count + 1, updated_at = ? WHERE school_id = ?', (now, school_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已在该校就读'}
        except Exception as e:
            logger.error(f'基础教育报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_basic_record(self, school_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_values = []
                    if 'grade' in kwargs:
                        update_fields.append('grade = ?')
                        update_values.append(kwargs['grade'])
                    if 'class_name' in kwargs:
                        update_fields.append('class_name = ?')
                        update_values.append(kwargs['class_name'])
                    if 'expected_graduation' in kwargs:
                        update_fields.append('expected_graduation = ?')
                        update_values.append(kwargs['expected_graduation'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if not update_fields:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    update_values.extend([school_id, student_id])
                    query = f'UPDATE basic_records SET {", ".join(update_fields)} WHERE school_id = ? AND student_id = ?'
                    cursor.execute(query, update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新基础教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_basic_records(self, school_id: str = None, grade: str = None,
                           status: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM basic_records WHERE 1=1'
                params = []
                if school_id:
                    query += ' AND school_id = ?'
                    params.append(school_id)
                if grade:
                    query += ' AND grade = ?'
                    params.append(grade)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY enrollment_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取基础教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 高等教育 ==========

    def create_university(self, university_name: str, university_type: str, **kwargs) -> Dict[str, Any]:
        try:
            university_id = f"uni_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = HIGHER_EDUCATION.get(university_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO higher_education ( university_id, university_name, university_type, address, phone, level, department_count, student_count, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, 'active', ?, ?) ''', (university_id, university_name, university_type,
                          kwargs.get('address'), kwargs.get('phone'),
                          kwargs.get('level', config.get('level', '')),
                          kwargs.get('department_count', 0),
                          kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'创建高等教育机构: {university_name} ({university_id})')
                    return {'success': True, 'university_id': university_id}
        except Exception as e:
            logger.error(f'创建高等教育机构失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_higher_education(self, university_id: str, student_id: int,
                                student_name: str, department: str, major: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM higher_education WHERE university_id = ?', (university_id,))
                    university = cursor.fetchone()
                    if not university:
                        return {'success': False, 'error': '高校不存在'}
                    if university[0] != 'active':
                        return {'success': False, 'error': '高校状态不允许招生'}
                    cursor.execute('INSERT OR IGNORE INTO higher_records (university_id, student_id, student_name, department, major, degree, enrollment_date, expected_graduation, education_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (university_id, student_id, student_name, department, major,
                                  kwargs.get('degree', '学士'), now[:10],
                                  kwargs.get('expected_graduation'),
                                  kwargs.get('education_type', 'adult'), 'enrolled'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE higher_education SET student_count = student_count + 1, updated_at = ? WHERE university_id = ?', (now, university_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已在该校就读'}
        except Exception as e:
            logger.error(f'高等教育报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_higher_record(self, university_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_values = []
                    if 'department' in kwargs:
                        update_fields.append('department = ?')
                        update_values.append(kwargs['department'])
                    if 'major' in kwargs:
                        update_fields.append('major = ?')
                        update_values.append(kwargs['major'])
                    if 'degree' in kwargs:
                        update_fields.append('degree = ?')
                        update_values.append(kwargs['degree'])
                    if 'expected_graduation' in kwargs:
                        update_fields.append('expected_graduation = ?')
                        update_values.append(kwargs['expected_graduation'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if not update_fields:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    update_values.extend([university_id, student_id])
                    query = f'UPDATE higher_records SET {", ".join(update_fields)} WHERE university_id = ? AND student_id = ?'
                    cursor.execute(query, update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新高等教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_higher_records(self, university_id: str = None, department: str = None,
                            status: str = None, page: int = 1,
                            page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM higher_records WHERE 1=1'
                params = []
                if university_id:
                    query += ' AND university_id = ?'
                    params.append(university_id)
                if department:
                    query += ' AND department = ?'
                    params.append(department)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY enrollment_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取高等教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 继续教育 ==========

    def create_continuing_course(self, course_name: str, course_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"cc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CONTINUING_EDUCATION.get(course_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO continuing_education ( course_id, course_name, course_type, provider, duration, credit, price, max_participants, enrolled_count, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?) ''', (course_id, course_name, course_type,
                          kwargs.get('provider'), kwargs.get('duration', config.get('form', '')),
                          kwargs.get('credit', 0), kwargs.get('price', 0),
                          kwargs.get('max_participants', 50),
                          kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'创建继续教育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建继续教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_continuing_course(self, course_id: str, student_id: int,
                                 student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM continuing_education WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许报名'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO continuing_records (course_id, student_id, student_name, enrollment_date, education_type, status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (course_id, student_id, student_name, now[:10],
                                  kwargs.get('education_type', 'adult'), 'in_progress'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE continuing_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该课程'}
        except Exception as e:
            logger.error(f'继续教育报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_continuing_score(self, course_id: str, student_id: int,
                                score: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            certificate_no = f"CEC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper( )}" if score >= 60 else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE continuing_records SET score = ?, completion_date = ?, certificate_no = ?, status = ? WHERE course_id = ? AND student_id = ? AND status = ? ''', (score, now[:10], certificate_no,
                          'completed' if score >= 60 else 'failed',
                          course_id, student_id, 'in_progress'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'certificate_no': certificate_no}
                    return {'success': False, 'error': '记录不存在或状态不允许'}
        except Exception as e:
            logger.error(f'记录继续教育成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_continuing_record(self, course_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_values = []
                    if 'completion_date' in kwargs:
                        update_fields.append('completion_date = ?')
                        update_values.append(kwargs['completion_date'])
                    if 'score' in kwargs:
                        update_fields.append('score = ?')
                        update_values.append(kwargs['score'])
                    if 'certificate_no' in kwargs:
                        update_fields.append('certificate_no = ?')
                        update_values.append(kwargs['certificate_no'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if not update_fields:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    update_values.extend([course_id, student_id])
                    query = f'UPDATE continuing_records SET {", ".join(update_fields)} WHERE course_id = ? AND student_id = ?'
                    cursor.execute(query, update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新继续教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_continuing_records(self, course_id: str = None, status: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM continuing_records WHERE 1=1'
                params = []
                if course_id:
                    query += ' AND course_id = ?'
                    params.append(course_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY enrollment_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取继续教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 终身学习 ==========

    def create_lifelong_program(self, program_name: str, program_type: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"llp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = LIFELONG_LEARNING.get(program_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO lifelong_learning ( program_id, program_name, program_type, provider, description, duration, max_participants, enrolled_count, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?) ''', (program_id, program_name, program_type,
                          kwargs.get('provider'), kwargs.get('description'),
                          kwargs.get('duration', config.get('goal', '')),
                          kwargs.get('max_participants', 100),
                          kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'创建终身学习项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建终身学习项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_lifelong_program(self, program_id: str, student_id: int,
                                student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM lifelong_learning WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    if program[2] != 'active':
                        return {'success': False, 'error': '项目状态不允许报名'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO learning_records (program_id, student_id, student_name, enrollment_date, education_type, status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (program_id, student_id, student_name, now[:10],
                                  kwargs.get('education_type', 'adult'), 'in_progress'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE lifelong_learning SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该项目'}
        except Exception as e:
            logger.error(f'终身学习报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_learning_progress(self, program_id: str, student_id: int,
                                 progress: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'completed' if progress >= 100 else 'in_progress'
            completion_date = now[:10] if progress >= 100 else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE learning_records SET progress = ?, status = ?, completion_date = ? WHERE program_id = ? AND student_id = ? ''', (progress, status, completion_date, program_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_lifelong_records(self, program_id: str = None, status: str = None,
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_records WHERE 1=1'
                params = []
                if program_id:
                    query += ' AND program_id = ?'
                    params.append(program_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY enrollment_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取终身学习记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 职业教育 ==========

    def create_vocational_school(self, school_name: str, school_type: str, **kwargs) -> Dict[str, Any]:
        try:
            school_id = f"voc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = VOCATIONAL_EDUCATION.get(school_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO vocational_education ( school_id, school_name, school_type, address, phone, specialty, skill_level, student_count, teacher_count, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?) ''', (school_id, school_name, school_type,
                          kwargs.get('address'), kwargs.get('phone'),
                          kwargs.get('specialty'), kwargs.get('skill_level', config.get('level', '')),
                          kwargs.get('teacher_count', 0),
                          kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'创建职业教育机构: {school_name} ({school_id})')
                    return {'success': True, 'school_id': school_id}
        except Exception as e:
            logger.error(f'创建职业教育机构失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_vocational_education(self, school_id: str, student_id: int,
                                    student_name: str, specialty: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM vocational_education WHERE school_id = ?', (school_id,))
                    school = cursor.fetchone()
                    if not school:
                        return {'success': False, 'error': '职业教育机构不存在'}
                    if school[0] != 'active':
                        return {'success': False, 'error': '机构状态不允许招生'}
                    cursor.execute('INSERT OR IGNORE INTO vocational_records (school_id, student_id, student_name, specialty, skill_level, enrollment_date, expected_graduation, education_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (school_id, student_id, student_name, specialty,
                                  kwargs.get('skill_level'), now[:10],
                                  kwargs.get('expected_graduation'),
                                  kwargs.get('education_type', 'adult'), 'enrolled'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE vocational_education SET student_count = student_count + 1, updated_at = ? WHERE school_id = ?', (now, school_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已在该机构就读'}
        except Exception as e:
            logger.error(f'职业教育报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_vocational_record(self, school_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_values = []
                    if 'specialty' in kwargs:
                        update_fields.append('specialty = ?')
                        update_values.append(kwargs['specialty'])
                    if 'skill_level' in kwargs:
                        update_fields.append('skill_level = ?')
                        update_values.append(kwargs['skill_level'])
                    if 'expected_graduation' in kwargs:
                        update_fields.append('expected_graduation = ?')
                        update_values.append(kwargs['expected_graduation'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if not update_fields:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    update_values.extend([school_id, student_id])
                    query = f'UPDATE vocational_records SET {", ".join(update_fields)} WHERE school_id = ? AND student_id = ?'
                    cursor.execute(query, update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新职业教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_vocational_records(self, school_id: str = None, specialty: str = None,
                                status: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM vocational_records WHERE 1=1'
                params = []
                if school_id:
                    query += ' AND school_id = ?'
                    params.append(school_id)
                if specialty:
                    query += ' AND specialty = ?'
                    params.append(specialty)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY enrollment_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取职业教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 特殊教育 ==========

    def create_special_institution(self, institution_name: str, institution_type: str, **kwargs) -> Dict[str, Any]:
        try:
            institution_id = f"spi_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SPECIAL_EDUCATION.get(institution_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO special_education ( institution_id, institution_name, institution_type, address, phone, service_type, capacity, enrolled_count, staff_count, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?) ''', (institution_id, institution_name, institution_type,
                          kwargs.get('address'), kwargs.get('phone'),
                          kwargs.get('service_type', config.get('type', '')),
                          kwargs.get('capacity', config.get('capacity', 50)),
                          kwargs.get('staff_count', 0),
                          kwargs.get('education_type', 'K12'), now, now))
                    conn.commit()
                    logger.info(f'创建特殊教育机构: {institution_name} ({institution_id})')
                    return {'success': True, 'institution_id': institution_id}
        except Exception as e:
            logger.error(f'创建特殊教育机构失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_special_education(self, institution_id: str, student_id: int,
                                 student_name: str, disability_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT capacity, enrolled_count, status FROM special_education WHERE institution_id = ?', (institution_id,))
                    institution = cursor.fetchone()
                    if not institution:
                        return {'success': False, 'error': '特殊教育机构不存在'}
                    if institution[2] != 'active':
                        return {'success': False, 'error': '机构状态不允许招生'}
                    if institution[0] and institution[1] >= institution[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO special_records (institution_id, student_id, student_name, disability_type, iep_plan, enrollment_date, expected_graduation, education_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (institution_id, student_id, student_name, disability_type,
                                  kwargs.get('iep_plan'), now[:10],
                                  kwargs.get('expected_graduation'),
                                  kwargs.get('education_type', 'K12'), 'enrolled'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE special_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE institution_id = ?', (now, institution_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已在该机构就读'}
        except Exception as e:
            logger.error(f'特殊教育报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_special_record(self, institution_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_values = []
                    if 'disability_type' in kwargs:
                        update_fields.append('disability_type = ?')
                        update_values.append(kwargs['disability_type'])
                    if 'iep_plan' in kwargs:
                        update_fields.append('iep_plan = ?')
                        update_values.append(kwargs['iep_plan'])
                    if 'expected_graduation' in kwargs:
                        update_fields.append('expected_graduation = ?')
                        update_values.append(kwargs['expected_graduation'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if not update_fields:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    update_values.extend([institution_id, student_id])
                    query = f'UPDATE special_records SET {", ".join(update_fields)} WHERE institution_id = ? AND student_id = ?'
                    cursor.execute(query, update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新特殊教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_special_records(self, institution_id: str = None, disability_type: str = None,
                             status: str = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM special_records WHERE 1=1'
                params = []
                if institution_id:
                    query += ' AND institution_id = ?'
                    params.append(institution_id)
                if disability_type:
                    query += ' AND disability_type = ?'
                    params.append(disability_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY enrollment_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取特殊教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 老年教育 ==========

    def create_senior_program(self, program_name: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"sen_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO lifelong_learning ( program_id, program_name, program_type, provider, description, duration, max_participants, enrolled_count, education_type, status, created_at, updated_at ) VALUES (?, ?, 'senior_learning', ?, ?, ?, ?, 0, 'adult', 'active', ?, ?) ''', (program_id, program_name,
                          kwargs.get('provider', '老年大学'), kwargs.get('description'),
                          kwargs.get('duration', '灵活'),
                          kwargs.get('max_participants', 50), now, now))
                    conn.commit()
                    logger.info(f'创建老年教育项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建老年教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_senior_program(self, program_id: str, student_id: int,
                              student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM lifelong_learning WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '老年教育项目不存在'}
                    if program[2] != 'active':
                        return {'success': False, 'error': '项目状态不允许报名'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO learning_records (program_id, student_id, student_name, enrollment_date, education_type, status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (program_id, student_id, student_name, now[:10],
                                  kwargs.get('education_type', 'adult'), 'in_progress'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE lifelong_learning SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该项目'}
        except Exception as e:
            logger.error(f'老年教育报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_senior_progress(self, program_id: str, student_id: int,
                               progress: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'completed' if progress >= 100 else 'in_progress'
            completion_date = now[:10] if progress >= 100 else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE learning_records SET progress = ?, status = ?, completion_date = ? WHERE program_id = ? AND student_id = ? ''', (progress, status, completion_date, program_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新老年教育进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_senior_records(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(''' SELECT lr.* FROM learning_records lr JOIN lifelong_learning ll ON lr.program_id = ll.program_id WHERE ll.program_type = 'senior_learning' ''')
                all_records = [dict(r) for r in cursor.fetchall()]
                total = len(all_records)
                records = all_records[(page - 1) * page_size:page * page_size]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取老年教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 全生命周期跟踪 ==========

    def create_lifecycle_tracking(self, student_id: int, student_name: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            tracking_id = f"lct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT tracking_id FROM lifecycle_tracking WHERE student_id = ?', (student_id,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已存在跟踪记录'}
                    cursor.execute(''' INSERT INTO lifecycle_tracking ( tracking_id, student_id, student_name, current_stage, education_type, total_learning_hours, total_courses, milestone_count, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 'tracking', ?, ?) ''', (tracking_id, student_id, student_name,
                          kwargs.get('current_stage', 'preschool'),
                          kwargs.get('education_type', 'K12'), now, now))
                    conn.commit()
                    logger.info(f'创建全生命周期跟踪: {student_name} ({tracking_id})')
                    return {'success': True, 'tracking_id': tracking_id}
        except Exception as e:
            logger.error(f'创建全生命周期跟踪失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_tracking_activity(self, tracking_id: str, stage_code: str,
                              activity_type: str, activity_name: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM lifecycle_tracking WHERE tracking_id = ?', (tracking_id,))
                    tracking = cursor.fetchone()
                    if not tracking:
                        return {'success': False, 'error': '跟踪记录不存在'}
                    if tracking[0] != 'tracking':
                        return {'success': False, 'error': '跟踪状态不允许添加活动'}
                    cursor.execute(''' INSERT INTO tracking_data (tracking_id, stage_code, activity_type, activity_name, duration_hours, completed, timestamp, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (tracking_id, stage_code, activity_type, activity_name,
                          kwargs.get('duration_hours', 0), kwargs.get('completed', 0),
                          now[:19], now))
                    cursor.execute(''' UPDATE lifecycle_tracking SET total_learning_hours = total_learning_hours + ?, total_courses = total_courses + 1, updated_at = ? WHERE tracking_id = ? ''', (kwargs.get('duration_hours', 0), now, tracking_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加跟踪活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_lifecycle_tracking(self, student_id: int = None,
                                tracking_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM lifecycle_tracking WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if tracking_id:
                    query += ' AND tracking_id = ?'
                    params.append(tracking_id)
                cursor.execute(query, params)
                tracking = cursor.fetchone()
                if not tracking:
                    return {'success': False, 'error': '跟踪记录不存在'}
                tracking_dict = dict(tracking)
                cursor.execute('SELECT * FROM tracking_data WHERE tracking_id = ? ORDER BY timestamp DESC',
                (tracking_dict['tracking_id'],))
                tracking_dict['activities'] = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'tracking': tracking_dict}
        except Exception as e:
            logger.error(f'获取全生命周期跟踪失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_lifecycle_report(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM lifecycle_tracking WHERE student_id = ?', (student_id,))
                tracking = cursor.fetchone()
                if not tracking:
                    return {'success': False, 'error': '跟踪记录不存在'}
                report = {
                    'student_id': student_id,
                    'student_name': tracking['student_name'],
                    'current_stage': tracking['current_stage'],
                    'education_type': tracking['education_type'],
                    'total_learning_hours': tracking['total_learning_hours'],
                    'total_courses': tracking['total_courses'],
                    'milestone_count': tracking['milestone_count'],
                    'stages': []
                }
                cursor.execute(''' SELECT sr.stage_code, sr.start_date, sr.end_date, sr.institution_name, sr.status FROM stage_records sr WHERE sr.student_id = ? ORDER BY sr.start_date ASC ''', (student_id,))
                report['stages'] = [dict(s) for s in cursor.fetchall()]
                cursor.execute(''' SELECT stage_code, COUNT(*) as activity_count, SUM(duration_hours) as total_hours FROM tracking_data td JOIN lifecycle_tracking lt ON td.tracking_id = lt.tracking_id WHERE lt.student_id = ? GROUP BY stage_code ''', (student_id,))
                report['stage_activity'] = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'生成全生命周期报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计功能 ==========

    def get_statistics(self, education_type: str = None, stage_code: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                stats['preschool'] = {
                    'institutions': 0, 'students': 0, 'records': 0
                }
                cursor.execute('SELECT COUNT(*) FROM preschool_education WHERE status = ?', ('active',))
                stats['preschool']['institutions'] = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(enrolled_count) FROM preschool_education WHERE status = ?', ('active',))
                result = cursor.fetchone()[0]
                stats['preschool']['students'] = result if result else 0
                cursor.execute('SELECT COUNT(*) FROM preschool_records')
                stats['preschool']['records'] = cursor.fetchone()[0]

                stats['basic'] = {
                    'schools': 0, 'students': 0, 'records': 0
                }
                cursor.execute('SELECT COUNT(*) FROM basic_education WHERE status = ?', ('active',))
                stats['basic']['schools'] = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(student_count) FROM basic_education WHERE status = ?', ('active',))
                result = cursor.fetchone()[0]
                stats['basic']['students'] = result if result else 0
                cursor.execute('SELECT COUNT(*) FROM basic_records')
                stats['basic']['records'] = cursor.fetchone()[0]

                stats['higher'] = {
                    'universities': 0, 'students': 0, 'records': 0
                }
                cursor.execute('SELECT COUNT(*) FROM higher_education WHERE status = ?', ('active',))
                stats['higher']['universities'] = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(student_count) FROM higher_education WHERE status = ?', ('active',))
                result = cursor.fetchone()[0]
                stats['higher']['students'] = result if result else 0
                cursor.execute('SELECT COUNT(*) FROM higher_records')
                stats['higher']['records'] = cursor.fetchone()[0]

                stats['continuing'] = {
                    'courses': 0, 'students': 0, 'records': 0, 'completed': 0
                }
                cursor.execute('SELECT COUNT(*) FROM continuing_education WHERE status = ?', ('active',))
                stats['continuing']['courses'] = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(enrolled_count) FROM continuing_education WHERE status = ?', ('active',))
                result = cursor.fetchone()[0]
                stats['continuing']['students'] = result if result else 0
                cursor.execute('SELECT COUNT(*) FROM continuing_records')
                stats['continuing']['records'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM continuing_records WHERE status = ?', ('completed',))
                stats['continuing']['completed'] = cursor.fetchone()[0]

                stats['lifelong'] = {
                    'programs': 0, 'students': 0, 'records': 0, 'completed': 0
                }
                cursor.execute('SELECT COUNT(*) FROM lifelong_learning WHERE status = ?', ('active',))
                stats['lifelong']['programs'] = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(enrolled_count) FROM lifelong_learning WHERE status = ?', ('active',))
                result = cursor.fetchone()[0]
                stats['lifelong']['students'] = result if result else 0
                cursor.execute('SELECT COUNT(*) FROM learning_records')
                stats['lifelong']['records'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM learning_records WHERE status = ?', ('completed',))
                stats['lifelong']['completed'] = cursor.fetchone()[0]

                stats['vocational'] = {
                    'schools': 0, 'students': 0, 'records': 0
                }
                cursor.execute('SELECT COUNT(*) FROM vocational_education WHERE status = ?', ('active',))
                stats['vocational']['schools'] = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(student_count) FROM vocational_education WHERE status = ?', ('active',))
                result = cursor.fetchone()[0]
                stats['vocational']['students'] = result if result else 0
                cursor.execute('SELECT COUNT(*) FROM vocational_records')
                stats['vocational']['records'] = cursor.fetchone()[0]

                stats['special'] = {
                    'institutions': 0, 'students': 0, 'records': 0
                }
                cursor.execute('SELECT COUNT(*) FROM special_education WHERE status = ?', ('active',))
                stats['special']['institutions'] = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(enrolled_count) FROM special_education WHERE status = ?', ('active',))
                result = cursor.fetchone()[0]
                stats['special']['students'] = result if result else 0
                cursor.execute('SELECT COUNT(*) FROM special_records')
                stats['special']['records'] = cursor.fetchone()[0]

                stats['lifecycle'] = {
                    'tracking_count': 0, 'active_alerts': 0
                }
                cursor.execute('SELECT COUNT(*) FROM lifecycle_tracking WHERE status = ?', ('tracking',))
                stats['lifecycle']['tracking_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM lifecycle_alerts WHERE status = ?', ('active',))
                stats['lifecycle']['active_alerts'] = cursor.fetchone()[0]

                stats['total'] = {
                    'institutions': (stats['preschool']['institutions'] + stats['basic']['schools'] +
                                     stats['higher']['universities'] + stats['vocational']['schools'] +
                                     stats['special']['institutions']),
                    'programs': (stats['continuing']['courses'] + stats['lifelong']['programs']),
                    'students': (stats['preschool']['students'] + stats['basic']['students'] +
                                  stats['higher']['students'] + stats['continuing']['students'] +
                                  stats['lifelong']['students'] + stats['vocational']['students'] +
                                  stats['special']['students']),
                    'records': (stats['preschool']['records'] + stats['basic']['records'] +
                                  stats['higher']['records'] + stats['continuing']['records'] +
                                  stats['lifelong']['records'] + stats['vocational']['records'] +
                                  stats['special']['records'])
                }

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}