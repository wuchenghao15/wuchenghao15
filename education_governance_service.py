#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育治理与领导力服务 (v15.20.0)
====================================
提供教育治理、学校领导、战略规划、组织管理、决策支持、绩效评估、领导力发展、治理评估等综合管理服务。

核心能力：
1. 教育治理 - 治理结构、权力配置、制度建设、监督机制
2. 领导力 - 领导班子、角色配置、职责分工、能力评估
3. 战略规划 - 规划制定、目标分解、实施跟踪、评估调整
4. 组织管理 - 组织结构、部门设置、岗位配置、人员编制
5. 决策支持 - 决策流程、数据分析、风险评估、方案优化、决策执行
6. 绩效评估 - 指标体系、评估实施、结果分析、反馈改进
7. 领导力发展 - 培训规划、能力提升、轮岗锻炼、考核评价
8. 治理评估 - 治理水平、合规性、效能评估、改进建议
9. 合规检查 - 制度合规、政策落实、风险排查、整改跟踪
10. 统计分析 - 治理数据统计与分析
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_governance_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationGovernance')


# ========== 治理配置 ==========

GOVERNANCE_MODELS = {
    'principal_responsibility': {'name': '校长负责制', 'description': '校长全面负责学校行政工作', 'applicable': ['k12', 'adult']},
    'board_system': {'name': '董事会制', 'description': '董事会为最高决策机构', 'applicable': ['adult', 'k12']},
    'council_system': {'name': '理事会制', 'description': '理事会行使决策和监督职能', 'applicable': ['adult']},
    'committee_system': {'name': '委员会制', 'description': '各类委员会分工协作', 'applicable': ['k12', 'adult']},
    'joint_meeting': {'name': '联席会议', 'description': '多部门联合决策机制', 'applicable': ['k12', 'adult']},
    'democratic_management': {'name': '民主管理', 'description': '教职工参与民主管理', 'applicable': ['k12', 'adult']},
    'academic_committee': {'name': '学术委员会', 'description': '学术事务决策机构', 'applicable': ['adult']},
    'staff_representative': {'name': '教职工代表大会', 'description': '教职工民主权利保障', 'applicable': ['k12', 'adult']}
}

LEADERSHIP_ROLES = {
    'principal': {'name': '校长', 'level': 'top', 'applicable': ['k12', 'adult']},
    'vice_principal': {'name': '副校长', 'level': 'top', 'applicable': ['k12', 'adult']},
    'secretary': {'name': '书记', 'level': 'top', 'applicable': ['k12', 'adult']},
    'dean': {'name': '院长', 'level': 'middle', 'applicable': ['adult']},
    'department_head': {'name': '系主任', 'level': 'middle', 'applicable': ['adult']},
    'section_head': {'name': '部门负责人', 'level': 'middle', 'applicable': ['k12', 'adult']},
    'grade_group_leader': {'name': '年级组长', 'level': 'middle', 'applicable': ['k12']},
    'class_teacher': {'name': '班主任', 'level': 'grassroots', 'applicable': ['k12']}
}

STRATEGIC_OBJECTIVES = {
    'school_running': {'name': '办学目标', 'description': '办学定位与发展方向', 'applicable': ['k12', 'adult']},
    'quality': {'name': '质量目标', 'description': '教育教学质量提升', 'applicable': ['k12', 'adult']},
    'development': {'name': '发展目标', 'description': '学校整体发展规划', 'applicable': ['k12', 'adult']},
    'innovation': {'name': '创新目标', 'description': '教育创新与改革', 'applicable': ['k12', 'adult']},
    'international': {'name': '国际化目标', 'description': '国际交流与合作', 'applicable': ['adult']},
    'social_service': {'name': '社会服务目标', 'description': '服务社会与地方发展', 'applicable': ['k12', 'adult']}
}

ORGANIZATION_STRUCTURE = {
    'line_function': {'name': '直线职能制', 'description': '垂直管理与职能分工', 'applicable': ['k12', 'adult']},
    'divisional': {'name': '事业部制', 'description': '按业务单元划分', 'applicable': ['adult']},
    'matrix': {'name': '矩阵制', 'description': '双重领导与项目管理', 'applicable': ['adult']},
    'flat': {'name': '扁平化', 'description': '减少层级提高效率', 'applicable': ['k12', 'adult']},
    'network': {'name': '网络化', 'description': '跨组织协作网络', 'applicable': ['adult']},
    'virtual': {'name': '虚拟组织', 'description': '灵活协作模式', 'applicable': ['adult']},
    'hybrid': {'name': '混合结构', 'description': '多种结构结合', 'applicable': ['k12', 'adult']}
}

