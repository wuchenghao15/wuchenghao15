# -*- coding: utf-8 -*-
"""
本地Agent管理器
负责管理本地Agent的注册、启动、停止、通信和任务调度
适配项目现有的DatabaseManager架构
"""

import os
import sys
import time
import json
import uuid
import threading
import logging
import subprocess
import signal
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models.local_agent import LocalAgent, AgentTask, AgentConversation, AgentStatus


class AgentManager:
    """本地Agent管理器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.running_agents: Dict[str, dict] = {}
        self.task_queue: List[dict] = []
        self.conversations: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._heartbeat_thread = None
        self._running = False
        
        self._load_agents_from_db()
    
    def _load_agents_from_db(self):
        """从数据库加载所有Agent"""
        try:
            agents = LocalAgent.get_all(self.db_manager)
            for agent in agents:
                agent_dict = agent.to_dict()
                if agent.status == AgentStatus.RUNNING.value:
                    self.running_agents[agent.agent_code] = {
                        'agent': agent_dict,
                        'process': None,
                        'start_time': None,
                        'last_heartbeat': None
                    }
            logger.info(f"已从数据库加载 {len(agents)} 个Agent")
        except Exception as e:
            logger.error(f"加载Agent失败: {e}")
    
    def start(self):
        """启动Agent管理器"""
        if self._running:
            return
        
        self._running = True
        logger.info("Agent管理器已启动")
        
        self._start_heartbeat_monitor()
    
    def stop(self):
        """停止Agent管理器"""
        if not self._running:
            return
        
        self._running = False
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        
        self.stop_all_agents()
        
        logger.info("Agent管理器已停止")
    
    def _start_heartbeat_monitor(self):
        """启动心跳监控线程"""
        def heartbeat_loop():
            while self._running:
                try:
                    self._check_agent_health()
                except Exception as e:
                    logger.error(f"心跳监控异常: {e}")
                time.sleep(30)
        
        self._heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
    
    def _check_agent_health(self):
        """检查Agent健康状态"""
        with self._lock:
            for agent_code, info in list(self.running_agents.items()):
                if info['process']:
                    try:
                        info['process'].poll()
                        if info['process'].returncode is not None:
                            logger.warning(f"Agent {agent_code} 进程已退出")
                            self._update_agent_status(agent_code, AgentStatus.STOPPED.value)
                            del self.running_agents[agent_code]
                    except Exception as e:
                        logger.error(f"检查Agent {agent_code} 状态失败: {e}")
    
    def register_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """注册新的Agent"""
        try:
            with self._lock:
                existing = LocalAgent.get_by_code(self.db_manager, agent_data.get('agent_code', ''))
                if existing:
                    return {
                        'success': False,
                        'message': f"Agent编号已存在: {agent_data.get('agent_code')}"
                    }
                
                agent_code = agent_data.get('agent_code') or f"AGENT_{uuid.uuid4().hex[:8].upper()}"
                
                new_agent = LocalAgent(
                    agent_name=agent_data['agent_name'],
                    agent_code=agent_code,
                    agent_type=agent_data.get('agent_type', 'user'),
                    description=agent_data.get('description', ''),
                    config=agent_data.get('config', {}),
                    capabilities=agent_data.get('capabilities', []),
                    tools=agent_data.get('tools', []),
                    llm_model=agent_data.get('llm_model', 'local'),
                    temperature=agent_data.get('temperature', 0.7),
                    requires_auth=agent_data.get('requires_auth', True),
                    allowed_roles=agent_data.get('allowed_roles', []),
                    created_by=agent_data.get('created_by')
                )
                
                new_agent.save(self.db_manager)
                
                logger.info(f"新Agent已注册: {agent_code}")
                
                return {
                    'success': True,
                    'message': f"Agent注册成功: {agent_code}",
                    'agent': new_agent.to_dict()
                }
        
        except Exception as e:
            logger.error(f"注册Agent失败: {e}")
            return {
                'success': False,
                'message': f"注册失败: {str(e)}"
            }
    
    def get_agent(self, agent_code: str) -> Optional[Dict[str, Any]]:
        """获取Agent信息"""
        try:
            agent = LocalAgent.get_by_code(self.db_manager, agent_code)
            
            if not agent:
                return None
            
            result = agent.to_dict()
            
            if agent_code in self.running_agents:
                result['is_running'] = True
                result['process_id'] = self.running_agents[agent_code].get('process_id')
            else:
                result['is_running'] = False
            
            return result
        except Exception as e:
            logger.error(f"获取Agent失败: {e}")
            return None
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """获取所有Agent列表"""
        try:
            agents = LocalAgent.get_all(self.db_manager)
            result = []
            
            for agent in agents:
                agent_dict = agent.to_dict()
                
                if agent.agent_code in self.running_agents:
                    agent_dict['is_running'] = True
                    agent_dict['process_id'] = self.running_agents[agent.agent_code].get('process_id')
                else:
                    agent_dict['is_running'] = False
                
                result.append(agent_dict)
            
            return result
        except Exception as e:
            logger.error(f"获取Agent列表失败: {e}")
            return []
    
    def start_agent(self, agent_code: str) -> Dict[str, Any]:
        """启动Agent"""
        try:
            with self._lock:
                agent = LocalAgent.get_by_code(self.db_manager, agent_code)
                if not agent:
                    return {
                        'success': False,
                        'message': f"未找到Agent: {agent_code}"
                    }
                
                if agent_code in self.running_agents:
                    return {
                        'success': False,
                        'message': f"Agent {agent_code} 已在运行"
                    }
                
                agent.status = AgentStatus.INITIALIZING.value
                agent.save(self.db_manager)
                
                port = self._allocate_port()
                
                process = subprocess.Popen(
                    [sys.executable, '-m', 'app.agents.local_agent_runner', agent_code, str(port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                )
                
                self.running_agents[agent_code] = {
                    'agent': agent.to_dict(),
                    'process': process,
                    'port': port,
                    'start_time': datetime.now().isoformat(),
                    'last_heartbeat': datetime.now().isoformat()
                }
                
                agent.status = AgentStatus.RUNNING.value
                agent.process_id = process.pid
                agent.port = port
                agent.last_run_at = datetime.now().isoformat()
                agent.save(self.db_manager)
                
                logger.info(f"Agent {agent_code} 已启动, PID: {process.pid}, 端口: {port}")
                
                return {
                    'success': True,
                    'message': f"Agent {agent_code} 启动成功",
                    'process_id': process.pid,
                    'port': port
                }
        
        except Exception as e:
            logger.error(f"启动Agent失败: {e}")
            if agent:
                agent.status = AgentStatus.ERROR.value
                agent.save(self.db_manager)
            return {
                'success': False,
                'message': f"启动失败: {str(e)}"
            }
    
    def stop_agent(self, agent_code: str) -> Dict[str, Any]:
        """停止Agent"""
        try:
            with self._lock:
                if agent_code not in self.running_agents:
                    return {
                        'success': False,
                        'message': f"Agent {agent_code} 未在运行"
                    }
                
                info = self.running_agents[agent_code]
                process = info.get('process')
                
                if process:
                    try:
                        process.send_signal(signal.SIGTERM)
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.send_signal(signal.SIGKILL)
                        process.wait(timeout=2)
                
                del self.running_agents[agent_code]
                
                agent = LocalAgent.get_by_code(self.db_manager, agent_code)
                if agent:
                    agent.status = AgentStatus.STOPPED.value
                    agent.process_id = None
                    agent.port = None
                    agent.save(self.db_manager)
                
                logger.info(f"Agent {agent_code} 已停止")
                
                return {
                    'success': True,
                    'message': f"Agent {agent_code} 停止成功"
                }
        
        except Exception as e:
            logger.error(f"停止Agent失败: {e}")
            return {
                'success': False,
                'message': f"停止失败: {str(e)}"
            }
    
    def restart_agent(self, agent_code: str) -> Dict[str, Any]:
        """重启Agent"""
        try:
            self.stop_agent(agent_code)
            time.sleep(1)
            return self.start_agent(agent_code)
        except Exception as e:
            logger.error(f"重启Agent失败: {e}")
            return {
                'success': False,
                'message': f"重启失败: {str(e)}"
            }
    
    def stop_all_agents(self):
        """停止所有运行中的Agent"""
        for agent_code in list(self.running_agents.keys()):
            self.stop_agent(agent_code)
    
    def _allocate_port(self) -> int:
        """分配可用端口"""
        import socket
        
        for port in range(8001, 8100):
            if port not in [info.get('port') for info in self.running_agents.values()]:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if s.connect_ex(('localhost', port)) != 0:
                        return port
        
        return 8001
    
    def _update_agent_status(self, agent_code: str, status: str):
        """更新Agent状态"""
        try:
            agent = LocalAgent.get_by_code(self.db_manager, agent_code)
            if agent:
                agent.status = status
                agent.save(self.db_manager)
        except Exception as e:
            logger.error(f"更新Agent状态失败: {e}")
    
    def submit_task(self, agent_code: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """提交任务给Agent"""
        try:
            if agent_code not in self.running_agents:
                return {
                    'success': False,
                    'message': f"Agent {agent_code} 未在运行"
                }
            
            agent = LocalAgent.get_by_code(self.db_manager, agent_code)
            if not agent:
                return {
                    'success': False,
                    'message': f"未找到Agent: {agent_code}"
                }
            
            task_code = f"TASK_{uuid.uuid4().hex[:12].upper()}"
            
            task = AgentTask(
                task_code=task_code,
                agent_id=agent.id,
                task_type=task_data.get('task_type', 'general'),
                title=task_data.get('title', '未命名任务'),
                description=task_data.get('description', ''),
                input_data=task_data.get('input_data', {}),
                expected_output=task_data.get('expected_output', {}),
                priority=task_data.get('priority', 0),
                created_by=task_data.get('created_by')
            )
            
            task.save(self.db_manager)
            
            self.task_queue.append({
                'task_code': task_code,
                'agent_code': agent_code,
                'task_data': task_data
            })
            
            logger.info(f"任务已提交: {task_code} -> {agent_code}")
            
            return {
                'success': True,
                'message': f"任务提交成功: {task_code}",
                'task_code': task_code
            }
        
        except Exception as e:
            logger.error(f"提交任务失败: {e}")
            return {
                'success': False,
                'message': f"提交失败: {str(e)}"
            }
    
    def get_task_status(self, task_code: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            task = AgentTask.get_by_code(self.db_manager, task_code)
            if task:
                return task.to_dict()
            return None
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return None
    
    def create_conversation(self, agent_code: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """创建对话"""
        try:
            agent = LocalAgent.get_by_code(self.db_manager, agent_code)
            if not agent:
                return {
                    'success': False,
                    'message': f"未找到Agent: {agent_code}"
                }
            
            conversation_id = f"CONV_{uuid.uuid4().hex[:12].upper()}"
            
            conversation = AgentConversation(
                conversation_id=conversation_id,
                agent_id=agent.id,
                user_id=user_id,
                messages=[],
                context={},
                is_active=True
            )
            
            conversation.save(self.db_manager)
            
            self.conversations[conversation_id] = {
                'agent_code': agent_code,
                'messages': [],
                'context': {}
            }
            
            logger.info(f"新对话创建: {conversation_id} -> {agent_code}")
            
            return {
                'success': True,
                'message': f"对话创建成功",
                'conversation_id': conversation_id
            }
        
        except Exception as e:
            logger.error(f"创建对话失败: {e}")
            return {
                'success': False,
                'message': f"创建失败: {str(e)}"
            }
    
    def send_message(self, conversation_id: str, message: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """发送消息"""
        try:
            conversation = AgentConversation.get_by_id(self.db_manager, conversation_id)
            if not conversation:
                return {
                    'success': False,
                    'message': f"未找到对话: {conversation_id}"
                }
            
            agent = LocalAgent.get_by_code(self.db_manager, conversation_id.split('_')[0])
            if not agent:
                agent = LocalAgent.get_all(self.db_manager)
                if agent:
                    agent = agent[0]
            
            messages = conversation.messages.copy()
            messages.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id
            })
            
            conversation.messages = messages
            conversation.message_count = len(messages)
            conversation.last_message_at = datetime.now().isoformat()
            conversation.save(self.db_manager)
            
            if conversation_id in self.conversations:
                self.conversations[conversation_id]['messages'] = messages
            
            response = self._generate_agent_response(agent, messages)
            
            messages.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            conversation.messages = messages
            conversation.message_count = len(messages)
            conversation.last_message_at = datetime.now().isoformat()
            conversation.save(self.db_manager)
            
            return {
                'success': True,
                'message': '消息发送成功',
                'response': response,
                'message_count': len(messages)
            }
        
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return {
                'success': False,
                'message': f"发送失败: {str(e)}"
            }
    
    def _generate_agent_response(self, agent: LocalAgent, messages: List[Dict]) -> str:
        """生成Agent响应"""
        try:
            from ai_engines.ai_engine_service import AIEngineService
            
            ai_engine = AIEngineService()
            
            system_prompt = f"""你是一个名为"{agent.agent_name}"的AI助手。
            
