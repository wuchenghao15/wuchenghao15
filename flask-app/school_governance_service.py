#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 学校治理与制度管理服务 (v15.11.0)
==========================================
提供学校规章制度、民主管理、决策管理、校务公开、合同管理、
法律事务、应急管理与档案管理等综合治理服务。模块同时支持成人教育
与 K12 教育的差异化需求。

核心能力：
1. 规章制度 - 校规校纪、制度发布、版本管理、制度汇编
2. 民主管理 - 教代会、学代会、家委会、校务委员会
3. 决策管理 - 重大事项决策、三重一大、决策记录
4. 校务公开 - 公开事项、公示管理、信息公开
5. 合同管理 - 合同台账、审批、执行
6. 法律事务 - 法律咨询、合同审查、纠纷处理
7. 应急管理 - 应急预案、事件处置、演练记录
8. 档案管理 - 学校档案、文件归档、查阅管理
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'school_governance_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SchoolGovernance')


# ========== 学校治理配置 ==========

# 制度类别
REGULATION_CATEGORIES = {
    'school_rules': {'name': '校规校纪', 'prefix': 'school_rules'},
    'student_discipline': {'name': '学生管理', 'prefix': 'student_discipline'},
    'teaching_management': {'name': '教学管理', 'prefix': 'teaching_management'},
    'personnel': {'name': '人事', 'prefix': 'personnel'},
    'finance': {'name': '财务', 'prefix': 'finance'},
    'safety': {'name': '安全', 'prefix': 'safety'},
    'logistics': {'name': '后勤', 'prefix': 'logistics'},
    'academic_affairs': {'name': '教务', 'prefix': 'academic_affairs'},
    'research': {'name': '科研', 'prefix': 'research'},
    'international': {'name': '国际交流', 'prefix': 'international'}
}

# 制度状态
REGULATION_STATUS = {
    'draft': {'name': '草稿', 'color': 'gray'},
    'under_review': {'name': '审核中', 'color': 'orange'},
    'published': {'name': '已发布', 'color': 'green'},
    'revising': {'name': '修订中', 'color': 'blue'},
    'abolished': {'name': '废止', 'color': 'red'}
}

# 会议类型
MEETING_TYPES = {
    'teacher_congress': {'name': '教代会', 'frequency': '每年一次'},
    'student_congress': {'name': '学代会', 'frequency': '每年一次'},
    'school_committee': {'name': '校务委员会', 'frequency': '每月一次'},
    'academic_committee': {'name': '学术委员会', 'frequency': '每季度一次'},
    'parent_committee': {'name': '家委会', 'frequency': '每学期一次'},
    'admin_meeting': {'name': '行政会', 'frequency': '每周一次'}
}

# 决策级别
DECISION_LEVELS = {
    'major': {'name': '重大', 'requires_committee': True},
    'important': {'name': '重要', 'requires_committee': True},
    'general': {'name': '一般', 'requires_committee': False},
    'routine': {'name': '日常', 'requires_committee': False}
}

# 校务公开类别
DISCLOSURE_CATEGORIES = {
    'school_overview': {'name': '学校概况', 'is_mandatory': True},
    'admissions': {'name': '招生', 'is_mandatory': True},
    'finance': {'name': '财务', 'is_mandatory': True},
    'personnel': {'name': '人事', 'is_mandatory': True},
    'teaching': {'name': '教学', 'is_mandatory': True},
    'safety': {'name': '安全', 'is_mandatory': True},
    'logistics': {'name': '后勤', 'is_mandatory': False},
    'student_affairs': {'name': '学生事务', 'is_mandatory': True},
    'other': {'name': '其他', 'is_mandatory': False}
}

# 合同类型
CONTRACT_TYPES = {
    'procurement': {'name': '采购', 'requires_legal_review': True},
    'service': {'name': '服务', 'requires_legal_review': True},
    'construction': {'name': '建设', 'requires_legal_review': True},
    'lease': {'name': '租赁', 'requires_legal_review': True},
    'cooperation': {'name': '合作', 'requires_legal_review': True},
    'employment': {'name': '聘用', 'requires_legal_review': False},
    'insurance': {'name': '保险', 'requires_legal_review': False},
    'other': {'name': '其他', 'requires_legal_review': False}
}

# 应急等级
EMERGENCY_LEVELS = {
    'level1': {'name': '一级特别重大', 'response_time': '立即响应'},
    'level2': {'name': '二级重大', 'response_time': '30分钟内响应'},
    'level3': {'name': '三级较大', 'response_time': '1小时内响应'},
    'level4': {'name': '四级一般', 'response_time': '2小时内响应'}
}

# 档案类别
ARCHIVE_CATEGORIES = {
    'administrative': {'name': '行政', 'retention_years': 30},
    'teaching': {'name': '教学', 'retention_years': 50},
    'student': {'name': '学生', 'retention_years': 50},
    'finance': {'name': '财务', 'retention_years': 25},
    'personnel': {'name': '人事', 'retention_years': 50},
    'asset': {'name': '资产', 'retention_years': 20},
    'contract': {'name': '合同', 'retention_years': 15},
    'meeting': {'name': '会议', 'retention_years': 30},
    'honor': {'name': '荣誉', 'retention_years': 100},
    'historical': {'name': '校史', 'retention_years': 100}
}


