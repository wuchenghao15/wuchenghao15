# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库优化系统使用示例
演示如何使用索引管理、快速查询、锁同步和数据库同步功能
"""

import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils import (
    init_database_optimization,
    shutdown_database_optimization,
    get_system_status,
    index_manager,
    fast_query,
    lock_sync_manager,
    db_sync_manager,
    LockType,
    ChangeType,
    SyncMode,
    synchronized
)


def example_index_management():
    """索引管理示例"""
    print("\n" + "=" * 60)
    print("索引管理示例")
    print("=" * 60)
    
    # 获取所有表
    tables = index_manager.get_all_tables()
    print(f"\n数据库中的表: {tables}")
    
    # 为所有表创建基础索引
    print("\n创建基础索引...")
    result = index_manager.create_basic_indexes_for_all_tables()
    for table, indexes in result.items():
        print(f"  表 {table}: 创建了索引 {indexes}")
    
    # 获取索引统计
    print("\n索引统计信息:")
    stats = index_manager.get_index_statistics()
    print(f"  总索引数: {stats.total_indexes}")
    print(f"  已使用索引: {stats.used_indexes}")
    print(f"  未使用索引: {stats.unused_indexes}")
    
    # 获取索引推荐
    print("\n索引推荐:")
    recommendations = index_manager.analyze_query_patterns()
    for rec in recommendations[:5]:
        print(f"  表 {rec.table}: {rec.columns} (分数: {rec.score:.2f}) - {rec.reason}")


def example_fast_query():
    """快速查询示例"""
    print("\n" + "=" * 60)
    print("快速查询示例")
    print("=" * 60)
    
    # 获取所有表
    tables = index_manager.get_all_tables()
    if not tables:
        print("\n数据库中没有表")
        return
    
    test_table = tables[0]
    print(f"\n使用表: {test_table}")
    
    # 多维度查询示例
    print("\n多维度查询:")
    try:
        # 这里需要根据实际表结构调整查询条件
        result = fast_query.multidimensional_query(
            table_name=test_table,
            conditions={},
            order_by=None,
            page=1,
            page_size=10,
            use_cache=True
        )
        print(f"  查询结果数: {result.total}")
        print(f"  返回数据: {len(result.results)} 条")
        print(f"  执行时间: {result.execution_time:.3f}秒")
    except Exception as e:
        print(f"  查询失败: {str(e)}")
    
    # 全文搜索示例
    print("\n全文搜索:")
    try:
        # 注册搜索表(假设表有name或title字段)
        columns = index_manager.get_table_columns(test_table)
        text_columns = [col['name'] for col in columns if 'text' in col['type'].lower() or 'char' in col['type'].lower()]
        
        if text_columns:
            fast_query.register_search_table(test_table, 'id', text_columns[:3])
            
            # 执行搜索
            result = fast_query.fulltext_search(
                table_name=test_table,
                query="test",
                columns=text_columns[:1] if text_columns else None,
                page=1,
                page_size=10
            )
            print(f"  搜索结果数: {result.total}")
            print(f"  返回数据: {len(result.results)} 条")
            print(f"  执行时间: {result.execution_time:.3f}秒")
        else:
            print(f"  表 {test_table} 没有适合搜索的文本字段")
    except Exception as e:
        print(f"  搜索失败: {str(e)}")
    
    # 查询统计
    print("\n查询统计:")
    stats = fast_query.get_query_stats()
    print(f"  {stats}")


def example_lock_sync():
    """锁同步示例"""
    print("\n" + "=" * 60)
    print("锁同步示例")
    print("=" * 60)
    
    # 使用读写锁
    print("\n读写锁示例:")
    try:
        with lock_sync_manager.read_lock(resource="test_resource", timeout=5.0):
            print("  获取读锁成功 - 可以执行读操作")
            time.sleep(0.1)
        print("  读锁已释放")
        
        with lock_sync_manager.write_lock(resource="test_resource", timeout=5.0):
            print("  获取写锁成功 - 可以执行写操作")
            time.sleep(0.1)
        print("  写锁已释放")
    except Exception as e:
        print(f"  锁操作失败: {str(e)}")
    
    # 使用装饰器
    print("\n同步装饰器示例:")
    @synchronized(resource="decorator_test", lock_type=LockType.WRITE)
    def protected_function():
        print("  在受保护的函数中执行操作")
        time.sleep(0.1)
        return "success"
    
    result = protected_function()
    print(f"  函数执行结果: {result}")
    
    # 异步执行示例
    print("\n异步执行示例:")
    
    def async_task():
        print("  异步任务开始执行")
        time.sleep(0.5)
        print("  异步任务完成")
        return "async_result"
    
    def callback(result):
        print(f"  异步任务回调: {result}")
    
    lock_sync_manager.execute_async(
        async_task,
        resource="async_test",
        lock_type=LockType.READ,
        callback=callback
    )
    
    print("  异步任务已提交,等待完成...")
    time.sleep(1.0)
    
    # 操作统计
    print("\n操作统计:")
    stats = lock_sync_manager.get_operation_stats()
    print(f"  {stats}")


def example_db_sync():
    """数据库同步示例"""
    print("\n" + "=" * 60)
    print("数据库同步示例")
    print("=" * 60)
    
    # 获取同步状态
    print("\n当前同步状态:")
    status = db_sync_manager.get_status()
    print(f"  同步模式: {status.mode.value}")
    print(f"  运行状态: {status.is_running}")
    print(f"  最后同步: {status.last_sync}")
    print(f"  待同步变更: {status.pending_changes}")
    print(f"  同步错误: {status.sync_errors}")
    print(f"  平均同步时间: {status.avg_sync_time:.3f}秒")
    
    # 追踪变更示例
    print("\n变更追踪示例:")
    tables = index_manager.get_all_tables()
    if tables:
        test_table = tables[0]
        change_id = db_sync_manager.track_change(
            table_name=test_table,
            primary_key="1",
            change_type=ChangeType.UPDATE,
            old_data={"field": "old_value"},
            new_data={"field": "new_value"}
        )
        print(f"  记录变更ID: {change_id}")
        
        # 获取待同步变更
        pending = db_sync_manager.change_tracker.get_pending_changes(limit=10)
        print(f"  待同步变更数: {len(pending)}")
    
    # 影子数据库示例
    print("\n影子数据库示例:")
    try:
        # 启用影子数据库
        db_sync_manager.enable_shadow_database()
        print("  影子数据库已启用")
        
        # 手动同步
        print("  执行手动同步...")
        success = db_sync_manager.sync_now()
        print(f"  同步结果: {'成功' if success else '失败'}")
        
        # 检查一致性
        print("  检查数据一致性...")
        consistency = db_sync_manager.check_data_consistency()
        print(f"  一致性报告: {consistency}")
        
    except Exception as e:
        print(f"  影子数据库操作失败: {str(e)}")


def example_system_status():
    """系统状态示例"""
    print("\n" + "=" * 60)
    print("系统状态示例")
    print("=" * 60)
    
    status = get_system_status()
    print(f"\n版本: {status['version']}")
    print(f"\n索引管理器状态: {status['index_manager']}")
    print(f"\n查询引擎状态: {status['query_engine']}")
    print(f"\n锁管理器状态: {status['lock_manager']}")
    print(f"\n同步管理器状态: {status['sync_manager']}")


def main():
    """主函数"""
    print("=" * 60)
    print("MTSCOS AI 数据库优化系统 - 使用示例")
    print("=" * 60)
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 初始化系统
        print("\n正在初始化数据库优化系统...")
        init_database_optimization()
        
        # 运行示例
        example_index_management()
        example_fast_query()
        example_lock_sync()
        example_db_sync()
        example_system_status()
        
        print("\n" + "=" * 60)
        print("示例运行完成!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断,正在关闭...")
    except Exception as e:
        print(f"\n\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭系统
        print("\n正在关闭数据库优化系统...")
        shutdown_database_optimization()
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
