#!/usr/bin/env python3
""" AI智能出题API v2.0 增强功能：错题复习、自适应出题、AI生成题目、题目质量评估、知识点查询 提供智能出题、题目集管理、做题统计等功能的REST API接口 """

from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin, allow_guest_access
from app.ai.ai_question_generator import ai_question_generator

ai_question_api = Bluelogger.info('ai_question_api', __name__)


@ai_question_api.route('/api/ai/question/generate', methods=['POST'])
@require_login
def generate_questions():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    count = int(data.get('count', 10))
    difficulty = data.get('difficulty', 'medium')
    topic = data.get('topic')
    use_ai = data.get('use_ai', False)

    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400

    result = ai_question_generator.generate_question_set(user_id, subject, count, difficulty, topic, use_ai)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 400


@ai_question_api.route('/api/ai/question/set/<set_id>', methods=['GET'])
@require_login
def get_question_set(set_id):
    result = ai_question_generator.get_question_set(set_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 404


@ai_question_api.route('/api/ai/question/set/<set_id>', methods=['DELETE'])
@require_login
def delete_question_set(set_id):
    result = ai_question_generator.delete_question_set(set_id)
    return jsonify(result)


@ai_question_api.route('/api/ai/question/statistics', methods=['GET'])
@require_login
def get_statistics():
    user_id = request.args.get('user_id')
    subject = request.args.get('subject')

    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400

    result = ai_question_generator.get_user_statistics(user_id, subject)
    return jsonify({'success': True, 'data': result})


@ai_question_api.route('/api/ai/question/statistics', methods=['POST'])
@require_login
def update_statistics():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    topic = data.get('topic')
    question_type = data.get('question_type', 'practice')
    is_correct = data.get('is_correct', True)

    if not user_id or not subject or not topic:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400

    result = ai_question_generator.update_statistics(user_id, subject, topic, question_type, is_correct)
    return jsonify(result)


@ai_question_api.route('/api/ai/question/topics/<subject>', methods=['GET'])
@require_login
def get_topics(subject):
    result = ai_question_generator.get_subject_topics(subject)
    return jsonify({'success': True, 'data': result})


@ai_question_api.route('/api/ai/question/subjects', methods=['GET'])
@allow_guest_access
def get_subjects():
    subjects = ai_question_generator.SUBJECTS
    return jsonify({'success': True, 'data': {'subjects': subjects}})


@ai_question_api.route('/api/ai/question/review', methods=['POST'])
@require_login
def generate_review_set():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    count = int(data.get('count', 10))

    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400

    result = ai_question_generator.generate_review_set(user_id, subject, count)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 400


@ai_question_api.route('/api/ai/question/adaptive', methods=['POST'])
@require_login
def generate_adaptive_questions():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    count = int(data.get('count', 10))
    use_ai = data.get('use_ai', False)

    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400

    result = ai_question_generator.generate_question_set(user_id, subject, count, difficulty=None, topic=None,
    use_ai=use_ai)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 400


@ai_question_api.route('/api/ai/question/ai_generate', methods=['POST'])
@require_login
def generate_ai_questions():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    count = int(data.get('count', 10))
    difficulty = data.get('difficulty', 'medium')
    topic = data.get('topic')

    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400

    result = ai_question_generator.generate_question_set(user_id, subject, count, difficulty, topic, use_ai=True)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 400


@ai_question_api.route('/api/ai/question/overall_stats', methods=['GET'])
@require_admin
def get_overall_stats():
    result = ai_question_generator.get_overall_stats()
    return jsonify({'success': True, 'data': result})


@ai_question_api.route('/api/ai/question/weaknesses', methods=['POST'])
@require_login
def get_user_weaknesses():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')

    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400

    weaknesses = ai_question_generator._analyze_user_weaknesses(user_id, subject)
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'subject': subject,
            'weaknesses': weaknesses,
            'count': len(weaknesses)
        }
    })


@ai_question_api.route('/api/ai/question/difficulty', methods=['POST'])
@require_login
def get_adaptive_difficulty():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')

    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400

    difficulty = ai_question_generator._calculate_adaptive_difficulty(user_id, subject)
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'subject': subject,
            'adaptive_difficulty': difficulty
        }
    })


@ai_question_api.route('/api/ai/question/export', methods=['POST'])
@require_admin
def export_questions():
    data = request.get_json() or {}
    questions = data.get('questions', [])

    if not questions:
        return jsonify({'success': False, 'error': '没有可导出的题目'}), 400

    import json
    import datetime
    from flask import Response

    export_data = {
        'export_time': datetime.datetime.now().isoformat(),
        'question_count': len(questions),
        'questions': questions
    }

    response = Response(
        json.dumps(export_data, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename=questions_export_{datetime.datetime.now().strftime( "%Y%m%d")}.json'
        }
    )
    return response


@ai_question_api.route('/api/ai/question/batch', methods=['POST'])
@require_admin
def generate_batch_questions():
    data = request.get_json() or {}
    user_id = data.get('user_id', '0')
    subjects = data.get('subjects', [])
    counts = data.get('counts', [])
    difficulty = data.get('difficulty', 'medium')
    use_ai = data.get('use_ai', False)

    if not subjects or not counts:
        return jsonify({'success': False, 'error': '科目和数量不能为空'}), 400

    if len(subjects) != len(counts):
        return jsonify({'success': False, 'error': '科目和数量数量不匹配'}), 400

    result = ai_question_generator.generate_batch_questions(user_id, subjects, counts, difficulty, use_ai)
    return jsonify({'success': True, 'data': result})


@ai_question_api.route('/api/ai/question/knowledge_stats', methods=['GET'])
@require_login
def get_knowledge_stats():
    subject = request.args.get('subject')
    result = ai_question_generator.get_knowledge_point_stats(subject)
    return jsonify({'success': True, 'data': result})


@ai_question_api.route('/api/ai/question/daily_stats', methods=['GET'])
@require_admin
def get_daily_stats():
    days = int(request.args.get('days', 30))
    result = ai_question_generator.get_daily_generation_stats(days)
    return jsonify({'success': True, 'data': result})