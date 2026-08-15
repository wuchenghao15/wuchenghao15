#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育可持续发展服务 (v15.16.0)
====================================
提供绿色教育、低碳校园、教育公平、可持续发展教育等综合管理服务。

核心能力：
1. 可持续项目 - 项目管理、活动跟踪、进度监控
2. 碳排放追踪 - 数据采集、碳核算、目标管理
3. 绿色举措 - 节能减排、垃圾分类、绿色建筑
4. 环保教育 - 课程管理、实践活动、环境意识
5. 教育公平 - 公平评估、资源分配、特殊群体支持
6. 社会责任 - 公益教育、教育扶贫、社区服务
7. 教育均衡 - 城乡均衡、师资均衡、资源均衡
8. 合作伙伴 - 合作管理、项目协同、资源共享
9. 碳减排 - 减排目标、实施方案、成效评估
10. 认证管理 - 可持续认证、绿色校园认证
11. 统计分析 - 综合数据统计与报表
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_sustainable_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationSustainable')


# ========== 可持续发展配置 ==========

SUSTAINABILITY_GOALS = {
    'quality_education': {'name': '优质教育', 'description': '确保包容和公平的优质教育，促进全民终身学习'},
    'zero_hunger': {'name': '零饥饿', 'description': '消除饥饿，实现粮食安全，改善营养状况和促进可持续农业'},
    'good_health': {'name': '良好健康', 'description': '确保健康的生活方式，促进各年龄段人群的福祉'},
    'clean_water': {'name': '清洁饮水', 'description': '确保人人获得清洁饮水和卫生设施'},
    'clean_energy': {'name': '清洁能源', 'description': '确保人人获得负担得起的、可靠的、可持续的现代能源'},
    'decent_work': {'name': '体面工作', 'description': '促进持久、包容和可持续的经济增长，实现充分和生产性就业及体面工作'},
    'climate_action': {'name': '气候行动', 'description': '采取紧急行动应对气候变化及其影响'},
    'partnerships': {'name': '合作伙伴', 'description': '加强执行手段，重振可持续发展全球伙伴关系'}
}

GREEN_INITIATIVES = {
    'energy_saving': {'name': '节能减排', 'target': '降低能耗20%'},
    'waste_sorting': {'name': '垃圾分类', 'target': '垃圾分类率达90%'},
    'green_building': {'name': '绿色建筑', 'target': '新建建筑100%绿色认证'},
    'renewable_energy': {'name': '可再生能源', 'target': '可再生能源占比30%'},
    'water_saving': {'name': '节水节电', 'target': '用水量减少15%'},
    'low_carbon_commute': {'name': '低碳出行', 'target': '绿色出行率50%'},
    'environmental_education': {'name': '环保教育', 'target': '全员覆盖'},
    'green_purchasing': {'name': '绿色采购', 'target': '绿色采购占比60%'}
}

CARBON_CATEGORIES = {
    'energy': {'name': '能源消耗', 'unit': '吨CO2'},
    'transport': {'name': '交通出行', 'unit': '吨CO2'},
    'building': {'name': '建筑运营', 'unit': '吨CO2'},
    'office': {'name': '办公用品', 'unit': '吨CO2'},
    'catering': {'name': '餐饮服务', 'unit': '吨CO2'},
    'waste': {'name': '废弃物处理', 'unit': '吨CO2'},
    'procurement': {'name': '采购运输', 'unit': '吨CO2'},
    'other': {'name': '其他', 'unit': '吨CO2'}
}

EQUITY_DIMENSIONS = {
    'opportunity': {'name': '教育机会公平', 'description': '确保所有学生获得平等的教育机会'},
    'resource': {'name': '资源分配公平', 'description': '均衡分配教育资源'},
    'gender': {'name': '性别平等', 'description': '消除性别歧视，促进男女平等教育'},
    'geographic': {'name': '地域均衡', 'description': '缩小城乡、区域教育差距'},
    'special': {'name': '特殊群体', 'description': '保障特殊教育需求群体的权益'},
    'economic': {'name': '经济背景', 'description': '减少经济因素对教育的影响'},
    'cultural': {'name': '文化多样性', 'description': '尊重和包容多元文化'},
    'language': {'name': '语言多样性', 'description': '保护和传承语言多样性'}
}

