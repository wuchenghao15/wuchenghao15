from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育规划咨询服务 (v15.29.0) ==================================== 提供教育规划、学习规划、升学规划、职业规划等综合咨询服务。  核心能力： 1. 教育规划咨询 - 教育路径规划、学习目标设定、教育资源配置、规划评估调整 2. 学习规划指导 - 学习计划制定、课程选择指导、学习方法优化、进度跟踪管理 3. 升学规划服务 - 升学目标定位、备考策略制定、志愿填报指导、录取结果跟进 4. 职业规划服务 - 职业兴趣测评、职业路径规划、技能提升计划、就业指导服务 5. 教育政策咨询 - 政策解读分析、政策影响评估、政策合规指导、政策动态跟踪 6. 教育投资咨询 - 投资方案设计、投资风险评估、投资回报分析、投资组合优化 7. 教育管理咨询 - 学校管理诊断、管理流程优化、绩效评估体系、管理能力提升 8. 教育改革咨询 - 改革方案设计、改革实施路径、改革效果评估、改革经验总结 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_planning_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationPlanning')


# ========== 教育规划配置 ==========

# 规划类型
PLANNING_TYPES = {
    'education': {'name': '教育规划', 'description': '整体教育路径与目标规划'},
    'learning': {'name': '学习规划', 'description': '学习计划与课程安排'},
    'admission': {'name': '升学规划', 'description': '升学目标与备考策略'},
    'career': {'name': '职业规划', 'description': '职业发展路径规划'},
    'development': {'name': '发展规划', 'description': '个人发展综合规划'},
    'strategy': {'name': '战略规划', 'description': '长期战略发展规划'},
    'financial': {'name': '财务规划', 'description': '教育投资财务规划'},
    'risk': {'name': '风险管理', 'description': '教育风险评估与管理'}
}

# 咨询模式
CONSULTING_MODES = {
    'one_on_one': {'name': '一对一咨询', 'duration': '60分钟', 'price_factor': 1.0},
    'group': {'name': '小组咨询', 'duration': '90分钟', 'price_factor': 0.6},
    'online': {'name': '线上咨询', 'duration': '45分钟', 'price_factor': 0.8},
    'offline': {'name': '线下咨询', 'duration': '60分钟', 'price_factor': 1.0},
    'remote': {'name': '远程咨询', 'duration': '50分钟', 'price_factor': 0.9},
    'on_site': {'name': '现场咨询', 'duration': '120分钟', 'price_factor': 1.2},
    'special': {'name': '专题咨询', 'duration': '150分钟', 'price_factor': 1.5},
    'comprehensive': {'name': '综合咨询', 'duration': '180分钟', 'price_factor': 2.0}
}

# 教育阶段
EDUCATION_LEVELS = {
    'preschool': {'name': '学前教育', 'age_range': '3-6岁', 'focus': '启蒙教育'},
    'primary': {'name': '小学教育', 'age_range': '6-12岁', 'focus': '基础培养'},
    'junior': {'name': '初中教育', 'age_range': '12-15岁', 'focus': '能力提升'},
    'senior': {'name': '高中教育', 'age_range': '15-18岁', 'focus': '升学备考'},
    'higher': {'name': '高等教育', 'age_range': '18-22岁', 'focus': '专业深造'},
    'continuing': {'name': '继续教育', 'age_range': '22+岁', 'focus': '终身学习'},
    'vocational': {'name': '职业教育', 'age_range': '16+岁', 'focus': '技能培养'},
    'lifelong': {'name': '终身教育', 'age_range': '不限', 'focus': '持续发展'}
}

# 职业领域
CAREER_FIELDS = {
    'tech': {'name': '科技', 'sub': ['软件开发', '人工智能', '大数据', '云计算']},
    'finance': {'name': '金融', 'sub': ['投资银行', '资产管理', '保险', '金融科技']},
    'education': {'name': '教育', 'sub': ['教师', '教育管理', '教育科技', '培训']},
    'medical': {'name': '医疗', 'sub': ['医生', '护士', '药学', '医疗管理']},
    'law': {'name': '法律', 'sub': ['律师', '法官', '法务', '合规']},
    'art': {'name': '艺术', 'sub': ['设计', '音乐', '绘画', '影视']},
    'engineering': {'name': '工程', 'sub': ['机械', '电气', '土木', '自动化']},
    'management': {'name': '管理', 'sub': ['企业管理', '项目管理', '运营', '人力资源']}
}

