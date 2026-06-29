# -*- coding: utf-8 -*-
"""
协作API接口
提供Agent与AI员工协同工作的RESTful接口
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

collaborative_api = Blueprint('collaborative_api', __name__)


def get_integration():
    """获取集成控制器"""
    try:
        from app.agents.agent_ai_employee_integration import get_integration
        return get_integration()
    except Exception as e:
        logger.error(f"获取集成控制器失败: {e}")
        return None


def get_task_scheduler():
    """获取任务调度器"""
    try:
        from app.agents.collaborative_task_scheduler import get_task_scheduler
        return get_task_scheduler()
    except Exception as e:
        logger.error(f"获取任务调度器失败: {e}")
        return None


@collaborative_api.route('/api/collaborative/task', methods=['POST'])
def submit_collaborative_task():
    """提交协作任务"""
    try:
        data = request.get_json() or {}
        task_type = data.get('task_type', 'general')
        task_data = data.get('task_data', {})
        priority = data.get('priority', 0)
        
        scheduler = get_task_scheduler()
        if not scheduler:
            return jsonify({'success': False, 'error': '任务调度器未初始化'})
        
        task_id = scheduler.submit_task(task_type, task_data, priority)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f"协作任务已提交: {task_id}"
        })
    
    except Exception as e:
        logger.error(f"提交协作任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    try:
        scheduler = get_task_scheduler()
        if not scheduler:
            return jsonify({'success': False, 'error': '任务调度器未初始化'})
        
        result = scheduler.get_task_status(task_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/task/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """取消任务"""
    try:
        scheduler = get_task_scheduler()
        if not scheduler:
            return jsonify({'success': False, 'error': '任务调度器未初始化'})
        
        result = scheduler.cancel_task(task_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/tasks/active', methods=['GET'])
def get_active_tasks():
    """获取活跃任务"""
    try:
        scheduler = get_task_scheduler()
        if not scheduler:
            return jsonify({'success': False, 'error': '任务调度器未初始化'})
        
        result = scheduler.get_active_tasks()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取活跃任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/tasks/completed', methods=['GET'])
def get_completed_tasks():
    """获取已完成任务"""
    try:
        limit = int(request.args.get('limit', 100))
        
        scheduler = get_task_scheduler()
        if not scheduler:
            return jsonify({'success': False, 'error': '任务调度器未初始化'})
        
        result = scheduler.get_completed_tasks(limit)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取已完成任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/scheduler/stats', methods=['GET'])
def get_scheduler_stats():
    """获取调度器统计"""
    try:
        scheduler = get_task_scheduler()
        if not scheduler:
            return jsonify({'success': False, 'error': '任务调度器未初始化'})
        
        result = scheduler.get_scheduler_stats()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取调度器统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/dispatch', methods=['POST'])
def dispatch_to_employee():
    """直接分派任务给AI员工"""
    try:
        data = request.get_json() or {}
        agent_code = data.get('agent_code', 'collaborative_api')
        task_type = data.get('task_type', 'general')
        task_data = data.get('task_data', {})
        employee_template = data.get('employee_template')
        
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        task = {
            'task_type': task_type,
            'task_data': task_data,
            'agent_code': agent_code
        }
        
        result = integration.dispatch_task_to_employee(agent_code, task, employee_template)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"分派任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/collaborate', methods=['POST'])
def create_collaboration():
    """创建多AI员工协作"""
    try:
        data = request.get_json() or {}
        agent_code = data.get('agent_code', 'collaborative_api')
        task_type = data.get('task_type', 'general')
        task_data = data.get('task_data', {})
        employee_templates = data.get('employee_templates', ['code_fixer', 'data_analyzer'])
        
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        task = {
            'task_type': task_type,
            'task_data': task_data,
            'agent_code': agent_code
        }
        
        result = integration.create_multi_agent_collaboration(
            agent_code, task, employee_templates
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"创建协作失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/session/<session_id>', methods=['GET'])
def get_collaboration_status(session_id):
    """获取协作会话状态"""
    try:
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        result = integration.get_collaboration_status(session_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取协作状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/session/<session_id>/complete', methods=['POST'])
def complete_collaboration(session_id):
    """完成协作会话"""
    try:
        data = request.get_json() or {}
        results = data.get('results', {})
        
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        result = integration.complete_collaboration(session_id, results)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"完成协作失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/sessions', methods=['GET'])
def get_active_collaborations():
    """获取所有活跃协作"""
    try:
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        result = integration.get_active_collaborations()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取活跃协作失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/message/send', methods=['POST'])
def send_message():
    """发送消息"""
    try:
        data = request.get_json() or {}
        from_agent_code = data.get('from_agent_code', 'collaborative_api')
        to_employee_id = data.get('to_employee_id')
        message_type = data.get('message_type', 'knowledge_share')
        content = data.get('content', {})
        
        if not to_employee_id:
            return jsonify({'success': False, 'error': '目标员工ID不能为空'})
        
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        message = {
            'type': message_type,
            'content': content
        }
        
        result = integration.send_message_between_agents(from_agent_code, to_employee_id, message)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/message/receive/<employee_id>', methods=['GET'])
def receive_messages(employee_id):
    """接收消息"""
    try:
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        result = integration.get_employee_messages(employee_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"接收消息失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/system/status', methods=['GET'])
def get_combined_status():
    """获取综合系统状态"""
    try:
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        result = integration.get_combined_system_status()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"获取综合状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/task-routing', methods=['GET'])
def get_task_routing():
    """获取任务路由配置"""
    try:
        scheduler = get_task_scheduler()
        if not scheduler:
            return jsonify({'success': False, 'error': '任务调度器未初始化'})
        
        routing = {
            'code_fix': ['ai_employee', 'agent'],
            'data_analysis': ['ai_employee', 'agent'],
            'security_scan': ['ai_employee'],
            'performance': ['ai_employee'],
            'quality_assurance': ['ai_employee'],
            'knowledge_management': ['ai_employee'],
            'task_coordination': ['agent'],
            'system_maintenance': ['ai_employee', 'agent'],
            'general': ['agent', 'ai_employee']
        }
        
        return jsonify({
            'success': True,
            'task_routing': routing,
            'total_task_types': len(routing)
        })
    
    except Exception as e:
        logger.error(f"获取任务路由失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@collaborative_api.route('/api/collaborative/employee-templates', methods=['GET'])
def get_employee_templates():
    """获取AI员工模板列表"""
    try:
        integration = get_integration()
        if not integration:
            return jsonify({'success': False, 'error': '集成控制器未初始化'})
        
        employee_system = integration.get_ai_employee_system()
        if not employee_system:
            return jsonify({'success': False, 'error': 'AI员工系统未初始化'})
        
        templates = employee_system.generator.EMPLOYEE_TEMPLATES
        
        return jsonify({
            'success': True,
            'templates': templates,
            'total': len(templates)
        })
    
    except Exception as e:
        logger.error(f"获取员工模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


def init_collaborative_api(app_instance):
    """初始化协作API"""
    try:
        from app.agents.agent_ai_employee_integration import init_integration
        from app.agents.collaborative_task_scheduler import init_task_scheduler
        
        init_integration()
        init_task_scheduler()
        
        app_instance.register_blueprint(collaborative_api)
        logger.info("[协作API] 协作API注册完成(Agent-AI员工协同工作)")
    
    except Exception as e:
        logger.warning(f"[协作API] 初始化协作API失败(非致命): {e}")


__all__ = ['collaborative_api', 'init_collaborative_api']