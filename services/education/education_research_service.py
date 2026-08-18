from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育科研管理服务 (v15.26.0) ==================================== 提供科研项目、团队、经费、成果、平台、合作、评价和信息等综合管理服务。  核心能力： 1. 科研项目 - 项目申报、立项管理、进度跟踪、结题验收 2. 科研团队 - 团队组建、成员管理、角色分配、绩效评估 3. 科研经费 - 经费预算、支出管理、报销审批、决算报告 4. 科研成果 - 成果登记、专利申报、论文发表、成果转化 5. 科研平台 - 平台建设、资源管理、开放共享、考核评估 6. 科研合作 - 合作洽谈、协议签署、联合研究、成果共享 7. 科研评价 - 评价指标、专家评审、结果公示、反馈改进 8. 科研信息 - 信息发布、数据统计、报表生成、决策支持  差异化支持：成人教育 / K12教育 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_research_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationResearch')


# ========== 科研配置 ==========

PROJECT_TYPES = {
    'national': {'name': '国家级项目', 'funding_level': 'high', 'approval_cycle': 6},
    'provincial': {'name': '省部级项目', 'funding_level': 'medium', 'approval_cycle': 4},
    'municipal': {'name': '市级项目', 'funding_level': 'medium', 'approval_cycle': 3},
    'institutional': {'name': '校级项目', 'funding_level': 'low', 'approval_cycle': 2},
    'horizontal': {'name': '横向项目', 'funding_level': 'variable', 'approval_cycle': 1},
    'vertical': {'name': '纵向项目', 'funding_level': 'medium', 'approval_cycle': 4},
    'international': {'name': '国际合作', 'funding_level': 'high', 'approval_cycle': 8},
    'industry': {'name': '产学研合作', 'funding_level': 'variable', 'approval_cycle': 2}
}

TEAM_ROLES = {
    'principal': {'name': '项目负责人', 'responsibility': '全面负责项目实施', 'weight': 1.0},
    'main_member': {'name': '主要成员', 'responsibility': '核心研究工作', 'weight': 0.7},
    'participant': {'name': '参与成员', 'responsibility': '辅助研究工作', 'weight': 0.3},
    'advisor': {'name': '顾问', 'responsibility': '专业指导咨询', 'weight': 0.2},
    'tech_advisor': {'name': '技术顾问', 'responsibility': '技术方案指导', 'weight': 0.25},
    'finance': {'name': '财务负责人', 'responsibility': '经费管理监督', 'weight': 0.15},
    'secretary': {'name': '秘书', 'responsibility': '文档资料管理', 'weight': 0.1},
    'reviewer': {'name': '评审专家', 'responsibility': '项目评审评估', 'weight': 0.1}
}

FUNDING_SOURCES = {
    'government': {'name': '政府资助', 'tax_deductible': True, 'report_required': True},
    'enterprise': {'name': '企业资助', 'tax_deductible': True, 'report_required': True},
    'research': {'name': '科研经费', 'tax_deductible': True, 'report_required': True},
    'donation': {'name': '社会捐赠', 'tax_deductible': True, 'report_required': False},
    'international': {'name': '国际资助', 'tax_deductible': False, 'report_required': True},
    'self_raised': {'name': '自筹资金', 'tax_deductible': False, 'report_required': False},
    'cooperation': {'name': '合作经费', 'tax_deductible': True, 'report_required': True},
    'special': {'name': '专项经费', 'tax_deductible': True, 'report_required': True}
}

ACHIEVEMENT_TYPES = {
    'paper': {'name': '论文', 'evaluation_weight': 1.0, 'indexed': ['SCI', 'EI', 'CSSCI', '核心期刊']},
    'book': {'name': '著作', 'evaluation_weight': 1.5, 'indexed': ['国家级出版社', '省级出版社']},
    'patent': {'name': '专利', 'evaluation_weight': 2.0, 'indexed': ['发明专利', '实用新型', '外观设计']},
    'software': {'name': '软件著作权', 'evaluation_weight': 0.8, 'indexed': ['计算机软件']},
    'invention': {'name': '技术发明', 'evaluation_weight': 2.5, 'indexed': ['国家级', '省部级']},
    'standard': {'name': '标准制定', 'evaluation_weight': 1.8, 'indexed': ['国家标准', '行业标准', '地方标准']},
    'transformation': {'name': '成果转化', 'evaluation_weight': 3.0, 'indexed': ['产业化', '技术转让']},
    'award': {'name': '获奖成果', 'evaluation_weight': 2.0, 'indexed': ['国家级', '省部级', '市级']}
}

