#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多级缓存系统 - 支持L1内存缓存、L2文件缓存、L3数据库缓存
"""

import os
import time
import json
import hashlib
import functools
import sys
from typing import Any, Dict, Optional, Callable, List, Union
from enum import Enum

# 使用标准库logging,避免与本地logging.py冲突
import importlib
logging = importlib.import_module('logging')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('multilevel_cache')

class CacheLevel(Enum):
    """缓存级别枚举"""
    L1 = "l1"  # 内存缓存 - 最快,容量小
    L2 = "l2"  # 文件缓存 - 中等速度,容量较大
    L3 = "l3"  # 数据库缓存 - 持久化,容量大

class CachePolicy(Enum):
    """缓存策略枚举"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最不常使用
    FIFO = "fifo"  # 先进先出
    TIME_BASED = "time_based"  # 基于时间

class MultiLevelCache:
    """多级缓存系统"""
    
    def __init__(self, config: Dict = None):
        """初始化多级缓存
        
        Args:
            config: 缓存配置
        """
        self.config = config or self._default_config()
        
        # L1 内存缓存
        self.l1_cache = {}
        self.l1_metadata = {}
        self.l1_max_size = self.config['l1_max_size']
        self.l1_ttl = self.config['l1_ttl']
        self.l1_policy = CachePolicy(self.config['l1_policy'])
        
        # L2 文件缓存
        self.l2_cache_dir = self.config['l2_cache_dir']
        self.l2_max_size = self.config['l2_max_size']
        self.l2_ttl = self.config['l2_ttl']
        self._init_l2_cache_dir()
        
        # L3 数据库缓存
        self.l3_db_path = self.config['l3_db_path']
        self.l3_ttl = self.config['l3_ttl']
        self._init_l3_database()
        
        # 统计信息
        self.stats = {
            'hits': {CacheLevel.L1: 0, CacheLevel.L2: 0, CacheLevel.L3: 0},
            'misses': {CacheLevel.L1: 0, CacheLevel.L2: 0, CacheLevel.L3: 0},
            'sets': {CacheLevel.L1: 0, CacheLevel.L2: 0, CacheLevel.L3: 0},
            'evictions': {CacheLevel.L1: 0, CacheLevel.L2: 0, CacheLevel.L3: 0}
        }
        
        # 缓存键前缀
        self.key_prefix = "mtscos_cache_"
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # L1 内存缓存配置
            'l1_max_size': 1000,
            'l1_ttl': 300,  # 5分钟
            'l1_policy': 'lru',
            
            # L2 文件缓存配置
            'l2_cache_dir': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cache/l2',
            'l2_max_size': 100 * 1024 * 1024,  # 100MB
            'l2_ttl': 3600,  # 1小时
            
            # L3 数据库缓存配置
            'l3_db_path': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cache/l3/cache.db',
            'l3_ttl': 86400,  # 24小时
            
            # 全局配置
            'enable_l1': True,
            'enable_l2': True,
            'enable_l3': True,
            'auto_promote': True,  # 自动升级缓存级别
            'auto_demote': True    # 自动降级缓存级别
        }
    
    def _init_l2_cache_dir(self):
        """初始化L2缓存目录"""
        if not os.path.exists(self.l2_cache_dir):
            os.makedirs(self.l2_cache_dir)
            logger.info(f"创建L2缓存目录: {self.l2_cache_dir}")
    
    def _init_l3_database(self):
        """初始化L3数据库"""
        import sqlite3
        
        db_dir = os.path.dirname(self.l3_db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        conn = sqlite3.connect(self.l3_db_path)
        cursor = conn.cursor()
        
        # 创建缓存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at REAL NOT NULL,
                accessed_at REAL NOT NULL,
                ttl REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                size INTEGER DEFAULT 0
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_accessed_at ON cache(accessed_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_created_at ON cache(created_at)')
        
        conn.commit()
        conn.close()
        logger.info(f"初始化L3数据库: {self.l3_db_path}")
    
    def _generate_key(self, key: str) -> str:
        """生成缓存键"""
        return self.key_prefix + hashlib.md5(key.encode()).hexdigest()
    
    def _get_l2_path(self, key: str) -> str:
        """获取L2缓存文件路径"""
        hashed_key = self._generate_key(key)
        # 使用两级目录结构避免单目录文件过多
        dir1 = hashed_key[:2]
        dir2 = hashed_key[2:4]
        cache_dir = os.path.join(self.l2_cache_dir, dir1, dir2)
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        return os.path.join(cache_dir, f"{hashed_key}.cache")
    
    def _is_expired(self, created_at: float, ttl: float) -> bool:
        """检查是否过期"""
        return time.time() - created_at > ttl
    
    # ==================== L1 内存缓存操作 ====================
    
    def _l1_get(self, key: str) -> Optional[Any]:
        """从L1缓存获取"""
        if not self.config['enable_l1']:
            return None
        
        cache_key = self._generate_key(key)
        
        if cache_key not in self.l1_cache:
            self.stats['misses'][CacheLevel.L1] += 1
            return None
        
        item = self.l1_cache[cache_key]
        
        if self._is_expired(item['created_at'], self.l1_ttl):
            del self.l1_cache[cache_key]
            del self.l1_metadata[cache_key]
            self.stats['misses'][CacheLevel.L1] += 1
            return None
        
        # 更新访问时间(用于LRU)
        self.l1_metadata[cache_key]['accessed_at'] = time.time()
        self.l1_metadata[cache_key]['access_count'] += 1
        
        self.stats['hits'][CacheLevel.L1] += 1
        return item['value']
    
    def _l1_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置L1缓存"""
        if not self.config['enable_l1']:
            return
        
        cache_key = self._generate_key(key)
        current_time = time.time()
        
        # 检查是否需要驱逐
        if len(self.l1_cache) >= self.l1_max_size:
            self._l1_evict()
        
        self.l1_cache[cache_key] = {
            'value': value,
            'created_at': current_time,
            'ttl': ttl or self.l1_ttl
        }
        
        self.l1_metadata[cache_key] = {
            'accessed_at': current_time,
            'access_count': 1
        }
        
        self.stats['sets'][CacheLevel.L1] += 1
    
    def _l1_evict(self):
        """L1缓存驱逐"""
        if not self.l1_cache:
            return
        
        evict_key = None
        
        if self.l1_policy == CachePolicy.LRU:
            # 最近最少使用
            evict_key = min(self.l1_metadata.keys(), 
                          key=lambda k: self.l1_metadata[k]['accessed_at'])
        elif self.l1_policy == CachePolicy.LFU:
            # 最不常使用
            evict_key = min(self.l1_metadata.keys(),
                          key=lambda k: self.l1_metadata[k]['access_count'])
        elif self.l1_policy == CachePolicy.FIFO:
            # 先进先出
            evict_key = min(self.l1_cache.keys(),
                          key=lambda k: self.l1_cache[k]['created_at'])
        
        if evict_key:
            del self.l1_cache[evict_key]
            del self.l1_metadata[evict_key]
            self.stats['evictions'][CacheLevel.L1] += 1
    
    def _l1_delete(self, key: str):
        """删除L1缓存"""
        cache_key = self._generate_key(key)
        if cache_key in self.l1_cache:
            del self.l1_cache[cache_key]
            if cache_key in self.l1_metadata:
                del self.l1_metadata[cache_key]
    
    # ==================== L2 文件缓存操作 ====================
    
    def _l2_get(self, key: str) -> Optional[Any]:
        """从L2缓存获取"""
        if not self.config['enable_l2']:
            return None
        
        cache_path = self._get_l2_path(key)
        
        if not os.path.exists(cache_path):
            self.stats['misses'][CacheLevel.L2] += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if self._is_expired(data['created_at'], data.get('ttl', self.l2_ttl)):
                os.remove(cache_path)
                self.stats['misses'][CacheLevel.L2] += 1
                return None
            
            # 更新访问时间
            data['accessed_at'] = time.time()
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            self.stats['hits'][CacheLevel.L2] += 1
            return data['value']
        
        except Exception as e:
            logger.error(f"L2缓存读取失败: {e}")
            self.stats['misses'][CacheLevel.L2] += 1
            return None
    
    def _l2_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置L2缓存"""
        if not self.config['enable_l2']:
            return
        
        cache_path = self._get_l2_path(key)
        current_time = time.time()
        
        data = {
            'key': key,
            'value': value,
            'created_at': current_time,
            'accessed_at': current_time,
            'ttl': ttl or self.l2_ttl
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        self.stats['sets'][CacheLevel.L2] += 1
    
    def _l2_delete(self, key: str):
        """删除L2缓存"""
        cache_path = self._get_l2_path(key)
        if os.path.exists(cache_path):
            os.remove(cache_path)
    
    # ==================== L3 数据库缓存操作 ====================
    
    def _l3_get(self, key: str) -> Optional[Any]:
        """从L3缓存获取"""
        if not self.config['enable_l3']:
            return None
        
        import sqlite3
        
        cache_key = self._generate_key(key)
        
        try:
            conn = sqlite3.connect(self.l3_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT value, created_at, ttl FROM cache WHERE key = ?', (cache_key,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                self.stats['misses'][CacheLevel.L3] += 1
                return None
            
            value_str, created_at, ttl = row
            
            if self._is_expired(created_at, ttl):
                cursor.execute('DELETE FROM cache WHERE key = ?', (cache_key,))
                conn.commit()
                conn.close()
                self.stats['misses'][CacheLevel.L3] += 1
                return None
            
            # 更新访问时间和访问次数
            cursor.execute('''
                UPDATE cache SET accessed_at = ?, access_count = access_count + 1 
                WHERE key = ?
            ''', (time.time(), cache_key))
            conn.commit()
            conn.close()
            
            self.stats['hits'][CacheLevel.L3] += 1
            return json.loads(value_str)
        
        except Exception as e:
            logger.error(f"L3缓存读取失败: {e}")
            self.stats['misses'][CacheLevel.L3] += 1
            return None
    
    def _l3_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置L3缓存"""
        if not self.config['enable_l3']:
            return
        
        import sqlite3
        
        cache_key = self._generate_key(key)
        current_time = time.time()
        value_str = json.dumps(value)
        
        try:
            conn = sqlite3.connect(self.l3_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache 
                (key, value, created_at, accessed_at, ttl, access_count, size)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            ''', (cache_key, value_str, current_time, current_time, ttl or self.l3_ttl, len(value_str)))
            
            conn.commit()
            conn.close()
            
            self.stats['sets'][CacheLevel.L3] += 1
        
        except Exception as e:
            logger.error(f"L3缓存写入失败: {e}")
    
    def _l3_delete(self, key: str):
        """删除L3缓存"""
        import sqlite3
        
        cache_key = self._generate_key(key)
        
        try:
            conn = sqlite3.connect(self.l3_db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache WHERE key = ?', (cache_key,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"L3缓存删除失败: {e}")
    
    # ==================== 公共接口 ====================
    
    def get(self, key: str) -> Optional[Any]:
        """从多级缓存获取数据
        
        查找顺序: L1 -> L2 -> L3
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值,如果不存在或过期返回None
        """
        # L1 查找
        value = self._l1_get(key)
        if value is not None:
            # 自动升级:L1命中,同时写入L2
            if self.config['auto_promote']:
                self._l2_set(key, value)
            return value
        
        # L2 查找
        value = self._l2_get(key)
        if value is not None:
            # 自动升级:L2命中,写入L1
            if self.config['auto_promote']:
                self._l1_set(key, value)
            return value
        
        # L3 查找
        value = self._l3_get(key)
        if value is not None:
            # 自动升级:L3命中,写入L1和L2
            if self.config['auto_promote']:
                self._l1_set(key, value)
                self._l2_set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            level: Optional[CacheLevel] = None):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)
            level: 缓存级别,默认为全部级别
        """
        if level is None or level == CacheLevel.L1:
            self._l1_set(key, value, ttl)
        
        if level is None or level == CacheLevel.L2:
            self._l2_set(key, value, ttl)
        
        if level is None or level == CacheLevel.L3:
            self._l3_set(key, value, ttl)
    
    def delete(self, key: str):
        """删除缓存"""
        self._l1_delete(key)
        self._l2_delete(key)
        self._l3_delete(key)
    
    def clear(self, level: Optional[CacheLevel] = None):
        """清空缓存"""
        if level is None or level == CacheLevel.L1:
            self.l1_cache.clear()
            self.l1_metadata.clear()
        
        if level is None or level == CacheLevel.L2:
            import shutil
            if os.path.exists(self.l2_cache_dir):
                shutil.rmtree(self.l2_cache_dir)
                os.makedirs(self.l2_cache_dir)
        
        if level is None or level == CacheLevel.L3:
            import sqlite3
            conn = sqlite3.connect(self.l3_db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache')
            conn.commit()
            conn.close()
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_hits = sum(self.stats['hits'].values())
        total_misses = sum(self.stats['misses'].values())
        total = total_hits + total_misses
        
        return {
            'l1': {
                'hits': self.stats['hits'][CacheLevel.L1],
                'misses': self.stats['misses'][CacheLevel.L1],
                'sets': self.stats['sets'][CacheLevel.L1],
                'evictions': self.stats['evictions'][CacheLevel.L1],
                'size': len(self.l1_cache)
            },
            'l2': {
                'hits': self.stats['hits'][CacheLevel.L2],
                'misses': self.stats['misses'][CacheLevel.L2],
                'sets': self.stats['sets'][CacheLevel.L2],
                'evictions': 0
            },
            'l3': {
                'hits': self.stats['hits'][CacheLevel.L3],
                'misses': self.stats['misses'][CacheLevel.L3],
                'sets': self.stats['sets'][CacheLevel.L3],
                'evictions': 0
            },
            'total': {
                'hits': total_hits,
                'misses': total_misses,
                'hit_rate': (total_hits / total * 100) if total > 0 else 0
            }
        }
    
    def decorator(self, ttl: Optional[int] = None, level: Optional[CacheLevel] = None):
        """缓存装饰器"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                key_parts = [
                    func.__module__,
                    func.__name__,
                    str(args),
                    str(sorted(kwargs.items()))
                ]
                cache_key = "::".join(key_parts)
                
                # 尝试获取缓存
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_value
                
                # 执行函数
                logger.debug(f"缓存未命中,执行函数: {cache_key}")
                result = func(*args, **kwargs)
                
                # 设置缓存
                self.set(cache_key, result, ttl, level)
                
                return result
            
            return wrapper
        
        return decorator

# 全局实例
multi_level_cache = MultiLevelCache()

def get_multi_level_cache() -> MultiLevelCache:
    """获取多级缓存实例"""
    return multi_level_cache

# 便捷函数
def cache_get(key: str) -> Optional[Any]:
    """获取缓存"""
    return multi_level_cache.get(key)

def cache_set(key: str, value: Any, ttl: Optional[int] = None):
    """设置缓存"""
    multi_level_cache.set(key, value, ttl)

def cache_delete(key: str):
    """删除缓存"""
    multi_level_cache.delete(key)

def cache_clear():
    """清空所有缓存"""
    multi_level_cache.clear()

def cache_stats() -> Dict:
    """获取缓存统计"""
    return multi_level_cache.get_stats()

if __name__ == '__main__':
    # 测试多级缓存
    cache = MultiLevelCache()
    
    # 设置缓存
    cache.set('test_key', {'name': 'test', 'value': 42})
    
    # 获取缓存(应该从L1获取)
    result = cache.get('test_key')
    print(f"第一次获取: {result}")
    
    # 再次获取(应该从L1获取,命中)
    result = cache.get('test_key')
    print(f"第二次获取: {result}")
    
    # 统计信息
    stats = cache.get_stats()
    print("\n缓存统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 测试装饰器
    @cache.decorator(ttl=60)
    def expensive_computation(x, y):
        print(f"执行计算: {x} + {y}")
        return x + y
    
    print("\n测试装饰器:")
    print(f"结果1: {expensive_computation(10, 20)}")
    print(f"结果2: {expensive_computation(10, 20)}")  # 应该命中缓存
    
    stats = cache.get_stats()
    print("\n最终统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
