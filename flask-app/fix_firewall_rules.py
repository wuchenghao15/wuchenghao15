import sys
sys.path.insert(0, '.')

from app.services.firewall_system import firewall_system

rules = [
    {
        'rule_id': 'rule_block_sql_injection',
        'name': 'SQL注入防护',
        'description': '阻止SQL注入攻击',
        'action': 'block',
        'priority': 10,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'regex',
             'value': r'.*(\'|\"|\s)(\s)*(union|select|insert|delete|drop|update)(\s+).*', 'options': 'i'},
        ],
    },
    {
        'rule_id': 'rule_block_xss',
        'name': 'XSS防护',
        'description': '阻止跨站脚本攻击',
        'action': 'block',
        'priority': 10,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'regex',
             'value': r'.*(<script|<iframe|<img|javascript:|onerror|onload).*', 'options': 'i'},
        ],
    },
    {
        'rule_id': 'rule_block_command_injection',
        'name': '命令注入防护',
        'description': '阻止命令注入攻击',
        'action': 'block',
        'priority': 10,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'regex',
             'value': r'.*(;|\||&|`|\$\(|\$\{).*(cat|ls|id|whoami).*', 'options': 'i'},
        ],
    },
    {
        'rule_id': 'rule_block_ssrf',
        'name': 'SSRF防护',
        'description': '阻止服务器端请求伪造',
        'action': 'block',
        'priority': 10,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'regex',
             'value': r'.*(127\.0\.0\.1|localhost|0\.0\.0\.0|file://).*', 'options': 'i'},
        ],
    },
    {
        'rule_id': 'rule_block_lfi',
        'name': '文件包含防护',
        'description': '阻止文件包含攻击',
        'action': 'block',
        'priority': 10,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'regex',
             'value': r'.*(php://|data://|expect://|\.\./).*', 'options': 'i'},
        ],
    },
    {
        'rule_id': 'rule_block_brute_force',
        'name': '暴力破解防护',
        'description': '限制登录接口频率',
        'action': 'block',
        'priority': 20,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'contains', 'value': '/login'},
        ],
    },
    {
        'rule_id': 'rule_block_sensitive_files',
        'name': '敏感文件防护',
        'description': '阻止访问敏感文件',
        'action': 'block',
        'priority': 10,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'regex',
             'value': r'.*(/\.env|/\.git|/config\.py|/settings\.py).*', 'options': 'i'},
        ],
    },
    {
        'rule_id': 'rule_block_path_traversal',
        'name': '路径遍历防护',
        'description': '阻止目录遍历攻击',
        'action': 'block',
        'priority': 10,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'regex',
             'value': r'.*(\.\./|\.\.\\).*', 'options': 'i'},
        ],
    },
    {
        'rule_id': 'rule_block_bot_scanners',
        'name': '扫描器防护',
        'description': '阻止常见扫描器和自动化工具访问',
        'action': 'block',
        'priority': 20,
        'enabled': True,
        'conditions': [
            {'field': 'header', 'header_name': 'User-Agent', 'operator': 'regex',
             'value': r'.*(sqlmap|nikto|nmap|masscan|dirb|gobuster|wpscan|hydra|metasploit|curl|wget).*', 'options': 'i'},
        ],
    },
    {
        'rule_id': 'rule_api_rate_limit',
        'name': 'API速率限制',
        'description': '限制API接口访问频率',
        'action': 'throttle',
        'priority': 30,
        'enabled': True,
        'conditions': [
            {'field': 'url', 'operator': 'starts_with', 'value': '/api/'},
        ],
    },
]

added = 0
for rule in rules:
    existing = firewall_system.get_rule(rule['rule_id'])
    if existing:
        firewall_system.update_rule(rule['rule_id'], rule)
        added += 1
    else:
        firewall_system.add_rule(rule)
        added += 1

print(f'成功添加/更新 {added} 条安全规则')

rules_list = firewall_system.list_rules()
print(f'\n当前规则数: {len(rules_list)}')
print('\n规则列表:')
for rule in rules_list:
    status = '✅' if rule.get('enabled') else '❌'
    action_map = {'block': '🔴 阻止', 'allow': '🟢 允许', 'throttle': '🟡 限流'}
    action = action_map.get(rule.get('action'), rule.get('action'))
    print(f'  {status} [{rule.get("priority", 0)}] {rule.get("name")} - {action}')

stats = firewall_system.get_statistics()
print(f'\n防火墙统计:')
print(f'  拦截请求数: {stats.get("blocked_requests", 0)}')
print(f'  允许请求数: {stats.get("allowed_requests", 0)}')
print(f'  规则总数: {stats.get("rule_count", 0)}')
