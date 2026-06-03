#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置存储API接口
"""

from flask import Blueprint, request, jsonify, abort
from app.ai.unified_config_storage import (
    config_storage, ConfigScope, ConfigType, ConfigSource
)

config_api_bp = Blueprint('config_api', __name__, url_prefix='/api/config')


@config_api_bp.route('/', methods=['GET'])
def get_configs():
    """获取配置列表"""
    scope = request.args.get('scope')
    module = request.args.get('module')
    
    scope_enum = None
    if scope:
        try:
            scope_enum = ConfigScope(scope)
        except ValueError:
            return jsonify({'error': '无效的scope参数'}), 400
    
    configs = config_storage.list_configs(scope=scope_enum, module=module)
    
    return jsonify({
        'success': True,
        'data': configs,
        'count': len(configs)
    })


@config_api_bp.route('/<key>', methods=['GET'])
def get_config(key):
    """获取单个配置"""
    config = config_storage.get_config(key)
    
    if not config:
        return jsonify({'error': '配置不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': config.to_dict()
    })


@config_api_bp.route('/<key>/value', methods=['GET'])
def get_config_value(key):
    """获取配置值"""
    default = request.args.get('default')
    
    value = config_storage.get_config_value(key)
    
    if value is None and default is not None:
        return jsonify({'success': True, 'data': default})
    
    return jsonify({
        'success': True,
        'data': value
    })


@config_api_bp.route('/<key>', methods=['PUT'])
def update_config(key):
    """更新配置"""
    data = request.get_json()
    
    if 'value' not in data:
        return jsonify({'error': '缺少value参数'}), 400
    
    success = config_storage.set_config(key, data['value'])
    
    if not success:
        return jsonify({'error': '配置更新失败'}), 500
    
    config = config_storage.get_config(key)
    
    return jsonify({
        'success': True,
        'data': config.to_dict()
    })


@config_api_bp.route('/', methods=['POST'])
def create_config():
    """创建配置"""
    data = request.get_json()
    
    required_fields = ['key', 'name', 'type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少{field}参数'}), 400
    
    try:
        config_type = ConfigType(data['type'])
    except ValueError:
        return jsonify({'error': '无效的type参数'}), 400
    
    kwargs = {}
    if 'scope' in data:
        try:
            kwargs['scope'] = ConfigScope(data['scope'])
        except ValueError:
            return jsonify({'error': '无效的scope参数'}), 400
    
    if 'default_value' in data:
        kwargs['default_value'] = data['default_value']
    if 'description' in data:
        kwargs['description'] = data['description']
    if 'options' in data:
        kwargs['options'] = data['options']
    if 'module' in data:
        kwargs['module'] = data['module']
    if 'component' in data:
        kwargs['component'] = data['component']
    if 'metadata' in data:
        kwargs['metadata'] = data['metadata']
    
    success = config_storage.create_config(data['key'], data['name'], config_type, **kwargs)
    
    if not success:
        return jsonify({'error': '配置创建失败'}), 500
    
    config = config_storage.get_config(data['key'])
    
    return jsonify({
        'success': True,
        'data': config.to_dict()
    }), 201


@config_api_bp.route('/<key>', methods=['DELETE'])
def delete_config(key):
    """删除配置"""
    success = config_storage.delete_config(key)
    
    if not success:
        return jsonify({'error': '配置删除失败'}), 500
    
    return jsonify({'success': True})


@config_api_bp.route('/module/<module>', methods=['GET'])
def get_module_configs(module):
    """获取模块配置"""
    configs = config_storage.get_module_configs(module)
    
    return jsonify({
        'success': True,
        'data': configs
    })


@config_api_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    status = config_storage.get_system_status()
    
    return jsonify({
        'success': True,
        'data': status
    })


@config_api_bp.route('/ai/recommendations', methods=['GET'])
def get_ai_recommendations():
    """获取AI推荐"""
    recommendations = config_storage.get_ai_recommendations()
    
    return jsonify({
        'success': True,
        'data': recommendations
    })


@config_api_bp.route('/ai/apply', methods=['POST'])
def apply_ai_recommendations():
    """应用AI推荐"""
    recommendations = config_storage.apply_ai_recommendations()
    
    return jsonify({
        'success': True,
        'data': recommendations
    })


@config_api_bp.route('/ai/analyze', methods=['GET'])
def analyze_configs():
    """分析配置状态"""
    analysis = config_storage.ai_optimizer.analyze_configs()
    
    return jsonify({
        'success': True,
        'data': analysis
    })


@config_api_bp.route('/batch', methods=['POST'])
def batch_update_configs():
    """批量更新配置"""
    data = request.get_json()
    
    if not isinstance(data, dict):
        return jsonify({'error': '数据格式错误'}), 400
    
    results = {}
    for key, value in data.items():
        success = config_storage.set_config(key, value)
        results[key] = success
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    return jsonify({
        'success': True,
        'data': results,
        'updated': success_count,
        'total': total_count
    })


@config_api_bp.route('/types', methods=['GET'])
def get_config_types():
    """获取配置类型列表"""
    types = {t.value: t.name for t in ConfigType}
    
    return jsonify({
        'success': True,
        'data': types
    })


@config_api_bp.route('/scopes', methods=['GET'])
def get_config_scopes():
    """获取配置作用域列表"""
    scopes = {s.value: s.name for s in ConfigScope}
    
    return jsonify({
        'success': True,
        'data': scopes
    })
