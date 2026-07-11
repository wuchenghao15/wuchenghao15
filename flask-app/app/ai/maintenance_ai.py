#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI维护员工
负责系统例行维护、健康检查、数据清理和版本升级
"""

import os
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from app.utils.logging import logger


class DatabaseCleaner:
    """数据库清理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '..', 'app.db')
        self.db_path = db_path
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def clean_old_logs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """清理旧日志"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
                if not cursor.fetchone():
                    return {'cleaned': 0, 'days_kept': days_to_keep, 'message': 'logs表不存在'}
                
                cursor.execute('SELECT COUNT(*) FROM logs WHERE created_at < ?', 
                              (datetime.now() - timedelta(days=days_to_keep)).isoformat()[:19])
                count = cursor.fetchone()[0]
                
                if count > 0:
                    cursor.execute('DELETE FROM logs WHERE created_at < ?', 
                                  (datetime.now() - timedelta(days=days_to_keep)).isoformat()[:19])
                    logger.info(f"清理了 {count} 条旧日志")
            
            return {'cleaned': count, 'days_kept': days_to_keep}
        except Exception as e:
            logger.error(f"清理日志失败: {e}")
            return {'cleaned': 0, 'days_kept': days_to_keep, 'error': str(e)}
    
    def clean_old_sessions(self, days_to_keep: int = 7) -> Dict[str, Any]:
        """清理旧会话"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM sessions WHERE last_activity < ?', 
                          (datetime.now() - timedelta(days=days_to_keep)).isoformat()[:19])
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute('DELETE FROM sessions WHERE last_activity < ?', 
                              (datetime.now() - timedelta(days=days_to_keep)).isoformat()[:19])
                logger.info(f"清理了 {count} 个旧会话")
        
        return {'cleaned': count, 'days_kept': days_to_keep}
    
    def clean_unverified_users(self, days_to_keep: int = 14) -> Dict[str, Any]:
        """清理未验证用户"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 0 AND created_at < ?', 
                          (datetime.now() - timedelta(days=days_to_keep)).isoformat()[:19])
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute('DELETE FROM users WHERE is_active = 0 AND created_at < ?', 
                              (datetime.now() - timedelta(days=days_to_keep)).isoformat()[:19])
                logger.info(f"清理了 {count} 个未验证用户")
        
        return {'cleaned': count, 'days_kept': days_to_keep}
    
    def vacuum_database(self) -> Dict[str, Any]:
        """压缩数据库"""
        try:
            with self._get_connection() as conn:
                conn.execute('VACUUM')
            logger.info("数据库压缩完成")
            return {'success': True}
        except Exception as e:
            logger.error(f"数据库压缩失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze_database(self) -> Dict[str, Any]:
        """分析数据库"""
        try:
            with self._get_connection() as conn:
                conn.execute('ANALYZE')
            logger.info("数据库分析完成")
            return {'success': True}
        except Exception as e:
            logger.error(f"数据库分析失败: {e}")
            return {'success': False, 'error': str(e)}


class LogCleaner:
    """日志清理器"""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'logs')
        self.log_dir = log_dir
    
    def clean_old_log_files(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """清理旧日志文件"""
        cleaned = 0
        if not os.path.exists(self.log_dir):
            return {'cleaned': 0, 'message': '日志目录不存在'}
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            if os.path.isfile(filepath):
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff_date:
                    try:
                        os.remove(filepath)
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"删除日志文件失败 {filename}: {e}")
        
        logger.info(f"清理了 {cleaned} 个旧日志文件")
        return {'cleaned': cleaned, 'days_kept': days_to_keep}
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        if not os.path.exists(self.log_dir):
            return {'total_files': 0, 'total_size': 0}
        
        total_files = 0
        total_size = 0
        
        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            if os.path.isfile(filepath):
                total_files += 1
                total_size += os.path.getsize(filepath)
        
        return {
            'total_files': total_files,
            'total_size': self._format_size(total_size),
            'total_size_bytes': total_size
        }
    
    def _format_size(self, bytes_size: int) -> str:
        """格式化文件大小"""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.2f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.2f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: str = None):
        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'backups')
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, description: str = '') -> Dict[str, Any]:
        """创建数据库备份"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '..', 'app.db')
        
        if not os.path.exists(db_path):
            return {'success': False, 'error': '数据库文件不存在'}
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"app_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            shutil.copy2(db_path, backup_path)
            
            metadata = {
                'backup_path': backup_path,
                'backup_time': datetime.now().isoformat(),
                'description': description,
                'file_size': os.path.getsize(backup_path)
            }
            
            metadata_path = backup_path + '.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"数据库备份成功: {backup_path}")
            return {'success': True, 'backup_path': backup_path, 'description': description}
        
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.db'):
                filepath = os.path.join(self.backup_dir, filename)
                metadata_path = filepath + '.json'
                
                backup_info = {
                    'filename': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'size_formatted': self._format_size(os.path.getsize(filepath)),
                    'modified_time': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                }
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        backup_info.update(metadata)
                    except Exception:
                        pass
                
                backups.append(backup_info)
        
        backups.sort(key=lambda x: x['modified_time'], reverse=True)
        return backups
    
    def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """恢复备份"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '..', 'app.db')
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': '备份文件不存在'}
        
        try:
            shutil.copy2(backup_path, db_path)
            logger.info(f"数据库恢复成功: {backup_path}")
            return {'success': True, 'message': '数据库恢复成功'}
        
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def cleanup_old_backups(self, keep_count: int = 7) -> Dict[str, Any]:
        """清理旧备份"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return {'cleaned': 0, 'message': '备份数量未超过保留数量'}
        
        to_remove = backups[keep_count:]
        cleaned = 0
        
        for backup in to_remove:
            try:
                os.remove(backup['path'])
                metadata_path = backup['path'] + '.json'
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                cleaned += 1
            except Exception as e:
                logger.error(f"删除备份失败 {backup['filename']}: {e}")
        
        logger.info(f"清理了 {cleaned} 个旧备份")
        return {'cleaned': cleaned, 'kept': keep_count}
    
    def _format_size(self, bytes_size: int) -> str:
        """格式化文件大小"""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.2f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.2f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