ENVIRONMENTAL_EDUCATION = {
    'awareness': {'name': '环境意识', 'description': '提升环境保护意识'},
    'sustainable_living': {'name': '可持续生活', 'description': '倡导可持续的生活方式'},
    'ecological_protection': {'name': '生态保护', 'description': '学习生态系统保护知识'},
    'climate_change': {'name': '气候变化', 'description': '了解气候变化及其应对'},
    'resource_conservation': {'name': '资源节约', 'description': '培养资源节约习惯'},
    'green_technology': {'name': '绿色技术', 'description': '学习绿色科技知识'},
    'environmental_practice': {'name': '环保实践', 'description': '参与环保实践活动'},
    'environmental_action': {'name': '环保行动', 'description': '组织和参与环保行动'}
}

SOCIAL_RESPONSIBILITY = {
    'public_education': {'name': '公益教育', 'description': '开展公益教育活动'},
    'education_poverty': {'name': '教育扶贫', 'description': '支持贫困地区教育发展'},
    'community_service': {'name': '社区服务', 'description': '参与社区服务活动'},
    'volunteer_service': {'name': '志愿者服务', 'description': '组织志愿者服务'},
    'cultural_heritage': {'name': '文化传承', 'description': '传承和弘扬文化遗产'},
    'tech_innovation': {'name': '科技创新', 'description': '推动科技创新教育'},
    'health_promotion': {'name': '健康促进', 'description': '促进健康生活方式'},
    'global_citizenship': {'name': '全球公民', 'description': '培养全球公民意识'}
}

EDUCATION_BALANCE = {
    'urban_rural': {'name': '城乡均衡', 'description': '缩小城乡教育差距'},
    'regional': {'name': '区域均衡', 'description': '促进区域教育协调发展'},
    'school': {'name': '校际均衡', 'description': '均衡校际资源配置'},
    'teacher': {'name': '师资均衡', 'description': '优化师资配置'},
    'facility': {'name': '设施均衡', 'description': '改善办学条件'},
    'curriculum': {'name': '课程均衡', 'description': '统一课程标准'},
    'resource': {'name': '资源均衡', 'description': '共享优质教育资源'},
    'evaluation': {'name': '评价均衡', 'description': '建立公平评价体系'}
}

PARTNERSHIP_TYPES = {
    'government': {'name': '政府合作', 'description': '与政府部门合作'},
    'enterprise': {'name': '企业合作', 'description': '与企业建立合作关系'},
    'ngo': {'name': 'NGO合作', 'description': '与非政府组织合作'},
    'international': {'name': '国际组织', 'description': '与国际组织合作'},
    'academic': {'name': '学术机构', 'description': '与高校和研究机构合作'},
    'community': {'name': '社区组织', 'description': '与社区组织合作'},
    'foundation': {'name': '基金会', 'description': '与基金会合作'},
    'media': {'name': '媒体', 'description': '与媒体机构合作'}
}


