# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新增AI并优化文档管理系统脚本
专门负责管理更新说明文档、工程文档和具体详细说明书
"""

import os
import sys
import logging
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhance_ai_and_documentation_system')

class AIAndDocumentationSystemEnhancer:
    """AI和文档管理系统增强器类"""

    def __init__(self):
        """初始化AI和文档管理系统增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.documentation_dir = os.path.join(self.data_dir, 'documentation_system')

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.documentation_dir, exist_ok=True)

        self.new_ai_types = [
            {
                'ai_type': 'documentation_management_ai',
                'name': '文档管理AI',
                'description': '专门负责文档的整体管理和组织',
                'functions': [
                    '文档结构管理',
                    '文档版本控制',
                    '文档分类管理',
                    '文档访问控制'
                ],
                'required_skills': ['documentation_management', 'version_control', 'organization']
            },
            {
                'ai_type': 'technical_documentation_ai',
                'name': '技术文档AI',
                'description': '专门负责工程文档和技术说明书的生成和更新',
                'functions': [
                    '技术文档生成',
                    '架构文档维护',
                    '技术规范编写'
                ],
                'required_skills': ['technical_writing', 'api_documentation', 'architecture_design']
            },
            {
                'ai_type': 'user_documentation_ai',
                'name': '用户文档AI',
                'description': '专门负责用户文档和使用说明书的生成和更新',
                'functions': [
                    '用户手册编写',
                    '操作指南生成',
                    '用户培训材料'
                ],
                'required_skills': ['user_writing', 'instructional_design', 'user_experience']
            },
            {
                'ai_type': 'change_documentation_ai',
                'name': '变更文档AI',
                'description': '专门负责变更日志和更新说明的管理',
                'functions': [
                    '更新说明文档生成',
                    '变更日志管理',
                ],
                'required_skills': ['change_documentation', 'changelog_management', 'release_notes']
            }
        ]

        self.documentation_system_configs = {
            'documentation_system': {
                'enabled': True,
                'documentation_features': ['management', 'technical', 'user', 'change'],
                'auto_backup': True,
                'backup_frequency': 'daily',
                'retention_period': 365,
                'compression': True
            },
            'documentation_management': {
                'enabled': True,
                'document_types': ['technical', 'user', 'change', 'training'],
                'version_control': True,
                'access_control': True,
                'search_enabled': True,
                'metadata_enabled': True
            },
            'technical_documentation': {
                'enabled': True,
                'document_formats': ['markdown', 'html', 'pdf'],
                'api_documentation': True,
                'architecture_documentation': True,
                'code_documentation': True,
            },
            'user_documentation': {
                'enabled': True,
                'document_formats': ['markdown', 'html', 'pdf'],
                'user_manual': True,
                'quick_start_guide': True,
                'faq': True,
                'troubleshooting_guide': True
            },
            'change_documentation': {
                'enabled': True,
                'document_formats': ['markdown', 'html', 'pdf'],
                'release_notes': True,
                'changelog': True,
                'upgrade_guide': True,
                'migration_guide': True
            },
            'reporting': {
                'enabled': True,
                'report_types': ['documentation_status', 'document_coverage', 'update_history', 'compliance'],
                'include_statistics': True,
                'include_visualization': True,
                'export_formats': ['pdf', 'excel', 'json', 'html']
            }
        }

    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documentation_system_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_name TEXT UNIQUE,
                        config_value TEXT,
                        description TEXT,
                        updated_at TEXT
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documentation_system_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        status_name TEXT UNIQUE,
                        status_value TEXT,
                        description TEXT,
                        updated_at TEXT
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documentation (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id TEXT UNIQUE,
                        title TEXT,
                        type TEXT,
                        format TEXT,
                        path TEXT,
                        version TEXT,
                        status TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        author TEXT,
                        description TEXT
                    )
                """)

                conn.commit()

            logger.info("数据库检查完成")
            return True
        except Exception as e:
            logger.error(f"检查数据库失败: {str(e)}")
            return False

    def add_new_ai_types(self) -> bool:
        """添加新AI类型"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ai_type TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        functions TEXT,
                        required_skills TEXT,
                        created_at TEXT
                    )
                """)

                added_count = 0
                for ai_type_info in self.new_ai_types:
                    cursor.execute(
                        "SELECT ai_type FROM ai_types WHERE ai_type = ?",
                        (ai_type_info['ai_type'],)
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO ai_types (ai_type, name, description, functions, required_skills, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                ai_type_info['ai_type'],
                                ai_type_info['name'],
                                ai_type_info['description'],
                                str(ai_type_info['functions']),
                                str(ai_type_info['required_skills']),
                                datetime.now().isoformat()
                            )
                        )
                        added_count += 1
                    else:
                        logger.info(f"AI类型已存在: {ai_type_info['name']} ({ai_type_info['ai_type']})")

                conn.commit()

            logger.info(f"添加AI类型完成,新增 {added_count} 个AI类型")
            return True
        except Exception as e:
            logger.error(f"添加新AI类型失败: {str(e)}")
            return False

    def optimize_documentation_system_configs(self) -> bool:
        """优化文档管理系统配置"""
        try:
            logger.info("开始优化文档管理系统配置")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updated_count = 0
                for config_category, config_values in self.documentation_system_configs.items():
                    for config_name, config_value in config_values.items():
                        full_config_name = f"documentation_{config_category}_{config_name}"
                        
                        cursor.execute(
                            "SELECT config_name FROM documentation_system_configs WHERE config_name = ?",
                            (full_config_name,)
                        )
                        if cursor.fetchone():
                            cursor.execute(
                                "UPDATE documentation_system_configs SET config_value = ?, updated_at = ? WHERE config_name = ?",
                                (str(config_value), datetime.now().isoformat(), full_config_name)
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO documentation_system_configs (config_name, config_value, description, updated_at) VALUES (?, ?, ?, ?)",
                                (
                                    full_config_name,
                                    str(config_value),
                                    f"文档管理系统 {config_category} 配置: {config_name}",
                                    datetime.now().isoformat()
                                )
                            )
                        updated_count += 1
                
                conn.commit()
            logger.info(f"文档管理系统配置优化完成,更新 {updated_count} 个配置项")
            return True
        except Exception as e:
            logger.error(f"优化文档管理系统配置失败: {str(e)}")
            return False

    def update_documentation_system_status(self) -> bool:
        """更新文档管理系统状态"""
        try:
            logger.info("开始更新文档管理系统状态")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                statuses = {
                    'documentation_system_enabled': 'True',
                    'last_document_update': datetime.now().isoformat(),
                    'total_documents': '0',
                    'technical_documents': '0',
                    'user_documents': '0',
                    'change_documents': '0',
                    'system_status': 'healthy'
                }

                updated_count = 0
                for status_name, status_value in statuses.items():
                    cursor.execute(
                        "SELECT status_name FROM documentation_system_status WHERE status_name = ?",
                        (status_name,)
                    )
                    if cursor.fetchone():
                        cursor.execute(
                            "UPDATE documentation_system_status SET status_value = ?, updated_at = ? WHERE status_name = ?",
                            (status_value, datetime.now().isoformat(), status_name)
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO documentation_system_status (status_name, status_value, description, updated_at) VALUES (?, ?, ?, ?)",
                            (
                                status_name,
                                status_value,
                                f"文档管理系统状态: {status_name}",
                                datetime.now().isoformat()
                            )
                        )
                    updated_count += 1
                conn.commit()

            logger.info(f"文档管理系统状态更新完成,更新 {updated_count} 个状态项")
            return True
        except Exception as e:
            logger.error(f"更新文档管理系统状态失败: {str(e)}")
            return False

    def add_initial_documents(self) -> bool:
        """添加初始文档记录"""
        try:
            logger.info("开始添加初始文档记录")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM documentation")
                if cursor.fetchone()[0] == 0:
                    initial_documents = [
                        {
                            'document_id': f"DOC_{datetime.now().strftime('%Y%m%d%H%M%S')}_1",
                            'title': '系统架构文档',
                            'type': 'technical',
                            'format': 'markdown',
                            'path': 'documentation/architecture.md',
                            'version': '1.0.0',
                            'status': 'active',
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat(),
                            'author': 'system',
                            'description': '系统架构设计文档'
                        },
                        {
                            'document_id': f"DOC_{datetime.now().strftime('%Y%m%d%H%M%S')}_2",
                            'title': '用户手册',
                            'type': 'user',
                            'format': 'markdown',
                            'path': 'documentation/user_manual.md',
                            'version': '1.0.0',
                            'status': 'active',
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat(),
                            'author': 'system',
                            'description': '用户使用手册'
                        },
                        {
                            'document_id': f"DOC_{datetime.now().strftime('%Y%m%d%H%M%S')}_3",
                            'title': '更新说明文档',
                            'type': 'change',
                            'format': 'markdown',
                            'path': 'documentation/release_notes.md',
                            'version': '1.0.0',
                            'status': 'active',
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat(),
                            'author': 'system',
                            'description': '系统更新说明文档'
                        }
                    ]

                    for doc in initial_documents:
                        cursor.execute("""
                            INSERT INTO documentation
                            (document_id, title, type, format, path, version, status, created_at, updated_at, author, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            doc['document_id'],
                            doc['title'],
                            doc['type'],
                            doc['format'],
                            doc['path'],
                            doc['version'],
                            doc['status'],
                            doc['created_at'],
                            doc['updated_at'],
                            doc['author'],
                            doc['description']
                        ))
                    conn.commit()
                    logger.info("初始文档记录添加完成")
                else:
                    logger.info("文档记录已存在,跳过初始文档添加")
            return True
        except Exception as e:
            logger.error(f"添加初始文档记录失败: {str(e)}")
            return False

    def get_documentation_system_configs(self) -> Dict[str, Any]:
        """获取文档管理系统配置"""
        try:
            logger.info("获取文档管理系统配置")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT config_name, config_value FROM documentation_system_configs")
                configs = {}
                for row in cursor.fetchall():
                    config_name = row[0]
                    try:
                        config_value = eval(row[1])
                    except Exception:
                        config_value = row[1]
                    configs[config_name] = config_value

            return configs
        except Exception as e:
            logger.error(f"获取文档管理系统配置失败: {str(e)}")
            return {}

    def get_documentation_system_status(self) -> Dict[str, Any]:
        """获取文档管理系统状态"""
        try:
            logger.info("获取文档管理系统状态")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT status_name, status_value FROM documentation_system_status")
                statuses = {}
                for row in cursor.fetchall():
                    status_name = row[0]
                    status_value = row[1]
                    statuses[status_name] = status_value

            return statuses
        except Exception as e:
            logger.error(f"获取文档管理系统状态失败: {str(e)}")
            return {}

    def get_documentation(self) -> List[Dict[str, Any]]:
        """获取文档列表"""
        try:
            logger.info("获取文档列表")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documentation ORDER BY updated_at DESC")
                documents = []
                for row in cursor.fetchall():
                    doc_info = {
                        'id': row[0],
                        'document_id': row[1],
                        'title': row[2],
                        'type': row[3],
                        'format': row[4],
                        'path': row[5],
                        'version': row[6],
                        'status': row[7],
                        'created_at': row[8],
                        'updated_at': row[9],
                        'author': row[10],
                        'description': row[11]
                    }
                    documents.append(doc_info)

            return documents
        except Exception as e:
            logger.error(f"获取文档列表失败: {str(e)}")
            return []

    def get_ai_types(self) -> List[Dict[str, Any]]:
        """获取AI类型"""
        try:
            logger.info("获取AI类型")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ai_types")
                ai_types = []
                for row in cursor.fetchall():
                    ai_type_info = {
                        'id': row[0],
                        'ai_type': row[1],
                        'name': row[2],
                        'description': row[3],
                        'functions': eval(row[4]) if row[4] else [],
                        'required_skills': eval(row[5]) if row[5] else [],
                        'created_at': row[6]
                    }
                    ai_types.append(ai_type_info)

            return ai_types
        except Exception as e:
            logger.error(f"获取AI类型失败: {str(e)}")
            return []

    def restart_documentation_system(self) -> bool:
        """重启文档管理系统"""
        try:
            logger.info("文档管理系统重启指令已准备就绪")
            logger.info("请根据需要重启文档管理系统相关服务")
            return True
        except Exception as e:
            logger.error(f"重启文档管理系统失败: {str(e)}")
            return False

    def enhance_system(self) -> Dict[str, Any]:
        """增强系统"""
        try:
            logger.info("开始增强系统")
            enhance_result = {
                'success': True,
                'steps': [],
                'errors': []
            }

            if self.check_database():
                enhance_result['steps'].append('数据库检查完成')
            else:
                enhance_result['errors'].append('数据库检查失败')
                enhance_result['success'] = False

            if self.add_new_ai_types():
                enhance_result['steps'].append('添加新AI类型完成')
            else:
                enhance_result['errors'].append('添加新AI类型失败')

            if self.optimize_documentation_system_configs():
                enhance_result['steps'].append('文档管理系统配置优化完成')
            else:
                enhance_result['errors'].append('文档管理系统配置优化失败')
                enhance_result['success'] = False

            if self.update_documentation_system_status():
                enhance_result['steps'].append('文档管理系统状态更新完成')
            else:
                enhance_result['errors'].append('文档管理系统状态更新失败')
                enhance_result['success'] = False

            if self.add_initial_documents():
                enhance_result['steps'].append('初始文档记录添加完成')
            else:
                enhance_result['errors'].append('初始文档记录添加失败')
                enhance_result['success'] = False

            if self.restart_documentation_system():
                enhance_result['steps'].append('文档管理系统重启指令已准备')
            else:
                enhance_result['errors'].append('文档管理系统重启失败')
                enhance_result['success'] = False

            logger.info(f"系统增强完成: {enhance_result}")
            return enhance_result
        except Exception as e:
            logger.error(f"增强系统失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)],
                'steps': []
            }

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("新增AI并优化文档管理系统脚本")
    logger.info("=" * 60)

    enhancer = AIAndDocumentationSystemEnhancer()

    logger.info("\n1. 增强系统")
    enhance_result = enhancer.enhance_system()
    if enhance_result['success']:
        logger.info("✅ 系统增强成功")
        for step in enhance_result['steps']:
            logger.info(f"  - {step}")
    else:
        logger.error("❌ 系统增强失败")
        for error in enhance_result['errors']:
            logger.error(f"  - {error}")

    logger.info("\n2. 获取AI类型")
    ai_types = enhancer.get_ai_types()
    documentation_ai_types = [ai for ai in ai_types if 'documentation' in ai['ai_type'] or 'Documentation' in ai['name']]
    logger.info(f"已添加 {len(documentation_ai_types)} 个文档管理系统相关AI类型")
    for ai_type in documentation_ai_types:
        logger.info(f"  - {ai_type['name']} ({ai_type['ai_type']})")
        logger.info(f"    描述: {ai_type['description']}")
        logger.info(f"    功能: {', '.join(ai_type['functions'])}")
        logger.info(f"    必需技能: {', '.join(ai_type['required_skills'])}")

    logger.info("\n3. 获取文档管理系统配置")
    documentation_configs = enhancer.get_documentation_system_configs()

    config_categories = {}
    for config_name, config_value in documentation_configs.items():
        parts = config_name.split('_')
        if len(parts) > 1:
            category = parts[1]
        else:
            category = 'other'
        if category not in config_categories:
            config_categories[category] = {}
        config_categories[category][config_name] = config_value
    
    for category, configs in config_categories.items():
        logger.info(f"\n  {category} 配置:")
        for config_name, config_value in configs.items():
            logger.info(f"    {config_name.split('_')[-1]}: {config_value}")

    logger.info("\n4. 获取文档管理系统状态")
    documentation_status = enhancer.get_documentation_system_status()
    logger.info(f"文档管理系统状态项数量: {len(documentation_status)}")
    for status_name, status_value in documentation_status.items():
        logger.info(f"  {status_name}: {status_value}")

    logger.info("\n5. 获取文档列表")
    documentation = enhancer.get_documentation()
    logger.info(f"文档记录数量: {len(documentation)}")
    for doc in documentation:
        logger.info(f"  - 标题: {doc['title']} (类型: {doc['type']})")
        logger.info(f"    版本: {doc['version']}")
        logger.info(f"    格式: {doc['format']}")
        logger.info(f"    状态: {doc['status']}")

    logger.info("系统增强完成")
    logger.info("=" * 60)

    return 0 if enhance_result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
