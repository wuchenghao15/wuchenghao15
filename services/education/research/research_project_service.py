from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 科研与项目管理服务 (v15.6.0) ==================================== 提供科研项目、学术论文、专利成果和创新竞赛等综合管理服务。  核心能力： 1. 科研项目 - 项目立项、进度追踪、经费管理 2. 学术论文 - 论文管理、发表记录、引用追踪 3. 专利成果 - 专利申请、知识产权管理 4. 创新竞赛 - 学科竞赛、创新创业、获奖管理 5. 科研团队 - 团队组建、角色分工、协作管理 6. 成果统计 - 科研产出、影响力分析 7. 成人科研 - 成人教育研究实践管理 8. K12科创 - 学生科技创新项目管理 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'research_project_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ResearchProject')


# ========== 科研配置 ==========

# 项目类型
PROJECT_TYPES = {
    'national': {'name': '国家级项目', 'level': 5, 'funding_range': '50-500万'},
    'provincial': {'name': '省部级项目', 'level': 4, 'funding_range': '10-100万'},
    'municipal': {'name': '市厅级项目', 'level': 3, 'funding_range': '5-50万'},
    'school': {'name': '校级项目', 'level': 2, 'funding_range': '1-10万'},
    'enterprise': {'name': '校企合作项目', 'level': 3, 'funding_range': '5-200万'},
    'international': {'name': '国际合作项目', 'level': 5, 'funding_range': '10-300万'},
    'student_innovation': {'name': '学生创新项目', 'level': 1, 'funding_range': '0.1-2万'},
    'teacher_research': {'name': '教师科研项目', 'level': 2, 'funding_range': '1-20万'}
}

# 项目状态
PROJECT_STATUS = {
    'draft': {'name': '草稿', 'color': '#d9d9d9'},
    'submitted': {'name': '已申报', 'color': '#1890ff'},
    'reviewing': {'name': '评审中', 'color': '#faad14'},
    'approved': {'name': '已立项', 'color': '#52c41a'},
    'rejected': {'name': '未立项', 'color': '#f5222d'},
    'ongoing': {'name': '进行中', 'color': '#1890ff'},
    'midterm': {'name': '中期检查', 'color': '#faad14'},
    'completed': {'name': '已结题', 'color': '#52c41a'},
    'terminated': {'name': '已终止', 'color': '#8c8c8c'},
    'delayed': {'name': '已延期', 'color': '#fa8c16'}
}

# 论文级别
PAPER_LEVELS = {
    'sci_q1': {'name': 'SCI一区', 'score': 100, 'description': '顶级期刊'},
    'sci_q2': {'name': 'SCI二区', 'score': 80, 'description': '权威期刊'},
    'sci_q3': {'name': 'SCI三区', 'score': 60, 'description': '重要期刊'},
    'sci_q4': {'name': 'SCI四区', 'score': 40, 'description': '一般期刊'},
    'ei': {'name': 'EI收录', 'score': 50, 'description': '工程索引'},
    'cssci': {'name': 'CSSCI', 'score': 50, 'description': '社科核心'},
    'cscd': {'name': 'CSCD', 'score': 30, 'description': '科技核心'},
    'core': {'name': '中文核心', 'score': 30, 'description': '北大核心'},
    'general': {'name': '普通期刊', 'score': 10, 'description': '正式期刊'},
    'conference': {'name': '会议论文', 'score': 15, 'description': '学术会议'}
}

# 专利类型
PATENT_TYPES = {
    'invention': {'name': '发明专利', 'protection_years': 20, 'score': 80},
    'utility_model': {'name': '实用新型', 'protection_years': 10, 'score': 40},
    'design': {'name': '外观设计', 'protection_years': 15, 'score': 30},
    'software_copyright': {'name': '软件著作权', 'protection_years': 50, 'score': 20},
    'integrated_circuit': {'name': '集成电路布图', 'protection_years': 10, 'score': 30},
    'plant_variety': {'name': '植物新品种', 'protection_years': 20, 'score': 50}
}

# 专利状态
PATENT_STATUS = {
    'drafting': {'name': '撰写中', 'color': '#d9d9d9'},
    'submitted': {'name': '已申请', 'color': '#1890ff'},
    'examining': {'name': '审查中', 'color': '#faad14'},
    'published': {'name': '已公布', 'color': '#1890ff'},
    'granted': {'name': '已授权', 'color': '#52c41a'},
    'rejected': {'name': '已驳回', 'color': '#f5222d'},
    'expired': {'name': '已失效', 'color': '#8c8c8c'},
    'transferred': {'name': '已转让', 'color': '#722ed1'}
}

