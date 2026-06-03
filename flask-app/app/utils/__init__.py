#!/usr/bin/env python3
"""
数据库优化工具包
包含索引管理、快速查询、锁同步和数据库同步等功能
"""

from app.utils.db_index_manager import index_manager, DatabaseIndexManager, IndexRecommendation
from app.utils.fast_query_engine import fast_query, FastQueryEngine, SearchResult
from app.utils.lock_sync_manager import (
    lock_sync_manager, distributed_lock,
    SyncAsyncManager, DistributedLock, ReadWriteLock,
    LockType, synchronized, async_synchronized
)
from app.utils.db_sync_manager import (
    db_sync_manager, DatabaseSyncManager,
    ChangeTracker, ShadowDatabase,
    SyncMode, ChangeType, ChangeLog
)

__version__ = "1.0.0"
__all__ = [
    # 索引管理
    'index_manager',
    'DatabaseIndexManager',
    'IndexRecommendation',
    
    # 快速查询
    'fast_query',
    'FastQueryEngine',
    'SearchResult',
    
    # 锁同步
    'lock_sync_manager',
    'distributed_lock',
    'SyncAsyncManager',
    'DistributedLock',
    'ReadWriteLock',
    'LockType',
    'synchronized',
    'async_synchronized',
    
    # 数据库同步
    'db_sync_manager',
    'DatabaseSyncManager',
    'ChangeTracker',
    'ShadowDatabase',
    'SyncMode',
    'ChangeType',
    'ChangeLog',
]


def init_database_optimization():
    """初始化数据库优化系统"""
    from app.utils.logging import logger
    
    logger.info("=" * 60)
    logger.info("初始化数据库优化系统")
    logger.info("=" * 60)
    
    # 初始化索引管理
    logger.info("[1/4] 初始化索引管理器...")
    try:
        index_manager.create_basic_indexes_for_all_tables()
        logger.info("✓ 基础索引创建完成")
    except Exception as e:
        logger.warning(f"创建基础索引时出错: {str(e)}")
    
    # 启动索引分析
    logger.info("[2/4] 启动索引自动分析...")
    try:
        index_manager.start_background_analysis()
        logger.info("✓ 索引自动分析已启动")
    except Exception as e:
        logger.warning(f"启动索引分析时出错: {str(e)}")
    
    # 启动异步任务队列
    logger.info("[3/4] 启动异步任务队列...")
    try:
        lock_sync_manager.start_async_workers(count=4)
        logger.info("✓ 异步任务队列已启动")
    except Exception as e:
        logger.warning(f"启动异步队列时出错: {str(e)}")
    
    # 启动数据库同步
    logger.info("[4/4] 启动数据库同步...")
    try:
        db_sync_manager.start_auto_sync(interval=60.0)
        logger.info("✓ 数据库同步已启动")
    except Exception as e:
        logger.warning(f"启动数据库同步时出错: {str(e)}")
    
    logger.info("=" * 60)
    logger.info("数据库优化系统初始化完成")
    logger.info("=" * 60)


def shutdown_database_optimization():
    """关闭数据库优化系统"""
    from app.utils.logging import logger
    
    logger.info("正在关闭数据库优化系统...")
    
    # 停止索引分析
    try:
        index_manager.stop_background_analysis()
        logger.info("✓ 索引分析已停止")
    except Exception as e:
        logger.warning(f"停止索引分析时出错: {str(e)}")
    
    # 停止异步队列
    try:
        lock_sync_manager.stop_async_workers()
        logger.info("✓ 异步队列已停止")
    except Exception as e:
        logger.warning(f"停止异步队列时出错: {str(e)}")
    
    # 停止数据库同步
    try:
        db_sync_manager.stop_auto_sync()
        logger.info("✓ 数据库同步已停止")
    except Exception as e:
        logger.warning(f"停止数据库同步时出错: {str(e)}")
    
    logger.info("数据库优化系统已关闭")


def get_system_status() -> dict:
    """获取系统状态"""
    status = {
        'version': __version__,
        'index_manager': {},
        'query_engine': {},
        'lock_manager': {},
        'sync_manager': {}
    }
    
    # 索引管理状态
    try:
        idx_stats = index_manager.get_index_statistics()
        status['index_manager'] = {
            'total_indexes': idx_stats.total_indexes,
            'used_indexes': idx_stats.used_indexes,
            'unused_indexes': idx_stats.unused_indexes,
            'slow_queries_count': len(idx_stats.slow_queries)
        }
    except Exception:
        pass
    
    # 查询引擎状态
    try:
        status['query_engine'] = fast_query.get_query_stats()
    except Exception:
        pass
    
    # 锁管理状态
    try:
        status['lock_manager'] = lock_sync_manager.get_operation_stats()
    except Exception:
        pass
    
    # 同步管理状态
    try:
        sync_status = db_sync_manager.get_status()
        status['sync_manager'] = {
            'mode': sync_status.mode.value,
            'is_running': sync_status.is_running,
            'last_sync': sync_status.last_sync,
            'pending_changes': sync_status.pending_changes,
            'sync_errors': sync_status.sync_errors,
            'avg_sync_time': sync_status.avg_sync_time
        }
    except Exception:
        pass
    
    return status
