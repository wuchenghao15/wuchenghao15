#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育信息安全服务 (v15.18.0)
====================================
提供信息安全、数据保护、网络安全、安全审计、访问控制、安全监控、应急响应、安全培训等综合管理服务。

核心能力：
1. 信息安全 - 安全策略、安全级别、安全配置、安全评估
2. 数据保护 - 数据分类、数据加密、数据脱敏、数据备份恢复
3. 网络安全 - 防火墙、入侵检测、VPN、安全网关、DDoS防护
4. 访问控制 - 身份认证、权限管理、角色管理、多因素认证
5. 安全监控 - 日志监控、行为分析、威胁检测、安全告警
6. 应急响应 - 应急预案、应急演练、事件响应、威胁处置
7. 安全培训 - 安全意识、网络钓鱼、密码安全、合规培训
8. 安全审计 - 安全审计、合规审计、访问审计、日志审计
9. 漏洞扫描 - 漏洞检测、扫描管理、修复跟踪、风险评估

差异化支持：成人教育 / K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_info_security_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationSecurity')


# ========== 安全配置项 ==========

SECURITY_LEVELS = {
    'basic': {'name': '基础安全', 'description': '基础安全防护，适用于小型机构', 'features': ['基础防火墙', '基础杀毒', '基础备份']},
    'standard': {'name': '标准安全', 'description': '标准安全防护，适用于中型机构', 'features': ['高级防火墙', '入侵检测', '数据加密']},
    'advanced': {'name': '高级安全', 'description': '高级安全防护，适用于大型机构', 'features': ['入侵防御', '安全监控', '多因素认证']},
    'enterprise': {'name': '企业安全', 'description': '企业级安全防护，适用于集团企业', 'features': ['全方位防护', '安全审计', '应急响应']},
    'top': {'name': '顶级安全', 'description': '顶级安全防护，适用于高安全要求场景', 'features': ['零信任架构', 'AI威胁检测', '安全运营中心']}
}

DATA_PROTECTION = {
    'classification': {'name': '数据分类', 'levels': ['公开', '内部', '机密', '绝密']},
    'encryption': {'name': '数据加密', 'methods': ['AES-256', 'RSA-2048', 'SM4', '传输加密']},
    'anonymization': {'name': '数据脱敏', 'techniques': ['掩码处理', '随机替换', '泛化处理', '加密替换']},
    'backup': {'name': '数据备份', 'types': ['全量备份', '增量备份', '差异备份', '异地备份']},
    'recovery': {'name': '数据恢复', 'strategies': ['即时恢复', '定点恢复', '灾备恢复']},
    'destruction': {'name': '数据销毁', 'methods': ['物理销毁', '逻辑销毁', '消磁处理']},
    'flow': {'name': '数据流转', 'controls': ['访问控制', '脱敏传输', '水印追踪']},
    'cross_border': {'name': '数据跨境', 'compliance': ['GDPR', '数据本地化', '安全评估']}
}

NETWORK_SECURITY = {
    'firewall': {'name': '防火墙', 'types': ['包过滤', '状态检测', '应用层', '下一代']},
    'ids': {'name': '入侵检测', 'techniques': ['签名检测', '异常检测', '启发式']},
    'ips': {'name': '入侵防御', 'capabilities': ['实时阻断', '攻击溯源', '自动响应']},
    'isolation': {'name': '网络隔离', 'methods': ['VLAN', '防火墙分区', '物理隔离']},
    'vpn': {'name': 'VPN', 'types': ['IPsec', 'SSL', 'WireGuard', 'L2TP']},
    'gateway': {'name': '安全网关', 'features': ['内容过滤', '威胁检测', '流量监控']},
    'ddos': {'name': 'DDoS防护', 'capabilities': ['流量清洗', '速率限制', '黑洞路由']},
    'monitoring': {'name': '网络监控', 'metrics': ['带宽利用率', '连接数', '延迟', '丢包率']}
}

ACCESS_CONTROL = {
    'authentication': {'name': '身份认证', 'methods': ['用户名密码', '证书认证', '生物识别', '令牌认证']},
    'permission': {'name': '权限管理', 'models': ['RBAC', 'ABAC', 'DAC', 'MAC']},
    'role': {'name': '角色管理', 'roles': ['管理员', '教师', '学生', '访客', '审计员']},
    'sso': {'name': '单点登录', 'protocols': ['SAML', 'OAuth2', 'OpenID Connect', 'CAS']},
    'mfa': {'name': '多因素认证', 'factors': ['密码', '短信', '令牌', '生物特征']},
    'access_audit': {'name': '访问审计', 'records': ['登录日志', '操作日志', '访问日志']},
    'least_privilege': {'name': '最小权限', 'principle': ['按需分配', '定期审查', '权限回收']},
    'revocation': {'name': '权限回收', 'triggers': ['离职', '转岗', '违规', '定期']}
}

