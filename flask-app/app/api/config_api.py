# -*- coding: utf-8 -*-
"""
配置管理API
提供系统配置的读取、写入、删除等操作
"""

from flask import Blueprint, jsonify, request
from app.config import (
    get_config_value,
    update_config,
    delete_config,
    get_all_configs,
    get_all_configs_with_category,
    get_config_category,
    init_database_config,
    refresh_config,
)
from app.services.db_config_manager import db_config_manager

config_api = Blueprint('config_api', __name__)


@config_api.route('/config', methods=['GET'])
def get_all_config():
    """获取所有配置"""
    try:
        configs = get_all_configs()
        return jsonify({
            'success': True,
            'data': configs,
            'count': len(configs)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/grouped', methods=['GET'])
def get_config_grouped():
    """获取所有配置（按分类分组）"""
    try:
        configs = get_all_configs_with_category()
        return jsonify({
            'success': True,
            'data': configs,
            'categories': list(configs.keys())
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/category/<category>', methods=['GET'])
def get_config_by_category(category):
    """获取指定分类的配置"""
    try:
        configs = get_config_category(category)
        return jsonify({
            'success': True,
            'category': category,
            'data': configs,
            'count': len(configs)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/<key>', methods=['GET'])
def get_config(key):
    """获取单个配置项"""
    try:
        value = get_config_value(key)
        if value is None:
            return jsonify({'success': False, 'message': f'配置项 {key} 不存在'}), 404
        return jsonify({
            'success': True,
            'key': key,
            'value': value
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/<key>', methods=['POST'])
def set_config(key):
    """设置单个配置项"""
    try:
        data = request.get_json()
        value = data.get('value')
        category = data.get('category', 'general')
        description = data.get('description', '')
        
        success = update_config(key, value, category, description)
        if success:
            return jsonify({
                'success': True,
                'message': f'配置 {key} 更新成功',
                'key': key,
                'value': value,
                'category': category
            })
        return jsonify({'success': False, 'message': f'配置 {key} 更新失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/<key>', methods=['DELETE'])
def remove_config(key):
    """删除配置项"""
    try:
        success = delete_config(key)
        if success:
            return jsonify({'success': True, 'message': f'配置 {key} 删除成功'})
        return jsonify({'success': False, 'message': f'配置 {key} 删除失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/batch', methods=['POST'])
def batch_set_config():
    """批量设置配置"""
    try:
        data = request.get_json()
        settings = data.get('settings', {})
        category = data.get('category', 'general')
        
        if not settings:
            return jsonify({'success': False, 'message': '配置数据不能为空'}), 400
        
        success = db_config_manager.batch_set(settings, category)
        if success:
            return jsonify({
                'success': True,
                'message': f'成功更新 {len(settings)} 个配置项',
                'updated_keys': list(settings.keys())
            })
        return jsonify({'success': False, 'message': '批量更新失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/init', methods=['POST'])
def init_config():
    """初始化默认配置到数据库"""
    try:
        init_database_config()
        return jsonify({
            'success': True,
            'message': '默认配置已初始化到数据库'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/refresh', methods=['POST'])
def refresh_config_api():
    """刷新配置缓存"""
    try:
        refresh_config()
        return jsonify({
            'success': True,
            'message': '配置已从数据库刷新'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/categories', methods=['GET'])
def get_categories():
    """获取所有配置分类"""
    try:
        categories = db_config_manager.get_categories()
        return jsonify({
            'success': True,
            'data': categories,
            'count': len(categories)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@config_api.route('/config/category/<category>/keys', methods=['GET'])
def get_keys_in_category(category):
    """获取指定分类的所有配置键"""
    try:
        keys = db_config_manager.get_keys_by_category(category)
        return jsonify({
            'success': True,
            'category': category,
            'data': keys,
            'count': len(keys)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
