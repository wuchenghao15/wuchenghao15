#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育太空探索服务 (v15.19.0)
====================================
提供太空科学、天文观测、航天工程、卫星技术、太空实验、深空探测、太空教育、太空创新等综合管理服务。

核心能力：
1. 太空科学 - 天文学/天体物理/行星科学/宇宙学/空间物理/地球科学/航天医学/生命科学
2. 天文观测 - 望远镜/射电望远镜/空间望远镜/光谱仪/探测器/卫星遥感
3. 航天工程 - 火箭技术/航天器设计/轨道力学/推进系统/导航控制/热防护
4. 卫星技术 - 通信卫星/遥感卫星/导航卫星/科学卫星/微卫星/纳米卫星
5. 太空实验 - 微重力实验/生命科学实验/材料科学实验/物理实验/天文观测/地球观测
6. 深空探测 - 月球探测/火星探测/小行星探测/彗星探测/木星探测/土星探测
7. 太空教育 - 天文课程/航天课程/太空夏令营/模拟飞行/太空竞赛/科普活动
8. 太空创新 - 太空旅游/商业航天/太空资源开发/太空采矿/太空工厂/太空农业
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_space_exploration_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SpaceExploration')


# ========== 太空配置 ==========

SPACE_SCIENCES = {
    'astronomy': {'name': '天文学', 'sub': ['恒星天文学', '星系天文学', '银河系', '河外星系', '宇宙学']},
    'astrophysics': {'name': '天体物理学', 'sub': ['天体力学', '天体光谱学', '高能天体物理', '等离子体物理']},
    'planetary_science': {'name': '行星科学', 'sub': ['行星形成', '行星大气', '行星地质', '行星探测']},
    'cosmology': {'name': '宇宙学', 'sub': ['宇宙起源', '宇宙演化', '暗物质', '暗能量']},
    'space_physics': {'name': '空间物理学', 'sub': ['太阳物理', '磁层物理', '电离层', '空间天气']},
    'earth_science': {'name': '地球科学', 'sub': ['地球系统', '气候变化', '遥感监测', '地球建模']},
    'space_medicine': {'name': '航天医学', 'sub': ['人体生理', '太空适应', '健康监测', '医疗保障']},
    'life_science': {'name': '生命科学', 'sub': ['太空生物学', '微重力生命', '生命起源', '宇航生态']}
}

OBSERVATION_TOOLS = {
    'telescope': {'name': '光学望远镜', 'sub': ['折射式', '反射式', '折反射式']},
    'radio_telescope': {'name': '射电望远镜', 'sub': ['单口径', '综合孔径', '甚长基线']},
    'space_telescope': {'name': '空间望远镜', 'sub': ['哈勃', '韦伯', '钱德拉', '斯皮策']},
    'spectrometer': {'name': '光谱仪', 'sub': ['光学光谱', '红外光谱', '紫外光谱', 'X射线光谱']},
    'detector': {'name': '探测器', 'sub': ['CCD', 'CMOS', '光子计数', '成像仪']},
    'satellite_remote_sensing': {'name': '卫星遥感', 'sub': ['可见光', '红外', '微波', '雷达']}
}

AEROSPACE_ENGINEERING = {
    'rocket_tech': {'name': '火箭技术', 'sub': ['液体火箭', '固体火箭', '混合动力', '可重复使用']},
    'spacecraft_design': {'name': '航天器设计', 'sub': ['载人飞船', '货运飞船', '空间站', '深空探测器']},
    'orbital_mechanics': {'name': '轨道力学', 'sub': ['开普勒轨道', '轨道转移', '轨道保持', '轨道机动']},
    'propulsion': {'name': '推进系统', 'sub': ['化学推进', '电推进', '核推进', '太阳帆']},
    'navigation': {'name': '导航控制', 'sub': ['惯性导航', '星光导航', 'GPS', '自主导航']},
    'thermal_protection': {'name': '热防护', 'sub': ['隔热瓦', '烧蚀材料', '主动冷却', '热控系统']}
}

