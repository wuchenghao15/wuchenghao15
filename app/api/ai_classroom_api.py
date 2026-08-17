#!/usr/bin/env python3
"""
AI课堂互动API接口
提供课堂互动相关的REST API服务
"""

from flask import Blueprint, request, jsonify
from app.ai.ai_classroom_interaction import ai_classroom_interaction

ai_classroom_api = Bluelogger.info('ai_classroom_api', __name__, url_prefix='/api/ai/classroom')

@ai_classroom_api.route('/session/start', methods=['POST'])
def start_session():
    """开始课堂会话"""
    data = request.get_json()
    course_id = data.get('course_id', '')
    course_name = data.get('course_name', '')
    teacher_id = data.get('teacher_id', '')
    teacher_name = data.get('teacher_name', '')
    
    if not course_id or not teacher_id:
        return jsonify({'success': False, 'error': '课程ID和教师ID不能为空'}), 400
    
    result = ai_classroom_interaction.start_classroom_session(course_id, course_name, teacher_id, teacher_name)
    return jsonify(result)

@ai_classroom_api.route('/session/end', methods=['POST'])
def end_session():
    """结束课堂会话"""
    data = request.get_json()
    session_id = data.get('session_id', '')
    
    if not session_id:
        return jsonify({'success': False, 'error': '会话ID不能为空'}), 400
    
    result = ai_classroom_interaction.end_classroom_session(session_id)
    return jsonify(result)

@ai_classroom_api.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话信息"""
    result = ai_classroom_interaction.get_session_info(session_id)
    
    if result:
        return jsonify({'success': True, 'data': result})
    else:
        return jsonify({'success': False, 'error': '会话不存在'}), 404

@ai_classroom_api.route('/attendance/check-in', methods=['POST'])
def check_in():
    """课堂签到"""
    data = request.get_json()
    session_id = data.get('session_id', '')
    user_id = data.get('user_id', '')
    user_name = data.get('user_name', '')
    
    if not session_id or not user_id:
        return jsonify({'success': False, 'error': '会话ID和用户ID不能为空'}), 400
    
    result = ai_classroom_interaction.check_in(session_id, user_id, user_name)
    return jsonify(result)

@ai_classroom_api.route('/attendance/<session_id>', methods=['GET'])
def get_attendance(session_id):
    """获取签到信息"""
    result = ai_classroom_interaction.get_attendance(session_id)
    return jsonify(result)

@ai_classroom_api.route('/interaction/add', methods=['POST'])
def add_interaction():
    """添加互动"""
    data = request.get_json()
    session_id = data.get('session_id', '')
    user_id = data.get('user_id', '')
    user_name = data.get('user_name', '')
    interaction_type = data.get('interaction_type', 'discussion')
    content = data.get('content', '')
    parent_id = data.get('parent_id', '')
    
    if not session_id or not user_id or not content:
        return jsonify({'success': False, 'error': '会话ID、用户ID和内容不能为空'}), 400
    
    result = ai_classroom_interaction.add_interaction(session_id, user_id, user_name, interaction_type, content,
    parent_id)
    return jsonify(result)

@ai_classroom_api.route('/interactions/<session_id>', methods=['GET'])
def get_interactions(session_id):
    """获取互动列表"""
    interaction_type = request.args.get('type', '')
    result = ai_classroom_interaction.get_interactions(session_id, interaction_type)
    return jsonify(result)

@ai_classroom_api.route('/quiz/create', methods=['POST'])
def create_quiz():
    """创建测验"""
    data = request.get_json()
    session_id = data.get('session_id', '')
    question = data.get('question', '')
    options = data.get('options', [])
    correct_answer = data.get('correct_answer', '')
    quiz_type = data.get('quiz_type', 'single_choice')
    time_limit = data.get('time_limit', 60)
    
    if not session_id or not question or not options or not correct_answer:
        return jsonify({'success': False, 'error': '会话ID、题目、选项和正确答案不能为空'}), 400
    
    result = ai_classroom_interaction.create_quiz(session_id, question, options, correct_answer, quiz_type, time_limit)
    return jsonify(result)

@ai_classroom_api.route('/quiz/answer', methods=['POST'])
def answer_quiz():
    """回答测验"""
    data = request.get_json()
    quiz_id = data.get('quiz_id', '')
    user_id = data.get('user_id', '')
    answer = data.get('answer', '')
    
    if not quiz_id or not user_id or not answer:
        return jsonify({'success': False, 'error': '测验ID、用户ID和答案不能为空'}), 400
    
    result = ai_classroom_interaction.answer_quiz(quiz_id, user_id, answer)
    return jsonify(result)

@ai_classroom_api.route('/quiz/results/<quiz_id>', methods=['GET'])
def get_quiz_results(quiz_id):
    """获取测验结果"""
    result = ai_classroom_interaction.get_quiz_results(quiz_id)
    return jsonify(result)

@ai_classroom_api.route('/poll/create', methods=['POST'])
def create_poll():
    """创建投票"""
    data = request.get_json()
    session_id = data.get('session_id', '')
    question = data.get('question', '')
    options = data.get('options', [])
    
    if not session_id or not question or not options:
        return jsonify({'success': False, 'error': '会话ID、问题和选项不能为空'}), 400
    
    result = ai_classroom_interaction.create_poll(session_id, question, options)
    return jsonify(result)

@ai_classroom_api.route('/poll/vote', methods=['POST'])
def vote_poll():
    """投票"""
    data = request.get_json()
    poll_id = data.get('poll_id', '')
    user_id = data.get('user_id', '')
    answer = data.get('answer', '')
    
    if not poll_id or not user_id or not answer:
        return jsonify({'success': False, 'error': '投票ID、用户ID和答案不能为空'}), 400
    
    result = ai_classroom_interaction.vote_poll(poll_id, user_id, answer)
    return jsonify(result)

@ai_classroom_api.route('/poll/results/<poll_id>', methods=['GET'])
def get_poll_results(poll_id):
    """获取投票结果"""
    result = ai_classroom_interaction.get_poll_results(poll_id)
    return jsonify(result)