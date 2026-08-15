#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育创新管理服务 (v15.22.0)
====================================
提供创新项目管理、创新人才培养、创新成果转化等综合管理服务。

核心能力：
1. 创新项目管理 - 项目创建、阶段管理、成员管理、任务管理
2. 创新人才培养 - 人才登记、角色管理、能力评估、成长轨迹
3. 创新成果转化 - 成果登记、转化管理、知识产权、产业化跟踪
4. 创新资金管理 - 资金申请、审批管理、预算控制、使用跟踪
5. 创新平台建设 - 平台创建、资源管理、运营维护、协作支持
6. 创新合作网络 - 合作建立、资源共享、协同创新、成果共享
7. 创新评估体系 - 评估指标、评分管理、报告生成、改进建议
8. 创新文化建设 - 文化活动、氛围营造、激励机制、创新宣传
9. 奖励管理 - 奖项设置、申报管理、评审流程、颁奖记录
10. 统计分析 - 创新数据汇总、趋势分析、决策支持

差异化支持：
- 成人教育：职业技能创新、企业培训、终身学习
- K12教育：素养培育、创客教育、STEM教育
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
    'teaching': {'name': '教学创新', 'description': '教学方法与模式创新', 'education_type': ['adult', 'k12']},
    'course': {'name': '课程创新', 'description': '课程内容与体系创新', 'education_type': ['adult', 'k12']},
    'technology': {'name': '技术创新', 'description': '教育技术与工具创新', 'education_type': ['adult', 'k12']},
    'management': {'name': '管理创新', 'description': '教育管理与治理创新', 'education_type': ['adult']},
    'model': {'name': '模式创新', 'description': '教育服务与运营模式创新', 'education_type': ['adult', 'k12']},
    'service': {'name': '服务创新', 'description': '教育服务方式创新', 'education_type': ['adult']},
    'product': {'name': '产品创新', 'description': '教育产品与资源创新', 'education_type': ['adult', 'k12']},
    'organization': {'name': '组织创新', 'description': '教育组织形态创新', 'education_type': ['adult']}
}

PROJECT_PHASES = {
    'idea': {'name': '创意阶段', 'description': '项目创意产生与筛选', 'order': 1},
    'rnd': {'name': '研发阶段', 'description': '方案设计与原型开发', 'order': 2},
    'pilot': {'name': '试点阶段', 'description': '小范围试验与验证', 'order': 3},
    'promotion': {'name': '推广阶段', 'description': '规模推广与应用', 'order': 4},
    'industrialization': {'name': '产业化阶段', 'description': '商业化与规模化', 'order': 5},
    'evaluation': {'name': '评估阶段', 'description': '效果评估与总结', 'order': 6},
    'iteration': {'name': '迭代阶段', 'description': '优化改进与升级', 'order': 7},
    'termination': {'name': '终止阶段', 'description': '项目结束与归档', 'order': 8}
}

TALENT_ROLES = {
    'mentor': {'name': '创新导师', 'description': '指导创新实践', 'education_type': ['adult', 'k12']},
    'practitioner': {'name': '创新实践者', 'description': '执行创新项目', 'education_type': ['adult', 'k12']},
    'researcher': {'name': '创新研究者', 'description': '开展创新研究', 'education_type': ['adult']},
    'manager': {'name': '创新管理者', 'description': '管理创新过程', 'education_type': ['adult']},
    'investor': {'name': '创新投资者', 'description': '提供资金支持', 'education_type': ['adult']},
    'promoter': {'name': '创新推广者', 'description': '推广创新成果', 'education_type': ['adult', 'k12']},
    'evaluator': {'name': '创新评估者', 'description': '评估创新成效', 'education_type': ['adult', 'k12']},
    'decision_maker': {'name': '创新决策者', 'description': '制定创新战略', 'education_type': ['adult']}
}

