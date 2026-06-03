# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""缓存工具模块"""

import time
import functools
import logging
from typing import Any, Dict, Optional, Callable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cache')

class CacheManager:
    """缓存管理器"""

    def __init__(self, default_ttl: int = 3600):
        """初始化缓存管理器

        Args:
            default_ttl: 默认缓存过期时间(秒)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """生成缓存键

        Args:
            func: 函数对象
            args: 函数参数
            kwargs: 函数关键字参数

        Returns:
            缓存键
        """
        key_parts = [
            func.__module__,
            func.__name__,
            str(args),
            str(sorted(kwargs.items()))
        ]
        return "::".join(key_parts)

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值,如果不存在或过期返回None
        """
        if key not in self.cache:
            return None

        item = self.cache[key]
        if time.time() > item['expiry']:
            self.misses += 1
            return None

        self.hits += 1
        return item['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)
        """
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expiry': time.time() + ttl
        }

    def delete(self, key: str) -> None:
        """删除缓存

        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def size(self) -> int:
        """获取缓存大小

        Returns:
            缓存项数量
        """
        return len(self.cache)

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            统计信息
        """
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total': self.hits + self.misses,
            'size': self.size()
        }

    def decorator(self, ttl: Optional[int] = None):
        """缓存装饰器

        Args:
            ttl: 过期时间(秒)

        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                key = self._generate_key(func, args, kwargs)
                cached_value = self.get(key)

                if cached_value is not None:
                    logger.debug(f"缓存命中: {key}")
                    return cached_value

                logger.debug(f"缓存未命中: {key}")
                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                return result

            return wrapper

        return decorator

cache_manager = CacheManager()

def get_cache_manager():
    """获取缓存管理器实例"""
    return cache_manager