PLATFORM_TYPES = {
    'key_lab': {'name': '重点实验室', 'level': 'national', 'requirement': 'high'},
    'engineering_center': {'name': '工程研究中心', 'level': 'provincial', 'requirement': 'medium'},
    'innovation_platform': {'name': '创新平台', 'level': 'municipal', 'requirement': 'medium'},
    'industry_base': {'name': '产学研基地', 'level': 'institutional', 'requirement': 'low'},
    'research_team': {'name': '科研团队', 'level': 'institutional', 'requirement': 'medium'},
    'research_center': {'name': '研究中心', 'level': 'provincial', 'requirement': 'medium'},
    'institute': {'name': '研究所', 'level': 'institutional', 'requirement': 'low'},
    'laboratory': {'name': '实验室', 'level': 'institutional', 'requirement': 'low'}
}

COOPERATION_TYPES = {
    'university_enterprise': {'name': '校企合作', 'duration': 'long', 'benefit': 'mutual'},
    'industry_research': {'name': '产学研合作', 'duration': 'medium', 'benefit': 'mutual'},
    'international': {'name': '国际合作', 'duration': 'variable', 'benefit': 'academic'},
    'inter_university': {'name': '校际合作', 'duration': 'medium', 'benefit': 'academic'},
    'interdisciplinary': {'name': '跨学科合作', 'duration': 'short', 'benefit': 'academic'},
    'industry': {'name': '行业合作', 'duration': 'long', 'benefit': 'practical'},
    'government': {'name': '政府合作', 'duration': 'medium', 'benefit': 'policy'},
    'community': {'name': '社区合作', 'duration': 'short', 'benefit': 'social'}
}

EVALUATION_CRITERIA = {
    'innovation': {'name': '创新性', 'weight': 0.15, 'description': '研究方法和成果的创新程度'},
    'academic_value': {'name': '学术价值', 'weight': 0.15, 'description': '对学科发展的贡献'},
    'application_value': {'name': '应用价值', 'weight': 0.15, 'description': '实际应用前景和效果'},
    'social_impact': {'name': '社会影响', 'weight': 0.15, 'description': '对社会发展的促进作用'},
    'economic_benefit': {'name': '经济效益', 'weight': 0.15, 'description': '产生的经济价值'},
    'team_contribution': {'name': '团队贡献', 'weight': 0.1, 'description': '团队协作和贡献度'},
    'research_quality': {'name': '研究质量', 'weight': 0.1, 'description': '研究过程和成果质量'},
    'transformation': {'name': '成果转化', 'weight': 0.15, 'description': '成果转化和产业化程度'}
}

INFORMATION_TYPES = {
    'project': {'name': '项目信息', 'category': 'management', 'access_level': 'public'},
    'team': {'name': '团队信息', 'category': 'management', 'access_level': 'internal'},
    'funding': {'name': '经费信息', 'category': 'finance', 'access_level': 'restricted'},
    'achievement': {'name': '成果信息', 'category': 'output', 'access_level': 'public'},
    'platform': {'name': '平台信息', 'category': 'infrastructure', 'access_level': 'public'},
    'cooperation': {'name': '合作信息', 'category': 'external', 'access_level': 'internal'},
    'evaluation': {'name': '评价信息', 'category': 'assessment', 'access_level': 'internal'},
    'statistics': {'name': '统计信息', 'category': 'analytics', 'access_level': 'public'}
}


