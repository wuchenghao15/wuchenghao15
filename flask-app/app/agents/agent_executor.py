# -*- coding: utf-8 -*-
"""
本地Agent执行器
负责执行Agent的任务、调用工具、与LLM交互
"""

import os
import sys
import time
import json
import uuid
import threading
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class AgentExecutor:
    """Agent执行器"""
    
    def __init__(self, agent_code: str, config: Dict[str, Any] = None):
        self.agent_code = agent_code
        self.config = config or {}
        self._running = False
        self._task_queue: List[Dict] = []
        self._lock = threading.Lock()
        self._executor_thread = None
        self._context: Dict[str, Any] = {}
        self._tool_registry: Dict[str, Callable] = {}
        
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        self._tool_registry = {
            'system_status': self._tool_system_status,
            'file_read': self._tool_file_read,
            'file_write': self._tool_file_write,
            'shell_exec': self._tool_shell_exec,
            'api_call': self._tool_api_call,
            'database_query': self._tool_database_query,
            'web_search': self._tool_web_search,
            'code_exec': self._tool_code_exec,
            'math_calc': self._tool_math_calc,
            'text_summary': self._tool_text_summary,
            'ai_employee_dispatch': self._tool_ai_employee_dispatch,
            'ai_employee_collaborate': self._tool_ai_employee_collaborate,
            'ai_employee_status': self._tool_ai_employee_status,
            'ai_employee_message': self._tool_ai_employee_message
        }
    
    def register_tool(self, tool_name: str, tool_func: Callable):
        """注册自定义工具"""
        self._tool_registry[tool_name] = tool_func
        logger.info(f"工具已注册: {tool_name}")
    
    def start(self):
        """启动执行器"""
        if self._running:
            return
        
        self._running = True
        logger.info(f"Agent执行器已启动: {self.agent_code}")
        
        self._executor_thread = threading.Thread(target=self._execute_loop, daemon=True)
        self._executor_thread.start()
    
    def stop(self):
        """停止执行器"""
        self._running = False
        
        if self._executor_thread:
            self._executor_thread.join(timeout=5)
        
        logger.info(f"Agent执行器已停止: {self.agent_code}")
    
    def _execute_loop(self):
        """执行循环"""
        while self._running:
            try:
                task = self._get_next_task()
                
                if task:
                    self._execute_task(task)
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"执行循环异常: {e}")
                time.sleep(1)
    
    def _get_next_task(self) -> Optional[Dict]:
        """获取下一个任务"""
        with self._lock:
            if self._task_queue:
                return self._task_queue.pop(0)
            return None
    
    def submit_task(self, task_data: Dict[str, Any]):
        """提交任务"""
        with self._lock:
            self._task_queue.append(task_data)
            logger.info(f"任务已提交: {task_data.get('task_type', 'unknown')}")
    
    def _execute_task(self, task: Dict[str, Any]):
        """执行任务"""
        try:
            task_type = task.get('task_type', 'general')
            input_data = task.get('input_data', {})
            
            logger.info(f"开始执行任务: {task_type}")
            
            if task_type == 'chat':
                result = self._handle_chat(input_data)
            elif task_type == 'tool_call':
                result = self._handle_tool_call(input_data)
            elif task_type == 'code_execution':
                result = self._handle_code_execution(input_data)
            elif task_type == 'data_analysis':
                result = self._handle_data_analysis(input_data)
            else:
                result = self._handle_general_task(input_data)
            
            logger.info(f"任务执行完成: {task_type}, 成功: {result.get('success', False)}")
            
            return result
        
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_chat(self, input_data: Dict) -> Dict[str, Any]:
        """处理聊天任务"""
        try:
            messages = input_data.get('messages', [])
            context = input_data.get('context', {})
            
            response = self._generate_response(messages, context)
            
            return {
                'success': True,
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_tool_call(self, input_data: Dict) -> Dict[str, Any]:
        """处理工具调用"""
        try:
            tool_name = input_data.get('tool_name')
            tool_args = input_data.get('args', {})
            
            if tool_name not in self._tool_registry:
                return {
                    'success': False,
                    'error': f"工具不存在: {tool_name}"
                }
            
            result = self._tool_registry[tool_name](**tool_args)
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_code_execution(self, input_data: Dict) -> Dict[str, Any]:
        """处理代码执行"""
        try:
            code = input_data.get('code', '')
            language = input_data.get('language', 'python')
            
            if language == 'python':
                result = self._execute_python_code(code)
            else:
                result = self._execute_other_code(code, language)
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_data_analysis(self, input_data: Dict) -> Dict[str, Any]:
        """处理数据分析"""
        try:
            data = input_data.get('data', {})
            analysis_type = input_data.get('analysis_type', 'summary')
            
            if analysis_type == 'summary':
                result = self._analyze_summary(data)
            elif analysis_type == 'statistics':
                result = self._analyze_statistics(data)
            elif analysis_type == 'trend':
                result = self._analyze_trend(data)
            else:
                result = self._analyze_general(data)
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_general_task(self, input_data: Dict) -> Dict[str, Any]:
        """处理通用任务"""
        try:
            prompt = input_data.get('prompt', '')
            context = input_data.get('context', {})
            
            response = self._generate_response([{'role': 'user', 'content': prompt}], context)
            
            return {
                'success': True,
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_response(self, messages: List[Dict], context: Dict = None) -> str:
        """生成响应"""
        try:
            from ai_engines.ai_engine_service import AIEngineService
            
            ai_engine = AIEngineService()
            
            system_prompt = self._build_system_prompt()
            
            response = ai_engine.call_engine(
                engine_type='local',
                prompt=system_prompt,
                messages=messages
            )
            
            if response and isinstance(response, dict):
                return response.get('content', '') or str(response)
            
            return str(response) if response else "抱歉，我无法回答这个问题。"
        
        except Exception as e:
            logger.error(f"生成响应失败: {e}")
            return f"生成响应时出错: {str(e)}"
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_desc = "\n".join([
            f"- {name}: {self._get_tool_description(name)}"
            for name in self._tool_registry.keys()
        ])
        
        return f"""你是一个智能Agent，名为"{self.agent_code}"。

配置: {json.dumps(self.config, ensure_ascii=False)}

可用工具:
{tools_desc}

当你需要执行操作时，请使用工具调用格式。
请以友好、专业的方式回答用户问题。
"""
    
    def _get_tool_description(self, tool_name: str) -> str:
        """获取工具描述"""
        descriptions = {
            'system_status': '获取系统状态信息',
            'file_read': '读取文件内容',
            'file_write': '写入文件内容',
            'shell_exec': '执行Shell命令',
            'api_call': '调用API接口',
            'database_query': '执行数据库查询',
            'web_search': '执行网络搜索',
            'code_exec': '执行代码',
            'math_calc': '数学计算',
            'text_summary': '文本摘要',
            'ai_employee_dispatch': '调用AI员工执行任务',
            'ai_employee_collaborate': '创建多AI员工协作任务',
            'ai_employee_status': '获取AI员工协作状态',
            'ai_employee_message': '向AI员工发送消息'
        }
        return descriptions.get(tool_name, '未知工具')
    
    def _execute_python_code(self, code: str) -> str:
        """执行Python代码"""
        try:
            local_vars = {}
            exec(code, {}, local_vars)
            
            if local_vars:
                return json.dumps(local_vars, ensure_ascii=False, default=str)
            
            return "代码执行成功，无返回值"
        
        except Exception as e:
            return f"代码执行失败: {str(e)}"
    
    def _execute_other_code(self, code: str, language: str) -> str:
        """执行其他语言代码"""
        return f"暂不支持执行{language}代码"
    
    def _analyze_summary(self, data: Dict) -> Dict:
        """数据摘要分析"""
        try:
            summary = {
                'total_records': len(data) if isinstance(data, list) else 'N/A',
                'keys': list(data.keys()) if isinstance(data, dict) else 'N/A',
                'data_type': type(data).__name__,
                'summary': '数据摘要分析完成'
            }
            return summary
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_statistics(self, data: Dict) -> Dict:
        """统计分析"""
        try:
            statistics = {
                'analysis_type': 'statistics',
                'count': len(data) if isinstance(data, (list, dict)) else 'N/A',
                'statistics': '统计分析完成'
            }
            return statistics
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_trend(self, data: Dict) -> Dict:
        """趋势分析"""
        try:
            trend = {
                'analysis_type': 'trend',
                'trend': '趋势分析完成'
            }
            return trend
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_general(self, data: Dict) -> Dict:
        """通用分析"""
        try:
            analysis = {
                'analysis_type': 'general',
                'analysis': '通用分析完成'
            }
            return analysis
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_system_status(self) -> Dict:
        """系统状态工具"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_total': f"{memory.total / 1024 ** 3:.2f} GB",
                'memory_available': f"{memory.available / 1024 ** 3:.2f} GB",
                'disk_usage': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids())
            }
        except ImportError:
            return {'error': 'psutil模块未安装'}
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_file_read(self, file_path: str) -> Dict:
        """文件读取工具"""
        try:
            if not os.path.exists(file_path):
                return {'error': f"文件不存在: {file_path}"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'file_path': file_path,
                'content': content[:5000] if len(content) > 5000 else content,
                'truncated': len(content) > 5000
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_file_write(self, file_path: str, content: str, append: bool = False) -> Dict:
        """文件写入工具"""
        try:
            mode = 'a' if append else 'w'
            
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'file_path': file_path,
                'written_bytes': len(content)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_shell_exec(self, command: str) -> Dict:
        """Shell命令执行工具"""
        try:
            import subprocess
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': '命令执行超时'}
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_api_call(self, url: str, method: str = 'GET', headers: Dict = None, data: Dict = None) -> Dict:
        """API调用工具"""
        try:
            import requests
            
            headers = headers or {}
            data = data or {}
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            try:
                response_json = response.json()
            except ValueError:
                response_json = response.text
            
            return {
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'response': response_json
            }
        except ImportError:
            return {'error': 'requests模块未安装'}
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_database_query(self, query: str, db_path: str = None) -> Dict:
        """数据库查询工具"""
        try:
            import sqlite3
            
            db_path = db_path or os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'app.db'
            )
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                result = {
                    'columns': columns,
                    'rows': rows,
                    'count': len(rows)
                }
            else:
                conn.commit()
                result = {
                    'affected_rows': cursor.rowcount,
                    'message': '查询执行成功'
                }
            
            conn.close()
            
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_web_search(self, query: str) -> Dict:
        """网络搜索工具"""
        try:
            return {
                'query': query,
                'results': [
                    {'title': '搜索结果1', 'url': 'https://example.com', 'summary': '这是搜索结果摘要'}
                ],
                'message': '网络搜索功能需要额外配置'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_code_exec(self, code: str, language: str = 'python') -> Dict:
        """代码执行工具"""
        try:
            if language == 'python':
                result = self._execute_python_code(code)
            else:
                result = f"暂不支持{language}语言"
            
            return {
                'language': language,
                'code': code,
                'result': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_math_calc(self, expression: str) -> Dict:
        """数学计算工具"""
        try:
            result = eval(expression)
            
            return {
                'expression': expression,
                'result': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_text_summary(self, text: str, max_length: int = 200) -> Dict:
        """文本摘要工具"""
        try:
            if len(text) <= max_length:
                summary = text
            else:
                summary = text[:max_length] + '...'
            
            return {
                'original_length': len(text),
                'summary_length': len(summary),
                'summary': summary
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_ai_employee_dispatch(self, task_type: str, task_data: Dict = None, 
                                   employee_template: str = None) -> Dict:
        """调用AI员工执行任务"""
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            
            task = {
                'task_type': task_type,
                'task_data': task_data or {},
                'agent_code': self.agent_code,
                'timestamp': datetime.now().isoformat()
            }
            
            result = integration.dispatch_task_to_employee(
                self.agent_code,
                task,
                employee_template
            )
            
            return result
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tool_ai_employee_collaborate(self, task_type: str, task_data: Dict = None,
                                        employee_templates: List[str] = None) -> Dict:
        """创建多AI员工协作任务"""
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            
            employee_templates = employee_templates or ['code_fixer', 'data_analyzer']
            
            task = {
                'task_type': task_type,
                'task_data': task_data or {},
                'agent_code': self.agent_code,
                'timestamp': datetime.now().isoformat()
            }
            
            result = integration.create_multi_agent_collaboration(
                self.agent_code,
                task,
                employee_templates
            )
            
            return result
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tool_ai_employee_status(self, session_id: str = None) -> Dict:
        """获取AI员工协作状态"""
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            
            if session_id:
                result = integration.get_collaboration_status(session_id)
            else:
                result = integration.get_active_collaborations()
            
            return result
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _tool_ai_employee_message(self, to_employee_id: str, message_type: str = 'knowledge_share',
                                    content: Dict = None) -> Dict:
        """向AI员工发送消息"""
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            
            message = {
                'type': message_type,
                'content': content or {},
                'from': self.agent_code,
                'timestamp': datetime.now().isoformat()
            }
            
            result = integration.send_message_between_agents(
                self.agent_code,
                to_employee_id,
                message
            )
            
            return result
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态"""
        return {
            'running': self._running,
            'agent_code': self.agent_code,
            'pending_tasks': len(self._task_queue),
            'registered_tools': list(self._tool_registry.keys()),
            'context_keys': list(self._context.keys())
        }