# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import logging
import threading
import subprocess
import random
from typing import Dict, List, Optional
from app.config import Config
from app.utils.logging import logger


class SandboxManager:
    """沙盒管理器: 用于管理AI实例的沙盒环境"""

    def __init__(self):
        self.sandboxes = {}
        self.sandbox_lock = threading.RLock()
        self.sandbox_config = self._load_sandbox_config()
        self._apply_system_rules_config()
        self.running_sandboxes = 0
        self._init_dynamic_config()
        self.max_sandboxes = self.sandbox_config.get('initial_max_sandboxes', 10)
        self._init_db_connection()

    def _init_dynamic_config(self):
        """初始化动态沙盒配置"""
        self.dynamic_config = {
            'enabled': True,
            'min_sandboxes': 5,
            'max_sandboxes': 50,
            'resource_threshold': {
                'cpu': 80.0,
                'memory': 80.0,
                'disk': 80.0
            },
            'adjustment_step': 5,
            'check_interval': 60,
            'last_adjustment': time.time()
        }

        if 'dynamic_sandbox' in self.sandbox_config:
            self.dynamic_config.update(self.sandbox_config['dynamic_sandbox'])

    def _load_sandbox_config(self):
        """加载沙盒配置"""
        default_config = {
            'isolation_level': 'medium',
            'initial_max_sandboxes': 50,
            'resource_limits': {
                'cpu': 50,
                'memory': 1024,
                'disk': 10240,
                'processes': 10
            },
            'file_system_access': True,
            'clipboard_access': False,
            'gpu_access': False,
            'dynamic_sandbox': {
                'min_sandboxes': 5,
                'max_sandboxes': 50,
                'adjustment_step': 5
            }
        }

        try:
            config_path = os.path.join('config', 'sandbox.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            logger.warning(f"加载沙盒配置失败: {str(e)}, 使用默认配置")

        return default_config

    def save_sandbox_config(self, config):
        """保存沙盒配置"""
        try:
            config_path = os.path.join('config', 'sandbox.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("沙盒配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存沙盒配置失败: {str(e)}")
            return False

    def _apply_system_rules_config(self):
        """从system_rules表读取沙盒配置并应用"""
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT rule_code, rule_value FROM system_rules WHERE rule_code LIKE 'SANDBOX_%'")
                rules = cursor.fetchall()
                
                for rule_code, rule_value in rules:
                    if rule_code == 'SANDBOX_ENABLED':
                        self.sandbox_config['enabled'] = bool(int(rule_value))
                    elif rule_code == 'SANDBOX_ISOLATION_LEVEL':
                        self.sandbox_config['isolation_level'] = rule_value
                    elif rule_code == 'SANDBOX_MAX_INSTANCES':
                        self.sandbox_config['initial_max_sandboxes'] = int(rule_value)
                    elif rule_code == 'SANDBOX_MIN_INSTANCES':
                        self.sandbox_config['min_sandboxes'] = int(rule_value)
                    elif rule_code == 'SANDBOX_RESOURCE_LIMIT_CPU':
                        self.sandbox_config['resource_limits']['cpu'] = int(rule_value)
                    elif rule_code == 'SANDBOX_RESOURCE_LIMIT_MEMORY':
                        self.sandbox_config['resource_limits']['memory'] = int(rule_value)
                    elif rule_code == 'SANDBOX_RESOURCE_LIMIT_DISK':
                        self.sandbox_config['resource_limits']['disk'] = int(rule_value)
                    elif rule_code == 'SANDBOX_RESOURCE_LIMIT_PROCESSES':
                        self.sandbox_config['resource_limits']['processes'] = int(rule_value)
                    elif rule_code == 'SANDBOX_FILE_SYSTEM_ACCESS':
                        self.sandbox_config['file_system_access'] = bool(int(rule_value))
                    elif rule_code == 'SANDBOX_CLIPBOARD_ACCESS':
                        self.sandbox_config['clipboard_access'] = bool(int(rule_value))
                    elif rule_code == 'SANDBOX_GPU_ACCESS':
                        self.sandbox_config['gpu_access'] = bool(int(rule_value))
                    elif rule_code == 'SANDBOX_NETWORK_ISOLATION_ENABLED':
                        self.sandbox_config['network_isolation'] = bool(int(rule_value))
            
            logger.info("沙盒配置已从system_rules表更新")
        except Exception as e:
            logger.warning(f"从system_rules读取沙盒配置失败: {str(e)}")

    def _init_db_connection(self):
        """初始化数据库连接"""
        self._db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

    def _get_db_connection(self):
        """获取数据库连接"""
        import sqlite3
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _record_sandbox_to_db(self, sandbox):
        """将沙盒记录写入数据库"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO sandbox_instances 
                    (sandbox_id, instance_id, status, isolation_level, 
                     resource_limits, file_system_access, network_isolation,
                     clipboard_access, gpu_access, created_at, prewarmed, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sandbox['sandbox_id'],
                    sandbox['instance_id'],
                    sandbox['status'],
                    self.sandbox_config.get('isolation_level', 'medium'),
                    json.dumps(self.sandbox_config.get('resource_limits', {})),
                    1 if self.sandbox_config.get('file_system_access', True) else 0,
                    1 if self.sandbox_config.get('network_isolation', True) else 0,
                    1 if self.sandbox_config.get('clipboard_access', False) else 0,
                    1 if self.sandbox_config.get('gpu_access', False) else 0,
                    time.strftime('%Y-%m-%d %H:%M:%S'),
                    1 if sandbox.get('prewarmed', False) else 0,
                    json.dumps(sandbox.get('config', {}))
                ))
                conn.commit()
            logger.info(f"沙盒记录已写入数据库: {sandbox['sandbox_id']}")
        except Exception as e:
            logger.error(f"写入沙盒记录失败: {str(e)}")

    def _update_sandbox_status(self, sandbox_id, status):
        """更新沙盒状态"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sandbox_instances SET status = ?, updated_at = ? WHERE sandbox_id = ?
                ''', (status, time.strftime('%Y-%m-%d %H:%M:%S'), sandbox_id))
                conn.commit()
        except Exception as e:
            logger.error(f"更新沙盒状态失败: {str(e)}")

    def _remove_sandbox_from_db(self, sandbox_id):
        """从数据库删除沙盒记录"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sandbox_instances WHERE sandbox_id = ?', (sandbox_id,))
                conn.commit()
            logger.info(f"沙盒记录已从数据库删除: {sandbox_id}")
        except Exception as e:
            logger.error(f"删除沙盒记录失败: {str(e)}")

    def _adjust_sandbox_limit(self):
        """根据资源使用情况动态调整沙盒上限"""
        if not self.dynamic_config['enabled']:
            return

        current_time = time.time()
        if current_time - self.dynamic_config['last_adjustment'] < self.dynamic_config['check_interval']:
            return

        system_resources = self._get_system_resource_usage()

        new_max = self.max_sandboxes

        if all(usage < threshold for usage, threshold in zip(
                system_resources.values(),
                self.dynamic_config['resource_threshold'].values())):
            new_max = min(
                self.max_sandboxes + self.dynamic_config['adjustment_step'],
                self.dynamic_config['max_sandboxes']
            )
        elif any(usage > threshold for usage, threshold in zip(
                system_resources.values(),
                self.dynamic_config['resource_threshold'].values())):
            new_max = max(
                self.max_sandboxes - self.dynamic_config['adjustment_step'],
                self.dynamic_config['min_sandboxes']
            )

        if new_max != self.max_sandboxes:
            old_max = self.max_sandboxes
            self.max_sandboxes = new_max
            self.dynamic_config['last_adjustment'] = current_time
            logger.info(f"沙盒上限已调整: {old_max} -> {new_max}")

    def _get_system_resource_usage(self):
        """获取系统资源使用情况"""
        try:
            import psutil
            return {
                'cpu': psutil.cpu_percent(),
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent
            }
        except Exception as e:
            logger.warning(f"获取系统资源使用情况失败: {str(e)}")
            return {
                'cpu': 50.0,
                'memory': 50.0,
                'disk': 50.0
            }

    def get_prewarmed_sandbox(self):
        """获取一个预温的沙盒

        Returns:
            Optional[Dict]: 预温的沙盒配置,或None如果没有可用的预温沙盒
        """
        with self.sandbox_lock:
            for instance_id, sandbox in self.sandboxes.items():
                if sandbox.get('prewarmed') and sandbox['status'] == 'running':
                    sandbox['prewarmed'] = False
                    logger.info(f"使用预温沙盒: {sandbox['sandbox_id']}")
                    return sandbox
            return None

    def create_sandbox(self, instance_id: str, config: Dict = None) -> Dict:
        """创建沙盒"""
        with self.sandbox_lock:
            if len(self.sandboxes) >= self.max_sandboxes:
                logger.warning("已达到沙盒上限")
                return None

            sandbox_id = f"sandbox_{instance_id}_{int(time.time())}"
            sandbox = {
                'sandbox_id': sandbox_id,
                'instance_id': instance_id,
                'status': 'created',
                'created_at': time.time(),
                'config': config or {},
                'prewarmed': False
            }
            self.sandboxes[instance_id] = sandbox
            self.running_sandboxes += 1
            
            self._record_sandbox_to_db(sandbox)
            
            logger.info(f"沙盒创建成功: {sandbox_id}")
            return sandbox

    def destroy_sandbox(self, instance_id: str) -> bool:
        """销毁沙盒"""
        with self.sandbox_lock:
            if instance_id in self.sandboxes:
                sandbox = self.sandboxes[instance_id]
                sandbox_id = sandbox.get('sandbox_id')
                self._remove_sandbox_from_db(sandbox_id)
                
                del self.sandboxes[instance_id]
                self.running_sandboxes -= 1
                logger.info(f"沙盒销毁成功: {instance_id}")
                return True
            return False

    def get_sandbox(self, instance_id: str) -> Optional[Dict]:
        """获取沙盒信息"""
        return self.sandboxes.get(instance_id)

    def get_all_sandboxes(self) -> List[Dict]:
        """获取所有沙盒"""
        return list(self.sandboxes.values())


sandbox_manager = SandboxManager()
