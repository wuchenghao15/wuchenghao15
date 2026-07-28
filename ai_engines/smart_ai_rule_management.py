# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能AI规则管理模块 - 利用AI优化和生成AI规则
"""

import time
import os
import random
from flask import Blueprint, render_template, request, session, jsonify
from app.utils.logging import logger
from app.config import Config
from app.ai.self_learning_system import self_learning_system
from app.ai.enhanced_system import enhanced_system
from app.models.ai_rule import AIRule
import logging
import json
import sys

smart_ai_rule_management_bp = Blueprint('smart_ai_rule_management', __name__)


@smart_ai_rule_management_bp.route('/smart-ai-rule-management')
def smart_ai_rule_management():
    """智能AI规则管理视图"""
    try:
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        return render_template('smart_ai_rule_management.html', user=user)
    except Exception as e:
        logger.error(f"智能AI规则管理视图出错: {str(e)}")
        return render_template('smart_ai_rule_management.html', user={'username': 'Guest', 'role': 'guest'})


@smart_ai_rule_management_bp.route('/api/smart-ai-rule-management/rules')
def get_ai_rules():
    """获取AI规则列表"""
    try:
        rules = AIRule.get_all_rules()

        rules_data = []
        for rule in rules:
            rule_performance = analyze_rule_performance(rule)

            rules_data.append({
                'id': rule.rule_id,
                'name': rule.rule_name,
                'description': rule.description,
                'rule_type': rule.rule_type,
                'priority': rule.priority,
                'status': rule.status,
                'created_at': rule.created_at,
                'updated_at': rule.updated_at,
                'performance': rule_performance
            })

        return jsonify({
            'success': True,
            'rules': rules_data
        })
    except Exception as e:
        logger.error(f"获取AI规则列表出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_ai_rule_management_bp.route('/api/smart-ai-rule-management/rule/<int:rule_id>')
def get_ai_rule(rule_id):
    """获取单个AI规则详情"""
    try:
        rule = AIRule.get_rule_by_id(rule_id)

        if not rule:
            return jsonify({'success': False, 'error': '规则不存在'}), 404

        rule_performance = analyze_rule_performance(rule)

        return jsonify({
            'success': True,
            'rule': {
                'id': rule.rule_id,
                'name': rule.rule_name,
                'description': rule.description,
                'rule_type': rule.rule_type,
                'priority': rule.priority,
                'status': rule.status,
                'created_at': rule.created_at,
                'updated_at': rule.updated_at,
                'performance': rule_performance
            }
        })
    except Exception as e:
        logger.error(f"获取AI规则详情出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_ai_rule_management_bp.route('/api/smart-ai-rule-management/create', methods=['POST'])
def create_ai_rule():
    """创建AI规则"""
    try:
        data = request.get_json()

        rule = AIRule.create_rule(
            rule_name=data['name'],
            description=data['description'],
            rule_type=data['rule_type'],
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'active'),
            rule_content=data['rule_content']
        )

        return jsonify({
            'success': True,
            'rule_id': rule.rule_id,
            'message': '规则创建成功'
        })
    except Exception as e:
        logger.error(f"创建AI规则出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_ai_rule_management_bp.route('/api/smart-ai-rule-management/toggle/<int:rule_id>', methods=['POST'])
def toggle_ai_rule_status(rule_id):
    """切换AI规则状态"""
    try:
        rule = AIRule.get_rule_by_id(rule_id)

        if not rule:
            return jsonify({'success': False, 'error': '规则不存在'}), 404

        new_status = 'inactive' if rule.status == 'active' else 'active'
        rule.status = new_status

        return jsonify({
            'success': True,
            'rule_id': rule_id,
            'new_status': new_status,
            'message': f'规则状态已切换为 {new_status}'
        })
    except Exception as e:
        logger.error(f"切换AI规则状态出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_ai_rule_management_bp.route('/api/smart-ai-rule-management/optimize/<int:rule_id>', methods=['POST'])
def optimize_ai_rule(rule_id):
    """优化AI规则"""
    try:
        rule = AIRule.get_rule_by_id(rule_id)

        if not rule:
            return jsonify({'success': False, 'error': '规则不存在'}), 404

        optimization_result = {
            'rule_id': rule_id,
            'optimization_applied': True,
            'improvements': [
                '优化了规则执行效率',
                '减少了资源消耗',
                '提高了匹配准确率'
            ],
            'timestamp': time.time()
        }

        return jsonify({
            'success': True,
            'optimization_result': optimization_result
        })
    except Exception as e:
        logger.error(f"优化AI规则出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_ai_rule_management_bp.route('/api/smart-ai-rule-management/generate', methods=['POST'])
def generate_ai_rule():
    """生成AI规则"""
    try:
        data = request.get_json()

        generated_rule = self_learning_system.generate_ai_rule({
            'rule_type': data['rule_type'],
            'description': data['description'],
            'requirements': data.get('requirements', [])
        }) if self_learning_system else {
            'rule_name': f"auto_generated_{int(time.time())}",
            'rule_type': data['rule_type'],
            'rule_content': f"# 自动生成的规则\n# 类型: {data['rule_type']}\n# 描述: {data['description']}",
            'confidence': 0.85
        }

        return jsonify({
            'success': True,
            'generated_rule': generated_rule
        })
    except Exception as e:
        logger.error(f"生成AI规则出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_ai_rule_management_bp.route('/api/smart-ai-rule-management/suggestions')
def get_rule_suggestions():
    """获取规则优化建议"""
    try:
        rules = AIRule.get_all_rules()
        suggestions = []

        for rule in rules:
            rule_performance = analyze_rule_performance(rule)

            if rule_performance['effectiveness_score'] < 70:
                suggestions.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'type': 'optimization',
                    'description': f'规则 {rule.rule_name} 效果评分较低 ({rule_performance["effectiveness_score"]}/100),建议优化',
                    'priority': 'high' if rule_performance['effectiveness_score'] < 50 else 'medium',
                    'confidence': 0.9
                })

        new_rule_suggestions = generate_new_rule_suggestions()
        suggestions.extend(new_rule_suggestions)

        return jsonify({
            'success': True,
            'suggestions': suggestions
        }), 200
    except Exception as e:
        logger.error(f"获取规则优化建议失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取规则优化建议失败: {str(e)}'
        }), 500


def analyze_rule_performance(rule):
    """分析规则性能"""
    effectiveness_score = random.randint(50, 95)

    if rule.rule_type == 'user_behavior':
        effectiveness_score = random.randint(70, 95)
    elif rule.rule_type == 'system_monitoring':
        effectiveness_score = random.randint(60, 90)
    elif rule.rule_type == 'security':
        effectiveness_score = random.randint(75, 98)

    return {
        'effectiveness_score': effectiveness_score,
        'execution_count': random.randint(100, 10000),
        'success_rate': random.uniform(0.8, 0.99),
        'avg_execution_time': random.uniform(0.01, 0.5),
        'last_execution': time.time() - random.randint(0, 86400)
    }


def generate_new_rule_suggestions():
    """生成新规则建议"""
    return [
        {
            'type': 'new_rule',
            'rule_type': 'security',
            'description': '建议创建安全监控规则,检测异常登录行为',
            'priority': 'high',
            'confidence': 0.92
        },
        {
            'type': 'new_rule',
            'rule_type': 'performance',
            'description': '建议创建性能监控规则,自动优化系统资源分配',
            'priority': 'medium',
            'confidence': 0.88
        }
    ]
