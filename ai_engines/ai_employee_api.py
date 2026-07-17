#!/usr/bin/env python3
"""
AI员工管理API蓝图
"""

from flask import Blueprint, jsonify, request
import logging

ai_employee_api = Blueprint('ai_employee_api', __name__)

logger = logging.getLogger('ai_employee_api')

try:
    from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
    ai_employee_manager = get_ai_employee_manager()
    logger.info("成功获取AI员工管理器实例")
except Exception as e:
    logger.error(f"获取AI员工管理器实例失败: {str(e)}")
    ai_employee_manager = None

@ai_employee_api.route('/api/ai-employees', methods=['GET'])
def get_ai_employees():
    """获取所有AI员工列表

    Returns:
        JSON响应,包含所有AI员工的详细信息
    """
    if not ai_employee_manager:
        return jsonify({"success": False, "message": "AI员工管理器未初始化"}), 500

    try:
        employees = ai_employee_manager.get_all_employees()
        return jsonify({
            "success": True,
            "data": employees
        })
    except Exception as e:
        logger.error(f"获取AI员工列表失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_employee_api.route('/api/ai-employees/<employee_id>', methods=['GET'])
def get_ai_employee(employee_id):
    """获取单个AI员工信息

    Args:
        employee_id: AI员工ID

    Returns:
        JSON响应,包含指定AI员工的详细信息
    """
    if not ai_employee_manager:
        return jsonify({"success": False, "message": "AI员工管理器未初始化"}), 500

    try:
        employee = ai_employee_manager.get_employee(employee_id)
        if employee:
            return jsonify({
                "success": True,
                "data": employee
            })
        else:
            return jsonify({"success": False, "message": "AI员工不存在"}), 404
    except Exception as e:
        logger.error(f"获取AI员工信息失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_employee_api.route('/api/ai-employees/<employee_id>/execute', methods=['POST'])
def execute_task(employee_id):
    """通过AI员工执行任务

    Args:
        employee_id: AI员工ID

    Returns:
        JSON响应,包含任务执行结果
    """
    if not ai_employee_manager:
        return jsonify({"success": False, "message": "AI员工管理器未初始化"}), 500

    try:
        task_data = request.get_json()
        result = ai_employee_manager.execute_task(employee_id, task_data)
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"执行任务失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_employee_api.route('/api/ai-employees/execute-by-role', methods=['POST'])
def execute_task_by_role():
    """通过角色执行任务

    Returns:
        JSON响应,包含任务执行结果
    """
    if not ai_employee_manager:
        return jsonify({"success": False, "message": "AI员工管理器未初始化"}), 500

    try:
        task_data = request.get_json()
        result = ai_employee_manager.execute_task_by_role(task_data)
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"通过角色执行任务失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_employee_api.route('/api/ai-employees/<employee_id>/upgrade', methods=['POST'])
def upgrade_ai_employee(employee_id):
    """升级单个AI员工

    Args:
        employee_id: AI员工ID

    Returns:
        JSON响应,包含升级结果
    """
    if not ai_employee_manager:
        return jsonify({"success": False, "message": "AI员工管理器未初始化"}), 500

    try:
        result = ai_employee_manager.upgrade_employee(employee_id)
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"升级AI员工失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_employee_api.route('/api/ai-employees/status', methods=['GET'])
def get_system_status():
    """获取AI员工系统状态

    Returns:
        JSON响应,包含系统状态信息
    """
    if not ai_employee_manager:
        return jsonify({"success": False, "message": "AI员工管理器未初始化"}), 500

    try:
        status = ai_employee_manager.get_system_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ai_employee_api.route('/api/ai-employees/instantiate', methods=['POST'])
def instantiate_ai_employee():
    """实例化新的AI员工

    Returns:
        JSON响应,包含新实例化的AI员工信息
    """
    if not ai_employee_manager:
        return jsonify({"success": False, "message": "AI员工管理器未初始化"}), 500

    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"success": False, "message": "请求数据为空"}), 400

        result = ai_employee_manager.instantiate_employee(request_data)
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"实例化AI员工失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
