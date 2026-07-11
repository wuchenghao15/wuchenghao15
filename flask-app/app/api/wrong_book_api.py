# -*- coding: utf-8 -*-
"""
智能错题本API
提供错题收集、复习管理、薄弱知识点分析等接口
"""

from flask import Blueprint, request, jsonify, session
from app.services.wrong_book_service import wrong_book_service
import logging

logger = logging.getLogger(__name__)

wrong_book_api = Blueprint('wrong_book_api', __name__)


def get_current_user():
    """获取当前用户"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = session.get('admin_user_id')
    return user_id


@wrong_book_api.route('/api/wrong-book/add', methods=['POST'])
def add_wrong_question():
    """
    添加错题
    
    Request Body:
        question_id: 题目ID（可选）
        question_text: 题目内容
        question_type: 题目类型
        subject: 科目
        knowledge_point: 知识点
        user_answer: 用户答案
        correct_answer: 正确答案
        difficulty: 难度
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        
        result = wrong_book_service.add_wrong_question(
            user_id=user_id,
            question_id=data.get('question_id'),
            question_text=data.get('question_text', ''),
            question_type=data.get('question_type', 'single'),
            subject=data.get('subject'),
            knowledge_point=data.get('knowledge_point'),
            user_answer=data.get('user_answer', ''),
            correct_answer=data.get('correct_answer', ''),
            difficulty=data.get('difficulty', 'medium')
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"添加错题失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@wrong_book_api.route('/api/wrong-book/list', methods=['GET'])
def get_wrong_list():
    """
    获取错题列表
    
    Query Parameters:
        subject: 科目（可选）
        knowledge_point: 知识点（可选）
        mastery_level: 掌握程度（可选）
        is_starred: 是否收藏（可选）
        page: 页码（默认1）
        page_size: 每页数量（默认20）
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        subject = request.args.get('subject')
        knowledge_point = request.args.get('knowledge_point')
        mastery_level = request.args.get('mastery_level', type=int)
        is_starred = request.args.get('is_starred')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        if is_starred is not None:
            is_starred = is_starred.lower() == 'true'
        
        result = wrong_book_service.get_wrong_questions(
            user_id=user_id,
            subject=subject,
            knowledge_point=knowledge_point,
            mastery_level=mastery_level,
            is_starred=is_starred,
            page=page,
            page_size=page_size
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取错题列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@wrong_book_api.route('/api/wrong-book/today-review', methods=['GET'])
def get_today_review():
    """
    获取今日待复习题目
    
    Query Parameters:
        count: 题目数量（默认20）
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        count = int(request.args.get('count', 20))
        
        result = wrong_book_service.get_today_review(
            user_id=user_id,
            count=count
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取待复习题目失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@wrong_book_api.route('/api/wrong-book/review', methods=['POST'])
def submit_review():
    """
    提交复习结果
    
    Request Body:
        wrong_question_id: 错题ID
        is_correct: 是否答对
        time_spent: 用时（秒）
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        wrong_question_id = data.get('wrong_question_id')
        is_correct = data.get('is_correct', False)
        time_spent = data.get('time_spent', 0)
        
        if not wrong_question_id:
            return jsonify({'success': False, 'error': '错题ID不能为空'}), 400
        
        result = wrong_book_service.submit_review_result(
            user_id=user_id,
            wrong_question_id=wrong_question_id,
            is_correct=is_correct,
            time_spent=time_spent
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"提交复习结果失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@wrong_book_api.route('/api/wrong-book/weak-points', methods=['GET'])
def get_weak_points():
    """
    获取薄弱知识点
    
    Query Parameters:
        subject: 科目（可选）
        limit: 返回数量（默认20）
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        subject = request.args.get('subject')
        limit = int(request.args.get('limit', 20))
        
        result = wrong_book_service.get_weak_points(
            user_id=user_id,
            subject=subject,
            limit=limit
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取薄弱知识点失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@wrong_book_api.route('/api/wrong-book/statistics', methods=['GET'])
def get_statistics():
    """
    获取错题本统计数据
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        result = wrong_book_service.get_statistics(user_id=user_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@wrong_book_api.route('/api/wrong-book/star/<int:wrong_id>', methods=['POST'])
def toggle_star(wrong_id):
    """
    切换收藏状态
    
    Path Parameters:
        wrong_id: 错题ID
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        result = wrong_book_service.toggle_star(
            user_id=user_id,
            wrong_question_id=wrong_id
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"切换收藏失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@wrong_book_api.route('/api/wrong-book/note/<int:wrong_id>', methods=['POST'])
def update_note(wrong_id):
    """
    更新错题笔记
    
    Path Parameters:
        wrong_id: 错题ID
        
    Request Body:
        note: 笔记内容
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        note = data.get('note', '')
        
        result = wrong_book_service.update_note(
            user_id=user_id,
            wrong_question_id=wrong_id,
            note=note
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"更新笔记失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@wrong_book_api.route('/api/wrong-book/<int:wrong_id>', methods=['DELETE'])
def delete_wrong(wrong_id):
    """
    删除错题
    
    Path Parameters:
        wrong_id: 错题ID
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        result = wrong_book_service.delete_wrong_question(
            user_id=user_id,
            wrong_question_id=wrong_id
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"删除错题失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500