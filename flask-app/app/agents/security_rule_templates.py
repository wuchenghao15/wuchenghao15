# -*- coding: utf-8 -*-
"""
数据安全系统规则模板
支持数据安全系统自动规则创建、更新迭代，方便AI员工自动触发规则执行操作
"""

class SecurityRuleTemplate:
    """数据安全系统规则模板"""
    
    # 数据访问安全规则
    ACCESS_SECURITY_RULES = [
        {
            'name': '异常访问频率检测',
            'template_key': 'abnormal_access_frequency',
            'category': 'access_security',
            'conditions': [
                {'field': 'access_attempts', 'operator': 'greater_than', 'value': 100},
                {'field': 'time_window_minutes', 'operator': 'less_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到异常访问频率，可能存在暴力破解', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'access_blocked'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'security_analysis', 'employee_template': 'security_analyzer'}}
            ],
            'priority': 15,
            'description': '短时间内大量访问尝试时触发告警'
        },
        {
            'name': '未授权访问检测',
            'template_key': 'unauthorized_access',
            'category': 'access_security',
            'conditions': [
                {'field': 'unauthorized_attempts', 'operator': 'greater_than', 'value': 3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到未授权访问尝试，请立即检查', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'security_alert'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'access_investigation', 'employee_template': 'security_investigator'}}
            ],
            'priority': 20,
            'description': '未授权访问次数过多时触发紧急告警'
        },
        {
            'name': '敏感数据访问告警',
            'template_key': 'sensitive_data_access',
            'category': 'access_security',
            'conditions': [
                {'field': 'sensitive_data_access', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到敏感数据访问，请审核', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'access_audit', 'employee_template': 'compliance_auditor'}},
                {'action_type': 'call_api', 'params': {'url': '/api/security/audit-log', 'method': 'POST'}}
            ],
            'priority': 12,
            'description': '敏感数据被访问时触发审计'
        },
        {
            'name': '跨权限访问检测',
            'template_key': 'cross_permission_access',
            'category': 'access_security',
            'conditions': [
                {'field': 'permission_violation', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到跨权限访问行为', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'permission_violation'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'violation_investigation', 'employee_template': 'security_investigator'}}
            ],
            'priority': 18,
            'description': '检测到跨权限访问时触发调查'
        },
        {
            'name': '访问时间异常检测',
            'template_key': 'access_time_anomaly',
            'category': 'access_security',
            'conditions': [
                {'field': 'access_hour', 'operator': 'less_than', 'value': 6},
                {'field': 'suspicious_access', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到非工作时间异常访问', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'time_based_analysis', 'employee_template': 'security_analyzer'}}
            ],
            'priority': 10,
            'description': '非工作时间异常访问时触发分析'
        }
    ]
    
    # 数据加密安全规则
    ENCRYPTION_SECURITY_RULES = [
        {
            'name': '弱加密检测',
            'template_key': 'weak_encryption_detected',
            'category': 'encryption_security',
            'conditions': [
                {'field': 'encryption_strength', 'operator': 'less_than', 'value': 128}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到弱加密方式，需要升级', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'encryption_upgrade', 'employee_template': 'security_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'encryption_review'}}
            ],
            'priority': 15,
            'description': '加密强度低于128位时触发升级'
        },
        {
            'name': '未加密敏感数据检测',
            'template_key': 'unencrypted_sensitive_data',
            'category': 'encryption_security',
            'conditions': [
                {'field': 'unencrypted_sensitive_fields', 'operator': 'greater_than', 'value': 0}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到未加密的敏感字段，需要立即加密', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'data_encryption', 'employee_template': 'security_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'security_critical'}}
            ],
            'priority': 25,
            'description': '敏感数据未加密时触发紧急处理'
        },
        {
            'name': '证书过期预警',
            'template_key': 'certificate_expiry_warning',
            'category': 'encryption_security',
            'conditions': [
                {'field': 'days_until_expiry', 'operator': 'less_than', 'value': 30}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'SSL/TLS证书将在30天内过期，请及时更新', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'certificate_renewal', 'employee_template': 'system_admin'}}
            ],
            'priority': 12,
            'description': '证书即将过期时提前预警'
        },
        {
            'name': '密钥轮换提醒',
            'template_key': 'key_rotation_reminder',
            'category': 'encryption_security',
            'conditions': [
                {'field': 'days_since_key_rotation', 'operator': 'greater_than', 'value': 90}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '加密密钥已使用超过90天，建议轮换', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'key_rotation', 'employee_template': 'security_engineer'}}
            ],
            'priority': 8,
            'description': '密钥使用过久时提醒轮换'
        }
    ]
    
    # 数据完整性安全规则
    INTEGRITY_SECURITY_RULES = [
        {
            'name': '数据篡改检测',
            'template_key': 'data_tampering_detected',
            'category': 'integrity_security',
            'conditions': [
                {'field': 'hash_mismatch', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到数据完整性被破坏，可能存在篡改', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'integrity_alert'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'tampering_investigation', 'employee_template': 'forensic_analyzer'}},
                {'action_type': 'execute_shell', 'params': {'command': 'sqlite3 app.db "PRAGMA integrity_check;"'}}
            ],
            'priority': 25,
            'description': '数据哈希校验失败时触发紧急调查'
        },
        {
            'name': '异常数据修改检测',
            'template_key': 'abnormal_data_modification',
            'category': 'integrity_security',
            'conditions': [
                {'field': 'modification_count', 'operator': 'greater_than', 'value': 50},
                {'field': 'time_window_minutes', 'operator': 'less_than', 'value': 10}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到异常频繁的数据修改操作', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'modification_audit', 'employee_template': 'compliance_auditor'}}
            ],
            'priority': 15,
            'description': '短时间内大量数据修改时触发审计'
        },
        {
            'name': '备份完整性校验',
            'template_key': 'backup_integrity_check',
            'category': 'integrity_security',
            'conditions': [
                {'field': 'backup_hash_mismatch', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '备份数据完整性校验失败，需要重新备份', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'backup_restore', 'employee_template': 'backup_admin'}},
                {'action_type': 'update_status', 'params': {'status': 'backup_failed'}}
            ],
            'priority': 20,
            'description': '备份数据完整性校验失败时触发修复'
        },
        {
            'name': '日志篡改检测',
            'template_key': 'log_tampering_detection',
            'category': 'integrity_security',
            'conditions': [
                {'field': 'log_sequence_broken', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到日志序列中断，可能存在篡改', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'log_investigation', 'employee_template': 'forensic_analyzer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/security/export-logs', 'method': 'POST'}}
            ],
            'priority': 22,
            'description': '日志序列异常时触发取证分析'
        }
    ]
    
    # 数据隐私保护规则
    PRIVACY_PROTECTION_RULES = [
        {
            'name': 'GDPR违规检测',
            'template_key': 'gdpr_violation_detected',
            'category': 'privacy_protection',
            'conditions': [
                {'field': 'pi_processing_without_consent', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到GDPR违规行为，需要立即处理', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'compliance_violation'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'gdpr_investigation', 'employee_template': 'compliance_officer'}}
            ],
            'priority': 25,
            'description': '检测到GDPR违规时触发紧急处理'
        },
        {
            'name': '数据保留超期检测',
            'template_key': 'data_retention_exceeded',
            'category': 'privacy_protection',
            'conditions': [
                {'field': 'data_age_days', 'operator': 'greater_than', 'value': 365}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '数据保留超过规定期限，需要清理或归档', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'data_cleanup', 'employee_template': 'data_steward'}},
                {'action_type': 'call_api', 'params': {'url': '/api/security/audit-log', 'method': 'POST'}}
            ],
            'priority': 10,
            'description': '数据保留超期时触发清理'
        },
        {
            'name': '跨境数据传输告警',
            'template_key': 'cross_border_transfer_alert',
            'category': 'privacy_protection',
            'conditions': [
                {'field': 'cross_border_transfer', 'operator': 'equals', 'value': True},
                {'field': 'destination_region', 'operator': 'not_in_list', 'value': ['CN', 'US', 'EU']}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到向非白名单地区的数据传输', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'transfer_review'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'transfer_audit', 'employee_template': 'compliance_officer'}}
            ],
            'priority': 15,
            'description': '跨境传输时触发合规审核'
        },
        {
            'name': '用户数据删除请求',
            'template_key': 'user_deletion_request',
            'category': 'privacy_protection',
            'conditions': [
                {'field': 'pending_deletion_requests', 'operator': 'greater_than', 'value': 0}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'data_deletion', 'employee_template': 'data_steward'}},
                {'action_type': 'call_api', 'params': {'url': '/api/security/process-deletion', 'method': 'POST'}}
            ],
            'priority': 12,
            'description': '有待处理的数据删除请求时自动处理'
        }
    ]
    
    # 数据泄露防护规则
    LEAKAGE_PREVENTION_RULES = [
        {
            'name': '敏感数据外泄检测',
            'template_key': 'sensitive_data_leakage',
            'category': 'leakage_prevention',
            'conditions': [
                {'field': 'outgoing_sensitive_content', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到敏感数据可能外泄，请立即处理', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'leakage_alert'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'leakage_investigation', 'employee_template': 'forensic_analyzer'}}
            ],
            'priority': 25,
            'description': '检测到敏感数据外泄时触发紧急响应'
        },
        {
            'name': '异常数据导出检测',
            'template_key': 'abnormal_data_export',
            'category': 'leakage_prevention',
            'conditions': [
                {'field': 'export_size_mb', 'operator': 'greater_than', 'value': 100},
                {'field': 'export_frequency', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到异常大量的数据导出操作', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'export_review'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'export_audit', 'employee_template': 'security_analyzer'}}
            ],
            'priority': 15,
            'description': '大量数据导出时触发审计'
        },
        {
            'name': '可疑数据传输告警',
            'template_key': 'suspicious_data_transfer',
            'category': 'leakage_prevention',
            'conditions': [
                {'field': 'unusual_destination', 'operator': 'equals', 'value': True},
                {'field': 'transfer_size_mb', 'operator': 'greater_than', 'value': 50}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到向异常目标的数据传输', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'transfer_investigation', 'employee_template': 'security_investigator'}},
                {'action_type': 'update_status', 'params': {'status': 'transfer_blocked'}}
            ],
            'priority': 20,
            'description': '可疑传输目标时触发阻断和调查'
        },
        {
            'name': '凭证泄露检测',
            'template_key': 'credential_leakage_detection',
            'category': 'leakage_prevention',
            'conditions': [
                {'field': 'credential_in_logs', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到凭证可能泄露，请立即修改密码', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'credential_rotation', 'employee_template': 'security_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'credential_compromised'}}
            ],
            'priority': 25,
            'description': '凭证泄露时触发紧急轮换'
        }
    ]
    
    # 安全审计规则
    SECURITY_AUDIT_RULES = [
        {
            'name': '定期安全扫描',
            'template_key': 'scheduled_security_scan',
            'category': 'security_audit',
            'conditions': [
                {'field': 'hours_since_last_scan', 'operator': 'greater_than', 'value': 24}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'security_scan', 'employee_template': 'security_scanner'}},
                {'action_type': 'call_api', 'params': {'url': '/api/security/scan', 'method': 'POST'}},
                {'action_type': 'notify_admin', 'params': {'message': '定期安全扫描已触发', 'level': 'info'}}
            ],
            'priority': 8,
            'description': '超过24小时未扫描时触发安全扫描'
        },
        {
            'name': '漏洞修复优先级评估',
            'template_key': 'vulnerability_severity_check',
            'category': 'security_audit',
            'conditions': [
                {'field': 'new_vulnerabilities', 'operator': 'greater_than', 'value': 5},
                {'field': 'critical_vulnerabilities', 'operator': 'greater_than', 'value': 0}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': f'发现 {0} 个高危漏洞，需要立即修复', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'vulnerability_fix', 'employee_template': 'security_engineer'}}
            ],
            'priority': 18,
            'description': '发现高危漏洞时触发紧急修复'
        },
        {
            'name': '安全配置基线检查',
            'template_key': 'security_baseline_check',
            'category': 'security_audit',
            'conditions': [
                {'field': 'days_since_baseline_check', 'operator': 'greater_than', 'value': 7}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'baseline_verification', 'employee_template': 'compliance_auditor'}},
                {'action_type': 'call_api', 'params': {'url': '/api/security/baseline-check', 'method': 'POST'}},
                {'action_type': 'notify_admin', 'params': {'message': '安全基线检查已完成', 'level': 'info'}}
            ],
            'priority': 6,
            'description': '定期进行安全基线检查'
        },
        {
            'name': '权限审计报告生成',
            'template_key': 'permission_audit_report',
            'category': 'security_audit',
            'conditions': [
                {'field': 'days_since_permission_audit', 'operator': 'greater_than', 'value': 30}
            ],
            'actions': [
                {'action_type': 'dispatch_task', 'params': {'task_type': 'permission_audit', 'employee_template': 'compliance_officer'}},
                {'action_type': 'call_api', 'params': {'url': '/api/security/permission-report', 'method': 'POST'}},
                {'action_type': 'notify_admin', 'params': {'message': '权限审计报告已生成', 'level': 'info'}}
            ],
            'priority': 5,
            'description': '定期生成权限审计报告'
        }
    ]
    
    # 数据库安全规则
    DATABASE_SECURITY_RULES = [
        {
            'name': 'SQL注入检测',
            'template_key': 'sql_injection_detected',
            'category': 'database_security',
            'conditions': [
                {'field': 'sql_injection_pattern', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到SQL注入攻击尝试', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'attack_detected'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'attack_analysis', 'employee_template': 'security_analyzer'}}
            ],
            'priority': 25,
            'description': '检测到SQL注入时触发紧急响应'
        },
        {
            'name': '数据库连接异常',
            'template_key': 'db_connection_anomaly',
            'category': 'database_security',
            'conditions': [
                {'field': 'failed_connections', 'operator': 'greater_than', 'value': 10},
                {'field': 'time_window_minutes', 'operator': 'less_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '数据库连接失败次数异常，可能存在攻击', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'db_investigation', 'employee_template': 'dba_security'}},
                {'action_type': 'update_status', 'params': {'status': 'db_alert'}}
            ],
            'priority': 15,
            'description': '数据库连接异常时触发分析'
        },
        {
            'name': '数据库性能异常',
            'template_key': 'db_performance_anomaly',
            'category': 'database_security',
            'conditions': [
                {'field': 'slow_query_ratio', 'operator': 'greater_than', 'value': 0.3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '数据库慢查询比例过高，可能存在异常', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'query_optimization', 'employee_template': 'dba_optimizer'}}
            ],
            'priority': 10,
            'description': '数据库性能异常时触发优化'
        },
        {
            'name': '数据库备份状态检查',
            'template_key': 'db_backup_status_check',
            'category': 'database_security',
            'conditions': [
                {'field': 'days_since_last_backup', 'operator': 'greater_than', 'value': 1}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '数据库已超过1天未备份，请检查', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'backup_check', 'employee_template': 'backup_admin'}}
            ],
            'priority': 12,
            'description': '数据库未按时备份时触发检查'
        }
    ]
    
    # 访问控制规则
    ACCESS_CONTROL_RULES = [
        {
            'name': '密码策略违规检测',
            'template_key': 'password_policy_violation',
            'category': 'access_control',
            'conditions': [
                {'field': 'weak_password_users', 'operator': 'greater_than', 'value': 0}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': f'发现 {0} 个用户使用弱密码', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'password_enforcement', 'employee_template': 'security_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'password_review'}}
            ],
            'priority': 15,
            'description': '发现弱密码时触发强制更新'
        },
        {
            'name': '账户锁定检测',
            'template_key': 'account_lockout_detection',
            'category': 'access_control',
            'conditions': [
                {'field': 'locked_accounts', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '大量账户被锁定，可能存在暴力破解', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'lockout_analysis', 'employee_template': 'security_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'lockout_alert'}}
            ],
            'priority': 12,
            'description': '账户锁定过多时触发分析'
        },
        {
            'name': '特权账户活动监控',
            'template_key': 'privileged_account_monitoring',
            'category': 'access_control',
            'conditions': [
                {'field': 'privileged_action_count', 'operator': 'greater_than', 'value': 20},
                {'field': 'time_window_minutes', 'operator': 'less_than', 'value': 30}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '特权账户活动频繁，请审核', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'privileged_audit', 'employee_template': 'compliance_officer'}}
            ],
            'priority': 12,
            'description': '特权账户活动异常时触发审计'
        },
        {
            'name': '会话超时检测',
            'template_key': 'session_timeout_detection',
            'category': 'access_control',
            'conditions': [
                {'field': 'active_sessions', 'operator': 'greater_than', 'value': 1000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '系统会话数过多，建议清理', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'session_cleanup', 'employee_template': 'system_admin'}}
            ],
            'priority': 6,
            'description': '会话数过多时触发清理'
        }
    ]
    
    ALL_TEMPLATES = (
        ACCESS_SECURITY_RULES + 
        ENCRYPTION_SECURITY_RULES + 
        INTEGRITY_SECURITY_RULES + 
        PRIVACY_PROTECTION_RULES + 
        LEAKAGE_PREVENTION_RULES +
        SECURITY_AUDIT_RULES +
        DATABASE_SECURITY_RULES +
        ACCESS_CONTROL_RULES
    )
    
    CATEGORIES = [
        'access_security', 
        'encryption_security', 
        'integrity_security', 
        'privacy_protection', 
        'leakage_prevention',
        'security_audit',
        'database_security',
        'access_control'
    ]