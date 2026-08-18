from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育可持续发展服务 (v15.23.0) ==================================== 提供绿色校园建设、可持续教育、环境教育、社会责任教育、教育公平、 资源优化配置、教育生态保护和可持续发展评估等综合管理服务。  核心能力： 1. 绿色校园 - 节能减排、可再生能源、绿色建筑、垃圾分类 2. 可持续教育 - 可持续发展课程、绿色教育理念、环保实践 3. 环境教育 - 环境科学、生态保护、气候变化、污染防治 4. 社会责任 - 公益教育、志愿服务、社区服务、社会关怀 5. 教育公平 - 教育机会平等、资源均衡分配、特殊教育保障 6. 资源优化 - 资源配置、资源共享、资源利用效率、资源节约 7. 生态保护 - 校园生态、生物多样性、生态修复、生态平衡 8. 评估体系 - 环境绩效、社会绩效、经济绩效、教育质量 9. 指标管理 - 可持续能力、公平程度、资源效率、生态健康 10. 统计分析 - 综合数据分析与报告 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_sustainability_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationSustainability')


# ========== 教育可持续发展配置 ==========

GREEN_CAMPUS = {
    'energy_saving': {'name': '节能减排', 'sub': ['能耗监测', '节能改造', '能效提升', '碳排放管理']},
    'renewable_energy': {'name': '可再生能源', 'sub': ['太阳能', '风能', '地热能', '生物质能']},
    'green_building': {'name': '绿色建筑', 'sub': ['绿色认证', '节能设计', '环保材料', '自然采光']},
    'waste_classification': {'name': '垃圾分类', 'sub': ['分类设施', '回收利用', '减量化', '资源化']},
    'water_management': {'name': '水资源管理', 'sub': ['节水设施', '中水回用', '雨水收集', '水质监测']},
    'greening': {'name': '绿化美化', 'sub': ['校园绿化', '屋顶花园', '垂直绿化', '景观设计']},
    'environmental_facilities': {'name': '环保设施', 'sub': ['污水处理', '空气净化', '噪声控制', '环保设备']},
    'low_carbon_life': {'name': '低碳生活', 'sub': ['低碳出行', '无纸化办公', '节约用电', '绿色消费']}
}

SUSTAINABLE_EDUCATION = {
    'sd_courses': {'name': '可持续发展课程', 'sub': ['SDGs教育', '可持续发展概论', '绿色经济学', '环境政策']},
    'green_education': {'name': '绿色教育理念', 'sub': ['生态文明', '绿色校园文化', '环保意识', '可持续价值观']},
    'environmental_practice': {'name': '环保实践', 'sub': ['环保活动', '实践项目', '实地考察', '实验研究']},
    'ecological_civilization': {'name': '生态文明教育', 'sub': ['生态文明理论', '生态伦理', '人与自然和谐']},
    'circular_economy': {'name': '循环经济教育', 'sub': ['循环经济原理', '资源循环利用', '绿色产业']},
    'green_technology': {'name': '绿色技术教育', 'sub': ['新能源技术', '节能环保技术', '绿色信息技术']},
    'sustainable_capability': {'name': '可持续发展能力', 'sub': ['系统思维', '创新能力', '协作能力', '决策能力']},
    'lifelong_learning': {'name': '终身学习', 'sub': ['继续教育', '职业培训', '技能提升', '知识更新']}
}

ENVIRONMENTAL_EDUCATION = {
    'environmental_science': {'name': '环境科学', 'sub': ['环境化学', '环境生物学', '环境物理学', '环境工程']},
    'ecological_protection': {'name': '生态保护', 'sub': ['生态系统', '生物多样性', '自然保护', '生态修复']},
    'climate_change': {'name': '气候变化', 'sub': ['全球变暖', '碳减排', '气候适应', '低碳发展']},
    'pollution_control': {'name': '污染防治', 'sub': ['水污染治理', '大气污染治理', '固体废弃物处理', '噪声治理']},
    'natural_resources': {'name': '自然资源保护', 'sub': ['水资源保护', '土地资源', '森林资源', '矿产资源']},
    'environmental_management': {'name': '环境管理', 'sub': ['环境规划', '环境监测', '环境影响评价']},
    'environmental_laws': {'name': '环境法规', 'sub': ['环境保护法', '环境标准', '环境政策', '国际公约']},
    'environmental_ethics': {'name': '环境伦理', 'sub': ['环境道德', '生态正义', '可持续伦理']}
}

