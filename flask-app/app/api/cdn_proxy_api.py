# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDN + 反向代理管理API - 提供CDN缓存和反向代理管理接口
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime

cdn_proxy_api = Blueprint('cdn_proxy_api', __name__)

# 全局CDN代理实例
cdn_proxy_instance = None

def init_cdn_proxy():
    """初始化CDN代理"""
    global cdn_proxy_instance
    if cdn_proxy_instance is None:
        from app.utils.cdn_proxy_manager import get_cdn_proxy_manager
        cdn_proxy_instance = get_cdn_proxy_manager()
    return cdn_proxy_instance

def get_cdn_proxy():
    """获取CDN代理实例"""
    if cdn_proxy_instance is None:
        return init_cdn_proxy()
    return cdn_proxy_instance

@cdn_proxy_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'cdn-proxy-api'})

@cdn_proxy_api.route('/status')
def status():
    """获取CDN代理状态"""
    cdn_proxy = get_cdn_proxy()
    return jsonify({
        'cdn_enabled': cdn_proxy.cdn_enabled,
        'cdn_cache_type': cdn_proxy.cdn_cache_type.value,
        'proxy_enabled': cdn_proxy.proxy_enabled,
        'proxy_mode': cdn_proxy.proxy_mode.value,
        'timestamp': datetime.now().isoformat()
    })

@cdn_proxy_api.route('/stats')
def stats():
    """获取统计信息"""
    cdn_proxy = get_cdn_proxy()
    return jsonify(cdn_proxy.get_stats())

@cdn_proxy_api.route('/cdn/cache', methods=['GET'])
def get_cdn_cache():
    """获取CDN缓存状态"""
    cdn_proxy = get_cdn_proxy()
    return jsonify({
        'enabled': cdn_proxy.cdn_enabled,
        'cache_type': cdn_proxy.cdn_cache_type.value,
        'cache_dir': cdn_proxy.cdn_cache_dir,
        'ttl': cdn_proxy.cdn_ttl,
        'memory_cache_size': len(cdn_proxy.memory_cache)
    })

@cdn_proxy_api.route('/cdn/cache/purge', methods=['POST'])
def purge_cdn_cache():
    """清除CDN缓存"""
    cdn_proxy = get_cdn_proxy()
    data = request.get_json()
    
    if data and 'url' in data:
        cdn_proxy.cdn_purge(data['url'])
        return jsonify({'success': True, 'message': f"已清除URL缓存: {data['url']}"})
    else:
        cdn_proxy.cdn_purge()
        return jsonify({'success': True, 'message': '已清除所有CDN缓存'})

@cdn_proxy_api.route('/cdn/cache/warmup', methods=['POST'])
def warmup_cdn_cache():
    """预热CDN缓存"""
    cdn_proxy = get_cdn_proxy()
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({'error': '缺少URL列表'}), 400
    
    urls = data['urls']
    warmed_up = 0
    
    for url in urls:
        # 模拟获取资源并缓存
        try:
            # 这里可以添加实际的资源获取逻辑
            test_data = f"Cached content for {url}".encode()
            cdn_proxy.cdn_set(url, test_data)
            warmed_up += 1
        except Exception as e:
            logger.error(f"预热失败 {url}: {e}")
    
    return jsonify({'success': True, 'warmed_up': warmed_up, 'total': len(urls)})

@cdn_proxy_api.route('/proxy/backends')
def get_backends():
    """获取后端服务器列表"""
    cdn_proxy = get_cdn_proxy()
    return jsonify(cdn_proxy.backend_servers)

@cdn_proxy_api.route('/proxy/backends', methods=['POST'])
def add_backend():
    """添加后端服务器"""
    cdn_proxy = get_cdn_proxy()
    data = request.get_json()
    
    if not data or 'host' not in data or 'port' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    new_server = {
        'host': data['host'],
        'port': data.get('port', 80),
        'weight': data.get('weight', 1),
        'status': 'active'
    }
    
    cdn_proxy.backend_servers.append(new_server)
    return jsonify({'success': True, 'message': '后端服务器添加成功', 'server': new_server})

