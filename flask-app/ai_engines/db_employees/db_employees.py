# -*- coding: utf-8 -*-
"""
4 个数据库管理 AI 员工实现
- DBShardDecisionAI  数据分散决策AI
- DBMigrationAI      数据迁移执行AI
- DBQueryRouterAI    查询路由优化AI
- DBHealthMonitorAI  数据库健康监控AI
"""

import os
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_db_employee import BaseDBEmployee
from ai_engines.db_schema_registry import (
    TABLE_REGISTRY, get_table_info, get_all_shard_dbs,
    get_tables_by_shard, get_migration_targets,
    TableCategory, DataHeat
)

logger = logging.getLogger(__name__)


class DBShardDecisionAI(BaseDBEmployee):
    """数据分散决策AI

    职责：分析表数据量/增长率，决策是否需要重新分片，生成热度降级/升级建议
    """

    def __init__(self):
        super().__init__(
            employee_id='db_shard_decision_001',
            name='数据分散决策AI',
            role='db_shard_decision',
            skills=['数据量分析', '增长率计算', '分片决策', '热度评级', '负载感知'],
            interval=3600  # 每小时分析一次
        )

    def _do_work(self):
        """执行分散决策分析"""
        if not self._manager:
            logger.warning("数据分散决策AI: 管理器未注入，跳过")
            return

        decisions = []
        app_db_path = os.path.join(self._manager.app_root, 'app.db')

        # 1. 分析 app.db 中注册表的数据量
        for table_name in get_migration_targets():
            try:
                probe = sqlite3.connect(app_db_path, timeout=3.0)
                probe.row_factory = sqlite3.Row
                c = probe.cursor()
                # 用 MAX(rowid) 替代 COUNT(*)，避免每小时守护线程触发全表扫描卡死
                c.execute(f'SELECT MAX(rowid) as cnt FROM {table_name}')
                row = c.fetchone()
                count = (row['cnt'] if row and row['cnt'] is not None else 0)
                probe.close()

                info = get_table_info(table_name)
                if info and count > 10000:
                    decisions.append({
                        'table': table_name,
                        'row_count': count,
                        'shard_db': info['shard_db'],
                        'recommendation': f"建议迁移到 {info['shard_db']}（当前 {count} 行）"
                    })
            except Exception as e:
                logger.debug(f"分析 {table_name} 失败: {e}")

        # 2. 检查各分片库容量
        for db_name in get_all_shard_dbs():
            shard_path = os.path.join(self._manager.db_dir, db_name)
            if os.path.exists(shard_path):
                size_mb = os.path.getsize(shard_path) / 1024 / 1024
                if size_mb > 500:
                    decisions.append({
                        'shard_db': db_name,
                        'size_mb': round(size_mb, 2),
                        'recommendation': f"分片库 {db_name} 大小 {round(size_mb, 2)}MB，建议归档冷数据"
                    })

        # 3. 热度降级/升级
        self._adjust_heat_levels()

        # 记录决策日志
        if decisions:
            for d in decisions:
                self._manager.log_decision(
                    decision_type='shard_decision',
                    details=str(d),
                    employee_id=self.employee_id,
                    action_taken='recorded'
                )
            logger.info(f"数据分散决策AI: 生成 {len(decisions)} 条决策建议")

        # 更新员工状态
        self._manager.update_employee_status(
            self.employee_id, 'running',
            last_task=f"分析了 {len(get_migration_targets())} 张表，生成 {len(decisions)} 条建议",
            task_count=None
        )

    def _adjust_heat_levels(self):
        """根据访问频率自动调整热度等级"""
        with self._manager.meta_cursor() as c:
            c.execute('SELECT table_name, read_count, write_count, heat_level FROM heat_metrics')
            rows = c.fetchall()
            for row in rows:
                total = row['read_count'] + row['write_count']
                if total > 1000:
                    new_heat = 'hot'
                elif total > 100:
                    new_heat = 'warm'
                else:
                    new_heat = 'cold'
                if row['heat_level'] != new_heat:
                    c.execute('UPDATE heat_metrics SET heat_level = ? WHERE table_name = ?',
                              (new_heat, row['table_name']))
                    self._manager.log_decision(
                        decision_type='heat_adjustment',
                        details=f"表 {row['table_name']} 热度 {row['heat_level']} → {new_heat} (总访问 {total})",
                        employee_id=self.employee_id
                    )