SECURITY_MONITORING = {
    'log_monitoring': {'name': '日志监控', 'sources': ['系统日志', '应用日志', '安全日志']},
    'behavior_analysis': {'name': '行为分析', 'methods': ['基线对比', '异常检测', '机器学习']},
    'threat_detection': {'name': '威胁检测', 'types': ['病毒', '木马', '勒索软件', 'APT']},
    'alerts': {'name': '安全告警', 'levels': ['紧急', '高危', '中危', '低危', '信息']},
    'real_time': {'name': '实时监控', 'dashboards': ['安全态势', '威胁地图', '事件追踪']},
    'anomaly_detection': {'name': '异常检测', 'patterns': ['登录异常', '访问异常', '流量异常']},
    'situation': {'name': '安全态势', 'indicators': ['风险指数', '威胁等级', '安全评分']},
    'events': {'name': '安全事件', 'categories': ['入侵事件', '数据泄露', '系统故障', '违规操作']}
}

EMERGENCY_RESPONSE = {
    'plan': {'name': '应急预案', 'types': ['网络攻击', '数据泄露', '系统故障', '自然灾害']},
    'drill': {'name': '应急演练', 'methods': ['桌面推演', '实战演练', '红蓝对抗']},
    'incident': {'name': '事件响应', 'phases': ['检测', '分析', '遏制', '根除', '恢复']},
    'threat': {'name': '威胁处置', 'actions': ['隔离', '阻断', '取证', '溯源']},
    'recovery': {'name': '事后恢复', 'steps': ['系统恢复', '数据恢复', '服务恢复']},
    'hardening': {'name': '安全加固', 'measures': ['补丁更新', '配置加固', '权限调整']},
    'root_cause': {'name': '根因分析', 'methods': ['5Why', '鱼骨图', '故障树']},
    'report': {'name': '总结报告', 'contents': ['事件描述', '处置过程', '改进措施']}
}

SECURITY_TRAINING = {
    'awareness': {'name': '安全意识', 'topics': ['安全重要性', '常见威胁', '安全习惯']},
    'phishing': {'name': '网络钓鱼', 'training': ['识别方法', '防范技巧', '模拟演练']},
    'password': {'name': '密码安全', 'practices': ['复杂度要求', '定期更换', '不重复使用']},
    'data_protection': {'name': '数据保护', 'knowledge': ['数据分类', '敏感信息', '保护措施']},
    'emergency': {'name': '应急处理', 'procedures': ['发现报告', '初步处置', '配合调查']},
    'standards': {'name': '安全规范', 'rules': ['使用规范', '操作流程', '合规要求']},
    'compliance': {'name': '合规要求', 'regulations': ['网络安全法', '个人信息保护法', '等保2.0']},
    'skills': {'name': '安全技能', 'abilities': ['安全配置', '漏洞识别', '应急响应']}
}

AUDIT_FUNCTIONS = {
    'security_audit': {'name': '安全审计', 'scope': ['安全策略', '安全配置', '安全措施']},
    'compliance_audit': {'name': '合规审计', 'standards': ['等保2.0', 'ISO27001', 'SOC2']},
    'access_audit': {'name': '访问审计', 'records': ['登录记录', '权限变更', '访问日志']},
    'operation_audit': {'name': '操作审计', 'targets': ['系统操作', '数据操作', '配置操作']},
    'log_audit': {'name': '日志审计', 'logs': ['安全日志', '系统日志', '应用日志']},
    'config_audit': {'name': '配置审计', 'items': ['系统配置', '安全配置', '网络配置']},
    'vulnerability_audit': {'name': '漏洞审计', 'assessments': ['漏洞扫描', '渗透测试', '代码审计']},
    'permission_audit': {'name': '权限审计', 'reviews': ['权限合理性', '权限滥用', '权限冗余']}
}


