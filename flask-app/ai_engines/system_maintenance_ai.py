#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统维护AI和全面检查修复脚本
"""

import os
import sqlite3
from contextlib import contextmanager
# JSON import removed - using database
import time
import logging
import subprocess
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('system_maintenance_ai')

class SystemMaintenanceAI:
    """系统维护AI"""

    def __init__(self):
        self.ai_id = f"system-maintenance-ai-{int(time.time())}"
        self.name = "系统维护AI"
        self.description = "负责系统全面维护检查、数据库修复和错误案例收集"
        self.created_at = datetime.now().isoformat()
        logger.info(f"✅ 新建系统维护AI: {self.ai_id}")

    def perform_system_check(self):
        """执行全面系统检查"""
        logger.info("=== 开始全面系统检查 ===")

        checks = {
            'system_files': self.check_system_files(),
            'database': self.check_database(),
            'dependencies': self.check_dependencies(),
            'configuration': self.check_configuration(),
            'ai_components': self.check_ai_components()
        }

        logger.info("=== 系统检查完成 ===")
        return checks

    def check_system_files(self):
        """检查系统文件"""
        logger.info("检查系统文件...")

        critical_files = [
            'app/__init__.py',
            'app/models/system_config.py',
            'app/api/__init__.py',
            'requirements.txt',
            'system_init.py'
        ]

        missing_files = []
        for file_path in critical_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)

        if missing_files:
            logger.warning(f"⚠️ 缺失文件: {missing_files}")
            return {'status': 'warning', 'missing_files': missing_files}
        else:
            logger.info("✅ 系统文件检查通过")
            return {'status': 'ok'}

    def check_database(self):
        """检查数据库"""
        logger.info("检查数据库...")

        try:
            db_path = 'data/mtscos_ai_project.db'
            if not os.path.exists('data'):
                os.makedirs('data')

            with sqlite3.connect(db_path) as conn:
                conn_cursor = conn.cursor()
                cursor = conn.cursor()
                
                # 检查关键表
                tables = ['users', 't_4eee826d5652464d', 't_c40db917ee9ecaca', 'user_snapshots']
                missing_tables = []
                
                for table in tables:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    if not cursor.fetchone():
                        missing_tables.append(table)
                

            if missing_tables:
                logger.warning(f"⚠️ 缺失表: {missing_tables}")
                return {'status': 'warning', 'missing_tables': missing_tables}
            else:

                pass
                return {'status': 'ok'}

        except Exception as e:
            logger.error(f"❌ 数据库检查失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def check_dependencies(self):
        """检查依赖项"""
        logger.info("检查依赖项...")

        try:
            import flask
            import sqlalchemy
            import numpy
            import sklearn
            import bs4
            import yaml

            logger.info("✅ 依赖项检查通过")
            return {'status': 'ok'}

            logger.warning(f"⚠️ 缺失依赖: {str(e)}")
            return {'status': 'warning', 'message': str(e)}

        except Exception as e:
            logger.error(f"❌ 依赖检查失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def check_configuration(self):
        """检查配置文件"""
        logger.info("检查配置文件...")

        config_files = [
            'app/config/ai_engine_config.json',
            'app/config/system_config.json',
            'app/config/services_config.json'
        ]
        missing_configs = []
        for config_file in config_files:
            if not os.path.exists(config_file):
                missing_configs.append(config_file)

        if missing_configs:
            logger.warning(f"⚠️ 缺失配置文件: {missing_configs}")
            return {'status': 'warning', 'missing_configs': missing_configs}
        else:
            logger.info("✅ 配置文件检查通过")

    def check_ai_components(self):
        """检查AI组件"""

        ai_components = [
            'app/ai/route_optimizer.py',
            'app/ai/engineer_ai.py',
            'app/ai/monitoring_ai.py'
        ]
        missing_components = []
        for component in ai_components:
            if not os.path.exists(component):
                missing_components.append(component)

        if missing_components:
            logger.warning(f"⚠️ 缺失AI组件: {missing_components}")
            return {'status': 'warning', 'missing_components': missing_components}
        else:
            logger.info("✅ AI组件检查通过")
            return {'status': 'ok'}

    def fix_database(self):
        """修复数据库"""
        logger.info("=== 开始数据库修复 ===")

        db_path = 'data/mtscos_ai_project.db'
        if not os.path.exists('data'):
            os.makedirs('data')

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 修复用户表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    is_active INTEGER DEFAULT 1,
                    hardware_admin_approved INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 修复AI实例表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS t_4eee826d5652464d (
                    instance_id TEXT PRIMARY KEY,
                    collection_id TEXT,
                    ai_type TEXT,
                    name TEXT,
                    ai_name TEXT,
                    description TEXT,
                    functions TEXT,
                    responsibilities TEXT,
                    status TEXT,
                    config TEXT,
                    bound_user TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')

            # 修复AI集表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS t_c40db917ee9ecaca (
                    collection_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')

            # 修复用户快照表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    timestamp TEXT,
                    snapshot_type TEXT,
                    data TEXT,
                    updated_at TEXT
                )
            ''')

            # 创建索引
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)',
                'CREATE INDEX IF NOT EXISTS idx_user_snapshots_session_id ON user_snapshots(session_id)',
            ]
            for idx_sql in indexes:
                cursor.execute(idx_sql)

            conn.commit()
            conn.close()

            logger.info("✅ 数据库修复完成")
            return {'status': 'ok'}

        except Exception as e:
            logger.error(f"❌ 数据库修复失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def report_database_status(self):
        """上报数据库状态"""
        logger.info("=== 开始数据库状态上报 ===")
        try:
            with sqlite3.connect(db_path) as conn:
                conn_cursor = conn.cursor()
                
                # 统计各表数据
                tables = ['users', 't_4eee826d5652464d', 't_c40db917ee9ecaca', 'user_snapshots']
                report = {}
                
                for table in tables:
                    count = cursor.fetchone()[0]
                    report[table] = count
                

                if not os.path.exists('reports'):
                    os.makedirs('reports')
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 数据库状态上报完成,保存至: {report_file}")

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def share_error_cases(self):
        """共享错误修复案例到脑库"""

        try:
            # 收集错误修复案例
            error_cases = [
                {
                    "id": "case-001",
                    "title": "SystemConfig 缺少 get_all_configs 方法",
                    "description": "SystemConfig 类缺少 get_all_configs 方法导致配置加载失败",
                    "solution": "在 SystemConfig 类中添加 get_all_configs 类方法,返回空字典作为默认值",
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "case-002",
                    "title": "用户快照表缺失",
                    "description": "缺少 user_snapshots 表导致索引创建失败",
                    "affected_files": ["数据库"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "case-003",
                    "title": "依赖项兼容性问题",
                    "solution": "更新 numpy 版本为 1.26.4,与 Python 3.14.2 兼容",
                    "affected_files": ["requirements.txt"],
                    "fix_date": self.created_at,
                },
                {
                    "id": "case-004",
                    "title": "缺失模块导入",
                    "description": "缺少 Blueprint 和 threading 导入",
                    "solution": "在相应文件中添加必要的导入语句",
                    "affected_files": ["多个API和视图文件"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                }
        ]

            # 保存到脑库
            brain_file = 'app/ai/brain/error_cases.json'
            if not os.path.exists('app/ai/brain'):
                os.makedirs('app/ai/brain')
            # 如果文件存在,读取现有数据
            existing_cases = []
            if os.path.exists(brain_file):
                with open(brain_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_cases = json.load(f)
                    except Exception:
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

            logger.info(f"✅ 错误修复案例共享完成,保存至: {brain_file}")
            logger.info(f"✅ 共共享 {len(error_cases)} 个新案例")
            return {'status': 'ok', 'cases': error_cases, 'total_cases': len(unique_cases)}
        except Exception as e:
            logger.error(f"❌ 共享错误修复案例失败: {str(e)}")

    def run_maintenance(self):
        """执行完整的维护流程"""
        logger.info("=== 开始完整系统维护流程 ===")
        
        results = {
            'checks': self.perform_system_check(),
            'database_fix': self.fix_database(),
            'error_cases': self.share_error_cases()
        }
        # 保存维护报告
        report_file = f'reports/maintenance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 维护报告保存至: {report_file}")
        logger.info("=== 系统维护流程完成 ===")

        return results

def main():
    """主函数"""
    logger.info("=== 启动系统维护AI ===")

    # 创建系统维护AI
    maintenance_ai = SystemMaintenanceAI()

    # 执行维护流程

    # 输出结果
    logger.info("\n=== 维护结果摘要 ===")
    logger.info(f"系统检查: {results['checks']}")
    logger.info(f"数据库报告: {results['database_report']}")
    logger.info(f"错误案例共享: {results['error_cases']}")


if __name__ == '__main__':
    main()
