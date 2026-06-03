#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Cache Module - Enhanced caching system with multiple backends
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from collections import OrderedDict

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
        return hashlib.md5(key.encode()).hexdigest()
    
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
    """Redis-based cache wrapper"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            import redis
            self.client = redis.Redis(host=self.host, port=self.port, db=self.db)
            self.client.ping()
        except Exception:
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if not self.client:
            return
        
        try:
            serialized = json.dumps(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
        except Exception:
            pass
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            return False
        
        try:
            return self.client.delete(key) > 0
        except Exception:
            return False
    
    def clear(self) -> None:
        """Clear all cache"""
        if self.client:
            try:
                self.client.flushdb()
            except Exception:
                pass
    
    def has(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception:
            return False

class CacheManager:
    """Unified cache manager supporting multiple backends"""
    
    def __init__(self, backend: str = "local", **kwargs):
        self.backend = backend
        
        if backend == "redis":
            self.cache = RedisCache(**kwargs)
        else:
            self.cache = LocalCache(**kwargs)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        self.cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        return self.cache.delete(key)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
    
    def has(self, key: str) -> bool:
        """Check if key exists"""
        return self.cache.has(key)
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics (only for local backend)"""
        if hasattr(self.cache, 'get_stats'):
            return self.cache.get_stats()
        return {}

# Global cache instance
cache = CacheManager()
