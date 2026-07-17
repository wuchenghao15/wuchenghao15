#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育合规与风险管理服务 (v15.18.0)
=========================================
提供合规管理、风险评估、内部控制、审计监督、合规培训、风险预警、合规报告、合规检查等综合管理服务。

核心能力：
1. 合规管理 - 合规政策、政策版本、合规评估、合规整改
2. 风险评估 - 风险识别、风险分析、风险评价、风险登记
3. 内部控制 - 控制设计、控制测试、控制评价、控制优化
4. 审计监督 - 审计计划、审计执行、审计发现、审计报告、跟踪整改
5. 合规培训 - 培训计划、培训实施、培训考核、培训记录
6. 风险预警 - 预警指标、预警监测、预警处置、预警历史
7. 合规报告 - 报告生成、报告审核、报告发布、报告归档
8. 合规检查 - 检查计划、检查执行、检查结果、问题整改
9. 举报管理 - 举报受理、举报调查、举报处置
10. 统计分析 - 综合统计报表
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_compliance_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationCompliance')


# ========== 合规配置 ==========

COMPLIANCE_AREAS = {
    'education_law': {'name': '教育法规', 'description': '教育相关法律法规合规'},
    'data_privacy': {'name': '数据隐私', 'description': '学生/教职工数据保护合规'},
    'security_compliance': {'name': '安全合规', 'description': '信息安全与网络安全合规'},
    'financial_compliance': {'name': '财务合规', 'description': '财务管理制度合规'},
    'human_resources': {'name': '人力资源', 'description': '人事管理与劳动合规'},
    'enrollment_compliance': {'name': '招生合规', 'description': '招生政策与流程合规'},
    'academic_integrity': {'name': '学术诚信', 'description': '学术规范与诚信要求'},
    'campus_safety': {'name': '校园安全', 'description': '校园安全管理合规'}
}

RISK_TYPES = {
    'strategic': {'name': '战略风险', 'description': '影响组织战略目标实现的风险'},
    'operational': {'name': '运营风险', 'description': '日常运营活动中的风险'},
    'financial': {'name': '财务风险', 'description': '财务方面的风险'},
    'compliance': {'name': '合规风险', 'description': '违反法律法规的风险'},
    'security': {'name': '安全风险', 'description': '人身与财产安全风险'},
    'reputation': {'name': '声誉风险', 'description': '损害组织声誉的风险'},
    'technical': {'name': '技术风险', 'description': '技术系统相关风险'},
    'market': {'name': '市场风险', 'description': '市场环境变化带来的风险'}
}

RISK_LEVELS = {
    'low': {'name': '低风险', 'score_range': (0, 20), 'color': '#22c55e'},
    'medium': {'name': '中等风险', 'score_range': (21, 40), 'color': '#eab308'},
    'high': {'name': '高风险', 'score_range': (41, 60), 'color': '#f97316'},
    'critical': {'name': '重大风险', 'score_range': (61, 80), 'color': '#ef4444'},
    'crisis': {'name': '危机风险', 'score_range': (81, 100), 'color': '#dc2626'}
}

CONTROL_TYPES = {
    'preventive': {'name': '预防性控制', 'description': '防止风险发生的控制措施'},
    'detective': {'name': '检测性控制', 'description': '发现已发生风险的控制措施'},
    'corrective': {'name': '纠正性控制', 'description': '纠正风险影响的控制措施'},
    'compensating': {'name': '补偿性控制', 'description': '弥补其他控制不足的措施'},
    'directive': {'name': '指导性控制', 'description': '引导合规行为的控制措施'}
}

AUDIT_TYPES = {
    'internal': {'name': '内部审计', 'description': '组织内部进行的审计'},
    'external': {'name': '外部审计', 'description': '外部机构进行的审计'},
    'special': {'name': '专项审计', 'description': '针对特定事项的审计'},
    'compliance': {'name': '合规审计', 'description': '合规性专项审计'},
    'performance': {'name': '绩效审计', 'description': '绩效评价审计'},
    'financial': {'name': '财务审计', 'description': '财务报表审计'},
    'it': {'name': 'IT审计', 'description': '信息技术审计'},
    'security': {'name': '安全审计', 'description': '安全管理审计'}
}

