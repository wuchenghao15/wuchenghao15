# -*- coding: utf-8 -*-
"""
智能学习路径推荐API
分析学生学习数据，推荐个性化学习路径
"""

from flask import Blueprint, jsonify, request
from app.services.ai_study_path_service import ai_study_path_service

study_path_api = Blueprint('study_path_api', __name__)


@study_path_api.route('/api/ai/study-path/generate', methods=['POST'])
def generate_study_path():
    """生成学习路径"""
    data = request.get_json()
    
    user_id = int(data.get('user_id', 1))
    subject = data.get('subject', None)
    days = int(data.get('days', 7))
    
    if days < 1 or days > 30:
        return jsonify({
            'success': False,
            'message': '天数必须在1-30之间'
        })
    
    result = ai_study_path_service.generate_study_path(user_id, subject, days)
    return jsonify(result)


@study_path_api.route('/api/ai/study-path/analyze', methods=['POST'])
def analyze_weak_points():
    """分析薄弱环节"""
    data = request.get_json()
    
    user_id = int(data.get('user_id', 1))
    subject = data.get('subject', None)
    
    result = ai_study_path_service.analyze_weak_points(user_id, subject)
    return jsonify(result)


@study_path_api.route('/api/ai/study-path/subjects', methods=['GET'])
def get_subjects():
    """获取科目列表"""
    result = ai_study_path_service.get_all_subjects()
    return jsonify(result)


@study_path_api.route('/api/ai/study-path/knowledge-graph', methods=['GET'])
def get_knowledge_graph():
    """获取知识图谱"""
    subject = request.args.get('subject', '')
    
    if not subject:
        return jsonify({
            'success': False,
            'message': '科目不能为空'
        })
    
    result = ai_study_path_service.get_subject_knowledge_graph(subject)
    return jsonify(result)


@study_path_api.route('/api/ai/study-path/progress', methods=['POST'])
def get_learning_progress():
    """获取学习进度"""
    data = request.get_json()
    
    user_id = int(data.get('user_id', 1))
    
    result = ai_study_path_service.get_learning_progress(user_id)
    return jsonify(result)
