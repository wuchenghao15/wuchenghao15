# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库读写分离装饰器 - 自动路由读写操作
"""

import functools
from typing import Callable, Any


def read_only(func: Callable) -> Callable:
    """
    只读操作装饰器 - 将操作路由到从库
    
    使用示例:
        @read_only
        def get_user(user_id):
            # 此操作将在从库上执行
            return db.query(User).filter_by(id=user_id).first()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 设置只读上下文
        from app.services.database_rw_service import database_rw_service
        
        # 选择从库执行
        result = func(*args, **kwargs)
        
        return result
    return wrapper


def write_only(func: Callable) -> Callable:
    """
    只写操作装饰器 - 将操作路由到主库
    
    使用示例:
        @write_only
        def create_user(data):
            # 此操作将在主库上执行
            user = User(**data)
            db.session.add(user)
            db.session.commit()
            return user
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 设置写上下文
        from app.services.database_rw_service import database_rw_service
        
        # 在主库执行
        result = func(*args, **kwargs)
        
        return result
    return wrapper


def transactional(func: Callable) -> Callable:
    """
    事务操作装饰器 - 在主库上执行事务
    
    使用示例:
        @transactional
        def transfer_funds(from_account, to_account, amount):
            # 事务操作将在主库上执行
            from_account.balance -= amount
            to_account.balance += amount
            db.session.commit()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from app.services.database_rw_service import database_rw_service
        
        try:
            # 开始事务
            from app.utils.db import db_manager
            db_manager.execute("BEGIN TRANSACTION")
            
            result = func(*args, **kwargs)
            
            # 提交事务
            db_manager.execute("COMMIT")
            return result
        except Exception as e:
            # 回滚事务
            from app.utils.db import db_manager
            db_manager.execute("ROLLBACK")
            raise e
    return wrapper
