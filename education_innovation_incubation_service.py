#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育创新孵化服务 (v15.13.0)
====================================
提供教育创新项目孵化、教育科技、教育创业、创新大赛、孵化器管理、
导师指导、投融资对接、知识产权转化等综合管理服务。

核心能力：
1. 创新项目 - 项目申报、评审、立项、管理
2. 孵化管理 - 场地管理、入驻管理、孵化记录
3. 导师指导 - 导师管理、配对、指导记录
4. 创新大赛 - 赛事组织、报名、评审、颁奖
5. 投融资对接 - 投资机构、融资轮次、投资交易
6. 知识产权 - 专利申请、商标注册、成果转化
7. 项目加速 - 加速计划、资源对接、路演安排
8. 毕业管理 - 毕业评估、成果验收、校友跟踪
9. 奖励激励 - 奖励政策、评审发放、绩效评估
10. 统计分析 - 孵化成效、投资回报、创新指数

差异化支持：
- 成人教育：职业技能创新、企业培训、终身学习
- K12教育：素质教育、创客教育、学科创新
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_innovation_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationInnovation')


# ========== 创新孵化配置 ==========

INNOVATION_TYPES = {
    'model': {'name': '模式创新', 'description': '教育模式与运营方式创新', 'suitable_for': ['adult', 'k12']},
    'technology': {'name': '技术创新', 'description': '教育技术与数字化工具创新', 'suitable_for': ['adult', 'k12']},
    'product': {'name': '产品创新', 'description': '教育产品与课程体系创新', 'suitable_for': ['adult', 'k12']},
    'service': {'name': '服务创新', 'description': '教育服务与支持体系创新', 'suitable_for': ['adult', 'k12']},
    'management': {'name': '管理创新', 'description': '教育机构管理与治理创新', 'suitable_for': ['adult']},
    'institution': {'name': '制度创新', 'description': '教育政策与制度设计创新', 'suitable_for': ['adult', 'k12']}
}

INCUBATION_STAGES = {
    'idea': {'name': '创意阶段', 'duration': '1-3个月', 'key_milestone': '创意验证'},
    'project': {'name': '立项阶段', 'duration': '1-2个月', 'key_milestone': '项目立项'},
    'development': {'name': '研发阶段', 'duration': '3-6个月', 'key_milestone': '原型开发'},
    'testing': {'name': '测试阶段', 'duration': '1-3个月', 'key_milestone': '试点验证'},
    'promotion': {'name': '推广阶段', 'duration': '2-4个月', 'key_milestone': '市场推广'},
    'operation': {'name': '运营阶段', 'duration': '6-12个月', 'key_milestone': '规模化运营'},
    'exit': {'name': '退出阶段', 'duration': '1-3个月', 'key_milestone': '成功退出'}
}

PROJECT_STATUS = {
    'incubating': {'name': '在孵', 'description': '正在孵化中'},
    'accelerating': {'name': '加速', 'description': '进入加速期'},
    'graduated': {'name': '毕业', 'description': '成功孵化毕业'},
    'terminated': {'name': '终止', 'description': '项目终止'},
    'transformed': {'name': '转型', 'description': '项目转型'}
}

COMPETITION_TYPES = {
    'innovation': {'name': '创新大赛', 'description': '教育创新项目竞赛', 'suitable_for': ['adult', 'k12']},
    'entrepreneurship': {'name': '创业大赛', 'description': '教育创业项目竞赛', 'suitable_for': ['adult']},
    'design': {'name': '设计大赛', 'description': '教育产品设计竞赛', 'suitable_for': ['adult', 'k12']},
    'skill': {'name': '技能大赛', 'description': '教育技能展示竞赛', 'suitable_for': ['adult', 'k12']},
    'academic': {'name': '学科竞赛', 'description': '学科教育创新竞赛', 'suitable_for': ['k12']}
}

