#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多级缓存服务 - 实现内存缓存、Redis缓存和文件缓存的多级缓存体系
"""

import json
import os
import time
import hashlib
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import OrderedDict


class CacheLevel(Enum):
    """缓存级别"""
    L1 = "l1"  # 内存缓存(最快,容量小)
    L2 = "l2"  # Redis缓存(较快,容量大)
    L3 = "l3"  # 文件缓存(较慢,容量超大)


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"       # 最近最少使用
    LFU = "lfu"       # 最不经常使用
    FIFO = "fifo"     # 先进先出
    TTL = "ttl"       # 时间过期


@dataclass
class CacheItem:
    """缓存项"""
    key: str
    value: Any
    created_at: float = field(default_factory=lambda: time.time())
    accessed_at: float = field(default_factory=lambda: time.time())
    access_count: int = 0
    ttl: int = 3600  # 过期时间(秒)
    level: CacheLevel = CacheLevel.L1

    def is_expired(self) -> bool:
        """检查是否过期"""
        return (time.time() - self.created_at) > self.ttl

    def touch(self):
        """更新访问时间和访问次数"""
        self.accessed_at = time.time()
        self.access_count += 1

    def to_dict(self) -> Dict:
        return {
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at,
            'accessed_at': self.accessed_at,
            'access_count': self.access_count,
            'ttl': self.ttl,
            'level': self.level.value
        }


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1024):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                return None
            
            # 移动到末尾表示最近使用
            self._cache.move_to_end(key)
            item = self._cache[key]
            
            if item.is_expired():
                del self._cache[key]
                return None
            
            item.touch()
            return item.value

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        with self._lock:
            if len(self._cache) >= self._max_size:
                # 移除最老的
                self._cache.popitem(last=False)
            
            self._cache[key] = CacheItem(
                key=key,
                value=value,
                ttl=ttl,
                level=CacheLevel.L1
            )

    def delete(self, key: str):
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)


class LFUCache:
    """LFU缓存实现"""
    
    def __init__(self, max_size: int = 1024):
        self._cache: Dict[str, CacheItem] = {}
        self._max_size = max_size
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            
            if item.is_expired():
                del self._cache[key]
                return None
            
            item.touch()
            return item.value

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        with self._lock:
            if len(self._cache) >= self._max_size:
                # 移除访问次数最少的
                min_key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
                del self._cache[min_key]
            
            self._cache[key] = CacheItem(
                key=key,
                value=value,
                ttl=ttl,
                level=CacheLevel.L1
            )

    def delete(self, key: str):
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)


class FIFOCache:
    """FIFO缓存实现"""
    
    def __init__(self, max_size: int = 1024):
        self._cache: Dict[str, CacheItem] = {}
        self._order: List[str] = []
        self._max_size = max_size
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            
            if item.is_expired():
                self._order.remove(key)
                del self._cache[key]
                return None
            
            item.touch()
            return item.value

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        with self._lock:
            if key in self._cache:
                self._order.remove(key)
            
            if len(self._order) >= self._max_size:
                # 移除最早的
                oldest_key = self._order.pop(0)
                del self._cache[oldest_key]
            
            self._order.append(key)
            self._cache[key] = CacheItem(
                key=key,
                value=value,
                ttl=ttl,
                level=CacheLevel.L1
            )

    def delete(self, key: str):
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                self._order.remove(key)
                del self._cache[key]

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._order.clear()
            self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)


class RedisCache:
    """Redis缓存封装"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self._host = host
        self._port = port
        self._db = db
        self._client = None
        self._connect()

    def _connect(self):
        """连接Redis"""
        try:
            import redis
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                decode_responses=True
            )
            # 测试连接
            self._client.ping()
        except Exception as e:
            from app.utils.logging import logger
            logger.warning(f"Redis连接失败: {str(e)}")
            self._client = None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._client:
            return None
        
        try:
            value = self._client.get(key)
            if value is None:
                return None
            
            return json.loads(value)
        except Exception as e:
            from app.utils.logging import logger
            logger.error(f"Redis获取失败: {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        if not self._client:
            return
        
        try:
            self._client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            from app.utils.logging import logger
            logger.error(f"Redis设置失败: {str(e)}")

    def delete(self, key: str):
        """删除缓存"""
        if not self._client:
            return
        
        try:
            self._client.delete(key)
        except Exception as e:
            from app.utils.logging import logger
            logger.error(f"Redis删除失败: {str(e)}")

    def clear(self):
        """清空缓存"""
        if not self._client:
            return
        
        try:
            self._client.flushdb()
        except Exception as e:
            from app.utils.logging import logger
            logger.error(f"Redis清空失败: {str(e)}")

    def size(self) -> int:
        """获取缓存大小"""
        if not self._client:
            return 0
        
        try:
            return self._client.dbsize()
        except Exception as e:
            from app.utils.logging import logger
            logger.error(f"Redis获取大小失败: {str(e)}")
            return 0


class FileCache:
    """文件缓存实现"""
    
    def __init__(self, cache_dir: str = '/app/data/cache'):
        self._cache_dir = cache_dir
        self._lock = threading.RLock()
        os.makedirs(self._cache_dir, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        """获取缓存文件路径"""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        sub_dir = hash_key[:2]
        dir_path = os.path.join(self._cache_dir, sub_dir)
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f"{hash_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        file_path = self._get_file_path(key)
        
        with self._lock:
            if not os.path.exists(file_path):
                return None
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查过期
                if 'created_at' in data and 'ttl' in data:
                    if (time.time() - data['created_at']) > data['ttl']:
                        os.remove(file_path)
                        return None
                
                return data.get('value')
            except Exception as e:
                from app.utils.logging import logger
                logger.error(f"文件缓存读取失败: {str(e)}")
                return None

    def set(self, key: str, value: Any, ttl: int = 86400):
        """设置缓存"""
        file_path = self._get_file_path(key)
        
        with self._lock:
            try:
                data = {
                    'key': key,
                    'value': value,
                    'created_at': time.time(),
                    'ttl': ttl
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
            except Exception as e:
                from app.utils.logging import logger
                logger.error(f"文件缓存写入失败: {str(e)}")

    def delete(self, key: str):
        """删除缓存"""
        file_path = self._get_file_path(key)
        
        with self._lock:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    from app.utils.logging import logger
                    logger.error(f"文件缓存删除失败: {str(e)}")

    def clear(self):
        """清空缓存"""
        with self._lock:
            try:
                for root, dirs, files in os.walk(self._cache_dir):
                    for file in files:
                        os.remove(os.path.join(root, file))
            except Exception as e:
                from app.utils.logging import logger
                logger.error(f"文件缓存清空失败: {str(e)}")

    def size(self) -> int:
        """获取缓存大小(文件数量)"""
        count = 0
        try:
            for root, dirs, files in os.walk(self._cache_dir):
                count += len(files)
            return count
        except Exception as e:
            from app.utils.logging import logger
            logger.error(f"文件缓存统计失败: {str(e)}")
            return 0


class MultiLevelCacheService:
    """多级缓存服务"""

    def __init__(self):
        self._strategy = CacheStrategy.LRU
        self._l1_cache = LRUCache(max_size=1024)  # 内存缓存
        self._l2_cache = RedisCache(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379))
        )  # Redis缓存
        self._l3_cache = FileCache()  # 文件缓存
        
        self._stats = {
            'hits': {
                'l1': 0,
                'l2': 0,
                'l3': 0
            },
            'misses': {
                'l1': 0,
                'l2': 0,
                'l3': 0
            },
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        self._stats_lock = threading.RLock()
        
        self._cache_warmup_thread = None
        self._cleanup_thread = None
        self._running = False
        
        from app.utils.logging import logger
        logger.info("多级缓存服务初始化完成")

    def set_strategy(self, strategy: CacheStrategy):
        """设置缓存策略"""
        self._strategy = strategy
        
        # 根据策略创建不同的L1缓存
        if strategy == CacheStrategy.LRU:
            self._l1_cache = LRUCache(max_size=1024)
        elif strategy == CacheStrategy.LFU:
            self._l1_cache = LFUCache(max_size=1024)
        elif strategy == CacheStrategy.FIFO:
            self._l1_cache = FIFOCache(max_size=1024)
        
        from app.utils.logging import logger
        logger.info(f"缓存策略已设置为: {strategy.value}")

    def get(self, key: str, levels: Optional[List[CacheLevel]] = None) -> Optional[Any]:
        """获取缓存(多级查找)"""
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3]
        
        # 按级别顺序查找
        for level in levels:
            value = self._get_from_level(key, level)
            if value is not None:
                # 向上缓存
                self._promote(key, value, level)
                return value
        
        return None

    def _get_from_level(self, key: str, level: CacheLevel) -> Optional[Any]:
        """从指定级别获取缓存"""
        value = None
        
        if level == CacheLevel.L1:
            value = self._l1_cache.get(key)
        elif level == CacheLevel.L2:
            value = self._l2_cache.get(key)
        elif level == CacheLevel.L3:
            value = self._l3_cache.get(key)
        
        # 更新统计
        with self._stats_lock:
            if value is not None:
                self._stats['hits'][level.value] += 1
            else:
                self._stats['misses'][level.value] += 1
        
        return value

    def _promote(self, key: str, value: Any, source_level: CacheLevel):
        """将缓存向上提升到更高级别"""
        # L3 -> L2 -> L1
        if source_level == CacheLevel.L3:
            self._l2_cache.set(key, value)
            self._l1_cache.set(key, value)
        elif source_level == CacheLevel.L2:
            self._l1_cache.set(key, value)

    def set(self, key: str, value: Any, ttl: int = 3600, 
            levels: Optional[List[CacheLevel]] = None):
        """设置缓存(多级写入)"""
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2]
        
        for level in levels:
            if level == CacheLevel.L1:
                self._l1_cache.set(key, value, ttl)
            elif level == CacheLevel.L2:
                self._l2_cache.set(key, value, ttl)
            elif level == CacheLevel.L3:
                self._l3_cache.set(key, value, ttl)
        
        with self._stats_lock:
            self._stats['sets'] += 1

    def delete(self, key: str):
        """删除缓存(多级删除)"""
        self._l1_cache.delete(key)
        self._l2_cache.delete(key)
        self._l3_cache.delete(key)
        
        with self._stats_lock:
            self._stats['deletes'] += 1

    def clear(self):
        """清空所有缓存"""
        self._l1_cache.clear()
        self._l2_cache.clear()
        self._l3_cache.clear()

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        with self._stats_lock:
            total_hits = sum(self._stats['hits'].values())
            total_misses = sum(self._stats['misses'].values())
            total_requests = total_hits + total_misses
            
            hit_rate = (total_hits / total_requests) * 100 if total_requests > 0 else 0
            
            return {
                'strategy': self._strategy.value,
                'hits': self._stats['hits'].copy(),
                'misses': self._stats['misses'].copy(),
                'sets': self._stats['sets'],
                'deletes': self._stats['deletes'],
                'evictions': self._stats['evictions'],
                'total_requests': total_requests,
                'hit_rate': round(hit_rate, 2),
                'sizes': {
                    'l1': self._l1_cache.size(),
                    'l2': self._l2_cache.size(),
                    'l3': self._l3_cache.size()
                }
            }

    def warmup(self, warmup_data: Dict[str, Any]):
        """预热缓存"""
        for key, value in warmup_data.items():
            self.set(key, value, ttl=3600)
        
        from app.utils.logging import logger
        logger.info(f"缓存预热完成,加载了 {len(warmup_data)} 条数据")

    def start_periodic_cleanup(self, interval_hours: int = 24):
        """启动定期清理任务"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            args=(interval_hours,),
            daemon=True
        )
        self._cleanup_thread.start()
        
        from app.utils.logging import logger
        logger.info(f"定期清理任务已启动,间隔 {interval_hours} 小时")

    def _cleanup_loop(self, interval_hours: int):
        """清理循环"""
        while self._running:
            try:
                self._cleanup_expired()
                time.sleep(interval_hours * 3600)
            except Exception as e:
                from app.utils.logging import logger
                logger.error(f"缓存清理失败: {str(e)}")
                time.sleep(3600)

    def _cleanup_expired(self):
        """清理过期缓存"""
        # 文件缓存需要手动清理
        count = 0
        try:
            for root, dirs, files in os.walk(self._l3_cache._cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if (time.time() - data.get('created_at', 0)) > data.get('ttl', 86400):
                                os.remove(file_path)
                                count += 1
                    except Exception:
                        os.remove(file_path)
                        count += 1
            
            from app.utils.logging import logger
            logger.info(f"清理了 {count} 个过期文件缓存")
        except Exception as e:
            from app.utils.logging import logger
            logger.error(f"清理过期缓存失败: {str(e)}")

    def stop(self):
        """停止服务"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)


# 创建全局实例
cache_service = MultiLevelCacheService()
