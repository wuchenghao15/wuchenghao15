# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
集群阵列AI Agent API接口
提供集群管理、AI员工管理、任务分配、监控和升级等功能
"""

import json
import time
from flask import Blueprint, jsonify, request, session

from .ai_cluster_manager import ai_cluster_manager
from .cluster_manager import cluster_manager
from .config_manager_employee import config_manager_employee

cluster_array_api = Blueprint('cluster_array_api', __name__)

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

@cluster_array_api.route('/api/cluster-array/status', methods=['GET'])
@require_login
def get_cluster_array_status():
    """获取集群阵列整体状态"""
    ai_status = ai_cluster_manager.get_cluster_status()
    server_status = cluster_manager.get_cluster_status()
    
    return jsonify({
        'success': True,
        'ai_clusters': ai_status,
        'server_cluster': server_status
    })

@cluster_array_api.route('/api/cluster-array/clusters', methods=['GET'])
@require_login
def get_clusters():
    """获取所有AI集群列表"""
    result = ai_cluster_manager.get_cluster_status()
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/clusters/<cluster_id>', methods=['GET'])
@require_login
def get_cluster(cluster_id):
    """获取指定集群详情"""
    result = ai_cluster_manager.get_cluster_status(cluster_id)
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/clusters', methods=['POST'])
@require_login
def create_cluster():
    """创建新的AI集群"""
    data = request.get_json()
    cluster_id = data.get('cluster_id')
    cluster_type = data.get('cluster_type')
    config = data.get('config', {})
    
    if not cluster_id or not cluster_type:
        return jsonify({
            'success': False,
            'error': 'cluster_id和cluster_type为必填项'
        }), 400
    
    success = ai_cluster_manager.create_cluster(cluster_id, cluster_type, config)
    return jsonify({
        'success': success,
        'message': f'集群 {cluster_id} 创建{"成功" if success else "失败"}'
    })

@cluster_array_api.route('/api/cluster-array/clusters/<cluster_id>', methods=['DELETE'])
@require_login
def delete_cluster(cluster_id):
    """删除指定集群"""
    success = ai_cluster_manager.delete_cluster(cluster_id)
    return jsonify({
        'success': success,
        'message': f'集群 {cluster_id} 删除{"成功" if success else "失败"}'
    })

@cluster_array_api.route('/api/cluster-array/clusters/<cluster_id>/status', methods=['PUT'])
@require_login
def update_cluster_status(cluster_id):
    """更新集群状态"""
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({
            'success': False,
            'error': 'status为必填项'
        }), 400
    
    result = ai_cluster_manager.get_cluster_status(cluster_id)
    if not result['success']:
        return jsonify(result)
    
    cluster = ai_cluster_manager.clusters.get(cluster_id)
    if cluster:
        success = cluster.update_status(status)
        return jsonify({
            'success': success,
            'message': f'集群 {cluster_id} 状态已更新为 {status}'
        })
    else:
        return jsonify({
            'success': False,
            'error': f'集群 {cluster_id} 不存在'
        })

@cluster_array_api.route('/api/cluster-array/employees', methods=['GET'])
@require_login
def get_employees():
    """获取所有AI员工列表"""
    result = ai_cluster_manager.get_employee_status()
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/employees/<employee_id>', methods=['GET'])
@require_login
def get_employee(employee_id):
    """获取指定员工详情"""
    result = ai_cluster_manager.get_employee_status(employee_id)
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/employees', methods=['POST'])
@require_login
def create_employee():
    """创建新的AI员工"""
    data = request.get_json()
    employee_id = data.get('employee_id')
    employee_type = data.get('employee_type')
    capabilities = data.get('capabilities', [])
    config = data.get('config', {})
    
    if not employee_id or not employee_type:
        return jsonify({
            'success': False,
            'error': 'employee_id和employee_type为必填项'
        }), 400
    
    success = ai_cluster_manager.create_employee(employee_id, employee_type, capabilities, config)
    return jsonify({
        'success': success,
        'message': f'AI员工 {employee_id} 创建{"成功" if success else "失败"}'
    })

@cluster_array_api.route('/api/cluster-array/employees/<employee_id>', methods=['DELETE'])
@require_login
def delete_employee(employee_id):
    """删除指定AI员工"""
    success = ai_cluster_manager.delete_employee(employee_id)
    return jsonify({
        'success': success,
        'message': f'AI员工 {employee_id} 删除{"成功" if success else "失败"}'
    })

@cluster_array_api.route('/api/cluster-array/employees/<employee_id>/assign', methods=['PUT'])
@require_login
def assign_employee_to_cluster(employee_id):
    """将员工分配到指定集群"""
    data = request.get_json()
    cluster_id = data.get('cluster_id')
    
    if not cluster_id:
        return jsonify({
            'success': False,
            'error': 'cluster_id为必填项'
        }), 400
    
    success = ai_cluster_manager.assign_employee_to_cluster(employee_id, cluster_id)
    return jsonify({
        'success': success,
        'message': f'员工 {employee_id} 分配到集群 {cluster_id} {"成功" if success else "失败"}'
    })

@cluster_array_api.route('/api/cluster-array/employees/<employee_id>/upgrade', methods=['PUT'])
@require_login
def upgrade_employee(employee_id):
    """升级指定员工"""
    data = request.get_json()
    upgrade_data = data.get('upgrade_data', {})
    
    result = ai_cluster_manager.get_employee_status(employee_id)
    if not result['success']:
        return jsonify(result)
    
    employee = ai_cluster_manager.employees.get(employee_id)
    if employee:
        success = employee.upgrade(upgrade_data)
        return jsonify({
            'success': success,
            'message': f'员工 {employee_id} 升级{"成功" if success else "失败"}'
        })
    else:
        return jsonify({
            'success': False,
            'error': f'员工 {employee_id} 不存在'
        })

@cluster_array_api.route('/api/cluster-array/clusters/<cluster_id>/tasks', methods=['POST'])
@require_login
def assign_task_to_cluster(cluster_id):
    """向集群分配任务"""
    data = request.get_json()
    task = data.get('task')
    
    if not task or 'task_id' not in task:
        return jsonify({
            'success': False,
            'error': 'task为必填项且必须包含task_id字段'
        }), 400
    
    result = ai_cluster_manager.assign_task(cluster_id, task)
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/upgrade-all', methods=['PUT'])
@require_login
def upgrade_all():
    """升级所有集群和员工"""
    data = request.get_json()
    upgrade_data = data.get('upgrade_data', {})
    
    result = ai_cluster_manager.upgrade_all(upgrade_data)
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/monitoring', methods=['PUT'])
@require_login
def set_monitoring():
    """启用或禁用监控"""
    data = request.get_json()
    enabled = data.get('enabled', True)
    
    success = ai_cluster_manager.set_monitoring_enabled(enabled)
    return jsonify({
        'success': success,
        'message': f'监控已{"启用" if enabled else "禁用"}'
    })

@cluster_array_api.route('/api/cluster-array/auto-upgrade', methods=['PUT'])
@require_login
def set_auto_upgrade():
    """启用或禁用自动升级"""
    data = request.get_json()
    enabled = data.get('enabled', True)
    
    success = ai_cluster_manager.set_auto_upgrade_enabled(enabled)
    return jsonify({
        'success': success,
        'message': f'自动升级已{"启用" if enabled else "禁用"}'
    })

@cluster_array_api.route('/api/cluster-array/server/status', methods=['GET'])
@require_login
def get_server_cluster_status():
    """获取服务器集群状态"""
    status = cluster_manager.get_cluster_status()
    return jsonify({
        'success': True,
        'status': status
    })

@cluster_array_api.route('/api/cluster-array/server/healthy-nodes', methods=['GET'])
@require_login
def get_healthy_nodes():
    """获取健康节点列表"""
    nodes = cluster_manager.get_healthy_nodes()
    return jsonify({
        'success': True,
        'healthy_nodes': nodes
    })

@cluster_array_api.route('/api/cluster-array/server/unhealthy-nodes', methods=['GET'])
@require_login
def get_unhealthy_nodes():
    """获取不健康节点列表"""
    nodes = cluster_manager.get_unhealthy_nodes()
    return jsonify({
        'success': True,
        'unhealthy_nodes': nodes
    })

@cluster_array_api.route('/api/cluster-array/server/join', methods=['POST'])
@require_login
def join_server_cluster():
    """加入服务器集群"""
    data = request.get_json()
    node_address = data.get('node_address')
    
    if not node_address:
        return jsonify({
            'success': False,
            'error': 'node_address为必填项'
        }), 400
    
    cluster_manager.join_cluster(node_address)
    return jsonify({
        'success': True,
        'message': f'节点 {node_address} 已加入集群'
    })

@cluster_array_api.route('/api/cluster-array/server/leave', methods=['POST'])
@require_login
def leave_server_cluster():
    """离开服务器集群"""
    data = request.get_json()
    node_address = data.get('node_address')
    
    if not node_address:
        return jsonify({
            'success': False,
            'error': 'node_address为必填项'
        }), 400
    
    cluster_manager.leave_cluster(node_address)
    return jsonify({
        'success': True,
        'message': f'节点 {node_address} 已离开集群'
    })

@cluster_array_api.route('/api/cluster-array/auto-extend', methods=['POST'])
@require_login
def trigger_auto_extend():
    """手动触发自动扩展"""
    try:
        ai_cluster_manager._auto_extend_system()
        return jsonify({
            'success': True,
            'message': '自动扩展已触发'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cluster_array_api.route('/api/cluster-array/shutdown', methods=['POST'])
@require_login
def shutdown_cluster_manager():
    """关闭集群管理器"""
    success = ai_cluster_manager.shutdown()
    return jsonify({
        'success': success,
        'message': '集群管理器已关闭'
    })

@cluster_array_api.route('/api/cluster-array/config/clusters', methods=['GET'])
@require_login
def get_cluster_configs():
    """获取所有集群配置"""
    cluster_id = request.args.get('cluster_id')
    task_data = {}
    if cluster_id:
        task_data['cluster_id'] = cluster_id
    result = config_manager_employee.execute_task({'task_type': 'get_cluster_config', **task_data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/clusters', methods=['POST'])
@require_login
def update_cluster_config():
    """创建或更新集群配置"""
    data = request.get_json()
    result = config_manager_employee.execute_task({'task_type': 'update_cluster_config', **data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/clusters/<cluster_id>', methods=['DELETE'])
@require_login
def delete_cluster_config(cluster_id):
    """删除集群配置"""
    result = config_manager_employee.execute_task({'task_type': 'delete_cluster_config', 'cluster_id': cluster_id})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/employees', methods=['GET'])
@require_login
def get_employee_configs():
    """获取所有员工配置"""
    employee_id = request.args.get('employee_id')
    task_data = {}
    if employee_id:
        task_data['employee_id'] = employee_id
    result = config_manager_employee.execute_task({'task_type': 'get_employee_config', **task_data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/employees', methods=['POST'])
@require_login
def update_employee_config():
    """创建或更新员工配置"""
    data = request.get_json()
    result = config_manager_employee.execute_task({'task_type': 'update_employee_config', **data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/employees/<employee_id>', methods=['DELETE'])
@require_login
def delete_employee_config(employee_id):
    """删除员工配置"""
    result = config_manager_employee.execute_task({'task_type': 'delete_employee_config', 'employee_id': employee_id})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/history', methods=['GET'])
@require_login
def get_config_history():
    """获取配置变更历史"""
    config_type = request.args.get('config_type')
    config_id = request.args.get('config_id')
    limit = request.args.get('limit', 50)
    task_data = {}
    if config_type:
        task_data['config_type'] = config_type
    if config_id:
        task_data['config_id'] = config_id
    if limit:
        task_data['limit'] = int(limit)
    result = config_manager_employee.execute_task({'task_type': 'get_config_history', **task_data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/snapshot', methods=['POST'])
@require_login
def create_snapshot():
    """创建配置快照"""
    data = request.get_json()
    result = config_manager_employee.execute_task({'task_type': 'create_snapshot', **data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/snapshot/restore', methods=['POST'])
@require_login
def restore_snapshot():
    """恢复配置快照"""
    data = request.get_json()
    result = config_manager_employee.execute_task({'task_type': 'restore_snapshot', **data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/export', methods=['GET'])
@require_login
def export_config():
    """导出配置"""
    export_type = request.args.get('export_type', 'all')
    result = config_manager_employee.execute_task({'task_type': 'export_config', 'export_type': export_type})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/import', methods=['POST'])
@require_login
def import_config():
    """导入配置"""
    data = request.get_json()
    result = config_manager_employee.execute_task({'task_type': 'import_config', **data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/validate', methods=['POST'])
@require_login
def validate_config():
    """验证配置"""
    data = request.get_json()
    result = config_manager_employee.execute_task({'task_type': 'validate_config', **data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/sync', methods=['POST'])
@require_login
def sync_config():
    """同步配置"""
    data = request.get_json()
    result = config_manager_employee.execute_task({'task_type': 'sync_config', **data})
    return jsonify(result)

@cluster_array_api.route('/api/cluster-array/config/status', methods=['GET'])
@require_login
def get_config_manager_status():
    """获取配置管理AI员工状态"""
    status = config_manager_employee.get_status()
    return jsonify({'success': True, 'status': status})