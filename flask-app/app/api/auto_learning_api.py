# -*- coding: utf-8 -*-
"""AI自动学习升级API"""
from flask import Blueprint, request, jsonify
try:
    from app.ai.auto_learning_upgrade import ai_auto_learning_system
except ImportError:
    try:
        from ai_engines.auto_learning_upgrade import ai_auto_learning_system
    except ImportError:
        ai_auto_learning_system = None
import json
import sys

auto_learning_api = Blueprint('auto_learning_api', __name__)

@auto_learning_api.route('/api/ai/learning/status', methods=['GET'])
def get_learning_status():
    """获取AI学习状态"""
    status = ai_auto_learning_system.get_learning_status()
    return jsonify({'success': True, 'data': status})

@auto_learning_api.route('/api/ai/learning/components', methods=['GET'])
def get_components():
    """获取所有AI组件状态"""
    components = ai_auto_learning_system.get_component_status()
    return jsonify({'success': True, 'data': components})

@auto_learning_api.route('/api/ai/learning/components/<component_id>', methods=['GET'])
def get_component(component_id):
    """获取单个AI组件状态"""
    component = ai_auto_learning_system.get_component_status(component_id)
    if component:
        return jsonify({'success': True, 'data': component})
    return jsonify({'success': False, 'message': '组件不存在'}), 404

@auto_learning_api.route('/api/ai/learning/start', methods=['POST'])
def start_learning():
    """启动AI自动学习"""
    result = ai_auto_learning_system.start_auto_learning()
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400

@auto_learning_api.route('/api/ai/learning/stop', methods=['POST'])
def stop_learning():
    """停止AI自动学习"""
    result = ai_auto_learning_system.stop_auto_learning()
    return jsonify(result)

@auto_learning_api.route('/api/ai/learning/trigger', methods=['POST'])
def trigger_learning():
    """触发立即学习"""
    data = request.get_json() or {}
    component_id = data.get('component_id')
    
    results = ai_auto_learning_system.trigger_immediate_learning(component_id)
    return jsonify({'success': True, 'message': '学习任务已触发', 'data': results})

@auto_learning_api.route('/api/ai/learning/upgrade', methods=['POST'])
def trigger_upgrade():
    """触发立即升级"""
    data = request.get_json() or {}
    component_id = data.get('component_id')
    
    results = ai_auto_learning_system.trigger_immediate_upgrade(component_id)
    return jsonify({'success': True, 'message': '升级任务已触发', 'data': results})

@auto_learning_api.route('/api/ai/learning/history', methods=['GET'])
def get_history():
    """获取学习升级历史"""
    limit = int(request.args.get('limit', 20))
    history = ai_auto_learning_system.get_upgrade_history(limit)
    return jsonify({'success': True, 'data': history})

@auto_learning_api.route('/api/ai/learning/config', methods=['GET'])
def get_config():
    """获取学习配置"""
    return jsonify({'success': True, 'data': ai_auto_learning_system.learning_config})

@auto_learning_api.route('/api/ai/learning/config', methods=['PUT'])
def update_config():
    """更新学习配置"""
    data = request.get_json() or {}
    result = ai_auto_learning_system.update_config(data)
    return jsonify(result)

@auto_learning_api.route('/api/ai/learning/upgrade/all', methods=['POST'])
def upgrade_all():
    """一键升级所有AI组件"""
    # 先执行学习
    learning_results = ai_auto_learning_system.perform_learning()
    
    # 再执行升级
    upgrade_results = ai_auto_learning_system.perform_upgrade()
    
    return jsonify({
        'success': True,
        'message': '所有AI组件学习和升级完成',
        'learning_results': learning_results,
        'upgrade_results': upgrade_results
    })
