#!/usr/bin/env python3
"""
AI管理API蓝图
包含AI子母服务器、AI集和AI监管相关的API端点
"""

from flask import Blueprint, jsonify, request
import logging

ai_management_api = Blueprint('ai_management_api', __name__)

logger = logging.getLogger('ai_management_api')

@ai_management_api.route('/api/ai-servers', methods=['GET'])
def get_ai_servers():
    """获取所有AI服务器节点"""
    try:
        from app.ai.ai_master_slave_manager import get_cluster_manager
        cluster_manager = get_cluster_manager()
        status = cluster_manager.get_cluster_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-servers/register', methods=['POST'])
def register_slave_server():
    """注册子服务器"""
    try:
        from app.ai.ai_master_slave_manager import get_cluster_manager
        cluster_manager = get_cluster_manager()
        if not cluster_manager.master_server:
            cluster_manager.create_master_server()
        slave_info = request.get_json()
        result = cluster_manager.master_server.register_slave_server(slave_info)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-servers/heartbeat', methods=['POST'])
def receive_heartbeat():
    """接收子服务器心跳"""
    try:
        from app.ai.ai_master_slave_manager import get_cluster_manager
        cluster_manager = get_cluster_manager()
        heartbeat_data = request.get_json()
        return jsonify({"success": True, "message": "心跳已接收"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-servers/tasks', methods=['POST'])
def submit_task():
    """提交任务到AI服务器集群"""
    try:
        from app.ai.ai_master_slave_manager import get_cluster_manager
        cluster_manager = get_cluster_manager()
        if not cluster_manager.master_server:
            cluster_manager.create_master_server()
        task_data = request.get_json()
        result = cluster_manager.master_server.submit_task(task_data)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-collections', methods=['POST'])
def create_ai_collection():
    """创建新的AI集"""
    try:
        from app.ai.ai_collection_manager import get_collection_manager
        collection_manager = get_collection_manager()
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        if not name:
            return jsonify({"success": False, "message": "AI集名称不能为空"}), 400
        result = collection_manager.create_collection(name, description)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-collections/<collection_id>/employees', methods=['POST'])
def add_employee_to_collection(collection_id):
    """向AI集添加AI员工"""
    try:
        from app.ai.ai_collection_manager import get_collection_manager
        collection_manager = get_collection_manager()
        data = request.get_json()
        employee_id = data.get('employee_id')
        if not employee_id:
            return jsonify({"success": False, "message": "AI员工ID不能为空"}), 400
        result = collection_manager.add_employee_to_collection(collection_id, employee_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-supervision/health', methods=['GET'])
def get_system_health():
    """获取系统健康状态"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        health = supervision_manager.get_system_health()
        return jsonify({"success": True, "data": health})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-supervision/employees/status', methods=['GET'])
def get_ai_employees_status():
    """获取所有AI员工状态"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        employees = supervision_manager.get_ai_employees_status()
        return jsonify({"success": True, "data": employees})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-supervision/upgrade', methods=['POST'])
def manual_upgrade_all():
    """手动升级所有AI组件"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        result = supervision_manager.manually_upgrade_all()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-supervision/maintenance', methods=['POST'])
def manual_perform_maintenance():
    """手动执行系统维护"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        result = supervision_manager.manually_perform_maintenance()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-supervision/monitoring', methods=['POST'])
def toggle_monitoring():
    """切换监控状态"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        data = request.get_json()
        enabled = data.get('enabled', True)
        supervision_manager.toggle_monitoring(enabled)
        return jsonify({"success": True, "message": f"监控已{'启用' if enabled else '禁用'}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-supervision/auto-upgrade', methods=['POST'])
def toggle_auto_upgrade():
    """切换自动升级状态"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        data = request.get_json()
        enabled = data.get('enabled', True)
        supervision_manager.toggle_auto_upgrade(enabled)
        return jsonify({"success": True, "message": f"自动升级已{'启用' if enabled else '禁用'}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-supervision/auto-maintenance', methods=['POST'])
def toggle_auto_maintenance():
    """切换自动维护状态"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        data = request.get_json()
        enabled = data.get('enabled', True)
        supervision_manager.toggle_auto_maintenance(enabled)
        return jsonify({"success": True, "message": f"自动维护已{'启用' if enabled else '禁用'}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-employees', methods=['GET'])
def get_ai_employees():
    """获取所有AI员工列表"""
    try:
        from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
        ai_employee_manager = get_ai_employee_manager()
        employees = ai_employee_manager.list_employees()
        return jsonify({"success": True, "data": employees})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-employees/<employee_id>/upgrade', methods=['POST'])
def upgrade_ai_employee(employee_id):
    """升级指定AI员工"""
    try:
        from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
        ai_employee_manager = get_ai_employee_manager()
        result = ai_employee_manager.upgrade_employee(employee_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-employees/upgrade-all', methods=['POST'])
def upgrade_all_ai_employees():
    """升级所有AI员工"""
    try:
        from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
        ai_employee_manager = get_ai_employee_manager()
        result = ai_employee_manager.upgrade_all_employees()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
