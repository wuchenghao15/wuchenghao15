# -*- coding: utf-8 -*-
"""
网络层安全系统规则模板
支持网络层安全系统自动规则创建、更新迭代，方便AI员工自动触发规则执行操作
"""

class NetworkSecurityRuleTemplate:
    """网络层安全系统规则模板"""
    
    # 防火墙安全规则
    FIREWALL_SECURITY_RULES = [
        {
            'name': '异常入站连接检测',
            'template_key': 'abnormal_inbound_connection',
            'category': 'firewall_security',
            'conditions': [
                {'field': 'inbound_connection_rate', 'operator': 'greater_than', 'value': 1000},
                {'field': 'time_window_seconds', 'operator': 'less_than', 'value': 60}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到异常入站连接，可能存在端口扫描', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'firewall_alert'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'connection_analysis', 'employee_template': 'network_security_analyzer'}}
            ],
            'priority': 15,
            'description': '短时间内大量入站连接时触发告警'
        },
        {
            'name': '被禁止端口访问',
            'template_key': 'blocked_port_access',
            'category': 'firewall_security',
            'conditions': [
                {'field': 'blocked_port_attempt', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到被禁止端口的访问尝试', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'port_blocked'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'port_scan_investigation', 'employee_template': 'security_investigator'}}
            ],
            'priority': 12,
            'description': '检测到被禁止端口访问时触发调查'
        },
        {
            'name': '防火墙规则冲突检测',
            'template_key': 'firewall_rule_conflict',
            'category': 'firewall_security',
            'conditions': [
                {'field': 'rule_conflict_detected', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到防火墙规则冲突，需要审核', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'rule_optimization', 'employee_template': 'firewall_admin'}},
                {'action_type': 'update_status', 'params': {'status': 'rule_review'}}
            ],
            'priority': 8,
            'description': '防火墙规则冲突时触发优化'
        },
        {
            'name': '防火墙规则过期提醒',
            'template_key': 'firewall_rule_expiry',
            'category': 'firewall_security',
            'conditions': [
                {'field': 'rules_expiring_soon', 'operator': 'greater_than', 'value': 0},
                {'field': 'days_until_expiry', 'operator': 'less_than', 'value': 7}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': f'{0} 条防火墙规则即将过期，需要审核', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'rule_review', 'employee_template': 'firewall_admin'}}
            ],
            'priority': 6,
            'description': '防火墙规则即将过期时提醒审核'
        },
        {
            'name': '防火墙连接数超限',
            'template_key': 'firewall_connection_limit',
            'category': 'firewall_security',
            'conditions': [
                {'field': 'active_connections', 'operator': 'greater_than', 'value': 10000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '防火墙活跃连接数超过10000，可能存在攻击', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'connection_optimization', 'employee_template': 'network_optimizer'}},
                {'action_type': 'update_status', 'params': {'status': 'connection_limit_alert'}}
            ],
            'priority': 15,
            'description': '连接数超限时触发优化'
        }
    ]
    
    # DDoS防护规则
    DDOS_PROTECTION_RULES = [
        {
            'name': 'DDoS攻击检测',
            'template_key': 'ddos_attack_detected',
            'category': 'ddos_protection',
            'conditions': [
                {'field': 'traffic_bps', 'operator': 'greater_than', 'value': 1000000000},
                {'field': 'packet_rate', 'operator': 'greater_than', 'value': 100000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到疑似DDoS攻击，流量异常激增', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'ddos_attack'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'ddos_mitigation', 'employee_template': 'ddos_protector'}},
                {'action_type': 'execute_shell', 'params': {'command': 'iptables -I INPUT -j DROP'}}
            ],
            'priority': 25,
            'description': 'DDoS攻击时触发紧急防护'
        },
        {
            'name': 'SYN Flood检测',
            'template_key': 'syn_flood_detected',
            'category': 'ddos_protection',
            'conditions': [
                {'field': 'half_open_connections', 'operator': 'greater_than', 'value': 5000},
                {'field': 'syn_rate', 'operator': 'greater_than', 'value': 1000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到SYN Flood攻击', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'syn_flood'}},
                {'action_type': 'execute_shell', 'params': {'command': 'sysctl -w net.ipv4.tcp_syncookies=1'}}
            ],
            'priority': 25,
            'description': 'SYN Flood攻击时触发防护'
        },
        {
            'name': 'HTTP Flood检测',
            'template_key': 'http_flood_detected',
            'category': 'ddos_protection',
            'conditions': [
                {'field': 'http_requests_per_second', 'operator': 'greater_than', 'value': 5000},
                {'field': 'unique_ips', 'operator': 'less_than', 'value': 100}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到HTTP Flood攻击', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'rate_limiting', 'employee_template': 'ddos_protector'}},
                {'action_type': 'update_status', 'params': {'status': 'http_flood'}}
            ],
            'priority': 22,
            'description': 'HTTP Flood时触发限流'
        },
        {
            'name': 'DNS Amplification检测',
            'template_key': 'dns_amplification_detected',
            'category': 'ddos_protection',
            'conditions': [
                {'field': 'dns_response_size', 'operator': 'greater_than', 'value': 500},
                {'field': 'dns_query_rate', 'operator': 'greater_than', 'value': 10000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到DNS Amplification攻击', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'dns_protection', 'employee_template': 'network_security_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'dns_amplification'}}
            ],
            'priority': 23,
            'description': 'DNS Amplification攻击时触发防护'
        },
        {
            'name': '流量限速触发',
            'template_key': 'rate_limit_triggered',
            'category': 'ddos_protection',
            'conditions': [
                {'field': 'rate_limit_hits', 'operator': 'greater_than', 'value': 100}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '流量限速触发次数过多，建议检查', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'traffic_analysis', 'employee_template': 'network_analyzer'}}
            ],
            'priority': 10,
            'description': '限速触发过多时触发分析'
        }
    ]
    
    # 入侵检测规则
    INTRUSION_DETECTION_RULES = [
        {
            'name': '网络入侵检测',
            'template_key': 'network_intrusion_detected',
            'category': 'intrusion_detection',
            'conditions': [
                {'field': 'intrusion_signature_match', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到网络入侵行为，请立即处理', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'intrusion_detected'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'intrusion_investigation', 'employee_template': 'forensic_analyzer'}},
                {'action_type': 'execute_shell', 'params': {'command': 'iptables -A INPUT -s {} -j DROP'}}
            ],
            'priority': 25,
            'description': '入侵检测时触发紧急响应'
        },
        {
            'name': '恶意流量检测',
            'template_key': 'malicious_traffic_detected',
            'category': 'intrusion_detection',
            'conditions': [
                {'field': 'malware_signature', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到恶意流量，请隔离受影响主机', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'malware_investigation', 'employee_template': 'security_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'malware_detected'}}
            ],
            'priority': 25,
            'description': '恶意流量时触发隔离'
        },
        {
            'name': '异常协议使用',
            'template_key': 'abnormal_protocol_usage',
            'category': 'intrusion_detection',
            'conditions': [
                {'field': 'unusual_protocol', 'operator': 'equals', 'value': True},
                {'field': 'protocol_frequency', 'operator': 'greater_than', 'value': 0.8}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到异常协议使用', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'protocol_analysis', 'employee_template': 'network_security_analyzer'}}
            ],
            'priority': 12,
            'description': '异常协议时触发分析'
        },
        {
            'name': '可疑网络扫描',
            'template_key': 'suspicious_network_scan',
            'category': 'intrusion_detection',
            'conditions': [
                {'field': 'port_scan_detected', 'operator': 'equals', 'value': True},
                {'field': 'scan_speed', 'operator': 'greater_than', 'value': 100}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到网络扫描行为', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'scan_detected'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'scan_investigation', 'employee_template': 'security_investigator'}}
            ],
            'priority': 15,
            'description': '网络扫描时触发阻断和调查'
        },
        {
            'name': '僵尸网络通信检测',
            'template_key': 'botnet_communication_detected',
            'category': 'intrusion_detection',
            'conditions': [
                {'field': 'botnet_signature', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到僵尸网络通信，请立即隔离', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'botnet_investigation', 'employee_template': 'forensic_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'botnet_alert'}}
            ],
            'priority': 25,
            'description': '僵尸网络通信时触发紧急隔离'
        }
    ]
    
    # SSL/TLS安全规则
    SSL_TLS_SECURITY_RULES = [
        {
            'name': '弱SSL/TLS协议检测',
            'template_key': 'weak_ssl_tls_detected',
            'category': 'ssl_tls_security',
            'conditions': [
                {'field': 'ssl_protocol_version', 'operator': 'less_than', 'value': 3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到使用弱SSL/TLS协议，需要升级', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'ssl_upgrade', 'employee_template': 'security_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'ssl_review'}}
            ],
            'priority': 15,
            'description': '弱协议时触发升级'
        },
        {
            'name': '证书链不完整',
            'template_key': 'incomplete_certificate_chain',
            'category': 'ssl_tls_security',
            'conditions': [
                {'field': 'certificate_chain_length', 'operator': 'less_than', 'value': 2}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '证书链不完整，可能导致连接问题', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'certificate_fix', 'employee_template': 'security_engineer'}}
            ],
            'priority': 10,
            'description': '证书链不完整时触发修复'
        },
        {
            'name': 'SSL握手异常',
            'template_key': 'ssl_handshake_anomaly',
            'category': 'ssl_tls_security',
            'conditions': [
                {'field': 'ssl_handshake_failures', 'operator': 'greater_than', 'value': 50},
                {'field': 'time_window_minutes', 'operator': 'less_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'SSL握手失败次数过多，可能存在攻击', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'ssl_investigation', 'employee_template': 'network_security_analyzer'}}
            ],
            'priority': 12,
            'description': '握手异常时触发调查'
        },
        {
            'name': '自签名证书检测',
            'template_key': 'self_signed_certificate',
            'category': 'ssl_tls_security',
            'conditions': [
                {'field': 'self_signed_in_production', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '生产环境检测到自签名证书，需要更换', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'certificate_replacement', 'employee_template': 'security_engineer'}},
                {'action_type': 'update_status', 'params': {'status': 'certificate_alert'}}
            ],
            'priority': 20,
            'description': '生产环境自签名证书时触发紧急更换'
        }
    ]
    
    # DNS安全规则
    DNS_SECURITY_RULES = [
        {
            'name': 'DNS隧道检测',
            'template_key': 'dns_tunnel_detected',
            'category': 'dns_security',
            'conditions': [
                {'field': 'dns_query_size_avg', 'operator': 'greater_than', 'value': 100},
                {'field': 'dns_query_frequency', 'operator': 'greater_than', 'value': 1000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到DNS隧道通信，可能存在数据外泄', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'dns_investigation', 'employee_template': 'forensic_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'dns_tunnel_alert'}}
            ],
            'priority': 23,
            'description': 'DNS隧道时触发紧急调查'
        },
        {
            'name': 'DNS放大攻击检测',
            'template_key': 'dns_amplification_attack',
            'category': 'dns_security',
            'conditions': [
                {'field': 'dns_response_ratio', 'operator': 'greater_than', 'value': 50}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到DNS放大攻击', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'dns_amplification_attack'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'dns_protection', 'employee_template': 'network_security_analyzer'}}
            ],
            'priority': 22,
            'description': 'DNS放大攻击时触发防护'
        },
        {
            'name': 'DNS缓存投毒检测',
            'template_key': 'dns_cache_poisoning',
            'category': 'dns_security',
            'conditions': [
                {'field': 'dns_mismatch_count', 'operator': 'greater_than', 'value': 10}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到DNS缓存可能中毒', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'dns_cache_clear', 'employee_template': 'network_admin'}},
                {'action_type': 'execute_shell', 'params': {'command': 'systemctl restart named'}}
            ],
            'priority': 20,
            'description': '缓存投毒时触发清理'
        },
        {
            'name': '异常DNS查询模式',
            'template_key': 'abnormal_dns_query_pattern',
            'category': 'dns_security',
            'conditions': [
                {'field': 'unusual_domain_pattern', 'operator': 'equals', 'value': True},
                {'field': 'query_count', 'operator': 'greater_than', 'value': 5000}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到异常DNS查询模式', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'dns_analysis', 'employee_template': 'network_security_analyzer'}}
            ],
            'priority': 12,
            'description': '异常DNS查询时触发分析'
        }
    ]
    
    # VPN/隧道安全规则
    VPN_TUNNEL_SECURITY_RULES = [
        {
            'name': 'VPN未授权访问',
            'template_key': 'vpn_unauthorized_access',
            'category': 'vpn_tunnel_security',
            'conditions': [
                {'field': 'vpn_unauthorized_attempts', 'operator': 'greater_than', 'value': 3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'VPN未授权访问次数过多', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'vpn_alert'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'vpn_investigation', 'employee_template': 'security_investigator'}}
            ],
            'priority': 15,
            'description': 'VPN未授权时触发告警'
        },
        {
            'name': 'VPN会话异常',
            'template_key': 'vpn_session_anomaly',
            'category': 'vpn_tunnel_security',
            'conditions': [
                {'field': 'vpn_session_duration', 'operator': 'greater_than', 'value': 86400}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'VPN会话持续时间异常长', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'session_audit', 'employee_template': 'security_analyzer'}}
            ],
            'priority': 8,
            'description': 'VPN会话异常时触发审计'
        },
        {
            'name': '隧道加密强度不足',
            'template_key': 'tunnel_encryption_weak',
            'category': 'vpn_tunnel_security',
            'conditions': [
                {'field': 'tunnel_encryption_bits', 'operator': 'less_than', 'value': 128}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '隧道加密强度低于128位，需要升级', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'tunnel_upgrade', 'employee_template': 'security_engineer'}}
            ],
            'priority': 12,
            'description': '加密强度不足时触发升级'
        }
    ]
    
    # 网络隔离安全规则
    NETWORK_ISOLATION_SECURITY_RULES = [
        {
            'name': '跨网段异常访问',
            'template_key': 'cross_subnet_anomaly',
            'category': 'network_isolation',
            'conditions': [
                {'field': 'cross_subnet_attempt', 'operator': 'equals', 'value': True},
                {'field': 'unauthorized_subnet', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到跨网段未授权访问', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'subnet_investigation', 'employee_template': 'network_security_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'isolation_violation'}}
            ],
            'priority': 15,
            'description': '跨网段异常时触发调查'
        },
        {
            'name': '广播风暴检测',
            'template_key': 'broadcast_storm_detected',
            'category': 'network_isolation',
            'conditions': [
                {'field': 'broadcast_traffic_ratio', 'operator': 'greater_than', 'value': 0.3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到广播风暴，网络可能存在环路', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'broadcast_analysis', 'employee_template': 'network_optimizer'}},
                {'action_type': 'execute_shell', 'params': {'command': 'switch-cli "show interfaces"'}}
            ],
            'priority': 18,
            'description': '广播风暴时触发分析'
        },
        {
            'name': 'MAC地址泛洪',
            'template_key': 'mac_flooding_detected',
            'category': 'network_isolation',
            'conditions': [
                {'field': 'mac_address_count', 'operator': 'greater_than', 'value': 1000},
                {'field': 'time_window_minutes', 'operator': 'less_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到MAC地址泛洪攻击', 'level': 'critical'}},
                {'action_type': 'update_status', 'params': {'status': 'mac_flood'}},
                {'action_type': 'execute_shell', 'params': {'command': 'switch-cli "show mac address-table count"'}}
            ],
            'priority': 22,
            'description': 'MAC泛洪时触发防护'
        },
        {
            'name': 'VLAN跳跃攻击检测',
            'template_key': 'vlan_hopping_detected',
            'category': 'network_isolation',
            'conditions': [
                {'field': 'vlan_tagging_anomaly', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到VLAN跳跃攻击尝试', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'vlan_security_check', 'employee_template': 'network_security_analyzer'}},
                {'action_type': 'update_status', 'params': {'status': 'vlan_hopping'}}
            ],
            'priority': 23,
            'description': 'VLAN跳跃时触发安全检查'
        }
    ]
    
    # 网络流量监控规则
    NETWORK_TRAFFIC_MONITORING_RULES = [
        {
            'name': '带宽使用率过高',
            'template_key': 'bandwidth_usage_high',
            'category': 'network_traffic_monitoring',
            'conditions': [
                {'field': 'bandwidth_usage_percent', 'operator': 'greater_than', 'value': 90}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '带宽使用率超过90%，需要优化', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'bandwidth_optimization', 'employee_template': 'network_optimizer'}},
                {'action_type': 'update_status', 'params': {'status': 'bandwidth_critical'}}
            ],
            'priority': 15,
            'description': '带宽过高时触发优化'
        },
        {
            'name': '延迟异常检测',
            'template_key': 'latency_anomaly_detected',
            'category': 'network_traffic_monitoring',
            'conditions': [
                {'field': 'average_latency_ms', 'operator': 'greater_than', 'value': 500}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '网络延迟超过500ms，存在异常', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'latency_analysis', 'employee_template': 'network_analyzer'}}
            ],
            'priority': 12,
            'description': '延迟异常时触发分析'
        },
        {
            'name': '丢包率异常',
            'template_key': 'packet_loss_anomaly',
            'category': 'network_traffic_monitoring',
            'conditions': [
                {'field': 'packet_loss_percent', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '网络丢包率超过5%，需要检查', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'network_diagnostic', 'employee_template': 'network_analyzer'}}
            ],
            'priority': 15,
            'description': '丢包率异常时触发诊断'
        },
        {
            'name': '流量峰值检测',
            'template_key': 'traffic_spike_detected',
            'category': 'network_traffic_monitoring',
            'conditions': [
                {'field': 'traffic_increase_ratio', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到流量突增5倍以上', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'traffic_analysis', 'employee_template': 'network_analyzer'}}
            ],
            'priority': 8,
            'description': '流量突增时触发分析'
        },
        {
            'name': '网络抖动检测',
            'template_key': 'network_jitter_detected',
            'category': 'network_traffic_monitoring',
            'conditions': [
                {'field': 'jitter_ms', 'operator': 'greater_than', 'value': 100}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '网络抖动超过100ms，影响服务质量', 'level': 'info'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'jitter_analysis', 'employee_template': 'network_analyzer'}}
            ],
            'priority': 10,
            'description': '网络抖动时触发分析'
        }
    ]
    
    ALL_TEMPLATES = (
        FIREWALL_SECURITY_RULES + 
        DDOS_PROTECTION_RULES + 
        INTRUSION_DETECTION_RULES + 
        SSL_TLS_SECURITY_RULES + 
        DNS_SECURITY_RULES +
        VPN_TUNNEL_SECURITY_RULES +
        NETWORK_ISOLATION_SECURITY_RULES +
        NETWORK_TRAFFIC_MONITORING_RULES
    )
    
    CATEGORIES = [
        'firewall_security',
        'ddos_protection',
        'intrusion_detection',
        'ssl_tls_security',
        'dns_security',
        'vpn_tunnel_security',
        'network_isolation',
        'network_traffic_monitoring'
    ]