描述: {agent.description}

能力: {', '.join(agent.capabilities or [])}

可用工具: {', '.join(agent.tools or [])}

请根据对话历史，以友好、专业的方式回答用户问题。
"""
            
            response = ai_engine.call_engine(
                engine_type='local',
                prompt=system_prompt,
                messages=messages
            )
            
            if response and isinstance(response, dict):
                return response.get('content', '') or str(response)
            
            return str(response) if response else "抱歉，我无法回答这个问题。"
        
        except Exception as e:
            logger.error(f"生成Agent响应失败: {e}")
            return f"抱歉，处理请求时出现错误: {str(e)}"
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取对话详情"""
        try:
            conversation = AgentConversation.get_by_id(self.db_manager, conversation_id)
            if conversation:
                return conversation.to_dict()
            return None
        except Exception as e:
            logger.error(f"获取对话失败: {e}")
            return None
    
    def get_conversations_by_agent(self, agent_code: str) -> List[Dict[str, Any]]:
        """获取Agent的所有对话"""
        try:
            agent = LocalAgent.get_by_code(self.db_manager, agent_code)
            if not agent:
                return []
            
            conversations = AgentConversation.get_by_agent(self.db_manager, agent.id)
            
            return [conv.to_dict() for conv in conversations]
        except Exception as e:
            logger.error(f"获取对话列表失败: {e}")
            return []
    
    def update_agent(self, agent_code: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Agent配置"""
        try:
            with self._lock:
                agent = LocalAgent.get_by_code(self.db_manager, agent_code)
                if not agent:
                    return {
                        'success': False,
                        'message': f"未找到Agent: {agent_code}"
                    }
                
                for key, value in update_data.items():
                    if hasattr(agent, key) and key not in ['id', 'agent_code', 'created_at']:
                        setattr(agent, key, value)
                
                agent.save(self.db_manager)
                
                if agent_code in self.running_agents:
                    self.running_agents[agent_code]['agent'] = agent.to_dict()
                
                logger.info(f"Agent {agent_code} 已更新")
                
                return {
                    'success': True,
                    'message': f"Agent {agent_code} 更新成功",
                    'agent': agent.to_dict()
                }
        
        except Exception as e:
            logger.error(f"更新Agent失败: {e}")
            return {
                'success': False,
                'message': f"更新失败: {str(e)}"
            }
    
    def delete_agent(self, agent_code: str) -> Dict[str, Any]:
        """删除Agent"""
        try:
            with self._lock:
                if agent_code in self.running_agents:
                    self.stop_agent(agent_code)
                
                agent = LocalAgent.get_by_code(self.db_manager, agent_code)
                if not agent:
                    return {
                        'success': False,
                        'message': f"未找到Agent: {agent_code}"
                    }
                
                tasks = self.db_manager.fetch_all(
                    f"SELECT * FROM {AgentTask.TABLE_NAME} WHERE agent_id = ?",
                    (agent.id,)
                )
                for task in tasks:
                    self.db_manager.delete(AgentTask.TABLE_NAME, 'id = ?', (task['id'],))
                
                conversations = self.db_manager.fetch_all(
                    f"SELECT * FROM {AgentConversation.TABLE_NAME} WHERE agent_id = ?",
                    (agent.id,)
                )
                for conv in conversations:
                    self.db_manager.delete(AgentConversation.TABLE_NAME, 'id = ?', (conv['id'],))
                
                agent.delete(self.db_manager)
                
                logger.info(f"Agent {agent_code} 已删除")
                
                return {
                    'success': True,
                    'message': f"Agent {agent_code} 删除成功"
                }
        
        except Exception as e:
            logger.error(f"删除Agent失败: {e}")
            return {
                'success': False,
                'message': f"删除失败: {str(e)}"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'manager_running': self._running,
            'total_agents': len(self.list_agents()),
            'running_agents': len(self.running_agents),
            'pending_tasks': len(self.task_queue),
            'active_conversations': len(self.conversations),
            'running_agent_list': list(self.running_agents.keys()),
            'timestamp': datetime.now().isoformat()
        }


_agent_manager_instance = None


def get_agent_manager(db_manager=None):
    """获取Agent管理器实例"""
    global _agent_manager_instance
    
    if _agent_manager_instance is None:
        if db_manager is None:
            try:
                from app.utils.db import db_manager as default_db_manager
                db_manager = default_db_manager
            except Exception as e:
                logger.error(f"无法获取默认数据库管理器: {e}")
                return None
        
        _agent_manager_instance = AgentManager(db_manager)
        _agent_manager_instance.start()
    
    return _agent_manager_instance