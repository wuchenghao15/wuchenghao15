#!/usr/bin/env python3
"""AI智能代码审查Agent"""

import os
import re
import logging
import ast
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AICodeReviewAgent(AIEmployee):
    """AI代码审查Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI代码审查专家"):
        super().__init__(employee_id, name, 'code_review', 8)
        self.skills = [
            '代码审查', '代码质量分析', '代码风格检查',
            '安全漏洞检测', '性能问题识别', '代码重构建议',
            '最佳实践检查', '代码复杂度分析'
        ]
        self.review_history = []
        self.total_reviews = 0
        self.total_issues_found = 0
        self.categories = ['security', 'performance', 'style', 'complexity', 'bug', 'refactor']
    
    def analyze_code(self, code: str, file_path: str = "") -> Dict[str, Any]:
        """分析代码质量"""
        issues = []
        file_name = os.path.basename(file_path)
        
        issues.extend(self._check_security(code, file_name))
        issues.extend(self._check_performance(code, file_name))
        issues.extend(self._check_style(code))
        issues.extend(self._check_complexity(code))
        issues.extend(self._check_common_bugs(code))
        
        self.total_reviews += 1
        self.total_issues_found += len(issues)
        
        review_result = {
            'file_path': file_path,
            'total_issues': len(issues),
            'issues': issues,
            'summary': self._generate_summary(issues),
            'timestamp': datetime.now().isoformat()
        }
        
        self.review_history.append(review_result)
        return review_result
    
    def _check_security(self, code: str, file_name: str) -> List[Dict]:
        """检查安全问题"""
        issues = []
        
        security_patterns = [
            (r'password\s*=\s*["\'].*["\']', '硬编码密码', 'security', 'critical'),
            (r'secret\s*=\s*["\'].*["\']', '硬编码密钥', 'security', 'critical'),
            (r'token\s*=\s*["\'].*["\']', '硬编码Token', 'security', 'critical'),
            (r'eval\(', '使用eval函数', 'security', 'high'),
            (r'exec\(', '使用exec函数', 'security', 'high'),
            (r'os\.system\(', '使用os.system', 'security', 'medium'),
            (r'subprocess\.Popen\(', '使用subprocess', 'security', 'medium'),
            (r'pickle\.load\(', '使用pickle加载', 'security', 'high'),
            (r'shelve\.open\(', '使用shelve', 'security', 'medium'),
        ]
        
        for pattern, description, category, severity in security_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'category': category,
                    'severity': severity,
                    'description': description,
                    'suggestion': self._get_suggestion(description)
                })
        
        return issues
    
    def _check_performance(self, code: str, file_name: str) -> List[Dict]:
        """检查性能问题"""
        issues = []
        
        perf_patterns = [
            (r'for\s+.*\s+in\s+range\(', '在循环中使用range', 'performance', 'medium'),
            (r'\.append\(', '循环中使用append', 'performance', 'low'),
            (r'string\s*\+=', '字符串拼接使用+=', 'performance', 'medium'),
            (r'\[\]\s*\+\s*\[\]', '列表拼接使用+', 'performance', 'medium'),
            (r'global\s+', '使用global变量', 'performance', 'low'),
            (r'lambda\s+', '过度使用lambda', 'performance', 'low'),
        ]
        
        for pattern, description, category, severity in perf_patterns:
            if re.search(pattern, code):
                issues.append({
                    'category': category,
                    'severity': severity,
                    'description': description,
                    'suggestion': self._get_suggestion(description)
                })
        
        return issues
    
    def _check_style(self, code: str) -> List[Dict]:
        """检查代码风格"""
        issues = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    'category': 'style',
                    'severity': 'low',
                    'description': f'第{i}行超过120字符',
                    'suggestion': '将长行拆分为多行'
                })
            if line.strip() and not line.strip().startswith('#'):
                if '    ' in line and '\t' in line:
                    issues.append({
                        'category': 'style',
                        'severity': 'medium',
                        'description': f'第{i}行混合使用空格和制表符',
                        'suggestion': '统一使用4个空格缩进'
                    })
        
        return issues
    
    def _check_complexity(self, code: str) -> List[Dict]:
        """检查代码复杂度"""
        issues = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    lines = node.lineno - (node.end_lineno or node.lineno)
                    if lines > 50:
                        issues.append({
                            'category': 'complexity',
                            'severity': 'high',
                            'description': f'函数{node.name}超过50行',
                            'suggestion': '将大型函数拆分为多个小函数'
                        })
        except SyntaxError:
            pass
        
        return issues
    
    def _check_common_bugs(self, code: str) -> List[Dict]:
        """检查常见Bug"""
        issues = []
        
        bug_patterns = [
            (r'==\s*None', '使用== None', 'bug', 'medium'),
            (r'!=\s*None', '使用!= None', 'bug', 'medium'),
            (r'is\s+not\s+None', '使用is not None', 'bug', 'low'),
            (r'except\s*:', '空except块', 'bug', 'high'),
            (r'pass\s*$', 'pass语句', 'bug', 'low'),
        ]
        
        for pattern, description, category, severity in bug_patterns:
            if re.search(pattern, code):
                issues.append({
                    'category': category,
                    'severity': severity,
                    'description': description,
                    'suggestion': self._get_suggestion(description)
                })
        
        return issues
    
    def _get_suggestion(self, issue_desc: str) -> str:
        """获取修复建议"""
        suggestions = {
            '硬编码密码': '使用环境变量或配置文件存储敏感信息',
            '硬编码密钥': '使用密钥管理服务或环境变量',
            '硬编码Token': '使用安全的密钥存储方案',
            '使用eval函数': '避免使用eval，考虑使用ast解析或函数映射',
            '使用exec函数': '避免使用exec，考虑使用安全的代码执行方式',
            '使用os.system': '使用subprocess模块并避免shell=True',
            '使用pickle加载': '考虑使用JSON或其他安全的序列化方式',
            '循环中使用range': '考虑使用enumerate或直接迭代',
            '循环中使用append': '考虑使用列表推导式',
            '字符串拼接使用+': '考虑使用join或f-string',
            '列表拼接使用+': '考虑使用extend方法',
            '使用global变量': '考虑通过参数传递或使用类属性',
            '使用== None': '应使用is None',
            '使用!= None': '应使用is not None',
            '空except块': '至少记录异常信息',
            'pass语句': '添加注释说明为何此处pass',
        }
        return suggestions.get(issue_desc, '请根据代码上下文进行优化')
    
    def _generate_summary(self, issues: List[Dict]) -> Dict:
        """生成审查摘要"""
        summary = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity in summary:
                summary[severity] += 1
        
        total = sum(summary.values())
        if total > 0:
            summary['score'] = max(0, 100 - (summary['critical'] * 10 + summary['high'] * 5 + summary['medium'] * 2))
        else:
            summary['score'] = 100
        
        return summary
    
    def get_stats(self) -> Dict:
        """获取审查统计"""
        return {
            'total_reviews': self.total_reviews,
            'total_issues_found': self.total_issues_found,
            'avg_issues_per_review': self.total_issues_found / max(1, self.total_reviews),
            'recent_reviews': self.review_history[-5:]
        }

code_review_agent = AICodeReviewAgent('ai_code_review_001')
