#!/usr/bin/env python3
"""
AI智能组卷API
提供试卷生成、试卷查询等功能的REST API接口
"""

from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_paper_generator import ai_paper_generator

ai_paper_api = Bluelogger.info('ai_paper_api', __name__)

@ai_paper_api.route('/api/ai/paper/generate', methods=['POST'])
@require_admin
def generate_paper():
    """生成试卷"""
    data = request.get_json() or {}
    title = data.get('title')
    subject = data.get('subject', '数学')
    total_score = int(data.get('total_score', 100))
    duration = int(data.get('duration', 120))
    difficulty = data.get('difficulty', 'balanced')
    topics = data.get('topics')
    question_types = data.get('question_types')
    
    if not title:
        return jsonify({'success': False, 'error': '试卷标题不能为空'}), 400
    
    if total_score < 50 or total_score > 300:
        return jsonify({'success': False, 'error': '总分应在50-300之间'}), 400
    
    result = ai_paper_generator.generate_paper(title, subject, total_score, duration, 
                                                difficulty, topics, question_types)
    return jsonify({'success': True, 'data': result})

@ai_paper_api.route('/api/ai/paper/<paper_id>', methods=['GET'])
@require_login
def get_paper(paper_id):
    """获取试卷"""
    result = ai_paper_generator.get_paper(paper_id)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': '试卷不存在'}), 404

@ai_paper_api.route('/api/ai/paper/list', methods=['GET'])
@require_login
def list_papers():
    """列出试卷"""
    subject = request.args.get('subject')
    limit = int(request.args.get('limit', 10))
    
    result = ai_paper_generator.list_papers(subject, limit)
    return jsonify({'success': True, 'data': result})

@ai_paper_api.route('/api/ai/paper/subjects', methods=['GET'])
@require_login
def get_subjects():
    """获取科目列表"""
    return jsonify({'success': True, 'data': ai_paper_generator.SUBJECT_TOPICS})

@ai_paper_api.route('/api/ai/paper/question-types', methods=['GET'])
@require_login
def get_question_types():
    """获取题型列表"""
    return jsonify({'success': True, 'data': ai_paper_generator.QUESTION_TYPES})