DECISION_PROCESSES = {
    'democratic': {'name': '民主决策', 'description': '广泛征求意见', 'applicable': ['k12', 'adult']},
    'scientific': {'name': '科学决策', 'description': '基于数据分析', 'applicable': ['k12', 'adult']},
    'collective': {'name': '集体决策', 'description': '领导班子集体研究', 'applicable': ['k12', 'adult']},
    'individual': {'name': '个人决策', 'description': '负责人独立决策', 'applicable': ['k12', 'adult']},
    'procedural': {'name': '程序化决策', 'description': '按既定流程决策', 'applicable': ['k12', 'adult']},
    'non_procedural': {'name': '非程序化决策', 'description': '灵活应对特殊情况', 'applicable': ['k12', 'adult']}
}

PERFORMANCE_DIMENSIONS = {
    'school_running': {'name': '办学绩效', 'description': '办学水平与效益', 'applicable': ['k12', 'adult']},
    'teaching': {'name': '教学绩效', 'description': '教学质量与效果', 'applicable': ['k12', 'adult']},
    'research': {'name': '科研绩效', 'description': '科研成果与创新', 'applicable': ['adult']},
    'management': {'name': '管理绩效', 'description': '管理效率与规范', 'applicable': ['k12', 'adult']},
    'social': {'name': '社会绩效', 'description': '社会贡献与影响', 'applicable': ['k12', 'adult']},
    'development': {'name': '发展绩效', 'description': '可持续发展能力', 'applicable': ['k12', 'adult']}
}

LEADERSHIP_COMPETENCIES = {
    'strategic_thinking': {'name': '战略思维', 'description': '宏观视野与长远规划', 'weight': 0.15},
    'change_leadership': {'name': '变革领导力', 'description': '推动改革与创新', 'weight': 0.15},
    'communication': {'name': '沟通能力', 'description': '有效沟通与协调', 'weight': 0.12},
    'team_building': {'name': '团队建设', 'description': '团队凝聚力与协作', 'weight': 0.12},
    'decision_making': {'name': '决策能力', 'description': '科学决策与判断', 'weight': 0.15},
    'innovation': {'name': '创新能力', 'description': '开拓创新与突破', 'weight': 0.12},
    'emotional_intelligence': {'name': '情商', 'description': '情绪管理与人际关系', 'weight': 0.1},
    'execution': {'name': '执行力', 'description': '落实能力与成效', 'weight': 0.19}
}

GOVERNANCE_INDICATORS = {
    'structure': {'name': '治理结构', 'description': '组织架构与权责配置', 'weight': 0.12},
    'decision_mechanism': {'name': '决策机制', 'description': '决策流程与科学性', 'weight': 0.14},
    'power_check': {'name': '权力制衡', 'description': '权力监督与制约', 'weight': 0.12},
    'supervision': {'name': '监督机制', 'description': '监督体系与效能', 'weight': 0.13},
    'democratic_participation': {'name': '民主参与', 'description': '教职工民主权利', 'weight': 0.12},
    'information_disclosure': {'name': '信息公开', 'description': '校务公开透明度', 'weight': 0.13},
    'accountability': {'name': '问责机制', 'description': '责任追究与落实', 'weight': 0.12},
    'performance_evaluation': {'name': '绩效评估', 'description': '评估体系与应用', 'weight': 0.12}
}


