#!/usr/bin/env python3
"""
AI学习进度API接口
提供学习进度追踪相关的REST API服务
"""

from flask import Blueprint, request, jsonify
from app.ai.ai_progress_tracker import ai_progress_tracker

ai_progress_api = Bluelogger.info('ai_progress_api', __name__, url_prefix='/api/ai/progress')

@ai_progress_api.route('/track', methods=['POST'])
def track_activity():
    """记录学习活动"""
    data = request.get_json()
    user_id = data.get('user_id', '')
    subject = data.get('subject', '')
    topic = data.get('topic', '')
    activity_type = data.get('activity_type', 'study')
    duration = data.get('duration', 0)
    score = data.get('score', 0)
    total_score = data.get('total_score', 100)
    completed = data.get('completed', 0)
    total = data.get('total', 0)
    
    if not user_id or not subject:
        return jsonify({'success': False, 'error': '用户ID和科目不能为空'}), 400
    
    result = ai_progress_tracker.track_study_activity(
        user_id, subject, topic, activity_type, duration, score, total_score, completed, total
    )
    return jsonify(result)

@ai_progress_api.route('/progress', methods=['GET'])
def get_progress():
    """获取学习进度"""
    user_id = request.args.get('user_id', '')
    subject = request.args.get('subject', '')
    topic = request.args.get('topic', '')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_progress_tracker.get_progress(user_id, subject, topic)
    return jsonify(result)

@ai_progress_api.route('/stats', methods=['GET'])
def get_stats():
    """获取学习统计"""
    user_id = request.args.get('user_id', '')
    period = request.args.get('period', 'week')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_progress_tracker.get_study_stats(user_id, period)
    return jsonify(result)

@ai_progress_api.route('/goal/set', methods=['POST'])
def set_goal():
    """设置周目标"""
    data = request.get_json()
    user_id = data.get('user_id', '')
    subject = data.get('subject', '')
    target_study_time = data.get('target_study_time', 0)
    target_completion = data.get('target_completion', 0)
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_progress_tracker.set_weekly_goal(user_id, subject, target_study_time, target_completion)
    return jsonify(result)

@ai_progress_api.route('/goal/get', methods=['GET'])
def get_goals():
    """获取周目标"""
    user_id = request.args.get('user_id', '')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_progress_tracker.get_weekly_goals(user_id)
    return jsonify(result)

@ai_progress_api.route('/report/weekly', methods=['GET'])
def generate_weekly_report():
    """生成周学习报告"""
    user_id = request.args.get('user_id', '')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_progress_tracker.generate_weekly_report(user_id)
    return jsonify(result)

@ai_progress_api.route('/reports', methods=['GET'])
def get_reports():
    """获取学习报告"""
    user_id = request.args.get('user_id', '')
    report_type = request.args.get('report_type', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_progress_tracker.get_reports(user_id, report_type, limit)
    return jsonify(result)

@ai_progress_api.route('/trend', methods=['GET'])
def get_trend():
    """获取学习进度趋势"""
    user_id = request.args.get('user_id', '')
    subject = request.args.get('subject', '')
    days = request.args.get('days', 7, type=int)
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_progress_tracker.get_progress_trend(user_id, subject, days)
    return jsonify(result)