TRANSFORMATION_MODES = {
    'technology_transfer': {'name': '技术转让', 'description': '技术成果转让', 'education_type': ['adult']},
    'patent_license': {'name': '专利许可', 'description': '专利技术许可', 'education_type': ['adult']},
    'industry_university': {'name': '产学研合作', 'description': '产学研协同创新', 'education_type': ['adult']},
    'incubator': {'name': '孵化器', 'description': '入驻孵化器培育', 'education_type': ['adult']},
    'accelerator': {'name': '加速器', 'description': '快速成长加速', 'education_type': ['adult']},
    'venture_capital': {'name': '创业投资', 'description': '引入风险投资', 'education_type': ['adult']},
    'enterprise_cooperation': {'name': '企业合作', 'description': '企业联合开发', 'education_type': ['adult']},
    'government_support': {'name': '政府支持', 'description': '获取政府资助', 'education_type': ['adult', 'k12']}
}

FUNDING_SOURCES = {
    'government': {'name': '政府资助', 'description': '政府专项资金', 'education_type': ['adult', 'k12']},
    'enterprise': {'name': '企业投资', 'description': '企业投入资金', 'education_type': ['adult']},
    'donation': {'name': '社会捐赠', 'description': '社会力量捐赠', 'education_type': ['adult', 'k12']},
    'research': {'name': '科研经费', 'description': '科研项目经费', 'education_type': ['adult']},
    'crowdfunding': {'name': '众筹', 'description': '众筹融资', 'education_type': ['adult']},
    'cooperation': {'name': '合作基金', 'description': '多方合作基金', 'education_type': ['adult']},
    'special': {'name': '专项基金', 'description': '专项创新基金', 'education_type': ['adult', 'k12']},
    'self': {'name': '自有资金', 'description': '自有资金投入', 'education_type': ['adult', 'k12']}
}

PLATFORM_TYPES = {
    'lab': {'name': '创新实验室', 'description': '专业创新实验场所', 'education_type': ['adult', 'k12']},
    'maker': {'name': '创客空间', 'description': '创客实践空间', 'education_type': ['adult', 'k12']},
    'incubator': {'name': '孵化器', 'description': '创业孵化基地', 'education_type': ['adult']},
    'accelerator': {'name': '加速器', 'description': '企业加速成长', 'education_type': ['adult']},
    'tech_transfer': {'name': '技术转移中心', 'description': '技术成果转移', 'education_type': ['adult']},
    'industry_university': {'name': '产学研平台', 'description': '产学研协同平台', 'education_type': ['adult']},
    'international': {'name': '国际合作平台', 'description': '国际交流合作', 'education_type': ['adult']},
    'alliance': {'name': '创新联盟', 'description': '创新合作联盟', 'education_type': ['adult', 'k12']}
}

COOPERATION_TYPES = {
    'school_enterprise': {'name': '校企合作', 'description': '学校与企业合作', 'education_type': ['adult']},
    'industry_university': {'name': '产学研合作', 'description': '产业、学校、科研合作', 'education_type': ['adult']},
    'international': {'name': '国际合作', 'description': '国际教育合作', 'education_type': ['adult']},
    'school_school': {'name': '校际合作', 'description': '学校间合作', 'education_type': ['adult', 'k12']},
    'industry': {'name': '行业合作', 'description': '跨行业合作', 'education_type': ['adult']},
    'interdisciplinary': {'name': '跨学科合作', 'description': '多学科交叉合作', 'education_type': ['adult', 'k12']},
    'community': {'name': '社区合作', 'description': '学校与社区合作', 'education_type': ['adult', 'k12']},
    'government': {'name': '政府合作', 'description': '与政府部门合作', 'education_type': ['adult', 'k12']}
}

ASSESSMENT_CRITERIA = {
    'innovation': {'name': '创新性', 'description': '创新程度与独特性', 'weight': 0.15},
    'practicality': {'name': '实用性', 'description': '实际应用价值', 'weight': 0.15},
    'impact': {'name': '影响力', 'description': '产生的影响范围', 'weight': 0.15},
    'sustainability': {'name': '可持续性', 'description': '长期发展潜力', 'weight': 0.12},
    'economic': {'name': '经济效益', 'description': '经济价值创造', 'weight': 0.13},
    'social': {'name': '社会效益', 'description': '社会价值贡献', 'weight': 0.15},
    'academic': {'name': '学术价值', 'description': '理论与学术贡献', 'weight': 0.10},
    'promotion': {'name': '推广价值', 'description': '可复制推广性', 'weight': 0.10}
}