class EducationSustainableService:
    """教育可持续发展服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS sustainability_projects (
                            project_id TEXT PRIMARY KEY,
                            project_name TEXT NOT NULL,
                            goal_type TEXT,
                            education_type TEXT,
                            description TEXT,
                            start_date TEXT,
                            end_date TEXT,
                            budget REAL,
                            status TEXT DEFAULT 'planning',
                            manager_id INTEGER,
                            manager_name TEXT,
                            participants INTEGER DEFAULT 0,
                            location TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS project_activities (
                            activity_id TEXT PRIMARY KEY,
                            project_id TEXT NOT NULL,
                            activity_name TEXT,
                            activity_date TEXT,
                            participants INTEGER DEFAULT 0,
                            description TEXT,
                            status TEXT DEFAULT 'pending',
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS carbon_tracking (
                            tracking_id TEXT PRIMARY KEY,
                            project_id TEXT,
                            category TEXT,
                            education_type TEXT,
                            description TEXT,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS carbon_data (
                            data_id TEXT PRIMARY KEY,
                            tracking_id TEXT NOT NULL,
                            record_date TEXT,
                            emission_value REAL,
                            unit TEXT DEFAULT '吨CO2',
                            source TEXT,
                            verified INTEGER DEFAULT 0,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS green_initiatives (
                            initiative_id TEXT PRIMARY KEY,
                            initiative_type TEXT,
                            education_type TEXT,
                            name TEXT NOT NULL,
                            description TEXT,
                            target TEXT,
                            status TEXT DEFAULT 'active',
                            start_date TEXT,
                            end_date TEXT,
                            responsible_unit TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS initiative_progress (
                            progress_id TEXT PRIMARY KEY,
                            initiative_id TEXT NOT NULL,
                            report_date TEXT,
                            progress REAL DEFAULT 0,
                            description TEXT,
                            evidence TEXT,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS environmental_education (
                            ee_id TEXT PRIMARY KEY,
                            ee_type TEXT,
                            education_type TEXT,
                            course_name TEXT NOT NULL,
                            description TEXT,
                            duration INTEGER DEFAULT 30,
                            target_audience TEXT,
                            instructor TEXT,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS education_programs (
                            program_id TEXT PRIMARY KEY,
                            ee_id TEXT NOT NULL,
                            program_name TEXT,
                            start_date TEXT,
                            end_date TEXT,
                            participants INTEGER DEFAULT 0,
                            max_participants INTEGER DEFAULT 50,
                            status TEXT DEFAULT 'scheduled',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS equity_programs (
                            program_id TEXT PRIMARY KEY,
                            equity_dimension TEXT,
                            education_type TEXT,
                            program_name TEXT NOT NULL,
                            description TEXT,
                            target_group TEXT,
                            coverage INTEGER DEFAULT 0,
                            budget REAL,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS equity_data (
                            data_id TEXT PRIMARY KEY,
                            program_id TEXT NOT NULL,
                            data_date TEXT,
                            indicator TEXT,
                            value REAL,
                            benchmark REAL,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS social_responsibility (
                            sr_id TEXT PRIMARY KEY,
                            sr_type TEXT,
                            education_type TEXT,
                            name TEXT NOT NULL,
                            description TEXT,
                            scope TEXT,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS responsibility_projects (
                            project_id TEXT PRIMARY KEY,
                            sr_id TEXT NOT NULL,
                            project_name TEXT,
                            start_date TEXT,
                            end_date TEXT,
                            beneficiaries INTEGER DEFAULT 0,
                            budget REAL,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS education_balance (
                            balance_id TEXT PRIMARY KEY,
                            balance_type TEXT,
                            education_type TEXT,
                            name TEXT NOT NULL,
                            description TEXT,
                            target_area TEXT,
                            priority INTEGER DEFAULT 1,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS balance_data (
                            data_id TEXT PRIMARY KEY,
                            balance_id TEXT NOT NULL,
                            data_date TEXT,
                            region TEXT,
                            indicator TEXT,
                            current_value REAL,
                            target_value REAL,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS partnerships (
                            partnership_id TEXT PRIMARY KEY,
                            partner_type TEXT,
                            partner_name TEXT NOT NULL,
                            education_type TEXT,
                            description TEXT,
                            contact_person TEXT,
                            contact_info TEXT,
                            status TEXT DEFAULT 'active',
                            established_date TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS partnership_projects (
                            pp_id TEXT PRIMARY KEY,
                            partnership_id TEXT NOT NULL,
                            project_name TEXT,
                            description TEXT,
                            start_date TEXT,
                            end_date TEXT,
                            budget REAL,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS carbon_reduction (
                            reduction_id TEXT PRIMARY KEY,
                            project_id TEXT,
                            education_type TEXT,
                            target_year INTEGER,
                            target_value REAL,
                            baseline_value REAL,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS reduction_targets (
                            target_id TEXT PRIMARY KEY,
                            reduction_id TEXT NOT NULL,
                            period TEXT,
                            target_value REAL,
                            actual_value REAL DEFAULT 0,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS sustainable_certifications (
                            cert_id TEXT PRIMARY KEY,
                            cert_name TEXT NOT NULL,
                            cert_type TEXT,
                            issuer TEXT,
                            validity_period INTEGER DEFAULT 3,
                            description TEXT,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS certification_records (
                            record_id TEXT PRIMARY KEY,
                            cert_id TEXT NOT NULL,
                            education_type TEXT,
                            entity_name TEXT,
                            issue_date TEXT,
                            expire_date TEXT,
                            status TEXT DEFAULT 'active',
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS community_engagement (
                            engagement_id TEXT PRIMARY KEY,
                            education_type TEXT,
                            activity_name TEXT NOT NULL,
                            description TEXT,
                            start_date TEXT,
                            end_date TEXT,
                            participants INTEGER DEFAULT 0,
                            impact TEXT,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS engagement_records (
                            record_id TEXT PRIMARY KEY,
                            engagement_id TEXT NOT NULL,
                            record_date TEXT,
                            activity TEXT,
                            participants INTEGER DEFAULT 0,
                            notes TEXT,
                            created_at TEXT
                        )
                    ''')
                    conn.commit()
                    logger.info('教育可持续发展服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 可持续项目 ==========

    def create_sustainability_project(self, project_name: str, goal_type: str,
                                       education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"sp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO sustainability_projects (
                            project_id, project_name, goal_type, education_type,
                            description, start_date, end_date, budget,
                            status, manager_id, manager_name, participants,
                            location, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, 0, ?, ?, ?)
                    ''', (project_id, project_name, goal_type, education_type,
                          kwargs.get('description'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('budget', 0),
                          kwargs.get('manager_id'), kwargs.get('manager_name'),
                          kwargs.get('location'), now, now))
                    conn.commit()
                    logger.info(f'创建可持续项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建可持续项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_project_activity(self, project_id: str, activity_name: str,
                              activity_date: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"pa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_activities (
                            activity_id, project_id, activity_name, activity_date,
                            participants, description, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (activity_id, project_id, activity_name, activity_date,
                          kwargs.get('participants', 0), kwargs.get('description'), now))
                    conn.commit()
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'添加项目活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_status(self, project_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE sustainability_projects SET status = ?, updated_at = ? WHERE project_id = ?',
                                 (status, now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新项目状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_sustainability_projects(self, education_type: str = None,
                                      status: str = None, page: int = 1,
                                      page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM sustainability_projects WHERE 1=1'
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
                projects = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'projects': projects, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取可持续项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 碳排放追踪 ==========

    def create_carbon_tracking(self, category: str, education_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            tracking_id = f"ct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO carbon_tracking (
                            tracking_id, project_id, category, education_type,
                            description, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (tracking_id, kwargs.get('project_id'), category,
                          education_type, kwargs.get('description'), now))
                    conn.commit()
                    return {'success': True, 'tracking_id': tracking_id}
        except Exception as e:
            logger.error(f'创建碳排放追踪失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_carbon_data(self, tracking_id: str, record_date: str,
                            emission_value: float, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"cd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO carbon_data (
                            data_id, tracking_id, record_date, emission_value,
                            unit, source, verified, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                    ''', (data_id, tracking_id, record_date, emission_value,
                          kwargs.get('unit', '吨CO2'), kwargs.get('source'), now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'记录碳排放数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_carbon_data(self, data_id: str, verified: bool = True) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE carbon_data SET verified = ? WHERE data_id = ?',
                                 (1 if verified else 0, data_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '数据不存在'}
        except Exception as e:
            logger.error(f'验证碳排放数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_carbon_summary(self, tracking_id: str, start_date: str = None,
                            end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT SUM(emission_value) as total FROM carbon_data WHERE tracking_id = ?'
                params = [tracking_id]
                if start_date:
                    query += ' AND record_date >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND record_date <= ?'
                    params.append(end_date)
                cursor.execute(query, params)
                result = cursor.fetchone()
                total = result[0] if result[0] else 0
                return {'success': True, 'total_emission': total}
        except Exception as e:
            logger.error(f'获取碳排放汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 绿色举措 ==========

    def create_green_initiative(self, initiative_type: str, education_type: str,
                                 name: str, **kwargs) -> Dict[str, Any]:
        try:
            initiative_id = f"gi_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = GREEN_INITIATIVES.get(initiative_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO green_initiatives (
                            initiative_id, initiative_type, education_type,
                            name, description, target, status,
                            start_date, end_date, responsible_unit,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
                    ''', (initiative_id, initiative_type, education_type, name,
                          kwargs.get('description'), kwargs.get('target', config.get('target')),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('responsible_unit'), now, now))
                    conn.commit()
                    logger.info(f'创建绿色举措: {name} ({initiative_id})')
                    return {'success': True, 'initiative_id': initiative_id}
        except Exception as e:
            logger.error(f'创建绿色举措失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_initiative_progress(self, initiative_id: str, report_date: str,
                                    progress: float, **kwargs) -> Dict[str, Any]:
        try:
            progress_id = f"ip_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO initiative_progress (
                            progress_id, initiative_id, report_date,
                            progress, description, evidence, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (progress_id, initiative_id, report_date, progress,
                          kwargs.get('description'), kwargs.get('evidence'), now))
                    conn.commit()
                    return {'success': True, 'progress_id': progress_id}
        except Exception as e:
            logger.error(f'更新绿色举措进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_green_initiatives(self, education_type: str = None,
                                initiative_type: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM green_initiatives WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if initiative_type:
                    query += ' AND initiative_type = ?'
                    params.append(initiative_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                initiatives = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'initiatives': initiatives, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取绿色举措列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_initiative_progress(self, initiative_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM initiative_progress WHERE initiative_id = ? ORDER BY report_date DESC',
                             (initiative_id,))
                progress = [dict(p) for p in cursor.fetchall()]
                latest = progress[0] if progress else None
                return {'success': True, 'progress_list': progress, 'latest_progress': latest['progress'] if latest else 0}
        except Exception as e:
            logger.error(f'获取绿色举措进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 环保教育 ==========

    def create_environmental_course(self, ee_type: str, education_type: str,
                                     course_name: str, **kwargs) -> Dict[str, Any]:
        try:
            ee_id = f"ee_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO environmental_education (
                            ee_id, ee_type, education_type, course_name,
                            description, duration, target_audience, instructor,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (ee_id, ee_type, education_type, course_name,
                          kwargs.get('description'), kwargs.get('duration', 30),
                          kwargs.get('target_audience'), kwargs.get('instructor'), now, now))
                    conn.commit()
                    logger.info(f'创建环保教育课程: {course_name} ({ee_id})')
                    return {'success': True, 'ee_id': ee_id}
        except Exception as e:
            logger.error(f'创建环保教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_education_program(self, ee_id: str, program_name: str,
                                  start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"ep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_programs (
                            program_id, ee_id, program_name, start_date,
                            end_date, participants, max_participants,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, 'scheduled', ?, ?)
                    ''', (program_id, ee_id, program_name, start_date,
                          kwargs.get('end_date'), kwargs.get('max_participants', 50), now, now))
                    conn.commit()
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建环保教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_program(self, program_id: str, participant_count: int = 1) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT participants, max_participants, status FROM education_programs WHERE program_id = ?',
                                 (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    if program[2] != 'scheduled':
                        return {'success': False, 'error': '项目状态不允许报名'}
                    if program[1] and program[0] + participant_count > program[1]:
                        return {'success': False, 'error': '名额不足'}
                    cursor.execute('UPDATE education_programs SET participants = participants + ?, updated_at = ? WHERE program_id = ?',
                                 (participant_count, now, program_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'报名环保教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_environmental_courses(self, education_type: str = None,
                                    ee_type: str = None, page: int = 1,
                                    page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM environmental_education WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if ee_type:
                    query += ' AND ee_type = ?'
                    params.append(ee_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                courses = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'courses': courses, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取环保教育课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育公平 ==========

    def create_equity_program(self, equity_dimension: str, education_type: str,
                               program_name: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"eq_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO equity_programs (
                            program_id, equity_dimension, education_type,
                            program_name, description, target_group,
                            coverage, budget, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (program_id, equity_dimension, education_type, program_name,
                          kwargs.get('description'), kwargs.get('target_group'),
                          kwargs.get('budget', 0), now, now))
                    conn.commit()
                    logger.info(f'创建教育公平项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建教育公平项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_equity_data(self, program_id: str, data_date: str,
                            indicator: str, value: float, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"ed_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO equity_data (
                            data_id, program_id, data_date, indicator,
                            value, benchmark, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, program_id, data_date, indicator, value,
                          kwargs.get('benchmark'), now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'记录教育公平数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_equity_coverage(self, program_id: str, coverage: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE equity_programs SET coverage = ?, updated_at = ? WHERE program_id = ?',
                                 (coverage, now, program_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新教育公平覆盖人数失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_equity_analysis(self, program_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM equity_data WHERE program_id = ? ORDER BY data_date DESC',
                             (program_id,))
                data = [dict(d) for d in cursor.fetchall()]
                if not data:
                    return {'success': False, 'error': '暂无数据'}
                latest = data[0]
                avg_value = sum(d['value'] for d in data) / len(data)
                benchmark = latest['benchmark'] if latest['benchmark'] else avg_value
                gap = abs(latest['value'] - benchmark) / benchmark * 100
                return {'success': True, 'latest_value': latest['value'], 'average_value': round(avg_value, 2),
                        'benchmark': benchmark, 'gap_percentage': round(gap, 2), 'data_points': len(data)}
        except Exception as e:
            logger.error(f'获取教育公平分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_equity_programs(self, education_type: str = None,
                              equity_dimension: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM equity_programs WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if equity_dimension:
                    query += ' AND equity_dimension = ?'
                    params.append(equity_dimension)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教育公平项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 社会责任 ==========

    def create_social_responsibility(self, sr_type: str, education_type: str,
                                      name: str, **kwargs) -> Dict[str, Any]:
        try:
            sr_id = f"sr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO social_responsibility (
                            sr_id, sr_type, education_type, name,
                            description, scope, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (sr_id, sr_type, education_type, name,
                          kwargs.get('description'), kwargs.get('scope'), now, now))
                    conn.commit()
                    logger.info(f'创建社会责任项目: {name} ({sr_id})')
                    return {'success': True, 'sr_id': sr_id}
        except Exception as e:
            logger.error(f'创建社会责任项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_responsibility_project(self, sr_id: str, project_name: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"rp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO responsibility_projects (
                            project_id, sr_id, project_name, start_date,
                            end_date, beneficiaries, budget, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (project_id, sr_id, project_name, kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('budget', 0), now, now))
                    conn.commit()
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'添加责任项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_beneficiaries(self, project_id: str, beneficiaries: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE responsibility_projects SET beneficiaries = ?, updated_at = ? WHERE project_id = ?',
                                 (beneficiaries, now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新受益人数失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_social_responsibility(self, education_type: str = None,
                                    sr_type: str = None, page: int = 1,
                                    page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM social_responsibility WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if sr_type:
                    query += ' AND sr_type = ?'
                    params.append(sr_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社会责任列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育均衡 ==========

    def create_education_balance(self, balance_type: str, education_type: str,
                                  name: str, **kwargs) -> Dict[str, Any]:
        try:
            balance_id = f"eb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_balance (
                            balance_id, balance_type, education_type, name,
                            description, target_area, priority, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (balance_id, balance_type, education_type, name,
                          kwargs.get('description'), kwargs.get('target_area'),
                          kwargs.get('priority', 1), now, now))
                    conn.commit()
                    logger.info(f'创建教育均衡项目: {name} ({balance_id})')
                    return {'success': True, 'balance_id': balance_id}
        except Exception as e:
            logger.error(f'创建教育均衡项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_balance_data(self, balance_id: str, data_date: str, region: str,
                             indicator: str, current_value: float,
                             target_value: float) -> Dict[str, Any]:
        try:
            data_id = f"bd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO balance_data (
                            data_id, balance_id, data_date, region,
                            indicator, current_value, target_value, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, balance_id, data_date, region, indicator,
                          current_value, target_value, now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'记录教育均衡数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_balance_status(self, balance_id: str, region: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM balance_data WHERE balance_id = ?'
                params = [balance_id]
                if region:
                    query += ' AND region = ?'
                    params.append(region)
                cursor.execute(f'{query} ORDER BY data_date DESC LIMIT 1', params)
                latest = cursor.fetchone()
                if not latest:
                    return {'success': False, 'error': '暂无数据'}
                progress = latest['current_value'] / latest['target_value'] * 100 if latest['target_value'] else 0
                return {'success': True, 'current_value': latest['current_value'],
                        'target_value': latest['target_value'], 'progress': round(progress, 2)}
        except Exception as e:
            logger.error(f'获取教育均衡状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_education_balance(self, education_type: str = None,
                                balance_type: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_balance WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if balance_type:
                    query += ' AND balance_type = ?'
                    params.append(balance_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY priority, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教育均衡列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合作伙伴 ==========

    def create_partnership(self, partner_type: str, partner_name: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            partnership_id = f"pt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO partnerships (
                            partnership_id, partner_type, partner_name,
                            education_type, description, contact_person,
                            contact_info, status, established_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (partnership_id, partner_type, partner_name, education_type,
                          kwargs.get('description'), kwargs.get('contact_person'),
                          kwargs.get('contact_info'), kwargs.get('established_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'创建合作伙伴: {partner_name} ({partnership_id})')
                    return {'success': True, 'partnership_id': partnership_id}
        except Exception as e:
            logger.error(f'创建合作伙伴失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_partnership_project(self, partnership_id: str, project_name: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            pp_id = f"pp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO partnership_projects (
                            pp_id, partnership_id, project_name, description,
                            start_date, end_date, budget, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (pp_id, partnership_id, project_name, kwargs.get('description'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('budget', 0), now, now))
                    conn.commit()
                    return {'success': True, 'pp_id': pp_id}
        except Exception as e:
            logger.error(f'创建合作项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_partnership_status(self, partnership_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE partnerships SET status = ?, updated_at = ? WHERE partnership_id = ?',
                                 (status, now, partnership_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '合作伙伴不存在'}
        except Exception as e:
            logger.error(f'更新合作伙伴状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_partnerships(self, education_type: str = None,
                           partner_type: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM partnerships WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if partner_type:
                    query += ' AND partner_type = ?'
                    params.append(partner_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                partners = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'partners': partners, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合作伙伴列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 碳减排 ==========

    def create_carbon_reduction(self, education_type: str, target_year: int,
                                 target_value: float, baseline_value: float,
                                 **kwargs) -> Dict[str, Any]:
        try:
            reduction_id = f"cr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO carbon_reduction (
                            reduction_id, project_id, education_type,
                            target_year, target_value, baseline_value,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (reduction_id, kwargs.get('project_id'), education_type,
                          target_year, target_value, baseline_value, now, now))
                    conn.commit()
                    logger.info(f'创建碳减排目标: {target_year}年 ({reduction_id})')
                    return {'success': True, 'reduction_id': reduction_id}
        except Exception as e:
            logger.error(f'创建碳减排目标失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_reduction_target(self, reduction_id: str, period: str,
                             target_value: float) -> Dict[str, Any]:
        try:
            target_id = f"rt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO reduction_targets (
                            target_id, reduction_id, period,
                            target_value, actual_value, created_at
                        ) VALUES (?, ?, ?, ?, 0, ?)
                    ''', (target_id, reduction_id, period, target_value, now))
                    conn.commit()
                    return {'success': True, 'target_id': target_id}
        except Exception as e:
            logger.error(f'添加减排阶段目标失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_reduction_progress(self, target_id: str, actual_value: float) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE reduction_targets SET actual_value = ? WHERE target_id = ?',
                                 (actual_value, target_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '目标不存在'}
        except Exception as e:
            logger.error(f'更新减排进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 认证管理 ==========

    def create_certification(self, cert_name: str, cert_type: str, **kwargs) -> Dict[str, Any]:
        try:
            cert_id = f"cf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO sustainable_certifications (
                            cert_id, cert_name, cert_type, issuer,
                            validity_period, description, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (cert_id, cert_name, cert_type, kwargs.get('issuer'),
                          kwargs.get('validity_period', 3), kwargs.get('description'), now))
                    conn.commit()
                    logger.info(f'创建认证类型: {cert_name} ({cert_id})')
                    return {'success': True, 'cert_id': cert_id}
        except Exception as e:
            logger.error(f'创建认证类型失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_certification(self, cert_id: str, education_type: str,
                            entity_name: str, issue_date: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"cr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            validity = kwargs.get('validity_period', 3)
            expire_date = (datetime.strptime(issue_date, '%Y-%m-%d') + timedelta(days=validity*365)).strftime('%Y-%m-%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certification_records (
                            record_id, cert_id, education_type,
                            entity_name, issue_date, expire_date,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (record_id, cert_id, education_type, entity_name,
                          issue_date, expire_date, now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id, 'expire_date': expire_date}
        except Exception as e:
            logger.error(f'颁发认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_certifications(self, education_type: str = None,
                             cert_type: str = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certification_records WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if cert_type:
                    query += ' AND cert_id IN (SELECT cert_id FROM sustainable_certifications WHERE cert_type = ?)'
                    params.append(cert_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY issue_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取认证列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_comprehensive_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                params = []
                where_clause = ''
                if education_type:
                    where_clause = 'WHERE education_type = ?'
                    params.append(education_type)

                cursor.execute(f'SELECT COUNT(*) FROM sustainability_projects {where_clause}', params)
                project_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM green_initiatives {where_clause}', params)
                initiative_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM environmental_education {where_clause}', params)
                course_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM equity_programs {where_clause}', params)
                equity_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM social_responsibility {where_clause}', params)
                sr_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM partnerships {where_clause}', params)
                partner_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT SUM(emission_value) FROM carbon_data WHERE verified = 1', [])
                total_emission = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM certification_records {where_clause}', params)
                cert_count = cursor.fetchone()[0]

                return {
                    'success': True,
                    'stats': {
                        'sustainability_projects': project_count,
                        'green_initiatives': initiative_count,
                        'environmental_courses': course_count,
                        'equity_programs': equity_count,
                        'social_responsibility': sr_count,
                        'partnerships': partner_count,
                        'total_carbon_emission': total_emission,
                        'certifications': cert_count
                    },
                    'education_type': education_type or 'all'
                }
        except Exception as e:
            logger.error(f'获取综合统计失败: {e}')
            return {'success': False, 'error': str(e)}