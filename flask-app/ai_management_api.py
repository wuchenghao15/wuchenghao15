#!/usr/bin/env python3
"""
AI Management API Blueprint

from flask import Blueprint, jsonify, request
from ai_master_slave_manager import ai_server_cluster_manager
from ai_collection_manager import ai_collection_manager
from ai_supervision_upgrade import ai_supervision_manager

# 创建蓝图
ai_management_api = Blueprint('ai_management_api', __name__)

# ------------------------------
# AI Server Management Endpoints
# ------------------------------
@ai_management_api.route('/api/ai/servers', methods=['GET'])
def get_all_servers():
    """获取所有AI服务器"""
    masters = ai_server_cluster_manager.get_all_master_servers()
    slaves = ai_server_cluster_manager.get_all_slave_servers()

    result = {
        'masters': [],
        'slaves': []
    }

    for master_id, master in masters.items():
        result['masters'].append({
            'node_id': master.node_id,
            'name': master.name,
            'ip': master.ip,
            'port': master.port,
            'status': master.status,
            'slave_count': len(master.slave_servers)
        })

    for slave_id, slave in slaves.items():
        result['slaves'].append({
            'node_id': slave.node_id,
            'name': slave.name,
            'ip': slave.ip,
            'port': slave.port,
            'status': slave.status,
            'master_id': slave.master_id,
            'ai_employee_count': len(slave.ai_employees)
        })


@ai_management_api.route('/api/ai/servers/master', methods=['POST'])
def create_master_server():
    """创建主服务器"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    name = data.get('name')
    ip = data.get('ip')
    port = data.get('port')

    if not all([name, ip, port]):
        return jsonify({'error': 'Missing required fields'}), 400

    master_id = ai_server_cluster_manager.create_master_server(name, ip, port)
    return jsonify({'master_id': master_id}), 201

@ai_management_api.route('/api/ai/servers/slave', methods=['POST'])
def create_slave_server():
    """创建从服务器"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400
    name = data.get('name')
    port = data.get('port')

    if not all([name, ip, port, master_id]):

    if not slave_id:

    return jsonify({'slave_id': slave_id}), 201

@ai_management_api.route('/api/ai/servers/<node_id>', methods=['GET'])
    """获取服务器详情"""
    server = ai_server_cluster_manager.get_master_server(node_id)
    if not server:
        server = ai_server_cluster_manager.get_slave_server(node_id)

    if not server:
        return jsonify({'error': 'Server not found'}), 404

    return jsonify(server.get_health_status())

@ai_management_api.route('/api/ai/servers/<node_id>', methods=['DELETE'])
def delete_server(node_id):
    """删除服务器"""
    ai_server_cluster_manager.remove_server(node_id)
    return jsonify({'message': 'Server removed'}), 200
@ai_management_api.route('/api/ai/servers/<node_id>/status', methods=['PUT'])
def update_server_status(node_id):
    """更新服务器状态"""
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    status = data['status']
    server = ai_server_cluster_manager.get_master_server(node_id)
    if not server:
        server = ai_server_cluster_manager.get_slave_server(node_id)
    if not server:
        return jsonify({'error': 'Server not found'}), 404

    server.update_status(status)
    return jsonify({'message': 'Status updated'}), 200

@ai_management_api.route('/api/ai/servers/cluster/health', methods=['GET'])
def get_cluster_health():
    report = ai_server_cluster_manager.get_cluster_health_report()

@ai_management_api.route('/api/ai/servers/task', methods=['POST'])
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400
    if not task:
        return jsonify({'error': 'Missing task data'}), 400
    node_id = ai_server_cluster_manager.distribute_task_to_cluster(task)
    if node_id:
    else:
        return jsonify({'error': 'Failed to distribute task'}), 500

# ------------------------------
# ------------------------------
@ai_management_api.route('/api/ai/collections', methods=['GET'])
def get_all_collections():
    """获取所有AI集合"""
    collections = ai_collection_manager.get_all_collections()
    result = []

    for collection_id, collection in collections.items():
        result.append(collection.get_collection_status())

    return jsonify(result)

@ai_management_api.route('/api/ai/collections', methods=['POST'])
def create_collection():
    """创建AI集合"""
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    name = data.get('name')
    description = data.get('description', '')
    if not name:
        return jsonify({'error': 'Missing name'}), 400

    collection_id = ai_collection_manager.create_collection(name, description)

@ai_management_api.route('/api/ai/collections/<collection_id>', methods=['GET'])
def get_collection(collection_id):
    collection = ai_collection_manager.get_collection(collection_id)
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404

    return jsonify(collection.get_collection_status())
@ai_management_api.route('/api/ai/collections/<collection_id>/employees', methods=['GET'])
def get_collection_employees(collection_id):
    """获取集合中的AI员工"""
    collection = ai_collection_manager.get_collection(collection_id)
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404

    employees = collection.get_all_ai_employees()
    return jsonify(employees)

@ai_management_api.route('/api/ai/collections/<collection_id>/employees', methods=['POST'])
def add_employee_to_collection(collection_id):
    """将AI员工添加到集合"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    employee_id = data.get('employee_id')
    employee_info = data.get('employee_info', {})
    if not employee_id:
        return jsonify({'error': 'Missing employee_id'}), 400

    ai_collection_manager.add_employee_to_collection(collection_id, employee_id, employee_info)
    return jsonify({'message': 'Employee added to collection'}), 200
