# -*- coding: utf-8 -*-
"""
AI员工自动衍生API
提供AI员工自动衍生、管理和查询的RESTful接口
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

employee_generator_api = Blueprint('employee_generator_api', __name__)


def get_employee_generator():
    """获取员工生成器实例"""
    from ai_engines.ai_employee_auto_generator import get_employee_generator
    return get_employee_generator()


@employee_generator_api.route('/api/employee/generator/info', methods=['GET'])
def get_generator_info():
    """获取员工生成器信息"""
    try:
        generator = get_employee_generator()
        status = generator.get_system_status()
        
        return jsonify({
            "success": True,
            "data": {
                "name": "AI员工自动衍生系统",
                "version": "1.0.0",
                "description": "自动分析系统功能，智能创建适配的AI员工，实现自我扩展和进化",
                "is_running": status["is_running"],
                "total_employees": status["total_employees"],
                "employee_types": status["employee_types"]
            }
        })
    except Exception as e:
        logger.error(f"获取生成器信息失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/start', methods=['POST'])
def start_generator():
    """启动员工生成器"""
    try:
        generator = get_employee_generator()
        generator.start()
        
        return jsonify({
            "success": True,
            "message": "AI员工自动衍生系统已启动"
        })
    except Exception as e:
        logger.error(f"启动生成器失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/stop', methods=['POST'])
def stop_generator():
    """停止员工生成器"""
    try:
        generator = get_employee_generator()
        generator.stop()
        
        return jsonify({
            "success": True,
            "message": "AI员工自动衍生系统已停止"
        })
    except Exception as e:
        logger.error(f"停止生成器失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/status', methods=['GET'])
def get_generator_status():
    """获取生成器状态"""
    try:
        generator = get_employee_generator()
        status = generator.get_system_status()
        stats = generator.get_employee_stats()
        
        return jsonify({
            "success": True,
            "data": {
                "status": status,
                "stats": stats
            }
        })
    except Exception as e:
        logger.error(f"获取生成器状态失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/list', methods=['GET'])
def list_employees():
    """列出所有AI员工"""
    try:
        generator = get_employee_generator()
        employees = generator.list_employees()
        
        return jsonify({
            "success": True,
            "data": employees,
            "count": len(employees)
        })
    except Exception as e:
        logger.error(f"获取员工列表失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/employee/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """获取单个AI员工详情"""
    try:
        generator = get_employee_generator()
        employee = generator.get_employee(employee_id)
        
        if not employee:
            return jsonify({"success": False, "message": "员工不存在"}), 404
        
        return jsonify({
            "success": True,
            "data": employee.to_dict()
        })
    except Exception as e:
        logger.error(f"获取员工详情失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/auto_generate', methods=['POST'])
def auto_generate():
    """自动衍生AI员工"""
    try:
        generator = get_employee_generator()
        result = generator.auto_generate_employees()
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"自动衍生失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/adapt', methods=['POST'])
def adapt_to_feature():
    """适配到新功能"""
    try:
        data = request.get_json() or {}
        
        feature_name = data.get('feature_name')
        feature_description = data.get('description', '')
        required_skills = data.get('skills', [])
        
        if not feature_name:
            return jsonify({"success": False, "message": "功能名称不能为空"}), 400
        
        generator = get_employee_generator()
        result = generator.adapt_to_new_feature(feature_name, feature_description, required_skills)
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"适配功能失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/create', methods=['POST'])
def create_employee():
    """手动创建AI员工"""
    try:
        data = request.get_json() or {}
        
        role = data.get('role')
        name = data.get('name')
        skills = data.get('skills', [])
        capabilities = data.get('capabilities', [])
        
        if not role or not name:
            return jsonify({"success": False, "message": "角色和名称不能为空"}), 400
        
        from ai_engines.ai_employee_auto_generator import EmployeeRole
        
        try:
            employee_role = EmployeeRole(role)
        except ValueError:
            return jsonify({"success": False, "message": f"无效的角色: {role}"}), 400
        
        generator = get_employee_generator()
        employee = generator.create_employee(employee_role, name, skills, capabilities)
        
        return jsonify({
            "success": True,
            "data": employee.to_dict()
        })
    except Exception as e:
        logger.error(f"创建员工失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/by_role/<role>', methods=['GET'])
def get_employees_by_role(role):
    """按角色获取AI员工"""
    try:
        generator = get_employee_generator()
        employees = generator.get_employees_by_role(role)
        
        return jsonify({
            "success": True,
            "data": [emp.to_dict() for emp in employees],
            "count": len(employees)
        })
    except Exception as e:
        logger.error(f"按角色获取员工失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/analyze_features', methods=['GET'])
def analyze_features():
    """分析所有系统功能"""
    try:
        generator = get_employee_generator()
        features = generator.feature_analyzer.analyze_all_features()
        role_requirements = generator.feature_analyzer.get_role_requirements()
        
        return jsonify({
            "success": True,
            "data": {
                "features": features,
                "role_requirements": role_requirements
            }
        })
    except Exception as e:
        logger.error(f"分析功能失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@employee_generator_api.route('/api/employee/generator/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        generator = get_employee_generator()
        stats = generator.get_employee_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500