#!/usr/bin/env python3
"""
MTSCOS Dynamic Question Engine API - 动态题目生成引擎API
支持：
1. AI自动动态生成题目（多态多维随机生成，避免撞库）
2. 网络爬虫获取题目
3. 动态多态多维随机高质量高数量动态注入所有科目题库
"""

import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin, allow_guest_access
from ai_engines.dynamic_question_engine import dynamic_question_engine, SUBJECTS, QUESTION_TYPES, DIFFICULTY_LEVELS

dynamic_question_api = Blueprint('dynamic_question_api', __name__)


@dynamic_question_api.route('/api/dynamic/generate', methods=['POST'])
@require_login
def generate_question():
    """动态生成单道题目"""
    data = request.get_json() or {}
    
    subject = data.get('subject', 'math')
    question_type = data.get('question_type', 'single_choice')
    difficulty = data.get('difficulty', 'easy')
    grade = data.get('grade', '初中')
    
    question = dynamic_question_engine.generate_question(subject, question_type, difficulty, grade)
    
    if question:
        return jsonify({
            'success': True,
            'message': '题目生成成功',
            'data': question
        })
    else:
        return jsonify({'success': False, 'error': '题目生成失败'})


@dynamic_question_api.route('/api/dynamic/batch_generate', methods=['POST'])
@require_admin
def batch_generate():
    """批量动态生成题目"""
    data = request.get_json() or {}
    
    subject = data.get('subject')
    count = int(data.get('count', 10))
    difficulty = data.get('difficulty')
    question_type = data.get('question_type')
    grade = data.get('grade', '初中')
    
    result = dynamic_question_engine.batch_generate(subject, count, difficulty, question_type, grade)
    return jsonify(result)


@dynamic_question_api.route('/api/dynamic/crawl', methods=['POST'])
@require_admin
def crawl_web_questions():
    """从网络爬取题目"""
    data = request.get_json() or {}
    
    subject = data.get('subject')
    count = int(data.get('count', 10))
    
    result = dynamic_question_engine.crawl_web_questions(subject, count)
    return jsonify(result)


@dynamic_question_api.route('/api/dynamic/import_crawled', methods=['POST'])
@require_admin
def import_crawled_questions():
    """批量导入爬取的题目"""
    data = request.get_json() or {}
    
    limit = int(data.get('limit', 100))
    
    result = dynamic_question_engine.import_crawled_questions(limit)
    return jsonify(result)


@dynamic_question_api.route('/api/dynamic/config', methods=['GET'])
@allow_guest_access
def get_config():
    """获取动态生成配置"""
    configs = {
        'max_daily_generation': dynamic_question_engine.get_config('max_daily_generation', '1000'),
        'generation_batch_size': dynamic_question_engine.get_config('generation_batch_size', '50'),
        'crawl_batch_size': dynamic_question_engine.get_config('crawl_batch_size', '20'),
        'similarity_threshold': dynamic_question_engine.get_config('similarity_threshold', '0.85'),
        'max_retries': dynamic_question_engine.get_config('max_retries', '3'),
        'auto_import_crawled': dynamic_question_engine.get_config('auto_import_crawled', '1'),
        'enable_ai_generation': dynamic_question_engine.get_config('enable_ai_generation', '1'),
        'enable_web_crawl': dynamic_question_engine.get_config('enable_web_crawl', '1'),
        'generation_interval': dynamic_question_engine.get_config('generation_interval', '1'),
        'crawl_interval': dynamic_question_engine.get_config('crawl_interval', '2')
    }
    
    return jsonify({'success': True, 'data': configs})


@dynamic_question_api.route('/api/dynamic/config/<key>', methods=['PUT'])
@require_admin
def update_config(key):
    """更新动态生成配置"""
    data = request.get_json() or {}
    value = data.get('value')
    
    if value is None:
        return jsonify({'success': False, 'error': '配置值不能为空'})
    
    dynamic_question_engine.set_config(key, str(value))
    return jsonify({'success': True, 'message': '配置更新成功', 'key': key, 'value': value})


@dynamic_question_api.route('/api/dynamic/history', methods=['GET'])
@allow_guest_access
def get_generation_history():
    """获取生成历史"""
    limit = int(request.args.get('limit', 20))
    
    result = dynamic_question_engine.get_generation_history(limit)
    return jsonify(result)


@dynamic_question_api.route('/api/dynamic/crawled_stats', methods=['GET'])
@allow_guest_access
def get_crawled_stats():
    """获取爬取统计"""
    result = dynamic_question_engine.get_crawled_count()
    return jsonify(result)


@dynamic_question_api.route('/api/dynamic/stats', methods=['GET'])
@allow_guest_access
def get_dynamic_stats():
    """获取动态生成统计"""
    result = dynamic_question_engine.get_dynamic_stats()
    return jsonify(result)


@dynamic_question_api.route('/api/dynamic/generate_options', methods=['GET'])
@allow_guest_access
def get_generate_options():
    """获取生成选项"""
    subjects_list = []
    for code, info in SUBJECTS.items():
        subjects_list.append({
            'code': code,
            'name': info['name'],
            'icon': info['icon']
        })
    
    question_types_list = []
    for code, info in QUESTION_TYPES.items():
        question_types_list.append({
            'code': code,
            'name': info['name']
        })
    
    difficulty_levels_list = []
    for code, info in DIFFICULTY_LEVELS.items():
        difficulty_levels_list.append({
            'code': code,
            'name': info['name']
        })
    
    return jsonify({
        'success': True,
        'data': {
            'subjects': subjects_list,
            'question_types': question_types_list,
            'difficulty_levels': difficulty_levels_list,
            'grades': ['小学', '初中', '高中']
        }
    })