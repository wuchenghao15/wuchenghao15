#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_cognitive_reasoning import ai_cognitive_reasoning

ai_cognitive_api = Bluelogger.info('ai_cognitive_api', __name__)

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/execute', methods=['POST'])
@require_login
def execute_reasoning():
    data = request.get_json() or {}
    reasoning_type = data.get('reasoning_type')
    input_data = data.get('input_data', {})
    goal = data.get('goal')
    
    if not reasoning_type or not goal:
        return jsonify({'success': False, 'error': '推理类型和目标不能为空'}), 400
    
    result = ai_cognitive_reasoning.execute_reasoning(reasoning_type, input_data, goal)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/deductive', methods=['POST'])
@require_login
def deductive_reasoning():
    data = request.get_json() or {}
    premises = data.get('premises', [])
    conclusion_goal = data.get('goal')
    
    if not premises or not conclusion_goal:
        return jsonify({'success': False, 'error': '前提条件和结论目标不能为空'}), 400
    
    result = ai_cognitive_reasoning.deductive_reasoning(premises, conclusion_goal)
    return jsonify({'success': True, 'data': result})

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/inductive', methods=['POST'])
@require_login
def inductive_reasoning():
    data = request.get_json() or {}
    observations = data.get('observations', [])
    pattern_goal = data.get('goal')
    
    if not observations or not pattern_goal:
        return jsonify({'success': False, 'error': '观察数据和模式目标不能为空'}), 400
    
    result = ai_cognitive_reasoning.inductive_reasoning(observations, pattern_goal)
    return jsonify({'success': True, 'data': result})

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/abductive', methods=['POST'])
@require_login
def abductive_reasoning():
    data = request.get_json() or {}
    evidence = data.get('evidence', [])
    hypothesis_goal = data.get('goal')
    
    if not evidence or not hypothesis_goal:
        return jsonify({'success': False, 'error': '证据和假设目标不能为空'}), 400
    
    result = ai_cognitive_reasoning.abductive_reasoning(evidence, hypothesis_goal)
    return jsonify({'success': True, 'data': result})

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/analogical', methods=['POST'])
@require_login
def analogical_reasoning():
    data = request.get_json() or {}
    source_domain = data.get('source_domain', {})
    target_domain = data.get('target_domain', {})
    mapping_goal = data.get('goal')
    
    if not source_domain or not target_domain or not mapping_goal:
        return jsonify({'success': False, 'error': '源域、目标域和映射目标不能为空'}), 400
    
    result = ai_cognitive_reasoning.analogical_reasoning(source_domain, target_domain, mapping_goal)
    return jsonify({'success': True, 'data': result})

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/causal', methods=['POST'])
@require_login
def causal_reasoning():
    data = request.get_json() or {}
    events = data.get('events', [])
    effect_goal = data.get('goal')
    
    if not events or not effect_goal:
        return jsonify({'success': False, 'error': '事件序列和效果目标不能为空'}), 400
    
    result = ai_cognitive_reasoning.causal_reasoning(events, effect_goal)
    return jsonify({'success': True, 'data': result})

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/tasks', methods=['GET'])
@require_login
def list_reasoning_tasks():
    reasoning_type = request.args.get('type')
    limit = int(request.args.get('limit', 20))
    
    tasks = ai_cognitive_reasoning.list_reasoning_tasks(reasoning_type, limit)
    return jsonify({'success': True, 'data': tasks})

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/tasks/<task_id>', methods=['GET'])
@require_login
def get_reasoning_task(task_id):
    task = ai_cognitive_reasoning.get_reasoning_task(task_id)
    if task:
        return jsonify({'success': True, 'data': task})
    return jsonify({'success': False, 'error': '推理任务不存在'}), 404

@ai_cognitive_api.route('/api/ai/cognitive/knowledge/add', methods=['POST'])
@require_login
def add_knowledge():
    data = request.get_json() or {}
    topic = data.get('topic')
    content = data.get('content')
    category = data.get('category')
    source = data.get('source', 'system')
    
    if not topic or not content:
        return jsonify({'success': False, 'error': '知识主题和内容不能为空'}), 400
    
    result = ai_cognitive_reasoning.add_knowledge(topic, content, category, source)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_cognitive_api.route('/api/ai/cognitive/knowledge/search', methods=['GET'])
@require_login
def search_knowledge():
    query = request.args.get('query', '')
    category = request.args.get('category')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'success': False, 'error': '搜索关键词不能为空'}), 400
    
    results = ai_cognitive_reasoning.search_knowledge(query, category, limit)
    return jsonify({'success': True, 'data': results})

@ai_cognitive_api.route('/api/ai/cognitive/knowledge/<knowledge_id>', methods=['GET'])
@require_login
def get_knowledge(knowledge_id):
    knowledge = ai_cognitive_reasoning.get_knowledge(knowledge_id)
    if knowledge:
        return jsonify({'success': True, 'data': knowledge})
    return jsonify({'success': False, 'error': '知识不存在'}), 404

@ai_cognitive_api.route('/api/ai/cognitive/statistics', methods=['GET'])
@require_admin
def get_cognitive_statistics():
    stats = ai_cognitive_reasoning.get_reasoning_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/summary', methods=['GET'])
@require_login
def get_reasoning_summary():
    stats = ai_cognitive_reasoning.get_reasoning_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_cognitive_api.route('/api/ai/cognitive/reasoning/history', methods=['GET'])
@require_login
def get_reasoning_history():
    limit = int(request.args.get('limit', 20))
    tasks = ai_cognitive_reasoning.list_reasoning_tasks(limit=limit)
    return jsonify({'success': True, 'data': tasks})

@ai_cognitive_api.route('/api/ai/cognitive/knowledge', methods=['POST'])
@require_login
def add_knowledge_simple():
    data = request.get_json() or {}
    topic = data.get('topic')
    content = data.get('content')
    category = data.get('category')
    source = data.get('source', 'system')
    
    if not topic or not content:
        return jsonify({'success': False, 'error': '知识主题和内容不能为空'}), 400
    
    result = ai_cognitive_reasoning.add_knowledge(topic, content, category=category, source=source)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400