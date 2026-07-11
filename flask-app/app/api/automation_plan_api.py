#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutomationPlanAgent API接口
提供自动化计划分析、拓展、优化等功能的HTTP访问
"""

from flask import Blueprint, jsonify, request
import logging

from ai_engines.automation_plan_agent import automation_plan_agent

logger = logging.getLogger(__name__)

automation_plan_api = Blueprint('automation_plan_api', __name__)


@automation_plan_api.route('/automation-plan-agent/status')
def get_agent_status():
    """获取AutomationPlanAgent状态"""
    try:
        status = automation_plan_agent.get_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"获取AutomationPlanAgent状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_plan_api.route('/automation-plan-agent/plans')
def list_plans():
    """获取所有自动化计划列表"""
    try:
        plans = automation_plan_agent.list_plans()
        return jsonify({
            'success': True,
            'plans': plans,
            'total': len(plans)
        })
    except Exception as e:
        logger.error(f"获取计划列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_plan_api.route('/automation-plan-agent/plans/<plan_id>')
def get_plan(plan_id):
    """获取单个计划详情"""
    try:
        plan = automation_plan_agent.get_plan(plan_id)
        if plan:
            return jsonify({
                'success': True,
                'plan': automation_plan_agent._plan_to_dict(plan)
            })
        else:
            return jsonify({
                'success': False,
                'error': f"计划不存在: {plan_id}"
            }), 404
    except Exception as e:
        logger.error(f"获取计划失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_plan_api.route('/automation-plan-agent/analyze')
def analyze_plans():
    """分析现有计划覆盖范围"""
    try:
        analysis = automation_plan_agent.analyze_plans()
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"分析计划失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_plan_api.route('/automation-plan-agent/expand')
def expand_features():
    """拓展缺失功能，创建新计划"""
    try:
        result = automation_plan_agent.expand_features()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"拓展功能失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_plan_api.route('/automation-plan-agent/optimize')
def optimize_plans():
    """优化现有计划"""
    try:
        result = automation_plan_agent.optimize_plans()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"优化计划失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_plan_api.route('/automation-plan-agent/auto-analyze-expand')
def auto_analyze_and_expand():
    """自动分析并拓展计划"""
    try:
        result = automation_plan_agent.auto_analyze_and_expand()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"自动分析拓展失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_plan_api.route('/automation-plan-agent/plans', methods=['POST'])
def create_plan():
    """创建自定义计划"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'plan_type', 'priority', 'schedule', 'tasks']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f"缺少必填字段: {field}"
                }), 400
        
        plan = automation_plan_agent.create_custom_plan(
            name=data['name'],
            plan_type=data['plan_type'],
            priority=data['priority'],
            schedule=data['schedule'],
            tasks=data['tasks'],
            description=data.get('description', '')
        )
        
        return jsonify({
            'success': True,
            'plan': automation_plan_agent._plan_to_dict(plan),
            'message': f"计划创建成功: {plan.name}"
        }), 201
    except Exception as e:
        logger.error(f"创建计划失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_plan_api.route('/automation-plan-agent/coverage-report')
def get_coverage_report():
    """获取计划覆盖报告"""
    try:
        analysis = automation_plan_agent.analyze_plans()
        
        report = {
            'total_plans': analysis['total_plans'],
            'function_areas': {
                'total': len(analysis['overall_coverage']),
                'fully_covered': len(analysis['fully_covered_areas']),
                'partial': len(analysis['partial_function_areas']),
                'missing': len(analysis['missing_function_areas'])
            },
            'coverage_details': analysis['overall_coverage'],
            'recommendations': analysis['recommendations'][:10],
            'optimization_opportunities': analysis['optimization_opportunities']
        }
        
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        logger.error(f"生成覆盖报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500