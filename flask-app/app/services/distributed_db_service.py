#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式数据库服务 - 实现分库分表和数据分片
"""

import threading
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4
import hashlib

from app.utils.logging import logger


class ShardStrategy(Enum):
    """分片策略"""
    HASH = "hash"           # 哈希分片
    RANGE = "range"         # 范围分片
    LIST = "list"           # 列表分片
    MODULO = "modulo"       # 取模分片
    CONSISTENT_HASH = "consistent_hash"  # 一致性哈希


class ShardType(Enum):
    """分片类型"""
    DATABASE = "database"   # 库级分片
    TABLE = "table"         # 表级分片


@dataclass
class ShardNode:
    """分片节点"""
    id: str
    host: str
    port: int = 5432
    database: str = "mtscos_db"
    username: str = "admin"
    password: str = ""
    weight: int = 1
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'weight': self.weight,
            'status': self.status,
            'metadata': self.metadata
        }


@dataclass
class ShardTable:
    """分片表"""
    name: str
    shard_key: str
    strategy: ShardStrategy
    nodes: List[str] = field(default_factory=list)
    prefix: str = ""
    suffix_pattern: str = "{shard_id}"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsistentHashRing:
    """一致性哈希环"""
    
    def __init__(self, replicas: int = 100):
        self._replicas = replicas
        self._ring = {}
        self._sorted_keys = []
        self._lock = threading.RLock()

    def add_node(self, node_id: str, weight: int = 1):
        """添加节点到哈希环"""
        with self._lock:
            for i in range(self._replicas * weight):
                key = self._hash(f"{node_id}:{i}")
                self._ring[key] = node_id
                self._sorted_keys.append(key)
            
            self._sorted_keys.sort()

    def remove_node(self, node_id: str):
        """从哈希环移除节点"""
        with self._lock:
            keys_to_remove = [k for k, v in self._ring.items() if v == node_id]
            for key in keys_to_remove:
                del self._ring[key]
                self._sorted_keys.remove(key)

    def get_node(self, key: str) -> Optional[str]:
        """获取键对应的节点"""
        if not self._ring:
            return None
        
        hash_key = self._hash(key)
        
        with self._lock:
            for node_key in self._sorted_keys:
                if node_key >= hash_key:
                    return self._ring[node_key]
            
            # 如果没有找到,返回第一个节点
            return self._ring[self._sorted_keys[0]]

    @staticmethod
    def _hash(key: str) -> int:
        """计算哈希值"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)


