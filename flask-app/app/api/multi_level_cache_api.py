# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多级缓存管理API - 提供缓存管理和监控接口
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime

multi_level_cache_api = Blueprint('multi_level_cache_api', __name__)

# 全局缓存实例
cache_instance = None

def init_cache():
    """初始化缓存"""
    global cache_instance
    if cache_instance is None:
        from app.utils.multi_level_cache import get_multi_level_cache
        cache_instance = get_multi_level_cache()
    return cache_instance

def get_cache():
    """获取缓存实例"""
    if cache_instance is None:
        return init_cache()
    return cache_instance

@multi_level_cache_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'multi-level-cache-api'})

@multi_level_cache_api.route('/stats')
def stats():
    """获取缓存统计信息"""
    cache = get_cache()
    stats = cache.get_stats()
    return jsonify(stats)

@multi_level_cache_api.route('/get/<key>')
def get_cache_item(key):
    """获取缓存项"""
    cache = get_cache()
    value = cache.get(key)
    if value is not None:
        return jsonify({'success': True, 'value': value})
    return jsonify({'success': False, 'error': '缓存不存在或已过期'}), 404

@multi_level_cache_api.route('/set', methods=['POST'])
def set_cache_item():
    """设置缓存项"""
    cache = get_cache()
    data = request.get_json()
    
    if not data or 'key' not in data or 'value' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    key = data['key']
    value = data['value']
    ttl = data.get('ttl')
    
    cache.set(key, value, ttl)
    return jsonify({'success': True, 'message': '缓存设置成功'})

@multi_level_cache_api.route('/delete/<key>', methods=['DELETE'])
def delete_cache_item(key):
    """删除缓存项"""
    cache = get_cache()
    cache.delete(key)
    return jsonify({'success': True, 'message': '缓存删除成功'})

@multi_level_cache_api.route('/clear')
def clear_cache():
    """清空缓存"""
    cache = get_cache()
    level = request.args.get('level')
    
    if level:
        from app.utils.multi_level_cache import CacheLevel
        try:
            cache_level = CacheLevel(level.lower())
            cache.clear(cache_level)
            return jsonify({'success': True, 'message': f'{level} 缓存已清空'})
        except ValueError:
            return jsonify({'error': f'无效的缓存级别: {level}'}), 400
    else:
        cache.clear()
        return jsonify({'success': True, 'message': '所有缓存已清空'})

@multi_level_cache_api.route('/health')
def health():
    """健康检查"""
    cache = get_cache()
    stats = cache.get_stats()
    return jsonify({
        'status': 'healthy',
        'l1_enabled': True,
        'l2_enabled': True,
        'l3_enabled': True,
        'timestamp': datetime.now().isoformat()
    })

@multi_level_cache_api.route('/config')
def get_config():
    """获取缓存配置"""
    cache = get_cache()
    return jsonify({
        'l1_max_size': cache.config['l1_max_size'],
        'l1_ttl': cache.config['l1_ttl'],
        'l1_policy': cache.config['l1_policy'],
        'l2_max_size': cache.config['l2_max_size'],
        'l2_ttl': cache.config['l2_ttl'],
        'l3_ttl': cache.config['l3_ttl'],
        'auto_promote': cache.config['auto_promote'],
        'auto_demote': cache.config['auto_demote']
    })

@multi_level_cache_api.route('/test')
def test_cache():
    """测试缓存功能"""
    cache = get_cache()
    
    # 设置测试缓存
    test_key = 'test_api_key'
    test_value = {'test': 'data', 'timestamp': datetime.now().isoformat()}
    
    # 设置缓存
    cache.set(test_key, test_value, ttl=300)
    
    # 获取缓存
    result = cache.get(test_key)
    
    # 统计信息
    stats = cache.get_stats()
    
    return jsonify({
        'success': True,
        'set_value': test_value,
        'get_value': result,
        'match': test_value == result,
        'stats': stats
    })

@multi_level_cache_api.route('/levels')
def get_levels():
    """获取缓存级别信息"""
    from app.utils.multi_level_cache import CacheLevel
    levels = {
        CacheLevel.L1.value: {
            'name': 'L1',
            'description': '内存缓存 - 最快,容量小',
            'ttl': '5分钟',
            'max_size': '1000条'
        },
        CacheLevel.L2.value: {
            'name': 'L2',
            'description': '文件缓存 - 中等速度,容量较大',
            'ttl': '1小时',
            'max_size': '100MB'
        },
        CacheLevel.L3.value: {
            'name': 'L3',
            'description': '数据库缓存 - 持久化,容量大',
            'ttl': '24小时',
            'max_size': '无限制'
        }
    }
    return jsonify(levels)
