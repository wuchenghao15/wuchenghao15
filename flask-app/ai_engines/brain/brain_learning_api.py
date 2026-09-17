# -*- coding: utf-8 -*-
r"""AI脑库学习API - 从脑库自动学习升级r"""
from flask import Blueprint, request, jsonify
from app.middlewares.system_container import system_container
from app.ai.brain_based_learning import brain_based_learning_system
import json
import sys

brain_learning_api = Blueprint(r'brain_learning_api', __name__)

@system_container(require_auth='admin')
@brain_learning_api.route(r'/api/ai/brain/connect', methods=[r'POST'])
@system_container(require_auth='admin')
def connect_to_brain():
    r"""连接到AI脑库r"""
    result = brain_based_learning_system.connect_to_brain()
    if result[r'success']:
        return jsonify(result)
    return jsonify(result), 500

@brain_learning_api.route(r'/api/ai/brain/status', methods=[r'GET'])
@system_container(require_auth='admin')
def get_brain_status():
    r"""获取脑库状态r"""
    status = brain_based_learning_system.get_brain_status()
    return jsonify({r'success': True, r'data': status})

@brain_learning_api.route(r'/api/ai/brain/learn', methods=[r'POST'])
@system_container(require_auth='admin')
def learn_from_brain():
    r"""从脑库学习r"""
    data = request.get_json() or {}
    component_id = data.get(r'component_id')

    if component_id:
        result = brain_based_learning_system.learn_from_brain(component_id)
    else:
        # 学习所有组件
        results = []
        components = list(brain_based_learning_system.component_knowledge_mapping.keys())
        for comp_id in components:
            result = brain_based_learning_system.learn_from_brain(comp_id)
            results.append(result)
        result = {r'success': True, r'message': r'所有组件学习完成', r'results': results}

    return jsonify(result)

@brain_learning_api.route(r'/api/ai/brain/upgrade', methods=[r'POST'])
@system_container(require_auth='admin')
def upgrade_from_brain():
    r"""从脑库升级r"""
    data = request.get_json() or {}
    component_id = data.get(r'component_id')

    if component_id:
        result = brain_based_learning_system.upgrade_from_brain(component_id)
    else:
        result = brain_based_learning_system.auto_learn_and_upgrade_all()

    return jsonify(result)

@brain_learning_api.route(r'/api/ai/brain/upgrade/all', methods=[r'POST'])
@system_container(require_auth='admin')
def upgrade_all_from_brain():
    r"""一键升级所有AI组件从脑库学习r"""
    result = brain_based_learning_system.auto_learn_and_upgrade_all()
    return jsonify(result)

@brain_learning_api.route(r'/api/ai/brain/progress', methods=[r'GET'])
@system_container(require_auth='admin')
def get_learning_progress():
    r"""获取学习进度r"""
    progress = brain_based_learning_system.get_learning_progress()
    return jsonify({r'success': True, r'data': progress})

@brain_learning_api.route(r'/api/ai/brain/sync/start', methods=[r'POST'])
@system_container(require_auth='admin')
def start_auto_sync():
    r"""启动脑库自动同步r"""
    result = brain_based_learning_system.start_auto_sync()
    return jsonify(result)

@brain_learning_api.route(r'/api/ai/brain/sync/stop', methods=[r'POST'])
@system_container(require_auth='admin')
def stop_auto_sync():
    r"""停止脑库自动同步r"""
    result = brain_based_learning_system.stop_auto_sync()
    return jsonify(result)

@brain_learning_api.route(r'/api/ai/brain/config', methods=[r'GET'])
@system_container(require_auth='admin')
def get_config():
    r"""获取脑库学习配置r"""
    return jsonify({r'success': True, r'data': brain_based_learning_system.config})

@brain_learning_api.route(r'/api/ai/brain/config', methods=[r'PUT'])
@system_container(require_auth='admin')
def update_config():
    r"""更新脑库学习配置r"""
    data = request.get_json() or {}
    brain_based_learning_system.config.update(data)
    return jsonify({r'success': True, r'message': r'配置更新成功', r'config': brain_based_learning_system.config})
