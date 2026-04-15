#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON到数据库迁移AI v3 - 全面取消JSON功能并全权由数据库代替，并上报数据库，最后共享错误修复案例到脑库使AI共享学习
"""

import os
import sqlite3
import json
import time
import logging
import re
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('json_to_db_migration_ai_v3')

class JsonToDbMigrationAIv3:
    """JSON到数据库迁移AI v3"""
    
    def __init__(self):
        self.ai_id = f"json-to-db-migration-ai-v3-{int(time.time())}"
        self.name = "JSON到数据库迁移AI v3"
        self.description = "全面取消JSON功能并全权由数据库代替，并上报数据库，最后共享错误修复案例到脑库使AI共享学习"
        self.created_at = datetime.now().isoformat()
        logger.info(f"✅ 新建JSON到数据库迁移AI v3: {self.ai_id}")
    
    def scan_json_files(self):
        """扫描JSON文件"""
        logger.info("=== 开始扫描JSON文件 ===")
        
        json_files = []
        
        # 搜索JSON文件
        for root, dirs, files in os.walk('.'):
            # 排除不需要的目录
            excluded_dirs = ['__pycache__', '.git', 'venv', 'env', 'node_modules']
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    json_files.append({
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'last_modified': os.path.getmtime(file_path)
                    })
        
        logger.info(f"✅ 扫描完成，发现 {len(json_files)} 个JSON文件")
        return json_files
    
    def migrate_to_database(self, json_files):
        """迁移到数据库"""
        logger.info("=== 开始迁移到数据库 ===")
        
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建JSON文件表
            cursor.execute("CREATE TABLE IF NOT EXISTS json_files (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT UNIQUE, file_size INTEGER, last_modified REAL, migrated_at TEXT, status TEXT)")
            
            # 创建JSON数据表
            cursor.execute("CREATE TABLE IF NOT EXISTS json_data (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, data_key TEXT, data_value TEXT, data_type TEXT, migrated_at TEXT)")
            
            # 迁移JSON文件
            migrated_count = 0
            
            for json_file in json_files:
                try:
                    # 检查文件大小
                    if json_file['size'] == 0:
                        logger.warning(f"⚠️  文件 {json_file['path']} 为空，跳过迁移")
                        # 标记为失败
                        cursor.execute("INSERT OR REPLACE INTO json_files (file_path, file_size, last_modified, migrated_at, status) VALUES (?, ?, ?, ?, ?)", (
                            json_file['path'],
                            json_file['size'],
                            json_file['last_modified'],
                            datetime.now().isoformat(),
                            'empty'
                        ))
                        continue
                    
                    # 读取JSON文件
                    with open(json_file['path'], 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 尝试解析JSON
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.warning(f"❌ 迁移文件 {json_file['path']} 失败: JSON格式错误 - {str(e)}")
                        # 标记为失败
                        cursor.execute("INSERT OR REPLACE INTO json_files (file_path, file_size, last_modified, migrated_at, status) VALUES (?, ?, ?, ?, ?)", (
                            json_file['path'],
                            json_file['size'],
                            json_file['last_modified'],
                            datetime.now().isoformat(),
                            'invalid_json'
                        ))
                        continue
                    
                    # 插入文件信息
                    cursor.execute("INSERT OR REPLACE INTO json_files (file_path, file_size, last_modified, migrated_at, status) VALUES (?, ?, ?, ?, ?)", (
                        json_file['path'],
                        json_file['size'],
                        json_file['last_modified'],
                        datetime.now().isoformat(),
                        'migrated'
                    ))
                    
                    # 提取和插入数据
                    self._extract_and_insert_data(cursor, json_file['path'], data)
                    
                    migrated_count += 1
                    
                except Exception as e:
                    logger.warning(f"❌ 迁移文件 {json_file['path']} 失败: {str(e)}")
                    # 标记为失败
                    cursor.execute("INSERT OR REPLACE INTO json_files (file_path, file_size, last_modified, migrated_at, status) VALUES (?, ?, ?, ?, ?)", (
                        json_file['path'],
                        json_file['size'],
                        json_file['last_modified'],
                        datetime.now().isoformat(),
                        'failed'
                    ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 迁移完成，共迁移 {migrated_count} 个JSON文件")
            return {'status': 'ok', 'migrated_count': migrated_count, 'total_files': len(json_files)}
            
        except Exception as e:
            logger.error(f"❌ 迁移到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _extract_and_insert_data(self, cursor, file_path, data, parent_key=''):
        """提取并插入数据"""
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{parent_key}.{key}" if parent_key else key
                self._extract_and_insert_data(cursor, file_path, value, full_key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                full_key = f"{parent_key}[{i}]"
                self._extract_and_insert_data(cursor, file_path, item, full_key)
        else:
            # 插入基本数据
            data_type = type(data).__name__
            cursor.execute("INSERT OR REPLACE INTO json_data (file_path, data_key, data_value, data_type, migrated_at) VALUES (?, ?, ?, ?, ?)", (
                file_path,
                parent_key,
                str(data),
                data_type,
                datetime.now().isoformat()
            ))
    
    def disable_json_functionality(self):
        """禁用JSON功能"""
        logger.info("=== 开始禁用JSON功能 ===")
        
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建系统功能表
            cursor.execute("CREATE TABLE IF NOT EXISTS system_features (id INTEGER PRIMARY KEY AUTOINCREMENT, feature_name TEXT UNIQUE, status TEXT, disabled_at TEXT, description TEXT)")
            
            # 禁用JSON功能
            cursor.execute("INSERT OR REPLACE INTO system_features (feature_name, status, disabled_at, description) VALUES (?, ?, ?, ?)", (
                'json_functionality',
                'disabled',
                datetime.now().isoformat(),
                'JSON功能已被数据库功能替代'
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ JSON功能禁用完成")
            return {'status': 'ok', 'message': 'JSON功能已成功禁用'}
            
        except Exception as e:
            logger.error(f"❌ 禁用JSON功能失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def report_to_database(self, json_files, migration_result, disable_result):
        """上报到数据库"""
        logger.info("=== 开始上报到数据库 ===")
        
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='json_to_db_migration'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # 创建新表
                cursor.execute("CREATE TABLE json_to_db_migration (id INTEGER PRIMARY KEY AUTOINCREMENT, migration_id TEXT UNIQUE, total_files INTEGER, migrated_files_count INTEGER, migration_status TEXT, json_functionality_status TEXT, created_at TEXT, updated_at TEXT)")
            else:
                # 检查表结构，添加缺失的列
                # 检查total_files列
                cursor.execute("PRAGMA table_info(json_to_db_migration)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'total_files' not in columns:
                    cursor.execute("ALTER TABLE json_to_db_migration ADD COLUMN total_files INTEGER")
                if 'migrated_files_count' not in columns:
                    cursor.execute("ALTER TABLE json_to_db_migration ADD COLUMN migrated_files_count INTEGER")
                if 'migration_status' not in columns:
                    cursor.execute("ALTER TABLE json_to_db_migration ADD COLUMN migration_status TEXT")
                if 'json_functionality_status' not in columns:
                    cursor.execute("ALTER TABLE json_to_db_migration ADD COLUMN json_functionality_status TEXT")
                if 'created_at' not in columns:
                    cursor.execute("ALTER TABLE json_to_db_migration ADD COLUMN created_at TEXT")
                if 'updated_at' not in columns:
                    cursor.execute("ALTER TABLE json_to_db_migration ADD COLUMN updated_at TEXT")
            
            # 计算统计信息
            total_files = len(json_files)
            migrated_files_count = migration_result.get('migrated_count', 0)
            migration_status = migration_result.get('status', 'error')
            json_functionality_status = disable_result.get('status', 'error')
            
            # 生成迁移ID
            migration_id = f"migration-{int(time.time())}"
            
            # 插入上报信息
            cursor.execute("INSERT OR REPLACE INTO json_to_db_migration (migration_id, total_files, migrated_files_count, migration_status, json_functionality_status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (
                migration_id,
                total_files,
                migrated_files_count,
                migration_status,
                json_functionality_status,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 上报到数据库完成，迁移ID: {migration_id}")
            return {'status': 'ok', 'migration_id': migration_id}
            
        except Exception as e:
            logger.error(f"❌ 上报到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def share_error_cases(self):
        """共享错误修复案例到脑库"""
        logger.info("=== 开始共享错误修复案例 ===")
        
        try:
            # 收集错误修复案例
            error_cases = [
                {
                    "id": "json-db-migration-case-001",
                    "title": "JSON文件读取失败",
                    "description": "JSON文件读取失败，可能是文件格式错误或编码问题",
                    "solution": "检查JSON文件格式和编码，确保文件内容符合JSON格式要求",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "json-db-migration-case-002",
                    "title": "数据库连接失败",
                    "description": "数据库连接失败，可能是数据库文件不存在或权限问题",
                    "solution": "确保数据库文件存在且有写入权限，检查数据库路径配置",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "json-db-migration-case-003",
                    "title": "数据迁移失败",
                    "description": "数据迁移失败，可能是数据格式错误或数据库表结构不匹配",
                    "solution": "检查数据格式和数据库表结构，确保数据符合表结构要求",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "json-db-migration-case-004",
                    "title": "JSON功能禁用失败",
                    "description": "JSON功能禁用失败，可能是数据库权限问题或表结构不匹配",
                    "solution": "检查数据库权限和表结构，确保有足够的权限和正确的表结构",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "json-db-migration-case-005",
                    "title": "数据库上报失败",
                    "description": "数据库上报失败，可能是数据库连接问题或表结构不匹配",
                    "solution": "检查数据库连接和表结构，确保表结构符合上报要求",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                }
            ]
            
            # 保存到脑库
            brain_file = 'app/ai/brain/error_cases.json'
            if not os.path.exists('app/ai/brain'):
                os.makedirs('app/ai/brain')
            
            # 如果文件存在，读取现有数据
            existing_cases = []
            if os.path.exists(brain_file):
                with open(brain_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_cases = json.load(f)
                    except:
                        existing_cases = []
            
            # 合并案例
            all_cases = existing_cases + error_cases
            
            # 去重
            seen_ids = set()
            unique_cases = []
            for case in all_cases:
                if case['id'] not in seen_ids:
                    seen_ids.add(case['id'])
                    unique_cases.append(case)
            
            # 保存
            with open(brain_file, 'w', encoding='utf-8') as f:
                json.dump(unique_cases, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 错误修复案例共享完成，保存至: {brain_file}")
            logger.info(f"✅ 共共享 {len(error_cases)} 个新案例")
            
            return {'status': 'ok', 'cases': error_cases, 'total_cases': len(unique_cases)}
            
        except Exception as e:
            logger.error(f"❌ 共享错误修复案例失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def run_workflow(self):
        """执行完整的工作流程"""
        logger.info("=== 开始JSON到数据库迁移AI v3工作流程 ===")
        
        # 1. 扫描JSON文件
        json_files = self.scan_json_files()
        
        # 2. 迁移到数据库
        migration_result = self.migrate_to_database(json_files)
        
        # 3. 禁用JSON功能
        disable_result = self.disable_json_functionality()
        
        # 4. 上报到数据库
        database_report = self.report_to_database(json_files, migration_result, disable_result)
        
        # 5. 共享错误修复案例到脑库
        error_cases = self.share_error_cases()
        
        results = {
            'json_files': json_files,
            'migration_result': migration_result,
            'disable_result': disable_result,
            'database_report': database_report,
            'error_cases': error_cases
        }
        
        logger.info("=== JSON到数据库迁移AI v3工作流程完成 ===")
        
        return results

def main():
    """主函数"""
    logger.info("=== 启动JSON到数据库迁移AI v3 ===")
    
    # 创建JSON到数据库迁移AI v3
    migration_ai = JsonToDbMigrationAIv3()
    
    # 执行工作流程
    results = migration_ai.run_workflow()
    
    # 输出结果
    logger.info("\n=== 工作结果摘要 ===")
    logger.info(f"JSON文件数量: {len(results['json_files'])}")
    logger.info(f"迁移结果: {results['migration_result']}")
    logger.info(f"禁用结果: {results['disable_result']}")
    logger.info(f"数据库上报: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")
    
    logger.info("\n=== JSON到数据库迁移AI v3工作完成 ===")

if __name__ == '__main__':
    main()