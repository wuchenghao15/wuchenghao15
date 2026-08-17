#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.data_visualization import AIDataVisualization
from app.ai.learning_incentive import AILearningIncentive

ai_viz_api = Bluelogger.info('ai_viz_api', __name__)

@ai_viz_api.route('/api/ai/viz/dashboard', methods=['GET'])
def get_dashboard_summary():
    """获取仪表板摘要"""
    try:
        viz = AIDataVisualization()
        summary = viz.generate_dashboard_summary()
        viz.close()
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/viz/learning-chart', methods=['GET'])
def get_learning_chart():
    """获取学习趋势图表数据"""
    user_id = request.args.get('user_id', '1')
    days = int(request.args.get('days', 30))
    
    try:
        viz = AIDataVisualization()
        data = viz.generate_learning_chart_data(user_id, days)
        viz.close()
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/viz/resource-pie', methods=['GET'])
def get_resource_pie():
    """获取资源分布饼图"""
    try:
        viz = AIDataVisualization()
        data = viz.generate_resource_pie_data()
        viz.close()
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/viz/skill-radar', methods=['GET'])
def get_skill_radar():
    """获取技能雷达图数据"""
    user_id = request.args.get('user_id', '1')
    
    try:
        viz = AIDataVisualization()
        data = viz.generate_skill_radar_data(user_id)
        viz.close()
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/viz/user-activity', methods=['GET'])
def get_user_activity():
    """获取用户活跃度柱状图"""
    try:
        viz = AIDataVisualization()
        data = viz.generate_user_activity_bar_data()
        viz.close()
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/viz/heatmap', methods=['GET'])
def get_heatmap_data():
    """获取学习热力图数据"""
    try:
        viz = AIDataVisualization()
        data = viz.generate_weekly_heatmap_data()
        viz.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/viz/system-metrics', methods=['GET'])
def get_system_metrics():
    """获取系统指标"""
    try:
        viz = AIDataVisualization()
        metrics = viz.generate_system_metrics()
        viz.close()
        
        return jsonify({
            'success': True,
            'data': metrics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/incentive/stats/<user_id>', methods=['GET'])
def get_user_incentive_stats(user_id):
    """获取用户激励统计"""
    try:
        incentive = AILearningIncentive()
        stats = incentive.get_user_stats(user_id)
        incentive.close()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/incentive/award', methods=['POST'])
def award_points():
    """奖励积分"""
    data = request.get_json() or {}
    user_id = data.get('user_id', '1')
    points = int(data.get('points', 0))
    reason = data.get('reason', '')
    
    if points <= 0:
        return jsonify({
            'success': False,
            'error': '积分必须大于0'
        }), 400
    
    try:
        incentive = AILearningIncentive()
        incentive.award_points(user_id, points, reason)
        stats = incentive.get_user_stats(user_id)
        incentive.close()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/incentive/leaderboard', methods=['GET'])
def get_leaderboard():
    """获取排行榜"""
    limit = int(request.args.get('limit', 10))
    
    try:
        incentive = AILearningIncentive()
        leaderboard = incentive.get_leaderboard(limit)
        incentive.close()
        
        return jsonify({
            'success': True,
            'data': leaderboard,
            'count': len(leaderboard)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_viz_api.route('/api/ai/incentive/badges', methods=['GET'])
def get_available_badges():
    """获取可用徽章"""
    try:
        incentive = AILearningIncentive()
        badges = incentive.get_available_badges()
        incentive.close()
        
        return jsonify({
            'success': True,
            'data': badges,
            'count': len(badges)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500