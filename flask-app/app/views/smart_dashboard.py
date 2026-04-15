#!/usr/bin/env python3
"""
智能仪表盘模块，利用AI自学习系统分析系统数据
"""

import time
import json
import os
from flask import Blueprint, render_template, request, session, jsonify
from app.utils.logging import logger
from app.config import Config
from app.ai.self_learning_system import self_learning_system
from app.ai.self_upgrading_system import self_upgrading_system
from app.ai.enhanced_system import enhanced_system
from app.ai.instances import ai_instance_manager
from app.ai.monitoring import ai_monitor
from app.ai.cluster_manager import cluster_manager

# 创建蓝图
smart_dashboard_bp = Blueprint('smart_dashboard', __name__)

@smart_dashboard_bp.route('/smart-dashboard')
def smart_dashboard():
    """智能仪表盘视图"""
    try:
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        return render_template('smart_dashboard.html', user=user)
    except Exception as e:
        logger.error(f"访问智能仪表盘时发生错误: {str(e)}")
        return f"访问智能仪表盘时发生错误: {str(e)}", 500

@smart_dashboard_bp.route('/api/smart-dashboard/data')
def get_smart_dashboard_data():
    """获取智能仪表盘数据"""
    try:
        # 1. 系统概览数据
        system_overview = {
            'system_status': '正常',
            'ai_instance_count': len(ai_instance_manager.ai_instances),
            'running_sandboxes': cluster_manager.get_running_sandboxes_count(),
            'active_users': get_active_user_count(),
            'total_users': get_total_user_count()
        }
        
        # 2. AI学习状态
        ai_learning_status = {
            'is_learning_enabled': self_learning_system.config.get('enabled', False),
            'learning_interval': self_learning_system.config.get('learning_interval', 3600),
            'last_learning_time': self_learning_system.get_last_learning_time(),
            'total_learning_sessions': self_learning_system.get_total_learning_sessions(),
            'learning_accuracy': self_learning_system.get_learning_accuracy()
        }
        
        # 3. 系统性能预测
        performance_prediction = self_learning_system.predict_system_performance()
        
        # 4. 异常检测结果
        anomaly_detection = ai_monitor.detect_anomalies()
        
        # 5. AI生成的优化建议
        optimization_suggestions = self_upgrading_system.get_optimization_suggestions()
        
        # 6. 增强系统数据
        enhanced_data = {
            'blueprint_usage': enhanced_system.get_enhanced_learning_data('blueprint_usage', limit=10),
            'sandbox_performance': enhanced_system.get_enhanced_learning_data('sandbox_performance', limit=10),
            'snapshot_management': enhanced_system.get_enhanced_learning_data('snapshot_management', limit=10)
        }
        
        return jsonify({
            'success': True,
            'system_overview': system_overview,
            'ai_learning_status': ai_learning_status,
            'performance_prediction': performance_prediction,
            'anomaly_detection': anomaly_detection,
            'optimization_suggestions': optimization_suggestions,
            'enhanced_data': enhanced_data
        }), 200
    except Exception as e:
        logger.error(f"获取智能仪表盘数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取智能仪表盘数据失败: {str(e)}'
        }), 500

@smart_dashboard_bp.route('/api/smart-dashboard/ai-insights')
def get_ai_insights():
    """获取AI洞察"""
    try:
        # 获取AI自学习系统的洞察
        ai_insights = self_learning_system.get_system_insights()
        
        # 获取增强系统的分析
        enhanced_analysis = {
            'blueprint_analysis': enhanced_system._analyze_blueprint_usage(),
            'sandbox_analysis': enhanced_system._analyze_sandbox_performance(),
            'snapshot_analysis': enhanced_system._analyze_snapshot_management()
        }
        
        # 生成增强建议
        enhanced_suggestions = enhanced_system._generate_enhanced_suggestions(
            enhanced_analysis['blueprint_analysis'],
            enhanced_analysis['sandbox_analysis'],
            enhanced_analysis['snapshot_analysis']
        )
        
        return jsonify({
            'success': True,
            'ai_insights': ai_insights,
            'enhanced_analysis': enhanced_analysis,
            'enhanced_suggestions': enhanced_suggestions
        }), 200
    except Exception as e:
        logger.error(f"获取AI洞察失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取AI洞察失败: {str(e)}'
        }), 500

@smart_dashboard_bp.route('/api/smart-dashboard/apply-suggestion', methods=['POST'])
def apply_suggestion():
    """应用AI优化建议"""
    try:
        data = request.json
        suggestion = data.get('suggestion')
        
        if not suggestion:
            return jsonify({
                'success': False,
                'error': '缺少建议数据'
            }), 400
        
        # 应用建议
        result = self_upgrading_system.apply_suggestion(suggestion)
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
    except Exception as e:
        logger.error(f"应用AI建议失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'应用AI建议失败: {str(e)}'
        }), 500

@smart_dashboard_bp.route('/api/smart-dashboard/start-learning')
def start_learning():
    """手动启动AI学习"""
    try:
        # 启动AI学习
        self_learning_system.start_learning()
        
        return jsonify({
            'success': True,
            'message': 'AI学习已启动'
        }), 200
    except Exception as e:
        logger.error(f"启动AI学习失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'启动AI学习失败: {str(e)}'
        }), 500

@smart_dashboard_bp.route('/api/smart-dashboard/system-health')
def get_system_health():
    """获取系统健康状态"""
    try:
        # 获取系统健康状态
        health_status = {
            'cpu_usage': get_cpu_usage(),
            'memory_usage': get_memory_usage(),
            'disk_usage': get_disk_usage(),
            'ai_instances_health': get_ai_instances_health(),
            'system_load': get_system_load()
        }
        
        return jsonify({
            'success': True,
            'health_status': health_status
        }), 200
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取系统健康状态失败: {str(e)}'
        }), 500

# 辅助函数
def get_active_user_count():
    """获取活跃用户数量"""
    # 这里可以从数据库获取实际活跃用户数量
    return 0

def get_total_user_count():
    """获取总用户数量"""
    # 这里可以从数据库获取实际总用户数量
    return 0

def get_cpu_usage():
    """获取CPU使用率"""
    try:
        import psutil
        return psutil.cpu_percent(interval=1)
    except Exception as e:
        logger.error(f"获取CPU使用率失败: {str(e)}")
        return 0.0

def get_memory_usage():
    """获取内存使用率"""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except Exception as e:
        logger.error(f"获取内存使用率失败: {str(e)}")
        return 0.0

def get_disk_usage():
    """获取磁盘使用率"""
    try:
        import psutil
        return psutil.disk_usage('/').percent
    except Exception as e:
        logger.error(f"获取磁盘使用率失败: {str(e)}")
        return 0.0

def get_ai_instances_health():
    """获取AI实例健康状态"""
    health_status = {}
    for instance_id, instance in ai_instance_manager.ai_instances.items():
        health_status[instance_id] = {
            'status': instance.get('status', 'unknown'),
            'last_health_check': instance.get('last_health_check', 0),
            'response_time': instance.get('response_time', 0.0)
        }
    return health_status

def get_system_load():
    """获取系统负载"""
    try:
        import psutil
        return psutil.getloadavg()[0]  # 获取1分钟负载
    except Exception as e:
        logger.error(f"获取系统负载失败: {str(e)}")
        return 0.0
