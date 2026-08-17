#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS K12教育API接口
=====================
提供K12教育相关的REST API接口，包括：
- 学生档案管理
- 知识点掌握度
- 错题本管理
- 家校互动
- 学习游戏化
- 综合素质评价
- 升学指导
"""

from flask import Blueprint, request, jsonify
from ..middlewares.access_control import require_admin
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from k12_education_service import (
    K12EducationService,
    K12GameService,
    K12ComprehensiveEvaluationService,
    K12CollegeAdmissionService,
    K12_SUBJECTS,
    LEARNING_TIERS,
    GRADE_GROUPS
)

k12_api = Bluelogger.info('k12_api', __name__)

k12_service = K12EducationService()
game_service = K12GameService()
eval_service = K12ComprehensiveEvaluationService()
admission_service = K12CollegeAdmissionService()


@k12_api.route('/api/k12/student/profile', methods=['POST'])
@require_admin
def create_student_profile():
    """创建K12学生档案"""
    data = request.get_json()
    user_id = data.get('user_id')
    grade = data.get('grade')
    subjects = data.get('subjects')
    parent_user_id = data.get('parent_user_id')
    class_id = data.get('class_id')

    if not user_id or not grade:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = k12_service.create_student_profile(user_id, grade, subjects, parent_user_id, class_id)
    return jsonify(result)


@k12_api.route('/api/k12/student/profile/<int:user_id>', methods=['GET'])
@require_admin
def get_student_profile(user_id):
    """获取学生档案"""
    result = k12_service.get_student_profile(user_id)
    return jsonify(result)


@k12_api.route('/api/k12/student/tier', methods=['PUT'])
@require_admin
def update_tier():
    """更新学习分层"""
    data = request.get_json()
    user_id = data.get('user_id')
    tier = data.get('tier')
    subject = data.get('subject')

    if not user_id or not tier:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = k12_service.update_learning_tier(user_id, tier, subject)
    return jsonify(result)


@k12_api.route('/api/k12/knowledge/points', methods=['POST'])
@require_admin
def add_knowledge_point():
    """添加知识点"""
    data = request.get_json()
    subject = data.get('subject')
    grade = data.get('grade')
    point_name = data.get('point_name')
    chapter = data.get('chapter')
    difficulty_level = data.get('difficulty_level', 2)

    if not subject or not grade or not point_name:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = k12_service.add_knowledge_point(subject, grade, point_name, chapter, difficulty_level)
    return jsonify(result)


@k12_api.route('/api/k12/knowledge/points', methods=['GET'])
@require_admin
def get_knowledge_points():
    """获取知识点列表"""
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    result = k12_service.get_knowledge_points(subject, grade)
    return jsonify(result)


@k12_api.route('/api/k12/knowledge/mastery', methods=['PUT'])
@require_admin
def update_mastery():
    """更新知识点掌握度"""
    data = request.get_json()
    user_id = data.get('user_id')
    point_id = data.get('point_id')
    is_correct = data.get('is_correct')

    if not user_id or not point_id or is_correct is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = k12_service.update_mastery(user_id, point_id, is_correct)
    return jsonify(result)


@k12_api.route('/api/k12/knowledge/mastery/<int:user_id>', methods=['GET'])
@require_admin
def get_mastery(user_id):
    """获取学生知识点掌握度"""
    subject = request.args.get('subject')
    result = k12_service.get_knowledge_mastery(user_id, subject)
    return jsonify(result)


@k12_api.route('/api/k12/wrong/questions', methods=['POST'])
@require_admin
def add_wrong_question():
    """添加错题"""
    data = request.get_json()
    user_id = data.get('user_id')
    subject = data.get('subject')
    question_id = data.get('question_id')
    point_id = data.get('point_id')
    wrong_type = data.get('wrong_type')
    note = data.get('note')

    if not user_id or not subject:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = k12_service.add_wrong_question(user_id, subject, question_id, point_id, wrong_type, note)
    return jsonify(result)


@k12_api.route('/api/k12/wrong/questions/<int:user_id>', methods=['GET'])
@require_admin
def get_wrong_questions(user_id):
    """获取学生错题"""
    subject = request.args.get('subject')
    resolved = request.args.get('resolved')
    result = k12_service.get_wrong_questions(user_id, subject, resolved)
    return jsonify(result)


@k12_api.route('/api/k12/wrong/questions/<wrong_id>/resolve', methods=['PUT'])
@require_admin
def resolve_wrong_question(wrong_id):
    """解决错题"""
    result = k12_service.resolve_wrong_question(wrong_id)
    return jsonify(result)


@k12_api.route('/api/k12/weak/points/<int:user_id>', methods=['GET'])
@require_admin
def get_weak_points(user_id):
    """获取薄弱知识点"""
    subject = request.args.get('subject')
    limit = request.args.get('limit', 10)
    result = k12_service.get_weak_points(user_id, subject, limit)
    return jsonify(result)


@k12_api.route('/api/k12/home-school/message', methods=['POST'])
@require_admin
def send_home_school_message():
    """发送家校消息"""
    data = request.get_json()
    student_user_id = data.get('student_user_id')
    sender_id = data.get('sender_id')
    sender_role = data.get('sender_role')
    message_type = data.get('message_type')
    title = data.get('title')
    content = data.get('content')

    if not student_user_id or not sender_id or not message_type:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = k12_service.send_home_school_message(student_user_id, sender_id, sender_role, message_type, title, content)
    return jsonify(result)


@k12_api.route('/api/k12/home-school/messages/<int:user_id>', methods=['GET'])
@require_admin
def get_home_school_messages(user_id):
    """获取家校消息"""
    result = k12_service.get_home_school_messages(user_id)
    return jsonify(result)


@k12_api.route('/api/k12/report/<int:user_id>', methods=['POST'])
@require_admin
def generate_report(user_id):
    """生成学习报告"""
    data = request.get_json()
    report_type = data.get('report_type', 'weekly')
    result = k12_service.generate_report(user_id, report_type)
    return jsonify(result)


@k12_api.route('/api/k12/game/status/<int:user_id>', methods=['GET'])
@require_admin
def get_game_status(user_id):
    """获取游戏状态"""
    result = game_service.get_user_game_status(user_id)
    return jsonify(result)


@k12_api.route('/api/k12/game/check-in/<int:user_id>', methods=['POST'])
@require_admin
def game_check_in(user_id):
    """每日签到"""
    result = game_service.login_check_in(user_id)
    return jsonify(result)


@k12_api.route('/api/k12/game/points', methods=['POST'])
@require_admin
def add_game_points():
    """添加游戏积分"""
    data = request.get_json()
    user_id = data.get('user_id')
    transaction_type = data.get('transaction_type')
    points = data.get('points')
    description = data.get('description', '')

    if not user_id or not transaction_type or points is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = game_service.add_points(user_id, transaction_type, points, description)
    return jsonify(result)


@k12_api.route('/api/k12/evaluation', methods=['POST'])
@require_admin
def create_evaluation():
    """创建综合素质评价"""
    data = request.get_json()
    user_id = data.get('user_id')
    eval_period = data.get('eval_period')
    created_by = data.get('created_by')

    if not user_id or not eval_period:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = eval_service.create_evaluation(user_id, eval_period, created_by)
    return jsonify(result)


@k12_api.route('/api/k12/evaluation/item', methods=['PUT'])
@require_admin
def update_eval_item():
    """更新评价项"""
    data = request.get_json()
    eval_id = data.get('eval_id')
    dimension = data.get('dimension')
    item_name = data.get('item_name')
    score = data.get('score')
    comments = data.get('comments', '')
    evidence = data.get('evidence', '')

    if not eval_id or not dimension or not item_name or score is None:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = eval_service.update_eval_item(eval_id, dimension, item_name, score, comments, evidence)
    return jsonify(result)


@k12_api.route('/api/k12/evaluation/<int:user_id>', methods=['GET'])
@require_admin
def get_evaluation(user_id):
    """获取评价结果"""
    eval_period = request.args.get('eval_period')
    result = eval_service.get_evaluation(user_id, eval_period)
    return jsonify(result)


@k12_api.route('/api/k12/evaluation/activity', methods=['POST'])
@require_admin
def add_activity_record():
    """添加活动记录"""
    data = request.get_json()
    user_id = data.get('user_id')
    activity_type = data.get('activity_type')
    activity_name = data.get('activity_name')
    dimension = data.get('dimension')
    score_contribution = data.get('score_contribution', 0)
    description = data.get('description', '')
    evidence = data.get('evidence', '')

    if not user_id or not activity_type or not activity_name or not dimension:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = eval_service.add_activity_record(user_id, activity_type, activity_name, dimension, score_contribution,
    description, evidence)
    return jsonify(result)


@k12_api.route('/api/k12/admission/plan', methods=['POST'])
@require_admin
def set_admission_plan():
    """设置升学计划"""
    data = request.get_json()
    user_id = data.get('user_id')
    exam_type = data.get('exam_type')
    target_province = data.get('target_province')
    estimated_score = data.get('estimated_score')
    interest_type = data.get('interest_type')

    if not user_id or not exam_type or not target_province:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = admission_service.set_admission_plan(user_id, exam_type, target_province, estimated_score, interest_type)
    return jsonify(result)


@k12_api.route('/api/k12/admission/subjects', methods=['POST'])
@require_admin
def recommend_subjects():
    """推荐选科"""
    data = request.get_json()
    user_id = data.get('user_id')
    grade = data.get('grade')

    if not user_id or not grade:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = admission_service.recommend_subjects(user_id, grade)
    return jsonify(result)


@k12_api.route('/api/k12/stats', methods=['GET'])
@require_admin
def get_k12_stats():
    """获取K12统计"""
    result = k12_service.get_statistics()
    return jsonify(result)


@k12_api.route('/api/k12/config/subjects', methods=['GET'])
@require_admin
def get_subjects_config():
    """获取科目配置"""
    return jsonify({'success': True, 'subjects': K12_SUBJECTS, 'grade_groups': GRADE_GROUPS,
    'learning_tiers': LEARNING_TIERS})