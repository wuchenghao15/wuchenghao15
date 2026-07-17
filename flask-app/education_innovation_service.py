#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育创新创业服务 (v15.17.0)
====================================
提供创新项目孵化、创业培训、创业指导、投融资对接、知识产权保护等综合服务。

核心能力：
1. 创新项目 - 项目申报、评审管理、跟踪评估
2. 孵化服务 - 孵化计划、项目入驻、阶段管理
3. 创业培训 - 课程管理、培训报名、成果认证
4. 创业导师 - 导师管理、匹配对接、指导记录
5. 投融资服务 - 融资对接、投资管理、项目估值
6. 知识产权 - 专利申请、商标注册、版权保护
7. 创业园区 - 园区管理、企业入驻、资源共享
8. 创业大赛 - 赛事组织、项目报名、评审颁奖
9. 创业生态 - 生态建设、资源整合、协作网络
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


# ========== 创新配置 ==========

INNOVATION_TYPES = {
    'tech': {'name': '技术创新', 'description': '基于新技术研发的创新'},
    'product': {'name': '产品创新', 'description': '新产品开发与优化'},
    'model': {'name': '模式创新', 'description': '商业模式创新'},
    'service': {'name': '服务创新', 'description': '服务方式与内容创新'},
    'management': {'name': '管理创新', 'description': '管理方法与流程创新'},
    'education': {'name': '教育创新', 'description': '教育理念与方法创新'},
    'content': {'name': '内容创新', 'description': '内容创作与呈现创新'},
    'business_model': {'name': '商业模式创新', 'description': '商业运作模式创新'}
}

INCUBATION_STAGES = {
    'idea': {'name': '创意阶段', 'description': '概念构思与可行性分析'},
    'seed': {'name': '种子阶段', 'description': '原型开发与初步验证'},
    'startup': {'name': '初创阶段', 'description': '产品上线与市场探索'},
    'growth': {'name': '成长阶段', 'description': '规模扩张与团队建设'},
    'expansion': {'name': '扩张阶段', 'description': '市场拓展与融资准备'},
    'mature': {'name': '成熟阶段', 'description': '稳定运营与规模化'},
    'transformation': {'name': '转型阶段', 'description': '业务转型与升级'},
    'exit': {'name': '退出阶段', 'description': '并购或上市退出'}
}

ENTREPRENEURSHIP_PROGRAMS = {
    'incubation': {'name': '创业孵化', 'duration': '3-6个月'},
    'training': {'name': '创业培训', 'duration': '1-3个月'},
    'competition': {'name': '创业竞赛', 'duration': '1-2个月'},
    'investment': {'name': '创业投资', 'duration': '长期'},
    'accelerator': {'name': '创业加速器', 'duration': '6-12个月'},
    'incubator': {'name': '创业孵化器', 'duration': '6-24个月'},
    'park': {'name': '创业园区', 'duration': '长期'},
    'community': {'name': '创业社区', 'duration': '长期'}
}

TRAINING_MODULES = {
    'foundation': {'name': '创业基础', 'hours': 16, 'level': '入门'},
    'business_plan': {'name': '商业计划', 'hours': 24, 'level': '进阶'},
    'marketing': {'name': '市场营销', 'hours': 20, 'level': '进阶'},
    'finance': {'name': '财务管理', 'hours': 18, 'level': '进阶'},
    'team': {'name': '团队管理', 'hours': 12, 'level': '入门'},
    'funding': {'name': '融资策略', 'hours': 20, 'level': '高级'},
    'legal': {'name': '法律合规', 'hours': 16, 'level': '入门'},
    'ip': {'name': '知识产权', 'hours': 16, 'level': '进阶'}
}

