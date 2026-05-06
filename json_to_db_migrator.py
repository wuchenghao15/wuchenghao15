#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSON数据迁移与数据库统一管理脚本"""

import os
import re
# JSON import removed - using database
import sqlite3
import glob
from datetime import datetime
from pathlib import Path

class JSONMigrator:
    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.project_dir = os.getcwd()
        self.migrated_count = 0
        self.deleted_files = []
        self.modified_files = []
        self.errors = []

    def connect(self):
        return sqlite3.connect(self.db_path)

    def find_all_json_files(self):
        """查找所有JSON文件"""
        json_files = []
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    if 'node_modules' not in root and '.git' not in root:
                        json_files.append(file_path)
        return json_files

    def create_data_tables(self):
        """创建统一的数据表"""
        conn = self.connect()
        cursor = conn.cursor()

        tables = [
            '''CREATE TABLE IF NOT EXISTS json_data_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT UNIQUE NOT NULL,
                data_key TEXT,
                data_type TEXT,
                content TEXT,
                record_count INTEGER DEFAULT 0,
                migrated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS system_configs (
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                config_type TEXT,
                description TEXT,
                category TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''',
                knowledge_type TEXT NOT NULL,
                knowledge_key TEXT,
                knowledge_value TEXT,
                domain TEXT,
                confidence REAL DEFAULT 0.5,
                source_file TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS migration_logs (
                target TEXT,
                status TEXT,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''CREATE TABLE IF NOT EXISTS code_replacement_map (
                original_pattern TEXT NOT NULL,
                replacement_pattern TEXT NOT NULL,
                file_type TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            '''
        ]

            cursor.execute(sql)
        conn.commit()
        print("  ✅ 数据表创建完成")

    def migrate_json_to_database(self, json_file):
        """将JSON文件数据迁移到数据库"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cursor = conn.cursor()
            data_type = type(data).__name__
            record_count = 0

            if isinstance(data, dict):
                for key, value in data.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO json_data_store
                        (source_file, data_key, data_type, content, record_count, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        os.path.basename(json_file),
                        key,
                        type(value).__name__,
                        str(value),
                        len(value) if isinstance(value, (list, dict)) else 1,
                        datetime.now().isoformat()
                    ))
                    record_count += 1
            elif isinstance(data, list):
                cursor.execute('''
                    INSERT OR REPLACE INTO json_data_store
                    (source_file, data_key, data_type, content, record_count, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    os.path.basename(json_file),
                    'root_array',
                    'list',
                    str(data),
                    len(data),
                    datetime.now().isoformat()
                record_count = len(data)
            conn.commit()

            print(f"  ✅ 迁移: {os.path.basename(json_file)} ({record_count} 条记录)")
        except Exception as e:
            print(f"  ❌ 迁移失败: {os.path.basename(json_file)} - {str(e)}")
            return False

        """删除JSON文件"""
            os.remove(json_file)
            print(f"  ✅ 删除: {os.path.basename(json_file)}")
        except Exception as e:
            print(f"  ❌ 删除失败: {os.path.basename(json_file)} - {str(e)}")
            return False

    def find_json_code_patterns(self):
        """查找代码中的JSON相关模式"""
        patterns = [
            (r'import\s+json', '# JSON import removed - using database
            (r'from\s+json\s+import', '# # from json import removed removed - using database storage'),
            (r'json\.load\(', 'JSON读取'),
            (r'json\.dump\(', 'JSON写入'),
            (r'json\.dumps\(', 'JSON序列化'),
            (r'json\.loads\(', 'JSON反序列化'),
            (r'\.json\b', 'JSON文件扩展名'),
            (r'open\([^)]*\.json', 'JSON文件打开'),
            (r'Path\([^)]*\.json', 'JSON路径'),
            (r'glob\([^)]*\.json', 'JSON glob'),
        ]
        return patterns

        """分析Python文件中的JSON使用"""

        json_usage = {}

            if 'node_modules' in root or '.git' in root or '__pycache__' in root:
            for file in files:
                    py_files.append(os.path.join(root, file))

        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_usage = []
                for pattern, desc in self.find_json_code_patterns():
                    matches = re.findall(pattern, content)
                    if matches:
                        file_usage.append({'pattern': desc, 'count': len(matches)})

                if file_usage:
                    json_usage[py_file] = file_usage
            except Exception:
                pass

        return json_usage
    def generate_replacement_code(self, usage_type, context=''):
        """生成替换代码（数据库版本）"""
        replacements = {
            '# JSON import removed - using database
': '# JSON imports removed - using database',
            '# # from json import removed removed - using database storage': '# JSON imports removed - using database',
            'JSON读取': 'db_manager.fetch_one/fetch_all',
            'JSON写入': 'db_manager.execute/insert',
            'JSON序列化': '直接存储到数据库',
            'JSON反序列化': '从数据库读取',
            'JSON文件扩展名': '.db',
            'JSON文件打开': '数据库连接',
            'JSON路径': '数据库表',
            'JSON glob': '数据库查询'
        }
        return replacements.get(usage_type, '# 需要手动替换')

    def replace_json_in_file(self, file_path, replacements_needed):
        """替换文件中的JSON代码"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            content = re.sub(r'import\s+json\s*\n?', '# JSON import removed - using database\n', content)
            content = re.sub(r'from\s+json\s+import\s+[^\n]+\n?', '# JSON import removed - using database\n', content)

            if 'json.load' in content:
                content = re.sub(
                    r'with\s+open\([^)]*\.json[^)]*\)\s+as\s+(\w+):\s*(\w+)\s*=\s*json\.load\(\1\)',
                    '# JSON load replaced with database read\ndb_manager.fetch_all(...)',
                    content
                )

                content = re.sub(
                    r'with\s+open\([^)]*\.json[^)]*\)\s+as\s+(\w+):\s*json\.dump\([^,]+,\s*\1\)',
                    '# JSON dump replaced with database write\ndb_manager.execute(...)',
                    content
                )

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            return False
        except Exception as e:
            self.errors.append({'file': file_path, 'error': str(e)})
            return False

        conn = self.connect()
        cursor = conn.cursor()
            INSERT INTO migration_logs (action, target, status, details)
            VALUES (?, ?, ?, ?)
        conn.commit()
        conn.close()

    def run_migration(self):
        """执行完整的迁移流程"""
        print("="*70)
        print("         JSON数据迁移与数据库统一管理系统")
        print("="*70)

        print("\n[步骤1] 创建统一数据表...")
        self.create_data_tables()
        print("\n[步骤2] 查找所有JSON文件...")
        json_files = self.find_all_json_files()
        print(f"  发现 {len(json_files)} 个JSON文件")
        print("\n[步骤3] 迁移JSON数据到数据库...")
            self.log_migration('migrate', json_file, 'success' if not any(e['file'] == json_file for e in self.errors) else 'failed')
        json_usage = self.analyze_python_files()
        print(f"  发现 {len(json_usage)} 个文件使用JSON相关代码")
        for file_path in json_usage.keys():
            if self.replace_json_in_file(file_path, json_usage[file_path]):

        print("\n[步骤6] 删除JSON文件...")
        for json_file in json_files:
            self.delete_json_file(json_file)
            self.log_migration('delete', json_file, 'success')

        print("\n" + "="*70)
        print("                    迁移完成报告")
        print("="*70)
        print(f"  迁移的JSON文件: {self.migrated_count}")
        print(f"  删除的JSON文件: {len(self.deleted_files)}")
        print(f"  修改的代码文件: {len(self.modified_files)}")
        print(f"  错误数量: {len(self.errors)}")

        if self.errors:
            print("\n错误详情:")
            for error in self.errors[:10]:
                print(f"  - {error['file']}: {error['error']}")

        self.log_migration('migration_complete', 'all', 'success',
                          f'Migrated: {self.migrated_count}, Deleted: {len(self.deleted_files)}, Modified: {len(self.modified_files)}')

        return {
            'migrated': self.migrated_count,
            'deleted': len(self.deleted_files),
            'modified': len(self.modified_files),
            'errors': len(self.errors)
        }

def main():
    migrator = JSONMigrator()
    result = migrator.run_migration()
    print(f"\n迁移结果: {result}")

if __name__ == "__main__":
    main()
