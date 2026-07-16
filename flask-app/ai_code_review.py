#!/usr/bin/env python3
"""
MTSCOS AI 代码审查服务 (v14.6.0)
==================================
基于静态分析和规则的代码审查引擎，支持多语言代码质量评估。

核心能力：
1. 多语言支持 - Python/JavaScript/HTML/CSS/SQL
2. 静态分析 - 语法/复杂度/重复/安全
3. 安全扫描 - SQL注入/XSS/硬编码密钥/危险函数
4. 代码规范 - PEP8 风格检查（基础版）
5. 复杂度分析 - 圈复杂度/函数长度/参数数量
6. 重复检测 - 代码块重复识别
7. 评分系统 - 综合质量评分（0-100）
8. 修复建议 - 自动生成改进建议
"""
import os
import re
import json
import sqlite3
import random
import logging
import ast
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_code_review.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AICodeReview')


# ========== 安全规则 ==========

SECURITY_PATTERNS = [
    {
        'id': 'SEC-001',
        'name': 'SQL 注入风险',
        'severity': 'critical',
        'pattern': r'execute\s*\(\s*["\'].*SELECT|INSERT|UPDATE|DELETE.*["\'].*\+|%s.*%|format\s*\(',
        'description': '检测到可能的 SQL 字符串拼接，存在注入风险',
        'suggestion': '使用参数化查询替代字符串拼接',
        'languages': ['python', 'javascript'],
    },
    {
        'id': 'SEC-002',
        'name': '硬编码密钥',
        'severity': 'high',
        'pattern': r'(password|passwd|pwd|secret|api_key|apikey|access_key|token)\s*=\s*["\'][^"\']{6,}["\']',
        'description': '检测到硬编码的密钥或密码',
        'suggestion': '从环境变量或密钥管理服务读取',
        'languages': ['python', 'javascript'],
    },
    {
        'id': 'SEC-003',
        'name': 'eval 函数使用',
        'severity': 'high',
        'pattern': r'\beval\s*\(',
        'description': '使用 eval 函数存在代码注入风险',
        'suggestion': '使用 ast.literal_eval 或避免动态执行',
        'languages': ['python', 'javascript'],
    },
    {
        'id': 'SEC-004',
        'name': 'exec 函数使用',
        'severity': 'high',
        'pattern': r'\bexec\s*\(',
        'description': '使用 exec 函数存在代码注入风险',
        'suggestion': '避免动态执行代码',
        'languages': ['python'],
    },
    {
        'id': 'SEC-005',
        'name': 'XSS 反射风险',
        'severity': 'high',
        'pattern': r'innerHTML\s*=|document\.write\s*\(',
        'description': '直接操作 innerHTML 或 document.write 可能导致 XSS',
        'suggestion': '使用 textContent 或对内容进行转义',
        'languages': ['javascript'],
    },
    {
        'id': 'SEC-006',
        'name': 'shell=True 风险',
        'severity': 'high',
        'pattern': r'subprocess\..*shell\s*=\s*True',
        'description': 'subprocess 使用 shell=True 存在命令注入风险',
        'suggestion': '使用列表参数避免 shell=True',
        'languages': ['python'],
    },
    {
        'id': 'SEC-007',
        'name': 'pickle 反序列化',
        'severity': 'high',
        'pattern': r'pickle\.loads?\s*\(',
        'description': 'pickle 反序列化存在远程代码执行风险',
        'suggestion': '使用 JSON 等安全格式',
        'languages': ['python'],
    },
    {
        'id': 'SEC-008',
        'name': '弱密码哈希',
        'severity': 'medium',
        'pattern': r'hashlib\.md5\s*\(|hashlib\.sha1\s*\(',
        'description': '使用弱哈希算法（MD5/SHA1）',
        'suggestion': '使用 SHA-256 或更强的算法',
        'languages': ['python'],
    },
    {
        'id': 'SEC-009',
        'name': 'TLS 验证禁用',
        'severity': 'high',
        'pattern': r'verify\s*=\s*False|CERT_NONE|ssl\._create_unverified_context',
        'description': '禁用 TLS 证书验证',
        'suggestion': '始终启用证书验证',
        'languages': ['python'],
    },
    {
        'id': 'SEC-010',
        'name': '调试模式开启',
        'severity': 'medium',
        'pattern': r'debug\s*=\s*True|DEBUG\s*=\s*True',
        'description': '生产环境开启调试模式可能泄露信息',
        'suggestion': '生产环境关闭调试模式',
        'languages': ['python', 'javascript'],
    },
]


