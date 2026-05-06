#!/usr/bin/env python3
"""
服务器优化AI API接口

from flask import Blueprint, jsonify, request
from services.server_optimizer_ai import server_optimizer_ai
from utils.logging import logger

server_optimizer_bp = Blueprint('server_optimizer', __name__, url_prefix='/api/server-optimizer')

@server_optimizer_bp.route('/status', methods=['GET'])
def get_server_status():
    """获取服务器状态"""
    try:
        status = server_optimizer_ai.get_current_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取服务器状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@server_optimizer_bp.route('/performance', methods=['GET'])
def get_performance_data():
    """获取性能数据"""
    try:
        performance_data = server_optimizer_ai.get_performance_data(hours)
        return jsonify({
            'success': True,
            'data': performance_data,
            'count': len(performance_data)
        })
    except Exception as e:
        logger.error(f"获取性能数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@server_optimizer_bp.route('/optimizations', methods=['GET'])
def get_optimization_history():
    """获取优化历史"""
    try:
        optimizations = server_optimizer_ai.get_optimization_history(days)
        return jsonify({
            'success': True,
            'data': optimizations,
            'count': len(optimizations)
        })
    except Exception as e:
        logger.error(f"获取优化历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@server_optimizer_bp.route('/events', methods=['GET'])
def get_server_events():
    """获取服务器事件"""
    try:
        events = server_optimizer_ai.get_server_events(days)
        return jsonify({
            'success': True,
            'count': len(events)
        })
    except Exception as e:
        logger.error(f"获取服务器事件失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@server_optimizer_bp.route('/optimize', methods=['POST'])
def run_optimization():
    """执行优化"""
    try:
        server_optimizer_ai._perform_optimization()

        return jsonify({
            'success': True,
            'message': '优化执行成功'
        })
    except Exception as e:
        logger.error(f"执行优化失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@server_optimizer_bp.route('/optimize/memory', methods=['POST'])
def optimize_memory():
    """优化内存"""
    try:

        if optimization:
            return jsonify({
                'success': True,
                'data': optimization
            })
        else:
            return jsonify({
                'success': True,
                'message': '内存优化完成，无明显改进'
            })
    except Exception as e:
        logger.error(f"内存优化失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@server_optimizer_bp.route('/optimize/disk', methods=['POST'])
def optimize_disk():
    """优化磁盘"""
    try:

        if optimization:
            return jsonify({
                'success': True,
                'data': optimization
            })
        else:
            return jsonify({
                'success': True,
            })
    except Exception as e:
        logger.error(f"磁盘优化失败: {str(e)}")
            'success': False,
            'error': str(e)

@server_optimizer_bp.route('/optimize/processes', methods=['POST'])
def optimize_processes():
    """优化进程"""
    try:

        if optimization:
            return jsonify({
                'success': True,
                'data': optimization
            })
        else:
            return jsonify({
                'success': True,
                'message': '进程优化完成，无明显改进'
    except Exception as e:
        logger.error(f"进程优化失败: {str(e)}")
        return jsonify({
            'success': False,
        }), 500

@server_optimizer_bp.route('/optimize/network', methods=['POST'])
    """优化网络"""
    try:

        if optimization:
            return jsonify({
                'success': True,
                'data': optimization
            })
        else:
            return jsonify({
                'success': True,
                'message': '网络优化完成，无明显改进'
            })
        logger.error(f"网络优化失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@server_optimizer_bp.route('/thresholds', methods=['GET'])
def get_thresholds():
    """获取优化阈值"""
    try:
            'success': True,
            'data': thresholds
        })
    except Exception as e:
        logger.error(f"获取优化阈值失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@server_optimizer_bp.route('/thresholds', methods=['POST'])
def set_thresholds():
    """设置优化阈值"""
    try:

        if data:
            for key, value in data.items():
                if key in server_optimizer_ai.thresholds:
                    server_optimizer_ai.thresholds[key] = value

            return jsonify({
                'success': True,
                'message': '阈值设置成功',
                'data': server_optimizer_ai.thresholds
            })
        else:
            return jsonify({
                'success': False,
                'error': '请提供阈值数据'
            }), 400
    except Exception as e:
        logger.error(f"设置优化阈值失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@server_optimizer_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """获取服务器指标"""
    try:
        status = server_optimizer_ai.get_current_status()

        performance_data = server_optimizer_ai.get_performance_data(1)  # 最近1小时

        # 计算平均值
        if performance_data:
            avg_cpu = sum([item['cpu_usage'] for item in performance_data]) / len(performance_data)
            avg_memory = sum([item['memory_usage'] for item in performance_data]) / len(performance_data)
            avg_disk = sum([item['disk_usage'] for item in performance_data]) / len(performance_data)
        else:
            avg_cpu = 0
            avg_disk = 0

        metrics = {
            'current': status.get('performance', {}),
            'average': {
                'cpu_usage': avg_cpu,
                'memory_usage': avg_memory,
                'disk_usage': avg_disk
            },
            'top_processes': status.get('top_processes', []),
            'recent_optimizations': status.get('recent_optimizations', [])
        }

        return jsonify({
            'success': True,
            'data': metrics
        })
        logger.error(f"获取服务器指标失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
