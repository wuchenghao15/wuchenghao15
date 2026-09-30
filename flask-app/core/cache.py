#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Cache Module - Enhanced caching system with multiple backends
优化版本: 连接池、重试机制、超时配置、错误日志、健康检查、批量操作、键前缀管理
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, Union, List, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict

# 配置日志
logger = logging.getLogger(__name__)

class LocalCache:
    """Local in-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
    
    def _get_key(self, key: str) -> str:
        """Generate a consistent key"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._get_key(key)
        
        if cache_key in self.cache:
            value, expire_time = self.cache[cache_key]
            if datetime.now() < expire_time:
                self.cache.move_to_end(cache_key)
                self.stats["hits"] += 1
                return json.loads(value)
            else:
                del self.cache[cache_key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        cache_key = self._get_key(key)
        
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            self.stats["evictions"] += 1
        
        expire_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
        self.cache[cache_key] = (json.dumps(value), expire_time)
        self.stats["sets"] += 1
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        cache_key = self._get_key(key)
        if cache_key in self.cache:
            del self.cache[cache_key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        self.stats = {k: 0 for k in self.stats}
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return self.stats.copy()
    
    def has(self, key: str) -> bool:
        """Check if key exists"""
        cache_key = self._get_key(key)
        if cache_key in self.cache:
            _, expire_time = self.cache[cache_key]
            if datetime.now() < expire_time:
                return True
            del self.cache[cache_key]
        return False

class RedisCache:
    """Redis-based cache wrapper with connection pooling, retry, and health check"""
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        max_connections: int = 20,
        retry_on_timeout: bool = True,
        key_prefix: str = "",
        default_ttl: int = 3600,
        max_retries: int = 3
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.max_connections = max_connections
        self.retry_on_timeout = retry_on_timeout
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.max_retries = max_retries
        
        self.client = None
        self._pool = None
        self._connect()
        
        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "retries": 0
        }
    
    def _connect(self):
        """Connect to Redis with connection pool"""
        try:
            import redis
            
            # 创建连接池
            self._pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout,
                decode_responses=True
            )
            
            self.client = redis.Redis(connection_pool=self._pool)
            self.client.ping()
            logger.info(f"Redis connected: {self.host}:{self.port}/{self.db}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.client = None
    
    def _make_key(self, key: str) -> str:
        """Generate key with prefix"""
        if self.key_prefix:
            return f"{self.key_prefix}:{key}"
        return key
    
    def _retry_operation(self, operation, *args, **kwargs):
        """Execute operation with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                self.stats["retries"] += 1
                logger.warning(f"Redis operation failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    self.stats["errors"] += 1
                    raise
                time.sleep(0.1 * (2 ** attempt))  # 指数退避
    
    def health_check(self) -> bool:
        """Check Redis connection health"""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with retry"""
        if not self.client:
            return None
        
        try:
            full_key = self._make_key(key)
            value = self._retry_operation(self.client.get, full_key)
            if value:
                self.stats["hits"] += 1
                return json.loads(value)
            self.stats["misses"] += 1
        except Exception as e:
            logger.error(f"Redis get failed for key '{key}': {e}")
            self.stats["errors"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with retry"""
        if not self.client:
            return False
        
        try:
            full_key = self._make_key(key)
            serialized = json.dumps(value, ensure_ascii=False)
            actual_ttl = ttl if ttl is not None else self.default_ttl
            
            if actual_ttl > 0:
                self._retry_operation(self.client.setex, full_key, actual_ttl, serialized)
            else:
                self._retry_operation(self.client.set, full_key, serialized)
            
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"Redis set failed for key '{key}': {e}")
            self.stats["errors"] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache with retry"""
        if not self.client:
            return False
        
        try:
            full_key = self._make_key(key)
            result = self._retry_operation(self.client.delete, full_key)
            self.stats["deletes"] += 1
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete failed for key '{key}': {e}")
            self.stats["errors"] += 1
            return False
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get multiple keys"""
        if not self.client or not keys:
            return {}
        
        try:
            full_keys = [self._make_key(k) for k in keys]
            values = self._retry_operation(self.client.mget, full_keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                        self.stats["hits"] += 1
                    except:
                        self.stats["misses"] += 1
                else:
                    self.stats["misses"] += 1
            return result
        except Exception as e:
            logger.error(f"Redis mget failed: {e}")
            self.stats["errors"] += 1
            return {}
    
    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Batch set multiple keys"""
        if not self.client or not mapping:
            return False
        
        try:
            pipe = self.client.pipeline()
            actual_ttl = ttl if ttl is not None else self.default_ttl
            
            for key, value in mapping.items():
                full_key = self._make_key(key)
                serialized = json.dumps(value, ensure_ascii=False)
                if actual_ttl > 0:
                    pipe.setex(full_key, actual_ttl, serialized)
                else:
                    pipe.set(full_key, serialized)
            
            self._retry_operation(pipe.execute)
            self.stats["sets"] += len(mapping)
            return True
        except Exception as e:
            logger.error(f"Redis mset failed: {e}")
            self.stats["errors"] += 1
            return False
    
    def clear(self) -> bool:
        """Clear all cache (dangerous: only clears current db)"""
        if not self.client:
            return False
        
        try:
            if self.key_prefix:
                # 只删除带前缀的键
                pattern = f"{self.key_prefix}:*"
                keys = self.client.keys(pattern)
                if keys:
                    self.client.delete(*keys)
            else:
                self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear failed: {e}")
            self.stats["errors"] += 1
            return False
    
    def has(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            full_key = self._make_key(key)
            return self._retry_operation(self.client.exists, full_key) > 0
        except Exception as e:
            logger.error(f"Redis exists check failed for key '{key}': {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return self.stats.copy()
    
    def close(self):
        """Close Redis connection pool"""
        if self._pool:
            self._pool.disconnect()
            self._pool = None
            self.client = None
            logger.info("Redis connection pool closed")

class CacheManager:
    """Unified cache manager supporting multiple backends with enhanced features"""
    
    def __init__(self, backend: str = "local", **kwargs):
        self.backend = backend
        
        if backend == "redis":
            self.cache = RedisCache(**kwargs)
        else:
            self.cache = LocalCache(**kwargs)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        return self.cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        return self.cache.delete(key)
    
    def clear(self) -> bool:
        """Clear all cache"""
        return self.cache.clear()
    
    def has(self, key: str) -> bool:
        """Check if key exists"""
        return self.cache.has(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if hasattr(self.cache, 'get_stats'):
            return self.cache.get_stats()
        return {}
    
    def health_check(self) -> bool:
        """Check cache backend health (Redis only)"""
        if hasattr(self.cache, 'health_check'):
            return self.cache.health_check()
        return True  # Local cache is always healthy
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get multiple keys (Redis only, fallback to single gets for local)"""
        if hasattr(self.cache, 'mget'):
            return self.cache.mget(keys)
        # Fallback for local cache
        result = {}
        for key in keys:
            value = self.cache.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Batch set multiple keys (Redis only, fallback to single sets for local)"""
        if hasattr(self.cache, 'mset'):
            return self.cache.mset(mapping, ttl)
        # Fallback for local cache
        for key, value in mapping.items():
            self.cache.set(key, value, ttl)
        return True
    
    def close(self):
        """Close cache backend connection (Redis only)"""
        if hasattr(self.cache, 'close'):
            self.cache.close()
    
    def get_or_set(self, key: str, default_func, ttl: Optional[int] = None) -> Any:
        """Get value from cache, or set it using default_func if not exists"""
        value = self.get(key)
        if value is None:
            value = default_func()
            self.set(key, value, ttl)
        return value

# Global cache instance
cache = CacheManager()