class SystemHealthChecker:
    """系统健康检查器"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '..', 'app.db')
    
    def check_database(self) -> Dict[str, Any]:
        """检查数据库状态"""
        result = {
            'status': 'healthy',
            'details': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM users')
                result['details']['user_count'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM questions')
                result['details']['question_count'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM exams')
                result['details']['exam_count'] = cursor.fetchone()[0]
                
                cursor.execute('PRAGMA integrity_check')
                integrity = cursor.fetchone()[0]
                if integrity != 'ok':
                    result['status'] = 'warning'
                    result['details']['integrity'] = integrity
                
                db_size = os.path.getsize(self.db_path)
                result['details']['size'] = self._format_size(db_size)
                
        except Exception as e:
            result['status'] = 'error'
            result['details']['error'] = str(e)
        
        return result
    
    def check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            disk = shutil.disk_usage('/')
            total = disk.total
            used = disk.used
            free = disk.free
            percent_used = (used / total) * 100
            
            status = 'healthy'
            if percent_used > 90:
                status = 'critical'
            elif percent_used > 80:
                status = 'warning'
            
            return {
                'status': status,
                'total': self._format_size(total),
                'used': self._format_size(used),
                'free': self._format_size(free),
                'percent_used': round(percent_used, 2)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def check_logs(self) -> Dict[str, Any]:
        """检查日志状态"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'logs')
        
        if not os.path.exists(log_dir):
            return {'status': 'warning', 'message': '日志目录不存在'}
        
        total_size = 0
        file_count = 0
        
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
                file_count += 1
        
        status = 'healthy'
        if total_size > 100 * 1024 * 1024:
            status = 'warning'
        elif total_size > 500 * 1024 * 1024:
            status = 'critical'
        
        return {
            'status': status,
            'file_count': file_count,
            'total_size': self._format_size(total_size)
        }
    
    def check_backups(self) -> Dict[str, Any]:
        """检查备份状态"""
        backup_manager = BackupManager()
        backups = backup_manager.list_backups()
        
        status = 'healthy'
        message = ''
        
        if not backups:
            status = 'warning'
            message = '没有找到备份文件'
        else:
            latest_backup = backups[0]
            backup_time = datetime.fromisoformat(latest_backup['modified_time'])
            if datetime.now() - backup_time > timedelta(days=7):
                status = 'warning'
                message = '最近备份已超过7天'
        
        return {
            'status': status,
            'backup_count': len(backups),
            'latest_backup': latest_backup['filename'] if backups else None,
            'latest_backup_time': latest_backup['modified_time'] if backups else None,
            'message': message
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """获取整体健康状态"""
        checks = {
            'database': self.check_database(),
            'disk_space': self.check_disk_space(),
            'logs': self.check_logs(),
            'backups': self.check_backups()
        }
        
        overall_status = 'healthy'
        for name, check in checks.items():
            if check['status'] == 'critical':
                overall_status = 'critical'
                break
            elif check['status'] == 'warning' and overall_status == 'healthy':
                overall_status = 'warning'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': checks
        }
    
    def _format_size(self, bytes_size: int) -> str:
        """格式化文件大小"""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.2f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.2f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


