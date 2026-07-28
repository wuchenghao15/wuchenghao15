#!/usr/bin/env python3
"""AI Agent统一管理API"""

from flask import Blueprint, jsonify, request
import json

ai_agents_api = Blueprint('ai_agents_api', __name__)

agents = {}

def register_agent(agent):
    """注册Agent"""
    agents[agent.employee_id] = agent

@ai_agents_api.route('/api/ai_agents/list')
def api_ai_agents_list():
    """获取所有Agent列表"""
    try:
        agent_list = []
        for agent_id, agent in agents.items():
            agent_list.append({
                'employee_id': agent.employee_id,
                'name': agent.name,
                'role': agent.role,
                'skills': agent.skills,
                'status': agent.status,
                'level': agent.level,
                'experience': agent.experience,
                'tasks_completed': agent.tasks_completed,
                'current_task': agent.current_task
            })
        
        return jsonify({
            'success': True,
            'data': agent_list,
            'total': len(agent_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agents_api.route('/api/ai_agents/<agent_id>')
def api_ai_agent_detail(agent_id):
    """获取单个Agent详情"""
    try:
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent不存在'}), 404
        
        agent = agents[agent_id]
        
        return jsonify({
            'success': True,
            'data': {
                'employee_id': agent.employee_id,
                'name': agent.name,
                'role': agent.role,
                'skills': agent.skills,
                'status': agent.status,
                'level': agent.level,
                'experience': agent.experience,
                'tasks_completed': agent.tasks_completed,
                'current_task': agent.current_task,
                'created_at': agent.created_at.isoformat() if agent.created_at else None,
                'last_active': agent.last_active.isoformat() if agent.last_active else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agents_api.route('/api/ai_agents/<agent_id>/stats')
def api_ai_agent_stats(agent_id):
    """获取Agent统计信息"""
    try:
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent不存在'}), 404
        
        agent = agents[agent_id]
        
        if hasattr(agent, 'get_stats'):
            stats = agent.get_stats()
        else:
            stats = {
                'tasks_completed': agent.tasks_completed,
                'experience': agent.experience
            }
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agents_api.route('/api/ai_agents/<agent_id>/skills')
def api_ai_agent_skills(agent_id):
    """获取Agent技能列表"""
    try:
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent不存在'}), 404
        
        agent = agents[agent_id]
        
        return jsonify({'success': True, 'data': agent.skills})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agents_api.route('/api/ai_agents/<agent_id>/assign', methods=['POST'])
def api_ai_agent_assign(agent_id):
    """分配任务给Agent"""
    try:
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent不存在'}), 404
        
        agent = agents[agent_id]
        data = request.get_json()
        
        if not data or 'task' not in data:
            return jsonify({'success': False, 'error': '缺少任务信息'}), 400
        
        task = data['task']
        result = agent.assign_task(task)
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agents_api.route('/api/ai_agents/<agent_id>/complete', methods=['POST'])
def api_ai_agent_complete(agent_id):
    """完成Agent任务"""
    try:
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent不存在'}), 404
        
        agent = agents[agent_id]
        data = request.get_json()
        
        result = agent.complete_task(data.get('result', {}))
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agents_api.route('/api/ai_agents/search')
def api_ai_agents_search():
    """搜索Agent"""
    try:
        query = request.args.get('q', '')
        role = request.args.get('role', '')
        
        filtered = []
        for agent_id, agent in agents.items():
            match = True
            
            if query:
                query_lower = query.lower()
                if query_lower not in agent.name.lower() and query_lower not in agent.role.lower():
                    match = False
            
            if role and agent.role != role:
                match = False
            
            if match:
                filtered.append({
                    'employee_id': agent.employee_id,
                    'name': agent.name,
                    'role': agent.role,
                    'skills': agent.skills[:5]
                })
        
        return jsonify({
            'success': True,
            'data': filtered,
            'total': len(filtered)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agents_api.route('/api/ai_agents/count')
def api_ai_agents_count():
    """获取Agent数量"""
    try:
        count_by_role = {}
        for agent in agents.values():
            count_by_role[agent.role] = count_by_role.get(agent.role, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(agents),
                'by_role': count_by_role
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agents_api.route('/api/ai_agents/<agent_id>/execute', methods=['POST'])
def api_ai_agent_execute(agent_id):
    """执行Agent方法"""
    try:
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent不存在'}), 404
        
        agent = agents[agent_id]
        data = request.get_json()
        
        if not data or 'method' not in data:
            return jsonify({'success': False, 'error': '缺少方法名'}), 400
        
        method_name = data['method']
        params = data.get('params', {})
        
        if not hasattr(agent, method_name):
            return jsonify({'success': False, 'error': '方法不存在'}), 400
        
        method = getattr(agent, method_name)
        
        if callable(method):
            result = method(**params)
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': True, 'data': method})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