class SchoolGovernanceService:
    """学校治理与制度管理服务"""

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
                    CREATE TABLE IF NOT EXISTS regulations (
                        regulation_id TEXT PRIMARY KEY,
                        regulation_name TEXT NOT NULL,
                        regulation_code TEXT,
                        category TEXT NOT NULL,
                        version TEXT DEFAULT 'v1.0',
                        description TEXT,
                        content TEXT,
                        effective_date TEXT,
                        expiry_date TEXT,
                        issued_by TEXT,
                        approved_by TEXT,
                        approved_at TEXT,
                        status TEXT DEFAULT 'draft',
                        education_type TEXT DEFAULT 'common',
                        attachments TEXT,
                        view_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS regulation_revisions (
                        revision_id TEXT PRIMARY KEY,
                        regulation_id TEXT NOT NULL,
                        old_version TEXT,
                        new_version TEXT,
                        revision_content TEXT,
                        revised_by TEXT,
                        revised_at TEXT,
                        approved_by TEXT,
                        approved_at TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meetings (
                        meeting_id TEXT PRIMARY KEY,
                        meeting_name TEXT NOT NULL,
                        meeting_type TEXT NOT NULL,
                        convener_id TEXT,
                        convener_name TEXT,
                        meeting_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        location TEXT,
                        attendees_count INTEGER DEFAULT 0,
                        agenda TEXT,
                        minutes TEXT,
                        resolutions TEXT,
                        status TEXT DEFAULT 'scheduled',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meeting_attendees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id TEXT NOT NULL,
                        user_id TEXT,
                        user_name TEXT,
                        role TEXT,
                        attend_status TEXT DEFAULT 'present',
                        proxy_name TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS major_decisions (
                        decision_id TEXT PRIMARY KEY,
                        decision_title TEXT NOT NULL,
                        decision_level TEXT NOT NULL,
                        category TEXT,
                        description TEXT,
                        rationale TEXT,
                        proposed_by TEXT,
                        proposed_date TEXT,
                        meeting_id TEXT,
                        alternatives TEXT,
                        final_decision TEXT,
                        decision_result TEXT,
                        implemented_by TEXT,
                        implementation_status TEXT DEFAULT 'pending',
                        status TEXT DEFAULT 'proposed',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS disclosures (
                        disclosure_id TEXT PRIMARY KEY,
                        disclosure_title TEXT NOT NULL,
                        disclosure_category TEXT NOT NULL,
                        content TEXT,
                        target_audience TEXT,
                        publish_date TEXT,
                        publish_channel TEXT,
                        feedback TEXT,
                        status TEXT DEFAULT 'draft',
                        published_by TEXT,
                        published_at TEXT,
                        expires_at TEXT,
                        view_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS contracts (
                        contract_id TEXT PRIMARY KEY,
                        contract_name TEXT NOT NULL,
                        contract_type TEXT NOT NULL,
                        contract_number TEXT,
                        party_a TEXT,
                        party_b TEXT,
                        signing_date TEXT,
                        effective_date TEXT,
                        expiry_date TEXT,
                        amount REAL DEFAULT 0,
                        payment_terms TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'draft',
                        legal_review INTEGER DEFAULT 0,
                        legal_reviewer TEXT,
                        legal_review_result TEXT,
                        attachments TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS contract_approvals (
                        approval_id TEXT PRIMARY KEY,
                        contract_id TEXT NOT NULL,
                        approver_id TEXT,
                        approver_name TEXT,
                        approval_level INTEGER,
                        approval_result TEXT,
                        approval_comment TEXT,
                        approved_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS legal_affairs (
                        legal_id TEXT PRIMARY KEY,
                        case_name TEXT NOT NULL,
                        case_type TEXT NOT NULL,
                        description TEXT,
                        involved_parties TEXT,
                        status TEXT DEFAULT 'open',
                        handler_id TEXT,
                        handler_name TEXT,
                        start_date TEXT,
                        close_date TEXT,
                        outcome TEXT,
                        documents TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS emergency_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        emergency_type TEXT,
                        emergency_level TEXT,
                        description TEXT,
                        response_procedures TEXT,
                        responsible_persons TEXT,
                        resources TEXT,
                        contact_list TEXT,
                        version TEXT DEFAULT 'v1.0',
                        approved_by TEXT,
                        approved_at TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS emergency_events (
                        event_id TEXT PRIMARY KEY,
                        event_name TEXT NOT NULL,
                        event_type TEXT,
                        emergency_level TEXT,
                        occurred_at TEXT,
                        location TEXT,
                        description TEXT,
                        affected_scope TEXT,
                        casualties INTEGER DEFAULT 0,
                        injuries INTEGER DEFAULT 0,
                        property_loss REAL DEFAULT 0,
                        response_actions TEXT,
                        handled_by TEXT,
                        handled_at TEXT,
                        outcome TEXT,
                        reported_to TEXT,
                        follow_up TEXT,
                        status TEXT DEFAULT 'ongoing',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS emergency_drills (
                        drill_id TEXT PRIMARY KEY,
                        plan_id TEXT,
                        drill_name TEXT NOT NULL,
                        drill_type TEXT,
                        drill_date TEXT,
                        participants_count INTEGER DEFAULT 0,
                        scenario TEXT,
                        execution TEXT,
                        evaluation TEXT,
                        issues_found TEXT,
                        improvements TEXT,
                        organized_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS archives (
                        archive_id TEXT PRIMARY KEY,
                        archive_name TEXT NOT NULL,
                        archive_code TEXT,
                        category TEXT NOT NULL,
                        description TEXT,
                        file_format TEXT,
                        storage_location TEXT,
                        box_number TEXT,
                        created_date TEXT,
                        retention_years INTEGER DEFAULT 30,
                        security_level TEXT DEFAULT 'internal',
                        responsible_person TEXT,
                        keywords TEXT,
                        related_files TEXT,
                        status TEXT DEFAULT 'archived',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS archive_access (
                        access_id TEXT PRIMARY KEY,
                        archive_id TEXT NOT NULL,
                        requester_id TEXT,
                        requester_name TEXT,
                        request_date TEXT,
                        purpose TEXT,
                        approved_by TEXT,
                        approved_at TEXT,
                        access_period TEXT,
                        access_status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('学校治理与制度管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 规章制度 ==========

    def _generate_regulation_code(self, category: str, conn) -> str:
        """生成制度编号：类别前缀-年份-序号"""
        config = REGULATION_CATEGORIES.get(category, {})
        prefix = config.get('prefix', category)
        year = datetime.now().year
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM regulations WHERE category = ? AND regulation_code LIKE ?',
            (category, f'{prefix}-{year}-%')
        )
        count = cursor.fetchone()[0] or 0
        return f'{prefix}-{year}-{count + 1:03d}'

    def create_regulation(self, regulation_name: str, category: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            regulation_id = f"sg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    code = self._generate_regulation_code(category, conn)
                    cursor.execute('''
                        INSERT INTO regulations (
                            regulation_id, regulation_name, regulation_code, category,
                            version, description, content, effective_date, expiry_date,
                            issued_by, approved_by, approved_at, status, education_type,
                            attachments, view_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, 0, ?, ?)
                    ''', (regulation_id, regulation_name, code, category,
                          kwargs.get('version', 'v1.0'),
                          kwargs.get('description'), kwargs.get('content'),
                          kwargs.get('effective_date'), kwargs.get('expiry_date'),
                          kwargs.get('issued_by'), kwargs.get('approved_by'),
                          kwargs.get('status', 'draft'),
                          kwargs.get('education_type', 'common'),
                          json.dumps(kwargs.get('attachments', []), ensure_ascii=False),
                          now, now))
                    conn.commit()
                    logger.info(f'创建规章制度: {regulation_name} ({regulation_id})')
                    return {'success': True, 'regulation_id': regulation_id, 'regulation_code': code}
        except Exception as e:
            logger.error(f'创建规章制度失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_regulation(self, regulation_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE regulations SET status = 'published', approved_by = ?,
                            approved_at = ?, effective_date = COALESCE(?, effective_date),
                            updated_at = ?
                        WHERE regulation_id = ? AND status IN ('draft', 'under_review')
                    ''', (kwargs.get('approved_by'), now,
                          kwargs.get('effective_date'), now, regulation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'发布规章制度: {regulation_id}')
                        return {'success': True, 'status': 'published'}
                    return {'success': False, 'error': '制度不存在或状态不允许发布'}
        except Exception as e:
            logger.error(f'发布规章制度失败: {e}')
            return {'success': False, 'error': str(e)}

    def revise_regulation(self, regulation_id: str, **kwargs) -> Dict[str, Any]:
        try:
            revision_id = f"sgr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            new_version = kwargs.get('new_version')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT version, status FROM regulations WHERE regulation_id = ?', (regulation_id,))
                    reg = cursor.fetchone()
                    if not reg:
                        return {'success': False, 'error': '制度不存在'}
                    old_version = reg[0]
                    if not new_version:
                        new_version = self._bump_version(old_version)
                    cursor.execute('''
                        INSERT INTO regulation_revisions (
                            revision_id, regulation_id, old_version, new_version,
                            revision_content, revised_by, revised_at, approved_by,
                            approved_at, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    ''', (revision_id, regulation_id, old_version, new_version,
                          kwargs.get('revision_content'),
                          kwargs.get('revised_by'), now,
                          kwargs.get('approved_by'),
                          kwargs.get('status', 'pending'), now))
                    cursor.execute('''
                        UPDATE regulations SET version = ?, status = 'revising',
                            content = COALESCE(?, content), updated_at = ?
                        WHERE regulation_id = ?
                    ''', (new_version, kwargs.get('content'), now, regulation_id))
                    conn.commit()
                    logger.info(f'修订规章制度: {regulation_id} -> {new_version}')
                    return {'success': True, 'revision_id': revision_id, 'new_version': new_version}
        except Exception as e:
            logger.error(f'修订规章制度失败: {e}')
            return {'success': False, 'error': str(e)}

    def _bump_version(self, version: str) -> str:
        try:
            parts = version.lstrip('v').split('.')
            if len(parts) >= 2:
                parts[1] = str(int(parts[1]) + 1)
                return 'v' + '.'.join(parts)
            return version
        except Exception:
            return version

    def abolish_regulation(self, regulation_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE regulations SET status = 'abolished',
                            expiry_date = COALESCE(?, expiry_date), updated_at = ?
                        WHERE regulation_id = ? AND status != 'abolished'
                    ''', (kwargs.get('expiry_date', now[:10]), now, regulation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'废止规章制度: {regulation_id}')
                        return {'success': True, 'status': 'abolished'}
                    return {'success': False, 'error': '制度不存在或已废止'}
        except Exception as e:
            logger.error(f'废止规章制度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_regulation(self, regulation_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('UPDATE regulations SET view_count = view_count + 1 WHERE regulation_id = ?', (regulation_id,))
                    cursor.execute('SELECT * FROM regulations WHERE regulation_id = ?', (regulation_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '制度不存在'}
                    regulation = dict(row)
                    if regulation.get('attachments'):
                        regulation['attachments'] = json.loads(regulation['attachments'])
                    cursor.execute('SELECT * FROM regulation_revisions WHERE regulation_id = ? ORDER BY created_at DESC', (regulation_id,))
                    regulation['revisions'] = [dict(r) for r in cursor.fetchall()]
                    conn.commit()
                    return {'success': True, 'regulation': regulation}
        except Exception as e:
            logger.error(f'获取制度详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_regulations(self, page: int = 1, page_size: int = 20,
                         **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM regulations WHERE 1=1'
                params = []
                if filters.get('category'):
                    query += ' AND category = ?'
                    params.append(filters['category'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取制度列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 民主管理（会议） ==========

    def create_meeting(self, meeting_name: str, meeting_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            meeting_id = f"sgm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO meetings (
                            meeting_id, meeting_name, meeting_type, convener_id,
                            convener_name, meeting_date, start_time, end_time,
                            location, attendees_count, agenda, minutes, resolutions,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, NULL, NULL, ?, ?, ?)
                    ''', (meeting_id, meeting_name, meeting_type,
                          kwargs.get('convener_id'), kwargs.get('convener_name'),
                          kwargs.get('meeting_date'),
                          kwargs.get('start_time'), kwargs.get('end_time'),
                          kwargs.get('location'),
                          json.dumps(kwargs.get('agenda', []), ensure_ascii=False),
                          kwargs.get('status', 'scheduled'), now, now))
                    conn.commit()
                    logger.info(f'创建会议: {meeting_name} ({meeting_id})')
                    return {'success': True, 'meeting_id': meeting_id}
        except Exception as e:
            logger.error(f'创建会议失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_meeting_attendance(self, meeting_id: str, attendees: List[Dict[str, Any]],
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT meeting_id FROM meetings WHERE meeting_id = ?', (meeting_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '会议不存在'}
                    cursor.execute('DELETE FROM meeting_attendees WHERE meeting_id = ?', (meeting_id,))
                    present_count = 0
                    for att in attendees:
                        status = att.get('attend_status', 'present')
                        if status == 'present':
                            present_count += 1
                        cursor.execute('''
                            INSERT INTO meeting_attendees (
                                meeting_id, user_id, user_name, role,
                                attend_status, proxy_name, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (meeting_id, att.get('user_id'), att.get('user_name'),
                              att.get('role'), status, att.get('proxy_name'), now))
                    cursor.execute('UPDATE meetings SET attendees_count = ?, updated_at = ? WHERE meeting_id = ?',
                                 (present_count, now, meeting_id))
                    conn.commit()
                    return {'success': True, 'attendees_count': present_count}
        except Exception as e:
            logger.error(f'记录会议出席失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_meeting_minutes(self, meeting_id: str, minutes: str,
                               resolutions: List[Dict[str, Any]],
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE meetings SET minutes = ?, resolutions = ?,
                            status = 'completed', updated_at = ?
                        WHERE meeting_id = ?
                    ''', (minutes,
                          json.dumps(resolutions, ensure_ascii=False),
                          now, meeting_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'记录会议纪要: {meeting_id}')
                        return {'success': True}
                    return {'success': False, 'error': '会议不存在'}
        except Exception as e:
            logger.error(f'记录会议纪要失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_meeting(self, meeting_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM meetings WHERE meeting_id = ?', (meeting_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '会议不存在'}
                    meeting = dict(row)
                    if meeting.get('agenda'):
                        meeting['agenda'] = json.loads(meeting['agenda'])
                    if meeting.get('resolutions'):
                        meeting['resolutions'] = json.loads(meeting['resolutions'])
                    cursor.execute('SELECT * FROM meeting_attendees WHERE meeting_id = ?', (meeting_id,))
                    meeting['attendees'] = [dict(a) for a in cursor.fetchall()]
                    return {'success': True, 'meeting': meeting}
        except Exception as e:
            logger.error(f'获取会议详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_meetings(self, page: int = 1, page_size: int = 20,
                      **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM meetings WHERE 1=1'
                params = []
                if filters.get('meeting_type'):
                    query += ' AND meeting_type = ?'
                    params.append(filters['meeting_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY meeting_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取会议列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 决策管理 ==========

    def propose_decision(self, decision_title: str, decision_level: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            decision_id = f"sgd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO major_decisions (
                            decision_id, decision_title, decision_level, category,
                            description, rationale, proposed_by, proposed_date,
                            meeting_id, alternatives, final_decision, decision_result,
                            implemented_by, implementation_status, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, 'pending', 'proposed', ?, ?)
                    ''', (decision_id, decision_title, decision_level,
                          kwargs.get('category'), kwargs.get('description'),
                          kwargs.get('rationale'), kwargs.get('proposed_by'),
                          kwargs.get('proposed_date', now[:10]),
                          kwargs.get('meeting_id'),
                          json.dumps(kwargs.get('alternatives', []), ensure_ascii=False),
                          now, now))
                    conn.commit()
                    logger.info(f'提议重大决策: {decision_title} ({decision_id})')
                    return {'success': True, 'decision_id': decision_id}
        except Exception as e:
            logger.error(f'提议决策失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_decision(self, decision_id: str, decision_result: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    new_status = 'approved' if decision_result == 'approved' else 'rejected'
                    cursor.execute('''
                        UPDATE major_decisions SET decision_result = ?, final_decision = ?,
                            status = ?, updated_at = ?
                        WHERE decision_id = ? AND status = 'proposed'
                    ''', (decision_result, kwargs.get('final_decision'),
                          new_status, now, decision_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审议决策: {decision_id} -> {new_status}')
                        return {'success': True, 'status': new_status}
                    return {'success': False, 'error': '决策不存在或状态不允许审议'}
        except Exception as e:
            logger.error(f'审议决策失败: {e}')
            return {'success': False, 'error': str(e)}

    def implement_decision(self, decision_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE major_decisions SET implemented_by = ?,
                            implementation_status = ?, status = 'implemented', updated_at = ?
                        WHERE decision_id = ? AND status = 'approved'
                    ''', (kwargs.get('implemented_by'),
                          kwargs.get('implementation_status', 'in_progress'),
                          now, decision_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'implemented'}
                    return {'success': False, 'error': '决策不存在或状态不允许执行'}
        except Exception as e:
            logger.error(f'执行决策失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_decisions(self, page: int = 1, page_size: int = 20,
                       **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM major_decisions WHERE 1=1'
                params = []
                if filters.get('decision_level'):
                    query += ' AND decision_level = ?'
                    params.append(filters['decision_level'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取决策列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 校务公开 ==========

    def create_disclosure(self, disclosure_title: str, disclosure_category: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            disclosure_id = f"sgd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO disclosures (
                            disclosure_id, disclosure_title, disclosure_category,
                            content, target_audience, publish_date, publish_channel,
                            feedback, status, published_by, published_at, expires_at,
                            view_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, 0, ?, ?)
                    ''', (disclosure_id, disclosure_title, disclosure_category,
                          kwargs.get('content'), kwargs.get('target_audience'),
                          kwargs.get('publish_date'),
                          json.dumps(kwargs.get('publish_channel', []), ensure_ascii=False),
                          json.dumps(kwargs.get('feedback', []), ensure_ascii=False),
                          kwargs.get('status', 'draft'),
                          kwargs.get('expires_at'), now, now))
                    conn.commit()
                    logger.info(f'创建公开事项: {disclosure_title} ({disclosure_id})')
                    return {'success': True, 'disclosure_id': disclosure_id}
        except Exception as e:
            logger.error(f'创建公开事项失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_disclosure(self, disclosure_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE disclosures SET status = 'published', published_by = ?,
                            published_at = ?, publish_date = COALESCE(?, publish_date), updated_at = ?
                        WHERE disclosure_id = ? AND status = 'draft'
                    ''', (kwargs.get('published_by'), now,
                          kwargs.get('publish_date', now[:10]), now, disclosure_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'发布公开事项: {disclosure_id}')
                        return {'success': True, 'status': 'published'}
                    return {'success': False, 'error': '事项不存在或状态不允许发布'}
        except Exception as e:
            logger.error(f'发布公开事项失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_disclosure_feedback(self, disclosure_id: str, feedback: Dict[str, Any],
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT feedback FROM disclosures WHERE disclosure_id = ?', (disclosure_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '事项不存在'}
                    existing = json.loads(row[0]) if row[0] else []
                    feedback.setdefault('submitted_at', now)
                    existing.append(feedback)
                    cursor.execute('UPDATE disclosures SET feedback = ?, updated_at = ? WHERE disclosure_id = ?',
                                 (json.dumps(existing, ensure_ascii=False), now, disclosure_id))
                    conn.commit()
                    return {'success': True, 'feedback_count': len(existing)}
        except Exception as e:
            logger.error(f'添加公开事项反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_disclosures(self, page: int = 1, page_size: int = 20,
                         **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM disclosures WHERE 1=1'
                params = []
                if filters.get('disclosure_category'):
                    query += ' AND disclosure_category = ?'
                    params.append(filters['disclosure_category'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY publish_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取公开事项列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合同管理 ==========

    def _generate_contract_number(self, contract_type: str, conn) -> str:
        """生成合同编号：合同类型前缀-年月-序号"""
        prefix = CONTRACT_TYPES.get(contract_type, {}).get('name', contract_type)
        ym = datetime.now().strftime('%Y%m')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM contracts WHERE contract_type = ? AND contract_number LIKE ?',
            (contract_type, f'{prefix}-{ym}-%')
        )
        count = cursor.fetchone()[0] or 0
        return f'{prefix}-{ym}-{count + 1:03d}'

    def create_contract(self, contract_name: str, contract_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            contract_id = f"sgc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CONTRACT_TYPES.get(contract_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    number = self._generate_contract_number(contract_type, conn)
                    cursor.execute('''
                        INSERT INTO contracts (
                            contract_id, contract_name, contract_type, contract_number,
                            party_a, party_b, signing_date, effective_date, expiry_date,
                            amount, payment_terms, description, status, legal_review,
                            legal_reviewer, legal_review_result, attachments,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)
                    ''', (contract_id, contract_name, contract_type, number,
                          kwargs.get('party_a'), kwargs.get('party_b'),
                          kwargs.get('signing_date'), kwargs.get('effective_date'),
                          kwargs.get('expiry_date'), kwargs.get('amount', 0),
                          kwargs.get('payment_terms'), kwargs.get('description'),
                          kwargs.get('status', 'draft'),
                          1 if config.get('requires_legal_review') else 0,
                          kwargs.get('legal_reviewer'),
                          json.dumps(kwargs.get('attachments', []), ensure_ascii=False),
                          now, now))
                    conn.commit()
                    logger.info(f'创建合同: {contract_name} ({contract_id})')
                    return {'success': True, 'contract_id': contract_id, 'contract_number': number}
        except Exception as e:
            logger.error(f'创建合同失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_contract(self, contract_id: str, reviewer_id: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE contracts SET legal_review = 1, legal_reviewer = ?,
                            legal_review_result = ?, status = 'reviewed', updated_at = ?
                        WHERE contract_id = ? AND legal_review = 0
                    ''', (reviewer_id, kwargs.get('legal_review_result', 'pass'),
                          now, contract_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'法务审查合同: {contract_id}')
                        return {'success': True, 'status': 'reviewed'}
                    return {'success': False, 'error': '合同不存在或已审查'}
        except Exception as e:
            logger.error(f'法务审查合同失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_contract(self, contract_id: str, approver_id: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            approval_id = f"sgca_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT contract_id FROM contracts WHERE contract_id = ?', (contract_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '合同不存在'}
                    cursor.execute('''
                        INSERT INTO contract_approvals (
                            approval_id, contract_id, approver_id, approver_name,
                            approval_level, approval_result, approval_comment, approved_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (approval_id, contract_id, approver_id,
                          kwargs.get('approver_name'),
                          kwargs.get('approval_level', 1),
                          kwargs.get('approval_result', 'approved'),
                          kwargs.get('approval_comment'), now, now))
                    if kwargs.get('approval_result', 'approved') == 'approved':
                        cursor.execute('UPDATE contracts SET status = ?, updated_at = ? WHERE contract_id = ?',
                                     (kwargs.get('final_status', 'approved'), now, contract_id))
                    conn.commit()
                    logger.info(f'审批合同: {contract_id}')
                    return {'success': True, 'approval_id': approval_id}
        except Exception as e:
            logger.error(f'审批合同失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_contract(self, contract_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM contracts WHERE contract_id = ?', (contract_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '合同不存在'}
                    contract = dict(row)
                    if contract.get('attachments'):
                        contract['attachments'] = json.loads(contract['attachments'])
                    cursor.execute('SELECT * FROM contract_approvals WHERE contract_id = ? ORDER BY approval_level', (contract_id,))
                    contract['approvals'] = [dict(a) for a in cursor.fetchall()]
                    return {'success': True, 'contract': contract}
        except Exception as e:
            logger.error(f'获取合同详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_contracts(self, page: int = 1, page_size: int = 20,
                       **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM contracts WHERE 1=1'
                params = []
                if filters.get('contract_type'):
                    query += ' AND contract_type = ?'
                    params.append(filters['contract_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合同列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 法律事务 ==========

    def create_legal_affair(self, case_name: str, case_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            legal_id = f"sgl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO legal_affairs (
                            legal_id, case_name, case_type, description,
                            involved_parties, status, handler_id, handler_name,
                            start_date, close_date, outcome, documents,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)
                    ''', (legal_id, case_name, case_type,
                          kwargs.get('description'),
                          kwargs.get('involved_parties'),
                          kwargs.get('status', 'open'),
                          kwargs.get('handler_id'), kwargs.get('handler_name'),
                          kwargs.get('start_date', now[:10]),
                          json.dumps(kwargs.get('documents', []), ensure_ascii=False),
                          now, now))
                    conn.commit()
                    logger.info(f'创建法律事务: {case_name} ({legal_id})')
                    return {'success': True, 'legal_id': legal_id}
        except Exception as e:
            logger.error(f'创建法律事务失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_legal_affair(self, legal_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    for field in ('description', 'involved_parties', 'status',
                                  'handler_id', 'handler_name', 'outcome'):
                        if field in kwargs:
                            updates.append(f'{field} = ?')
                            params.append(kwargs[field])
                    if not updates:
                        return {'success': False, 'error': '未提供更新字段'}
                    updates.append('updated_at = ?')
                    params.append(now)
                    params.append(legal_id)
                    cursor.execute(f'UPDATE legal_affairs SET {", ".join(updates)} WHERE legal_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '法律事务不存在'}
        except Exception as e:
            logger.error(f'更新法律事务失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_legal_affair(self, legal_id: str, outcome: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE legal_affairs SET status = 'closed', outcome = ?,
                            close_date = ?, updated_at = ?
                        WHERE legal_id = ? AND status != 'closed'
                    ''', (outcome, kwargs.get('close_date', now[:10]), now, legal_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'结案法律事务: {legal_id}')
                        return {'success': True, 'status': 'closed'}
                    return {'success': False, 'error': '法律事务不存在或已结案'}
        except Exception as e:
            logger.error(f'结案法律事务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_legal_affairs(self, page: int = 1, page_size: int = 20,
                           **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM legal_affairs WHERE 1=1'
                params = []
                if filters.get('case_type'):
                    query += ' AND case_type = ?'
                    params.append(filters['case_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取法律事务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 应急管理 ==========

    def create_emergency_plan(self, plan_name: str, emergency_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"sge_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO emergency_plans (
                            plan_id, plan_name, emergency_type, emergency_level,
                            description, response_procedures, responsible_persons,
                            resources, contact_list, version, approved_by, approved_at,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)
                    ''', (plan_id, plan_name, emergency_type,
                          kwargs.get('emergency_level'),
                          kwargs.get('description'),
                          json.dumps(kwargs.get('response_procedures', []), ensure_ascii=False),
                          json.dumps(kwargs.get('responsible_persons', []), ensure_ascii=False),
                          json.dumps(kwargs.get('resources', []), ensure_ascii=False),
                          json.dumps(kwargs.get('contact_list', []), ensure_ascii=False),
                          kwargs.get('version', 'v1.0'),
                          kwargs.get('status', 'draft'), now, now))
                    conn.commit()
                    logger.info(f'创建应急预案: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建应急预案失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_emergency_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE emergency_plans SET status = 'approved', approved_by = ?,
                            approved_at = ?, version = COALESCE(?, version), updated_at = ?
                        WHERE plan_id = ? AND status = 'draft'
                    ''', (kwargs.get('approved_by'), now,
                          kwargs.get('version'), now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审批应急预案: {plan_id}')
                        return {'success': True, 'status': 'approved'}
                    return {'success': False, 'error': '预案不存在或状态不允许审批'}
        except Exception as e:
            logger.error(f'审批应急预案失败: {e}')
            return {'success': False, 'error': str(e)}

    def report_emergency_event(self, event_name: str, event_type: str,
                               emergency_level: str, **kwargs) -> Dict[str, Any]:
        try:
            event_id = f"sge_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO emergency_events (
                            event_id, event_name, event_type, emergency_level,
                            occurred_at, location, description, affected_scope,
                            casualties, injuries, property_loss, response_actions,
                            handled_by, handled_at, outcome, reported_to, follow_up,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, NULL, ?, ?, ?)
                    ''', (event_id, event_name, event_type, emergency_level,
                          kwargs.get('occurred_at', now),
                          kwargs.get('location'), kwargs.get('description'),
                          kwargs.get('affected_scope'),
                          kwargs.get('casualties', 0), kwargs.get('injuries', 0),
                          kwargs.get('property_loss', 0),
                          json.dumps(kwargs.get('response_actions', []), ensure_ascii=False),
                          kwargs.get('reported_to'),
                          kwargs.get('status', 'ongoing'), now, now))
                    conn.commit()
                    logger.info(f'报告应急事件: {event_name} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'报告应急事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def handle_emergency_event(self, event_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT response_actions FROM emergency_events WHERE event_id = ?', (event_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '事件不存在'}
                    actions = json.loads(row[0]) if row[0] else []
                    new_action = kwargs.get('response_action')
                    if new_action:
                        actions.append({'action': new_action, 'time': now})
                    cursor.execute('''
                        UPDATE emergency_events SET response_actions = ?,
                            handled_by = COALESCE(?, handled_by), handled_at = ?,
                            outcome = COALESCE(?, outcome), follow_up = COALESCE(?, follow_up),
                            status = ?, updated_at = ?
                        WHERE event_id = ?
                    ''', (json.dumps(actions, ensure_ascii=False),
                          kwargs.get('handled_by'), now,
                          kwargs.get('outcome'), kwargs.get('follow_up'),
                          kwargs.get('status', 'resolved'), now, event_id))
                    conn.commit()
                    logger.info(f'处置应急事件: {event_id}')
                    return {'success': True, 'status': kwargs.get('status', 'resolved')}
        except Exception as e:
            logger.error(f'处置应急事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def conduct_emergency_drill(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        try:
            drill_id = f"sgd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id FROM emergency_plans WHERE plan_id = ?', (plan_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '预案不存在'}
                    cursor.execute('''
                        INSERT INTO emergency_drills (
                            drill_id, plan_id, drill_name, drill_type, drill_date,
                            participants_count, scenario, execution, evaluation,
                            issues_found, improvements, organized_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (drill_id, plan_id,
                          kwargs.get('drill_name', '应急演练'),
                          kwargs.get('drill_type'),
                          kwargs.get('drill_date', now[:10]),
                          kwargs.get('participants_count', 0),
                          kwargs.get('scenario'), kwargs.get('execution'),
                          kwargs.get('evaluation'), kwargs.get('issues_found'),
                          kwargs.get('improvements'),
                          kwargs.get('organized_by'), now))
                    conn.commit()
                    logger.info(f'组织应急演练: {plan_id} ({drill_id})')
                    return {'success': True, 'drill_id': drill_id}
        except Exception as e:
            logger.error(f'组织应急演练失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_emergency_plans(self, page: int = 1, page_size: int = 20,
                             **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM emergency_plans WHERE 1=1'
                params = []
                if filters.get('emergency_type'):
                    query += ' AND emergency_type = ?'
                    params.append(filters['emergency_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取应急预案列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_emergency_events(self, page: int = 1, page_size: int = 20,
                              **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM emergency_events WHERE 1=1'
                params = []
                if filters.get('event_type'):
                    query += ' AND event_type = ?'
                    params.append(filters['event_type'])
                if filters.get('emergency_level'):
                    query += ' AND emergency_level = ?'
                    params.append(filters['emergency_level'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY occurred_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取应急事件列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 档案管理 ==========

    def _generate_archive_code(self, category: str, conn) -> str:
        """生成档案编号：类别-年份-序号"""
        year = datetime.now().year
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM archives WHERE category = ? AND archive_code LIKE ?',
            (category, f'{category}-{year}-%')
        )
        count = cursor.fetchone()[0] or 0
        return f'{category}-{year}-{count + 1:04d}'

    def create_archive(self, archive_name: str, category: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            archive_id = f"sga_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ARCHIVE_CATEGORIES.get(category, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    code = self._generate_archive_code(category, conn)
                    cursor.execute('''
                        INSERT INTO archives (
                            archive_id, archive_name, archive_code, category,
                            description, file_format, storage_location, box_number,
                            created_date, retention_years, security_level,
                            responsible_person, keywords, related_files, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (archive_id, archive_name, code, category,
                          kwargs.get('description'),
                          kwargs.get('file_format'),
                          kwargs.get('storage_location'),
                          kwargs.get('box_number'),
                          kwargs.get('created_date', now[:10]),
                          kwargs.get('retention_years', config.get('retention_years', 30)),
                          kwargs.get('security_level', 'internal'),
                          kwargs.get('responsible_person'),
                          json.dumps(kwargs.get('keywords', []), ensure_ascii=False),
                          json.dumps(kwargs.get('related_files', []), ensure_ascii=False),
                          kwargs.get('status', 'archived'), now, now))
                    conn.commit()
                    logger.info(f'创建档案: {archive_name} ({archive_id})')
                    return {'success': True, 'archive_id': archive_id, 'archive_code': code}
        except Exception as e:
            logger.error(f'创建档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def request_archive_access(self, archive_id: str, requester_id: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            access_id = f"sgac_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT archive_id FROM archives WHERE archive_id = ?', (archive_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '档案不存在'}
                    cursor.execute('''
                        INSERT INTO archive_access (
                            access_id, archive_id, requester_id, requester_name,
                            request_date, purpose, approved_by, approved_at,
                            access_period, access_status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, 'pending', ?)
                    ''', (access_id, archive_id, requester_id,
                          kwargs.get('requester_name'),
                          kwargs.get('request_date', now[:10]),
                          kwargs.get('purpose'),
                          kwargs.get('access_period'), now))
                    conn.commit()
                    logger.info(f'申请查阅档案: {archive_id} ({access_id})')
                    return {'success': True, 'access_id': access_id}
        except Exception as e:
            logger.error(f'申请查阅档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_archive_access(self, access_id: str, approved_by: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    access_status = kwargs.get('access_status', 'approved')
                    cursor.execute('''
                        UPDATE archive_access SET approved_by = ?, approved_at = ?,
                            access_status = ?
                        WHERE access_id = ? AND access_status = 'pending'
                    ''', (approved_by, now, access_status, access_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审批档案查阅: {access_id} -> {access_status}')
                        return {'success': True, 'access_status': access_status}
                    return {'success': False, 'error': '查阅申请不存在或已审批'}
        except Exception as e:
            logger.error(f'审批档案查阅失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_archives(self, page: int = 1, page_size: int = 20,
                      **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM archives WHERE 1=1'
                params = []
                if filters.get('category'):
                    query += ' AND category = ?'
                    params.append(filters['category'])
                if filters.get('security_level'):
                    query += ' AND security_level = ?'
                    params.append(filters['security_level'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取档案列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_archive_access(self, page: int = 1, page_size: int = 20,
                            **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM archive_access WHERE 1=1'
                params = []
                if filters.get('archive_id'):
                    query += ' AND archive_id = ?'
                    params.append(filters['archive_id'])
                if filters.get('access_status'):
                    query += ' AND access_status = ?'
                    params.append(filters['access_status'])
                if filters.get('requester_id'):
                    query += ' AND requester_id = ?'
                    params.append(filters['requester_id'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取档案查阅记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                reg_filter = ' WHERE education_type = ?' if education_type else ''
                reg_params = [education_type] if education_type else []

                # 制度类别分布
                cursor.execute(
                    f'SELECT category, COUNT(*) as cnt FROM regulations{reg_filter} GROUP BY category',
                    reg_params
                )
                regulation_category = {row['category']: row['cnt'] for row in cursor.fetchall()}

                # 制度状态分布
                cursor.execute(
                    f'SELECT status, COUNT(*) as cnt FROM regulations{reg_filter} GROUP BY status',
                    reg_params
                )
                regulation_status = {row['status']: row['cnt'] for row in cursor.fetchall()}

                # 会议类型统计
                cursor.execute('SELECT meeting_type, COUNT(*) as cnt FROM meetings GROUP BY meeting_type')
                meeting_types = {row['meeting_type']: row['cnt'] for row in cursor.fetchall()}

                # 决策级别分布
                cursor.execute('SELECT decision_level, COUNT(*) as cnt FROM major_decisions GROUP BY decision_level')
                decision_levels = {row['decision_level']: row['cnt'] for row in cursor.fetchall()}

                # 合同类型分布
                cursor.execute('SELECT contract_type, COUNT(*) as cnt FROM contracts GROUP BY contract_type')
                contract_types = {row['contract_type']: row['cnt'] for row in cursor.fetchall()}

                # 应急事件统计
                cursor.execute('SELECT status, COUNT(*) as cnt FROM emergency_events GROUP BY status')
                emergency_events = {row['status']: row['cnt'] for row in cursor.fetchall()}
                cursor.execute('SELECT emergency_level, COUNT(*) as cnt FROM emergency_events GROUP BY emergency_level')
                emergency_levels = {row['emergency_level']: row['cnt'] for row in cursor.fetchall()}

                # 档案类别分布
                cursor.execute('SELECT category, COUNT(*) as cnt FROM archives GROUP BY category')
                archive_categories = {row['category']: row['cnt'] for row in cursor.fetchall()}

                cursor.execute('SELECT COUNT(*) as cnt FROM regulations')
                total_regulations = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM meetings')
                total_meetings = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM major_decisions')
                total_decisions = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM contracts')
                total_contracts = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM legal_affairs')
                total_legal = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM emergency_plans')
                total_plans = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM emergency_events')
                total_events = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM archives')
                total_archives = cursor.fetchone()['cnt']

                return {
                    'success': True,
                    'education_type': education_type,
                    'summary': {
                        'total_regulations': total_regulations,
                        'total_meetings': total_meetings,
                        'total_decisions': total_decisions,
                        'total_contracts': total_contracts,
                        'total_legal_affairs': total_legal,
                        'total_emergency_plans': total_plans,
                        'total_emergency_events': total_events,
                        'total_archives': total_archives
                    },
                    'regulation_category_distribution': regulation_category,
                    'regulation_status_distribution': regulation_status,
                    'meeting_type_statistics': meeting_types,
                    'decision_level_distribution': decision_levels,
                    'contract_type_distribution': contract_types,
                    'emergency_event_statistics': {
                        'by_status': emergency_events,
                        'by_level': emergency_levels
                    },
                    'archive_category_distribution': archive_categories
                }
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = SchoolGovernanceService()
    print('学校治理与制度管理服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
