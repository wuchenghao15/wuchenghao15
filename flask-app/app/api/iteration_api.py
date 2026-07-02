# -*- coding: utf-8 -*-
"""
自动迭代更新API接口
提供迭代计划管理、AI员工分配、迭代规则配置等功能
"""

from flask import Blueprint, jsonify, request
from app.agents.iteration_engine import get_iteration_engine
from app.agents.iteration_rules import IterationConfig
from app.utils.logging import logger

iteration_api = Blueprint('iteration_api', __name__, url_prefix='/api')


@iteration_api.route('/iteration/plans', methods=['GET'])
def get_iteration_plans():
    """获取迭代计划列表"""
    try:
        engine = get_iteration_engine()
        plans = engine.get_iteration_plans()
        
        return jsonify({
            'success': True,
            'data': plans,
            'count': len(plans)
        })
    except Exception as e:
        logger.error(f"获取迭代计划失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取迭代计划失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/plans/<plan_id>', methods=['GET'])
def get_iteration_plan(plan_id):
    """获取单个迭代计划详情"""
    try:
        engine = get_iteration_engine()
        plans = engine.get_iteration_plans()
        plan = next((p for p in plans if p['plan_id'] == plan_id), None)
        
        if not plan:
            return jsonify({
                'success': False,
                'error': '迭代计划不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': plan
        })
    except Exception as e:
        logger.error(f"获取迭代计划详情失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取迭代计划详情失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/trigger', methods=['POST'])
def trigger_iteration():
    """触发迭代更新"""
    try:
        data = request.json or {}
        iteration_type = data.get('type', 'on_demand')
        
        engine = get_iteration_engine()
        result = engine.trigger_on_demand_iteration()
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"触发迭代失败: {e}")
        return jsonify({
            'success': False,
            'error': f'触发迭代失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/rules', methods=['GET'])
def get_iteration_rules():
    """获取迭代规则配置"""
    try:
        config = IterationConfig()
        
        return jsonify({
            'success': True,
            'data': {
                'cycles': config.ITERATION_CYCLES,
                'approval_rules': config.APPROVAL_RULES,
                'rollback_rules': config.ROLLBACK_STRATEGIES,
                'testing_standards': config.TEST_CRITERIA
            }
        })
    except Exception as e:
        logger.error(f"获取迭代规则失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取迭代规则失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/rules/cycles', methods=['GET'])
def get_iteration_cycles():
    """获取迭代周期配置"""
    try:
        config = IterationConfig()
        
        return jsonify({
            'success': True,
            'data': config.ITERATION_CYCLES
        })
    except Exception as e:
        logger.error(f"获取迭代周期失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取迭代周期失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/employees', methods=['GET'])
def get_ai_employees():
    """获取AI员工角色配置"""
    try:
        config = IterationConfig()
        
        return jsonify({
            'success': True,
            'data': config.AI_EMPLOYEE_ROLES,
            'count': len(config.AI_EMPLOYEE_ROLES)
        })
    except Exception as e:
        logger.error(f"获取AI员工配置失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取AI员工配置失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/employees/<employee_type>', methods=['GET'])
def get_ai_employee(employee_type):
    """获取单个AI员工角色配置"""
    try:
        config = IterationConfig()
        employee = config.AI_EMPLOYEE_ROLES.get(employee_type)
        
        if not employee:
            return jsonify({
                'success': False,
                'error': 'AI员工类型不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': employee
        })
    except Exception as e:
        logger.error(f"获取AI员工配置失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取AI员工配置失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/status', methods=['GET'])
def get_iteration_status():
    """获取迭代引擎状态"""
    try:
        engine = get_iteration_engine()
        plans = engine.get_iteration_plans()
        
        status_counts = {}
        for plan in plans:
            status = plan['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'engine_status': 'running',
                'total_plans': len(plans),
                'status_counts': status_counts,
                'recent_plans': plans[:5]
            }
        })
    except Exception as e:
        logger.error(f"获取迭代引擎状态失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取迭代引擎状态失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/config', methods=['POST'])
def update_iteration_config():
    """更新迭代配置"""
    try:
        data = request.json or {}
        
        config = IterationConfig()
        
        if 'cycles' in data:
            for cycle_name, cycle_config in data['cycles'].items():
                if cycle_name in config.ITERATION_CYCLES:
                    config.ITERATION_CYCLES[cycle_name].update(cycle_config)
        
        if 'employees' in data:
            for emp_type, emp_config in data['employees'].items():
                if emp_type in config.AI_EMPLOYEE_ROLES:
                    config.AI_EMPLOYEE_ROLES[emp_type].update(emp_config)
        
        return jsonify({
            'success': True,
            'message': '迭代配置更新成功'
        })
    except Exception as e:
        logger.error(f"更新迭代配置失败: {e}")
        return jsonify({
            'success': False,
            'error': f'更新迭代配置失败: {str(e)}'
        }), 500


@iteration_api.route('/iteration/run', methods=['POST'])
def run_iteration():
    """手动运行一次迭代"""
    try:
        data = request.json or {}
        iteration_type = data.get('type', 'daily')
        
        engine = get_iteration_engine()
        result = engine.run_iteration(iteration_type)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"运行迭代失败: {e}")
        return jsonify({
            'success': False,
            'error': f'运行迭代失败: {str(e)}'
        }), 500
