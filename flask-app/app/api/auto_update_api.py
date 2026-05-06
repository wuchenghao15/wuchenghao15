#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动更新管理器API蓝图，提供自动更新功能的RESTful API接口

from flask import Blueprint, jsonify, request
from app.ai.auto_update_manager import ai_auto_update_manager

# 创建API蓝图
auto_update_api_bp = Blueprint('auto_update_api', __name__)


@auto_update_api_bp.route('/status', methods=['GET'])
def get_status():
    """获取AI自动更新管理器状态"""
    try:
        status = ai_auto_update_manager.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取状态失败: {str(e)}'
        }), 500


@auto_update_api_bp.route('/config', methods=['GET'])
def get_config():
    """获取AI自动更新管理器配置"""
    try:
        return jsonify({
            'data': status['config']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取配置失败: {str(e)}'
        }), 500


@auto_update_api_bp.route('/config', methods=['PUT'])
def update_config():
    """更新AI自动更新管理器配置"""
    try:
        if not isinstance(new_config, dict):
            return jsonify({
                'success': False,
                'error': '配置必须是JSON对象'
            }), 400

        ai_auto_update_manager.update_config(new_config)
        return jsonify({
            'success': True,
            'message': '配置更新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'更新配置失败: {str(e)}'
        }), 500


@auto_update_api_bp.route('/start', methods=['POST'])
def start_manager():
    """启动AI自动更新管理器"""
    try:
        return jsonify({
            'success': True,
            'message': 'AI自动更新管理器已启动'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'启动管理器失败: {str(e)}'
        }), 500


@auto_update_api_bp.route('/stop', methods=['POST'])
def stop_manager():
    """停止AI自动更新管理器"""
    try:
        return jsonify({
            'success': True,
            'message': 'AI自动更新管理器已停止'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'停止管理器失败: {str(e)}'
        }), 500


@auto_update_api_bp.route('/restart', methods=['POST'])
def restart_manager():
    """重启AI自动更新管理器"""
    try:
        ai_auto_update_manager.start()
        return jsonify({
            'success': True,
            'message': 'AI自动更新管理器已重启'
        })
    except Exception as e:
            'error': f'重启管理器失败: {str(e)}'
        }), 500


@auto_update_api_bp.route('/trigger-update', methods=['POST'])
def trigger_update():
    """触发手动更新

    Request Body:
    {
        "update_type": "route_rules"  # 可选，更新类型
    }
    try:
        data = request.json or {}

        ai_auto_update_manager.trigger_update(update_type)
        return jsonify({
            'success': True,
            'message': f'手动更新已触发，类型: {update_type}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'触发手动更新失败: {str(e)}'
        }), 500


@auto_update_api_bp.route('/update-types', methods=['GET'])
def get_update_types():
    """获取支持的更新类型"""
    try:
        status = ai_auto_update_manager.get_status()
            'success': True,
            'data': status['config']['update_types']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取更新类型失败: {str(e)}'


@auto_update_api_bp.route('/enable-update-type', methods=['POST'])
def enable_update_type():
    """启用特定类型的更新

    Request Body:
    {
        "update_type": "route_rules"
    }
    try:
        data = request.json
        if not data or 'update_type' not in data:
                'success': False,
                'error': '请求体必须包含update_type字段'
            }), 400

        update_type = data['update_type']
        config = ai_auto_update_manager.get_status()['config']
        if update_type not in config['update_types']:
                'success': False,
                'error': f'不支持的更新类型: {update_type}'
            }), 400

        new_config = {
            'update_types': {
                update_type: True
            }
        }
        ai_auto_update_manager.update_config(new_config)

        return jsonify({
            'success': True,
            'message': f'已启用 {update_type} 类型的更新'
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'启用更新类型失败: {str(e)}'
        }), 500


@auto_update_api_bp.route('/disable-update-type', methods=['POST'])
def disable_update_type():
    """禁用特定类型的更新

    Request Body:
    {
        "update_type": "route_rules"
    }
    try:
        data = request.json
        if not data or 'update_type' not in data:
            return jsonify({
                'error': '请求体必须包含update_type字段'
            }), 400

        update_type = data['update_type']
        config = ai_auto_update_manager.get_status()['config']

        if update_type not in config['update_types']:
            return jsonify({
                'success': False,
            }), 400

            'update_types': {
                **config['update_types'],
        }
        ai_auto_update_manager.update_config(new_config)

        return jsonify({
            'message': f'已禁用 {update_type} 类型的更新'
    except Exception as e:
            'success': False,
            'error': f'禁用更新类型失败: {str(e)}'
