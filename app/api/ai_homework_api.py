#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_homework_grading import ai_homework_grading

ai_homework_api = Bluelogger.info('ai_homework_api', __name__)

@ai_homework_api.route('/api/ai/homework/create', methods=['POST'])
@require_admin
def create_assignment():
    data = request.get_json() or {}
    title = data.get('title')
    subject = data.get('subject')
    grade_level = data.get('grade_level')
    total_score = data.get('total_score', 100)
    deadline = data.get('deadline')
    questions = data.get('questions')
    
    if not title or not subject:
        return jsonify({'success': False, 'error': '标题和科目不能为空'}), 400
    
    result = ai_homework_grading.create_assignment(title, subject, grade_level, total_score, deadline, questions)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_homework_api.route('/api/ai/homework/submit', methods=['POST'])
@require_login
def submit_homework():
    data = request.get_json() or {}
    assignment_id = data.get('assignment_id')
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    if not assignment_id or not user_id or not answers:
        return jsonify({'success': False, 'error': '作业ID、用户ID和答案不能为空'}), 400
    
    result = ai_homework_grading.submit_homework(assignment_id, user_id, answers)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_homework_api.route('/api/ai/homework/grade/<submission_id>', methods=['POST'])
@require_admin
def grade_submission(submission_id):
    result = ai_homework_grading.grade_submission(submission_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_homework_api.route('/api/ai/homework/submission/<submission_id>', methods=['GET'])
@require_login
def get_submission(submission_id):
    result = ai_homework_grading.get_submission(submission_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 404

@ai_homework_api.route('/api/ai/homework/submissions', methods=['GET'])
@require_login
def list_submissions():
    assignment_id = request.args.get('assignment_id')
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 20))
    
    result = ai_homework_grading.list_submissions(assignment_id, user_id, limit)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_homework_api.route('/api/ai/homework/assignment/<assignment_id>', methods=['GET'])
@require_login
def get_assignment(assignment_id):
    result = ai_homework_grading.get_assignment(assignment_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 404

@ai_homework_api.route('/api/ai/homework/assignments', methods=['GET'])
@require_login
def list_assignments():
    subject = request.args.get('subject')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 20))
    
    result = ai_homework_grading.list_assignments(subject, status, limit)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_homework_api.route('/api/ai/homework/analytics/<assignment_id>', methods=['GET'])
@require_admin
def get_grading_analytics(assignment_id):
    result = ai_homework_grading.get_grading_analytics(assignment_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_homework_api.route('/api/ai/homework/types', methods=['GET'])
@require_login
def get_question_types():
    return jsonify({
        'success': True,
        'data': {
            'question_types': ai_homework_grading.QUESTION_TYPES,
            'grading_status': ai_homework_grading.GRADING_STATUS,
            'score_levels': ai_homework_grading.SCORE_LEVELS
        }
    })