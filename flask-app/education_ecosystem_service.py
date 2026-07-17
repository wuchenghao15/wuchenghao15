#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育生态服务 (v15.15.0)
=============================
提供教育生态合作伙伴、产业链协同、资源对接、生态合作、行业联盟、
生态数据共享、生态治理、生态运营等综合管理服务。

核心能力：
1. 合作伙伴管理 - 伙伴注册、资质审核、信息维护、关系管理
2. 合作联盟 - 联盟创建、成员管理、合作协议、联盟活动
3. 资源对接 - 资源池管理、资源匹配、资源共享、资源交易
4. 生态数据 - 数据采集、数据共享、数据权限、数据审计
5. 生态治理 - 治理架构、成员选举、决策管理、规则制定
6. 生态运营 - 运营计划、运营执行、效果评估、优化调整
7. 生态活动 - 活动策划、活动报名、活动执行、活动复盘
8. 收益分配 - 收益计算、分配规则、分配执行
9. 评价体系 - 伙伴评价、服务评价、评价统计
10. 统计分析 - 生态数据统计与可视化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_ecosystem_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationEcosystem')


# ========== 生态配置 ==========

PARTNER_TYPES = {
    'school': {'name': '学校', 'education_types': ['k12', 'higher']},
    'institution': {'name': '教育机构', 'education_types': ['k12', 'higher', 'vocational', 'adult']},
    'training': {'name': '培训机构', 'education_types': ['k12', 'vocational', 'adult']},
    'enterprise': {'name': '企业', 'education_types': ['vocational', 'adult']},
    'government': {'name': '政府', 'education_types': ['k12', 'higher', 'vocational', 'adult']},
    'ngo': {'name': '社会组织', 'education_types': ['k12', 'higher', 'adult']},
    'research': {'name': '科研机构', 'education_types': ['higher', 'vocational']},
    'media': {'name': '媒体', 'education_types': ['k12', 'higher', 'adult']}
}

COOPERATION_MODELS = {
    'strategic_alliance': {'name': '战略联盟', 'requires_agreement': True},
    'project_cooperation': {'name': '项目合作', 'requires_agreement': True},
    'resource_sharing': {'name': '资源共享', 'requires_agreement': False},
    'joint_operation': {'name': '联合运营', 'requires_agreement': True},
    'technical_cooperation': {'name': '技术合作', 'requires_agreement': True},
    'talent_cooperation': {'name': '人才合作', 'requires_agreement': True},
    'funding_cooperation': {'name': '资金合作', 'requires_agreement': True},
    'brand_cooperation': {'name': '品牌合作', 'requires_agreement': True}
}

ECOSYSTEM_ROLES = {
    'core_member': {'name': '核心成员', 'permission_level': 5},
    'strategic_partner': {'name': '战略伙伴', 'permission_level': 4},
    'regular_member': {'name': '普通成员', 'permission_level': 3},
    'observer': {'name': '观察员', 'permission_level': 2},
    'supplier': {'name': '供应商', 'permission_level': 2},
    'service_provider': {'name': '服务商', 'permission_level': 2},
    'customer': {'name': '客户', 'permission_level': 1},
    'investor': {'name': '投资者', 'permission_level': 3}
}

INDUSTRY_SECTORS = {
    'k12': {'name': 'K12教育', 'description': '基础教育阶段'},
    'higher': {'name': '高等教育', 'description': '大学及以上教育'},
    'vocational': {'name': '职业教育', 'description': '职业技能培训'},
    'adult': {'name': '成人教育', 'description': '成人继续教育'},
    'online': {'name': '在线教育', 'description': '互联网教育平台'},
    'edtech': {'name': '教育科技', 'description': '教育技术与产品'},
    'publishing': {'name': '教育出版', 'description': '教材与出版物'},
    'equipment': {'name': '教育装备', 'description': '教学设备与器材'}
}

RESOURCE_TYPES = {
    'course': {'name': '课程资源', 'unit': '门'},
    'teacher': {'name': '师资资源', 'unit': '人'},
    'technology': {'name': '技术资源', 'unit': '项'},
    'funding': {'name': '资金资源', 'unit': '元'},
    'channel': {'name': '渠道资源', 'unit': '个'},
    'brand': {'name': '品牌资源', 'unit': '项'},
    'data': {'name': '数据资源', 'unit': '条'},
    'facility': {'name': '设施资源', 'unit': '套'}
}

ALLIANCE_TYPES = {
    'industry': {'name': '行业联盟', 'scope': 'national'},
    'regional': {'name': '区域联盟', 'scope': 'local'},
    'discipline': {'name': '学科联盟', 'scope': 'specialized'},
    'technology': {'name': '技术联盟', 'scope': 'technical'},
    'industry_chain': {'name': '产业联盟', 'scope': 'cross-industry'},
    'international': {'name': '国际联盟', 'scope': 'global'}
}