class MaintenanceAIEmployee:
    """AI维护员工"""
    
    def __init__(self):
        self.db_cleaner = DatabaseCleaner()
        self.log_cleaner = LogCleaner()
        self.backup_manager = BackupManager()
        self.health_checker = SystemHealthChecker()
        self.initialized_at = datetime.now().isoformat()
        self.last_maintenance = None
        
        logger.info("AI维护员工初始化完成")
    
    def run_routine_maintenance(self) -> Dict[str, Any]:
        """运行例行维护"""
        self.last_maintenance = datetime.now().isoformat()
        
        results = {
            'started_at': self.last_maintenance,
            'tasks': []
        }
        
        results['tasks'].append({
            'name': '清理旧日志',
            'result': self.db_cleaner.clean_old_logs(30)
        })
        
        results['tasks'].append({
            'name': '清理旧会话',
            'result': self.db_cleaner.clean_old_sessions(7)
        })
        
        results['tasks'].append({
            'name': '清理未验证用户',
            'result': self.db_cleaner.clean_unverified_users(14)
        })
        
        results['tasks'].append({
            'name': '清理旧日志文件',
            'result': self.log_cleaner.clean_old_log_files(30)
        })
        
        results['tasks'].append({
            'name': '清理旧备份',
            'result': self.backup_manager.cleanup_old_backups(7)
        })
        
        results['tasks'].append({
            'name': '数据库压缩',
            'result': self.db_cleaner.vacuum_database()
        })
        
        results['tasks'].append({
            'name': '数据库分析',
            'result': self.db_cleaner.analyze_database()
        })
        
        logger.info("例行维护完成")
        return results
    
    def create_backup(self, description: str = '') -> Dict[str, Any]:
        """创建备份"""
        return self.backup_manager.create_backup(description)
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        return self.health_checker.get_overall_health()
    
    def get_maintenance_summary(self) -> Dict[str, Any]:
        """获取维护摘要"""
        return {
            'initialized_at': self.initialized_at,
            'last_maintenance': self.last_maintenance,
            'log_stats': self.log_cleaner.get_log_stats(),
            'backup_count': len(self.backup_manager.list_backups()),
            'health_status': self.health_checker.get_overall_health()['overall_status']
        }
    
    def upgrade_system_version(self) -> Dict[str, Any]:
        """升级系统版本"""
        try:
            from app.services.system_version_service import system_version_service
            result = system_version_service.upgrade_system_version()
            logger.info(f"系统版本升级: {result}")
            return result
        except Exception as e:
            logger.error(f"系统版本升级失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_health_check(self) -> Dict[str, Any]:
        """运行健康检查"""
        return self.health_checker.get_overall_health()
    
    def get_status(self) -> Dict[str, Any]:
        """获取维护状态"""
        return {
            'initialized_at': self.initialized_at,
            'last_maintenance': self.last_maintenance,
            'health_status': self.health_checker.get_overall_health(),
            'log_stats': self.log_cleaner.get_log_stats(),
            'backup_count': len(self.backup_manager.list_backups())
        }


maintenance_ai = MaintenanceAIEmployee()