# -*- coding: utf-8 -*-
"""
CoreAgentsAPI - 核心Agent API蓝图
提供5大核心Agent的统一API接口
"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

core_agents_api = Blueprint('core_agents_api', __name__, url_prefix='/api/core-agents')


@core_agents_api.route('/agents', methods=['GET'])
def get_agents():
    """获取所有核心Agent状态"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        agents = orchestrator.get_all_agents()
        
        return jsonify({
            'success': True,
            'agents': agents
        })
    
    except Exception as e:
        logger.error(f"获取Agent状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/agent/<agent_type>', methods=['GET'])
def get_agent(agent_type):
    """获取单个Agent状态"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        agent = orchestrator.get_agent(agent_type)
        
        if not agent:
            return jsonify({'success': False, 'error': 'Agent不存在'}), 404
        
        return jsonify({
            'success': True,
            'agent': agent.get_status()
        })
    
    except Exception as e:
        logger.error(f"获取Agent状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/agent/<agent_type>/execute', methods=['POST'])
def execute_agent(agent_type):
    """执行单个Agent"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        agent = orchestrator.get_agent(agent_type)
        
        if not agent:
            return jsonify({'success': False, 'error': 'Agent不存在'}), 404
        
        context = request.get_json() or {}
        result = agent.execute(context)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"执行Agent失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/workflow/<workflow_type>', methods=['POST'])
def run_workflow(workflow_type):
    """运行工作流"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        result = orchestrator.run_workflow(workflow_type, context)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"运行工作流失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/workflow/full', methods=['POST'])
def run_full_workflow():
    """运行完整工作流"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        result = orchestrator.run_workflow('full')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"运行完整工作流失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/workflow/debug-fix', methods=['POST'])
def run_debug_fix_workflow():
    """运行调试修复工作流"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        result = orchestrator.run_workflow('debug_fix')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"运行调试修复工作流失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/workflow/ops-check', methods=['POST'])
def run_ops_check_workflow():
    """运行运维巡检工作流"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        result = orchestrator.run_workflow('ops_check')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"运行运维巡检工作流失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/workflow/upgrade', methods=['POST'])
def run_upgrade_workflow():
    """运行版本升级工作流"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        if context.get('action') == 'upgrade':
            result = orchestrator.run_workflow('upgrade', context)
        else:
            result = orchestrator.run_workflow('upgrade', {'action': 'check'})
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"运行版本升级工作流失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/workflow/architecture', methods=['POST'])
def run_architecture_workflow():
    """运行部署架构工作流"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        if context.get('action') == 'plan':
            result = orchestrator.run_workflow('architecture', context)
        else:
            result = orchestrator.run_workflow('architecture', {'action': 'discover'})
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"运行部署架构工作流失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/exception-capture', methods=['POST'])
def capture_exception():
    """手动触发异常捕捉"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        result = orchestrator._run_exception_capture(context)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"异常捕捉失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/code-debug', methods=['POST'])
def code_debug():
    """手动触发代码分析"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        result = orchestrator._run_code_debug(context)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"代码分析失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/auto-fix', methods=['POST'])
def auto_fix():
    """手动触发自动修复"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        result = orchestrator._run_auto_fix(context)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"自动修复失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/ops-inspection', methods=['POST'])
def ops_inspection():
    """手动触发运维巡检"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        result = orchestrator._run_ops_inspection(context)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"运维巡检失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/version-upgrade', methods=['POST'])
def version_upgrade():
    """手动触发版本升级"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        result = orchestrator._run_version_upgrade(context)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"版本升级失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_agents_api.route('/deployment-architecture', methods=['POST'])
def deployment_architecture():
    """手动触发部署架构分析"""
    try:
        from app.agents.agent_orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        context = request.get_json() or {}
        
        result = orchestrator._run_deployment_architecture(context)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"部署架构分析失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