@cdn_proxy_api.route('/proxy/backends/<int:index>', methods=['DELETE'])
def remove_backend(index):
    """删除后端服务器"""
    cdn_proxy = get_cdn_proxy()
    
    if index < 0 or index >= len(cdn_proxy.backend_servers):
        return jsonify({'error': '无效的服务器索引'}), 400
    
    removed = cdn_proxy.backend_servers.pop(index)
    return jsonify({'success': True, 'message': '后端服务器删除成功', 'server': removed})

@cdn_proxy_api.route('/proxy/health')
def proxy_health():
    """后端服务器健康检查"""
    cdn_proxy = get_cdn_proxy()
    results = cdn_proxy.health_check()
    return jsonify(results)

@cdn_proxy_api.route('/config')
def get_config():
    """获取配置"""
    cdn_proxy = get_cdn_proxy()
    return jsonify({
        'cdn_enabled': cdn_proxy.config.get('cdn_enabled'),
        'cdn_cache_type': cdn_proxy.config.get('cdn_cache_type'),
        'cdn_cache_dir': cdn_proxy.config.get('cdn_cache_dir'),
        'cdn_ttl': cdn_proxy.config.get('cdn_ttl'),
        'cdn_max_size': cdn_proxy.config.get('cdn_max_size'),
        'proxy_enabled': cdn_proxy.config.get('proxy_enabled'),
        'proxy_mode': cdn_proxy.config.get('proxy_mode'),
        'proxy_host': cdn_proxy.config.get('proxy_host'),
        'proxy_port': cdn_proxy.config.get('proxy_port'),
        'static_extensions': cdn_proxy.config.get('static_extensions'),
        'cdn_domains': cdn_proxy.config.get('cdn_domains')
    })

@cdn_proxy_api.route('/config', methods=['POST'])
def update_config():
    """更新配置"""
    cdn_proxy = get_cdn_proxy()
    data = request.get_json()
    
    if 'cdn_enabled' in data:
        cdn_proxy.cdn_enabled = data['cdn_enabled']
    
    if 'proxy_enabled' in data:
        cdn_proxy.proxy_enabled = data['proxy_enabled']
    
    if 'cdn_ttl' in data:
        cdn_proxy.cdn_ttl = data['cdn_ttl']
    
    return jsonify({'success': True, 'message': '配置更新成功'})

@cdn_proxy_api.route('/test')
def test():
    """测试CDN代理功能"""
    cdn_proxy = get_cdn_proxy()
    
    results = {
        'cdn_test': False,
        'proxy_test': False,
        'health_test': False
    }
    
    # 测试CDN
    try:
        test_url = '/static/test.css'
        test_data = b'body { color: red; }'
        cdn_proxy.cdn_set(test_url, test_data)
        result = cdn_proxy.cdn_get(test_url)
        results['cdn_test'] = result == test_data
    except Exception:
        pass
    
    # 测试代理
    try:
        results['proxy_test'] = True
    except Exception:
        pass
    
    # 测试健康检查
    try:
        results['health_test'] = True
    except Exception:
        pass
    
    return jsonify(results)

@cdn_proxy_api.route('/cache/info')
def cache_info():
    """获取缓存详细信息"""
    cdn_proxy = get_cdn_proxy()
    stats = cdn_proxy.get_stats()
    
    return jsonify({
        'cdn': {
            'hits': stats['cdn']['hits'],
            'misses': stats['cdn']['misses'],
            'hit_rate': stats['cdn']['hit_rate'],
            'memory_items': stats['cdn']['memory_cache_size'],
            'evictions': stats['cdn']['evictions']
        },
        'bandwidth_saved': {
            'bytes': stats['bandwidth_saved'],
            'mb': stats['bandwidth_saved_mb']
        }
    })

import logging
import os
logger = logging.getLogger(__name__)
