# -*- coding: utf-8 -*-
"""
CodeDebugAgent - 代码问题寻断Agent
分析代码问题，定位根因，提供修复方案
"""
import json
import logging
import ast
import os
import re
from datetime import datetime
from typing import Dict, Any, List

from .base_core_agent import BaseCoreAgent

logger = logging.getLogger(__name__)


class CodeDebugAgent(BaseCoreAgent):
    """代码问题寻断Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id='core_code_debug',
            agent_name='代码问题寻断Agent',
            agent_type='code_debug'
        )
        self.analyzed_files = 0
        self.issues_found = 0
    
    def analyze_code(self, file_path: str) -> List[Dict]:
        """分析单个文件的代码问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            issues.extend(self._check_syntax_errors(file_path, code))
            issues.extend(self._check_security_issues(file_path, code))
            issues.extend(self._check_performance_issues(file_path, code))
            issues.extend(self._check_best_practices(file_path, code))
            
            self.analyzed_files += 1
            self.issues_found += len(issues)
            
        except Exception as e:
            issues.append({
                'type': 'file_access_error',
                'severity': 'error',
                'message': f"无法读取文件: {str(e)}",
                'line': 0,
                'suggestion': '检查文件路径和权限'
            })
        
        return issues
    
    def _check_syntax_errors(self, file_path: str, code: str) -> List[Dict]:
        """检查语法错误"""
        issues = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append({
                'type': 'syntax_error',
                'severity': 'error',
                'message': str(e),
                'line': e.lineno or 0,
                'suggestion': '修复语法错误'
            })
        return issues
    
    def _check_security_issues(self, file_path: str, code: str) -> List[Dict]:
        """检查安全问题"""
        issues = []
        
        security_patterns = [
            (r'password\s*=\s*["\'].*["\']', 'hardcoded_password', '发现硬编码密码'),
            (r'secret\s*=\s*["\'].*["\']', 'hardcoded_secret', '发现硬编码密钥'),
            (r'exec\s*\(', 'unsafe_exec', '使用了不安全的exec函数'),
            (r'eval\s*\(', 'unsafe_eval', '使用了不安全的eval函数'),
            (r'subprocess\.call\s*\(', 'unsafe_subprocess', '使用了subprocess.call'),
            (r'os\.system\s*\(', 'unsafe_os_system', '使用了os.system'),
            (r'flask\.request\.form', 'csrf_risk', '直接使用form数据，存在CSRF风险'),
        ]
        
        for pattern, issue_type, message in security_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code.count('\n', 0, match.start()) + 1
                issues.append({
                    'type': issue_type,
                    'severity': 'critical',
                    'message': message,
                    'line': line_num,
                    'suggestion': self._get_security_suggestion(issue_type)
                })
        
        return issues
    
    def _get_security_suggestion(self, issue_type: str) -> str:
        """获取安全修复建议"""
        suggestions = {
            'hardcoded_password': '使用环境变量或配置文件存储密码',
            'hardcoded_secret': '使用密钥管理服务或环境变量',
            'unsafe_exec': '避免使用exec，改用其他方式实现动态逻辑',
            'unsafe_eval': '避免使用eval，改用ast.literal_eval或其他安全方式',
            'unsafe_subprocess': '使用subprocess.run并指定shell=False',
            'unsafe_os_system': '改用subprocess模块并进行输入验证',
            'csrf_risk': '添加CSRF防护中间件'
        }
        return suggestions.get(issue_type, '请修复安全问题')
    
    def _check_performance_issues(self, file_path: str, code: str) -> List[Dict]:
        """检查性能问题"""
        issues = []
        
        performance_patterns = [
            (r'\bO\(\s*n\s*\*\*\s*2\b', 'quadratic_complexity', '发现O(n^2)复杂度代码'),
            (r'\bO\(\s*n\s*\*\*\s*3\b', 'cubic_complexity', '发现O(n^3)复杂度代码'),
            (r'for\s+\w+\s+in\s+\w+:\s*\n\s+for\s+\w+\s+in\s+\w+:', 'nested_loop', '发现嵌套循环'),
            (r'sleep\s*\(', 'unnecessary_sleep', '使用了sleep函数'),
            (r'global\s+\w+', 'global_variable', '使用了全局变量'),
        ]
        
        for pattern, issue_type, message in performance_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code.count('\n', 0, match.start()) + 1
                issues.append({
                    'type': issue_type,
                    'severity': 'warning',
                    'message': message,
                    'line': line_num,
                    'suggestion': self._get_performance_suggestion(issue_type)
                })
        
        return issues
    
    def _get_performance_suggestion(self, issue_type: str) -> str:
        """获取性能优化建议"""
        suggestions = {
            'quadratic_complexity': '考虑使用哈希表或更高效的算法',
            'cubic_complexity': '重新设计算法，降低时间复杂度',
            'nested_loop': '考虑使用向量化操作或预计算',
            'unnecessary_sleep': '检查sleep是否必要，考虑使用异步方式',
            'global_variable': '尽量避免全局变量，使用局部变量或类属性'
        }
        return suggestions.get(issue_type, '请优化性能')
    
    def _check_best_practices(self, file_path: str, code: str) -> List[Dict]:
        """检查最佳实践"""
        issues = []
        
        patterns = [
            (r'\bprint\s*\(', 'print_statement', '使用了print语句', 'warning'),
            (r'\bimport\s+(sys|os|json)\s*$', 'unused_import', '可能存在未使用的导入', 'info'),
            (r'\bpass\s*$', 'pass_statement', '使用了pass语句', 'info'),
            (r'\bTODO\b', 'todo_comment', '存在TODO注释', 'info'),
            (r'\bFIXME\b', 'fixme_comment', '存在FIXME注释', 'warning'),
        ]
        
        for pattern, issue_type, message, severity in patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                line_num = code.count('\n', 0, match.start()) + 1
                issues.append({
                    'type': issue_type,
                    'severity': severity,
                    'message': message,
                    'line': line_num,
                    'suggestion': '按照注释提示进行修复'
                })
        
        return issues
    
    def execute(self, context: Dict = None) -> Dict:
        """执行代码分析"""
        task_id = self.generate_task_id()
        self.status = 'running'
        self.heartbeat()
        
        try:
            files_to_analyze = context.get('files', []) if context else []
            
            if not files_to_analyze:
                files_to_analyze = self._get_python_files()
            
            all_issues = []
            for file_path in files_to_analyze[:20]:
                issues = self.analyze_code(file_path)
                all_issues.extend([{**issue, 'file': file_path} for issue in issues])
            
            self.report_to_db(task_id, 'completed', {
                'analyzed_files': self.analyzed_files,
                'issues_found': self.issues_found,
                'issues': all_issues,
                'summary': self._generate_summary(all_issues)
            })
            
            self.record_task(task_id, 'completed', {'issues_count': len(all_issues)})
            
            self.status = 'idle'
            
            return {
                'success': True,
                'task_id': task_id,
                'agent': self.agent_name,
                'analyzed_files': len(files_to_analyze),
                'issues_found': len(all_issues),
                'issues': all_issues,
                'summary': self._generate_summary(all_issues)
            }
        
        except Exception as e:
            return self.handle_error(e, task_id)
    
    def _get_python_files(self) -> List[str]:
        """获取项目中的Python文件"""
        project_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app'
        python_files = []
        
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        return python_files
    
    def _generate_summary(self, issues: List[Dict]) -> Dict:
        """生成分析摘要"""
        by_severity = {'critical': 0, 'error': 0, 'warning': 0, 'info': 0}
        by_type = {}
        
        for issue in issues:
            severity = issue.get('severity', 'info')
            issue_type = issue.get('type', 'unknown')
            
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[issue_type] = by_type.get(issue_type, 0) + 1
        
        return {
            'by_severity': by_severity,
            'by_type': by_type,
            'total': len(issues)
        }