SATELLITE_TECHNOLOGY = {
    'communication_satellite': {'name': '通信卫星', 'sub': ['GEO', 'MEO', 'LEO', '中继卫星']},
    'remote_sensing_satellite': {'name': '遥感卫星', 'sub': ['资源卫星', '气象卫星', '海洋卫星', '环境卫星']},
    'navigation_satellite': {'name': '导航卫星', 'sub': ['GPS', '北斗', 'GLONASS', 'Galileo']},
    'science_satellite': {'name': '科学卫星', 'sub': ['天文卫星', '地球物理卫星', '空间科学卫星']},
    'microsatellite': {'name': '微卫星', 'sub': ['CubeSat', '纳米卫星', '皮卫星']},
    'nanosatellite': {'name': '纳米卫星', 'sub': ['1U', '2U', '3U', '6U CubeSat']}
}

SPACE_EXPERIMENTS = {
    'microgravity': {'name': '微重力实验', 'sub': ['流体力学', '燃烧科学', '相变研究', '胶体科学']},
    'life_science': {'name': '生命科学实验', 'sub': ['细胞生物学', '植物生长', '动物实验', '人体研究']},
    'materials': {'name': '材料科学实验', 'sub': ['晶体生长', '合金制备', '复合材料', '新型材料']},
    'physics': {'name': '物理实验', 'sub': ['量子物理', '相对论验证', '高能物理', '凝聚态']},
    'astronomical_observation': {'name': '天文观测', 'sub': ['深空观测', '系外行星', '引力波', '黑洞']},
    'earth_observation': {'name': '地球观测', 'sub': ['气候变化', '环境监测', '灾害预警', '资源调查']}
}

DEEP_SPACE = {
    'lunar': {'name': '月球探测', 'sub': ['绕月探测', '落月探测', '月面巡视', '月球基地']},
    'mars': {'name': '火星探测', 'sub': ['轨道探测', '着陆探测', '巡视探测', '样品返回']},
    'asteroid': {'name': '小行星探测', 'sub': ['近地小行星', '主带小行星', '采样返回', '偏转任务']},
    'comet': {'name': '彗星探测', 'sub': ['彗核探测', '彗尾研究', '冰成分分析']},
    'jupiter': {'name': '木星探测', 'sub': ['木星大气', '木星卫星', '木卫二', '大红斑']},
    'saturn': {'name': '土星探测', 'sub': ['土星环', '土卫六', '卡西尼', '泰坦大气']}
}

SPACE_EDUCATION = {
    'astronomy_course': {'name': '天文课程', 'sub': ['基础天文', '星空观测', '天体摄影', '宇宙学']},
    'aerospace_course': {'name': '航天课程', 'sub': ['航天史', '火箭原理', '航天器设计', '空间技术']},
    'space_camp': {'name': '太空夏令营', 'sub': ['模拟训练', '航天体验', '科学实验', '团队合作']},
    'simulation_flight': {'name': '模拟飞行', 'sub': ['飞行模拟器', '空间站模拟', '任务模拟']},
    'space_competition': {'name': '太空竞赛', 'sub': ['火箭竞赛', '卫星设计', '创意比赛']},
    'science_popularization': {'name': '科普活动', 'sub': ['天文讲座', '观测活动', '展览', '工作坊']}
}

SPACE_INNOVATION = {
    'space_tourism': {'name': '太空旅游', 'sub': ['亚轨道旅游', '轨道旅游', '太空酒店']},
    'commercial_space': {'name': '商业航天', 'sub': ['商业发射', '卫星运营', '航天服务']},
    'space_resource': {'name': '太空资源开发', 'sub': ['月球资源', '小行星资源', '太阳能']},
    'space_mining': {'name': '太空采矿', 'sub': ['矿物开采', '水资源提取', '氦-3']},
    'space_factory': {'name': '太空工厂', 'sub': ['微重力制造', '3D打印', '生物医药']},
    'space_agriculture': {'name': '太空农业', 'sub': ['植物栽培', '水培系统', '闭环生态']}
}


