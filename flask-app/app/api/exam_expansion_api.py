#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试系统拓展API模块
提供考试预约、错题重做、考试笔记、考试收藏、成绩对比分析等功能的API接口
"""

from flask import Blueprint, jsonify, request, session
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

exam_expansion_api = Blueprint('exam_expansion_api', __name__, url_prefix='/api/exam/expansion')


def get_user_id() -> str:
    """获取当前用户ID"""
    return session.get('user_id', '')


def require_login():
    """检查登录状态"""
    if not get_user_id():
        return jsonify({'success': False, 'error': '请先登录'}), 401
    return None


# ==================== 考试预约API ====================

@exam_expansion_api.route('/appointments', methods=['GET'])
def get_appointments():
    """获取用户预约列表"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        status = request.args.get('status')
        appointments = service.get_user_appointments(get_user_id(), status)
        
        return jsonify({
            'success': True,
            'data': appointments,
            'count': len(appointments)
        })
    except Exception as e:
        logger.error(f"获取预约列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/appointments', methods=['POST'])
def create_appointment():
    """创建考试预约"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        data = request.get_json()
        exam_id = data.get('exam_id')
        scheduled_time = data.get('scheduled_time')
        
        if not exam_id or not scheduled_time:
            return jsonify({'success': False, 'error': '缺少必填参数'}), 400
        
        service = get_exam_expansion_service()
        appointment_id = service.create_appointment(get_user_id(), exam_id, scheduled_time)
        
        if appointment_id:
            return jsonify({
                'success': True,
                'appointment_id': appointment_id,
                'message': '预约成功'
            }), 201
        else:
            return jsonify({'success': False, 'error': '预约失败'}), 500
    except Exception as e:
        logger.error(f"创建预约失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/appointments/<appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    """更新预约状态"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({'success': False, 'error': '缺少状态参数'}), 400
        
        service = get_exam_expansion_service()
        success = service.update_appointment_status(appointment_id, status)
        
        if success:
            return jsonify({'success': True, 'message': '状态更新成功'})
        else:
            return jsonify({'success': False, 'error': '更新失败'}), 500
    except Exception as e:
        logger.error(f"更新预约状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/appointments/<appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    """取消预约"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        success = service.delete_appointment(appointment_id)
        
        if success:
            return jsonify({'success': True, 'message': '预约已取消'})
        else:
            return jsonify({'success': False, 'error': '取消失败'}), 500
    except Exception as e:
        logger.error(f"取消预约失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 错题重做API ====================

@exam_expansion_api.route('/wrong-questions/review', methods=['GET'])
def get_wrong_questions_for_review():
    """获取待复习错题"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        limit = int(request.args.get('limit', 10))
        questions = service.get_wrong_questions_for_review(get_user_id(), limit)
        
        return jsonify({
            'success': True,
            'data': questions,
            'count': len(questions)
        })
    except Exception as e:
        logger.error(f"获取待复习错题失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/wrong-questions/review', methods=['POST'])
def record_review():
    """记录错题复习"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        data = request.get_json()
        question_id = data.get('question_id')
        exam_id = data.get('exam_id')
        mastered = data.get('mastered', False)
        notes = data.get('notes', '')
        
        if not question_id or not exam_id:
            return jsonify({'success': False, 'error': '缺少必填参数'}), 400
        
        service = get_exam_expansion_service()
        success = service.record_wrong_question_review(get_user_id(), question_id, exam_id, mastered, notes)
        
        if success:
            return jsonify({'success': True, 'message': '复习记录已保存'})
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500
    except Exception as e:
        logger.error(f"记录错题复习失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/wrong-questions/stats', methods=['GET'])
def get_review_stats():
    """获取错题复习统计"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        stats = service.get_review_stats(get_user_id())
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logger.error(f"获取错题复习统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 考试笔记API ====================

@exam_expansion_api.route('/notes', methods=['GET'])
def get_notes():
    """获取考试笔记"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        exam_id = request.args.get('exam_id')
        notes = service.get_exam_notes(get_user_id(), exam_id)
        
        return jsonify({
            'success': True,
            'data': notes,
            'count': len(notes)
        })
    except Exception as e:
        logger.error(f"获取考试笔记失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/notes', methods=['POST'])
def add_note():
    """添加考试笔记"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        data = request.get_json()
        exam_id = data.get('exam_id')
        content = data.get('content')
        question_id = data.get('question_id')
        note_type = data.get('note_type', 'general')
        
        if not exam_id or not content:
            return jsonify({'success': False, 'error': '缺少必填参数'}), 400
        
        service = get_exam_expansion_service()
        note_id = service.add_exam_note(get_user_id(), exam_id, content, question_id, note_type)
        
        if note_id:
            return jsonify({
                'success': True,
                'note_id': note_id,
                'message': '笔记添加成功'
            }), 201
        else:
            return jsonify({'success': False, 'error': '添加失败'}), 500
    except Exception as e:
        logger.error(f"添加考试笔记失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """删除考试笔记"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        success = service.delete_exam_note(note_id)
        
        if success:
            return jsonify({'success': True, 'message': '笔记已删除'})
        else:
            return jsonify({'success': False, 'error': '删除失败'}), 500
    except Exception as e:
        logger.error(f"删除考试笔记失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 考试收藏API ====================

@exam_expansion_api.route('/favorites', methods=['GET'])
def get_favorites():
    """获取用户收藏"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        folder_name = request.args.get('folder_name', '')
        favorites = service.get_user_favorites(get_user_id(), folder_name)
        
        return jsonify({
            'success': True,
            'data': favorites,
            'count': len(favorites)
        })
    except Exception as e:
        logger.error(f"获取用户收藏失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/favorites', methods=['POST'])
def add_favorite():
    """收藏考试"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        data = request.get_json()
        exam_id = data.get('exam_id')
        folder_name = data.get('folder_name', '')
        
        if not exam_id:
            return jsonify({'success': False, 'error': '缺少考试ID'}), 400
        
        service = get_exam_expansion_service()
        success = service.add_exam_favorite(get_user_id(), exam_id, folder_name)
        
        if success:
            return jsonify({'success': True, 'message': '收藏成功'})
        else:
            return jsonify({'success': False, 'error': '收藏失败'}), 500
    except Exception as e:
        logger.error(f"收藏考试失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/favorites', methods=['DELETE'])
def remove_favorite():
    """取消收藏"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        data = request.get_json()
        exam_id = data.get('exam_id')
        
        if not exam_id:
            return jsonify({'success': False, 'error': '缺少考试ID'}), 400
        
        service = get_exam_expansion_service()
        success = service.remove_exam_favorite(get_user_id(), exam_id)
        
        if success:
            return jsonify({'success': True, 'message': '已取消收藏'})
        else:
            return jsonify({'success': False, 'error': '取消收藏失败'}), 500
    except Exception as e:
        logger.error(f"取消收藏失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/favorites/folders', methods=['GET'])
def get_favorite_folders():
    """获取收藏文件夹"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        folders = service.get_favorite_folders(get_user_id())
        
        return jsonify({'success': True, 'data': folders})
    except Exception as e:
        logger.error(f"获取收藏文件夹失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 成绩对比分析API ====================

@exam_expansion_api.route('/scores/compare', methods=['POST'])
def compare_scores():
    """成绩对比分析"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        data = request.get_json()
        exam_id = data.get('exam_id')
        current_score = data.get('current_score')
        
        if not exam_id or current_score is None:
            return jsonify({'success': False, 'error': '缺少必填参数'}), 400
        
        service = get_exam_expansion_service()
        result = service.compare_scores(get_user_id(), exam_id, float(current_score))
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"成绩对比分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/scores/history', methods=['GET'])
def get_score_history():
    """获取成绩历史"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        exam_id = request.args.get('exam_id')
        limit = int(request.args.get('limit', 10))
        history = service.get_score_history(get_user_id(), exam_id, limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取成绩历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 考试标签API ====================

@exam_expansion_api.route('/tags', methods=['GET'])
def get_tags():
    """获取考试标签"""
    exam_id = request.args.get('exam_id')
    
    if not exam_id:
        return jsonify({'success': False, 'error': '缺少考试ID'}), 400
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        tags = service.get_exam_tags(exam_id)
        
        return jsonify({'success': True, 'data': tags})
    except Exception as e:
        logger.error(f"获取考试标签失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/tags', methods=['POST'])
def add_tag():
    """添加考试标签"""
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        data = request.get_json()
        exam_id = data.get('exam_id')
        tag_name = data.get('tag_name')
        tag_color = data.get('tag_color', '#6366f1')
        
        if not exam_id or not tag_name:
            return jsonify({'success': False, 'error': '缺少必填参数'}), 400
        
        service = get_exam_expansion_service()
        success = service.add_exam_tag(exam_id, tag_name, tag_color)
        
        if success:
            return jsonify({'success': True, 'message': '标签添加成功'})
        else:
            return jsonify({'success': False, 'error': '添加失败'}), 500
    except Exception as e:
        logger.error(f"添加考试标签失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_expansion_api.route('/tags/<tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """删除考试标签"""
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        success = service.delete_exam_tag(tag_id)
        
        if success:
            return jsonify({'success': True, 'message': '标签已删除'})
        else:
            return jsonify({'success': False, 'error': '删除失败'}), 500
    except Exception as e:
        logger.error(f"删除考试标签失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 综合统计API ====================

@exam_expansion_api.route('/stats', methods=['GET'])
def get_expansion_stats():
    """获取拓展功能统计"""
    error = require_login()
    if error:
        return error
    
    try:
        from app.services.exam_expansion_service import get_exam_expansion_service
        
        service = get_exam_expansion_service()
        
        review_stats = service.get_review_stats(get_user_id())
        favorites = service.get_user_favorites(get_user_id())
        appointments = service.get_user_appointments(get_user_id())
        notes = service.get_exam_notes(get_user_id())
        
        return jsonify({
            'success': True,
            'data': {
                'review': review_stats,
                'favorites_count': len(favorites),
                'appointments_count': len(appointments),
                'notes_count': len(notes)
            }
        })
    except Exception as e:
        logger.error(f"获取拓展统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500