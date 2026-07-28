#!/usr/bin/env python3
"""
AI学习路径推荐API
提供学习路径生成、进度跟踪、计划管理等功能的REST API接口
"""

from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_learning_path_recommender import ai_learning_path_recommender

ai_learning_path_api = Bluelogger.info('ai_learning_path_api', __name__)

@ai_learning_path_api.route('/api/ai/learning-path/generate', methods=['POST'])
@require_login
def generate_learning_path():
    """生成学习路径"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    target_score = data.get('target_score')
    
    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400
    
    result = ai_learning_path_recommender.generate_learning_path(user_id, subject, target_score)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result)

@ai_learning_path_api.route('/api/ai/learning-path/<path_id>', methods=['GET'])
@require_login
def get_learning_path(path_id):
    """获取学习路径"""
    result = ai_learning_path_recommender.get_learning_path(path_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 404

@ai_learning_path_api.route('/api/ai/learning-path/user/<user_id>', methods=['GET'])
@require_login
def get_user_paths(user_id):
    """获取用户学习路径列表"""
    result = ai_learning_path_recommender.get_user_paths(user_id)
    return jsonify({'success': True, 'data': result})

@ai_learning_path_api.route('/api/ai/learning-path/plan/<plan_id>', methods=['GET'])
@require_login
def get_plan_items(plan_id):
    """获取计划项列表"""
    result = ai_learning_path_recommender.get_plan_items(plan_id)
    return jsonify({'success': True, 'data': result})

@ai_learning_path_api.route('/api/ai/learning-path/plan/<plan_id>/item/<order_num>', methods=['PUT'])
@require_login
def update_plan_item(plan_id, order_num):
    """更新计划项状态"""
    data = request.get_json() or {}
    status = data.get('status')
    
    if not status:
        return jsonify({'success': False, 'error': '状态不能为空'}), 400
    
    result = ai_learning_path_recommender.update_plan_item_status(plan_id, int(order_num), status)
    return jsonify(result)