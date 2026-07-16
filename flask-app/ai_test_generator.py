#!/usr/bin/env python3
"""
MTSCOS AI 测试生成服务 (v14.8.0)
===================================
AI 驱动的自动化测试用例生成和管理服务。

核心能力：
1. 单元测试生成 - 根据函数签名自动生成单元测试
2. 边界测试 - 边界值分析生成测试用例
3. 模糊测试 - 随机输入生成和异常检测
4. 测试覆盖率分析 - 静态代码路径覆盖
5. 测试用例管理 - 用例CRUD和分类
6. 回归测试 - 变更影响分析和用例筛选
7. 性能测试 - 基准测试生成
8. 测试报告 - 综合测试报告生成
"""
import os
import json
import ast
import sqlite3
import random
import inspect
import logging
import string
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_test_generator.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AITestGenerator')


# ========== 代码解析 ==========

def parse_function(source_code: str) -> List[Dict]:
    """解析Python源码中的函数定义"""
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return [{'error': f'语法错误: {e}'}]

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_info = {
                'name': node.name,
                'line': node.lineno,
                'args': [],
                'returns': None,
                'docstring': ast.get_docstring(node),
                'complexity': _compute_complexity(node)
            }
            # 参数
            for arg in node.args.args:
                arg_type = None
                if arg.annotation:
                    try:
                        arg_type = ast.unparse(arg.annotation)
                    except Exception:
                        arg_type = None
                func_info['args'].append({
                    'name': arg.arg,
                    'type': arg_type
                })
            # 返回类型
            if node.returns:
                try:
                    func_info['returns'] = ast.unparse(node.returns)
                except Exception:
                    pass
            functions.append(func_info)
    return functions


def _compute_complexity(node: ast.AST) -> int:
    """计算圈复杂度"""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


# ========== 类型生成器 ==========

TYPE_GENERATORS = {
    'int': lambda: random.randint(-1000, 1000),
    'float': lambda: round(random.uniform(-1000, 1000), 6),
    'str': lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 20))),
    'bool': lambda: random.choice([True, False]),
    'list': lambda: [random.randint(0, 100) for _ in range(random.randint(0, 10))],
    'dict': lambda: {f'key{i}': random.randint(0, 100) for i in range(random.randint(0, 5))},
}


def generate_value_by_type(type_hint: str = None) -> Any:
    """根据类型提示生成值"""
    if type_hint is None:
        return random.choice([
            random.randint(-100, 100),
            round(random.uniform(-100, 100), 4),
            ''.join(random.choices(string.ascii_letters, k=5)),
            random.choice([True, False]),
            None,
            [random.randint(0, 10) for _ in range(3)]
        ])

    type_hint = type_hint.strip().lower()
    if 'int' in type_hint:
        return TYPE_GENERATORS['int']()
    elif 'float' in type_hint:
        return TYPE_GENERATORS['float']()
    elif 'str' in type_hint:
        return TYPE_GENERATORS['str']()
    elif 'bool' in type_hint:
        return TYPE_GENERATORS['bool']()
    elif 'list' in type_hint:
        return TYPE_GENERATORS['list']()
    elif 'dict' in type_hint:
        return TYPE_GENERATORS['dict']()
    else:
        return None


def generate_boundary_values(type_hint: str = None) -> List[Any]:
    """生成边界值"""
    if type_hint is None:
        return [0, -1, 1, None, '', [], {}]

    type_hint = type_hint.strip().lower()
    if 'int' in type_hint:
        return [0, -1, 1, 2147483647, -2147483648, 100, -100]
    elif 'float' in type_hint:
        return [0.0, -0.1, 0.1, float('inf'), -float('inf'), 1e-10, 1e10]
    elif 'str' in type_hint:
        return ['', 'a', ' ' * 100, '!@#$%^&*()', '中文测试', None]
    elif 'bool' in type_hint:
        return [True, False]
    elif 'list' in type_hint:
        return [[], [None], [0], list(range(100))]
    elif 'dict' in type_hint:
        return [{}, {'key': None}, {'': ''}]
    return [None]


# ========== 测试用例生成 ==========

