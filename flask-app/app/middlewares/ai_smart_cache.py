#!/usr/bin/env python3
"""
AI智能缓存中间件
根据请求频率和响应时间自动调整缓存策略
"""

import time
import json
import hashlib
import logging

from app.utils.logging import logger
from flask import request, make_response

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AI Smart Cache - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_smart_cache.log'),
        logging.StreamHandler()
    ]
)

class AISmartCache:
    """AI智能缓存类"""
    
    def __init__(self):
        self.cache = {}  # 缓存存储，格式：{cache_key: {data: response_data, timestamp: timestamp, ttl: ttl}}
        self.cache_stats = {}  # 缓存统计，格式：{cache_key: {hit_count: int, miss_count: int, avg_processing_time: float}}
        self.request_history = {}  # 请求历史，格式：{cache_key: [timestamp1, timestamp2, ...]}
        self.response_times = {}  # 响应时间历史，格式：{cache_key: [time1, time2, ...]}
        
        # 智能缓存配置
        self.config = {
            'default_ttl': 300,  # 默认缓存过期时间（秒）
            'max_ttl': 3600,  # 最大缓存过期时间
            'min_ttl': 60,  # 最小缓存过期时间
            'cleanup_interval': 3600,  # 缓存清理间隔（秒）
            'popular_threshold': 10,  # 请求频率阈值，超过该值视为热门请求
            'slow_threshold': 0.5,  # 响应时间阈值（秒），超过该值视为慢请求
            'cacheable_status_codes': [200, 304],  # 可缓存的HTTP状态码
            'cacheable_methods': ['GET', 'HEAD']  # 可缓存的HTTP方法
        }
        
        # 启动缓存清理线程
        self._start_cleanup_thread()
        
        logger.info("AI智能缓存初始化完成")
    
    def _start_cleanup_thread(self):
        """启动缓存清理线程"""
        def cleanup_cache():
            while True:
                time.sleep(self.config['cleanup_interval'])
                self._cleanup_expired_cache()
        
        cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, cache_entry in self.cache.items():
            if current_time - cache_entry['timestamp'] > cache_entry['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def _generate_cache_key(self):
        """生成缓存键"""
        # 基于请求方法、路径和参数生成缓存键
        key_parts = [
            request.method,
            request.path,
            json.dumps(request.args.to_dict(), sort_keys=True),
            json.dumps(request.form.to_dict(), sort_keys=True)
        ]
        
        # 如果是JSON请求，也将请求体加入缓存键
        if request.is_json:
            try:
                json_data = request.get_json()
                if json_data:
                    key_parts.append(json.dumps(json_data, sort_keys=True))
            except Exception as e:
                logger.debug(f"无法解析JSON请求体: {str(e)}")
        
        # 生成MD5哈希作为缓存键
        cache_key = hashlib.md5('|'.join(key_parts).encode('utf-8')).hexdigest()
        return cache_key
    
    def _calculate_dynamic_ttl(self, cache_key: str) -> int:
        """基于AI学习计算动态缓存过期时间
        
        Args:
            cache_key: 缓存键
            
        Returns:
            动态计算的TTL（秒）
        """
        # 如果缓存键不在统计中，使用默认TTL
        if cache_key not in self.cache_stats:
            return self.config['default_ttl']
        
        stats = self.cache_stats[cache_key]
        
        # 计算请求频率（最近5分钟）
        current_time = time.time()
        five_minutes_ago = current_time - 300
        recent_requests = [t for t in self.request_history.get(cache_key, []) if t >= five_minutes_ago]
        request_frequency = len(recent_requests) / 5  # 每分钟请求数
        
        # 计算平均响应时间
        avg_response_time = stats.get('avg_processing_time', 0)
        
        # 基于请求频率和响应时间计算动态TTL
        ttl = self.config['default_ttl']
        
        # 如果是热门请求，增加TTL
        if request_frequency > self.config['popular_threshold']:
            ttl += int(ttl * 0.5)  # 增加50%
        
        # 如果是慢请求，增加TTL
        if avg_response_time > self.config['slow_threshold']:
            ttl += int(ttl * 0.3)  # 增加30%
        
        # 如果是冷门请求，减少TTL
        if request_frequency < 1:
            ttl = max(self.config['min_ttl'], int(ttl * 0.5))  # 减少50%
        
        # 确保TTL在合理范围内
        ttl = max(self.config['min_ttl'], min(self.config['max_ttl'], ttl))
        
        logger.debug(f"缓存键 {cache_key} 动态TTL计算: 请求频率={request_frequency:.2f} 次/分钟, 平均响应时间={avg_response_time:.4f} 秒, TTL={ttl} 秒")
        
        return ttl
    
    def _update_cache_stats(self, cache_key: str, is_hit: bool, processing_time: float):
        """更新缓存统计信息"""
        # 更新请求历史
        if cache_key not in self.request_history:
            self.request_history[cache_key] = []
        self.request_history[cache_key].append(time.time())
        
        # 只保留最近100个请求时间
        if len(self.request_history[cache_key]) > 100:
            self.request_history[cache_key] = self.request_history[cache_key][-100:]
        
        # 更新响应时间历史
        if cache_key not in self.response_times:
            self.response_times[cache_key] = []
        self.response_times[cache_key].append(processing_time)
        
        # 只保留最近100个响应时间
        if len(self.response_times[cache_key]) > 100:
            self.response_times[cache_key] = self.response_times[cache_key][-100:]
        
        # 更新缓存统计
        if cache_key not in self.cache_stats:
            self.cache_stats[cache_key] = {
                'hit_count': 0,
                'miss_count': 0,
                'avg_processing_time': processing_time
            }
        
        if is_hit:
            self.cache_stats[cache_key]['hit_count'] += 1
        else:
            self.cache_stats[cache_key]['miss_count'] += 1
        
        # 更新平均处理时间
        total_processing_time = sum(self.response_times[cache_key])
        self.cache_stats[cache_key]['avg_processing_time'] = total_processing_time / len(self.response_times[cache_key])
    
    def smart_cache_middleware(self, app):
        """智能缓存中间件"""
        @app.before_request
        def before_request():
            # 只缓存GET和HEAD请求
            if request.method not in self.config['cacheable_methods']:
                return
            
            # 生成缓存键
            cache_key = self._generate_cache_key()
            request.cache_key = cache_key
            request.cache_hit = False
            request.processing_start_time = time.time()
            
            # 检查缓存
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                current_time = time.time()
                
                # 检查缓存是否过期
                if current_time - cache_entry['timestamp'] <= cache_entry['ttl']:
                    # 缓存命中
                    logger.debug(f"缓存命中: {cache_key}")
                    request.cache_hit = True
                    
                    # 更新缓存统计
                    processing_time = time.time() - request.processing_start_time
                    self._update_cache_stats(cache_key, True, processing_time)
                    
                    # 返回缓存的响应
                    response = make_response(cache_entry['data']['body'])
                    response.status_code = cache_entry['data']['status_code']
                    response.headers = cache_entry['data']['headers']
                    response.headers['X-Cache'] = 'HIT'
                    response.headers['X-Cache-TTL'] = str(int(cache_entry['ttl'] - (current_time - cache_entry['timestamp'])))
                    return response
        
        @app.after_request
        def after_request(response):
            # 跳过非GET/HEAD请求
            if request.method not in self.config['cacheable_methods']:
                return response
            
            # 跳过不可缓存的状态码
            if response.status_code not in self.config['cacheable_status_codes']:
                return response
            
            cache_key = getattr(request, 'cache_key', None)
            if not cache_key:
                return response
            
            # 计算处理时间
            processing_time = time.time() - getattr(request, 'processing_start_time', time.time())
            
            # 更新缓存统计（未命中）
            if not getattr(request, 'cache_hit', False):
                self._update_cache_stats(cache_key, False, processing_time)
                
                # 缓存响应
                cache_entry = {
                    'data': {
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'body': response.get_data()
                    },
                    'timestamp': time.time(),
                    'ttl': self._calculate_dynamic_ttl(cache_key)
                }
                
                self.cache[cache_key] = cache_entry
                logger.debug(f"缓存更新: {cache_key}, TTL: {cache_entry['ttl']} 秒")
                
                response.headers['X-Cache'] = 'MISS'
                response.headers['X-Cache-TTL'] = str(cache_entry['ttl'])
            
            return response
        
        logger.info("AI智能缓存中间件注册完成")
        return app
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        # 计算总体缓存命中率
        total_hits = sum(stats['hit_count'] for stats in self.cache_stats.values())
        total_misses = sum(stats['miss_count'] for stats in self.cache_stats.values())
        total_requests = total_hits + total_misses
        hit_ratio = total_hits / total_requests if total_requests > 0 else 0
        
        return {
            'total_cache_size': len(self.cache),
            'total_requests': total_requests,
            'hits': total_hits,
            'misses': total_misses,
            'hit_ratio': hit_ratio,
            'cache_stats': self.cache_stats
        }
    
    def clear_cache(self, cache_key: Optional[str] = None):
        """清除缓存
        
        Args:
            cache_key: 可选，指定要清除的缓存键，不指定则清除所有缓存
        """
        if cache_key:
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.info(f"清除缓存: {cache_key}")
        else:
            self.cache.clear()
            logger.info("清除所有缓存")

# 导入threading模块
import threading

# 创建全局AI智能缓存实例
ai_smart_cache = AISmartCache()


def ai_smart_cache_middleware(app):
    """AI智能缓存中间件"""
    return ai_smart_cache.smart_cache_middleware(app)

# 优先级配置
ai_smart_cache_priority = 15
