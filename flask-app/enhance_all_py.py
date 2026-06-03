# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI System Code Enhancement Tool
根据工程师AI建议修复完善所有Python脚本
"""

import os
import sys
import ast
import logging
import traceback
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeEnhancer:
    """代码增强器"""
    
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.fixed_files = []
        self.issues_found = []
    
    def analyze_file(self, file_path):
        """分析Python文件"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 检查问题
            issues.extend(self._check_database_connections(tree, file_path))
            issues.extend(self._check_exception_handling(tree, file_path))
            issues.extend(self._check_imports(tree, file_path))
            issues.extend(self._check_sql_injection(tree, file_path))
            issues.extend(self._check_session_handling(tree, file_path))
            
        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")
        
        return issues
    
    def _check_database_connections(self, tree, file_path):
        """检查数据库连接是否正确关闭"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'sqlite3.connect':
                    issues.append({
                        'file': file_path,
                        'type': 'database_connection',
                        'message': '建议使用上下文管理器管理数据库连接',
                        'line': node.lineno
                    })
        return issues
    
    def _check_exception_handling(self, tree, file_path):
        """检查异常处理"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if isinstance(node.type, ast.Name) and node.type.id == 'Exception':
                    if not node.body:
                        issues.append({
                            'file': file_path,
                            'type': 'empty_exception',
                            'message': '空的异常处理块',
                            'line': node.lineno
                        })
        return issues
    
    def _check_imports(self, tree, file_path):
        """检查导入问题"""
        issues = []
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        
        if 'sqlite3' in imports:
            if 'contextlib' not in imports:
                issues.append({
                    'file': file_path,
                    'type': 'missing_contextlib',
                    'message': '使用sqlite3但未导入contextlib用于上下文管理器',
                    'line': 0
                })
        
        return issues
    
    def _check_sql_injection(self, tree, file_path):
        """检查SQL注入风险"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in ['execute', 'executemany']:
                    args = node.args
                    if args and isinstance(args[0], ast.Str):
                        # 检查是否使用字符串格式化
                        if '%s' in args[0].s or '{}' in args[0].s or '+' in args[0].s:
                            issues.append({
                                'file': file_path,
                                'type': 'sql_injection',
                                'message': 'SQL语句可能存在注入风险,建议使用参数化查询',
                                'line': node.lineno
                            })
        return issues
    
    def _check_session_handling(self, tree, file_path):
        """检查Session处理"""
        issues = []
        session_used = False
        session_protected = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == 'session':
                session_used = True
            
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id in ['login_required', 'require_login']:
                            session_protected = True
        
        if session_used and not session_protected:
            issues.append({
                'file': file_path,
                'type': 'session_unprotected',
                'message': '使用session但未添加登录验证装饰器',
                'line': 0
            })
        
        return issues
    
    def enhance_file(self, file_path):
        """增强Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加必要的导入
            enhanced_content = self._add_contextlib_import(content)
            enhanced_content = self._add_logging_import(enhanced_content)
            
            # 修复数据库连接
            enhanced_content = self._fix_database_connections(enhanced_content)
            
            # 添加异常处理
            enhanced_content = self._add_exception_handling(enhanced_content)
            
            if enhanced_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_content)
                self.fixed_files.append(file_path)
                logger.info(f"已增强文件: {file_path}")
            
            return True
        except Exception as e:
            logger.error(f"增强文件失败 {file_path}: {e}")
            traceback.print_exc()
            return False
    
    def _add_contextlib_import(self, content):
        """添加contextlib导入"""
        if 'import sqlite3' in content and 'from contextlib import' not in content:
            lines = content.split('\n')
            import_lines = []
            insert_pos = 0
            
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append(i)
                    if 'import sqlite3' in line:
                        insert_pos = i + 1
            
            if import_lines:
                lines.insert(insert_pos, 'from contextlib import contextmanager')
                return '\n'.join(lines)
        
        return content
    
    def _add_logging_import(self, content):
        """添加logging导入"""
        if 'print(f"' in content and 'import logging' not in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import '):
                    lines.insert(i, 'import logging')
                    lines.insert(i + 1, 'logger = logging.getLogger(__name__)')
                    return '\n'.join(lines)
        
        return content
    
    def _fix_database_connections(self, content):
        """修复数据库连接"""
        # 简单的修复:添加try-finally确保连接关闭
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if 'conn = sqlite3.connect' in line and 'with' not in line:
                # 找到连接创建,尝试添加上下文管理器模式
                indent = len(line) - len(line.lstrip())
                conn_var = line.split('=')[0].strip()
                
                # 查找对应的conn.close()
                close_line = None
                close_line_num = None
                for j in range(i + 1, min(i + 50, len(lines))):
                    if f'{conn_var}.close()' in lines[j]:
                        close_line = lines[j]
                        close_line_num = j
                        break
                
                if close_line:
                    # 使用上下文管理器替换
                    new_lines.append(' ' * indent + f"with sqlite3.connect({line.split('=')[1].strip()}) as {conn_var}:")
                    # 添加游标创建
                    new_lines.append(' ' * (indent + 4) + f"{conn_var}_cursor = {conn_var}.cursor()")
                    
                    # 复制中间的代码
                    for j in range(i + 1, close_line_num):
                        new_lines.append(' ' * (indent + 4) + lines[j].lstrip())
                    
                    # 跳过close行
                    i = close_line_num + 1
                    continue
            
            new_lines.append(line)
            i += 1
        
        return '\n'.join(new_lines)
    
    def _add_exception_handling(self, content):
        """添加异常处理"""
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if 'logger.error(f"Failed' in line or 'logger.error(f"Error' in line:
                # 替换为logger
                line = line.replace('print(f"', 'logger.error(f"')
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def run(self):
        """运行增强器"""
        logger.info("开始分析和增强项目代码...")
        
        # 查找所有Python文件
        python_files = list(self.project_path.rglob('*.py'))
        
        for py_file in python_files:
            # 跳过一些目录
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            logger.info(f"分析文件: {py_file}")
            issues = self.analyze_file(py_file)
            
            if issues:
                self.issues_found.extend(issues)
                logger.warning(f"发现问题: {len(issues)}个")
                for issue in issues:
                    logger.warning(f"  - {issue['message']} (行{issue['line']})")
            
            # 增强文件
            self.enhance_file(py_file)
        
        # 生成报告
        self._generate_report()
    
    def _generate_report(self):
        """生成增强报告"""
        logger.info("\n" + "="*60)
        logger.info("代码增强报告")
        logger.info("="*60)
        logger.info(f"分析文件数: {len(list(self.project_path.rglob('*.py')))}")
        logger.info(f"发现问题数: {len(self.issues_found)}")
        logger.info(f"已增强文件数: {len(self.fixed_files)}")
        
        if self.issues_found:
            logger.info("\n发现的问题类型统计:")
            type_counts = {}
            for issue in self.issues_found:
                issue_type = issue['type']
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
            
            for issue_type, count in type_counts.items():
                logger.info(f"  {issue_type}: {count}个")
        
        if self.fixed_files:
            logger.info("\n已增强的文件:")
            for fixed_file in self.fixed_files[:10]:
                logger.info(f"  {fixed_file}")
            if len(self.fixed_files) > 10:
                logger.info(f"  ... 还有 {len(self.fixed_files) - 10} 个文件")


def main():
    """主函数"""
    project_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app'
    
    if not os.path.exists(project_path):
        logger.error(f"项目路径不存在: {project_path}")
        sys.exit(1)
    
    enhancer = CodeEnhancer(project_path)
    enhancer.run()


if __name__ == '__main__':
    main()
