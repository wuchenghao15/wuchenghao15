#!/usr/bin/env python3
"""
系统维护服务 - 例行维护和升级管理

import os
import time
# JSON import removed - using database
import shutil
import subprocess
import threading
from datetime import datetime, timedelta
from utils.logging import logger
from utils.db import db_manager
from config.config import config

class MaintenanceService:
    """系统维护服务"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化维护服务"""
        self.backup_path = 'backups'
        self.log_path = 'logs'
        self.maintenance_history = []
        self.upgrade_history = []

        # 创建必要的目录
        self._create_directories()

        # 启动维护线程
        self._start_maintenance_threads()

        logger.info("系统维护服务初始化成功")

    def _create_directories(self):
        """创建必要的目录"""
        directories = [self.backup_path, self.log_path]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"创建目录: {directory}")

    def _start_maintenance_threads(self):
        """启动维护线程"""
        # 自动备份线程
        self._backup_thread = threading.Thread(target=self._auto_backup, daemon=True)
        self._backup_thread.start()

        # 日志轮转线程
        self._log_rotation_thread = threading.Thread(target=self._log_rotation, daemon=True)
        self._log_rotation_thread.start()

        # 健康检查线程
        self._health_check_thread = threading.Thread(target=self._health_check, daemon=True)
        self._health_check_thread.start()

        # 依赖检查线程
        self._dependency_check_thread = threading.Thread(target=self._dependency_check, daemon=True)
        self._dependency_check_thread.start()

        logger.info("维护线程启动成功")

    def _auto_backup(self):
        """自动备份"""
        while True:
            try:
                if config.MAINTENANCE_CONFIG['auto_backup']:
                    logger.info("开始执行自动备份")
                    self.perform_backup()

                time.sleep(config.MAINTENANCE_CONFIG['backup_interval'])
            except Exception as e:
                logger.error(f"自动备份失败: {str(e)}")
                time.sleep(config.MAINTENANCE_CONFIG['backup_interval'])

        """执行备份

        Returns:
            dict: 备份结果
        logger.info("开始执行备份")

        result = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'backups': []
        }

        try:
            # 备份数据库
            db_backup = self._backup_database()

            # 备份配置文件
            config_backup = self._backup_config()
            result['backups'].append(config_backup)

            # 备份日志
            log_backup = self._backup_logs()
            result['backups'].append(log_backup)

            # 清理过期备份
            self._cleanup_old_backups()

            # 记录备份历史
            self.maintenance_history.append(result)

            logger.info(f"备份完成: {len(result['backups'])} 个项目备份成功")
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"备份失败: {str(e)}")


    def _backup_database(self):
        """备份数据库

        Returns:
            dict: 数据库备份信息
        db_type = config.DATABASE_CONFIG['type']
        backup_file = os.path.join(
            self.backup_path,
            f"database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )

        try:
            if db_type == 'sqlite':
                db_file = config.DATABASE_CONFIG['sqlite']['database']
                if os.path.exists(db_file):
                    return {
                        'type': 'database',
                        'file': backup_file,
                        'size': os.path.getsize(backup_file),
                        'status': 'success'
                    }
            return {
                'type': 'database',
                'file': None,
                'status': 'skipped',
                'reason': f'数据库类型 {db_type} 不支持或数据库文件不存在'
            }
        except Exception as e:
            return {
                'type': 'database',
                'status': 'failed',
                'error': str(e)
            }
    def _backup_config(self):
        """备份配置文件

            dict: 配置文件备份信息
        backup_file = os.path.join(
            f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        try:
            config.save_to_file(backup_file)
            return {
                'type': 'config',
                'file': backup_file,
            }
            return {
                'type': 'config',
                'status': 'failed',
                'error': str(e)
            }

    def _backup_logs(self):

        Returns:
            dict: 日志备份信息
            self.backup_path,
        )
        try:
            log_file = config.LOGGING_CONFIG['file']
            if os.path.exists(log_file):
                shutil.make_archive(
                    backup_file.replace('.tar.gz', ''),
                )
                    'file': backup_file,
                }
            return {
                'file': None,
                'status': 'skipped',
                'reason': '日志文件不存在'
            }
        except Exception as e:
            return {
                'type': 'logs',
                'file': None,
                'status': 'failed',
            }

    def _cleanup_old_backups(self):
        """清理过期备份"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

                filepath = os.path.join(self.backup_path, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                        os.remove(filepath)
                        logger.info(f"删除过期备份: {filepath}")
            logger.error(f"清理过期备份失败: {str(e)}")

    def _log_rotation(self):
        """日志轮转"""
        while True:
                if config.MAINTENANCE_CONFIG['log_rotation']:
                    logger.info("开始执行日志轮转")
                    self.rotate_logs()
            except Exception as e:
        """执行日志轮转

        Returns:
            dict: 日志轮转结果
        result = {
            'status': 'success',
        try:
            log_file = config.LOGGING_CONFIG['file']
            if os.path.exists(log_file):
                file_size = os.path.getsize(log_file)
                max_size = config.MAINTENANCE_CONFIG['log_max_size']

                if file_size > max_size:
                    # 轮转日志
                    shutil.move(log_file, rotated_file)

                    # 创建新日志文件
                    open(log_file, 'a').close()

                    result['rotated_files'].append({
                        'original': log_file,
                        'size': file_size

                    self._compress_old_logs()

                    logger.info(f"日志轮转完成: {rotated_file}")
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"日志轮转失败: {str(e)}")

        return result

    def _compress_old_logs(self):
        """压缩旧日志"""
        try:
            log_dir = os.path.dirname(config.LOGGING_CONFIG['file'])
            log_basename = os.path.basename(config.LOGGING_CONFIG['file'])

            for filename in os.listdir(log_dir):
                if filename.startswith(log_basename + '.') and not filename.endswith('.gz'):
                    filepath = os.path.join(log_dir, filename)
                        compressed_file = filepath + '.gz'
                        with open(filepath, 'rb') as f_in:
                            with gzip.open(compressed_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        os.remove(filepath)
                        logger.info(f"压缩旧日志: {compressed_file}")
        except Exception as e:
            logger.error(f"压缩旧日志失败: {str(e)}")

    def _health_check(self):
        while True:
                health_report = self.perform_health_check()
                if health_report['status'] == 'unhealthy':
                    logger.warning(f"系统健康检查发现问题: {health_report['issues']}")
                time.sleep(config.MAINTENANCE_CONFIG['health_check_interval'])
            except Exception as e:
                time.sleep(config.MAINTENANCE_CONFIG['health_check_interval'])

    def perform_health_check(self):

        Returns:
            dict: 健康检查报告
        import psutil

        report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'checks': {},
            'issues': []
        }

        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            report['checks']['cpu'] = {
                'usage': cpu_percent,
                'status': 'ok' if cpu_percent < 90 else 'warning'
            }

            # 内存检查
                'usage': memory.percent,
                'available': memory.available,
                'status': 'ok' if memory.percent < 90 else 'warning'
            }

            # 磁盘检查
            disk = psutil.disk_usage('/')
            report['checks']['disk'] = {
                'usage': disk.percent,
                'free': disk.free,
                'status': 'ok' if disk.percent < 90 else 'warning'
            }
            # 数据库检查
            report['checks']['database'] = {
                'status': 'ok' if db_healthy else 'error'
            }

            # 检查是否有问题
                if check_result['status'] != 'ok':
                    report['issues'].append(f"{check_name}: {check_result['status']}")
                    report['status'] = 'unhealthy'

        except Exception as e:
            report['status'] = 'error'
            report['error'] = str(e)
            logger.error(f"健康检查出错: {str(e)}")

        return report

    def _check_database_health(self):
        """检查数据库健康状态

        Returns:
            bool: 数据库是否健康
        try:
            result = db_manager.fetch_one('SELECT 1')
            return result is not None
            return False

    def _dependency_check(self):
        """依赖检查"""
        while True:
                if config.MAINTENANCE_CONFIG['dependency_check']:
                    self.check_dependencies()

                time.sleep(86400)  # 每天检查一次
            except Exception as e:
                logger.error(f"依赖检查失败: {str(e)}")

    def check_dependencies(self):
        """检查项目依赖
        Returns:
            dict: 依赖检查报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'dependencies': [],
            'outdated': [],
            'missing': []
        }

        try:
            # 检查requirements.txt
            if os.path.exists('requirements.txt'):
                with open('requirements.txt', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            report['dependencies'].append(line)

            if os.path.exists('package.json'):
                # JSON load replaced with database read
db_manager.fetch_all(...)
                        report['dependencies'].extend(package_data['dependencies'].keys())

            logger.info(f"依赖检查完成: {len(report['dependencies'])} 个依赖")
        except Exception as e:
            logger.error(f"依赖检查失败: {str(e)}")

        return report

    def perform_upgrade(self, target_version=None):
        """执行升级

        Args:
            target_version: 目标版本

        Returns:
            dict: 升级结果
        logger.info(f"开始执行系统升级，目标版本: {target_version or config.VERSION}")

        result = {
            'current_version': config.VERSION,
            'target_version': target_version,
            'status': 'success',
            'steps': []
        }

        try:
            # 1. 备份当前系统
            step1 = {'name': 'backup', 'status': 'running'}
            result['steps'].append(step1)
            step1['status'] = 'success' if backup_result['status'] == 'success' else 'failed'
            step1['result'] = backup_result

            # 2. 检查磁盘空间
            step2 = {'name': 'check_disk_space', 'status': 'running'}
            result['steps'].append(step2)
            import psutil
            disk = psutil.disk_usage('/')
            free_space_mb = disk.free / (1024 * 1024)
                step2['status'] = 'failed'
                step2['error'] = f'磁盘空间不足: {free_space_mb:.2f}MB < {config.UPGRADE_CONFIG["min_free_space_mb"]}MB'
                result['status'] = 'failed'
                return result
            step2['status'] = 'success'
            step2['result'] = f'可用空间: {free_space_mb:.2f}MB'

            # 3. 更新配置文件
            step3 = {'name': 'update_config', 'status': 'running'}
            result['steps'].append(step3)
            if target_version:
                config.VERSION = target_version
            config.save_to_file('config/config.json')
            step3['status'] = 'success'

            # 4. 更新依赖
            step4 = {'name': 'update_dependencies', 'status': 'running'}
            result['steps'].append(step4)
                    subprocess.run(['pip3', 'install', '-r', 'requirements.txt'],
                step4['status'] = 'success'
            except Exception as e:
                step4['status'] = 'warning'
                step4['error'] = str(e)

            # 5. 清理缓存
            result['steps'].append(step5)
            self._cleanup_cache()
            step5['status'] = 'success'
            # 记录升级历史
            self.upgrade_history.append(result)

            logger.info(f"系统升级完成: {config.VERSION}")
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"系统升级失败: {str(e)}")

            # 尝试回滚
            if config.UPGRADE_CONFIG['rollback_on_failure']:
                logger.info("尝试回滚系统")
                self._rollback_upgrade()

        return result
    def _cleanup_cache(self):
        cache_dirs = ['__pycache__', '.pytest_cache', 'node_modules/.cache', '.cache']
                try:
                    if os.path.isfile(cache_dir):
                        os.remove(cache_dir)
                    else:
                        shutil.rmtree(cache_dir)
                    logger.info(f"清理缓存: {cache_dir}")
                except Exception as e:
                    logger.error(f"清理缓存失败: {cache_dir}: {str(e)}")

    def _rollback_upgrade(self):
        """回滚升级"""
        logger.info("开始回滚系统")
        # 这里可以实现回滚逻辑，从备份中恢复
        """获取维护报告

        Returns:
            dict: 维护报告
        return {
            'generated_at': datetime.now().isoformat(),
            'current_version': config.VERSION,
            'build_date': config.BUILD_DATE,
            'maintenance_history': self.maintenance_history[-20:],  # 最近20条记录
            'upgrade_history': self.upgrade_history[-10:],  # 最近10条记录
            'maintenance_config': config.MAINTENANCE_CONFIG,
            'next_backup': self._get_next_backup_time(),
            'next_health_check': self._get_next_health_check_time()
        }

    def _get_next_backup_time(self):
        if self.maintenance_history:
            last_backup = datetime.fromisoformat(self.maintenance_history[-1]['timestamp'])
            return next_backup.isoformat()
        return datetime.now().isoformat()
        """获取下次健康检查时间"""
        return (datetime.now() + timedelta(seconds=config.MAINTENANCE_CONFIG['health_check_interval'])).isoformat()

maintenance_service = MaintenanceService()