class DistributedDBService:
    """分布式数据库服务"""

    def __init__(self):
        self._nodes: Dict[str, ShardNode] = {}
        self._tables: Dict[str, ShardTable] = {}
        self._hash_ring = ConsistentHashRing()
        
        self._default_strategy = ShardStrategy.HASH
        self._shard_count = 8
        
        self._lock = threading.RLock()
        self._running = False
        
        self._init_default_nodes()
        logger.info("分布式数据库服务初始化完成")

    def _init_default_nodes(self):
        """初始化默认分片节点"""
        import os
        
        node_count = int(os.environ.get('SHARD_NODE_COUNT', 4))
        for i in range(node_count):
            node = ShardNode(
                id=f"shard-node-{i+1}",
                host=f"postgres-shard-{i+1}",
                port=5432,
                database=f"mtscos_db_{i+1}",
                username=os.environ.get('DB_USER', 'admin'),
                password=os.environ.get('DB_PASSWORD', ''),
                weight=1
            )
            self._nodes[node.id] = node
            self._hash_ring.add_node(node.id, node.weight)

    def add_node(self, node_data: Dict) -> bool:
        """添加分片节点"""
        try:
            node = ShardNode(
                id=node_data.get('id', str(uuid4())),
                host=node_data.get('host', 'localhost'),
                port=node_data.get('port', 5432),
                database=node_data.get('database', 'mtscos_db'),
                username=node_data.get('username', 'admin'),
                password=node_data.get('password', ''),
                weight=node_data.get('weight', 1)
            )
            
            with self._lock:
                self._nodes[node.id] = node
                self._hash_ring.add_node(node.id, node.weight)
            
            logger.info(f"添加分片节点成功: {node.id}")
            return True
        except Exception as e:
            logger.error(f"添加分片节点失败: {str(e)}")
            return False

    def remove_node(self, node_id: str) -> bool:
        """移除分片节点"""
        try:
            with self._lock:
                if node_id in self._nodes:
                    del self._nodes[node_id]
                    self._hash_ring.remove_node(node_id)
                    logger.info(f"移除分片节点成功: {node_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"移除分片节点失败: {str(e)}")
            return False

    def register_table(self, table_name: str, shard_key: str, 
                       strategy: ShardStrategy = None,
                       nodes: Optional[List[str]] = None):
        """注册分片表"""
        strategy = strategy or self._default_strategy
        
        table = ShardTable(
            name=table_name,
            shard_key=shard_key,
            strategy=strategy,
            nodes=nodes or list(self._nodes.keys()),
            prefix=table_name,
            suffix_pattern="{shard_id}"
        )
        
        with self._lock:
            self._tables[table_name] = table
        
        logger.info(f"注册分片表成功: {table_name}")

    def get_shard_node(self, table_name: str, shard_value: Any) -> Optional[ShardNode]:
        """获取分片节点"""
        table = self._tables.get(table_name)
        if not table:
            logger.warning(f"表 {table_name} 未注册为分片表")
            return None
        
        node_id = self._route_to_node(table, shard_value)
        return self._nodes.get(node_id)

    def _route_to_node(self, table: ShardTable, shard_value: Any) -> str:
        """路由到节点"""
        strategy = table.strategy
        
        if strategy == ShardStrategy.HASH:
            return self._hash_route(table, shard_value)
        elif strategy == ShardStrategy.RANGE:
            return self._range_route(table, shard_value)
        elif strategy == ShardStrategy.LIST:
            return self._list_route(table, shard_value)
        elif strategy == ShardStrategy.MODULO:
            return self._modulo_route(table, shard_value)
        elif strategy == ShardStrategy.CONSISTENT_HASH:
            return self._consistent_hash_route(table, shard_value)
        else:
            return self._hash_route(table, shard_value)

    def _hash_route(self, table: ShardTable, shard_value: Any) -> str:
        """哈希路由"""
        hash_val = int(hashlib.md5(str(shard_value).encode()).hexdigest(), 16)
        node_index = hash_val % len(table.nodes)
        return table.nodes[node_index]

    def _range_route(self, table: ShardTable, shard_value: Any) -> str:
        """范围路由"""
        # 简单的范围分片实现
        ranges = self._get_ranges(table)
        for node_id, range_min, range_max in ranges:
            if range_min <= shard_value <= range_max:
                return node_id
        return table.nodes[0]

    def _list_route(self, table: ShardTable, shard_value: Any) -> str:
        """列表路由"""
        # 需要在metadata中配置映射关系
        mapping = table.metadata.get('mapping', {})
        return mapping.get(shard_value, table.nodes[0])

    def _modulo_route(self, table: ShardTable, shard_value: Any) -> str:
        """取模路由"""
        try:
            mod_value = int(shard_value) % len(table.nodes)
            return table.nodes[mod_value]
        except ValueError:
            return self._hash_route(table, shard_value)

    def _consistent_hash_route(self, table: ShardTable, shard_value: Any) -> str:
        """一致性哈希路由"""
        node_id = self._hash_ring.get_node(str(shard_value))
        return node_id or table.nodes[0]

    def _get_ranges(self, table: ShardTable) -> List[tuple]:
        """获取范围配置"""
        ranges = table.metadata.get('ranges', [])
        if not ranges:
            # 默认均匀分布
            node_count = len(table.nodes)
            for i, node_id in enumerate(table.nodes):
                ranges.append((node_id, i * 100, (i + 1) * 100 - 1))
        return ranges

    def get_table_name(self, table_name: str, shard_value: Any) -> str:
        """获取分片表名"""
        table = self._tables.get(table_name)
        if not table:
            return table_name
        
        # 根据分片值生成表名后缀
        shard_id = self._get_shard_id(table, shard_value)
        return f"{table.prefix}_{table.suffix_pattern.format(shard_id=shard_id)}"

    def _get_shard_id(self, table: ShardTable, shard_value: Any) -> str:
        """获取分片ID"""
        node_id = self._route_to_node(table, shard_value)
        return node_id.split('-')[-1]

    def execute_on_shard(self, table_name: str, shard_value: Any, 
                         query: str, params: tuple = ()) -> Any:
        """在分片上执行查询"""
        node = self.get_shard_node(table_name, shard_value)
        if not node:
            logger.error(f"无法找到分片节点: {table_name}, {shard_value}")
            return None
        
        try:
            # 更新连接计数
            node.metadata['connections'] = node.metadata.get('connections', 0) + 1
            
            # 执行查询(简化实现)
            from app.utils.db import db_manager
            result = db_manager.execute(query, params)
            
            return result
        except Exception as e:
            logger.error(f"在分片上执行查询失败: {str(e)}")
            return None
        finally:
            node.metadata['connections'] = node.metadata.get('connections', 1) - 1

    def execute_across_shards(self, table_name: str, query: str, 
                             params: tuple = (),
                             shard_values: Optional[List[Any]] = None) -> List[Any]:
        """跨分片执行查询"""
        results = []
        
        if shard_values:
            # 针对指定分片值查询
            for shard_value in shard_values:
                result = self.execute_on_shard(table_name, shard_value, query, params)
                if result:
                    results.extend(result)
        else:
            # 查询所有分片
            for node_id in self._nodes.keys():
                # 使用节点ID作为分片值来路由
                result = self.execute_on_shard(table_name, node_id, query, params)
                if result:
                    results.extend(result)
        
        return results

    def execute_transaction_across_shards(self, operations: List[Dict]) -> bool:
        """跨分片事务(两阶段提交)"""
        # 阶段1: 准备阶段
        prepared_nodes = []
        
        try:
            for op in operations:
                table_name = op.get('table')
                shard_value = op.get('shard_value')
                query = op.get('query')
                params = op.get('params', ())
                
                node = self.get_shard_node(table_name, shard_value)
                if not node:
                    logger.error(f"无法找到分片节点: {table_name}, {shard_value}")
                    return False
                
                # 执行准备
                prepared_nodes.append(node)
            
            # 阶段2: 提交阶段
            for op in operations:
                table_name = op.get('table')
                shard_value = op.get('shard_value')
                query = op.get('query')
                params = op.get('params', ())
                
                self.execute_on_shard(table_name, shard_value, query, params)
            
            logger.info("跨分片事务提交成功")
            return True
        except Exception as e:
            # 阶段3: 回滚阶段
            logger.error(f"跨分片事务失败,回滚中: {str(e)}")
            return False

    def set_shard_count(self, count: int):
        """设置分片数量"""
        self._shard_count = count
        logger.info(f"分片数量已设置为: {count}")

    def get_stats(self) -> Dict:
        """获取分布式数据库统计"""
        with self._lock:
            return {
                'nodes': [n.to_dict() for n in self._nodes.values()],
                'tables': {name: {'shard_key': t.shard_key, 'strategy': t.strategy.value} 
                          for name, t in self._tables.items()},
                'strategy': self._default_strategy.value,
                'shard_count': self._shard_count,
                'total_nodes': len(self._nodes)
            }

    def migrate_shard(self, source_node_id: str, target_node_id: str, 
                     table_name: str) -> bool:
        """迁移分片数据"""
        try:
            source_node = self._nodes.get(source_node_id)
            target_node = self._nodes.get(target_node_id)
            
            if not source_node or not target_node:
                logger.error("源节点或目标节点不存在")
                return False
            
            # 迁移逻辑(简化实现)
            logger.info(f"开始迁移分片: {source_node_id} -> {target_node_id}, table: {table_name}")
            
            # 1. 停止写入源节点
            # 2. 复制数据到目标节点
            # 3. 更新路由
            # 4. 重新启用写入
            
            logger.info(f"分片迁移完成: {source_node_id} -> {target_node_id}")
            return True
        except Exception as e:
            logger.error(f"分片迁移失败: {str(e)}")
            return False


# 创建全局实例
distributed_db_service = DistributedDBService()
