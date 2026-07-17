#!/usr/bin/env python3
"""
AI自学习与系统升级API
提供自学习管理、技能进化、智能决策、神经网络训练等功能
"""

import os
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

ai_self_learning_api = Blueprint('ai_self_learning_api', __name__)


def _get_self_learning_system():
    try:
        from app.ai.ai_self_learning import ai_self_learning_system
        return ai_self_learning_system
    except Exception as e:
        return None


def _get_skill_evolution():
    try:
        from app.ai.ai_skill_evolution import skill_evolution_system
        return skill_evolution_system
    except Exception as e:
        return None


def _get_orchestrator():
    try:
        from app.ai.ai_orchestrator import ai_orchestrator
        return ai_orchestrator
    except Exception as e:
        return None


@ai_self_learning_api.route('/api/ai/selflearning/status', methods=['GET'])
@require_admin
def get_self_learning_status():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    return jsonify({
        'success': True,
        'data': {
            'is_learning': system.is_learning,
            'learning_rate': system.learning_rate,
            'knowledge_base_size': system.knowledge_base_size,
            'learning_cycles': system.learning_cycles,
            'last_learning_time': system.last_learning_time,
            'model_version': system.model_version
        },
        'timestamp': datetime.now().isoformat()
    })


@ai_self_learning_api.route('/api/ai/selflearning/start', methods=['POST'])
@require_admin
def start_self_learning():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    data = request.get_json() or {}
    learning_type = data.get('learning_type', 'auto')
    duration = data.get('duration', 3600)
    
    try:
        result = system.start_learning(learning_type=learning_type, duration=duration)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/selflearning/stop', methods=['POST'])
@require_admin
def stop_self_learning():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    try:
        result = system.stop_learning()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/selflearning/pause', methods=['POST'])
@require_admin
def pause_self_learning():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    try:
        result = system.pause_learning()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/selflearning/resume', methods=['POST'])
@require_admin
def resume_self_learning():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    try:
        result = system.resume_learning()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/selflearning/progress', methods=['GET'])
@require_admin
def get_learning_progress():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    progress = system.get_learning_progress()
    return jsonify({'success': True, 'data': progress, 'timestamp': datetime.now().isoformat()})


@ai_self_learning_api.route('/api/ai/selflearning/train', methods=['POST'])
@require_admin
def train_model():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    data = request.get_json() or {}
    epochs = data.get('epochs', 10)
    batch_size = data.get('batch_size', 32)
    learning_rate = data.get('learning_rate', 0.001)
    
    try:
        result = system.train_model(epochs=epochs, batch_size=batch_size, learning_rate=learning_rate)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/selflearning/evaluate', methods=['POST'])
