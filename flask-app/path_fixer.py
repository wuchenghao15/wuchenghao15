#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径自动修复工具
自动修复项目中的路径引用问题
"""
import os
import re
import sqlite3
import json
from datetime import datetime

PROJECT_ROOT = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
import os
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

class PathFixer:
    """路径修复器"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.db_path = DATABASE_PATH
        self.fixed_count = 0
        self.failed_count = 0
        self.fix_log = []
    
    def get_common_import_mappings(self):
        """获取常用导入路径映射"""
        return {
            'app.ai': 'app.ai',
            'app.models': 'app.models',
            'app.utils': 'app.utils',
            'app.services': 'app.services',
            'app.routes': 'app.routes',
            'app.middlewares': 'app.middlewares',
            'app.api': 'app.api',
        }
    
    def fix_import_statement(self, content, file_path):
        """修复导入语句"""
        original = content
        file_dir = os.path.dirname(file_path)
        
        import_patterns = [
            (r'from\s+["\']\.(\.[^"\']+)["\']', r'from "\1"'),
            (r'from\s+["\']__init__["\']', ''),
            (r'import\s+["\']\.([^"\']+)["\']', r'import "\1"'),
        ]
        
        for pattern, replacement in import_patterns:
            content = re.sub(pattern, replacement, content)
        
        return content != original, content
    
    def fix_template_references(self, content):
        """修复模板引用"""
        original = content
        
        href_patterns = [
            (r'href=["\']/static/([^"\']+)["\']', r'href="{{ url_for(\'static\', filename=\'\1\') }}"'),
            (r'href=["\']/templates/([^"\']+)["\']', r'href="{{ url_for(\'\1\') }}"'),
        ]
        
        for pattern, replacement in href_patterns:
            content = re.sub(pattern, replacement, content)
        
        return content != original, content
    
    def fix_relative_paths(self, content):
        """修复相对路径"""
        original = content
        
        path_patterns = [
            (r'\.\./images/', '/static/images/'),
            (r'\.\./css/', '/static/css/'),
            (r'\.\./js/', '/static/js/'),
            (r'\.\./assets/', '/static/assets/'),
        ]
        
        for pattern, replacement in path_patterns:
            content = re.sub(pattern, replacement, content)
        
        return content != original, content
    
    def fix_file(self, file_path):
        """修复单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original = content
            changes = []
            
            if file_path.endswith('.py'):
                fixed, content = self.fix_import_statement(content, file_path)
                if fixed:
                    changes.append('fixed_imports')
            
            if file_path.endswith(('.html', '.js')):
                fixed, content = self.fix_template_references(content)
                if fixed:
                    changes.append('fixed_template_refs')
                
                fixed, content = self.fix_relative_paths(content)
                if fixed:
                    changes.append('fixed_relative_paths')
            
            if changes:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fix_log.append({
                    'file': file_path,
                    'changes': changes,
                    'status': 'success'
                })
                self.fixed_count += 1
                return True
            else:
                return False
                
        except Exception as e:
            self.fix_log.append({
                'file': file_path,
                'error': str(e),
                'status': 'failed'
            })
            self.failed_count += 1
            return False
    
    def scan_and_fix(self):
        """扫描并修复"""
        print("[路径修复] 开始扫描和修复...")
        
        flask_app_dir = os.path.join(self.project_root, 'flask-app')
        
        extensions = ['.py', '.html', '.js']
        
        for root, dirs, files in os.walk(flask_app_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    self.fix_file(file_path)
        
        print(f"  修复成功: {self.fixed_count} 个文件")
        print(f"  修复失败: {self.failed_count} 个文件")
        
        return self.fix_log
    
    def save_fix_log(self):
        """保存修复日志到数据库"""
        print("[路径修复] 保存修复日志到数据库...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS path_fix_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                file_path TEXT,
                changes TEXT,
                status TEXT
            )
        ''')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for log in self.fix_log:
            cursor.execute('''
                INSERT INTO path_fix_log (timestamp, file_path, changes, status)
                VALUES (?, ?, ?, ?)
            ''', (
                timestamp,
                log['file'],
                json.dumps(log.get('changes', []), ensure_ascii=False),
                log['status']
            ))
        
        conn.commit()
        conn.close()
        
        print(f"  已保存 {len(self.fix_log)} 条修复日志")
    
    def run(self):
        """运行修复流程"""
        print("=" * 60)
        print("路径自动修复工具")
        print("=" * 60)
        
        self.scan_and_fix()
        self.save_fix_log()
        
        print("\n" + "=" * 60)
        print("修复完成！")
        print("=" * 60)
        print(f"修复成功: {self.fixed_count}")
        print(f"修复失败: {self.failed_count}")
        
        return {
            'fixed': self.fixed_count,
            'failed': self.failed_count,
            'logs': self.fix_log[:10]
        }

if __name__ == '__main__':
    fixer = PathFixer()
    result = fixer.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))