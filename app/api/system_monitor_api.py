#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.system_monitor import AISystemMonitor

system_monitor_api = Bluelogger.info('system_monitor_api', __name__)

@system_monitor_api.route('/api/monitor/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        monitor = AISystemMonitor()
        status = monitor.get_system_status()
        monitor.close()
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@system_monitor_api.route('/api/monitor/health', methods=['GET'])
def get_health_summary():
    """获取健康检查摘要"""
    try:
        monitor = AISystemMonitor()
        health = monitor.get_health_summary()
        monitor.close()
        
        return jsonify({
            'success': True,
            'data': health
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@system_monitor_api.route('/api/monitor/alerts', methods=['GET'])
def get_alerts():
    """获取告警摘要"""
    try:
        monitor = AISystemMonitor()
        alerts = monitor.get_alert_summary()
        monitor.close()
        
        return jsonify({
            'success': True,
            'data': alerts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@system_monitor_api.route('/api/monitor/metrics', methods=['GET'])
def get_recent_metrics():
    """获取最近的系统指标"""
    minutes = int(request.args.get('minutes', 60))
    
    try:
        monitor = AISystemMonitor()
        metrics = monitor.get_recent_metrics(minutes)
        monitor.close()
        
        return jsonify({
            'success': True,
            'data': metrics,
            'count': len(metrics)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@system_monitor_api.route('/api/monitor/database', methods=['GET'])
def get_database_stats():
    """获取数据库统计"""
    try:
        monitor = AISystemMonitor()
        stats = monitor.get_database_stats()
        monitor.close()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@system_monitor_api.route('/api/monitor/processes', methods=['GET'])
def get_process_status():
    """获取进程状态"""
    process_name = request.args.get('name')
    
    try:
        monitor = AISystemMonitor()
        processes = monitor.get_process_status(process_name)
        monitor.close()
        
        return jsonify({
            'success': True,
            'data': processes,
            'count': len(processes)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@system_monitor_api.route('/api/monitor/collect', methods=['POST'])
def collect_metrics():
    """收集系统指标"""
    try:
        monitor = AISystemMonitor()
        monitor.collect_system_metrics()
        monitor.close()
        
        return jsonify({
            'success': True,
            'message': '系统指标已收集'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500