class EducationGovernanceService:
    """教育治理与领导力服务"""

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
                    CREATE TABLE IF NOT EXISTS governance_structure (
                        structure_id TEXT PRIMARY KEY,
                        structure_name TEXT NOT NULL,
                        governance_model TEXT,
                        education_type TEXT,
                        description TEXT,
                        effective_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS governance_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        structure_id TEXT NOT NULL,
                        member_id INTEGER,
                        member_name TEXT,
                        role TEXT,
                        term_start TEXT,
                        term_end TEXT,
                        status TEXT DEFAULT 'active',
                        UNIQUE(structure_id, member_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strategic_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        education_type TEXT,
                        start_year INTEGER,
                        end_year INTEGER,
                        vision TEXT,
                        mission TEXT,
                        objectives TEXT,
                        status TEXT DEFAULT 'draft',
                        approved_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plan_objectives (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT NOT NULL,
                        objective_type TEXT,
                        objective_name TEXT,
                        target_value TEXT,
                        baseline_value TEXT,
                        responsible_unit TEXT,
                        timeline TEXT,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'pending'
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leadership_team (
                        team_id TEXT PRIMARY KEY,
                        team_name TEXT NOT NULL,
                        education_type TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        description TEXT,
                        established_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leadership_roles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team_id TEXT NOT NULL,
                        role_code TEXT,
                        role_name TEXT,
                        person_id INTEGER,
                        person_name TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        responsibilities TEXT,
                        status TEXT DEFAULT 'active'
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS organization_chart (
                        chart_id TEXT PRIMARY KEY,
                        chart_name TEXT NOT NULL,
                        structure_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        version INTEGER DEFAULT 1,
                        effective_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS organizational_units (
                        unit_id TEXT PRIMARY KEY,
                        chart_id TEXT NOT NULL,
                        unit_name TEXT NOT NULL,
                        parent_unit_id TEXT,
                        unit_type TEXT,
                        head_id INTEGER,
                        head_name TEXT,
                        staff_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS decision_records (
                        decision_id TEXT PRIMARY KEY,
                        decision_title TEXT NOT NULL,
                        education_type TEXT,
                        decision_type TEXT,
                        decision_process TEXT,
                        related_units TEXT,
                        content TEXT,
                        decision_makers TEXT,
                        decision_date TEXT,
                        status TEXT DEFAULT 'proposed',
                        implementation_status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS decision_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        decision_id TEXT NOT NULL,
                        analysis_type TEXT,
                        analysis_content TEXT,
                        risk_level TEXT,
                        recommendations TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_evaluation (
                        eval_id TEXT PRIMARY KEY,
                        eval_name TEXT NOT NULL,
                        education_type TEXT,
                        eval_period TEXT,
                        eval_dimensions TEXT,
                        target_unit TEXT,
                        target_type TEXT,
                        status TEXT DEFAULT 'planning',
                        start_date TEXT,
                        end_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        eval_id TEXT NOT NULL,
                        evaluated_unit TEXT,
                        dimension TEXT,
                        score REAL,
                        weight REAL,
                        weighted_score REAL,
                        comments TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leadership_development (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        education_type TEXT,
                        target_role TEXT,
                        program_type TEXT,
                        duration INTEGER,
                        description TEXT,
                        capacity_builder TEXT,
                        status TEXT DEFAULT 'planning',
                        start_date TEXT,
                        end_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS development_programs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        program_id TEXT NOT NULL,
                        person_id INTEGER,
                        person_name TEXT,
                        competency TEXT,
                        current_level REAL,
                        target_level REAL,
                        activities TEXT,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        completed_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS governance_assessment (
                        assessment_id TEXT PRIMARY KEY,
                        assessment_name TEXT NOT NULL,
                        education_type TEXT,
                        assessment_period TEXT,
                        indicators TEXT,
                        methodology TEXT,
                        status TEXT DEFAULT 'planning',
                        start_date TEXT,
                        end_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        assessment_id TEXT NOT NULL,
                        indicator TEXT,
                        score REAL,
                        weight REAL,
                        weighted_score REAL,
                        rating TEXT,
                        improvement_suggestions TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS governance_compliance (
                        compliance_id TEXT PRIMARY KEY,
                        compliance_name TEXT NOT NULL,
                        education_type TEXT,
                        compliance_category TEXT,
                        related_policy TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        deadline TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        compliance_id TEXT NOT NULL,
                        check_item TEXT,
                        is_compliant INTEGER DEFAULT 0,
                        findings TEXT,
                        corrective_actions TEXT,
                        responsible_person TEXT,
                        status TEXT DEFAULT 'pending',
                        verified_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS board_meetings (
                        meeting_id TEXT PRIMARY KEY,
                        meeting_name TEXT NOT NULL,
                        education_type TEXT,
                        meeting_type TEXT,
                        structure_id TEXT,
                        date TEXT,
                        time TEXT,
                        location TEXT,
                        agenda TEXT,
                        attendees TEXT,
                        status TEXT DEFAULT 'scheduled',
                        minutes_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meeting_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id TEXT NOT NULL,
                        agenda_item TEXT,
                        discussion_content TEXT,
                        resolution TEXT,
                        action_items TEXT,
                        responsible_party TEXT,
                        deadline TEXT,
                        status TEXT DEFAULT 'pending'
                    )
                ''')
                conn.commit()
                logger.info('教育治理与领导力服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 教育治理 ==========

    def create_governance_structure(self, structure_name: str, governance_model: str,
                                    education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            structure_id = f"gov_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO governance_structure (
                            structure_id, structure_name, governance_model,
                            education_type, description, effective_date, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (structure_id, structure_name, governance_model,
                          education_type, kwargs.get('description'),
                          kwargs.get('effective_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'创建治理结构: {structure_name} ({structure_id})')
                    return {'success': True, 'structure_id': structure_id}
        except Exception as e:
            logger.error(f'创建治理结构失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_governance_member(self, structure_id: str, member_id: int,
                              member_name: str, role: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO governance_members '
                                   '(structure_id, member_id, member_name, role, term_start, term_end, status) '
                                   'VALUES (?, ?, ?, ?, ?, ?, \'active\')',
                                  (structure_id, member_id, member_name, role,
                                   kwargs.get('term_start', datetime.now().strftime('%Y-%m-%d')),
                                   kwargs.get('term_end')))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成员已在该治理结构中'}
        except Exception as e:
            logger.error(f'添加治理成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_governance_structure(self, structure_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM governance_structure WHERE structure_id = ?', (structure_id,))
                structure = cursor.fetchone()
                if structure:
                    cursor.execute('SELECT * FROM governance_members WHERE structure_id = ? AND status = ?',
                                  (structure_id, 'active'))
                    members = [dict(m) for m in cursor.fetchall()]
                    return {'success': True, 'structure': dict(structure), 'members': members}
                return {'success': False, 'error': '治理结构不存在'}
        except Exception as e:
            logger.error(f'获取治理结构失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_governance_structures(self, education_type: str = None,
                                   status: str = 'active', page: int = 1,
                                   page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM governance_structure WHERE 1=1'
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
                structures = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'structures': structures, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取治理结构列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 领导力 ==========

    def create_leadership_team(self, team_name: str, education_type: str,
                               leader_id: int, leader_name: str, **kwargs) -> Dict[str, Any]:
        try:
            team_id = f"ldt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO leadership_team (
                            team_id, team_name, education_type, leader_id,
                            leader_name, description, established_date, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (team_id, team_name, education_type, leader_id,
                          leader_name, kwargs.get('description'),
                          kwargs.get('established_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'创建领导班子: {team_name} ({team_id})')
                    return {'success': True, 'team_id': team_id}
        except Exception as e:
            logger.error(f'创建领导班子失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_leadership_role(self, team_id: str, role_code: str,
                               person_id: int, person_name: str, **kwargs) -> Dict[str, Any]:
        try:
            config = LEADERSHIP_ROLES.get(role_code, {})
            role_name = config.get('name', role_code)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO leadership_roles (
                            team_id, role_code, role_name, person_id,
                            person_name, start_date, end_date, responsibilities, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
                    ''', (team_id, role_code, role_name, person_id,
                          person_name, kwargs.get('start_date', datetime.now().strftime('%Y-%m-%d')),
                          kwargs.get('end_date'), kwargs.get('responsibilities')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配领导角色失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_leadership_team(self, team_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM leadership_team WHERE team_id = ?', (team_id,))
                team = cursor.fetchone()
                if team:
                    cursor.execute('SELECT * FROM leadership_roles WHERE team_id = ? AND status = ?',
                                  (team_id, 'active'))
                    roles = [dict(r) for r in cursor.fetchall()]
                    return {'success': True, 'team': dict(team), 'roles': roles}
                return {'success': False, 'error': '领导班子不存在'}
        except Exception as e:
            logger.error(f'获取领导班子失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_leadership_competency(self, team_id: str, person_id: int,
                                        competencies: Dict[str, float]) -> Dict[str, Any]:
        try:
            total_score = 0.0
            total_weight = 0.0
            for code, score in competencies.items():
                config = LEADERSHIP_COMPETENCIES.get(code)
                if config:
                    weight = config.get('weight', 0.125)
                    total_score += score * weight
                    total_weight += weight
            avg_score = round(total_score / total_weight, 2) if total_weight > 0 else 0
            level = '卓越' if avg_score >= 90 else ('优秀' if avg_score >= 80 else ('良好' if avg_score >= 70 else ('合格' if avg_score >= 60 else '待提升')))
            return {'success': True, 'total_score': avg_score, 'level': level, 'competencies': competencies}
        except Exception as e:
            logger.error(f'领导力评估失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 战略规划 ==========

    def create_strategic_plan(self, plan_name: str, education_type: str,
                              start_year: int, end_year: int, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"spn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO strategic_plans (
                            plan_id, plan_name, education_type, start_year,
                            end_year, vision, mission, objectives, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (plan_id, plan_name, education_type, start_year,
                          end_year, kwargs.get('vision'), kwargs.get('mission'),
                          json.dumps(kwargs.get('objectives', [])), now, now))
                    conn.commit()
                    logger.info(f'创建战略规划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建战略规划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_plan_objective(self, plan_id: str, objective_type: str,
                           objective_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO plan_objectives (
                            plan_id, objective_type, objective_name, target_value,
                            baseline_value, responsible_unit, timeline, progress, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'pending')
                    ''', (plan_id, objective_type, objective_name,
                          kwargs.get('target_value'), kwargs.get('baseline_value'),
                          kwargs.get('responsible_unit'), kwargs.get('timeline')))
                    conn.commit()
                    return {'success': True, 'objective_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加规划目标失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_objective_progress(self, objective_id: int, progress: float) -> Dict[str, Any]:
        try:
            progress = max(0, min(100, progress))
            status = 'completed' if progress >= 100 else ('in_progress' if progress > 0 else 'pending')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE plan_objectives SET progress = ?, status = ? WHERE id = ?',
                                  (progress, status, objective_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress, 'status': status}
                    return {'success': False, 'error': '目标不存在'}
        except Exception as e:
            logger.error(f'更新目标进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_strategic_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE strategic_plans SET status = ?, approved_at = ?, updated_at = ? WHERE plan_id = ? AND status = ?',
                                  ('approved', now, now, plan_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '规划状态不允许审批'}
        except Exception as e:
            logger.error(f'审批战略规划失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 组织管理 ==========

    def create_organization_chart(self, chart_name: str, structure_type: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            chart_id = f"org_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO organization_chart (
                            chart_id, chart_name, structure_type, education_type,
                            description, version, effective_date, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 1, ?, 'active', ?, ?)
                    ''', (chart_id, chart_name, structure_type, education_type,
                          kwargs.get('description'), kwargs.get('effective_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'创建组织结构图: {chart_name} ({chart_id})')
                    return {'success': True, 'chart_id': chart_id}
        except Exception as e:
            logger.error(f'创建组织结构图失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_organizational_unit(self, chart_id: str, unit_name: str,
                                unit_type: str, **kwargs) -> Dict[str, Any]:
        try:
            unit_id = f"ou_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO organizational_units (
                            unit_id, chart_id, unit_name, parent_unit_id,
                            unit_type, head_id, head_name, staff_count,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (unit_id, chart_id, unit_name, kwargs.get('parent_unit_id'),
                          unit_type, kwargs.get('head_id'), kwargs.get('head_name'),
                          kwargs.get('staff_count', 0), kwargs.get('description'), now, now))
                    conn.commit()
                    return {'success': True, 'unit_id': unit_id}
        except Exception as e:
            logger.error(f'添加组织单元失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_organization_chart(self, chart_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM organization_chart WHERE chart_id = ?', (chart_id,))
                chart = cursor.fetchone()
                if chart:
                    cursor.execute('SELECT * FROM organizational_units WHERE chart_id = ? AND status = ?',
                                  (chart_id, 'active'))
                    units = [dict(u) for u in cursor.fetchall()]
                    return {'success': True, 'chart': dict(chart), 'units': units}
                return {'success': False, 'error': '组织结构图不存在'}
        except Exception as e:
            logger.error(f'获取组织结构图失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_unit_head(self, unit_id: str, head_id: int, head_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE organizational_units SET head_id = ?, head_name = ?, updated_at = ? WHERE unit_id = ?',
                                  (head_id, head_name, now, unit_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '组织单元不存在'}
        except Exception as e:
            logger.error(f'更新单元负责人失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 决策支持 ==========

    def create_decision(self, decision_title: str, education_type: str,
                        decision_type: str, decision_process: str, **kwargs) -> Dict[str, Any]:
        try:
            decision_id = f"dcs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO decision_records (
                            decision_id, decision_title, education_type,
                            decision_type, decision_process, related_units,
                            content, decision_makers, decision_date, status,
                            implementation_status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', 'pending', ?, ?)
                    ''', (decision_id, decision_title, education_type,
                          decision_type, decision_process,
                          json.dumps(kwargs.get('related_units', [])),
                          kwargs.get('content'),
                          json.dumps(kwargs.get('decision_makers', [])),
                          kwargs.get('decision_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'创建决策记录: {decision_title} ({decision_id})')
                    return {'success': True, 'decision_id': decision_id}
        except Exception as e:
            logger.error(f'创建决策记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_decision_analysis(self, decision_id: str, analysis_type: str,
                              analysis_content: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO decision_analysis (
                            decision_id, analysis_type, analysis_content,
                            risk_level, recommendations, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (decision_id, analysis_type, analysis_content,
                          kwargs.get('risk_level', 'medium'),
                          kwargs.get('recommendations'), datetime.now().isoformat()))
                    conn.commit()
                    return {'success': True, 'analysis_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加决策分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_decision(self, decision_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE decision_records SET status = ?, updated_at = ? WHERE decision_id = ? AND status = ?',
                                  ('approved', now, decision_id, 'proposed'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '决策状态不允许审批'}
        except Exception as e:
            logger.error(f'审批决策失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_decision_implementation(self, decision_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE decision_records SET implementation_status = ?, updated_at = ? WHERE decision_id = ?',
                                  (status, now, decision_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '决策记录不存在'}
        except Exception as e:
            logger.error(f'更新决策执行状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_decision_analytics(self, education_type: str = None,
                               period: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) as total, status, implementation_status FROM decision_records WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if period:
                    query += ' AND decision_date LIKE ?'
                    params.append(f"{period}%")
                query += ' GROUP BY status, implementation_status'
                cursor.execute(query, params)
                stats = cursor.fetchall()
                return {'success': True, 'analytics': [{'total': s[0], 'status': s[1], 'implementation_status': s[2]} for s in stats]}
        except Exception as e:
            logger.error(f'获取决策分析数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 绩效评估 ==========

    def create_performance_evaluation(self, eval_name: str, education_type: str,
                                       eval_period: str, **kwargs) -> Dict[str, Any]:
        try:
            eval_id = f"pev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO performance_evaluation (
                            eval_id, eval_name, education_type, eval_period,
                            eval_dimensions, target_unit, target_type, status,
                            start_date, end_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, ?, ?)
                    ''', (eval_id, eval_name, education_type, eval_period,
                          json.dumps(kwargs.get('eval_dimensions', [])),
                          kwargs.get('target_unit'), kwargs.get('target_type'),
                          kwargs.get('start_date'), kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建绩效评估: {eval_name} ({eval_id})')
                    return {'success': True, 'eval_id': eval_id}
        except Exception as e:
            logger.error(f'创建绩效评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_evaluation_result(self, eval_id: str, evaluated_unit: str,
                                  dimension: str, score: float, **kwargs) -> Dict[str, Any]:
        try:
            dim_config = PERFORMANCE_DIMENSIONS.get(dimension, {})
            weight = kwargs.get('weight', 0.1667)
            weighted_score = round(score * weight, 2)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_results (
                            eval_id, evaluated_unit, dimension, score,
                            weight, weighted_score, comments, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (eval_id, evaluated_unit, dimension, score,
                          weight, weighted_score, kwargs.get('comments'),
                          datetime.now().isoformat()))
                    conn.commit()
                    return {'success': True, 'result_id': cursor.lastrowid, 'weighted_score': weighted_score}
        except Exception as e:
            logger.error(f'提交评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_evaluation_summary(self, eval_id: str, evaluated_unit: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT SUM(weighted_score), SUM(weight) FROM evaluation_results WHERE eval_id = ? AND evaluated_unit = ?',
                              (eval_id, evaluated_unit))
                result = cursor.fetchone()
                if result and result[1] and result[1] > 0:
                    total_score = round(result[0] / result[1], 2)
                    grade = 'A' if total_score >= 90 else ('B' if total_score >= 80 else ('C' if total_score >= 70 else ('D' if total_score >= 60 else 'E')))
                    return {'success': True, 'total_score': total_score, 'grade': grade}
                return {'success': False, 'error': '未找到评估结果'}
        except Exception as e:
            logger.error(f'计算评估汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_results(self, eval_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_results WHERE eval_id = ?', (eval_id,))
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results}
        except Exception as e:
            logger.error(f'获取评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 领导力发展 ==========

    def create_development_program(self, program_name: str, education_type: str,
                                    target_role: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"ldp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO leadership_development (
                            program_id, program_name, education_type,
                            target_role, program_type, duration, description,
                            capacity_builder, status, start_date, end_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, ?, ?)
                    ''', (program_id, program_name, education_type, target_role,
                          kwargs.get('program_type'), kwargs.get('duration', 12),
                          kwargs.get('description'), kwargs.get('capacity_builder'),
                          kwargs.get('start_date'), kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建领导力发展项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建领导力发展项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_in_development(self, program_id: str, person_id: int,
                               person_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO development_programs (
                            program_id, person_id, person_name, competency,
                            current_level, target_level, activities, progress, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'active')
                    ''', (program_id, person_id, person_name,
                          kwargs.get('competency'), kwargs.get('current_level', 0),
                          kwargs.get('target_level', 100), kwargs.get('activities')))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'报名领导力发展项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_development_progress(self, record_id: int, progress: float) -> Dict[str, Any]:
        try:
            progress = max(0, min(100, progress))
            status = 'completed' if progress >= 100 else 'active'
            completed_at = datetime.now().strftime('%Y-%m-%d') if progress >= 100 else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE development_programs SET progress = ?, status = ?, completed_at = ? WHERE id = ?',
                                  (progress, status, completed_at, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress, 'status': status}
                    return {'success': False, 'error': '发展记录不存在'}
        except Exception as e:
            logger.error(f'更新发展进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_development_effectiveness(self, program_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as total, AVG(progress) as avg_progress, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as completed FROM development_programs WHERE program_id = ?',
                              ('completed', program_id))
                result = cursor.fetchone()
                if result:
                    effectiveness = round(result[1] / 100 * 100, 2) if result[1] else 0
                    return {'success': True, 'total_participants': result[0], 'avg_progress': round(result[1], 2) if result[1] else 0, 'completed_count': result[2], 'effectiveness': effectiveness}
                return {'success': False, 'error': '未找到发展项目记录'}
        except Exception as e:
            logger.error(f'评估发展项目效果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 治理评估 ==========

    def create_governance_assessment(self, assessment_name: str, education_type: str,
                                      assessment_period: str, **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"gas_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO governance_assessment (
                            assessment_id, assessment_name, education_type,
                            assessment_period, indicators, methodology, status,
                            start_date, end_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'planning', ?, ?, ?, ?)
                    ''', (assessment_id, assessment_name, education_type, assessment_period,
                          json.dumps(kwargs.get('indicators', [])), kwargs.get('methodology'),
                          kwargs.get('start_date'), kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建治理评估: {assessment_name} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建治理评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_assessment_result(self, assessment_id: str, indicator: str,
                                  score: float, **kwargs) -> Dict[str, Any]:
        try:
            ind_config = GOVERNANCE_INDICATORS.get(indicator, {})
            weight = kwargs.get('weight', ind_config.get('weight', 0.125))
            weighted_score = round(score * weight, 2)
            rating = '优秀' if score >= 90 else ('良好' if score >= 80 else ('合格' if score >= 70 else ('基本合格' if score >= 60 else '不合格')))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO assessment_results (
                            assessment_id, indicator, score, weight,
                            weighted_score, rating, improvement_suggestions, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (assessment_id, indicator, score, weight, weighted_score,
                          rating, kwargs.get('improvement_suggestions'), datetime.now().isoformat()))
                    conn.commit()
                    return {'success': True, 'result_id': cursor.lastrowid, 'rating': rating}
        except Exception as e:
            logger.error(f'提交评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_assessment_overall(self, assessment_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT SUM(weighted_score), SUM(weight) FROM assessment_results WHERE assessment_id = ?',
                              (assessment_id,))
                result = cursor.fetchone()
                if result and result[1] and result[1] > 0:
                    total_score = round(result[0] / result[1], 2)
                    level = '优秀' if total_score >= 90 else ('良好' if total_score >= 80 else ('合格' if total_score >= 70 else ('基本合格' if total_score >= 60 else '不合格')))
                    return {'success': True, 'overall_score': total_score, 'level': level}
                return {'success': False, 'error': '未找到评估结果'}
        except Exception as e:
            logger.error(f'计算综合评估得分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_assessment_report(self, assessment_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM governance_assessment WHERE assessment_id = ?', (assessment_id,))
                assessment = cursor.fetchone()
                if not assessment:
                    return {'success': False, 'error': '评估不存在'}
                cursor.execute('SELECT * FROM assessment_results WHERE assessment_id = ?', (assessment_id,))
                results = [dict(r) for r in cursor.fetchall()]
                overall = self.calculate_assessment_overall(assessment_id)
                return {'success': True, 'assessment': dict(assessment), 'results': results, 'overall': overall.get('overall_score'), 'level': overall.get('level')}
        except Exception as e:
            logger.error(f'获取评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合规检查 ==========

    def create_compliance_item(self, compliance_name: str, education_type: str,
                                compliance_category: str, **kwargs) -> Dict[str, Any]:
        try:
            compliance_id = f"cpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO governance_compliance (
                            compliance_id, compliance_name, education_type,
                            compliance_category, related_policy, description,
                            status, deadline, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (compliance_id, compliance_name, education_type,
                          compliance_category, kwargs.get('related_policy'),
                          kwargs.get('description'), kwargs.get('deadline'), now, now))
                    conn.commit()
                    logger.info(f'创建合规检查项: {compliance_name} ({compliance_id})')
                    return {'success': True, 'compliance_id': compliance_id}
        except Exception as e:
            logger.error(f'创建合规检查项失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_compliance_check(self, compliance_id: str, check_item: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO compliance_checks (
                            compliance_id, check_item, is_compliant, findings,
                            corrective_actions, responsible_person, status
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
                    ''', (compliance_id, check_item, kwargs.get('is_compliant', 0),
                          kwargs.get('findings'), kwargs.get('corrective_actions'),
                          kwargs.get('responsible_person')))
                    conn.commit()
                    return {'success': True, 'check_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加合规检查项失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_compliance_status(self, compliance_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE governance_compliance SET status = ?, updated_at = ? WHERE compliance_id = ?',
                                  (status, now, compliance_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '合规项不存在'}
        except Exception as e:
            logger.error(f'更新合规状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_compliance_check(self, check_id: int, is_compliant: bool, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE compliance_checks SET is_compliant = ?, status = ?, verified_at = ?, findings = ?, corrective_actions = ? WHERE id = ?',
                                  (1 if is_compliant else 0, 'verified' if is_compliant else 'non_compliant',
                                   datetime.now().strftime('%Y-%m-%d'), kwargs.get('findings'),
                                   kwargs.get('corrective_actions'), check_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '检查项不存在'}
        except Exception as e:
            logger.error(f'验证合规检查失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_governance_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                params = []
                where_clause = ''
                if education_type:
                    where_clause = ' WHERE education_type = ?'
                    params.append(education_type)
                
                cursor.execute(f'SELECT COUNT(*) FROM governance_structure{where_clause}', params)
                structure_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM leadership_team{where_clause}', params)
                team_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM strategic_plans{where_clause}', params)
                plan_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM organization_chart{where_clause}', params)
                org_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM decision_records{where_clause}', params)
                decision_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM performance_evaluation{where_clause}', params)
                eval_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM governance_compliance{where_clause}', params)
                compliance_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM board_meetings{where_clause}', params)
                meeting_count = cursor.fetchone()[0]
                
                return {
                    'success': True,
                    'statistics': {
                        'governance_structures': structure_count,
                        'leadership_teams': team_count,
                        'strategic_plans': plan_count,
                        'organization_charts': org_count,
                        'decisions': decision_count,
                        'performance_evaluations': eval_count,
                        'compliance_items': compliance_count,
                        'board_meetings': meeting_count
                    }
                }
        except Exception as e:
            logger.error(f'获取治理统计数据失败: {e}')
            return {'success': False, 'error': str(e)}