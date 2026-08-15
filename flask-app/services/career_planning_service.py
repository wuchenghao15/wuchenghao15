#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 学生生涯规划服务 (v15.9.0)
====================================
提供学生生涯发展档案、职业测评、升学规划与职业探索等综合管理服务。
同时支持成人教育与K12教育的差异化需求。

核心能力：
1. 生涯档案 - 学生生涯发展档案、兴趣特长记录
2. 职业测评 - 霍兰德兴趣、MBTI性格、职业价值观、能力倾向测评
3. 升学规划 - 升学路径、目标院校、专业选择指导
4. 职业探索 - 职业信息库、职业体验、行业认知
5. 选科指导 - K12新高考选科、成人专业选择
6. 生涯课程 - 生涯规划课程、讲座、活动
7. 咨询辅导 - 一对一咨询、团体辅导
8. 成人职业发展与K12升学规划差异化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'career_planning_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CareerPlanning')


# ========== 生涯规划配置 ==========

# 职业测评量表
INTEREST_INVENTORIES = {
    'holland': {'name': '霍兰德职业兴趣测评', 'questions': 60, 'duration_minutes': 20},
    'mbti': {'name': 'MBTI性格类型测评', 'questions': 93, 'duration_minutes': 30},
    'career_values': {'name': '职业价值观测评', 'questions': 40, 'duration_minutes': 15},
    'ability_aptitude': {'name': '能力倾向测评', 'questions': 50, 'duration_minutes': 25},
    'career_maturity': {'name': '职业成熟度测评', 'questions': 36, 'duration_minutes': 15}
}

# 霍兰德6种职业兴趣类型
HOLLAND_TYPES = {
    'R': {'name': '实用型', 'traits': ['动手能力强', '喜欢具体任务', '重视实际', '不善言辞'], 'suitable_jobs': ['工程师', '技术员', '机械师', '农艺师', '运动员']},
    'I': {'name': '研究型', 'traits': ['善于观察思考', '逻辑分析强', '喜欢探究', '独立工作'], 'suitable_jobs': ['科学家', '研究员', '医师', '程序员', '分析师']},
    'A': {'name': '艺术型', 'traits': ['富有想象', '追求个性', '情感丰富', '不喜约束'], 'suitable_jobs': ['设计师', '作家', '音乐家', '演员', '摄影师']},
    'S': {'name': '社会型', 'traits': ['乐于助人', '善于沟通', '合作意识强', '责任感强'], 'suitable_jobs': ['教师', '心理咨询师', '社工', '护士', '人力资源']},
    'E': {'name': '企业型', 'traits': ['领导欲强', '敢于冒险', '目标导向', '善说服人'], 'suitable_jobs': ['管理者', '销售经理', '创业者', '律师', '市场专员']},
    'C': {'name': '常规型', 'traits': ['细心条理', '服从规范', '注重细节', '稳定可靠'], 'suitable_jobs': ['会计', '行政专员', '银行职员', '统计员', '档案管理']}
}

# MBTI 16种性格类型
MBTI_TYPES = {
    'ISTJ': {'name': '物流师', 'characteristics': '严谨、负责、务实', 'suitable_careers': ['会计师', '审计', '工程师', '军官']},
    'ISFJ': {'name': '守卫者', 'characteristics': '忠诚、体贴、细致', 'suitable_careers': ['护士', '教师', '社工', '客服']},
    'INFJ': {'name': '提倡者', 'characteristics': '理想主义、有洞察力', 'suitable_careers': ['心理咨询师', '作家', '教师', '艺术家']},
    'INTJ': {'name': '建筑师', 'characteristics': '独立、战略思维强', 'suitable_careers': ['科学家', '建筑师', '战略顾问', '投资人']},
    'ISTP': {'name': '鉴赏家', 'characteristics': '灵活、善于操作', 'suitable_careers': ['工程师', '飞行员', '机械师', '程序员']},
    'ISFP': {'name': '探险家', 'characteristics': '敏感、审美、和谐', 'suitable_careers': ['设计师', '艺术家', '兽医', '厨师']},
    'INFP': {'name': '调停者', 'characteristics': '理想主义、富有同情心', 'suitable_careers': ['作家', '心理咨询师', '艺术家', '教师']},
    'INTP': {'name': '逻辑学家', 'characteristics': '理性、好奇、创新', 'suitable_careers': ['科学家', '程序员', '分析师', '教授']},
    'ESTP': {'name': '企业家', 'characteristics': '精力充沛、行动派', 'suitable_careers': ['销售', '创业者', '运动员', '急救员']},
    'ESFP': {'name': '表演者', 'characteristics': '热情、活泼、社交', 'suitable_careers': ['演员', '主持人', '销售', '导游']},
    'ENFP': {'name': '竞选者', 'characteristics': '热情、有创意、自由', 'suitable_careers': ['记者', '营销', '心理咨询师', '演员']},
    'ENTP': {'name': '辩论家', 'characteristics': '机智、好奇、创新', 'suitable_careers': ['创业者', '律师', '投资人', '发明家']},
    'ESTJ': {'name': '总经理', 'characteristics': '果断、组织、务实', 'suitable_careers': ['管理者', '军官', '法官', '财务']},
    'ESFJ': {'name': '执政官', 'characteristics': '热心、合作、忠诚', 'suitable_careers': ['教师', '护士', '人力', '客服']},
    'ENFJ': {'name': '主人公', 'characteristics': '有魅力、有感染力', 'suitable_careers': ['教师', '心理咨询师', '管理者', '外交官']},
    'ENTJ': {'name': '指挥官', 'characteristics': '果断、领导力强', 'suitable_careers': ['CEO', '律师', '投资人', '政治家']}
}

