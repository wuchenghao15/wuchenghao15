# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
运维监控API - 提供系统健康检查、日志聚合、性能监控、数据可视化等功能
"""

from flask import Blueprint, jsonify, request, session
import logging
import sqlite3
import json
import psutil
import time
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import os
import sys

# 设置日志
logger = logging.getLogger(__name__)

# 创建蓝图
admin_monitoring_api = Blueprint('admin_monitoring_api', __name__, url_prefix='/api/admin/monitoring')

# 数据库路径 - 动态计算确保正确性
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

# ==================== 权限检查装饰器 ====================

def require_admin_role(func):
    """管理员权限检查装饰器"""
    def decorated(*args, **kwargs):
        role = session.get('role', 'guest')
        if role not in ['admin', 'super_admin']:
            return jsonify({
                'success': False,
                'error': '权限不足，需要管理员权限'
            }), 403
        return func(*args, **kwargs)
    decorated.__name__ = func.__name__
    return decorated


# ==================== 系统健康检查 ====================

@admin_monitoring_api.route('/health', methods=['GET'])
def system_health_check():
    """
    系统健康检查 - 综合检查所有系统组件的健康状态
    返回各组件的健康状态、资源使用情况和潜在问题
    """
    try:
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'metrics': {},
            'warnings': [],
            'recommendations': []
        }
        
        # CPU健康检查
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        health_status['components']['cpu'] = {
            'status': 'healthy' if cpu_usage < 80 else 'warning' if cpu_usage < 95 else 'critical',
            'usage_percent': cpu_usage,
            'core_count': cpu_count,
            'frequency_mhz': cpu_freq.current if cpu_freq else 0
        }
        
        if cpu_usage >= 80:
            health_status['warnings'].append(f'CPU使用率过高: {cpu_usage}%')
            if cpu_usage >= 95:
                health_status['overall_status'] = 'critical'
            else:
                health_status['overall_status'] = 'warning'
        
        # 内存健康检查
        memory = psutil.virtual_memory()
        health_status['components']['memory'] = {
            'status': 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 95 else 'critical',
            'total_mb': memory.total / (1024 * 1024),
            'available_mb': memory.available / (1024 * 1024),
            'used_mb': memory.used / (1024 * 1024),
            'usage_percent': memory.percent
        }
        
        if memory.percent >= 80:
            health_status['warnings'].append(f'内存使用率过高: {memory.percent}%')
            if memory.percent >= 95:
                health_status['overall_status'] = 'critical'
        
        # 磁盘健康检查
        disk = psutil.disk_usage('/')
        health_status['components']['disk'] = {
            'status': 'healthy' if disk.percent < 80 else 'warning' if disk.percent < 95 else 'critical',
            'total_gb': disk.total / (1024 * 1024 * 1024),
            'used_gb': disk.used / (1024 * 1024 * 1024),
            'free_gb': disk.free / (1024 * 1024 * 1024),
            'usage_percent': disk.percent
        }
        
        if disk.percent >= 80:
            health_status['warnings'].append(f'磁盘使用率过高: {disk.percent}%')
            if disk.percent >= 95:
                health_status['overall_status'] = 'critical'
        
        # 数据库健康检查
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
                
                # 检查数据库表数量
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
                # 检查数据库连接数
                cursor.execute('PRAGMA busy_timeout')
                busy_timeout = cursor.fetchone()[0]
                
                health_status['components']['database'] = {
                    'status': 'healthy',
                    'size_mb': db_size / (1024 * 1024),
                    'table_count': table_count,
                    'busy_timeout_ms': busy_timeout,
                    'connection': 'active'
                }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'critical',
                'error': str(e),
                'connection': 'failed'
            }
            health_status['warnings'].append(f'数据库连接异常: {str(e)}')
            health_status['overall_status'] = 'critical'
        
        # 网络健康检查
        try:
            net_io = psutil.net_io_counters()
            health_status['components']['network'] = {
                'status': 'healthy',
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors': net_io.errin + net_io.errout
            }
            
            if net_io.errin + net_io.errout > 0:
                health_status['warnings'].append(f'网络存在错误: 输入{net_io.errin}个, 输出{net_io.errout}个')
        except Exception as e:
            health_status['components']['network'] = {
                'status': 'warning',
                'error': str(e)
            }
        
        # 进程健康检查
        process = psutil.Process()
        health_status['components']['process'] = {
            'status': 'healthy',
            'pid': process.pid,
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'thread_count': process.num_threads(),
            'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0
        }
        
        # 生成优化建议
        health_status['recommendations'] = _generate_health_recommendations(health_status)
        
        # 综合指标
        health_status['metrics'] = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory.percent,
            'disk_usage': disk.percent,
            'process_cpu': process.cpu_percent(),
            'process_memory': process.memory_percent()
        }
        
        return jsonify({
            'success': True,
            'data': health_status
        })
        
    except Exception as e:
        logger.error(f'系统健康检查失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _generate_health_recommendations(health_status: Dict) -> List[str]:
    """根据健康状态生成优化建议"""
    recommendations = []
    
    # CPU建议
    if health_status['components']['cpu']['usage_percent'] >= 80:
        recommendations.append('建议检查高CPU消耗进程，考虑优化算法或增加计算资源')
    
    # 内存建议
    if health_status['components']['memory']['usage_percent'] >= 80:
        recommendations.append('建议检查内存泄漏问题，清理缓存或增加内存资源')
    
    # 磁盘建议
    if health_status['components']['disk']['usage_percent'] >= 80:
        recommendations.append('建议清理临时文件和日志，执行数据库压缩，或扩展存储空间')
    
    # 数据库建议
    if health_status['components']['database']['status'] == 'warning':
        recommendations.append('建议优化数据库查询，增加索引，或考虑数据库分片')
    
    # 网络建议
    if health_status['components']['network']['errors'] > 0:
        recommendations.append('建议检查网络配置，排查网络错误原因')
    
    return recommendations


# ==================== 日志聚合 ====================

@admin_monitoring_api.route('/logs/aggregated', methods=['GET'])
@require_admin_role
def get_aggregated_logs():
    """
    获取聚合日志 - 汇总各类日志并提供统计分析
    支持按类型、时间范围、级别等筛选
    """
    try:
        log_type = request.args.get('type', 'all')
        level = request.args.get('level', 'all')
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 100))
        
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        aggregated_logs = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {},
            'logs': []
        }
        
        # 获取系统日志
        if log_type in ['all', 'system']:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                if level == 'all':
                    cursor.execute('''
                        SELECT id, level, module, message, ip_address, created_at 
                        FROM system_logs 
                        WHERE created_at > ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (time_threshold, limit))
                else:
                    cursor.execute('''
                        SELECT id, level, module, message, ip_address, created_at 
                        FROM system_logs 
                        WHERE created_at > ? AND level = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (time_threshold, level, limit))
                
                columns = ['id', 'level', 'module', 'message', 'ip_address', 'created_at']
                system_logs = []
                for row in cursor.fetchall():
                    system_logs.append(dict(zip(columns, row)))
                
                aggregated_logs['logs'].extend(system_logs)
                
                # 统计各级别日志数量
                cursor.execute('''
                    SELECT level, COUNT(*) 
                    FROM system_logs 
                    WHERE created_at > ? 
                    GROUP BY level
                ''', (time_threshold,))
                
                for row in cursor.fetchall():
                    aggregated_logs['statistics'][f'system_{row[0]}'] = row[1]
        
        # 获取访问日志
        if log_type in ['all', 'access']:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, path, user_id, username, role, ip_address, user_agent, access_time, method 
                    FROM access_logs 
                    WHERE access_time > ? 
                    ORDER BY access_time DESC 
                    LIMIT ?
                ''', (time_threshold, limit))
                
                columns = ['id', 'path', 'user_id', 'username', 'role', 'ip_address', 'user_agent', 'access_time', 'method']
                access_logs = []
                for row in cursor.fetchall():
                    access_logs.append(dict(zip(columns, row)))
                
                aggregated_logs['logs'].extend(access_logs)
                
                # 统计各角色访问次数
                cursor.execute('''
                    SELECT role, COUNT(*) 
                    FROM access_logs 
                    WHERE access_time > ? 
                    GROUP BY role
                ''', (time_threshold,))
                
                for row in cursor.fetchall():
                    aggregated_logs['statistics'][f'access_{row[0]}'] = row[1]
        
        # 获取监控日志
        if log_type in ['all', 'monitor']:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, metric_type, metric_value, metric_unit, created_at 
                    FROM monitor_metrics 
                    WHERE created_at > ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (time_threshold, limit))
                
                columns = ['id', 'metric_type', 'metric_value', 'metric_unit', 'created_at']
                monitor_logs = []
                for row in cursor.fetchall():
                    monitor_logs.append(dict(zip(columns, row)))
                
                aggregated_logs['logs'].extend(monitor_logs)
        
        # 获取错误日志
        if log_type in ['all', 'error']:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, error_type, message, details, resolved, created_at 
                    FROM ai_learning_errors 
                    WHERE created_at > ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (time_threshold, limit))
                
                columns = ['id', 'error_type', 'message', 'details', 'resolved', 'created_at']
                error_logs = []
                for row in cursor.fetchall():
                    error_logs.append(dict(zip(columns, row)))
                
                aggregated_logs['logs'].extend(error_logs)
                
                # 统计未解决错误
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM ai_learning_errors 
                    WHERE created_at > ? AND resolved = 0
                ''', (time_threshold,))
                
                aggregated_logs['statistics']['unresolved_errors'] = cursor.fetchone()[0]
        
        # 统计总数
        aggregated_logs['statistics']['total_logs'] = len(aggregated_logs['logs'])
        
        return jsonify({
            'success': True,
            'data': aggregated_logs,
            'count': len(aggregated_logs['logs'])
        })
        
    except Exception as e:
        logger.error(f'获取聚合日志失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_monitoring_api.route('/logs/statistics', methods=['GET'])
@require_admin_role
def get_log_statistics():
    """
    获取日志统计分析 - 提供各类日志的统计图表数据
    支持趋势分析、分布分析等
    """
    try:
        hours = int(request.args.get('hours', 24))
        granularity = request.args.get('granularity', 'hour')  # hour, day
        
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        statistics = {
            'timestamp': datetime.now().isoformat(),
            'time_range': {
                'start': time_threshold.isoformat(),
                'end': datetime.now().isoformat()
            },
            'system_logs': {},
            'access_logs': {},
            'error_logs': {},
            'trends': {}
        }
        
        # 系统日志统计
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 按级别统计
            cursor.execute('''
                SELECT level, COUNT(*) 
                FROM system_logs 
                WHERE created_at > ? 
                GROUP BY level
            ''', (time_threshold,))
            
            level_stats = {}
            for row in cursor.fetchall():
                level_stats[row[0]] = row[1]
            
            statistics['system_logs']['by_level'] = level_stats
            
            # 按模块统计
            cursor.execute('''
                SELECT module, COUNT(*) 
                FROM system_logs 
                WHERE created_at > ? 
                GROUP BY module 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            ''', (time_threshold,))
            
            module_stats = {}
            for row in cursor.fetchall():
                module_stats[row[0]] = row[1]
            
            statistics['system_logs']['by_module'] = module_stats
            
            # 按时间段统计趋势
            if granularity == 'hour':
                cursor.execute('''
                    SELECT strftime('%Y-%m-%d %H', created_at) as time_slot, level, COUNT(*) 
                    FROM system_logs 
                    WHERE created_at > ? 
                    GROUP BY time_slot, level
                    ORDER BY time_slot
                ''', (time_threshold,))
            else:
                cursor.execute('''
                    SELECT strftime('%Y-%m-%d', created_at) as time_slot, level, COUNT(*) 
                    FROM system_logs 
                    WHERE created_at > ? 
                    GROUP BY time_slot, level
                    ORDER BY time_slot
                ''', (time_threshold,))
            
            trend_data = []
            for row in cursor.fetchall():
                trend_data.append({
                    'time': row[0],
                    'level': row[1],
                    'count': row[2]
                })
            
            statistics['trends']['system_logs'] = trend_data
        
        # 访问日志统计
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 按路径统计
            cursor.execute('''
                SELECT path, COUNT(*) 
                FROM access_logs 
                WHERE access_time > ? 
                GROUP BY path 
                ORDER BY COUNT(*) DESC 
                LIMIT 20
            ''', (time_threshold,))
            
            path_stats = {}
            for row in cursor.fetchall():
                path_stats[row[0]] = row[1]
            
            statistics['access_logs']['by_path'] = path_stats
            
            # 按角色统计
            cursor.execute('''
                SELECT role, COUNT(*) 
                FROM access_logs 
                WHERE access_time > ? 
                GROUP BY role
            ''', (time_threshold,))
            
            role_stats = {}
            for row in cursor.fetchall():
                role_stats[row[0]] = row[1]
            
            statistics['access_logs']['by_role'] = role_stats
            
            # 按IP统计
            cursor.execute('''
                SELECT ip_address, COUNT(*) 
                FROM access_logs 
                WHERE access_time > ? 
                GROUP BY ip_address 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            ''', (time_threshold,))
            
            ip_stats = {}
            for row in cursor.fetchall():
                ip_stats[row[0]] = row[1]
            
            statistics['access_logs']['by_ip'] = ip_stats
            
            # 按方法统计
            cursor.execute('''
                SELECT method, COUNT(*) 
                FROM access_logs 
                WHERE access_time > ? 
                GROUP BY method
            ''', (time_threshold,))
            
            method_stats = {}
            for row in cursor.fetchall():
                method_stats[row[0]] = row[1]
            
            statistics['access_logs']['by_method'] = method_stats
        
        # 错误日志统计
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 按类型统计
            cursor.execute('''
                SELECT error_type, COUNT(*) 
                FROM ai_learning_errors 
                WHERE created_at > ? 
                GROUP BY error_type
            ''', (time_threshold,))
            
            error_type_stats = {}
            for row in cursor.fetchall():
                error_type_stats[row[0]] = row[1]
            
            statistics['error_logs']['by_type'] = error_type_stats
            
            # 按解决状态统计
            cursor.execute('''
                SELECT resolved, COUNT(*) 
                FROM ai_learning_errors 
                WHERE created_at > ? 
                GROUP BY resolved
            ''', (time_threshold,))
            
            resolved_stats = {}
            for row in cursor.fetchall():
                resolved_stats['resolved' if row[0] else 'unresolved'] = row[1]
            
            statistics['error_logs']['by_status'] = resolved_stats
        
        return jsonify({
            'success': True,
            'data': statistics
        })
        
    except Exception as e:
        logger.error(f'获取日志统计失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 性能监控与分析 ====================

@admin_monitoring_api.route('/performance', methods=['GET'])
def get_performance_metrics():
    """
    获取性能指标 - 实时性能数据和历史趋势
    支持多种图表类型的数据格式
    """
    try:
        hours = int(request.args.get('hours', 1))
        chart_type = request.args.get('chart_type', 'line')  # line, bar, pie, gauge
        
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        performance_data = {
            'timestamp': datetime.now().isoformat(),
            'chart_type': chart_type,
            'real_time': {},
            'historical': {},
            'analysis': {}
        }
        
        # 实时性能数据
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        performance_data['real_time'] = {
            'cpu': {
                'value': cpu_usage,
                'unit': '%',
                'status': 'healthy' if cpu_usage < 80 else 'warning' if cpu_usage < 95 else 'critical'
            },
            'memory': {
                'value': memory.percent,
                'unit': '%',
                'available': memory.available,
                'status': 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 95 else 'critical'
            },
            'disk': {
                'value': disk.percent,
                'unit': '%',
                'free': disk.free,
                'status': 'healthy' if disk.percent < 80 else 'warning' if disk.percent < 95 else 'critical'
            },
            'network': {
                'sent': net_io.bytes_sent,
                'recv': net_io.bytes_recv,
                'unit': 'bytes'
            }
        }
        
        # 历史性能数据 - 从monitor_metrics表获取
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # CPU历史
            cursor.execute('''
                SELECT metric_value, created_at 
                FROM monitor_metrics 
                WHERE metric_type = 'cpu_usage' AND created_at > ? 
                ORDER BY created_at ASC
            ''', (time_threshold,))
            
            cpu_history = []
            for row in cursor.fetchall():
                cpu_history.append({
                    'value': row[0],
                    'timestamp': row[1]
                })
            
            performance_data['historical']['cpu'] = cpu_history
            
            # 内存历史
            cursor.execute('''
                SELECT metric_value, created_at 
                FROM monitor_metrics 
                WHERE metric_type = 'memory_usage' AND created_at > ? 
                ORDER BY created_at ASC
            ''', (time_threshold,))
            
            memory_history = []
            for row in cursor.fetchall():
                memory_history.append({
                    'value': row[0],
                    'timestamp': row[1]
                })
            
            performance_data['historical']['memory'] = memory_history
            
            # 磁盘历史
            cursor.execute('''
                SELECT metric_value, created_at 
                FROM monitor_metrics 
                WHERE metric_type = 'disk_usage' AND created_at > ? 
                ORDER BY created_at ASC
            ''', (time_threshold,))
            
            disk_history = []
            for row in cursor.fetchall():
                disk_history.append({
                    'value': row[0],
                    'timestamp': row[1]
                })
            
            performance_data['historical']['disk'] = disk_history
        
        # 性能分析
        performance_data['analysis'] = _analyze_performance(performance_data)
        
        # 根据图表类型调整数据格式
        if chart_type == 'gauge':
            # 仪表盘格式
            performance_data['gauges'] = {
                'cpu': {'value': cpu_usage, 'min': 0, 'max': 100},
                'memory': {'value': memory.percent, 'min': 0, 'max': 100},
                'disk': {'value': disk.percent, 'min': 0, 'max': 100}
            }
        elif chart_type == 'pie':
            # 饼图格式 - 资源分布
            performance_data['pie_data'] = {
                'memory_distribution': [
                    {'label': '已使用', 'value': memory.used},
                    {'label': '可用', 'value': memory.available}
                ],
                'disk_distribution': [
                    {'label': '已使用', 'value': disk.used},
                    {'label': '可用', 'value': disk.free}
                ]
            }
        
        return jsonify({
            'success': True,
            'data': performance_data
        })
        
    except Exception as e:
        logger.error(f'获取性能指标失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _analyze_performance(performance_data: Dict) -> Dict:
    """分析性能数据，识别瓶颈并生成优化建议"""
    analysis = {
        'bottlenecks': [],
        'optimizations': [],
        'risk_level': 'low'
    }
    
    # 实时数据分析
    real_time = performance_data['real_time']
    
    # CPU瓶颈检测
    if real_time['cpu']['value'] >= 80:
        analysis['bottlenecks'].append({
            'type': 'cpu',
            'severity': 'high' if real_time['cpu']['value'] >= 95 else 'medium',
            'value': real_time['cpu']['value'],
            'description': 'CPU使用率过高，可能导致系统响应延迟'
        })
        analysis['optimizations'].append({
            'target': 'cpu',
            'suggestion': '检查高CPU消耗进程，优化计算密集型任务',
            'priority': 'high'
        })
    
    # 内存瓶颈检测
    if real_time['memory']['value'] >= 80:
        analysis['bottlenecks'].append({
            'type': 'memory',
            'severity': 'high' if real_time['memory']['value'] >= 95 else 'medium',
            'value': real_time['memory']['value'],
            'description': '内存使用率过高，可能导致系统不稳定'
        })
        analysis['optimizations'].append({
            'target': 'memory',
            'suggestion': '检查内存泄漏，清理缓存，考虑增加内存资源',
            'priority': 'high'
        })
    
    # 磁盘瓶颈检测
    if real_time['disk']['value'] >= 80:
        analysis['bottlenecks'].append({
            'type': 'disk',
            'severity': 'high' if real_time['disk']['value'] >= 95 else 'medium',
            'value': real_time['disk']['value'],
            'description': '磁盘空间不足，可能导致写入失败'
        })
        analysis['optimizations'].append({
            'target': 'disk',
            'suggestion': '清理临时文件和日志，压缩数据库，扩展存储',
            'priority': 'high'
        })
    
    # 历史数据分析 - 趋势预测
    historical = performance_data['historical']
    
    for metric_type in ['cpu', 'memory', 'disk']:
        history = historical.get(metric_type, [])
        if len(history) >= 10:
            # 计算平均值和趋势
            values = [h['value'] for h in history[-10:]]
            avg_value = sum(values) / len(values)
            
            # 简单趋势检测 (最后5个值与前5个值比较)
            if len(values) >= 10:
                recent_avg = sum(values[-5:]) / 5
                earlier_avg = sum(values[:5]) / 5
                
                if recent_avg > earlier_avg * 1.1:  # 增长超过10%
                    analysis['optimizations'].append({
                        'target': metric_type,
                        'suggestion': f'{metric_type}使用呈上升趋势，建议关注增长原因',
                        'priority': 'medium'
                    })
            
            # 记录平均值
            analysis[f'{metric_type}_avg'] = avg_value
    
    # 风险等级评估
    if len([b for b in analysis['bottlenecks'] if b['severity'] == 'high']) >= 2:
        analysis['risk_level'] = 'critical'
    elif len([b for b in analysis['bottlenecks'] if b['severity'] == 'high']) >= 1:
        analysis['risk_level'] = 'high'
    elif len(analysis['bottlenecks']) >= 2:
        analysis['risk_level'] = 'medium'
    elif len(analysis['bottlenecks']) >= 1:
        analysis['risk_level'] = 'low'
    
    return analysis


@admin_monitoring_api.route('/performance/bottleneck', methods=['GET'])
@require_admin_role
def identify_bottleneck():
    """
    性能瓶颈识别 - 深入分析系统性能瓶颈
    提供详细的瓶颈报告和优化方案
    """
    try:
        # 收集详细的性能数据
        process = psutil.Process()
        
        bottleneck_report = {
            'timestamp': datetime.now().isoformat(),
            'bottlenecks': [],
            'top_processes': [],
            'resource_analysis': {},
            'optimization_plan': []
        }
        
        # 分析CPU瓶颈
        cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
        avg_cpu = sum(cpu_usage) / len(cpu_usage)
        
        if avg_cpu >= 70:
            # 获取高CPU消耗进程
            high_cpu_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if proc.info['cpu_percent'] > 10:
                        high_cpu_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            high_cpu_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            bottleneck_report['top_processes'] = high_cpu_processes[:10]
            
            bottleneck_report['bottlenecks'].append({
                'type': 'cpu',
                'severity': 'critical' if avg_cpu >= 95 else 'high' if avg_cpu >= 85 else 'medium',
                'current_value': avg_cpu,
                'threshold': 70,
                'description': f'CPU平均使用率{avg_cpu}%超过阈值',
                'affected_cores': [i for i, usage in enumerate(cpu_usage) if usage >= 80]
            })
        
        # 分析内存瓶颈
        memory = psutil.virtual_memory()
        
        if memory.percent >= 70:
            bottleneck_report['bottlenecks'].append({
                'type': 'memory',
                'severity': 'critical' if memory.percent >= 95 else 'high' if memory.percent >= 85 else 'medium',
                'current_value': memory.percent,
                'threshold': 70,
                'description': f'内存使用率{memory.percent}%超过阈值',
                'available_mb': memory.available / (1024 * 1024)
            })
        
        # 分析磁盘瓶颈
        disk = psutil.disk_usage('/')
        
        if disk.percent >= 70:
            bottleneck_report['bottlenecks'].append({
                'type': 'disk',
                'severity': 'critical' if disk.percent >= 95 else 'high' if disk.percent >= 85 else 'medium',
                'current_value': disk.percent,
                'threshold': 70,
                'description': f'磁盘使用率{disk.percent}%超过阈值',
                'free_gb': disk.free / (1024 * 1024 * 1024)
            })
        
        # 网络瓶颈分析
        net_io = psutil.net_io_counters()
        bottleneck_report['resource_analysis']['network'] = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'errors': net_io.errin + net_io.errout,
            'drops': net_io.dropin + net_io.dropout
        }
        
        # 生成优化方案
        for bottleneck in bottleneck_report['bottlenecks']:
            optimization = {
                'target': bottleneck['type'],
                'priority': bottleneck['severity'],
                'actions': []
            }
            
            if bottleneck['type'] == 'cpu':
                optimization['actions'].extend([
                    '检查并优化高CPU消耗进程',
                    '考虑使用异步处理减少CPU阻塞',
                    '评估是否需要增加计算资源'
                ])
            
            elif bottleneck['type'] == 'memory':
                optimization['actions'].extend([
                    '检查是否存在内存泄漏',
                    '清理不必要的缓存数据',
                    '优化数据结构减少内存占用',
                    '考虑增加物理内存'
                ])
            
            elif bottleneck['type'] == 'disk':
                optimization['actions'].extend([
                    '清理临时文件和日志文件',
                    '执行数据库压缩和清理',
                    '归档历史数据',
                    '扩展存储容量'
                ])
            
            bottleneck_report['optimization_plan'].append(optimization)
        
        return jsonify({
            'success': True,
            'data': bottleneck_report
        })
        
    except Exception as e:
        logger.error(f'性能瓶颈识别失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_monitoring_api.route('/performance/optimize', methods=['POST'])
@require_admin_role
def generate_optimization_suggestions():
    """
    生成优化建议 - 根据当前系统状态生成具体的优化建议
    """
    try:
        # 获取当前性能状态
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        suggestions = {
            'timestamp': datetime.now().isoformat(),
            'immediate_actions': [],
            'long_term_improvements': [],
            'priority_order': []
        }
        
        # 即时优化建议
        if cpu_usage >= 80:
            suggestions['immediate_actions'].append({
                'action': '限制后台进程',
                'description': '临时限制非关键后台进程的CPU使用',
                'impact': '中等',
                'risk': '低'
            })
            suggestions['immediate_actions'].append({
                'action': '重启高消耗服务',
                'description': '重启CPU消耗异常的服务进程',
                'impact': '高',
                'risk': '中'
            })
        
        if memory.percent >= 80:
            suggestions['immediate_actions'].append({
                'action': '清理缓存',
                'description': '释放不必要的缓存数据',
                'impact': '中等',
                'risk': '低'
            })
            suggestions['immediate_actions'].append({
                'action': '重启内存泄漏进程',
                'description': '识别并重启存在内存泄漏的进程',
                'impact': '高',
                'risk': '中'
            })
        
        if disk.percent >= 80:
            suggestions['immediate_actions'].append({
                'action': '清理临时文件',
                'description': '删除临时文件和旧日志',
                'impact': '中等',
                'risk': '低'
            })
            suggestions['immediate_actions'].append({
                'action': '数据库压缩',
                'description': '执行数据库VACUUM操作',
                'impact': '高',
                'risk': '中'
            })
        
        # 长期优化建议
        suggestions['long_term_improvements'].extend([
            {
                'action': '实施负载均衡',
                'description': '将高负载任务分散到多个实例',
                'timeline': '1-2周',
                'cost': '中'
            },
            {
                'action': '优化数据库查询',
                'description': '添加索引、优化SQL查询',
                'timeline': '3-5天',
                'cost': '低'
            },
            {
                'action': '引入缓存策略',
                'description': '使用Redis或内存缓存减少数据库访问',
                'timeline': '1周',
                'cost': '中'
            },
            {
                'action': '异步任务处理',
                'description': '将耗时操作转为异步处理',
                'timeline': '1-2周',
                'cost': '中'
            }
        ])
        
        # 优先级排序
        priorities = []
        
        if cpu_usage >= 95:
            priorities.append(('cpu', 'critical'))
        elif cpu_usage >= 80:
            priorities.append(('cpu', 'high'))
        
        if memory.percent >= 95:
            priorities.append(('memory', 'critical'))
        elif memory.percent >= 80:
            priorities.append(('memory', 'high'))
        
        if disk.percent >= 95:
            priorities.append(('disk', 'critical'))
        elif disk.percent >= 80:
            priorities.append(('disk', 'high'))
        
        # 按优先级排序
        priorities.sort(key=lambda x: x[1], reverse=True)
        suggestions['priority_order'] = priorities
        
        return jsonify({
            'success': True,
            'data': suggestions
        })
        
    except Exception as e:
        logger.error(f'生成优化建议失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 数据可视化 ====================

@admin_monitoring_api.route('/dashboard/data', methods=['GET'])
def get_dashboard_data():
    """
    获取仪表板数据 - 综合仪表板所需的所有数据
    支持实时更新和交互式展示
    """
    try:
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'charts': {},
            'tables': {},
            'alerts': [],
            'widgets': {}
        }
        
        # 系统概览
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        dashboard['summary'] = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory.percent,
            'disk_usage': disk.percent,
            'status': 'healthy' if max(cpu_usage, memory.percent, disk.percent) < 80 else 'warning'
        }
        
        # 用户统计
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM sessions WHERE expires_at > ?', (datetime.now(),))
            active_session = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM questions')
            question_count = cursor.fetchone()[0]
            
            dashboard['summary']['user_count'] = user_count
            dashboard['summary']['active_sessions'] = active_session
            dashboard['summary']['question_count'] = question_count
        
        # CPU趋势图表数据
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            time_threshold = datetime.now() - timedelta(hours=24)
            
            cursor.execute('''
                SELECT strftime('%Y-%m-%d %H', created_at) as hour, AVG(metric_value) as avg_value
                FROM monitor_metrics 
                WHERE metric_type = 'cpu_usage' AND created_at > ? 
                GROUP BY hour 
                ORDER BY hour
            ''', (time_threshold,))
            
            cpu_chart_data = []
            for row in cursor.fetchall():
                cpu_chart_data.append({
                    'time': row[0],
                    'value': row[1]
                })
            
            dashboard['charts']['cpu_trend'] = {
                'type': 'line',
                'title': 'CPU使用率趋势',
                'data': cpu_chart_data,
                'config': {
                    'xAxis': 'time',
                    'yAxis': 'value',
                    'yAxisLabel': '使用率 (%)',
                    'colors': ['#3b82f6']
                }
            }
            
            # 内存趋势图表数据
            cursor.execute('''
                SELECT strftime('%Y-%m-%d %H', created_at) as hour, AVG(metric_value) as avg_value
                FROM monitor_metrics 
                WHERE metric_type = 'memory_usage' AND created_at > ? 
                GROUP BY hour 
                ORDER BY hour
            ''', (time_threshold,))
            
            memory_chart_data = []
            for row in cursor.fetchall():
                memory_chart_data.append({
                    'time': row[0],
                    'value': row[1]
                })
            
            dashboard['charts']['memory_trend'] = {
                'type': 'line',
                'title': '内存使用率趋势',
                'data': memory_chart_data,
                'config': {
                    'xAxis': 'time',
                    'yAxis': 'value',
                    'yAxisLabel': '使用率 (%)',
                    'colors': ['#10b981']
                }
            }
            
            # 磁盘使用饼图
            dashboard['charts']['disk_usage'] = {
                'type': 'pie',
                'title': '磁盘空间分布',
                'data': [
                    {'label': '已使用', 'value': disk.used, 'color': '#ef4444'},
                    {'label': '可用空间', 'value': disk.free, 'color': '#22c55e'}
                ]
            }
            
            # 访问统计柱状图
            cursor.execute('''
                SELECT path, COUNT(*) as count
                FROM access_logs 
                WHERE access_time > ? 
                GROUP BY path 
                ORDER BY count DESC 
                LIMIT 10
            ''', (time_threshold,))
            
            access_chart_data = []
            for row in cursor.fetchall():
                access_chart_data.append({
                    'label': row[0][:30],  # 截断路径
                    'value': row[1]
                })
            
            dashboard['charts']['top_access'] = {
                'type': 'bar',
                'title': '热门访问路径',
                'data': access_chart_data,
                'config': {
                    'xAxis': 'label',
                    'yAxis': 'value',
                    'yAxisLabel': '访问次数'
                }
            }
        
        # 告警表格
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, alert_type, alert_level, message, resolved, created_at 
                FROM monitor_alerts 
                WHERE resolved = 0 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            
            columns = ['id', 'alert_type', 'alert_level', 'message', 'resolved', 'created_at']
            alerts_table = []
            for row in cursor.fetchall():
                alerts_table.append(dict(zip(columns, row)))
            
            dashboard['tables']['recent_alerts'] = alerts_table
        
        # 系统状态组件
        dashboard['widgets']['system_status'] = {
            'cpu': {
                'value': cpu_usage,
                'status': 'healthy' if cpu_usage < 80 else 'warning' if cpu_usage < 95 else 'critical',
                'icon': 'cpu'
            },
            'memory': {
                'value': memory.percent,
                'status': 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 95 else 'critical',
                'icon': 'memory'
            },
            'disk': {
                'value': disk.percent,
                'status': 'healthy' if disk.percent < 80 else 'warning' if disk.percent < 95 else 'critical',
                'icon': 'disk'
            }
        }
        
        # 实时告警
        dashboard['alerts'] = alerts_table
        
        return jsonify({
            'success': True,
            'data': dashboard
        })
        
    except Exception as e:
        logger.error(f'获取仪表板数据失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_monitoring_api.route('/dashboard/realtime', methods=['GET'])
def get_realtime_data():
    """
    获取实时数据 - 用于实时更新的数据源
    支持WebSocket推送格式
    """
    try:
        realtime = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }
        
        # 实时CPU
        realtime['metrics']['cpu'] = {
            'value': psutil.cpu_percent(interval=0.5),
            'per_cpu': psutil.cpu_percent(interval=0.5, percpu=True)
        }
        
        # 实时内存
        memory = psutil.virtual_memory()
        realtime['metrics']['memory'] = {
            'value': memory.percent,
            'available': memory.available,
            'used': memory.used
        }
        
        # 实时磁盘IO
        disk_io = psutil.disk_io_counters()
        realtime['metrics']['disk_io'] = {
            'read_bytes': disk_io.read_bytes if disk_io else 0,
            'write_bytes': disk_io.write_bytes if disk_io else 0
        }
        
        # 实时网络IO
        net_io = psutil.net_io_counters()
        realtime['metrics']['network'] = {
            'sent': net_io.bytes_sent,
            'recv': net_io.bytes_recv
        }
        
        # 实时进程数
        realtime['metrics']['process_count'] = len(psutil.pids())
        
        return jsonify({
            'success': True,
            'data': realtime
        })
        
    except Exception as e:
        logger.error(f'获取实时数据失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_monitoring_api.route('/dashboard/configure', methods=['POST'])
@require_admin_role
def configure_dashboard():
    """
    配置仪表板 - 自定义仪表板布局和显示内容
    """
    try:
        config = request.get_json()
        
        # 保存配置到数据库
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 创建仪表板配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dashboard_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    config_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            user_id = session.get('user_id', 0)
            
            # 检查是否已有配置
            cursor.execute('SELECT id FROM dashboard_config WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE dashboard_config 
                    SET config_json = ?, updated_at = ? 
                    WHERE user_id = ?
                ''', (json.dumps(config), datetime.now(), user_id))
            else:
                cursor.execute('''
                    INSERT INTO dashboard_config (user_id, config_json)
                    VALUES (?, ?)
                ''', (user_id, json.dumps(config)))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '仪表板配置已保存'
        })
        
    except Exception as e:
        logger.error(f'配置仪表板失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 服务监控 ====================

@admin_monitoring_api.route('/services', methods=['GET'])
def get_services_status():
    """
    获取服务状态 - 监控所有系统服务的运行状态
    """
    try:
        services = {
            'timestamp': datetime.now().isoformat(),
            'services': [],
            'summary': {}
        }
        
        # 定义服务列表
        service_list = [
            {'name': '数据库服务', 'id': 'database', 'type': 'core'},
            {'name': '监控系统', 'id': 'monitor', 'type': 'monitoring'},
            {'name': '会话管理', 'id': 'session', 'type': 'core'},
            {'name': '权限管理', 'id': 'permission', 'type': 'security'},
            {'name': '规则引擎', 'id': 'rule', 'type': 'core'},
            {'name': '缓存系统', 'id': 'cache', 'type': 'performance'},
            {'name': 'AI引擎', 'id': 'ai_engine', 'type': 'ai'},
            {'name': 'API路由', 'id': 'api', 'type': 'network'}
        ]
        
        # 检查各服务状态
        for service in service_list:
            status = _check_service_status(service['id'])
            service['status'] = status['status']
            service['details'] = status['details']
            service['last_check'] = datetime.now().isoformat()
            services['services'].append(service)
        
        # 统计摘要
        status_counts = {}
        for service in services['services']:
            status_counts[service['status']] = status_counts.get(service['status'], 0) + 1
        
        services['summary'] = {
            'total': len(services['services']),
            'healthy': status_counts.get('healthy', 0),
            'warning': status_counts.get('warning', 0),
            'critical': status_counts.get('critical', 0),
            'unknown': status_counts.get('unknown', 0)
        }
        
        return jsonify({
            'success': True,
            'data': services
        })
        
    except Exception as e:
        logger.error(f'获取服务状态失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _check_service_status(service_id: str) -> Dict:
    """检查单个服务状态"""
    status = {'status': 'unknown', 'details': {}}
    
    try:
        if service_id == 'database':
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                status['status'] = 'healthy'
                status['details']['connection'] = 'active'
        
        elif service_id == 'monitor':
            from app.utils.monitor_manager import get_monitor_manager
            monitor = get_monitor_manager()
            if monitor.is_running:
                status['status'] = 'healthy'
                status['details']['running'] = True
            else:
                status['status'] = 'warning'
                status['details']['running'] = False
        
        elif service_id == 'session':
            from app.utils.session_manager import get_session_manager
            sm = get_session_manager()
            status['status'] = 'healthy'
            status['details']['active_sessions'] = len(sm.get_active_sessions())
        
        elif service_id == 'permission':
            from app.utils.permission_manager import get_permission_manager
            pm = get_permission_manager()
            status['status'] = 'healthy'
            status['details']['roles_count'] = len(pm.get_all_roles())
        
        elif service_id == 'rule':
            from app.utils.rule_manager import get_rule_manager
            rm = get_rule_manager()
            status['status'] = 'healthy'
            status['details']['rules_loaded'] = True
        
        elif service_id == 'cache':
            status['status'] = 'healthy'
            status['details']['cache_enabled'] = True
        
        elif service_id == 'ai_engine':
            # 简单检查AI引擎目录
            ai_engine_path = os.path.join(os.path.dirname(DB_PATH), 'ai_engines')
            if os.path.exists(ai_engine_path):
                status['status'] = 'healthy'
                status['details']['engine_path'] = ai_engine_path
            else:
                status['status'] = 'warning'
                status['details']['engine_path'] = 'not found'
        
        elif service_id == 'api':
            status['status'] = 'healthy'
            status['details']['api_running'] = True
        
    except Exception as e:
        status['status'] = 'warning'
        status['details']['error'] = str(e)
    
    return status


# ==================== 监控规则配置 ====================

@admin_monitoring_api.route('/rules', methods=['GET'])
@require_admin_role
def get_monitoring_rules():
    """
    获取监控规则 - 查看当前的监控阈值和规则配置
    """
    try:
        rules = {
            'timestamp': datetime.now().isoformat(),
            'thresholds': {},
            'alerts': {},
            'notifications': {}
        }
        
        from app.utils.rule_manager import get_rule_manager
        rm = get_rule_manager()
        
        # 获取监控阈值规则
        threshold_rules = [
            'MONITOR_THRESHOLD_CPU',
            'MONITOR_THRESHOLD_MEMORY',
            'ALERT_THRESHOLD_DISK',
            'MONITOR_ALERT_ENABLED',
            'NAV_ANOMALY_BACK_THRESHOLD',
            'NAV_ANOMALY_TIME_WINDOW'
        ]
        
        for rule_name in threshold_rules:
            rules['thresholds'][rule_name] = rm.get_rule(rule_name) or '未设置'
        
        # 获取告警配置
        rules['alerts']['enabled'] = str(rm.get_rule('MONITOR_ALERT_ENABLED')).lower() == 'true'
        rules['alerts']['auto_resolve'] = str(rm.get_rule('MONITOR_AUTO_RESOLVE')).lower() == 'true'
        
        return jsonify({
            'success': True,
            'data': rules
        })
        
    except Exception as e:
        logger.error(f'获取监控规则失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_monitoring_api.route('/rules/update', methods=['POST'])
@require_admin_role
def update_monitoring_rules():
    """
    更新监控规则 - 设置监控阈值和告警规则
    """
    try:
        data = request.get_json()
        
        from app.utils.rule_manager import get_rule_manager
        rm = get_rule_manager()
        
        # 更新阈值规则
        if 'thresholds' in data:
            for rule_name, value in data['thresholds'].items():
                rm.set_rule(rule_name, str(value))
        
        return jsonify({
            'success': True,
            'message': '监控规则已更新'
        })
        
    except Exception as e:
        logger.error(f'更新监控规则失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 系统资源监控 ====================

@admin_monitoring_api.route('/resources', methods=['GET'])
def get_system_resources():
    """
    获取系统资源详情 - 详细的资源使用情况
    """
    try:
        resources = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {},
            'memory': {},
            'disk': {},
            'network': {},
            'process': {}
        }
        
        # CPU详情
        resources['cpu'] = {
            'usage_percent': psutil.cpu_percent(interval=1),
            'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
            'count': psutil.cpu_count(),
            'count_logical': psutil.cpu_count(logical=True),
            'count_physical': psutil.cpu_count(logical=False),
            'freq': {
                'current': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'min': psutil.cpu_freq().min if psutil.cpu_freq() else 0,
                'max': psutil.cpu_freq().max if psutil.cpu_freq() else 0
            }
        }
        
        # 内存详情
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        resources['memory'] = {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'free': memory.free,
            'percent': memory.percent,
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'free': swap.free,
                'percent': swap.percent
            }
        }
        
        # 磁盘详情
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        resources['disk'] = {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent,
            'io': {
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0
            }
        }
        
        # 网络详情
        net_io = psutil.net_io_counters()
        resources['network'] = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'errors': {
                'in': net_io.errin,
                'out': net_io.errout
            },
            'drops': {
                'in': net_io.dropin,
                'out': net_io.dropout
            }
        }
        
        # 进程详情
        process = psutil.Process()
        resources['process'] = {
            'pid': process.pid,
            'name': process.name(),
            'status': process.status(),
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'threads': process.num_threads(),
            'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0,
            'connections': len(process.connections()) if hasattr(process, 'connections') else 0
        }
        
        return jsonify({
            'success': True,
            'data': resources
        })
        
    except Exception as e:
        logger.error(f'获取系统资源失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 错误处理 ====================

@admin_monitoring_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API endpoint not found'
    }), 404


@admin_monitoring_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


@admin_monitoring_api.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Permission denied'
    }), 403