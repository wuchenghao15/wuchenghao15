# -*- coding: utf-8 -*-
"""
AI试卷自动组卷API接口
提供试卷组卷、预览、保存等功能
"""

from flask import Blueprint, jsonify, request, session
import json
import logging

logger = logging.getLogger(__name__)

exam_composition_bp = Blueprint('exam_composition_api', __name__)

try:
    from app.services.ai_exam_composition_service import AIExamCompositionService
    composition_service = AIExamCompositionService()
except ImportError as e:
    logger.error(f"[组卷API] 导入服务失败: {e}")
    composition_service = None


@exam_composition_bp.route('/api/ai/exam-compose', methods=['POST'])
def compose_exam():
    """自动组卷"""
    try:
        if not composition_service:
            return jsonify({"success": False, "error": "组卷服务未初始化"}), 500
        
        data = request.get_json() or {}
        
        subject = data.get('subject', '')
        total_questions = data.get('total_questions', 50)
        types = data.get('types')
        difficulty_ratio = data.get('difficulty_ratio')
        type_ratio = data.get('type_ratio')
        total_score = data.get('total_score', 100)
        exam_name = data.get('exam_name')
        
        if not subject:
            return jsonify({"success": False, "error": "请选择科目"}), 400
        
        exam_data = composition_service.compose_exam(
            subject=subject,
            total_questions=total_questions,
            types=types,
            difficulty_ratio=difficulty_ratio,
            type_ratio=type_ratio,
            total_score=total_score,
            exam_name=exam_name
        )
        
        return jsonify({
            "success": True,
            "data": exam_data
        })
    
    except Exception as e:
        logger.error(f"[组卷API] 组卷失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@exam_composition_bp.route('/api/ai/exam-compose/preview', methods=['POST'])
def preview_exam():
    """预览试卷"""
    try:
        if not composition_service:
            return jsonify({"success": False, "error": "组卷服务未初始化"}), 500
        
        data = request.get_json() or {}
        
        subject = data.get('subject', '')
        total_questions = data.get('total_questions', 50)
        types = data.get('types')
        difficulty_ratio = data.get('difficulty_ratio')
        type_ratio = data.get('type_ratio')
        total_score = data.get('total_score', 100)
        
        if not subject:
            return jsonify({"success": False, "error": "请选择科目"}), 400
        
        exam_data = composition_service.compose_exam(
            subject=subject,
            total_questions=total_questions,
            types=types,
            difficulty_ratio=difficulty_ratio,
            type_ratio=type_ratio,
            total_score=total_score
        )
        
        preview = composition_service.preview_exam(exam_data)
        
        return jsonify({
            "success": True,
            "data": preview
        })
    
    except Exception as e:
        logger.error(f"[组卷API] 预览失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@exam_composition_bp.route('/api/ai/exam-compose/save', methods=['POST'])
def save_exam():
    """保存试卷"""
    try:
        if not composition_service:
            return jsonify({"success": False, "error": "组卷服务未初始化"}), 500
        
        data = request.get_json() or {}
        exam_data = data.get('exam_data')
        
        if not exam_data:
            return jsonify({"success": False, "error": "缺少试卷数据"}), 400
        
        user_id = session.get('user_id', 0)
        exam_id = composition_service.save_exam(exam_data, user_id)
        
        if exam_id > 0:
            return jsonify({
                "success": True,
                "exam_id": exam_id,
                "message": "试卷保存成功"
            })
        else:
            return jsonify({"success": False, "error": "保存试卷失败"}), 500
    
    except Exception as e:
        logger.error(f"[组卷API] 保存失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@exam_composition_bp.route('/api/ai/exam-compose/statistics', methods=['GET'])
def get_statistics():
    """获取组卷统计信息"""
    try:
        if not composition_service:
            return jsonify({"success": False, "error": "组卷服务未初始化"}), 500
        
        subject = request.args.get('subject')
        stats = composition_service.get_exam_statistics(subject)
        
        return jsonify({
            "success": True,
            "data": stats
        })
    
    except Exception as e:
        logger.error(f"[组卷API] 获取统计失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@exam_composition_bp.route('/api/ai/exam-compose/subjects', methods=['GET'])
def get_subjects():
    """获取科目列表"""
    try:
        if not composition_service:
            return jsonify({"success": False, "error": "组卷服务未初始化"}), 500
        
        subjects = composition_service.subjects
        
        return jsonify({
            "success": True,
            "data": subjects
        })
    
    except Exception as e:
        logger.error(f"[组卷API] 获取科目失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@exam_composition_bp.route('/api/ai/exam-compose/types', methods=['GET'])
def get_question_types():
    """获取题型列表"""
    try:
        if not composition_service:
            return jsonify({"success": False, "error": "组卷服务未初始化"}), 500
        
        types = composition_service.question_types
        
        return jsonify({
            "success": True,
            "data": types
        })
    
    except Exception as e:
        logger.error(f"[组卷API] 获取题型失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500