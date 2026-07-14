#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
升级后的AI引擎API - 提供AI调用、规则管理、模型切换接口
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime

ai_engine_api = Blueprint('ai_engine_api', __name__)

# 全局AI引擎管理器实例
ai_engine_manager_instance = None

def init_ai_engine():
    """初始化AI引擎管理器"""
    global ai_engine_manager_instance
    if ai_engine_manager_instance is None:
        from app.utils.ai_engine import get_ai_engine_manager
        ai_engine_manager_instance = get_ai_engine_manager()
    return ai_engine_manager_instance

def get_ai_engine_manager():
    """获取AI引擎管理器实例"""
    if ai_engine_manager_instance is None:
        return init_ai_engine()
    return ai_engine_manager_instance

@ai_engine_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'ai-engine-api', 'version': '2.0'})

# ==================== AI调用接口 ====================

@ai_engine_api.route('/generate', methods=['POST'])
def generate():
    """生成AI响应"""
    manager = get_ai_engine_manager()
    data = request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    prompt = data['prompt']
    model_type = data.get('model')
    system_prompt = data.get('system_prompt')
    
    result = manager.generate_response(prompt, model=model_type, system_prompt=system_prompt)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@ai_engine_api.route('/models')
def get_models():
    """获取可用模型列表"""
    manager = get_ai_engine_manager()
    models = manager.get_models()
    return jsonify(models)

@ai_engine_api.route('/models/<model_type>', methods=['POST'])
def set_model(model_type):
    """设置活动模型"""
    manager = get_ai_engine_manager()
    success = manager.set_model(model_type)
    
    if success:
        return jsonify({'success': True, 'message': f"模型已切换为: {model_type}"})
    else:
        return jsonify({'error': '模型不存在'}), 404

# ==================== 规则管理接口 ====================

@ai_engine_api.route('/rules')
def get_rules():
    """获取所有规则"""
    manager = get_ai_engine_manager()
    rules = manager.get_rules()
    
    result = []
    for rule in rules:
        result.append({
            'name': rule.name,
            'type': rule.rule_type,
            'priority': rule.priority,
            'enabled': rule.enabled,
            'condition': rule.condition
        })
    
    return jsonify(result)

@ai_engine_api.route('/rules/<rule_name>')
def get_rule(rule_name):
    """获取规则详情"""
    manager = get_ai_engine_manager()
    rules = manager.get_rules()
    
    for rule in rules:
        if rule.name == rule_name:
            return jsonify({
                'name': rule.name,
                'type': rule.rule_type,
                'priority': rule.priority,
                'enabled': rule.enabled,
                'condition': rule.condition
            })
    
    return jsonify({'error': '规则不存在'}), 404

@ai_engine_api.route('/rules/<rule_name>/enable', methods=['POST'])
def enable_rule(rule_name):
    """启用规则"""
    manager = get_ai_engine_manager()
    success = manager.rule_engine.enable_rule(rule_name)
    
    if success:
        return jsonify({'success': True, 'message': f"规则已启用: {rule_name}"})
    else:
        return jsonify({'error': '规则不存在'}), 404

@ai_engine_api.route('/rules/<rule_name>/disable', methods=['POST'])
def disable_rule(rule_name):
    """禁用规则"""
    manager = get_ai_engine_manager()
    success = manager.rule_engine.disable_rule(rule_name)
    
    if success:
        return jsonify({'success': True, 'message': f"规则已禁用: {rule_name}"})
    else:
        return jsonify({'error': '规则不存在'}), 404

@ai_engine_api.route('/rules/execute', methods=['POST'])
def execute_rules():
    """执行规则"""
    manager = get_ai_engine_manager()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '缺少数据'}), 400
    
    results = manager.execute_rules(data)
    return jsonify(results)

@ai_engine_api.route('/rules/add', methods=['POST'])
def add_rule():
    """添加规则"""
    from app.utils.ai_engine import Rule
    
    manager = get_ai_engine_manager()
    data = request.get_json()
    
    required_fields = ['name', 'rule_type', 'condition']
    if not all(f in data for f in required_fields):
        return jsonify({'error': '缺少必要参数'}), 400
    
    # 创建简单的动作函数
    def default_action(d):
        return {'matched': True, 'rule': data['name']}
    
    rule = Rule(
        name=data['name'],
        rule_type=data['rule_type'],
        condition=data['condition'],
        action=default_action,
        priority=data.get('priority', 1)
    )
    
    manager.add_rule(rule)
    return jsonify({'success': True, 'message': f"规则已添加: {data['name']}"})

@ai_engine_api.route('/rules/<rule_name>/remove', methods=['DELETE'])
def remove_rule(rule_name):
    """移除规则"""
    manager = get_ai_engine_manager()
    manager.rule_engine.remove_rule(rule_name)
    return jsonify({'success': True, 'message': f"规则已移除: {rule_name}"})

# ==================== 系统状态 ====================

@ai_engine_api.route('/status')
def status():
    """获取系统状态"""
    manager = get_ai_engine_manager()
    models = manager.get_models()
    rules = manager.get_rules()
    
    return jsonify({
        'status': 'running',
        'version': '2.0',
        'models': len(models),
        'rules': len(rules),
        'timestamp': datetime.now().isoformat()
    })

@ai_engine_api.route('/health')
def health():
    """健康检查"""
    manager = get_ai_engine_manager()
    
    try:
        # 测试AI引擎
        response = manager.generate_response("test")
        ai_ok = response['success']
        
        # 测试规则引擎
        rules = manager.get_rules()
        rules_ok = len(rules) > 0
        
        return jsonify({
            'status': 'healthy' if (ai_ok and rules_ok) else 'degraded',
            'ai_engine': ai_ok,
            'rule_engine': rules_ok,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@ai_engine_api.route('/test')
def test():
    """测试功能"""
    manager = get_ai_engine_manager()
    
    results = {
        'ai_test': False,
        'model_test': False,
        'rule_test': False,
        'security_test': False
    }
    
    # 测试AI生成
    try:
        response = manager.generate_response("hello")
        results['ai_test'] = response['success']
    except Exception:
        pass
    
    # 测试模型列表
    try:
        models = manager.get_models()
        results['model_test'] = len(models) > 0
    except Exception:
        pass
    
    # 测试规则
    try:
        rules = manager.get_rules()
        results['rule_test'] = len(rules) > 0
    except Exception:
        pass
    
    # 测试安全规则
    try:
        response = manager.generate_response("my password is secret")
        results['security_test'] = not response['success']
    except Exception:
        pass
    
    return jsonify(results)