MENTOR_ROLES = {
    'technical': {'name': '技术导师', 'description': '提供技术指导', 'expertise': ['教育技术', '软件开发', '数据分析']},
    'business': {'name': '商业导师', 'description': '提供商业指导', 'expertise': ['商业模式', '市场营销', '运营管理']},
    'education': {'name': '教育导师', 'description': '提供教育指导', 'expertise': ['教育理论', '课程设计', '教学方法']},
    'legal': {'name': '法律导师', 'description': '提供法律指导', 'expertise': ['知识产权', '公司法', '合规管理']},
    'finance': {'name': '财务导师', 'description': '提供财务指导', 'expertise': ['财务管理', '投融资', '税务筹划']}
}

INVESTMENT_TYPES = {
    'angel': {'name': '天使投资', 'stage': '早期', 'typical_amount': '50-500万'},
    'seed': {'name': '种子轮', 'stage': '种子期', 'typical_amount': '10-100万'},
    'series_a': {'name': 'A轮', 'stage': '成长期', 'typical_amount': '500万-2亿'},
    'series_b': {'name': 'B轮', 'stage': '扩张期', 'typical_amount': '2亿-10亿'},
    'series_c': {'name': 'C轮', 'stage': '成熟期', 'typical_amount': '10亿以上'},
    'strategic': {'name': '战略投资', 'stage': '成熟期', 'typical_amount': '视情况'}
}

IP_TYPES = {
    'patent': {'name': '专利', 'sub_types': ['发明专利', '实用新型', '外观设计'], 'protection_period': '20年/10年/15年'},
    'trademark': {'name': '商标', 'sub_types': ['文字商标', '图形商标', '组合商标'], 'protection_period': '10年'},
    'copyright': {'name': '著作权', 'sub_types': ['作品著作权', '软件著作权'], 'protection_period': '作者终身+50年'},
    'software_copyright': {'name': '软件著作权', 'sub_types': ['教育软件', '学习平台', '管理系统'], 'protection_period': '作者终身+50年'},
    'trade_secret': {'name': '商业秘密', 'sub_types': ['技术秘密', '经营秘密'], 'protection_period': '长期'}
}

SUPPORT_LEVELS = {
    'basic': {'name': '基础支持', 'benefits': ['办公场地', '基础培训', '网络服务'], 'monthly_fee': 0},
    'growth': {'name': '成长支持', 'benefits': ['导师指导', '市场对接', '法务咨询'], 'monthly_fee': 500},
    'accelerate': {'name': '加速支持', 'benefits': ['投资对接', '路演机会', '媒体宣传'], 'monthly_fee': 1500},
    'excellent': {'name': '卓越支持', 'benefits': ['专项基金', '海外资源', '上市辅导'], 'monthly_fee': 5000}
}


