#!/usr/bin/env python3
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.agent_factory import agent_factory

agent_management_api = Bluelogger.info('agent_management_api', __name__)

@agent_management_api.route('/api/agent/list', methods=['GET'])
@require_admin
def list_agents():
    try:
        agent_type = request.args.get('type')
        agents = agent_factory.list_agents(agent_type=agent_type)
        
        return jsonify({
            'success': True,
            'data': agents,
            'count': len(agents)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/create', methods=['POST'])
@require_admin
def create_agent():
    try:
        data = request.get_json() or {}
        agent_type = data.get('agent_type', 'base')
        name = data.get('name')
        config = data.get('config', {})
        
        if not name:
            return jsonify({'success': False, 'error': '请提供代理名称'}), 400
        
        agent = agent_factory.create_agent(agent_type, name, config)
        
        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type,
                'name': agent.name,
                'config': config
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/bulk_create', methods=['POST'])
@require_admin
def bulk_create_agents():
    try:
        data = request.get_json() or {}
        agents_data = data.get('agents', [])
        
        if not agents_data:
            return jsonify({'success': False, 'error': '请提供代理数据'}), 400
        
        created = agent_factory.bulk_create_agents(agents_data)
        
        return jsonify({
            'success': True,
            'data': created,
            'count': len(created)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/<agent_id>', methods=['GET'])
@require_admin
def get_agent(agent_id):
    try:
        agent = agent_factory.get_agent(agent_id)
        
        if not agent:
            return jsonify({'success': False, 'error': '代理不存在'}), 404
        
        state = agent.get_all_state()
        registry_info = agent.get_registry_info()
        
        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type,
                'name': agent.name,
                'status': registry_info.get('status') if registry_info else 'active',
                'state': state,
                'registry_info': registry_info
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/<agent_id>', methods=['PUT'])
@require_admin
def update_agent(agent_id):
    try:
        data = request.get_json() or {}
        config = data.get('config', {})
        
        success = agent_factory.update_agent_config(agent_id, config)
        
        if not success:
            return jsonify({'success': False, 'error': '代理不存在'}), 404
        
        agent = agent_factory.get_agent(agent_id)
        
        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type,
                'name': agent.name,
                'updated_config': config
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/<agent_id>', methods=['DELETE'])
@require_admin
def delete_agent(agent_id):
    try:
        agent_factory.delete_agent(agent_id)
        
        return jsonify({
            'success': True,
            'message': '代理删除成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/<agent_id>/state', methods=['GET'])
@require_admin
def get_agent_state(agent_id):
    try:
        state = agent_factory.get_agent_state(agent_id)
        
        if state is None:
            return jsonify({'success': False, 'error': '代理不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': state
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/<agent_id>/state', methods=['PUT'])
@require_admin
def set_agent_state(agent_id):
    try:
        data = request.get_json() or {}
        state_dict = data.get('state', {})
        
        success = agent_factory.set_agent_state(agent_id, state_dict)
        
        if not success:
            return jsonify({'success': False, 'error': '代理不存在'}), 404
        
        return jsonify({
            'success': True,
            'message': '代理状态更新成功',
            'updated_keys': list(state_dict.keys())
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/<agent_id>/state/<key>', methods=['GET'])
@require_admin
def get_agent_state_key(agent_id, key):
    try:
        agent = agent_factory.get_agent(agent_id)
        
        if not agent:
            return jsonify({'success': False, 'error': '代理不存在'}), 404
        
        value = getattr(agent, key, None)
        
        return jsonify({
            'success': True,
            'data': {
                'key': key,
                'value': value
            }
        })
    except AttributeError:
        return jsonify({'success': False, 'error': f'属性 {key} 不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/<agent_id>/state/<key>', methods=['PUT'])
@require_admin
def set_agent_state_key(agent_id, key):
    try:
        agent = agent_factory.get_agent(agent_id)
        
        if not agent:
            return jsonify({'success': False, 'error': '代理不存在'}), 404
        
        data = request.get_json() or {}
        value = data.get('value')
        
        setattr(agent, key, value)
        
        return jsonify({
            'success': True,
            'data': {
                'key': key,
                'value': value
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/<agent_id>/state/<key>', methods=['DELETE'])
@require_admin
def delete_agent_state_key(agent_id, key):
    try:
        agent = agent_factory.get_agent(agent_id)
        
        if not agent:
            return jsonify({'success': False, 'error': '代理不存在'}), 404
        
        delattr(agent, key)
        
        return jsonify({
            'success': True,
            'message': f'属性 {key} 删除成功'
        })
    except AttributeError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/count', methods=['GET'])
@require_admin
def count_agents():
    try:
        agent_type = request.args.get('type')
        count = agent_factory.count_agents(agent_type=agent_type)
        
        return jsonify({
            'success': True,
            'data': {
                'count': count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/types', methods=['GET'])
@require_admin
def get_agent_types():
    try:
        types = agent_factory.get_agent_types()
        
        return jsonify({
            'success': True,
            'data': types
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/status/<agent_id>', methods=['PUT'])
@require_admin
def update_agent_status(agent_id):
    try:
        agent = agent_factory.get_agent(agent_id)
        
        if not agent:
            return jsonify({'success': False, 'error': '代理不存在'}), 404
        
        data = request.get_json() or {}
        status = data.get('status')
        
        if not status:
            return jsonify({'success': False, 'error': '请提供状态'}), 400
        
        agent.update_status(status)
        
        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent_id,
                'status': status
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_management_api.route('/api/agent/create_or_get', methods=['POST'])
@require_admin
def create_or_get_agent():
    try:
        data = request.get_json() or {}
        agent_type = data.get('agent_type', 'base')
        name = data.get('name')
        config = data.get('config', {})
        
        if not name:
            return jsonify({'success': False, 'error': '请提供代理名称'}), 400
        
        agent = agent_factory.create_or_get_agent(agent_type, name, config)
        
        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type,
                'name': agent.name,
                'created': not agent.get_registry_info() or agent.get_registry_info().get(
                'created_at') == agent.get_registry_info().get('updated_at')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500