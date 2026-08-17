#!/usr/bin/env python3
"""
AI集群管理API
提供集群状态查询、集群创建/销毁、员工管理、任务调度等功能
"""

import os
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

ai_cluster_api = Bluelogger.info('ai_cluster_api', __name__)


def _get_cluster_manager():
    try:
        from ai_engines.cluster_matrix_manager import ClusterMatrixManager
        return ClusterMatrixManager()
    except Exception as e:
        return None


def _get_ai_cluster_manager():
    try:
        from ai_engines.ai_cluster_manager import ai_cluster_manager
        return ai_cluster_manager
    except Exception as e:
        return None


@ai_cluster_api.route('/api/ai/cluster/status', methods=['GET'])
@require_admin
def get_cluster_status():
    manager = _get_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': '集群管理器不可用'}), 503
    
    return jsonify({
        'success': True,
        'data': {
            'initialized': manager._initialized,
            'timestamp': datetime.now().isoformat()
        }
    })


@ai_cluster_api.route('/api/ai/cluster/matrix/employee', methods=['GET'])
@require_admin
def get_employee_cluster_matrix():
    manager = _get_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': '集群管理器不可用'}), 503
    
    try:
        result = manager.get_employee_cluster_matrix()
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/list', methods=['GET'])
@require_admin
def list_clusters():
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    try:
        clusters = []
        for cluster_id, cluster in manager.clusters.items():
            clusters.append({
                'cluster_id': cluster_id,
                'cluster_type': cluster.cluster_type,
                'status': cluster.status,
                'employee_count': len(cluster.employees),
                'task_queue_length': len(cluster.task_queue),
                'created_at': cluster.created_at,
                'last_updated': cluster.last_updated
            })
        
        return jsonify({
            'success': True,
            'data': clusters,
            'count': len(clusters),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/<cluster_id>', methods=['GET'])
@require_admin
def get_cluster_detail(cluster_id):
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    try:
        if cluster_id not in manager.clusters:
            return jsonify({'success': False, 'error': '集群不存在'}), 404
        
        cluster = manager.clusters[cluster_id]
        
        employees = []
        for emp_id, emp in cluster.employees.items():
            employees.append({
                'employee_id': emp.employee_id,
                'employee_type': emp.employee_type,
                'status': emp.status,
                'capabilities': emp.capabilities,
                'assigned_cluster': emp.assigned_cluster,
                'tasks_completed': emp.performance_metrics.get('tasks_completed', 0),
                'success_rate': emp.performance_metrics.get('success_rate', 0),
                'last_heartbeat': emp.last_heartbeat
            })
        
        return jsonify({
            'success': True,
            'data': {
                'cluster_id': cluster_id,
                'cluster_type': cluster.cluster_type,
                'status': cluster.status,
                'employees': employees,
                'employee_count': len(employees),
                'task_queue_length': len(cluster.task_queue),
                'created_at': cluster.created_at,
                'last_updated': cluster.last_updated
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster', methods=['POST'])
@require_admin
def create_cluster():
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    data = request.get_json() or {}
    
    cluster_type = data.get('cluster_type', 'general')
    cluster_name = data.get('cluster_name', f'cluster_{int(datetime.now().timestamp())}')
    
    try:
        result = manager.create_cluster(cluster_name, cluster_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/<cluster_id>', methods=['DELETE'])
@require_admin
def destroy_cluster(cluster_id):
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    try:
        result = manager.destroy_cluster(cluster_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/<cluster_id>/employees', methods=['GET'])
@require_admin
def get_cluster_employees(cluster_id):
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    try:
        if cluster_id not in manager.clusters:
            return jsonify({'success': False, 'error': '集群不存在'}), 404
        
        cluster = manager.clusters[cluster_id]
        
        employees = []
        for emp_id, emp in cluster.employees.items():
            employees.append({
                'employee_id': emp.employee_id,
                'employee_type': emp.employee_type,
                'status': emp.status,
                'capabilities': emp.capabilities,
                'performance': emp.performance_metrics,
                'last_heartbeat': emp.last_heartbeat,
                'created_at': emp.created_at
            })
        
        return jsonify({
            'success': True,
            'data': employees,
            'count': len(employees),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/<cluster_id>/employee/<employee_id>', methods=['GET'])
@require_admin
def get_cluster_employee_detail(cluster_id, employee_id):
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    try:
        if cluster_id not in manager.clusters:
            return jsonify({'success': False, 'error': '集群不存在'}), 404
        
        cluster = manager.clusters[cluster_id]
        
        if employee_id not in cluster.employees:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        emp = cluster.employees[employee_id]
        
        return jsonify({
            'success': True,
            'data': {
                'employee_id': emp.employee_id,
                'employee_type': emp.employee_type,
                'status': emp.status,
                'capabilities': emp.capabilities,
                'assigned_cluster': emp.assigned_cluster,
                'performance_metrics': emp.performance_metrics,
                'last_heartbeat': emp.last_heartbeat,
                'created_at': emp.created_at,
                'last_task': emp.last_task
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/<cluster_id>/assign', methods=['POST'])
@require_admin
def assign_employee_to_cluster(cluster_id):
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    data = request.get_json() or {}
    employee_id = data.get('employee_id')
    
    if not employee_id:
        return jsonify({'success': False, 'error': 'employee_id不能为空'}), 400
    
    try:
        result = manager.assign_employee(cluster_id, employee_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/<cluster_id>/unassign', methods=['POST'])
@require_admin
def unassign_employee_from_cluster(cluster_id):
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    data = request.get_json() or {}
    employee_id = data.get('employee_id')
    
    if not employee_id:
        return jsonify({'success': False, 'error': 'employee_id不能为空'}), 400
    
    try:
        result = manager.unassign_employee(cluster_id, employee_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/<cluster_id>/scale', methods=['POST'])
@require_admin
def scale_cluster(cluster_id):
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    data = request.get_json() or {}
    target_size = data.get('target_size')
    
    if target_size is None:
        return jsonify({'success': False, 'error': 'target_size不能为空'}), 400
    
    try:
        result = manager.scale_cluster(cluster_id, target_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/<cluster_id>/tasks', methods=['GET'])
@require_admin
def get_cluster_tasks(cluster_id):
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    try:
        if cluster_id not in manager.clusters:
            return jsonify({'success': False, 'error': '集群不存在'}), 404
        
        cluster = manager.clusters[cluster_id]
        
        tasks = []
        for task in cluster.task_queue:
            tasks.append({
                'task_id': task.get('task_id'),
                'task_type': task.get('task_type'),
                'priority': task.get('priority', 'normal'),
                'status': task.get('status', 'pending'),
                'created_at': task.get('created_at')
            })
        
        return jsonify({
            'success': True,
            'data': tasks,
            'count': len(tasks),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/performance', methods=['GET'])
@require_admin
def get_cluster_performance():
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    try:
        performance = {}
        for cluster_id, cluster in manager.clusters.items():
            total_tasks = 0
            total_success = 0
            
            for emp_id, emp in cluster.employees.items():
                total_tasks += emp.performance_metrics.get('tasks_completed', 0)
                total_success += emp.performance_metrics.get('success_tasks', 0)
            
            performance[cluster_id] = {
                'cluster_type': cluster.cluster_type,
                'status': cluster.status,
                'employee_count': len(cluster.employees),
                'total_tasks_completed': total_tasks,
                'total_success_tasks': total_success,
                'overall_success_rate': round(total_success / max(total_tasks, 1) * 100, 2),
                'task_queue_length': len(cluster.task_queue)
            }
        
        return jsonify({
            'success': True,
            'data': performance,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_cluster_api.route('/api/ai/cluster/health', methods=['GET'])
@require_admin
def cluster_health_check():
    manager = _get_ai_cluster_manager()
    if not manager:
        return jsonify({'success': False, 'error': 'AI集群管理器不可用'}), 503
    
    try:
        health = []
        for cluster_id, cluster in manager.clusters.items():
            healthy_employees = 0
            for emp_id, emp in cluster.employees.items():
                if emp.status == 'active':
                    healthy_employees += 1
            
            health.append({
                'cluster_id': cluster_id,
                'cluster_type': cluster.cluster_type,
                'status': cluster.status,
                'total_employees': len(cluster.employees),
                'healthy_employees': healthy_employees,
                'health_percentage': round(healthy_employees / max(len(cluster.employees), 1) * 100, 2),
                'task_queue_length': len(cluster.task_queue)
            })
        
        overall_health = 'healthy' if all(h['health_percentage'] >= 80 for h in health) else 'warning'
        
        return jsonify({
            'success': True,
            'overall_health': overall_health,
            'data': health,
            'cluster_count': len(health),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500