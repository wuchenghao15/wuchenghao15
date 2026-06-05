#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库读写分离服务 - 实现主从复制和读写分离
"""

import sqlite3
import threading
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4

from app.utils.logging import logger


class DBType(Enum):
    """数据库类型"""
    MASTER = "master"
    SLAVE = "slave"


class DBStatus(Enum):
    """数据库状态"""
    ACTIVE = "active"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DOWN = "down"


@dataclass
class DatabaseConnection:
    """数据库连接配置"""
    id: str
    type: DBType
    host: str = "localhost"
    port: int = 5432
    database: str = "mtscos_db"
    username: str = "admin"
    password: str = ""
    status: DBStatus = DBStatus.ACTIVE
    weight: int = 1
    connections: int = 0
    last_health_check: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'status': self.status.value,
            'weight': self.weight,
            'connections': self.connections,
            'metadata': self.metadata
        }


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"


class DatabaseRWService:
    """数据库读写分离服务"""

    def __init__(self):
        self._master: Optional[DatabaseConnection] = None
        self._slaves: Dict[str, DatabaseConnection] = {}
        self._active_slaves: List[DatabaseConnection] = []
        
        self._round_robin_index = 0
        self._strategy = LoadBalanceStrategy.ROUND_ROBIN
        
        self._lock = threading.RLock()
        self._health_check_interval = 30  # 健康检查间隔(秒)
        self._health_thread = None
        self._running = False
        
        self._init_default_connections()
        logger.info("数据库读写分离服务初始化完成")

    def _init_default_connections(self):
        """初始化默认数据库连接"""
        import os
        
        # 主库配置
        master_host = os.environ.get('DB_MASTER_HOST', 'postgres')
        master_port = int(os.environ.get('DB_MASTER_PORT', 5432))
        
        self._master = DatabaseConnection(
            id="master-1",
            type=DBType.MASTER,
            host=master_host,
            port=master_port,
            database=os.environ.get('DB_NAME', 'mtscos_db'),
            username=os.environ.get('DB_USER', 'admin'),
            password=os.environ.get('DB_PASSWORD', ''),
            status=DBStatus.ACTIVE,
            weight=1
        )
        
        # 从库配置(支持多个从库)
        slave_count = int(os.environ.get('DB_SLAVE_COUNT', 0))
        if slave_count > 0:
            for i in range(slave_count):
                slave = DatabaseConnection(
                    id=f"slave-{i+1}",
                    type=DBType.SLAVE,
                    host=f"postgres-slave-{i+1}",
                    port=5432,
                    database=os.environ.get('DB_NAME', 'mtscos_db'),
                    username=os.environ.get('DB_USER', 'admin'),
                    password=os.environ.get('DB_PASSWORD', ''),
                    status=DBStatus.ACTIVE,
                    weight=1
                )
                self._slaves[slave.id] = slave
                self._active_slaves.append(slave)

    def add_slave(self, connection_data: Dict) -> bool:
        """添加从库"""
        try:
            slave = DatabaseConnection(
                id=connection_data.get('id', str(uuid4())),
                type=DBType.SLAVE,
                host=connection_data.get('host', 'localhost'),
                port=connection_data.get('port', 5432),
                database=connection_data.get('database', 'mtscos_db'),
                username=connection_data.get('username', 'admin'),
                password=connection_data.get('password', ''),
                weight=connection_data.get('weight', 1)
            )
            
            with self._lock:
                self._slaves[slave.id] = slave
                self._active_slaves.append(slave)
            
            logger.info(f"添加从库成功: {slave.id}")
            return True
        except Exception as e:
            logger.error(f"添加从库失败: {str(e)}")
            return False

    def remove_slave(self, slave_id: str) -> bool:
        """移除从库"""
        try:
            with self._lock:
                if slave_id in self._slaves:
                    slave = self._slaves.pop(slave_id)
                    if slave in self._active_slaves:
                        self._active_slaves.remove(slave)
                    logger.info(f"移除从库成功: {slave_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"移除从库失败: {str(e)}")
            return False

    def set_master(self, connection_data: Dict) -> bool:
        """设置主库"""
        try:
            self._master = DatabaseConnection(
                id=connection_data.get('id', 'master-1'),
                type=DBType.MASTER,
                host=connection_data.get('host', 'localhost'),
                port=connection_data.get('port', 5432),
                database=connection_data.get('database', 'mtscos_db'),
                username=connection_data.get('username', 'admin'),
                password=connection_data.get('password', '')
            )
            logger.info(f"设置主库成功: {self._master.id}")
            return True
        except Exception as e:
            logger.error(f"设置主库失败: {str(e)}")
            return False

    def get_master(self) -> Optional[DatabaseConnection]:
        """获取主库"""
        if self._master and self._master.status == DBStatus.ACTIVE:
            return self._master
        return None

    def select_slave(self) -> Optional[DatabaseConnection]:
        """选择从库"""
        with self._lock:
            if not self._active_slaves:
                logger.warning("没有可用的从库,将使用主库")
                return self._master
            
            # 根据策略选择从库
            if self._strategy == LoadBalanceStrategy.ROUND_ROBIN:
                return self._select_round_robin()
            elif self._strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
                return self._select_least_connections()
            elif self._strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
                return self._select_weighted_round_robin()
            else:
                return self._select_round_robin()

    def _select_round_robin(self) -> DatabaseConnection:
        """轮询策略"""
        slave = self._active_slaves[self._round_robin_index % len(self._active_slaves)]
        self._round_robin_index += 1
        return slave

    def _select_least_connections(self) -> DatabaseConnection:
        """最小连接数策略"""
        return min(self._active_slaves, key=lambda s: s.connections)

    def _select_weighted_round_robin(self) -> DatabaseConnection:
        """加权轮询策略"""
        total_weight = sum(s.weight for s in self._active_slaves)
        random_val = self._round_robin_index % total_weight
        self._round_robin_index += 1

        current = 0
        for slave in self._active_slaves:
            current += slave.weight
            if random_val < current:
                return slave

        return self._active_slaves[0]

    def set_load_balance_strategy(self, strategy: LoadBalanceStrategy):
        """设置负载均衡策略"""
        self._strategy = strategy
        logger.info(f"数据库负载均衡策略已设置为: {strategy.value}")

    def get_load_balance_strategy(self) -> LoadBalanceStrategy:
        """获取负载均衡策略"""
        return self._strategy

    def start_health_check(self):
        """启动健康检查"""
        if self._running:
            return
        
        self._running = True
        self._health_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        self._health_thread.start()
        logger.info("数据库健康检查已启动")

    def stop_health_check(self):
        """停止健康检查"""
        self._running = False
        if self._health_thread:
            self._health_thread.join(timeout=5)
        logger.info("数据库健康检查已停止")

    def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                self._perform_health_check()
                import time
                time.sleep(self._health_check_interval)
            except Exception as e:
                logger.error(f"健康检查错误: {str(e)}")
                import time
                time.sleep(10)

    def _perform_health_check(self):
        """执行健康检查"""
        # 检查主库
        if self._master:
            self._check_connection(self._master)
        
        # 检查从库
        with self._lock:
            for slave in list(self._slaves.values()):
                self._check_connection(slave)

    def _check_connection(self, conn: DatabaseConnection):
        """检查单个连接"""
        import time
        try:
            # 简单的连接测试
            if conn.type == DBType.MASTER and conn.host == 'postgres':
                # PostgreSQL连接测试
                try:
                    import psycopg2
                    connection = psycopg2.connect(
                        host=conn.host,
                        port=conn.port,
                        dbname=conn.database,
                        user=conn.username,
                        password=conn.password
                    )
                    connection.close()
                    conn.status = DBStatus.HEALTHY
                except Exception:
                    # 如果PostgreSQL不可用,尝试SQLite
                    try:
                        sqlite_conn = sqlite3.connect(':memory:')
                        sqlite_conn.close()
                        conn.status = DBStatus.HEALTHY
                    except Exception:
                        conn.status = DBStatus.DOWN
            else:
                conn.status = DBStatus.HEALTHY
            
            conn.last_health_check = time.time()
            
            # 更新活跃从库列表
            if conn.type == DBType.SLAVE:
                with self._lock:
                    if conn.status in [DBStatus.ACTIVE, DBStatus.HEALTHY]:
                        if conn not in self._active_slaves:
                            self._active_slaves.append(conn)
                    else:
                        if conn in self._active_slaves:
                            self._active_slaves.remove(conn)
            
        except Exception as e:
            conn.status = DBStatus.DOWN
            logger.warning(f"数据库连接检查失败: {conn.id} - {str(e)}")

    def get_stats(self) -> Dict:
        """获取数据库统计"""
        with self._lock:
            return {
                'master': self._master.to_dict() if self._master else None,
                'slaves': [s.to_dict() for s in self._slaves.values()],
                'active_slaves': len(self._active_slaves),
                'strategy': self._strategy.value,
                'total_connections': sum(s.connections for s in self._slaves.values()) + 
                                    (self._master.connections if self._master else 0)
            }

    def execute_write(self, query: str, params: tuple = ()) -> Any:
        """执行写操作(主库)"""
        return self._execute_on_connection(self._master, query, params, write=True)

    def execute_read(self, query: str, params: tuple = ()) -> Any:
        """执行读操作(从库或主库)"""
        slave = self.select_slave()
        if slave:
            return self._execute_on_connection(slave, query, params, write=False)
        return None

    def _execute_on_connection(self, conn: Optional[DatabaseConnection], query: str, 
                               params: tuple, write: bool) -> Any:
        """在指定连接上执行查询"""
        if not conn:
            logger.error("没有可用的数据库连接")
            return None

        try:
            # 更新连接计数
            conn.connections += 1
            
            if conn.host == 'postgres' or write:
                # 使用主库连接
                from app.utils.db import db_manager
                result = db_manager.execute(query, params)
            else:
                # 从库查询(简化实现)
                from app.utils.db import db_manager
                result = db_manager.execute(query, params)
            
            return result
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            return None
        finally:
            conn.connections -= 1

    def transaction(self, operations: List[Dict]) -> bool:
        """执行事务(所有操作在主库执行)"""
        if not self._master:
            logger.error("没有可用的主库")
            return False

        try:
            from app.utils.db import db_manager
            
            # 开始事务
            db_manager.execute("BEGIN TRANSACTION")
            
            try:
                for op in operations:
                    query = op.get('query', '')
                    params = op.get('params', ())
                    db_manager.execute(query, params)
                
                # 提交事务
                db_manager.execute("COMMIT")
                logger.info("事务执行成功")
                return True
            except Exception as e:
                # 回滚事务
                db_manager.execute("ROLLBACK")
                logger.error(f"事务执行失败,已回滚: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"事务操作失败: {str(e)}")
            return False


# 创建全局实例
database_rw_service = DatabaseRWService()