# ========== 代码规范规则 ==========

STYLE_PATTERNS = [
    {
        'id': 'STYLE-001',
        'name': '行过长',
        'severity': 'low',
        'check': lambda lines: [
            {'line': i + 1, 'message': f'行长度 {len(line)} 超过 120 字符'}
            for i, line in enumerate(lines)
            if len(line) > 120
        ]
    },
    {
        'id': 'STYLE-002',
        'name': '尾随空格',
        'severity': 'low',
        'check': lambda lines: [
            {'line': i + 1, 'message': '存在尾随空格'}
            for i, line in enumerate(lines)
            if line != line.rstrip() and line.strip()
        ]
    },
    {
        'id': 'STYLE-003',
        'name': '混合缩进',
        'severity': 'medium',
        'check': lambda lines: [
            {'line': i + 1, 'message': '混合使用空格和 Tab 缩进'}
            for i, line in enumerate(lines)
            if '\t' in line and '    ' in line[:8]
        ]
    },
    {
        'id': 'STYLE-004',
        'name': 'TODO/FIXME 注释',
        'severity': 'low',
        'check': lambda lines: [
            {'line': i + 1, 'message': f'存在 TODO/FIXME 注释: {line.strip()[:80]}'}
            for i, line in enumerate(lines)
            if re.search(r'#\s*(TODO|FIXME|HACK|XXX)', line, re.IGNORECASE)
        ]
    },
]


# ========== 复杂度分析 ==========