TRAINING_TOPICS = {
    'law': {'name': '法律法规', 'description': '教育相关法律法规培训'},
    'data_protection': {'name': '数据保护', 'description': '个人信息保护培训'},
    'information_security': {'name': '信息安全', 'description': '网络与信息安全培训'},
    'academic_integrity': {'name': '学术诚信', 'description': '学术规范与诚信培训'},
    'anti_fraud': {'name': '反舞弊', 'description': '反舞弊与廉洁教育'},
    'professional_ethics': {'name': '职业操守', 'description': '职业道德与操守培训'},
    'emergency_management': {'name': '应急管理', 'description': '突发事件应急处理培训'},
    'compliance_awareness': {'name': '合规意识', 'description': '合规文化与意识培训'}
}

WARNING_INDICATORS = {
    'risk': {'name': '风险指标', 'description': '风险监测相关指标'},
    'compliance': {'name': '合规指标', 'description': '合规状况相关指标'},
    'financial': {'name': '财务指标', 'description': '财务运营相关指标'},
    'operational': {'name': '运营指标', 'description': '运营效率相关指标'},
    'security': {'name': '安全指标', 'description': '安全状况相关指标'},
    'performance': {'name': '绩效指标', 'description': '绩效表现相关指标'},
    'public_opinion': {'name': '舆情指标', 'description': '公众舆论相关指标'},
    'quality': {'name': '质量指标', 'description': '教育质量相关指标'}
}

REPORT_TYPES = {
    'compliance': {'name': '合规报告', 'description': '合规状况综合报告'},
    'risk': {'name': '风险报告', 'description': '风险评估与管理报告'},
    'audit': {'name': '审计报告', 'description': '审计结果报告'},
    'rectification': {'name': '整改报告', 'description': '问题整改情况报告'},
    'annual': {'name': '年度报告', 'description': '年度合规管理报告'},
    'special': {'name': '专项报告', 'description': '专项事项报告'},
    'regulatory': {'name': '监管报告', 'description': '向监管机构提交的报告'},
    'internal': {'name': '内部报告', 'description': '内部管理报告'}
}


