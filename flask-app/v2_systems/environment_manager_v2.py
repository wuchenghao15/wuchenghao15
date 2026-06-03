# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统环境管理系统 V2.0 (Environment Manager)
增强版系统环境管理系统，支持多环境配置、环境变量管理、依赖管理和系统监控
"""

import os
import sys
import time
import uuid
import json
import shutil
import hashlib
import logging
import threading
import sqlite3
import subprocess
import platform
import psutil
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('environment_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EnvironmentManager')

class EnvironmentType(Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class ConfigStatus(Enum):
    """配置状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    PENDING = "pending"

class DependencyStatus(Enum):
    """依赖状态枚举"""
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    OUTDATED = "outdated"
    CONFLICT = "conflict"

@dataclass
class EnvironmentConfig:
    """环境配置"""
    config_id: str
    name: str
    env_type: EnvironmentType
    description: str = ""
    variables: Dict[str, str] = None
    status: ConfigStatus = ConfigStatus.ACTIVE
    created_at: float = 0.0
    updated_at: float = 0.0
    created_by: str = "system"
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class Dependency:
    """依赖项"""
    dep_id: str
    name: str
    version: str
    source: str = "pypi"
    status: DependencyStatus = DependencyStatus.NOT_INSTALLED
    required_version: str = ""
    installed_version: str = ""
    last_checked: float = 0.0
    metadata: Dict = field(default_factory=dict)

@dataclass
class SystemMetric:
    """系统指标"""
    metric_id: str
    metric_type: str
    value: float
    unit: str
    timestamp: float = 0.0
    tags: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

@dataclass
class ConfigBackup:
    """配置备份"""
    backup_id: str
    config_id: str
    backup_data: str
    checksum: str
    created_at: float = 0.0
    created_by: str = "system"
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

