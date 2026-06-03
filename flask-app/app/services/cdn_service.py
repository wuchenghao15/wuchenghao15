#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDN服务 - 实现内容分发网络和静态资源缓存
"""

import os
import hashlib
import time
import threading
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

from app.utils.logging import logger


class CDNProvider(Enum):
    """CDN提供商"""
    LOCAL = "local"
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    CLOUDFLARE = "cloudflare"
    AWS_CLOUDFRONT = "aws_cloudfront"


class CacheStatus(Enum):
    """缓存状态"""
    HIT = "hit"
    MISS = "miss"
    EXPIRED = "expired"


@dataclass
class CDNResource:
    """CDN资源"""
    url: str
    local_path: str
    etag: str
    last_modified: float
    ttl: int = 3600
    status: str = "active"
    size: int = 0
    hit_count: int = 0
    last_accessed: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'url': self.url,
            'local_path': self.local_path,
            'etag': self.etag,
            'last_modified': self.last_modified,
            'ttl': self.ttl,
            'status': self.status,
            'size': self.size,
            'hit_count': self.hit_count,
            'last_accessed': self.last_accessed
        }


@dataclass
class OriginServer:
    """源站服务器"""
    id: str
    host: str
    port: int = 80
    protocol: str = "http"
    weight: int = 1
    status: str = "active"

    def get_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"


class CDNService:
    """CDN服务"""

    def __init__(self):
        self._provider = CDNProvider.LOCAL
        self._resources: Dict[str, CDNResource] = {}
        self._origin_servers: List[OriginServer] = []
        self._cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cdn_cache')
        self._stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0,
            'bytes_served': 0,
            'origin_requests': 0
        }
        self._lock = threading.RLock()
        self._running = False
        
        os.makedirs(self._cache_dir, exist_ok=True)
        self._init_default_origins()
        logger.info("CDN服务初始化完成")

    def _init_default_origins(self):
        """初始化默认源站"""
        self._origin_servers.append(OriginServer(
            id="origin-primary",
            host="localhost",
            port=8888,
            protocol="http",
            weight=3
        ))
        self._origin_servers.append(OriginServer(
            id="origin-secondary",
            host="localhost",
            port=8889,
            protocol="http",
            weight=1
        ))

    def set_provider(self, provider: CDNProvider):
        """设置CDN提供商"""
        self._provider = provider
        logger.info(f"CDN提供商已设置为: {provider.value}")

    def get_provider(self) -> CDNProvider:
        """获取CDN提供商"""
        return self._provider

    def add_origin_server(self, server_data: Dict):
        """添加源站服务器"""
        server = OriginServer(
            id=server_data.get('id', str(id(server_data))),
            host=server_data.get('host', 'localhost'),
            port=server_data.get('port', 80),
            protocol=server_data.get('protocol', 'http'),
            weight=server_data.get('weight', 1)
        )
        self._origin_servers.append(server)
        logger.info(f"添加源站服务器: {server.id}")

    def remove_origin_server(self, server_id: str):
        """移除源站服务器"""
        self._origin_servers = [s for s in self._origin_servers if s.id != server_id]
        logger.info(f"移除源站服务器: {server_id}")

    def _select_origin(self) -> OriginServer:
        """选择源站服务器(加权轮询)"""
        total_weight = sum(s.weight for s in self._origin_servers)
        if total_weight == 0:
            return self._origin_servers[0]
        
        import random
        random_val = random.randint(1, total_weight)
        current = 0
        for server in self._origin_servers:
            current += server.weight
            if random_val <= current:
                return server
        return self._origin_servers[0]

    def get_resource(self, url: str) -> Optional[CDNResource]:
        """获取CDN资源"""
        with self._lock:
            return self._resources.get(url)

    def _generate_etag(self, content: bytes) -> str:
        """生成ETag"""
        return hashlib.md5(content).hexdigest()

    def _get_cache_path(self, url: str) -> str:
        """获取缓存文件路径"""
        hash_val = hashlib.md5(url.encode()).hexdigest()
        sub_dir = hash_val[:2]
        dir_path = os.path.join(self._cache_dir, sub_dir)
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, hash_val)

    def _fetch_from_origin(self, url: str) -> Optional[bytes]:
        """从源站获取资源"""
        origin = self._select_origin()
        full_url = f"{origin.get_url()}{url}"
        
        try:
            import requests
            response = requests.get(full_url)
            if response.status_code == 200:
                with self._lock:
                    self._stats['origin_requests'] += 1
                return response.content
            return None
        except Exception as e:
            logger.error(f"从源站获取资源失败: {str(e)}")
            return None

    def serve(self, url: str) -> Dict:
        """提供CDN资源服务"""
        with self._lock:
            self._stats['total_requests'] += 1
        
        # 检查缓存
        resource = self.get_resource(url)
        
        if resource:
            # 检查缓存是否过期
            if time.time() - resource.last_modified < resource.ttl:
                # 缓存命中
                with self._lock:
                    resource.hit_count += 1
                    resource.last_accessed = time.time()
                    self._stats['hits'] += 1
                
                # 读取缓存文件
                try:
                    with open(resource.local_path, 'rb') as f:
                        content = f.read()
                    
                    with self._lock:
                        self._stats['bytes_served'] += len(content)
                    
                    return {
                        'status': CacheStatus.HIT.value,
                        'content': content,
                        'etag': resource.etag,
                        'last_modified': resource.last_modified
                    }
                except Exception as e:
                    logger.error(f"读取缓存文件失败: {str(e)}")
        
        # 缓存未命中或过期,从源站获取
        content = self._fetch_from_origin(url)
        if content is None:
            return {'status': 'error', 'error': '无法获取资源'}
        
        # 保存到缓存
        etag = self._generate_etag(content)
        cache_path = self._get_cache_path(url)
        
        try:
            with open(cache_path, 'wb') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"写入缓存文件失败: {str(e)}")
        
        # 更新资源记录
        new_resource = CDNResource(
            url=url,
            local_path=cache_path,
            etag=etag,
            last_modified=time.time(),
            ttl=3600,
            size=len(content),
            hit_count=1,
            last_accessed=time.time()
        )
        
        with self._lock:
            self._resources[url] = new_resource
            self._stats['misses'] += 1
            self._stats['bytes_served'] += len(content)
        
        return {
            'status': CacheStatus.MISS.value,
            'content': content,
            'etag': etag,
            'last_modified': new_resource.last_modified
        }

    def purge_cache(self, url: Optional[str] = None):
        """清除缓存"""
        with self._lock:
            if url:
                # 清除指定URL的缓存
                resource = self._resources.get(url)
                if resource and os.path.exists(resource.local_path):
                    os.remove(resource.local_path)
                    del self._resources[url]
                    logger.info(f"清除缓存: {url}")
            else:
                # 清除所有缓存
                for resource in self._resources.values():
                    if os.path.exists(resource.local_path):
                        os.remove(resource.local_path)
                self._resources.clear()
                logger.info("清除所有缓存")

    def purge_expired(self):
        """清除过期缓存"""
        now = time.time()
        expired_count = 0
        
        with self._lock:
            expired_urls = [url for url, resource in self._resources.items()
                          if now - resource.last_modified > resource.ttl]
            
            for url in expired_urls:
                resource = self._resources[url]
                if os.path.exists(resource.local_path):
                    os.remove(resource.local_path)
                del self._resources[url]
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"清除过期缓存: {expired_count} 个")

    def get_stats(self) -> Dict:
        """获取CDN统计"""
        with self._lock:
            hit_rate = (self._stats['hits'] / self._stats['total_requests']) * 100 \
                       if self._stats['total_requests'] > 0 else 0
            
            return {
                'provider': self._provider.value,
                'total_requests': self._stats['total_requests'],
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'bytes_served': self._stats['bytes_served'],
                'origin_requests': self._stats['origin_requests'],
                'cached_resources': len(self._resources),
                'origin_servers': [s.id for s in self._origin_servers]
            }

    def start_cache_cleanup(self, interval_hours: int = 24):
        """启动定期缓存清理"""
        if self._running:
            return
        
        self._running = True
        thread = threading.Thread(target=self._cleanup_loop, args=(interval_hours,), daemon=True)
        thread.start()
        logger.info(f"定期缓存清理已启动,间隔 {interval_hours} 小时")

    def _cleanup_loop(self, interval_hours: int):
        """清理循环"""
        while self._running:
            try:
                self.purge_expired()
                time.sleep(interval_hours * 3600)
            except Exception as e:
                logger.error(f"缓存清理错误: {str(e)}")
                time.sleep(3600)

    def stop(self):
        """停止服务"""
        self._running = False


# 创建全局实例
cdn_service = CDNService()
