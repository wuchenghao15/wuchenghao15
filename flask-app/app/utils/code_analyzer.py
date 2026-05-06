#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码分析器模块
负责分析项目代码质量，检测潜在问题和错误

import os
import re
import ast
import logging
from typing import List, Dict, Any

# 配置日志
logger = logging.getLogger('code_analyzer')

class CodeAnalyzer:
    """代码分析器类"""

    def __init__(self):
        """初始化代码分析器"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.python_extensions = ['.py']
        self.ignored_dirs = ['__pycache__', 'venv', 'env', '.git', 'static', 'templates']
        logger.info("代码分析器初始化完成")

    def analyze_project(self) -> List[Dict[str, Any]]:
        """分析整个项目的代码"""
        issues = []
        try:
            # 遍历项目目录
            for root, dirs, files in os.walk(self.project_root):
                # 忽略指定目录
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

                # 分析Python文件
                for file in files:
                    if any(file.endswith(ext) for ext in self.python_extensions):
                        file_path = os.path.join(root, file)
                        file_issues = self.analyze_file(file_path)
                        issues.extend(file_issues)

            logger.info(f"代码分析完成，发现 {len(issues)} 个问题")
        except Exception as e:
            logger.error(f"分析项目时出错: {str(e)}")

        return issues

    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """分析单个文件的代码"""
        issues = []
            with open(file_path, 'r', encoding='utf-8') as f:

            # 分析语法
            syntax_issues = self._analyze_syntax(file_path, content)
            issues.extend(syntax_issues)

            # 分析代码质量
            quality_issues = self._analyze_quality(file_path, content)
            issues.extend(quality_issues)

        except Exception as e:
            logger.error(f"分析文件 {file_path} 时出错: {str(e)}")


    def _analyze_syntax(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """分析代码语法"""
            # 尝试解析代码
            ast.parse(content)
            issues.append({
                'type': 'syntax_error',
                'description': f"语法错误: {e.msg}",
                'file': file_path,
                'line': e.lineno,
                'severity': 'high'
            })
        except Exception as e:
            issues.append({
                'type': 'parse_error',
                'description': f"解析错误: {str(e)}",
                'file': file_path,
                'severity': 'high'
            })


    def _analyze_quality(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """分析代码质量"""

        # 检查每行代码
            if len(line) > 100:
                    'type': 'line_length',
                    'description': "行长度超过100个字符",
                    'file': file_path,
                    'line': line_num,
                    'severity': 'medium'
                })

            # 检查空白字符
            if line and line[-1].isspace():
                    'type': 'trailing_whitespace',
                    'description': "行尾有空白字符",
                    'file': file_path,
                    'line': line_num,
                })

            # 检查注释
            if '#' in line and line.strip().startswith('#'):
                if not line.strip().startswith('# '):
                        'type': 'comment_format',
                        'description': "注释格式不正确，应该以 '# ' 开头",
                        'file': file_path,
                        'severity': 'low'
                    })

            # 检查未使用的导入
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                pass
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                    if function_lines > 50:
                        issues.append({
                            'type': 'function_length',
                            'description': f"函数 {node.name} 长度超过50行",
                            'file': file_path,
                            'line': node.lineno,
                            'severity': 'medium'
        except Exception as e:

        return issues
        """检测常见错误"""
        # 检测潜在的错误模式
        error_patterns = [
            (r'print\(.*\)\s*$', '可能的调试代码'),
            (r'pass\s*$', '空代码块'),
            (r'except\s+Exception\s*:', '捕获所有异常'),
        ]

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, description in error_patterns:
                if re.search(pattern, line):
                    issues.append({
                        'type': 'common_error',
                        'file': 'unknown',
                        'line': line_num,
                        'severity': 'medium'
                    })


    def check_imports(self, file_path: str) -> List[Dict[str, Any]]:
        """检查导入语句"""
        issues = []
            with open(file_path, 'r', encoding='utf-8') as f:

            tree = ast.parse(content)
            for node in ast.walk(tree):
                    for alias in node.names:
                            'type': 'import',
                            'description': f"导入模块: {alias.name}",
                            'file': file_path,
                            'line': node.lineno,
                            'severity': 'low'
                        })
                elif isinstance(node, ast.ImportFrom):
                    issues.append({
                        'type': 'import_from',
                        'severity': 'low'
                    })
        except Exception as e:

        return issues
    def get_code_metrics(self, file_path: str) -> Dict[str, Any]:
        """获取代码 metrics"""
            'file_path': file_path,
            'lines': 0,
            'classes': 0,
        }

                content = f.read()

            lines = content.split('\n')
            metrics['lines'] = len(lines)
            # 计算注释行数
            for line in lines:
                if line.strip().startswith('#'):

            # 计算函数和类的数量
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    metrics['functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics['classes'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics['imports'] += 1


if __name__ == '__main__':
    # 测试代码分析器
    print(f"发现 {len(issues)} 个问题:")
    for issue in issues:

    # 测试代码 metrics
    test_file = os.path.join(os.path.dirname(__file__), '..', 'ai', 'engineer_ai.py')
    if os.path.exists(test_file):
        print("\n代码 metrics:")
            print(f"{key}: {value}")