class DBMigrationAI(BaseDBEmployee):
    """数据迁移执行AI

    职责：执行分批迁移任务，MD5一致性校验，断点续传
    """

    def __init__(self):
        super().__init__(
            employee_id='db_migration_001',
            name='数据迁移执行AI',
            role='db_migration',
            skills=['分批迁移', 'MD5校验', '断点续传', '一致性验证', '事务管理'],
            interval=60  # 每分钟检查迁移队列
        )
        self._migration_framework = None

    def _do_work(self):
        """执行迁移任务"""
        if not self._manager:
            logger.warning("数据迁移执行AI: 管理器未注入，跳过")
            return

        # 延迟加载迁移框架
        if self._migration_framework is None:
            try:
                from .migration_framework import MigrationFramework
                self._migration_framework = MigrationFramework(self._manager)
            except Exception as e:
                logger.error(f"数据迁移执行AI: 加载迁移框架失败: {e}")
                return

        # 获取待迁移任务
        pending = self._manager.get_migration_status()
        pending_tasks = [t for t in pending if t['status'] in ('pending', 'running')]

        if not pending_tasks:
            logger.debug("数据迁移执行AI: 无待迁移任务")
            return

        # 执行一个批次的迁移
        for task in pending_tasks:
            table_name = task['table_name']
            try:
                result = self._migration_framework.migrate_next_batch(table_name)
                logger.info(f"数据迁移执行AI: {table_name} 迁移进度 {result.get('completed_rows', 0)}/{result.get('total_rows', 0)}")

                if result.get('status') == 'completed':
                    self._manager.log_decision(
                        decision_type='migration_completed',
                        details=f"表 {table_name} 迁移完成 (MD5: {result.get('md5_check', 'N/A')})",
                        employee_id=self.employee_id,
                        action_taken=f"迁移 {result.get('completed_rows', 0)} 行到 {result.get('target_db')}"
                    )
                    # 一次只处理一个完成的迁移
                    break
            except Exception as e:
                logger.error(f"数据迁移执行AI: 迁移 {table_name} 失败: {e}")
                self._manager.update_migration_progress(
                    table_name, task.get('completed_rows', 0), 'error', error=str(e)
                )
                self._manager.update_employee_status(
                    self.employee_id, 'error', error=str(e)
                )
                break

        self._manager.update_employee_status(
            self.employee_id, 'running',
            last_task=f"处理了 {len(pending_tasks)} 个待迁移任务"
        )


class DBQueryRouterAI(BaseDBEmployee):
    """查询路由优化AI

    职责：分析查询统计，优化路由策略，识别热点查询
    """

    def __init__(self):
        super().__init__(
            employee_id='db_query_router_001',
            name='查询路由优化AI',
            role='db_query_router',
            skills=['查询路由', '热点识别', '缓存优化', '负载均衡', '跨分片优化'],
            interval=300  # 每5分钟优化一次
        )

    def _do_work(self):
        """执行路由优化分析"""
        if not self._manager:
            logger.warning("查询路由优化AI: 管理器未注入，跳过")
            return

        # 1. 分析查询统计
        with self._manager.meta_cursor() as c:
            c.execute('''
                SELECT shard_db, table_name, query_type, query_count, last_access
                FROM query_stats
                ORDER BY query_count DESC
                LIMIT 20
            ''')
            hot_queries = c.fetchall()

        # 2. 识别热点查询（query_count > 100）
        hot_count = 0
        for q in hot_queries:
            if q['query_count'] > 100:
                hot_count += 1
                self._manager.log_decision(
                    decision_type='hot_query_identified',
                    details=f"热点查询: {q['shard_db']}.{q['table_name']} ({q['query_type']}) 访问 {q['query_count']} 次",
                    employee_id=self.employee_id,
                    action_taken='建议预缓存'
                )

        # 3. 分析各分片库负载分布
        with self._manager.meta_cursor() as c:
            c.execute('''
                SELECT shard_db, SUM(query_count) as total_queries
                FROM query_stats
                GROUP BY shard_db
                ORDER BY total_queries DESC
            ''')
            load_distribution = c.fetchall()

        # 4. 负载均衡建议（如果某分片库负载过高）
        for load in load_distribution:
            if load['total_queries'] and load['total_queries'] > 5000:
                self._manager.log_decision(
                    decision_type='load_imbalance',
                    details=f"分片库 {load['shard_db']} 查询负载 {load['total_queries']}，建议负载均衡",
                    employee_id=self.employee_id,
                    action_taken='建议拆分或增加副本'
                )

        logger.info(f"查询路由优化AI: 识别 {hot_count} 个热点查询，分析 {len(load_distribution)} 个分片库负载")

        self._manager.update_employee_status(
            self.employee_id, 'running',
            last_task=f"识别 {hot_count} 个热点查询，分析 {len(load_distribution)} 个分片库"
        )