# 竞赛类型
COMPETITION_TYPES = {
    'academic': {'name': '学科竞赛', 'level': 'national'},
    'innovation': {'name': '创新创业', 'level': 'national'},
    'technology': {'name': '科技竞赛', 'level': 'national'},
    'math_modeling': {'name': '数学建模', 'level': 'national'},
    'programming': {'name': '程序设计', 'level': 'national'},
    'robot': {'name': '机器人竞赛', 'level': 'international'},
    'science_fair': {'name': '科学展览', 'level': 'school'},
    'subject_olympiad': {'name': '学科奥赛', 'level': 'international'}
}

# 获奖等级
AWARD_LEVELS = {
    'special': {'name': '特等奖', 'score': 100},
    'first': {'name': '一等奖', 'score': 80},
    'second': {'name': '二等奖', 'score': 60},
    'third': {'name': '三等奖', 'score': 40},
    'excellence': {'name': '优秀奖', 'score': 20},
    'participation': {'name': '参与奖', 'score': 5}
}

# 项目角色
PROJECT_ROLES = {
    'pi': {'name': '项目负责人', 'permissions': 'full'},
    'co_pi': {'name': '联合负责人', 'permissions': 'manage'},
    'core_member': {'name': '核心成员', 'permissions': 'edit'},
    'member': {'name': '参与成员', 'permissions': 'contribute'},
    'student': {'name': '学生助理', 'permissions': 'view'},
    'advisor': {'name': '指导教师', 'permissions': 'view'},
    'consultant': {'name': '顾问', 'permissions': 'view'}
}

# 经费类型
BUDGET_CATEGORIES = {
    'equipment': {'name': '设备费', 'description': '仪器设备购置'},
    'materials': {'name': '材料费', 'description': '实验材料耗材'},
    'travel': {'name': '差旅费', 'description': '调研考察差旅'},
    'conference': {'name': '会议费', 'description': '学术会议交流'},
    'publication': {'name': '出版费', 'description': '论文版面出版'},
    'labor': {'name': '劳务费', 'description': '人员劳务支出'},
    'consulting': {'name': '咨询费', 'description': '专家咨询评审'},
    'other': {'name': '其他费用', 'description': '其他相关支出'}
}


