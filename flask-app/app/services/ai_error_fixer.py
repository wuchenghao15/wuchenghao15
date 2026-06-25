import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""
AI错误检测和修复服务
自动检测和修复代码错误、异常、逻辑漏洞和数学错误
"""

import re
import ast
import traceback
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import math
import json

class MathErrorDetector:
    """数学错误检测器"""
    
    @staticmethod
    def detect_division_by_zero(code: str, language: str = 'python') -> List[Dict]:
        """
        检测除零错误
        Args:
            code: 源代码
            language: 编程语言
        Returns:
            错误列表
        """
        errors = []
        
        if language == 'python':
            # 检测除零模式
            patterns = [
                r'(\w+)\s*/\s*0(?!\d)',  # x / 0
                r'(\w+)\s*//\s*0(?!\d)',  # x // 0
                r'(\w+)\s*%\s*0(?!\d)',  # x % 0
            ]
            
            for i, line in enumerate(code.split('\n'), 1):
                for pattern in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        var_name = match.group(1)
                        # 排除数学常量
                        if var_name not in ['inf', 'float', 'int']:
                            errors.append({
                                'type': 'division_by_zero',
                                'line': i,
                                'column': match.start(),
                                'message': f'检测到除零错误: {var_name} / 0',
                                'severity': 'high',
                                'code_snippet': line.strip(),
                                'suggestion': f'在除法前检查 {var_name} 是否为零'
                            })
        
        return errors
    
    @staticmethod
    def detect_negative_square_root(code: str, language: str = 'python') -> List[Dict]:
        """
        检测负数平方根错误
        Args:
            code: 源代码
            language: 编程语言
        Returns:
            错误列表
        """
        errors = []
        
        if language == 'python':
            patterns = [
                r'math\.sqrt\s*\(\s*(-?\w+)\s*\)',
                r'np\.sqrt\s*\(\s*(-?\w+)\s*\)',
                r'sqrt\s*\(\s*(-?\w+)\s*\)',
            ]
            
            for i, line in enumerate(code.split('\n'), 1):
                for pattern in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        value = match.group(1)
                        # 检查是否为负数字面量或变量
                        if value.startswith('-') or (not value.replace('.', '').replace('-', '').isdigit() and not value.startswith('-')):
                            # 尝试解析值
                            try:
                                if value.replace('.', '').replace('-', '').isdigit():
                                    num_value = float(value)
                                    if num_value < 0:
                                        errors.append({
                                            'type': 'negative_square_root',
                                            'line': i,
                                            'column': match.start(),
                                            'message': f'尝试对负数 {value} 求平方根',
                                            'severity': 'high',
                                            'code_snippet': line.strip(),
                                            'suggestion': '使用 cmath.sqrt() 处理复数，或在求平方根前检查值是否为负'
                                        })
                            except ValueError:
                                # 如果无法确定值，添加警告
                                if not any(keyword in line for keyword in ['cmath', 'complex', 'abs']):
                                    errors.append({
                                        'type': 'potential_negative_square_root',
                                        'line': i,
                                        'column': match.start(),
                                        'message': f'可能对负数求平方根: {value}',
                                        'severity': 'medium',
                                        'code_snippet': line.strip(),
                                        'suggestion': f'在求平方根前检查 {value} 是否为负，或使用 cmath.sqrt()'
                                    })
        
        return errors
    
    @staticmethod
    def detect_quadratic_negative_discriminant(code: str) -> List[Dict]:
        """
        检测二次方程求根公式中判别式小于零的情况
        Args:
            code: 源代码
        Returns:
            错误列表
        """
        errors = []
        
        # 检测判别式计算
        discriminant_pattern = r'(delta|D|b\s*\*\s*b)\s*=\s*([^;]+)'
        sqrt_pattern = r'sqrt\s*\(\s*([^)]+)\s*\)'
        
        lines = code.split('\n')
        discriminant_value = None
        discriminant_line = None
        
        for i, line in enumerate(lines, 1):
            # 检测判别式赋值
            disc_match = re.search(discriminant_pattern, line)
            if disc_match:
                expr = disc_match.group(2).strip()
                # 检查是否包含负号
                if '-' in expr and ('4' in expr and 'a' in expr and 'c' in expr):
                    discriminant_value = expr
                    discriminant_line = i
                    
                    # 检查判别式是否直接用于开方
                    for j in range(i, min(i + 5, len(lines) + 1)):
                        if j < len(lines):
                            sqrt_match = re.search(sqrt_pattern, lines[j])
                            if sqrt_match and discriminant_value:
                                errors.append({
                                    'type': 'quadratic_negative_discriminant',
                                    'line': j,
                                    'column': sqrt_match.start(),
                                    'message': '二次方程判别式可能小于零',
                                    'severity': 'medium',
                                    'code_snippet': lines[j].strip(),
                                    'suggestion': '判别式小于零时方程无实数解，需要使用复数或在求解前检查判别式'
                                })
                                break
        
        return errors
    
    @staticmethod
    def detect_overflow_errors(code: str) -> List[Dict]:
        """检测数值溢出错误"""
        errors = []
        
        # 检测可能导致溢出的操作
        patterns = [
            (r'factorial\s*\(\s*(\d+)\s*\)', '阶乘计算'),
            (r'(\w+)\s*\*\*\s*(\d+)', '指数运算'),
            (r'math\.exp\s*\(\s*(\d+)\s*\)', '指数运算'),
        ]
        
        for i, line in enumerate(code.split('\n'), 1):
            for pattern, op_name in patterns:
                match = re.search(pattern, line)
                if match:
                    if op_name == '阶乘计算':
                        value = int(match.group(1))
                        if value > 170:  # Python float 的限制
                            errors.append({
                                'type': 'numeric_overflow',
                                'line': i,
                                'message': f'阶乘计算可能导致溢出: {value}!',
                                'severity': 'medium',
                                'code_snippet': line.strip(),
                                'suggestion': '使用 decimal 模块或对数方法计算大数阶乘'
                            })
        
        return errors


class ExceptionErrorDetector:
    """异常错误检测器"""
    
    @staticmethod
    def detect_null_pointer(code: str, language: str = 'python') -> List[Dict]:
        """检测空指针引用"""
        errors = []
        
        if language == 'python':
            patterns = [
                (r'(\w+)\s*\.(\w+)\s*\(\)', '可能对None调用方法'),
                (r'if\s+not\s+(\w+)\s*:.*?(\w+)\s*\.', '空值检查后的使用'),
            ]
            
            for i, line in enumerate(code.split('\n'), 1):
                # 检测 NoneType 错误
                if 'NoneType' in line or "'NoneType'" in line:
                    errors.append({
                        'type': 'null_pointer',
                        'line': i,
                        'message': '检测到 NoneType 相关错误',
                        'severity': 'critical',
                        'code_snippet': line.strip(),
                        'suggestion': '在访问对象属性或方法前检查对象是否为 None'
                    })
                
                # 检测可能对 None 调用方法
                match = re.match(r'(\w+)\s*\.(\w+)\s*\(', line)
                if match:
                    var_name = match.group(1)
                    if var_name not in ['self', 'cls', 'super']:
                        # 简化检测，提示可能的问题
                        if any(keyword in line.lower() for keyword in ['find', 'get', 'select', 'query']):
                            errors.append({
                                'type': 'potential_null_pointer',
                                'line': i,
                                'message': f'可能对 None 值调用方法: {var_name}',
                                'severity': 'medium',
                                'code_snippet': line.strip(),
                                'suggestion': f'在使用 {var_name} 前添加 None 检查: if {var_name} is not None:'
                            })
        
        return errors
    
    @staticmethod
    def detect_unhandled_exception(code: str) -> List[Dict]:
        """检测未处理的异常"""
        errors = []
        
        # 检测可能抛出异常的操作
        risky_patterns = [
            (r'open\s*\(\s*([^)]+)\s*\)', '文件操作'),
            (r'requests\.', 'HTTP请求'),
            (r'db\.', '数据库操作'),
            (r'eval\s*\(', '动态代码执行'),
            (r'exec\s*\(', '动态代码执行'),
        ]
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 检测 try 语句
                if isinstance(node, ast.Try):
                    # 检查是否有 except 块
                    if len(node.handlers) == 0:
                        errors.append({
                            'type': 'unhandled_exception',
                            'line': node.lineno,
                            'message': '检测到可能抛出异常的代码但未捕获',
                            'severity': 'high',
                            'code_snippet': 'try block without except',
                            'suggestion': '添加 except 块来处理可能的异常'
                        })
                    
                    # 检查 except 是否捕获所有异常
                    for handler in node.handlers:
                        if handler.type is None:  # bare except
                            break
                        if isinstance(handler.type, ast.Name):
                            if handler.type.id in ['Exception', 'BaseException']:
                                break
        except SyntaxError:
            pass
        
        return errors
    
    @staticmethod
    def detect_type_mismatch(code: str) -> List[Dict]:
        """检测类型不匹配错误"""
        errors = []
        
        type_operations = [
            (r'str\s*\(\s*(\w+)\s*\)', r'\1.*isinstance\s*\(\s*\1\s*,\s*int\s*\)', '字符串转整数'),
            (r'int\s*\(\s*(\w+)\s*\)', r'isinstance\s*\(\s*\1\s*,\s*str\s*\)', '整数转字符串'),
        ]
        
        for i, line in enumerate(code.split('\n'), 1):
            for pattern, check_pattern, desc in type_operations:
                match = re.search(pattern, line)
                if match:
                    var_name = match.group(1)
                    # 简单检查，可能存在类型问题
                    if any(f'isinstance({var_name}' in code for _ in [1]):
                        errors.append({
                            'type': 'potential_type_mismatch',
                            'line': i,
                            'message': f'可能存在类型转换问题: {desc}',
                            'severity': 'low',
                            'code_snippet': line.strip(),
                            'suggestion': f'在转换前检查 {var_name} 的类型'
                        })
        
        return errors


class LogicErrorDetector:
    """逻辑错误检测器"""
    
    @staticmethod
    def detect_infinite_loop(code: str) -> List[Dict]:
        """检测无限循环"""
        errors = []
        
        # 检测 while True 但没有 break
        lines = code.split('\n')
        in_while_true = False
        while_line = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if re.match(r'while\s+True\s*:', stripped) or re.match(r'while\s+1\s*:', stripped):
                in_while_true = True
                while_line = i
            
            if in_while_true:
                if 'break' in stripped or 'return' in stripped:
                    in_while_true = False
                
                # 检查循环条件修改
                if i > while_line and (stripped.startswith('if ') or stripped.startswith('elif ')):
                    # 继续检查
                    pass
                
                # 如果循环体太长但没有退出条件
                if i - while_line > 50 and in_while_true:
                    errors.append({
                        'type': 'potential_infinite_loop',
                        'line': while_line,
                        'message': 'while True 循环可能没有退出条件',
                        'severity': 'medium',
                        'code_snippet': lines[while_line - 1].strip(),
                        'suggestion': '确保循环有明确的退出条件（break 或 return）'
                    })
                    in_while_true = False
        
        return errors
    
    @staticmethod
    def detect_off_by_one(code: str) -> List[Dict]:
        """检测 off-by-one 错误"""
        errors = []
        
        patterns = [
            (r'range\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)', '范围错误'),
            (r'for\s+\w+\s+in\s+range\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)', '循环边界'),
        ]
        
        for i, line in enumerate(code.split('\n'), 1):
            for pattern, desc in patterns:
                match = re.search(pattern, line)
                if match:
                    start, end = match.groups()
                    try:
                        # 检查是否 start >= end
                        if start.isdigit() and end.isdigit():
                            if int(start) >= int(end):
                                errors.append({
                                    'type': 'off_by_one',
                                    'line': i,
                                    'message': f'range 范围可能不正确: range({start}, {end})',
                                    'severity': 'low',
                                    'code_snippet': line.strip(),
                                    'suggestion': f'检查 range({start}, {end}) 是否符合预期，可能需要 range({start}, {end})'
                                })
                    except ValueError:
                        pass
        
        return errors
    
    @staticmethod
    def detect_dead_code(code: str) -> List[Dict]:
        """检测死代码"""
        errors = []
        
        lines = code.split('\n')
        found_return = False
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 检测 return/break/continue 后的代码
            if found_return and stripped and not stripped.startswith('#'):
                if not stripped.startswith('"""') and not stripped.startswith("'''"):
                    # 可能是死代码
                    if any(stripped.startswith(kw) for kw in ['if ', 'elif ', 'else:', 'for ', 'while ', 'def ']):
                        errors.append({
                            'type': 'dead_code',
                            'line': i,
                            'message': '检测到可能无法执行的代码',
                            'severity': 'low',
                            'code_snippet': stripped,
                            'suggestion': '检查代码逻辑，确保所有代码路径都可执行'
                        })
            
            # 检测 return 语句
            if stripped.startswith('return') and not stripped.startswith('return '):
                found_return = True
            elif stripped and not stripped.startswith('#'):
                found_return = False
        
        return errors