class EducationResearchService:
    """教育科研管理服务"""

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

                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_projects ( project_id TEXT PRIMARY KEY, project_name TEXT NOT NULL, project_type TEXT NOT NULL, education_type TEXT, principal_id INTEGER, principal_name TEXT, department TEXT, budget REAL DEFAULT 0, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'applied', description TEXT, keywords TEXT, expected_outcome TEXT, progress INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS project_details ( id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, phase TEXT, phase_start TEXT, phase_end TEXT, phase_progress INTEGER DEFAULT 0, milestones TEXT, deliverables TEXT, issues TEXT, FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_teams ( team_id TEXT PRIMARY KEY, team_name TEXT NOT NULL, education_type TEXT, department TEXT, leader_id INTEGER, leader_name TEXT, description TEXT, member_count INTEGER DEFAULT 0, established_date TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS team_members ( id INTEGER PRIMARY KEY AUTOINCREMENT, team_id TEXT NOT NULL, member_id INTEGER NOT NULL, member_name TEXT, role TEXT DEFAULT 'participant', join_date TEXT, contribution_rate REAL DEFAULT 0.3, FOREIGN KEY (team_id) REFERENCES research_teams(team_id), UNIQUE(team_id, member_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_funding ( funding_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, funding_source TEXT NOT NULL, amount REAL DEFAULT 0, approved_amount REAL DEFAULT 0, balance REAL DEFAULT 0, budget_details TEXT, status TEXT DEFAULT 'pending', start_date TEXT, end_date TEXT, FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS funding_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, funding_id TEXT NOT NULL, record_type TEXT, amount REAL, description TEXT, payee TEXT, payment_date TEXT, receipt_url TEXT, status TEXT DEFAULT 'pending', approved_by INTEGER, approved_at TEXT, FOREIGN KEY (funding_id) REFERENCES research_funding(funding_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_achievements ( achievement_id TEXT PRIMARY KEY, achievement_name TEXT NOT NULL, achievement_type TEXT NOT NULL, education_type TEXT, project_id TEXT, team_id TEXT, author_ids TEXT, author_names TEXT, publish_date TEXT, journal_name TEXT, volume TEXT, pages TEXT, index_type TEXT, status TEXT DEFAULT 'draft', description TEXT, impact_factor REAL DEFAULT 0, citation_count INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT, FOREIGN KEY (project_id) REFERENCES research_projects(project_id), FOREIGN KEY (team_id) REFERENCES research_teams(team_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS achievement_details ( id INTEGER PRIMARY KEY AUTOINCREMENT, achievement_id TEXT NOT NULL, detail_type TEXT, detail_content TEXT, attachment_url TEXT, FOREIGN KEY (achievement_id) REFERENCES research_achievements(achievement_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_platforms ( platform_id TEXT PRIMARY KEY, platform_name TEXT NOT NULL, platform_type TEXT NOT NULL, education_type TEXT, director_id INTEGER, director_name TEXT, department TEXT, location TEXT, equipment_value REAL DEFAULT 0, staff_count INTEGER DEFAULT 0, opening_hours TEXT, is_open INTEGER DEFAULT 1, status TEXT DEFAULT 'active', description TEXT, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS platform_resources ( id INTEGER PRIMARY KEY AUTOINCREMENT, platform_id TEXT NOT NULL, resource_name TEXT, resource_type TEXT, quantity INTEGER DEFAULT 1, status TEXT DEFAULT 'available', location TEXT, purchase_date TEXT, value REAL DEFAULT 0, FOREIGN KEY (platform_id) REFERENCES research_platforms(platform_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_cooperation ( cooperation_id TEXT PRIMARY KEY, cooperation_name TEXT NOT NULL, cooperation_type TEXT NOT NULL, education_type TEXT, partner_name TEXT, partner_type TEXT, start_date TEXT, end_date TEXT, budget REAL DEFAULT 0, objectives TEXT, status TEXT DEFAULT 'negotiating', contact_person TEXT, contact_info TEXT, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS cooperation_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, cooperation_id TEXT NOT NULL, record_date TEXT, activity_type TEXT, description TEXT, participants TEXT, outcomes TEXT, FOREIGN KEY (cooperation_id) REFERENCES research_cooperation(cooperation_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_evaluation ( evaluation_id TEXT PRIMARY KEY, evaluation_name TEXT NOT NULL, target_type TEXT, target_id TEXT, education_type TEXT, criteria TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'ongoing', created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS evaluation_results ( id INTEGER PRIMARY KEY AUTOINCREMENT, evaluation_id TEXT NOT NULL, criterion_code TEXT, score REAL DEFAULT 0, max_score REAL DEFAULT 100, weight REAL DEFAULT 0, comment TEXT, evaluator_id INTEGER, evaluator_name TEXT, FOREIGN KEY (evaluation_id) REFERENCES research_evaluation(evaluation_id) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_information ( info_id TEXT PRIMARY KEY, info_type TEXT NOT NULL, education_type TEXT, title TEXT NOT NULL, content TEXT, publisher_id INTEGER, publisher_name TEXT, publish_date TEXT, is_public INTEGER DEFAULT 1, views INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS information_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, info_id TEXT NOT NULL, record_date TEXT, record_type TEXT, data_content TEXT, FOREIGN KEY (info_id) REFERENCES research_information(info_id) ) ''')

                conn.commit()
                logger.info('教育科研管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 科研项目管理 ==========

    def create_project(self, project_name: str, project_type: str,
                        principal_id: int, principal_name: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"rpj_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PROJECT_TYPES.get(project_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_projects ( project_id, project_name, project_type, education_type, principal_id, principal_name, department, budget, start_date, end_date, status, description, keywords, expected_outcome, progress, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?, ?, ?, 0, ?, ?) ''', (project_id, project_name, project_type,
                          kwargs.get('education_type'),
                          principal_id, principal_name,
                          kwargs.get('department'),
                          kwargs.get('budget', 0),
                          kwargs.get('start_date'),
                          kwargs.get('end_date'),
                          kwargs.get('description'),
                          kwargs.get('keywords'),
                          kwargs.get('expected_outcome'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建科研项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建科研项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_project(self, project_id: str, approved: bool,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_projects SET status = ?, updated_at = ? WHERE project_id = ? AND status = ?',
                                 (status, now, project_id, 'applied'))
                    if cursor.rowcount > 0:
                        if approved:
                            cursor.execute('UPDATE research_projects SET start_date = ?, end_date = ? WHERE project_id = ?',
                                         (kwargs.get('start_date', now[:10]),
                                          kwargs.get('end_date'),
                                          project_id))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '项目状态不允许审核'}
        except Exception as e:
            logger.error(f'审核科研项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_progress(self, project_id: str, progress: int,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_projects SET progress = ?, updated_at = ? WHERE project_id = ?',
                                 (progress, now, project_id))
                    if cursor.rowcount > 0:
                        status = 'completed' if progress >= 100 else 'in_progress'
                        cursor.execute('UPDATE research_projects SET status = ? WHERE project_id = ?',
                                     (status, project_id))
                        conn.commit()
                        return {'success': True, 'progress': progress, 'status': status}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新项目进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_project(self, project_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_projects SET status = ?, progress = 100, end_date = ?, updated_at = ? WHERE project_id = ?',
                                 ('completed', kwargs.get('end_date', now[:10]), now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'completed'}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'项目结题失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 科研团队管理 ==========

    def create_team(self, team_name: str, leader_id: int, leader_name: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            team_id = f"rtm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_teams ( team_id, team_name, education_type, department, leader_id, leader_name, description, member_count, established_date, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'active', ?, ?) ''', (team_id, team_name, kwargs.get('education_type'),
                          kwargs.get('department'), leader_id, leader_name,
                          kwargs.get('description'),
                          kwargs.get('established_date', now[:10]),
                          now, now))
                    cursor.execute('INSERT INTO team_members (team_id, member_id, member_name, role, join_date, contribution_rate) VALUES (?, ?, ?, \'principal\', ?, 1.0)',
                                 (team_id, leader_id, leader_name, now))
                    conn.commit()
                    logger.info(f'创建科研团队: {team_name} ({team_id})')
                    return {'success': True, 'team_id': team_id}
        except Exception as e:
            logger.error(f'创建科研团队失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_team_member(self, team_id: str, member_id: int, member_name: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            role = kwargs.get('role', 'participant')
            config = TEAM_ROLES.get(role, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO team_members (team_id, member_id, member_name, role, join_date, contribution_rate) VALUES (?, ?, ?, ?, ?, ?)',
                                 (team_id, member_id, member_name, role, now,
                                  kwargs.get('contribution_rate', config.get('weight', 0.3))))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE research_teams SET member_count = member_count + 1, updated_at = ? WHERE team_id = ?',
                                     (now, team_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成员已加入团队'}
        except Exception as e:
            logger.error(f'添加团队成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_member_role(self, team_id: str, member_id: int, role: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            config = TEAM_ROLES.get(role, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE team_members SET role = ?, contribution_rate = ?, join_date = ? WHERE team_id = ? AND member_id = ?',
                                 (role, config.get('weight', 0.3), now, team_id, member_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'role': role}
                    return {'success': False, 'error': '成员不存在'}
        except Exception as e:
            logger.error(f'更新成员角色失败: {e}')
            return {'success': False, 'error': str(e)}

    def remove_team_member(self, team_id: str, member_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM team_members WHERE team_id = ? AND member_id = ?',
                                 (team_id, member_id))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE research_teams SET member_count = member_count - 1, updated_at = ? WHERE team_id = ?',
                                     (now, team_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成员不存在'}
        except Exception as e:
            logger.error(f'移除团队成员失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 科研经费管理 ==========

    def create_funding(self, project_id: str, funding_source: str,
                       amount: float, **kwargs) -> Dict[str, Any]:
        try:
            funding_id = f"rfd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = FUNDING_SOURCES.get(funding_source, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_funding ( funding_id, project_id, funding_source, amount, approved_amount, balance, budget_details, status, start_date, end_date ) VALUES (?, ?, ?, ?, 0, 0, ?, 'pending', ?, ?) ''', (funding_id, project_id, funding_source, amount,
                          kwargs.get('budget_details'),
                          kwargs.get('start_date'),
                          kwargs.get('end_date')))
                    conn.commit()
                    logger.info(f'创建科研经费: {funding_source} ({funding_id})')
                    return {'success': True, 'funding_id': funding_id}
        except Exception as e:
            logger.error(f'创建科研经费失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_funding(self, funding_id: str, approved_amount: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_funding SET status = ?, approved_amount = ?, balance = ?, start_date = ? WHERE funding_id = ? AND status = ?',
                                 ('approved', approved_amount, approved_amount, now[:10], funding_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'approved_amount': approved_amount}
                    return {'success': False, 'error': '经费状态不允许审核'}
        except Exception as e:
            logger.error(f'审批科研经费失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_expense(self, funding_id: str, amount: float, description: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT balance, status FROM research_funding WHERE funding_id = ?', (funding_id,))
                    funding = cursor.fetchone()
                    if not funding:
                        return {'success': False, 'error': '经费不存在'}
                    if funding[1] != 'approved':
                        return {'success': False, 'error': '经费未审批通过'}
                    if funding[0] < amount:
                        return {'success': False, 'error': '余额不足'}
                    cursor.execute(''' INSERT INTO funding_records (funding_id, record_type, amount, description, payee, payment_date, receipt_url, status) VALUES (?, 'expense', ?, ?, ?, ?, ?, 'pending') ''', (funding_id, amount, description,
                          kwargs.get('payee'), kwargs.get('payment_date', now[:10]),
                          kwargs.get('receipt_url')))
                    cursor.execute('UPDATE research_funding SET balance = balance - ? WHERE funding_id = ?',
                                 (amount, funding_id))
                    conn.commit()
                    return {'success': True, 'remaining_balance': funding[0] - amount}
        except Exception as e:
            logger.error(f'记录经费支出失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_expense(self, record_id: int, approved_by: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE funding_records SET status = ?, approved_by = ?, approved_at = ? WHERE id = ? AND status = ?',
                                 ('approved', approved_by, now, record_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报销记录不存在或已审批'}
        except Exception as e:
            logger.error(f'审批经费报销失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 科研成果管理 ==========

    def create_achievement(self, achievement_name: str, achievement_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            achievement_id = f"rac_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ACHIEVEMENT_TYPES.get(achievement_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_achievements ( achievement_id, achievement_name, achievement_type, education_type, project_id, team_id, author_ids, author_names, publish_date, journal_name, volume, pages, index_type, status, description, impact_factor, citation_count, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, 0, 0, ?, ?) ''', (achievement_id, achievement_name, achievement_type,
                          kwargs.get('education_type'), kwargs.get('project_id'),
                          kwargs.get('team_id'), kwargs.get('author_ids'),
                          kwargs.get('author_names'), kwargs.get('publish_date'),
                          kwargs.get('journal_name'), kwargs.get('volume'),
                          kwargs.get('pages'), kwargs.get('index_type'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建科研成果: {achievement_name} ({achievement_id})')
                    return {'success': True, 'achievement_id': achievement_id}
        except Exception as e:
            logger.error(f'创建科研成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_achievement(self, achievement_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_achievements SET status = ?, updated_at = ? WHERE achievement_id = ? AND status = ?',
                                 ('submitted', now, achievement_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'submitted'}
                    return {'success': False, 'error': '成果状态不允许提交'}
        except Exception as e:
            logger.error(f'提交科研成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_achievement(self, achievement_id: str, approved: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_achievements SET status = ?, updated_at = ? WHERE achievement_id = ? AND status = ?',
                                 (status, now, achievement_id, 'submitted'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '成果状态不允许审核'}
        except Exception as e:
            logger.error(f'审核科研成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_citation(self, achievement_id: str, citation_count: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_achievements SET citation_count = ?, updated_at = ? WHERE achievement_id = ?',
                                 (citation_count, now, achievement_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'citation_count': citation_count}
                    return {'success': False, 'error': '成果不存在'}
        except Exception as e:
            logger.error(f'更新引用次数失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_achievements(self, achievement_type: str = None, status: str = None,
                          education_type: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM research_achievements WHERE 1=1'
                params = []
                if achievement_type:
                    query += ' AND achievement_type = ?'
                    params.append(achievement_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                achievements = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'achievements': achievements, 'total': total, 'page': page,
                'page_size': page_size}
        except Exception as e:
            logger.error(f'获取成果列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 科研平台管理 ==========

    def create_platform(self, platform_name: str, platform_type: str,
                        director_id: int, director_name: str, **kwargs) -> Dict[str, Any]:
        try:
            platform_id = f"rpf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PLATFORM_TYPES.get(platform_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_platforms ( platform_id, platform_name, platform_type, education_type, director_id, director_name, department, location, equipment_value, staff_count, opening_hours, is_open, status, description, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active', ?, ?, ?) ''', (platform_id, platform_name, platform_type,
                          kwargs.get('education_type'),
                          director_id, director_name,
                          kwargs.get('department'), kwargs.get('location'),
                          kwargs.get('equipment_value', 0),
                          kwargs.get('staff_count', 0),
                          kwargs.get('opening_hours'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建科研平台: {platform_name} ({platform_id})')
                    return {'success': True, 'platform_id': platform_id}
        except Exception as e:
            logger.error(f'创建科研平台失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_resource(self, platform_id: str, resource_name: str, resource_type: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO platform_resources (platform_id, resource_name, resource_type, quantity, status, location, purchase_date, value) VALUES (?, ?, ?, ?, 'available', ?, ?, ?) ''', (platform_id, resource_name, resource_type,
                          kwargs.get('quantity', 1), kwargs.get('location'),
                          kwargs.get('purchase_date', now[:10]),
                          kwargs.get('value', 0)))
                    conn.commit()
                    return {'success': True, 'resource_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加平台资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_resource_status(self, resource_id: int, status: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE platform_resources SET status = ? WHERE id = ?',
                                 (status, resource_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '资源不存在'}
        except Exception as e:
            logger.error(f'更新资源状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_platform_status(self, platform_id: str, is_open: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_platforms SET is_open = ?, status = ?, updated_at = ? WHERE platform_id = ?',
                                 (1 if is_open else 0, 'active' if is_open else 'closed', now, platform_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'is_open': is_open}
                    return {'success': False, 'error': '平台不存在'}
        except Exception as e:
            logger.error(f'更新平台状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 科研合作管理 ==========

    def create_cooperation(self, cooperation_name: str, cooperation_type: str,
                           partner_name: str, **kwargs) -> Dict[str, Any]:
        try:
            cooperation_id = f"rcp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COOPERATION_TYPES.get(cooperation_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_cooperation ( cooperation_id, cooperation_name, cooperation_type, education_type, partner_name, partner_type, start_date, end_date, budget, objectives, status, contact_person, contact_info, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'negotiating', ?, ?, ?, ?) ''', (cooperation_id, cooperation_name, cooperation_type,
                          kwargs.get('education_type'), partner_name,
                          kwargs.get('partner_type'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('budget', 0),
                          kwargs.get('objectives'), kwargs.get('contact_person'),
                          kwargs.get('contact_info'), now, now))
                    conn.commit()
                    logger.info(f'创建科研合作: {cooperation_name} ({cooperation_id})')
                    return {'success': True, 'cooperation_id': cooperation_id}
        except Exception as e:
            logger.error(f'创建科研合作失败: {e}')
            return {'success': False, 'error': str(e)}

    def sign_cooperation(self, cooperation_id: str, start_date: str = None,
                         end_date: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_cooperation SET status = ?, start_date = ?, end_date = ?, updated_at = ? WHERE cooperation_id = ? AND status = ?',
                                 ('active', start_date or now[:10], end_date, now, cooperation_id, 'negotiating'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'active'}
                    return {'success': False, 'error': '合作状态不允许签署'}
        except Exception as e:
            logger.error(f'签署合作协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_cooperation_record(self, cooperation_id: str, activity_type: str,
                               description: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO cooperation_records (cooperation_id, record_date, activity_type, description, participants, outcomes) VALUES (?, ?, ?, ?, ?, ?) ''', (cooperation_id, kwargs.get('record_date', now[:10]),
                          activity_type, description,
                          kwargs.get('participants'), kwargs.get('outcomes')))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加合作记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_cooperation(self, cooperation_id: str, outcomes: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE research_cooperation SET status = ?, end_date = ?, updated_at = ? WHERE cooperation_id = ?',
                                 ('completed', now[:10], now, cooperation_id))
                    if outcomes:
                        cursor.execute(''' INSERT INTO cooperation_records (cooperation_id, record_date, activity_type, description, outcomes) VALUES (?, ?, 'completion', '合作项目完成', ?) ''', (cooperation_id, now[:10], outcomes))
                    conn.commit()
                    return {'success': True, 'status': 'completed'}
        except Exception as e:
            logger.error(f'完成科研合作失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 科研评价管理 ==========

    def create_evaluation(self, evaluation_name: str, target_type: str,
                          target_id: str, **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"rev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            criteria = json.dumps(list(EVALUATION_CRITERIA.keys()))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_evaluation ( evaluation_id, evaluation_name, target_type, target_id, education_type, criteria, start_date, end_date, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ongoing', ?, ?) ''', (evaluation_id, evaluation_name, target_type, target_id,
                          kwargs.get('education_type'), criteria,
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建科研评价: {evaluation_name} ({evaluation_id})')
                    return {'success': True, 'evaluation_id': evaluation_id}
        except Exception as e:
            logger.error(f'创建科研评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_evaluation_result(self, evaluation_id: str, criterion_code: str,
                                  score: float, evaluator_id: int, evaluator_name: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            config = EVALUATION_CRITERIA.get(criterion_code, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO evaluation_results (evaluation_id, criterion_code, score, max_score, weight, comment, evaluator_id, evaluator_name) VALUES (?, ?, ?, 100, ?, ?, ?, ?)',
                                 (evaluation_id, criterion_code, score,
                                  config.get('weight', 0), kwargs.get('comment'),
                                  evaluator_id, evaluator_name))
                    conn.commit()
                    return {'success': True, 'criterion_code': criterion_code, 'score': score}
        except Exception as e:
            logger.error(f'提交评价结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_evaluation_score(self, evaluation_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT criterion_code, score, weight FROM evaluation_results WHERE evaluation_id = ?', (evaluation_id,))
                    results = cursor.fetchall()
                    if not results:
                        return {'success': False, 'error': '暂无评价结果'}
                    total_score = 0.0
                    total_weight = 0.0
                    for r in results:
                        weight = r[2] or EVALUATION_CRITERIA.get(r[0], {}).get('weight', 0.125)
                        total_score += r[1] * weight
                        total_weight += weight
                    final_score = round(total_score / total_weight, 2) if total_weight > 0 else 0
                    cursor.execute('UPDATE research_evaluation SET status = ?, updated_at = ? WHERE evaluation_id = ?',
                                 ('completed', now, evaluation_id))
                    conn.commit()
                    return {'success': True, 'final_score': final_score, 'details': [{'criterion': r[0], 'score': r[1],
                    'weight': weight} for r, weight in zip(results, [r[2] or EVALUATION_CRITERIA.get(r[0],
                    {}).get('weight', 0.125) for r in results])]}
        except Exception as e:
            logger.error(f'计算评价总分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_report(self, evaluation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM research_evaluation WHERE evaluation_id = ?', (evaluation_id,))
                evaluation = cursor.fetchone()
                if not evaluation:
                    return {'success': False, 'error': '评价不存在'}
                cursor.execute('SELECT * FROM evaluation_results WHERE evaluation_id = ?', (evaluation_id,))
                results = [dict(r) for r in cursor.fetchall()]
                total_score = sum(r['score'] * (r['weight'] or EVALUATION_CRITERIA.get(r['criterion_code'],
                {}).get('weight', 0.125)) for r in results)
                total_weight = sum(r['weight'] or EVALUATION_CRITERIA.get(r['criterion_code'], {}).get('weight',
                0.125) for r in results)
                final_score = round(total_score / total_weight, 2) if total_weight > 0 else 0
                return {
                    'success': True,
                    'evaluation': dict(evaluation),
                    'results': results,
                    'final_score': final_score,
                    'grade': 'A' if final_score >= 90 else 'B' if final_score >= 80 else 'C' if final_score >= 70 else 
                    'D' if final_score >= 60 else 'F'
                }
        except Exception as e:
            logger.error(f'获取评价报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 科研信息管理 ==========

    def publish_information(self, info_type: str, title: str, content: str,
                            publisher_id: int, publisher_name: str, **kwargs) -> Dict[str, Any]:
        try:
            info_id = f"rin_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INFORMATION_TYPES.get(info_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_information ( info_id, info_type, education_type, title, content, publisher_id, publisher_name, publish_date, is_public, views, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?) ''', (info_id, info_type, kwargs.get('education_type'),
                          title, content, publisher_id, publisher_name,
                          kwargs.get('publish_date', now[:10]),
                          kwargs.get('is_public', 1), now, now))
                    conn.commit()
                    logger.info(f'发布科研信息: {title} ({info_id})')
                    return {'success': True, 'info_id': info_id}
        except Exception as e:
            logger.error(f'发布科研信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_info_record(self, info_id: str, record_type: str, data_content: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO information_records (info_id, record_date, record_type, data_content) VALUES (?, ?, ?, ?)',
                                 (info_id, now[:10], record_type, data_content))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加信息记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_information(self, info_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM research_information WHERE info_id = ?', (info_id,))
                    info = cursor.fetchone()
                    if not info:
                        return {'success': False, 'error': '信息不存在'}
                    cursor.execute('UPDATE research_information SET views = views + 1 WHERE info_id = ?', (info_id,))
                    conn.commit()
                    return {'success': True, 'information': dict(info)}
        except Exception as e:
            logger.error(f'获取科研信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_information(self, info_type: str = None, education_type: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM research_information WHERE is_public = 1'
                params = []
                if info_type:
                    query += ' AND info_type = ?'
                    params.append(info_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY publish_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                infos = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'information': infos, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取信息列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_research_statistics(self, education_type: str = None,
                                 start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                project_query = 'SELECT COUNT(*) FROM research_projects WHERE 1=1'
                project_params = []
                if education_type:
                    project_query += ' AND education_type = ?'
                    project_params.append(education_type)
                if start_date:
                    project_query += ' AND created_at >= ?'
                    project_params.append(start_date)
                if end_date:
                    project_query += ' AND created_at <= ?'
                    project_params.append(end_date)
                cursor.execute(project_query, project_params)
                stats['total_projects'] = cursor.fetchone()[0]

                cursor.execute(project_query.replace('COUNT(*)', 'COUNT(*) FILTER (WHERE status = "completed")'),
                project_params)
                stats['completed_projects'] = cursor.fetchone()[0]

                team_query = 'SELECT COUNT(*) FROM research_teams WHERE 1=1'
                team_params = []
                if education_type:
                    team_query += ' AND education_type = ?'
                    team_params.append(education_type)
                cursor.execute(team_query, team_params)
                stats['total_teams'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM team_members')
                stats['total_members'] = cursor.fetchone()[0]

                funding_query = 'SELECT SUM(approved_amount) FROM research_funding WHERE status = "approved"'
                funding_params = []
                if education_type:
                    funding_query += ' AND project_id IN ( SELECT project_id FROM research_projects WHERE education_type = ?)'
                    funding_params.append(education_type)
                cursor.execute(funding_query, funding_params)
                stats['total_funding'] = cursor.fetchone()[0] or 0

                achievement_query = 'SELECT COUNT(*) FROM research_achievements WHERE status = "approved"'
                achievement_params = []
                if education_type:
                    achievement_query += ' AND education_type = ?'
                    achievement_params.append(education_type)
                cursor.execute(achievement_query, achievement_params)
                stats['total_achievements'] = cursor.fetchone()[0]

                platform_query = 'SELECT COUNT(*) FROM research_platforms WHERE status = "active"'
                platform_params = []
                if education_type:
                    platform_query += ' AND education_type = ?'
                    platform_params.append(education_type)
                cursor.execute(platform_query, platform_params)
                stats['active_platforms'] = cursor.fetchone()[0]

                cooperation_query = 'SELECT COUNT(*) FROM research_cooperation WHERE status = "active"'
                cooperation_params = []
                if education_type:
                    cooperation_query += ' AND education_type = ?'
                    cooperation_params.append(education_type)
                cursor.execute(cooperation_query, cooperation_params)
                stats['active_cooperations'] = cursor.fetchone()[0]

                stats['education_type'] = education_type or 'all'
                stats['period'] = {'start_date': start_date, 'end_date': end_date}
                stats['generated_at'] = datetime.now().isoformat()

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取科研统计失败: {e}')
            return {'success': False, 'error': str(e)}