class ResearchProjectService:
    """科研与项目管理服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_projects ( project_id TEXT PRIMARY KEY, project_name TEXT NOT NULL, project_type TEXT NOT NULL, project_level INTEGER, discipline TEXT, education_type TEXT, description TEXT, objectives TEXT, methodology TEXT, pi_id INTEGER, pi_name TEXT, start_date TEXT, end_date TEXT, total_budget REAL DEFAULT 0, spent_budget REAL DEFAULT 0, funding_source TEXT, status TEXT DEFAULT 'draft', progress INTEGER DEFAULT 0, keywords TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS project_members ( id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, user_id INTEGER NOT NULL, user_name TEXT, role TEXT DEFAULT 'member', contribution TEXT, joined_at TEXT, UNIQUE(project_id, user_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS project_milestones ( milestone_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL, description TEXT, due_date TEXT, completed_date TEXT, status TEXT DEFAULT 'pending', deliverables TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS project_budgets ( budget_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, category TEXT NOT NULL, budget_amount REAL, spent_amount REAL DEFAULT 0, description TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS budget_transactions ( transaction_id TEXT PRIMARY KEY, budget_id TEXT NOT NULL, project_id TEXT NOT NULL, amount REAL NOT NULL, transaction_type TEXT, description TEXT, receipt_url TEXT, spender_id INTEGER, spender_name TEXT, transaction_date TEXT, approved_by INTEGER, status TEXT DEFAULT 'pending', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS research_papers ( paper_id TEXT PRIMARY KEY, title TEXT NOT NULL, paper_level TEXT, journal_name TEXT, publish_date TEXT, volume TEXT, issue TEXT, pages TEXT, doi TEXT, abstract TEXT, keywords TEXT, project_id TEXT, corresponding_author INTEGER, authors TEXT, author_ids TEXT, file_url TEXT, citation_count INTEGER DEFAULT 0, impact_factor REAL, status TEXT DEFAULT 'published', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS patents ( patent_id TEXT PRIMARY KEY, title TEXT NOT NULL, patent_type TEXT NOT NULL, application_no TEXT, patent_no TEXT, applicants TEXT, inventors TEXT, inventor_ids TEXT, filing_date TEXT, publication_date TEXT, grant_date TEXT, expiry_date TEXT, abstract TEXT, project_id TEXT, status TEXT DEFAULT 'drafting', transfer_amount REAL, transfer_to TEXT, transfer_date TEXT, file_url TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS competitions ( competition_id TEXT PRIMARY KEY, competition_name TEXT NOT NULL, competition_type TEXT, level TEXT, organizer TEXT, description TEXT, start_date TEXT, end_date TEXT, registration_deadline TEXT, location TEXT, website TEXT, status TEXT DEFAULT 'upcoming', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS competition_awards ( award_id TEXT PRIMARY KEY, competition_id TEXT NOT NULL, competition_name TEXT, team_name TEXT, award_level TEXT, student_id INTEGER, student_name TEXT, advisor_id INTEGER, advisor_name TEXT, award_date TEXT, certificate_url TEXT, description TEXT, education_type TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS project_reports ( report_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, report_type TEXT, title TEXT, content TEXT, summary TEXT, achievements TEXT, problems TEXT, next_plan TEXT, submitted_by INTEGER, submitted_by_name TEXT, submitted_at TEXT, reviewed_by INTEGER, reviewed_at TEXT, review_comment TEXT, status TEXT DEFAULT 'submitted', created_at TEXT ) ''')
                conn.commit()
                logger.info('科研与项目管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 科研项目 ==========

    def create_project(self, project_name: str, project_type: str,
                        pi_id: int, pi_name: str, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"rpr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PROJECT_TYPES.get(project_type, {})
            keywords = json.dumps(kwargs.get('keywords'), ensure_ascii=False) if kwargs.get('keywords') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_projects ( project_id, project_name, project_type, project_level, discipline, education_type, description, objectives, methodology, pi_id, pi_name, start_date, end_date, total_budget, funding_source, status, progress, keywords, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', 0, ?, ?, ?) ''', (project_id, project_name, project_type,
                          config.get('level', 1), kwargs.get('discipline'),
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('objectives'), kwargs.get('methodology'),
                          pi_id, pi_name, kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('total_budget', 0),
                          kwargs.get('funding_source'), keywords, now, now))
                    cursor.execute(''' INSERT INTO project_members (project_id, user_id, user_name, role, joined_at) VALUES (?, ?, ?, 'pi', ?) ''', (project_id, pi_id, pi_name, now))
                    conn.commit()
                    logger.info(f'创建科研项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建科研项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM research_projects WHERE project_id = ?', (project_id,))
                row = cursor.fetchone()
                if row:
                    project = dict(row)
                    if project.get('keywords'):
                        project['keywords'] = json.loads(project['keywords'])
                    return project
                return None
        except Exception as e:
            logger.error(f'获取科研项目失败: {e}')
            return None

    def list_projects(self, project_type: str = None, status: str = None,
                       pi_id: int = None, education_type: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM research_projects WHERE 1=1'
                params = []
                if project_type:
                    query += ' AND project_type = ?'
                    params.append(project_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if pi_id:
                    query += ' AND pi_id = ?'
                    params.append(pi_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
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

    def update_project_status(self, project_id: str, status: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['status = ?', 'updated_at = ?']
                    params = [status, now]
                    if 'progress' in kwargs:
                        update_fields.append('progress = ?')
                        params.append(kwargs['progress'])
                    params.append(project_id)
                    cursor.execute(f''' UPDATE research_projects SET {", ".join(update_fields)} WHERE project_id = ? ''', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'项目状态更新: {project_id} -> {status}')
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新项目状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 项目成员 ==========

    def add_member(self, project_id: str, user_id: int,
                    user_name: str, role: str = 'member',
                    **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT OR IGNORE INTO project_members (project_id, user_id, user_name, role, contribution, joined_at) VALUES (?, ?, ?, ?, ?, ?) ''', (project_id, user_id, user_name, role,
                          kwargs.get('contribution'), now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '该成员已存在'}
        except Exception as e:
            logger.error(f'添加项目成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_project_members(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM project_members WHERE project_id = ? ORDER BY joined_at', (project_id,))
                members = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'members': members}
        except Exception as e:
            logger.error(f'获取项目成员失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 里程碑管理 ==========

    def create_milestone(self, project_id: str, title: str,
                          due_date: str, **kwargs) -> Dict[str, Any]:
        try:
            milestone_id = f"mst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO project_milestones ( milestone_id, project_id, title, description, due_date, status, deliverables, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?) ''', (milestone_id, project_id, title,
                          kwargs.get('description'), due_date,
                          kwargs.get('deliverables'), now, now))
                    conn.commit()
                    return {'success': True, 'milestone_id': milestone_id}
        except Exception as e:
            logger.error(f'创建里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_milestone(self, milestone_id: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE project_milestones SET status = 'completed', completed_date = ?, deliverables = ?, updated_at = ? WHERE milestone_id = ? AND status = 'pending' ''', (kwargs.get('completed_date', now[:10]),
                          kwargs.get('deliverables'), now, milestone_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '里程碑状态不允许完成'}
        except Exception as e:
            logger.error(f'完成里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_milestones(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM project_milestones WHERE project_id = ? ORDER BY due_date', (project_id,))
                milestones = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'milestones': milestones}
        except Exception as e:
            logger.error(f'获取里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 经费管理 ==========

    def create_budget(self, project_id: str, category: str,
                       budget_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            budget_id = f"bud_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO project_budgets ( budget_id, project_id, category, budget_amount, spent_amount, description, created_at, updated_at ) VALUES (?, ?, ?, ?, 0, ?, ?, ?) ''', (budget_id, project_id, category, budget_amount,
                          kwargs.get('description'), now, now))
                    conn.commit()
                    return {'success': True, 'budget_id': budget_id}
        except Exception as e:
            logger.error(f'创建预算失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_expense(self, budget_id: str, project_id: str,
                        amount: float, **kwargs) -> Dict[str, Any]:
        try:
            transaction_id = f"btx_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT budget_amount, spent_amount FROM project_budgets WHERE budget_id = ?',
                    (budget_id,))
                    budget = cursor.fetchone()
                    if not budget:
                        return {'success': False, 'error': '预算不存在'}
                    if budget[0] and budget[1] + amount > budget[0]:
                        return {'success': False, 'error': '超出预算'}
                    cursor.execute(''' INSERT INTO budget_transactions ( transaction_id, budget_id, project_id, amount, transaction_type, description, receipt_url, spender_id, spender_name, transaction_date, approved_by, status, created_at ) VALUES (?, ?, ?, ?, 'expense', ?, ?, ?, ?, ?, ?, 'pending', ?) ''', (transaction_id, budget_id, project_id, amount,
                          kwargs.get('description'), kwargs.get('receipt_url'),
                          kwargs.get('spender_id'), kwargs.get('spender_name'),
                          kwargs.get('transaction_date', now[:10]),
                          kwargs.get('approved_by'), now))
                    conn.commit()
                    return {'success': True, 'transaction_id': transaction_id}
        except Exception as e:
            logger.error(f'记录支出失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_expense(self, transaction_id: str, approved: bool,
                         approved_by: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT budget_id, project_id, amount FROM budget_transactions WHERE transaction_id = ? AND status = ?', (transaction_id,
                    'pending'))
                    txn = cursor.fetchone()
                    if not txn:
                        return {'success': False, 'error': '支出记录不存在或已处理'}
                    cursor.execute('UPDATE budget_transactions SET status = ?, approved_by = ? WHERE transaction_id = ?',
                                 (status, approved_by, transaction_id))
                    if approved:
                        cursor.execute('UPDATE project_budgets SET spent_amount = spent_amount + ?, updated_at = ? WHERE budget_id = ?', (txn[2], now, txn[0]))
                        cursor.execute('UPDATE research_projects SET spent_budget = spent_budget + ?, updated_at = ? WHERE project_id = ?', (txn[2], now, txn[1]))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'审批支出失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_project_budget(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM project_budgets WHERE project_id = ?', (project_id,))
                budgets = [dict(b) for b in cursor.fetchall()]
                cursor.execute('SELECT SUM(budget_amount), SUM(spent_amount) FROM project_budgets WHERE project_id = ?',
                (project_id,))
                totals = cursor.fetchone()
                return {
                    'success': True,
                    'budgets': budgets,
                    'total_budget': totals[0] or 0,
                    'total_spent': totals[1] or 0,
                    'remaining': (totals[0] or 0) - (totals[1] or 0)
                }
        except Exception as e:
            logger.error(f'获取项目预算失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 论文管理 ==========

    def add_paper(self, title: str, paper_level: str,
                   **kwargs) -> Dict[str, Any]:
        try:
            paper_id = f"ppr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            authors = json.dumps(kwargs.get('authors'), ensure_ascii=False) if kwargs.get('authors') else None
            author_ids = json.dumps(kwargs.get('author_ids'), ensure_ascii=False) if kwargs.get('author_ids') else None
            keywords = json.dumps(kwargs.get('keywords'), ensure_ascii=False) if kwargs.get('keywords') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO research_papers ( paper_id, title, paper_level, journal_name, publish_date, volume, issue, pages, doi, abstract, keywords, project_id, corresponding_author, authors, author_ids, file_url, citation_count, impact_factor, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'published', ?, ?) ''', (paper_id, title, paper_level,
                          kwargs.get('journal_name'), kwargs.get('publish_date'),
                          kwargs.get('volume'), kwargs.get('issue'),
                          kwargs.get('pages'), kwargs.get('doi'),
                          kwargs.get('abstract'), keywords,
                          kwargs.get('project_id'), kwargs.get('corresponding_author'),
                          authors, author_ids, kwargs.get('file_url'),
                          kwargs.get('impact_factor', 0), now, now))
                    conn.commit()
                    logger.info(f'添加论文: {title} ({paper_id})')
                    return {'success': True, 'paper_id': paper_id}
        except Exception as e:
            logger.error(f'添加论文失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_papers(self, project_id: str = None, paper_level: str = None,
                     author_id: int = None, page: int = 1,
                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM research_papers WHERE 1=1'
                params = []
                if project_id:
                    query += ' AND project_id = ?'
                    params.append(project_id)
                if paper_level:
                    query += ' AND paper_level = ?'
                    params.append(paper_level)
                if author_id:
                    query += ' AND author_ids LIKE ?'
                    params.append(f'%{author_id}%')
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY publish_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                papers = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'papers': papers, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取论文列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 专利管理 ==========

    def add_patent(self, title: str, patent_type: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            patent_id = f"ptn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            applicants = json.dumps(kwargs.get('applicants'), ensure_ascii=False) if kwargs.get('applicants') else None
            inventors = json.dumps(kwargs.get('inventors'), ensure_ascii=False) if kwargs.get('inventors') else None
            inventor_ids = json.dumps(kwargs.get('inventor_ids'),
            ensure_ascii=False) if kwargs.get('inventor_ids') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO patents ( patent_id, title, patent_type, application_no, patent_no, applicants, inventors, inventor_ids, filing_date, publication_date, grant_date, expiry_date, abstract, project_id, status, file_url, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (patent_id, title, patent_type,
                          kwargs.get('application_no'), kwargs.get('patent_no'),
                          applicants, inventors, inventor_ids,
                          kwargs.get('filing_date'), kwargs.get('publication_date'),
                          kwargs.get('grant_date'), kwargs.get('expiry_date'),
                          kwargs.get('abstract'), kwargs.get('project_id'),
                          kwargs.get('status', 'drafting'), kwargs.get('file_url'),
                          now, now))
                    conn.commit()
                    logger.info(f'添加专利: {title} ({patent_id})')
                    return {'success': True, 'patent_id': patent_id}
        except Exception as e:
            logger.error(f'添加专利失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_patent_status(self, patent_id: str, status: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['status = ?', 'updated_at = ?']
                    params = [status, now]
                    if status == 'granted':
                        update_fields.append('grant_date = ?')
                        params.append(kwargs.get('grant_date', now[:10]))
                    if status == 'transferred':
                        update_fields.extend(['transfer_amount = ?', 'transfer_to = ?', 'transfer_date = ?'])
                        params.extend([kwargs.get('transfer_amount', 0), kwargs.get('transfer_to'),
                        kwargs.get('transfer_date', now[:10])])
                    params.append(patent_id)
                    cursor.execute(f''' UPDATE patents SET {", ".join(update_fields)} WHERE patent_id = ? ''', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '专利不存在'}
        except Exception as e:
            logger.error(f'更新专利状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_patents(self, patent_type: str = None, status: str = None,
                      inventor_id: int = None, page: int = 1,
                      page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM patents WHERE 1=1'
                params = []
                if patent_type:
                    query += ' AND patent_type = ?'
                    params.append(patent_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if inventor_id:
                    query += ' AND inventor_ids LIKE ?'
                    params.append(f'%{inventor_id}%')
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY filing_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                patents = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'patents': patents, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取专利列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 竞赛管理 ==========

    def create_competition(self, competition_name: str, competition_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            competition_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO competitions ( competition_id, competition_name, competition_type, level, organizer, description, start_date, end_date, registration_deadline, location, website, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'upcoming', ?, ?) ''', (competition_id, competition_name, competition_type,
                          kwargs.get('level'), kwargs.get('organizer'),
                          kwargs.get('description'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('registration_deadline'),
                          kwargs.get('location'), kwargs.get('website'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建竞赛: {competition_name} ({competition_id})')
                    return {'success': True, 'competition_id': competition_id}
        except Exception as e:
            logger.error(f'创建竞赛失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_award(self, competition_id: str, award_level: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            award_id = f"awd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT competition_name FROM competitions WHERE competition_id = ?',
                    (competition_id,))
                    comp = cursor.fetchone()
                    comp_name = comp[0] if comp else kwargs.get('competition_name', '')
                    cursor.execute(''' INSERT INTO competition_awards ( award_id, competition_id, competition_name, team_name, award_level, student_id, student_name, advisor_id, advisor_name, award_date, certificate_url, description, education_type, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (award_id, competition_id, comp_name,
                          kwargs.get('team_name'), award_level,
                          kwargs.get('student_id'), kwargs.get('student_name'),
                          kwargs.get('advisor_id'), kwargs.get('advisor_name'),
                          kwargs.get('award_date', now[:10]),
                          kwargs.get('certificate_url'),
                          kwargs.get('description'),
                          kwargs.get('education_type'), now))
                    conn.commit()
                    logger.info(f'记录获奖: {comp_name} - {award_level}')
                    return {'success': True, 'award_id': award_id}
        except Exception as e:
            logger.error(f'记录获奖失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_awards(self, student_id: int = None, competition_type: str = None,
                     education_type: str = None, page: int = 1,
                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = ''' SELECT ca.* FROM competition_awards ca LEFT JOIN competitions c ON ca.competition_id = c.competition_id WHERE 1=1 '''
                params = []
                if student_id:
                    query += ' AND ca.student_id = ?'
                    params.append(student_id)
                if competition_type:
                    query += ' AND c.competition_type = ?'
                    params.append(competition_type)
                if education_type:
                    query += ' AND ca.education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY ca.award_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                awards = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'awards': awards, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取获奖列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 项目报告 ==========

    def submit_project_report(self, project_id: str, report_type: str,
                               title: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"prr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO project_reports ( report_id, project_id, report_type, title, content, summary, achievements, problems, next_plan, submitted_by, submitted_by_name, submitted_at, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitted', ?) ''', (report_id, project_id, report_type, title,
                          kwargs.get('content'), kwargs.get('summary'),
                          kwargs.get('achievements'), kwargs.get('problems'),
                          kwargs.get('next_plan'),
                          kwargs.get('submitted_by'),
                          kwargs.get('submitted_by_name'), now, now))
                    conn.commit()
                    logger.info(f'提交项目报告: {report_id}')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'提交项目报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_project_report(self, report_id: str, reviewed_by: int,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE project_reports SET reviewed_by = ?, reviewed_at = ?, review_comment = ?, status = 'reviewed' WHERE report_id = ? AND status = 'submitted' ''', (reviewed_by, now, kwargs.get('review_comment'), report_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报告状态不允许审核'}
        except Exception as e:
            logger.error(f'审核项目报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 科研统计 ==========

    def get_research_statistics(self, education_type: str = None,
                                  year: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*), SUM(total_budget), SUM(spent_budget) FROM research_projects WHERE status IN (?, ?)'
                params = ['ongoing', 'completed']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if year:
                    query += ' AND strftime("%Y", start_date) = ?'
                    params.append(year)
                cursor.execute(query, params)
                proj_row = cursor.fetchone()
                cursor.execute('SELECT paper_level, COUNT(*) FROM research_papers WHERE 1=1 GROUP BY paper_level')
                paper_by_level = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT patent_type, COUNT(*) FROM patents WHERE status = ? GROUP BY patent_type',
                ('granted',))
                patent_by_type = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT award_level, COUNT(*) FROM competition_awards WHERE 1=1 GROUP BY award_level')
                award_by_level = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'success': True,
                    'stats': {
                        'projects': {
                            'total': proj_row[0] or 0,
                            'total_budget': proj_row[1] or 0,
                            'spent_budget': proj_row[2] or 0
                        },
                        'papers_by_level': paper_by_level,
                        'patents_by_type': patent_by_type,
                        'awards_by_level': award_by_level
                    }
                }
        except Exception as e:
            logger.error(f'获取科研统计失败: {e}')
            return {'success': False, 'error': str(e)}







































