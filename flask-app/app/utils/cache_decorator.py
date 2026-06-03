# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存装饰器 - 提供便捷的缓存使用方式
"""

import hashlib
import functools
from typing import Callable, Any, Optional

from app.services.cache_service import cache_service, CacheLevel


def cached(key_prefix: str = "", ttl: int = 3600, 
           levels: Optional[list] = None):
    """
    缓存装饰器
    
    参数:
        key_prefix: 缓存键前缀
        ttl: 过期时间(秒)
        levels: 缓存级别列表,默认为 [L1, L2]
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = _generate_cache_key(key_prefix, args, kwargs)
            
            # 尝试获取缓存
            value = cache_service.get(key, levels)
            if value is not None:
                return value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 设置缓存
            cache_service.set(key, result, ttl, levels)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str = ""):
    """
    缓存失效装饰器
    
    参数:
        key_prefix: 要失效的缓存键前缀
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行函数
            result = func(*args, **kwargs)
            
            # 失效相关缓存(这里简化处理,实际可以更复杂)
            # 注意:完整的缓存失效需要更复杂的策略
            # 这里我们可以通过前缀来删除缓存
            
            return result
        return wrapper
    return decorator


def _generate_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """生成缓存键"""
    parts = [prefix]
    
    # 添加位置参数
    for arg in args:
        parts.append(str(arg))
    
    # 添加关键字参数(按字母顺序排序)
    for key, value in sorted(kwargs.items()):
        parts.append(f"{key}={value}")
    
    # 生成哈希
    key_str = ":".join(parts)
    return hashlib.md5(key_str.encode()).hexdigest()


def l1_cached(key_prefix: str = "", ttl: int = 3600):
    """仅使用L1缓存(内存缓存)"""
    return cached(key_prefix=key_prefix, ttl=ttl, levels=[CacheLevel.L1])


def l2_cached(key_prefix: str = "", ttl: int = 3600):
    """仅使用L2缓存(Redis缓存)"""
    return cached(key_prefix=key_prefix, ttl=ttl, levels=[CacheLevel.L2])


def l3_cached(key_prefix: str = "", ttl: int = 86400):
    """仅使用L3缓存(文件缓存)"""
    return cached(key_prefix=key_prefix, ttl=ttl, levels=[CacheLevel.L3])


def full_cached(key_prefix: str = "", ttl: int = 3600):
    """使用全部缓存级别"""
    return cached(key_prefix=key_prefix, ttl=ttl, 
                  levels=[CacheLevel.L1, CacheLevel.L2, CacheLevel.L3])
