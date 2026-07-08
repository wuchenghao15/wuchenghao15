# -*- coding: utf-8 -*-
"""
AI智能题目生成API
从文本内容自动生成考试题目
"""

from flask import Blueprint, jsonify, request
from app.services.ai_question_generation_service import ai_question_generation_service

ai_generation_api = Blueprint('ai_generation_api', __name__)


@ai_generation_api.route('/api/ai/generate-questions', methods=['POST'])
def generate_questions():
    """从文本生成题目"""
    data = request.get_json()
    
    text = data.get('text', '')
    count = int(data.get('count', 10))
    types = data.get('types', [])
    difficulty = data.get('difficulty', 'medium')
    subject = data.get('subject', None)
    
    if not text or len(text) < 50:
        return jsonify({
            'success': False,
            'message': '文本内容太短，至少需要50个字符'
        })
    
    if count < 1 or count > 50:
        return jsonify({
            'success': False,
            'message': '题目数量必须在1-50之间'
        })
    
    result = ai_question_generation_service.generate_questions(
        text=text,
        count=count,
        types=types if types else None,
        difficulty=difficulty,
        subject=subject
    )
    
    return jsonify(result)


@ai_generation_api.route('/api/ai/generate-questions/save', methods=['POST'])
def save_generated_questions():
    """保存生成的题目"""
    data = request.get_json()
    
    questions = data.get('questions', [])
    user_id = data.get('user_id', 0)
    
    if not questions:
        return jsonify({
            'success': False,
            'message': '题目列表不能为空'
        })
    
    result = ai_question_generation_service.save_questions(questions, user_id)
    return jsonify(result)


@ai_generation_api.route('/api/ai/generate-questions/stats', methods=['GET'])
def get_generation_stats():
    """获取生成统计"""
    result = ai_question_generation_service.get_generation_stats()
    return jsonify(result)


@ai_generation_api.route('/api/ai/generate-questions/subjects', methods=['GET'])
def get_subjects():
    """获取支持的科目列表"""
    subjects = list(ai_question_generation_service.subject_keywords.keys())
    return jsonify({
        'success': True,
        'data': subjects
    })


@ai_generation_api.route('/api/ai/generate-questions/types', methods=['GET'])
def get_question_types():
    """获取支持的题型列表"""
    types = ai_question_generation_service.question_types
    return jsonify({
        'success': True,
        'data': types
    })


@ai_generation_api.route('/api/ai/detect-subject', methods=['POST'])
def detect_subject():
    """自动检测文本科目"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({
            'success': False,
            'message': '文本内容不能为空'
        })
    
    subject = ai_question_generation_service.detect_subject(text)
    return jsonify({
        'success': True,
        'data': {
            'subject': subject
        }
    })


@ai_generation_api.route('/api/ai/extract-key-points', methods=['POST'])
def extract_key_points():
    """提取文本关键点"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({
            'success': False,
            'message': '文本内容不能为空'
        })
    
    key_points = ai_question_generation_service.extract_key_points(text)
    return jsonify({
        'success': True,
        'data': {
            'key_points': key_points
        }
    })