class EnvironmentManager:
    """增强版系统环境管理系统"""
    
    def __init__(self):
        """初始化环境管理系统"""
        self.environments: Dict[str, EnvironmentConfig] = {}
        self.dependencies: Dict[str, Dependency] = {}
        self.metrics_history: List[SystemMetric] = []
        self.backups: Dict[str, ConfigBackup] = {}
        
        self.current_environment: Optional[str] = None
        
        self.lock = threading.Lock()
        self.metric_buffer_size = 1000
        
        self._init_database()
        self._init_default_environments()
        self._load_system_info()
        
        self._start_metrics_collector()
        self._start_health_monitor()
        
        logger.info("系统环境管理系统初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_conn = sqlite3.connect('environment_manager.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS environments (
                    config_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    env_type TEXT NOT NULL,
                    description TEXT,
                    variables TEXT,
                    status TEXT DEFAULT 'active',
                    created_at REAL,
                    updated_at REAL,
                    created_by TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependencies (
                    dep_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    source TEXT DEFAULT 'pypi',
                    status TEXT DEFAULT 'not_installed',
                    required_version TEXT,
                    installed_version TEXT,
                    last_checked REAL,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    metric_id TEXT PRIMARY KEY,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    timestamp REAL,
                    tags TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_backups (
                    backup_id TEXT PRIMARY KEY,
                    config_id TEXT NOT NULL,
                    backup_data TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at REAL,
                    created_by TEXT,
                    FOREIGN KEY (config_id) REFERENCES environments(config_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_info (
                    info_key TEXT PRIMARY KEY,
                    info_value TEXT NOT NULL,
                    updated_at REAL
                )
            ''')
            
            self.db_conn.commit()
            logger.info("环境管理数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def _init_default_environments(self):
        """初始化默认环境"""
        default_envs = [
            EnvironmentConfig(
                config_id="env_dev",
                name="开发环境",
                env_type=EnvironmentType.DEVELOPMENT,
                description="用于日常开发和调试",
                variables={
                    "DEBUG": "true",
                    "LOG_LEVEL": "DEBUG",
                    "API_URL": "http://localhost:8000",
                    "DATABASE_URL": "sqlite:///dev.db",
                    "ENVIRONMENT": "development"
                }
            ),
            EnvironmentConfig(
                config_id="env_test",
                name="测试环境",
                env_type=EnvironmentType.TESTING,
                description="用于单元测试和集成测试",
                variables={
                    "DEBUG": "true",
                    "LOG_LEVEL": "INFO",
                    "API_URL": "http://test:8000",
                    "DATABASE_URL": "sqlite:///test.db",
                    "ENVIRONMENT": "testing"
                }
            ),
            EnvironmentConfig(
                config_id="env_staging",
                name="预发布环境",
                env_type=EnvironmentType.STAGING,
                description="用于上线前测试",
                variables={
                    "DEBUG": "false",
                    "LOG_LEVEL": "WARNING",
                    "API_URL": "https://staging.example.com",
                    "DATABASE_URL": "postgresql://user:pass@staging:5432/db",
                    "ENVIRONMENT": "staging"
                }
            ),
            EnvironmentConfig(
                config_id="env_prod",
                name="生产环境",
                env_type=EnvironmentType.PRODUCTION,
                description="正式生产环境",
                variables={
                    "DEBUG": "false",
                    "LOG_LEVEL": "ERROR",
                    "API_URL": "https://api.example.com",
                    "DATABASE_URL": "postgresql://user:pass@prod:5432/db",
                    "ENVIRONMENT": "production"
                }
            )
        ]
        
        with self.lock:
            for env in default_envs:
                if env.config_id not in self.environments:
                    self.environments[env.config_id] = env
                    self._save_environment(env)
    
    def _load_system_info(self):
        """加载系统信息"""
        try:
            sys_info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_release": platform.release(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "cpu_count": str(psutil.cpu_count()),
                "memory_total": str(psutil.virtual_memory().total),
                "disk_total": str(psutil.disk_usage('/').total)
            }
            
            cursor = self.db_conn.cursor()
            for key, value in sys_info.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO system_info (info_key, info_value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, value, time.time()))
            
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"加载系统信息失败: {str(e)}")
    
    def _save_environment(self, env: EnvironmentConfig):
        """保存环境配置到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO environments
                (config_id, name, env_type, description, variables, status, 
                 created_at, updated_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                env.config_id, env.name, env.env_type.value, env.description,
                json.dumps(env.variables), env.status.value, env.created_at,
                env.updated_at, env.created_by
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存环境配置失败: {str(e)}")
    
    def create_environment(self, name: str, env_type: EnvironmentType,
                         description: str = "", variables: Dict = None) -> str:
        """创建环境配置"""
        config_id = f"env_{uuid.uuid4().hex[:8]}"
        
        env = EnvironmentConfig(
            config_id=config_id,
            name=name,
            env_type=env_type,
            description=description,
            variables=variables or {}
        )
        
        with self.lock:
            self.environments[config_id] = env
            self._save_environment(env)
        
        logger.info(f"创建环境配置: {name} ({config_id})")
        return config_id
    
    def get_environment(self, config_id: str) -> Optional[EnvironmentConfig]:
        """获取环境配置"""
        with self.lock:
            return self.environments.get(config_id)
    
    def update_environment(self, config_id: str, **kwargs) -> bool:
        """更新环境配置"""
        with self.lock:
            env = self.environments.get(config_id)
            if not env:
                return False
            
            if 'name' in kwargs:
                env.name = kwargs['name']
            if 'description' in kwargs:
                env.description = kwargs['description']
            if 'variables' in kwargs:
                env.variables.update(kwargs['variables'])
            if 'status' in kwargs:
                env.status = kwargs['status']
            
            env.updated_at = time.time()
            self._save_environment(env)
        
        logger.info(f"更新环境配置: {config_id}")
        return True
    
    def delete_environment(self, config_id: str) -> bool:
        """删除环境配置"""
        with self.lock:
            if config_id not in self.environments:
                return False
            
            if config_id.startswith("env_") and config_id in ["env_dev", "env_test", "env_staging", "env_prod"]:
                logger.error("不能删除默认环境")
                return False
            
            del self.environments[config_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM environments WHERE config_id = ?', (config_id,))
            self.db_conn.commit()
        
        logger.info(f"删除环境配置: {config_id}")
        return True
    
    def list_environments(self) -> List[Dict]:
        """列出所有环境配置"""
        with self.lock:
            return [{
                "config_id": env.config_id,
                "name": env.name,
                "env_type": env.env_type.value,
                "description": env.description,
                "status": env.status.value,
                "var_count": len(env.variables),
                "created_at": env.created_at,
                "updated_at": env.updated_at
            } for env in self.environments.values()]
    
    def activate_environment(self, config_id: str) -> bool:
        """激活环境"""
        with self.lock:
            env = self.environments.get(config_id)
            if not env:
                return False
            
            if self.current_environment:
                old_env = self.environments.get(self.current_environment)
                if old_env:
                    old_env.status = ConfigStatus.INACTIVE
                    self._save_environment(old_env)
            
            self.current_environment = config_id
            env.status = ConfigStatus.ACTIVE
            self._save_environment(env)
            
            for key, value in env.variables.items():
                os.environ[key] = value
        
        logger.info(f"激活环境: {config_id}")
        return True
    
    def get_environment_variables(self, config_id: str = None) -> Dict[str, str]:
        """获取环境变量"""
        if config_id:
            env = self.environments.get(config_id)
            if env:
                return env.variables.copy()
        return dict(os.environ)
    
    def set_variable(self, config_id: str, key: str, value: str) -> bool:
        """设置环境变量"""
        with self.lock:
            env = self.environments.get(config_id)
            if not env:
                return False
            
            env.variables[key] = value
            env.updated_at = time.time()
            self._save_environment(env)
            
            if self.current_environment == config_id:
                os.environ[key] = value
        
        logger.debug(f"设置环境变量: {config_id}.{key}={value}")
        return True
    
    def delete_variable(self, config_id: str, key: str) -> bool:
        """删除环境变量"""
        with self.lock:
            env = self.environments.get(config_id)
            if not env:
                return False
            
            if key in env.variables:
                del env.variables[key]
                env.updated_at = time.time()
                self._save_environment(env)
                
                if self.current_environment == config_id:
                    os.environ.pop(key, None)
        
        return True
    
    def add_dependency(self, name: str, version: str, source: str = "pypi",
                      required_version: str = "") -> str:
        """添加依赖项"""
        dep_id = f"dep_{uuid.uuid4().hex[:8]}"
        
        dep = Dependency(
            dep_id=dep_id,
            name=name,
            version=version,
            source=source,
            required_version=required_version
        )
        
        with self.lock:
            self.dependencies[dep_id] = dep
            self._save_dependency(dep)
        
        logger.info(f"添加依赖: {name}=={version}")
        return dep_id
    
    def _save_dependency(self, dep: Dependency):
        """保存依赖到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO dependencies
                (dep_id, name, version, source, status, required_version, 
                 installed_version, last_checked, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dep.dep_id, dep.name, dep.version, dep.source, dep.status.value,
                dep.required_version, dep.installed_version, dep.last_checked,
                json.dumps(dep.metadata)
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存依赖失败: {str(e)}")
    
    def check_dependencies(self) -> List[Dict]:
        """检查依赖状态"""
        results = []
        
        for dep_id, dep in self.dependencies.items():
            dep.last_checked = time.time()
            
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'show', dep.name],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    installed_version = ""
                    for line in lines:
                        if line.startswith('Version:'):
                            installed_version = line.split(':', 1)[1].strip()
                            break
                    
                    dep.installed_version = installed_version
                    
                    if installed_version == dep.version:
                        dep.status = DependencyStatus.INSTALLED
                    else:
                        dep.status = DependencyStatus.OUTDATED
                else:
                    dep.status = DependencyStatus.NOT_INSTALLED
                    dep.installed_version = ""
            
            except Exception as e:
                dep.status = DependencyStatus.CONFLICT
            
            with self.lock:
                self._save_dependency(dep)
            
            results.append({
                "dep_id": dep.dep_id,
                "name": dep.name,
                "required_version": dep.version,
                "installed_version": dep.installed_version,
                "status": dep.status.value
            })
        
        return results
    
    def install_dependency(self, dep_id: str) -> bool:
        """安装依赖"""
        dep = self.dependencies.get(dep_id)
        if not dep:
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', f"{dep.name}=={dep.version}"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                dep.status = DependencyStatus.INSTALLED
                dep.installed_version = dep.version
                self._save_dependency(dep)
                logger.info(f"安装成功: {dep.name}=={dep.version}")
                return True
            else:
                logger.error(f"安装失败: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"安装异常: {str(e)}")
            return False
    
    def list_dependencies(self) -> List[Dict]:
        """列出所有依赖"""
        with self.lock:
            return [{
                "dep_id": dep.dep_id,
                "name": dep.name,
                "required_version": dep.version,
                "installed_version": dep.installed_version,
                "source": dep.source,
                "status": dep.status.value,
                "last_checked": dep.last_checked
            } for dep in self.dependencies.values()]
    
    def backup_environment(self, config_id: str) -> str:
        """备份环境配置"""
        env = self.environments.get(config_id)
        if not env:
            raise ValueError(f"环境配置不存在: {config_id}")
        
        backup_id = f"backup_{uuid.uuid4().hex[:8]}"
        
        backup_data = json.dumps({
            "config_id": env.config_id,
            "name": env.name,
            "env_type": env.env_type.value,
            "description": env.description,
            "variables": env.variables,
            "status": env.status.value,
            "created_at": env.created_at,
            "created_by": env.created_by
        }, ensure_ascii=False)
        
        checksum = hashlib.md5(backup_data.encode()).hexdigest()
        
        backup = ConfigBackup(
            backup_id=backup_id,
            config_id=config_id,
            backup_data=backup_data,
            checksum=checksum
        )
        
        with self.lock:
            self.backups[backup_id] = backup
            self._save_backup(backup)
        
        logger.info(f"备份环境配置: {config_id} -> {backup_id}")
        return backup_id
    
    def _save_backup(self, backup: ConfigBackup):
        """保存备份到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO config_backups
                (backup_id, config_id, backup_data, checksum, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                backup.backup_id, backup.config_id, backup.backup_data,
                backup.checksum, backup.created_at, backup.created_by
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存备份失败: {str(e)}")
    
    def restore_backup(self, backup_id: str) -> bool:
        """恢复配置备份"""
        backup = self.backups.get(backup_id)
        if not backup:
            return False
        
        try:
            data = json.loads(backup.backup_data)
            
            env = EnvironmentConfig(
                config_id=data['config_id'],
                name=data['name'],
                env_type=EnvironmentType(data['env_type']),
                description=data.get('description', ''),
                variables=data['variables'],
                status=ConfigStatus(data['status']),
                created_at=data['created_at'],
                created_by=data.get('created_by', 'system')
            )
            
            with self.lock:
                self.environments[env.config_id] = env
                self._save_environment(env)
            
            logger.info(f"恢复配置备份: {backup_id} -> {env.config_id}")
            return True
        
        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            return False
    
    def list_backups(self, config_id: str = None) -> List[Dict]:
        """列出备份"""
        with self.lock:
            result = []
            for backup_id, backup in self.backups.items():
                if config_id and backup.config_id != config_id:
                    continue
                
                result.append({
                    "backup_id": backup.backup_id,
                    "config_id": backup.config_id,
                    "checksum": backup.checksum,
                    "created_at": backup.created_at,
                    "created_by": backup.created_by
                })
            
            return sorted(result, key=lambda x: x['created_at'], reverse=True)
    
    def collect_metrics(self) -> Dict[str, float]:
        """收集系统指标"""
        metrics = {}
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics['cpu_usage'] = cpu_percent
            
            memory = psutil.virtual_memory()
            metrics['memory_usage'] = memory.percent
            metrics['memory_available'] = memory.available / (1024**3)
            
            disk = psutil.disk_usage('/')
            metrics['disk_usage'] = disk.percent
            
            metrics['load_average'] = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
            
            network = psutil.net_io_counters()
            metrics['network_bytes_sent'] = network.bytes_sent
            metrics['network_bytes_recv'] = network.bytes_recv
            
            self._record_metrics(metrics)
        
        except Exception as e:
            logger.error(f"收集指标失败: {str(e)}")
        
        return metrics
    
    def _record_metrics(self, metrics: Dict):
        """记录指标"""
        timestamp = time.time()
        
        with self.lock:
            for metric_type, value in metrics.items():
                metric = SystemMetric(
                    metric_id=f"metric_{uuid.uuid4().hex[:8]}",
                    metric_type=metric_type,
                    value=value,
                    unit=self._get_metric_unit(metric_type)
                )
                
                self.metrics_history.append(metric)
                
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute('''
                        INSERT INTO system_metrics
                        (metric_id, metric_type, value, unit, timestamp, tags)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        metric.metric_id, metric.metric_type, metric.value,
                        metric.unit, metric.timestamp, json.dumps(metric.tags)
                    ))
                    self.db_conn.commit()
                except Exception as e:
                    logger.error(f"保存指标失败: {str(e)}")
                
                if len(self.metrics_history) > self.metric_buffer_size:
                    self.metrics_history.pop(0)
    
    def _get_metric_unit(self, metric_type: str) -> str:
        """获取指标单位"""
        units = {
            'cpu_usage': '%',
            'memory_usage': '%',
            'disk_usage': '%',
            'load_average': '',
            'memory_available': 'GB',
            'network_bytes_sent': 'bytes',
            'network_bytes_recv': 'bytes'
        }
        return units.get(metric_type, '')
    
    def get_metrics_history(self, metric_type: str = None, limit: int = 100) -> List[Dict]:
        """获取指标历史"""
        with self.lock:
            metrics = self.metrics_history[-limit:]
            
            if metric_type:
                metrics = [m for m in metrics if m.metric_type == metric_type]
            
            return [{
                "metric_type": m.metric_type,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp
            } for m in metrics]
    
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT info_key, info_value FROM system_info')
        
        info = {}
        for row in cursor.fetchall():
            info[row[0]] = row[1]
        
        return info
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            total_envs = len(self.environments)
            active_envs = sum(1 for e in self.environments.values() if e.status == ConfigStatus.ACTIVE)
            
            total_deps = len(self.dependencies)
            installed_deps = sum(1 for d in self.dependencies.values() if d.status == DependencyStatus.INSTALLED)
            
            total_backups = len(self.backups)
            
            current_metrics = {}
            if self.metrics_history:
                latest_metrics = self.metrics_history[-1]
                current_metrics[latest_metrics.metric_type] = latest_metrics.value
            
            return {
                "total_environments": total_envs,
                "active_environments": active_envs,
                "total_dependencies": total_deps,
                "installed_dependencies": installed_deps,
                "total_backups": total_backups,
                "metrics_count": len(self.metrics_history),
                "current_metrics": current_metrics,
                "system_info": self.get_system_info()
            }
    
    def _start_metrics_collector(self):
        """启动指标收集线程"""
        self.metrics_collector = threading.Thread(
            target=self._metrics_collector_loop,
            name="metrics_collector",
            daemon=True
        )
        self.metrics_collector.start()
    
    def _metrics_collector_loop(self):
        """指标收集循环"""
        while True:
            try:
                self.collect_metrics()
                time.sleep(30)
            except Exception as e:
                logger.error(f"指标收集错误: {str(e)}")
                time.sleep(60)
    
    def _start_health_monitor(self):
        """启动健康监控线程"""
        self.health_monitor = threading.Thread(
            target=self._health_monitor_loop,
            name="health_monitor",
            daemon=True
        )
        self.health_monitor.start()
    
    def _health_monitor_loop(self):
        """健康监控循环"""
        while True:
            try:
                self._check_health()
                time.sleep(60)
            except Exception as e:
                logger.error(f"健康监控错误: {str(e)}")
                time.sleep(60)
    
    def _check_health(self):
        """检查系统健康状态"""
        if not self.metrics_history:
            return
        
        latest = self.metrics_history[-1]
        
        if latest.metric_type == 'cpu_usage' and latest.value > 90:
            logger.warning(f"CPU使用率过高: {latest.value}%")
        
        if latest.metric_type == 'memory_usage' and latest.value > 90:
            logger.warning(f"内存使用率过高: {latest.value}%")
    
    def export_config(self, config_id: str, output_file: str) -> bool:
        """导出配置"""
        env = self.environments.get(config_id)
        if not env:
            return False
        
        data = {
            "version": "2.0",
            "exported_at": time.time(),
            "environment": {
                "config_id": env.config_id,
                "name": env.name,
                "env_type": env.env_type.value,
                "description": env.description,
                "variables": env.variables
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"导出配置: {config_id} -> {output_file}")
            return True
        
        except Exception as e:
            logger.error(f"导出配置失败: {str(e)}")
            return False
    
    def import_config(self, input_file: str) -> str:
        """导入配置"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            env_data = data['environment']
            
            env = EnvironmentConfig(
                config_id=env_data['config_id'],
                name=env_data['name'],
                env_type=EnvironmentType(env_data['env_type']),
                description=env_data.get('description', ''),
                variables=env_data['variables']
            )
            
            with self.lock:
                self.environments[env.config_id] = env
                self._save_environment(env)
            
            logger.info(f"导入配置: {input_file} -> {env.config_id}")
            return env.config_id
        
        except Exception as e:
            logger.error(f"导入配置失败: {str(e)}")
            raise


def test_environment_manager():
    """测试环境管理系统"""
    print("系统环境管理系统 V2.0 测试")
    print("=" * 60)
    
    em = EnvironmentManager()
    
    print("列出环境配置:")
    envs = em.list_environments()
    for env in envs:
        print(f"  {env['name']}: {env['env_type']} ({env['status']})")
    
    print("\n创建新环境:")
    new_env_id = em.create_environment(
        name="自定义环境",
        env_type=EnvironmentType.DEVELOPMENT,
        description="自定义开发环境",
        variables={"CUSTOM_VAR": "test", "API_KEY": "xxx"}
    )
    print(f"  创建环境: {new_env_id}")
    
    print("\n设置环境变量:")
    em.set_variable(new_env_id, "NEW_VAR", "new_value")
    print("  变量设置完成")
    
    print("\n获取环境变量:")
    vars = em.get_environment_variables(new_env_id)
    print(f"  变量数量: {len(vars)}")
    
    print("\n添加依赖:")
    dep_id = em.add_dependency("requests", "2.28.0")
    print(f"  添加依赖: {dep_id}")
    
    print("\n检查依赖:")
    deps = em.check_dependencies()
    for dep in deps:
        print(f"  {dep['name']}: {dep['status']}")
    
    print("\n备份环境:")
    backup_id = em.backup_environment("env_dev")
    print(f"  备份: {backup_id}")
    
    print("\n列出备份:")
    backups = em.list_backups()
    for backup in backups[:3]:
        print(f"  {backup['backup_id']}: {backup['created_at']}")
    
    print("\n收集系统指标:")
    metrics = em.collect_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n获取系统信息:")
    sys_info = em.get_system_info()
    for key, value in list(sys_info.items())[:5]:
        print(f"  {key}: {value}")
    
    print("\n导出配置:")
    if em.export_config("env_dev", "env_dev_export.json"):
        print("  导出成功")
    
    print("\n获取统计信息:")
    stats = em.get_stats()
    for key, value in stats.items():
        if not isinstance(value, dict):
            print(f"  {key}: {value}")
    
    print("\n系统环境管理系统 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_environment_manager()