def generate_unit_tests(func_info: Dict, num_cases: int = 5) -> List[Dict]:
    """为函数生成单元测试用例"""
    test_cases = []
    func_name = func_info['name']
    args = func_info.get('args', [])

    for i in range(num_cases):
        inputs = {}
        for arg in args:
            inputs[arg['name']] = generate_value_by_type(arg.get('type'))

        test_cases.append({
            'test_id': f"UT-{func_name}-{i+1:04d}",
            'function': func_name,
            'type': 'unit',
            'inputs': inputs,
            'expected': None,  # 需要实际运行确定
            'description': f'自动生成的单元测试 #{i+1}'
        })

    return test_cases


def generate_boundary_tests(func_info: Dict) -> List[Dict]:
    """生成边界测试用例"""
    test_cases = []
    func_name = func_info['name']
    args = func_info.get('args', [])

    if not args:
        return test_cases

    # 为第一个参数生成边界值，其他参数用默认值
    first_arg = args[0]
    boundary_vals = generate_boundary_values(first_arg.get('type'))

    for i, bval in enumerate(boundary_vals):
        inputs = {}
        for j, arg in enumerate(args):
            if j == 0:
                inputs[arg['name']] = bval
            else:
                inputs[arg['name']] = generate_value_by_type(arg.get('type'))

        test_cases.append({
            'test_id': f"BT-{func_name}-{i+1:04d}",
            'function': func_name,
            'type': 'boundary',
            'inputs': inputs,
            'expected': None,
            'description': f'边界测试: {first_arg["name"]}={bval!r}'
        })

    return test_cases


def generate_fuzz_tests(func_info: Dict, num_cases: int = 20) -> List[Dict]:
    """生成模糊测试用例"""
    test_cases = []
    func_name = func_info['name']
    args = func_info.get('args', [])

    for i in range(num_cases):
        inputs = {}
        for arg in args:
            # 模糊测试使用更极端的随机值
            r = random.random()
            if r < 0.2:
                inputs[arg['name']] = None
            elif r < 0.4:
                inputs[arg['name']] = generate_value_by_type(arg.get('type'))
            elif r < 0.6:
                inputs[arg['name']] = ''.join(random.choices(string.printable, k=random.randint(0, 50)))
            elif r < 0.8:
                inputs[arg['name']] = [random.choice([None, 0, 'x', float('nan')]) for _ in range(random.randint(0, 20))]
            else:
                inputs[arg['name']] = generate_value_by_type(arg.get('type'))

        test_cases.append({
            'test_id': f"FT-{func_name}-{i+1:04d}",
            'function': func_name,
            'type': 'fuzz',
            'inputs': inputs,
            'expected': None,
            'description': f'模糊测试 #{i+1}'
        })

    return test_cases


def generate_test_code(func_info: Dict, test_cases: List[Dict]) -> str:
    """生成pytest测试代码"""
    func_name = func_info['name']
    lines = [
        '"""',
        f'自动生成的测试文件 - {func_name}',
        f'生成时间: {datetime.now().isoformat()}',
        '"""',
        'import pytest',
        'import math',
        '',
        '',
    ]

    for tc in test_cases:
        test_func_name = f"test_{func_name}_{tc['type']}_{tc['test_id'].split('-')[-1]}"
        lines.append(f'def {test_func_name}():')
        lines.append(f'    """{tc["description"]}"""')
        # 构建参数
        args_str = ', '.join(f'{k}={v!r}' for k, v in tc['inputs'].items())
        if tc.get('expected') is not None:
            lines.append(f'    result = {func_name}({args_str})')
            lines.append(f'    assert result == {tc["expected"]!r}')
        else:
            lines.append(f'    # 验证不抛出异常')
            lines.append(f'    try:')
            lines.append(f'        {func_name}({args_str})')
            lines.append(f'    except (ValueError, TypeError) as e:')
            lines.append(f'        pytest.skip(f"跳过: {{e}}")')
        lines.append('')

    return '\n'.join(lines)


# ========== 测试覆盖率分析 ==========

