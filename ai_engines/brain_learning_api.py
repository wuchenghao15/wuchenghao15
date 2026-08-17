# -*- coding: utf-8 -*-
"""AI脑库学习API - 从脑库自动学习升级"""
from flask import Blueprint, request, jsonify
from app.ai.brain_based_learning import brain_based_learning_system
import json
import sys

brain_learning_api = Blueprint('brain_learning_api', __name__)

@brain_learning_api.route('/api/ai/brain/connect', methods=['POST'])
def connect_to_brain():
    """连接到AI脑库"""
    result = brain_based_learning_system.connect_to_brain()
    if result['success']:
        return jsonify(result)
    return jsonify(result), 500

@brain_learning_api.route('/api/ai/brain/status', methods=['GET'])
def get_brain_status():
    """获取脑库状态"""
    status = brain_based_learning_system.get_brain_status()
    return jsonify({'success': True, 'data': status})

@brain_learning_api.route('/api/ai/brain/learn', methods=['POST'])
def learn_from_brain():
    """从脑库学习"""
    data = request.get_json() or {}
    component_id = data.get('component_id')
    
    if component_id:
        result = brain_based_learning_system.learn_from_brain(component_id)
    else:
        # 学习所有组件
        results = []
        components = list(brain_based_learning_system.component_knowledge_mapping.keys())
        for comp_id in components:
            result = brain_based_learning_system.learn_from_brain(comp_id)
            results.append(result)
        result = {'success': True, 'message': '所有组件学习完成', 'results': results}
    
    return jsonify(result)

@brain_learning_api.route('/api/ai/brain/upgrade', methods=['POST'])
def upgrade_from_brain():
    """从脑库升级"""
    data = request.get_json() or {}
    component_id = data.get('component_id')
    
    if component_id:
        result = brain_based_learning_system.upgrade_from_brain(component_id)
    else:
        result = brain_based_learning_system.auto_learn_and_upgrade_all()
    
    return jsonify(result)

@brain_learning_api.route('/api/ai/brain/upgrade/all', methods=['POST'])
def upgrade_all_from_brain():
    """一键升级所有AI组件从脑库学习"""
    result = brain_based_learning_system.auto_learn_and_upgrade_all()
    return jsonify(result)

@brain_learning_api.route('/api/ai/brain/progress', methods=['GET'])
def get_learning_progress():
    """获取学习进度"""
    progress = brain_based_learning_system.get_learning_progress()
    return jsonify({'success': True, 'data': progress})

@brain_learning_api.route('/api/ai/brain/sync/start', methods=['POST'])
def start_auto_sync():
    """启动脑库自动同步"""
    result = brain_based_learning_system.start_auto_sync()
    return jsonify(result)

@brain_learning_api.route('/api/ai/brain/sync/stop', methods=['POST'])
def stop_auto_sync():
    """停止脑库自动同步"""
    result = brain_based_learning_system.stop_auto_sync()
    return jsonify(result)

@brain_learning_api.route('/api/ai/brain/config', methods=['GET'])
def get_config():
    """获取脑库学习配置"""
    return jsonify({'success': True, 'data': brain_based_learning_system.config})

@brain_learning_api.route('/api/ai/brain/config', methods=['PUT'])
def update_config():
    """更新脑库学习配置"""
    data = request.get_json() or {}
    brain_based_learning_system.config.update(data)
    return jsonify({'success': True, 'message': '配置更新成功', 'config': brain_based_learning_system.config})