DATA_SHARING_MODELS = {
    'public': {'name': '公开共享', 'require_approval': False},
    'authorized': {'name': '授权共享', 'require_approval': True},
    'paid': {'name': '有偿共享', 'require_approval': True},
    'joint_analysis': {'name': '联合分析', 'require_approval': True},
    'anonymous': {'name': '匿名共享', 'require_approval': False},
    'encrypted': {'name': '加密共享', 'require_approval': True}
}

GOVERNANCE_TYPES = {
    'council': {'name': '理事会', 'term': '2年'},
    'supervisory': {'name': '监事会', 'term': '2年'},
    'general_assembly': {'name': '会员大会', 'term': '1年'},
    'professional_committee': {'name': '专业委员会', 'term': '2年'},
    'working_group': {'name': '工作小组', 'term': '1年'},
    'secretariat': {'name': '秘书处', 'term': '1年'}
}


class EducationEcosystemService:
    """教育生态服务"""

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
                    CREATE TABLE IF NOT EXISTS ecosystem_partners (
                        partner_id TEXT PRIMARY KEY,
                        partner_name TEXT NOT NULL,
                        partner_type TEXT NOT NULL,
                        education_type TEXT,
                        ecosystem_role TEXT DEFAULT 'regular_member',
                        industry_sector TEXT,
                        registration_date TEXT,
                        status TEXT DEFAULT 'pending',
                        contact_person TEXT,
                        contact_phone TEXT,
                        contact_email TEXT,
                        address TEXT,
                        province TEXT,
                        city TEXT,
                        website TEXT,
                        logo_url TEXT,
                        description TEXT,
                        annual_revenue TEXT,
                        employee_count INTEGER,
                        established_year INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS partner_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        partner_id TEXT NOT NULL,
                        profile_type TEXT,
                        profile_data TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        FOREIGN KEY (partner_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cooperation_agreements (
                        agreement_id TEXT PRIMARY KEY,
                        partner_id_a TEXT NOT NULL,
                        partner_id_b TEXT NOT NULL,
                        cooperation_model TEXT NOT NULL,
                        education_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        agreement_content TEXT,
                        status TEXT DEFAULT 'draft',
                        sign_date TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (partner_id_a) REFERENCES ecosystem_partners(partner_id),
                        FOREIGN KEY (partner_id_b) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cooperation_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        agreement_id TEXT,
                        education_type TEXT,
                        industry_sector TEXT,
                        description TEXT,
                        budget REAL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'planning',
                        progress REAL DEFAULT 0,
                        leader_id TEXT,
                        leader_name TEXT,
                        participating_partners TEXT,
                        deliverables TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (agreement_id) REFERENCES cooperation_agreements(agreement_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS industry_alliances (
                        alliance_id TEXT PRIMARY KEY,
                        alliance_name TEXT NOT NULL,
                        alliance_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        founding_date TEXT,
                        headquarters TEXT,
                        logo_url TEXT,
                        member_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alliance_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alliance_id TEXT NOT NULL,
                        partner_id TEXT NOT NULL,
                        member_role TEXT DEFAULT 'member',
                        join_date TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (alliance_id) REFERENCES industry_alliances(alliance_id),
                        FOREIGN KEY (partner_id) REFERENCES ecosystem_partners(partner_id),
                        UNIQUE(alliance_id, partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_pool (
                        resource_id TEXT PRIMARY KEY,
                        resource_name TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        education_type TEXT,
                        owner_id TEXT NOT NULL,
                        owner_name TEXT,
                        description TEXT,
                        quantity INTEGER DEFAULT 1,
                        unit TEXT,
                        value REAL DEFAULT 0,
                        is_shared INTEGER DEFAULT 0,
                        sharing_model TEXT,
                        access_level TEXT DEFAULT 'public',
                        tags TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (owner_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_sharing (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_id TEXT NOT NULL,
                        provider_id TEXT NOT NULL,
                        receiver_id TEXT NOT NULL,
                        sharing_model TEXT NOT NULL,
                        education_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'pending',
                        cost REAL DEFAULT 0,
                        usage_count INTEGER DEFAULT 0,
                        approved_at TEXT,
                        created_at TEXT,
                        FOREIGN KEY (resource_id) REFERENCES resource_pool(resource_id),
                        FOREIGN KEY (provider_id) REFERENCES ecosystem_partners(partner_id),
                        FOREIGN KEY (receiver_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ecosystem_data (
                        data_id TEXT PRIMARY KEY,
                        data_name TEXT NOT NULL,
                        data_type TEXT,
                        education_type TEXT,
                        source_id TEXT,
                        source_name TEXT,
                        description TEXT,
                        data_format TEXT,
                        record_count INTEGER DEFAULT 0,
                        sharing_model TEXT DEFAULT 'public',
                        is_encrypted INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_access_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_id TEXT NOT NULL,
                        accessor_id TEXT NOT NULL,
                        access_type TEXT,
                        access_time TEXT,
                        duration INTEGER DEFAULT 0,
                        data_usage TEXT,
                        FOREIGN KEY (data_id) REFERENCES ecosystem_data(data_id),
                        FOREIGN KEY (accessor_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS governance_structure (
                        structure_id TEXT PRIMARY KEY,
                        structure_name TEXT NOT NULL,
                        governance_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        term TEXT,
                        member_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS governance_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        structure_id TEXT NOT NULL,
                        partner_id TEXT NOT NULL,
                        member_name TEXT,
                        position TEXT,
                        term_start TEXT,
                        term_end TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (structure_id) REFERENCES governance_structure(structure_id),
                        FOREIGN KEY (partner_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ecosystem_operations (
                        operation_id TEXT PRIMARY KEY,
                        operation_name TEXT NOT NULL,
                        education_type TEXT,
                        operation_type TEXT,
                        description TEXT,
                        target_metrics TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'planning',
                        budget REAL DEFAULT 0,
                        responsible_id TEXT,
                        responsible_name TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (responsible_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operation_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        operation_id TEXT NOT NULL,
                        record_type TEXT,
                        record_content TEXT,
                        record_time TEXT,
                        operator_id TEXT,
                        FOREIGN KEY (operation_id) REFERENCES ecosystem_operations(operation_id),
                        FOREIGN KEY (operator_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ecosystem_events (
                        event_id TEXT PRIMARY KEY,
                        event_name TEXT NOT NULL,
                        event_type TEXT,
                        education_type TEXT,
                        industry_sector TEXT,
                        description TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        organizer_id TEXT,
                        organizer_name TEXT,
                        status TEXT DEFAULT 'planned',
                        cover_image TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (organizer_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS event_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL,
                        partner_id TEXT NOT NULL,
                        participant_name TEXT,
                        participant_role TEXT,
                        register_time TEXT,
                        attended INTEGER DEFAULT 0,
                        FOREIGN KEY (event_id) REFERENCES ecosystem_events(event_id),
                        FOREIGN KEY (partner_id) REFERENCES ecosystem_partners(partner_id),
                        UNIQUE(event_id, partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ecosystem_benefits (
                        benefit_id TEXT PRIMARY KEY,
                        benefit_name TEXT NOT NULL,
                        education_type TEXT,
                        benefit_type TEXT,
                        description TEXT,
                        total_amount REAL DEFAULT 0,
                        distribution_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS benefit_distribution (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        benefit_id TEXT NOT NULL,
                        partner_id TEXT NOT NULL,
                        amount REAL DEFAULT 0,
                        distribution_ratio REAL DEFAULT 0,
                        distribution_date TEXT,
                        status TEXT DEFAULT 'pending',
                        FOREIGN KEY (benefit_id) REFERENCES ecosystem_benefits(benefit_id),
                        FOREIGN KEY (partner_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ecosystem_ratings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_type TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        rater_id TEXT NOT NULL,
                        rater_name TEXT,
                        rating INTEGER NOT NULL,
                        comment TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        FOREIGN KEY (rater_id) REFERENCES ecosystem_partners(partner_id)
                    )
                ''')
                conn.commit()
                logger.info('教育生态服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 合作伙伴管理 ==========

    def register_partner(self, partner_name: str, partner_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            partner_id = f"ep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PARTNER_TYPES.get(partner_type, {})
            education_types = config.get('education_types', ['k12', 'adult'])
            education_type = kwargs.get('education_type', education_types[0])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ecosystem_partners (
                            partner_id, partner_name, partner_type, education_type,
                            ecosystem_role, industry_sector, registration_date,
                            status, contact_person, contact_phone, contact_email,
                            address, province, city, website, logo_url, description,
                            annual_revenue, employee_count, established_year,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (partner_id, partner_name, partner_type, education_type,
                          kwargs.get('ecosystem_role', 'regular_member'),
                          kwargs.get('industry_sector'), now[:10], 'pending',
                          kwargs.get('contact_person'), kwargs.get('contact_phone'),
                          kwargs.get('contact_email'), kwargs.get('address'),
                          kwargs.get('province'), kwargs.get('city'),
                          kwargs.get('website'), kwargs.get('logo_url'),
                          kwargs.get('description'), kwargs.get('annual_revenue'),
                          kwargs.get('employee_count'), kwargs.get('established_year'),
                          now, now))
                    conn.commit()
                    logger.info(f'注册合作伙伴: {partner_name} ({partner_id})')
                    return {'success': True, 'partner_id': partner_id}
        except Exception as e:
            logger.error(f'注册合作伙伴失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_partner(self, partner_id: str, approved: bool,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ecosystem_partners SET status = ?, updated_at = ? WHERE partner_id = ? AND status = ?',
                                 (status, now, partner_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '合作伙伴状态不允许审核'}
        except Exception as e:
            logger.error(f'审核合作伙伴失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_partner_profile(self, partner_id: str, profile_type: str,
                               profile_data: Dict, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT partner_id FROM ecosystem_partners WHERE partner_id = ?', (partner_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '合作伙伴不存在'}
                    data_json = json.dumps(profile_data, ensure_ascii=False)
                    cursor.execute('INSERT OR REPLACE INTO partner_profiles (partner_id, profile_type, profile_data, education_type, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (partner_id, profile_type, data_json, kwargs.get('education_type'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新合作伙伴资料失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_partners(self, partner_type: str = None, education_type: str = None,
                      status: str = 'approved', page: int = 1,
                      page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ecosystem_partners WHERE 1=1'
                params = []
                if partner_type:
                    query += ' AND partner_type = ?'
                    params.append(partner_type)
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
                partners = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'partners': partners, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合作伙伴列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合作联盟 ==========

    def create_alliance(self, alliance_name: str, alliance_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            alliance_id = f"al_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ALLIANCE_TYPES.get(alliance_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO industry_alliances (
                            alliance_id, alliance_name, alliance_type, education_type,
                            description, founding_date, headquarters, logo_url,
                            member_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (alliance_id, alliance_name, alliance_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          now[:10], kwargs.get('headquarters'), kwargs.get('logo_url'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建联盟: {alliance_name} ({alliance_id})')
                    return {'success': True, 'alliance_id': alliance_id}
        except Exception as e:
            logger.error(f'创建联盟失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_alliance_member(self, alliance_id: str, partner_id: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT partner_id, education_type FROM ecosystem_partners WHERE partner_id = ?', (partner_id,))
                    partner = cursor.fetchone()
                    if not partner:
                        return {'success': False, 'error': '合作伙伴不存在'}
                    cursor.execute('INSERT OR IGNORE INTO alliance_members (alliance_id, partner_id, member_role, join_date, status) VALUES (?, ?, ?, ?, ?)',
                                 (alliance_id, partner_id, kwargs.get('member_role', 'member'), now[:10], 'active'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE industry_alliances SET member_count = member_count + 1, updated_at = ? WHERE alliance_id = ?', (now, alliance_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该联盟'}
        except Exception as e:
            logger.error(f'添加联盟成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_cooperation_agreement(self, partner_id_a: str, partner_id_b: str,
                                     cooperation_model: str, **kwargs) -> Dict[str, Any]:
        try:
            agreement_id = f"ca_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COOPERATION_MODELS.get(cooperation_model, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM ecosystem_partners WHERE partner_id = ?', (partner_id_a,))
                    edu_type_a = cursor.fetchone()
                    cursor.execute('SELECT education_type FROM ecosystem_partners WHERE partner_id = ?', (partner_id_b,))
                    edu_type_b = cursor.fetchone()
                    if not edu_type_a or not edu_type_b:
                        return {'success': False, 'error': '合作伙伴不存在'}
                    education_type = kwargs.get('education_type', edu_type_a[0] if edu_type_a[0] == edu_type_b[0] else 'mixed')
                    cursor.execute('''
                        INSERT INTO cooperation_agreements (
                            agreement_id, partner_id_a, partner_id_b, cooperation_model,
                            education_type, start_date, end_date, agreement_content,
                            status, sign_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (agreement_id, partner_id_a, partner_id_b, cooperation_model,
                          education_type, kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('agreement_content'), 'draft', None, now, now))
                    conn.commit()
                    logger.info(f'创建合作协议: {agreement_id}')
                    return {'success': True, 'agreement_id': agreement_id}
        except Exception as e:
            logger.error(f'创建合作协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def sign_agreement(self, agreement_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE cooperation_agreements SET status = ?, sign_date = ?, updated_at = ? WHERE agreement_id = ? AND status = ?',
                                 ('active', now[:10], now, agreement_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'active'}
                    return {'success': False, 'error': '协议状态不允许签署'}
        except Exception as e:
            logger.error(f'签署协议失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源对接 ==========

    def add_resource(self, resource_name: str, resource_type: str,
                     owner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"rs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = RESOURCE_TYPES.get(resource_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT partner_name, education_type FROM ecosystem_partners WHERE partner_id = ?', (owner_id,))
                    owner = cursor.fetchone()
                    if not owner:
                        return {'success': False, 'error': '所有者不存在'}
                    cursor.execute('''
                        INSERT INTO resource_pool (
                            resource_id, resource_name, resource_type, education_type,
                            owner_id, owner_name, description, quantity, unit,
                            value, is_shared, sharing_model, access_level, tags,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (resource_id, resource_name, resource_type,
                          kwargs.get('education_type', owner[1]),
                          owner_id, owner[0], kwargs.get('description'),
                          kwargs.get('quantity', 1), config.get('unit', '项'),
                          kwargs.get('value', 0), kwargs.get('is_shared', 0),
                          kwargs.get('sharing_model'), kwargs.get('access_level', 'public'),
                          kwargs.get('tags'), now, now))
                    conn.commit()
                    logger.info(f'添加资源: {resource_name} ({resource_id})')
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'添加资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def request_resource_sharing(self, resource_id: str, receiver_id: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT owner_id, sharing_model, education_type FROM resource_pool WHERE resource_id = ?', (resource_id,))
                    resource = cursor.fetchone()
                    if not resource:
                        return {'success': False, 'error': '资源不存在'}
                    sharing_model = kwargs.get('sharing_model', resource[1] or 'authorized')
                    cursor.execute('INSERT OR IGNORE INTO resource_sharing (resource_id, provider_id, receiver_id, sharing_model, education_type, start_date, end_date, status, cost, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (resource_id, resource[0], receiver_id, sharing_model,
                                  kwargs.get('education_type', resource[2]),
                                  now[:10], kwargs.get('end_date'), 'pending',
                                  kwargs.get('cost', 0), now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已申请该资源共享'}
        except Exception as e:
            logger.error(f'申请资源共享失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_resource_sharing(self, resource_sharing_id: int, approved: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE resource_sharing SET status = ?, approved_at = ? WHERE id = ? AND status = ?',
                                 (status, now[:10] if approved else None, resource_sharing_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '资源共享申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核资源共享失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_resources(self, keyword: str = None, resource_type: str = None,
                         education_type: str = None, is_shared: bool = True,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM resource_pool WHERE 1=1'
                params = []
                if keyword:
                    query += ' AND (resource_name LIKE ? OR description LIKE ?)'
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if is_shared is not None:
                    query += ' AND is_shared = ?'
                    params.append(1 if is_shared else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索资源失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 生态数据 ==========

    def create_data_set(self, data_name: str, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"ds_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ecosystem_data (
                            data_id, data_name, data_type, education_type,
                            source_id, source_name, description, data_format,
                            record_count, sharing_model, is_encrypted,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, data_name, kwargs.get('data_type'),
                          kwargs.get('education_type'), kwargs.get('source_id'),
                          kwargs.get('source_name'), kwargs.get('description'),
                          kwargs.get('data_format'), kwargs.get('record_count', 0),
                          kwargs.get('sharing_model', 'public'),
                          kwargs.get('is_encrypted', 0), now, now))
                    conn.commit()
                    logger.info(f'创建数据集: {data_name} ({data_id})')
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'创建数据集失败: {e}')
            return {'success': False, 'error': str(e)}

    def request_data_access(self, data_id: str, accessor_id: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT sharing_model, is_encrypted FROM ecosystem_data WHERE data_id = ?', (data_id,))
                    data_set = cursor.fetchone()
                    if not data_set:
                        return {'success': False, 'error': '数据集不存在'}
                    model = DATA_SHARING_MODELS.get(data_set[0], {})
                    if model.get('require_approval', True):
                        cursor.execute('INSERT INTO data_access_logs (data_id, accessor_id, access_type, access_time, data_usage) VALUES (?, ?, ?, ?, ?)',
                                     (data_id, accessor_id, 'request', now, kwargs.get('data_usage')))
                        conn.commit()
                        return {'success': True, 'status': 'pending'}
                    cursor.execute('INSERT INTO data_access_logs (data_id, accessor_id, access_type, access_time, data_usage) VALUES (?, ?, ?, ?, ?)',
                                 (data_id, accessor_id, 'access', now, kwargs.get('data_usage')))
                    conn.commit()
                    return {'success': True, 'status': 'granted'}
        except Exception as e:
            logger.error(f'申请数据访问失败: {e}')
            return {'success': False, 'error': str(e)}

    def audit_data_access(self, data_id: str = None, accessor_id: str = None,
                          start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_access_logs WHERE 1=1'
                params = []
                if data_id:
                    query += ' AND data_id = ?'
                    params.append(data_id)
                if accessor_id:
                    query += ' AND accessor_id = ?'
                    params.append(accessor_id)
                if start_date:
                    query += ' AND access_time >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND access_time <= ?'
                    params.append(end_date)
                query += ' ORDER BY access_time DESC'
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'access_logs': logs}
        except Exception as e:
            logger.error(f'审计数据访问失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_data_sets(self, education_type: str = None, sharing_model: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ecosystem_data WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if sharing_model:
                    query += ' AND sharing_model = ?'
                    params.append(sharing_model)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                data_sets = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'data_sets': data_sets, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取数据集列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 生态治理 ==========

    def create_governance_structure(self, structure_name: str, governance_type: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            structure_id = f"gs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = GOVERNANCE_TYPES.get(governance_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO governance_structure (
                            structure_id, structure_name, governance_type, education_type,
                            description, term, member_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (structure_id, structure_name, governance_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('term', config.get('term', '2年')), now, now))
                    conn.commit()
                    logger.info(f'创建治理结构: {structure_name} ({structure_id})')
                    return {'success': True, 'structure_id': structure_id}
        except Exception as e:
            logger.error(f'创建治理结构失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_governance_member(self, structure_id: str, partner_id: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT partner_name FROM ecosystem_partners WHERE partner_id = ?', (partner_id,))
                    partner = cursor.fetchone()
                    if not partner:
                        return {'success': False, 'error': '合作伙伴不存在'}
                    cursor.execute('INSERT OR IGNORE INTO governance_members (structure_id, partner_id, member_name, position, term_start, term_end, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (structure_id, partner_id, partner[0],
                                  kwargs.get('position'), now[:10],
                                  kwargs.get('term_end'), 'active'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE governance_structure SET member_count = member_count + 1, updated_at = ? WHERE structure_id = ?', (now, structure_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该治理结构'}
        except Exception as e:
            logger.error(f'添加治理成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def conduct_election(self, structure_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT governance_type FROM governance_structure WHERE structure_id = ?', (structure_id,))
                    structure = cursor.fetchone()
                    if not structure:
                        return {'success': False, 'error': '治理结构不存在'}
                    election_data = {
                        'election_date': now[:10],
                        'candidates': kwargs.get('candidates', []),
                        'voters': kwargs.get('voters', []),
                        'results': kwargs.get('results', {}),
                        'method': kwargs.get('method', 'vote')
                    }
                    cursor.execute('INSERT INTO operation_records (operation_id, record_type, record_content, record_time) VALUES (?, ?, ?, ?)',
                                 (structure_id, 'election', json.dumps(election_data, ensure_ascii=False), now))
                    conn.commit()
                    return {'success': True, 'election_date': now[:10]}
        except Exception as e:
            logger.error(f'执行选举失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_governance_rule(self, structure_id: str, rule_name: str,
                               rule_content: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            rule_data = {
                'rule_name': rule_name,
                'rule_content': rule_content,
                'effective_date': kwargs.get('effective_date', now[:10]),
                'status': kwargs.get('status', 'active')
            }
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO operation_records (operation_id, record_type, record_content, record_time) VALUES (?, ?, ?, ?)',
                                 (structure_id, 'rule', json.dumps(rule_data, ensure_ascii=False), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'创建治理规则失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 生态运营 ==========

    def create_operation_plan(self, operation_name: str, **kwargs) -> Dict[str, Any]:
        try:
            operation_id = f"op_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ecosystem_operations (
                            operation_id, operation_name, education_type, operation_type,
                            description, target_metrics, start_date, end_date,
                            status, budget, responsible_id, responsible_name,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (operation_id, operation_name, kwargs.get('education_type'),
                          kwargs.get('operation_type'), kwargs.get('description'),
                          json.dumps(kwargs.get('target_metrics', {}), ensure_ascii=False),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          'planning', kwargs.get('budget', 0),
                          kwargs.get('responsible_id'), kwargs.get('responsible_name'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建运营计划: {operation_name} ({operation_id})')
                    return {'success': True, 'operation_id': operation_id}
        except Exception as e:
            logger.error(f'创建运营计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_operation(self, operation_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ecosystem_operations SET status = ?, updated_at = ? WHERE operation_id = ? AND status = ?',
                                 ('executing', now, operation_id, 'planning'))
                    if cursor.rowcount > 0:
                        execution_data = {
                            'action': 'execute',
                            'timestamp': now,
                            'operator': kwargs.get('operator'),
                            'details': kwargs.get('details', {})
                        }
                        cursor.execute('INSERT INTO operation_records (operation_id, record_type, record_content, record_time) VALUES (?, ?, ?, ?)',
                                     (operation_id, 'execution', json.dumps(execution_data, ensure_ascii=False), now))
                        conn.commit()
                        return {'success': True, 'status': 'executing'}
                    return {'success': False, 'error': '运营计划状态不允许执行'}
        except Exception as e:
            logger.error(f'执行运营计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_operation(self, operation_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ecosystem_operations SET status = ?, updated_at = ? WHERE operation_id = ? AND status = ?',
                                 ('completed', now, operation_id, 'executing'))
                    if cursor.rowcount > 0:
                        evaluation_data = {
                            'evaluation_date': now[:10],
                            'metrics': kwargs.get('metrics', {}),
                            'score': kwargs.get('score'),
                            'comments': kwargs.get('comments', ''),
                            'recommendations': kwargs.get('recommendations', [])
                        }
                        cursor.execute('INSERT INTO operation_records (operation_id, record_type, record_content, record_time) VALUES (?, ?, ?, ?)',
                                     (operation_id, 'evaluation', json.dumps(evaluation_data, ensure_ascii=False), now))
                        conn.commit()
                        return {'success': True, 'status': 'completed'}
                    return {'success': False, 'error': '运营计划状态不允许评估'}
        except Exception as e:
            logger.error(f'评估运营计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def optimize_operation(self, operation_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            optimization_data = {
                'optimization_date': now[:10],
                'changes': kwargs.get('changes', []),
                'reason': kwargs.get('reason', ''),
                'expected_impact': kwargs.get('expected_impact', {})
            }
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO operation_records (operation_id, record_type, record_content, record_time) VALUES (?, ?, ?, ?)',
                                 (operation_id, 'optimization', json.dumps(optimization_data, ensure_ascii=False), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'优化运营计划失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 生态活动 ==========

    def create_event(self, event_name: str, **kwargs) -> Dict[str, Any]:
        try:
            event_id = f"ee_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ecosystem_events (
                            event_id, event_name, event_type, education_type,
                            industry_sector, description, location, start_date,
                            end_date, start_time, end_time, max_participants,
                            registered_count, organizer_id, organizer_name,
                            status, cover_image, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
                    ''', (event_id, event_name, kwargs.get('event_type'),
                          kwargs.get('education_type'), kwargs.get('industry_sector'),
                          kwargs.get('description'), kwargs.get('location'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('start_time', '09:00'),
                          kwargs.get('end_time', '17:00'),
                          kwargs.get('max_participants', 100),
                          kwargs.get('organizer_id'), kwargs.get('organizer_name'),
                          'planned', kwargs.get('cover_image'), now, now))
                    conn.commit()
                    logger.info(f'创建生态活动: {event_name} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'创建生态活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_event(self, event_id: str, partner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM ecosystem_events WHERE event_id = ?', (event_id,))
                    event = cursor.fetchone()
                    if not event:
                        return {'success': False, 'error': '活动不存在'}
                    if event[2] != 'planned':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if event[0] and event[1] >= event[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO event_participants (event_id, partner_id, participant_name, participant_role, register_time) VALUES (?, ?, ?, ?, ?)',
                                 (event_id, partner_id, kwargs.get('participant_name'),
                                  kwargs.get('participant_role', 'participant'), now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE ecosystem_events SET registered_count = registered_count + 1, updated_at = ? WHERE event_id = ?', (now, event_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_event_attendance(self, event_id: str, partner_id: str, attended: bool = True) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE event_participants SET attended = ? WHERE event_id = ? AND partner_id = ?',
                                 (1 if attended else 0, event_id, partner_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录活动出席失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_event(self, event_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ecosystem_events SET status = ?, updated_at = ? WHERE event_id = ? AND status = ?',
                                 ('completed', now, event_id, 'planned'))
                    if cursor.rowcount > 0:
                        cursor.execute('SELECT COUNT(*) FROM event_participants WHERE event_id = ? AND attended = 1', (event_id,))
                        attended_count = cursor.fetchone()[0]
                        cursor.execute('UPDATE ecosystem_events SET registered_count = ? WHERE event_id = ?', (attended_count, event_id))
                        conn.commit()
                        return {'success': True, 'status': 'completed', 'attended_count': attended_count}
                    return {'success': False, 'error': '活动状态不允许结束'}
        except Exception as e:
            logger.error(f'结束活动失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 收益分配 ==========

    def create_benefit(self, benefit_name: str, **kwargs) -> Dict[str, Any]:
        try:
            benefit_id = f"bf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ecosystem_benefits (
                            benefit_id, benefit_name, education_type, benefit_type,
                            description, total_amount, distribution_count,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ''', (benefit_id, benefit_name, kwargs.get('education_type'),
                          kwargs.get('benefit_type'), kwargs.get('description'),
                          kwargs.get('total_amount', 0), now, now))
                    conn.commit()
                    logger.info(f'创建收益: {benefit_name} ({benefit_id})')
                    return {'success': True, 'benefit_id': benefit_id}
        except Exception as e:
            logger.error(f'创建收益失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_distribution(self, benefit_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT total_amount, education_type FROM ecosystem_benefits WHERE benefit_id = ?', (benefit_id,))
                    benefit = cursor.fetchone()
                    if not benefit:
                        return {'success': False, 'error': '收益不存在'}
                    total_amount = benefit[0]
                    education_type = benefit[1]
                    distributions = kwargs.get('distributions', [])
                    total_ratio = sum(d.get('ratio', 0) for d in distributions)
                    if total_ratio != 1 and total_ratio != 100:
                        return {'success': False, 'error': '分配比例总和必须为1或100'}
                    ratio_adjust = 100 if total_ratio == 100 else 1
                    for dist in distributions:
                        ratio = dist.get('ratio', 0) / ratio_adjust
                        amount = total_amount * ratio
                        cursor.execute('INSERT INTO benefit_distribution (benefit_id, partner_id, amount, distribution_ratio, distribution_date, status) VALUES (?, ?, ?, ?, ?, ?)',
                                     (benefit_id, dist['partner_id'], amount, ratio, now[:10], 'pending'))
                    conn.commit()
                    return {'success': True, 'distribution_count': len(distributions)}
        except Exception as e:
            logger.error(f'计算收益分配失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_distribution(self, benefit_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE benefit_distribution SET status = ? WHERE benefit_id = ? AND status = ?',
                                 ('approved', benefit_id, 'pending'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE ecosystem_benefits SET distribution_count = distribution_count + 1, updated_at = ? WHERE benefit_id = ?', (now, benefit_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '没有待审核的分配记录'}
        except Exception as e:
            logger.error(f'审核收益分配失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 评价体系 ==========

    def rate_entity(self, target_type: str, target_id: str, rater_id: str,
                    rating: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT partner_name FROM ecosystem_partners WHERE partner_id = ?', (rater_id,))
                    rater = cursor.fetchone()
                    if not rater:
                        return {'success': False, 'error': '评价者不存在'}
                    cursor.execute('INSERT OR REPLACE INTO ecosystem_ratings (target_type, target_id, rater_id, rater_name, rating, comment, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (target_type, target_id, rater_id, rater[0], rating,
                                  kwargs.get('comment'), kwargs.get('education_type'), now))
                    conn.commit()
                    cursor.execute('SELECT AVG(rating), COUNT(*) FROM ecosystem_ratings WHERE target_type = ? AND target_id = ?', (target_type, target_id))
                    stats = cursor.fetchone()
                    avg = round(stats[0], 1) if stats[0] else 0
                    count = stats[1] or 0
                    return {'success': True, 'average_rating': avg, 'rating_count': count}
        except Exception as e:
            logger.error(f'评价实体失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_entity_ratings(self, target_type: str, target_id: str,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ecosystem_ratings WHERE target_type = ? AND target_id = ?'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', (target_type, target_id))
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, (target_type, target_id, page_size, (page - 1) * page_size))
                ratings = [dict(r) for r in cursor.fetchall()]
                cursor.execute('SELECT AVG(rating) FROM ecosystem_ratings WHERE target_type = ? AND target_id = ?', (target_type, target_id))
                avg = cursor.fetchone()[0]
                return {'success': True, 'ratings': ratings, 'average_rating': round(avg, 1) if avg else 0, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取实体评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_rating_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT target_type, AVG(rating) as avg_rating, COUNT(*) as total_count FROM ecosystem_ratings WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY target_type'
                cursor.execute(query, params)
                summaries = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'summary': summaries}
        except Exception as e:
            logger.error(f'获取评价统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_ecosystem_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                partner_query = 'SELECT COUNT(*) FROM ecosystem_partners WHERE status = ?'
                partner_params = ['approved']
                if education_type:
                    partner_query += ' AND education_type = ?'
                    partner_params.append(education_type)
                cursor.execute(partner_query, partner_params)
                stats['total_partners'] = cursor.fetchone()[0]

                alliance_query = 'SELECT COUNT(*) FROM industry_alliances WHERE status = ?'
                alliance_params = ['active']
                if education_type:
                    alliance_query += ' AND education_type = ?'
                    alliance_params.append(education_type)
                cursor.execute(alliance_query, alliance_params)
                stats['total_alliances'] = cursor.fetchone()[0]

                resource_query = 'SELECT COUNT(*) FROM resource_pool'
                resource_params = []
                if education_type:
                    resource_query += ' WHERE education_type = ?'
                    resource_params.append(education_type)
                cursor.execute(resource_query, resource_params)
                stats['total_resources'] = cursor.fetchone()[0]

                agreement_query = 'SELECT COUNT(*) FROM cooperation_agreements WHERE status = ?'
                agreement_params = ['active']
                if education_type:
                    agreement_query += ' AND education_type = ?'
                    agreement_params.append(education_type)
                cursor.execute(agreement_query, agreement_params)
                stats['active_agreements'] = cursor.fetchone()[0]

                event_query = 'SELECT COUNT(*) FROM ecosystem_events WHERE status = ?'
                event_params = ['completed']
                if education_type:
                    event_query += ' AND education_type = ?'
                    event_params.append(education_type)
                cursor.execute(event_query, event_params)
                stats['completed_events'] = cursor.fetchone()[0]

                rating_query = 'SELECT AVG(rating) FROM ecosystem_ratings'
                rating_params = []
                if education_type:
                    rating_query += ' WHERE education_type = ?'
                    rating_params.append(education_type)
                cursor.execute(rating_query, rating_params)
                avg_rating = cursor.fetchone()[0]
                stats['average_rating'] = round(avg_rating, 1) if avg_rating else 0

                cursor.execute('SELECT partner_type, COUNT(*) as cnt FROM ecosystem_partners WHERE status = ? GROUP BY partner_type', ('approved',))
                stats['partner_type_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}

                cursor.execute('SELECT industry_sector, COUNT(*) as cnt FROM ecosystem_partners WHERE status = ? GROUP BY industry_sector', ('approved',))
                stats['sector_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}

                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取生态统计失败: {e}')
            return {'success': False, 'error': str(e)}