# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动清理和优化系统脚本
删除多余备份,优化冗余,多余参数,多余设置,临时优化文件和脚本,更新文件脚本临时文件文件夹等
"""

import os
import sys
import logging
import shutil
import glob
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_cleanup_optimizer')

class AICleanupOptimizer:
    """AI清理和优化器类"""

    def __init__(self):
        """初始化AI清理和优化器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')

        self.cleanup_targets = {
            'backup_files': {
                'patterns': ['*_backup*', '*_bak*', 'backup_*', 'bak_*'],
                'directories': [self.data_dir],
                'max_age_days': 7
            },
            'temporary_files': {
                'patterns': ['*.tmp', '*.temp', 'temp_*', 'tmp_*'],
                'directories': [self.project_root, self.data_dir],
                'max_age_days': 1
            },
            'log_files': {
                'patterns': ['*.log'],
                'directories': [self.project_root, self.data_dir],
                'max_age_days': 30
            },
            'optimizer_files': {
                'patterns': ['*_optimizer.py', '*_optimizer.sh', 'optimize_*'],
                'directories': [self.project_root],
                'max_age_days': 3
            },
            'test_files': {
                'patterns': ['test_*.py', 'test_*.sh'],
                'directories': [self.project_root],
                'max_age_days': 7
            },
            'temporary_directories': {
                'patterns': ['temp_*', 'tmp_*'],
                'directories': [self.project_root, self.data_dir],
                'max_age_days': 1
            }
        }

        self.redundant_configs = {
            'version_system_configs': [
                'version_general_compression',
            ],
            'documentation_system_configs': [
                'documentation_general_compression',
            ],
            'ai_system_configs': [
                'ai_general_compression',
                'ai_general_retention_period'
            ]
        }

        logger.info("AI清理和优化器初始化完成")

    def get_file_age_days(self, file_path: str) -> float:
        """获取文件的年龄(天数)"""
        try:
            file_stat = os.stat(file_path)
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            now = datetime.now()
            age_days = (now - file_mtime).total_seconds() / 86400
            return age_days
        except Exception as e:
            logger.error(f"获取文件年龄失败: {str(e)}")
            return float('inf')

    def find_files(self, pattern: str, directory: str) -> List[str]:
        """根据模式查找文件"""
        try:
            search_pattern = os.path.join(directory, '**', pattern)
            files = glob.glob(search_pattern, recursive=True)
            return files
        except Exception as e:
            logger.error(f"查找文件失败: {str(e)}")
            return []

    def cleanup_files(self) -> Dict[str, Any]:
        """清理文件"""
        try:
            logger.info("开始清理文件")

            cleanup_result = {
                'total_files_deleted': 0,
                'files_deleted_by_type': {},
                'errors': []
            }

            for target_type, target_config in self.cleanup_targets.items():
                files_deleted = 0

                for directory in target_config['directories']:
                    if not os.path.exists(directory):
                        continue

                    for pattern in target_config['patterns']:
                        files = self.find_files(pattern, directory)

                        for file_path in files:
                            if os.path.abspath(file_path) == os.path.abspath(__file__):
                                continue

                            age_days = self.get_file_age_days(file_path)
                            if age_days > target_config['max_age_days']:
                                try:
                                    if os.path.isfile(file_path):
                                        os.remove(file_path)
                                    elif os.path.isdir(file_path):
                                        shutil.rmtree(file_path)
                                    files_deleted += 1
                                    logger.info(f"删除 {target_type}: {file_path} (年龄: {age_days:.2f} 天)")
                                except Exception as e:
                                    error_msg = f"删除 {file_path} 失败: {str(e)}"
                                    logger.error(error_msg)
                                    cleanup_result['errors'].append(error_msg)

                cleanup_result['files_deleted_by_type'][target_type] = files_deleted
                cleanup_result['total_files_deleted'] += files_deleted

            logger.info(f"文件清理完成,共删除 {cleanup_result['total_files_deleted']} 个文件")
            return cleanup_result
        except Exception as e:
            logger.error(f"清理文件失败: {str(e)}")
            return {
                'total_files_deleted': 0,
                'files_deleted_by_type': {},
                'errors': [str(e)]
            }

    def cleanup_redundant_configs(self) -> Dict[str, Any]:
        """清理冗余配置"""
        try:
            logger.info("开始清理冗余配置")

            cleanup_result = {
                'total_configs_deleted': 0,
                'configs_deleted_by_table': {},
                'errors': []
            }

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for table_name, redundant_configs in self.redundant_configs.items():
                    configs_deleted = 0
                    for config_name in redundant_configs:
                        try:
                            cursor.execute(
                                f"SELECT config_name FROM {table_name} WHERE config_name = ?",
                                (config_name,)
                            )
                            if cursor.fetchone():
                                cursor.execute(
                                    f"DELETE FROM {table_name} WHERE config_name = ?",
                                    (config_name,)
                                )
                                logger.info(f"删除冗余配置: {config_name} 从 {table_name}")
                                configs_deleted += 1
                        except Exception as e:
                            error_msg = f"删除配置 {config_name} 失败: {str(e)}"
                            logger.error(error_msg)
                            cleanup_result['errors'].append(error_msg)

                    cleanup_result['configs_deleted_by_table'][table_name] = configs_deleted
                    cleanup_result['total_configs_deleted'] += configs_deleted

                conn.commit()

            logger.info(f"冗余配置清理完成,共删除 {cleanup_result['total_configs_deleted']} 个配置")
            return cleanup_result
        except Exception as e:
            logger.error(f"清理冗余配置失败: {str(e)}")
            return {
                'total_configs_deleted': 0,
                'configs_deleted_by_table': {},
                'errors': [str(e)]
            }

    def optimize_database(self) -> bool:
        """优化数据库"""
        try:
            logger.info("开始优化数据库")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                conn.commit()
            logger.info("数据库优化完成")
            return True
        except Exception as e:
            logger.error(f"优化数据库失败: {str(e)}")
            return False

    def optimize_directory_structure(self) -> Dict[str, Any]:
        """优化目录结构"""
        try:
            logger.info("开始优化目录结构")

            optimize_result = {
                'directories_cleaned': 0,
                'directories_organized': 0,
                'errors': []
            }

            for root, dirs, files in os.walk(self.project_root, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            optimize_result['directories_cleaned'] += 1
                            logger.info(f"删除空目录: {dir_path}")
                    except Exception as e:
                        error_msg = f"删除空目录 {dir_path} 失败: {str(e)}"
                        logger.error(error_msg)
                        optimize_result['errors'].append(error_msg)

            necessary_dirs = [
                os.path.join(self.data_dir, 'backup'),
                os.path.join(self.data_dir, 'temp')
            ]

            for dir_path in necessary_dirs:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"确保目录存在: {dir_path}")
                except Exception as e:
                    error_msg = f"创建目录 {dir_path} 失败: {str(e)}"
                    logger.error(error_msg)
                    optimize_result['errors'].append(error_msg)

            logger.info(f"目录结构优化完成,清理 {optimize_result['directories_cleaned']} 个空目录,组织 {optimize_result['directories_organized']} 个目录")
            return optimize_result
        except Exception as e:
            logger.error(f"优化目录结构失败: {str(e)}")
            return {
                'directories_cleaned': 0,
                'directories_organized': 0,
                'errors': [str(e)]
            }

    def run_cleanup_and_optimization(self) -> Dict[str, Any]:
        """运行清理和优化"""
        try:
            logger.info("开始运行清理和优化")

            overall_result = {
                'success': True,
                'steps': [],
                'results': {},
                'errors': []
            }

            logger.info("\n1. 清理文件")
            file_cleanup_result = self.cleanup_files()
            overall_result['results']['file_cleanup'] = file_cleanup_result
            if file_cleanup_result['errors']:
                overall_result['errors'].extend(file_cleanup_result['errors'])
                overall_result['success'] = False

            logger.info("\n2. 清理冗余配置")
            config_cleanup_result = self.cleanup_redundant_configs()
            overall_result['results']['config_cleanup'] = config_cleanup_result
            if config_cleanup_result['errors']:
                overall_result['errors'].extend(config_cleanup_result['errors'])
                overall_result['success'] = False

            logger.info("\n3. 优化数据库")
            if self.optimize_database():
                overall_result['steps'].append("数据库优化完成")
            else:
                error_msg = "数据库优化失败"
                logger.error(error_msg)
                overall_result['errors'].append(error_msg)
                overall_result['success'] = False

            logger.info("\n4. 优化目录结构")
            directory_optimize_result = self.optimize_directory_structure()
            overall_result['results']['directory_optimize'] = directory_optimize_result
            overall_result['steps'].append(f"目录结构优化完成,清理 {directory_optimize_result['directories_cleaned']} 个空目录,组织 {directory_optimize_result['directories_organized']} 个目录")
            if directory_optimize_result['errors']:
                overall_result['errors'].extend(directory_optimize_result['errors'])
                overall_result['success'] = False

            return overall_result
        except Exception as e:
            logger.error(f"运行清理和优化失败: {str(e)}")
            return {
                'success': False,
                'steps': [],
                'results': {},
                'errors': [str(e)]
            }

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("AI自动清理和优化系统脚本")
    logger.info("=" * 60)

    optimizer = AICleanupOptimizer()

    logger.info("开始执行清理和优化任务")
    result = optimizer.run_cleanup_and_optimization()

    if result['success']:
        logger.info("✅ 清理和优化成功完成")
        for step in result['steps']:
            logger.info(f"  - {step}")
    else:
        logger.error("❌ 清理和优化过程中出现错误")
        for error in result['errors']:
            logger.error(f"  - {error}")

    logger.info("\n详细结果:")
    if 'file_cleanup' in result['results']:
        file_result = result['results']['file_cleanup']
        logger.info(f"  文件清理: 删除 {file_result['total_files_deleted']} 个文件")

    if 'config_cleanup' in result['results']:
        config_result = result['results']['config_cleanup']
        logger.info(f"  配置清理: 删除 {config_result['total_configs_deleted']} 个配置")

    if 'directory_optimize' in result['results']:
        dir_result = result['results']['directory_optimize']
        logger.info(f"  目录优化: 清理 {dir_result['directories_cleaned']} 个空目录,组织 {dir_result['directories_organized']} 个目录")

    logger.info("\n" + "=" * 60)
    logger.info("清理和优化完成")
    logger.info("=" * 60)

    return 0 if result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