class EducationSpaceExplorationService:
    """教育太空探索服务"""

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
                    CREATE TABLE IF NOT EXISTS space_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_type TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        subject TEXT,
                        description TEXT,
                        duration_hours REAL DEFAULT 40,
                        credits INTEGER DEFAULT 3,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_modules (
                        module_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        module_name TEXT NOT NULL,
                        module_order INTEGER DEFAULT 1,
                        duration_hours REAL DEFAULT 4,
                        content TEXT,
                        resources TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS astronomical_observation (
                        observation_id TEXT PRIMARY KEY,
                        target_name TEXT NOT NULL,
                        target_type TEXT,
                        tool_type TEXT,
                        location TEXT,
                        education_type TEXT,
                        max_participants INTEGER DEFAULT 20,
                        registered_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'scheduled',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS observation_records (
                        record_id TEXT PRIMARY KEY,
                        observation_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        observation_date TEXT,
                        data_collected TEXT,
                        notes TEXT,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aerospace_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        project_type TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        description TEXT,
                        objectives TEXT,
                        duration_days INTEGER DEFAULT 30,
                        budget REAL DEFAULT 0,
                        team_size INTEGER DEFAULT 5,
                        status TEXT DEFAULT 'planning',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_details (
                        detail_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        phase_name TEXT NOT NULL,
                        phase_order INTEGER DEFAULT 1,
                        start_date TEXT,
                        end_date TEXT,
                        milestones TEXT,
                        resources TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS satellite_mission (
                        mission_id TEXT PRIMARY KEY,
                        mission_name TEXT NOT NULL,
                        satellite_type TEXT,
                        education_type TEXT,
                        orbit_type TEXT,
                        launch_date TEXT,
                        expected_duration_days INTEGER,
                        objectives TEXT,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mission_data (
                        data_id TEXT PRIMARY KEY,
                        mission_id TEXT NOT NULL,
                        data_type TEXT,
                        data_content TEXT,
                        collection_time TEXT,
                        file_url TEXT,
                        status TEXT DEFAULT 'processed',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS space_experiments (
                        experiment_id TEXT PRIMARY KEY,
                        experiment_name TEXT NOT NULL,
                        experiment_type TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        description TEXT,
                        objectives TEXT,
                        required_equipment TEXT,
                        duration_hours REAL DEFAULT 2,
                        safety_requirements TEXT,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiment_results (
                        result_id TEXT PRIMARY KEY,
                        experiment_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        experiment_date TEXT,
                        data TEXT,
                        observations TEXT,
                        conclusion TEXT,
                        score REAL,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS deep_space_mission (
                        mission_id TEXT PRIMARY KEY,
                        mission_name TEXT NOT NULL,
                        target_body TEXT,
                        mission_type TEXT,
                        education_type TEXT,
                        launch_window TEXT,
                        mission_duration_days INTEGER,
                        objectives TEXT,
                        spacecraft TEXT,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mission_status (
                        status_id TEXT PRIMARY KEY,
                        mission_id TEXT NOT NULL,
                        phase TEXT,
                        status TEXT DEFAULT 'in_progress',
                        progress_percent REAL DEFAULT 0,
                        milestone TEXT,
                        update_time TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS space_education (
                        education_id TEXT PRIMARY KEY,
                        activity_name TEXT NOT NULL,
                        activity_type TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        description TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_participants INTEGER DEFAULT 50,
                        registered_count INTEGER DEFAULT 0,
                        fee REAL DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_events (
                        event_id TEXT PRIMARY KEY,
                        education_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        register_date TEXT,
                        attended INTEGER DEFAULT 0,
                        feedback TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS space_innovation (
                        innovation_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        innovation_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        objectives TEXT,
                        feasibility REAL DEFAULT 0,
                        impact REAL DEFAULT 0,
                        status TEXT DEFAULT 'idea',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_projects (
                        project_id TEXT PRIMARY KEY,
                        innovation_id TEXT NOT NULL,
                        team_name TEXT,
                        team_members TEXT,
                        timeline TEXT,
                        budget REAL DEFAULT 0,
                        resources TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS space_resources (
                        resource_id TEXT PRIMARY KEY,
                        resource_name TEXT NOT NULL,
                        resource_type TEXT,
                        location TEXT,
                        quantity INTEGER DEFAULT 0,
                        unit TEXT,
                        status TEXT DEFAULT 'available',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_management (
                        management_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        transaction_type TEXT,
                        quantity INTEGER,
                        user_id INTEGER,
                        user_name TEXT,
                        transaction_date TEXT,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS space_research (
                        research_id TEXT PRIMARY KEY,
                        research_name TEXT NOT NULL,
                        research_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        objectives TEXT,
                        methodology TEXT,
                        status TEXT DEFAULT 'ongoing',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS research_publications (
                        publication_id TEXT PRIMARY KEY,
                        research_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        authors TEXT,
                        journal TEXT,
                        publication_date TEXT,
                        doi TEXT,
                        abstract TEXT,
                        status TEXT DEFAULT 'published',
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育太空探索服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 太空科学 ==========

    def create_space_course(self, course_name: str, course_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"spc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO space_courses (
                            course_id, course_name, course_type, education_type,
                            grade_level, subject, description, duration_hours,
                            credits, teacher_id, teacher_name, max_students,
                            enrolled_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (course_id, course_name, course_type,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('subject'), kwargs.get('description'),
                          kwargs.get('duration_hours', 40), kwargs.get('credits', 3),
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('max_students', 30), now, now))
                    conn.commit()
                    logger.info(f'创建太空课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建太空课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_space_course(self, course_id: str, student_id: int,
                            student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM space_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO course_modules (module_id, course_id, module_name) VALUES (?, ?, ?)',
                                 (f"mod_{uuid.uuid4().hex[:12]}", course_id, '课程介绍'))
                    cursor.execute('UPDATE space_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'太空课程选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_course_module(self, course_id: str, module_name: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            module_id = f"mod_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM course_modules WHERE course_id = ?', (course_id,))
                    count = cursor.fetchone()[0]
                    cursor.execute('''
                        INSERT INTO course_modules (
                            module_id, course_id, module_name, module_order,
                            duration_hours, content, resources, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (module_id, course_id, module_name, count + 1,
                          kwargs.get('duration_hours', 4), kwargs.get('content'),
                          kwargs.get('resources'), now))
                    conn.commit()
                    return {'success': True, 'module_id': module_id}
        except Exception as e:
            logger.error(f'创建课程模块失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_space_courses(self, education_type: str = None, course_type: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM space_courses WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if course_type:
                    query += ' AND course_type = ?'
                    params.append(course_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                courses = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'courses': courses, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取太空课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 天文观测 ==========

    def create_observation(self, target_name: str, tool_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            observation_id = f"obs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO astronomical_observation (
                            observation_id, target_name, target_type, tool_type,
                            location, education_type, max_participants,
                            registered_count, description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'scheduled', ?, ?)
                    ''', (observation_id, target_name, kwargs.get('target_type'),
                          tool_type, kwargs.get('location'),
                          kwargs.get('education_type'), kwargs.get('max_participants', 20),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建天文观测: {target_name} ({observation_id})')
                    return {'success': True, 'observation_id': observation_id}
        except Exception as e:
            logger.error(f'创建天文观测失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_observation(self, observation_id: str, student_id: int,
                             student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM astronomical_observation WHERE observation_id = ?', (observation_id,))
                    obs = cursor.fetchone()
                    if not obs:
                        return {'success': False, 'error': '观测活动不存在'}
                    if obs[2] != 'scheduled':
                        return {'success': False, 'error': '观测活动状态不允许报名'}
                    if obs[0] and obs[1] >= obs[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO observation_records (record_id, observation_id, student_id, student_name, status) VALUES (?, ?, ?, ?, \'registered\')',
                                 (f"rec_{uuid.uuid4().hex[:12]}", observation_id, student_id, student_name))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE astronomical_observation SET registered_count = registered_count + 1, updated_at = ? WHERE observation_id = ?', (now, observation_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该观测'}
        except Exception as e:
            logger.error(f'观测报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_observation_data(self, record_id: str, data_collected: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE observation_records SET data_collected = ?, notes = ?, observation_date = ?, status = ? WHERE record_id = ?',
                                 (data_collected, kwargs.get('notes'), now[:10], 'completed', record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'记录观测数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_observations(self, education_type: str = None, tool_type: str = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM astronomical_observation WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if tool_type:
                    query += ' AND tool_type = ?'
                    params.append(tool_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                observations = [dict(o) for o in cursor.fetchall()]
                return {'success': True, 'observations': observations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取观测列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 航天工程 ==========

    def create_aerospace_project(self, project_name: str, project_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"asp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO aerospace_projects (
                            project_id, project_name, project_type, education_type,
                            grade_level, description, objectives, duration_days,
                            budget, team_size, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?)
                    ''', (project_id, project_name, project_type,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('description'), kwargs.get('objectives'),
                          kwargs.get('duration_days', 30), kwargs.get('budget', 0),
                          kwargs.get('team_size', 5), now, now))
                    conn.commit()
                    logger.info(f'创建航天工程项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建航天工程项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_project_phase(self, project_id: str, phase_name: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            detail_id = f"pdt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM project_details WHERE project_id = ?', (project_id,))
                    count = cursor.fetchone()[0]
                    cursor.execute('''
                        INSERT INTO project_details (
                            detail_id, project_id, phase_name, phase_order,
                            start_date, end_date, milestones, resources, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (detail_id, project_id, phase_name, count + 1,
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('milestones'), kwargs.get('resources'), now))
                    conn.commit()
                    return {'success': True, 'detail_id': detail_id}
        except Exception as e:
            logger.error(f'添加项目阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_status(self, project_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE aerospace_projects SET status = ?, updated_at = ? WHERE project_id = ?',
                                 (status, now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新项目状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_aerospace_projects(self, education_type: str = None, project_type: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM aerospace_projects WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if project_type:
                    query += ' AND project_type = ?'
                    params.append(project_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                projects = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'projects': projects, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取航天工程项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 卫星技术 ==========

    def create_satellite_mission(self, mission_name: str, satellite_type: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            mission_id = f"stm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO satellite_mission (
                            mission_id, mission_name, satellite_type, education_type,
                            orbit_type, launch_date, expected_duration_days,
                            objectives, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?)
                    ''', (mission_id, mission_name, satellite_type,
                          kwargs.get('education_type'), kwargs.get('orbit_type'),
                          kwargs.get('launch_date'), kwargs.get('expected_duration_days'),
                          kwargs.get('objectives'), now, now))
                    conn.commit()
                    logger.info(f'创建卫星任务: {mission_name} ({mission_id})')
                    return {'success': True, 'mission_id': mission_id}
        except Exception as e:
            logger.error(f'创建卫星任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_mission_data(self, mission_id: str, data_type: str, data_content: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"mdt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO mission_data (
                            data_id, mission_id, data_type, data_content,
                            collection_time, file_url, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'processed', ?)
                    ''', (data_id, mission_id, data_type, data_content,
                          now, kwargs.get('file_url'), now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'添加任务数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_mission_status(self, mission_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE satellite_mission SET status = ?, updated_at = ? WHERE mission_id = ?',
                                 (status, now, mission_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '任务不存在'}
        except Exception as e:
            logger.error(f'更新任务状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_satellite_missions(self, education_type: str = None, satellite_type: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM satellite_mission WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if satellite_type:
                    query += ' AND satellite_type = ?'
                    params.append(satellite_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                missions = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'missions': missions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取卫星任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 太空实验 ==========

    def create_space_experiment(self, experiment_name: str, experiment_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            experiment_id = f"spe_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO space_experiments (
                            experiment_id, experiment_name, experiment_type, education_type,
                            grade_level, description, objectives, required_equipment,
                            duration_hours, safety_requirements, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?)
                    ''', (experiment_id, experiment_name, experiment_type,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('description'), kwargs.get('objectives'),
                          kwargs.get('required_equipment'), kwargs.get('duration_hours', 2),
                          kwargs.get('safety_requirements'), now, now))
                    conn.commit()
                    logger.info(f'创建太空实验: {experiment_name} ({experiment_id})')
                    return {'success': True, 'experiment_id': experiment_id}
        except Exception as e:
            logger.error(f'创建太空实验失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_experiment_result(self, experiment_id: str, student_id: int,
                                  student_name: str, data: str, **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"ser_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO experiment_results (
                            result_id, experiment_id, student_id, student_name,
                            experiment_date, data, observations, conclusion,
                            score, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
                    ''', (result_id, experiment_id, student_id, student_name,
                          now[:10], data, kwargs.get('observations'),
                          kwargs.get('conclusion'), kwargs.get('score'), now))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'记录实验结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_experiment(self, result_id: str, score: float, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE experiment_results SET score = ?, conclusion = ? WHERE result_id = ?',
                                 (score, kwargs.get('conclusion'), result_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '实验结果不存在'}
        except Exception as e:
            logger.error(f'评估实验失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_experiment_results(self, experiment_id: str = None, student_id: int = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM experiment_results WHERE 1=1'
                params = []
                if experiment_id:
                    query += ' AND experiment_id = ?'
                    params.append(experiment_id)
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取实验结果列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_space_experiments(self, education_type: str = None, experiment_type: str = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM space_experiments WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if experiment_type:
                    query += ' AND experiment_type = ?'
                    params.append(experiment_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                experiments = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'experiments': experiments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取太空实验列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 深空探测 ==========

    def create_deep_space_mission(self, mission_name: str, target_body: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            mission_id = f"dsm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO deep_space_mission (
                            mission_id, mission_name, target_body, mission_type,
                            education_type, launch_window, mission_duration_days,
                            objectives, spacecraft, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?)
                    ''', (mission_id, mission_name, target_body, kwargs.get('mission_type'),
                          kwargs.get('education_type'), kwargs.get('launch_window'),
                          kwargs.get('mission_duration_days'), kwargs.get('objectives'),
                          kwargs.get('spacecraft'), now, now))
                    conn.commit()
                    logger.info(f'创建深空探测任务: {mission_name} ({mission_id})')
                    return {'success': True, 'mission_id': mission_id}
        except Exception as e:
            logger.error(f'创建深空探测任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_mission_status(self, mission_id: str, phase: str, status: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            status_id = f"mst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO mission_status (
                            status_id, mission_id, phase, status,
                            progress_percent, milestone, update_time, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (status_id, mission_id, phase, status,
                          kwargs.get('progress_percent', 0), kwargs.get('milestone'),
                          now, now))
                    cursor.execute('UPDATE deep_space_mission SET status = ?, updated_at = ? WHERE mission_id = ?',
                                 (status, now, mission_id))
                    conn.commit()
                    return {'success': True, 'status_id': status_id}
        except Exception as e:
            logger.error(f'更新深空任务状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_mission_status(self, mission_id: str, page: int = 1,
                            page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM mission_status WHERE mission_id = ? ORDER BY update_time DESC'
                cursor.execute('SELECT COUNT(*) as cnt FROM mission_status WHERE mission_id = ?', (mission_id,))
                total = cursor.fetchone()['cnt']
                cursor.execute(query + ' LIMIT ? OFFSET ?', (mission_id, page_size, (page - 1) * page_size))
                status_list = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'status_list': status_list, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取任务状态列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_deep_space_missions(self, education_type: str = None, target_body: str = None,
                                 page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM deep_space_mission WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if target_body:
                    query += ' AND target_body = ?'
                    params.append(target_body)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                missions = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'missions': missions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取深空探测任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 太空教育 ==========

    def create_space_education(self, activity_name: str, activity_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            education_id = f"sed_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO space_education (
                            education_id, activity_name, activity_type, education_type,
                            grade_level, description, location, start_date,
                            end_date, max_participants, registered_count, fee,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'scheduled', ?, ?)
                    ''', (education_id, activity_name, activity_type,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('description'), kwargs.get('location'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('max_participants', 50), kwargs.get('fee', 0),
                          now, now))
                    conn.commit()
                    logger.info(f'创建太空教育活动: {activity_name} ({education_id})')
                    return {'success': True, 'education_id': education_id}
        except Exception as e:
            logger.error(f'创建太空教育活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_education(self, education_id: str, student_id: int,
                           student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM space_education WHERE education_id = ?', (education_id,))
                    edu = cursor.fetchone()
                    if not edu:
                        return {'success': False, 'error': '教育活动不存在'}
                    if edu[2] != 'scheduled':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if edu[0] and edu[1] >= edu[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO education_events (event_id, education_id, student_id, student_name, register_date) VALUES (?, ?, ?, ?, ?)',
                                 (f"eev_{uuid.uuid4().hex[:12]}", education_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE space_education SET registered_count = registered_count + 1, updated_at = ? WHERE education_id = ?', (now, education_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'教育活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_attendance(self, event_id: str, attended: bool = True) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE education_events SET attended = ? WHERE event_id = ?',
                                 (1 if attended else 0, event_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_space_education(self, education_type: str = None, activity_type: str = None,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM space_education WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if activity_type:
                    query += ' AND activity_type = ?'
                    params.append(activity_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                activities = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'activities': activities, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取太空教育活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 太空创新 ==========

    def create_innovation(self, project_name: str, innovation_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            innovation_id = f"sin_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO space_innovation (
                            innovation_id, project_name, innovation_type, education_type,
                            description, objectives, feasibility, impact,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'idea', ?, ?)
                    ''', (innovation_id, project_name, innovation_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('objectives'), kwargs.get('feasibility', 0),
                          kwargs.get('impact', 0), now, now))
                    conn.commit()
                    logger.info(f'创建太空创新项目: {project_name} ({innovation_id})')
                    return {'success': True, 'innovation_id': innovation_id}
        except Exception as e:
            logger.error(f'创建太空创新项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def develop_innovation(self, innovation_id: str, team_name: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"inp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_projects (
                            project_id, innovation_id, team_name, team_members,
                            timeline, budget, resources, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (project_id, innovation_id, team_name,
                          kwargs.get('team_members'), kwargs.get('timeline'),
                          kwargs.get('budget', 0), kwargs.get('resources'), now))
                    cursor.execute('UPDATE space_innovation SET status = ?, updated_at = ? WHERE innovation_id = ?',
                                 ('development', now, innovation_id))
                    conn.commit()
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'开发创新项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_innovation(self, innovation_id: str, feasibility: float,
                            impact: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE space_innovation SET feasibility = ?, impact = ?, updated_at = ? WHERE innovation_id = ?',
                                 (feasibility, impact, now, innovation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '创新项目不存在'}
        except Exception as e:
            logger.error(f'评估创新项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_space_innovations(self, education_type: str = None, innovation_type: str = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM space_innovation WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if innovation_type:
                    query += ' AND innovation_type = ?'
                    params.append(innovation_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                innovations = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'innovations': innovations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取太空创新项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源管理 ==========

    def add_space_resource(self, resource_name: str, resource_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"sre_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO space_resources (
                            resource_id, resource_name, resource_type, location,
                            quantity, unit, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'available', ?, ?)
                    ''', (resource_id, resource_name, resource_type,
                          kwargs.get('location'), kwargs.get('quantity', 0),
                          kwargs.get('unit'), now, now))
                    conn.commit()
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'添加太空资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def manage_resource(self, resource_id: str, transaction_type: str,
                        quantity: int, **kwargs) -> Dict[str, Any]:
        try:
            management_id = f"rmg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT quantity FROM space_resources WHERE resource_id = ?', (resource_id,))
                    current = cursor.fetchone()
                    if not current:
                        return {'success': False, 'error': '资源不存在'}
                    new_quantity = current[0] + quantity if transaction_type == 'add' else current[0] - quantity
                    if new_quantity < 0:
                        return {'success': False, 'error': '资源数量不足'}
                    cursor.execute('UPDATE space_resources SET quantity = ?, updated_at = ? WHERE resource_id = ?',
                                 (new_quantity, now, resource_id))
                    cursor.execute('''
                        INSERT INTO resource_management (
                            management_id, resource_id, transaction_type, quantity,
                            user_id, user_name, transaction_date, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (management_id, resource_id, transaction_type, quantity,
                          kwargs.get('user_id'), kwargs.get('user_name'),
                          now[:10], kwargs.get('notes'), now))
                    conn.commit()
                    return {'success': True, 'management_id': management_id}
        except Exception as e:
            logger.error(f'资源管理操作失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_space_resources(self, resource_type: str = None, status: str = None,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM space_resources WHERE 1=1'
                params = []
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取太空资源列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_resource_transactions(self, resource_id: str, page: int = 1,
                                  page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM resource_management WHERE resource_id = ? ORDER BY transaction_date DESC'
                cursor.execute('SELECT COUNT(*) as cnt FROM resource_management WHERE resource_id = ?', (resource_id,))
                total = cursor.fetchone()['cnt']
                cursor.execute(query + ' LIMIT ? OFFSET ?', (resource_id, page_size, (page - 1) * page_size))
                transactions = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'transactions': transactions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资源交易记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_service_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                results = {}

                for table, label in [
                    ('space_courses', 'courses'),
                    ('astronomical_observation', 'observations'),
                    ('aerospace_projects', 'projects'),
                    ('satellite_mission', 'satellite_missions'),
                    ('space_experiments', 'experiments'),
                    ('deep_space_mission', 'deep_space_missions'),
                    ('space_education', 'education_activities'),
                    ('space_innovation', 'innovations'),
                    ('space_resources', 'resources')
                ]:
                    if education_type:
                        cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE education_type = ?', (education_type,))
                    else:
                        cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    results[label] = cursor.fetchone()[0]

                cursor.execute('SELECT SUM(quantity) FROM space_resources')
                results['total_resource_quantity'] = cursor.fetchone()[0] or 0

                return {'success': True, 'statistics': results}
        except Exception as e:
            logger.error(f'获取服务统计失败: {e}')
            return {'success': False, 'error': str(e)}