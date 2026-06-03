# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
优化的前后端交互API - 包含缓存机制
"""

from flask import Blueprint, request, jsonify
import time
import json

# 创建蓝图
optimized_api = Blueprint('optimized_api', __name__)

# 内存缓存装饰器,用于降低服务器运算
def cache_with_expiry(seconds):
    """带过期时间的缓存装饰器"""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(kwargs)
            now = time.time()

            # 检查缓存是否存在且未过期
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < seconds:
                    return result

            # 缓存不存在或已过期,重新计算
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator


@optimized_api.route('/api/optimized/data', methods=['GET'])
@cache_with_expiry(30)  # 缓存30秒
def get_optimized_data():
    """获取优化后的数据 - 包含缓存机制"""
    # 模拟耗时运算
    time.sleep(0.5)

    return jsonify({
        'status': 'success',
        'message': '优化的数据获取',
        'timestamp': time.time(),
        'data': {
            'optimized': True,
            'cached': True,
            'version': '2.0.0',
            'features': ['缓存机制', '优化的前后端交互', '降低服务器运算', '错误处理']
        }
    })


@optimized_api.route('/api/optimized/calculation', methods=['POST'])
@cache_with_expiry(60)  # 缓存60秒
def optimized_calculation():
    """优化的计算API - 包含请求验证"""
    try:
        # 获取请求数据
        data = request.get_json()

        # 请求验证
        if not data or 'numbers' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少numbers参数'
            }), 400

        numbers = data['numbers']

        # 数据类型验证
        if not isinstance(numbers, list):
            return jsonify({
                'status': 'error',
                'message': 'numbers必须是列表'
            }), 400

        time.sleep(1)

        result = {
            'sum': sum(numbers),
            'average': sum(numbers) / len(numbers) if numbers else 0,
            'max': max(numbers) if numbers else 0,
            'min': min(numbers) if numbers else 0,
            'count': len(numbers)
        }

        return jsonify({
            'status': 'success',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'计算失败: {str(e)}'
        }), 500


@optimized_api.route('/api/optimized/health', methods=['GET'])
def health_check():
    """健康检查API - 轻量级,无耗时操作"""
    return jsonify({
        'status': 'success',
        'version': '2.0.0'
    })


@optimized_api.route('/api/optimized/version', methods=['GET'])
def get_version():
    """获取版本信息 - 静态数据,快速响应"""
    return jsonify({
        'status': 'success',
        'version': '2.0.0',
        'features': [
            '前后端交互优化',
            '缓存机制',
            '降低服务器运算',
            '统一错误处理',
            '请求验证',
        ]
    })