MENTOR_ROLES = {
    'entrepreneurship': {'name': '创业导师', 'expertise': '创业经验指导'},
    'technical': {'name': '技术导师', 'expertise': '技术研发指导'},
    'business': {'name': '商业导师', 'expertise': '商业模式设计'},
    'industry': {'name': '行业导师', 'expertise': '行业趋势分析'},
    'investment': {'name': '投资导师', 'expertise': '投融资指导'},
    'legal': {'name': '法律导师', 'expertise': '法律风险防控'},
    'finance': {'name': '财务导师', 'expertise': '财务管理咨询'},
    'management': {'name': '管理导师', 'expertise': '企业管理指导'}
}

INVESTMENT_TYPES = {
    'angel': {'name': '天使投资', 'stage': '种子期', 'amount': '10万-500万'},
    'vc': {'name': '风险投资', 'stage': '成长期', 'amount': '500万-5000万'},
    'pe': {'name': '私募股权', 'stage': '成熟期', 'amount': '5000万以上'},
    'crowdfunding': {'name': '众筹', 'stage': '初创期', 'amount': '1万-100万'},
    'government': {'name': '政府扶持', 'stage': '各阶段', 'amount': '视政策'},
    'bank': {'name': '银行贷款', 'stage': '成长期', 'amount': '灵活'},
    'corporate': {'name': '企业投资', 'stage': '各阶段', 'amount': '灵活'},
    'personal': {'name': '个人投资', 'stage': '各阶段', 'amount': '灵活'}
}

IP_PROTECTION = {
    'patent': {'name': '专利', 'duration': '20年', 'type': '发明/实用新型/外观'},
    'trademark': {'name': '商标', 'duration': '10年', 'type': '文字/图形/组合'},
    'copyright': {'name': '版权', 'duration': '作者终生+50年', 'type': '作品/软件'},
    'trade_secret': {'name': '商业秘密', 'duration': '长期', 'type': '技术/经营信息'},
    'domain': {'name': '域名', 'duration': '1-10年', 'type': '网址'},
    'software_copyright': {'name': '软件著作权', 'duration': '50年', 'type': '软件作品'},
    'ic_layout': {'name': '集成电路布图', 'duration': '10年', 'type': '芯片设计'},
    'plant_variety': {'name': '植物新品种', 'duration': '15-20年', 'type': '农业品种'}
}

COMPETITION_TYPES = {
    'innovation': {'name': '创新创业大赛', 'scope': '综合性'},
    'business_plan': {'name': '商业计划竞赛', 'scope': '商业策划'},
    'tech': {'name': '科技竞赛', 'scope': '科技创新'},
    'creative': {'name': '创意大赛', 'scope': '创意设计'},
    'challenge': {'name': '创业挑战赛', 'scope': '专项挑战'},
    'roadshow': {'name': '路演大赛', 'scope': '项目展示'},
    'industry': {'name': '行业竞赛', 'scope': '特定行业'},
    'international': {'name': '国际竞赛', 'scope': '跨国参与'}
}


