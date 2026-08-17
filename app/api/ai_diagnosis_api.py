#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_learning_diagnosis import ai_learning_diagnosis

ai_diagnosis_api = Bluelogger.info('ai_diagnosis_api', __name__)

@ai_diagnosis_api.route('/api/ai/diagnosis/diagnose', methods=['POST'])
@require_login
def diagnose_learning():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    exam_data = data.get('exam_data')
    homework_data = data.get('homework_data')
    practice_data = data.get('practice_data')
    
    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400
    
    result = ai_learning_diagnosis.diagnose_learning(user_id, subject, exam_data, homework_data, practice_data)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_diagnosis_api.route('/api/ai/diagnosis/<record_id>', methods=['GET'])
@require_login
def get_diagnosis(record_id):
    result = ai_learning_diagnosis.get_diagnosis(record_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 404

@ai_diagnosis_api.route('/api/ai/diagnosis/list', methods=['GET'])
@require_login
def list_diagnoses():
    user_id = request.args.get('user_id')
    subject = request.args.get('subject')
    limit = int(request.args.get('limit', 20))
    
    result = ai_learning_diagnosis.list_diagnoses(user_id, subject, limit)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_diagnosis_api.route('/api/ai/diagnosis/analytics', methods=['GET'])
@require_login
def get_learning_analytics():
    user_id = request.args.get('user_id')
    subject = request.args.get('subject')
    
    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400
    
    result = ai_learning_diagnosis.get_learning_analytics(user_id, subject)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_diagnosis_api.route('/api/ai/diagnosis/tasks', methods=['GET'])
@require_login
def get_improvement_tasks():
    user_id = request.args.get('user_id')
    subject = request.args.get('subject')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_learning_diagnosis.get_improvement_tasks(user_id, subject)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_diagnosis_api.route('/api/ai/diagnosis/task/<task_id>', methods=['PUT'])
@require_login
def update_task_status(task_id):
    data = request.get_json() or {}
    status = data.get('status')
    current_score = data.get('current_score')
    
    if not status:
        return jsonify({'success': False, 'error': '状态不能为空'}), 400
    
    result = ai_learning_diagnosis.update_task_status(task_id, status, current_score)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_diagnosis_api.route('/api/ai/diagnosis/knowledge_points', methods=['GET'])
@require_login
def get_knowledge_points():
    subject = request.args.get('subject')
    
    if not subject:
        return jsonify({'success': False, 'error': '科目不能为空'}), 400
    
    result = ai_learning_diagnosis.get_knowledge_points(subject)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_diagnosis_api.route('/api/ai/diagnosis/history', methods=['GET'])
@require_login
def get_diagnosis_history():
    user_id = request.args.get('user_id')
    subject = request.args.get('subject')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_learning_diagnosis.get_diagnosis_history(user_id, subject)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_diagnosis_api.route('/api/ai/diagnosis/report', methods=['POST'])
@require_login
def generate_report():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    
    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400
    
    result = ai_learning_diagnosis.generate_report(user_id, subject)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_diagnosis_api.route('/api/ai/diagnosis/domains', methods=['GET'])
@require_login
def get_knowledge_domains():
    return jsonify({
        'success': True,
        'data': {
            'knowledge_domains': ai_learning_diagnosis.KNOWLEDGE_DOMAINS,
            'diagnosis_levels': ai_learning_diagnosis.DIAGNOSIS_LEVELS,
            'skill_levels': ai_learning_diagnosis.SKILL_LEVELS
        }
    })