# 政策领域
POLICY_AREAS = {
    'reform': {'name': '教育改革', 'impact': '高', 'frequency': '持续'},
    'investment': {'name': '教育投入', 'impact': '中', 'frequency': '年度'},
    'equity': {'name': '教育公平', 'impact': '高', 'frequency': '持续'},
    'quality': {'name': '教育质量', 'impact': '高', 'frequency': '持续'},
    'teacher': {'name': '教师队伍', 'impact': '中', 'frequency': '季度'},
    'curriculum': {'name': '课程改革', 'impact': '高', 'frequency': '年度'},
    'examination': {'name': '考试招生', 'impact': '高', 'frequency': '年度'},
    'international': {'name': '国际交流', 'impact': '中', 'frequency': '季度'}
}

# 投资类型
INVESTMENT_TYPES = {
    'school': {'name': '学校投资', 'risk_level': '中', 'return_period': '长期'},
    'training': {'name': '培训投资', 'risk_level': '低', 'return_period': '短期'},
    'edtech': {'name': '教育科技', 'risk_level': '高', 'return_period': '中期'},
    'real_estate': {'name': '教育地产', 'risk_level': '中', 'return_period': '长期'},
    'publishing': {'name': '教育出版', 'risk_level': '低', 'return_period': '中期'},
    'service': {'name': '教育服务', 'risk_level': '低', 'return_period': '短期'},
    'online': {'name': '在线教育', 'risk_level': '中', 'return_period': '中期'},
    'finance': {'name': '教育金融', 'risk_level': '高', 'return_period': '中期'}
}

# 管理领域
MANAGEMENT_AREAS = {
    'school': {'name': '学校管理', 'focus': '整体运营'},
    'teaching': {'name': '教学管理', 'focus': '教学质量'},
    'hr': {'name': '人事管理', 'focus': '师资建设'},
    'finance': {'name': '财务管理', 'focus': '资金运作'},
    'logistics': {'name': '后勤管理', 'focus': '服务保障'},
    'quality': {'name': '质量管理', 'focus': '标准体系'},
    'safety': {'name': '安全管理', 'focus': '风险防控'},
    'it': {'name': '信息化管理', 'focus': '技术支撑'}
}

# 改革领域
REFORM_AREAS = {
    'system': {'name': '教育体制', 'difficulty': '高', 'impact': '深远'},
    'curriculum': {'name': '课程体系', 'difficulty': '中', 'impact': '广泛'},
    'method': {'name': '教学方法', 'difficulty': '低', 'impact': '直接'},
    'evaluation': {'name': '评价体系', 'difficulty': '中', 'impact': '全面'},
    'mechanism': {'name': '管理机制', 'difficulty': '中', 'impact': '内部'},
    'model': {'name': '办学模式', 'difficulty': '高', 'impact': '外部'},
    'governance': {'name': '教育治理', 'difficulty': '高', 'impact': '宏观'},
    'ecology': {'name': '教育生态', 'difficulty': '高', 'impact': '长期'}
}


