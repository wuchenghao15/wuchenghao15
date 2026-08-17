#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS数据缓存服务
提供内存缓存和文件缓存功能
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class CacheEntry:
    """缓存条目"""
    
    def __init__(self, key: str, value: Any, ttl: int = 300, 
                 created_at: float = None):
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = created_at or time.time()
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at >= self.ttl
    
    def access(self):
        """访问计数"""
        self.access_count += 1

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.is_running = False
        self.cleanup_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'cache_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'default_ttl': 300,
            'max_entries': 1000,
            'cleanup_interval': 60,
            'persist_enabled': False,
            'persist_path': 'cache',
            'persist_interval': 300
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'cache_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                time.sleep(self.config['cleanup_interval'])
                self._cleanup_expired()
                
                if self.config['persist_enabled']:
                    self._persist_cache()
            except Exception as e:
                logger(f"[缓存] 清理循环错误: {e}")
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        expired_keys = []
        
        with self.lock:
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
        
        if expired_keys:
            logger(f"[缓存] 清理过期缓存: {len(expired_keys)}条")
    
    def _persist_cache(self):
        """持久化缓存"""
        persist_dir = self.config['persist_path']
        os.makedirs(persist_dir, exist_ok=True)
        
        try:
            cache_data = {}
            
            with self.lock:
                for key, entry in self.cache.items():
                    cache_data[key] = {
                        'value': entry.value,
                        'ttl': entry.ttl,
                        'created_at': entry.created_at
                    }
            
            persist_file = os.path.join(persist_dir, f"cache_{int(time.time())}.json")
            with open(persist_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            self._cleanup_old_persist_files()
        except Exception as e:
            logger(f"[缓存] 持久化失败: {e}")
    
    def _cleanup_old_persist_files(self):
        """清理旧的持久化文件"""
        persist_dir = self.config['persist_path']
        
        try:
            files = [f for f in os.listdir(persist_dir) if f.startswith('cache_')]
            files.sort()
            
            if len(files) > 5:
                for f in files[:-5]:
                    os.remove(os.path.join(persist_dir, f))
        except Exception as e:
            logger(f"[缓存] 清理持久化文件失败: {e}")
    
    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        ttl = ttl or self.config['default_ttl']
        
        with self.lock:
            if len(self.cache) >= self.config['max_entries']:
                self._evict()
            
            self.cache[key] = CacheEntry(key, value, ttl)
        
        logger(f"[缓存] 设置缓存: {key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        with self.lock:
            entry = self.cache.get(key)
            
            if entry:
                if entry.is_expired():
                    del self.cache[key]
                    return default
                
                entry.access()
                return entry.value
        
        return default
    
    def delete(self, key: str):
        """删除缓存"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
        
        logger(f"[缓存] 删除缓存: {key}")
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        with self.lock:
            entry = self.cache.get(key)
            
            if entry and entry.is_expired():
                del self.cache[key]
                return False
            
            return entry is not None
    
    def _evict(self):
        """淘汰策略：LRU"""
        with self.lock:
            if self.cache:
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k].created_at)
                del self.cache[oldest_key]
    
    def clear(self):
        """清空所有缓存"""
        with self.lock:
            self.cache.clear()
        
        logger(f"[缓存] 清空所有缓存")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            total = len(self.cache)
            expired = sum(1 for entry in self.cache.values() if entry.is_expired())
            total_access = sum(entry.access_count for entry in self.cache.values())
            
            return {
                'total_entries': total,
                'expired_entries': expired,
                'total_access': total_access,
                'max_entries': self.config['max_entries'],
                'default_ttl': self.config['default_ttl']
            }
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键"""
        with self.lock:
            return list(self.cache.keys())
    
    def get_cache_info(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存信息"""
        with self.lock:
            entry = self.cache.get(key)
            
            if entry:
                return {
                    'key': key,
                    'ttl': entry.ttl,
                    'created_at': datetime.fromtimestamp(entry.created_at).isoformat(),
                    'access_count': entry.access_count,
                    'is_expired': entry.is_expired()
                }
        
        return None
    
    def start(self):
        """启动缓存服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger(f"[缓存] 数据缓存服务已启动")
    
    def stop(self):
        """停止缓存服务"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
        
        if self.config['persist_enabled']:
            self._persist_cache()
        
        logger(f"[缓存] 数据缓存服务已停止")

cache_manager = CacheManager()

def cached(key_prefix: str = '', ttl: int = 300):
    """装饰器：缓存函数结果"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            args_key = json.dumps({'args': args, 'kwargs': kwargs})
            cache_key = f"{key_prefix}:{func.__name__}:{args_key}"
            
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
