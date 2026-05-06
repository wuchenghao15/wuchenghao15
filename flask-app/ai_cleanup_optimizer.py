#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动清理和优化系统脚本
删除多余备份，优化冗余，多余参数，多余设置，临时优化文件和脚本，更新文件脚本临时文件文件夹等

import os
import sys
import logging
import shutil
import glob
# JSON import removed - using database
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 配置日志
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

        # 清理目标
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
                'patterns': ['*.log'],
                'directories': [self.project_root, self.data_dir],
                'max_age_days': 30
                'patterns': ['*_optimizer.py', '*_optimizer.sh', 'optimize_*'],
                'directories': [self.project_root],
                'max_age_days': 3
            },
                'patterns': ['test_*.py', 'test_*.sh'],
                'directories': [self.project_root],
                'max_age_days': 7
            'temporary_directories': {
                'directories': [self.project_root, self.data_dir],
                'max_age_days': 1
        }

        # 冗余配置清理
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
        """获取文件的年龄（天数）"""
            file_stat = os.stat(file_path)
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            now = datetime.now()
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

                'total_files_deleted': 0,
                'files_deleted_by_type': {},
                'errors': []
            }
            for target_type, target_config in self.cleanup_targets.items():
                files_deleted = 0

                for directory in target_config['directories']:
                        continue

                    for pattern in target_config['patterns']:

                        for file_path in files:
                            # 跳过当前脚本
                            if os.path.abspath(file_path) == os.path.abspath(__file__):
                                continue

                            # 检查文件年龄
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

            logger.info(f"文件清理完成，共删除 {cleanup_result['total_files_deleted']} 个文件")
        except Exception as e:
            logger.error(f"清理文件失败: {str(e)}")
            return {
                'total_files_deleted': 0,
                'files_deleted_by_type': {},
                'errors': [str(e)]
            }

    def cleanup_redundant_configs(self) -> Dict[str, Any]:
        try:
            logger.info("开始清理冗余配置")

            cleanup_result = {
                'total_configs_deleted': 0,
                'configs_deleted_by_table': {},
            }
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for table_name, redundant_configs in self.redundant_configs.items():
                configs_deleted = 0
                    try:
                            f"SELECT config_name FROM {table_name} WHERE config_name = ?",
                            (config_name,)
                        )
                            # 删除冗余配置
                            cursor.execute(
                                f"DELETE FROM {table_name} WHERE config_name = ?",
                                (config_name,)
                            logger.info(f"删除冗余配置: {config_name} 从 {table_name}")
                    except Exception as e:
                        error_msg = f"删除配置 {config_name} 失败: {str(e)}"
                        logger.error(error_msg)
                        cleanup_result['errors'].append(error_msg)
                    cleanup_result['configs_deleted_by_table'][table_name] = configs_deleted
                    cleanup_result['total_configs_deleted'] += configs_deleted

            conn.commit()
            conn.close()

            logger.info(f"冗余配置清理完成，共删除 {cleanup_result['total_configs_deleted']} 个配置")
            return cleanup_result
        except Exception as e:
            logger.error(f"清理冗余配置失败: {str(e)}")
            return {
                'total_configs_deleted': 0,
                'configs_deleted_by_table': {},
                'errors': [str(e)]
            }

    def optimize_database(self) -> bool:
        try:
            logger.info("开始优化数据库")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # 执行VACUUM操作优化数据库
            cursor.execute("VACUUM")
            conn.commit()
            conn.close()
            logger.info("数据库优化完成")
            logger.error(f"优化数据库失败: {str(e)}")
            return False

    def optimize_directory_structure(self) -> Dict[str, Any]:
        try:
            logger.info("开始优化目录结构")

            optimize_result = {
                'directories_cleaned': 0,
                'directories_organized': 0,
            }

            # 清理空目录
            for root, dirs, files in os.walk(self.project_root, topdown=False):
                    dir_path = os.path.join(root, dir_name)
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            optimize_result['directories_cleaned'] += 1
                            logger.info(f"删除空目录: {dir_path}")
                    except Exception as e:

            # 确保必要的目录存在
            necessary_dirs = [
                os.path.join(self.data_dir, 'backup'),
                os.path.join(self.data_dir, 'temp')

            for dir_path in necessary_dirs:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"确保目录存在: {dir_path}")
                except Exception as e:
                    error_msg = f"创建目录 {dir_path} 失败: {str(e)}"
                    optimize_result['errors'].append(error_msg)
            logger.info(f"目录结构优化完成，清理 {optimize_result['directories_cleaned']} 个空目录，组织 {optimize_result['directories_organized']} 个目录")
            return optimize_result
        except Exception as e:
            return {
                'directories_cleaned': 0,
                'errors': [str(e)]

    def run_cleanup_and_optimization(self) -> Dict[str, Any]:
        """运行清理和优化"""
            logger.info("开始运行清理和优化")

            overall_result = {
                'success': True,
                'steps': [],
                'results': {},
                'errors': []

            # 步骤1: 清理文件
            logger.info("\n1. 清理文件")
            overall_result['results']['file_cleanup'] = file_cleanup_result
            if file_cleanup_result['errors']:
                overall_result['errors'].extend(file_cleanup_result['errors'])
                overall_result['success'] = False

            # 步骤2: 清理冗余配置
            config_cleanup_result = self.cleanup_redundant_configs()
            if config_cleanup_result['errors']:
                overall_result['errors'].extend(config_cleanup_result['errors'])
                overall_result['success'] = False

            # 步骤3: 优化数据库
            logger.info("\n3. 优化数据库")
            if self.optimize_database():
                overall_result['steps'].append("数据库优化完成")
            else:
                logger.error(error_msg)
                overall_result['errors'].append(error_msg)
                overall_result['success'] = False

            # 步骤4: 优化目录结构
            logger.info("\n4. 优化目录结构")
            directory_optimize_result = self.optimize_directory_structure()
            overall_result['results']['directory_optimize'] = directory_optimize_result
            overall_result['steps'].append(f"目录结构优化完成，清理 {directory_optimize_result['directories_cleaned']} 个空目录，组织 {directory_optimize_result['directories_organized']} 个目录")
            if directory_optimize_result['errors']:
                overall_result['errors'].extend(directory_optimize_result['errors'])
                overall_result['success'] = False

            return overall_result
        except Exception as e:
            logger.error(f"运行清理和优化失败: {str(e)}")
            return {
                'steps': [],
                'results': {},
            }
def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("AI自动清理和优化系统脚本")
    logger.info("=" * 60)

    optimizer = AICleanupOptimizer()

    # 运行清理和优化
    logger.info("开始执行清理和优化任务")

    if result['success']:
        logger.info("✅ 清理和优化成功完成")
        for step in result['steps']:
            logger.info(f"  - {step}")
    else:
        logger.error("❌ 清理和优化过程中出现错误")
        for error in result['errors']:
            logger.error(f"  - {error}")

    # 显示详细结果
    logger.info("\n详细结果:")
    if 'file_cleanup' in result['results']:
        file_result = result['results']['file_cleanup']

        config_result = result['results']['config_cleanup']
        logger.info(f"  配置清理: 删除 {config_result['total_configs_deleted']} 个配置")

    if 'directory_optimize' in result['results']:
        dir_result = result['results']['directory_optimize']
        logger.info(f"  目录优化: 清理 {dir_result['directories_cleaned']} 个空目录，组织 {dir_result['directories_organized']} 个目录")

    logger.info("\n" + "=" * 60)
    logger.info("清理和优化完成")
    logger.info("=" * 60)

    return 0 if result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
