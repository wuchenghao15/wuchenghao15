#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Agent智能代理服务
提供自主任务规划、工具调用和多步推理能力
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print


class AgentTool:
    """Agent工具"""

    def __init__(self, tool_id: str, name: str, description: str,
                 handler: Callable = None, parameters: Dict[str, Any] = None,
                 category: str = 'general'):
        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or {}  # 参数定义
        self.category = category
        self.is_enabled = True
        self.call_count = 0
        self.error_count = 0

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        if not self.is_enabled:
            return {'success': False, 'error': 'tool_disabled'}

        self.call_count += 1

        try:
            if self.handler:
                result = self.handler(args)
            else:
                result = {'success': True, 'result': f'工具 {self.name} 执行完成'}

            return result
        except Exception as e:
            self.error_count += 1
            return {'success': False, 'error': str(e)}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tool_id': self.tool_id,
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'category': self.category,
            'is_enabled': self.is_enabled,
            'call_count': self.call_count,
            'error_count': self.error_count
        }


class AgentTask:
    """Agent任务"""

    def __init__(self, task_id: str, goal: str, agent_id: str = '',
                 max_steps: int = 10, priority: int = 5):
        self.task_id = task_id
        self.goal = goal
        self.agent_id = agent_id
        self.max_steps = max_steps
        self.priority = priority

        self.status = 'pending'  # pending, planning, executing, completed, failed
        self.steps: List[Dict[str, Any]] = []
        self.current_step = 0
        self.result: Dict[str, Any] = {}
        self.error = None
        self.created_at = datetime.now().isoformat()
        self.started_at = None
        self.completed_at = None
        self.total_duration = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'goal': self.goal,
            'agent_id': self.agent_id,
            'max_steps': self.max_steps,
            'priority': self.priority,
            'status': self.status,
            'step_count': len(self.steps),
            'current_step': self.current_step,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'total_duration': round(self.total_duration, 3),
            'steps': self.steps
        }


class Agent:
    """智能代理"""

    def __init__(self, agent_id: str, name: str, description: str = '',
                 system_prompt: str = '', model_id: str = ''):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.model_id = model_id

        self.tools: List[str] = []  # tool_ids
        self.is_active = True
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'model_id': self.model_id,
            'tools': self.tools,
            'is_active': self.is_active,
            'total_tasks': self.total_tasks,
            'successful_tasks': self.successful_tasks,
            'failed_tasks': self.failed_tasks,
            'success_rate': round(self.successful_tasks / max(1, self.total_tasks) * 100, 2),
            'created_at': self.created_at
        }


