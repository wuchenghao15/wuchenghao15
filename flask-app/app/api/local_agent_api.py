# -*- coding: utf-8 -*-
"""
本地Agent API接口
提供Agent管理、任务调度和对话交互的RESTful API
"""

from flask import Blueprint, request, jsonify
import logging
import uuid

logger = logging.getLogger(__name__)

local_agent_api = Blueprint('local_agent_api', __name__)


def get_agent_manager():
    """获取Agent管理器实例"""
    try:
        from app.agents.agent_manager import get_agent_manager
        return get_agent_manager()
    except Exception as e:
        logger.error(f"获取Agent管理器失败: {e}")
        return None


def get_db():
    """获取数据库实例"""
    try:
        from app.utils.db import db_manager
        return db_manager
    except Exception as e:
        logger.error(f"获取数据库实例失败: {e}")
        return None


@local_agent_api.route('/api/local-agents', methods=['GET'])
def list_agents():
    """获取所有Agent列表"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        agents = manager.list_agents()
        
        return jsonify({
            'success': True,
            'data': agents,
            'total': len(agents)
        })
    
    except Exception as e:
        logger.error(f"获取Agent列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>', methods=['GET'])
def get_agent(agent_code):
    """获取单个Agent信息"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        agent = manager.get_agent(agent_code)
        
        if not agent:
            return jsonify({'success': False, 'error': f"未找到Agent: {agent_code}"})
        
        return jsonify({
            'success': True,
            'data': agent
        })
    
    except Exception as e:
        logger.error(f"获取Agent失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents', methods=['POST'])
def create_agent():
    """创建新的Agent"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        data = request.get_json() or {}
        
        if not data.get('agent_name'):
            return jsonify({'success': False, 'error': 'Agent名称不能为空'})
        
        result = manager.register_agent(data)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"创建Agent失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>', methods=['PUT'])
def update_agent(agent_code):
    """更新Agent配置"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        data = request.get_json() or {}
        
        result = manager.update_agent(agent_code, data)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"更新Agent失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>', methods=['DELETE'])
def delete_agent(agent_code):
    """删除Agent"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        result = manager.delete_agent(agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"删除Agent失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>/start', methods=['POST'])
def start_agent(agent_code):
    """启动Agent"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        result = manager.start_agent(agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"启动Agent失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>/stop', methods=['POST'])
def stop_agent(agent_code):
    """停止Agent"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        result = manager.stop_agent(agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"停止Agent失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>/restart', methods=['POST'])
def restart_agent(agent_code):
    """重启Agent"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        result = manager.restart_agent(agent_code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"重启Agent失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/status', methods=['GET'])
def get_system_status():
    """获取Agent系统状态"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        status = manager.get_system_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
    
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>/tasks', methods=['POST'])
def submit_task(agent_code):
    """提交任务给Agent"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        data = request.get_json() or {}
        
        result = manager.submit_task(agent_code, data)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/tasks/<task_code>', methods=['GET'])
def get_task_status(task_code):
    """获取任务状态"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        task = manager.get_task_status(task_code)
        
        if not task:
            return jsonify({'success': False, 'error': f"未找到任务: {task_code}"})
        
        return jsonify({
            'success': True,
            'data': task
        })
    
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>/conversations', methods=['POST'])
def create_conversation(agent_code):
    """创建对话"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        result = manager.create_conversation(agent_code, user_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """获取对话详情"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        conversation = manager.get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({'success': False, 'error': f"未找到对话: {conversation_id}"})
        
        return jsonify({
            'success': True,
            'data': conversation
        })
    
    except Exception as e:
        logger.error(f"获取对话失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/conversations/<conversation_id>/messages', methods=['POST'])
def send_message(conversation_id):
    """发送消息"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        data = request.get_json() or {}
        message = data.get('message', '')
        user_id = data.get('user_id')
        
        if not message:
            return jsonify({'success': False, 'error': '消息内容不能为空'})
        
        result = manager.send_message(conversation_id, message, user_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/<agent_code>/conversations', methods=['GET'])
def get_conversations(agent_code):
    """获取Agent的所有对话"""
    try:
        manager = get_agent_manager()
        if not manager:
            return jsonify({'success': False, 'error': 'Agent管理器未初始化'})
        
        conversations = manager.get_conversations_by_agent(agent_code)
        
        return jsonify({
            'success': True,
            'data': conversations,
            'total': len(conversations)
        })
    
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        manager = get_agent_manager()
        
        if manager:
            status = manager.get_system_status()
            return jsonify({
                'success': True,
                'status': 'healthy',
                'manager_running': status.get('manager_running', False),
                'running_agents': status.get('running_agents', 0)
            })
        else:
            return jsonify({
                'success': True,
                'status': 'unhealthy',
                'manager_running': False,
                'running_agents': 0
            })
    
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({'success': False, 'error': str(e)})


@local_agent_api.route('/api/local-agents/init', methods=['POST'])
def init_agents():
    """初始化Agent系统"""
    try:
        db = get_db()
        if not db:
            return jsonify({'success': False, 'error': '数据库未初始化'})
        
        from app.models.local_agent import init_local_agent_tables
        
        init_local_agent_tables(db)
        
        return jsonify({
            'success': True,
            'message': 'Agent系统初始化完成'
        })
    
    except Exception as e:
        logger.error(f"初始化Agent系统失败: {e}")
        return jsonify({'success': False, 'error': str(e)})