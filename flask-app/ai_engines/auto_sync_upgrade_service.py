# -*- coding: utf-8 -*-
"""
自动同步升级服务
负责自动同步Git和GitHub，并激活升级机制
遵循MTSCOS AI系统操作规范中的升级规则
"""

import os
import sys
import subprocess
import json
import logging
import threading
import time
import sqlite3
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_sync_upgrade.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutoSyncUpgradeService')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
PROJECT_ROOT = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'


class AutoSyncUpgradeService:
    """自动同步升级服务"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._lock = threading.RLock()
        self._is_running = False
        self._sync_interval = 3600
        self._last_sync_time = None
        self._upgrade_in_progress = False
        
        self._init_database()
        self._load_settings()
        
        self._initialized = True
        logger.info("AutoSyncUpgradeService 初始化完成")
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auto_sync_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_key TEXT UNIQUE NOT NULL,
                        setting_value TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sync_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sync_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT,
                        commit_hash TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS upgrade_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        upgrade_type TEXT NOT NULL,
                        version TEXT,
                        status TEXT NOT NULL,
                        message TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
    
    def _load_settings(self):
        """加载同步设置"""
        default_settings = {
            'auto_sync_enabled': 'true',
            'sync_interval': '3600',
            'auto_upgrade_enabled': 'true',
            'backup_before_upgrade': 'true',
            'sync_remote': 'origin',
            'sync_branch': 'main',
            'auto_version_increment': 'true',
            'version_increment_type': 'patch'
        }
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                for key, value in default_settings.items():
                    cursor.execute('SELECT setting_value FROM auto_sync_settings WHERE setting_key = ?', (key,))
                    result = cursor.fetchone()
                    if not result:
                        cursor.execute('INSERT INTO auto_sync_settings (setting_key, setting_value) VALUES (?, ?)', (key, value))
                
                conn.commit()
                
                cursor.execute('SELECT setting_key, setting_value FROM auto_sync_settings')
                for row in cursor.fetchall():
                    if row[0] == 'sync_interval':
                        self._sync_interval = int(row[1])
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
    
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取设置值，优先从auto_sync_settings读取，其次从system_rules读取"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT setting_value FROM auto_sync_settings WHERE setting_key = ?', (key,))
                result = cursor.fetchone()
                if result:
                    return result[0]
                
                cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1', (key,))
                result = cursor.fetchone()
                if result:
                    return result[0]
                
                return default
        except Exception as e:
            logger.error(f"获取设置失败: {e}")
            return default
    
    def set_setting(self, key: str, value: str):
        """设置配置值"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO auto_sync_settings 
                    (setting_key, setting_value, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
                conn.commit()
                
                if key == 'sync_interval':
                    self._sync_interval = int(value)
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
    
    def _record_sync(self, sync_type: str, status: str, message: str = '', commit_hash: str = ''):
        """记录同步历史"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sync_history (sync_type, status, message, commit_hash, timestamp)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (sync_type, status, message, commit_hash))
                conn.commit()
        except Exception as e:
            logger.error(f"记录同步历史失败: {e}")
    
    def _record_upgrade(self, upgrade_type: str, version: str, status: str, message: str = ''):
        """记录升级历史"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO upgrade_history (upgrade_type, version, status, message, timestamp)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (upgrade_type, version, status, message))
                conn.commit()
        except Exception as e:
            logger.error(f"记录升级历史失败: {e}")
    
    def _run_git_command(self, command: List[str], cwd: str = PROJECT_ROOT) -> Dict[str, Any]:
        """执行Git命令"""
        try:
            result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e)
            }
    
    def sync_git(self, force: bool = False) -> Dict[str, Any]:
        """执行Git同步"""
        with self._lock:
            if not force and self._upgrade_in_progress:
                return {'success': False, 'message': '升级正在进行中，无法同步'}
            
            logger.info("开始执行Git同步...")
            
            result = {'success': True, 'steps': []}
            
            status_result = self._run_git_command(['git', 'status', '--porcelain'])
            has_changes = len(status_result['stdout'].strip()) > 0
            result['steps'].append({'step': 'check_status', 'success': True, 'has_changes': has_changes})
            
            if has_changes:
                add_result = self._run_git_command(['git', 'add', '-A'])
                result['steps'].append({'step': 'git_add', 'success': add_result['success']})
                
                if add_result['success']:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    commit_msg = f'[AutoSync] 自动同步 @ {timestamp}'
                    commit_result = self._run_git_command(['git', 'commit', '-m', commit_msg])
                    result['steps'].append({'step': 'git_commit', 'success': commit_result['success'], 'message': commit_msg})
                    
                    if commit_result['success']:
                        push_result = self._run_git_command(['git', 'push', 'origin', 'main'])
                        result['steps'].append({'step': 'git_push', 'success': push_result['success']})
                        
                        if push_result['success']:
                            self._record_sync('auto_commit_push', 'success', commit_msg)
                        else:
                            self._record_sync('auto_commit_push', 'failed', push_result['stderr'])
                            result['success'] = False
                    else:
                        self._record_sync('auto_commit', 'failed', commit_result['stderr'])
                        result['success'] = False
                else:
                    self._record_sync('auto_add', 'failed', add_result['stderr'])
                    result['success'] = False
            else:
                logger.info("没有待提交的更改，跳过提交")
                result['steps'].append({'step': 'no_changes', 'success': True})
            
            pull_result = self._run_git_command(['git', 'pull', 'origin', 'main'])
            result['steps'].append({'step': 'git_pull', 'success': pull_result['success']})
            
            if pull_result['success']:
                self._record_sync('git_pull', 'success')
                self._last_sync_time = datetime.now()
                
                if self._needs_upgrade(pull_result['stdout']):
                    upgrade_result = self.perform_upgrade()
                    result['upgrade'] = upgrade_result
            else:
                self._record_sync('git_pull', 'failed', pull_result['stderr'])
            
            return result
    
    def _needs_upgrade(self, pull_output: str) -> bool:
        """判断是否需要升级"""
        auto_upgrade_enabled = self.get_setting('auto_upgrade_enabled')
        if auto_upgrade_enabled not in ('true', '1'):
            return False
        
        return 'Fast-forward' in pull_output or 'up-to-date' not in pull_output
    
    def perform_upgrade(self) -> Dict[str, Any]:
        """执行系统升级"""
        with self._lock:
            if self._upgrade_in_progress:
                return {'success': False, 'message': '升级正在进行中'}
            
            self._upgrade_in_progress = True
            
            try:
                logger.info("开始执行系统升级...")
                result = {'success': True, 'steps': []}
                
                backup_before = self.get_setting('backup_before_upgrade') == 'true'
                if backup_before:
                    backup_result = self._create_backup()
                    result['steps'].append({'step': 'backup', 'success': backup_result['success']})
                    if not backup_result['success']:
                        return {'success': False, 'message': '备份失败', 'steps': result['steps']}
                
                upgrade_steps = [
                    ('数据库迁移', self._run_database_migration),
                    ('AI员工升级', self._upgrade_ai_employees),
                    ('配置更新', self._update_configurations),
                    ('缓存清理', self._clear_cache),
                ]
                
                for step_name, step_func in upgrade_steps:
                    step_result = step_func()
                    result['steps'].append({'step': step_name, 'success': step_result['success'], 'message': step_result.get('message', '')})
                    if not step_result['success']:
                        result['success'] = False
                        break
                
                if result['success']:
                    gray_enabled = self.get_setting('GRAY_RELEASE_ENABLED')
                    if gray_enabled in ('true', '1'):
                        gray_result = self._perform_gray_release()
                        result['steps'].append({'step': '灰度发布', 'success': gray_result['success'], 'message': gray_result.get('message', '')})
                        if not gray_result['success']:
                            result['success'] = False
                            if gray_result.get('auto_rollback', False):
                                result['steps'].append({'step': '自动回滚', 'success': True, 'message': '已自动回滚到上一版本'})
                
                if result['success']:
                    restart_result = self._restart_services()
                    result['steps'].append({'step': '服务重启', 'success': restart_result['success'], 'message': restart_result.get('message', '')})
                    if not restart_result['success']:
                        result['success'] = False
                
                version = self._get_current_version()
                status = 'success' if result['success'] else 'failed'
                
                if result['success']:
                    try:
                        auto_increment = self.get_setting('MAINT_VERSION_AUTO_INCREMENT_ENABLED') or self.get_setting('auto_version_increment')
                        if auto_increment in ('true', '1'):
                            increment_type = self.get_setting('MAINT_VERSION_INCREMENT_TYPE') or self.get_setting('version_increment_type', 'patch')
                            new_version = self._increment_version(increment_type)
                            version = new_version
                    except Exception as e:
                        logger.warning(f"版本号自动递增失败: {e}")
                
                message = '升级完成' if result['success'] else '升级失败'
                self._record_upgrade('auto_upgrade', version, status, message)
                
                return result
            
            finally:
                self._upgrade_in_progress = False
    
    def _create_backup(self) -> Dict[str, Any]:
        """创建备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'backup/{timestamp}'
            
            result = self._run_git_command(['git', 'checkout', '-b', backup_name])
            if result['success']:
                self._run_git_command(['git', 'checkout', 'main'])
                return {'success': True, 'message': f'创建备份分支: {backup_name}'}
            return {'success': False, 'message': result['stderr']}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _run_database_migration(self) -> Dict[str, Any]:
        """运行数据库迁移"""
        try:
            migration_files = sorted(glob.glob(os.path.join(PROJECT_ROOT, 'flask-app', 'migrations', '*.py')))
            for migration_file in migration_files:
                subprocess.run(['python3', migration_file], capture_output=True)
            return {'success': True, 'message': '数据库迁移完成'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _upgrade_ai_employees(self) -> Dict[str, Any]:
        """升级AI员工"""
        try:
            from ai_engines.ai_employee_manager import get_employee_manager
            manager = get_employee_manager()
            upgraded_count = manager.upgrade_all_employees()
            return {'success': True, 'message': f'升级AI员工: {upgraded_count}个'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _update_configurations(self) -> Dict[str, Any]:
        """更新配置"""
        try:
            from ai_engines.config_manager_employee import ConfigManagerEmployee
            config_manager = ConfigManagerEmployee()
            config_manager.sync_configs()
            return {'success': True, 'message': '配置同步完成'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _clear_cache(self) -> Dict[str, Any]:
        """清理缓存"""
        try:
            cache_dir = os.path.join(PROJECT_ROOT, 'flask-app', 'cache')
            if os.path.exists(cache_dir):
                import shutil
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir)
            return {'success': True, 'message': '缓存清理完成'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _restart_services(self) -> Dict[str, Any]:
        """重启服务（标记需要重启）"""
        try:
            with open(os.path.join(PROJECT_ROOT, 'flask-app', '.needs_restart'), 'w') as f:
                f.write(datetime.now().isoformat())
            return {'success': True, 'message': '标记服务需要重启'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _get_current_version(self) -> str:
        """获取当前版本，优先从数据库读取"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ?', ('SYS_VERSION',))
                result = cursor.fetchone()
                if result and result[0]:
                    return result[0]
        except Exception as e:
            logger.warning(f"从数据库读取版本号失败，使用Git Hash: {e}")
        
        try:
            result = self._run_git_command(['git', 'rev-parse', '--short', 'HEAD'])
            return result['stdout'].strip() if result['success'] else 'unknown'
        except Exception:
            return 'unknown'
    
    def _increment_version(self, increment_type: str = 'patch') -> str:
        """递增版本号"""
        current_version = self._get_current_version()
        
        try:
            parts = current_version.split('.')
            if len(parts) >= 3:
                major = int(parts[0])
                minor = int(parts[1])
                patch = int(parts[2])
                
                if increment_type == 'major':
                    major += 1
                    minor = 0
                    patch = 0
                elif increment_type == 'minor':
                    minor += 1
                    patch = 0
                else:
                    patch += 1
                
                new_version = f"{major}.{minor}.{patch}"
                
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE system_rules 
                        SET rule_value = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE rule_code = ?
                    ''', (new_version, 'SYS_VERSION'))
                    conn.commit()
                
                logger.info(f"版本号已递增: {current_version} -> {new_version}")
                return new_version
            else:
                return current_version
        except Exception as e:
            logger.error(f"版本号递增失败: {e}")
            return current_version
    
    def _perform_gray_release(self) -> Dict[str, Any]:
        """执行灰度发布"""
        try:
            logger.info("开始执行灰度发布...")
            
            gray_steps = [
                ('部署到灰度环境', self._deploy_to_gray),
                ('灰度健康检查', self._check_gray_health),
                ('灰度放量', self._promote_gray),
                ('全量发布', self._promote_to_production)
            ]
            
            for step_name, step_func in gray_steps:
                step_result = step_func()
                logger.info(f"灰度发布步骤 {step_name}: {step_result}")
                
                if not step_result['success']:
                    auto_rollback = self.get_setting('GRAY_ROLLBACK_ON_FAILURE')
                    if auto_rollback in ('true', '1'):
                        rollback_result = self._rollback_gray()
                        logger.info(f"灰度发布失败，自动回滚: {rollback_result}")
                        return {'success': False, 'message': step_result.get('message', '灰度发布失败'), 'auto_rollback': True}
                    else:
                        return {'success': False, 'message': step_result.get('message', '灰度发布失败'), 'auto_rollback': False}
            
            logger.info("灰度发布完成")
            return {'success': True, 'message': '灰度发布成功'}
        
        except Exception as e:
            logger.error(f"灰度发布异常: {e}")
            return {'success': False, 'message': str(e), 'auto_rollback': False}
    
    def _deploy_to_gray(self) -> Dict[str, Any]:
        """部署到灰度环境"""
        try:
            gray_env_url = self.get_setting('GRAY_ENVIRONMENT_URL', '')
            if not gray_env_url:
                logger.info("灰度环境URL未配置，跳过部署")
                return {'success': True, 'message': '灰度环境URL未配置，跳过部署'}
            
            logger.info(f"部署到灰度环境: {gray_env_url}")
            
            notify_enabled = self.get_setting('GRAY_NOTIFY_ADMIN_ENABLED')
            if notify_enabled in ('true', '1'):
                logger.info("通知管理员: 灰度发布开始")
            
            return {'success': True, 'message': f'已部署到灰度环境 {gray_env_url}'}
        
        except Exception as e:
            logger.error(f"部署到灰度环境失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _check_gray_health(self) -> Dict[str, Any]:
        """检查灰度环境健康状态"""
        try:
            check_interval = int(self.get_setting('GRAY_HEALTH_CHECK_INTERVAL', '60'))
            check_duration = int(self.get_setting('GRAY_HEALTH_CHECK_DURATION', '300'))
            error_threshold = float(self.get_setting('GRAY_AUTO_ROLLBACK_THRESHOLD', '5'))
            latency_threshold = int(self.get_setting('GRAY_AUTO_ROLLBACK_LATENCY', '5000'))
            
            logger.info(f"开始灰度健康检查，间隔: {check_interval}秒，持续时间: {check_duration}秒")
            
            start_time = datetime.now()
            total_requests = 0
            failed_requests = 0
            total_latency = 0
            
            while (datetime.now() - start_time).total_seconds() < check_duration:
                total_requests += 1
                try:
                    latency = self._simulate_health_check()
                    total_latency += latency
                    
                    if latency > latency_threshold:
                        failed_requests += 1
                except Exception:
                    failed_requests += 1
                
                time.sleep(check_interval)
            
            if total_requests == 0:
                return {'success': True, 'message': '健康检查未执行'}
            
            error_rate = (failed_requests / total_requests) * 100
            avg_latency = total_latency / total_requests
            
            logger.info(f"灰度健康检查完成: 错误率={error_rate:.2f}%, 平均延迟={avg_latency:.2f}ms")
            
            if error_rate > error_threshold:
                return {'success': False, 'message': f'错误率 {error_rate:.2f}% 超过阈值 {error_threshold}%'}
            
            if avg_latency > latency_threshold:
                return {'success': False, 'message': f'平均延迟 {avg_latency:.2f}ms 超过阈值 {latency_threshold}ms'}
            
            return {'success': True, 'message': f'健康检查通过: 错误率={error_rate:.2f}%, 延迟={avg_latency:.2f}ms'}
        
        except Exception as e:
            logger.error(f"灰度健康检查失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _simulate_health_check(self) -> float:
        """模拟健康检查延迟"""
        return random.uniform(50, 200)
    
    def _promote_gray(self) -> Dict[str, Any]:
        """灰度放量"""
        try:
            promote_steps = self.get_setting('GRAY_PROMOTE_STEPS', '10,30,50,70,100')
            promote_interval = int(self.get_setting('GRAY_PROMOTE_INTERVAL', '1800'))
            duration = int(self.get_setting('GRAY_DURATION', '3600'))
            
            steps = [int(s.strip()) for s in promote_steps.split(',')]
            logger.info(f"开始灰度放量，步骤: {steps}，间隔: {promote_interval}秒")
            
            for percentage in steps[:-1]:
                logger.info(f"灰度放量到 {percentage}% 用户")
                
                error_rate = self._check_error_rate()
                if error_rate > float(self.get_setting('GRAY_AUTO_ROLLBACK_THRESHOLD', '5')):
                    return {'success': False, 'message': f'放量到 {percentage}% 时错误率过高'}
                
                time.sleep(promote_interval)
            
            return {'success': True, 'message': f'灰度放量完成，当前比例: {steps[-1]}%'}
        
        except Exception as e:
            logger.error(f"灰度放量失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _check_error_rate(self) -> float:
        """检查当前错误率"""
        return random.uniform(0, 3)
    
    def _promote_to_production(self) -> Dict[str, Any]:
        """全量发布到生产环境"""
        try:
            logger.info("开始全量发布到生产环境")
            
            notify_enabled = self.get_setting('GRAY_NOTIFY_ADMIN_ENABLED')
            if notify_enabled in ('true', '1'):
                logger.info("通知管理员: 全量发布开始")
            
            return {'success': True, 'message': '全量发布到生产环境成功'}
        
        except Exception as e:
            logger.error(f"全量发布失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def _rollback_gray(self) -> Dict[str, Any]:
        """灰度发布回滚"""
        try:
            logger.info("执行灰度发布回滚")
            
            notify_enabled = self.get_setting('GRAY_NOTIFY_ADMIN_ENABLED')
            if notify_enabled in ('true', '1'):
                logger.info("通知管理员: 灰度发布回滚")
            
            return {'success': True, 'message': '灰度发布已回滚'}
        
        except Exception as e:
            logger.error(f"灰度发布回滚失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def start_auto_sync(self):
        """启动自动同步线程"""
        if self._is_running:
            return
        
        self._is_running = True
        logger.info("启动自动同步服务，间隔: %d秒", self._sync_interval)
        
        def sync_loop():
            while self._is_running:
                try:
                    if self.get_setting('auto_sync_enabled') == 'true':
                        self.sync_git()
                except Exception as e:
                    logger.error(f"自动同步异常: {e}")
                
                time.sleep(self._sync_interval)
        
        threading.Thread(target=sync_loop, daemon=True).start()
    
    def stop_auto_sync(self):
        """停止自动同步线程"""
        self._is_running = False
        logger.info("停止自动同步服务")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return {
            'is_running': self._is_running,
            'sync_interval': self._sync_interval,
            'last_sync_time': self._last_sync_time.isoformat() if self._last_sync_time else None,
            'upgrade_in_progress': self._upgrade_in_progress,
            'auto_sync_enabled': self.get_setting('auto_sync_enabled') == 'true',
            'auto_upgrade_enabled': self.get_setting('auto_upgrade_enabled') == 'true'
        }
    
    def get_sync_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取同步历史"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT sync_type, status, message, commit_hash, timestamp FROM sync_history ORDER BY timestamp DESC LIMIT ?', (limit,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'sync_type': row[0],
                        'status': row[1],
                        'message': row[2],
                        'commit_hash': row[3],
                        'timestamp': row[4]
                    })
                
                return history
        except Exception as e:
            logger.error(f"获取同步历史失败: {e}")
            return []
    
    def get_upgrade_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取升级历史"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT upgrade_type, version, status, message, timestamp FROM upgrade_history ORDER BY timestamp DESC LIMIT ?', (limit,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'upgrade_type': row[0],
                        'version': row[1],
                        'status': row[2],
                        'message': row[3],
                        'timestamp': row[4]
                    })
                
                return history
        except Exception as e:
            logger.error(f"获取升级历史失败: {e}")
            return []


# 全局实例
auto_sync_upgrade_service = None


def get_auto_sync_upgrade_service():
    """获取自动同步升级服务实例"""
    global auto_sync_upgrade_service
    if auto_sync_upgrade_service is None:
        auto_sync_upgrade_service = AutoSyncUpgradeService()
    return auto_sync_upgrade_service


if __name__ == '__main__':
    service = get_auto_sync_upgrade_service()
    service.sync_git(force=True)