SOCIAL_RESPONSIBILITY = {
    'public_welfare': {'name': '公益教育', 'sub': ['公益理念', '慈善教育', '社会责任意识']},
    'volunteer_service': {'name': '志愿服务', 'sub': ['志愿者招募', '志愿活动', '志愿培训', '志愿时长']},
    'community_service': {'name': '社区服务', 'sub': ['社区实践', '社区建设', '社区调研', '社区联动']},
    'social_care': {'name': '社会关怀', 'sub': ['弱势群体关怀', '公益捐赠', '扶贫帮困']},
    'fairness_justice': {'name': '公平正义', 'sub': ['社会公平', '司法公正', '权利保障']},
    'public_interest': {'name': '公共利益', 'sub': ['公共事务', '公共政策', '公共参与']},
    'citizen_education': {'name': '公民教育', 'sub': ['公民意识', '公民权利', '公民责任']},
    'social_participation': {'name': '社会参与', 'sub': ['社会实践', '社会调研', '社会创新']}
}

EDUCATION_EQUITY = {
    'equal_opportunity': {'name': '教育机会平等', 'sub': ['入学机会', '升学机会', '就业机会']},
    'resource_balance': {'name': '资源均衡分配', 'sub': ['师资均衡', '设施均衡', '经费均衡']},
    'special_education': {'name': '特殊教育保障', 'sub': ['残疾教育', '融合教育', '个别化教育']},
    'disadvantaged_groups': {'name': '弱势群体教育', 'sub': ['贫困学生', '留守儿童', '流动儿童']},
    'urban_rural_integration': {'name': '城乡教育一体化', 'sub': ['城乡师资交流', '城乡资源共享', '城乡差距缩小']},
    'regional_coordination': {'name': '区域教育协调', 'sub': ['区域合作', '教育联盟', '资源统筹']},
    'quality_sharing': {'name': '优质教育共享', 'sub': ['名校带动', '在线教育', '教育帮扶']},
    'education_poverty_alleviation': {'name': '教育扶贫', 'sub': ['资助政策', '对口支援', '教育脱贫']}
}

RESOURCE_OPTIMIZATION = {
    'resource_allocation': {'name': '资源配置', 'sub': ['师资配置', '设备配置', '经费配置']},
    'resource_sharing': {'name': '资源共享', 'sub': ['校际共享', '区域共享', '平台共享']},
    'resource_efficiency': {'name': '资源利用效率', 'sub': ['利用率提升', '效能评估', '优化改进']},
    'resource_conservation': {'name': '资源节约', 'sub': ['节约用电', '节约用水', '节约用纸']},
    'resource_circulation': {'name': '资源循环', 'sub': ['教材循环', '设备循环', '资源再生']},
    'resource_regeneration': {'name': '资源再生', 'sub': ['废物利用', '能源回收', '材料再生']},
    'smart_management': {'name': '智慧管理', 'sub': ['智慧校园', '智能设备', '数据分析']},
    'sustainable_consumption': {'name': '可持续消费', 'sub': ['绿色采购', '节能减排', '低碳生活']}
}

ECOSYSTEM_PROTECTION = {
    'campus_ecology': {'name': '校园生态', 'sub': ['生态系统保护', '生态环境改善', '生态景观']},
    'biodiversity': {'name': '生物多样性', 'sub': ['物种保护', '栖息地保护', '生态廊道']},
    'ecological_restoration': {'name': '生态修复', 'sub': ['退化生态修复', '植被恢复', '湿地保护']},
    'ecological_balance': {'name': '生态平衡', 'sub': ['生态系统稳定', '食物链平衡', '生态承载力']},
    'ecological_monitoring': {'name': '生态监测', 'sub': ['环境监测', '生态评估', '数据采集']},
    'ecological_education': {'name': '生态教育', 'sub': ['生态课程', '实践活动', '科普宣传']},
    'ecological_planning': {'name': '生态规划', 'sub': ['生态设计', '绿色发展规划', '可持续布局']},
    'ecological_construction': {'name': '生态建设', 'sub': ['生态工程', '绿化建设', '环保设施']}
}