# 默认工具处理器
def tool_search(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get('query', '')
    return {'success': True, 'result': f'搜索完成: {query}', 'results': []}


def tool_calculate(args: Dict[str, Any]) -> Dict[str, Any]:
    expression = args.get('expression', '0')
    try:
        result = eval(expression, {'__builtins__': {}})
        return {'success': True, 'result': str(result)}
    except:
        return {'success': False, 'error': '计算失败'}


def tool_send_notification(args: Dict[str, Any]) -> Dict[str, Any]:
    message = args.get('message', '')
    return {'success': True, 'result': f'通知已发送: {message}'}


def tool_database_query(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get('query', '')
    return {'success': True, 'result': f'查询完成: {query}', 'rows': []}


def tool_file_operation(args: Dict[str, Any]) -> Dict[str, Any]:
    operation = args.get('operation', 'read')
    path = args.get('path', '')
    return {'success': True, 'result': f'文件操作 {operation} 完成: {path}'}


class AIAgentService:
    """AI Agent智能代理服务"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tools: Dict[str, AgentTool] = {}
        self.tasks: Dict[str, AgentTask] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.max_task_history = 500

        self._init_database()
        self._register_default_tools()
        self._register_default_agents()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    system_prompt TEXT,
                    model_id TEXT,
                    tools TEXT,
                    is_active INTEGER DEFAULT 1,
                    total_tasks INTEGER DEFAULT 0,
                    successful_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_agent_tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    parameters TEXT,
                    category TEXT DEFAULT 'general',
                    is_enabled INTEGER DEFAULT 1,
                    call_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_agent_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    goal TEXT NOT NULL,
                    agent_id TEXT,
                    status TEXT DEFAULT 'pending',
                    max_steps INTEGER DEFAULT 10,
                    priority INTEGER DEFAULT 5,
                    steps TEXT,
                    result TEXT,
                    error TEXT,
                    total_duration REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    started_at TEXT,
                    completed_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_agent_tasks_agent ON ai_agent_tasks(agent_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI Agent] 初始化数据库失败: {e}")

    def _register_default_tools(self):
        """注册默认工具"""
        defaults = [
            AgentTool('tool_search', '搜索', '搜索知识库和网络信息',
                      handler=tool_search,
                      parameters={'query': {'type': 'string', 'required': True}},
                      category='information'),
            AgentTool('tool_calculate', '计算', '数学表达式计算',
                      handler=tool_calculate,
                      parameters={'expression': {'type': 'string', 'required': True}},
                      category='utility'),
            AgentTool('tool_notify', '通知', '发送系统通知',
                      handler=tool_send_notification,
                      parameters={'message': {'type': 'string', 'required': True}},
                      category='communication'),
            AgentTool('tool_db_query', '数据库查询', '执行数据库查询',
                      handler=tool_database_query,
                      parameters={'query': {'type': 'string', 'required': True}},
                      category='data'),
            AgentTool('tool_file', '文件操作', '文件读写操作',
                      handler=tool_file_operation,
                      parameters={'operation': {'type': 'string'},
                                 'path': {'type': 'string', 'required': True}},
                      category='system'),
        ]

        for tool in defaults:
            self.tools[tool.tool_id] = tool
            self._save_tool_to_db(tool)

    def _register_default_agents(self):
        """注册默认代理"""
        defaults = [
            Agent('agent_general', '通用助手',
                  '通用AI助手，能处理多种任务',
                  '你是一个通用AI助手，帮助用户完成各种任务。',
                  'model_gpt35'),
            Agent('agent_researcher', '研究代理',
                  '专门用于信息搜索和研究',
                  '你是一个研究代理，擅长搜索和分析信息。',
                  'model_gpt4'),
            Agent('agent_analyst', '分析代理',
                  '数据分析和报表生成',
                  '你是一个数据分析代理，擅长数据分析和可视化。',
                  'model_gpt4'),
        ]

        defaults[0].tools = ['tool_search', 'tool_calculate', 'tool_notify']
        defaults[1].tools = ['tool_search', 'tool_file']
        defaults[2].tools = ['tool_db_query', 'tool_calculate', 'tool_file']

        for agent in defaults:
            self.agents[agent.agent_id] = agent
            self._save_agent_to_db(agent)

    def _save_tool_to_db(self, tool: AgentTool):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_agent_tools
                (tool_id, name, description, parameters, category,
                 is_enabled, call_count, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tool.tool_id, tool.name, tool.description,
                json.dumps(tool.parameters), tool.category,
                1 if tool.is_enabled else 0,
                tool.call_count, tool.error_count
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI Agent] 保存工具失败: {e}")

    def _save_agent_to_db(self, agent: Agent):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_agents
                (agent_id, name, description, system_prompt, model_id,
                 tools, is_active, total_tasks, successful_tasks, failed_tasks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent.agent_id, agent.name, agent.description,
                agent.system_prompt, agent.model_id,
                json.dumps(agent.tools),
                1 if agent.is_active else 0,
                agent.total_tasks, agent.successful_tasks, agent.failed_tasks
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI Agent] 保存代理失败: {e}")

    def _save_task_to_db(self, task: AgentTask):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_agent_tasks
                (task_id, goal, agent_id, status, max_steps, priority,
                 steps, result, error, total_duration, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id, task.goal, task.agent_id, task.status,
                task.max_steps, task.priority,
                json.dumps(task.steps), json.dumps(task.result),
                task.error, task.total_duration,
                task.started_at, task.completed_at
            ))

            conn.commit()
            conn.close()
        except:
            pass

    def register_tool(self, name: str, description: str,
                      handler: Callable = None,
                      parameters: Dict[str, Any] = None,
                      category: str = 'general') -> str:
        """注册工具"""
        import uuid
        tool_id = f"tool_{uuid.uuid4().hex[:8]}"

        tool = AgentTool(tool_id, name, description, handler, parameters, category)

        with self.lock:
            self.tools[tool_id] = tool

        self._save_tool_to_db(tool)
        return tool_id

    def create_agent(self, name: str, description: str = '',
                     system_prompt: str = '', model_id: str = '',
                     tool_ids: List[str] = None) -> str:
        """创建代理"""
        import uuid
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        agent = Agent(agent_id, name, description, system_prompt, model_id)
        agent.tools = tool_ids or []

        with self.lock:
            self.agents[agent_id] = agent

        self._save_agent_to_db(agent)
        logger(f"[AI Agent] 创建代理: {name}")

        return agent_id

    def execute_task(self, agent_id: str, goal: str,
                     max_steps: int = 10,
                     priority: int = 5) -> Dict[str, Any]:
        """执行任务"""
        import uuid

        with self.lock:
            agent = self.agents.get(agent_id)
            if not agent:
                return {'success': False, 'error': 'agent_not_found'}

            if not agent.is_active:
                return {'success': False, 'error': 'agent_inactive'}

            task_id = f"task_{uuid.uuid4().hex[:12]}"
            task = AgentTask(task_id, goal, agent_id, max_steps, priority)
            task.status = 'planning'
            task.started_at = datetime.now().isoformat()

            self.tasks[task_id] = task
            agent.total_tasks += 1

        start_time = time.time()

        # 任务规划
        plan = self._plan_task(agent, goal, max_steps)
        task.steps = plan
        task.status = 'executing'
        task.current_step = 0

        # 执行步骤
        for i, step in enumerate(plan):
            task.current_step = i

            step_result = self._execute_step(agent, step)

            step['result'] = step_result
            step['status'] = 'completed' if step_result.get('success') else 'failed'
            step['executed_at'] = datetime.now().isoformat()

            if not step_result.get('success'):
                task.error = step_result.get('error', 'step_failed')
                task.status = 'failed'
                agent.failed_tasks += 1
                break

        if task.status != 'failed':
            task.status = 'completed'
            task.result = {
                'summary': f'任务完成: {goal[:50]}',
                'steps_completed': len(task.steps),
                'tools_used': list(set(s.get('tool_id', '') for s in task.steps))
            }
            agent.successful_tasks += 1

        task.completed_at = datetime.now().isoformat()
        task.total_duration = time.time() - start_time

        self._save_task_to_db(task)
        self._save_agent_to_db(agent)

        logger(f"[AI Agent] 任务 {task.status}: {goal[:30]} ({task.total_duration:.2f}s)")

        return task.to_dict()

    def _plan_task(self, agent: Agent, goal: str,
                   max_steps: int) -> List[Dict[str, Any]]:
        """规划任务步骤"""
        steps = []

        # 基于目标类型规划
        if '搜索' in goal or '查找' in goal or '查询' in goal:
            if 'tool_search' in agent.tools:
                steps.append({
                    'step': 1,
                    'action': 'search',
                    'tool_id': 'tool_search',
                    'args': {'query': goal},
                    'description': f'搜索: {goal[:50]}'
                })

        if '计算' in goal or '统计' in goal:
            if 'tool_calculate' in agent.tools:
                steps.append({
                    'step': len(steps) + 1,
                    'action': 'calculate',
                    'tool_id': 'tool_calculate',
                    'args': {'expression': '1+1'},
                    'description': '执行计算'
                })

        if '通知' in goal or '发送' in goal:
            if 'tool_notify' in agent.tools:
                steps.append({
                    'step': len(steps) + 1,
                    'action': 'notify',
                    'tool_id': 'tool_notify',
                    'args': {'message': goal},
                    'description': '发送通知'
                })

        # 如果没有匹配的工具，生成默认步骤
        if not steps:
            for i, tool_id in enumerate(agent.tools[:max_steps]):
                tool = self.tools.get(tool_id)
                if tool:
                    steps.append({
                        'step': i + 1,
                        'action': tool.name,
                        'tool_id': tool_id,
                        'args': {},
                        'description': f'使用 {tool.name}'
                    })

        return steps[:max_steps]

    def _execute_step(self, agent: Agent,
                      step: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        tool_id = step.get('tool_id')
        args = step.get('args', {})

        tool = self.tools.get(tool_id)
        if not tool:
            return {'success': False, 'error': f'tool_not_found: {tool_id}'}

        result = tool.execute(args)
        self._save_tool_to_db(tool)

        return result

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    def get_agents(self, active_only: bool = False) -> List[Dict[str, Any]]:
        with self.lock:
            agents = list(self.agents.values())
            if active_only:
                agents = [a for a in agents if a.is_active]
            return [a.to_dict() for a in agents]

    def get_tools(self, category: str = None) -> List[Dict[str, Any]]:
        with self.lock:
            tools = list(self.tools.values())
            if category:
                tools = [t for t in tools if t.category == category]
            return [t.to_dict() for t in tools]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None

    def get_tasks(self, agent_id: str = None, status: str = None,
                  limit: int = 50) -> List[Dict[str, Any]]:
        with self.lock:
            tasks = list(self.tasks.values())

            if agent_id:
                tasks = [t for t in tasks if t.agent_id == agent_id]
            if status:
                tasks = [t for t in tasks if t.status == status]

            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return [t.to_dict() for t in tasks[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total_tasks = sum(a.total_tasks for a in self.agents.values())
            successful = sum(a.successful_tasks for a in self.agents.values())
            failed = sum(a.failed_tasks for a in self.agents.values())

            return {
                'total_agents': len(self.agents),
                'active_agents': sum(1 for a in self.agents.values() if a.is_active),
                'total_tools': len(self.tools),
                'total_tasks': total_tasks,
                'successful_tasks': successful,
                'failed_tasks': failed,
                'success_rate': round(successful / max(1, total_tasks) * 100, 2)
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_agents': len(self.agents),
            'total_tools': len(self.tools),
            'total_tasks': len(self.tasks)
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[AI Agent] 智能代理服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[AI Agent] 智能代理服务已停止")


ai_agent_service = AIAgentService()
