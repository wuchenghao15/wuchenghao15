# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""系统环境管理器 - 增强版"""

import os
import sys
import time
import json
import uuid
import logging
import platform
import psutil
import subprocess
import sqlite3
import threading
from enum import Enum
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('environment_manager')


class EnvironmentType(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    STAGING = "staging"


class DependencyStatus(Enum):
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    OUTDATED = "outdated"
    UNKNOWN = "unknown"


class SystemMetricType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"


class EnvironmentManager:
    """系统环境管理器 - 增强版"""

    def __init__(self):
        """初始化环境管理器"""
        self.system_type = platform.system()
        self.system_version = platform.version()
        self.python_version = platform.python_version()
        self.manager_version = "2.0.0"
        
        self.environment_type = self._detect_environment()
        self.monitoring_history: List[Dict] = []
        self.monitoring_enabled = False
        
        self._init_database()
        
        logger.info(f"环境管理器初始化完成,系统: {self.system_type}, 版本: {self.manager_version}, 环境: {self.environment_type.value}")

    def _init_database(self):
        """初始化数据库"""
        try:
            db_path = 'environment_manager.db'
            self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS environments (
                    env_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    env_type TEXT NOT NULL,
                    description TEXT,
                    config TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS environment_variables (
                    var_id TEXT PRIMARY KEY,
                    env_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    is_secret BOOLEAN DEFAULT FALSE,
                    description TEXT,
                    created_at REAL,
                    FOREIGN KEY (env_id) REFERENCES environments(env_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependencies (
                    dep_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    required_version TEXT,
                    status TEXT NOT NULL,
                    install_command TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    metric_id TEXT PRIMARY KEY,
                    metric_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_backups (
                    backup_id TEXT PRIMARY KEY,
                    backup_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    env_id TEXT,
                    created_at REAL,
                    FOREIGN KEY (env_id) REFERENCES environments(env_id)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_environments_type ON environments(env_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)')
            
            self.db_conn.commit()
            
            self._load_default_environment()
        except Exception as e:
            logger.error(f"环境管理数据库初始化失败: {str(e)}")

    def _detect_environment(self) -> EnvironmentType:
        """检测当前环境类型"""
        env_name = os.environ.get('ENVIRONMENT', 'development').lower()
        
        if env_name == 'production':
            return EnvironmentType.PRODUCTION
        elif env_name == 'staging':
            return EnvironmentType.STAGING
        elif env_name == 'testing':
            return EnvironmentType.TESTING
        else:
            return EnvironmentType.DEVELOPMENT

    def _load_default_environment(self):
        """加载默认环境配置"""
        default_config = {
            'debug': True,
            'log_level': 'INFO',
            'max_workers': 4,
            'timeout': 30,
            'retry_count': 3
        }
        
        env = {
            'env_id': 'default',
            'name': '默认环境',
            'env_type': self.environment_type.value,
            'description': '系统默认环境配置',
            'config': json.dumps(default_config),
            'is_active': True,
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM environments WHERE env_id = ?', ('default',))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO environments 
                (env_id, name, env_type, description, config, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                env['env_id'],
                env['name'],
                env['env_type'],
                env['description'],
                env['config'],
                env['is_active'],
                env['created_at'],
                env['updated_at']
            ))
            self.db_conn.commit()

    def create_environment(self, name: str, env_type: EnvironmentType,
                          description: str = "", config: Dict = None) -> str:
        """创建环境配置"""
        if config is None:
            config = {}
        
        env_id = f"env_{uuid.uuid4().hex[:8]}"
        
        env = {
            'env_id': env_id,
            'name': name,
            'env_type': env_type.value,
            'description': description,
            'config': json.dumps(config),
            'is_active': True,
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT INTO environments 
            (env_id, name, env_type, description, config, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            env['env_id'],
            env['name'],
            env['env_type'],
            env['description'],
            env['config'],
            env['is_active'],
            env['created_at'],
            env['updated_at']
        ))
        self.db_conn.commit()
        
        logger.info(f"创建环境: {name} ({env_id})")
        return env_id

    def get_environment(self, env_id: str) -> Optional[Dict]:
        """获取环境配置"""
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM environments WHERE env_id = ?', (env_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'env_id': row[0],
                'name': row[1],
                'env_type': row[2],
                'description': row[3],
                'config': json.loads(row[4]),
                'is_active': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            }
        
        return None

    def list_environments(self) -> List[Dict]:
        """列出所有环境配置"""
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM environments')
        
        environments = []
        for row in cursor.fetchall():
            environments.append({
                'env_id': row[0],
                'name': row[1],
                'env_type': row[2],
                'description': row[3],
                'is_active': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        return environments

    def set_environment_variable(self, env_id: str, name: str, value: str,
                                is_secret: bool = False, description: str = "") -> bool:
        """设置环境变量"""
        var_id = f"var_{uuid.uuid4().hex[:8]}"
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO environment_variables 
                (var_id, env_id, name, value, is_secret, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                var_id,
                env_id,
                name,
                value,
                is_secret,
                description,
                time.time()
            ))
            self.db_conn.commit()
            
            os.environ[name] = value
            logger.info(f"设置环境变量: {name}")
            return True
        except Exception as e:
            logger.error(f"设置环境变量失败: {str(e)}")
            return False

    def get_environment_variables(self, env_id: str) -> List[Dict]:
        """获取环境变量"""
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM environment_variables WHERE env_id = ?', (env_id,))
        
        variables = []
        for row in cursor.fetchall():
            variables.append({
                'var_id': row[0],
                'name': row[2],
                'value': row[3] if not row[4] else '***',
                'is_secret': row[4],
                'description': row[5],
                'created_at': row[6]
            })
        
        return variables

    def get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            'system_type': self.system_type,
            'system_version': self.system_version,
            'python_version': self.python_version,
            'environment_type': self.environment_type.value,
            'hostname': platform.node(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'machine': platform.machine()
        }

    def monitor_system(self) -> Dict:
        """监控系统状态"""
        try:
            logger.info("开始监控系统状态...")

            cpu_freq = psutil.cpu_freq()
            system_status = {
                'cpu': {
                    'count': psutil.cpu_count(),
                    'usage': psutil.cpu_percent(interval=1),
                    'frequency': cpu_freq.current if cpu_freq else None,
                    'cores': psutil.cpu_percent(percpu=True)
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'used': psutil.virtual_memory().used,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': [],
                'network': {
                    'connections': len(psutil.net_connections()),
                    'interfaces': []
                },
                'process': {
                    'count': len(psutil.pids()),
                    'running': 0,
                    'sleeping': 0,
                    'total_threads': 0
                },
                'system': {
                    'version': self.system_version,
                    'python_version': self.python_version,
                    'uptime': time.time() - psutil.boot_time()
                },
                'timestamp': time.time()
            }

            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    system_status['disk'].append({
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'fstype': part.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except:
                    pass

            for iface, addrs in psutil.net_if_addrs().items():
                addresses = []
                for addr in addrs:
                    addresses.append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                system_status['network']['interfaces'].append({
                    'name': iface,
                    'addresses': addresses
                })

            for pid in psutil.pids()[:20]:
                try:
                    proc = psutil.Process(pid)
                    system_status['process']['total_threads'] += proc.num_threads()
                    if proc.status() == 'running':
                        system_status['process']['running'] += 1
                    elif proc.status() == 'sleeping':
                        system_status['process']['sleeping'] += 1
                except:
                    pass

            self._save_system_metrics(system_status)
            
            if len(self.monitoring_history) >= 100:
                self.monitoring_history.pop(0)
            self.monitoring_history.append(system_status)

            logger.info("系统状态监控完成")
            return system_status
        except Exception as e:
            logger.error(f"监控系统状态失败: {e}")
            return {}

    def _save_system_metrics(self, metrics: Dict):
        """保存系统指标到数据库"""
        try:
            metric_id = f"metric_{uuid.uuid4().hex[:8]}"
            
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (metric_id, metric_type, value, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                metric_id + '_cpu',
                SystemMetricType.CPU.value,
                json.dumps(metrics['cpu']),
                metrics['timestamp']
            ))
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (metric_id, metric_type, value, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                metric_id + '_memory',
                SystemMetricType.MEMORY.value,
                json.dumps(metrics['memory']),
                metrics['timestamp']
            ))
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (metric_id, metric_type, value, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                metric_id + '_disk',
                SystemMetricType.DISK.value,
                json.dumps(metrics['disk']),
                metrics['timestamp']
            ))
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (metric_id, metric_type, value, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                metric_id + '_network',
                SystemMetricType.NETWORK.value,
                json.dumps(metrics['network']),
                metrics['timestamp']
            ))
            
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存系统指标失败: {str(e)}")

    def get_system_metrics(self, metric_type: SystemMetricType = None,
                          start_time: float = None, end_time: float = None) -> List[Dict]:
        """获取系统指标历史"""
        query = 'SELECT * FROM system_metrics WHERE 1=1'
        params = []
        
        if metric_type:
            query += ' AND metric_type = ?'
            params.append(metric_type.value)
        
        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)
        
        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)
        
        query += ' ORDER BY timestamp DESC LIMIT 100'
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        
        metrics = []
        for row in cursor.fetchall():
            metrics.append({
                'metric_id': row[0],
                'metric_type': row[1],
                'value': json.loads(row[2]),
                'timestamp': row[3]
            })
        
        return metrics

    def check_dependency(self, name: str, required_version: str = "") -> Dict:
        """检查依赖状态"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', name],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    'name': name,
                    'version': None,
                    'required_version': required_version,
                    'status': DependencyStatus.NOT_INSTALLED.value
                }
            
            version = None
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':')[1].strip()
                    break
            
            status = DependencyStatus.INSTALLED.value
            if required_version and version != required_version:
                status = DependencyStatus.OUTDATED.value
            
            return {
                'name': name,
                'version': version,
                'required_version': required_version,
                'status': status
            }
            
        except Exception as e:
            return {
                'name': name,
                'version': None,
                'required_version': required_version,
                'status': DependencyStatus.UNKNOWN.value,
                'error': str(e)
            }

    def install_dependency(self, name: str, version: str = "") -> bool:
        """安装依赖"""
        try:
            package = f"{name}=={version}" if version else name
            
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"依赖安装成功: {package}")
                return True
            else:
                logger.error(f"依赖安装失败: {package}, 错误: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"依赖安装失败: {name}, 错误: {str(e)}")
            return False

    def get_dependency_stats(self) -> Dict:
        """获取依赖统计信息"""
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {'error': '无法获取依赖列表'}
        
        lines = result.stdout.strip().split('\n')[2:]
        dependencies = []
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                dependencies.append({
                    'name': parts[0],
                    'version': parts[1]
                })
        
        return {
            'total_dependencies': len(dependencies),
            'dependencies': dependencies[:50]
        }

    def backup_config(self, env_id: str, backup_name: str = "") -> str:
        """备份配置"""
        env = self.get_environment(env_id)
        if not env:
            return ""
        
        backup_id = f"backup_{uuid.uuid4().hex[:8]}"
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO config_backups 
                (backup_id, backup_name, content, env_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                backup_id,
                backup_name or f"备份_{int(time.time())}",
                json.dumps(env),
                env_id,
                time.time()
            ))
            self.db_conn.commit()
            
            logger.info(f"配置备份成功: {backup_id}")
            return backup_id
        except Exception as e:
            logger.error(f"配置备份失败: {str(e)}")
            return ""

    def restore_config(self, backup_id: str) -> bool:
        """恢复配置"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT * FROM config_backups WHERE backup_id = ?', (backup_id,))
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"备份不存在: {backup_id}")
                return False
            
            env_data = json.loads(row[2])
            
            cursor.execute('''
                UPDATE environments 
                SET name = ?, env_type = ?, description = ?, config = ?, updated_at = ?
                WHERE env_id = ?
            ''', (
                env_data['name'],
                env_data['env_type'],
                env_data['description'],
                json.dumps(env_data['config']),
                time.time(),
                env_data['env_id']
            ))
            self.db_conn.commit()
            
            logger.info(f"配置恢复成功: {backup_id}")
            return True
        except Exception as e:
            logger.error(f"配置恢复失败: {str(e)}")
            return False

    def list_backups(self, env_id: str = None) -> List[Dict]:
        """列出备份"""
        query = 'SELECT * FROM config_backups WHERE 1=1'
        params = []
        
        if env_id:
            query += ' AND env_id = ?'
            params.append(env_id)
        
        query += ' ORDER BY created_at DESC'
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        
        backups = []
        for row in cursor.fetchall():
            backups.append({
                'backup_id': row[0],
                'backup_name': row[1],
                'env_id': row[3],
                'created_at': row[4]
            })
        
        return backups

    def get_environment_stats(self) -> Dict:
        """获取环境统计信息"""
        env_list = self.list_environments()
        backups = self.list_backups()
        metrics = self.get_system_metrics()
        
        return {
            'total_environments': len(env_list),
            'active_environments': sum(1 for e in env_list if e['is_active']),
            'total_backups': len(backups),
            'recent_metrics_count': len(metrics),
            'system_info': self.get_system_info()
        }


environment_manager = EnvironmentManager()