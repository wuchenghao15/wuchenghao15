from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育法律事务服务 (v15.18.0) ==================================== 提供教育领域法律事务、合同管理、知识产权、纠纷处理等综合法律服务。  核心能力： 1. 法律事务 - 文件管理、法律审查、法律意见、法律研究 2. 合同管理 - 合同起草、版本管理、审批流程、合同归档 3. 知识产权 - 知识产权登记、专利管理、商标管理、版权保护 4. 纠纷处理 - 案件登记、案件管理、诉讼代理、仲裁代理 5. 法律顾问 - 法律咨询、法律意见、合规指导、风险提示 6. 法律合规 - 合规审查、合规检查、合规培训、合规报告 7. 法律培训 - 培训管理、培训安排、培训记录、培训评估 8. 法律风险管理 - 风险识别、风险评估、风险控制、风险预警 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_legal_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationLegal')


# ========== 法律配置 ==========

LEGAL_AREAS = {
    'education': {'name': '教育法', 'description': '教育领域相关法律法规'},
    'civil': {'name': '民法', 'description': '民事法律关系规范'},
    'criminal': {'name': '刑法', 'description': '刑事法律责任规范'},
    'administrative': {'name': '行政法', 'description': '行政法律关系规范'},
    'labor': {'name': '劳动法', 'description': '劳动关系与劳动权益'},
    'contract': {'name': '合同法', 'description': '合同订立与履行规则'},
    'intellectual_property': {'name': '知识产权法', 'description': '知识产权保护法律'},
    'data_protection': {'name': '数据保护法', 'description': '数据安全与隐私保护'}
}

CONTRACT_TYPES = {
    'cooperation': {'name': '合作协议', 'requires_approval': True},
    'service': {'name': '服务合同', 'requires_approval': True},
    'procurement': {'name': '采购合同', 'requires_approval': True},
    'labor': {'name': '劳动合同', 'requires_approval': True},
    'lease': {'name': '租赁合同', 'requires_approval': True},
    'authorization': {'name': '授权协议', 'requires_approval': True},
    'confidentiality': {'name': '保密协议', 'requires_approval': True},
    'framework': {'name': '框架协议', 'requires_approval': True}
}

IP_TYPES = {
    'patent': {'name': '专利', 'category': 'industrial'},
    'trademark': {'name': '商标', 'category': 'commercial'},
    'copyright': {'name': '版权', 'category': 'creative'},
    'trade_secret': {'name': '商业秘密', 'category': 'confidential'},
    'domain': {'name': '域名', 'category': 'commercial'},
    'software_copyright': {'name': '软件著作权', 'category': 'creative'},
    'circuit_layout': {'name': '集成电路布图', 'category': 'industrial'},
    'plant_variety': {'name': '植物新品种', 'category': 'industrial'}
}

DISPUTE_TYPES = {
    'contract': {'name': '合同纠纷', 'legal_area': 'contract'},
    'labor': {'name': '劳动纠纷', 'legal_area': 'labor'},
    'intellectual_property': {'name': '知识产权纠纷', 'legal_area': 'intellectual_property'},
    'tort': {'name': '侵权纠纷', 'legal_area': 'civil'},
    'administrative': {'name': '行政纠纷', 'legal_area': 'administrative'},
    'civil': {'name': '民事纠纷', 'legal_area': 'civil'},
    'criminal': {'name': '刑事纠纷', 'legal_area': 'criminal'},
    'foreign': {'name': '涉外纠纷', 'legal_area': 'civil'}
}

LEGAL_SERVICE_TYPES = {
    'consultation': {'name': '法律咨询', 'requires_record': True},
    'contract_review': {'name': '合同审查', 'requires_record': True},
    'legal_opinion': {'name': '法律意见', 'requires_record': True},
    'litigation': {'name': '诉讼代理', 'requires_record': True},
    'arbitration': {'name': '仲裁代理', 'requires_record': True},
    'compliance_review': {'name': '合规审查', 'requires_record': True},
    'risk_assessment': {'name': '风险评估', 'requires_record': True},
    'training': {'name': '法律培训', 'requires_record': True}
}

