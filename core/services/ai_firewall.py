#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Firewall（AI 防火墙核心）
- 统一规则引擎：从 app.db.ai_firewall_rules 读取并缓存到内存
- 请求拦截：before_request 时对 method/path/query/body/header/ua/ip 扫描
- 24 条种子规则（SQLi/XSS/SSRF/路径遍历/命令注入/恶意 UA/恶意 IP/速率/敏感词/方法白名单）
- 所有命中写入 security_events_log（复用 security_middleware 表，避免重复）
"""
import os
import re
import time
import json
import sqlite3
import hashlib
import logging
from datetime import datetime
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DB = os.path.join(BASE_DIR, 'app.db')

RULE_TABLE = 'ai_firewall_rules'
EVENT_TABLE = 'security_events_log'

ALLOWED_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}

RULE_CACHE = {
    'loaded_at': 0,
    'ttl': 15,
    'rules': [],
}

IP_RATE_STATE = defaultdict(lambda: deque(maxlen=512))
UA_RATE_STATE = defaultdict(lambda: deque(maxlen=512))
USER_RATE_STATE = defaultdict(lambda: deque(maxlen=512))
PATH_TRAVERSAL_RE = re.compile(r'(?:\.\.[/\\]){2,}|(?:%2e%2e[/\\]){2,}|/etc/(passwd|shadow|hosts|nginx|\w+/)|\bwindows[\\/]+system32\b', re.I)
SQLI_RE = re.compile(
    r"(\bunion\s+(all\s+)?select\b|\bselect\s+.+\s+from\s+\w+\b|\bdrop\s+(table|database)\b|\binsert\s+into\b|\bdelete\s+from\b|\bupdate\s+\w+\s+set\b|\bor\s+1\s*=\s*1\b|\band\s+1\s*=\s*1\b|\bexec(ute)?\s*\(|\bdeclare\s+@\w+\b|--\s+.*$|/\*.*?\*/|\bwaitfor\s+delay\b|\bsleep\s*\(\s*\d+\s*\)|\bbenchmark\s*\(|\binformation_schema\b|\b0x[0-9a-f]{5,}\b)",
    re.I | re.S
)
XSS_RE = re.compile(
    r"(<script[^>]*>.*?</script>|<svg[^>]*\son\w+\s*=|javascript:\s*\w|onload\s*=|onerror\s*=|onclick\s*=|<iframe[^>]*src=|<img[^>]+\son\w+\s*=|document\.(cookie|location)|window\.(location|open)|eval\s*\(|expression\s*\()",
    re.I | re.S
)
SSRF_RE = re.compile(
    r"(https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.|169\.254\.|metadata\.google\.internal|169\.254\.169\.254|aws\.amazon\.com\.cn/latest/meta-data/)|\bfile://|\bgopher://|\bdict://|\bftp://(localhost|127\.0\.0\.1))",
    re.I
)
CMD_INJECT_RE = re.compile(
    r"[;&|`$]\s*(ls|cat|id|whoami|uname|curl|wget|nc|bash|sh|zsh|rm|mkfifo|python|perl|ruby|php|node|chmod|chown|tar|dd|iptables|systemctl|passwd)\b|(\b(?:wget|curl)\s+https?://\S+\s+\|\s+(?:ba|z|k|da)?sh\b)",
    re.I
)
MALICIOUS_UA_RE = re.compile(
    r"(sqlmap|nmap|nikto|havij|acunetix|nessus|masscan|zgrab|dirbuster|gobuster|wfuzz|hydra|john|metasploit|fridaythe13th|python-requests/\s*$|curl/\s*$|wget/\s*$|\bbot\b.*scanner|exploit-db|cve-\d{4}-\d{4,7}\s*probe)",
    re.I
)
SENSITIVE_WORDS_RE = re.compile(
    r"(select\s+\*\s+from\s+users|union\s+select\s+@@version|root\x00toor|xp_cmdshell|load_file\s*\(|into\s+outfile|\bdrop\s+table\s+wp_|base64_decode\s*\(\s*['\"]?\s*PD9waH)",
    re.I
)

# ===== 升级：新增高级威胁检测正则 =====

# XXE 注入（XML External Entity）
XXE_RE = re.compile(
    r"(<!ENTITY\s+|<!DOCTYPE\s+\w+\s+\[|SYSTEM\s+[\"']file://|SYSTEM\s+[\"']http|<!ENTITY\s+%\s*\w+\s+SYSTEM|parameter\s+entity|%\w+;)",
    re.I | re.S
)

# 服务端模板注入（SSTI: Jinja2/Twig/FreeMarker）
SSTI_RE = re.compile(
    r"(\{\{.*?\}\}|\{%.*?%\}|\$\{.*?\}|#set\s*\(|#foreach\s*\(|#if\s*\(|\{\{.*?__class__.*?\}\}|\{\{.*?__subclasses__.*?\}\}|\{\{.*?__globals__.*?\}\}|\{\{.*?__import__.*?\}\}|\{\{.*?__builtins__.*?\}\})",
    re.I | re.S
)

# PHP 反序列化 / Java 反序列化载荷
DESERIAL_RE = re.compile(
    r"(O:\d+:\"|a:\d+:\{|s:\d+:\"|b:0;|b:1;|N;|i:\d+;|d:[\d.]+;|__wakeup\(|__destruct\(|__toString\(|Serializable|readObject|writeObject|java\.util\.HashMap|javax\.script|org\.apache\.commons\.collections|com\.sun\.org\.apache\.xalan|ysoserial|java\.rmi\.registry|rmi://|ldap://\d|JNDI|InitialContext|remoteReference)",
    re.I | re.S
)

# 敏感文件读取（补充 PATH_TRAVERSAL 覆盖不到的）
SENSITIVE_FILE_RE = re.compile(
    r"(/proc/(self|version|cpuinfo|meminfo)|/sys/(class|kernel|net)|/var/(log|spool|lib)/|/root/\.|/home/\w+/\.ssh/|/home/\w+/\.bash_history|/home/\w+/\.env|/var/www/\.env|/app/\.env|/opt/\.env|/srv/\.env|\.aws/credentials|\.git/config|\.svn/entries|\.htaccess|\.htpasswd|web\.config|wp-config\.php|configuration\.php|settings\.py|local_settings\.py|config\.database)",
    re.I
)

# HTTP 请求走私 / CRLF 注入
CRLF_RE = re.compile(
    r"(\r\n\r\n|\n\n|\r\nSet-Cookie:|\r\nLocation:|\r\nContent-Length:|\r\nTransfer-Encoding:|%0d%0a%0d%0a|%0d%0aSet-Cookie:|%0d%0aLocation:|%0d%0aContent-Length:|%0d%0aTransfer-Encoding:)",
    re.I
)

# Open Redirect
OPEN_REDIRECT_RE = re.compile(
    r"(redirect_uri=https?://(?!localhost|127\.0\.0\.1|\[::1\])|return_url=https?://(?!localhost|127\.0\.0\.1)|next=https?://(?!localhost|127\.0\.0\.1)|callback=https?://(?!localhost|127\.0\.0\.1)|url=https?://(?!localhost|127\.0\.0\.1)[a-z0-9.-]+\.[a-z]{2,})",
    re.I
)

# 越权 IDOR 检测模式（参数中的可疑数字递增）
IDOR_RE = re.compile(
    r"(user_id=0|user_id=-1|id=0|id=-1|uid=0|uid=-1|admin=1|role=admin|role=super_admin|is_admin=1|is_superuser=1|debug=1|test=1|internal=1)",
    re.I
)

# GraphQL 注入
GRAPHQL_INJECT_RE = re.compile(
    r"(__schema|__type|__typename|__field|mutation\s*\{|query\s*\{.*\bintrospection\b|batch\s*:\s*\[)",
    re.I | re.S
)

# NoSQL 注入
NOSQL_INJECT_RE = re.compile(
    r"(\$where\s*:|\$ne\s*:|\$gt\s*:|\$lt\s*:|\$gte\s*:|\$lte\s*:|\$in\s*:|\$nin\s*:|\$regex\s*:|\$exists\s*:|\$or\s*:|\$and\s*:|\$not\s*:|\.find\s*\(\s*\{)",
    re.I
)

# JWT 篡改检测
JWT_RE = re.compile(
    r"(eyJhbGciOiJub25lIn0\.|eyJhbGciOiJcIlwiXCJ9\.|eyJhbGciOlwiYWxnXCI6XCJub25lXCJ9\.|eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0\.|alg[\"']?\s*:\s*[\"']none[\"'])",
    re.I
)



def _conn():
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_firewall_tables():
    """幂等创建表（规则 + 事件）"""
    try:
        with _conn() as conn:
            conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {RULE_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'warning',
                    rule_type TEXT NOT NULL,
                    pattern TEXT,
                    scope TEXT NOT NULL DEFAULT 'all',
                    ip_list TEXT,
                    methods TEXT,
                    path_prefix TEXT,
                    rate_limit INTEGER,
                    rate_window INTEGER,
                    action TEXT NOT NULL DEFAULT 'block',
                    status TEXT NOT NULL DEFAULT 'enabled',
                    priority INTEGER NOT NULL DEFAULT 100,
                    description TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    hit_count INTEGER NOT NULL DEFAULT 0,
                    last_hit_at TEXT
                )
            ''')
            conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {EVENT_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    rule_code TEXT,
                    target TEXT,
                    severity TEXT,
                    description TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    request_path TEXT,
                    request_method TEXT,
                    matched TEXT,
                    details TEXT,
                    timestamp TEXT
                )
            ''')
            conn.commit()
        return True
    except Exception as e:
        logger.warning(f"[ai_firewall] init table fail: {e}")
        return False


DEFAULT_SEED_RULES = [
    ('SQLI_001', 'SQL注入检测-基础语法', 'injection', 'critical', 'regex', SQLI_RE.pattern, 'param,path,body', None, None, None, None, None, 'block', 10, '常规 SQL 注入关键词和布尔盲注检测'),
    ('SQLI_002', 'SQL注入检测-敏感函数', 'injection', 'high', 'regex', SENSITIVE_WORDS_RE.pattern, 'param,body', None, None, None, None, None, 'block', 20, 'select * from users / @@version / into outfile 等高危语句'),
    ('XSS_001', '跨站脚本-script标签', 'xss', 'high', 'regex', XSS_RE.pattern, 'param,path,body', None, None, None, None, None, 'block', 30, 'script 标签 / onerror / onload / svg on* / javascript: 伪协议'),
    ('SSRF_001', '服务端请求伪造-内网/元数据', 'ssrf', 'critical', 'regex', SSRF_RE.pattern, 'param,body', None, None, None, None, None, 'block', 40, '访问 127/10/172.16/192.168/metadata/169.254 以及 file/gopher/dict 协议'),
    ('TRAV_001', '路径遍历与敏感文件', 'traversal', 'high', 'regex', PATH_TRAVERSAL_RE.pattern, 'path,param,body', None, None, None, None, None, 'block', 50, '../../.. 与 /etc/passwd / Windows system32 访问'),
    ('CMD_001', '命令注入与RCE载荷', 'rce', 'critical', 'regex', CMD_INJECT_RE.pattern, 'param,body', None, None, None, None, None, 'block', 60, '; | & $() ` 管道 + ls/cat/id/curl/wget/nc/bash 组合 / 管道下载执行'),
    ('UA_001', '恶意扫描器UA', 'scanner', 'warning', 'regex', MALICIOUS_UA_RE.pattern, 'header', None, None, None, None, None, 'block', 70, 'sqlmap/nmap/nikto/havij/nessus/masscan/dirbuster/wfuzz/hydra 等'),
    ('METHOD_001', 'HTTP方法白名单', 'protocol', 'low', 'method_whitelist', None, 'method', None, 'GET,POST,PUT,DELETE,PATCH,HEAD,OPTIONS', None, None, None, 'block', 80, '仅允许标准 HTTP 方法'),
    ('RATE_IP_001', '单IP每分钟请求上限', 'ratelimit', 'medium', 'rate', None, 'ip', None, None, None, 180, 60, 'block', 90, '单 IP 180 req/60s 触发拦截（可按实际调整）'),
    ('RATE_PATH_001', '登录接口速率限制', 'ratelimit', 'high', 'rate', None, 'path', None, None, '/api/auth/login', 10, 60, 'block', 95, '登录接口 10 次/分钟防暴力破解'),
    ('IP_BL_001', '全局IP黑名单（空，管理员可追加）', 'blacklist', 'high', 'ip_blacklist', None, 'ip', '', None, None, None, None, 'block', 110, '逗号分隔 IP/CIDR，命中即拦截（默认留空，管理员通过 API 维护）'),
    ('UA_BL_001', 'UA黑名单（空，管理员可追加）', 'blacklist', 'warning', 'ua_blacklist', None, 'header', None, None, None, None, None, 'block', 120, '逗号分隔 UA 子串黑名单（默认留空）'),
    ('BODY_SCAN', '请求体安全扫描（大正则）', 'injection', 'medium', 'regex', '', 'body', None, None, None, None, None, 'log', 130, '对 application/json / www-form-urlencoded 做组合扫描（仅记录）'),
    ('API_KEY_001', '防止明文硬编码 API Key', 'secleak', 'high', 'regex', r"(?i)(sk-[\w-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z\-_]{20,})", 'param,body,header', None, None, None, None, None, 'log', 140, '检测 OpenAI / GitHub / AWS / GCP 密钥（仅记录，便于事后审计）'),
    ('HDR_001', 'Host 头合法性检查', 'protocol', 'medium', 'regex', r"^\s*$", 'header', None, None, None, None, None, 'block', 150, 'Host 头为空时拦截（防 Host 头攻击）'),
    ('HDR_002', 'Content-Length 巨包防护', 'protocol', 'medium', 'header_maxlen', None, 'header', None, None, None, None, None, 'block', 160, 'Content-Length 超过 32MB 时拦截'),
    ('CSRF_001', 'Cookie 无 SameSite 提示（仅日志）', 'cookie', 'low', 'log_only', None, 'header', None, None, None, None, None, 'log', 170, '登录写 Cookie 时记录 SameSite 配置（不拦截）'),
    ('CORS_001', '非浏览器 Origin 告警（仅日志）', 'cors', 'low', 'log_only', None, 'header', None, None, None, None, None, 'log', 180, 'Origin 与 Host 不一致时记录（便于事后）'),
    ('FILE_001', '上传文件扩展名黑名单', 'upload', 'high', 'ext_blacklist', None, 'path,body', None, None, None, None, None, 'block', 190, '.php .phtml .jsp .asp .aspx .asa .cer .exe .vbs .ps1 .sh .cmd'),
    ('FILE_002', '上传文件 MIME 检查（仅日志）', 'upload', 'medium', 'log_only', None, 'header', None, None, None, None, None, 'log', 200, '上传时 Content-Type 与扩展不匹配则记录（不拦截）'),
    ('PATH_001', '常见后端管理路径探测', 'recon', 'medium', 'regex', r"(?i)(\.(env|git(ignore|/HEAD)?|svn|bak|old|sql|swp|ini|conf|log|yaml|yml|json)(\?|$)|/wp-(admin|login|content)|/phpmyadmin(?:/|$)|/adminer\.php|/cpanel(?:/|$)|/\.DS_Store|/\.htaccess|/\.htpasswd)", 'path', None, None, None, None, None, 'block', 210, '探测 git 泄露 / wp-admin / phpmyadmin / 备份文件 / env 等'),
    ('INFO_001', '敏感参数暴露告警（仅日志）', 'secleak', 'medium', 'regex', r"(?i)(password|passwd|pwd|token|secret|apikey|api_key|private[_-]?key)=", 'param,body,header', None, None, None, None, None, 'log', 220, '日志级敏感参数在 URL/Body 里被传入（只记录不拦截）'),
    ('BOT_001', '无头浏览器指纹拦截（默认disable，管理员可开）', 'bot', 'medium', 'regex', r"(?i)(headlesschrome|phantomjs|puppeteer|selenium|webdriver|cypress)", 'header', None, None, None, None, None, 'disabled', 230, '匹配无头 UA，默认关闭防止误伤正常浏览器'),
    ('GLOBAL_001', '全局请求审计日志（仅记录）', 'audit', 'low', 'log_only', None, 'all', None, None, None, None, None, 'log', 999, '所有请求（正常+异常）统一打事件表，便于 SIEM 接入'),

    # ===== 升级：新增高级威胁检测规则 =====
    ('XXE_001', 'XXE外部实体注入', 'injection', 'critical', 'regex', XXE_RE.pattern, 'param,body', None, None, None, None, None, 'block', 55, '检测XML外部实体注入：DOCTYPE/ENTITY/SYSTEM/参数实体'),
    ('SSTI_001', '服务端模板注入', 'injection', 'critical', 'regex', SSTI_RE.pattern, 'param,body', None, None, None, None, None, 'block', 56, 'Jinja2/Twig/FreeMarker SSTI：{{}}/{%%}/__class__/__subclasses__'),
    ('DESERIAL_001', '反序列化攻击载荷', 'injection', 'critical', 'regex', DESERIAL_RE.pattern, 'param,body', None, None, None, None, None, 'block', 57, 'PHP/Java反序列化：O:a:s:/__wakeup/ysoserial/JNDI'),
    ('SENSFILE_001', '敏感文件路径探测', 'recon', 'high', 'regex', SENSITIVE_FILE_RE.pattern, 'path,param,body', None, None, None, None, None, 'block', 58, '读取/proc/sys/.ssh/.env/.git/config等敏感路径'),
    ('CRLF_001', 'CRLF注入/HTTP请求走私', 'injection', 'high', 'regex', CRLF_RE.pattern, 'param,header', None, None, None, None, None, 'block', 65, 'CRLF注入：%0d%0a/双换行/Set-Cookie头注入'),
    ('REDIRECT_001', '开放重定向', 'redirect', 'high', 'regex', OPEN_REDIRECT_RE.pattern, 'param', None, None, None, None, None, 'block', 75, 'redirect_uri/next/return_url指向外部域名'),
    ('IDOR_001', '越权参数模式检测（仅日志）', 'auth', 'medium', 'regex', IDOR_RE.pattern, 'param,body', None, None, None, None, None, 'log', 85, '检测user_id=0/id=-1/admin=1/role=admin等越权模式'),
    ('GRAPHQL_001', 'GraphQL注入/内省', 'injection', 'high', 'regex', GRAPHQL_INJECT_RE.pattern, 'param,body', None, None, None, None, None, 'block', 95, '__schema/__type/introspection/batch GraphQL攻击'),
    ('NOSQL_001', 'NoSQL注入', 'injection', 'high', 'regex', NOSQL_INJECT_RE.pattern, 'param,body', None, None, None, None, None, 'block', 96, '$where/$ne/$gt/$regex等NoSQL注入操作符'),
    ('JWT_001', 'JWT令牌篡改（alg=none）', 'auth', 'critical', 'regex', JWT_RE.pattern, 'param,header', None, None, None, None, None, 'block', 97, '检测JWT alg=none攻击/降级签名算法'),
    ('RATE_LOGIN_002', '注册接口速率限制', 'ratelimit', 'high', 'rate', None, 'path', None, None, '/auth/register', 5, 60, 'block', 98, '注册接口 5 次/分钟防批量注册'),
    ('RATE_PWD_001', '密码重置接口速率限制', 'ratelimit', 'high', 'rate', None, 'path', None, None, '/auth/forgot_password', 3, 300, 'block', 99, '密码重置 3 次/5分钟防邮件轰炸'),
    ('RATE_API_001', 'API全局速率限制', 'ratelimit', 'medium', 'rate', None, 'path', None, None, '/api/', 300, 60, 'block', 100, '单IP对/api/路径 300次/分钟上限'),
    ('SQLI_003', 'SQL注入-时间盲注增强', 'injection', 'high', 'regex', r"(?i)(pg_sleep\s*\(\s*\d+\s*\)|SLEEP\s*\(\s*\d+\s*\)|WAITFOR\s+DELAY\s+'[^']+'|WAITFOR\s+TIME\s+'[^']+'|BENCHMARK\s*\(\s*\d+\s*,|GET_LOCK\s*\(|RELEASE_LOCK\s*\(|\bIF\s*\(\s*1\s*=\s*1\s*,\s*SLEEP\s*\(|\bCASE\s+WHEN\s+.*\s+THEN\s+.*\s+END\b)", 'param,body', None, None, None, None, None, 'block', 105, 'pg_sleep/SLEEP/WAITFOR/BENCHMARK时间盲注增强检测'),
    ('XSS_002', 'XSS-DOM注入增强', 'xss', 'high', 'regex', r"(?i)(innerHTML\s*=|outerHTML\s*=|document\.write\s*\(|document\.writeln\s*\(|\.innerHTML\s*=\s*[^;]+|location\.hash\s*\.|location\.search\s*\.|window\.name\s*[^=]*[<]|\.insertAdjacentHTML\s*\(|\.appendChild\s*\(\s*document\.create)", 'param,body', None, None, None, None, None, 'block', 108, 'DOM XSS：innerHTML/outerHTML/document.write/insertAdjacentHTML'),
]


def seed_default_firewall_rules(force_refresh=False):
    """幂等插入 24 条默认规则（按 rule_code 去重）；若规则存在则保留管理员改过的 action/status，仅补 description/category/severity"""
    init_firewall_tables()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ok = 0
    updated = 0
    try:
        with _conn() as conn:
            for (rule_code, name, category, severity, rule_type, pattern, scope, ip_list, methods,
                 path_prefix, rate_limit, rate_window, action, priority, description) in DEFAULT_SEED_RULES:
                row = conn.execute(f"SELECT id FROM {RULE_TABLE} WHERE rule_code=?", (rule_code,)).fetchone()
                if not row:
                    conn.execute(f'''
                        INSERT INTO {RULE_TABLE} (
                            rule_code,name,category,severity,rule_type,pattern,scope,ip_list,methods,
                            path_prefix,rate_limit,rate_window,action,status,priority,description,created_at,updated_at
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        rule_code, name, category, severity, rule_type, pattern, scope, ip_list or '', methods or '',
                        path_prefix or '', rate_limit or 0, rate_window or 0, action,
                        'disabled' if rule_code in ('BOT_001',) else 'enabled',
                        priority, description, now, now
                    ))
                    ok += 1
                elif force_refresh:
                    conn.execute(f'''
                        UPDATE {RULE_TABLE} SET name=?,category=?,severity=?,rule_type=?,pattern=?,scope=?,
                            ip_list=COALESCE(NULLIF(ip_list,''),?),
                            methods=COALESCE(NULLIF(methods,''),?),
                            path_prefix=COALESCE(NULLIF(path_prefix,''),?),
                            rate_limit=?,rate_window=?,priority=?,description=?,updated_at=?
                        WHERE rule_code=?
                    ''', (
                        name, category, severity, rule_type, pattern, scope,
                        ip_list or '', methods or '', path_prefix or '',
                        rate_limit or 0, rate_window or 0, priority, description, now,
                        rule_code
                    ))
                    updated += 1
            conn.commit()
    except Exception as e:
        logger.warning(f"[ai_firewall] seed fail: {e}")
        return -1
    logger.info(f"[ai_firewall] seed done: inserted={ok}, updated={updated}, total_expected={len(DEFAULT_SEED_RULES)}")
    return ok + updated


def load_rules(force=False):
    """规则缓存（默认 TTL 15 秒，避免每次请求查 DB）"""
    now_ts = time.time()
    if (not force) and RULE_CACHE['rules'] and (now_ts - RULE_CACHE['loaded_at'] < RULE_CACHE['ttl']):
        return RULE_CACHE['rules']
    try:
        with _conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM {RULE_TABLE} WHERE status='enabled' ORDER BY priority ASC"
            ).fetchall()
            RULE_CACHE['rules'] = [dict(r) for r in rows]
            RULE_CACHE['loaded_at'] = now_ts
    except Exception as e:
        logger.warning(f"[ai_firewall] load rules fail: {e}")
        RULE_CACHE['rules'] = []
    return RULE_CACHE['rules']


def _log_event(rule, request_obj=None, matched_snippet='', extra=None):
    """把命中写入 security_events_log"""
    try:
        if request_obj is None:
            ip, ua, path, method = '', '', '', ''
        else:
            from flask import request as _rq
            ip = _rq.headers.get('X-Forwarded-For', '').split(',')[0].strip() or _rq.remote_addr or ''
            ua = _rq.headers.get('User-Agent', '') or ''
            path = _rq.path or ''
            method = _rq.method or ''
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        severity = rule.get('severity') if rule else 'info'
        rule_code = rule.get('rule_code') if rule else ''
        desc = rule.get('description') if rule else 'global audit'
        with _conn() as conn:
            conn.execute(f'''
                INSERT INTO {EVENT_TABLE} (
                    event_type,rule_code,target,severity,description,
                    ip_address,user_agent,request_path,request_method,matched,details,timestamp
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                (rule or {}).get('category', 'audit') or 'audit',
                rule_code,
                (rule or {}).get('name', 'MTSCOS AI Firewall') or '',
                severity or 'info',
                desc or '',
                ip, ua, path, method,
                (matched_snippet or '')[:800],
                json.dumps(extra or {}, ensure_ascii=False)[:4000],
                ts,
            ))
            if rule and rule.get('id'):
                conn.execute(f"UPDATE {RULE_TABLE} SET hit_count=hit_count+1, last_hit_at=? WHERE id=?", (ts, rule['id']))
            conn.commit()
    except Exception as e:
        logger.warning(f"[ai_firewall] log event fail: {e}")


def _extract_inputs(request_obj):
    """把请求中的字符串（query/path/body/headers）拼成 {scope: text} dict 便于正则扫描"""
    try:
        path = request_obj.path or ''
        query_dict = request_obj.args.to_dict(flat=False) if request_obj.args else {}
        query_text = '\n'.join(f"{k}={';'.join(v if isinstance(v, list) else [v])}" for k, v in query_dict.items())
        headers = '\n'.join(f"{k}: {v}" for k, v in request_obj.headers.items() if k.lower() != 'cookie') or ''
        ua = request_obj.headers.get('User-Agent', '') or ''
        host = request_obj.headers.get('Host', '') or ''
        content_length = request_obj.headers.get('Content-Length')
        method = request_obj.method or ''
        body_text = ''
        ctype = request_obj.headers.get('Content-Type', '') or ''
        try:
            if request_obj.content_length and request_obj.content_length > 0 and request_obj.content_length < 8 * 1024 * 1024:
                if 'json' in ctype:
                    j = request_obj.get_json(silent=True)
                    if j is not None:
                        body_text = json.dumps(j, ensure_ascii=False)
                elif 'x-www-form-urlencoded' in ctype or 'multipart/form-data' in ctype:
                    fd = request_obj.form.to_dict(flat=False) if request_obj.form else {}
                    body_text = '\n'.join(f"{k}={';'.join(v if isinstance(v, list) else [v])}" for k, v in fd.items())
        except Exception:
            body_text = ''
        ip = (request_obj.headers.get('X-Forwarded-For', '').split(',')[0].strip() or request_obj.remote_addr or '').strip()
        return {
            'path': path,
            'param': query_text,
            'body': body_text,
            'header': headers,
            'ua': ua,
            'host': host,
            'method': method,
            'ip': ip,
            'content_length': int(content_length) if (content_length and content_length.isdigit()) else 0,
            'content_type': ctype,
        }
    except Exception as e:
        logger.warning(f"[ai_firewall] extract fail: {e}")
        return {
            'path': '', 'param': '', 'body': '', 'header': '',
            'ua': '', 'host': '', 'method': '', 'ip': '',
            'content_length': 0, 'content_type': ''
        }


def check_request(request_obj):
    """
    对进来的 request 跑所有启用规则。
    返回 tuple: (block_bool, status_code_int, message_str, matched_rule_dict_or_None)
    """
    rules = load_rules()
    data = _extract_inputs(request_obj)
    block_code = None
    block_msg = None
    matched_rule = None
    matched_snippet = ''

    for rule in rules:
        try:
            scope = (rule.get('scope') or 'all').lower()
            scopes = {s.strip() for s in scope.split(',')}
            if 'all' in scopes:
                scopes = {'path', 'param', 'body', 'header', 'ua', 'host', 'method', 'ip'}
            rt = (rule.get('rule_type') or '').lower()
            severity = rule.get('severity') or 'info'
            action = (rule.get('action') or 'block').lower()
            code = rule.get('rule_code') or ''
            matched_here = False
            snippet = ''

            if rt == 'regex' and rule.get('pattern'):
                combined_parts = []
                if 'path' in scopes: combined_parts.append(data['path'])
                if 'param' in scopes: combined_parts.append(data['param'])
                if 'body' in scopes: combined_parts.append(data['body'])
                if 'header' in scopes: combined_parts.append(data['header'])
                if 'ua' in scopes: combined_parts.append(data['ua'])
                if 'host' in scopes: combined_parts.append(data['host'])
                combined = '\n'.join(combined_parts)
                if not combined:
                    continue
                try:
                    comp = re.compile(rule['pattern'], re.I | re.S)
                except re.error:
                    comp = re.compile(re.escape(rule['pattern']), re.I | re.S)
                m = comp.search(combined)
                if m:
                    matched_here = True
                    snippet = (m.group(0) or '')[:200]
            elif rt == 'method_whitelist':
                methods = {x.strip().upper() for x in (rule.get('methods') or '').split(',') if x.strip()} or ALLOWED_METHODS
                if data['method'] and data['method'].upper() not in methods:
                    matched_here = True
                    snippet = f"method={data['method']} not in {sorted(methods)}"
            elif rt == 'header_maxlen':
                limit = 32 * 1024 * 1024
                if data['content_length'] and data['content_length'] > limit:
                    matched_here = True
                    snippet = f"content_length={data['content_length']} > {limit}"
            elif rt == 'ip_blacklist':
                ips = [x.strip() for x in (rule.get('ip_list') or '').split(',') if x.strip()]
                if data['ip'] and data['ip'] in ips:
                    matched_here = True
                    snippet = f"ip={data['ip']} in blacklist"
            elif rt == 'ua_blacklist':
                tokens = [x.strip().lower() for x in (rule.get('pattern') or '').split(',') if x.strip()]
                if tokens and data['ua']:
                    low = data['ua'].lower()
                    hit = next((t for t in tokens if t in low), None)
                    if hit:
                        matched_here = True
                        snippet = f"ua contains '{hit}'"
            elif rt == 'rate':
                now_ts = time.time()
                path_prefix = (rule.get('path_prefix') or '').strip()
                rl = rule.get('rate_limit') or 0
                rw = rule.get('rate_window') or 60
                if rl <= 0:
                    continue
                if path_prefix and not data['path'].startswith(path_prefix):
                    continue
                bucket_key = f"{code}:{data['ip']}:{path_prefix or '*'}"
                dq = IP_RATE_STATE[bucket_key]
                dq.append(now_ts)
                while dq and dq[0] < now_ts - rw:
                    dq.popleft()
                if len(dq) > rl:
                    matched_here = True
                    snippet = f"rate={len(dq)}/{rw}s limit={rl} key={bucket_key}"
            elif rt == 'ext_blacklist':
                forbidden = {'.php', '.phtml', '.jsp', '.asp', '.aspx', '.asa', '.cer', '.exe', '.vbs', '.ps1', '.sh', '.cmd', '.bat'}
                p = (data['path'] or '').lower()
                if any(p.endswith(ext) or (ext + '?') in p or (ext + '&') in p for ext in forbidden):
                    matched_here = True
                    snippet = f"path={data['path']} ends with forbidden extension"
            elif rt == 'log_only':
                matched_here = True
                snippet = f"log-only event, scope={rule.get('scope')}"
                if action == 'disabled':
                    continue
            elif rt == '':
                continue

            if matched_here:
                _log_event(rule, request_obj, matched_snippet=snippet, extra={
                    'ip': data['ip'], 'host': data['host'],
                    'ua_sha': hashlib.sha256((data['ua'] or '').encode()).hexdigest()[:12],
                    'ua_preview': (data['ua'] or '')[:120],
                    'cl': data['content_length'],
                    'ct': data['content_type'],
                })
                if action in ('block', 'deny', 'reject'):
                    if block_code is None:
                        matched_rule = rule
                        matched_snippet = snippet
                        block_code = 403 if severity in ('critical', 'high') else (429 if rt == 'rate' else 400)
                        block_msg = f"[MTSCOS AI Firewall] Blocked by rule {rule.get('rule_code')} ({rule.get('name')})"
                    # 高危：一旦命中一条 block 级就直接返回
                    if severity in ('critical',):
                        return True, block_code, block_msg, matched_rule

        except Exception as e:
            logger.warning(f"[ai_firewall] rule {rule.get('rule_code')} error: {e}")

    # GLOBAL_001：全局审计（无阻断） - 通过伪规则对象落表
    try:
        if RULE_CACHE['rules']:
            global_rule = next((r for r in RULE_CACHE['rules'] if r.get('rule_code') == 'GLOBAL_001' and (r.get('action') or '').lower() != 'disabled'), None)
            if global_rule and request_obj:
                # 每 64 条写一条（避免全局审计写爆）
                bk = f"GLOBAL_AUDIT_{datetime.now().minute // 2}_{hashlib.md5((data['ip'] or data['ua']).encode()).hexdigest()[:4]}"
                IP_RATE_STATE[bk].append(time.time())
                if len(IP_RATE_STATE[bk]) <= 1:
                    _log_event(global_rule, request_obj, matched_snippet='global_audit', extra={
                        'ip': data['ip'], 'ua_sha': hashlib.sha256((data['ua'] or '').encode()).hexdigest()[:12],
                        'method': data['method'], 'path': data['path'], 'cl': data['content_length'],
                    })
    except Exception:
        pass

    if block_code is not None:
        return True, block_code, (block_msg or '[MTSCOS AI Firewall] Request blocked'), matched_rule
    return False, 200, '', None


# ============== CRUD Helpers（供 API Blueprint 调用） ==============

def list_rules(keyword=None, category=None, status=None):
    try:
        q = f"SELECT * FROM {RULE_TABLE} WHERE 1=1"
        args = []
        if keyword:
            q += " AND (name LIKE ? OR rule_code LIKE ? OR description LIKE ?)"
            args.extend([f'%{keyword}%'] * 3)
        if category:
            q += " AND category=?"
            args.append(category)
        if status:
            q += " AND status=?"
            args.append(status)
        q += " ORDER BY priority ASC"
        with _conn() as conn:
            return [dict(r) for r in conn.execute(q, args).fetchall()]
    except Exception as e:
        logger.warning(f"[ai_firewall] list fail: {e}")
        return []


def get_rule(rule_id):
    try:
        with _conn() as conn:
            r = conn.execute(f"SELECT * FROM {RULE_TABLE} WHERE id=?", (rule_id,)).fetchone()
            return dict(r) if r else None
    except Exception:
        return None


def create_or_update_rule(rule_id=None, **kw):
    allowed = {
        'rule_code', 'name', 'category', 'severity', 'rule_type', 'pattern',
        'scope', 'ip_list', 'methods', 'path_prefix', 'rate_limit', 'rate_window',
        'action', 'status', 'priority', 'description'
    }
    data = {k: v for k, v in kw.items() if k in allowed}
    if not data:
        return None
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['updated_at'] = now
    try:
        with _conn() as conn:
            if rule_id:
                sets = ','.join(f"{k}=?" for k in data.keys())
                conn.execute(f"UPDATE {RULE_TABLE} SET {sets} WHERE id=?", list(data.values()) + [rule_id])
            else:
                data['created_at'] = now
                if not data.get('rule_code'):
                    data['rule_code'] = 'CUST_' + hashlib.md5((data.get('name') or '') + now).hexdigest()[:10].upper()
                cols = ','.join(data.keys())
                phs = ','.join(['?'] * len(data))
                conn.execute(f"INSERT INTO {RULE_TABLE}({cols}) VALUES({phs})", list(data.values()))
                rule_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.commit()
        RULE_CACHE['loaded_at'] = 0
        return get_rule(rule_id)
    except Exception as e:
        logger.warning(f"[ai_firewall] save fail: {e}")
        return None


def toggle_rule(rule_id, status):
    status = 'enabled' if str(status).lower() in ('1', 'true', 'enable', 'enabled') else 'disabled'
    return create_or_update_rule(rule_id, status=status)


def delete_rule(rule_id):
    try:
        with _conn() as conn:
            conn.execute(f"DELETE FROM {RULE_TABLE} WHERE id=?", (rule_id,))
            conn.commit()
        RULE_CACHE['loaded_at'] = 0
        return True
    except Exception:
        return False


def list_events(limit=100, rule_code=None, severity=None):
    try:
        q = f"SELECT * FROM {EVENT_TABLE} WHERE 1=1"
        args = []
        if rule_code:
            q += " AND rule_code=?"
            args.append(rule_code)
        if severity:
            q += " AND severity=?"
            args.append(severity)
        q += " ORDER BY id DESC LIMIT ?"
        args.append(int(limit))
        with _conn() as conn:
            return [dict(r) for r in conn.execute(q, args).fetchall()]
    except Exception as e:
        logger.warning(f"[ai_firewall] list events fail: {e}")
        return []


def stats_summary():
    try:
        with _conn() as conn:
            total_rules = conn.execute(f"SELECT COUNT(*) FROM {RULE_TABLE}").fetchone()[0]
            enabled = conn.execute(f"SELECT COUNT(*) FROM {RULE_TABLE} WHERE status='enabled'").fetchone()[0]
            total_hits = conn.execute(f"SELECT COALESCE(SUM(hit_count),0) FROM {RULE_TABLE}").fetchone()[0]
            total_events = conn.execute(f"SELECT COUNT(*) FROM {EVENT_TABLE}").fetchone()[0]
            last_24h_events = conn.execute(
                f"SELECT COUNT(*) FROM {EVENT_TABLE} WHERE timestamp >= datetime('now','-24 hours')"
            ).fetchone()[0]
            by_severity = dict(conn.execute(
                f"SELECT COALESCE(severity,'info') s, COUNT(*) c FROM {EVENT_TABLE} GROUP BY s"
            ).fetchall())
            top_rules = [dict(r) for r in conn.execute(
                f"SELECT rule_code,name,category,severity,hit_count,last_hit_at FROM {RULE_TABLE} ORDER BY hit_count DESC LIMIT 10"
            ).fetchall()]
            return {
                'total_rules': total_rules, 'enabled_rules': enabled,
                'total_hits': int(total_hits), 'total_events': total_events,
                'last_24h_events': last_24h_events,
                'events_by_severity': by_severity,
                'top_hit_rules': top_rules,
            }
    except Exception as e:
        logger.warning(f"[ai_firewall] stats fail: {e}")
        return {}
