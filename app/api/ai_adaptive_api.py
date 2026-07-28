#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_adaptive_learning import ai_adaptive_learning

ai_adaptive_api = Bluelogger.info('ai_adaptive_api', __name__)

@ai_adaptive_api.route('/api/ai/adaptive/profile', methods=['GET'])
@require_login
def get_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    profile = ai_adaptive_learning.get_or_create_profile(user_id)
    if profile:
        return jsonify({'success': True, 'data': profile})
    return jsonify({'success': False, 'error': '获取学习档案失败'}), 400

@ai_adaptive_api.route('/api/ai/adaptive/profile', methods=['PUT'])
@require_login
def update_profile():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    updates = data.get('updates', {})
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_adaptive_learning.update_profile(user_id, updates)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_adaptive_api.route('/api/ai/adaptive/profile/analyze', methods=['POST'])
@require_login
def analyze_learning_style():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    interactions = data.get('interactions', [])
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_adaptive_learning.analyze_learning_style(user_id, interactions)
    return jsonify({'success': True, 'data': result})

@ai_adaptive_api.route('/api/ai/adaptive/path', methods=['POST'])
@require_login
def create_learning_path():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    objectives = data.get('objectives', [])
    
    if not user_id or not subject or not objectives:
        return jsonify({'success': False, 'error': '用户ID、科目和学习目标不能为空'}), 400
    
    result = ai_adaptive_learning.create_learning_path(user_id, subject, objectives)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_adaptive_api.route('/api/ai/adaptive/path/<path_id>', methods=['GET'])
@require_login
def get_learning_path(path_id):
    path = ai_adaptive_learning.get_learning_path(path_id)
    if path:
        return jsonify({'success': True, 'data': path})
    return jsonify({'success': False, 'error': '学习路径不存在'}), 404

@ai_adaptive_api.route('/api/ai/adaptive/path/user/<user_id>', methods=['GET'])
@require_login
def get_user_paths(user_id):
    paths = ai_adaptive_learning.get_user_paths(user_id)
    return jsonify({'success': True, 'data': paths})

@ai_adaptive_api.route('/api/ai/adaptive/progress', methods=['POST'])
@require_login
def update_progress():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    path_id = data.get('path_id')
    step_id = data.get('step_id')
    score = data.get('score')
    completed = data.get('completed', False)
    
    if not path_id or not step_id:
        return jsonify({'success': False, 'error': '路径ID和步骤ID不能为空'}), 400
    
    result = ai_adaptive_learning.update_learning_progress(user_id, path_id, step_id, score, completed)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_adaptive_api.route('/api/ai/adaptive/gaps', methods=['POST'])
@require_login
def detect_knowledge_gaps():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_adaptive_learning.detect_knowledge_gaps(user_id, subject)
    return jsonify({'success': True, 'data': result})

@ai_adaptive_api.route('/api/ai/adaptive/recommendations', methods=['POST'])
@require_login
def generate_recommendations():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_adaptive_learning.generate_recommendations(user_id)
    return jsonify({'success': True, 'data': result})

@ai_adaptive_api.route('/api/ai/adaptive/interaction', methods=['POST'])
@require_login
def record_interaction():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    action = data.get('action')
    content = data.get('content', '')
    duration = data.get('duration', 0.0)
    success = data.get('success', False)
    score = data.get('score', 0.0)
    
    if not user_id or not subject or not action:
        return jsonify({'success': False, 'error': '用户ID、科目和动作不能为空'}), 400
    
    result = ai_adaptive_learning.record_interaction(user_id, subject, action, content, duration, success, score)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_adaptive_api.route('/api/ai/adaptive/statistics', methods=['GET'])
@require_admin
def get_adaptive_statistics():
    user_id = request.args.get('user_id')
    stats = ai_adaptive_learning.get_learning_statistics(user_id)
    return jsonify({'success': True, 'data': stats})

@ai_adaptive_api.route('/api/ai/adaptive/summary', methods=['GET'])
@require_login
def get_adaptive_summary():
    stats = ai_adaptive_learning.get_learning_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_adaptive_api.route('/api/ai/adaptive/profile', methods=['POST'])
@require_login
def create_profile():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    learning_style = data.get('learning_style')
    subject = data.get('subject')
    objectives = data.get('objectives', '')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_adaptive_learning.create_profile(user_id, learning_style, subject, objectives)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_adaptive_api.route('/api/ai/adaptive/profiles', methods=['GET'])
@require_login
def list_profiles():
    profiles = ai_adaptive_learning.list_profiles()
    return jsonify({'success': True, 'data': profiles})

@ai_adaptive_api.route('/api/ai/adaptive/progress/<user_id>', methods=['GET'])
@require_login
def get_user_progress(user_id):
    progress = ai_adaptive_learning.get_user_progress(user_id)
    return jsonify({'success': True, 'data': progress})

@ai_adaptive_api.route('/api/ai/adaptive/gaps/<user_id>', methods=['GET'])
@require_login
def get_user_gaps(user_id):
    subject = request.args.get('subject')
    gaps = ai_adaptive_learning.detect_knowledge_gaps(user_id, subject)
    return jsonify({'success': True, 'data': gaps})

@ai_adaptive_api.route('/api/ai/adaptive/recommendations/<user_id>', methods=['GET'])
@require_login
def get_user_recommendations(user_id):
    recommendations = ai_adaptive_learning.generate_recommendations(user_id)
    return jsonify({'success': True, 'data': recommendations})