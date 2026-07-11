# -*- coding: utf-8 -*-
"""
Agent-AI员工集成模块
实现Agent助手与AI员工系统的协同工作
"""

import json
import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AgentAIEmployeeIntegration:
    """Agent与AI员工集成控制器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._active_collaborations = {}
        self._task_mapping = {}
        self._ai_employee_cache = {}
        self._agent_cache = {}
        
    def get_ai_employee_system(self):
        """获取AI员工增强系统"""
        try:
            from app.ai.ai_employee_enhanced_system import get_enhanced_system
            return get_enhanced_system()
        except Exception as e:
            logger.error(f"获取AI员工系统失败: {e}")
            return None
    
    def get_agent_manager(self):
        """获取Agent管理器"""
        try:
            from app.agents.agent_manager import get_agent_manager
            return get_agent_manager()
        except Exception as e:
            logger.error(f"获取Agent管理器失败: {e}")
            return None
    
    def find_best_employee_for_task(self, task_type: str, task_context: Dict = None) -> Optional[str]:
        """根据任务类型找到最合适的AI员工模板名称"""
        task_context = task_context or {}
        
        employee_system = self.get_ai_employee_system()
        if not employee_system:
            return None
        
        employee_templates = employee_system.generator.EMPLOYEE_TEMPLATES
        
        task_template_mapping = {
            'code_fix': ['code_fixer'],
            'data_analysis': ['data_analyzer'],
            'security_scan': ['security_guard'],
            'performance': ['performance_optimizer'],
            'quality_assurance': ['qa_validator'],
            'knowledge_management': ['knowledge_manager'],
            'task_coordination': ['coordinator'],
            'system_maintenance': ['system_maintenance'],
            'general': ['code_fixer', 'data_analyzer']
        }
        
        best_templates = task_template_mapping.get(task_type, task_template_mapping['general'])
        
        for template_key in best_templates:
            template = employee_templates.get(template_key)
            if template:
                return template_key
        
        return None
    
    def dispatch_task_to_employee(self, agent_code: str, task: Dict, 
                                   employee_template: str = None) -> Dict:
        """将任务分派给AI员工"""
        try:
            employee_system = self.get_ai_employee_system()
            if not employee_system:
                return {'success': False, 'error': 'AI员工系统未初始化'}
            
            if not employee_template:
                employee_template = self.find_best_employee_for_task(
                    task.get('task_type', 'general')
                )
                if not employee_template:
                    employee_template = 'code_fixer'
            
            generation_result = employee_system.create_full_employee(
                employee_template,
                level='specialist'
            )
            
            if not generation_result['success']:
                return generation_result
            
            employee = generation_result['employee']
            employee_id = employee['employee_id']
            
            collaboration_result = employee_system.assign_collaborative_task(
                task,
                [employee_id]
            )
            
            if not collaboration_result['success']:
                return collaboration_result
            
            session_id = collaboration_result['session_id']
            
            with self._lock:
                self._active_collaborations[session_id] = {
                    'session_id': session_id,
                    'agent_code': agent_code,
                    'employee_id': employee_id,
                    'employee_name': employee['name'],
                    'task': task,
                    'status': 'in_progress',
                    'created_at': datetime.now().isoformat(),
                    'collaboration_result': collaboration_result
                }
            
            return {
                'success': True,
                'session_id': session_id,
                'employee_id': employee_id,
                'employee_name': employee['name'],
                'message': f"任务已分派给AI员工: {employee['name']}"
            }
        
        except Exception as e:
            logger.error(f"分派任务给AI员工失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def delegate_task_to_agent(self, employee_id: str, task: Dict, 
                                agent_code: str = None) -> Dict:
        """AI员工将任务委派给Agent"""
        try:
            agent_manager = self.get_agent_manager()
            if not agent_manager:
                return {'success': False, 'error': 'Agent管理器未初始化'}
            
            if not agent_code:
                agents = agent_manager.get_all_agents()
                if agents:
                    agent_code = agents[0].agent_code
                else:
                    return {'success': False, 'error': '无可用Agent'}
            
            task_id = agent_manager.submit_task(agent_code, task)
            
            return {
                'success': True,
                'task_id': task_id,
                'agent_code': agent_code,
                'message': f"任务已委派给Agent: {agent_code}"
            }
        
        except Exception as e:
            logger.error(f"委派任务给Agent失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_multi_agent_collaboration(self, agent_code: str, task: Dict, 
                                         employee_templates: List[str]) -> Dict:
        """创建多AI员工协作任务"""
        try:
            employee_system = self.get_ai_employee_system()
            if not employee_system:
                return {'success': False, 'error': 'AI员工系统未初始化'}
            
            participants = []
            
            for template in employee_templates:
                generation_result = employee_system.create_full_employee(
                    template,
                    level='specialist'
                )
                
                if generation_result['success']:
                    participants.append(generation_result['employee']['employee_id'])
                else:
                    logger.warning(f"创建AI员工失败: {template}")
            
            if not participants:
                return {'success': False, 'error': '未能创建任何AI员工'}
            
            collaboration_result = employee_system.assign_collaborative_task(
                task,
                participants
            )
            
            if collaboration_result['success']:
                session_id = collaboration_result['session_id']
                
                with self._lock:
                    self._active_collaborations[session_id] = {
                        'session_id': session_id,
                        'agent_code': agent_code,
                        'participants': participants,
                        'task': task,
                        'status': 'collaborating',
                        'created_at': datetime.now().isoformat(),
                        'collaboration_result': collaboration_result
                    }
            
            return collaboration_result
        
        except Exception as e:
            logger.error(f"创建多AI员工协作失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_collaboration_status(self, session_id: str) -> Dict:
        """获取协作状态"""
        try:
            with self._lock:
                collaboration = self._active_collaborations.get(session_id)
            
            if not collaboration:
                return {'success': False, 'error': '协作会话不存在'}
            
            employee_system = self.get_ai_employee_system()
            if employee_system:
                report = employee_system.collaboration.get_collaboration_report(session_id)
                if report.get('success', True):
                    collaboration['report'] = report.get('session', {})
            
            return {
                'success': True,
                'collaboration': collaboration
            }
        
        except Exception as e:
            logger.error(f"获取协作状态失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def complete_collaboration(self, session_id: str, results: Dict = None) -> Dict:
        """完成协作并汇总结果"""
        try:
            with self._lock:
                collaboration = self._active_collaborations.get(session_id)
            
            if not collaboration:
                return {'success': False, 'error': '协作会话不存在'}
            
            results = results or {}
            
            collaboration['status'] = 'completed'
            collaboration['results'] = results
            collaboration['completed_at'] = datetime.now().isoformat()
            
            with self._lock:
                self._active_collaborations[session_id] = collaboration
            
            return {
                'success': True,
                'session_id': session_id,
                'collaboration': collaboration,
                'message': '协作已完成'
            }
        
        except Exception as e:
            logger.error(f"完成协作失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_active_collaborations(self) -> List[Dict]:
        """获取所有活跃的协作会话"""
        try:
            with self._lock:
                collaborations = list(self._active_collaborations.values())
            
            return {
                'success': True,
                'collaborations': collaborations,
                'total': len(collaborations)
            }
        
        except Exception as e:
            logger.error(f"获取活跃协作失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_message_between_agents(self, from_agent_code: str, 
                                     to_employee_id: str, message: Dict) -> Dict:
        """在Agent和AI员工之间发送消息"""
        try:
            employee_system = self.get_ai_employee_system()
            if not employee_system:
                return {'success': False, 'error': 'AI员工系统未初始化'}
            
            message_type = message.get('type', 'knowledge_share')
            content = message.get('content', {})
            
            result = employee_system.collaboration.send_message(
                from_agent_code,
                to_employee_id,
                message_type,
                content
            )
            
            return result
        
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_employee_messages(self, employee_id: str) -> Dict:
        """获取AI员工的消息"""
        try:
            employee_system = self.get_ai_employee_system()
            if not employee_system:
                return {'success': False, 'error': 'AI员工系统未初始化'}
            
            messages = employee_system.collaboration.receive_messages(employee_id)
            
            return {
                'success': True,
                'messages': messages,
                'total': len(messages)
            }
        
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_combined_system_status(self) -> Dict:
        """获取Agent和AI员工系统的综合状态"""
        try:
            status = {}
            
            agent_manager = self.get_agent_manager()
            if agent_manager:
                agent_status = agent_manager.get_system_status()
                status['agent_system'] = agent_status
            
            employee_system = self.get_ai_employee_system()
            if employee_system:
                employee_status = employee_system.get_system_status()
                status['employee_system'] = employee_status
            
            with self._lock:
                status['active_collaborations'] = len(self._active_collaborations)
            
            return {
                'success': True,
                'status': status
            }
        
        except Exception as e:
            logger.error(f"获取综合状态失败: {e}")
            return {'success': False, 'error': str(e)}


_integration_instance = None

def get_integration():
    """获取集成控制器实例"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = AgentAIEmployeeIntegration()
    return _integration_instance

def init_integration():
    """初始化集成控制器"""
    integration = get_integration()
    logger.info("[Agent-AI员工集成] 集成控制器初始化完成")
    return integration