@require_admin
def evaluate_model():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    try:
        metrics = system.evaluate_model()
        return jsonify({'success': True, 'data': metrics, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/selflearning/knowledge', methods=['POST'])
@require_admin
def add_learning_knowledge():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    data = request.get_json() or {}
    knowledge = data.get('knowledge')
    
    if not knowledge:
        return jsonify({'success': False, 'error': '知识内容不能为空'}), 400
    
    try:
        result = system.add_knowledge(knowledge)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/selflearning/knowledge/batch', methods=['POST'])
@require_admin
def batch_add_knowledge():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    data = request.get_json() or {}
    knowledge_items = data.get('items', [])
    
    if not knowledge_items:
        return jsonify({'success': False, 'error': '知识列表不能为空'}), 400
    
    try:
        results = []
        for item in knowledge_items:
            result = system.add_knowledge(item)
            results.append(result)
        
        success_count = sum(1 for r in results if r.get('success'))
        return jsonify({
            'success': success_count == len(results),
            'total': len(results),
            'success_count': success_count,
            'failed_count': len(results) - success_count,
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/selflearning/stats', methods=['GET'])
@require_admin
def get_learning_stats():
    system = _get_self_learning_system()
    if not system:
        return jsonify({'success': False, 'error': '自学习系统不可用'}), 503
    
    stats = system.get_statistics()
    return jsonify({'success': True, 'data': stats, 'timestamp': datetime.now().isoformat()})


@ai_self_learning_api.route('/api/ai/skill/evolution/status', methods=['GET'])
@require_admin
def get_skill_evolution_status():
    system = _get_skill_evolution()
    if not system:
        return jsonify({'success': False, 'error': '技能进化系统不可用'}), 503
    
    return jsonify({
        'success': True,
        'data': {
            'active_skills': system.active_skills,
            'evolving_skills': system.evolving_skills,
            'skill_count': system.skill_count,
            'evolution_cycles': system.evolution_cycles
        },
        'timestamp': datetime.now().isoformat()
    })


@ai_self_learning_api.route('/api/ai/skill/evolution/start', methods=['POST'])
@require_admin
def start_skill_evolution():
    system = _get_skill_evolution()
    if not system:
        return jsonify({'success': False, 'error': '技能进化系统不可用'}), 503
    
    data = request.get_json() or {}
    skill_name = data.get('skill_name')
    
    try:
        if skill_name:
            result = system.evolve_skill(skill_name)
        else:
            result = system.evolve_all_skills()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/skill/evolution/list', methods=['GET'])
@require_admin
def list_skills():
    system = _get_skill_evolution()
    if not system:
        return jsonify({'success': False, 'error': '技能进化系统不可用'}), 503
    
    skills = system.list_skills()
    return jsonify({'success': True, 'data': skills, 'timestamp': datetime.now().isoformat()})


@ai_self_learning_api.route('/api/ai/skill/evolution/<skill_name>', methods=['GET'])
@require_admin
def get_skill_detail(skill_name):
    system = _get_skill_evolution()
    if not system:
        return jsonify({'success': False, 'error': '技能进化系统不可用'}), 503
    
    try:
        skill = system.get_skill(skill_name)
        if not skill:
            return jsonify({'success': False, 'error': '技能不存在'}), 404
        return jsonify({'success': True, 'data': skill, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/orchestrator/status', methods=['GET'])
@require_admin
def get_orchestrator_status():
    orchestrator = _get_orchestrator()
    if not orchestrator:
        return jsonify({'success': False, 'error': 'AI编排器不可用'}), 503
    
    return jsonify({
        'success': True,
        'data': {
            'is_running': orchestrator.is_running,
            'active_tasks': orchestrator.active_tasks,
            'completed_tasks': orchestrator.completed_tasks,
            'failed_tasks': orchestrator.failed_tasks,
            'pending_tasks': orchestrator.pending_tasks
        },
        'timestamp': datetime.now().isoformat()
    })


@ai_self_learning_api.route('/api/ai/orchestrator/task', methods=['POST'])
@require_admin
def submit_orchestrator_task():
    orchestrator = _get_orchestrator()
    if not orchestrator:
        return jsonify({'success': False, 'error': 'AI编排器不可用'}), 503
    
    data = request.get_json() or {}
    task_type = data.get('task_type')
    task_data = data.get('task_data', {})
    
    if not task_type:
        return jsonify({'success': False, 'error': 'task_type不能为空'}), 400
    
    try:
        result = orchestrator.submit_task(task_type, task_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/orchestrator/tasks', methods=['GET'])
@require_admin
def list_orchestrator_tasks():
    orchestrator = _get_orchestrator()
    if not orchestrator:
        return jsonify({'success': False, 'error': 'AI编排器不可用'}), 503
    
    try:
        tasks = orchestrator.list_tasks()
        return jsonify({'success': True, 'data': tasks, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/orchestrator/task/<task_id>', methods=['GET'])
@require_admin
def get_orchestrator_task(task_id):
    orchestrator = _get_orchestrator()
    if not orchestrator:
        return jsonify({'success': False, 'error': 'AI编排器不可用'}), 503
    
    try:
        task = orchestrator.get_task(task_id)
        if not task:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        return jsonify({'success': True, 'data': task, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/system/upgrade/check', methods=['GET'])
@require_admin
def check_system_upgrade():
    try:
        from ai_engines.system_upgrade_manager import system_upgrade_manager
        result = system_upgrade_manager.check_for_updates()
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/system/upgrade/execute', methods=['POST'])
@require_admin
def execute_system_upgrade():
    try:
        from ai_engines.system_upgrade_manager import system_upgrade_manager
        data = request.get_json() or {}
        upgrade_type = data.get('upgrade_type', 'full')
        
        result = system_upgrade_manager.execute_upgrade(upgrade_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/system/upgrade/history', methods=['GET'])
@require_admin
def get_upgrade_history():
    try:
        from ai_engines.system_upgrade_manager import system_upgrade_manager
        history = system_upgrade_manager.get_upgrade_history()
        return jsonify({'success': True, 'data': history, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_self_learning_api.route('/api/ai/system/health', methods=['GET'])
@require_admin
def system_health_check():
    self_learning_ok = _get_self_learning_system() is not None
    skill_evolution_ok = _get_skill_evolution() is not None
    orchestrator_ok = _get_orchestrator() is not None
    
    overall_health = 'healthy' if all([self_learning_ok, skill_evolution_ok, orchestrator_ok]) else 'warning'
    
    return jsonify({
        'success': True,
        'overall_health': overall_health,
        'data': {
            'self_learning_system': 'running' if self_learning_ok else 'unavailable',
            'skill_evolution_system': 'running' if skill_evolution_ok else 'unavailable',
            'orchestrator': 'running' if orchestrator_ok else 'unavailable'
        },
        'timestamp': datetime.now().isoformat()
    })