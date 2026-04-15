#!/usr/bin/env python3
"""
双数据库备份功能测试脚本
"""

from app.utils.dual_db import dual_db_manager
from app.utils.logging import logger

if __name__ == "__main__":
    print("=== 双数据库备份功能测试 ===")
    
    # 获取同步状态
    status = dual_db_manager.get_sync_status()
    print(f"同步状态: {status}")
    
    # 执行手动备份
    print("\n执行手动备份...")
    dual_db_manager.backup_now()
    
    # 测试数据恢复
    print("\n测试数据恢复功能...")
    # 这里可以先向主数据库插入一些测试数据，然后同步到备份数据库，再从备份数据库恢复
    
    # 测试获取数据库连接
    print("\n测试获取主数据库连接...")
    primary_db = dual_db_manager.get_primary_db()
    print(f"主数据库类型: {primary_db.db_type}")
    
    print("\n测试获取备份数据库连接...")
    backup_db = dual_db_manager.get_backup_db()
    print(f"备份数据库类型: {backup_db.db_type}")
    
    print("\n=== 测试完成 ===")