class EducationInnovationService:
    """教育创新创业服务"""

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
                        innovation_type TEXT,
                        education_type TEXT,
                        category TEXT,
                        description TEXT,
                        founder_name TEXT,
                        founder_id INTEGER,
                        team_members TEXT,
                        status TEXT DEFAULT 'draft',
                        stage TEXT DEFAULT 'idea',
                        score REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        content TEXT,
                        milestones TEXT,
                        budget REAL DEFAULT 0,
                        target_market TEXT,
                        competitive_analysis TEXT,
                        risks TEXT,
                        mitigation_strategy TEXT,
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS incubation_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        program_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        duration TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_seats INTEGER DEFAULT 20,
                        enrolled_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS program_applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        program_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        applicant_id INTEGER,
                        applicant_name TEXT,
                        application_date TEXT,
                        status TEXT DEFAULT 'pending',
                        review_notes TEXT,
                        FOREIGN KEY(program_id) REFERENCES incubation_programs(program_id),
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS entrepreneurship_training (
                        training_id TEXT PRIMARY KEY,
                        training_name TEXT NOT NULL,
                        module_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        duration_hours INTEGER,
                        start_date TEXT,
                        end_date TEXT,
                        instructor TEXT,
                        max_participants INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        training_id TEXT NOT NULL,
                        participant_id INTEGER,
                        participant_name TEXT,
                        enrollment_date TEXT,
                        attendance_rate REAL DEFAULT 0,
                        completion_status TEXT DEFAULT 'in_progress',
                        certificate_no TEXT,
                        FOREIGN KEY(training_id) REFERENCES entrepreneurship_training(training_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mentorship (
                        mentor_id TEXT PRIMARY KEY,
                        mentor_name TEXT NOT NULL,
                        mentor_role TEXT,
                        expertise TEXT,
                        education_type TEXT,
                        experience_years INTEGER,
                        availability TEXT,
                        hourly_rate REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mentor_matching (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mentor_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        student_id INTEGER,
                        match_date TEXT,
                        status TEXT DEFAULT 'matched',
                        session_count INTEGER DEFAULT 0,
                        FOREIGN KEY(mentor_id) REFERENCES mentorship(mentor_id),
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS investment_deals (
                        deal_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        investment_type TEXT,
                        investor_name TEXT,
                        amount REAL,
                        equity_percent REAL,
                        deal_date TEXT,
                        status TEXT DEFAULT 'negotiating',
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS deal_flow (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deal_id TEXT NOT NULL,
                        stage TEXT,
                        comment TEXT,
                        update_date TEXT,
                        FOREIGN KEY(deal_id) REFERENCES investment_deals(deal_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ip_protection (
                        ip_id TEXT PRIMARY KEY,
                        ip_type TEXT,
                        education_type TEXT,
                        name TEXT NOT NULL,
                        description TEXT,
                        applicant_name TEXT,
                        applicant_id INTEGER,
                        status TEXT DEFAULT 'pending',
                        registration_no TEXT,
                        application_date TEXT,
                        approval_date TEXT,
                        expiry_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ip_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ip_id TEXT NOT NULL,
                        project_id TEXT,
                        record_type TEXT,
                        detail TEXT,
                        record_date TEXT,
                        FOREIGN KEY(ip_id) REFERENCES ip_protection(ip_id),
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS startup_parks (
                        park_id TEXT PRIMARY KEY,
                        park_name TEXT NOT NULL,
                        location TEXT,
                        education_type TEXT,
                        description TEXT,
                        total_area REAL,
                        available_area REAL,
                        resident_count INTEGER DEFAULT 0,
                        services TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS park_residents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        park_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        company_name TEXT,
                        resident_date TEXT,
                        area_allocated REAL,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY(park_id) REFERENCES startup_parks(park_id),
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS startup_competitions (
                        competition_id TEXT PRIMARY KEY,
                        competition_name TEXT NOT NULL,
                        competition_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        registration_deadline TEXT,
                        max_teams INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'registration',
                        prizes TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS competition_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        competition_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        team_name TEXT,
                        rank INTEGER,
                        score REAL,
                        prize TEXT,
                        status TEXT DEFAULT 'participating',
                        FOREIGN KEY(competition_id) REFERENCES startup_competitions(competition_id),
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS startup_ecosystem (
                        ecosystem_id TEXT PRIMARY KEY,
                        ecosystem_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        members_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ecosystem_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ecosystem_id TEXT NOT NULL,
                        member_id INTEGER,
                        member_name TEXT,
                        member_type TEXT,
                        join_date TEXT,
                        FOREIGN KEY(ecosystem_id) REFERENCES startup_ecosystem(ecosystem_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS venture_capital (
                        vc_id TEXT PRIMARY KEY,
                        vc_name TEXT NOT NULL,
                        fund_size REAL,
                        investment_focus TEXT,
                        education_type TEXT,
                        contact_info TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vc_portfolio (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vc_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        investment_amount REAL,
                        investment_date TEXT,
                        equity_percent REAL,
                        FOREIGN KEY(vc_id) REFERENCES venture_capital(vc_id),
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                conn.commit()
                logger.info('教育创新创业服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 创新项目 ==========

    def create_innovation_project(self, project_name: str, innovation_type: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"inv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_projects (
                            project_id, project_name, innovation_type,
                            education_type, category, description,
                            founder_name, founder_id, team_members,
                            status, stage, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', 'idea', ?, ?)
                    ''', (project_id, project_name, innovation_type,
                          education_type, kwargs.get('category'),
                          kwargs.get('description'), kwargs.get('founder_name'),
                          kwargs.get('founder_id'), kwargs.get('team_members'),
                          now, now))
                    cursor.execute('INSERT INTO project_details (project_id) VALUES (?)', (project_id,))
                    conn.commit()
                    logger.info(f'创建创新项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建创新项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_project_review(self, project_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE innovation_projects SET status = ?, updated_at = ? WHERE project_id = ? AND status = ?',
                                 ('reviewing', now, project_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'reviewing'}
                    return {'success': False, 'error': '项目状态不允许提交'}
        except Exception as e:
            logger.error(f'提交项目评审失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_project(self, project_id: str, approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE innovation_projects SET status = ?, score = ?, updated_at = ? WHERE project_id = ? AND status = ?',
                                 (status, kwargs.get('score', 0), now, project_id, 'reviewing'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status, 'score': kwargs.get('score', 0)}
                    return {'success': False, 'error': '项目状态不允许评审'}
        except Exception as e:
            logger.error(f'评审项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_stage(self, project_id: str, stage: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE innovation_projects SET stage = ?, updated_at = ? WHERE project_id = ?',
                                 (stage, now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'stage': stage}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新项目阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 孵化服务 ==========

    def create_incubation_program(self, program_name: str, program_type: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"inc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ENTREPRENEURSHIP_PROGRAMS.get(program_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO incubation_programs (
                            program_id, program_name, program_type,
                            education_type, description, duration,
                            start_date, end_date, max_seats,
                            enrolled_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'open', ?, ?)
                    ''', (program_id, program_name, program_type,
                          education_type, kwargs.get('description'),
                          kwargs.get('duration', config.get('duration', '3个月')),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('max_seats', 20), now, now))
                    conn.commit()
                    logger.info(f'创建孵化项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建孵化项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_incubation_program(self, program_id: str, project_id: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_seats, enrolled_count, status FROM incubation_programs WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '孵化项目不存在'}
                    if program[2] != 'open':
                        return {'success': False, 'error': '孵化项目报名已关闭'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO program_applications (program_id, project_id, applicant_id, applicant_name, application_date, status) VALUES (?, ?, ?, ?, ?, \'pending\')',
                                 (program_id, project_id, kwargs.get('applicant_id'), kwargs.get('applicant_name'), now[:10]))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已申请该项目'}
        except Exception as e:
            logger.error(f'申请孵化项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_application(self, application_id: int, approved: bool,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT program_id FROM program_applications WHERE id = ? AND status = ?', (application_id, 'pending'))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '申请记录不存在'}
                    cursor.execute('UPDATE program_applications SET status = ?, review_notes = ? WHERE id = ?',
                                 (status, kwargs.get('review_notes'), application_id))
                    if approved:
                        cursor.execute('UPDATE incubation_programs SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE program_id = ?', (now, app[0]))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'审核申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_incubation_programs(self, education_type: str = None,
                                  status: str = None, page: int = 1,
                                  page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM incubation_programs WHERE 1=1'
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
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取孵化项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创业培训 ==========

    def create_training(self, training_name: str, module_type: str,
                        education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"trn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TRAINING_MODULES.get(module_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO entrepreneurship_training (
                            training_id, training_name, module_type,
                            education_type, description, duration_hours,
                            start_date, end_date, instructor,
                            max_participants, enrolled_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'open', ?, ?)
                    ''', (training_id, training_name, module_type,
                          education_type, kwargs.get('description'),
                          kwargs.get('duration_hours', config.get('hours', 16)),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('instructor'), kwargs.get('max_participants', 30),
                          now, now))
                    conn.commit()
                    logger.info(f'创建培训课程: {training_name} ({training_id})')
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建培训课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_training(self, training_id: str, participant_id: int,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM entrepreneurship_training WHERE training_id = ?', (training_id,))
                    training = cursor.fetchone()
                    if not training:
                        return {'success': False, 'error': '培训课程不存在'}
                    if training[2] != 'open':
                        return {'success': False, 'error': '培训课程报名已关闭'}
                    if training[0] and training[1] >= training[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO training_records (training_id, participant_id, participant_name, enrollment_date) VALUES (?, ?, ?, ?)',
                                 (training_id, participant_id, kwargs.get('participant_name'), now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE entrepreneurship_training SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE training_id = ?', (now, training_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该培训'}
        except Exception as e:
            logger.error(f'报名培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_completion(self, record_id: int, attendance_rate: float,
                                    **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            completion_status = 'completed' if attendance_rate >= 80 else 'incomplete'
            certificate_no = f"TCR{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if completion_status == 'completed' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE training_records SET attendance_rate = ?, completion_status = ?, certificate_no = ? WHERE id = ?',
                                 (attendance_rate, completion_status, certificate_no, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'completion_status': completion_status, 'certificate_no': certificate_no}
                    return {'success': False, 'error': '培训记录不存在'}
        except Exception as e:
            logger.error(f'记录培训完成状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_trainings(self, education_type: str = None, module_type: str = None,
                       status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM entrepreneurship_training WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if module_type:
                    query += ' AND module_type = ?'
                    params.append(module_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                trainings = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'trainings': trainings, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取培训列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创业导师 ==========

    def register_mentor(self, mentor_name: str, mentor_role: str,
                         education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            mentor_id = f"mtr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = MENTOR_ROLES.get(mentor_role, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO mentorship (
                            mentor_id, mentor_name, mentor_role,
                            expertise, education_type, experience_years,
                            availability, hourly_rate, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (mentor_id, mentor_name, mentor_role,
                          kwargs.get('expertise', config.get('expertise', '')),
                          education_type, kwargs.get('experience_years', 0),
                          kwargs.get('availability'), kwargs.get('hourly_rate', 0),
                          now, now))
                    conn.commit()
                    logger.info(f'注册导师: {mentor_name} ({mentor_id})')
                    return {'success': True, 'mentor_id': mentor_id}
        except Exception as e:
            logger.error(f'注册导师失败: {e}')
            return {'success': False, 'error': str(e)}

    def match_mentor(self, mentor_id: str, project_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO mentor_matching (mentor_id, project_id, student_id, match_date, status) VALUES (?, ?, ?, ?, \'matched\')',
                                 (mentor_id, project_id, kwargs.get('student_id'), now[:10]))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已匹配该导师'}
        except Exception as e:
            logger.error(f'匹配导师失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_mentor_session(self, match_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE mentor_matching SET session_count = session_count + 1 WHERE id = ?', (match_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '匹配记录不存在'}
        except Exception as e:
            logger.error(f'记录导师会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_mentors(self, mentor_role: str = None, education_type: str = None,
                      status: str = 'active', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM mentorship WHERE 1=1'
                params = []
                if mentor_role:
                    query += ' AND mentor_role = ?'
                    params.append(mentor_role)
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
                mentors = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'mentors': mentors, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取导师列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 投融资服务 ==========

    def create_investment_deal(self, project_id: str, investment_type: str,
                                amount: float, **kwargs) -> Dict[str, Any]:
        try:
            deal_id = f"ivd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO investment_deals (
                            deal_id, project_id, investment_type,
                            investor_name, amount, equity_percent,
                            deal_date, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'negotiating')
                    ''', (deal_id, project_id, investment_type,
                          kwargs.get('investor_name'), amount,
                          kwargs.get('equity_percent', 0), now[:10]))
                    cursor.execute('INSERT INTO deal_flow (deal_id, stage, comment, update_date) VALUES (?, ?, ?, ?)',
                                 (deal_id, 'negotiating', 'Deal created', now[:10]))
                    conn.commit()
                    logger.info(f'创建投资交易: {deal_id}')
                    return {'success': True, 'deal_id': deal_id}
        except Exception as e:
            logger.error(f'创建投资交易失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_deal_stage(self, deal_id: str, stage: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE investment_deals SET status = ?, updated_at = ? WHERE deal_id = ?',
                                 (stage, now, deal_id))
                    cursor.execute('INSERT INTO deal_flow (deal_id, stage, comment, update_date) VALUES (?, ?, ?, ?)',
                                 (deal_id, stage, kwargs.get('comment', ''), now[:10]))
                    conn.commit()
                    return {'success': True, 'stage': stage}
        except Exception as e:
            logger.error(f'更新交易阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_vc(self, vc_name: str, **kwargs) -> Dict[str, Any]:
        try:
            vc_id = f"vc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO venture_capital (
                            vc_id, vc_name, fund_size,
                            investment_focus, education_type,
                            contact_info, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (vc_id, vc_name, kwargs.get('fund_size', 0),
                          kwargs.get('investment_focus'), kwargs.get('education_type'),
                          kwargs.get('contact_info'), now, now))
                    conn.commit()
                    logger.info(f'注册创投机构: {vc_name} ({vc_id})')
                    return {'success': True, 'vc_id': vc_id}
        except Exception as e:
            logger.error(f'注册创投机构失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_vc_portfolio(self, vc_id: str, project_id: str,
                          investment_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO vc_portfolio (vc_id, project_id, investment_amount, investment_date, equity_percent) VALUES (?, ?, ?, ?, ?)',
                                 (vc_id, project_id, investment_amount, now[:10], kwargs.get('equity_percent', 0)))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加投资组合失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_deals(self, project_id: str = None, status: str = None,
                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM investment_deals WHERE 1=1'
                params = []
                if project_id:
                    query += ' AND project_id = ?'
                    params.append(project_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY deal_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                deals = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'deals': deals, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取交易列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识产权 ==========

    def apply_ip_protection(self, ip_type: str, name: str, education_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            ip_id = f"ip_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = IP_PROTECTION.get(ip_type, {})
            duration = int(config.get('duration', '10年').replace('年', '')) if '年' in str(config.get('duration', '')) else 10
            expiry_date = (datetime.now() + timedelta(days=duration * 365)).isoformat()[:10] if duration > 0 else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ip_protection (
                            ip_id, ip_type, education_type, name,
                            description, applicant_name, applicant_id,
                            status, application_date, expiry_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                    ''', (ip_id, ip_type, education_type, name,
                          kwargs.get('description'), kwargs.get('applicant_name'),
                          kwargs.get('applicant_id'), now[:10], expiry_date,
                          now, now))
                    conn.commit()
                    logger.info(f'申请知识产权: {name} ({ip_id})')
                    return {'success': True, 'ip_id': ip_id}
        except Exception as e:
            logger.error(f'申请知识产权失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_ip_protection(self, ip_id: str, approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            registration_no = f"IPR{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if approved else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ip_protection SET status = ?, registration_no = ?, approval_date = ?, updated_at = ? WHERE ip_id = ? AND status = ?',
                                 (status, registration_no, now[:10] if approved else None, now, ip_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status, 'registration_no': registration_no}
                    return {'success': False, 'error': '申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核知识产权失败: {e}')
            return {'success': False, 'error': str(e)}

    def link_ip_to_project(self, ip_id: str, project_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO ip_records (ip_id, project_id, record_type, detail, record_date) VALUES (?, ?, \'link\', \'Linked to project\', ?)',
                                 (ip_id, project_id, now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'关联知识产权失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ip_protections(self, ip_type: str = None, education_type: str = None,
                             status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ip_protection WHERE 1=1'
                params = []
                if ip_type:
                    query += ' AND ip_type = ?'
                    params.append(ip_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY application_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                protections = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'protections': protections, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取知识产权列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创业园区 ==========

    def create_startup_park(self, park_name: str, location: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            park_id = f"prk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO startup_parks (
                            park_id, park_name, location,
                            education_type, description, total_area,
                            available_area, resident_count, services,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (park_id, park_name, location, education_type,
                          kwargs.get('description'), kwargs.get('total_area', 0),
                          kwargs.get('available_area', kwargs.get('total_area', 0)),
                          kwargs.get('services'), now, now))
                    conn.commit()
                    logger.info(f'创建创业园区: {park_name} ({park_id})')
                    return {'success': True, 'park_id': park_id}
        except Exception as e:
            logger.error(f'创建创业园区失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_park_residency(self, park_id: str, project_id: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT available_area, resident_count, status FROM startup_parks WHERE park_id = ?', (park_id,))
                    park = cursor.fetchone()
                    if not park:
                        return {'success': False, 'error': '创业园区不存在'}
                    if park[2] != 'active':
                        return {'success': False, 'error': '园区状态不允许入驻'}
                    if park[0] and park[0] < kwargs.get('area_required', 0):
                        return {'success': False, 'error': '可用面积不足'}
                    cursor.execute('INSERT OR IGNORE INTO park_residents (park_id, project_id, company_name, resident_date, area_allocated, status) VALUES (?, ?, ?, ?, ?, \'active\')',
                                 (park_id, project_id, kwargs.get('company_name'), now[:10], kwargs.get('area_allocated', 0)))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE startup_parks SET available_area = available_area - ?, resident_count = resident_count + 1, updated_at = ? WHERE park_id = ?',
                                     (kwargs.get('area_allocated', 0), now, park_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已入驻该园区'}
        except Exception as e:
            logger.error(f'申请园区入驻失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_resident_status(self, resident_id: int, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT park_id, area_allocated FROM park_residents WHERE id = ?', (resident_id,))
                    resident = cursor.fetchone()
                    if not resident:
                        return {'success': False, 'error': '入驻记录不存在'}
                    cursor.execute('UPDATE park_residents SET status = ? WHERE id = ?', (status, resident_id))
                    if status == 'left':
                        cursor.execute('UPDATE startup_parks SET available_area = available_area + ?, resident_count = resident_count - 1, updated_at = ? WHERE park_id = ?',
                                     (resident[1], now, resident[0]))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'更新入驻状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_startup_parks(self, education_type: str = None, status: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM startup_parks WHERE 1=1'
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
                parks = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'parks': parks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取创业园区列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创业大赛 ==========

    def create_competition(self, competition_name: str, competition_type: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            competition_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO startup_competitions (
                            competition_id, competition_name, competition_type,
                            education_type, description, start_date,
                            end_date, registration_deadline, max_teams,
                            registered_count, status, prizes,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'registration', ?, ?, ?)
                    ''', (competition_id, competition_name, competition_type,
                          education_type, kwargs.get('description'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('registration_deadline'),
                          kwargs.get('max_teams', 100), kwargs.get('prizes'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建创业大赛: {competition_name} ({competition_id})')
                    return {'success': True, 'competition_id': competition_id}
        except Exception as e:
            logger.error(f'创建创业大赛失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_competition(self, competition_id: str, project_id: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_teams, registered_count, status FROM startup_competitions WHERE competition_id = ?', (competition_id,))
                    comp = cursor.fetchone()
                    if not comp:
                        return {'success': False, 'error': '大赛不存在'}
                    if comp[2] != 'registration':
                        return {'success': False, 'error': '报名已截止'}
                    if comp[0] and comp[1] >= comp[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO competition_results (competition_id, project_id, team_name, status) VALUES (?, ?, ?, \'participating\')',
                                 (competition_id, project_id, kwargs.get('team_name')))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE startup_competitions SET registered_count = registered_count + 1, updated_at = ? WHERE competition_id = ?', (now, competition_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目已报名'}
        except Exception as e:
            logger.error(f'大赛报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_competition_result(self, result_id: int, rank: int, score: float,
                                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE competition_results SET rank = ?, score = ?, prize = ?, status = ? WHERE id = ?',
                                 (rank, score, kwargs.get('prize'), 'completed', result_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'rank': rank, 'score': score}
                    return {'success': False, 'error': '参赛记录不存在'}
        except Exception as e:
            logger.error(f'记录大赛结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_competitions(self, education_type: str = None, competition_type: str = None,
                           status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM startup_competitions WHERE 1=1'
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
            logger.error(f'获取大赛列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创业生态 ==========

    def create_ecosystem(self, ecosystem_name: str, education_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            ecosystem_id = f"eco_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO startup_ecosystem (
                            ecosystem_id, ecosystem_name, education_type,
                            description, members_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (ecosystem_id, ecosystem_name, education_type,
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建创业生态: {ecosystem_name} ({ecosystem_id})')
                    return {'success': True, 'ecosystem_id': ecosystem_id}
        except Exception as e:
            logger.error(f'创建创业生态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_ecosystem_member(self, ecosystem_id: str, member_id: int,
                              member_name: str, member_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO ecosystem_members (ecosystem_id, member_id, member_name, member_type, join_date) VALUES (?, ?, ?, ?, ?)',
                                 (ecosystem_id, member_id, member_name, member_type, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE startup_ecosystem SET members_count = members_count + 1, updated_at = ? WHERE ecosystem_id = ?', (now, ecosystem_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该生态'}
        except Exception as e:
            logger.error(f'添加生态成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ecosystem_members(self, ecosystem_id: str, member_type: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ecosystem_members WHERE ecosystem_id = ?'
                params = [ecosystem_id]
                if member_type:
                    query += ' AND member_type = ?'
                    params.append(member_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY join_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                members = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'members': members, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取生态成员列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ecosystems(self, education_type: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM startup_ecosystem WHERE 1=1'
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
                ecosystems = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'ecosystems': ecosystems, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取创业生态列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计服务 ==========

    def get_innovation_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                if education_type:
                    cursor.execute('SELECT COUNT(*) FROM innovation_projects WHERE education_type = ?', (education_type,))
                    stats['total_projects'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM innovation_projects WHERE education_type = ? AND status = ?', (education_type, 'approved'))
                    stats['approved_projects'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM incubation_programs WHERE education_type = ?', (education_type,))
                    stats['incubation_programs'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM entrepreneurship_training WHERE education_type = ?', (education_type,))
                    stats['trainings'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM startup_competitions WHERE education_type = ?', (education_type,))
                    stats['competitions'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM ip_protection WHERE education_type = ?', (education_type,))
                    stats['ip_protections'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM mentorship WHERE education_type = ?', (education_type,))
                    stats['mentors'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM investment_deals WHERE project_id IN (SELECT project_id FROM innovation_projects WHERE education_type = ?)', (education_type,))
                    stats['deals'] = cursor.fetchone()[0]
                else:
                    cursor.execute('SELECT COUNT(*) FROM innovation_projects')
                    stats['total_projects'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM innovation_projects WHERE status = ?', ('approved',))
                    stats['approved_projects'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM incubation_programs')
                    stats['incubation_programs'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM entrepreneurship_training')
                    stats['trainings'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM startup_competitions')
                    stats['competitions'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM ip_protection')
                    stats['ip_protections'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM mentorship')
                    stats['mentors'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM investment_deals')
                    stats['deals'] = cursor.fetchone()[0]
                stats['education_type'] = education_type or 'all'
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}