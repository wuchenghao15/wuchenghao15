#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_emotion_analysis import emotion_analysis_system

ai_emotion_api = Bluelogger.info('ai_emotion_api', __name__)

@ai_emotion_api.route('/api/ai/emotion/detect', methods=['POST'])
@require_login
def detect_emotion():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    text_content = data.get('text_content')
    behavior_data = data.get('behavior_data')
    source = data.get('source', 'text')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = emotion_analysis_system.detect_emotion(user_id, text_content, behavior_data, source)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_emotion_api.route('/api/ai/emotion/history', methods=['GET'])
@require_login
def get_user_emotion_history():
    user_id = request.args.get('user_id')
    days = int(request.args.get('days', 7))
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = emotion_analysis_system.get_user_emotion_history(user_id, days)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_emotion_api.route('/api/ai/emotion/profile', methods=['GET'])
@require_login
def get_user_emotion_profile():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = emotion_analysis_system.get_user_emotion_profile(user_id)
    if isinstance(result, dict) and 'error' not in result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error') if isinstance(result, dict) else str(result)}), 400

@ai_emotion_api.route('/api/ai/emotion/intervention', methods=['POST'])
@require_login
def generate_intervention():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    emotion_type = data.get('emotion_type')
    
    if not user_id or not emotion_type:
        return jsonify({'success': False, 'error': '用户ID和情感类型不能为空'}), 400
    
    result = emotion_analysis_system.generate_intervention(user_id, emotion_type)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_emotion_api.route('/api/ai/emotion/intervention/<intervention_id>/execute', methods=['POST'])
@require_admin
def execute_intervention(intervention_id):
    result = emotion_analysis_system.execute_intervention(intervention_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_emotion_api.route('/api/ai/emotion/alerts', methods=['GET'])
@require_login
def get_emotion_alerts():
    status = request.args.get('status', 'active')
    
    result = emotion_analysis_system.get_emotion_alerts(status)
    return jsonify({'success': True, 'data': result, 'count': len(result)})

@ai_emotion_api.route('/api/ai/emotion/alerts/<alert_id>/resolve', methods=['POST'])
@require_admin
def resolve_alert(alert_id):
    result = emotion_analysis_system.resolve_alert(alert_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_emotion_api.route('/api/ai/emotion/summary', methods=['GET'])
@require_login
def get_emotion_summary():
    result = emotion_analysis_system.get_emotion_summary()
    return jsonify({'success': True, 'data': result})

@ai_emotion_api.route('/api/ai/emotion/types', methods=['GET'])
@require_login
def get_emotion_types():
    return jsonify({
        'success': True,
        'data': {
            'emotion_types': emotion_analysis_system.EMOTION_TYPES,
            'emotion_levels': emotion_analysis_system.EMOTION_LEVELS,
            'analysis_sources': emotion_analysis_system.ANALYSIS_SOURCES
        }
    })