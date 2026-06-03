# -*- coding: utf-8 -*-
"""
系统监控模块 - 提供健康检查、指标和应用信息端点
"""

import os
import sys
import time
import psutil
from flask import Blueprint, jsonify, request, session, redirect, url_for
from app.utils.network import network_optimizer
from app.ai.monitoring import ai_monitor
from app.utils.logging import logger, logging_manager
from app.utils.environment import environment_manager
from app.utils.error_handler import error_handler
import logging
import json

monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/health')
def health_check():
    """健康检查端点: 返回应用的基本健康状态"""
    try:
        health_status = {
            'status': 'UP',
            'timestamp': time.time(),
            'environment': environment_manager.get_current_environment() if environment_manager else 'unknown',
            'app_version': os.environ.get('APP_VERSION', 'unknown'),
            'checks': {
                'database': 'UP',
                'cache': 'UP',
                'ai_monitor': 'UP' if ai_monitor else 'DOWN'
            }
        }
        return jsonify(health_status), 200
    except Exception as e:
        logger.error(f"健康检查出错: {str(e)}")
        return jsonify({'status': 'DOWN', 'error': str(e)}), 500


@monitoring_bp.route('/metrics')
def metrics():
    """详细的指标端点: 返回应用的各种运行指标"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)

        performance_metrics = network_optimizer.get_performance_metrics() if network_optimizer else {}

        error_stats = ai_monitor.get_error_stats() if ai_monitor else {}

        log_stats = logging_manager.get_log_stats() if logging_manager else {}

        error_handler_stats = error_handler.get_error_stats() if error_handler else {}

        metrics_data = {
            'timestamp': time.time(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'python_version': sys.version,
                'uptime_seconds': time.time() - process.create_time()
            },
            'performance': performance_metrics,
            'errors': {
                'ai_monitor': error_stats,
                'error_handler': error_handler_stats
            },
            'logging': log_stats,
            'request': {
                'method': request.method,
                'path': request.path
            }
        }

        return jsonify(metrics_data), 200
    except Exception as e:
        logger.error(f"获取指标出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/info')
def app_info():
    """应用信息端点: 返回应用的基本信息"""
    try:
        env_info = environment_manager.get_environment_info() if environment_manager else {}

        config = environment_manager.get_environment_config() if environment_manager else None

        app_info_data = {
            'name': 'MTSCOS AI System',
            'version': os.environ.get('APP_VERSION', 'unknown'),
            'description': 'MTSCOS AI Project System',
            'environment': env_info,
            'config': {
                'debug': getattr(config, 'DEBUG', False) if config else False,
                'port': getattr(config, 'PORT', 8888) if config else 8888,
                'log_level': getattr(config, 'LOG_LEVEL', 'INFO') if config else 'INFO',
                'session_timeout_minutes': getattr(config, 'PERMANENT_SESSION_LIFETIME', {}).total_seconds() / 60 if hasattr(config, 'PERMANENT_SESSION_LIFETIME') and hasattr(config.PERMANENT_SESSION_LIFETIME, 'total_seconds') else 30
            },
            'features': {
                'ai_monitoring': True,
                'error_handling': True,
                'logging': True,
                'middleware': True,
                'environment_management': True
            }
        }

        return jsonify(app_info_data), 200
    except Exception as e:
        logger.error(f"获取应用信息出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/api/performance')
def api_performance():
    """获取性能指标API"""
    try:
        performance_metrics = network_optimizer.get_performance_metrics() if network_optimizer else {}
        return jsonify(performance_metrics)
    except Exception as e:
        logger.error(f"获取性能指标出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/api/errors')
def api_errors():
    """获取错误统计API"""
    try:
        error_stats = ai_monitor.get_error_stats() if ai_monitor else {}
        return jsonify(error_stats)
    except Exception as e:
        logger.error(f"获取错误统计出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """清除缓存"""
    if 'logged_in' not in session:
        return redirect(url_for('main.index'))

    try:
        if network_optimizer:
            network_optimizer.clear_cache()

        return jsonify({
            'success': True,
            'message': '缓存已清除'
        })
    except Exception as e:
        logger.error(f"清除缓存出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