class EducationInnovationService:
    """教育创新管理服务"""

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
                        education_type TEXT,
                        description TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        budget REAL DEFAULT 0,
                        status TEXT DEFAULT 'idea',
                        start_date TEXT,
                        end_date TEXT,
                        expected_outcome TEXT,
                        actual_outcome TEXT,
                        progress REAL DEFAULT 0,
                        visibility TEXT DEFAULT 'internal',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_phases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        phase TEXT NOT NULL,
                        phase_name TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        completed_at TEXT,
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        member_id INTEGER NOT NULL,
                        member_name TEXT,
                        role TEXT,
                        join_date TEXT,
                        leave_date TEXT,
                        UNIQUE(project_id, member_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_tasks (
                        task_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        task_name TEXT NOT NULL,
                        description TEXT,
                        assignee_id INTEGER,
                        assignee_name TEXT,
                        priority TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'pending',
                        due_date TEXT,
                        completed_at TEXT,
                        created_at TEXT,
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_talent (
                        talent_id TEXT PRIMARY KEY,
                        talent_name TEXT NOT NULL,
                        education_type TEXT,
                        email TEXT,
                        phone TEXT,
                        department TEXT,
                        position TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        talent_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        expertise TEXT,
                        skills TEXT,
                        experience TEXT,
                        achievements TEXT,
                        FOREIGN KEY(talent_id) REFERENCES innovation_talent(talent_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_results (
                        result_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        result_name TEXT NOT NULL,
                        result_type TEXT,
                        description TEXT,
                        intellectual_property TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS result_transformation (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        result_id TEXT NOT NULL,
                        transformation_mode TEXT,
                        partner TEXT,
                        agreement_date TEXT,
                        value REAL DEFAULT 0,
                        status TEXT DEFAULT 'planning',
                        progress REAL DEFAULT 0,
                        FOREIGN KEY(result_id) REFERENCES innovation_results(result_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS funding_management (
                        funding_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        amount REAL DEFAULT 0,
                        allocated_amount REAL DEFAULT 0,
                        used_amount REAL DEFAULT 0,
                        budget_details TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS funding_applications (
                        application_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        funding_source TEXT,
                        amount REAL DEFAULT 0,
                        purpose TEXT,
                        budget_plan TEXT,
                        status TEXT DEFAULT 'submitted',
                        review_comments TEXT,
                        approved_amount REAL,
                        approved_at TEXT,
                        created_at TEXT,
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_platforms (
                        platform_id TEXT PRIMARY KEY,
                        platform_name TEXT NOT NULL,
                        platform_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        location TEXT,
                        capacity INTEGER DEFAULT 0,
                        current_users INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS platform_resources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform_id TEXT NOT NULL,
                        resource_name TEXT,
                        resource_type TEXT,
                        quantity INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'available',
                        FOREIGN KEY(platform_id) REFERENCES innovation_platforms(platform_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cooperation_networks (
                        network_id TEXT PRIMARY KEY,
                        network_name TEXT NOT NULL,
                        cooperation_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        partner_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cooperation_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        network_id TEXT NOT NULL,
                        partner_name TEXT,
                        partner_type TEXT,
                        cooperation_content TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'ongoing',
                        FOREIGN KEY(network_id) REFERENCES cooperation_networks(network_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_system (
                        assessment_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        assessment_type TEXT,
                        criteria TEXT,
                        weights TEXT,
                        scheduled_date TEXT,
                        status TEXT DEFAULT 'scheduled',
                        created_at TEXT,
                        FOREIGN KEY(project_id) REFERENCES innovation_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        assessment_id TEXT NOT NULL,
                        criterion TEXT,
                        score REAL,
                        comment TEXT,
                        FOREIGN KEY(assessment_id) REFERENCES assessment_system(assessment_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_culture (
                        culture_id TEXT PRIMARY KEY,
                        culture_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        objectives TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS culture_initiatives (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        culture_id TEXT NOT NULL,
                        initiative_name TEXT,
                        description TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'planned',
                        FOREIGN KEY(culture_id) REFERENCES innovation_culture(culture_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_awards (
                        award_id TEXT PRIMARY KEY,
                        award_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        level TEXT,
                        criteria TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS award_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        award_id TEXT NOT NULL,
                        project_id TEXT,
                        talent_id TEXT,
                        applicant_name TEXT,
                        application_date TEXT,
                        status TEXT DEFAULT 'submitted',
                        result TEXT,
                        awarded_at TEXT,
                        FOREIGN KEY(award_id) REFERENCES innovation_awards(award_id)
                    )
                ''')
                conn.commit()
                logger.info('教育创新管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 创新项目管理 ==========

    def create_project(self, project_name: str, innovation_type: str,
                       education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"ipr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_projects (
                            project_id, project_name, innovation_type, education_type,
                            description, leader_id, leader_name, budget,
                            status, start_date, end_date, expected_outcome,
                            actual_outcome, progress, visibility, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'idea', ?, ?, ?, NULL, 0, ?, ?, ?)
                    ''', (project_id, project_name, innovation_type, education_type,
                          kwargs.get('description'), kwargs.get('leader_id'),
                          kwargs.get('leader_name'), kwargs.get('budget', 0),
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          kwargs.get('expected_outcome'),
                          kwargs.get('visibility', 'internal'), now, now))
                    conn.commit()
                    logger.info(f'创建创新项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建创新项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_phase(self, project_id: str, phase: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            phase_config = PROJECT_PHASES.get(phase, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM innovation_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('SELECT id FROM project_phases WHERE project_id = ? AND phase = ?', (project_id, phase))
                    if cursor.fetchone():
                        cursor.execute('''
                            UPDATE project_phases SET status = ?, start_date = ?, end_date = ?, description = ?, completed_at = ?
                            WHERE project_id = ? AND phase = ?
                        ''', (kwargs.get('status', 'in_progress'), kwargs.get('start_date'),
                              kwargs.get('end_date'), kwargs.get('description'),
                              kwargs.get('completed_at'), project_id, phase))
                    else:
                        cursor.execute('''
                            INSERT INTO project_phases (project_id, phase, phase_name, start_date, end_date, status, description, completed_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (project_id, phase, phase_config.get('name'), kwargs.get('start_date'),
                              kwargs.get('end_date'), kwargs.get('status', 'in_progress'),
                              kwargs.get('description'), kwargs.get('completed_at')))
                    cursor.execute('UPDATE innovation_projects SET status = ?, updated_at = ? WHERE project_id = ?',
                                  (phase, now, project_id))
                    conn.commit()
                    return {'success': True, 'phase': phase}
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
                                  (project_id, member_id, member_name, kwargs.get('role', 'member'), now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成员已加入项目'}
        except Exception as e:
            logger.error(f'添加项目成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_project_task(self, project_id: str, task_name: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"ptk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_tasks (task_id, project_id, task_name, description,
                                                   assignee_id, assignee_name, priority, status,
                                                   due_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (task_id, project_id, task_name, kwargs.get('description'),
                          kwargs.get('assignee_id'), kwargs.get('assignee_name'),
                          kwargs.get('priority', 'medium'), kwargs.get('due_date'), now))
                    conn.commit()
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'创建项目任务失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创新人才培养 ==========

    def register_talent(self, talent_name: str, education_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            talent_id = f"tal_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_talent (talent_id, talent_name, education_type,
                                                      email, phone, department, position,
                                                      status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (talent_id, talent_name, education_type, kwargs.get('email'),
                          kwargs.get('phone'), kwargs.get('department'),
                          kwargs.get('position'), now, now))
                    conn.commit()
                    logger.info(f'注册创新人才: {talent_name} ({talent_id})')
                    return {'success': True, 'talent_id': talent_id}
        except Exception as e:
            logger.error(f'注册创新人才失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_talent_profile(self, talent_id: str, role: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM talent_profiles WHERE talent_id = ? AND role = ?', (talent_id, role))
                    if cursor.fetchone():
                        cursor.execute('''
                            UPDATE talent_profiles SET expertise = ?, skills = ?, experience = ?, achievements = ?
                            WHERE talent_id = ? AND role = ?
                        ''', (kwargs.get('expertise'), kwargs.get('skills'),
                              kwargs.get('experience'), kwargs.get('achievements'),
                              talent_id, role))
                    else:
                        cursor.execute('''
                            INSERT INTO talent_profiles (talent_id, role, expertise, skills, experience, achievements)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (talent_id, role, kwargs.get('expertise'), kwargs.get('skills'),
                              kwargs.get('experience'), kwargs.get('achievements')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新人才档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_talent(self, talent_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            total_score = 0
            total_weight = 0
            for criterion, score in assessment_data.get('scores', {}).items():
                weight = ASSESSMENT_CRITERIA.get(criterion, {}).get('weight', 0.125)
                total_score += score * weight
                total_weight += weight
            avg_score = round(total_score / total_weight, 2) if total_weight > 0 else 0
            level = 'excellent' if avg_score >= 90 else ('good' if avg_score >= 80 else ('qualified' if avg_score >= 60 else 'needs_improvement'))
            return {'success': True, 'score': avg_score, 'level': level}
        except Exception as e:
            logger.error(f'人才评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_talent(self, education_type: str = None, role: str = None,
                    page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM innovation_talent WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                talent = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'talent': talent, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取人才列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 成果转化 ==========

    def register_result(self, project_id: str, result_name: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"irs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_results (result_id, project_id, result_name,
                                                        result_type, description,
                                                        intellectual_property, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (result_id, project_id, result_name, kwargs.get('result_type'),
                          kwargs.get('description'), kwargs.get('intellectual_property'), now))
                    conn.commit()
                    logger.info(f'登记创新成果: {result_name} ({result_id})')
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'登记创新成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_transformation_plan(self, result_id: str, transformation_mode: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO result_transformation (result_id, transformation_mode, partner,
                                                           agreement_date, value, status, progress)
                        VALUES (?, ?, ?, ?, ?, 'planning', 0)
                    ''', (result_id, transformation_mode, kwargs.get('partner'),
                          kwargs.get('agreement_date'), kwargs.get('value', 0)))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'创建转化计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_transformation_progress(self, transformation_id: int,
                                        progress: float, **kwargs) -> Dict[str, Any]:
        try:
            status = 'completed' if progress >= 100 else ('in_progress' if progress > 0 else 'planning')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE result_transformation SET progress = ?, status = ? WHERE id = ?',
                                  (progress, status, transformation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '转化记录不存在'}
        except Exception as e:
            logger.error(f'更新转化进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_results(self, project_id: str = None, status: str = None,
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM innovation_results WHERE 1=1'
                params = []
                if project_id:
                    query += ' AND project_id = ?'
                    params.append(project_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取成果列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资金管理 ==========

    def create_funding_application(self, project_id: str, funding_source: str,
                                    amount: float, **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"fap_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO funding_applications (application_id, project_id, funding_source,
                                                          amount, purpose, budget_plan, status,
                                                          review_comments, approved_amount, approved_at, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'submitted', NULL, NULL, NULL, ?)
                    ''', (application_id, project_id, funding_source, amount,
                          kwargs.get('purpose'), kwargs.get('budget_plan'), now))
                    conn.commit()
                    logger.info(f'创建资金申请: {application_id}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'创建资金申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_funding_application(self, application_id: str, approved: bool,
                                    **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE funding_applications SET status = ?, review_comments = ?,
                                                       approved_amount = ?, approved_at = ?
                        WHERE application_id = ?
                    ''', (status, kwargs.get('review_comments'),
                          kwargs.get('approved_amount'), now, application_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '资金申请不存在'}
        except Exception as e:
            logger.error(f'审核资金申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def allocate_funding(self, project_id: str, source: str, amount: float,
                         **kwargs) -> Dict[str, Any]:
        try:
            funding_id = f"fnd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO funding_management (funding_id, project_id, source, amount,
                                                        allocated_amount, used_amount, budget_details, status, created_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?, 'allocated', ?)
                    ''', (funding_id, project_id, source, amount, amount,
                          kwargs.get('budget_details'), now))
                    conn.commit()
                    return {'success': True, 'funding_id': funding_id}
        except Exception as e:
            logger.error(f'分配资金失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_funding_usage(self, funding_id: str, amount: float,
                             **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT used_amount, allocated_amount FROM funding_management WHERE funding_id = ?', (funding_id,))
                    funding = cursor.fetchone()
                    if not funding:
                        return {'success': False, 'error': '资金记录不存在'}
                    new_used = funding[0] + amount
                    if new_used > funding[1]:
                        return {'success': False, 'error': '使用金额超过分配额度'}
                    status = 'fully_used' if new_used >= funding[1] else 'in_use'
                    cursor.execute('UPDATE funding_management SET used_amount = ?, status = ? WHERE funding_id = ?',
                                  (new_used, status, funding_id))
                    conn.commit()
                    return {'success': True, 'remaining': funding[1] - new_used}
        except Exception as e:
            logger.error(f'记录资金使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_funding_summary(self, project_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT SUM(amount) as total, SUM(used_amount) as used FROM funding_management WHERE 1=1'
                params = []
                if project_id:
                    query += ' AND project_id = ?'
                    params.append(project_id)
                cursor.execute(query, params)
                summary = cursor.fetchone()
                total = summary['total'] or 0
                used = summary['used'] or 0
                return {'success': True, 'total': total, 'used': used, 'remaining': total - used}
        except Exception as e:
            logger.error(f'获取资金汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 平台建设 ==========

    def create_platform(self, platform_name: str, platform_type: str,
                        education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            platform_id = f"plt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_platforms (platform_id, platform_name, platform_type,
                                                          education_type, description, location,
                                                          capacity, current_users, status,
                                                          created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (platform_id, platform_name, platform_type, education_type,
                          kwargs.get('description'), kwargs.get('location'),
                          kwargs.get('capacity', 0), now, now))
                    conn.commit()
                    logger.info(f'创建创新平台: {platform_name} ({platform_id})')
                    return {'success': True, 'platform_id': platform_id}
        except Exception as e:
            logger.error(f'创建创新平台失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_platform_resource(self, platform_id: str, resource_name: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO platform_resources (platform_id, resource_name, resource_type, quantity, status)
                        VALUES (?, ?, ?, ?, 'available')
                    ''', (platform_id, resource_name, kwargs.get('resource_type'),
                          kwargs.get('quantity', 1)))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加平台资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_platform_status(self, platform_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE innovation_platforms SET status = ?, updated_at = ? WHERE platform_id = ?',
                                  (status, now, platform_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '平台不存在'}
        except Exception as e:
            logger.error(f'更新平台状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_platforms(self, education_type: str = None, platform_type: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM innovation_platforms WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if platform_type:
                    query += ' AND platform_type = ?'
                    params.append(platform_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                platforms = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'platforms': platforms, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取平台列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合作网络 ==========

    def create_cooperation_network(self, network_name: str, cooperation_type: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            network_id = f"cnw_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cooperation_networks (network_id, network_name, cooperation_type,
                                                           education_type, description, partner_count,
                                                           status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (network_id, network_name, cooperation_type, education_type,
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建合作网络: {network_name} ({network_id})')
                    return {'success': True, 'network_id': network_id}
        except Exception as e:
            logger.error(f'创建合作网络失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_cooperation_partner(self, network_id: str, partner_name: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cooperation_records (network_id, partner_name, partner_type,
                                                          cooperation_content, start_date, end_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'ongoing')
                    ''', (network_id, partner_name, kwargs.get('partner_type'),
                          kwargs.get('cooperation_content'), kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date')))
                    cursor.execute('UPDATE cooperation_networks SET partner_count = partner_count + 1, updated_at = ? WHERE network_id = ?',
                                  (now, network_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加合作方失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_cooperation_status(self, record_id: int, status: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE cooperation_records SET status = ? WHERE id = ?',
                                  (status, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '合作记录不存在'}
        except Exception as e:
            logger.error(f'更新合作状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_cooperation_networks(self, education_type: str = None,
                                  page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM cooperation_networks WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                networks = [dict(n) for n in cursor.fetchall()]
                return {'success': True, 'networks': networks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合作网络列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 评估体系 ==========

    def create_assessment(self, project_id: str, assessment_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"ast_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            criteria = json.dumps(list(ASSESSMENT_CRITERIA.keys()))
            weights = json.dumps({k: v.get('weight', 0.125) for k, v in ASSESSMENT_CRITERIA.items()})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO assessment_system (assessment_id, project_id, assessment_type,
                                                       criteria, weights, scheduled_date, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'scheduled', ?)
                    ''', (assessment_id, project_id, assessment_type, criteria, weights,
                          kwargs.get('scheduled_date'), now))
                    conn.commit()
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_assessment_scores(self, assessment_id: str, scores: Dict[str, float]) -> Dict[str, Any]:
        try:
            total_score = 0
            total_weight = 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for criterion, score in scores.items():
                        weight = ASSESSMENT_CRITERIA.get(criterion, {}).get('weight', 0.125)
                        total_score += score * weight
                        total_weight += weight
                        cursor.execute('INSERT INTO assessment_scores (assessment_id, criterion, score) VALUES (?, ?, ?)',
                                      (assessment_id, criterion, score))
                    avg_score = round(total_score / total_weight, 2) if total_weight > 0 else 0
                    cursor.execute('UPDATE assessment_system SET status = ? WHERE assessment_id = ?',
                                  ('completed', assessment_id))
                    conn.commit()
                    return {'success': True, 'overall_score': avg_score}
        except Exception as e:
            logger.error(f'记录评估分数失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_assessment_report(self, assessment_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM assessment_system WHERE assessment_id = ?', (assessment_id,))
                assessment = cursor.fetchone()
                if not assessment:
                    return {'success': False, 'error': '评估不存在'}
                cursor.execute('SELECT * FROM assessment_scores WHERE assessment_id = ?', (assessment_id,))
                scores = [dict(s) for s in cursor.fetchall()]
                total_score = sum(s['score'] * ASSESSMENT_CRITERIA.get(s['criterion'], {}).get('weight', 0.125) for s in scores)
                avg_score = round(total_score / len(scores), 2) if scores else 0
                recommendations = []
                for s in scores:
                    if s['score'] < 70:
                        recommendations.append(f"{ASSESSMENT_CRITERIA.get(s['criterion'], {}).get('name', s['criterion'])}需要改进")
                return {'success': True, 'assessment': dict(assessment), 'scores': scores,
                        'overall_score': avg_score, 'recommendations': recommendations}
        except Exception as e:
            logger.error(f'生成评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_assessments(self, project_id: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM assessment_system WHERE 1=1'
                params = []
                if project_id:
                    query += ' AND project_id = ?'
                    params.append(project_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                assessments = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assessments': assessments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评估列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创新文化 ==========

    def create_culture_program(self, culture_name: str, education_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            culture_id = f"cul_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_culture (culture_id, culture_name, education_type,
                                                        description, objectives, status,
                                                        created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (culture_id, culture_name, education_type, kwargs.get('description'),
                          kwargs.get('objectives'), now, now))
                    conn.commit()
                    logger.info(f'创建创新文化项目: {culture_name} ({culture_id})')
                    return {'success': True, 'culture_id': culture_id}
        except Exception as e:
            logger.error(f'创建创新文化项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_culture_initiative(self, culture_id: str, initiative_name: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO culture_initiatives (culture_id, initiative_name, description,
                                                          start_date, end_date, status)
                        VALUES (?, ?, ?, ?, ?, 'planned')
                    ''', (culture_id, initiative_name, kwargs.get('description'),
                          kwargs.get('start_date'), kwargs.get('end_date')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加文化活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_initiative_status(self, initiative_id: int, status: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE culture_initiatives SET status = ? WHERE id = ?',
                                  (status, initiative_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '活动不存在'}
        except Exception as e:
            logger.error(f'更新活动状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_culture_programs(self, education_type: str = None,
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM innovation_culture WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取文化项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 奖励管理 ==========

    def create_award(self, award_name: str, education_type: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            award_id = f"awd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_awards (award_id, award_name, education_type,
                                                        description, level, criteria, status,
                                                        created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (award_id, award_name, education_type, kwargs.get('description'),
                          kwargs.get('level', 'school'), kwargs.get('criteria'), now, now))
                    conn.commit()
                    logger.info(f'创建奖项: {award_name} ({award_id})')
                    return {'success': True, 'award_id': award_id}
        except Exception as e:
            logger.error(f'创建奖项失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_award_application(self, award_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO award_records (award_id, project_id, talent_id, applicant_name,
                                                   application_date, status, result, awarded_at)
                        VALUES (?, ?, ?, ?, ?, 'submitted', NULL, NULL)
                    ''', (award_id, kwargs.get('project_id'), kwargs.get('talent_id'),
                          kwargs.get('applicant_name'), now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'提交奖项申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_award_application(self, record_id: int, result: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'awarded' if result == 'win' else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE award_records SET status = ?, result = ?, awarded_at = ? WHERE id = ?',
                                  (status, result, now[:10] if result == 'win' else None, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '奖项申请记录不存在'}
        except Exception as e:
            logger.error(f'评审奖项申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_awards(self, education_type: str = None, status: str = None,
                    page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM innovation_awards WHERE 1=1'
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
                awards = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'awards': awards, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取奖项列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_innovation_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                filters = 'WHERE education_type = ?' if education_type else 'WHERE 1=1'
                params = [education_type] if education_type else []
                
                cursor.execute(f'SELECT COUNT(*) as count FROM innovation_projects {filters}', params)
                projects = cursor.fetchone()['count'] or 0
                
                cursor.execute(f'SELECT COUNT(*) as count FROM innovation_talent {filters}', params)
                talent = cursor.fetchone()['count'] or 0
                
                cursor.execute(f'SELECT COUNT(*) as count FROM innovation_results {filters}', params)
                results = cursor.fetchone()['count'] or 0
                
                cursor.execute(f'SELECT COUNT(*) as count FROM innovation_platforms {filters}', params)
                platforms = cursor.fetchone()['count'] or 0
                
                cursor.execute(f'SELECT COUNT(*) as count FROM cooperation_networks {filters}', params)
                networks = cursor.fetchone()['count'] or 0
                
                cursor.execute(f'SELECT SUM(amount) as total FROM funding_management', params)
                funding = cursor.fetchone()['total'] or 0
                
                cursor.execute(f'SELECT COUNT(*) as count FROM innovation_awards {filters}', params)
                awards = cursor.fetchone()['count'] or 0
                
                cursor.execute(f'SELECT COUNT(*) as count FROM assessment_system WHERE status = "completed"', params)
                assessments = cursor.fetchone()['count'] or 0
                
                return {
                    'success': True,
                    'education_type': education_type or 'all',
                    'summary': {
                        'total_projects': projects,
                        'total_talent': talent,
                        'total_results': results,
                        'total_platforms': platforms,
                        'total_networks': networks,
                        'total_funding': round(funding, 2),
                        'total_awards': awards,
                        'completed_assessments': assessments
                    }
                }
        except Exception as e:
            logger.error(f'获取创新统计汇总失败: {e}')
            return {'success': False, 'error': str(e)}