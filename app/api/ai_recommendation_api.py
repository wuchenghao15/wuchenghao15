#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_resource_recommendation import ai_resource_recommendation

ai_recommendation_api = Bluelogger.info('ai_recommendation_api', __name__)

@ai_recommendation_api.route('/api/ai/recommendation/generate', methods=['POST'])
@require_login
def generate_recommendations():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    count = data.get('count', 10)
    strategy = data.get('strategy', 'hybrid')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_resource_recommendation.generate_recommendations(user_id, count, strategy)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_recommendation_api.route('/api/ai/recommendation/resource', methods=['POST'])
@require_admin
def add_resource():
    data = request.get_json() or {}
    title = data.get('title')
    resource_type = data.get('resource_type')
    subject = data.get('subject')
    category = data.get('category')
    difficulty = data.get('difficulty', 1)
    duration = data.get('duration', 0.0)
    tags = data.get('tags', [])
    description = data.get('description', '')
    url = data.get('url', '')
    
    if not title or not resource_type:
        return jsonify({'success': False, 'error': '资源标题和类型不能为空'}), 400
    
    result = ai_resource_recommendation.add_resource(title, resource_type, subject, category, 
                                                      difficulty, duration, 0.0, tags, description, url)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_recommendation_api.route('/api/ai/recommendation/resources', methods=['GET'])
@require_login
def search_resources():
    query = request.args.get('query', '')
    subject = request.args.get('subject')
    resource_type = request.args.get('type')
    difficulty = request.args.get('difficulty')
    limit = int(request.args.get('limit', 20))
    
    results = ai_resource_recommendation.search_resources(query, subject, resource_type, difficulty, limit)
    return jsonify({'success': True, 'data': results})

@ai_recommendation_api.route('/api/ai/recommendation/resources/<resource_id>', methods=['GET'])
@require_login
def get_resource(resource_id):
    resource = ai_resource_recommendation.get_resource(resource_id)
    if resource:
        return jsonify({'success': True, 'data': resource})
    return jsonify({'success': False, 'error': '资源不存在'}), 404

@ai_recommendation_api.route('/api/ai/recommendation/interaction', methods=['POST'])
@require_login
def record_interaction():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    resource_id = data.get('resource_id')
    action = data.get('action')
    duration = data.get('duration', 0.0)
    rating = data.get('rating', 0)
    completed = data.get('completed', False)
    
    if not user_id or not resource_id or not action:
        return jsonify({'success': False, 'error': '用户ID、资源ID和动作不能为空'}), 400
    
    result = ai_resource_recommendation.record_interaction(user_id, resource_id, action, duration, rating, completed)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_recommendation_api.route('/api/ai/recommendation/profile', methods=['GET'])
@require_login
def get_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    profile = ai_resource_recommendation.get_or_create_profile(user_id)
    if profile:
        return jsonify({'success': True, 'data': profile})
    return jsonify({'success': False, 'error': '获取用户档案失败'}), 400

@ai_recommendation_api.route('/api/ai/recommendation/profile', methods=['PUT'])
@require_login
def update_profile():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    updates = data.get('updates', {})
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_resource_recommendation.update_profile(user_id, updates)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_recommendation_api.route('/api/ai/recommendation/feedback', methods=['POST'])
@require_login
def submit_feedback():
    data = request.get_json() or {}
    task_id = data.get('task_id')
    resource_id = data.get('resource_id')
    accepted = data.get('accepted', False)
    feedback = data.get('feedback', '')
    
    if not task_id or not resource_id:
        return jsonify({'success': False, 'error': '任务ID和资源ID不能为空'}), 400
    
    result = ai_resource_recommendation.submit_feedback(task_id, resource_id, accepted, feedback)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_recommendation_api.route('/api/ai/recommendation/tasks', methods=['GET'])
@require_login
def list_recommendation_tasks():
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 20))
    
    tasks = ai_resource_recommendation.list_recommendation_tasks(user_id, limit)
    return jsonify({'success': True, 'data': tasks})

@ai_recommendation_api.route('/api/ai/recommendation/statistics', methods=['GET'])
@require_admin
def get_recommendation_statistics():
    stats = ai_resource_recommendation.get_recommendation_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_recommendation_api.route('/api/ai/recommendation/summary', methods=['GET'])
@require_login
def get_recommendation_summary():
    stats = ai_resource_recommendation.get_recommendation_statistics()
    return jsonify({'success': True, 'data': stats})