class CodeFixer:
    """代码修复器"""
    
    @staticmethod
    def fix_division_by_zero(code: str, error_info: Dict) -> Tuple[str, str]:
        """
        修复除零错误
        Args:
            code: 源代码
            error_info: 错误信息
        Returns:
            (修复后的代码, 修复说明)
        """
        line_num = error_info.get('line', 0)
        lines = code.split('\n')
        
        if 0 < line_num <= len(lines):
            line = lines[line_num - 1]
            
            # 添加零值检查
            # 匹配除法表达式
            match = re.search(r'(\w+)\s*/\s*0(?!\d)', line)
            if match:
                var_name = match.group(1)
                indent = ' ' * (len(line) - len(line.lstrip()))
                
                # 在原行前添加检查
                check_code = f'{indent}if {var_name} != 0:\n'
                lines[line_num - 1] = check_code + indent + '    ' + line
                
                explanation = f"""添加了零值检查：
if {var_name} != 0:
    # 原代码
这样可以避免 {var_name} 为零时出现除零错误"""
        
        return '\n'.join(lines), explanation if 'check_code' in locals() else "无法自动修复"
    
    @staticmethod
    def fix_negative_square_root(code: str, error_info: Dict) -> Tuple[str, str]:
        """
        修复负数平方根错误
        Args:
            code: 源代码
            error_info: 错误信息
        Returns:
            (修复后的代码, 修复说明)
        """
        line_num = error_info.get('line', 0)
        lines = code.split('\n')
        
        if 0 < line_num <= len(lines):
            line = lines[line_num - 1]
            
            # 检查是否已导入 cmath
            has_cmath = 'import cmath' in code
            
            # 修改 sqrt 调用
            new_line = re.sub(r'math\.sqrt', 'cmath.sqrt', line)
            new_line = re.sub(r'np\.sqrt', 'cmath.sqrt', new_line)
            new_line = re.sub(r'\bsqrt\b', 'cmath.sqrt', new_line)
            
            if new_line != line:
                lines[line_num - 1] = new_line
                
                explanation = """使用 cmath.sqrt 替代 math.sqrt：
- cmath.sqrt 可以处理负数和复数
- 负数的平方根将返回复数形式
例如：cmath.sqrt(-1) 返回 1j"""
                
                # 如果没有导入 cmath，添加导入
                if not has_cmath:
                    lines.insert(0, 'import cmath')
                    explanation += "\n\n已自动添加：import cmath"
        
        return '\n'.join(lines), explanation if 'new_line' in locals() else "无法自动修复"
    
    @staticmethod
    def fix_quadratic_negative_discriminant(code: str, error_info: Dict) -> Tuple[str, str]:
        """
        修复二次方程负判别式错误
        Args:
            code: 源代码
            error_info: 错误信息
        Returns:
            (修复后的代码, 修复说明)
        """
        explanation = """二次方程判别式小于零时的处理方案：

方案1：使用复数
import cmath
delta = b*b - 4*a*c
x1 = (-b + cmath.sqrt(delta)) / (2*a)
x2 = (-b - cmath.sqrt(delta)) / (2*a)

方案2：检查判别式后再求解
if delta >= 0:
    x1 = (-b + math.sqrt(delta)) / (2*a)
    x2 = (-b - math.sqrt(delta)) / (2*a)
else:
    print("方程无实数解")"""
        
        return code, explanation
    
    @staticmethod
    def fix_null_pointer(code: str, error_info: Dict) -> Tuple[str, str]:
        """
        修复空指针错误
        Args:
            code: 源代码
            error_info: 错误信息
        Returns:
            (修复后的代码, 修复说明)
        """
        explanation = """修复空指针错误的建议：

1. 添加 None 检查：
if obj is not None:
    obj.method()
else:
    # 处理 None 的情况

2. 使用条件表达式：
result = obj.value if obj is not None else default_value

3. 使用 getattr：
result = getattr(obj, 'value', default_value)

4. 使用 try-except：
try:
    result = obj.value
except AttributeError:
    result = default_value"""
        
        return code, explanation
    
    @staticmethod
    def fix_unhandled_exception(code: str, error_info: Dict) -> Tuple[str, str]:
        """
        修复未处理异常
        Args:
            code: 源代码
            error_info: 错误信息
        Returns:
            (修复后的代码, 修复说明)
        """
        explanation = """添加异常处理的建议：

1. 捕获特定异常：
try:
    # 可能出错的代码
    result = risky_operation()
except ValueError as e:
    print(f"值错误: {e}")
    # 处理 ValueError
except Exception as e:
    print(f"其他错误: {e}")
    # 处理其他异常

2. 使用 finally 确保清理：
try:
    file = open('data.txt')
    content = file.read()
finally:
    file.close()  # 始终执行

3. 使用 context manager（推荐）：
with open('data.txt') as file:
    content = file.read()
# 文件自动关闭"""
        
        return code, explanation
    
    @staticmethod
    def add_exception_handling(code: str, operations: List[str]) -> str:
        """
        为指定操作添加异常处理
        Args:
            code: 源代码
            operations: 需要添加异常处理的操作
        Returns:
            修复后的代码
        """
        for op in operations:
            # 为文件操作添加异常处理
            if 'open' in op:
                code = re.sub(
                    r'(\w+)\s*=\s*open\s*\(\s*([^)]+)\s*\)',
                    r'try:\n    \1 = open(\2)\nexcept FileNotFoundError:\n    \1 = None',
                    code
                )
        
        return code