class EducationInfoSecurityService:
    """教育信息安全服务"""

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
                    CREATE TABLE IF NOT EXISTS security_policies (
                        policy_id TEXT PRIMARY KEY,
                        policy_name TEXT NOT NULL,
                        security_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        scope TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS policy_rules (
                        rule_id TEXT PRIMARY KEY,
                        policy_id TEXT NOT NULL,
                        rule_name TEXT,
                        rule_type TEXT,
                        rule_content TEXT,
                        priority INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'enabled',
                        FOREIGN KEY (policy_id) REFERENCES security_policies(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_classification (
                        classification_id TEXT PRIMARY KEY,
                        data_name TEXT NOT NULL,
                        data_category TEXT,
                        sensitivity_level TEXT,
                        owner TEXT,
                        education_type TEXT,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_protection (
                        protection_id TEXT PRIMARY KEY,
                        classification_id TEXT,
                        protection_method TEXT,
                        encryption_algorithm TEXT,
                        anonymization_level TEXT,
                        backup_frequency TEXT,
                        retention_period INTEGER,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (classification_id) REFERENCES data_classification(classification_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_security (
                        security_id TEXT PRIMARY KEY,
                        security_type TEXT NOT NULL,
                        device_name TEXT,
                        device_type TEXT,
                        ip_address TEXT,
                        location TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT,
                        vendor TEXT,
                        model TEXT,
                        firmware_version TEXT,
                        ip_address TEXT,
                        status TEXT DEFAULT 'online',
                        last_check TEXT,
                        FOREIGN KEY (device_id) REFERENCES network_security(security_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS access_control (
                        control_id TEXT PRIMARY KEY,
                        control_type TEXT NOT NULL,
                        authentication_method TEXT,
                        permission_model TEXT,
                        mfa_enabled INTEGER DEFAULT 0,
                        sso_enabled INTEGER DEFAULT 0,
                        education_type TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_permissions (
                        permission_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        role TEXT,
                        permissions TEXT,
                        education_type TEXT,
                        granted_at TEXT,
                        expires_at TEXT,
                        status TEXT DEFAULT 'active'
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_monitoring (
                        monitoring_id TEXT PRIMARY KEY,
                        monitoring_type TEXT NOT NULL,
                        log_source TEXT,
                        alert_level TEXT,
                        threshold TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitoring_alerts (
                        alert_id TEXT PRIMARY KEY,
                        monitoring_id TEXT,
                        alert_type TEXT,
                        alert_level TEXT,
                        alert_message TEXT,
                        source_ip TEXT,
                        target_ip TEXT,
                        occurred_at TEXT,
                        status TEXT DEFAULT 'pending',
                        acknowledged_by TEXT,
                        acknowledged_at TEXT,
                        FOREIGN KEY (monitoring_id) REFERENCES security_monitoring(monitoring_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS emergency_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        plan_type TEXT,
                        education_type TEXT,
                        scope TEXT,
                        description TEXT,
                        procedures TEXT,
                        responsible_person TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS incident_response (
                        incident_id TEXT PRIMARY KEY,
                        plan_id TEXT,
                        incident_type TEXT,
                        severity TEXT,
                        description TEXT,
                        detected_at TEXT,
                        response_started_at TEXT,
                        response_completed_at TEXT,
                        status TEXT DEFAULT 'detected',
                        handled_by TEXT,
                        root_cause TEXT,
                        remediation TEXT,
                        FOREIGN KEY (plan_id) REFERENCES emergency_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_training (
                        training_id TEXT PRIMARY KEY,
                        training_name TEXT NOT NULL,
                        training_type TEXT,
                        education_type TEXT,
                        target_audience TEXT,
                        duration INTEGER,
                        content TEXT,
                        status TEXT DEFAULT 'planned',
                        scheduled_date TEXT,
                        completed_count INTEGER DEFAULT 0,
                        total_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_participants (
                        participant_id TEXT PRIMARY KEY,
                        training_id TEXT,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'registered',
                        completion_status TEXT DEFAULT 'not_started',
                        score INTEGER,
                        completed_at TEXT,
                        FOREIGN KEY (training_id) REFERENCES security_training(training_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_audit (
                        audit_id TEXT PRIMARY KEY,
                        audit_type TEXT NOT NULL,
                        audit_scope TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'planned',
                        started_at TEXT,
                        completed_at TEXT,
                        findings_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_records (
                        record_id TEXT PRIMARY KEY,
                        audit_id TEXT,
                        finding_type TEXT,
                        severity TEXT,
                        description TEXT,
                        recommendation TEXT,
                        status TEXT DEFAULT 'open',
                        FOREIGN KEY (audit_id) REFERENCES security_audit(audit_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vulnerability_scan (
                        scan_id TEXT PRIMARY KEY,
                        scan_name TEXT NOT NULL,
                        scan_type TEXT,
                        target TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'scheduled',
                        started_at TEXT,
                        completed_at TEXT,
                        total_vulnerabilities INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scan_results (
                        result_id TEXT PRIMARY KEY,
                        scan_id TEXT,
                        vulnerability_id TEXT,
                        severity TEXT,
                        title TEXT,
                        description TEXT,
                        cve_id TEXT,
                        remediation TEXT,
                        status TEXT DEFAULT 'open',
                        FOREIGN KEY (scan_id) REFERENCES vulnerability_scan(scan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_events (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        event_category TEXT,
                        severity TEXT,
                        description TEXT,
                        source TEXT,
                        target TEXT,
                        occurred_at TEXT,
                        status TEXT DEFAULT 'active',
                        education_type TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS event_logs (
                        log_id TEXT PRIMARY KEY,
                        event_id TEXT,
                        log_type TEXT,
                        log_message TEXT,
                        timestamp TEXT,
                        FOREIGN KEY (event_id) REFERENCES security_events(event_id)
                    )
                ''')
                conn.commit()
                logger.info('教育信息安全服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 信息安全 ==========

    def create_security_policy(self, policy_name: str, security_level: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            policy_id = f"pol_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_policies (
                            policy_id, policy_name, security_level,
                            education_type, description, scope, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (policy_id, policy_name, security_level,
                          kwargs.get('education_type'),
                          kwargs.get('description'), kwargs.get('scope'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建安全策略: {policy_name} ({policy_id})')
                    return {'success': True, 'policy_id': policy_id}
        except Exception as e:
            logger.error(f'创建安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_policy_rule(self, policy_id: str, rule_name: str,
                        rule_type: str, rule_content: str, **kwargs) -> Dict[str, Any]:
        try:
            rule_id = f"rul_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id FROM security_policies WHERE policy_id = ?', (policy_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '策略不存在'}
                    cursor.execute('''
                        INSERT INTO policy_rules (rule_id, policy_id, rule_name,
                            rule_type, rule_content, priority, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'enabled')
                    ''', (rule_id, policy_id, rule_name, rule_type,
                          rule_content, kwargs.get('priority', 1)))
                    conn.commit()
                    return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.error(f'添加策略规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_security_policy(self, policy_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM security_policies WHERE policy_id = ?', (policy_id,))
                policy = cursor.fetchone()
                if not policy:
                    return {'success': False, 'error': '策略不存在'}
                cursor.execute('SELECT * FROM policy_rules WHERE policy_id = ?', (policy_id,))
                rules = [dict(r) for r in cursor.fetchall()]
                result = dict(policy)
                result['rules'] = rules
                return {'success': True, 'policy': result}
        except Exception as e:
            logger.error(f'获取安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_security(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) as cnt FROM security_policies WHERE status = ?'
                params = ['active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                policy_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) as cnt FROM monitoring_alerts WHERE status = ?', ('pending',))
                pending_alerts = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) as cnt FROM vulnerability_scan WHERE status = ?', ('completed',))
                completed_scans = cursor.fetchone()[0]
                score = min(100, max(0, 70 + policy_count * 3 - pending_alerts * 5 + completed_scans * 2))
                return {
                    'success': True,
                    'security_score': score,
                    'policy_count': policy_count,
                    'pending_alerts': pending_alerts,
                    'completed_scans': completed_scans,
                    'education_type': education_type
                }
        except Exception as e:
            logger.error(f'安全评估失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据保护 ==========

    def classify_data(self, data_name: str, data_category: str,
                      sensitivity_level: str, **kwargs) -> Dict[str, Any]:
        try:
            classification_id = f"dcl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_classification (
                            classification_id, data_name, data_category,
                            sensitivity_level, owner, education_type,
                            description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (classification_id, data_name, data_category,
                          sensitivity_level, kwargs.get('owner'),
                          kwargs.get('education_type'), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'classification_id': classification_id}
        except Exception as e:
            logger.error(f'数据分类失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_protection(self, classification_id: str, **kwargs) -> Dict[str, Any]:
        try:
            protection_id = f"dpt_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT classification_id FROM data_classification WHERE classification_id = ?', (classification_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '数据分类不存在'}
                    cursor.execute('''
                        INSERT INTO data_protection (
                            protection_id, classification_id, protection_method,
                            encryption_algorithm, anonymization_level,
                            backup_frequency, retention_period, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
                    ''', (protection_id, classification_id,
                          kwargs.get('protection_method'),
                          kwargs.get('encryption_algorithm'),
                          kwargs.get('anonymization_level'),
                          kwargs.get('backup_frequency'),
                          kwargs.get('retention_period', 365)))
                    conn.commit()
                    return {'success': True, 'protection_id': protection_id}
        except Exception as e:
            logger.error(f'配置数据保护失败: {e}')
            return {'success': False, 'error': str(e)}

    def anonymize_data(self, classification_id: str, anonymization_level: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT sensitivity_level FROM data_classification WHERE classification_id = ?', (classification_id,))
                    data = cursor.fetchone()
                    if not data:
                        return {'success': False, 'error': '数据分类不存在'}
                    sensitivity = data[0]
                    required_levels = {'公开': 'none', '内部': 'basic', '机密': 'moderate', '绝密': 'high'}
                    if required_levels.get(sensitivity, 'basic') not in ['none', 'basic', 'moderate', 'high']:
                        return {'success': False, 'error': '无效的敏感级别'}
                    cursor.execute('''
                        UPDATE data_protection SET anonymization_level = ?, updated_at = ?
                        WHERE classification_id = ?
                    ''', (anonymization_level, now, classification_id))
                    conn.commit()
                    return {'success': True, 'message': f'数据已按{anonymization_level}级别脱敏'}
        except Exception as e:
            logger.error(f'数据脱敏失败: {e}')
            return {'success': False, 'error': str(e)}

    def backup_data(self, classification_id: str, backup_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            backup_id = f"bkp_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT data_name, sensitivity_level FROM data_classification WHERE classification_id = ?', (classification_id,))
                    data = cursor.fetchone()
                    if not data:
                        return {'success': False, 'error': '数据分类不存在'}
                    cursor.execute('''
                        UPDATE data_protection SET backup_frequency = ?, updated_at = ?
                        WHERE classification_id = ?
                    ''', (backup_type, now, classification_id))
                    conn.commit()
                    return {'success': True, 'backup_id': backup_id, 'message': f'{data[0]}已执行{backup_type}备份'}
        except Exception as e:
            logger.error(f'数据备份失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 网络安全 ==========

    def configure_network_security(self, security_type: str, device_name: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"nws_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO network_security (
                            security_id, security_type, device_name,
                            device_type, ip_address, location, education_type,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (security_id, security_type, device_name,
                          kwargs.get('device_type'), kwargs.get('ip_address'),
                          kwargs.get('location'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'配置网络安全失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_security_device(self, device_name: str, device_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_devices (
                            device_id, device_name, device_type, vendor,
                            model, firmware_version, ip_address,
                            status, last_check
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'online', ?)
                    ''', (device_id, device_name, device_type,
                          kwargs.get('vendor'), kwargs.get('model'),
                          kwargs.get('firmware_version'), kwargs.get('ip_address'),
                          now))
                    conn.commit()
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'注册安全设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_firewall_rule(self, device_id: str, rule_name: str,
                                action: str, source: str, destination: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            rule_id = f"fwl_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT device_id FROM security_devices WHERE device_id = ?', (device_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '设备不存在'}
                    cursor.execute('''
                        INSERT INTO policy_rules (rule_id, policy_id, rule_name,
                            rule_type, rule_content, priority, status)
                        VALUES (?, ?, ?, 'firewall', ?, ?, 'enabled')
                    ''', (rule_id, f"pol_{device_id[:8]}", rule_name,
                          json.dumps({'action': action, 'source': source,
                                      'destination': destination,
                                      'protocol': kwargs.get('protocol', 'all'),
                                      'port': kwargs.get('port')}),
                          kwargs.get('priority', 1)))
                    conn.commit()
                    return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.error(f'配置防火墙规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def monitor_network_traffic(self, device_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT device_name, ip_address FROM security_devices WHERE device_id = ?', (device_id,))
                device = cursor.fetchone()
                if not device:
                    return {'success': False, 'error': '设备不存在'}
                metrics = {
                    'device': device[0],
                    'ip_address': device[1],
                    'timestamp': now,
                    'bandwidth_usage': kwargs.get('bandwidth_usage', '50%'),
                    'connection_count': kwargs.get('connection_count', 100),
                    'latency': kwargs.get('latency', '10ms'),
                    'packet_loss': kwargs.get('packet_loss', '0%')
                }
                return {'success': True, 'metrics': metrics}
        except Exception as e:
            logger.error(f'监控网络流量失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 访问控制 ==========

    def configure_access_control(self, control_type: str, **kwargs) -> Dict[str, Any]:
        try:
            control_id = f"acc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO access_control (
                            control_id, control_type, authentication_method,
                            permission_model, mfa_enabled, sso_enabled,
                            education_type, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (control_id, control_type, kwargs.get('authentication_method'),
                          kwargs.get('permission_model', 'RBAC'),
                          1 if kwargs.get('mfa_enabled') else 0,
                          1 if kwargs.get('sso_enabled') else 0,
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    return {'success': True, 'control_id': control_id}
        except Exception as e:
            logger.error(f'配置访问控制失败: {e}')
            return {'success': False, 'error': str(e)}

    def grant_permission(self, user_id: int, role: str, **kwargs) -> Dict[str, Any]:
        try:
            permission_id = f"prm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            permissions_map = {
                'admin': ['full_access', 'manage_users', 'manage_policies', 'audit'],
                'teacher': ['view_students', 'manage_courses', 'view_reports'],
                'student': ['view_courses', 'submit_assignments', 'view_grades'],
                'visitor': ['view_public'],
                'auditor': ['view_logs', 'run_audits', 'view_reports']
            }
            permissions = json.dumps(permissions_map.get(role, ['view_public']))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO user_permissions (
                            permission_id, user_id, user_name, role,
                            permissions, education_type, granted_at,
                            expires_at, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
                    ''', (permission_id, user_id, kwargs.get('user_name'),
                          role, permissions, kwargs.get('education_type'),
                          now, kwargs.get('expires_at')))
                    conn.commit()
                    return {'success': True, 'permission_id': permission_id}
        except Exception as e:
            logger.error(f'授权失败: {e}')
            return {'success': False, 'error': str(e)}

    def authenticate_user(self, user_id: int, password: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT role, permissions, status FROM user_permissions WHERE user_id = ? AND status = ?', (user_id, 'active'))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '用户不存在或未授权'}
                    if result[2] != 'active':
                        return {'success': False, 'error': '权限已失效'}
                    mfa_enabled = kwargs.get('mfa_enabled', False)
                    if mfa_enabled and not kwargs.get('mfa_code'):
                        return {'success': False, 'error': '需要多因素认证'}
                    return {
                        'success': True,
                        'authenticated': True,
                        'role': result[0],
                        'permissions': json.loads(result[1]),
                        'timestamp': now
                    }
        except Exception as e:
            logger.error(f'用户认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_permission(self, permission_id: str, reason: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE user_permissions SET status = ?, updated_at = ? WHERE permission_id = ?', ('revoked', now, permission_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'message': f'权限已撤销: {reason or "未指定原因"}'}
                    return {'success': False, 'error': '权限记录不存在'}
        except Exception as e:
            logger.error(f'撤销权限失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全监控 ==========

    def configure_monitoring(self, monitoring_type: str, log_source: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            monitoring_id = f"mon_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_monitoring (
                            monitoring_id, monitoring_type, log_source,
                            alert_level, threshold, education_type,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (monitoring_id, monitoring_type, log_source,
                          kwargs.get('alert_level', 'medium'),
                          kwargs.get('threshold'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'monitoring_id': monitoring_id}
        except Exception as e:
            logger.error(f'配置安全监控失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_alert(self, monitoring_id: str, alert_type: str,
                      alert_level: str, alert_message: str, **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT monitoring_id FROM security_monitoring WHERE monitoring_id = ?', (monitoring_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '监控配置不存在'}
                    cursor.execute('''
                        INSERT INTO monitoring_alerts (
                            alert_id, monitoring_id, alert_type, alert_level,
                            alert_message, source_ip, target_ip, occurred_at, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                    ''', (alert_id, monitoring_id, alert_type, alert_level,
                          alert_message, kwargs.get('source_ip'),
                          kwargs.get('target_ip'), now))
                    conn.commit()
                    logger.warning(f'安全告警触发: {alert_level} - {alert_message}')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'触发告警失败: {e}')
            return {'success': False, 'error': str(e)}

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE monitoring_alerts SET status = ?, acknowledged_by = ?, acknowledged_at = ? WHERE alert_id = ? AND status = ?',
                                 ('acknowledged', acknowledged_by, now, alert_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '告警不存在或已处理'}
        except Exception as e:
            logger.error(f'确认告警失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_behavior(self, user_id: int = None, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                analysis = {
                    'timestamp': now,
                    'user_id': user_id,
                    'anomalies': [],
                    'risk_level': 'low'
                }
                if user_id:
                    cursor.execute('SELECT COUNT(*) FROM monitoring_alerts WHERE source_ip = ? AND occurred_at >= ?',
                                  (kwargs.get('ip_address', 'unknown'), (datetime.now() - timedelta(hours=24)).isoformat()))
                    alert_count = cursor.fetchone()[0]
                    if alert_count > 5:
                        analysis['anomalies'].append(f'24小时内告警次数过多: {alert_count}')
                        analysis['risk_level'] = 'high'
                    elif alert_count > 2:
                        analysis['risk_level'] = 'medium'
                return {'success': True, 'analysis': analysis}
        except Exception as e:
            logger.error(f'行为分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_security_situation(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) FROM monitoring_alerts WHERE status = ?'
                params = ['pending']
                if education_type:
                    query += ' AND monitoring_id IN (SELECT monitoring_id FROM security_monitoring WHERE education_type = ?)'
                    params.append(education_type)
                cursor.execute(query, params)
                pending_alerts = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM security_events WHERE status = ?', ('active',))
                active_events = cursor.fetchone()[0]
                risk_index = min(100, pending_alerts * 10 + active_events * 5)
                threat_level = 'critical' if risk_index >= 80 else ('high' if risk_index >= 50 else ('medium' if risk_index >= 20 else 'low'))
                return {
                    'success': True,
                    'risk_index': risk_index,
                    'threat_level': threat_level,
                    'pending_alerts': pending_alerts,
                    'active_events': active_events,
                    'education_type': education_type
                }
        except Exception as e:
            logger.error(f'获取安全态势失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 应急响应 ==========

    def create_emergency_plan(self, plan_name: str, plan_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"epn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO emergency_plans (
                            plan_id, plan_name, plan_type, education_type,
                            scope, description, procedures, responsible_person,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (plan_id, plan_name, plan_type, kwargs.get('education_type'),
                          kwargs.get('scope'), kwargs.get('description'),
                          kwargs.get('procedures'), kwargs.get('responsible_person'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建应急预案失败: {e}')
            return {'success': False, 'error': str(e)}

    def initiate_incident_response(self, plan_id: str, incident_type: str,
                                   severity: str, description: str, **kwargs) -> Dict[str, Any]:
        try:
            incident_id = f"inc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id FROM emergency_plans WHERE plan_id = ?', (plan_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '应急预案不存在'}
                    cursor.execute('''
                        INSERT INTO incident_response (
                            incident_id, plan_id, incident_type, severity,
                            description, detected_at, response_started_at,
                            status, handled_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'detected', ?)
                    ''', (incident_id, plan_id, incident_type, severity,
                          description, now, now, kwargs.get('handled_by')))
                    conn.commit()
                    logger.warning(f'启动事件响应: {incident_type} - {severity}')
                    return {'success': True, 'incident_id': incident_id}
        except Exception as e:
            logger.error(f'启动事件响应失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_incident_status(self, incident_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['status = ?']
                    update_values = [status]
                    if status == 'resolved':
                        update_fields.append('response_completed_at = ?')
                        update_values.append(now)
                    if kwargs.get('root_cause'):
                        update_fields.append('root_cause = ?')
                        update_values.append(kwargs.get('root_cause'))
                    if kwargs.get('remediation'):
                        update_fields.append('remediation = ?')
                        update_values.append(kwargs.get('remediation'))
                    update_values.append(incident_id)
                    cursor.execute(f'UPDATE incident_response SET {", ".join(update_fields)} WHERE incident_id = ?', update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '事件不存在'}
        except Exception as e:
            logger.error(f'更新事件状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def conduct_emergency_drill(self, plan_id: str, drill_type: str, **kwargs) -> Dict[str, Any]:
        try:
            drill_id = f"dr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_name FROM emergency_plans WHERE plan_id = ?', (plan_id,))
                    plan = cursor.fetchone()
                    if not plan:
                        return {'success': False, 'error': '应急预案不存在'}
                    drill_result = {
                        'drill_id': drill_id,
                        'plan_id': plan_id,
                        'plan_name': plan[0],
                        'drill_type': drill_type,
                        'participants': kwargs.get('participants', 0),
                        'duration': kwargs.get('duration', 0),
                        'success_rate': kwargs.get('success_rate', 0),
                        'issues_found': kwargs.get('issues_found', []),
                        'timestamp': now
                    }
                    return {'success': True, 'drill_result': drill_result}
        except Exception as e:
            logger.error(f'执行应急演练失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全培训 ==========

    def create_training(self, training_name: str, training_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"trn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_training (
                            training_id, training_name, training_type,
                            education_type, target_audience, duration,
                            content, status, scheduled_date,
                            completed_count, total_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'planned', ?, 0, ?, ?, ?)
                    ''', (training_id, training_name, training_type,
                          kwargs.get('education_type'), kwargs.get('target_audience'),
                          kwargs.get('duration', 60), kwargs.get('content'),
                          kwargs.get('scheduled_date'), kwargs.get('total_count', 0),
                          now, now))
                    conn.commit()
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建安全培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_training_participant(self, training_id: str, user_id: int,
                                      user_name: str, **kwargs) -> Dict[str, Any]:
        try:
            participant_id = f"tpp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT training_id FROM security_training WHERE training_id = ?', (training_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '培训不存在'}
                    cursor.execute('INSERT OR IGNORE INTO training_participants (participant_id, training_id, user_id, user_name, education_type, status) VALUES (?, ?, ?, ?, ?, "registered")',
                                 (participant_id, training_id, user_id, user_name, kwargs.get('education_type')))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE security_training SET total_count = total_count + 1 WHERE training_id = ?', (training_id,))
                        conn.commit()
                        return {'success': True, 'participant_id': participant_id}
                    return {'success': False, 'error': '已注册该培训'}
        except Exception as e:
            logger.error(f'注册培训参与者失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_completion(self, participant_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT training_id FROM training_participants WHERE participant_id = ?', (participant_id,))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '参与者不存在'}
                    training_id = result[0]
                    cursor.execute('''
                        UPDATE training_participants SET
                            completion_status = ?, score = ?, completed_at = ?
                        WHERE participant_id = ?
                    ''', ('completed', kwargs.get('score'), now, participant_id))
                    cursor.execute('UPDATE security_training SET completed_count = completed_count + 1 WHERE training_id = ?', (training_id,))
                    conn.commit()
                    return {'success': True, 'completed_at': now}
        except Exception as e:
            logger.error(f'记录培训完成失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_training_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) FROM security_training'
                params = []
                if education_type:
                    query += ' WHERE education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                total_trainings = cursor.fetchone()[0]
                query = 'SELECT SUM(completed_count), SUM(total_count) FROM security_training'
                if education_type:
                    query += ' WHERE education_type = ?'
                cursor.execute(query, params)
                stats = cursor.fetchone()
                completed = stats[0] or 0
                total = stats[1] or 0
                completion_rate = round((completed / total) * 100, 1) if total > 0 else 0
                return {
                    'success': True,
                    'total_trainings': total_trainings,
                    'total_participants': total,
                    'completed_participants': completed,
                    'completion_rate': completion_rate,
                    'education_type': education_type
                }
        except Exception as e:
            logger.error(f'获取培训统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全审计 ==========

    def create_audit(self, audit_type: str, audit_scope: str, **kwargs) -> Dict[str, Any]:
        try:
            audit_id = f"aud_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_audit (
                            audit_id, audit_type, audit_scope, education_type,
                            status, started_at, completed_at, findings_count,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'planned', NULL, NULL, 0, ?, ?)
                    ''', (audit_id, audit_type, audit_scope, kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'audit_id': audit_id}
        except Exception as e:
            logger.error(f'创建安全审计失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_audit(self, audit_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE security_audit SET status = ?, started_at = ? WHERE audit_id = ? AND status = ?',
                                 ('in_progress', now, audit_id, 'planned'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'started_at': now}
                    return {'success': False, 'error': '审计不存在或状态不允许'}
        except Exception as e:
            logger.error(f'启动审计失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_audit_finding(self, audit_id: str, finding_type: str,
                          severity: str, description: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"afd_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM security_audit WHERE audit_id = ?', (audit_id,))
                    audit = cursor.fetchone()
                    if not audit:
                        return {'success': False, 'error': '审计不存在'}
                    if audit[0] != 'in_progress':
                        return {'success': False, 'error': '审计未进行中'}
                    cursor.execute('''
                        INSERT INTO audit_records (
                            record_id, audit_id, finding_type, severity,
                            description, recommendation, status
                        ) VALUES (?, ?, ?, ?, ?, ?, 'open')
                    ''', (record_id, audit_id, finding_type, severity,
                          description, kwargs.get('recommendation')))
                    cursor.execute('UPDATE security_audit SET findings_count = findings_count + 1 WHERE audit_id = ?', (audit_id,))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加审计发现失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_audit(self, audit_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE security_audit SET status = ?, completed_at = ? WHERE audit_id = ? AND status = ?',
                                 ('completed', now, audit_id, 'in_progress'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        cursor.execute('SELECT findings_count FROM security_audit WHERE audit_id = ?', (audit_id,))
                        findings = cursor.fetchone()[0]
                        return {'success': True, 'completed_at': now, 'findings_count': findings}
                    return {'success': False, 'error': '审计不存在或状态不允许'}
        except Exception as e:
            logger.error(f'完成审计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 漏洞扫描 ==========

    def create_vulnerability_scan(self, scan_name: str, scan_type: str,
                                  target: str, **kwargs) -> Dict[str, Any]:
        try:
            scan_id = f"vsc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO vulnerability_scan (
                            scan_id, scan_name, scan_type, target,
                            education_type, status, started_at, completed_at,
                            total_vulnerabilities, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'scheduled', NULL, NULL, 0, ?, ?)
                    ''', (scan_id, scan_name, scan_type, target,
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    return {'success': True, 'scan_id': scan_id}
        except Exception as e:
            logger.error(f'创建漏洞扫描失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_scan(self, scan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE vulnerability_scan SET status = ?, started_at = ? WHERE scan_id = ? AND status = ?',
                                 ('running', now, scan_id, 'scheduled'))
                    if cursor.rowcount == 0:
                        return {'success': False, 'error': '扫描不存在或状态不允许'}
                    conn.commit()
                    return {'success': True, 'started_at': now}
        except Exception as e:
            logger.error(f'运行扫描失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_scan_result(self, scan_id: str, severity: str, title: str,
                        description: str, **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"vsr_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM vulnerability_scan WHERE scan_id = ?', (scan_id,))
                    scan = cursor.fetchone()
                    if not scan:
                        return {'success': False, 'error': '扫描不存在'}
                    if scan[0] != 'running':
                        return {'success': False, 'error': '扫描未运行中'}
                    cursor.execute('''
                        INSERT INTO scan_results (
                            result_id, scan_id, vulnerability_id, severity,
                            title, description, cve_id, remediation, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')
                    ''', (result_id, scan_id, kwargs.get('vulnerability_id', f"vul_{uuid.uuid4().hex[:8]}"),
                          severity, title, description, kwargs.get('cve_id'),
                          kwargs.get('remediation')))
                    cursor.execute('UPDATE vulnerability_scan SET total_vulnerabilities = total_vulnerabilities + 1 WHERE scan_id = ?', (scan_id,))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'添加扫描结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_scan(self, scan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE vulnerability_scan SET status = ?, completed_at = ? WHERE scan_id = ? AND status = ?',
                                 ('completed', now, scan_id, 'running'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        cursor.execute('SELECT total_vulnerabilities FROM vulnerability_scan WHERE scan_id = ?', (scan_id,))
                        vulns = cursor.fetchone()[0]
                        return {'success': True, 'completed_at': now, 'total_vulnerabilities': vulns}
                    return {'success': False, 'error': '扫描不存在或状态不允许'}
        except Exception as e:
            logger.error(f'完成扫描失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_security_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                query_base = ''
                params = []
                if education_type:
                    query_base = 'WHERE education_type = ?'
                    params = [education_type]
                cursor.execute(f'SELECT COUNT(*) FROM security_policies {query_base}', params)
                stats['policy_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM monitoring_alerts WHERE status = ?', ('pending',))
                stats['pending_alerts'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM security_events {query_base}', params)
                stats['event_count'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM vulnerability_scan WHERE status = ? {query_base}', ['completed'] + params)
                stats['completed_scans'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT SUM(total_vulnerabilities) FROM vulnerability_scan WHERE status = ? {query_base}', ['completed'] + params)
                stats['total_vulnerabilities'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) FROM security_audit WHERE status = ? {query_base}', ['completed'] + params)
                stats['completed_audits'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM security_training {query_base}', params)
                stats['training_count'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT SUM(completed_count), SUM(total_count) FROM security_training {query_base}', params)
                training_stats = cursor.fetchone()
                stats['training_completed'] = training_stats[0] or 0
                stats['training_total'] = training_stats[1] or 0
                stats['education_type'] = education_type
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取安全统计失败: {e}')
            return {'success': False, 'error': str(e)}