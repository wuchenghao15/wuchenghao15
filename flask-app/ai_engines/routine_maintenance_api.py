#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动例行维护升级系统API接口
提供维护任务调度、执行和监控功能
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

from app.ai.auto_routine_maintenance import (
    auto_routine_maintenance_system,
    TaskType,
    TaskPriority,
    MaintenanceTask
)

logger = logging.getLogger('routine_maintenance_api')

maintenance_bp = Blueprint('routine_maintenance', __name__, url_prefix='/api/maintenance')


@maintenance_bp.route('/status', methods=['GET'])
def get_maintenance_status():
    """获取维护系统状态"""
    try:
        status = auto_routine_maintenance_system.get_maintenance_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"获取维护状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有维护任务"""
    try:
        tasks = auto_routine_maintenance_system.scheduler.get_all_tasks()
        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/tasks', methods=['POST'])
def create_task():
    """创建新的维护任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        task_type_str = data.get('task_type')
        task_name = data.get('name', f'Task {task_type_str}')
        priority_str = data.get('priority', 'NORMAL')
        schedule_time = data.get('schedule_time')
        
        try:
            task_type = TaskType(task_type_str)
        except ValueError:
            return jsonify({'success': False, 'error': f'无效的任务类型: {task_type_str}'}), 400
        
        try:
            priority = TaskPriority[priority_str.upper()]
        except KeyError:
            priority = TaskPriority.NORMAL
        
        schedule_dt = None
        if schedule_time:
            try:
                schedule_dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
            except Exception:
                return jsonify({'success': False, 'error': '无效的时间格式'}), 400
        
        task = auto_routine_maintenance_system.scheduler.schedule_task(
            task_type=task_type,
            name=task_name,
            schedule_time=schedule_dt
        )
        
        return jsonify({
            'success': True,
            'message': f'任务已创建: {task.name}',
            'task_id': task.id
        })
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取特定任务状态"""
    try:
        status = auto_routine_maintenance_system.scheduler.get_task_status(task_id)
        
        if not status:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        return jsonify({
            'success': True,
            'task': status
        })
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/tasks/<task_id>/execute', methods=['POST'])
def execute_task(task_id):
    """执行特定任务"""
    try:
        success = auto_routine_maintenance_system.scheduler.execute_task(task_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'任务已开始执行: {task_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': '任务执行失败或任务正在运行'
            }), 400
    except Exception as e:
        logger.error(f"执行任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    try:
        success = auto_routine_maintenance_system.scheduler.cancel_task(task_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'任务已取消: {task_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': '任务取消失败或任务正在运行'
            }), 400
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/tasks/completed', methods=['GET'])
def get_completed_tasks():
    """获取已完成任务"""
    try:
        limit = int(request.args.get('limit', 100))
        tasks = auto_routine_maintenance_system.scheduler.get_completed_tasks(limit)
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })
    except Exception as e:
        logger.error(f"获取已完成任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取调度统计"""
    try:
        stats = auto_routine_maintenance_system.scheduler.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/scheduled', methods=['GET'])
def get_next_scheduled():
    """获取下一个调度的任务"""
    try:
        next_tasks = auto_routine_maintenance_system._get_next_scheduled_tasks()
        
        return jsonify({
            'success': True,
            'next_tasks': next_tasks,
            'count': len(next_tasks)
        })
    except Exception as e:
        logger.error(f"获取调度任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/window/execute', methods=['POST'])
def execute_maintenance_window():
    """执行维护窗口"""
    try:
        data = request.get_json() or {}
        window_type = data.get('window_type', 'daily')
        
        if window_type not in ['daily', 'weekly', 'monthly']:
            return jsonify({
                'success': False,
                'error': '无效的维护窗口类型'
            }), 400
        
        result = auto_routine_maintenance_system.execute_maintenance_window(window_type)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"执行维护窗口失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/upgrade/check', methods=['POST'])
def check_upgrades():
    """检查并执行升级"""
    try:
        result = auto_routine_maintenance_system.check_and_perform_upgrades()
        
        return jsonify({
            'success': True,
            'upgrade_info': result
        })
    except Exception as e:
        logger.error(f"检查升级失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/history', methods=['GET'])
def get_maintenance_history():
    """获取维护历史"""
    try:
        limit = int(request.args.get('limit', 50))
        history = auto_routine_maintenance_system.get_maintenance_history(limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取维护历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/policies', methods=['GET'])
def get_maintenance_policies():
    """获取维护策略"""
    try:
        policies = auto_routine_maintenance_system.maintenance_policies
        
        return jsonify({
            'success': True,
            'policies': policies
        })
    except Exception as e:
        logger.error(f"获取维护策略失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/enable', methods=['POST'])
def enable_maintenance():
    """启用维护系统"""
    try:
        auto_routine_maintenance_system.enable_maintenance()
        return jsonify({
            'success': True,
            'message': '自动维护系统已启用'
        })
    except Exception as e:
        logger.error(f"启用维护系统失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/disable', methods=['POST'])
def disable_maintenance():
    """禁用维护系统"""
    try:
        auto_routine_maintenance_system.disable_maintenance()
        return jsonify({
            'success': True,
            'message': '自动维护系统已禁用'
        })
    except Exception as e:
        logger.error(f"禁用维护系统失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/auto-upgrade/enable', methods=['POST'])
def enable_auto_upgrade():
    """启用自动升级"""
    try:
        auto_routine_maintenance_system.enable_auto_upgrade()
        return jsonify({
            'success': True,
            'message': '自动升级已启用'
        })
    except Exception as e:
        logger.error(f"启用自动升级失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/auto-upgrade/disable', methods=['POST'])
def disable_auto_upgrade():
    """禁用自动升级"""
    try:
        auto_routine_maintenance_system.disable_auto_upgrade()
        return jsonify({
            'success': True,
            'message': '自动升级已禁用'
        })
    except Exception as e:
        logger.error(f"禁用自动升级失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/task-types', methods=['GET'])
def get_task_types():
    """获取所有任务类型"""
    try:
        task_types = [
            {
                'value': tt.value,
                'name': tt.name.replace('_', ' ').title(),
                'description': get_task_type_description(tt)
            }
            for tt in TaskType
        ]
        
        return jsonify({
            'success': True,
            'task_types': task_types
        })
    except Exception as e:
        logger.error(f"获取任务类型失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def get_task_type_description(task_type: TaskType) -> str:
    """获取任务类型描述"""
    descriptions = {
        TaskType.SYSTEM_CHECK: '检查系统资源使用情况',
        TaskType.DATABASE_CLEANUP: '清理数据库冗余数据',
        TaskType.LOG_CLEANUP: '清理过期日志文件',
        TaskType.CACHE_CLEANUP: '清理应用缓存',
        TaskType.SECURITY_SCAN: '执行安全漏洞扫描',
        TaskType.PERFORMANCE_TUNE: '系统性能调优',
        TaskType.BACKUP: '执行数据备份',
        TaskType.UPGRADE_CHECK: '检查系统更新',
        TaskType.DEPENDENCY_UPDATE: '更新项目依赖',
        TaskType.HEALTH_CHECK: '系统健康检查',
        TaskType.METRICS_COLLECTION: '收集系统指标'
    }
    return descriptions.get(task_type, '未知任务类型')
