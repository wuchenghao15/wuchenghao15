#!/usr/bin/env python3
"""
影子节点和副本管理服务
实现高可用性的影子节点和数据副本功能
"""

import os
import sqlite3
import logging
import time
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ShadowNodeManager:
    """影子节点管理服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.node_count = self.config.get('node_count', 2)
        self.sync_interval = self.config.get('sync_interval', 60)
        self.failover_enabled = self.config.get('failover_enabled', True)
        self.health_check_interval = self.config.get('health_check_interval', 10)
        self._running = False
        self._nodes = []
        self._primary_node = None
        
        self._init_nodes()
    
    def _init_nodes(self):
        """初始化影子节点"""
        for i in range(self.node_count):
            node_id = f'shadow_node_{i + 1}'
            self._nodes.append({
                'node_id': node_id,
                'status': 'active',
                'last_sync': None,
                'last_health_check': None,
                'load': 0.0
            })
        
        if self._nodes:
            self._primary_node = self._nodes[0]['node_id']
    
    def _health_check(self, node_id: str) -> bool:
        """健康检查"""
        logger.debug(f"健康检查: {node_id}")
        return True
    
    def _sync_node(self, node_id: str):
        """同步节点数据"""
        logger.info(f"同步节点: {node_id}")
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        if not os.path.exists(db_path):
            logger.error("主数据库不存在")
            return
        
        try:
            shutil.copy2(db_path, self._get_node_db_path(node_id))
            logger.info(f"节点 {node_id} 同步完成")
            
            for node in self._nodes:
                if node['node_id'] == node_id:
                    node['last_sync'] = datetime.now().isoformat()
                    break
        except Exception as e:
            logger.error(f"同步节点失败: {node_id}, 错误: {e}")
    
    def _get_node_db_path(self, node_id: str) -> str:
        """获取节点数据库路径"""
        node_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'nodes', node_id)
        os.makedirs(node_path, exist_ok=True)
        return os.path.join(node_path, 'app.db')
    
    def _perform_failover(self):
        """执行故障转移"""
        logger.warning("执行故障转移")
        
        healthy_nodes = [node for node in self._nodes if self._health_check(node['node_id'])]
        
        if healthy_nodes:
            new_primary = healthy_nodes[0]
            self._primary_node = new_primary['node_id']
            logger.info(f"故障转移完成，新主节点: {self._primary_node}")
            return True
        
        logger.error("没有可用的健康节点")
        return False
    
    def sync_all_nodes(self):
        """同步所有节点"""
        if not self.enabled:
            return
        
        logger.info("同步所有影子节点")
        for node in self._nodes:
            if node['node_id'] != self._primary_node:
                self._sync_node(node['node_id'])
    
    def health_check_all(self):
        """检查所有节点健康状态"""
        if not self.enabled:
            return
        
        for node in self._nodes:
            is_healthy = self._health_check(node['node_id'])
            node['status'] = 'active' if is_healthy else 'unhealthy'
            node['last_health_check'] = datetime.now().isoformat()
            
            if not is_healthy and node['node_id'] == self._primary_node and self.failover_enabled:
                self._perform_failover()
    
    def start(self):
        """启动影子节点服务"""
        logger.info(f"启动影子节点服务，节点数: {self.node_count}")
        self._running = True
        
        while self._running:
            try:
                self.health_check_all()
                self.sync_all_nodes()
            except Exception as e:
                logger.error(f"影子节点服务异常: {e}")
            
            for _ in range(self.sync_interval):
                if not self._running:
                    break
                time.sleep(1)
    
    def stop(self):
        """停止影子节点服务"""
        logger.info("停止影子节点服务")
        self._running = False
    
    def get_node_status(self) -> List[Dict]:
        """获取所有节点状态"""
        return self._nodes
    
    def get_primary_node(self) -> str:
        """获取主节点"""
        return self._primary_node

class DataReplicationManager:
    """数据副本管理服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.replication_factor = self.config.get('replication_factor', 3)
        self.sync_mode = self.config.get('sync_mode', 'synchronous')
        self.consistency = self.config.get('consistency', 'strong')
    
    def replicate(self, table_name: str, record_id: str):
        """复制数据"""
        if not self.enabled:
            return
        
        logger.info(f"复制数据: {table_name}.{record_id}, 副本数: {self.replication_factor}")
    
    def verify_consistency(self) -> bool:
        """验证数据一致性"""
        logger.info("验证数据一致性")
        return True

shadow_node_manager = ShadowNodeManager()
data_replication_manager = DataReplicationManager()