COMPLIANCE_CHECKLIST = {
    'data_privacy': {'name': '数据隐私', 'required': True},
    'information_security': {'name': '信息安全', 'required': True},
    'enrollment': {'name': '招生合规', 'required': True},
    'financial': {'name': '财务合规', 'required': True},
    'employment': {'name': '用工合规', 'required': True},
    'academic_integrity': {'name': '学术诚信', 'required': True},
    'campus_safety': {'name': '校园安全', 'required': True},
    'external_cooperation': {'name': '对外合作', 'required': True}
}

TRAINING_TOPICS = {
    'education_law': {'name': '教育法规', 'duration': 3},
    'contract_management': {'name': '合同管理', 'duration': 2},
    'intellectual_property': {'name': '知识产权', 'duration': 3},
    'data_protection': {'name': '数据保护', 'duration': 2},
    'labor_compliance': {'name': '劳动合规', 'duration': 2},
    'academic_integrity': {'name': '学术诚信', 'duration': 1},
    'risk_prevention': {'name': '风险防范', 'duration': 2},
    'emergency_response': {'name': '应急处理', 'duration': 1}
}

RISK_LEVELS = {
    'low': {'name': '低风险', 'color': '#22c55e', 'action': '监控'},
    'medium': {'name': '中等风险', 'color': '#eab308', 'action': '关注'},
    'high': {'name': '高风险', 'color': '#f97316', 'action': '处理'},
    'critical': {'name': '重大风险', 'color': '#ef4444', 'action': '紧急'},
    'crisis': {'name': '危机风险', 'color': '#dc2626', 'action': '立即'}
}