# 职业价值观
CAREER_VALUES = {
    'achievement': {'name': '成就', 'description': '追求挑战和成果，看重能力发挥与贡献'},
    'autonomy': {'name': '自主', 'description': '重视工作独立性，自由安排工作方式'},
    'security': {'name': '保障', 'description': '看重稳定收入、福利与职业安全'},
    'relationships': {'name': '关系', 'description': '重视同事关系、团队氛围与协作'},
    'success': {'name': '成功', 'description': '追求地位、认可、晋升机会与社会影响力'},
    'creativity': {'name': '创造', 'description': '追求创新、表达个性、做创造性工作'},
    'work_life_balance': {'name': '工作生活平衡', 'description': '重视工作与生活平衡，关注家庭与个人时间'}
}

# 升学路径
EDUCATION_PATHS = {
    'middle_to_high': {'name': '中考升学', 'target': '普通高中/职业高中'},
    'high_to_college': {'name': '高考升学', 'target': '本科/专科院校'},
    'vocational_to_college': {'name': '职校升学', 'target': '应用型本科/高职院校'},
    'adult_to_college': {'name': '成人升学', 'target': '成人本科/网络教育/自学考试'},
    'master_postgrad': {'name': '考研升学', 'target': '硕士研究生/博士研究生'},
    'abroad': {'name': '出国留学', 'target': '海外本科/研究生'}
}

# 新高考选科组合
SUBJECT_COMBINATIONS = {
    'physics_chem_bio': {'name': '物化生', 'subjects': ['物理', '化学', '生物'], 'suitable_majors': ['医学', '工科', '理科']},
    'physics_chem_geo': {'name': '物化地', 'subjects': ['物理', '化学', '地理'], 'suitable_majors': ['工科', '地质', '环境']},
    'physics_chem_pol': {'name': '物化政', 'subjects': ['物理', '化学', '政治'], 'suitable_majors': ['工科', '法学', '公安']},
    'physics_bio_geo': {'name': '物生地', 'subjects': ['物理', '生物', '地理'], 'suitable_majors': ['工科', '农学', '地理']},
    'history_pol_geo': {'name': '史政地', 'subjects': ['历史', '政治', '地理'], 'suitable_majors': ['文科', '法学', '教育']},
    'history_pol_bio': {'name': '史政生', 'subjects': ['历史', '政治', '生物'], 'suitable_majors': ['文科', '医学', '教育']},
    'history_geo_bio': {'name': '史地生', 'subjects': ['历史', '地理', '生物'], 'suitable_majors': ['文科', '农学', '环境']},
    'history_pol_chem': {'name': '史政化', 'subjects': ['历史', '政治', '化学'], 'suitable_majors': ['文科', '医学', '法学']}
}

# 职业大类
CAREER_CATEGORIES = {
    'tech': {'name': '技术', 'sub_categories': ['软件', '硬件', '人工智能', '网络安全']},
    'medical': {'name': '医疗', 'sub_categories': ['临床', '护理', '药学', '公共卫生']},
    'education': {'name': '教育', 'sub_categories': ['基础教育', '高等教育', '职业教育', '特殊教育']},
    'finance': {'name': '金融', 'sub_categories': ['银行', '证券', '保险', '投资']},
    'culture': {'name': '文化', 'sub_categories': ['传媒', '出版', '艺术', '体育']},
    'service': {'name': '服务', 'sub_categories': ['餐饮', '旅游', '酒店', '物流']},
    'manufacturing': {'name': '制造', 'sub_categories': ['机械', '汽车', '电子', '能源']},
    'agriculture': {'name': '农业', 'sub_categories': ['种植', '养殖', '农产品加工', '林业']},
    'government': {'name': '公共', 'sub_categories': ['公务员', '国防', '司法', '社会组织']},
    'research': {'name': '科研', 'sub_categories': ['自然科学', '工程技术', '社会科学', '人文研究']}
}

