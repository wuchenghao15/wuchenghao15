#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控相关路由
"""

from flask import Blueprint, render_template, jsonify, request
from app.ai.intelligence_manager import intelligence_manager
from app.ai.thread_process_manager import ai_thread_process_manager
from app.ai.ai_engine_integrator import ai_engine_integrator
from app.services.service_manager import service_manager
from app.services.log_manager import log_manager

# 导入用户状态检查装饰器
from app.views.main import check_user_status

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/monitoring')
@check_user_status
def monitoring():
    """系统监控面板"""
    return render_template('monitoring.html')

@monitoring_bp.route('/api/monitoring/resources')
@check_user_status
def get_resources():
    """获取系统资源使用情况"""
    try:
        # 从智体管家获取系统资源状态
        system_resources = intelligence_manager.system_resources
        
        # 构建响应数据
        resources_data = {
            'cpu': system_resources.get('cpu', {}).get('usage', 0),
            'memory': system_resources.get('memory', {}).get('usage', 0),
            'disk': system_resources.get('disk', {}).get('usage', 0),
            'network': system_resources.get('network', {}).get('usage', 0)
        }
        
        return jsonify(resources_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/services')
@check_user_status
def get_services():
    """获取服务状态"""
    try:
        # 从服务管理器获取服务状态
        services = service_manager.get_all_service_status()
        return jsonify(services)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/ai-engines')
@check_user_status
def get_ai_engines():
    """获取AI引擎状态"""
    try:
        # 从AI引擎集成器获取健康状态
        health_status = ai_engine_integrator.health_status
        return jsonify(health_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/components')
@check_user_status
def get_components():
    """获取系统组件状态"""
    try:
        # 从智体管家获取组件状态
        components = intelligence_manager.component_status
        return jsonify(components)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/monitoring/thread-manager')
@check_user_status
def get_thread_manager():
    """获取线程管理器状态"""
    try:
        # 从线程进程管理器获取状态
        status = ai_thread_process_manager.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/log-management')
@check_user_status
def log_management():
    """日志管理面板"""
    return render_template('log_management.html')

@monitoring_bp.route('/api/logs/analysis')
@check_user_status
def get_log_analysis():
    """获取日志分析数据"""
    try:
        # 获取查询参数
        time_range = request.args.get('time_range', '24h')
        level = request.args.get('level', 'all')
        module = request.args.get('module', 'all')
        
        # 执行日志分析
        analysis = log_manager.analyze_logs(time_range=time_range, level=level, module=module)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/logs/latest')
@check_user_status
def get_latest_logs():
    """获取最近日志"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        level = request.args.get('level', 'all')
        module = request.args.get('module', 'all')
        
        # 获取最近日志
        logs = log_manager.get_latest_logs(limit=limit, level=level, module=module)
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/logs/clean')
@check_user_status
def clean_logs():
    """清理日志"""
    try:
        # 获取查询参数
        days = request.args.get('days', 7, type=int)
        
        # 执行日志清理
        result = log_manager.clean_old_logs(days=days)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/logs/export')
@check_user_status
def export_logs():
    """导出日志"""
    try:
        # 获取查询参数
        time_range = request.args.get('time_range', '24h')
        level = request.args.get('level', 'all')
        module = request.args.get('module', 'all')
        format = request.args.get('format', 'json')
        
        # 执行日志导出
        export_path = log_manager.export_logs(time_range=time_range, level=level, module=module, format=format)
        return jsonify({'export_path': export_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500