class ErrorFixer:
    """综合错误修复器"""
    
    def __init__(self):
        self.math_detector = MathErrorDetector()
        self.exception_detector = ExceptionErrorDetector()
        self.logic_detector = LogicErrorDetector()
        self.fixer = CodeFixer()
    
    def detect_all_errors(self, code: str, language: str = 'python') -> List[Dict]:
        """
        检测所有类型的错误
        Args:
            code: 源代码
            language: 编程语言
        Returns:
            错误列表
        """
        all_errors = []
        
        # 数学错误检测
        all_errors.extend(self.math_detector.detect_division_by_zero(code, language))
        all_errors.extend(self.math_detector.detect_negative_square_root(code, language))
        all_errors.extend(self.math_detector.detect_quadratic_negative_discriminant(code))
        
        # 异常错误检测
        all_errors.extend(self.exception_detector.detect_null_pointer(code, language))
        all_errors.extend(self.exception_detector.detect_unhandled_exception(code))
        all_errors.extend(self.exception_detector.detect_type_mismatch(code))
        
        # 逻辑错误检测
        all_errors.extend(self.logic_detector.detect_infinite_loop(code))
        all_errors.extend(self.logic_detector.detect_off_by_one(code))
        all_errors.extend(self.logic_detector.detect_dead_code(code))
        
        # 按严重程度排序
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        all_errors.sort(key=lambda x: severity_order.get(x.get('severity', 'info'), 5))
        
        return all_errors
    
    def fix_error(self, code: str, error_info: Dict) -> Tuple[str, str]:
        """
        修复指定错误
        Args:
            code: 源代码
            error_info: 错误信息
        Returns:
            (修复后的代码, 修复说明)
        """
        error_type = error_info.get('type', '')
        
        fix_methods = {
            'division_by_zero': self.fixer.fix_division_by_zero,
            'negative_square_root': self.fixer.fix_negative_square_root,
            'quadratic_negative_discriminant': self.fixer.fix_quadratic_negative_discriminant,
            'null_pointer': self.fixer.fix_null_pointer,
            'unhandled_exception': self.fixer.fix_unhandled_exception,
        }
        
        fix_method = fix_methods.get(error_type)
        if fix_method:
            return fix_method(code, error_info)
        
        return code, "该错误类型暂不支持自动修复"
    
    def auto_fix_all(self, code: str, language: str = 'python') -> Tuple[str, List[Dict]]:
        """
        自动修复所有可自动修复的错误
        Args:
            code: 源代码
            language: 编程语言
        Returns:
            (修复后的代码, 修复报告)
        """
        errors = self.detect_all_errors(code, language)
        fixed_errors = []
        
        # 按行号排序，从上到下修复
        errors.sort(key=lambda x: x.get('line', 0))
        
        for error in errors:
            # 只修复可以自动修复的错误
            if error.get('severity') in ['low', 'medium'] or error.get('type') in [
                'division_by_zero',
                'negative_square_root'
            ]:
                fixed_code, explanation = self.fix_error(code, error)
                
                if fixed_code != code:
                    fixed_errors.append({
                        'original_error': error,
                        'explanation': explanation,
                        'fixed': True
                    })
                    code = fixed_code
        
        return code, fixed_errors


# 全局错误修复器实例
error_fixer = ErrorFixer()


def fix_code(code: str, language: str = 'python') -> Dict:
    """
    修复代码中的错误
    Args:
        code: 源代码
        language: 编程语言
    Returns:
        修复结果字典
    """
    fixer = ErrorFixer()
    
    # 检测所有错误
    errors = fixer.detect_all_errors(code, language)
    
    # 自动修复
    fixed_code, fix_reports = fixer.auto_fix_all(code, language)
    
    return {
        'original_code': code,
        'fixed_code': fixed_code,
        'errors': errors,
        'fix_reports': fix_reports,
        'total_errors': len(errors),
        'fixed_count': len(fix_reports),
        'timestamp': datetime.now().isoformat()
    }


# 导出
__all__ = [
    'MathErrorDetector',
    'ExceptionErrorDetector',
    'LogicErrorDetector',
    'CodeFixer',
    'ErrorFixer',
    'error_fixer',
    'fix_code'
]
