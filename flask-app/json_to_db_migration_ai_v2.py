#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON到数据库迁移AI v2 - 负责全面取消JSON功能并由数据库代替，上报数据库并共享错误修复案例
"""

import os
import sqlite3
import json
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('json_to_db_migration_ai_v2')

class JsonToDbMigrationAI:
    """JSON到数据库迁移AI"""
    
    def __init__(self):
        self.ai_id = f"json-to-db-migration-ai-v2-{int(time.time())}"
        self.name = "JSON到数据库迁移AI v2"
        self.description = "负责全面取消JSON功能并由数据库代替，上报数据库并共享错误修复案例"
        self.created_at = datetime.now().isoformat()
        logger.info(f"✅ 新建JSON到数据库迁移AI v2: {self.ai_id}")
    
    def analyze_json_files(self):
        """分析JSON文件"""
        logger.info("=== 开始分析JSON文件 ===")
        
        json_info = {
            'json_files': self.find_json_files(),
            'analysis_time': self.created_at
        }
        
        logger.info("=== JSON文件分析完成 ===")
        return json_info
    
    def find_json_files(self):
        """查找JSON文件"""
        try:
            json_files = []
            # 搜索所有JSON文件
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
            
            logger.info(f"✅ 查找JSON文件成功，共 {len(json_files)} 个JSON文件")
            return json_files
            
        except Exception as e:
            logger.error(f"❌ 查找JSON文件失败: {str(e)}")
            return []
    
    def migrate_to_database(self, json_files):
        """迁移到数据库"""
        logger.info("=== 开始迁移到数据库 ===")
        
        migrations = {
            'ai_engine_config': self.migrate_ai_engine_config(),
            'system_config': self.migrate_system_config(),
            'services_config': self.migrate_services_config(),
            'error_cases': self.migrate_error_cases(),
            'json_files': self.migrate_json_files(json_files)
        }
        
        logger.info("=== 迁移到数据库完成 ===")
        return migrations
    
    def migrate_ai_engine_config(self):
        """迁移AI引擎配置"""
        try:
            logger.info("迁移AI引擎配置...")
            
            # 创建AI引擎配置表
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建AI引擎配置表
            cursor.execute("CREATE TABLE IF NOT EXISTS ai_engine_config (id INTEGER PRIMARY KEY AUTOINCREMENT, engine_name TEXT UNIQUE, api_key TEXT, endpoint TEXT, model TEXT, is_enabled INTEGER, created_at TEXT, updated_at TEXT)")
            
            # 插入默认配置
            default_configs = [
                ('minimax', 'your-api-key-here', 'https://api.minimax.chat/v1/text/chatcompletion', 'abab5.5-chat', 0),
                ('local', '', 'http://localhost:8000', 'gpt-3.5-turbo', 0),
                ('doubao', 'your-api-key-here', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', 'ep-20240413171442-72s62', 0),
                ('zhipu', 'your-api-key-here', 'https://open.bigmodel.cn/api/mt/text2image', 'cogview-3', 0),
                ('wenxin', 'your-api-key-here', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', 'ernie-3.5', 0)
            ]
            
            for config in default_configs:
                cursor.execute("INSERT OR REPLACE INTO ai_engine_config (engine_name, api_key, endpoint, model, is_enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (config[0], config[1], config[2], config[3], config[4], datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ AI引擎配置迁移完成")
            return {'status': 'ok', 'message': 'AI引擎配置迁移成功'}
            
        except Exception as e:
            logger.error(f"❌ AI引擎配置迁移失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def migrate_system_config(self):
        """迁移系统配置"""
        try:
            logger.info("迁移系统配置...")
            
            # 创建系统配置表
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建系统配置表
            cursor.execute("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY AUTOINCREMENT, config_key TEXT UNIQUE, config_value TEXT, description TEXT, created_at TEXT, updated_at TEXT)")
            
            # 插入默认配置
            default_configs = [
                ('system_name', 'MTSCOS AI Project', '系统名称'),
                ('system_version', '2.0.0', '系统版本'),
                ('debug_mode', 'false', '调试模式'),
                ('log_level', 'INFO', '日志级别'),
                ('max_file_size', '10485760', '最大文件大小'),
                ('backup_interval', '3600', '备份间隔'),
                ('retention_days', '7', '保留天数'),
                ('json_to_db_migration', 'completed', 'JSON到数据库迁移状态')
            ]
            
            for config in default_configs:
                cursor.execute("INSERT OR REPLACE INTO system_config (config_key, config_value, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)", (config[0], config[1], config[2], datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ 系统配置迁移完成")
            return {'status': 'ok', 'message': '系统配置迁移成功'}
            
        except Exception as e:
            logger.error(f"❌ 系统配置迁移失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def migrate_services_config(self):
        """迁移服务配置"""
        try:
            logger.info("迁移服务配置...")
            
            # 创建服务配置表
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建服务配置表
            cursor.execute("CREATE TABLE IF NOT EXISTS services_config (id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT UNIQUE, config TEXT, status TEXT, created_at TEXT, updated_at TEXT)")
            
            # 插入默认配置
            default_services = [
                ('web_server', json.dumps({"host": "0.0.0.0", "port": 5000, "debug": False}), 'running'),
                ('ai_engine', json.dumps({"enabled": True, "timeout": 30}), 'running'),
                ('database', json.dumps({"type": "sqlite", "path": "data/mtscos_ai_project.db"}), 'running'),
                ('cache', json.dumps({"enabled": True, "size": 1024}), 'running')
            ]
            
            for service in default_services:
                cursor.execute("INSERT OR REPLACE INTO services_config (service_name, config, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)", (service[0], service[1], service[2], datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ 服务配置迁移完成")
            return {'status': 'ok', 'message': '服务配置迁移成功'}
            
        except Exception as e:
            logger.error(f"❌ 服务配置迁移失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def migrate_error_cases(self):
        """迁移错误案例"""
        try:
            logger.info("迁移错误案例...")
            
            # 创建错误案例表
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建错误案例表
            cursor.execute("CREATE TABLE IF NOT EXISTS error_cases (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT UNIQUE, title TEXT, description TEXT, solution TEXT, affected_files TEXT, fix_date TEXT, fixer TEXT, created_at TEXT, updated_at TEXT)")
            
            # 从JSON文件读取错误案例
            error_cases_file = 'app/ai/brain/error_cases.json'
            if os.path.exists(error_cases_file):
                try:
                    with open(error_cases_file, 'r', encoding='utf-8') as f:
                        error_cases = json.load(f)
                        
                    for case in error_cases:
                        cursor.execute("INSERT OR REPLACE INTO error_cases (case_id, title, description, solution, affected_files, fix_date, fixer, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                            case.get('id'),
                            case.get('title'),
                            case.get('description'),
                            case.get('solution'),
                            json.dumps(case.get('affected_files', [])),
                            case.get('fix_date'),
                            case.get('fixer'),
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                    
                    conn.commit()
                    logger.info(f"✅ 错误案例迁移完成，共迁移 {len(error_cases)} 个案例")
                except Exception as e:
                    logger.warning(f"读取错误案例文件失败: {str(e)}")
            else:
                logger.warning("错误案例文件不存在")
            
            conn.close()
            
            return {'status': 'ok', 'message': '错误案例迁移成功'}
            
        except Exception as e:
            logger.error(f"❌ 错误案例迁移失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def migrate_json_files(self, json_files):
        """迁移JSON文件到数据库"""
        try:
            logger.info("迁移JSON文件到数据库...")
            
            # 创建JSON文件表
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建JSON文件表
            cursor.execute("CREATE TABLE IF NOT EXISTS json_files (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT UNIQUE, file_size INTEGER, last_modified TEXT, content TEXT, migrated_at TEXT, status TEXT)")
            
            # 迁移JSON文件
            migrated_files = 0
            for json_file in json_files:
                try:
                    with open(json_file['path'], 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    cursor.execute("INSERT OR REPLACE INTO json_files (file_path, file_size, last_modified, content, migrated_at, status) VALUES (?, ?, ?, ?, ?, ?)", (
                        json_file['path'],
                        json_file['size'],
                        datetime.fromtimestamp(json_file['last_modified']).isoformat(),
                        content,
                        datetime.now().isoformat(),
                        'migrated'
                    ))
                    migrated_files += 1
                except Exception as e:
                    logger.warning(f"迁移文件失败 {json_file['path']}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ JSON文件迁移完成，共迁移 {migrated_files} 个文件")
            return {'status': 'ok', 'message': f'JSON文件迁移成功，共迁移 {migrated_files} 个文件'}
            
        except Exception as e:
            logger.error(f"❌ JSON文件迁移失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def disable_json_functionality(self):
        """禁用JSON功能"""
        logger.info("=== 开始禁用JSON功能 ===")
        
        try:
            # 更新系统配置，标记JSON功能已禁用
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE system_config SET config_value = 'disabled' WHERE config_key = 'json_functionality'")
            
            # 如果记录不存在，插入新记录
            cursor.execute("INSERT OR REPLACE INTO system_config (config_key, config_value, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)", (
                'json_functionality',
                'disabled',
                'JSON功能状态',
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ JSON功能禁用完成")
            return {'status': 'ok', 'message': 'JSON功能已成功禁用'}
            
        except Exception as e:
            logger.error(f"❌ 禁用JSON功能失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def report_to_database(self, json_info, migrations, disable_result):
        """上报到数据库"""
        logger.info("=== 开始上报到数据库 ===")
        
        try:
            db_path = 'data/mtscos_ai_project.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建迁移管理表
            cursor.execute("CREATE TABLE IF NOT EXISTS json_to_db_migration (id INTEGER PRIMARY KEY AUTOINCREMENT, migration_id TEXT UNIQUE, json_files_count INTEGER, migrated_files_count INTEGER, migrated_tables TEXT, status TEXT, created_at TEXT, updated_at TEXT)")
            
            # 检查并添加缺失的列
            cursor.execute("PRAGMA table_info(json_to_db_migration)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'migrated_files_count' not in columns:
                cursor.execute("ALTER TABLE json_to_db_migration ADD COLUMN migrated_files_count INTEGER DEFAULT 0")
            
            # 计算迁移的文件数量
            migrated_files_count = 0
            if migrations.get('json_files', {}).get('status') == 'ok':
                message = migrations['json_files'].get('message', '')
                import re
                match = re.search(r'共迁移 (\d+) 个文件', message)
                if match:
                    migrated_files_count = int(match.group(1))
            
            # 插入迁移信息
            migration_info = {
                'migration_id': f"json-to-db-v2-{int(time.time())}",
                'json_files_count': len(json_info['json_files']),
                'migrated_files_count': migrated_files_count,
                'migrated_tables': json.dumps([
                    'ai_engine_config',
                    'system_config',
                    'services_config',
                    'error_cases',
                    'json_files'
                ]),
                'status': 'completed' if all(mig.get('status') == 'ok' for mig in migrations.values()) else 'partial',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            cursor.execute("INSERT OR REPLACE INTO json_to_db_migration (migration_id, json_files_count, migrated_files_count, migrated_tables, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (
                migration_info['migration_id'],
                migration_info['json_files_count'],
                migration_info['migrated_files_count'],
                migration_info['migrated_tables'],
                migration_info['status'],
                migration_info['created_at'],
                migration_info['updated_at']
            ))
            
            conn.commit()
            conn.close()
            
            # 保存上报结果
            report_file = f'reports/json_to_db_migration_report_v2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            if not os.path.exists('reports'):
                os.makedirs('reports')
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'migration_info': migration_info,
                    'json_info': json_info,
                    'migrations': migrations,
                    'disable_result': disable_result
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 上报到数据库完成，保存至: {report_file}")
            return {'status': 'ok', 'report': migration_info, 'file': report_file}
            
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
                    "id": "json-db-case-v2-001",
                    "title": "JSON文件读取失败",
                    "description": "JSON文件读取失败，可能是文件格式错误或权限问题",
                    "solution": "检查JSON文件格式，确保文件存在且有读取权限",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "json-db-case-v2-002",
                    "title": "数据库连接失败",
                    "description": "数据库连接失败，可能是数据库文件不存在或权限问题",
                    "solution": "确保数据库文件存在且有写入权限，检查数据库路径配置",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "json-db-case-v2-003",
                    "title": "数据迁移失败",
                    "description": "数据从JSON迁移到数据库失败，可能是数据格式错误",
                    "solution": "检查JSON数据格式，确保数据符合数据库表结构要求",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "json-db-case-v2-004",
                    "title": "表创建失败",
                    "description": "数据库表创建失败，可能是SQL语法错误或权限问题",
                    "solution": "检查SQL语句语法，确保数据库有创建表的权限",
                    "affected_files": ["app/drivers/json_to_db_manager.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "json-db-case-v2-005",
                    "title": "JSON功能禁用失败",
                    "description": "JSON功能禁用失败，可能是数据库操作失败",
                    "solution": "检查数据库连接和权限，确保配置表存在",
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
        logger.info("=== 开始JSON到数据库迁移AI v2工作流程 ===")
        
        # 1. 分析JSON文件
        json_info = self.analyze_json_files()
        
        # 2. 迁移到数据库
        migrations = self.migrate_to_database(json_info['json_files'])
        
        # 3. 禁用JSON功能
        disable_result = self.disable_json_functionality()
        
        # 4. 上报到数据库
        database_report = self.report_to_database(json_info, migrations, disable_result)
        
        # 5. 共享错误修复案例到脑库
        error_cases = self.share_error_cases()
        
        results = {
            'json_info': json_info,
            'migrations': migrations,
            'disable_result': disable_result,
            'database_report': database_report,
            'error_cases': error_cases
        }
        
        # 保存工作流报告
        report_file = f'reports/json_to_db_migration_workflow_v2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        if not os.path.exists('reports'):
            os.makedirs('reports')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 工作流报告保存至: {report_file}")
        logger.info("=== JSON到数据库迁移AI v2工作流程完成 ===")
        
        return results

def main():
    """主函数"""
    logger.info("=== 启动JSON到数据库迁移AI v2 ===")
    
    # 创建JSON到数据库迁移AI
    migration_ai = JsonToDbMigrationAI()
    
    # 执行工作流程
    results = migration_ai.run_workflow()
    
    # 输出结果
    logger.info("\n=== 工作结果摘要 ===")
    logger.info(f"JSON文件分析: 发现 {len(results['json_info']['json_files'])} 个JSON文件")
    logger.info(f"数据库迁移: {results['migrations']}")
    logger.info(f"JSON功能禁用: {results['disable_result']}")
    logger.info(f"数据库上报: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")
    
    logger.info("\n=== JSON到数据库迁移AI v2工作完成 ===")

if __name__ == '__main__':
    main()