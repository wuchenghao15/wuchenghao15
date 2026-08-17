#!/usr/bin/env python3
"""
AI学习预警API
提供学习预警检测、预警管理、风险画像等功能的REST API接口
"""

from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_learning_alert import ai_learning_alert

ai_alert_api = Bluelogger.info('ai_alert_api', __name__)

@ai_alert_api.route('/api/ai/alert/analyze', methods=['POST'])
@require_login
def analyze_student():
    """分析学生学习状态"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_learning_alert.analyze_student(user_id)
    return jsonify({'success': True, 'data': result})

@ai_alert_api.route('/api/ai/alert/user/<user_id>', methods=['GET'])
@require_login
def get_user_alerts(user_id):
    """获取用户预警列表"""
    status = request.args.get('status')
    alerts = ai_learning_alert.get_alerts_by_user(user_id, status)
    return jsonify({'success': True, 'data': alerts})

@ai_alert_api.route('/api/ai/alert/<alert_id>/resolve', methods=['POST'])
@require_login
def resolve_alert(alert_id):
    """解决预警"""
    data = request.get_json() or {}
    resolved_by = data.get('resolved_by', '')
    
    success = ai_learning_alert.resolve_alert(alert_id, resolved_by)
    if success:
        return jsonify({'success': True, 'message': '预警已解决'})
    return jsonify({'success': False, 'error': '预警不存在或已解决'}), 404

@ai_alert_api.route('/api/ai/alert/risk-profile/<user_id>', methods=['GET'])
@require_login
def get_risk_profile(user_id):
    """获取风险画像"""
    result = ai_learning_alert.get_risk_profile(user_id)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': '风险画像不存在'}), 404

@ai_alert_api.route('/api/ai/alert/types', methods=['GET'])
@require_login
def get_alert_types():
    """获取预警类型"""
    return jsonify({'success': True, 'data': ai_learning_alert.ALERT_TYPES})

@ai_alert_api.route('/api/ai/alert/levels', methods=['GET'])
@require_login
def get_alert_levels():
    """获取预警级别"""
    return jsonify({'success': True, 'data': ai_learning_alert.ALERT_LEVELS})