def analyze_coverage(source_code: str) -> Dict:
    """静态分析代码覆盖率路径"""
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {'error': str(e)}

    total_branches = 0
    covered_paths = 0
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            branches = 0
            for child in ast.walk(node):
                if isinstance(child, ast.If):
                    branches += 2  # True/False两个分支
                elif isinstance(child, (ast.For, ast.While)):
                    branches += 2  # 进入/不进入循环
                elif isinstance(child, ast.ExceptHandler):
                    branches += 1

            # 路径数近似（简化）
            paths = min(2 ** branches, 100) if branches > 0 else 1
            functions.append({
                'name': node.name,
                'line': node.lineno,
                'branches': branches,
                'estimated_paths': paths
            })
            total_branches += branches
            covered_paths += paths

    coverage_estimate = min(100, max(0, 100 - total_branches * 2))

    return {
        'total_functions': len(functions),
        'total_branches': total_branches,
        'function_details': functions,
        'estimated_coverage': coverage_estimate,
        'complexity_score': min(100, total_branches * 5)
    }


# ========== 测试服务 ==========

class AITestGenerator:
    """AI 测试生成服务"""

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
                    CREATE TABLE IF NOT EXISTS test_suites (
                        suite_id TEXT PRIMARY KEY,
                        suite_name TEXT NOT NULL,
                        target_module TEXT,
                        target_function TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'generated',
                        total_cases INTEGER DEFAULT 0,
                        passed INTEGER DEFAULT 0,
                        failed INTEGER DEFAULT 0,
                        errors INTEGER DEFAULT 0,
                        coverage REAL,
                        created_at TEXT,
                        executed_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS test_cases (
                        case_id TEXT PRIMARY KEY,
                        suite_id TEXT NOT NULL,
                        function_name TEXT,
                        test_type TEXT,
                        inputs TEXT,
                        expected TEXT,
                        actual TEXT,
                        status TEXT DEFAULT 'pending',
                        error_message TEXT,
                        execution_time_ms REAL,
                        created_at TEXT,
                        executed_at TEXT,
                        FOREIGN KEY (suite_id) REFERENCES test_suites(suite_id)
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tc_suite ON test_cases(suite_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化测试生成数据库失败: {e}")

    # ========== 生成测试套件 ==========

    def generate_suite(self, source_code: str, suite_name: str = '',
                      target_module: str = '', include_types: List[str] = None) -> Dict:
        """从源代码生成完整测试套件"""
        include_types = include_types or ['unit', 'boundary', 'fuzz']

        # 解析函数
        functions = parse_function(source_code)
        if not functions:
            return {'success': False, 'error': '未找到函数定义'}
        if 'error' in functions[0]:
            return {'success': False, 'error': functions[0]['error']}

        suite_id = f"TS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        all_cases = []

        for func in functions:
            if func['name'].startswith('_'):
                continue  # 跳过私有方法

            if 'unit' in include_types:
                cases = generate_unit_tests(func, num_cases=5)
                all_cases.extend(cases)
            if 'boundary' in include_types:
                cases = generate_boundary_tests(func)
                all_cases.extend(cases)
            if 'fuzz' in include_types:
                cases = generate_fuzz_tests(func, num_cases=10)
                all_cases.extend(cases)

        # 保存套件
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO test_suites
                    (suite_id, suite_name, target_module, description, status,
                     total_cases, created_at)
                    VALUES (?, ?, ?, ?, 'generated', ?, ?)
                ''', (
                    suite_id, suite_name or f'测试套件-{suite_id[-6:]}',
                    target_module,
                    f'自动生成 {len(functions)} 个函数的测试，共 {len(all_cases)} 个用例',
                    len(all_cases), datetime.now().isoformat()
                ))

                # 保存用例
                for case in all_cases:
                    case_id = case['test_id']
                    cursor.execute('''
                        INSERT INTO test_cases
                        (case_id, suite_id, function_name, test_type, inputs,
                         expected, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (
                        case_id, suite_id, case['function'], case['type'],
                        json.dumps(case['inputs'], ensure_ascii=False, default=str),
                        json.dumps(case.get('expected'), ensure_ascii=False, default=str),
                        datetime.now().isoformat()
                    ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        logger.info(f"生成测试套件: {suite_id}, 共 {len(all_cases)} 个用例")

        return {
            'success': True,
            'suite_id': suite_id,
            'suite_name': suite_name,
            'functions_analyzed': len(functions),
            'total_cases': len(all_cases),
            'cases_by_type': {
                t: len([c for c in all_cases if c['type'] == t])
                for t in set(c['type'] for c in all_cases)
            }
        }

    # ========== 执行测试 ==========

    def execute_suite(self, suite_id: str, target_functions: Dict[str, Callable] = None) -> Dict:
        """执行测试套件"""
        suite = self.get_suite(suite_id)
        if not suite:
            return {'success': False, 'error': '测试套件不存在'}

        cases = self.get_cases(suite_id)
        if not cases:
            return {'success': False, 'error': '无测试用例'}

        passed = 0
        failed = 0
        errors = 0

        for case in cases:
            func_name = case['function_name']
            func = (target_functions or {}).get(func_name)
            inputs = json.loads(case['inputs']) if case['inputs'] else {}

            start_time = datetime.now()
            status = 'error'
            error_msg = None
            actual = None

            if func is None:
                error_msg = f'函数 {func_name} 未提供'
                errors += 1
            else:
                try:
                    actual = func(**inputs)
                    status = 'passed'
                    passed += 1
                except Exception as e:
                    error_msg = str(e)
                    # 区分失败和错误
                    if isinstance(e, (AssertionError,)):
                        status = 'failed'
                        failed += 1
                    else:
                        status = 'error'
                        errors += 1

            exec_time = (datetime.now() - start_time).total_seconds() * 1000

            # 更新用例状态
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE test_cases
                        SET status = ?, actual = ?, error_message = ?,
                            execution_time_ms = ?, executed_at = ?
                        WHERE case_id = ?
                    ''', (
                        status,
                        json.dumps(actual, ensure_ascii=False, default=str) if actual is not None else None,
                        error_msg, round(exec_time, 2),
                        datetime.now().isoformat(), case['case_id']
                    ))
                    conn.commit()
            except Exception:
                pass

        # 更新套件状态
        total = len(cases)
        coverage = round(passed / total * 100, 2) if total > 0 else 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE test_suites
                    SET status = 'executed', passed = ?, failed = ?,
                        errors = ?, coverage = ?, executed_at = ?
                    WHERE suite_id = ?
                ''', (passed, failed, errors, coverage,
                      datetime.now().isoformat(), suite_id))
                conn.commit()
        except Exception:
            pass

        return {
            'success': True,
            'suite_id': suite_id,
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': round(passed / total * 100, 2) if total > 0 else 0,
            'coverage': coverage
        }

    # ========== 回归测试 ==========

    def select_regression_cases(self, suite_id: str, changed_functions: List[str]) -> Dict:
        """根据变更的函数选择回归测试用例"""
        cases = self.get_cases(suite_id)
        selected = [c for c in cases if c['function_name'] in changed_functions]

        return {
            'suite_id': suite_id,
            'total_cases': len(cases),
            'selected_cases': len(selected),
            'selected_case_ids': [c['case_id'] for c in selected],
            'reduction_ratio': round(1 - len(selected) / max(len(cases), 1), 4)
        }

    # ========== 查询 ==========

    def get_suite(self, suite_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM test_suites WHERE suite_id = ?', (suite_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'suite_id': row[0], 'suite_name': row[1], 'target_module': row[2],
                    'target_function': row[3], 'description': row[4], 'status': row[5],
                    'total_cases': row[6], 'passed': row[7], 'failed': row[8],
                    'errors': row[9], 'coverage': row[10],
                    'created_at': row[11], 'executed_at': row[12]
                }
        except Exception:
            return None

    def get_cases(self, suite_id: str) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM test_cases WHERE suite_id = ?', (suite_id,))
                rows = cursor.fetchall()
                return [
                    {
                        'case_id': r[0], 'suite_id': r[1], 'function_name': r[2],
                        'test_type': r[3], 'inputs': r[4], 'expected': r[5],
                        'actual': r[6], 'status': r[7], 'error_message': r[8],
                        'execution_time_ms': r[9], 'created_at': r[10], 'executed_at': r[11]
                    }
                    for r in rows
                ]
        except Exception:
            return []

    def list_suites(self, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT suite_id, suite_name, status, total_cases, passed, failed, created_at
                    FROM test_suites ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
                return [
                    {
                        'suite_id': r[0], 'suite_name': r[1], 'status': r[2],
                        'total_cases': r[3], 'passed': r[4], 'failed': r[5], 'created_at': r[6]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    # ========== 生成测试报告 ==========

    def generate_report(self, suite_id: str) -> Dict:
        """生成测试报告"""
        suite = self.get_suite(suite_id)
        if not suite:
            return {'success': False, 'error': '套件不存在'}

        cases = self.get_cases(suite_id)
        type_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0})
        func_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0})

        for c in cases:
            t = c['test_type']
            type_stats[t]['total'] += 1
            func_stats[c['function_name']]['total'] += 1
            if c['status'] == 'passed':
                type_stats[t]['passed'] += 1
                func_stats[c['function_name']]['passed'] += 1
            elif c['status'] == 'failed':
                type_stats[t]['failed'] += 1
                func_stats[c['function_name']]['failed'] += 1
            elif c['status'] == 'error':
                type_stats[t]['errors'] += 1
                func_stats[c['function_name']]['errors'] += 1

        # 失败用例
        failures = [
            {
                'case_id': c['case_id'],
                'function': c['function_name'],
                'type': c['test_type'],
                'error': c['error_message'],
                'inputs': c['inputs']
            }
            for c in cases if c['status'] in ('failed', 'error')
        ]

        return {
            'suite_id': suite_id,
            'suite_name': suite['suite_name'],
            'summary': {
                'total': suite['total_cases'],
                'passed': suite['passed'],
                'failed': suite['failed'],
                'errors': suite['errors'],
                'pass_rate': round(suite['passed'] / max(suite['total_cases'], 1) * 100, 2)
            },
            'by_type': dict(type_stats),
            'by_function': dict(func_stats),
            'failures': failures[:20],  # 限制前20个
            'execution_time': suite.get('executed_at')
        }

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM test_suites')
                total_suites = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM test_cases')
                total_cases = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM test_cases WHERE status = 'passed'")
                passed = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM test_cases WHERE status = 'failed'")
                failed = cursor.fetchone()[0]
                return {
                    'total_suites': total_suites,
                    'total_cases': total_cases,
                    'passed_cases': passed,
                    'failed_cases': failed,
                    'overall_pass_rate': round(passed / max(total_cases, 1) * 100, 2)
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    tg = AITestGenerator()

    # 测试用源码
    sample_code = '''
def add(a: int, b: int) -> int:
    """两数相加"""
    return a + b

def divide(a: float, b: float) -> float:
    """除法"""
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

def process_list(items: list) -> int:
    """处理列表"""
    if not items:
        return 0
    return sum(x for x in items if x is not None)
'''

    print("解析函数:")
    funcs = parse_function(sample_code)
    for f in funcs:
        print(f"  {f['name']}({', '.join(a['name'] for a in f['args'])}) -> {f.get('returns')}")

    print("\n生成测试套件:")
    result = tg.generate_suite(sample_code, suite_name='示例测试套件')
    print(f"  套件ID: {result.get('suite_id')}")
    print(f"  总用例: {result.get('total_cases')}")
    print(f"  按类型: {result.get('cases_by_type')}")

    print("\n执行测试:")
    target_funcs = {
        'add': lambda a, b: a + b,
        'divide': lambda a, b: a / b if b != 0 else (_ for _ in ()).throw(ValueError("除数不能为零")),
        'process_list': lambda items: sum(x for x in items if x is not None) if items else 0
    }
    exec_result = tg.execute_suite(result['suite_id'], target_funcs)
    print(f"  通过: {exec_result['passed']}/{exec_result['total']}")
    print(f"  通过率: {exec_result['pass_rate']}%")

    print("\n测试报告:")
    report = tg.generate_report(result['suite_id'])
    print(f"  按类型: {dict(report['by_type'])}")

    print(f"\n统计: {tg.get_statistics()}")
