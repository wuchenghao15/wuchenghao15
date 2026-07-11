# -*- coding: utf-8 -*-
"""
AI员工增强系统API
提供AI员工管理、协作、思维评估等接口
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

ai_employee_enhanced_api = Blueprint('ai_employee_enhanced_api', __name__)


def get_enhanced_system():
    """获取增强系统实例"""
    try:
        from app.ai.ai_employee_enhanced_system import get_enhanced_system
        return get_enhanced_system()
    except Exception as e:
        logger.error(f"获取增强系统失败: {e}")
        return None


@ai_employee_enhanced_api.route('/ai-employee-enhanced/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        status = system.get_system_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
    
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/generate', methods=['POST'])
def generate_employee():
    """生成AI员工"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        data = request.get_json() or {}
        template_key = data.get('template_key', 'code_fixer')
        level = data.get('level', 'specialist')
        supervisor_id = data.get('supervisor_id')
        custom_config = data.get('custom_config', {})
        
        result = system.create_full_employee(
            template_key, level, supervisor_id
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"生成AI员工失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/auto-generate', methods=['POST'])
def auto_generate_employees():
    """基于系统需求自动生成AI员工"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        result = system.generator.auto_generate_based_needs()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"自动生成AI员工失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/templates/list', methods=['GET'])
def get_templates():
    """获取AI员工模板列表"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        templates = system.generator.EMPLOYEE_TEMPLATES
        
        return jsonify({
            'success': True,
            'templates': templates,
            'total': len(templates)
        })
    
    except Exception as e:
        logger.error(f"获取模板列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/organization/structure', methods=['GET'])
def get_organization_structure():
    """获取组织结构"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        structure = system.organization.get_organization_structure()
        
        return jsonify({
            'success': True,
            'data': structure
        })
    
    except Exception as e:
        logger.error(f"获取组织结构失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/organization/hierarchy-levels', methods=['GET'])
def get_hierarchy_levels():
    """获取层级定义"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        levels = system.organization.HIERARCHY_LEVELS
        
        return jsonify({
            'success': True,
            'levels': levels,
            'total': len(levels)
        })
    
    except Exception as e:
        logger.error(f"获取层级定义失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/collaboration/create', methods=['POST'])
def create_collaboration():
    """创建协作会话"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        data = request.get_json() or {}
        participants = data.get('participants', [])
        task = data.get('task', {})
        
        result = system.assign_collaborative_task(task, participants)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"创建协作会话失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/collaboration/report/<session_id>', methods=['GET'])
def get_collaboration_report(session_id):
    """获取协作报告"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        report = system.collaboration.get_collaboration_report(session_id)
        
        return jsonify(report)
    
    except Exception as e:
        logger.error(f"获取协作报告失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/collaboration/contribute', methods=['POST'])
def add_contribution():
    """添加协作贡献"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        data = request.get_json() or {}
        session_id = data.get('session_id')
        employee_id = data.get('employee_id')
        contribution = data.get('contribution', {})
        
        result = system.collaboration.add_contribution(
            session_id, employee_id, contribution
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"添加协作贡献失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/message/send', methods=['POST'])
def send_message():
    """发送消息"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        data = request.get_json() or {}
        from_id = data.get('from_id', 'system')
        to_id = data.get('to_id')
        message_type = data.get('message_type', 'task_request')
        content = data.get('content', {})
        
        result = system.collaboration.send_message(
            from_id, to_id, message_type, content
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/message/receive/<employee_id>', methods=['GET'])
def receive_messages(employee_id):
    """接收消息"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        unread_only = request.args.get('unread_only', 'true').lower() == 'true'
        
        messages = system.collaboration.receive_messages(
            employee_id, unread_only
        )
        
        return jsonify({
            'success': True,
            'messages': messages,
            'total': len(messages)
        })
    
    except Exception as e:
        logger.error(f"接收消息失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/thinking/evaluate', methods=['POST'])
def evaluate_thinking():
    """评估思维"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        data = request.get_json() or {}
        employee_id = data.get('employee_id')
        task_type = data.get('task_type', 'code_fix')
        context = data.get('context', {})
        
        evaluation = system.thinking_matrix.evaluate_thinking(
            employee_id, task_type, context
        )
        
        return jsonify({
            'success': True,
            'evaluation': evaluation
        })
    
    except Exception as e:
        logger.error(f"评估思维失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/thinking/report/<employee_id>', methods=['GET'])
def get_thinking_report(employee_id):
    """获取思维报告"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        report = system.thinking_matrix.get_thinking_report(employee_id)
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        logger.error(f"获取思维报告失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/thinking/dimensions', methods=['GET'])
def get_thinking_dimensions():
    """获取思维维度定义"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        dimensions = system.thinking_matrix.DIMENSIONS
        
        return jsonify({
            'success': True,
            'dimensions': dimensions,
            'total': len(dimensions)
        })
    
    except Exception as e:
        logger.error(f"获取思维维度失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/train/<employee_id>', methods=['POST'])
def train_employee(employee_id):
    """培训AI员工"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        data = request.get_json() or {}
        training_type = data.get('training_type', 'code_fix')
        
        result = system.train_employee(employee_id, training_type)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"培训AI员工失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/generation/statistics', methods=['GET'])
def get_generation_statistics():
    """获取生成统计"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        stats = system.generator.get_generation_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    
    except Exception as e:
        logger.error(f"获取生成统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@ai_employee_enhanced_api.route('/ai-employee-enhanced/needs/analyze', methods=['GET'])
def analyze_system_needs():
    """分析系统需求"""
    try:
        system = get_enhanced_system()
        if not system:
            return jsonify({'success': False, 'error': '系统未初始化'})
        
        needs = system.generator.analyze_system_needs()
        
        return jsonify({
            'success': True,
            'needs': needs
        })
    
    except Exception as e:
        logger.error(f"分析系统需求失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


# 初始化增强系统
def init_enhanced_system():
    """初始化增强系统"""
    try:
        from app.ai.ai_employee_enhanced_system import init_enhanced_system
        init_enhanced_system()
        logger.info("[API] AI员工增强系统初始化完成")
    except Exception as e:
        logger.warning(f"[API] AI员工增强系统初始化失败: {e}")


# 导出蓝图和初始化函数
__all__ = ['ai_employee_enhanced_api', 'init_enhanced_system']