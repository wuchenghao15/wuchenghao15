#!/usr/bin/env python3
"""
AI管理API蓝图
包含AI子母服务器、AI集和AI监管相关的API端点
"""

from flask import Blueprint, jsonify, request
import logging

# 创建蓝图
ai_management_api = Blueprint('ai_management_api', __name__)

# 配置日志
logger = logging.getLogger('ai_management_api')

# ------------------------------
# AI子母服务器API
# ------------------------------

@ai_management_api.route('/api/ai-servers', methods=['GET'])
def get_ai_servers():
    """获取所有AI服务器节点"""
    try:
        from app.ai.ai_master_slave_manager import get_cluster_manager
        cluster_manager = get_cluster_manager()
        
        status = cluster_manager.get_cluster_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        logger.error(f"获取AI服务器列表失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/register_slave', methods=['POST'])
def register_slave_server():
    """注册子服务器"""
    try:
        from app.ai.ai_master_slave_manager import get_cluster_manager
        cluster_manager = get_cluster_manager()
        
        slave_info = request.get_json()
        if not cluster_manager.master_server:
            # 如果母服务器不存在，创建一个
            cluster_manager.create_master_server()
        
        result = cluster_manager.master_server.register_slave_server(slave_info)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"注册子服务器失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/heartbeat', methods=['POST'])
def receive_heartbeat():
    """接收子服务器心跳"""
    try:
        from app.ai.ai_master_slave_manager import get_cluster_manager
        cluster_manager = get_cluster_manager()
        
        heartbeat_data = request.get_json()
        # 简单处理心跳，更新子服务器状态
        return jsonify({"success": True, "message": "心跳已接收"})
    except Exception as e:
        logger.error(f"处理心跳失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/submit_task', methods=['POST'])
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
        logger.error(f"提交任务失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# ------------------------------
# AI集管理API
# ------------------------------

@ai_management_api.route('/api/ai-collections', methods=['GET'])
def get_ai_collections():
    """获取所有AI集"""
    try:
        from app.ai.ai_collection_manager import get_collection_manager
        collection_manager = get_collection_manager()
        
        collections = collection_manager.list_collections()
        return jsonify({"success": True, "data": collections})
    except Exception as e:
        logger.error(f"获取AI集列表失败: {str(e)}")
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
        
        collection = collection_manager.create_collection(name, description)
        return jsonify({"success": True, "data": collection.get_status()})
    except Exception as e:
        logger.error(f"创建AI集失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-collections/<collection_id>', methods=['GET'])
def get_ai_collection(collection_id):
    """获取指定AI集"""
    try:
        from app.ai.ai_collection_manager import get_collection_manager
        collection_manager = get_collection_manager()
        
        collection = collection_manager.get_collection(collection_id)
        if not collection:
            return jsonify({"success": False, "message": "AI集不存在"}), 404
        
        return jsonify({"success": True, "data": collection.get_status()})
    except Exception as e:
        logger.error(f"获取AI集失败: {str(e)}")
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
        
        success = collection_manager.add_employee_to_collection(collection_id, employee_id)
        if not success:
            return jsonify({"success": False, "message": "添加AI员工失败"}), 400
        
        return jsonify({"success": True, "message": "AI员工已添加到AI集"})
    except Exception as e:
        logger.error(f"向AI集添加AI员工失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-collections/<collection_id>/tasks', methods=['POST'])
def submit_task_to_collection(collection_id):
    """向AI集提交任务"""
    try:
        from app.ai.ai_collection_manager import get_collection_manager
        collection_manager = get_collection_manager()
        
        task_data = request.get_json()
        task = collection_manager.submit_task_to_collection(collection_id, task_data)
        
        if not task:
            return jsonify({"success": False, "message": "提交任务失败"}), 400
        
        return jsonify({"success": True, "data": task})
    except Exception as e:
        logger.error(f"向AI集提交任务失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# ------------------------------
# AI监管和升级API
# ------------------------------

@ai_management_api.route('/api/system-health', methods=['GET'])
def get_system_health():
    """获取系统健康状态"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        
        health = supervision_manager.get_system_health()
        return jsonify({"success": True, "data": health})
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/ai-employees/status', methods=['GET'])
def get_ai_employees_status():
    """获取所有AI员工状态"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        
        employees = supervision_manager.get_ai_employees_status()
        return jsonify({"success": True, "data": employees})
    except Exception as e:
        logger.error(f"获取AI员工状态失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/manual-upgrade', methods=['POST'])
def manual_upgrade_all():
    """手动升级所有AI组件"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        
        result = supervision_manager.manually_upgrade_all()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"手动升级失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/manual-maintenance', methods=['POST'])
def manual_perform_maintenance():
    """手动执行系统维护"""
    try:
        from app.ai.ai_supervision_upgrade import get_supervision_manager
        supervision_manager = get_supervision_manager()
        
        result = supervision_manager.manually_perform_maintenance()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"手动执行维护失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/monitoring/toggle', methods=['POST'])
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
        logger.error(f"切换监控状态失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/auto-upgrade/toggle', methods=['POST'])
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
        logger.error(f"切换自动升级状态失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_management_api.route('/api/auto-maintenance/toggle', methods=['POST'])
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
        logger.error(f"切换自动维护状态失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# ------------------------------
# AI员工管理API (扩展现有功能)
# ------------------------------

@ai_management_api.route('/api/ai-employees', methods=['GET'])
def get_ai_employees():
    """获取所有AI员工列表"""
    try:
        from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
        ai_employee_manager = get_ai_employee_manager()
        
        employees = ai_employee_manager.list_employees()
        return jsonify({"success": True, "data": employees})
    except Exception as e:
        logger.error(f"获取AI员工列表失败: {str(e)}")
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
        logger.error(f"升级AI员工失败: {str(e)}")
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
        logger.error(f"升级所有AI员工失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
