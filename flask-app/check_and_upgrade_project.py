#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目参数检查和自动升级脚本
检查项目参数在数据库中是否正确，并自动升级项目

import os
import sys
import logging
# JSON import removed - using database
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('check_and_upgrade_project')

class ProjectCheckerAndUpgrader:
    """项目检查和升级器类"""

    def __init__(self):
        """初始化项目检查和升级器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')

        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        # 项目参数定义
        self.expected_params = {
            'project_name': 'MTSCOS AI Project',
            'project_version': '1.0.0',
            'database_version': '1.0.0',
            'ai_system_version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'auto_upgrade': True,
            'enable_ai': True,
            'enable_git': True,
            'enable_monitoring': True,
            'enable_security': True,
            'max_ai_instances': 10,
            'log_level': 'INFO'
        }

        logger.info("项目检查和升级器初始化完成")

    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            logger.info("开始检查数据库")

            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查项目参数表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    param_name TEXT UNIQUE,
                    param_value TEXT,
                    description TEXT,
                    updated_at TEXT
                )

            # 检查AI实例表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_instances (
                    ai_type TEXT,
                    name TEXT,
                    status TEXT,
                    config TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    created_at TEXT,
                    access_count INTEGER DEFAULT 0
                )

            conn.commit()
            conn.close()

            logger.info("数据库检查完成")
        except Exception as e:
            return False

    def check_project_parameters(self) -> Dict[str, Any]:
        """检查项目参数"""
        try:
            logger.info("开始检查项目参数")

            conn = sqlite3.connect(self.db_path)

            # 获取现有参数
            cursor.execute("SELECT param_name, param_value FROM project_parameters")

            missing_params = []
            incorrect_params = []

            for param_name, expected_value in self.expected_params.items():
                if param_name not in existing_params:
                    missing_params.append(param_name)
                else:
                    # 检查值是否正确
                    existing_value = existing_params[param_name]
                    if str(existing_value) != str(expected_value):
                        incorrect_params.append({
                            'param_name': param_name,
                            'expected': expected_value,
                            'actual': existing_value
                        })

            conn.close()

            result = {
                'missing_params': missing_params,
                'incorrect_params': incorrect_params,
                'existing_params': existing_params
            }

            logger.info(f"项目参数检查完成: 缺失 {len(missing_params)} 个参数, 不正确 {len(incorrect_params)} 个参数")
            return result
            logger.error(f"检查项目参数失败: {str(e)}")
            return {'error': str(e)}

    def fix_project_parameters(self) -> bool:
        try:
            logger.info("开始修复项目参数")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # 检查参数
            check_result = self.check_project_parameters()

            if 'error' in check_result:
                return False
            for param_name in check_result['missing_params']:
                value = self.expected_params[param_name]
                cursor.execute(
                    "INSERT INTO project_parameters (param_name, param_value, description, updated_at) VALUES (?, ?, ?, ?)",
                    (param_name, str(value), f"项目参数 {param_name}", datetime.now().isoformat())
                )

            # 修复不正确的参数
            for param_info in check_result['incorrect_params']:
                param_name = param_info['param_name']
                value = self.expected_params[param_name]
                cursor.execute(
                    "UPDATE project_parameters SET param_value = ?, updated_at = ? WHERE param_name = ?",
                    (str(value), datetime.now().isoformat(), param_name)
                )

            conn.commit()

            logger.info("项目参数修复完成")
            return True
        except Exception as e:
            logger.error(f"修复项目参数失败: {str(e)}")
            return False

    def upgrade_project(self) -> Dict[str, Any]:
        """升级项目"""
        try:
            logger.info("开始升级项目")

            upgrade_result = {
                'success': True,
                'errors': []
            # 步骤1: 检查数据库
                upgrade_result['steps'].append('数据库检查完成')
                upgrade_result['success'] = False

            # 步骤2: 修复项目参数
            if self.fix_project_parameters():
            else:
                upgrade_result['success'] = False

            # 步骤3: 更新版本号
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # 更新项目版本
                new_version = '1.0.1'  # 示例版本号
                cursor.execute(
                    "UPDATE project_parameters SET param_value = ?, updated_at = ? WHERE param_name = 'project_version'",
                )
                # 更新数据库版本
                new_db_version = '1.0.1'
                cursor.execute(
                    (new_db_version, datetime.now().isoformat())
                )
                # 更新AI系统版本
                cursor.execute(
                    "UPDATE project_parameters SET param_value = ?, updated_at = ? WHERE param_name = 'ai_system_version'",
                    (new_ai_version, datetime.now().isoformat())
                )
                conn.commit()
                conn.close()

                upgrade_result['steps'].append(f'版本更新完成: 项目={new_version}, 数据库={new_db_version}, AI系统={new_ai_version}')
            except Exception as e:
                upgrade_result['errors'].append(f'版本更新失败: {str(e)}')
                upgrade_result['success'] = False

            # 步骤4: 清理和优化
            try:
                cursor = conn.cursor()

                # 执行VACUUM来优化数据库
                cursor.execute("VACUUM")

                conn.commit()
                conn.close()
                upgrade_result['steps'].append('数据库优化完成')
                upgrade_result['errors'].append(f'数据库优化失败: {str(e)}')
                # 不影响整体升级结果

            logger.info(f"项目升级完成: {upgrade_result}")
            return upgrade_result
            return {
                'success': False,
            }

        """获取项目状态"""
        try:

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT param_name, param_value FROM project_parameters")
            params = {row[0]: row[1] for row in cursor.fetchall()}

            # 获取AI实例数量
            cursor.execute("SELECT COUNT(*) FROM ai_instances")
            # 获取知识库条目数量
            cursor.execute("SELECT COUNT(*) FROM knowledge_base")
            knowledge_count = cursor.fetchone()[0]
            conn.close()

            status = {
                'database_version': params.get('database_version', 'Unknown'),
                'ai_system_version': params.get('ai_system_version', 'Unknown'),
                'ai_instances_count': ai_count,
                'auto_upgrade': params.get('auto_upgrade', 'False') == 'True',
                'enable_ai': params.get('enable_ai', 'False') == 'True',
                'enable_git': params.get('enable_git', 'False') == 'True',
                'enable_monitoring': params.get('enable_monitoring', 'False') == 'True',
                'enable_security': params.get('enable_security', 'False') == 'True'

            logger.info(f"项目状态: {status}")
            return status
        except Exception as e:
            logger.error(f"获取项目状态失败: {str(e)}")
            return {'error': str(e)}

def main():
    logger.info("=" * 60)
    logger.info("项目参数检查和自动升级脚本")
    logger.info("=" * 60)

    checker = ProjectCheckerAndUpgrader()

    # 检查项目参数
    logger.info("\n1. 检查项目参数")
    check_result = checker.check_project_parameters()

    if 'error' in check_result:
        logger.error(f"参数检查失败: {check_result['error']}")
    else:
        if check_result['missing_params']:
        if check_result['incorrect_params']:
            for param in check_result['incorrect_params']:
                logger.warning(f"  - {param['param_name']}: 期望={param['expected']}, 实际={param['actual']}")

    # 升级项目
    logger.info("\n2. 升级项目")
    upgrade_result = checker.upgrade_project()

    if upgrade_result['success']:
        logger.info("✅ 项目升级成功")
        for step in upgrade_result['steps']:
            logger.info(f"  - {step}")
    else:
        logger.error("❌ 项目升级失败")
        for error in upgrade_result['errors']:
            logger.error(f"  - {error}")

    # 获取项目状态
    logger.info("\n3. 获取项目状态")
    status = checker.get_project_status()

    if 'error' in status:
        logger.error(f"获取状态失败: {status['error']}")
        logger.info("项目状态:")
        for key, value in status.items():
            logger.info(f"  {key}: {value}")

    logger.info("\n" + "=" * 60)
    logger.info("项目检查和升级完成")
    logger.info("=" * 60)

    return 0 if upgrade_result['success'] else 1

    sys.exit(main())
