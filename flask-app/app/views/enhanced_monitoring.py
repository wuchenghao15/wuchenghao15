# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强型系统监控模块 - 利用AI预测系统故障和优化性能
"""

import time
import os
import psutil
import platform
import random
from flask import Blueprint, render_template, request, session, jsonify
from app.utils.logging import logger
from app.config import Config
from app.ai.self_learning_system import self_learning_system
from app.ai.enhanced_system import enhanced_system
import logging
import json
import sys

enhanced_monitoring_bp = Blueprint('enhanced_monitoring', __name__)


@enhanced_monitoring_bp.route('/enhanced-monitoring')
def enhanced_monitoring():
    """增强型系统监控视图"""
    try:
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        return render_template('enhanced_monitoring.html', user=user)
    except Exception as e:
        logger.error(f"增强型系统监控视图出错: {str(e)}")
        return render_template('enhanced_monitoring.html', user={'username': 'Guest', 'role': 'guest'})


@enhanced_monitoring_bp.route('/api/enhanced-monitoring/status')
def get_system_status():
    """获取实时系统状态"""
    try:
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }

        cpu_info = {
            'cpu_count': psutil.cpu_count(logical=True),
            'cpu_percent': psutil.cpu_percent(interval=0.1, percpu=True),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }

        memory_info = {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'used': psutil.virtual_memory().used,
            'percent': psutil.virtual_memory().percent
        }

        disk_info = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except (PermissionError, FileNotFoundError):
                continue

        network_info = {
            'bytes_sent': psutil.net_io_counters().bytes_sent,
            'bytes_recv': psutil.net_io_counters().bytes_recv,
            'packets_sent': psutil.net_io_counters().packets_sent,
            'packets_recv': psutil.net_io_counters().packets_recv
        }

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                proc_info = proc.info
                proc_info['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc_info['create_time']))
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_processes = processes[:10]

        boot_time = psutil.boot_time()

        return jsonify({
            'success': True,
            'system_info': system_info,
            'cpu_info': cpu_info,
            'memory_info': memory_info,
            'disk_info': disk_info,
            'network_info': network_info,
            'top_processes': top_processes,
            'boot_time': boot_time
        })
    except Exception as e:
        logger.error(f"获取系统状态出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@enhanced_monitoring_bp.route('/api/enhanced-monitoring/performance-optimization')
def get_performance_optimization():
    """获取性能优化建议"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')

        optimization_input = {
            'cpu_percent': cpu_percent,
            'memory_total': memory_info.total,
            'memory_used': memory_info.used,
            'memory_percent': memory_info.percent,
            'disk_total': disk_usage.total,
            'disk_percent': disk_usage.percent,
            'timestamp': time.time()
        }

        optimization_suggestions = self_learning_system.generate_performance_optimizations(optimization_input)

        return jsonify({
            'success': True,
            'optimization_suggestions': optimization_suggestions
        })
    except Exception as e:
        logger.error(f"获取性能优化建议出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@enhanced_monitoring_bp.route('/api/enhanced-monitoring/resource-forecast')
def get_resource_forecast():
    """获取资源使用预测"""
    try:
        current_cpu = psutil.cpu_percent(interval=0.1)
        current_memory = psutil.virtual_memory().percent
        current_disk = psutil.disk_usage('/').percent
        forecast_hours = 24

        cpu_forecast = generate_resource_forecast_data(current_cpu, forecast_hours)
        memory_forecast = generate_resource_forecast_data(current_memory, forecast_hours)
        disk_forecast = generate_resource_forecast_data(current_disk, forecast_hours)

        return jsonify({
            'success': True,
            'cpu_forecast': cpu_forecast,
            'memory_forecast': memory_forecast,
            'disk_forecast': disk_forecast
        })
    except Exception as e:
        logger.error(f"获取资源预测出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@enhanced_monitoring_bp.route('/api/enhanced-monitoring/anomaly-detection')
def get_anomaly_detection():
    """获取异常检测结果"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        network_sent = psutil.net_io_counters().bytes_sent
        network_recv = psutil.net_io_counters().bytes_recv

        anomalies = detect_system_anomalies({
            'cpu_usage': cpu_percent,
            'memory_usage': memory_percent,
            'disk_usage': disk_percent,
            'network_sent': network_sent,
            'network_recv': network_recv,
            'timestamp': time.time()
        })

        return jsonify({
            'success': True,
            'anomalies': anomalies
        })
    except Exception as e:
        logger.error(f"获取异常检测出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@enhanced_monitoring_bp.route('/api/enhanced-monitoring/health-score')
def get_system_health_score():
    """获取系统健康评分"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        health_score = calculate_system_health_score({
            'cpu_usage': cpu_percent,
            'memory_usage': memory_percent,
            'disk_usage': disk_percent
        })

        health_status = get_health_status(health_score)

        return jsonify({
            'success': True,
            'timestamp': time.time(),
            'health_score': health_score,
            'health_status': health_status
        })
    except Exception as e:
        logger.error(f"获取系统健康评分失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取系统健康评分失败: {str(e)}'}), 500


def generate_maintenance_suggestions(predictions):
    """生成维护建议"""
    suggestions = []

    if predictions.get('cpu_failure_probability', 0) > 0.7:
        suggestions.append({
            'id': f'maint_cpu_{int(time.time())}',
            'type': 'cpu',
            'severity': 'high',
            'description': 'CPU使用率持续过高,建议优化或升级',
            'suggestion': '1. 检查并优化高CPU使用率的进程\n2. 考虑增加CPU核心数或升级CPU\n3. 调整系统资源分配策略',
            'confidence': predictions.get('cpu_failure_probability', 0)
        })

    if predictions.get('memory_failure_probability', 0) > 0.7:
        suggestions.append({
            'id': f'maint_memory_{int(time.time())}',
            'type': 'memory',
            'severity': 'high',
            'description': '内存使用率持续过高,建议增加内存或优化内存使用',
            'suggestion': '1. 检查内存泄漏问题\n2. 增加系统内存\n3. 优化应用程序内存使用',
            'confidence': predictions.get('memory_failure_probability', 0)
        })

    if predictions.get('disk_failure_probability', 0) > 0.7:
        suggestions.append({
            'id': f'maint_disk_{int(time.time())}',
            'type': 'disk',
            'severity': 'high',
            'description': '磁盘空间不足,建议清理磁盘或增加存储容量',
            'suggestion': '1. 清理临时文件和日志\n2. 删除不需要的文件\n3. 扩展磁盘容量',
            'confidence': predictions.get('disk_failure_probability', 0)
        })

    return suggestions


def generate_resource_forecast_data(current_value, forecast_hours):
    """生成资源预测数据"""
    forecast = []
    current = current_value

    for hour in range(forecast_hours):
        trend_factor = random.uniform(-2, 2)
        random_factor = random.uniform(-10, 10)
        predicted = max(0, min(100, current + trend_factor + random_factor))

        forecast.append({
            'hour': hour + 1,
            'predicted_value': predicted,
            'timestamp': time.time() + (hour * 3600)
        })

        current = predicted

    return forecast


def detect_system_anomalies(system_data):
    """检测系统异常"""
    anomalies = []

    avg_cpu = sum(system_data['cpu_usage']) / len(system_data['cpu_usage']) if system_data['cpu_usage'] else 0

    if avg_cpu > 90:
        anomalies.append({
            'id': f'anomaly_cpu_{int(time.time())}',
            'type': 'cpu',
            'severity': 'critical',
            'description': f'CPU使用率异常高: {avg_cpu:.2f}%',
            'timestamp': system_data['timestamp']
        })
    elif avg_cpu > 75:
        anomalies.append({
            'id': f'anomaly_cpu_{int(time.time())}',
            'type': 'cpu',
            'severity': 'warning',
            'description': f'CPU使用率偏高: {avg_cpu:.2f}%',
            'timestamp': system_data['timestamp']
        })

    if system_data['memory_usage'] > 90:
        anomalies.append({
            'id': f'anomaly_memory_{int(time.time())}',
            'type': 'memory',
            'severity': 'critical',
            'description': f'内存使用率异常高: {system_data["memory_usage"]:.2f}%',
            'timestamp': system_data['timestamp']
        })
    elif system_data['memory_usage'] > 80:
        anomalies.append({
            'id': f'anomaly_memory_{int(time.time())}',
            'type': 'memory',
            'severity': 'warning',
            'description': f'内存使用率偏高: {system_data["memory_usage"]:.2f}%',
            'timestamp': system_data['timestamp']
        })

    if system_data['disk_usage'] > 90:
        anomalies.append({
            'id': f'anomaly_disk_{int(time.time())}',
            'type': 'disk',
            'severity': 'critical',
            'description': f'磁盘使用率异常高: {system_data["disk_usage"]:.2f}%',
            'timestamp': system_data['timestamp']
        })
    elif system_data['disk_usage'] > 80:
        anomalies.append({
            'id': f'anomaly_disk_{int(time.time())}',
            'type': 'disk',
            'severity': 'warning',
            'description': f'磁盘使用率偏高: {system_data["disk_usage"]:.2f}%',
            'timestamp': system_data['timestamp']
        })

    return anomalies


def calculate_system_health_score(system_metrics):
    """计算系统健康评分"""
    cpu_score = max(0, 100 - system_metrics['cpu_usage'])
    memory_score = max(0, 100 - system_metrics['memory_usage'])
    disk_score = max(0, 100 - system_metrics['disk_usage'])

    health_score = (cpu_score * 0.4) + (memory_score * 0.4) + (disk_score * 0.2)

    return round(health_score, 2)


def get_health_status(score):
    """根据健康评分获取状态"""
    if score >= 90:
        return 'excellent'
    elif score >= 75:
        return 'good'
    elif score >= 60:
        return 'fair'
    elif score >= 40:
        return 'poor'
    else:
        return 'critical'
