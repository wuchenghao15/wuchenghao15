#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_intelligent_decision import ai_intelligent_decision

ai_decision_api = Bluelogger.info('ai_decision_api', __name__)

@ai_decision_api.route('/api/ai/decision/generate', methods=['POST'])
@require_login
def generate_decision():
    data = request.get_json() or {}
    decision_type = data.get('decision_type')
    user_id = data.get('user_id')
    input_data = data.get('input_data', {})
    
    if not decision_type:
        return jsonify({'success': False, 'error': '决策类型不能为空'}), 400
    
    result = ai_intelligent_decision.generate_decision(decision_type, user_id, input_data)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_decision_api.route('/api/ai/decision/rule', methods=['POST'])
@require_admin
def add_decision_rule():
    data = request.get_json() or {}
    rule_name = data.get('rule_name')
    decision_type = data.get('decision_type')
    conditions = data.get('conditions', [])
    actions = data.get('actions', [])
    priority = data.get('priority', 1)
    
    if not rule_name or not decision_type:
        return jsonify({'success': False, 'error': '规则名称和决策类型不能为空'}), 400
    
    result = ai_intelligent_decision.add_decision_rule(rule_name, decision_type, conditions, actions, priority)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_decision_api.route('/api/ai/decision/rules', methods=['GET'])
@require_login
def get_decision_rules():
    decision_type = request.args.get('decision_type')
    rules = ai_intelligent_decision.get_decision_rules(decision_type)
    return jsonify({'success': True, 'data': rules})

@ai_decision_api.route('/api/ai/decision/tasks', methods=['GET'])
@require_login
def list_decision_tasks():
    decision_type = request.args.get('type')
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 20))
    
    tasks = ai_intelligent_decision.list_decision_tasks(decision_type, user_id, limit)
    return jsonify({'success': True, 'data': tasks})

@ai_decision_api.route('/api/ai/decision/tasks/<task_id>', methods=['GET'])
@require_login
def get_decision_task(task_id):
    task = ai_intelligent_decision.get_decision_task(task_id)
    if task:
        return jsonify({'success': True, 'data': task})
    return jsonify({'success': False, 'error': '决策任务不存在'}), 404

@ai_decision_api.route('/api/ai/decision/execute/<task_id>', methods=['POST'])
@require_login
def execute_decision(task_id):
    result = ai_intelligent_decision.execute_decision(task_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_decision_api.route('/api/ai/decision/statistics', methods=['GET'])
@require_admin
def get_decision_statistics():
    stats = ai_intelligent_decision.get_decision_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_decision_api.route('/api/ai/decision/summary', methods=['GET'])
@require_login
def get_decision_summary():
    stats = ai_intelligent_decision.get_decision_statistics()
    return jsonify({'success': True, 'data': stats})