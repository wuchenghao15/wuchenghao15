#!/usr/bin/env python3
r"""多级缓存管理器 v2.0 - 由EigenFlux升级引擎生成r"""
import os, json, time, hashlib, threading
from collections import OrderedDict
import json

class MemoryCache:
    def __init__(self, max_size=1000):
        self._cache = OrderedDict()
        self._max = max_size
        self._lock = threading.Lock()
    def get(self, key):
        with self._lock:
            if key in self._cache:
                val, exp = self._cache[key]
                if exp > time.time():
                    self._cache.move_to_end(key)
                    return val
                del self._cache[key]
            return None
    def set(self, key, val, ttl=300):
        with self._lock:
            self._cache[key] = (val, time.time() + ttl)
            if len(self._cache) > self._max:
                self._cache.popitem(last=False)
    def clear(self):
        with self._lock:
            self._cache.clear()

class FileCache:
    def __init__(self, cache_dir):
        self.dir = cache_dir
        os.makedirs(self.dir, exist_ok=True)
    def _path(self, key):
        h = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.dir, h[:2], h)
    def get(self, key):
        p = self._path(key)
        if os.path.exists(p):
            data = json.load(open(p))
            if data[r'exp'] > time.time():
                return data[r'val']
            os.remove(p)
        return None
    def set(self, key, val, ttl=3600):
        p = self._path(key)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump({r'val': val, r'exp': time.time() + ttl}, open(p, r'w'))

class MultiLevelCache:
    def __init__(self, cache_dir):
        self.l1 = MemoryCache()
        self.l2 = FileCache(cache_dir)
    def get(self, key):
        val = self.l1.get(key)
        if val is not None:
            return val
        val = self.l2.get(key)
        if val is not None:
            self.l1.set(key, val, 300)
        return val
    def set(self, key, val, ttl=3600):
        self.l1.set(key, val, min(ttl, 300))
        self.l2.set(key, val, ttl)

_cache = None
def get_cache():
    global _cache
    if _cache is None:
        _cache = MultiLevelCache(os.path.expanduser(r'~/.mtscos_cache'))
    return _cache