class EducationLegalService:
    """教育法律事务服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS legal_documents ( document_id TEXT PRIMARY KEY, document_name TEXT NOT NULL, legal_area TEXT, document_type TEXT, education_type TEXT, content TEXT, version TEXT DEFAULT '1.0', status TEXT DEFAULT 'draft', created_by TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS document_reviews ( review_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, reviewer_id INTEGER, reviewer_name TEXT, review_status TEXT DEFAULT 'pending', review_comments TEXT, review_date TEXT, FOREIGN KEY (document_id) REFERENCES legal_documents(document_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS contracts ( contract_id TEXT PRIMARY KEY, contract_name TEXT NOT NULL, contract_type TEXT, education_type TEXT, party_a TEXT, party_b TEXT, amount REAL DEFAULT 0, start_date TEXT, end_date TEXT, duration_days INTEGER, status TEXT DEFAULT 'draft', template_id TEXT, created_by TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS contract_versions ( version_id TEXT PRIMARY KEY, contract_id TEXT NOT NULL, version_number TEXT, content TEXT, change_summary TEXT, created_by TEXT, created_at TEXT, FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS contract_approvals ( approval_id TEXT PRIMARY KEY, contract_id TEXT NOT NULL, approver_id INTEGER, approver_name TEXT, approval_level INTEGER, approval_status TEXT DEFAULT 'pending', approval_comments TEXT, approval_date TEXT, FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS intellectual_property ( ip_id TEXT PRIMARY KEY, ip_name TEXT NOT NULL, ip_type TEXT, education_type TEXT, owner_name TEXT, registration_number TEXT, registration_date TEXT, expiration_date TEXT, status TEXT DEFAULT 'pending', description TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ip_registrations ( reg_id TEXT PRIMARY KEY, ip_id TEXT NOT NULL, registration_agency TEXT, application_date TEXT, approval_date TEXT, registration_number TEXT, certificate_url TEXT, status TEXT DEFAULT 'applied', FOREIGN KEY (ip_id) REFERENCES intellectual_property(ip_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS dispute_cases ( case_id TEXT PRIMARY KEY, case_name TEXT NOT NULL, dispute_type TEXT, education_type TEXT, legal_area TEXT, parties TEXT, amount REAL DEFAULT 0, case_status TEXT DEFAULT 'pending', court TEXT, filing_date TEXT, description TEXT, created_by TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS case_management ( record_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, action_type TEXT, action_description TEXT, responsible_person TEXT, deadline TEXT, status TEXT DEFAULT 'pending', completed_date TEXT, FOREIGN KEY (case_id) REFERENCES dispute_cases(case_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS legal_advisory ( advisory_id TEXT PRIMARY KEY, advisory_type TEXT, education_type TEXT, client_name TEXT, client_id INTEGER, subject TEXT, description TEXT, status TEXT DEFAULT 'pending', assigned_lawyer TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS advisory_records ( record_id TEXT PRIMARY KEY, advisory_id TEXT NOT NULL, record_type TEXT, content TEXT, created_by TEXT, created_at TEXT, FOREIGN KEY (advisory_id) REFERENCES legal_advisory(advisory_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS compliance_reviews ( review_id TEXT PRIMARY KEY, review_type TEXT, education_type TEXT, review_scope TEXT, review_date TEXT, status TEXT DEFAULT 'pending', reviewer_id INTEGER, reviewer_name TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS review_results ( result_id TEXT PRIMARY KEY, review_id TEXT NOT NULL, checklist_item TEXT, compliance_status TEXT, issue_description TEXT, recommendation TEXT, risk_level TEXT, FOREIGN KEY (review_id) REFERENCES compliance_reviews(review_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS legal_training ( training_id TEXT PRIMARY KEY, training_name TEXT NOT NULL, training_topic TEXT, education_type TEXT, trainer_name TEXT, trainer_id INTEGER, duration_hours INTEGER DEFAULT 2, start_date TEXT, end_date TEXT, location TEXT, max_participants INTEGER DEFAULT 50, registered_count INTEGER DEFAULT 0, status TEXT DEFAULT 'planned', materials_url TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS training_attendance ( attendance_id TEXT PRIMARY KEY, training_id TEXT NOT NULL, participant_id INTEGER, participant_name TEXT, education_type TEXT, attendance_status TEXT DEFAULT 'registered', completed_hours REAL DEFAULT 0, score REAL, feedback TEXT, attended_date TEXT, FOREIGN KEY (training_id) REFERENCES legal_training(training_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS legal_risk ( risk_id TEXT PRIMARY KEY, risk_name TEXT NOT NULL, risk_category TEXT, education_type TEXT, risk_level TEXT DEFAULT 'low', description TEXT, impact_description TEXT, likelihood REAL DEFAULT 0.5, impact REAL DEFAULT 0.5, status TEXT DEFAULT 'identified', owner_name TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS risk_assessments ( assessment_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL, assessment_date TEXT, assessor_id INTEGER, assessor_name TEXT, risk_level TEXT, assessment_note TEXT, mitigation_plan TEXT, FOREIGN KEY (risk_id) REFERENCES legal_risk(risk_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS legal_events ( event_id TEXT PRIMARY KEY, event_name TEXT NOT NULL, event_type TEXT, education_type TEXT, event_date TEXT, description TEXT, status TEXT DEFAULT 'upcoming', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS event_records ( record_id TEXT PRIMARY KEY, event_id TEXT NOT NULL, record_type TEXT, content TEXT, responsible_person TEXT, created_at TEXT, FOREIGN KEY (event_id) REFERENCES legal_events(event_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS regulatory_updates ( update_id TEXT PRIMARY KEY, title TEXT NOT NULL, legal_area TEXT, education_type TEXT, update_date TEXT, effective_date TEXT, source TEXT, content_summary TEXT, impact_level TEXT DEFAULT 'low', status TEXT DEFAULT 'unread', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS update_notifications ( notification_id TEXT PRIMARY KEY, update_id TEXT NOT NULL, user_id INTEGER, user_name TEXT, read_status TEXT DEFAULT 'unread', read_date TEXT, FOREIGN KEY (update_id) REFERENCES regulatory_updates(update_id) ) ''')
                conn.commit()
                logger.info('教育法律事务服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 法律事务 ==========

    def create_legal_document(self, document_name: str, legal_area: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            document_id = f"ld_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO legal_documents ( document_id, document_name, legal_area, document_type, education_type, content, version, status, created_by, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, '1.0', 'draft', ?, ?, ?) ''', (document_id, document_name, legal_area,
                          kwargs.get('document_type'), kwargs.get('education_type'),
                          kwargs.get('content'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建法律文件: {document_name} ({document_id})')
                    return {'success': True, 'document_id': document_id}
        except Exception as e:
            logger.error(f'创建法律文件失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_document(self, document_id: str, reviewer_id: int,
                        reviewer_name: str, **kwargs) -> Dict[str, Any]:
        try:
            review_id = f"rv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO document_reviews ( review_id, document_id, reviewer_id, reviewer_name, review_status, review_comments, review_date ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (review_id, document_id, reviewer_id, reviewer_name,
                          kwargs.get('review_status', 'pending'),
                          kwargs.get('review_comments'), now))
                    conn.commit()
                    return {'success': True, 'review_id': review_id}
        except Exception as e:
            logger.error(f'审查文件失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_legal_opinion(self, document_id: str, opinion_content: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            opinion_id = f"lo_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE legal_documents SET status = ?, updated_at = ? WHERE document_id = ?',
                                 ('reviewed', now, document_id))
                    cursor.execute(''' INSERT INTO advisory_records ( record_id, advisory_id, record_type, content, created_by, created_at ) VALUES (?, ?, 'opinion', ?, ?, ?) ''', (opinion_id, document_id, opinion_content,
                          kwargs.get('created_by'), now))
                    conn.commit()
                    return {'success': True, 'opinion_id': opinion_id}
        except Exception as e:
            logger.error(f'生成法律意见失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_legal_documents(self, legal_area: str = None, education_type: str = None,
                             status: str = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM legal_documents WHERE 1=1'
                params = []
                if legal_area:
                    query += ' AND legal_area = ?'
                    params.append(legal_area)
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
                documents = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'documents': documents, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取法律文件列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合同管理 ==========

    def create_contract(self, contract_name: str, contract_type: str,
                        party_a: str, party_b: str, **kwargs) -> Dict[str, Any]:
        try:
            contract_id = f"ct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CONTRACT_TYPES.get(contract_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO contracts ( contract_id, contract_name, contract_type, education_type, party_a, party_b, amount, start_date, end_date, duration_days, status, template_id, created_by, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (contract_id, contract_name, contract_type,
                          kwargs.get('education_type'), party_a, party_b,
                          kwargs.get('amount', 0), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('duration_days'),
                          'draft', kwargs.get('template_id'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建合同: {contract_name} ({contract_id})')
                    return {'success': True, 'contract_id': contract_id}
        except Exception as e:
            logger.error(f'创建合同失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_contract_version(self, contract_id: str, version_number: str,
                             content: str, **kwargs) -> Dict[str, Any]:
        try:
            version_id = f"cv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO contract_versions ( version_id, contract_id, version_number, content, change_summary, created_by, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (version_id, contract_id, version_number, content,
                          kwargs.get('change_summary'), kwargs.get('created_by'), now))
                    cursor.execute('UPDATE contracts SET version = ?, updated_at = ? WHERE contract_id = ?',
                                 (version_number, now, contract_id))
                    conn.commit()
                    return {'success': True, 'version_id': version_id}
        except Exception as e:
            logger.error(f'添加合同版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_contract_approval(self, contract_id: str, **kwargs) -> Dict[str, Any]:
        try:
            approval_id = f"ca_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE contracts SET status = ? WHERE contract_id = ?',
                                 ('pending_approval', contract_id))
                    cursor.execute(''' INSERT INTO contract_approvals ( approval_id, contract_id, approver_id, approver_name, approval_level, approval_status, approval_comments, approval_date ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?) ''', (approval_id, contract_id, kwargs.get('approver_id'),
                          kwargs.get('approver_name'), kwargs.get('approval_level', 1),
                          kwargs.get('approval_comments'), now))
                    conn.commit()
                    return {'success': True, 'approval_id': approval_id}
        except Exception as e:
            logger.error(f'提交合同审批失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_contract(self, approval_id: str, approval_status: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT contract_id FROM contract_approvals WHERE approval_id = ?',
                                 (approval_id,))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '审批记录不存在'}
                    contract_id = result[0]
                    cursor.execute('UPDATE contract_approvals SET approval_status = ?, approval_comments = ?, approval_date = ? WHERE approval_id = ?',
                                 (approval_status, kwargs.get('approval_comments'), now, approval_id))
                    if approval_status == 'approved':
                        cursor.execute('UPDATE contracts SET status = ?, updated_at = ? WHERE contract_id = ?',
                                     ('approved', now, contract_id))
                    elif approval_status == 'rejected':
                        cursor.execute('UPDATE contracts SET status = ?, updated_at = ? WHERE contract_id = ?',
                                     ('draft', now, contract_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'审批合同失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_contract(self, contract_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE contracts SET status = ?, updated_at = ? WHERE contract_id = ?',
                                 ('archived', now, contract_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '合同不存在'}
        except Exception as e:
            logger.error(f'归档合同失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识产权 ==========

    def register_ip(self, ip_name: str, ip_type: str, owner_name: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            ip_id = f"ip_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = IP_TYPES.get(ip_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO intellectual_property ( ip_id, ip_name, ip_type, education_type, owner_name, registration_number, registration_date, expiration_date, status, description, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (ip_id, ip_name, ip_type, kwargs.get('education_type'),
                          owner_name, kwargs.get('registration_number'),
                          kwargs.get('registration_date'), kwargs.get('expiration_date'),
                          'pending', kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'注册知识产权: {ip_name} ({ip_id})')
                    return {'success': True, 'ip_id': ip_id}
        except Exception as e:
            logger.error(f'注册知识产权失败: {e}')
            return {'success': False, 'error': str(e)}

    def track_ip_registration(self, ip_id: str, registration_agency: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            reg_id = f"ir_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ip_registrations ( reg_id, ip_id, registration_agency, application_date, approval_date, registration_number, certificate_url, status ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (reg_id, ip_id, registration_agency,
                          kwargs.get('application_date', now[:10]),
                          kwargs.get('approval_date'), kwargs.get('registration_number'),
                          kwargs.get('certificate_url'), 'applied'))
                    conn.commit()
                    return {'success': True, 'reg_id': reg_id}
        except Exception as e:
            logger.error(f'跟踪知识产权注册失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_ip_status(self, ip_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE intellectual_property SET status = ?, expiration_date = ?, updated_at = ? WHERE ip_id = ?',
                                 (status, kwargs.get('expiration_date'), now, ip_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '知识产权不存在'}
        except Exception as e:
            logger.error(f'更新知识产权状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ip_assets(self, ip_type: str = None, education_type: str = None,
                       status: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM intellectual_property WHERE 1=1'
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
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                assets = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assets': assets, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取知识产权列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 纠纷处理 ==========

    def create_dispute_case(self, case_name: str, dispute_type: str,
                            parties: str, **kwargs) -> Dict[str, Any]:
        try:
            case_id = f"dc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = DISPUTE_TYPES.get(dispute_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO dispute_cases ( case_id, case_name, dispute_type, education_type, legal_area, parties, amount, case_status, court, filing_date, description, created_by, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (case_id, case_name, dispute_type, kwargs.get('education_type'),
                          config.get('legal_area', dispute_type), parties,
                          kwargs.get('amount', 0), 'pending', kwargs.get('court'),
                          kwargs.get('filing_date', now[:10]), kwargs.get('description'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建纠纷案件: {case_name} ({case_id})')
                    return {'success': True, 'case_id': case_id}
        except Exception as e:
            logger.error(f'创建纠纷案件失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_case_action(self, case_id: str, action_type: str,
                        action_description: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"cm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO case_management ( record_id, case_id, action_type, action_description, responsible_person, deadline, status, completed_date ) VALUES (?, ?, ?, ?, ?, ?, 'pending', NULL) ''', (record_id, case_id, action_type, action_description,
                          kwargs.get('responsible_person'), kwargs.get('deadline')))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加案件行动失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_case_status(self, case_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE dispute_cases SET case_status = ?, updated_at = ? WHERE case_id = ?',
                                 (status, now, case_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '案件不存在'}
        except Exception as e:
            logger.error(f'更新案件状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_dispute_cases(self, dispute_type: str = None, education_type: str = None,
                           case_status: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM dispute_cases WHERE 1=1'
                params = []
                if dispute_type:
                    query += ' AND dispute_type = ?'
                    params.append(dispute_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if case_status:
                    query += ' AND case_status = ?'
                    params.append(case_status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                cases = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'cases': cases, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取纠纷案件列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 法律顾问 ==========

    def create_advisory_request(self, advisory_type: str, client_name: str,
                                subject: str, **kwargs) -> Dict[str, Any]:
        try:
            advisory_id = f"la_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO legal_advisory ( advisory_id, advisory_type, education_type, client_name, client_id, subject, description, status, assigned_lawyer, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (advisory_id, advisory_type, kwargs.get('education_type'),
                          client_name, kwargs.get('client_id'), subject,
                          kwargs.get('description'), 'pending',
                          kwargs.get('assigned_lawyer'), now, now))
                    conn.commit()
                    logger.info(f'创建法律咨询请求: {subject} ({advisory_id})')
                    return {'success': True, 'advisory_id': advisory_id}
        except Exception as e:
            logger.error(f'创建法律咨询请求失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_advisory(self, advisory_id: str, lawyer_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE legal_advisory SET assigned_lawyer = ?, status = ?, updated_at = ? WHERE advisory_id = ?',
                                 (lawyer_name, 'processing', now, advisory_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '咨询请求不存在'}
        except Exception as e:
            logger.error(f'分配法律顾问失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_advisory_record(self, advisory_id: str, record_type: str,
                            content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"ar_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO advisory_records ( record_id, advisory_id, record_type, content, created_by, created_at ) VALUES (?, ?, ?, ?, ?, ?) ''', (record_id, advisory_id, record_type, content,
                          kwargs.get('created_by'), now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加咨询记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_advisory(self, advisory_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE legal_advisory SET status = ?, updated_at = ? WHERE advisory_id = ?',
                                 ('closed', now, advisory_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '咨询请求不存在'}
        except Exception as e:
            logger.error(f'关闭咨询请求失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 法律合规 ==========

    def create_compliance_review(self, review_type: str, review_scope: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            review_id = f"cr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO compliance_reviews ( review_id, review_type, education_type, review_scope, review_date, status, reviewer_id, reviewer_name, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (review_id, review_type, kwargs.get('education_type'),
                          review_scope, kwargs.get('review_date', now[:10]),
                          'pending', kwargs.get('reviewer_id'),
                          kwargs.get('reviewer_name'), now, now))
                    conn.commit()
                    logger.info(f'创建合规审查: {review_scope} ({review_id})')
                    return {'success': True, 'review_id': review_id}
        except Exception as e:
            logger.error(f'创建合规审查失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_review_result(self, review_id: str, checklist_item: str,
                          compliance_status: str, **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"rr_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO review_results ( result_id, review_id, checklist_item, compliance_status, issue_description, recommendation, risk_level ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (result_id, review_id, checklist_item, compliance_status,
                          kwargs.get('issue_description'), kwargs.get('recommendation'),
                          kwargs.get('risk_level', 'low')))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'添加审查结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_compliance_review(self, review_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE compliance_reviews SET status = ?, updated_at = ? WHERE review_id = ?',
                                 ('completed', now, review_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '合规审查不存在'}
        except Exception as e:
            logger.error(f'完成合规审查失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_compliance_reviews(self, review_type: str = None, education_type: str = None,
                                status: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM compliance_reviews WHERE 1=1'
                params = []
                if review_type:
                    query += ' AND review_type = ?'
                    params.append(review_type)
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
                reviews = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reviews': reviews, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合规审查列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 法律培训 ==========

    def create_training(self, training_name: str, training_topic: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"lt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TRAINING_TOPICS.get(training_topic, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO legal_training ( training_id, training_name, training_topic, education_type, trainer_name, trainer_id, duration_hours, start_date, end_date, location, max_participants, registered_count, status, materials_url, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?) ''', (training_id, training_name, training_topic,
                          kwargs.get('education_type'), kwargs.get('trainer_name'),
                          kwargs.get('trainer_id'), config.get('duration', 2),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('location'), kwargs.get('max_participants', 50),
                          'planned', kwargs.get('materials_url'), now, now))
                    conn.commit()
                    logger.info(f'创建法律培训: {training_name} ({training_id})')
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建法律培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_training(self, training_id: str, participant_id: int,
                          participant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            attendance_id = f"ta_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM legal_training WHERE training_id = ?',
                                 (training_id,))
                    training = cursor.fetchone()
                    if not training:
                        return {'success': False, 'error': '培训不存在'}
                    if training[2] != 'planned':
                        return {'success': False, 'error': '培训状态不允许报名'}
                    if training[0] and training[1] >= training[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO training_attendance (attendance_id, training_id, participant_id, participant_name, education_type, attendance_status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (attendance_id, training_id, participant_id, participant_name,
                                  kwargs.get('education_type'), 'registered'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE legal_training SET registered_count = registered_count + 1, updated_at = ? WHERE training_id = ?',
                                     (now, training_id))
                        conn.commit()
                        return {'success': True, 'attendance_id': attendance_id}
                    return {'success': False, 'error': '已报名该培训'}
        except Exception as e:
            logger.error(f'报名培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_attendance(self, attendance_id: str, completed_hours: float,
                                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE training_attendance SET attendance_status = ?, completed_hours = ?, score = ?, feedback = ?, attended_date = ? WHERE attendance_id = ?',
                                 ('completed', completed_hours, kwargs.get('score'),
                                  kwargs.get('feedback'), now[:10], attendance_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录培训出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_trainings(self, training_topic: str = None, education_type: str = None,
                       status: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM legal_training WHERE 1=1'
                params = []
                if training_topic:
                    query += ' AND training_topic = ?'
                    params.append(training_topic)
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
                trainings = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'trainings': trainings, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取培训列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 法律风险管理 ==========

    def identify_risk(self, risk_name: str, risk_category: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            risk_id = f"lr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO legal_risk ( risk_id, risk_name, risk_category, education_type, risk_level, description, impact_description, likelihood, impact, status, owner_name, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (risk_id, risk_name, risk_category, kwargs.get('education_type'),
                          kwargs.get('risk_level', 'low'), kwargs.get('description'),
                          kwargs.get('impact_description'), kwargs.get('likelihood', 0.5),
                          kwargs.get('impact', 0.5), 'identified',
                          kwargs.get('owner_name'), now, now))
                    conn.commit()
                    logger.info(f'识别法律风险: {risk_name} ({risk_id})')
                    return {'success': True, 'risk_id': risk_id}
        except Exception as e:
            logger.error(f'识别法律风险失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_risk(self, risk_id: str, assessor_id: int, assessor_name: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"ra_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO risk_assessments ( assessment_id, risk_id, assessment_date, assessor_id, assessor_name, risk_level, assessment_note, mitigation_plan ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (assessment_id, risk_id, now[:10], assessor_id, assessor_name,
                          kwargs.get('risk_level'), kwargs.get('assessment_note'),
                          kwargs.get('mitigation_plan')))
                    cursor.execute('UPDATE legal_risk SET risk_level = ?, updated_at = ? WHERE risk_id = ?',
                                 (kwargs.get('risk_level'), now, risk_id))
                    conn.commit()
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'评估法律风险失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_risk_status(self, risk_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE legal_risk SET status = ?, updated_at = ? WHERE risk_id = ?',
                                 (status, now, risk_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '风险不存在'}
        except Exception as e:
            logger.error(f'更新风险状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_risks(self, risk_category: str = None, education_type: str = None,
                   risk_level: str = None, page: int = 1,
                   page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM legal_risk WHERE 1=1'
                params = []
                if risk_category:
                    query += ' AND risk_category = ?'
                    params.append(risk_category)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if risk_level:
                    query += ' AND risk_level = ?'
                    params.append(risk_level)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                risks = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'risks': risks, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取风险列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 法规更新 ==========

    def add_regulatory_update(self, title: str, legal_area: str,
                              content_summary: str, **kwargs) -> Dict[str, Any]:
        try:
            update_id = f"ru_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO regulatory_updates ( update_id, title, legal_area, education_type, update_date, effective_date, source, content_summary, impact_level, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (update_id, title, legal_area, kwargs.get('education_type'),
                          kwargs.get('update_date', now[:10]), kwargs.get('effective_date'),
                          kwargs.get('source'), content_summary,
                          kwargs.get('impact_level', 'low'), 'unread', now))
                    conn.commit()
                    logger.info(f'添加法规更新: {title} ({update_id})')
                    return {'success': True, 'update_id': update_id}
        except Exception as e:
            logger.error(f'添加法规更新失败: {e}')
            return {'success': False, 'error': str(e)}

    def mark_update_read(self, update_id: str, user_id: int, user_name: str) -> Dict[str, Any]:
        try:
            notification_id = f"un_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO update_notifications (notification_id, update_id, user_id, user_name, read_status, read_date) VALUES (?, ?, ?, ?, ?, ?)',
                                 (notification_id, update_id, user_id, user_name, 'read', now))
                    cursor.execute('UPDATE regulatory_updates SET status = ? WHERE update_id = ?',
                                 ('read', update_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'标记法规更新已读失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_regulatory_updates(self, legal_area: str = None, education_type: str = None,
                                status: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM regulatory_updates WHERE 1=1'
                params = []
                if legal_area:
                    query += ' AND legal_area = ?'
                    params.append(legal_area)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY update_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                updates = [dict(u) for u in cursor.fetchall()]
                return {'success': True, 'updates': updates, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取法规更新列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_legal_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                filters = '' if not education_type else f"AND education_type = '{education_type}'"
                stats = {}

                cursor.execute(f'SELECT COUNT(*) FROM legal_documents WHERE 1=1 {filters}')
                stats['total_documents'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM contracts WHERE 1=1 {filters}')
                stats['total_contracts'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM intellectual_property WHERE 1=1 {filters}')
                stats['total_ip_assets'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM dispute_cases WHERE 1=1 {filters}')
                stats['total_cases'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM legal_advisory WHERE 1=1 {filters}')
                stats['total_advisories'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM compliance_reviews WHERE 1=1 {filters}')
                stats['total_compliance_reviews'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM legal_training WHERE 1=1 {filters}')
                stats['total_trainings'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM legal_risk WHERE 1=1 {filters}')
                stats['total_risks'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT risk_level, COUNT(*) FROM legal_risk WHERE 1=1 {filters} GROUP BY risk_level')
                stats['risk_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}

                cursor.execute(f'SELECT status, COUNT(*) FROM contracts WHERE 1=1 {filters} GROUP BY status')
                stats['contract_status_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}

                stats['education_type'] = education_type or 'all'
                stats['generated_at'] = datetime.now().isoformat()

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取法律统计数据失败: {e}')
            return {'success': False, 'error': str(e)}