ASSESSMENT_CRITERIA = {
    'environmental_performance': {'name': '环境绩效', 'sub': ['节能减排', '污染控制', '资源节约']},
    'social_performance': {'name': '社会绩效', 'sub': ['公益贡献', '社区服务', '社会责任']},
    'economic_performance': {'name': '经济绩效', 'sub': ['成本效益', '资源效率', '可持续投资']},
    'education_quality': {'name': '教育质量', 'sub': ['教学水平', '学习成果', '发展成效']},
    'sustainable_capability': {'name': '可持续能力', 'sub': ['创新能力', '适应能力', '发展潜力']},
    'fairness_degree': {'name': '公平程度', 'sub': ['机会平等', '资源均衡', '差距缩小']},
    'resource_efficiency': {'name': '资源效率', 'sub': ['利用效率', '共享程度', '循环利用']},
    'ecological_health': {'name': '生态健康', 'sub': ['生态系统健康', '生物多样性', '环境质量']}
}


class EducationSustainabilityService:
    """教育可持续发展服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS green_campus ( campus_id TEXT PRIMARY KEY, campus_name TEXT NOT NULL, energy_saving_target REAL, carbon_emission REAL, renewable_energy_ratio REAL, waste_recycling_rate REAL, water_saving_rate REAL, greening_area REAL, environmental_certification TEXT, status TEXT DEFAULT 'active', education_type TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS campus_initiatives ( initiative_id TEXT PRIMARY KEY, campus_id TEXT NOT NULL, initiative_name TEXT NOT NULL, initiative_type TEXT, description TEXT, start_date TEXT, end_date TEXT, budget REAL, progress REAL DEFAULT 0, responsible_person TEXT, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS sustainable_education ( program_id TEXT PRIMARY KEY, program_name TEXT NOT NULL, program_type TEXT, education_type TEXT, grade_level INTEGER, course_count INTEGER DEFAULT 0, student_count INTEGER DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS education_programs ( ep_id TEXT PRIMARY KEY, program_id TEXT NOT NULL, course_name TEXT NOT NULL, course_type TEXT, teacher_id INTEGER, teacher_name TEXT, education_type TEXT, grade_level INTEGER, semester TEXT, credit_hours INTEGER DEFAULT 3, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS environmental_education ( ee_id TEXT PRIMARY KEY, program_name TEXT NOT NULL, program_type TEXT, education_type TEXT, target_group TEXT, activity_count INTEGER DEFAULT 0, participant_count INTEGER DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS eco_curriculum ( ec_id TEXT PRIMARY KEY, ee_id TEXT NOT NULL, curriculum_name TEXT NOT NULL, curriculum_type TEXT, education_type TEXT, grade_level INTEGER, duration_hours REAL, resource_materials TEXT, assessment_method TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS social_responsibility ( sr_id TEXT PRIMARY KEY, program_name TEXT NOT NULL, program_type TEXT, education_type TEXT, target_group TEXT, activity_count INTEGER DEFAULT 0, volunteer_hours REAL DEFAULT 0, impact_score REAL DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS responsibility_projects ( rp_id TEXT PRIMARY KEY, sr_id TEXT NOT NULL, project_name TEXT NOT NULL, project_type TEXT, education_type TEXT, start_date TEXT, end_date TEXT, target_beneficiaries INTEGER, actual_beneficiaries INTEGER DEFAULT 0, budget REAL, responsible_person TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS education_equity ( eq_id TEXT PRIMARY KEY, program_name TEXT NOT NULL, program_type TEXT, education_type TEXT, target_group TEXT, coverage_rate REAL DEFAULT 0, equity_index REAL DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS equity_measures ( em_id TEXT PRIMARY KEY, eq_id TEXT NOT NULL, measure_name TEXT NOT NULL, measure_type TEXT, education_type TEXT, target_population INTEGER, reached_population INTEGER DEFAULT 0, allocated_budget REAL, utilized_budget REAL DEFAULT 0, effectiveness REAL DEFAULT 0, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_optimization ( ro_id TEXT PRIMARY KEY, program_name TEXT NOT NULL, program_type TEXT, education_type TEXT, resource_type TEXT, optimization_rate REAL DEFAULT 0, cost_saving REAL DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_allocation ( ra_id TEXT PRIMARY KEY, ro_id TEXT NOT NULL, resource_name TEXT NOT NULL, resource_type TEXT, education_type TEXT, allocated_amount REAL, used_amount REAL DEFAULT 0, efficiency_rate REAL DEFAULT 0, allocation_strategy TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ecosystem_protection ( ep_id TEXT PRIMARY KEY, program_name TEXT NOT NULL, program_type TEXT, education_type TEXT, protected_area REAL DEFAULT 0, biodiversity_index REAL DEFAULT 0, ecological_health REAL DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS eco_projects ( proj_id TEXT PRIMARY KEY, ep_id TEXT NOT NULL, project_name TEXT NOT NULL, project_type TEXT, education_type TEXT, start_date TEXT, end_date TEXT, target_area REAL, achieved_area REAL DEFAULT 0, budget REAL, responsible_person TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS sustainability_assessment ( sa_id TEXT PRIMARY KEY, assessment_name TEXT NOT NULL, assessment_type TEXT, education_type TEXT, campus_id TEXT, assessment_period TEXT, overall_score REAL DEFAULT 0, status TEXT DEFAULT 'pending', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS assessment_results ( ar_id TEXT PRIMARY KEY, sa_id TEXT NOT NULL, criterion_type TEXT, score REAL DEFAULT 0, weight REAL DEFAULT 0, weighted_score REAL DEFAULT 0, comments TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS sustainability_metrics ( metric_id TEXT PRIMARY KEY, metric_name TEXT NOT NULL, metric_type TEXT, unit TEXT, target_value REAL, baseline_value REAL, education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS metric_data ( md_id TEXT PRIMARY KEY, metric_id TEXT NOT NULL, period TEXT, actual_value REAL, target_value REAL, deviation REAL DEFAULT 0, education_type TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS sustainability_alerts ( alert_id TEXT PRIMARY KEY, alert_name TEXT NOT NULL, alert_type TEXT, metric_id TEXT, threshold REAL, current_value REAL, severity TEXT DEFAULT 'warning', education_type TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS alert_history ( ah_id TEXT PRIMARY KEY, alert_id TEXT NOT NULL, trigger_time TEXT, trigger_value REAL, resolved_time TEXT, resolution_method TEXT, status TEXT DEFAULT 'triggered', created_at TEXT ) ''')
                conn.commit()
                logger.info('教育可持续发展服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 绿色校园 ==========

    def create_green_campus(self, campus_name: str, **kwargs) -> Dict[str, Any]:
        try:
            campus_id = f"gc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO green_campus ( campus_id, campus_name, energy_saving_target, carbon_emission, renewable_energy_ratio, waste_recycling_rate, water_saving_rate, greening_area, environmental_certification, status, education_type, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?) ''', (campus_id, campus_name,
                          kwargs.get('energy_saving_target'),
                          kwargs.get('carbon_emission'),
                          kwargs.get('renewable_energy_ratio'),
                          kwargs.get('waste_recycling_rate'),
                          kwargs.get('water_saving_rate'),
                          kwargs.get('greening_area'),
                          kwargs.get('environmental_certification'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建绿色校园: {campus_name} ({campus_id})')
                    return {'success': True, 'campus_id': campus_id}
        except Exception as e:
            logger.error(f'创建绿色校园失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_campus_initiative(self, campus_id: str, initiative_name: str,
                              initiative_type: str, **kwargs) -> Dict[str, Any]:
        try:
            initiative_id = f"ci_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM green_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    cursor.execute(''' INSERT INTO campus_initiatives ( initiative_id, campus_id, initiative_name, initiative_type, description, start_date, end_date, budget, progress, responsible_person, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?) ''', (initiative_id, campus_id, initiative_name,
                          initiative_type, kwargs.get('description'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('budget', 0), kwargs.get('responsible_person'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'添加校园举措: {initiative_name} ({initiative_id})')
                    return {'success': True, 'initiative_id': initiative_id}
        except Exception as e:
            logger.error(f'添加校园举措失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_initiative_progress(self, initiative_id: str, progress: float,
                                    **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE campus_initiatives SET progress = ?, updated_at = ? WHERE initiative_id = ?',
                                 (progress, now, initiative_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress}
                    return {'success': False, 'error': '举措不存在'}
        except Exception as e:
            logger.error(f'更新举措进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_green_campuses(self, education_type: str = None,
                            status: str = 'active', page: int = 1,
                            page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM green_campus WHERE 1=1'
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
                campuses = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'campuses': campuses, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取绿色校园列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 可持续教育 ==========

    def create_sustainable_program(self, program_name: str, program_type: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"sep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO sustainable_education ( program_id, program_name, program_type, education_type, grade_level, course_count, student_count, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, 'active', ?, ?) ''', (program_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建可持续教育项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建可持续教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_education_course(self, program_id: str, course_name: str,
                             course_type: str, **kwargs) -> Dict[str, Any]:
        try:
            ep_id = f"ec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM sustainable_education WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute(''' INSERT INTO education_programs ( ep_id, program_id, course_name, course_type, teacher_id, teacher_name, education_type, grade_level, semester, credit_hours, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (ep_id, program_id, course_name, course_type,
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('semester'), kwargs.get('credit_hours', 3),
                          kwargs.get('description'), now, now))
                    cursor.execute('UPDATE sustainable_education SET course_count = course_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                    conn.commit()
                    return {'success': True, 'ep_id': ep_id}
        except Exception as e:
            logger.error(f'添加教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_student(self, program_id: str, student_id: int,
                       student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM sustainable_education WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('UPDATE sustainable_education SET student_count = student_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'学生报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_sustainable_programs(self, education_type: str = None,
                                   program_type: str = None, page: int = 1,
                                   page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM sustainable_education WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if program_type:
                    query += ' AND program_type = ?'
                    params.append(program_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取可持续教育项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 环境教育 ==========

    def create_environmental_program(self, program_name: str, program_type: str,
                                      **kwargs) -> Dict[str, Any]:
        try:
            ee_id = f"eep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO environmental_education ( ee_id, program_name, program_type, education_type, target_group, activity_count, participant_count, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, 'active', ?, ?) ''', (ee_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('target_group'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建环境教育项目: {program_name} ({ee_id})')
                    return {'success': True, 'ee_id': ee_id}
        except Exception as e:
            logger.error(f'创建环境教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_eco_curriculum(self, ee_id: str, curriculum_name: str,
                           curriculum_type: str, **kwargs) -> Dict[str, Any]:
        try:
            ec_id = f"ecc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM environmental_education WHERE ee_id = ?', (ee_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute(''' INSERT INTO eco_curriculum ( ec_id, ee_id, curriculum_name, curriculum_type, education_type, grade_level, duration_hours, resource_materials, assessment_method, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (ec_id, ee_id, curriculum_name, curriculum_type,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('duration_hours'), kwargs.get('resource_materials'),
                          kwargs.get('assessment_method'), now, now))
                    conn.commit()
                    return {'success': True, 'ec_id': ec_id}
        except Exception as e:
            logger.error(f'添加生态课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_activity(self, ee_id: str, participant_count: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE environmental_education SET activity_count = activity_count + 1, participant_count = participant_count + ?, updated_at = ? WHERE ee_id = ?',
                                 (participant_count, now, ee_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'记录活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_environmental_programs(self, education_type: str = None,
                                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM environmental_education WHERE 1=1'
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
            logger.error(f'获取环境教育项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 社会责任 ==========

    def create_social_program(self, program_name: str, program_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            sr_id = f"sr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO social_responsibility ( sr_id, program_name, program_type, education_type, target_group, activity_count, volunteer_hours, impact_score, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, 'active', ?, ?) ''', (sr_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('target_group'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建社会责任项目: {program_name} ({sr_id})')
                    return {'success': True, 'sr_id': sr_id}
        except Exception as e:
            logger.error(f'创建社会责任项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_responsibility_project(self, sr_id: str, project_name: str,
                                    project_type: str, **kwargs) -> Dict[str, Any]:
        try:
            rp_id = f"rp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM social_responsibility WHERE sr_id = ?', (sr_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute(''' INSERT INTO responsibility_projects ( rp_id, sr_id, project_name, project_type, education_type, start_date, end_date, target_beneficiaries, actual_beneficiaries, budget, responsible_person, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?) ''', (rp_id, sr_id, project_name, project_type,
                          kwargs.get('education_type'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('target_beneficiaries'),
                          kwargs.get('budget', 0), kwargs.get('responsible_person'),
                          now, now))
                    cursor.execute('UPDATE social_responsibility SET activity_count = activity_count + 1, updated_at = ? WHERE sr_id = ?', (now, sr_id))
                    conn.commit()
                    return {'success': True, 'rp_id': rp_id}
        except Exception as e:
            logger.error(f'添加责任项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_volunteer_hours(self, sr_id: str, hours: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE social_responsibility SET volunteer_hours = volunteer_hours + ?, updated_at = ? WHERE sr_id = ?',
                                 (hours, now, sr_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'记录志愿时长失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_impact_score(self, sr_id: str, impact_score: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE social_responsibility SET impact_score = ?, updated_at = ? WHERE sr_id = ?',
                                 (impact_score, now, sr_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'impact_score': impact_score}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新影响评分失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_social_programs(self, education_type: str = None,
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM social_responsibility WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY impact_score DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社会责任项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育公平 ==========

    def create_equity_program(self, program_name: str, program_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            eq_id = f"eq_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO education_equity ( eq_id, program_name, program_type, education_type, target_group, coverage_rate, equity_index, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, 'active', ?, ?) ''', (eq_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('target_group'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建教育公平项目: {program_name} ({eq_id})')
                    return {'success': True, 'eq_id': eq_id}
        except Exception as e:
            logger.error(f'创建教育公平项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_equity_measure(self, eq_id: str, measure_name: str,
                           measure_type: str, **kwargs) -> Dict[str, Any]:
        try:
            em_id = f"em_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM education_equity WHERE eq_id = ?', (eq_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute(''' INSERT INTO equity_measures ( em_id, eq_id, measure_name, measure_type, education_type, target_population, reached_population, allocated_budget, utilized_budget, effectiveness, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, 0, 'active', ?, ?) ''', (em_id, eq_id, measure_name, measure_type,
                          kwargs.get('education_type'), kwargs.get('target_population'),
                          kwargs.get('allocated_budget', 0), now, now))
                    conn.commit()
                    return {'success': True, 'em_id': em_id}
        except Exception as e:
            logger.error(f'添加公平措施失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_measure_effectiveness(self, em_id: str, reached_population: int,
                                     utilized_budget: float, effectiveness: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE equity_measures SET reached_population = ?, utilized_budget = ?, effectiveness = ?, updated_at = ? WHERE em_id = ?',
                                 (reached_population, utilized_budget, effectiveness, now, em_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'effectiveness': effectiveness}
                    return {'success': False, 'error': '措施不存在'}
        except Exception as e:
            logger.error(f'更新措施效果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_equity_programs(self, education_type: str = None,
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_equity WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY equity_index DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教育公平项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源优化 ==========

    def create_resource_program(self, program_name: str, program_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            ro_id = f"ro_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO resource_optimization ( ro_id, program_name, program_type, education_type, resource_type, optimization_rate, cost_saving, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, 'active', ?, ?) ''', (ro_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('resource_type'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建资源优化项目: {program_name} ({ro_id})')
                    return {'success': True, 'ro_id': ro_id}
        except Exception as e:
            logger.error(f'创建资源优化项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_resource_allocation(self, ro_id: str, resource_name: str,
                                resource_type: str, **kwargs) -> Dict[str, Any]:
        try:
            ra_id = f"ra_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM resource_optimization WHERE ro_id = ?', (ro_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute(''' INSERT INTO resource_allocation ( ra_id, ro_id, resource_name, resource_type, education_type, allocated_amount, used_amount, efficiency_rate, allocation_strategy, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, 'active', ?, ?) ''', (ra_id, ro_id, resource_name, resource_type,
                          kwargs.get('education_type'), kwargs.get('allocated_amount', 0),
                          kwargs.get('allocation_strategy'), now, now))
                    conn.commit()
                    return {'success': True, 'ra_id': ra_id}
        except Exception as e:
            logger.error(f'添加资源分配失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_resource_efficiency(self, ra_id: str, used_amount: float,
                                    efficiency_rate: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE resource_allocation SET used_amount = ?, efficiency_rate = ?, updated_at = ? WHERE ra_id = ?',
                                 (used_amount, efficiency_rate, now, ra_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'efficiency_rate': efficiency_rate}
                    return {'success': False, 'error': '资源分配不存在'}
        except Exception as e:
            logger.error(f'更新资源效率失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_resource_programs(self, education_type: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM resource_optimization WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY optimization_rate DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资源优化项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 生态保护 ==========

    def create_eco_program(self, program_name: str, program_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            ep_id = f"ecp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ecosystem_protection ( ep_id, program_name, program_type, education_type, protected_area, biodiversity_index, ecological_health, description, status, created_at, updated_at ) VALUES (?, ?, ?, ?, 0, 0, 0, ?, 'active', ?, ?) ''', (ep_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建生态保护项目: {program_name} ({ep_id})')
                    return {'success': True, 'ep_id': ep_id}
        except Exception as e:
            logger.error(f'创建生态保护项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_eco_project(self, ep_id: str, project_name: str,
                         project_type: str, **kwargs) -> Dict[str, Any]:
        try:
            proj_id = f"epj_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM ecosystem_protection WHERE ep_id = ?', (ep_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute(''' INSERT INTO eco_projects ( proj_id, ep_id, project_name, project_type, education_type, start_date, end_date, target_area, achieved_area, budget, responsible_person, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?) ''', (proj_id, ep_id, project_name, project_type,
                          kwargs.get('education_type'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('target_area', 0),
                          kwargs.get('budget', 0), kwargs.get('responsible_person'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'proj_id': proj_id}
        except Exception as e:
            logger.error(f'添加生态项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_eco_project_progress(self, proj_id: str, achieved_area: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE eco_projects SET achieved_area = ?, updated_at = ? WHERE proj_id = ?',
                                 (achieved_area, now, proj_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'achieved_area': achieved_area}
                    return {'success': False, 'error': '生态项目不存在'}
        except Exception as e:
            logger.error(f'更新生态项目进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_eco_programs(self, education_type: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ecosystem_protection WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY ecological_health DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取生态保护项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 评估体系 ==========

    def create_assessment(self, assessment_name: str, assessment_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            sa_id = f"sa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO sustainability_assessment ( sa_id, assessment_name, assessment_type, education_type, campus_id, assessment_period, overall_score, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 0, 'pending', ?, ?) ''', (sa_id, assessment_name, assessment_type,
                          kwargs.get('education_type'), kwargs.get('campus_id'),
                          kwargs.get('assessment_period'), now, now))
                    conn.commit()
                    logger.info(f'创建可持续性评估: {assessment_name} ({sa_id})')
                    return {'success': True, 'sa_id': sa_id}
        except Exception as e:
            logger.error(f'创建可持续性评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_assessment_result(self, sa_id: str, criterion_type: str,
                               score: float, weight: float = 0.125) -> Dict[str, Any]:
        try:
            ar_id = f"ar_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            weighted_score = score * weight
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM sustainability_assessment WHERE sa_id = ?', (sa_id,))
                    assessment = cursor.fetchone()
                    if not assessment:
                        return {'success': False, 'error': '评估不存在'}
                    cursor.execute(''' INSERT INTO assessment_results ( ar_id, sa_id, criterion_type, score, weight, weighted_score, comments, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (ar_id, sa_id, criterion_type, score, weight, weighted_score,
                          None, now))
                    cursor.execute('SELECT SUM(weighted_score) FROM assessment_results WHERE sa_id = ?', (sa_id,))
                    total = cursor.fetchone()[0] or 0
                    cursor.execute('UPDATE sustainability_assessment SET overall_score = ?, updated_at = ? WHERE sa_id = ?',
                                 (round(total, 2), now, sa_id))
                    conn.commit()
                    return {'success': True, 'weighted_score': weighted_score, 'overall_score': round(total, 2)}
        except Exception as e:
            logger.error(f'添加评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_assessment(self, sa_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE sustainability_assessment SET status = ?, updated_at = ? WHERE sa_id = ? AND status = ?',
                                 ('completed', now, sa_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'completed'}
                    return {'success': False, 'error': '评估状态不允许完成'}
        except Exception as e:
            logger.error(f'完成评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_assessments(self, education_type: str = None,
                          status: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM sustainability_assessment WHERE 1=1'
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
                assessments = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assessments': assessments, 'total': total, 'page': page,
                'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评估列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 指标管理 ==========

    def create_metric(self, metric_name: str, metric_type: str,
                       unit: str, **kwargs) -> Dict[str, Any]:
        try:
            metric_id = f"sm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO sustainability_metrics ( metric_id, metric_name, metric_type, unit, target_value, baseline_value, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (metric_id, metric_name, metric_type, unit,
                          kwargs.get('target_value'), kwargs.get('baseline_value'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建可持续性指标: {metric_name} ({metric_id})')
                    return {'success': True, 'metric_id': metric_id}
        except Exception as e:
            logger.error(f'创建可持续性指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_metric_data(self, metric_id: str, period: str,
                            actual_value: float, **kwargs) -> Dict[str, Any]:
        try:
            md_id = f"md_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            target_value = kwargs.get('target_value')
            deviation = actual_value - target_value if target_value else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM sustainability_metrics WHERE metric_id = ?', (metric_id,))
                    metric = cursor.fetchone()
                    if not metric:
                        return {'success': False, 'error': '指标不存在'}
                    cursor.execute(''' INSERT INTO metric_data ( md_id, metric_id, period, actual_value, target_value, deviation, education_type, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (md_id, metric_id, period, actual_value,
                          target_value, deviation, kwargs.get('education_type'), now))
                    conn.commit()
                    return {'success': True, 'md_id': md_id, 'deviation': deviation}
        except Exception as e:
            logger.error(f'记录指标数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_alert(self, alert_name: str, alert_type: str,
                     metric_id: str, threshold: float, **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"al_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM sustainability_metrics WHERE metric_id = ?', (metric_id,))
                    metric = cursor.fetchone()
                    if not metric:
                        return {'success': False, 'error': '指标不存在'}
                    cursor.execute(''' INSERT INTO sustainability_alerts ( alert_id, alert_name, alert_type, metric_id, threshold, current_value, severity, education_type, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?) ''', (alert_id, alert_name, alert_type, metric_id, threshold,
                          kwargs.get('severity', 'warning'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建预警: {alert_name} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_alert(self, alert_id: str, current_value: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            ah_id = f"ah_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT threshold, severity FROM sustainability_alerts WHERE alert_id = ? AND status = ?', (alert_id, 'active'))
                    alert = cursor.fetchone()
                    if not alert:
                        return {'success': False, 'error': '预警不存在或已禁用'}
                    threshold, severity = alert
                    triggered = abs(
                    current_value - threshold) / threshold >= 0.1 if threshold != 0 else current_value != 0
                    if triggered:
                        cursor.execute('UPDATE sustainability_alerts SET current_value = ?, updated_at = ? WHERE alert_id = ?',
                                     (current_value, now, alert_id))
                        cursor.execute(''' INSERT INTO alert_history (ah_id, alert_id, trigger_time, trigger_value, status, created_at) VALUES (?, ?, ?, ?, 'triggered', ?) ''', (ah_id, alert_id, now, current_value, now))
                        conn.commit()
                        return {'success': True, 'triggered': True, 'severity': severity, 'ah_id': ah_id}
                    return {'success': True, 'triggered': False}
        except Exception as e:
            logger.error(f'触发预警失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_sustainability_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query_params = []
                type_filter = ''
                if education_type:
                    type_filter = ' AND education_type = ?'
                    query_params.append(education_type)

                cursor.execute(f'SELECT COUNT(*) FROM green_campus WHERE status = "active"{type_filter}', query_params)
                green_campus_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM sustainable_education WHERE status = "active"{type_filter}',
                query_params)
                sustainable_program_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM environmental_education WHERE status = "active"{type_filter}',
                query_params)
                environmental_program_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM social_responsibility WHERE status = "active"{type_filter}',
                query_params)
                social_program_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM education_equity WHERE status = "active"{type_filter}',
                query_params)
                equity_program_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM resource_optimization WHERE status = "active"{type_filter}',
                query_params)
                resource_program_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM ecosystem_protection WHERE status = "active"{type_filter}',
                query_params)
                eco_program_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT AVG( overall_score) FROM sustainability_assessment WHERE status = "completed"{type_filter}', query_params)
                avg_assessment_score = round(cursor.fetchone()[0] or 0, 2)

                cursor.execute(f'SELECT COUNT( *) FROM sustainability_assessment WHERE status = "completed"{type_filter}', query_params)
                completed_assessment_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM sustainability_alerts WHERE status = "active"{type_filter}',
                query_params)
                active_alert_count = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT SUM( volunteer_hours) FROM social_responsibility WHERE status = "active"{type_filter}', query_params)
                total_volunteer_hours = round(cursor.fetchone()[0] or 0, 2)

                statistics = {
                    'green_campus_count': green_campus_count,
                    'sustainable_program_count': sustainable_program_count,
                    'environmental_program_count': environmental_program_count,
                    'social_program_count': social_program_count,
                    'equity_program_count': equity_program_count,
                    'resource_program_count': resource_program_count,
                    'eco_program_count': eco_program_count,
                    'avg_assessment_score': avg_assessment_score,
                    'completed_assessment_count': completed_assessment_count,
                    'active_alert_count': active_alert_count,
                    'total_volunteer_hours': total_volunteer_hours,
                    'education_type': education_type or 'all'
                }
                return {'success': True, 'statistics': statistics}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}