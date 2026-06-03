# -*- coding: utf-8 -*-
"""自动计划调度API - AI驱动的任务调度系统"""
from flask import Blueprint, request, jsonify
from app.ai.auto_scheduler import auto_scheduler
import json

scheduler_api = Blueprint('scheduler_api', __name__)

@scheduler_api.route('/api/scheduler/tasks', methods=['GET'])
def get_tasks():
    """获取所有计划任务"""
    tasks = auto_scheduler.get_tasks()
    return jsonify({'success': True, 'data': tasks})

@scheduler_api.route('/api/scheduler/tasks', methods=['POST'])
def add_task():
    """添加计划任务"""
    data = request.get_json()
    
    task_id = data.get('task_id')
    task_config = data.get('config', {})
    
    if not task_id:
        return jsonify({'success': False, 'message': '缺少task_id'}), 400
    
    result = auto_scheduler.add_task(task_id, task_config)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400

@scheduler_api.route('/api/scheduler/tasks/<task_id>', methods=['DELETE'])
def remove_task(task_id):
    """移除计划任务"""
    result = auto_scheduler.remove_task(task_id)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 404

@scheduler_api.route('/api/scheduler/tasks/<task_id>/run', methods=['POST'])
def run_task_now(task_id):
    """立即执行任务"""
    result = auto_scheduler.run_task_now(task_id)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 404

@scheduler_api.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """启动调度器"""
    result = auto_scheduler.start_scheduler()
    return jsonify(result)

@scheduler_api.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """停止调度器"""
    result = auto_scheduler.stop_scheduler()
    return jsonify(result)

@scheduler_api.route('/api/scheduler/status', methods=['GET'])
def get_status():
    """获取调度器状态"""
    return jsonify({
        'success': True,
        'data': {
            'is_running': auto_scheduler.is_running,
            'task_count': len(auto_scheduler.scheduled_tasks),
            'history_count': len(auto_scheduler.task_history)
        }
    })

@scheduler_api.route('/api/scheduler/history', methods=['GET'])
def get_history():
    """获取任务执行历史"""
    limit = int(request.args.get('limit', 50))
    history = auto_scheduler.get_task_history(limit)
    return jsonify({'success': True, 'data': history})

@scheduler_api.route('/api/scheduler/defaults', methods=['POST'])
def load_defaults():
    """加载默认任务模板"""
    result = auto_scheduler.load_default_tasks()
    return jsonify(result)

@scheduler_api.route('/api/scheduler/templates', methods=['GET'])
def get_templates():
    """获取任务模板"""
    templates = auto_scheduler.task_templates
    return jsonify({'success': True, 'data': templates})

@scheduler_api.route('/api/scheduler/ai/predict', methods=['POST'])
def ai_predict():
    """AI预测任务负载"""
    result = auto_scheduler.ai_predict_task_load()
    return jsonify(result)

@scheduler_api.route('/api/scheduler/ai/optimize', methods=['POST'])
def ai_optimize():
    """AI优化任务调度"""
    result = auto_scheduler.ai_optimize_schedule()
    return jsonify(result)

@scheduler_api.route('/api/scheduler/config', methods=['GET'])
def get_config():
    """获取调度器配置"""
    return jsonify({'success': True, 'data': auto_scheduler.config})

@scheduler_api.route('/api/scheduler/config', methods=['PUT'])
def update_config():
    """更新调度器配置"""
    data = request.get_json() or {}
    auto_scheduler.config.update(data)
    return jsonify({'success': True, 'message': '配置更新成功', 'config': auto_scheduler.config})
