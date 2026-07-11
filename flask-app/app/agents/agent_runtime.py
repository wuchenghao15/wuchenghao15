# -*- coding: utf-8 -*-
"""
AgentRuntime - Agent运行时载体
支持私有化本地Agent(LangGraph)和云端托管Agent(Claude/GPT4o/豆包)
"""
import json
import logging
import os
import threading
from datetime import datetime
from typing import Dict, Any, List, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AgentRuntime(ABC):
    """Agent运行时基类"""
    
    def __init__(self, runtime_type: str, name: str):
        self.runtime_type = runtime_type
        self.name = name
        self.status = 'idle'
        self.last_execution = None
        self.execution_count = 0
    
    @abstractmethod
    def execute(self, task: Dict) -> Dict:
        """执行任务"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict:
        """获取状态"""
        pass
    
    def report_result(self, task_id: str, status: str, data: Dict = None):
        """上报结果到数据库"""
        try:
            from app.utils.db import db_manager
            
            db_manager.create_table('agent_runtime_tasks', {
                'task_id': 'TEXT PRIMARY KEY',
                'runtime_type': 'TEXT',
                'runtime_name': 'TEXT',
                'status': 'TEXT',
                'data': 'TEXT',
                'created_at': 'TEXT',
                'updated_at': 'TEXT'
            })
            
            now = datetime.now().isoformat()
            task_data = {
                'task_id': task_id,
                'runtime_type': self.runtime_type,
                'runtime_name': self.name,
                'status': status,
                'data': json.dumps(data or {}, ensure_ascii=False),
                'created_at': now,
                'updated_at': now
            }
            
            existing = db_manager.fetch_one(
                'SELECT task_id FROM agent_runtime_tasks WHERE task_id = ?',
                (task_id,)
            )
            
            if existing:
                db_manager.update(
                    'agent_runtime_tasks',
                    {k: v for k, v in task_data.items() if k != 'task_id'},
                    'task_id = ?',
                    (task_id,)
                )
            else:
                db_manager.insert('agent_runtime_tasks', task_data)
                
            logger.info(f"[{self.name}] 上报结果成功: {task_id}")
        except Exception as e:
            logger.error(f"[{self.name}] 上报结果失败: {e}")


class LocalLangGraphRuntime(AgentRuntime):
    """本地LangGraph Agent运行时"""
    
    def __init__(self):
        super().__init__('local', 'LangGraph本地Agent')
        self.graph = None
        self.tools = {}
        self.state = {}
        self._init_graph()
    
    def _init_graph(self):
        """初始化LangGraph图"""
        try:
            from langgraph.graph import StateGraph, END
            from langgraph.checkpoint.memory import MemorySaver
            
            class AgentState:
                messages: List[Dict] = []
                task: Dict = {}
                result: Dict = {}
            
            self.graph = StateGraph(AgentState)
            
            self.graph.add_node('task_analyzer', self._task_analyzer_node)
            self.graph.add_node('tool_executor', self._tool_executor_node)
            self.graph.add_node('result_summarizer', self._result_summarizer_node)
            
            self.graph.add_edge('task_analyzer', 'tool_executor')
            self.graph.add_edge('tool_executor', 'result_summarizer')
            self.graph.add_edge('result_summarizer', END)
            
            self.graph.set_entry_point('task_analyzer')
            
            self.graph = self.graph.compile(checkpointer=MemorySaver())
            
            logger.info("[LangGraph] 本地Agent图初始化完成")
        except ImportError as e:
            logger.warning(f"[LangGraph] 初始化失败(未安装langgraph): {e}")
    
    def _task_analyzer_node(self, state):
        """任务分析节点"""
        task = state.get('task', {})
        task_type = task.get('type', 'unknown')
        
        analysis = {
            'task_type': task_type,
            'params': task.get('params', {}),
            'tools_needed': self._determine_tools(task_type),
            'analysis_time': datetime.now().isoformat()
        }
        
        return {**state, 'messages': state.get('messages', []) + [analysis]}
    
    def _tool_executor_node(self, state):
        """工具执行节点"""
        messages = state.get('messages', [])
        task = state.get('task', {})
        
        tool_results = []
        
        if self.graph:
            tools_needed = messages[-1].get('tools_needed', [])
            
            for tool_name in tools_needed[:3]:
                tool = self.tools.get(tool_name)
                if tool:
                    try:
                        result = tool(task.get('params', {}))
                        tool_results.append({
                            'tool': tool_name,
                            'success': True,
                            'result': result
                        })
                    except Exception as e:
                        tool_results.append({
                            'tool': tool_name,
                            'success': False,
                            'error': str(e)
                        })
        
        return {**state, 'messages': messages + [{'tool_results': tool_results}]}
    
    def _result_summarizer_node(self, state):
        """结果汇总节点"""
        messages = state.get('messages', [])
        tool_results = messages[-1].get('tool_results', [])
        
        summary = {
            'success': all(r.get('success') for r in tool_results),
            'tool_results': tool_results,
            'summary': self._generate_summary(tool_results),
            'completed_at': datetime.now().isoformat()
        }
        
        return {**state, 'result': summary}
    
    def _determine_tools(self, task_type: str) -> List[str]:
        """确定需要的工具"""
        tool_mapping = {
            'code_analysis': ['code_debug', 'security_scan'],
            'bug_fix': ['code_debug', 'auto_fix', 'github_commit'],
            'ops_inspection': ['system_monitor', 'database_check'],
            'version_upgrade': ['version_check', 'backup', 'deploy'],
            'data_analysis': ['database_query', 'report_generator']
        }
        return tool_mapping.get(task_type, ['default_tool'])
    
    def _generate_summary(self, tool_results: List[Dict]) -> str:
        """生成摘要"""
        success_count = sum(1 for r in tool_results if r.get('success'))
        total_count = len(tool_results)
        
        if total_count == 0:
            return '无工具执行结果'
        elif success_count == total_count:
            return f'所有工具执行成功 ({success_count}/{total_count})'
        else:
            return f'部分工具执行失败 ({success_count}/{total_count})'
    
    def register_tool(self, tool_name: str, tool_func: Callable):
        """注册工具"""
        self.tools[tool_name] = tool_func
        logger.info(f"[LangGraph] 已注册工具: {tool_name}")
    
    def execute(self, task: Dict) -> Dict:
        """执行任务"""
        self.status = 'running'
        self.execution_count += 1
        self.last_execution = datetime.now()
        
        try:
            if not self.graph:
                return {
                    'success': False,
                    'error': 'LangGraph未初始化，请安装langgraph库',
                    'runtime': self.name
                }
            
            config = {"configurable": {"thread_id": f"thread_{datetime.now().timestamp()}"}}
            result = self.graph.invoke({'task': task}, config)
            
            final_result = result.get('result', {})
            
            self.report_result(task.get('task_id', 'unknown'), 
                             'completed' if final_result.get('success') else 'failed',
                             final_result)
            
            self.status = 'idle'
            
            return {
                'success': final_result.get('success', False),
                'result': final_result,
                'runtime': self.name,
                'execution_count': self.execution_count
            }
        
        except Exception as e:
            self.status = 'error'
            self.report_result(task.get('task_id', 'unknown'), 'failed', {'error': str(e)})
            
            return {
                'success': False,
                'error': str(e),
                'runtime': self.name
            }
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'runtime_type': self.runtime_type,
            'name': self.name,
            'status': self.status,
            'execution_count': self.execution_count,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'tools_registered': list(self.tools.keys()),
            'graph_initialized': self.graph is not None
        }


class CloudAgentRuntime(AgentRuntime):
    """云端Agent运行时基类"""
    
    def __init__(self, provider: str, name: str, api_key_env: str):
        super().__init__('cloud', name)
        self.provider = provider
        self.api_key = os.environ.get(api_key_env)
        self.api_url = ''
        self.initialized = False
    
    def _init_client(self):
        """初始化客户端"""
        pass
    
    def execute(self, task: Dict) -> Dict:
        """执行任务"""
        self.status = 'running'
        self.execution_count += 1
        self.last_execution = datetime.now()
        
        if not self.api_key:
            self.status = 'error'
            return {
                'success': False,
                'error': f'{self.provider} API密钥未设置',
                'runtime': self.name
            }
        
        try:
            result = self._call_api(task)
            
            self.report_result(task.get('task_id', 'unknown'), 
                             'completed' if result.get('success') else 'failed',
                             result)
            
            self.status = 'idle'
            
            return {
                'success': result.get('success', False),
                'result': result,
                'runtime': self.name,
                'provider': self.provider
            }
        
        except Exception as e:
            self.status = 'error'
            return {
                'success': False,
                'error': str(e),
                'runtime': self.name,
                'provider': self.provider
            }
    
    def _call_api(self, task: Dict) -> Dict:
        """调用云端API"""
        return {'success': False, 'error': '未实现'}
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'runtime_type': self.runtime_type,
            'name': self.name,
            'provider': self.provider,
            'status': self.status,
            'api_key_configured': self.api_key is not None,
            'execution_count': self.execution_count,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None
        }


class ClaudeAgentRuntime(CloudAgentRuntime):
    """Claude Agent运行时"""
    
    def __init__(self):
        super().__init__('claude', 'Claude Agent', 'ANTHROPIC_API_KEY')
        self.api_url = 'https://api.anthropic.com/v1/messages'
    
    def _call_api(self, task: Dict) -> Dict:
        """调用Claude API"""
        try:
            import requests
            
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key,
                'Anthropic-Version': '2023-06-01'
            }
            
            payload = {
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 4096,
                'messages': [
                    {
                        'role': 'user',
                        'content': json.dumps(task, ensure_ascii=False)
                    }
                ]
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('content', [])[0].get('text', '')
                
                try:
                    result = json.loads(content)
                    return {'success': True, 'response': result}
                except json.JSONDecodeError:
                    return {'success': True, 'response': {'text': content}}
            
            return {'success': False, 'error': f'API返回错误: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


class GPT4oAgentRuntime(CloudAgentRuntime):
    """GPT-4o Agent运行时"""
    
    def __init__(self):
        super().__init__('gpt4o', 'GPT-4o Agent', 'OPENAI_API_KEY')
        self.api_url = 'https://api.openai.com/v1/chat/completions'
    
    def _call_api(self, task: Dict) -> Dict:
        """调用GPT-4o API"""
        try:
            import requests
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            payload = {
                'model': 'gpt-4o',
                'max_tokens': 4096,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是一个智能Agent，负责执行各种任务并返回JSON格式的结果。'
                    },
                    {
                        'role': 'user',
                        'content': json.dumps(task, ensure_ascii=False)
                    }
                ],
                'response_format': {'type': 'json_object'}
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [])[0].get('message', {}).get('content', '')
                
                try:
                    result = json.loads(content)
                    return {'success': True, 'response': result}
                except json.JSONDecodeError:
                    return {'success': True, 'response': {'text': content}}
            
            return {'success': False, 'error': f'API返回错误: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


class DoubaoAgentRuntime(CloudAgentRuntime):
    """豆包企业版Agent运行时"""
    
    def __init__(self):
        super().__init__('doubao', '豆包企业版Agent', 'DOUBAO_API_KEY')
        self.api_url = 'https://api.doubao.com/v1/chat/completions'
    
    def _call_api(self, task: Dict) -> Dict:
        """调用豆包API"""
        try:
            import requests
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            payload = {
                'model': 'doubao-pro',
                'max_tokens': 4096,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是豆包企业版智能Agent，负责执行各种任务。'
                    },
                    {
                        'role': 'user',
                        'content': json.dumps(task, ensure_ascii=False)
                    }
                ]
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [])[0].get('message', {}).get('content', '')
                
                try:
                    result = json.loads(content)
                    return {'success': True, 'response': result}
                except json.JSONDecodeError:
                    return {'success': True, 'response': {'text': content}}
            
            return {'success': False, 'error': f'API返回错误: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


class AgentRuntimeManager:
    """Agent运行时管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.runtimes = {}
        self._init_runtimes()
    
    def _init_runtimes(self):
        """初始化所有运行时"""
        self.runtimes['local_langgraph'] = LocalLangGraphRuntime()
        self.runtimes['claude'] = ClaudeAgentRuntime()
        self.runtimes['gpt4o'] = GPT4oAgentRuntime()
        self.runtimes['doubao'] = DoubaoAgentRuntime()
        
        logger.info("[Agent运行时] 运行时管理器初始化完成")
    
    def get_runtime(self, runtime_id: str):
        """获取运行时"""
        return self.runtimes.get(runtime_id)
    
    def get_all_runtimes(self) -> Dict:
        """获取所有运行时状态"""
        return {k: v.get_status() for k, v in self.runtimes.items()}
    
    def execute_task(self, runtime_id: str, task: Dict) -> Dict:
        """执行任务"""
        runtime = self.runtimes.get(runtime_id)
        
        if not runtime:
            return {'success': False, 'error': f'运行时不存在: {runtime_id}'}
        
        return runtime.execute(task)
    
    def register_tool(self, tool_name: str, tool_func: Callable):
        """注册工具到所有本地运行时"""
        for runtime in self.runtimes.values():
            if isinstance(runtime, LocalLangGraphRuntime):
                runtime.register_tool(tool_name, tool_func)


def get_runtime_manager() -> AgentRuntimeManager:
    """获取运行时管理器实例"""
    return AgentRuntimeManager()


def init_runtime_manager():
    """初始化运行时管理器"""
    return get_runtime_manager()
