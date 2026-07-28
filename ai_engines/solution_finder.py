# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
解决方案搜索器
从网络中搜索安全问题的解决方案和修复方法
"""

import os
import json
import uuid
import sqlite3
import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

SOLUTION_SOURCES = [
    {'name': 'OWASP', 'url': 'https://owasp.org/', 'type': 'security'},
    {'name': 'CVE', 'url': 'https://cve.mitre.org/', 'type': 'security'},
    {'name': 'NIST', 'url': 'https://www.nist.gov/', 'type': 'security'},
    {'name': 'GitHub Security', 'url': 'https://github.com/security', 'type': 'security'},
    {'name': 'Python Security', 'url': 'https://docs.python.org/3/library/security.html', 'type': 'python'},
    {'name': 'Flask Security', 'url': 'https://flask.palletsprojects.com/en/latest/security/', 'type': 'flask'},
    {'name': 'SQLite Security', 'url': 'https://www.sqlite.org/security.html', 'type': 'database'}
]

ISSUE_SOLUTIONS_DB = {
    'hardcoded_credentials': {
        'title': '硬编码凭证解决方案',
        'solutions': [
            '将敏感凭证移至环境变量',
            '使用配置文件管理敏感信息，确保配置文件不在版本控制中',
            '使用密钥管理服务（如AWS KMS、HashiCorp Vault）',
            '定期轮换敏感凭证',
            '使用加密存储敏感数据'
        ],
        'references': ['OWASP Top 10', 'CWE-798']
    },
    'code_execution': {
        'title': '代码执行漏洞解决方案',
        'solutions': [
            '禁止使用exec()和eval()函数',
            '使用ast.literal_eval()替代eval()',
            '对所有输入进行严格验证和过滤',
            '使用白名单机制限制可执行代码',
            '实施代码审查流程'
        ],
        'references': ['OWASP Top 10', 'CWE-94']
    },
    'command_injection': {
        'title': '命令注入漏洞解决方案',
        'solutions': [
            '使用subprocess时指定shell=False',
            '使用绝对路径执行命令',
            '对所有输入进行白名单验证',
            '避免拼接命令字符串',
            '使用参数化命令执行'
        ],
        'references': ['OWASP Top 10', 'CWE-78']
    },
    'deserialization': {
        'title': '反序列化漏洞解决方案',
        'solutions': [
            '避免使用pickle序列化敏感数据',
            '使用JSON替代pickle',
            '实施严格的输入验证',
            '使用安全的序列化库',
            '对反序列化数据进行签名验证'
        ],
        'references': ['OWASP Top 10', 'CWE-502']
    },
    'sql_injection': {
        'title': 'SQL注入漏洞解决方案',
        'solutions': [
            '使用参数化查询（Prepared Statements）',
            '使用ORM框架（如SQLAlchemy）',
            '对用户输入进行严格验证和转义',
            '实施最小权限原则',
            '使用WAF（Web应用防火墙）'
        ],
        'references': ['OWASP Top 10', 'CWE-89']
    },
    'xss': {
        'title': '跨站脚本攻击解决方案',
        'solutions': [
            '对所有输出进行HTML转义',
            '使用Content Security Policy (CSP)',
            '使用安全的模板引擎',
            '对用户输入进行严格验证',
            '设置HttpOnly和Secure Cookie标志'
        ],
        'references': ['OWASP Top 10', 'CWE-79']
    },
    'csrf': {
        'title': '跨站请求伪造解决方案',
        'solutions': [
            '实施CSRF Token验证',
            '使用SameSite Cookie属性',
            '验证请求来源',
            '使用双重提交Cookie',
            '实施Referer头验证'
        ],
        'references': ['OWASP Top 10', 'CWE-352']
    },
    'debug_enabled': {
        'title': '调试模式开启解决方案',
        'solutions': [
            '生产环境禁用DEBUG模式',
            '设置DEBUG=False',
            '使用环境变量控制调试模式',
            '实施访问控制限制调试接口',
            '定期检查配置文件'
        ],
        'references': ['OWASP Configuration', 'CWE-489']
    },
    'weak_secret_key': {
        'title': '弱密钥解决方案',
        'solutions': [
            '使用至少32位的随机SECRET_KEY',
            '使用os.urandom()生成密钥',
            '定期轮换密钥',
            '将密钥存储在安全位置',
            '使用密钥派生函数'
        ],
        'references': ['OWASP Security', 'CWE-326']
    },
    'http_port_open': {
        'title': 'HTTP端口开放解决方案',
        'solutions': [
            '使用HTTPS替代HTTP',
            '配置SSL/TLS证书',
            '强制HTTPS重定向',
            '关闭不必要的HTTP端口',
            '使用HSTS头'
        ],
        'references': ['OWASP Transport Layer Protection', 'CWE-319']
    },
    'env_file': {
        'title': '环境变量文件解决方案',
        'solutions': [
            '将.env文件添加到.gitignore',
            '设置文件权限为仅所有者可读',
            '使用环境变量管理敏感配置',
            '使用配置管理工具',
            '定期审查.env文件内容'
        ],
        'references': ['OWASP Configuration', 'CWE-526']
    },
    'db_permissions': {
        'title': '数据库权限解决方案',
        'solutions': [
            '限制数据库文件权限为600',
            '实施最小权限原则',
            '使用专用数据库用户',
            '定期审查权限设置',
            '加密数据库连接'
        ],
        'references': ['OWASP Database Security', 'CWE-276']
    }
}

class SolutionFinder:
    """解决方案搜索器"""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'issue_solutions.db')
        self._create_tables()
        self.solutions = {}

    def _create_tables(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issue_solutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    solution_id TEXT UNIQUE,
                    issue_id TEXT,
                    finding_id TEXT,
                    category TEXT,
                    severity TEXT,
                    title TEXT,
                    solutions TEXT,
                    ref_links TEXT,
                    source TEXT,
                    searched_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_id TEXT UNIQUE,
                    search_query TEXT,
                    results_count INTEGER,
                    success BOOLEAN,
                    searched_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("[SolutionFinder] 数据库表创建完成")

    def find_solution(self, issue: Dict) -> Dict[str, Any]:
        """为问题搜索解决方案"""
        logger.info(f"[SolutionFinder] 搜索问题解决方案: {issue['category']}")
        
        category = issue.get('category', 'unknown')
        solution_id = f"sol_{uuid.uuid4().hex[:8]}"
        
        if category in ISSUE_SOLUTIONS_DB:
            db_solution = ISSUE_SOLUTIONS_DB[category]
            solution = {
                'solution_id': solution_id,
                'issue_id': issue.get('issue_id', ''),
                'finding_id': issue.get('finding_id', ''),
                'category': category,
                'severity': issue.get('severity', 'medium'),
                'title': db_solution['title'],
                'solutions': db_solution['solutions'],
                'references': db_solution['references'],
                'source': 'knowledge_base',
                'searched_at': datetime.now().isoformat(),
                'search_query': f"{category} security fix solution"
            }
            
            self._save_solution(solution)
            self.solutions[solution_id] = solution
            
            logger.info(f"[SolutionFinder] 从知识库找到解决方案: {solution['title']}")
            return solution
        
        web_solution = self._search_web(category, issue)
        if web_solution:
            web_solution['solution_id'] = solution_id
            web_solution['issue_id'] = issue.get('issue_id', '')
            web_solution['finding_id'] = issue.get('finding_id', '')
            web_solution['searched_at'] = datetime.now().isoformat()
            
            self._save_solution(web_solution)
            self.solutions[solution_id] = web_solution
            
            return web_solution
        
        return {
            'solution_id': solution_id,
            'issue_id': issue.get('issue_id', ''),
            'finding_id': issue.get('finding_id', ''),
            'category': category,
            'severity': issue.get('severity', 'medium'),
            'title': f"{category}解决方案",
            'solutions': ['暂无具体解决方案，请参考通用安全最佳实践'],
            'references': [],
            'source': 'fallback',
            'searched_at': datetime.now().isoformat()
        }

    def _search_web(self, category: str, issue: Dict) -> Optional[Dict]:
        """从网络搜索解决方案"""
        logger.info(f"[SolutionFinder] 从网络搜索: {category}")
        
        search_query = f"{category} security vulnerability fix python flask"
        
        try:
            time.sleep(random.uniform(1, 3))
            
            mock_results = self._generate_mock_solution(category)
            if mock_results:
                self._log_search(search_query, len(mock_results['solutions']), True)
                return mock_results
            
            self._log_search(search_query, 0, False)
        except Exception as e:
            logger.error(f"[SolutionFinder] 网络搜索失败: {e}")
            self._log_search(search_query, 0, False)
        
        return None

    def _generate_mock_solution(self, category: str) -> Optional[Dict]:
        """生成模拟解决方案（实际环境中调用真实搜索）"""
        general_solutions = {
            'default': {
                'title': f"{category}安全问题解决方案",
                'solutions': [
                    '实施最小权限原则',
                    '对输入进行严格验证',
                    '使用参数化查询防止注入攻击',
                    '定期更新依赖库',
                    '实施安全代码审查',
                    '启用安全日志记录',
                    '配置Web应用防火墙',
                    '定期执行安全扫描'
                ],
                'references': ['OWASP', 'CWE'],
                'source': 'web_search'
            }
        }
        
        return general_solutions.get('default')

    def _log_search(self, query: str, count: int, success: bool):
        """记录搜索历史"""
        try:
            search_id = f"search_{uuid.uuid4().hex[:8]}"
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO solution_history (search_id, search_query, results_count, success)
                    VALUES (?, ?, ?, ?)
                ''', (search_id, query, count, success))
                conn.commit()
        except Exception as e:
            logger.error(f"[SolutionFinder] 记录搜索历史失败: {e}")

    def _save_solution(self, solution: Dict):
        """保存解决方案到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO issue_solutions 
                    (solution_id, issue_id, finding_id, category, severity, title, 
                     solutions, ref_links, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    solution['solution_id'],
                    solution['issue_id'],
                    solution['finding_id'],
                    solution['category'],
                    solution['severity'],
                    solution['title'],
                    json.dumps(solution['solutions'], ensure_ascii=False),
                    json.dumps(solution.get('references', []), ensure_ascii=False),
                    solution.get('source', 'unknown')
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[SolutionFinder] 保存解决方案失败: {e}")

    def find_solutions_batch(self, issues: List[Dict]) -> List[Dict]:
        """批量搜索解决方案"""
        logger.info(f"[SolutionFinder] 批量搜索 {len(issues)} 个问题的解决方案...")
        
        solutions = []
        for issue in issues:
            solution = self.find_solution(issue)
            solutions.append(solution)
        
        logger.info(f"[SolutionFinder] 批量搜索完成，找到 {len(solutions)} 个解决方案")
        return solutions

    def get_solution_by_issue_id(self, issue_id: str) -> Optional[Dict]:
        """根据问题ID获取解决方案"""
        for solution in self.solutions.values():
            if solution.get('issue_id') == issue_id:
                return solution
        return None

    def get_all_solutions(self) -> List[Dict]:
        """获取所有解决方案"""
        return list(self.solutions.values())

    def get_solutions_by_severity(self, severity: str) -> List[Dict]:
        """按危险等级获取解决方案"""
        return [s for s in self.solutions.values() if s.get('severity') == severity]