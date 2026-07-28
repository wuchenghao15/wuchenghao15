# -*- coding: utf-8 -*-
"""
AI 智能分散数据库核心管理器
激活现有 DistributedDatabaseManager + 新增 AI 智能层
按 "表类型 + 功能模块 + 数据热度" 三维分散数据
"""

import os
import sys
import json
import logging
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engines.db_schema_registry import (
    TABLE_REGISTRY, get_table_info, get_all_shard_dbs,
    get_tables_by_shard, get_migration_targets,
    TableCategory, DataHeat
)

logger = logging.getLogger(__name__)


class AIDistributedDatabaseManager:
    """AI 智能分散数据库管理器

    功能：
    1. 管理 6 个物理分片库（core/logs/exam_behavior/ai_engine/knowledge/archive）
    2. 维护 7 张元数据表（ai_distributed_db.db）记录路由、迁移进度、热度、员工状态、决策日志
    3. 提供统一的查询路由接口（route_query）
    4. 初始化迁移队列（6 张膨胀日志表）
    5. 管理分片连接（check_same_thread=False, timeout=30）
    """

    def __init__(self):
        self.app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_dir = os.path.join(self.app_root, 'databases')
        self.meta_db_path = os.path.join(self.app_root, 'ai_distributed_db.db')

        # 确保目录存在
        os.makedirs(self.db_dir, exist_ok=True)

        # 元数据库连接（独立于 app.db，避免 889MB 主库阻塞）
        self.meta_conn = sqlite3.connect(
            self.meta_db_path, check_same_thread=False, timeout=30.0
        )
        self.meta_conn.row_factory = sqlite3.Row

        # 分片库连接缓存 {db_name: sqlite3.Connection}
        self.shard_connections: Dict[str, sqlite3.Connection] = {}
        self._conn_lock = threading.Lock()

        # 初始化
        self._init_meta_tables()
        self._init_shards()
        self._init_migration_queue()

        # 员工引用（延迟注入）
        self.employees: Dict[str, Any] = {}

        logger.info("AIDistributedDatabaseManager 初始化完成")

    # ============================================================
    # 元数据表初始化（7 张表）
    # ============================================================
    def _init_meta_tables(self):
        """初始化 7 张元数据表到 ai_distributed_db.db"""
        c = self.meta_conn.cursor()

        # 1. 分片库注册表
        c.execute('''
            CREATE TABLE IF NOT EXISTS shard_registry (
                db_name TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                table_count INTEGER DEFAULT 0,
                size_bytes INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. 表路由表
        c.execute('''
            CREATE TABLE IF NOT EXISTS table_routing (
                table_name TEXT PRIMARY KEY,
                shard_db TEXT NOT NULL,
                category TEXT NOT NULL,
                module TEXT NOT NULL,
                heat TEXT NOT NULL,
                migrated INTEGER DEFAULT 0,
                row_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. 迁移进度表
        c.execute('''
            CREATE TABLE IF NOT EXISTS migration_progress (
                table_name TEXT PRIMARY KEY,
                source_db TEXT NOT NULL,
                target_db TEXT NOT NULL,
                batch_size INTEGER DEFAULT 1000,
                total_rows INTEGER DEFAULT 0,
                completed_rows INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                md5_check TEXT,
                last_batch_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 4. 查询统计表
        c.execute('''
            CREATE TABLE IF NOT EXISTS query_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shard_db TEXT NOT NULL,
                table_name TEXT,
                query_type TEXT,
                query_count INTEGER DEFAULT 0,
                avg_time_ms REAL DEFAULT 0,
                last_access TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 5. 热度指标表
        c.execute('''
            CREATE TABLE IF NOT EXISTS heat_metrics (
                table_name TEXT PRIMARY KEY,
                read_count INTEGER DEFAULT 0,
                write_count INTEGER DEFAULT 0,
                last_access TEXT,
                heat_level TEXT DEFAULT 'warm',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 6. 员工状态表
        c.execute('''
            CREATE TABLE IF NOT EXISTS employee_status (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'idle',
                last_task TEXT,
                task_count INTEGER DEFAULT 0,
                last_error TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 7. AI 决策日志表
        c.execute('''
            CREATE TABLE IF NOT EXISTS decision_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_type TEXT NOT NULL,
                employee_id TEXT,
                details TEXT,
                action_taken TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.meta_conn.commit()
        logger.info("元数据表初始化完成（7张表）")

    # ============================================================
    # 分片库初始化
    # ============================================================
    def _init_shards(self):
        """初始化 6 个分片库并注册到元数据表"""
        c = self.meta_conn.cursor()

        # 从注册表获取所有分片库及其分类
        shard_categories = {}
        for table_name, info in TABLE_REGISTRY.items():
            shard_db = info['shard_db']
            category = info['category'].value
            if shard_db not in shard_categories:
                shard_categories[shard_db] = category

        # 注册分片库
        for shard_db, category in shard_categories.items():
            # 创建物理库文件（连接即创建）
            shard_path = os.path.join(self.db_dir, shard_db)
            conn = self._get_or_create_shard_connection(shard_db)

            # 计算该分片库的表数量
            tables = get_tables_by_shard(shard_db)

            # 注册到元数据表
            c.execute('''
                INSERT OR REPLACE INTO shard_registry
                (db_name, category, table_count, size_bytes, status, updated_at)
                VALUES (?, ?, ?, ?, 'active', ?)
            ''', (shard_db, category, len(tables),
                  os.path.getsize(shard_path) if os.path.exists(shard_path) else 0,
                  datetime.now().isoformat()))

            # 注册表路由
            for table_name in tables:
                info = get_table_info(table_name)
                if info:
                    c.execute('''
                        INSERT OR REPLACE INTO table_routing
                        (table_name, shard_db, category, module, heat, migrated)
                        VALUES (?, ?, ?, ?, ?, 0)
                    ''', (table_name, shard_db, info['category'],
                          info['module'], info['heat']))

        self.meta_conn.commit()
        logger.info(f"分片库初始化完成: {list(shard_categories.keys())}")

    def _init_migration_queue(self):
        """初始化迁移队列：向 migration_progress 插入 6 张膨胀日志表的待迁移记录"""
        c = self.meta_conn.cursor()
        app_db_path = os.path.join(self.app_root, 'app.db')

        for table_name in get_migration_targets():
            info = get_table_info(table_name)
            if not info:
                continue

            # 检查是否已存在迁移记录
            c.execute('SELECT table_name FROM migration_progress WHERE table_name = ?',
                      (table_name,))
            if c.fetchone():
                continue

            # 尝试获取源表行数（容错处理，app.db 可能被锁）
            # 用 MAX(rowid) 替代 COUNT(*)：O(log n) 走 rowid 索引，毫秒级返回；
            # MAX(rowid) 是行数上界估计（有删除时偏大），足够用于进度展示，迁移时以实际批次为准。
            row_count = -1  # 默认未知，避免 COUNT(*) 全表扫描卡死
            try:
                probe = sqlite3.connect(app_db_path, timeout=3.0)
                probe.row_factory = sqlite3.Row
                pc = probe.cursor()
                pc.execute(f'SELECT MAX(rowid) as cnt FROM {table_name}')
                row = pc.fetchone()
                if row and row['cnt'] is not None:
                    row_count = row['cnt']
                else:
                    row_count = 0  # 空表
                probe.close()
            except Exception as e:
                logger.warning(f"获取 {table_name} 行数失败（跳过）: {e}")
                row_count = -1  # 未知行数

            c.execute('''
                INSERT OR REPLACE INTO migration_progress
                (table_name, source_db, target_db, batch_size, total_rows,
                 completed_rows, status, created_at)
                VALUES (?, ?, ?, 1000, ?, 0, 'pending', ?)
            ''', (table_name, app_db_path, info['shard_db'],
                  row_count, datetime.now().isoformat()))

        self.meta_conn.commit()
        logger.info(f"迁移队列初始化完成: {len(get_migration_targets())} 张表待迁移")

    # ============================================================
    # 分片连接管理
    # ============================================================
    def _get_or_create_shard_connection(self, db_name: str) -> sqlite3.Connection:
        """获取或创建分片库连接（带线程安全缓存）"""
        with self._conn_lock:
            if db_name not in self.shard_connections:
                shard_path = os.path.join(self.db_dir, db_name)
                conn = sqlite3.connect(
                    shard_path, check_same_thread=False, timeout=30.0
                )
                conn.row_factory = sqlite3.Row
                self.shard_connections[db_name] = conn
                logger.info(f"分片库连接已创建: {db_name}")
            return self.shard_connections[db_name]

    def get_shard_connection(self, db_name: str) -> sqlite3.Connection:
        """公开接口：获取分片库连接"""
        return self._get_or_create_shard_connection(db_name)

    @contextmanager
    def shard_cursor(self, db_name: str):
        """获取分片库游标的上下文管理器"""
        conn = self._get_or_create_shard_connection(db_name)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @contextmanager
    def meta_cursor(self):
        """获取元数据库游标的上下文管理器"""
        cursor = self.meta_conn.cursor()
        try:
            yield cursor
            self.meta_conn.commit()
        except Exception:
            self.meta_conn.rollback()
            raise
        finally:
            cursor.close()

    # ============================================================
    # 查询路由
    # ============================================================
    def route_query(self, table_name: str, operation: str = 'select') -> Dict[str, Any]:
        """路由查询到正确的分片库

        Args:
            table_name: 表名
            operation: 操作类型（select/insert/update/delete）

        Returns:
            路由信息字典 {shard_db, category, module, heat, migrated, connection}
        """
        info = get_table_info(table_name)
        if not info:
            return {
                'shard_db': 'app.db',
                'category': 'unknown',
                'module': 'unknown',
                'heat': 'unknown',
                'migrated': 0,
                'connection': None,
                'message': f'表 {table_name} 未在注册表中，路由到默认主库'
            }

        # 更新热度指标
        self.update_heat(table_name, operation)

        # 更新查询统计
        self._record_query_stats(info['shard_db'], table_name, operation)

        connection = self._get_or_create_shard_connection(info['shard_db'])

        # 检查迁移状态
        with self.meta_cursor() as c:
            c.execute('SELECT migrated FROM table_routing WHERE table_name = ?',
                      (table_name,))
            row = c.fetchone()
            migrated = row['migrated'] if row else 0

        return {
            'shard_db': info['shard_db'],
            'category': info['category'],
            'module': info['module'],
            'heat': info['heat'],
            'migrated': migrated,
            'connection': connection,
            'message': f'路由到 {info["shard_db"]} ({"已迁移" if migrated else "未迁移"})'
        }

    def update_heat(self, table_name: str, access_type: str):
        """更新表的热度指标"""
        with self.meta_cursor() as c:
            c.execute('SELECT * FROM heat_metrics WHERE table_name = ?', (table_name,))
            row = c.fetchone()

            now = datetime.now().isoformat()
            if row:
                read_count = row['read_count'] + (1 if access_type == 'select' else 0)
                write_count = row['write_count'] + (1 if access_type != 'select' else 0)
                # 热度自动评级
                total = read_count + write_count
                if total > 1000:
                    heat = 'hot'
                elif total > 100:
                    heat = 'warm'
                else:
                    heat = 'cold'
                c.execute('''
                    UPDATE heat_metrics SET read_count=?, write_count=?, last_access=?, heat_level=?, updated_at=?
                    WHERE table_name=?
                ''', (read_count, write_count, now, heat, now, table_name))
            else:
                c.execute('''
                    INSERT INTO heat_metrics (table_name, read_count, write_count, last_access, heat_level, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (table_name,
                      1 if access_type == 'select' else 0,
                      1 if access_type != 'select' else 0,
                      now, 'warm', now))

    def _record_query_stats(self, shard_db: str, table_name: str, operation: str):
        """记录查询统计"""
        with self.meta_cursor() as c:
            c.execute('''
                SELECT id, query_count FROM query_stats
                WHERE shard_db=? AND table_name=? AND query_type=?
                ORDER BY id DESC LIMIT 1
            ''', (shard_db, table_name, operation))
            row = c.fetchone()
            now = datetime.now().isoformat()
            if row:
                c.execute('UPDATE query_stats SET query_count=?, last_access=? WHERE id=?',
                          (row['query_count'] + 1, now, row['id']))
            else:
                c.execute('''
                    INSERT INTO query_stats (shard_db, table_name, query_type, query_count, last_access)
                    VALUES (?, ?, ?, 1, ?)
                ''', (shard_db, table_name, operation, now))

    # ============================================================
    # 员工管理
    # ============================================================
    def register_employee(self, employee):
        """注册数据库管理员工"""
        employee.set_manager(self)
        self.employees[employee.employee_id] = employee

        # 写入元数据表
        with self.meta_cursor() as c:
            c.execute('''
                INSERT OR REPLACE INTO employee_status
                (employee_id, name, role, status, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee.employee_id, employee.name, employee.role,
                  employee.status, datetime.now().isoformat()))
        logger.info(f"数据库员工已注册: {employee.name} ({employee.employee_id})")

    def update_employee_status(self, employee_id: str, status: str,
                               last_task: str = None, task_count: int = None,
                               error: str = None):
        """更新员工状态"""
        with self.meta_cursor() as c:
            updates = ['status = ?', 'updated_at = ?']
            params = [status, datetime.now().isoformat()]
            if last_task is not None:
                updates.append('last_task = ?')
                params.append(last_task)
            if task_count is not None:
                updates.append('task_count = ?')
                params.append(task_count)
            if error is not None:
                updates.append('last_error = ?')
                params.append(error)
            params.append(employee_id)
            c.execute(f'UPDATE employee_status SET {", ".join(updates)} WHERE employee_id = ?',
                      params)

    # ============================================================
    # 决策日志
    # ============================================================
    def log_decision(self, decision_type: str, details: str,
                     employee_id: str = None, action_taken: str = None):
        """记录 AI 决策日志"""
        with self.meta_cursor() as c:
            c.execute('''
                INSERT INTO decision_log (decision_type, employee_id, details, action_taken)
                VALUES (?, ?, ?, ?)
            ''', (decision_type, employee_id, details, action_taken))

    # ============================================================
    # 迁移进度管理
    # ============================================================
    def get_migration_status(self, table_name: str = None) -> List[Dict[str, Any]]:
        """获取迁移进度"""
        with self.meta_cursor() as c:
            if table_name:
                c.execute('SELECT * FROM migration_progress WHERE table_name = ?', (table_name,))
            else:
                c.execute('SELECT * FROM migration_progress ORDER BY created_at')
            rows = c.fetchall()
        return [dict(row) for row in rows]

    def update_migration_progress(self, table_name: str, completed_rows: int,
                                   status: str, md5_check: str = None,
                                   error: str = None):
        """更新迁移进度"""
        with self.meta_cursor() as c:
            updates = ['completed_rows = ?', 'status = ?', 'last_batch_at = ?']
            params = [completed_rows, status, datetime.now().isoformat()]
            if md5_check:
                updates.append('md5_check = ?')
                params.append(md5_check)
            if error:
                updates.append('error_message = ?')
                params.append(error)
            if status == 'completed':
                updates.append('completed_at = ?')
                params.append(datetime.now().isoformat())
            params.append(table_name)
            c.execute(f'UPDATE migration_progress SET {", ".join(updates)} WHERE table_name = ?',
                      params)

        # 更新表路由的 migrated 标记
        if status == 'completed':
            with self.meta_cursor() as c:
                c.execute('UPDATE table_routing SET migrated = 1 WHERE table_name = ?',
                          (table_name,))

    # ============================================================
    # 健康检查
    # ============================================================
    def check_shard_health(self) -> List[Dict[str, Any]]:
        """检查所有分片库健康状态"""
        results = []
        for db_name in get_all_shard_dbs():
            shard_path = os.path.join(self.db_dir, db_name)
            health = {
                'db_name': db_name,
                'exists': os.path.exists(shard_path),
                'size_bytes': os.path.getsize(shard_path) if os.path.exists(shard_path) else 0,
                'size_mb': round(os.path.getsize(shard_path) / 1024 / 1024, 2) if os.path.exists(shard_path) else 0,
                'table_count': len(get_tables_by_shard(db_name)),
                'status': 'healthy',
                'issues': []
            }

            # 检查连接
            try:
                conn = self._get_or_create_shard_connection(db_name)
                c = conn.cursor()
                c.execute('PRAGMA journal_mode')
                journal = c.fetchone()
                health['journal_mode'] = journal[0] if journal else 'unknown'
                c.close()

                # 容量预警（>500MB）
                if health['size_mb'] > 500:
                    health['status'] = 'warning'
                    health['issues'].append(f"库大小 {health['size_mb']}MB 超过 500MB 预警线")
            except Exception as e:
                health['status'] = 'error'
                health['issues'].append(f"连接失败: {e}")

            results.append(health)
        return results

    # ============================================================
    # 状态汇总
    # ============================================================
    def get_status(self) -> Dict[str, Any]:
        """获取系统整体状态"""
        with self.meta_cursor() as c:
            c.execute('SELECT COUNT(*) as cnt FROM shard_registry')
            shard_count = c.fetchone()['cnt']

            c.execute('SELECT COUNT(*) as cnt FROM table_routing')
            table_count = c.fetchone()['cnt']

            c.execute('SELECT COUNT(*) as cnt FROM table_routing WHERE migrated = 1')
            migrated_count = c.fetchone()['cnt']

            c.execute("SELECT COUNT(*) as cnt FROM migration_progress WHERE status = 'pending'")
            pending_migrations = c.fetchone()['cnt']

            c.execute("SELECT COUNT(*) as cnt FROM migration_progress WHERE status = 'completed'")
            completed_migrations = c.fetchone()['cnt']

            c.execute('SELECT COUNT(*) as cnt FROM employee_status')
            employee_count = c.fetchone()['cnt']

            c.execute('SELECT COUNT(*) as cnt FROM decision_log')
            decision_count = c.fetchone()['cnt']

        return {
            'initialized': True,
            'meta_db_path': self.meta_db_path,
            'db_dir': self.db_dir,
            'shard_count': shard_count,
            'table_count': table_count,
            'migrated_tables': migrated_count,
            'pending_migrations': pending_migrations,
            'completed_migrations': completed_migrations,
            'employee_count': employee_count,
            'decision_count': decision_count,
            'timestamp': datetime.now().isoformat()
        }

    def get_shards_info(self) -> List[Dict[str, Any]]:
        """获取所有分片库信息"""
        with self.meta_cursor() as c:
            c.execute('SELECT * FROM shard_registry ORDER BY category')
            rows = c.fetchall()
        return [dict(row) for row in rows]

    def get_routing_table(self) -> List[Dict[str, Any]]:
        """获取表路由表"""
        with self.meta_cursor() as c:
            c.execute('SELECT * FROM table_routing ORDER BY shard_db, table_name')
            rows = c.fetchall()
        return [dict(row) for row in rows]

    def get_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的 AI 决策日志"""
        with self.meta_cursor() as c:
            c.execute('SELECT * FROM decision_log ORDER BY id DESC LIMIT ?', (limit,))
            rows = c.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        """关闭所有连接"""
        for conn in self.shard_connections.values():
            try:
                conn.close()
            except Exception:
                pass
        try:
            self.meta_conn.close()
        except Exception:
            pass
        logger.info("AIDistributedDatabaseManager 所有连接已关闭")


# ============================================================
# 延迟单例（避免导入时阻塞）
# ============================================================
_ai_distributed_db_manager_instance: Optional[AIDistributedDatabaseManager] = None
_instance_lock = threading.Lock()


def get_ai_distributed_db_manager() -> AIDistributedDatabaseManager:
    """获取 AIDistributedDatabaseManager 单例（延迟加载）"""
    global _ai_distributed_db_manager_instance
    if _ai_distributed_db_manager_instance is None:
        with _instance_lock:
            if _ai_distributed_db_manager_instance is None:
                _ai_distributed_db_manager_instance = AIDistributedDatabaseManager()
    return _ai_distributed_db_manager_instance


def reset_ai_distributed_db_manager():
    """重置单例（用于测试）"""
    global _ai_distributed_db_manager_instance
    if _ai_distributed_db_manager_instance is not None:
        _ai_distributed_db_manager_instance.close()
        _ai_distributed_db_manager_instance = None