# 咨询类型
COUNSELING_TYPES = {
    'individual': {'name': '一对一咨询', 'duration': 60},
    'group': {'name': '团体辅导', 'duration': 90},
    'workshop': {'name': '工作坊', 'duration': 120},
    'parent': {'name': '家长咨询', 'duration': 45},
    'crisis': {'name': '紧急咨询', 'duration': 30}
}


class CareerPlanningService:
    """学生生涯规划服务"""

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
                    CREATE TABLE IF NOT EXISTS career_profiles (
                        profile_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        grade_level TEXT,
                        interests TEXT,
                        strengths TEXT,
                        weaknesses TEXT,
                        values TEXT,
                        holland_code TEXT,
                        mbti_type TEXT,
                        career_goal TEXT,
                        target_major TEXT,
                        target_school TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        inventory_type TEXT NOT NULL,
                        status TEXT DEFAULT 'in_progress',
                        questions_answered INTEGER DEFAULT 0,
                        total_questions INTEGER DEFAULT 0,
                        answers TEXT,
                        result_code TEXT,
                        result_summary TEXT,
                        result_details TEXT,
                        score REAL,
                        started_at TEXT,
                        completed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_explorations (
                        exploration_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        career_category TEXT,
                        career_name TEXT,
                        exploration_type TEXT,
                        description TEXT,
                        duration_hours REAL,
                        outcome TEXT,
                        rating INTEGER,
                        reflection TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_info_library (
                        career_id TEXT PRIMARY KEY,
                        career_name TEXT NOT NULL,
                        career_category TEXT,
                        description TEXT,
                        required_education TEXT,
                        required_skills TEXT,
                        salary_range TEXT,
                        employment_outlook TEXT,
                        work_environment TEXT,
                        related_majors TEXT,
                        growth_path TEXT,
                        view_count INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_plans (
                        plan_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        current_stage TEXT,
                        target_stage TEXT,
                        target_school TEXT,
                        target_major TEXT,
                        application_year TEXT,
                        requirements TEXT,
                        progress INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'planning',
                        notes TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS subject_selections (
                        selection_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        grade_level TEXT,
                        combination TEXT,
                        subjects TEXT,
                        selected_at TEXT,
                        advisor_id INTEGER,
                        advisor_name TEXT,
                        advice TEXT,
                        rationale TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_type TEXT,
                        description TEXT,
                        target_audience TEXT,
                        instructor TEXT,
                        duration_hours REAL,
                        schedule TEXT,
                        location TEXT,
                        max_participants INTEGER DEFAULT 50,
                        enrolled_count INTEGER DEFAULT 0,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        register_time TEXT,
                        attendance_status TEXT DEFAULT 'registered',
                        completion INTEGER DEFAULT 0,
                        created_at TEXT,
                        UNIQUE(course_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS counseling_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        counselor_id INTEGER,
                        counselor_name TEXT,
                        counseling_type TEXT,
                        topic TEXT,
                        content TEXT,
                        suggestions TEXT,
                        next_steps TEXT,
                        session_date TEXT,
                        duration INTEGER,
                        status TEXT DEFAULT 'booked',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_milestones (
                        milestone_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        milestone_name TEXT NOT NULL,
                        milestone_type TEXT,
                        target_date TEXT,
                        achieved_date TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_goal_tracking (
                        goal_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        goal_name TEXT NOT NULL,
                        goal_type TEXT,
                        description TEXT,
                        target_date TEXT,
                        progress INTEGER DEFAULT 0,
                        milestones TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS career_events (
                        event_id TEXT PRIMARY KEY,
                        event_name TEXT NOT NULL,
                        event_type TEXT,
                        description TEXT,
                        organizer TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        location TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        target_audience TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('学生生涯规划服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 生涯档案 ==========

    def create_profile(self, user_id: int, user_name: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            profile_id = f"cp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT profile_id FROM career_profiles WHERE user_id = ?', (user_id,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该用户生涯档案已存在'}
                    cursor.execute('''
                        INSERT INTO career_profiles (
                            profile_id, user_id, user_name, education_type,
                            grade_level, interests, strengths, weaknesses,
                            values, holland_code, mbti_type, career_goal,
                            target_major, target_school, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (profile_id, user_id, user_name,
                          kwargs.get('education_type'),
                          kwargs.get('grade_level'),
                          json.dumps(kwargs.get('interests', []), ensure_ascii=False),
                          json.dumps(kwargs.get('strengths', []), ensure_ascii=False),
                          json.dumps(kwargs.get('weaknesses', []), ensure_ascii=False),
                          json.dumps(kwargs.get('values', []), ensure_ascii=False),
                          kwargs.get('holland_code'),
                          kwargs.get('mbti_type'),
                          kwargs.get('career_goal'),
                          kwargs.get('target_major'),
                          kwargs.get('target_school'), now, now))
                    conn.commit()
                    logger.info(f'创建生涯档案: {user_name} ({profile_id})')
                    return {'success': True, 'profile_id': profile_id}
        except Exception as e:
            logger.error(f'创建生涯档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_profile(self, user_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM career_profiles WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '生涯档案不存在'}
                profile = dict(row)
                for key in ['interests', 'strengths', 'weaknesses', 'values']:
                    if profile.get(key):
                        try:
                            profile[key] = json.loads(profile[key])
                        except (ValueError, TypeError):
                            pass
                return {'success': True, 'profile': profile}
        except Exception as e:
            logger.error(f'获取生涯档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_profile(self, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            json_fields = ['interests', 'strengths', 'weaknesses', 'values']
            direct_fields = ['education_type', 'grade_level', 'holland_code',
                             'mbti_type', 'career_goal', 'target_major',
                             'target_school', 'user_name']
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    sets = []
                    params = []
                    for field in direct_fields:
                        if field in kwargs:
                            sets.append(f'{field} = ?')
                            params.append(kwargs[field])
                    for field in json_fields:
                        if field in kwargs:
                            sets.append(f'{field} = ?')
                            params.append(json.dumps(kwargs[field], ensure_ascii=False))
                    if not sets:
                        return {'success': False, 'error': '没有可更新的字段'}
                    sets.append('updated_at = ?')
                    params.append(now)
                    params.append(user_id)
                    cursor.execute(f'UPDATE career_profiles SET {", ".join(sets)} WHERE user_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '生涯档案不存在'}
        except Exception as e:
            logger.error(f'更新生涯档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 职业测评 ==========

    def start_assessment(self, user_id: int, inventory_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            if inventory_type not in INTEREST_INVENTORIES:
                return {'success': False, 'error': '不支持的测评类型'}
            assessment_id = f"ca_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INTEREST_INVENTORIES[inventory_type]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_assessments (
                            assessment_id, user_id, user_name, inventory_type,
                            status, questions_answered, total_questions,
                            answers, started_at, created_at
                        ) VALUES (?, ?, ?, ?, 'in_progress', 0, ?, '[]', ?, ?)
                    ''', (assessment_id, user_id, kwargs.get('user_name'),
                          inventory_type, config['questions'], now, now))
                    conn.commit()
                    logger.info(f'开始测评: {config["name"]} ({assessment_id})')
                    return {
                        'success': True,
                        'assessment_id': assessment_id,
                        'inventory_name': config['name'],
                        'total_questions': config['questions'],
                        'duration_minutes': config['duration_minutes']
                    }
        except Exception as e:
            logger.error(f'开始测评失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_assessment(self, assessment_id: str,
                          answers: List[Any]) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT inventory_type, status, total_questions FROM career_assessments WHERE assessment_id = ?',
                                 (assessment_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '测评记录不存在'}
                    if row['status'] == 'completed':
                        return {'success': False, 'error': '测评已完成'}
                    inventory_type = row['inventory_type']
                    result = self._calculate_assessment(inventory_type, answers)
                    cursor.execute('''
                        UPDATE career_assessments SET
                            status = 'completed', questions_answered = ?,
                            answers = ?, result_code = ?, result_summary = ?,
                            result_details = ?, score = ?, completed_at = ?
                        WHERE assessment_id = ?
                    ''', (len(answers), json.dumps(answers, ensure_ascii=False),
                          result['result_code'], result['result_summary'],
                          json.dumps(result['result_details'], ensure_ascii=False),
                          result.get('score'), now, assessment_id))
                    conn.commit()
                    logger.info(f'提交测评完成: {assessment_id} -> {result["result_code"]}')
                    return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f'提交测评失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_assessment(self, inventory_type: str,
                              answers: List[Any]) -> Dict[str, Any]:
        """计算测评结果，霍兰德生成holland_code，MBTI生成类型"""
        result = {'result_code': '', 'result_summary': '', 'result_details': {}, 'score': None}
        if inventory_type == 'holland':
            scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
            for ans in answers:
                if isinstance(ans, dict):
                    dim = ans.get('dimension')
                    val = ans.get('value', 1)
                    if dim in scores:
                        scores[dim] += val
            sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top3 = [d[0] for d in sorted_dims[:3]]
            holland_code = ''.join(top3)
            details = {
                'dimension_scores': scores,
                'holland_code': holland_code,
                'type_info': {d: HOLLAND_TYPES.get(d, {}) for d in top3}
            }
            result['result_code'] = holland_code
            result['result_summary'] = f'霍兰德职业兴趣代码: {holland_code}'
            result['result_details'] = details
            result['score'] = sum(scores.values())
        elif inventory_type == 'mbti':
            dims = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
            for ans in answers:
                if isinstance(ans, dict):
                    dim = ans.get('dimension')
                    val = ans.get('value', 1)
                    if dim in dims:
                        dims[dim] += val
            type_code = ('E' if dims['E'] >= dims['I'] else 'I') + \
                        ('S' if dims['S'] >= dims['N'] else 'N') + \
                        ('T' if dims['T'] >= dims['F'] else 'F') + \
                        ('J' if dims['J'] >= dims['P'] else 'P')
            type_info = MBTI_TYPES.get(type_code, {})
            details = {
                'dimension_scores': dims,
                'mbti_type': type_code,
                'type_info': type_info
            }
            result['result_code'] = type_code
            result['result_summary'] = f'MBTI性格类型: {type_code} ({type_info.get("name", "")})'
            result['result_details'] = details
        elif inventory_type == 'career_values':
            value_scores = {k: 0 for k in CAREER_VALUES.keys()}
            for ans in answers:
                if isinstance(ans, dict):
                    val_key = ans.get('dimension')
                    val = ans.get('value', 1)
                    if val_key in value_scores:
                        value_scores[val_key] += val
            sorted_values = sorted(value_scores.items(), key=lambda x: x[1], reverse=True)
            top_values = sorted_values[:3]
            result['result_code'] = ','.join([v[0] for v in top_values])
            result['result_summary'] = '核心职业价值观: ' + '、'.join(
                [CAREER_VALUES.get(v[0], {}).get('name', v[0]) for v in top_values])
            result['result_details'] = {'value_scores': value_scores, 'top_values': top_values}
            result['score'] = sum(value_scores.values())
        else:
            total = len(answers)
            correct = sum(1 for a in answers if isinstance(a, dict) and a.get('correct'))
            score = round(correct / total * 100, 1) if total else 0
            result['result_code'] = 'completed'
            result['result_summary'] = f'{INTEREST_INVENTORIES.get(inventory_type, {}).get("name", "")}完成'
            result['result_details'] = {'total': total, 'correct': correct, 'wrong': total - correct}
            result['score'] = score
        return result

    def get_assessment(self, assessment_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM career_assessments WHERE assessment_id = ?', (assessment_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '测评记录不存在'}
                assessment = dict(row)
                for key in ['answers', 'result_details']:
                    if assessment.get(key):
                        try:
                            assessment[key] = json.loads(assessment[key])
                        except (ValueError, TypeError):
                            pass
                return {'success': True, 'assessment': assessment}
        except Exception as e:
            logger.error(f'获取测评结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_assessments(self, user_id: int, page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM career_assessments WHERE user_id = ?'
                params = [user_id]
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取测评列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 职业探索 ==========

    def add_career_to_library(self, career_name: str, career_category: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            career_id = f"ci_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_info_library (
                            career_id, career_name, career_category, description,
                            required_education, required_skills, salary_range,
                            employment_outlook, work_environment, related_majors,
                            growth_path, view_count, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
                    ''', (career_id, career_name, career_category,
                          kwargs.get('description'),
                          kwargs.get('required_education'),
                          json.dumps(kwargs.get('required_skills', []), ensure_ascii=False),
                          kwargs.get('salary_range'),
                          kwargs.get('employment_outlook'),
                          kwargs.get('work_environment'),
                          json.dumps(kwargs.get('related_majors', []), ensure_ascii=False),
                          kwargs.get('growth_path'), now, now))
                    conn.commit()
                    logger.info(f'添加职业信息: {career_name} ({career_id})')
                    return {'success': True, 'career_id': career_id}
        except Exception as e:
            logger.error(f'添加职业信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_careers(self, keyword: str = None, category: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM career_info_library WHERE is_active = 1'
                params = []
                if keyword:
                    query += ' AND (career_name LIKE ? OR description LIKE ?)'
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                if category:
                    query += ' AND career_category = ?'
                    params.append(category)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY view_count DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                for item in items:
                    for key in ['required_skills', 'related_majors']:
                        if item.get(key):
                            try:
                                item[key] = json.loads(item[key])
                            except (ValueError, TypeError):
                                pass
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索职业失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_exploration(self, user_id: int, career_name: str,
                           exploration_type: str, **kwargs) -> Dict[str, Any]:
        try:
            valid_types = ['shadow', 'interview', 'research', 'practice']
            if exploration_type not in valid_types:
                return {'success': False, 'error': f'无效的探索类型，可选: {valid_types}'}
            exploration_id = f"ce_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_explorations (
                            exploration_id, user_id, career_category, career_name,
                            exploration_type, description, duration_hours, outcome,
                            rating, reflection, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (exploration_id, user_id,
                          kwargs.get('career_category'), career_name,
                          exploration_type, kwargs.get('description'),
                          kwargs.get('duration_hours'), kwargs.get('outcome'),
                          kwargs.get('rating'), kwargs.get('reflection'), now))
                    conn.commit()
                    logger.info(f'记录职业探索: {career_name} ({exploration_id})')
                    return {'success': True, 'exploration_id': exploration_id}
        except Exception as e:
            logger.error(f'记录职业探索失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_explorations(self, user_id: int, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM career_explorations WHERE user_id = ?'
                params = [user_id]
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取探索记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 升学规划与选科 ==========

    def create_education_plan(self, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"ep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_plans (
                            plan_id, user_id, user_name, education_type,
                            current_stage, target_stage, target_school,
                            target_major, application_year, requirements,
                            progress, status, notes, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'planning', ?, ?, ?)
                    ''', (plan_id, user_id, kwargs.get('user_name'),
                          kwargs.get('education_type'),
                          kwargs.get('current_stage'),
                          kwargs.get('target_stage'),
                          kwargs.get('target_school'),
                          kwargs.get('target_major'),
                          kwargs.get('application_year'),
                          json.dumps(kwargs.get('requirements', []), ensure_ascii=False),
                          kwargs.get('notes'), now, now))
                    conn.commit()
                    logger.info(f'创建升学规划: {plan_id}')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建升学规划失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_education_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            direct_fields = ['user_name', 'education_type', 'current_stage',
                             'target_stage', 'target_school', 'target_major',
                             'application_year', 'progress', 'status', 'notes']
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    sets = []
                    params = []
                    for field in direct_fields:
                        if field in kwargs:
                            sets.append(f'{field} = ?')
                            params.append(kwargs[field])
                    if 'requirements' in kwargs:
                        sets.append('requirements = ?')
                        params.append(json.dumps(kwargs['requirements'], ensure_ascii=False))
                    if not sets:
                        return {'success': False, 'error': '没有可更新的字段'}
                    sets.append('updated_at = ?')
                    params.append(now)
                    params.append(plan_id)
                    cursor.execute(f'UPDATE education_plans SET {", ".join(sets)} WHERE plan_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '升学规划不存在'}
        except Exception as e:
            logger.error(f'更新升学规划失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_subject_selection(self, user_id: int, combination: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            selection_id = f"ss_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SUBJECT_COMBINATIONS.get(combination, {})
            subjects = kwargs.get('subjects') or config.get('subjects', [])
            education_type = kwargs.get('education_type', 'k12')
            # 成人记录专业选择，组合字段记录专业方向
            if education_type == 'adult':
                subjects = kwargs.get('subjects', [])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO subject_selections (
                            selection_id, user_id, user_name, grade_level,
                            combination, subjects, selected_at, advisor_id,
                            advisor_name, advice, rationale, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (selection_id, user_id, kwargs.get('user_name'),
                          kwargs.get('grade_level'), combination,
                          json.dumps(subjects, ensure_ascii=False),
                          kwargs.get('selected_at', now[:10]),
                          kwargs.get('advisor_id'), kwargs.get('advisor_name'),
                          kwargs.get('advice'), kwargs.get('rationale'), now))
                    conn.commit()
                    logger.info(f'记录选科: {combination} ({selection_id})')
                    return {'success': True, 'selection_id': selection_id}
        except Exception as e:
            logger.error(f'记录选科失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_education_plans(self, user_id: int = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_plans WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(p) for p in cursor.fetchall()]
                for item in items:
                    if item.get('requirements'):
                        try:
                            item['requirements'] = json.loads(item['requirements'])
                        except (ValueError, TypeError):
                            pass
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取升学规划列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 生涯课程与活动 ==========

    def create_career_course(self, course_name: str, course_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            valid_types = ['course', 'lecture', 'activity']
            if course_type not in valid_types:
                return {'success': False, 'error': f'无效课程类型，可选: {valid_types}'}
            course_id = f"cc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_courses (
                            course_id, course_name, course_type, description,
                            target_audience, instructor, duration_hours, schedule,
                            location, max_participants, enrolled_count,
                            education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                    ''', (course_id, course_name, course_type,
                          kwargs.get('description'),
                          kwargs.get('target_audience'),
                          kwargs.get('instructor'),
                          kwargs.get('duration_hours'),
                          kwargs.get('schedule'), kwargs.get('location'),
                          kwargs.get('max_participants', 50),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建生涯课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建生涯课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_career_course(self, course_id: str, user_id: int,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count FROM career_courses WHERE course_id = ?',
                                 (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO course_registrations
                            (course_id, user_id, user_name, register_time, attendance_status, completion, created_at)
                        VALUES (?, ?, ?, ?, 'registered', 0, ?)
                    ''', (course_id, user_id, kwargs.get('user_name'), now, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE career_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?',
                                     (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该课程'}
        except Exception as e:
            logger.error(f'课程报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_career_event(self, event_name: str, event_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            valid_types = ['career_fair', 'university_visit', 'industry_visit',
                           'expert_talk', 'skills_competition']
            if event_type not in valid_types:
                return {'success': False, 'error': f'无效活动类型，可选: {valid_types}'}
            event_id = f"cev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_events (
                            event_id, event_name, event_type, description,
                            organizer, start_date, end_date, location,
                            max_participants, registered_count, target_audience,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                    ''', (event_id, event_name, event_type,
                          kwargs.get('description'),
                          kwargs.get('organizer'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('location'),
                          kwargs.get('max_participants', 100),
                          kwargs.get('target_audience'), now, now))
                    conn.commit()
                    logger.info(f'创建生涯活动: {event_name} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'创建生涯活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_career_event(self, event_id: str, user_id: int,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count FROM career_events WHERE event_id = ?',
                                 (event_id,))
                    event = cursor.fetchone()
                    if not event:
                        return {'success': False, 'error': '活动不存在'}
                    if event[0] and event[1] >= event[0]:
                        return {'success': False, 'error': '活动名额已满'}
                    cursor.execute('UPDATE career_events SET registered_count = registered_count + 1, updated_at = ? WHERE event_id = ?',
                                 (now, event_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_career_events(self, page: int = 1, page_size: int = 20,
                           **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM career_events WHERE 1=1'
                params = []
                if filters.get('event_type'):
                    query += ' AND event_type = ?'
                    params.append(filters['event_type'])
                if filters.get('target_audience'):
                    query += ' AND target_audience = ?'
                    params.append(filters['target_audience'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_date DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 咨询辅导 ==========

    def book_counseling(self, user_id: int, counselor_id: int,
                        counseling_type: str, **kwargs) -> Dict[str, Any]:
        try:
            if counseling_type not in COUNSELING_TYPES:
                return {'success': False, 'error': '不支持的咨询类型'}
            session_id = f"cs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COUNSELING_TYPES[counseling_type]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO counseling_sessions (
                            session_id, user_id, user_name, counselor_id,
                            counselor_name, counseling_type, topic, session_date,
                            duration, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'booked', ?)
                    ''', (session_id, user_id, kwargs.get('user_name'),
                          counselor_id, kwargs.get('counselor_name'),
                          counseling_type, kwargs.get('topic'),
                          kwargs.get('session_date', now[:10]),
                          config['duration'], now))
                    conn.commit()
                    logger.info(f'预约咨询: {session_id}')
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'预约咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_counseling(self, session_id: str, content: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE counseling_sessions SET
                            content = ?, suggestions = ?, next_steps = ?,
                            status = 'completed'
                        WHERE session_id = ? AND status = 'booked'
                    ''', (content, kwargs.get('suggestions'),
                          kwargs.get('next_steps'), session_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '咨询记录不存在或状态不允许更新'}
        except Exception as e:
            logger.error(f'记录咨询内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_counseling(self, user_id: int = None, page: int = 1,
                        page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM counseling_sessions WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY session_date DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取咨询列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 目标与里程碑 ==========

    def create_goal(self, user_id: int, goal_name: str, goal_type: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            valid_types = ['short_term', 'mid_term', 'long_term']
            if goal_type not in valid_types:
                return {'success': False, 'error': f'无效目标类型，可选: {valid_types}'}
            goal_id = f"cg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_goal_tracking (
                            goal_id, user_id, goal_name, goal_type, description,
                            target_date, progress, milestones, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, '[]', 'active', ?, ?)
                    ''', (goal_id, user_id, goal_name, goal_type,
                          kwargs.get('description'),
                          kwargs.get('target_date'), now, now))
                    conn.commit()
                    logger.info(f'创建生涯目标: {goal_name} ({goal_id})')
                    return {'success': True, 'goal_id': goal_id}
        except Exception as e:
            logger.error(f'创建生涯目标失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_goal_progress(self, goal_id: str, progress: int,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            progress = max(0, min(100, int(progress)))
            status = kwargs.get('status', ('completed' if progress >= 100 else 'active'))
            milestones = kwargs.get('milestones')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if milestones is not None:
                        cursor.execute('''
                            UPDATE career_goal_tracking SET
                                progress = ?, status = ?, milestones = ?, updated_at = ?
                            WHERE goal_id = ?
                        ''', (progress, status,
                              json.dumps(milestones, ensure_ascii=False),
                              now, goal_id))
                    else:
                        cursor.execute('''
                            UPDATE career_goal_tracking SET
                                progress = ?, status = ?, updated_at = ?
                            WHERE goal_id = ?
                        ''', (progress, status, now, goal_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress, 'status': status}
                    return {'success': False, 'error': '目标不存在'}
        except Exception as e:
            logger.error(f'更新目标进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_milestone(self, user_id: int, milestone_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            valid_types = ['assessment', 'exploration', 'selection',
                           'application', 'decision']
            milestone_type = kwargs.get('milestone_type')
            if milestone_type and milestone_type not in valid_types:
                return {'success': False, 'error': f'无效里程碑类型，可选: {valid_types}'}
            milestone_id = f"cm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO career_milestones (
                            milestone_id, user_id, milestone_name, milestone_type,
                            target_date, achieved_date, status, description,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, NULL, 'pending', ?, ?, ?)
                    ''', (milestone_id, user_id, milestone_name, milestone_type,
                          kwargs.get('target_date'), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建里程碑: {milestone_name} ({milestone_id})')
                    return {'success': True, 'milestone_id': milestone_id}
        except Exception as e:
            logger.error(f'创建里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_milestone(self, milestone_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            achieved_date = kwargs.get('achieved_date', now[:10])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE career_milestones SET
                            status = 'achieved', achieved_date = ?, updated_at = ?
                        WHERE milestone_id = ? AND status = 'pending'
                    ''', (achieved_date, now, milestone_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'achieved_date': achieved_date}
                    return {'success': False, 'error': '里程碑不存在或已完成'}
        except Exception as e:
            logger.error(f'完成里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                edu_cond = ''
                params = []
                if education_type:
                    edu_cond = ' AND education_type = ?'
                    params = [education_type]
                stats = {'education_type': education_type}

                cursor.execute(f'SELECT COUNT(*) FROM career_profiles WHERE 1=1{edu_cond}', params)
                stats['profile_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM career_assessments WHERE status = ?', ('completed',))
                stats['completed_assessments'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM career_assessments WHERE status = ?', ('in_progress',))
                stats['in_progress_assessments'] = cursor.fetchone()[0]

                cursor.execute('SELECT inventory_type, COUNT(*) FROM career_assessments WHERE status = ? GROUP BY inventory_type', ('completed',))
                stats['assessment_by_type'] = {r[0]: r[1] for r in cursor.fetchall()}

                cursor.execute('SELECT holland_code, COUNT(*) FROM career_profiles WHERE holland_code IS NOT NULL AND holland_code != "" GROUP BY holland_code')
                stats['holland_distribution'] = {r[0]: r[1] for r in cursor.fetchall()}

                cursor.execute('SELECT mbti_type, COUNT(*) FROM career_profiles WHERE mbti_type IS NOT NULL AND mbti_type != "" GROUP BY mbti_type')
                stats['mbti_distribution'] = {r[0]: r[1] for r in cursor.fetchall()}

                cursor.execute(f'SELECT status, COUNT(*) FROM education_plans WHERE 1=1{edu_cond}', params)
                stats['plan_status'] = {r[0]: r[1] for r in cursor.fetchall()}

                cursor.execute('SELECT combination, COUNT(*) FROM subject_selections GROUP BY combination')
                stats['subject_selection_distribution'] = {r[0]: r[1] for r in cursor.fetchall()}

                cursor.execute('SELECT COUNT(*) FROM counseling_sessions')
                stats['counseling_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT status, COUNT(*) FROM counseling_sessions GROUP BY status')
                stats['counseling_status'] = {r[0]: r[1] for r in cursor.fetchall()}

                cursor.execute('SELECT COUNT(*) FROM career_events')
                stats['event_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COALESCE(SUM(registered_count), 0) FROM career_events')
                stats['event_total_participants'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM career_courses')
                stats['course_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COALESCE(SUM(enrolled_count), 0) FROM career_courses')
                stats['course_total_enrolled'] = cursor.fetchone()[0]

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = CareerPlanningService()
    print('学生生涯规划服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