class EducationComplianceService:
    """教育合规与风险管理服务"""

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
                    CREATE TABLE IF NOT EXISTS compliance_policies (
                        policy_id TEXT PRIMARY KEY,
                        policy_name TEXT NOT NULL,
                        compliance_area TEXT NOT NULL,
                        policy_code TEXT UNIQUE,
                        education_type TEXT,
                        description TEXT,
                        scope TEXT,
                        status TEXT DEFAULT 'active',
                        effective_date TEXT,
                        expiry_date TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS policy_versions (
                        version_id TEXT PRIMARY KEY,
                        policy_id TEXT NOT NULL,
                        version_number TEXT NOT NULL,
                        change_description TEXT,
                        status TEXT DEFAULT 'draft',
                        effective_date TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES compliance_policies(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_checks (
                        check_id TEXT PRIMARY KEY,
                        check_name TEXT NOT NULL,
                        compliance_area TEXT,
                        education_type TEXT,
                        check_scope TEXT,
                        frequency TEXT DEFAULT 'quarterly',
                        description TEXT,
                        status TEXT DEFAULT 'planned',
                        scheduled_date TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS check_results (
                        result_id TEXT PRIMARY KEY,
                        check_id TEXT NOT NULL,
                        check_date TEXT,
                        findings TEXT,
                        issues_found INTEGER DEFAULT 0,
                        severity TEXT,
                        status TEXT DEFAULT 'open',
                        assignee TEXT,
                        due_date TEXT,
                        completed_date TEXT,
                        created_at TEXT,
                        FOREIGN KEY (check_id) REFERENCES compliance_checks(check_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        assessment_name TEXT NOT NULL,
                        education_type TEXT,
                        risk_type TEXT,
                        description TEXT,
                        risk_level TEXT DEFAULT 'medium',
                        risk_score INTEGER DEFAULT 50,
                        probability INTEGER DEFAULT 50,
                        impact INTEGER DEFAULT 50,
                        status TEXT DEFAULT 'pending',
                        assessed_by TEXT,
                        assessed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_registers (
                        register_id TEXT PRIMARY KEY,
                        assessment_id TEXT NOT NULL,
                        risk_category TEXT,
                        risk_description TEXT,
                        risk_level TEXT,
                        risk_score INTEGER,
                        mitigation_status TEXT DEFAULT 'pending',
                        owner TEXT,
                        created_at TEXT,
                        FOREIGN KEY (assessment_id) REFERENCES risk_assessments(assessment_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_mitigation (
                        mitigation_id TEXT PRIMARY KEY,
                        register_id TEXT NOT NULL,
                        strategy TEXT,
                        target_risk_level TEXT,
                        resources_required TEXT,
                        timeline TEXT,
                        status TEXT DEFAULT 'planned',
                        created_by TEXT,
                        created_at TEXT,
                        FOREIGN KEY (register_id) REFERENCES risk_registers(register_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mitigation_actions (
                        action_id TEXT PRIMARY KEY,
                        mitigation_id TEXT NOT NULL,
                        action_description TEXT NOT NULL,
                        responsible_party TEXT,
                        due_date TEXT,
                        status TEXT DEFAULT 'pending',
                        completed_date TEXT,
                        created_at TEXT,
                        FOREIGN KEY (mitigation_id) REFERENCES risk_mitigation(mitigation_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS internal_controls (
                        control_id TEXT PRIMARY KEY,
                        control_name TEXT NOT NULL,
                        control_type TEXT,
                        compliance_area TEXT,
                        education_type TEXT,
                        description TEXT,
                        effectiveness TEXT DEFAULT 'unknown',
                        status TEXT DEFAULT 'active',
                        owner TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS control_testing (
                        test_id TEXT PRIMARY KEY,
                        control_id TEXT NOT NULL,
                        test_type TEXT,
                        test_date TEXT,
                        test_results TEXT,
                        pass_rate REAL,
                        status TEXT DEFAULT 'pending',
                        tester TEXT,
                        created_at TEXT,
                        FOREIGN KEY (control_id) REFERENCES internal_controls(control_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        audit_type TEXT,
                        education_type TEXT,
                        audit_scope TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'planned',
                        auditor TEXT,
                        budget TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_findings (
                        finding_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        finding_description TEXT NOT NULL,
                        severity TEXT DEFAULT 'medium',
                        recommendation TEXT,
                        status TEXT DEFAULT 'open',
                        assignee TEXT,
                        due_date TEXT,
                        completed_date TEXT,
                        created_at TEXT,
                        FOREIGN KEY (plan_id) REFERENCES audit_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_training (
                        training_id TEXT PRIMARY KEY,
                        training_name TEXT NOT NULL,
                        training_topic TEXT,
                        education_type TEXT,
                        target_audience TEXT,
                        duration TEXT,
                        format TEXT DEFAULT 'online',
                        description TEXT,
                        status TEXT DEFAULT 'planned',
                        scheduled_date TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_records (
                        record_id TEXT PRIMARY KEY,
                        training_id TEXT NOT NULL,
                        participant_id INTEGER NOT NULL,
                        participant_name TEXT,
                        completion_status TEXT DEFAULT 'incomplete',
                        score INTEGER,
                        completed_date TEXT,
                        created_at TEXT,
                        FOREIGN KEY (training_id) REFERENCES compliance_training(training_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_alerts (
                        alert_id TEXT PRIMARY KEY,
                        alert_name TEXT NOT NULL,
                        indicator_type TEXT,
                        education_type TEXT,
                        threshold_value REAL,
                        current_value REAL,
                        alert_level TEXT DEFAULT 'warning',
                        status TEXT DEFAULT 'active',
                        trigger_time TEXT,
                        acknowledged_by TEXT,
                        acknowledged_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_history (
                        history_id TEXT PRIMARY KEY,
                        alert_id TEXT NOT NULL,
                        status TEXT,
                        action_taken TEXT,
                        handled_by TEXT,
                        handled_at TEXT,
                        created_at TEXT,
                        FOREIGN KEY (alert_id) REFERENCES risk_alerts(alert_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_reports (
                        report_id TEXT PRIMARY KEY,
                        report_name TEXT NOT NULL,
                        report_type TEXT,
                        education_type TEXT,
                        period_start TEXT,
                        period_end TEXT,
                        status TEXT DEFAULT 'draft',
                        generated_by TEXT,
                        file_path TEXT,
                        generated_at TEXT,
                        approved_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_schedules (
                        schedule_id TEXT PRIMARY KEY,
                        report_type TEXT NOT NULL,
                        education_type TEXT,
                        frequency TEXT DEFAULT 'monthly',
                        next_run_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS whistleblower_reports (
                        report_id TEXT PRIMARY KEY,
                        report_type TEXT,
                        education_type TEXT,
                        description TEXT NOT NULL,
                        evidence TEXT,
                        reporter_identity TEXT DEFAULT 'anonymous',
                        status TEXT DEFAULT 'pending',
                        priority TEXT DEFAULT 'medium',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_handlings (
                        handling_id TEXT PRIMARY KEY,
                        report_id TEXT NOT NULL,
                        action_description TEXT,
                        investigator TEXT,
                        investigation_status TEXT,
                        findings TEXT,
                        resolution TEXT,
                        handled_at TEXT,
                        created_at TEXT,
                        FOREIGN KEY (report_id) REFERENCES whistleblower_reports(report_id)
                    )
                ''')
                conn.commit()
                logger.info('教育合规与风险管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 合规管理 ==========

    def create_policy(self, policy_name: str, compliance_area: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            policy_id = f"pol_{uuid.uuid4().hex[:12]}"
            policy_code = f"POL{datetime.now().strftime('%Y%m')}{uuid.uuid4().hex[:4].upper()}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO compliance_policies (
                            policy_id, policy_name, compliance_area, policy_code,
                            education_type, description, scope, status,
                            effective_date, expiry_date, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
                    ''', (policy_id, policy_name, compliance_area, policy_code,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('scope'), kwargs.get('effective_date'),
                          kwargs.get('expiry_date'), kwargs.get('created_by'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建合规政策: {policy_name} ({policy_id})')
                    return {'success': True, 'policy_id': policy_id, 'policy_code': policy_code}
        except Exception as e:
            logger.error(f'创建合规政策失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_policy_version(self, policy_id: str, change_description: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            version_id = f"ver_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM policy_versions WHERE policy_id = ?', (policy_id,))
                    count = cursor.fetchone()[0]
                    version_number = f"V{count + 1}.0"
                    cursor.execute('''
                        INSERT INTO policy_versions (
                            version_id, policy_id, version_number,
                            change_description, status, effective_date,
                            created_by, created_at
                        ) VALUES (?, ?, ?, ?, 'draft', ?, ?, ?)
                    ''', (version_id, policy_id, version_number, change_description,
                          kwargs.get('effective_date'), kwargs.get('created_by'), now))
                    conn.commit()
                    return {'success': True, 'version_id': version_id, 'version_number': version_number}
        except Exception as e:
            logger.error(f'更新政策版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_policy_version(self, version_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id FROM policy_versions WHERE version_id = ? AND status = ?',
                                 (version_id, 'draft'))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '版本不存在或状态不允许'}
                    policy_id = result[0]
                    cursor.execute('UPDATE policy_versions SET status = ?, effective_date = ?, updated_at = ? WHERE version_id = ?',
                                 ('approved', now[:10], now, version_id))
                    cursor.execute('UPDATE compliance_policies SET updated_at = ? WHERE policy_id = ?',
                                 (now, policy_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'审批政策版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_policies(self, compliance_area: str = None, education_type: str = None,
                       status: str = 'active', page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM compliance_policies WHERE 1=1'
                params = []
                if compliance_area:
                    query += ' AND compliance_area = ?'
                    params.append(compliance_area)
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
                policies = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'policies': policies, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取政策列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 风险管理 ==========

    def create_risk_assessment(self, assessment_name: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"rsa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            probability = kwargs.get('probability', 50)
            impact = kwargs.get('impact', 50)
            risk_score = round((probability * impact) / 10)
            if risk_score <= 20:
                risk_level = 'low'
            elif risk_score <= 40:
                risk_level = 'medium'
            elif risk_score <= 60:
                risk_level = 'high'
            elif risk_score <= 80:
                risk_level = 'critical'
            else:
                risk_level = 'crisis'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO risk_assessments (
                            assessment_id, assessment_name, education_type,
                            risk_type, description, risk_level, risk_score,
                            probability, impact, status, assessed_by,
                            assessed_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (assessment_id, assessment_name, kwargs.get('education_type'),
                          kwargs.get('risk_type'), kwargs.get('description'),
                          risk_level, risk_score, probability, impact,
                          kwargs.get('assessed_by'), now[:10], now))
                    conn.commit()
                    logger.info(f'创建风险评估: {assessment_name} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id, 'risk_level': risk_level, 'risk_score': risk_score}
        except Exception as e:
            logger.error(f'创建风险评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_risk_register(self, assessment_id: str, risk_description: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            register_id = f"rgr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            risk_score = kwargs.get('risk_score', 50)
            if risk_score <= 20:
                risk_level = 'low'
            elif risk_score <= 40:
                risk_level = 'medium'
            elif risk_score <= 60:
                risk_level = 'high'
            elif risk_score <= 80:
                risk_level = 'critical'
            else:
                risk_level = 'crisis'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO risk_registers (
                            register_id, assessment_id, risk_category,
                            risk_description, risk_level, risk_score,
                            mitigation_status, owner, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (register_id, assessment_id, kwargs.get('risk_category'),
                          risk_description, risk_level, risk_score,
                          kwargs.get('owner'), now))
                    conn.commit()
                    return {'success': True, 'register_id': register_id}
        except Exception as e:
            logger.error(f'添加风险登记失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_mitigation(self, register_id: str, strategy: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            mitigation_id = f"mtg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO risk_mitigation (
                            mitigation_id, register_id, strategy,
                            target_risk_level, resources_required, timeline,
                            status, created_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?)
                    ''', (mitigation_id, register_id, strategy,
                          kwargs.get('target_risk_level'),
                          kwargs.get('resources_required'),
                          kwargs.get('timeline'), kwargs.get('created_by'), now))
                    conn.commit()
                    return {'success': True, 'mitigation_id': mitigation_id}
        except Exception as e:
            logger.error(f'创建风险缓解方案失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_mitigation_action(self, mitigation_id: str, action_description: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            action_id = f"mta_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO mitigation_actions (
                            action_id, mitigation_id, action_description,
                            responsible_party, due_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    ''', (action_id, mitigation_id, action_description,
                          kwargs.get('responsible_party'), kwargs.get('due_date'), now))
                    conn.commit()
                    return {'success': True, 'action_id': action_id}
        except Exception as e:
            logger.error(f'添加缓解措施失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 内部控制 ==========

    def create_control(self, control_name: str, control_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            control_id = f"ctl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO internal_controls (
                            control_id, control_name, control_type,
                            compliance_area, education_type, description,
                            effectiveness, status, owner, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'unknown', 'active', ?, ?, ?)
                    ''', (control_id, control_name, control_type,
                          kwargs.get('compliance_area'), kwargs.get('education_type'),
                          kwargs.get('description'), kwargs.get('owner'), now, now))
                    conn.commit()
                    logger.info(f'创建内部控制: {control_name} ({control_id})')
                    return {'success': True, 'control_id': control_id}
        except Exception as e:
            logger.error(f'创建内部控制失败: {e}')
            return {'success': False, 'error': str(e)}

    def perform_control_test(self, control_id: str, test_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            test_id = f"ctt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            pass_rate = kwargs.get('pass_rate', 0)
            status = 'passed' if pass_rate >= 80 else 'failed'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO control_testing (
                            test_id, control_id, test_type, test_date,
                            test_results, pass_rate, status, tester, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (test_id, control_id, test_type, now[:10],
                          kwargs.get('test_results'), pass_rate, status,
                          kwargs.get('tester'), now))
                    cursor.execute('UPDATE internal_controls SET effectiveness = ?, updated_at = ? WHERE control_id = ?',
                                 ('effective' if pass_rate >= 80 else 'ineffective', now, control_id))
                    conn.commit()
                    return {'success': True, 'test_id': test_id, 'status': status}
        except Exception as e:
            logger.error(f'执行控制测试失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_control(self, control_id: str, effectiveness: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE internal_controls SET effectiveness = ?, updated_at = ? WHERE control_id = ?',
                                 (effectiveness, now, control_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '控制不存在'}
        except Exception as e:
            logger.error(f'评价控制有效性失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_controls(self, control_type: str = None, education_type: str = None,
                       status: str = 'active', page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM internal_controls WHERE 1=1'
                params = []
                if control_type:
                    query += ' AND control_type = ?'
                    params.append(control_type)
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
                controls = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'controls': controls, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取控制列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 审计监督 ==========

    def create_audit_plan(self, plan_name: str, audit_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"aud_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO audit_plans (
                            plan_id, plan_name, audit_type, education_type,
                            audit_scope, start_date, end_date, status,
                            auditor, budget, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?, ?, ?, ?)
                    ''', (plan_id, plan_name, audit_type, kwargs.get('education_type'),
                          kwargs.get('audit_scope'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('auditor'),
                          kwargs.get('budget'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建审计计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建审计计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_audit_status(self, plan_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE audit_plans SET status = ?, updated_at = ? WHERE plan_id = ?',
                                 (status, now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '审计计划不存在'}
        except Exception as e:
            logger.error(f'更新审计状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_audit_finding(self, plan_id: str, finding_description: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            finding_id = f"afd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO audit_findings (
                            finding_id, plan_id, finding_description,
                            severity, recommendation, status, assignee,
                            due_date, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?)
                    ''', (finding_id, plan_id, finding_description,
                          kwargs.get('severity', 'medium'),
                          kwargs.get('recommendation'), kwargs.get('assignee'),
                          kwargs.get('due_date'), now))
                    conn.commit()
                    return {'success': True, 'finding_id': finding_id}
        except Exception as e:
            logger.error(f'添加审计发现失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_audit_finding(self, finding_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE audit_findings SET status = ?, completed_date = ? WHERE finding_id = ? AND status = ?',
                                 ('resolved', now[:10], finding_id, 'open'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '发现不存在或已解决'}
        except Exception as e:
            logger.error(f'解决审计发现失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_audit_findings(self, plan_id: str = None, status: str = None,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM audit_findings WHERE 1=1'
                params = []
                if plan_id:
                    query += ' AND plan_id = ?'
                    params.append(plan_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                findings = [dict(f) for f in cursor.fetchall()]
                return {'success': True, 'findings': findings, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取审计发现列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合规培训 ==========

    def create_training(self, training_name: str, training_topic: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"trn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO compliance_training (
                            training_id, training_name, training_topic,
                            education_type, target_audience, duration,
                            format, description, status, scheduled_date,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?, ?, ?)
                    ''', (training_id, training_name, training_topic,
                          kwargs.get('education_type'), kwargs.get('target_audience'),
                          kwargs.get('duration'), kwargs.get('format', 'online'),
                          kwargs.get('description'), kwargs.get('scheduled_date'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建合规培训: {training_name} ({training_id})')
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建合规培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_training(self, training_id: str, participant_id: int,
                         participant_name: str) -> Dict[str, Any]:
        try:
            record_id = f"trr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM compliance_training WHERE training_id = ?', (training_id,))
                    training = cursor.fetchone()
                    if not training:
                        return {'success': False, 'error': '培训不存在'}
                    if training[0] != 'active':
                        return {'success': False, 'error': '培训未开始'}
                    cursor.execute('SELECT record_id FROM training_records WHERE training_id = ? AND participant_id = ?',
                                 (training_id, participant_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该培训'}
                    cursor.execute('''
                        INSERT INTO training_records (
                            record_id, training_id, participant_id,
                            participant_name, completion_status, created_at
                        ) VALUES (?, ?, ?, ?, 'incomplete', ?)
                    ''', (record_id, training_id, participant_id, participant_name, now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'报名培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_completion(self, record_id: str, score: int = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            completion_status = 'completed' if score is not None else 'completed'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE training_records SET completion_status = ?, score = ?, completed_date = ? WHERE record_id = ?',
                                 (completion_status, score, now[:10], record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '培训记录不存在'}
        except Exception as e:
            logger.error(f'记录培训完成失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_training_records(self, training_id: str = None, participant_id: int = None,
                               completion_status: str = None, page: int = 1,
                               page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM training_records WHERE 1=1'
                params = []
                if training_id:
                    query += ' AND training_id = ?'
                    params.append(training_id)
                if participant_id:
                    query += ' AND participant_id = ?'
                    params.append(participant_id)
                if completion_status:
                    query += ' AND completion_status = ?'
                    params.append(completion_status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取培训记录列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 风险预警 ==========

    def create_risk_alert(self, alert_name: str, indicator_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"ral_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            current_value = kwargs.get('current_value', 0)
            threshold_value = kwargs.get('threshold_value', 0)
            if current_value >= threshold_value * 1.5:
                alert_level = 'critical'
            elif current_value >= threshold_value * 1.2:
                alert_level = 'warning'
            else:
                alert_level = 'info'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO risk_alerts (
                            alert_id, alert_name, indicator_type,
                            education_type, threshold_value, current_value,
                            alert_level, status, trigger_time, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (alert_id, alert_name, indicator_type,
                          kwargs.get('education_type'), threshold_value,
                          current_value, alert_level, now, now))
                    conn.commit()
                    logger.info(f'创建风险预警: {alert_name} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id, 'alert_level': alert_level}
        except Exception as e:
            logger.error(f'创建风险预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE risk_alerts SET status = ?, acknowledged_by = ?, acknowledged_at = ? WHERE alert_id = ? AND status = ?',
                                 ('acknowledged', acknowledged_by, now[:10], alert_id, 'active'))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            INSERT INTO alert_history (history_id, alert_id, status, action_taken, handled_by, handled_at, created_at)
                            VALUES (?, ?, ?, 'Acknowledged', ?, ?, ?)
                        ''', (f"ahl_{uuid.uuid4().hex[:12]}", alert_id, 'acknowledged', acknowledged_by, now[:10], now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警不存在或已处理'}
        except Exception as e:
            logger.error(f'确认预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_alert_value(self, alert_id: str, current_value: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT threshold_value FROM risk_alerts WHERE alert_id = ?', (alert_id,))
                    alert = cursor.fetchone()
                    if not alert:
                        return {'success': False, 'error': '预警不存在'}
                    threshold_value = alert[0]
                    if current_value >= threshold_value * 1.5:
                        alert_level = 'critical'
                    elif current_value >= threshold_value * 1.2:
                        alert_level = 'warning'
                    else:
                        alert_level = 'info'
                    cursor.execute('UPDATE risk_alerts SET current_value = ?, alert_level = ?, updated_at = ? WHERE alert_id = ?',
                                 (current_value, alert_level, now, alert_id))
                    conn.commit()
                    return {'success': True, 'alert_level': alert_level}
        except Exception as e:
            logger.error(f'更新预警值失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_alerts(self, indicator_type: str = None, alert_level: str = None,
                     status: str = None, page: int = 1,
                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM risk_alerts WHERE 1=1'
                params = []
                if indicator_type:
                    query += ' AND indicator_type = ?'
                    params.append(indicator_type)
                if alert_level:
                    query += ' AND alert_level = ?'
                    params.append(alert_level)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY trigger_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预警列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合规报告 ==========

    def generate_report(self, report_name: str, report_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO compliance_reports (
                            report_id, report_name, report_type,
                            education_type, period_start, period_end,
                            status, generated_by, file_path,
                            generated_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?)
                    ''', (report_id, report_name, report_type,
                          kwargs.get('education_type'), kwargs.get('period_start'),
                          kwargs.get('period_end'), kwargs.get('generated_by'),
                          kwargs.get('file_path'), now[:10], now))
                    conn.commit()
                    logger.info(f'生成合规报告: {report_name} ({report_id})')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'生成报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE compliance_reports SET status = ?, approved_at = ? WHERE report_id = ? AND status = ?',
                                 ('approved', now[:10], report_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报告不存在或状态不允许'}
        except Exception as e:
            logger.error(f'审批报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE compliance_reports SET status = ?, updated_at = ? WHERE report_id = ? AND status = ?',
                                 ('published', now, report_id, 'approved'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报告未审批或已发布'}
        except Exception as e:
            logger.error(f'发布报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_reports(self, report_type: str = None, education_type: str = None,
                     status: str = None, page: int = 1,
                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM compliance_reports WHERE 1=1'
                params = []
                if report_type:
                    query += ' AND report_type = ?'
                    params.append(report_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY generated_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                reports = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reports': reports, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取报告列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合规检查 ==========

    def create_check(self, check_name: str, **kwargs) -> Dict[str, Any]:
        try:
            check_id = f"chk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO compliance_checks (
                            check_id, check_name, compliance_area,
                            education_type, check_scope, frequency,
                            description, status, scheduled_date,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?, ?, ?)
                    ''', (check_id, check_name, kwargs.get('compliance_area'),
                          kwargs.get('education_type'), kwargs.get('check_scope'),
                          kwargs.get('frequency', 'quarterly'), kwargs.get('description'),
                          kwargs.get('scheduled_date'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建合规检查: {check_name} ({check_id})')
                    return {'success': True, 'check_id': check_id}
        except Exception as e:
            logger.error(f'创建合规检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def perform_check(self, check_id: str, **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"chr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            issues_found = kwargs.get('issues_found', 0)
            severity = kwargs.get('severity', 'low') if issues_found == 0 else kwargs.get('severity', 'medium')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE compliance_checks SET status = ?, updated_at = ? WHERE check_id = ?',
                                 ('completed', now, check_id))
                    cursor.execute('''
                        INSERT INTO check_results (
                            result_id, check_id, check_date, findings,
                            issues_found, severity, status, assignee,
                            due_date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
                    ''', (result_id, check_id, now[:10], kwargs.get('findings'),
                          issues_found, severity, kwargs.get('assignee'),
                          kwargs.get('due_date'), now))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'执行合规检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_check_issue(self, result_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE check_results SET status = ?, completed_date = ? WHERE result_id = ? AND status = ?',
                                 ('resolved', now[:10], result_id, 'open'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '检查结果不存在或已解决'}
        except Exception as e:
            logger.error(f'解决检查问题失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_check_results(self, check_id: str = None, severity: str = None,
                            status: str = None, page: int = 1,
                            page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM check_results WHERE 1=1'
                params = []
                if check_id:
                    query += ' AND check_id = ?'
                    params.append(check_id)
                if severity:
                    query += ' AND severity = ?'
                    params.append(severity)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY check_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取检查结果列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 举报管理 ==========

    def submit_whistleblower_report(self, description: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"wbl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO whistleblower_reports (
                            report_id, report_type, education_type,
                            description, evidence, reporter_identity,
                            status, priority, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (report_id, kwargs.get('report_type'), kwargs.get('education_type'),
                          description, kwargs.get('evidence'),
                          kwargs.get('reporter_identity', 'anonymous'),
                          kwargs.get('priority', 'medium'), now))
                    conn.commit()
                    logger.info(f'提交举报: {report_id}')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'提交举报失败: {e}')
            return {'success': False, 'error': str(e)}

    def investigate_report(self, report_id: str, **kwargs) -> Dict[str, Any]:
        try:
            handling_id = f"whh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE whistleblower_reports SET status = ? WHERE report_id = ?',
                                 ('investigating', report_id))
                    cursor.execute('''
                        INSERT INTO report_handlings (
                            handling_id, report_id, action_description,
                            investigator, investigation_status, created_at
                        ) VALUES (?, ?, ?, ?, 'in_progress', ?)
                    ''', (handling_id, report_id, kwargs.get('action_description'),
                          kwargs.get('investigator'), now))
                    conn.commit()
                    return {'success': True, 'handling_id': handling_id}
        except Exception as e:
            logger.error(f'调查举报失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_report(self, report_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE whistleblower_reports SET status = ? WHERE report_id = ?',
                                 ('resolved', report_id))
                    cursor.execute('''
                        INSERT INTO report_handlings (
                            handling_id, report_id, action_description,
                            investigator, investigation_status, findings,
                            resolution, handled_at, created_at
                        ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?)
                    ''', (f"whh_{uuid.uuid4().hex[:12]}", report_id, kwargs.get('action_description'),
                          kwargs.get('investigator'), kwargs.get('findings'),
                          kwargs.get('resolution'), now[:10], now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'解决举报失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_compliance_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = f" WHERE education_type = '{education_type}'" if education_type else ""
                
                cursor.execute(f'SELECT COUNT(*) FROM compliance_policies{where_clause}')
                policy_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM risk_assessments{where_clause}')
                assessment_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM audit_findings WHERE status = "open"{where_clause}')
                open_findings = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM compliance_training{where_clause}')
                training_count = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM risk_alerts WHERE status = "active"{where_clause}')
                active_alerts = cursor.fetchone()[0]
                
                cursor.execute(f'SELECT COUNT(*) FROM whistleblower_reports WHERE status = "pending"{where_clause}')
                pending_reports = cursor.fetchone()[0]
                
                return {
                    'success': True,
                    'stats': {
                        'total_policies': policy_count,
                        'total_assessments': assessment_count,
                        'open_findings': open_findings,
                        'total_trainings': training_count,
                        'active_alerts': active_alerts,
                        'pending_reports': pending_reports,
                        'education_type': education_type or 'all'
                    }
                }
        except Exception as e:
            logger.error(f'获取合规统计失败: {e}')
            return {'success': False, 'error': str(e)}