def analyze_python_complexity(code: str) -> Dict:
    """分析 Python 代码复杂度"""
    result = {
        'functions': [],
        'classes': [],
        'max_complexity': 0,
        'avg_complexity': 0,
        'total_functions': 0
    }

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {'error': f'语法错误: {e}'}

    complexities = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 计算圈复杂度（基于分支点）
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1

            args_count = len(node.args.args)
            line_count = (node.end_lineno or node.lineno) - node.lineno + 1 if hasattr(node, 'end_lineno') else 0

            result['functions'].append({
                'name': node.name,
                'line': node.lineno,
                'complexity': complexity,
                'args_count': args_count,
                'line_count': line_count
            })
            result['total_functions'] += 1
            complexities.append(complexity)

            if complexity > result['max_complexity']:
                result['max_complexity'] = complexity

        elif isinstance(node, ast.ClassDef):
            methods = sum(1 for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
            result['classes'].append({
                'name': node.name,
                'line': node.lineno,
                'methods': methods
            })

    if complexities:
        result['avg_complexity'] = round(sum(complexities) / len(complexities), 2)

    return result


# ========== 重复代码检测 ==========

def detect_duplicates(lines: List[str], min_lines: int = 6) -> List[Dict]:
    """检测重复代码块"""
    duplicates = []
    n = len(lines)
    seen_blocks = {}

    for i in range(n - min_lines + 1):
        block = '\n'.join(line.strip() for line in lines[i:i + min_lines] if line.strip())
        if len(block) < 30:  # 太短忽略
            continue
        block_hash = hashlib.md5(block.encode('utf-8')).hexdigest()

        if block_hash in seen_blocks:
            duplicates.append({
                'block_start': i + 1,
                'original_start': seen_blocks[block_hash],
                'lines': min_lines,
                'preview': block[:100]
            })
        else:
            seen_blocks[block_hash] = i + 1

    return duplicates


import hashlib


# ========== 代码审查引擎 ==========

class AICodeReview:
    """AI 代码审查服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_code_reviews (
                        review_id TEXT PRIMARY KEY,
                        file_path TEXT,
                        language TEXT,
                        line_count INTEGER,
                        score INTEGER,
                        grade TEXT,
                        issues TEXT,
                        metrics TEXT,
                        suggestions TEXT,
                        created_at TEXT,
                        reviewed_by TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_file ON ai_code_reviews(file_path)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化代码审查数据库失败: {e}")

    # ========== 审查执行 ==========

    def review_code(self, code: str, language: str = 'python', file_path: str = '',
                   reviewed_by: str = 'system') -> Dict:
        """审查代码"""
        review_id = f"CR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        lines = code.split('\n')
        line_count = len(lines)
        issues = []
        suggestions = []

        # 1. 安全扫描
        security_issues = self._scan_security(code, language)
        issues.extend(security_issues)

        # 2. 风格检查
        style_issues = self._check_style(lines)
        issues.extend(style_issues)

        # 3. 复杂度分析
        complexity = {}
        if language == 'python':
            complexity = analyze_python_complexity(code)
            # 高复杂度函数标记
            for func in complexity.get('functions', []):
                if func['complexity'] > 10:
                    issues.append({
                        'type': 'complexity',
                        'severity': 'medium',
                        'line': func['line'],
                        'message': f"函数 {func['name']} 圈复杂度过高 ({func['complexity']})",
                        'suggestion': '考虑拆分函数'
                    })
                if func['line_count'] > 50:
                    issues.append({
                        'type': 'length',
                        'severity': 'low',
                        'line': func['line'],
                        'message': f"函数 {func['name']} 行数较多 ({func['line_count']})",
                        'suggestion': '考虑拆分为更小的函数'
                    })
                if func['args_count'] > 5:
                    issues.append({
                        'type': 'args',
                        'severity': 'low',
                        'line': func['line'],
                        'message': f"函数 {func['name']} 参数过多 ({func['args_count']})",
                        'suggestion': '考虑使用参数对象'
                    })

        # 4. 重复代码检测
        duplicates = detect_duplicates(lines)
        for dup in duplicates:
            issues.append({
                'type': 'duplicate',
                'severity': 'medium',
                'line': dup['block_start'],
                'message': f"检测到重复代码块（与第 {dup['original_start']} 行重复）",
                'suggestion': '提取为公共函数'
            })

        # 5. 计算评分
        score, grade = self._compute_score(issues, line_count)

        # 6. 生成建议
        suggestions = self._generate_suggestions(issues, complexity, line_count)

        metrics = {
            'line_count': line_count,
            'issue_count': len(issues),
            'critical_count': sum(1 for i in issues if i['severity'] == 'critical'),
            'high_count': sum(1 for i in issues if i['severity'] == 'high'),
            'medium_count': sum(1 for i in issues if i['severity'] == 'medium'),
            'low_count': sum(1 for i in issues if i['severity'] == 'low'),
            'complexity': complexity,
            'duplicates': len(duplicates)
        }

        # 保存审查记录
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_code_reviews
                    (review_id, file_path, language, line_count, score, grade,
                     issues, metrics, suggestions, created_at, reviewed_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    review_id, file_path, language, line_count, score, grade,
                    json.dumps(issues, ensure_ascii=False),
                    json.dumps(metrics, ensure_ascii=False),
                    json.dumps(suggestions, ensure_ascii=False),
                    datetime.now().isoformat(), reviewed_by
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存审查记录失败: {e}")

        return {
            'success': True,
            'review_id': review_id,
            'score': score,
            'grade': grade,
            'issues': issues,
            'metrics': metrics,
            'suggestions': suggestions
        }

    def review_file(self, file_path: str, language: str = None, reviewed_by: str = 'system') -> Dict:
        """审查文件"""
        if not os.path.exists(file_path):
            return {'success': False, 'error': '文件不存在'}

        # 自动检测语言
        if not language:
            ext = os.path.splitext(file_path)[1].lower()
            lang_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'javascript',
                '.html': 'html', '.css': 'css', '.sql': 'sql'
            }
            language = lang_map.get(ext, 'unknown')
            if language == 'unknown':
                return {'success': False, 'error': f'不支持的语言: {ext}'}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return self.review_code(code, language, file_path, reviewed_by)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _scan_security(self, code: str, language: str) -> List[Dict]:
        """安全扫描"""
        issues = []
        for pattern_def in SECURITY_PATTERNS:
            if language not in pattern_def['languages']:
                continue
            matches = re.finditer(pattern_def['pattern'], code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_no = code[:match.start()].count('\n') + 1
                issues.append({
                    'type': 'security',
                    'rule_id': pattern_def['id'],
                    'severity': pattern_def['severity'],
                    'line': line_no,
                    'message': pattern_def['description'],
                    'suggestion': pattern_def['suggestion']
                })
        return issues

    def _check_style(self, lines: List[str]) -> List[Dict]:
        """风格检查"""
        issues = []
        for style_def in STYLE_PATTERNS:
            results = style_def['check'](lines)
            for r in results:
                issues.append({
                    'type': 'style',
                    'rule_id': style_def['id'],
                    'severity': style_def['severity'],
                    'line': r['line'],
                    'message': r['message'],
                    'suggestion': '遵循代码规范'
                })
        return issues

    def _compute_score(self, issues: List[Dict], line_count: int) -> Tuple[int, str]:
        """计算代码质量评分"""
        base_score = 100
        # 按严重程度扣分
        severity_weights = {'critical': 25, 'high': 15, 'medium': 8, 'low': 3}
        for issue in issues:
            base_score -= severity_weights.get(issue['severity'], 5)

        # 按行数归一化（小文件更严格）
        if line_count > 0:
            density_penalty = (len(issues) / line_count) * 20
            base_score -= density_penalty

        score = max(0, min(100, int(base_score)))

        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'

        return score, grade

    def _generate_suggestions(self, issues: List[Dict], complexity: Dict,
                             line_count: int) -> List[Dict]:
        """生成改进建议"""
        suggestions = []

        critical = [i for i in issues if i['severity'] == 'critical']
        high = [i for i in issues if i['severity'] == 'high']
        duplicates = [i for i in issues if i['type'] == 'duplicate']

        if critical:
            suggestions.append({
                'priority': 'urgent',
                'category': 'security',
                'message': f'发现 {len(critical)} 个严重安全问题，必须立即修复',
                'items': [i['message'] for i in critical[:5]]
            })

        if high:
            suggestions.append({
                'priority': 'high',
                'category': 'security',
                'message': f'发现 {len(high)} 个高风险问题，建议尽快修复',
                'items': [i['message'] for i in high[:5]]
            })

        if complexity.get('max_complexity', 0) > 10:
            suggestions.append({
                'priority': 'medium',
                'category': 'refactor',
                'message': f"最高圈复杂度 {complexity['max_complexity']}，建议重构复杂函数",
                'items': [f"{f['name']} (复杂度: {f['complexity']})" for f in complexity.get('functions', []) if f['complexity'] > 10][:5]
            })

        if duplicates:
            suggestions.append({
                'priority': 'medium',
                'category': 'refactor',
                'message': f'发现 {len(duplicates)} 处重复代码，建议提取公共方法'
            })

        style_count = sum(1 for i in issues if i['type'] == 'style')
        if style_count > 5:
            suggestions.append({
                'priority': 'low',
                'category': 'style',
                'message': f'发现 {style_count} 个风格问题，建议格式化代码'
            })

        if not suggestions:
            suggestions.append({
                'priority': 'info',
                'category': 'general',
                'message': '代码质量良好，未发现明显问题'
            })

        return suggestions

    # ========== 查询统计 ==========

    def get_review(self, review_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_code_reviews WHERE review_id = ?', (review_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'review_id': row[0], 'file_path': row[1], 'language': row[2],
                    'line_count': row[3], 'score': row[4], 'grade': row[5],
                    'issues': json.loads(row[6]) if row[6] else [],
                    'metrics': json.loads(row[7]) if row[7] else {},
                    'suggestions': json.loads(row[8]) if row[8] else [],
                    'created_at': row[9], 'reviewed_by': row[10]
                }
        except Exception:
            return None

    def list_reviews(self, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT review_id, file_path, language, line_count, score, grade, created_at
                    FROM ai_code_reviews
                    ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
                return [
                    {
                        'review_id': r[0], 'file_path': r[1], 'language': r[2],
                        'line_count': r[3], 'score': r[4], 'grade': r[5], 'created_at': r[6]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_code_reviews')
                total_reviews = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(score) FROM ai_code_reviews')
                avg_score = cursor.fetchone()[0] or 0
                cursor.execute('SELECT grade, COUNT(*) FROM ai_code_reviews GROUP BY grade')
                grade_dist = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'total_reviews': total_reviews,
                    'avg_score': round(avg_score, 2),
                    'grade_distribution': grade_dist
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    reviewer = AICodeReview()

    test_code = '''
import os
import pickle

password = "hardcoded_secret_12345"

def complex_function(a, b, c, d, e, f, g):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return a + b + c + d + e
    return None

def query_user(user_id):
    sql = "SELECT * FROM users WHERE id = " + user_id
    return execute(sql)

def load_data(data):
    return pickle.loads(data)

eval("print('hello')")
'''

    print("代码审查测试:")
    result = reviewer.review_code(test_code, language='python', file_path='test.py')
    print(f"评分: {result['score']}/100 ({result['grade']})")
    print(f"问题数: {len(result['issues'])}")
    print(f"统计: {result['metrics']['critical_count']} critical, {result['metrics']['high_count']} high")
    print("\n建议:")
    for s in result['suggestions']:
        print(f"  [{s['priority']}] {s['message']}")

    print(f"\n审查历史: {reviewer.get_statistics()}")
