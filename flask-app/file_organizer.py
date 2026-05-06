#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统文件整理和路径修复工具
根据AI建议整理系统文件，归类同类型文件文档，自动修复路径引用
"""
import os
import re
import sqlite3
import hashlib
import json
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'app.db')

class FileOrganizer:
    """文件整理器"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.db_path = DATABASE_PATH
        self.file_extensions = {
            '.py': 'Python脚本',
            '.js': 'JavaScript脚本',
            '.html': 'HTML页面',
            '.css': 'CSS样式',
            '.md': 'Markdown文档',
            '.json': 'JSON数据',
            '.sh': 'Shell脚本',
            '.sql': 'SQL脚本',
            '.txt': '文本文件',
            '.yml': 'YAML配置',
            '.yaml': 'YAML配置',
            '.xml': 'XML配置',
            '.env': '环境变量',
        }
        
        self.category_rules = {
            'AI系统': ['ai_', 'brain', 'learning', 'employee'],
            '考试系统': ['exam', 'test', 'question', 'paper'],
            '用户系统': ['user', 'login', 'auth', 'permission'],
            '系统工具': ['fix', 'debug', 'check', 'monitor'],
            '备份相关': ['backup', 'restore', 'snapshot'],
            '部署脚本': ['deploy', 'docker', 'start', 'run'],
        }
        
        self.duplicate_files = []
        self.path_issues = []
        self.file_categories = defaultdict(list)
        self.fix_recommendations = []
    
    def calculate_file_hash(self, filepath):
        """计算文件MD5哈希"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def scan_project(self):
        """扫描项目文件"""
        print("[1/5] 扫描项目文件结构...")
        all_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
            
            for file in files:
                if file.startswith('.') or file.endswith('.pyc'):
                    continue
                    
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, self.project_root)
                
                ext = os.path.splitext(file)[1].lower()
                category = self.categorize_file(file, ext)
                
                file_info = {
                    'path': filepath,
                    'relative_path': rel_path,
                    'name': file,
                    'extension': ext,
                    'category': category,
                    'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S') if os.path.exists(filepath) else None,
                    'hash': self.calculate_file_hash(filepath)
                }
                
                all_files.append(file_info)
                self.file_categories[category].append(file_info)
        
        print(f"  发现 {len(all_files)} 个文件")
        return all_files
    
    def categorize_file(self, filename, ext):
        """分类文件"""
        filename_lower = filename.lower()
        
        for category, keywords in self.category_rules.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return category
        
        return self.file_extensions.get(ext, '其他文件')
    
    def find_duplicates(self, all_files):
        """查找重复文件"""
        print("[2/5] 查找重复文件...")
        
        hash_map = defaultdict(list)
        for file_info in all_files:
            if file_info['hash']:
                hash_map[file_info['hash']].append(file_info)
        
        for file_hash, files in hash_map.items():
            if len(files) > 1:
                self.duplicate_files.append({
                    'hash': file_hash,
                    'files': files,
                    'action': '保留最新，删除其他' if len(files) > 1 else '保留'
                })
        
        print(f"  发现 {len(self.duplicate_files)} 组重复文件")
        return self.duplicate_files
    
    def analyze_path_references(self, all_files):
        """分析路径引用"""
        print("[3/5] 分析路径引用问题...")
        
        path_patterns = [
            (r'from\s+["\']([^"\']+)["\']', 'import'),
            (r'import\s+["\']([^"\']+)["\']', 'import'),
            (r'require\s*\(["\']([^"\']+)["\']\)', 'require'),
            (r'from\s+["\']\.\./([^"\']+)["\']', 'relative_import'),
            (r'href=["\']([^"\']+)["\']', 'href'),
            (r'src=["\']([^"\']+)["\']', 'src'),
        ]
        
        py_files = [f for f in all_files if f['extension'] == '.py']
        
        for file_info in py_files:
            try:
                with open(file_info['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern, ref_type in path_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match.startswith('/') or match.startswith('.'):
                            continue
                        
                        if not self.validate_import_path(file_info['path'], match):
                            self.path_issues.append({
                                'file': file_info['relative_path'],
                                'import': match,
                                'type': ref_type,
                                'status': 'missing'
                            })
            except Exception as e:
                pass
        
        print(f"  发现 {len(self.path_issues)} 个路径问题")
        return self.path_issues
    
    def validate_import_path(self, current_file, import_path):
        """验证导入路径是否存在"""
        current_dir = os.path.dirname(current_file)
        
        possible_paths = [
            os.path.join(current_dir, import_path),
            os.path.join(current_dir, import_path + '.py'),
            os.path.join(self.project_root, import_path),
            os.path.join(self.project_root, import_path + '.py'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return True
        return False
    
    def generate_fix_recommendations(self):
        """生成修复建议"""
        print("[4/5] 生成修复建议...")
        
        recommendations = []
        
        for dup in self.duplicate_files:
            rec = {
                'type': 'duplicate_files',
                'description': f"发现 {len(dup['files'])} 个重复文件: {[f['relative_path'] for f in dup['files']]}",
                'action': '整理重复文件，保留最新版本',
                'priority': 'high' if len(dup['files']) > 2 else 'medium',
                'files': [f['relative_path'] for f in dup['files']],
                'suggested_action': 'merge' if len(dup['files']) > 2 else 'keep_latest'
            }
            recommendations.append(rec)
        
        for issue in self.path_issues[:50]:
            rec = {
                'type': 'path_reference',
                'description': f"文件 {issue['file']} 中引用 {issue['import']} 不存在",
                'action': f"修复 {issue['import']} 引用或创建对应文件",
                'priority': 'medium',
                'file': issue['file'],
                'missing_import': issue['import']
            }
            recommendations.append(rec)
        
        self.fix_recommendations = recommendations
        print(f"  生成 {len(recommendations)} 条修复建议")
        return recommendations
    
    def save_to_database(self):
        """保存到数据库"""
        print("[5/5] 上传修复方案到数据库...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_organization_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                type TEXT,
                description TEXT,
                action TEXT,
                priority TEXT,
                file_path TEXT,
                details TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_category_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                file_path TEXT,
                file_name TEXT,
                file_size INTEGER,
                modified_time TEXT,
                file_hash TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for rec in self.fix_recommendations:
            cursor.execute('''
                INSERT INTO file_organization_log 
                (timestamp, type, description, action, priority, file_path, details, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                rec['type'],
                rec['description'],
                rec['action'],
                rec['priority'],
                rec.get('file', ''),
                json.dumps(rec, ensure_ascii=False),
                'pending'
            ))
        
        for category, files in self.file_categories.items():
            for file_info in files:
                cursor.execute('''
                    INSERT INTO file_category_index
                    (category, file_path, file_name, file_size, modified_time, file_hash, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    category,
                    file_info['relative_path'],
                    file_info['name'],
                    file_info['size'],
                    file_info['modified'],
                    file_info['hash'],
                    'active'
                ))
        
        conn.commit()
        conn.close()
        
        print(f"  已保存 {len(self.fix_recommendations)} 条修复建议")
        print(f"  已索引 {sum(len(f) for f in self.file_categories.values())} 个文件")
    
    def run(self):
        """运行整理流程"""
        print("=" * 60)
        print("系统文件整理和路径修复工具")
        print("=" * 60)
        
        all_files = self.scan_project()
        self.find_duplicates(all_files)
        self.analyze_path_references(all_files)
        self.generate_fix_recommendations()
        self.save_to_database()
        
        print("\n" + "=" * 60)
        print("整理完成！")
        print("=" * 60)
        print(f"总文件数: {len(all_files)}")
        print(f"重复文件组: {len(self.duplicate_files)}")
        print(f"路径问题: {len(self.path_issues)}")
        print(f"修复建议: {len(self.fix_recommendations)}")
        
        return {
            'total_files': len(all_files),
            'duplicates': len(self.duplicate_files),
            'path_issues': len(self.path_issues),
            'recommendations': len(self.fix_recommendations)
        }

if __name__ == '__main__':
    organizer = FileOrganizer()
    result = organizer.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))