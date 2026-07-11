# -*- coding: utf-8 -*-
"""AI计划员工API - 智能创建和管理自动计划"""

import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, request, jsonify
from ai_engines.ai_plan_employee import ai_plan_employee

plan_employee_api_bp = Blueprint("plan_employee_api", __name__)

@plan_employee_api.route('/api/plan/employee/info', methods=['GET'])
def get_plan_employee_info():
    """获取AI计划员工信息"""
    info = {
        'employee_id': ai_plan_employee.employee_id,
        'name': ai_plan_employee.name,
        'type': ai_plan_employee.type,
        'skills': ai_plan_employee.skills,
        'responsibilities': ai_plan_employee.responsibilities,
        'status': ai_plan_employee.status
    }
    return jsonify({'success': True, 'data': info})

@plan_employee_api.route('/api/plan/employee/plans', methods=['GET'])
def get_all_plans():
    """获取所有计划"""
    plans = ai_plan_employee.get_all_plans()
    return jsonify({'success': True, 'data': plans})

@plan_employee_api.route('/api/plan/employee/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """获取指定计划详情"""
    plan = ai_plan_employee.get_plan(plan_id)
    if not plan:
        return jsonify({'success': False, 'message': '计划不存在'}), 404
    return jsonify({'success': True, 'data': plan})

@plan_employee_api.route('/api/plan/employee/generate', methods=['POST'])
def generate_plan():
    """智能生成计划"""
    data = request.get_json() or {}
    plan_type = data.get('plan_type', 'daily')
    custom_tasks = data.get('tasks')
    name = data.get('name')
    description = data.get('description')
    priority = data.get('priority')

    plan = ai_plan_employee.generate_plan(
        plan_type=plan_type,
        custom_tasks=custom_tasks,
        name=name,
        description=description,
        priority=priority
    )

    if not plan:
        return jsonify({'success': False, 'message': f'未知计划类型: {plan_type}'}), 400

    return jsonify({'success': True, 'data': plan})

@plan_employee_api.route('/api/plan/employee/auto_generate', methods=['POST'])
def auto_generate_plans():
    """自动生成所有必要的计划"""
    plans = ai_plan_employee.auto_generate_plans()
    return jsonify({
        'success': True,
        'message': f'已生成 {len(plans)} 个计划',
        'data': plans
    })

@plan_employee_api.route('/api/plan/employee/custom', methods=['POST'])
def create_custom_plan():
    """创建自定义计划"""
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    tasks = data.get('tasks')

    if not name or not tasks:
        return jsonify({'success': False, 'message': '缺少必要参数: name 和 tasks'}), 400

    plan = ai_plan_employee.create_custom_plan(
        name=name,
        description=description or '',
        tasks=tasks
    )

    return jsonify({'success': True, 'data': plan})

@plan_employee_api.route('/api/plan/employee/plans/<plan_id>/execute', methods=['POST'])
def execute_plan(plan_id):
    """执行指定计划"""
    result = ai_plan_employee.execute_plan(plan_id)
    if not result['success']:
        return jsonify(result), 400
    return jsonify(result)

@plan_employee_api.route('/api/plan/employee/plans/<plan_id>', methods=['PUT'])
def update_plan(plan_id):
    """更新计划"""
    data = request.get_json() or {}
    success = ai_plan_employee.update_plan(plan_id, data)
    
    if not success:
        return jsonify({'success': False, 'message': '计划不存在'}), 404

    plan = ai_plan_employee.get_plan(plan_id)
    return jsonify({'success': True, 'data': plan})

@plan_employee_api.route('/api/plan/employee/plans/<plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    """删除计划"""
    success = ai_plan_employee.delete_plan(plan_id)
    
    if not success:
        return jsonify({'success': False, 'message': '计划不存在'}), 404

    return jsonify({'success': True, 'message': '计划已删除'})

@plan_employee_api.route('/api/plan/employee/analyze', methods=['GET'])
def analyze_and_plan():
    """智能分析系统状态并生成/调整计划"""
    analysis = ai_plan_employee.analyze_and_plan()
    return jsonify({'success': True, 'data': analysis})

@plan_employee_api.route('/api/plan/employee/history', methods=['GET'])
def get_execution_history():
    """获取执行历史"""
    limit = int(request.args.get('limit', 50))
    history = ai_plan_employee.get_execution_history(limit)
    return jsonify({'success': True, 'data': history})

@plan_employee_api.route('/api/plan/employee/templates', methods=['GET'])
def get_plan_templates():
    """获取可用计划模板"""
    templates = ai_plan_employee.plan_templates
    return jsonify({'success': True, 'data': templates})

@plan_employee_api.route('/api/plan/employee/context', methods=['POST'])
def set_system_context():
    """设置系统上下文"""
    data = request.get_json() or {}
    ai_plan_employee.set_system_context(data)
    return jsonify({'success': True, 'message': '系统上下文已更新'})