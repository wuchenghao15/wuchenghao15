# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDN + 反向代理管理器 - 支持静态资源加速、请求转发、负载均衡
"""

import os
import time
import hashlib
import json
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cdn_proxy')

class CDNCacheType(Enum):
    """CDN缓存类型"""
    MEMORY = "memory"      # 内存缓存
    DISK = "disk"          # 磁盘缓存
    REDIS = "redis"        # Redis缓存
    CLOUD = "cloud"        # 云CDN

class ProxyMode(Enum):
    """代理模式"""
    REVERSE = "reverse"        # 反向代理
    FORWARD = "forward"        # 正向代理
    TRANSparent = "transparent" # 透明代理

class CDNProxyManager:
    """CDN + 反向代理管理器"""
    
    def __init__(self, config: Dict = None):
        """初始化CDN代理管理器
        
        Args:
            config: 配置字典
        """
        self.config = config or self._default_config()
        
        # CDN配置
        self.cdn_enabled = self.config.get('cdn_enabled', True)
        self.cdn_cache_type = CDNCacheType(self.config.get('cdn_cache_type', 'memory'))
        self.cdn_cache_dir = self.config.get('cdn_cache_dir', '/tmp/cdn_cache')
        self.cdn_ttl = self.config.get('cdn_ttl', 3600)
        
        # 反向代理配置
        self.proxy_enabled = self.config.get('proxy_enabled', True)
        self.proxy_mode = ProxyMode(self.config.get('proxy_mode', 'reverse'))
        self.backend_servers = self.config.get('backend_servers', [])
        
        # 缓存存储
        self.memory_cache = {}
        self.cache_metadata = {}
        
        # 统计信息
        self.stats = {
            'cdn_hits': 0,
            'cdn_misses': 0,
            'proxy_requests': 0,
            'proxy_errors': 0,
            'cache_evictions': 0,
            'bandwidth_saved': 0
        }
        
        # 初始化缓存目录
        self._init_cache_dir()
        
        logger.info("CDN + 反向代理管理器初始化完成")
        logger.info(f"CDN缓存类型: {self.cdn_cache_type.value}")
        logger.info(f"代理模式: {self.proxy_mode.value}")
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # CDN配置
            'cdn_enabled': True,
            'cdn_cache_type': 'memory',
            'cdn_cache_dir': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cache/cdn',
            'cdn_ttl': 3600,
            'cdn_max_size': 100 * 1024 * 1024,  # 100MB
            'cdn_compress': True,
            'cdn_purge_interval': 3600,
            
            # 反向代理配置
            'proxy_enabled': True,
            'proxy_mode': 'reverse',
            'proxy_host': 'localhost',
            'proxy_port': 8080,
            'proxy_timeout': 30,
            'proxy_buffer_size': 8192,
            
            # 后端服务器配置
            'backend_servers': [
                {'host': 'localhost', 'port': 8888, 'weight': 1, 'status': 'active'},
                {'host': 'localhost', 'port': 8889, 'weight': 1, 'status': 'active'},
                {'host': 'localhost', 'port': 8890, 'weight': 2, 'status': 'active'}
            ],
            
            # 缓存策略
            'cache_strategy': 'lru',
            'cache_max_items': 1000,
            
            # 静态资源配置
            'static_extensions': ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'],
            'static_path': '/static/',
            
            # CDN域名配置
            'cdn_domains': [
                'cdn.example.com',
                'cdn2.example.com'
            ]
        }
    
    def _init_cache_dir(self):
        """初始化缓存目录"""
        if not os.path.exists(self.cdn_cache_dir):
            os.makedirs(self.cdn_cache_dir)
            logger.info(f"创建CDN缓存目录: {self.cdn_cache_dir}")
    
    def _generate_cache_key(self, url: str) -> str:
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _is_static_file(self, path: str) -> bool:
        """判断是否为静态文件"""
        ext = os.path.splitext(path)[1].lower()
        return ext in self.config.get('static_extensions', [])
    
    # ==================== CDN缓存操作 ====================
    
    def cdn_get(self, url: str) -> Optional[bytes]:
        """从CDN缓存获取资源"""
        if not self.cdn_enabled:
            return None
        
        cache_key = self._generate_cache_key(url)
        
        # 检查内存缓存
        if cache_key in self.memory_cache:
            item = self.memory_cache[cache_key]
            if not self._is_expired(item['created_at'], item['ttl']):
                self.stats['cdn_hits'] += 1
                return item['data']
            else:
                del self.memory_cache[cache_key]
        
        # 检查磁盘缓存
        if self.cdn_cache_type in [CDNCacheType.DISK, CDNCacheType.CLOUD]:
            cache_path = os.path.join(self.cdn_cache_dir, cache_key)
            if os.path.exists(cache_path):
                # 检查过期时间(存储在单独的元数据文件)
                meta_path = cache_path + '.meta'
                if os.path.exists(meta_path):
                    with open(meta_path, 'r') as f:
                        meta = json.load(f)
                        if not self._is_expired(meta['created_at'], meta['ttl']):
                            with open(cache_path, 'rb') as f:
                                data = f.read()
                            self.stats['cdn_hits'] += 1
                            # 同时加载到内存
                            self.memory_cache[cache_key] = {
                                'data': data,
                                'created_at': time.time(),
                                'ttl': meta['ttl']
                            }
                            return data
        
        self.stats['cdn_misses'] += 1
        return None
    
    def cdn_set(self, url: str, data: bytes, ttl: Optional[int] = None):
        """设置CDN缓存"""
        if not self.cdn_enabled:
            return
        
        cache_key = self._generate_cache_key(url)
        ttl = ttl or self.cdn_ttl
        
        # 内存缓存
        if len(self.memory_cache) >= self.config.get('cache_max_items', 1000):
            self._evict_cache()
        
        self.memory_cache[cache_key] = {
            'data': data,
            'created_at': time.time(),
            'ttl': ttl
        }
        
        # 磁盘缓存
        if self.cdn_cache_type in [CDNCacheType.DISK, CDNCacheType.CLOUD]:
            cache_path = os.path.join(self.cdn_cache_dir, cache_key)
            with open(cache_path, 'wb') as f:
                f.write(data)
            
            # 保存元数据
            meta_path = cache_path + '.meta'
            with open(meta_path, 'w') as f:
                json.dump({
                    'url': url,
                    'created_at': time.time(),
                    'ttl': ttl,
                    'size': len(data)
                }, f)
    
    def _is_expired(self, created_at: float, ttl: float) -> bool:
        """检查是否过期"""
        return time.time() - created_at > ttl
    
    def _evict_cache(self):
        """缓存驱逐"""
        if not self.memory_cache:
            return
        
        # LRU策略
        oldest_key = min(self.memory_cache.keys(), 
                        key=lambda k: self.memory_cache[k]['created_at'])
        del self.memory_cache[oldest_key]
        self.stats['cache_evictions'] += 1
    
    def cdn_purge(self, url: str = None):
        """清除CDN缓存"""
        if url:
            cache_key = self._generate_cache_key(url)
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            if self.cdn_cache_type in [CDNCacheType.DISK, CDNCacheType.CLOUD]:
                cache_path = os.path.join(self.cdn_cache_dir, cache_key)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                meta_path = cache_path + '.meta'
                if os.path.exists(meta_path):
                    os.remove(meta_path)
        else:
            # 清除所有缓存
            self.memory_cache.clear()
            
            if self.cdn_cache_type in [CDNCacheType.DISK, CDNCacheType.CLOUD]:
                for f in os.listdir(self.cdn_cache_dir):
                    os.remove(os.path.join(self.cdn_cache_dir, f))
    
    # ==================== 反向代理操作 ====================
    
    def _select_backend(self) -> Optional[Dict]:
        """选择后端服务器"""
        active_servers = [s for s in self.backend_servers if s['status'] == 'active']
        
        if not active_servers:
            return None
        
        # 加权随机选择
        total_weight = sum(s['weight'] for s in active_servers)
        import random
        rand = random.randint(1, total_weight)
        
        for server in active_servers:
            rand -= server['weight']
            if rand <= 0:
                return server
        
        return active_servers[0]
    
    def proxy_request(self, method: str, path: str, headers: Dict = None, 
                     body: bytes = None) -> Tuple[int, Dict, bytes]:
        """代理请求到后端服务器"""
        if not self.proxy_enabled:
            return 503, {}, b"Proxy disabled"
        
        backend = self._select_backend()
        if not backend:
            return 503, {}, b"No backend servers available"
        
        try:
            import http.client
            
            conn = http.client.HTTPConnection(backend['host'], backend['port'], 
                                            timeout=self.config.get('proxy_timeout', 30))
            
            # 构建请求头
            proxy_headers = headers.copy() if headers else {}
            proxy_headers['X-Forwarded-For'] = '127.0.0.1'
            proxy_headers['X-Forwarded-Proto'] = 'http'
            proxy_headers['X-Forwarded-Host'] = self.config.get('proxy_host', 'localhost')
            
            conn.request(method, path, body, proxy_headers)
            response = conn.getresponse()
            
            response_headers = dict(response.getheaders())
            response_body = response.read()
            
            conn.close()
            
            self.stats['proxy_requests'] += 1
            
            return response.status, response_headers, response_body
        
        except Exception as e:
            logger.error(f"代理请求失败: {e}")
            self.stats['proxy_errors'] += 1
            return 500, {}, str(e).encode()
    
    def process_request(self, method: str, path: str, headers: Dict = None, 
                       body: bytes = None) -> Tuple[int, Dict, bytes]:
        """处理请求(CDN + 代理)"""
        # 检查是否为静态资源
        if self._is_static_file(path):
            # 尝试从CDN获取
            cdn_data = self.cdn_get(path)
            if cdn_data:
                return 200, {'X-Cache': 'HIT', 'Content-Length': len(cdn_data)}, cdn_data
        
        # 代理到后端
        status, response_headers, response_body = self.proxy_request(method, path, headers, body)
        
        # 如果是静态资源且响应成功,缓存到CDN
        if status == 200 and self._is_static_file(path):
            self.cdn_set(path, response_body)
            # 计算节省的带宽
            self.stats['bandwidth_saved'] += len(response_body)
        
        return status, response_headers, response_body
    
    # ==================== 统计与监控 ====================
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_requests = self.stats['cdn_hits'] + self.stats['cdn_misses']
        hit_rate = (self.stats['cdn_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cdn': {
                'enabled': self.cdn_enabled,
                'cache_type': self.cdn_cache_type.value,
                'hits': self.stats['cdn_hits'],
                'misses': self.stats['cdn_misses'],
                'hit_rate': f"{hit_rate:.2f}%",
                'evictions': self.stats['cache_evictions'],
                'memory_cache_size': len(self.memory_cache)
            },
            'proxy': {
                'enabled': self.proxy_enabled,
                'mode': self.proxy_mode.value,
                'requests': self.stats['proxy_requests'],
                'errors': self.stats['proxy_errors'],
                'backend_count': len(self.backend_servers),
                'active_backends': sum(1 for s in self.backend_servers if s['status'] == 'active')
            },
            'bandwidth_saved': self.stats['bandwidth_saved'],
            'bandwidth_saved_mb': self.stats['bandwidth_saved'] / (1024 * 1024)
        }
    
    def health_check(self):
        """健康检查后端服务器"""
        results = []
        
        for server in self.backend_servers:
            try:
                import http.client
                conn = http.client.HTTPConnection(server['host'], server['port'], timeout=5)
                conn.request('GET', '/health')
                response = conn.getresponse()
                status = response.status
                conn.close()
                
                server['status'] = 'active' if status == 200 else 'degraded'
                results.append({'server': f"{server['host']}:{server['port']}", 'status': server['status']})
            except Exception as e:
                server['status'] = 'down'
                results.append({'server': f"{server['host']}:{server['port']}", 'status': 'down', 'error': str(e)})
        
        return results

# 全局实例
cdn_proxy_manager = CDNProxyManager()

def get_cdn_proxy_manager() -> CDNProxyManager:
    """获取CDN代理管理器实例"""
    return cdn_proxy_manager

# 便捷函数
def cdn_get(url: str) -> Optional[bytes]:
    """从CDN获取资源"""
    return cdn_proxy_manager.cdn_get(url)

def cdn_set(url: str, data: bytes, ttl: Optional[int] = None):
    """设置CDN缓存"""
    cdn_proxy_manager.cdn_set(url, data, ttl)

def cdn_purge(url: str = None):
    """清除CDN缓存"""
    cdn_proxy_manager.cdn_purge(url)

def proxy_request(method: str, path: str, headers: Dict = None, body: bytes = None):
    """代理请求"""
    return cdn_proxy_manager.proxy_request(method, path, headers, body)

def process_request(method: str, path: str, headers: Dict = None, body: bytes = None):
    """处理请求"""
    return cdn_proxy_manager.process_request(method, path, headers, body)

def cdn_proxy_stats():
    """获取统计信息"""
    return cdn_proxy_manager.get_stats()

def health_check():
    """健康检查"""
    return cdn_proxy_manager.health_check()

if __name__ == '__main__':
    # 测试CDN代理
    manager = CDNProxyManager()
    
    print("🚀 CDN + 反向代理测试")
    print("=" * 60)
    
    # 测试1: CDN缓存
    print("\n📝 测试1: CDN缓存")
    test_url = '/static/test.js'
    test_data = b'console.log("Hello CDN");'
    
    # 设置缓存
    manager.cdn_set(test_url, test_data)
    print(f"  设置缓存: {test_url}")
    
    # 获取缓存(应该命中)
    result = manager.cdn_get(test_url)
    print(f"  获取缓存: {'命中' if result else '未命中'}")
    print(f"  数据匹配: {result == test_data}")
    
    # 测试2: 统计信息
    print("\n📝 测试2: 统计信息")
    stats = manager.get_stats()
    print(f"  CDN命中: {stats['cdn']['hits']}")
    print(f"  CDN未命中: {stats['cdn']['misses']}")
    print(f"  命中率: {stats['cdn']['hit_rate']}")
    
    # 测试3: 健康检查
    print("\n📝 测试3: 后端健康检查")
    results = manager.health_check()
    for result in results:
        status = "✅" if result['status'] == 'active' else "❌"
        print(f"  {status} {result['server']}: {result['status']}")
    
    # 测试4: 清除缓存
    print("\n📝 测试4: 清除缓存")
    manager.cdn_purge(test_url)
    result = manager.cdn_get(test_url)
    print(f"  清除后获取: {'未命中' if result is None else '命中'}")
    
    print("\n🎉 测试完成!")