class EducationInnovationIncubationService:
    """教育创新孵化服务"""

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
                    CREATE TABLE IF NOT EXISTS innovation_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        innovation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        problem_statement TEXT,
                        solution TEXT,
                        target_audience TEXT,
                        market_analysis TEXT,
                        business_model TEXT,
                        founder_name TEXT,
                        founder_id INTEGER,
                        team_size INTEGER DEFAULT 1,
                        support_level TEXT DEFAULT 'basic',
                        status TEXT DEFAULT 'incubating',
                        current_stage TEXT DEFAULT 'idea',
                        total_investment REAL DEFAULT 0,
                        funding_raised REAL DEFAULT 0,
                        ip_count INTEGER DEFAULT 0,
                        competition_wins INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        member_id INTEGER NOT NULL,
                        member_name TEXT,
                        role TEXT DEFAULT 'member',
                        join_date TEXT,
                        UNIQUE(project_id, member_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_milestones (
                        milestone_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        stage TEXT NOT NULL,
                        milestone_name TEXT NOT NULL,
                        description TEXT,
                        target_date TEXT,
                        completed_date TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_documents (
                        doc_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        doc_type TEXT,
                        doc_name TEXT NOT NULL,
                        file_url TEXT,
                        uploaded_by INTEGER,
                        uploaded_at TEXT,
                        is_approved INTEGER DEFAULT 0
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS incubator_spaces (
                        space_id TEXT PRIMARY KEY,
                        space_name TEXT NOT NULL,
                        location TEXT,
                        capacity INTEGER DEFAULT 10,
                        occupied_count INTEGER DEFAULT 0,
                        monthly_rent REAL DEFAULT 0,
                        amenities TEXT,
                        status TEXT DEFAULT 'available',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS space_occupancy (
                        occupancy_id TEXT PRIMARY KEY,
                        space_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT,
                        monthly_fee REAL,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        UNIQUE(space_id, project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mentor_profiles (
                        mentor_id TEXT PRIMARY KEY,
                        mentor_name TEXT NOT NULL,
                        mentor_role TEXT NOT NULL,
                        education_type TEXT,
                        expertise TEXT,
                        experience_years INTEGER DEFAULT 0,
                        organization TEXT,
                        title TEXT,
                        contact_email TEXT,
                        contact_phone TEXT,
                        availability TEXT,
                        hourly_rate REAL DEFAULT 0,
                        assigned_projects INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mentor_assignments (
                        assignment_id TEXT PRIMARY KEY,
                        mentor_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT,
                        hours_per_week INTEGER DEFAULT 2,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        UNIQUE(mentor_id, project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS competition_events (
                        event_id TEXT PRIMARY KEY,
                        event_name TEXT NOT NULL,
                        competition_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        organizer TEXT,
                        description TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        registration_deadline TEXT,
                        location TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        prize_pool REAL DEFAULT 0,
                        status TEXT DEFAULT 'announced',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS competition_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        team_name TEXT,
                        leader_name TEXT,
                        submission_date TEXT,
                        score REAL,
                        rank INTEGER,
                        award TEXT,
                        status TEXT DEFAULT 'registered',
                        UNIQUE(event_id, project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS investment_rounds (
                        round_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        round_type TEXT NOT NULL,
                        round_number INTEGER DEFAULT 1,
                        target_amount REAL NOT NULL,
                        raised_amount REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS investment_deals (
                        deal_id TEXT PRIMARY KEY,
                        round_id TEXT NOT NULL,
                        investor_name TEXT NOT NULL,
                        investment_amount REAL NOT NULL,
                        equity_percentage REAL,
                        deal_date TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS intellectual_property (
                        ip_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        ip_type TEXT NOT NULL,
                        ip_name TEXT NOT NULL,
                        description TEXT,
                        registration_no TEXT,
                        registration_date TEXT,
                        expiration_date TEXT,
                        owner TEXT,
                        status TEXT DEFAULT 'applied',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ip_transactions (
                        transaction_id TEXT PRIMARY KEY,
                        ip_id TEXT NOT NULL,
                        transaction_type TEXT,
                        buyer_name TEXT,
                        seller_name TEXT,
                        transaction_amount REAL,
                        transaction_date TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_rewards (
                        reward_id TEXT PRIMARY KEY,
                        reward_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        eligibility TEXT,
                        amount REAL DEFAULT 0,
                        max_winners INTEGER DEFAULT 1,
                        application_deadline TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS incubation_records (
                        record_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        action_type TEXT,
                        action_description TEXT,
                        performed_by TEXT,
                        performed_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育创新孵化服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 创新项目 ==========

    def create_project(self, project_name: str, innovation_type: str,
                       education_type: str, founder_name: str,
                       founder_id: int, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"prj_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_projects (
                            project_id, project_name, innovation_type,
                            education_type, description, problem_statement,
                            solution, target_audience, market_analysis,
                            business_model, founder_name, founder_id,
                            team_size, support_level, status, current_stage,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'basic', 'incubating', 'idea', ?, ?)
                    ''', (project_id, project_name, innovation_type,
                          education_type, kwargs.get('description'),
                          kwargs.get('problem_statement'), kwargs.get('solution'),
                          kwargs.get('target_audience'), kwargs.get('market_analysis'),
                          kwargs.get('business_model'), founder_name, founder_id,
                          now, now))
                    cursor.execute('INSERT INTO project_members (project_id, member_id, member_name, role, join_date) VALUES (?, ?, ?, ?, ?)',
                                 (project_id, founder_id, founder_name, 'founder', now[:10]))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'create', '项目创建', founder_name, now[:10]))
                    conn.commit()
                    logger.info(f'创建创新项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建创新项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_stage(self, project_id: str, stage: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT current_stage FROM innovation_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('UPDATE innovation_projects SET current_stage = ?, updated_at = ? WHERE project_id = ?',
                                 (stage, now, project_id))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'stage_update', f'阶段变更: {project[0]} -> {stage}', 'system', now[:10]))
                    conn.commit()
                    return {'success': True, 'stage': stage}
        except Exception as e:
            logger.error(f'更新项目阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_project_member(self, project_id: str, member_id: int,
                           member_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO project_members (project_id, member_id, member_name, role, join_date) VALUES (?, ?, ?, ?, ?)',
                                 (project_id, member_id, member_name, kwargs.get('role', 'member'), now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE innovation_projects SET team_size = team_size + 1, updated_at = ? WHERE project_id = ?',
                                     (now, project_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成员已加入'}
        except Exception as e:
            logger.error(f'添加项目成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_projects(self, education_type: str = None, status: str = None,
                      stage: str = None, page: int = 1,
                      page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM innovation_projects WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if stage:
                    query += ' AND current_stage = ?'
                    params.append(stage)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                projects = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'projects': projects, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 孵化管理 ==========

    def create_incubator_space(self, space_name: str, **kwargs) -> Dict[str, Any]:
        try:
            space_id = f"spc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO incubator_spaces (
                            space_id, space_name, location, capacity,
                            occupied_count, monthly_rent, amenities,
                            status, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 0, ?, ?, 'available', ?, ?, ?)
                    ''', (space_id, space_name, kwargs.get('location'),
                          kwargs.get('capacity', 10), kwargs.get('monthly_rent', 0),
                          kwargs.get('amenities'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建孵化场地: {space_name} ({space_id})')
                    return {'success': True, 'space_id': space_id}
        except Exception as e:
            logger.error(f'创建孵化场地失败: {e}')
            return {'success': False, 'error': str(e)}

    def occupy_space(self, space_id: str, project_id: str,
                     start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            occupancy_id = f"occ_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT capacity, occupied_count, monthly_rent FROM incubator_spaces WHERE space_id = ?',
                                 (space_id,))
                    space = cursor.fetchone()
                    if not space:
                        return {'success': False, 'error': '场地不存在'}
                    if space[1] >= space[0]:
                        return {'success': False, 'error': '场地已满'}
                    cursor.execute('INSERT INTO space_occupancy (occupancy_id, space_id, project_id, start_date, end_date, monthly_fee, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (occupancy_id, space_id, project_id, start_date,
                                  kwargs.get('end_date'), space[2], 'active', now, now))
                    cursor.execute('UPDATE incubator_spaces SET occupied_count = occupied_count + 1, status = ? WHERE space_id = ?',
                                 ('full' if space[1] + 1 >= space[0] else 'available', space_id))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'occupy_space', f'入驻场地: {space_id}', 'system', start_date))
                    conn.commit()
                    return {'success': True, 'occupancy_id': occupancy_id}
        except Exception as e:
            logger.error(f'场地入驻失败: {e}')
            return {'success': False, 'error': str(e)}

    def release_space(self, occupancy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT space_id, project_id, status FROM space_occupancy WHERE occupancy_id = ?',
                                 (occupancy_id,))
                    occupancy = cursor.fetchone()
                    if not occupancy:
                        return {'success': False, 'error': '入驻记录不存在'}
                    if occupancy[2] != 'active':
                        return {'success': False, 'error': '状态不允许释放'}
                    cursor.execute('UPDATE space_occupancy SET status = ?, updated_at = ? WHERE occupancy_id = ?',
                                 ('released', now, occupancy_id))
                    cursor.execute('UPDATE incubator_spaces SET occupied_count = occupied_count - 1, status = ?, updated_at = ? WHERE space_id = ?',
                                 ('available', now, occupancy[0]))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", occupancy[1], 'release_space', '场地释放', 'system', now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'场地释放失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_incubator_spaces(self, education_type: str = None,
                              status: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM incubator_spaces WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                spaces = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'spaces': spaces, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取场地列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 导师指导 ==========

    def register_mentor(self, mentor_name: str, mentor_role: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            mentor_id = f"mtr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO mentor_profiles (
                            mentor_id, mentor_name, mentor_role,
                            education_type, expertise, experience_years,
                            organization, title, contact_email,
                            contact_phone, availability, hourly_rate,
                            assigned_projects, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
                    ''', (mentor_id, mentor_name, mentor_role,
                          kwargs.get('education_type'), kwargs.get('expertise'),
                          kwargs.get('experience_years', 0), kwargs.get('organization'),
                          kwargs.get('title'), kwargs.get('contact_email'),
                          kwargs.get('contact_phone'), kwargs.get('availability'),
                          kwargs.get('hourly_rate', 0), now, now))
                    conn.commit()
                    logger.info(f'注册导师: {mentor_name} ({mentor_id})')
                    return {'success': True, 'mentor_id': mentor_id}
        except Exception as e:
            logger.error(f'注册导师失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_mentor(self, mentor_id: str, project_id: str,
                      start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            assignment_id = f"asm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM mentor_profiles WHERE mentor_id = ?', (mentor_id,))
                    mentor = cursor.fetchone()
                    if not mentor:
                        return {'success': False, 'error': '导师不存在'}
                    if mentor[0] != 1:
                        return {'success': False, 'error': '导师不可用'}
                    cursor.execute('INSERT OR IGNORE INTO mentor_assignments (assignment_id, mentor_id, project_id, start_date, end_date, hours_per_week, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (assignment_id, mentor_id, project_id, start_date,
                                  kwargs.get('end_date'), kwargs.get('hours_per_week', 2),
                                  'active', now, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE mentor_profiles SET assigned_projects = assigned_projects + 1, updated_at = ? WHERE mentor_id = ?',
                                     (now, mentor_id))
                        cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                     (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'mentor_assigned', f'导师分配: {mentor_id}', 'system', start_date))
                        conn.commit()
                        return {'success': True, 'assignment_id': assignment_id}
                    return {'success': False, 'error': '导师已分配'}
        except Exception as e:
            logger.error(f'导师分配失败: {e}')
            return {'success': False, 'error': str(e)}

    def unassign_mentor(self, assignment_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT mentor_id, project_id, status FROM mentor_assignments WHERE assignment_id = ?',
                                 (assignment_id,))
                    assignment = cursor.fetchone()
                    if not assignment:
                        return {'success': False, 'error': '分配记录不存在'}
                    if assignment[2] != 'active':
                        return {'success': False, 'error': '状态不允许取消'}
                    cursor.execute('UPDATE mentor_assignments SET status = ?, end_date = ?, updated_at = ? WHERE assignment_id = ?',
                                 ('completed', now[:10], now, assignment_id))
                    cursor.execute('UPDATE mentor_profiles SET assigned_projects = assigned_projects - 1, updated_at = ? WHERE mentor_id = ?',
                                 (now, assignment[0]))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", assignment[1], 'mentor_unassigned', '导师取消分配', 'system', now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'取消导师分配失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_mentors(self, mentor_role: str = None, education_type: str = None,
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM mentor_profiles WHERE is_active = 1'
                params = []
                if mentor_role:
                    query += ' AND mentor_role = ?'
                    params.append(mentor_role)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY assigned_projects ASC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                mentors = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'mentors': mentors, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取导师列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创新大赛 ==========

    def create_competition(self, event_name: str, competition_type: str,
                           education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            event_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO competition_events (
                            event_id, event_name, competition_type,
                            education_type, organizer, description,
                            start_date, end_date, registration_deadline,
                            location, max_participants, registered_count,
                            prize_pool, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'announced', ?, ?)
                    ''', (event_id, event_name, competition_type,
                          education_type, kwargs.get('organizer'),
                          kwargs.get('description'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('registration_deadline'),
                          kwargs.get('location'), kwargs.get('max_participants', 100),
                          kwargs.get('prize_pool', 0), now, now))
                    conn.commit()
                    logger.info(f'创建创新大赛: {event_name} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'创建创新大赛失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_competition(self, event_id: str, project_id: str,
                             team_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM competition_events WHERE event_id = ?',
                                 (event_id,))
                    event = cursor.fetchone()
                    if not event:
                        return {'success': False, 'error': '赛事不存在'}
                    if event[2] != 'announced':
                        return {'success': False, 'error': '赛事状态不允许报名'}
                    if event[1] >= event[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO competition_participants (event_id, project_id, team_name, leader_name, submission_date, status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (event_id, project_id, team_name, kwargs.get('leader_name'), now[:10], 'registered'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE competition_events SET registered_count = registered_count + 1, updated_at = ? WHERE event_id = ?',
                                     (now, event_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该赛事'}
        except Exception as e:
            logger.error(f'大赛报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_competition_entry(self, event_id: str, project_id: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE competition_participants SET submission_date = ?, status = ? WHERE event_id = ? AND project_id = ?',
                                 (now[:10], 'submitted', event_id, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'提交参赛作品失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_competition(self, event_id: str, project_id: str,
                             score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE competition_participants SET score = ?, rank = ?, award = ?, status = ? WHERE event_id = ? AND project_id = ?',
                                 (score, kwargs.get('rank'), kwargs.get('award'), 'evaluated', event_id, project_id))
                    if cursor.rowcount > 0:
                        if kwargs.get('award'):
                            cursor.execute('UPDATE innovation_projects SET competition_wins = competition_wins + 1, updated_at = ? WHERE project_id = ?',
                                         (now, project_id))
                        conn.commit()
                        return {'success': True, 'score': score, 'award': kwargs.get('award')}
                    return {'success': False, 'error': '参赛记录不存在'}
        except Exception as e:
            logger.error(f'大赛评审失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_competitions(self, education_type: str = None,
                          competition_type: str = None, status: str = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM competition_events WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if competition_type:
                    query += ' AND competition_type = ?'
                    params.append(competition_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                competitions = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'competitions': competitions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取赛事列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 投融资对接 ==========

    def create_investment_round(self, project_id: str, round_type: str,
                                target_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            round_id = f"inv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM investment_rounds WHERE project_id = ?', (project_id,))
                    count = cursor.fetchone()[0]
                    cursor.execute('''
                        INSERT INTO investment_rounds (
                            round_id, project_id, round_type, round_number,
                            target_amount, raised_amount, start_date,
                            end_date, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, 'open', ?, ?)
                    ''', (round_id, project_id, round_type, count + 1,
                          target_amount, kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建融资轮次: {round_type} ({round_id})')
                    return {'success': True, 'round_id': round_id}
        except Exception as e:
            logger.error(f'创建融资轮次失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_investment_deal(self, round_id: str, investor_name: str,
                               investment_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            deal_id = f"del_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT project_id, raised_amount, target_amount FROM investment_rounds WHERE round_id = ?',
                                 (round_id,))
                    round_info = cursor.fetchone()
                    if not round_info:
                        return {'success': False, 'error': '轮次不存在'}
                    cursor.execute('INSERT INTO investment_deals (deal_id, round_id, investor_name, investment_amount, equity_percentage, deal_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (deal_id, round_id, investor_name, investment_amount,
                                  kwargs.get('equity_percentage'), now[:10], 'pending', now))
                    new_raised = round_info[1] + investment_amount
                    cursor.execute('UPDATE investment_rounds SET raised_amount = ?, status = ?, updated_at = ? WHERE round_id = ?',
                                 (new_raised, 'completed' if new_raised >= round_info[2] else 'open', now, round_id))
                    cursor.execute('UPDATE innovation_projects SET funding_raised = funding_raised + ?, updated_at = ? WHERE project_id = ?',
                                 (investment_amount, now, round_info[0]))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", round_info[0], 'investment', f'投资到账: {investment_amount}', investor_name, now[:10]))
                    conn.commit()
                    return {'success': True, 'deal_id': deal_id}
        except Exception as e:
            logger.error(f'记录投资交易失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_investment_deal(self, deal_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT round_id, investor_name, investment_amount FROM investment_deals WHERE deal_id = ? AND status = ?',
                                 (deal_id, 'pending'))
                    deal = cursor.fetchone()
                    if not deal:
                        return {'success': False, 'error': '交易记录不存在或状态不正确'}
                    cursor.execute('UPDATE investment_deals SET status = ?, updated_at = ? WHERE deal_id = ?',
                                 ('approved', now, deal_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'审批投资交易失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_investment_rounds(self, project_id: str = None,
                               status: str = None, page: int = 1,
                               page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM investment_rounds WHERE 1=1'
                params = []
                if project_id:
                    query += ' AND project_id = ?'
                    params.append(project_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY round_number DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                rounds = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rounds': rounds, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取融资轮次失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识产权 ==========

    def register_ip(self, project_id: str, ip_type: str, ip_name: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            ip_id = f"ip_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO intellectual_property (
                            ip_id, project_id, ip_type, ip_name,
                            description, registration_no, registration_date,
                            expiration_date, owner, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?, ?)
                    ''', (ip_id, project_id, ip_type, ip_name,
                          kwargs.get('description'), kwargs.get('registration_no'),
                          kwargs.get('registration_date'), kwargs.get('expiration_date'),
                          kwargs.get('owner'), now, now))
                    cursor.execute('UPDATE innovation_projects SET ip_count = ip_count + 1, updated_at = ? WHERE project_id = ?',
                                 (now, project_id))
                    conn.commit()
                    logger.info(f'注册知识产权: {ip_name} ({ip_id})')
                    return {'success': True, 'ip_id': ip_id}
        except Exception as e:
            logger.error(f'注册知识产权失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_ip_status(self, ip_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE intellectual_property SET status = ?, registration_no = ?, registration_date = ?, expiration_date = ?, updated_at = ? WHERE ip_id = ?',
                                 (status, kwargs.get('registration_no'), kwargs.get('registration_date'), kwargs.get('expiration_date'), now, ip_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '知识产权记录不存在'}
        except Exception as e:
            logger.error(f'更新知识产权状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_ip_transaction(self, ip_id: str, transaction_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            transaction_id = f"tra_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO ip_transactions (transaction_id, ip_id, transaction_type, buyer_name, seller_name, transaction_amount, transaction_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (transaction_id, ip_id, transaction_type,
                                  kwargs.get('buyer_name'), kwargs.get('seller_name'),
                                  kwargs.get('transaction_amount'), now[:10], 'pending', now))
                    conn.commit()
                    return {'success': True, 'transaction_id': transaction_id}
        except Exception as e:
            logger.error(f'创建知识产权交易失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ip(self, project_id: str = None, ip_type: str = None,
                status: str = None, page: int = 1,
                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM intellectual_property WHERE 1=1'
                params = []
                if project_id:
                    query += ' AND project_id = ?'
                    params.append(project_id)
                if ip_type:
                    query += ' AND ip_type = ?'
                    params.append(ip_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                ip_list = [dict(ip) for ip in cursor.fetchall()]
                return {'success': True, 'ip_list': ip_list, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取知识产权列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 项目加速 ==========

    def upgrade_to_accelerate(self, project_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM innovation_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    if project[0] != 'incubating':
                        return {'success': False, 'error': '项目状态不允许升级'}
                    cursor.execute('UPDATE innovation_projects SET status = ?, support_level = ?, updated_at = ? WHERE project_id = ?',
                                 ('accelerating', 'accelerate', now, project_id))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'upgrade', '升级为加速项目', 'system', now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'升级加速项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def schedule_pitch(self, project_id: str, pitch_date: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO project_milestones (milestone_id, project_id, stage, milestone_name, description, target_date, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (f"mls_{uuid.uuid4().hex[:12]}", project_id, 'operation', '路演', kwargs.get('description', '项目路演'), pitch_date, 'pending', now, now))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'pitch_scheduled', f'路演安排: {pitch_date}', kwargs.get('performed_by', 'system'), now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'安排路演失败: {e}')
            return {'success': False, 'error': str(e)}

    def connect_investor(self, project_id: str, investor_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'investor_connection', f'投资人对接: {investor_name}', kwargs.get('performed_by', 'system'), now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'投资人对接失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 毕业管理 ==========

    def graduate_project(self, project_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM innovation_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('UPDATE innovation_projects SET status = ?, current_stage = ?, updated_at = ? WHERE project_id = ?',
                                 ('graduated', 'exit', now, project_id))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'graduate', '项目毕业', kwargs.get('performed_by', 'system'), now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'项目毕业失败: {e}')
            return {'success': False, 'error': str(e)}

    def terminate_project(self, project_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM innovation_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('UPDATE innovation_projects SET status = ?, updated_at = ? WHERE project_id = ?',
                                 ('terminated', now, project_id))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'terminate', f'项目终止: {kwargs.get("reason", "")}', kwargs.get('performed_by', 'system'), now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'项目终止失败: {e}')
            return {'success': False, 'error': str(e)}

    def transform_project(self, project_id: str, new_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT innovation_type FROM innovation_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('UPDATE innovation_projects SET status = ?, innovation_type = ?, updated_at = ? WHERE project_id = ?',
                                 ('transformed', new_type, now, project_id))
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'transform', f'项目转型: {project[0]} -> {new_type}', kwargs.get('performed_by', 'system'), now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'项目转型失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 奖励激励 ==========

    def create_reward_program(self, reward_name: str, **kwargs) -> Dict[str, Any]:
        try:
            reward_id = f"rwd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_rewards (
                            reward_id, reward_name, education_type,
                            description, eligibility, amount, max_winners,
                            application_deadline, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
                    ''', (reward_id, reward_name, kwargs.get('education_type'),
                          kwargs.get('description'), kwargs.get('eligibility'),
                          kwargs.get('amount', 0), kwargs.get('max_winners', 1),
                          kwargs.get('application_deadline'), now, now))
                    conn.commit()
                    logger.info(f'创建奖励计划: {reward_name} ({reward_id})')
                    return {'success': True, 'reward_id': reward_id}
        except Exception as e:
            logger.error(f'创建奖励计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def award_reward(self, reward_id: str, project_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO incubation_records (record_id, project_id, action_type, action_description, performed_by, performed_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"rec_{uuid.uuid4().hex[:12]}", project_id, 'reward', f'获得奖励: {reward_id}', kwargs.get('performed_by', 'system'), now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'发放奖励失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_rewards(self, education_type: str = None, status: str = None,
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM innovation_rewards WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                rewards = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rewards': rewards, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取奖励列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_incubation_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                filters = '' if not education_type else f" WHERE education_type = '{education_type}'"

                cursor.execute(f'SELECT COUNT(*) FROM innovation_projects{filters}')
                total_projects = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM innovation_projects WHERE status = "graduated"{(" AND education_type = ?" if education_type else "")}', (education_type,) if education_type else ())
                graduated_projects = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM innovation_projects WHERE status = "incubating"{(" AND education_type = ?" if education_type else "")}', (education_type,) if education_type else ())
                incubating_projects = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM innovation_projects WHERE status = "accelerating"{(" AND education_type = ?" if education_type else "")}', (education_type,) if education_type else ())
                accelerating_projects = cursor.fetchone()[0]

                cursor.execute(f'SELECT SUM(funding_raised) FROM innovation_projects{filters}')
                total_funding = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT SUM(ip_count) FROM innovation_projects{filters}')
                total_ip = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT SUM(competition_wins) FROM innovation_projects{filters}')
                total_wins = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM mentor_profiles WHERE is_active = 1{(" AND education_type = ?" if education_type else "")}', (education_type,) if education_type else ())
                active_mentors = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM incubator_spaces{(" AND education_type = ?" if education_type else "")}', (education_type,) if education_type else ())
                total_spaces = cursor.fetchone()[0]

                cursor.execute(f'SELECT SUM(occupied_count) FROM incubator_spaces{(" AND education_type = ?" if education_type else "")}', (education_type,) if education_type else ())
                occupied_spaces = cursor.fetchone()[0] or 0

                return {
                    'success': True,
                    'total_projects': total_projects,
                    'graduated_projects': graduated_projects,
                    'incubating_projects': incubating_projects,
                    'accelerating_projects': accelerating_projects,
                    'graduation_rate': round(graduated_projects / total_projects * 100, 1) if total_projects > 0 else 0,
                    'total_funding': total_funding,
                    'total_ip': total_ip,
                    'total_competition_wins': total_wins,
                    'active_mentors': active_mentors,
                    'total_spaces': total_spaces,
                    'occupied_spaces': occupied_spaces,
                    'space_utilization': round(occupied_spaces / total_spaces * 100, 1) if total_spaces > 0 else 0,
                    'education_type': education_type or 'all'
                }
        except Exception as e:
            logger.error(f'获取孵化统计失败: {e}')
            return {'success': False, 'error': str(e)}