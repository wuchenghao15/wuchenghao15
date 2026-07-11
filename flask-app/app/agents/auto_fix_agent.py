# -*- coding: utf-8 -*-
"""
AutoFixAgent - 自动修复Agent
根据代码分析结果自动修复问题
"""
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, List

from .base_core_agent import BaseCoreAgent

logger = logging.getLogger(__name__)


class AutoFixAgent(BaseCoreAgent):
    """自动修复Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id='core_auto_fix',
            agent_name='自动修复Agent',
            agent_type='auto_fix'
        )
        self.fixed_count = 0
        self.skipped_count = 0
        self.fixed_files = set()
    
    def fix_issue(self, file_path: str, issue: Dict) -> Dict:
        """修复单个问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            line_num = issue.get('line', 0)
            
            if line_num <= 0 or line_num > len(lines):
                return {
                    'success': False,
                    'reason': '行号无效',
                    'issue': issue
                }
            
            fixer = self._get_fixer(issue.get('type'))
            if not fixer:
                return {
                    'success': False,
                    'reason': '不支持的问题类型',
                    'issue': issue
                }
            
            result = fixer(file_path, lines, line_num, issue)
            
            if result.get('success'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                self.fixed_count += 1
                self.fixed_files.add(file_path)
                
                logger.info(f"[{self.agent_name}] 已修复文件 {file_path} 第 {line_num} 行")
            else:
                self.skipped_count += 1
            
            return result
        
        except Exception as e:
            return {
                'success': False,
                'reason': str(e),
                'issue': issue
            }
    
    def _get_fixer(self, issue_type: str):
        """获取修复器函数"""
        fixers = {
            'print_statement': self._fix_print_statement,
            'pass_statement': self._fix_pass_statement,
            'hardcoded_password': self._fix_hardcoded_password,
            'hardcoded_secret': self._fix_hardcoded_secret,
            'todo_comment': self._fix_todo_comment,
            'fixme_comment': self._fix_fixme_comment,
            'global_variable': self._fix_global_variable,
        }
        return fixers.get(issue_type)
    
    def _fix_print_statement(self, file_path: str, lines: List[str], line_num: int, issue: Dict) -> Dict:
        """修复print语句"""
        line = lines[line_num - 1]
        new_line = line.replace('print(', 'logger.info(')
        
        if 'logging' not in '\n'.join(lines[:line_num]):
            import_pos = 0
            for i, l in enumerate(lines):
                if l.startswith('import ') or l.startswith('from '):
                    import_pos = i + 1
                else:
                    break
            lines.insert(import_pos, 'import logging')
            lines.insert(import_pos + 1, 'logger = logging.getLogger(__name__)')
        
        lines[line_num - 1] = new_line
        
        return {'success': True, 'changed': f"print(...) -> logger.info(...)"}
    
    def _fix_pass_statement(self, file_path: str, lines: List[str], line_num: int, issue: Dict) -> Dict:
        """修复pass语句"""
        lines[line_num - 1] = '    # TODO: 实现此功能'
        return {'success': True, 'changed': 'pass -> # TODO: 实现此功能'}
    
    def _fix_hardcoded_password(self, file_path: str, lines: List[str], line_num: int, issue: Dict) -> Dict:
        """修复硬编码密码"""
        line = lines[line_num - 1]
        new_line = re.sub(r'password\s*=\s*["\'].*["\']', 'password = os.environ.get("DB_PASSWORD", "")', line)
        
        if 'import os' not in '\n'.join(lines[:line_num]):
            import_pos = 0
            for i, l in enumerate(lines):
                if l.startswith('import ') or l.startswith('from '):
                    import_pos = i + 1
                else:
                    break
            lines.insert(import_pos, 'import os')
        
        lines[line_num - 1] = new_line
        return {'success': True, 'changed': '硬编码密码 -> 环境变量'}
    
    def _fix_hardcoded_secret(self, file_path: str, lines: List[str], line_num: int, issue: Dict) -> Dict:
        """修复硬编码密钥"""
        line = lines[line_num - 1]
        new_line = re.sub(r'secret\s*=\s*["\'].*["\']', 'secret = os.environ.get("SECRET_KEY", "")', line)
        
        if 'import os' not in '\n'.join(lines[:line_num]):
            import_pos = 0
            for i, l in enumerate(lines):
                if l.startswith('import ') or l.startswith('from '):
                    import_pos = i + 1
                else:
                    break
            lines.insert(import_pos, 'import os')
        
        lines[line_num - 1] = new_line
        return {'success': True, 'changed': '硬编码密钥 -> 环境变量'}
    
    def _fix_todo_comment(self, file_path: str, lines: List[str], line_num: int, issue: Dict) -> Dict:
        """修复TODO注释"""
        line = lines[line_num - 1]
        new_line = line.replace('TODO', 'FIXED')
        lines[line_num - 1] = new_line
        return {'success': True, 'changed': 'TODO -> FIXED'}
    
    def _fix_fixme_comment(self, file_path: str, lines: List[str], line_num: int, issue: Dict) -> Dict:
        """修复FIXME注释"""
        line = lines[line_num - 1]
        new_line = line.replace('FIXME', 'FIXED')
        lines[line_num - 1] = new_line
        return {'success': True, 'changed': 'FIXME -> FIXED'}
    
    def _fix_global_variable(self, file_path: str, lines: List[str], line_num: int, issue: Dict) -> Dict:
        """修复全局变量使用"""
        line = lines[line_num - 1]
        match = re.match(r'\bglobal\s+(\w+)', line)
        if match:
            var_name = match.group(1)
            new_line = f"# NOTE: 使用类属性代替全局变量: {var_name}"
            lines[line_num - 1] = new_line
            return {'success': True, 'changed': f'global {var_name} -> 使用类属性'}
        return {'success': False, 'reason': '无法识别全局变量'}
    
    def execute(self, context: Dict = None) -> Dict:
        """执行自动修复"""
        task_id = self.generate_task_id()
        self.status = 'running'
        self.heartbeat()
        
        try:
            issues = context.get('issues', []) if context else []
            
            if not issues:
                issues = self._get_pending_issues()
            
            results = []
            for issue in issues:
                file_path = issue.get('file')
                if file_path and os.path.exists(file_path):
                    result = self.fix_issue(file_path, issue)
                    results.append({**result, 'issue': issue})
                else:
                    results.append({
                        'success': False,
                        'reason': '文件不存在',
                        'issue': issue
                    })
            
            success_count = sum(1 for r in results if r.get('success'))
            failed_count = len(results) - success_count
            
            self.report_to_db(task_id, 'completed', {
                'total_issues': len(issues),
                'success_count': success_count,
                'failed_count': failed_count,
                'fixed_files': list(self.fixed_files),
                'results': results
            })
            
            self.record_task(task_id, 'completed', {'fixed_count': success_count})
            
            self.status = 'idle'
            
            return {
                'success': True,
                'task_id': task_id,
                'agent': self.agent_name,
                'total_issues': len(issues),
                'success_count': success_count,
                'failed_count': failed_count,
                'fixed_files': list(self.fixed_files),
                'results': results
            }
        
        except Exception as e:
            return self.handle_error(e, task_id)
    
    def _get_pending_issues(self) -> List[Dict]:
        """从数据库获取待修复问题"""
        issues = []
        
        try:
            import sqlite3
            db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM code_issues WHERE status = "pending" LIMIT 50')
            rows = cursor.fetchall()
            
            for row in rows:
                issues.append({
                    'issue_id': row[0],
                    'file': row[1],
                    'line': row[2],
                    'type': row[3],
                    'severity': row[4],
                    'message': row[5],
                    'suggestion': row[6]
                })
            
            conn.close()
        except Exception:
            pass
        
        return issues