class EducationPlanningService:
    """教育规划咨询服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS planning_consulting ( consult_id TEXT PRIMARY KEY, planning_type TEXT NOT NULL, education_level TEXT, education_type TEXT NOT NULL, client_id INTEGER, client_name TEXT, consult_mode TEXT, consultant_id INTEGER, consultant_name TEXT, consult_date TEXT, duration INTEGER, status TEXT DEFAULT 'pending', goals TEXT, recommendations TEXT, follow_up_date TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS consulting_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, consult_id TEXT NOT NULL, record_type TEXT, content TEXT, recorded_by TEXT, recorded_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_planning ( plan_id TEXT PRIMARY KEY, plan_name TEXT NOT NULL, education_level TEXT, education_type TEXT NOT NULL, student_id INTEGER, student_name TEXT, target_score REAL, current_score REAL, subjects TEXT, schedule TEXT, resources TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'draft', progress REAL DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS planning_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id TEXT NOT NULL, milestone TEXT, target_date TEXT, completed INTEGER DEFAULT 0, completed_at TEXT, note TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS admission_planning ( plan_id TEXT PRIMARY KEY, plan_name TEXT NOT NULL, target_school TEXT, target_major TEXT, education_level TEXT, education_type TEXT NOT NULL, student_id INTEGER, student_name TEXT, exam_type TEXT, target_score REAL, current_score REAL, application_deadline TEXT, status TEXT DEFAULT 'draft', progress REAL DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS admission_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id TEXT NOT NULL, exam_name TEXT, exam_date TEXT, score REAL, result TEXT, note TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS career_planning ( plan_id TEXT PRIMARY KEY, plan_name TEXT NOT NULL, career_field TEXT, target_position TEXT, education_type TEXT NOT NULL, client_id INTEGER, client_name TEXT, interest_score TEXT, skill_assessment TEXT, education_background TEXT, experience TEXT, target_salary REAL, timeline TEXT, status TEXT DEFAULT 'draft', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS career_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id TEXT NOT NULL, achievement TEXT, date TEXT, type TEXT, note TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_consulting ( consult_id TEXT PRIMARY KEY, policy_area TEXT NOT NULL, education_level TEXT, education_type TEXT NOT NULL, client_id INTEGER, client_name TEXT, policy_name TEXT, policy_date TEXT, impact_analysis TEXT, recommendations TEXT, compliance_requirements TEXT, status TEXT DEFAULT 'completed', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS policy_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, consult_id TEXT NOT NULL, policy_change TEXT, effective_date TEXT, impact_level TEXT, action_required TEXT, completed INTEGER DEFAULT 0 ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS investment_consulting ( consult_id TEXT PRIMARY KEY, investment_type TEXT NOT NULL, education_type TEXT NOT NULL, client_id INTEGER, client_name TEXT, investment_amount REAL, risk_tolerance TEXT, return_objective REAL, time_horizon INTEGER, portfolio TEXT, risk_assessment TEXT, return_projection TEXT, status TEXT DEFAULT 'completed', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS investment_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, consult_id TEXT NOT NULL, investment_item TEXT, amount REAL, date TEXT, performance REAL, note TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS management_consulting ( consult_id TEXT PRIMARY KEY, management_area TEXT NOT NULL, education_type TEXT NOT NULL, client_id INTEGER, client_name TEXT, organization_name TEXT, diagnosis TEXT, recommendations TEXT, implementation_plan TEXT, timeline TEXT, budget REAL, status TEXT DEFAULT 'completed', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS management_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, consult_id TEXT NOT NULL, milestone TEXT, target_date TEXT, completed INTEGER DEFAULT 0, completed_at TEXT, responsible TEXT, note TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS reform_consulting ( consult_id TEXT PRIMARY KEY, reform_area TEXT NOT NULL, education_type TEXT NOT NULL, client_id INTEGER, client_name TEXT, organization_name TEXT, current_state TEXT, desired_state TEXT, reform_plan TEXT, risk_assessment TEXT, implementation_steps TEXT, expected_outcome TEXT, status TEXT DEFAULT 'planned', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS reform_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, consult_id TEXT NOT NULL, phase TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'pending', outcome TEXT, note TEXT ) ''')
                conn.commit()
                logger.info('教育规划咨询服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 教育规划咨询 ==========

    def create_planning_consult(self, planning_type: str, education_type: str,
                                  client_id: int, client_name: str, **kwargs) -> Dict[str, Any]:
        try:
            consult_id = f"plc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PLANNING_TYPES.get(planning_type, {})
            mode_config = CONSULTING_MODES.get(kwargs.get('consult_mode'), {})
            duration = int(mode_config.get('duration', 60))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO planning_consulting ( consult_id, planning_type, education_level, education_type, client_id, client_name, consult_mode, consultant_id, consultant_name, consult_date, duration, status, goals, recommendations, follow_up_date, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?) ''', (consult_id, planning_type, kwargs.get('education_level'),
                          education_type, client_id, client_name,
                          kwargs.get('consult_mode'), kwargs.get('consultant_id'),
                          kwargs.get('consultant_name'), kwargs.get('consult_date'),
                          duration, kwargs.get('goals'), kwargs.get('recommendations'),
                          kwargs.get('follow_up_date'), now, now))
                    conn.commit()
                    logger.info(f'创建教育规划咨询: {config.get("name", planning_type)} ({consult_id})')
                    return {'success': True, 'consult_id': consult_id}
        except Exception as e:
            logger.error(f'创建教育规划咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_planning_status(self, consult_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE planning_consulting SET status = ?, recommendations = ?, follow_up_date = ?, updated_at = ? WHERE consult_id = ? ''', (status, kwargs.get('recommendations'),
                          kwargs.get('follow_up_date'), now, consult_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '咨询记录不存在'}
        except Exception as e:
            logger.error(f'更新教育规划状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_consulting_record(self, consult_id: str, record_type: str,
                               content: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO consulting_records (consult_id, record_type, content, recorded_by, recorded_at) VALUES (?, ?, ?, ?, ?) ''', (consult_id, record_type, content,
                          kwargs.get('recorded_by'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加咨询记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_planning_history(self, client_id: int, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM planning_consulting WHERE client_id = ?'
                params = [client_id]
                if kwargs.get('planning_type'):
                    query += ' AND planning_type = ?'
                    params.append(kwargs.get('planning_type'))
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                query += ' ORDER BY consult_date DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取规划历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习规划指导 ==========

    def create_learning_plan(self, plan_name: str, education_type: str,
                              student_id: int, student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"lnp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO learning_planning ( plan_id, plan_name, education_level, education_type, student_id, student_name, target_score, current_score, subjects, schedule, resources, start_date, end_date, status, progress, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', 0, ?, ?) ''', (plan_id, plan_name, kwargs.get('education_level'),
                          education_type, student_id, student_name,
                          kwargs.get('target_score'), kwargs.get('current_score'),
                          json.dumps(kwargs.get('subjects', [])),
                          json.dumps(kwargs.get('schedule', {})),
                          json.dumps(kwargs.get('resources', [])),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建学习规划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建学习规划失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_learning_progress(self, plan_id: str, progress: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            progress = min(max(progress, 0), 100)
            status = 'completed' if progress >= 100 else 'active' if progress > 0 else 'draft'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE learning_planning SET progress = ?, status = ?, current_score = ?, updated_at = ? WHERE plan_id = ? ''', (progress, status, kwargs.get('current_score'), now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress, 'status': status}
                    return {'success': False, 'error': '学习规划不存在'}
        except Exception as e:
            logger.error(f'更新学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_plan_milestone(self, plan_id: str, milestone: str,
                            target_date: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO planning_records (plan_id, milestone, target_date, note) VALUES (?, ?, ?, ?) ''', (plan_id, milestone, target_date, kwargs.get('note')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_milestone(self, record_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE planning_records SET completed = 1, completed_at = ? WHERE id = ?',
                                 (now, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '里程碑记录不存在'}
        except Exception as e:
            logger.error(f'完成里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 升学规划服务 ==========

    def create_admission_plan(self, plan_name: str, target_school: str,
                               education_type: str, student_id: int,
                               student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"adp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO admission_planning ( plan_id, plan_name, target_school, target_major, education_level, education_type, student_id, student_name, exam_type, target_score, current_score, application_deadline, status, progress, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', 0, ?, ?) ''', (plan_id, plan_name, target_school, kwargs.get('target_major'),
                          kwargs.get('education_level'), education_type,
                          student_id, student_name, kwargs.get('exam_type'),
                          kwargs.get('target_score'), kwargs.get('current_score'),
                          kwargs.get('application_deadline'), now, now))
                    conn.commit()
                    logger.info(f'创建升学规划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建升学规划失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_exam_score(self, plan_id: str, exam_name: str, exam_date: str,
                           score: float, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO admission_records (plan_id, exam_name, exam_date, score, result, note) VALUES (?, ?, ?, ?, ?, ?) ''', (plan_id, exam_name, exam_date, score,
                          kwargs.get('result'), kwargs.get('note')))
                    cursor.execute('UPDATE admission_planning SET current_score = ?, updated_at = ? WHERE plan_id = ?',
                                 (score, datetime.now().isoformat(), plan_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录考试成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_admission_progress(self, plan_id: str, progress: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            progress = min(max(progress, 0), 100)
            status = 'completed' if progress >= 100 else 'active' if progress > 0 else 'draft'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE admission_planning SET progress = ?, status = ?, updated_at = ? WHERE plan_id = ?',
                                 (progress, status, now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress, 'status': status}
                    return {'success': False, 'error': '升学规划不存在'}
        except Exception as e:
            logger.error(f'更新升学进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_admission_status(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM admission_planning WHERE plan_id = ?', (plan_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '升学规划不存在'}
                cursor.execute('SELECT * FROM admission_records WHERE plan_id = ? ORDER BY exam_date DESC', (plan_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'plan': dict(plan), 'exam_records': records}
        except Exception as e:
            logger.error(f'获取升学状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 职业规划服务 ==========

    def create_career_plan(self, plan_name: str, career_field: str,
                            education_type: str, client_id: int,
                            client_name: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"crp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO career_planning ( plan_id, plan_name, career_field, target_position, education_type, client_id, client_name, interest_score, skill_assessment, education_background, experience, target_salary, timeline, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?) ''', (plan_id, plan_name, career_field, kwargs.get('target_position'),
                          education_type, client_id, client_name,
                          json.dumps(kwargs.get('interest_score', {})),
                          json.dumps(kwargs.get('skill_assessment', {})),
                          kwargs.get('education_background'),
                          kwargs.get('experience'), kwargs.get('target_salary'),
                          json.dumps(kwargs.get('timeline', {})), now, now))
                    conn.commit()
                    logger.info(f'创建职业规划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建职业规划失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_career_assessment(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            updates = []
            params = []
            if kwargs.get('interest_score'):
                updates.append('interest_score = ?')
                params.append(json.dumps(kwargs.get('interest_score')))
            if kwargs.get('skill_assessment'):
                updates.append('skill_assessment = ?')
                params.append(json.dumps(kwargs.get('skill_assessment')))
            if kwargs.get('target_salary') is not None:
                updates.append('target_salary = ?')
                params.append(kwargs.get('target_salary'))
            if kwargs.get('target_position'):
                updates.append('target_position = ?')
                params.append(kwargs.get('target_position'))
            if updates:
                params.append(now)
                params.append(plan_id)
                with self._lock:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f'UPDATE career_planning SET {", ".join(updates)}, updated_at = ? WHERE plan_id = ?', params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
            return {'success': False, 'error': '无更新内容或职业规划不存在'}
        except Exception as e:
            logger.error(f'更新职业评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_career_achievement(self, plan_id: str, achievement: str, date: str,
                                type: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO career_records (plan_id, achievement, date, type, note) VALUES (?, ?, ?, ?, ?) ''', (plan_id, achievement, date, type, kwargs.get('note')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加职业成就失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_career_report(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM career_planning WHERE plan_id = ?', (plan_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '职业规划不存在'}
                cursor.execute('SELECT * FROM career_records WHERE plan_id = ? ORDER BY date DESC', (plan_id,))
                achievements = [dict(a) for a in cursor.fetchall()]
                plan_dict = dict(plan)
                report = {
                    'plan_id': plan_id,
                    'plan_name': plan_dict['plan_name'],
                    'career_field': plan_dict['career_field'],
                    'target_position': plan_dict['target_position'],
                    'target_salary': plan_dict['target_salary'],
                    'achievement_count': len(achievements),
                    'recent_achievements': achievements[:5]
                }
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'生成职业报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_career_options(self, career_field: str = None) -> Dict[str, Any]:
        try:
            options = {}
            if career_field:
                if career_field in CAREER_FIELDS:
                    options[career_field] = CAREER_FIELDS[career_field]
            else:
                options = CAREER_FIELDS
            return {'success': True, 'options': options}
        except Exception as e:
            logger.error(f'获取职业选项失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育政策咨询 ==========

    def create_policy_consult(self, policy_area: str, education_type: str,
                               client_id: int, client_name: str, **kwargs) -> Dict[str, Any]:
        try:
            consult_id = f"pdc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO policy_consulting ( consult_id, policy_area, education_level, education_type, client_id, client_name, policy_name, policy_date, impact_analysis, recommendations, compliance_requirements, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?) ''', (consult_id, policy_area, kwargs.get('education_level'),
                          education_type, client_id, client_name,
                          kwargs.get('policy_name'), kwargs.get('policy_date'),
                          kwargs.get('impact_analysis'), kwargs.get('recommendations'),
                          kwargs.get('compliance_requirements'), now, now))
                    conn.commit()
                    logger.info(f'创建政策咨询: {policy_area} ({consult_id})')
                    return {'success': True, 'consult_id': consult_id}
        except Exception as e:
            logger.error(f'创建政策咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_policy_change(self, consult_id: str, policy_change: str,
                           effective_date: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO policy_records (consult_id, policy_change, effective_date, impact_level, action_required, completed) VALUES (?, ?, ?, ?, ?, 0) ''', (consult_id, policy_change, effective_date,
                          kwargs.get('impact_level'), kwargs.get('action_required')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加政策变更失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_policy_action(self, record_id: int) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE policy_records SET completed = 1 WHERE id = ?', (record_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '政策记录不存在'}
        except Exception as e:
            logger.error(f'完成政策行动失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_policy_updates(self, policy_area: str = None, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM policy_consulting WHERE 1=1'
                params = []
                if policy_area:
                    query += ' AND policy_area = ?'
                    params.append(policy_area)
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(kwargs.get('limit', 20))
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取政策更新失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育投资咨询 ==========

    def create_investment_consult(self, investment_type: str, education_type: str,
                                   client_id: int, client_name: str, **kwargs) -> Dict[str, Any]:
        try:
            consult_id = f"ivc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO investment_consulting ( consult_id, investment_type, education_type, client_id, client_name, investment_amount, risk_tolerance, return_objective, time_horizon, portfolio, risk_assessment, return_projection, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?) ''', (consult_id, investment_type, education_type,
                          client_id, client_name, kwargs.get('investment_amount'),
                          kwargs.get('risk_tolerance'), kwargs.get('return_objective'),
                          kwargs.get('time_horizon'),
                          json.dumps(kwargs.get('portfolio', {})),
                          kwargs.get('risk_assessment'),
                          kwargs.get('return_projection'), now, now))
                    conn.commit()
                    logger.info(f'创建投资咨询: {investment_type} ({consult_id})')
                    return {'success': True, 'consult_id': consult_id}
        except Exception as e:
            logger.error(f'创建投资咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_investment_record(self, consult_id: str, investment_item: str,
                               amount: float, date: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO investment_records (consult_id, investment_item, amount, date, performance, note) VALUES (?, ?, ?, ?, ?, ?) ''', (consult_id, investment_item, amount, date,
                          kwargs.get('performance'), kwargs.get('note')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加投资记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_investment_performance(self, record_id: int, performance: float) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE investment_records SET performance = ? WHERE id = ?',
                                 (performance, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'performance': performance}
                    return {'success': False, 'error': '投资记录不存在'}
        except Exception as e:
            logger.error(f'更新投资表现失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_investment_summary(self, client_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM investment_consulting WHERE client_id = ? ORDER BY created_at DESC',
                (client_id,))
                consults = [dict(c) for c in cursor.fetchall()]
                total_investment = sum(c.get('investment_amount', 0) for c in consults)
                return {'success': True, 'total_investment': total_investment, 'consults': consults}
        except Exception as e:
            logger.error(f'获取投资汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育管理咨询 ==========

    def create_management_consult(self, management_area: str, education_type: str,
                                   client_id: int, client_name: str, **kwargs) -> Dict[str, Any]:
        try:
            consult_id = f"mgc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO management_consulting ( consult_id, management_area, education_type, client_id, client_name, organization_name, diagnosis, recommendations, implementation_plan, timeline, budget, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?) ''', (consult_id, management_area, education_type,
                          client_id, client_name, kwargs.get('organization_name'),
                          kwargs.get('diagnosis'), kwargs.get('recommendations'),
                          kwargs.get('implementation_plan'),
                          json.dumps(kwargs.get('timeline', {})),
                          kwargs.get('budget'), now, now))
                    conn.commit()
                    logger.info(f'创建管理咨询: {management_area} ({consult_id})')
                    return {'success': True, 'consult_id': consult_id}
        except Exception as e:
            logger.error(f'创建管理咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_management_milestone(self, consult_id: str, milestone: str,
                                  target_date: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO management_records (consult_id, milestone, target_date, responsible, note) VALUES (?, ?, ?, ?, ?) ''', (consult_id, milestone, target_date,
                          kwargs.get('responsible'), kwargs.get('note')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加管理里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_management_milestone(self, record_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE management_records SET completed = 1, completed_at = ? WHERE id = ?',
                                 (now, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '管理记录不存在'}
        except Exception as e:
            logger.error(f'完成管理里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_management_status(self, consult_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM management_consulting WHERE consult_id = ?', (consult_id,))
                consult = cursor.fetchone()
                if not consult:
                    return {'success': False, 'error': '管理咨询不存在'}
                cursor.execute('SELECT * FROM management_records WHERE consult_id = ? ORDER BY target_date',
                (consult_id,))
                records = [dict(r) for r in cursor.fetchall()]
                completed = sum(1 for r in records if r.get('completed') == 1)
                total = len(records)
                progress = (completed / total * 100) if total > 0 else 0
                return {'success': True, 'consult': dict(consult), 'milestones': records, 'progress': progress}
        except Exception as e:
            logger.error(f'获取管理状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育改革咨询 ==========

    def create_reform_consult(self, reform_area: str, education_type: str,
                               client_id: int, client_name: str, **kwargs) -> Dict[str, Any]:
        try:
            consult_id = f"rfc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO reform_consulting ( consult_id, reform_area, education_type, client_id, client_name, organization_name, current_state, desired_state, reform_plan, risk_assessment, implementation_steps, expected_outcome, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?) ''', (consult_id, reform_area, education_type,
                          client_id, client_name, kwargs.get('organization_name'),
                          kwargs.get('current_state'), kwargs.get('desired_state'),
                          kwargs.get('reform_plan'), kwargs.get('risk_assessment'),
                          kwargs.get('implementation_steps'),
                          kwargs.get('expected_outcome'), now, now))
                    conn.commit()
                    logger.info(f'创建改革咨询: {reform_area} ({consult_id})')
                    return {'success': True, 'consult_id': consult_id}
        except Exception as e:
            logger.error(f'创建改革咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_reform_phase(self, consult_id: str, phase: str, start_date: str,
                          end_date: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO reform_records (consult_id, phase, start_date, end_date, status, outcome, note) VALUES (?, ?, ?, ?, 'pending', ?, ?) ''', (consult_id, phase, start_date, end_date,
                          kwargs.get('outcome'), kwargs.get('note')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加改革阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_reform_phase_status(self, record_id: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE reform_records SET status = ?, outcome = ?, updated_at = ? WHERE id = ?',
                                 (status, kwargs.get('outcome'), now, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '改革记录不存在'}
        except Exception as e:
            logger.error(f'更新改革阶段状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_reform_progress(self, consult_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM reform_consulting WHERE consult_id = ?', (consult_id,))
                consult = cursor.fetchone()
                if not consult:
                    return {'success': False, 'error': '改革咨询不存在'}
                cursor.execute('SELECT * FROM reform_records WHERE consult_id = ? ORDER BY start_date', (consult_id,))
                phases = [dict(p) for p in cursor.fetchall()]
                completed = sum(1 for p in phases if p.get('status') == 'completed')
                total = len(phases)
                progress = (completed / total * 100) if total > 0 else 0
                return {'success': True, 'consult': dict(consult), 'phases': phases, 'progress': progress}
        except Exception as e:
            logger.error(f'获取改革进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计与报表 ==========

    def get_service_statistics(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                cursor.execute('SELECT COUNT(*) FROM planning_consulting')
                stats['total_planning_consults'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM learning_planning')
                stats['total_learning_plans'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM admission_planning')
                stats['total_admission_plans'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM career_planning')
                stats['total_career_plans'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM policy_consulting')
                stats['total_policy_consults'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM investment_consulting')
                stats['total_investment_consults'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM management_consulting')
                stats['total_management_consults'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM reform_consulting')
                stats['total_reform_consults'] = cursor.fetchone()[0]

                cursor.execute('SELECT education_type, COUNT(*) FROM planning_consulting GROUP BY education_type')
                stats['planning_by_type'] = {r[0]: r[1] for r in cursor.fetchall()}

                cursor.execute('SELECT planning_type, COUNT(*) FROM planning_consulting GROUP BY planning_type')
                stats['planning_by_category'] = {r[0]: r[1] for r in cursor.fetchall()}

                if kwargs.get('client_id'):
                    client_id = kwargs.get('client_id')
                    cursor.execute('SELECT COUNT(*) FROM planning_consulting WHERE client_id = ?', (client_id,))
                    stats['client_planning_consults'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM learning_planning WHERE student_id = ?', (client_id,))
                    stats['client_learning_plans'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM admission_planning WHERE student_id = ?', (client_id,))
                    stats['client_admission_plans'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM career_planning WHERE client_id = ?', (client_id,))
                    stats['client_career_plans'] = cursor.fetchone()[0]

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取服务统计失败: {e}')
            return {'success': False, 'error': str(e)}