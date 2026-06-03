# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能仪表盘模块 - 利用AI自学习系统分析系统数据
"""

import time
import os
import psutil
from flask import Blueprint, render_template, request, session, jsonify
from app.utils.logging import logger
from app.config import Config
from app.ai.self_learning_system import self_learning_system
from app.ai.self_upgrading_system import self_upgrading_system
from app.ai.enhanced_system import enhanced_system
from app.ai.instances import ai_instance_manager
from app.ai.monitoring import ai_monitor
from app.ai.cluster_manager import cluster_manager
import logging
import json
import sys

smart_dashboard_bp = Blueprint('smart_dashboard', __name__)


@smart_dashboard_bp.route('/smart-dashboard')
def smart_dashboard():
    """智能仪表盘视图"""
    try:
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        return render_template('smart_dashboard.html', user=user)
    except Exception as e:
        logger.error(f"智能仪表盘视图出错: {str(e)}")
        return render_template('smart_dashboard.html', user={'username': 'Guest', 'role': 'guest'})


@smart_dashboard_bp.route('/api/smart-dashboard/data')
def get_smart_dashboard_data():
    """获取智能仪表盘数据"""
    try:
        system_overview = {
            'system_status': '正常',
            'ai_instance_count': len(ai_instance_manager.ai_instances) if ai_instance_manager else 0,
            'running_sandboxes': cluster_manager.get_running_sandboxes_count() if cluster_manager else 0,
            'active_users': get_active_user_count(),
            'total_users': get_total_user_count()
        }

        ai_learning_status = {
            'is_learning_enabled': self_learning_system.config.get('enabled', False) if self_learning_system else False,
            'learning_interval': self_learning_system.config.get('learning_interval', 3600) if self_learning_system else 3600,
            'last_learning_time': self_learning_system.get_last_learning_time() if self_learning_system else 0,
            'total_learning_sessions': self_learning_system.get_total_learning_sessions() if self_learning_system else 0,
            'learning_accuracy': self_learning_system.get_learning_accuracy() if self_learning_system else 0
        }

        performance_prediction = self_learning_system.predict_system_performance() if self_learning_system else {}

        anomaly_detection = ai_monitor.detect_anomalies() if ai_monitor else {}

        optimization_suggestions = self_upgrading_system.get_optimization_suggestions() if self_upgrading_system else []

        enhanced_data = {
            'blueprint_usage': enhanced_system.get_enhanced_learning_data('blueprint_usage', limit=10) if enhanced_system else [],
            'sandbox_performance': enhanced_system.get_enhanced_learning_data('sandbox_performance', limit=10) if enhanced_system else [],
            'snapshot_management': enhanced_system.get_enhanced_learning_data('snapshot_management', limit=10) if enhanced_system else []
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
        return jsonify({'success': False, 'error': str(e)})


@smart_dashboard_bp.route('/api/smart-dashboard/insights')
def get_ai_insights():
    """获取AI洞察"""
    try:
        ai_insights = self_learning_system.get_system_insights() if self_learning_system else {}

        enhanced_analysis = {
            'blueprint_analysis': enhanced_system._analyze_blueprint_usage() if enhanced_system else {},
            'sandbox_analysis': enhanced_system._analyze_sandbox_performance() if enhanced_system else {},
            'snapshot_analysis': enhanced_system._analyze_snapshot_management() if enhanced_system else {}
        }

        enhanced_recommendations = generate_enhanced_recommendations(
            enhanced_analysis.get('blueprint_analysis', {}),
            enhanced_analysis.get('sandbox_analysis', {}),
            enhanced_analysis.get('snapshot_analysis', {})
        )

        return jsonify({
            'success': True,
            'ai_insights': ai_insights,
            'enhanced_analysis': enhanced_analysis,
            'enhanced_recommendations': enhanced_recommendations
        })
    except Exception as e:
        logger.error(f"获取AI洞察出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_dashboard_bp.route('/api/smart-dashboard/apply-suggestion', methods=['POST'])
def apply_suggestion():
    """应用优化建议"""
    try:
        data = request.get_json()
        suggestion = data.get('suggestion')

        if not suggestion:
            return jsonify({'success': False, 'error': '缺少建议内容'})

        result = self_upgrading_system.apply_suggestion(suggestion) if self_upgrading_system else {'status': 'applied'}

        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"应用优化建议出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_dashboard_bp.route('/api/smart-dashboard/start-learning', methods=['POST'])
def start_learning():
    """手动启动AI学习"""
    try:
        if self_learning_system:
            self_learning_system.start_learning()
            return jsonify({'success': True, 'message': 'AI学习已启动'})
        return jsonify({'success': False, 'error': '学习系统未初始化'})
    except Exception as e:
        logger.error(f"启动AI学习出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_dashboard_bp.route('/api/smart-dashboard/health')
def get_system_health():
    """获取系统健康状态"""
    try:
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
        return jsonify({'success': False, 'error': str(e)})


def generate_enhanced_recommendations(blueprint_analysis, sandbox_analysis, snapshot_analysis):
    """生成增强建议"""
    recommendations = []

    if blueprint_analysis.get('usage_count', 0) > 100:
        recommendations.append({
            'type': 'blueprint',
            'priority': 'medium',
            'description': '蓝图使用频率较高,建议优化蓝图管理策略'
        })

    if sandbox_analysis.get('performance_score', 100) < 70:
        recommendations.append({
            'type': 'sandbox',
            'priority': 'high',
            'description': '沙箱性能评分较低,建议检查沙箱配置'
        })

    if snapshot_analysis.get('snapshot_count', 0) > 50:
        recommendations.append({
            'type': 'snapshot',
            'priority': 'low',
            'description': '快照数量较多,建议清理旧快照以释放存储空间'
        })

    return recommendations


def get_active_user_count():
    """获取活跃用户数量"""
    return 10


def get_total_user_count():
    """获取总用户数量"""
    return 50


def get_cpu_usage():
    """获取CPU使用率"""
    try:
        return psutil.cpu_percent(interval=0.1)
    except Exception as e:
        logger.error(f"获取CPU使用率出错: {str(e)}")
        return 0


def get_memory_usage():
    """获取内存使用率"""
    try:
        return psutil.virtual_memory().percent
    except Exception as e:
        logger.error(f"获取内存使用率出错: {str(e)}")
        return 0


def get_disk_usage():
    """获取磁盘使用率"""
    try:
        return psutil.disk_usage('/').percent
    except Exception as e:
        logger.error(f"获取磁盘使用率出错: {str(e)}")
        return 0


def get_ai_instances_health():
    """获取AI实例健康状态"""
    health_status = {}
    try:
        if ai_instance_manager and hasattr(ai_instance_manager, 'ai_instances'):
            for instance_id, instance in ai_instance_manager.ai_instances.items():
                health_status[instance_id] = {
                    'status': instance.get('status', 'unknown'),
                    'last_health_check': instance.get('last_health_check', 0),
                    'response_time': instance.get('response_time', 0.0)
                }
    except Exception as e:
        logger.error(f"获取AI实例健康状态出错: {str(e)}")
    return health_status


def get_system_load():
    """获取系统负载"""
    try:
        return psutil.getloadavg()[0]
    except Exception as e:
        logger.error(f"获取系统负载出错: {str(e)}")
        return 0
