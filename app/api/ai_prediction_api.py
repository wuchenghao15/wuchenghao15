#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_learning_prediction import ai_learning_prediction

ai_prediction_api = Bluelogger.info('ai_prediction_api', __name__)

@ai_prediction_api.route('/api/ai/prediction/predict', methods=['POST'])
@require_login
def predict():
    data = request.get_json() or {}
    prediction_type = data.get('prediction_type')
    user_id = data.get('user_id')
    subject = data.get('subject')
    prediction_interval = data.get('interval', '7d')
    
    if not prediction_type or not user_id:
        return jsonify({'success': False, 'error': '预测类型和用户ID不能为空'}), 400
    
    result = ai_learning_prediction.predict(prediction_type, user_id, subject, prediction_interval)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_prediction_api.route('/api/ai/prediction/tasks', methods=['GET'])
@require_login
def list_prediction_tasks():
    prediction_type = request.args.get('type')
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 20))
    
    tasks = ai_learning_prediction.list_prediction_tasks(prediction_type, user_id, limit)
    return jsonify({'success': True, 'data': tasks})

@ai_prediction_api.route('/api/ai/prediction/tasks/<task_id>', methods=['GET'])
@require_login
def get_prediction_task(task_id):
    task = ai_learning_prediction.get_prediction_task(task_id)
    if task:
        return jsonify({'success': True, 'data': task})
    return jsonify({'success': False, 'error': '预测任务不存在'}), 404

@ai_prediction_api.route('/api/ai/prediction/validate/<task_id>', methods=['POST'])
@require_login
def validate_prediction(task_id):
    data = request.get_json() or {}
    actual_result = data.get('actual_result', {})
    
    result = ai_learning_prediction.validate_prediction(task_id, actual_result)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_prediction_api.route('/api/ai/prediction/statistics', methods=['GET'])
@require_admin
def get_prediction_statistics():
    stats = ai_learning_prediction.get_prediction_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_prediction_api.route('/api/ai/prediction/summary', methods=['GET'])
@require_login
def get_prediction_summary():
    stats = ai_learning_prediction.get_prediction_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_prediction_api.route('/api/ai/prediction/features/<user_id>', methods=['GET'])
@require_login
def get_user_features(user_id):
    features = ai_learning_prediction.extract_features(user_id)
    return jsonify({'success': True, 'data': features})