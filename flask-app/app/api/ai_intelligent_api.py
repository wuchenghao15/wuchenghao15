# -*- coding: utf-8 -*-
"""
AI智能升级API
提供系统智能分析、智能推荐、智能运维、智能优化等接口
"""

from flask import Blueprint, request, jsonify, session
from app.services.ai_intelligent_upgrade_service import ai_intelligent_upgrade_service
import logging

logger = logging.getLogger(__name__)

ai_intelligent_api = Blueprint('ai_intelligent_api', __name__)


def get_current_user():
    """获取当前用户"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = session.get('admin_user_id')
    return user_id


@ai_intelligent_api.route('/api/ai/intelligent/health-analysis', methods=['POST'])
def health_analysis():
    """AI智能系统健康分析"""
    try:
        result = ai_intelligent_upgrade_service.analyze_system_health()
        return jsonify(result)
    except Exception as e:
        logger.error(f"健康分析失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_intelligent_api.route('/api/ai/intelligent/recommendations', methods=['GET', 'POST'])
def smart_recommendations():
    """AI智能推荐"""
    try:
        user_id = get_current_user()
        limit = int(request.args.get('limit', 10))
        result = ai_intelligent_upgrade_service.generate_smart_recommendations(
            user_id=user_id, limit=limit
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"生成推荐失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_intelligent_api.route('/api/ai/intelligent/maintenance', methods=['POST'])
def run_maintenance():
    """执行AI智能运维"""
    try:
        result = ai_intelligent_upgrade_service.run_intelligent_maintenance()
        return jsonify(result)
    except Exception as e:
        logger.error(f"智能运维失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_intelligent_api.route('/api/ai/intelligent/optimization-suggestions', methods=['GET', 'POST'])
def optimization_suggestions():
    """AI优化建议"""
    try:
        result = ai_intelligent_upgrade_service.generate_optimization_suggestions()
        return jsonify(result)
    except Exception as e:
        logger.error(f"生成优化建议失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_intelligent_api.route('/api/ai/intelligent/predictions', methods=['GET', 'POST'])
def system_predictions():
    """AI系统趋势预测"""
    try:
        result = ai_intelligent_upgrade_service.predict_system_trends()
        return jsonify(result)
    except Exception as e:
        logger.error(f"趋势预测失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_intelligent_api.route('/api/ai/intelligent/statistics', methods=['GET'])
def system_statistics():
    """获取系统全面统计"""
    try:
        result = ai_intelligent_upgrade_service.get_system_statistics()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