@ai_management_api.route('/api/ai/collections/<collection_id>/employees/<employee_id>', methods=['DELETE'])
def remove_employee_from_collection(collection_id, employee_id):
    """从集合中移除AI员工"""
    ai_collection_manager.remove_employee_from_collection(collection_id, employee_id)

@ai_management_api.route('/api/ai/collections/<collection_id>/tasks', methods=['POST'])
def add_task_to_collection(collection_id):
    data = request.get_json()
        return jsonify({'error': 'Invalid input'}), 400
    ai_collection_manager.add_task_to_collection(collection_id, data['task'])
    return jsonify({'message': 'Task added to collection'}), 200
@ai_management_api.route('/api/ai/collections/tasks/distribute', methods=['POST'])
def distribute_collection_tasks():
    """分发所有集合的任务"""
    distributed_tasks = ai_collection_manager.distribute_tasks()
    return jsonify({'distributed_tasks': distributed_tasks}), 200

# ------------------------------
# ------------------------------
@ai_management_api.route('/api/ai/supervision/metrics', methods=['GET'])
def get_supervision_metrics():
    """获取系统监控指标"""
        'system': ai_supervision_manager.get_system_metrics(),
        'ai_servers': ai_supervision_manager.get_ai_server_metrics(),
        'ai_employees': ai_supervision_manager.get_ai_employee_metrics()
    }
    return jsonify(metrics)

@ai_management_api.route('/api/ai/supervision/alerts', methods=['GET'])
def get_alerts():
    """获取所有活跃警报"""

@ai_management_api.route('/api/ai/supervision/alerts/history', methods=['GET'])
def get_alert_history():
    """获取警报历史"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(ai_supervision_manager.get_alert_history(limit))

@ai_management_api.route('/api/ai/supervision/alerts/<alert_id>', methods=['PUT'])
def resolve_alert(alert_id):
    """解决警报"""
    success = ai_supervision_manager.resolve_alert(alert_id)
    if success:
        return jsonify({'message': 'Alert resolved'}), 200
    else:
        return jsonify({'error': 'Alert not found'}), 404

@ai_management_api.route('/api/ai/supervision/report', methods=['GET'])
def get_supervision_report():
    """获取综合监控报告"""
    return jsonify(ai_supervision_manager.get_comprehensive_report())

@ai_management_api.route('/api/ai/upgrade/check', methods=['GET'])
def check_for_upgrades():
    """检查是否有可用升级"""
    upgrades = ai_supervision_manager.check_for_upgrades()
    return jsonify(upgrades)

@ai_management_api.route('/api/ai/upgrade/<upgrade_id>', methods=['POST'])
def perform_upgrade(upgrade_id):
    """执行升级"""
    result = ai_supervision_manager.perform_upgrade(upgrade_id)
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@ai_management_api.route('/api/ai/upgrade/history', methods=['GET'])
def get_upgrade_history():
    """获取升级历史"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(ai_supervision_manager.get_upgrade_history(limit))

@ai_management_api.route('/api/ai/maintenance/tasks', methods=['GET'])
def get_maintenance_tasks():
    """获取维护任务"""
    return jsonify(ai_supervision_manager.maintenance_tasks)

@ai_management_api.route('/api/ai/maintenance/tasks', methods=['POST'])
def schedule_maintenance_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    ai_supervision_manager.schedule_maintenance_task(data)
    return jsonify({'message': 'Maintenance task scheduled'}), 201

@ai_management_api.route('/api/ai/maintenance/tasks/<task_id>', methods=['POST'])
def execute_maintenance_task(task_id):
    success = ai_supervision_manager.execute_maintenance_task(task_id)
    if success:
        return jsonify({'message': 'Maintenance task executed'}), 200
    else:
        return jsonify({'error': 'Maintenance task not found or already executed'}), 404

# ------------------------------
@ai_management_api.route('/api/ai/employees/collections/<employee_id>', methods=['GET'])
def get_employee_collections(employee_id):
    """获取AI员工所属的所有集合"""
    return jsonify({'collections': collections})
@ai_management_api.route('/api/ai/management/status', methods=['GET'])
def get_management_status():
    """获取AI管理系统的整体状态"""
    # 获取集群健康
    cluster_health = ai_server_cluster_manager.get_cluster_health_report()

    # 获取集合状态
    collection_status = ai_collection_manager.get_collection_status_report()

    # 获取监控指标
    metrics = ai_supervision_manager.get_comprehensive_report()

    # 获取活跃警报
    active_alerts = ai_supervision_manager.get_active_alerts()

    return jsonify({
        'cluster_health': cluster_health,
        'collection_status': collection_status,
        'metrics': metrics,
        'active_alerts': active_alerts
    })

@ai_management_api.route('/api/ai/management/initialize', methods=['POST'])
def initialize_ai_management():
    """初始化AI管理系统"""
    # 这里可以添加初始化逻辑，例如创建默认的主服务器和集合

    # 创建默认主服务器
        ip='127.0.0.1',
        port=5001
    )
    # 创建默认从服务器
    slave_id = ai_server_cluster_manager.create_slave_server(
        name='Default Slave Server',
        ip='127.0.0.1',
        port=5002,
        master_id=master_id
    )

    # 创建默认AI集合
    collection_id = ai_collection_manager.create_collection(
        name='Default AI Collection',
        description='Default collection for AI employees'
    )

    return jsonify({
        'message': 'AI management system initialized',
        'default_master_id': master_id,
        'default_slave_id': slave_id,
        'default_collection_id': collection_id
    }), 201