class DBHealthMonitorAI(BaseDBEmployee):
    """数据库健康监控AI

    职责：监控各分片库容量/锁状态/性能，触发清理和归档
    """

    def __init__(self):
        super().__init__(
            employee_id='db_health_monitor_001',
            name='数据库健康监控AI',
            role='db_health_monitor',
            skills=['健康检查', '容量监控', '锁状态检测', '性能分析', '自动归档'],
            interval=120  # 每2分钟检查一次
        )

    def _do_work(self):
        """执行健康检查"""
        if not self._manager:
            logger.warning("数据库健康监控AI: 管理器未注入，跳过")
            return

        health_results = self._manager.check_shard_health()
        warnings = []
        errors = []

        for health in health_results:
            if health['status'] == 'warning':
                warnings.append(health)
            elif health['status'] == 'error':
                errors.append(health)

            # 容量预警日志
            if health.get('size_mb', 0) > 500:
                self._manager.log_decision(
                    decision_type='capacity_warning',
                    details=f"分片库 {health['db_name']} 容量 {health['size_mb']}MB 超过预警线",
                    employee_id=self.employee_id,
                    action_taken='建议归档冷数据到 archive.db'
                )

        # 检查 app.db 锁状态
        app_db_path = os.path.join(self._manager.app_root, 'app.db')
        journal_path = app_db_path + '-journal'
        if os.path.exists(journal_path):
            self._manager.log_decision(
                decision_type='lock_detected',
                details=f"app.db 存在 journal 文件，可能有未提交事务",
                employee_id=self.employee_id,
                action_taken='记录预警'
            )

        if errors:
            logger.error(f"数据库健康监控AI: {len(errors)} 个分片库异常, {len(warnings)} 个预警")
        elif warnings:
            logger.warning(f"数据库健康监控AI: {len(warnings)} 个分片库预警")
        else:
            logger.debug(f"数据库健康监控AI: 全部 {len(health_results)} 个分片库健康")

        self._manager.update_employee_status(
            self.employee_id, 'running',
            last_task=f"检查 {len(health_results)} 个分片库 ({len(warnings)} 预警, {len(errors)} 异常)"
        )


# ============================================================
# 员工管理
# ============================================================
_db_employees: Dict[str, BaseDBEmployee] = {}
_employees_lock = None


def init_db_employees(manager=None) -> List[Dict[str, Any]]:
    """初始化 4 个数据库管理 AI 员工

    Args:
        manager: AIDistributedDatabaseManager 实例（可选，延迟注入）

    Returns:
        员工状态列表
    """
    global _db_employees

    employees = [
        DBShardDecisionAI(),
        DBMigrationAI(),
        DBQueryRouterAI(),
        DBHealthMonitorAI(),
    ]

    _db_employees = {emp.employee_id: emp for emp in employees}

    # 注入管理器并注册
    if manager is not None:
        for emp in employees:
            manager.register_employee(emp)

    # 注册到全局 AI 员工管理器
    try:
        from ai_engines.ai_employees import ai_employee_manager
        for emp in employees:
            if emp.employee_id not in ai_employee_manager.employees:
                ai_employee_manager.add_employee(emp)
    except Exception as e:
        logger.warning(f"注册到全局AI员工管理器失败: {e}")

    logger.info(f"数据库管理AI员工初始化完成: {len(employees)} 名员工")
    return [emp.get_status() for emp in employees]


def get_db_employees() -> Dict[str, BaseDBEmployee]:
    """获取所有数据库管理员工"""
    return _db_employees


def get_db_employee(employee_id: str) -> Optional[BaseDBEmployee]:
    """获取指定数据库管理员工"""
    return _db_employees.get(employee_id)


def start_all_db_employees() -> Dict[str, bool]:
    """启动所有数据库管理员工的守护线程"""
    results = {}
    for emp_id, emp in _db_employees.items():
        results[emp_id] = emp.start()
    return results


def stop_all_db_employees() -> Dict[str, bool]:
    """停止所有数据库管理员工的守护线程"""
    results = {}
    for emp_id, emp in _db_employees.items():
        results[emp_id] = emp.stop()
    return results


def get_db_employees_status() -> List[Dict[str, Any]]:
    """获取所有数据库管理员工状态"""
    return [emp.get_status() for emp in _db_employees.values()]
