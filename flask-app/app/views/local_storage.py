#!/usr/bin/env python3
"""
本地存储视图，提供替代localStorage的API端点
"""

from flask import Blueprint, request, jsonify, session
from app.models.local_storage import LocalStorage
from app.utils.logging import logger

local_storage_bp = Blueprint('local_storage', __name__)

@local_storage_bp.route('/api/local-storage/set', methods=['POST'])
def set_local_storage():
    """设置本地存储值"""
    try:
        data = request.get_json()
        if not data or 'key' not in data:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        key = data['key']
        value = data.get('value')
        ttl = data.get('ttl')
        
        # 获取当前用户ID（如果已登录）
        user_id = session.get('user_id')
        
        success = LocalStorage.set(key, value, user_id=user_id, ttl=ttl)
        
        if success:
            return jsonify({'success': True, 'message': '存储成功'})
        else:
            return jsonify({'success': False, 'message': '存储失败'}), 500
    except Exception as e:
        logger.error(f"设置本地存储失败: {str(e)}")
        return jsonify({'success': False, 'message': f'存储失败: {str(e)'}), 500

@local_storage_bp.route('/api/local-storage/get/<key>', methods=['GET'])
def get_local_storage(key):
    """获取本地存储值"""
    try:
        # 获取当前用户ID（如果已登录）
        user_id = session.get('user_id')
        
        value = LocalStorage.get(key, user_id=user_id)
        
        return jsonify({'success': True, 'value': value})
    except Exception as e:
        logger.error(f"获取本地存储失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)'}), 500

@local_storage_bp.route('/api/local-storage/remove/<key>', methods=['DELETE'])
def remove_local_storage(key):
    """删除本地存储值"""
    try:
        # 获取当前用户ID（如果已登录）
        user_id = session.get('user_id')
        
        success = LocalStorage.remove(key, user_id=user_id)
        
        if success:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 500
    except Exception as e:
        logger.error(f"删除本地存储失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)'}), 500

@local_storage_bp.route('/api/local-storage/clear', methods=['DELETE'])
def clear_local_storage():
    """清空本地存储值"""
    try:
        # 获取当前用户ID（如果已登录）
        user_id = session.get('user_id')
        
        success = LocalStorage.clear(user_id=user_id)
        
        if success:
            return jsonify({'success': True, 'message': '清空成功'})
        else:
            return jsonify({'success': False, 'message': '清空失败'}), 500
    except Exception as e:
        logger.error(f"清空本地存储失败: {str(e)}")
        return jsonify({'success': False, 'message': f'清空失败: {str(e)'}), 500

@local_storage_bp.route('/api/local-storage/all', methods=['GET'])
def get_all_local_storage():
    """获取所有本地存储值"""
    try:
        # 获取当前用户ID（如果已登录）
        user_id = session.get('user_id')
        
        values = LocalStorage.get_all(user_id=user_id)
        
        return jsonify({'success': True, 'values': values})
    except Exception as e:
        logger.error(f"获取所有本地存储失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)'}), 500
