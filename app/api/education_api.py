#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教育综合API接口
整合教学大纲、题库同步、学习追踪相关API
"""

from flask import Blueprint, request, jsonify
from functools import wraps

education_api = Bluelogger.info('education_api', __name__)


def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        role = session.get('role', 'guest')
        if role not in ['admin', 'super_admin', 'teacher']:
            return jsonify({'success': False, 'error': '权限不足'}), 403
        return f(*args, **kwargs)
    return decorated_function


@education_api.route('/api/education/curriculum', methods=['POST'])
@require_admin
def create_curriculum():
    from curriculum_service import curriculum_service
    data = request.json
    result = curriculum_service.create_curriculum(
        name=data.get('name'),
        subject=data.get('subject'),
        education_level=data.get('education_level'),
        grade=data.get('grade'),
        description=data.get('description', ''),
        created_by=data.get('created_by')
    )
    return jsonify(result)


@education_api.route('/api/education/curriculum/list', methods=['GET'])
@require_admin
def list_curricula():
    from curriculum_service import curriculum_service
    subject = request.args.get('subject')
    education_level = request.args.get('education_level')
    grade = request.args.get('grade')
    curricula = curriculum_service.list_curricula(subject, education_level, grade)
    return jsonify({'success': True, 'data': curricula})


@education_api.route('/api/education/curriculum/<curriculum_id>', methods=['GET'])
@require_admin
def get_curriculum(curriculum_id):
    from curriculum_service import curriculum_service
    curriculum = curriculum_service.get_curriculum(curriculum_id)
    if curriculum:
        return jsonify({'success': True, 'data': curriculum})
    else:
        return jsonify({'success': False, 'error': '大纲不存在'})


@education_api.route('/api/education/curriculum/<curriculum_id>', methods=['PUT'])
@require_admin
def update_curriculum(curriculum_id):
    from curriculum_service import curriculum_service
    data = request.json
    result = curriculum_service.update_curriculum(curriculum_id, **data)
    return jsonify(result)


@education_api.route('/api/education/curriculum/<curriculum_id>', methods=['DELETE'])
@require_admin
def delete_curriculum(curriculum_id):
    from curriculum_service import curriculum_service
    result = curriculum_service.delete_curriculum(curriculum_id)
    return jsonify(result)


@education_api.route('/api/education/curriculum/<curriculum_id>/chapter', methods=['POST'])
@require_admin
def add_chapter(curriculum_id):
    from curriculum_service import curriculum_service
    data = request.json
    result = curriculum_service.add_chapter(
        curriculum_id=curriculum_id,
        name=data.get('name'),
        chapter_number=data.get('chapter_number', 0),
        description=data.get('description', ''),
        estimated_hours=data.get('estimated_hours', 0),
        prerequisite_chapter=data.get('prerequisite_chapter'),
        is_required=data.get('is_required', True)
    )
    return jsonify(result)


@education_api.route('/api/education/curriculum/<curriculum_id>/kp', methods=['POST'])
@require_admin
def add_knowledge_point(curriculum_id):
    from curriculum_service import curriculum_service
    data = request.json
    result = curriculum_service.add_knowledge_point(
        chapter_id=data.get('chapter_id'),
        curriculum_id=curriculum_id,
        name=data.get('name'),
        knowledge_code=data.get('knowledge_code', ''),
        difficulty=data.get('difficulty', 'medium'),
        mastery_level=data.get('mastery_level', 'basic'),
        description=data.get('description', ''),
        learning_objectives=data.get('learning_objectives', ''),
        teaching_hours=data.get('teaching_hours', 1),
        assessment_method=data.get('assessment_method', ''),
        sequence_number=data.get('sequence_number', 0),
        is_core=data.get('is_core', False)
    )
    return jsonify(result)


@education_api.route('/api/education/curriculum/<curriculum_id>/kp/list', methods=['GET'])
@require_admin
def get_knowledge_points(curriculum_id):
    from curriculum_service import curriculum_service
    kps = curriculum_service.get_knowledge_points_by_curriculum(curriculum_id)
    return jsonify({'success': True, 'data': kps})


@education_api.route('/api/education/curriculum/<curriculum_id>/standard', methods=['POST'])
@require_admin
def add_standard(curriculum_id):
    from curriculum_service import curriculum_service
    data = request.json
    result = curriculum_service.add_standard(
        curriculum_id=curriculum_id,
        standard_code=data.get('standard_code'),
        standard_name=data.get('standard_name'),
        description=data.get('description', ''),
        domain=data.get('domain', ''),
        cluster=data.get('cluster', '')
    )
    return jsonify(result)


@education_api.route('/api/education/curriculum/<curriculum_id>/version', methods=['POST'])
@require_admin
def generate_version(curriculum_id):
    from curriculum_service import curriculum_service
    data = request.json
    result = curriculum_service.generate_version(
        curriculum_id=curriculum_id,
        change_description=data.get('change_description'),
        changed_by=data.get('changed_by')
    )
    return jsonify(result)


@education_api.route('/api/education/sync/map', methods=['POST'])
@require_admin
def map_question_to_kp():
    from question_bank_sync_service import question_bank_sync_service
    data = request.json
    result = question_bank_sync_service.map_question_to_kp(
        question_id=data.get('question_id'),
        kp_id=data.get('kp_id'),
        curriculum_id=data.get('curriculum_id'),
        mapping_type=data.get('mapping_type', 'manual'),
        confidence=data.get('confidence', 0.8)
    )
    return jsonify(result)


@education_api.route('/api/education/sync/batch_map', methods=['POST'])
@require_admin
def batch_map_questions():
    from question_bank_sync_service import question_bank_sync_service
    data = request.json
    result = question_bank_sync_service.batch_map_questions(
        question_ids=data.get('question_ids', []),
        kp_id=data.get('kp_id'),
        curriculum_id=data.get('curriculum_id')
    )
    return jsonify(result)


@education_api.route('/api/education/sync/exam/<exam_id>/curriculum/<curriculum_id>', methods=['POST'])
@require_admin
def sync_exam_with_curriculum(exam_id, curriculum_id):
    from question_bank_sync_service import question_bank_sync_service
    result = question_bank_sync_service.sync_exam_with_curriculum(exam_id, curriculum_id)
    return jsonify(result)


@education_api.route('/api/education/sync/kp/<kp_id>/generate', methods=['POST'])
@require_admin
def generate_questions_by_kp(kp_id):
    from question_bank_sync_service import question_bank_sync_service
    data = request.json
    result = question_bank_sync_service.generate_questions_by_kp(
        kp_id=kp_id,
        count=data.get('count', 5),
        difficulty=data.get('difficulty', 'medium')
    )
    return jsonify(result)


@education_api.route('/api/education/sync/curriculum/<curriculum_id>/generate_exam', methods=['POST'])
@require_admin
def generate_exam_by_curriculum(curriculum_id):
    from question_bank_sync_service import question_bank_sync_service
    data = request.json
    result = question_bank_sync_service.generate_exam_by_curriculum(
        curriculum_id=curriculum_id,
        exam_name=data.get('exam_name'),
        total_questions=data.get('total_questions', 20),
        duration_minutes=data.get('duration_minutes', 60),
        creator_id=data.get('creator_id')
    )
    return jsonify(result)


@education_api.route('/api/education/sync/curriculum/<curriculum_id>/stats', methods=['GET'])
@require_admin
def get_curriculum_stats(curriculum_id):
    from question_bank_sync_service import question_bank_sync_service
    stats = question_bank_sync_service.get_curriculum_stats(curriculum_id)
    return jsonify({'success': True, 'data': stats})


@education_api.route('/api/education/sync/tasks', methods=['GET'])
@require_admin
def list_sync_tasks():
    from question_bank_sync_service import question_bank_sync_service
    status = request.args.get('status')
    tasks = question_bank_sync_service.list_sync_tasks(status)
    return jsonify({'success': True, 'data': tasks})


@education_api.route('/api/education/learning/start', methods=['POST'])
@require_admin
def start_curriculum_learning():
    from learning_curriculum_service import learning_curriculum_service
    data = request.json
    result = learning_curriculum_service.start_curriculum(
        user_id=data.get('user_id'),
        curriculum_id=data.get('curriculum_id')
    )
    return jsonify(result)


@education_api.route('/api/education/learning/kp_progress', methods=['PUT'])
@require_admin
def update_kp_progress():
    from learning_curriculum_service import learning_curriculum_service
    data = request.json
    result = learning_curriculum_service.update_kp_progress(
        user_id=data.get('user_id'),
        kp_id=data.get('kp_id'),
        correct=data.get('correct'),
        total_attempts=data.get('total_attempts', 1)
    )
    return jsonify(result)


@education_api.route('/api/education/learning/chapter_progress', methods=['PUT'])
@require_admin
def update_chapter_progress():
    from learning_curriculum_service import learning_curriculum_service
    data = request.json
    result = learning_curriculum_service.update_chapter_progress(
        user_id=data.get('user_id'),
        chapter_id=data.get('chapter_id'),
        progress=data.get('progress')
    )
    return jsonify(result)


@education_api.route('/api/education/learning/user/<user_id>/progress', methods=['GET'])
@require_admin
def get_user_curriculum_progress(user_id):
    from learning_curriculum_service import learning_curriculum_service
    curriculum_id = request.args.get('curriculum_id')
    result = learning_curriculum_service.get_curriculum_progress(int(user_id), curriculum_id)
    return jsonify(result)


@education_api.route('/api/education/learning/user/<user_id>/kp_progress', methods=['GET'])
@require_admin
def get_user_kp_progress(user_id):
    from learning_curriculum_service import learning_curriculum_service
    kp_id = request.args.get('kp_id')
    result = learning_curriculum_service.get_kp_progress(int(user_id), kp_id)
    return jsonify(result)


@education_api.route('/api/education/learning/user/<user_id>/recommendations', methods=['GET'])
@require_admin
def get_user_recommendations(user_id):
    from learning_curriculum_service import learning_curriculum_service
    curriculum_id = request.args.get('curriculum_id')
    result = learning_curriculum_service.get_recommendations(int(user_id), curriculum_id)
    return jsonify(result)


@education_api.route('/api/education/learning/user/<user_id>/recommendations/generate', methods=['POST'])
@require_admin
def generate_user_recommendations(user_id):
    from learning_curriculum_service import learning_curriculum_service
    data = request.json
    result = learning_curriculum_service.generate_recommendations(
        user_id=int(user_id),
        curriculum_id=data.get('curriculum_id')
    )
    return jsonify(result)


@education_api.route('/api/education/learning/user/<user_id>/assessment', methods=['POST'])
@require_admin
def record_assessment(user_id):
    from learning_curriculum_service import learning_curriculum_service
    data = request.json
    result = learning_curriculum_service.record_assessment(
        user_id=int(user_id),
        curriculum_id=data.get('curriculum_id'),
        exam_id=data.get('exam_id'),
        overall_score=data.get('overall_score', 0),
        kp_scores=data.get('kp_scores'),
        strengths=data.get('strengths'),
        weaknesses=data.get('weaknesses'),
        recommendations=data.get('recommendations')
    )
    return jsonify(result)


@education_api.route('/api/education/learning/user/<user_id>/assessment/history', methods=['GET'])
@require_admin
def get_user_assessment_history(user_id):
    from learning_curriculum_service import learning_curriculum_service
    curriculum_id = request.args.get('curriculum_id')
    result = learning_curriculum_service.get_assessment_history(int(user_id), curriculum_id)
    return jsonify(result)


@education_api.route('/api/education/learning/user/<user_id>/stats', methods=['GET'])
@require_admin
def get_user_curriculum_stats(user_id):
    from learning_curriculum_service import learning_curriculum_service
    stats = learning_curriculum_service.get_curriculum_stats_for_user(int(user_id))
    return jsonify({'success': True, 'data': stats})


@education_api.route('/api/education/stats', methods=['GET'])
@require_admin
def get_education_stats():
    from curriculum_service import curriculum_service
    from question_bank_sync_service import question_bank_sync_service
    
    curricula = curriculum_service.list_curricula()
    total_curricula = len(curricula)
    
    total_kps = 0
    total_chapters = 0
    for cur in curricula:
        kps = curriculum_service.get_knowledge_points_by_curriculum(cur['curriculum_id'])
        total_kps += len(kps)
    
    return jsonify({
        'success': True,
        'total_curricula': total_curricula,
        'total_knowledge_points': total_kps,
        'total_chapters': total_chapters
    })