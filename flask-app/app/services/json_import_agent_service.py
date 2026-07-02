# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
JSON数据导入Agent服务
负责执行JSON数据上传到数据库的任务
"""

import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.utils.db import db_manager
from app.utils.ai_json_importer import ai_json_importer
from app.utils.logging import logger
from app.models.local_agent import LocalAgent, AgentTask, AgentStatus


class JsonImportAgentService:
    """JSON数据导入Agent服务"""
    
    AGENT_CODE = 'AGENT_JSON_IMPORT_001'
    AGENT_NAME = 'JSON数据导入Agent'
    
    def __init__(self):
        self.db = db_manager
        self._ensure_agent_registered()
    
    def _ensure_agent_registered(self):
        """确保Agent已注册"""
        agent = LocalAgent.get_by_code(self.db, self.AGENT_CODE)
        if not agent:
            agent = LocalAgent(
                agent_name=self.AGENT_NAME,
                agent_code=self.AGENT_CODE,
                agent_type='worker',
                description='负责将JSON数据自动扫描、匹配并增量保存到数据库的AI Agent',
                capabilities=['database_access', 'json_processing', 'data_import', 'incremental_sync', 'auto_matching'],
                tools=['json_scanner', 'table_matcher', 'data_converter', 'incremental_saver', 'import_monitor'],
                status='stopped',
                llm_model='local',
                temperature=0.4,
                requires_auth=True,
                allowed_roles=['super_admin', 'admin', 'developer']
            )
            agent.save(self.db)
            logger.info(f"JSON数据导入Agent注册成功: {self.AGENT_NAME}")
        else:
            logger.debug(f"JSON数据导入Agent已存在: {self.AGENT_NAME}")
    
    def get_agent(self) -> Optional[LocalAgent]:
        """获取Agent实例"""
        return LocalAgent.get_by_code(self.db, self.AGENT_CODE)
    
    def create_task(self, json_data: List[Dict], table_name: str = None, auto_create: bool = True, 
                   priority: int = 0) -> AgentTask:
        """创建JSON数据导入任务
        
        Args:
            json_data: JSON数据列表
            table_name: 指定目标表名（可选）
            auto_create: 是否自动创建新表
            priority: 任务优先级
            
        Returns:
            AgentTask实例
        """
        agent = self.get_agent()
        if not agent:
            raise ValueError("JSON数据导入Agent未注册")
        
        task_code = f"IMPORT_{uuid.uuid4().hex[:8].upper()}"
        input_data = {
            'json_data': json_data,
            'table_name': table_name,
            'auto_create': auto_create
        }
        
        task = AgentTask(
            task_code=task_code,
            agent_id=agent.id,
            task_type='json_import',
            title=f'JSON数据导入任务 - {len(json_data)}条记录',
            description=f'从JSON数据导入{len(json_data)}条记录到数据库',
            input_data=input_data,
            expected_output={},
            status='pending',
            priority=priority,
            created_by=None
        )
        task.save(self.db)
        
        logger.info(f"创建JSON数据导入任务: {task_code}, 记录数: {len(json_data)}")
        return task
    
    def execute_task(self, task_code: str) -> AgentTask:
        """执行JSON数据导入任务
        
        Args:
            task_code: 任务代码
            
        Returns:
            更新后的AgentTask实例
        """
        task = AgentTask.get_by_code(self.db, task_code)
        if not task:
            raise ValueError(f"任务不存在: {task_code}")
        
        agent = self.get_agent()
        if not agent:
            raise ValueError("JSON数据导入Agent未注册")
        
        if task.status != 'pending':
            raise ValueError(f"任务状态不允许执行: {task.status}")
        
        task.status = 'running'
        task.start_time = datetime.now().isoformat()
        task.save(self.db)
        
        start_time = datetime.now()
        
        try:
            input_data = task.input_data
            json_data = input_data.get('json_data', [])
            table_name = input_data.get('table_name')
            auto_create = input_data.get('auto_create', True)
            
            if not json_data:
                raise ValueError("JSON数据为空")
            
            result = ai_json_importer.import_json_data(json_data, table_name, auto_create)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            task.status = 'completed' if result['success'] else 'failed'
            task.end_time = datetime.now().isoformat()
            task.execution_time = execution_time
            task.output_data = {
                'success': result['success'],
                'message': result['message'],
                'table_name': result.get('table_name'),
                'stats': result['stats'],
                'elapsed_time': result.get('elapsed_time')
            }
            task.is_successful = result['success']
            task.error_message = '' if result['success'] else result['message']
            task.logs = self._format_logs(result)
            
            agent.task_count = (agent.task_count or 0) + 1
            if result['success']:
                agent.success_rate = ((agent.success_rate or 0) * (agent.task_count - 1) + 100) / agent.task_count
            else:
                agent.success_rate = ((agent.success_rate or 0) * (agent.task_count - 1)) / agent.task_count
            agent.last_run_at = datetime.now().isoformat()
            agent.status = 'running'
            agent.save(self.db)
            
            logger.info(f"JSON数据导入任务执行完成: {task_code}, 成功: {result['success']}, "
                      f"新增: {result['stats']['inserted']}, 更新: {result['stats']['updated']}")
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            task.status = 'failed'
            task.end_time = datetime.now().isoformat()
            task.execution_time = execution_time
            task.is_successful = False
            task.error_message = str(e)
            task.logs = f"执行失败: {str(e)}"
            
            agent.task_count = (agent.task_count or 0) + 1
            agent.success_rate = ((agent.success_rate or 0) * (agent.task_count - 1)) / agent.task_count
            agent.last_run_at = datetime.now().isoformat()
            agent.save(self.db)
            
            logger.error(f"JSON数据导入任务执行失败: {task_code}, 错误: {str(e)}")
        
        task.save(self.db)
        return task
    
    def execute_direct(self, json_data: List[Dict], table_name: str = None, 
                      auto_create: bool = True) -> Dict[str, Any]:
        """直接执行JSON数据导入（不创建任务记录）
        
        Args:
            json_data: JSON数据列表
            table_name: 指定目标表名（可选）
            auto_create: 是否自动创建新表
            
        Returns:
            导入结果
        """
        agent = self.get_agent()
        if agent:
            agent.status = 'running'
            agent.last_run_at = datetime.now().isoformat()
            agent.save(self.db)
        
        result = ai_json_importer.import_json_data(json_data, table_name, auto_create)
        
        if agent:
            agent.status = 'stopped'
            agent.task_count = (agent.task_count or 0) + 1
            if result['success']:
                agent.success_rate = ((agent.success_rate or 0) * (agent.task_count - 1) + 100) / agent.task_count
            else:
                agent.success_rate = ((agent.success_rate or 0) * (agent.task_count - 1)) / agent.task_count
            agent.save(self.db)
        
        return result
    
    def analyze_data(self, json_data: List[Dict]) -> Dict[str, Any]:
        """分析JSON数据，提供导入建议"""
        return ai_json_importer.analyze_json_for_import(json_data)
    
    def get_task_history(self, limit: int = 20) -> List[AgentTask]:
        """获取任务执行历史"""
        agent = self.get_agent()
        if not agent:
            return []
        
        table_name = AgentTask._get_table_name(self.db)
        query = f"SELECT * FROM {table_name} WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?"
        results = self.db.fetch_all(query, (agent.id, limit))
        return [AgentTask._from_db_row(row) for row in results]
    
    def get_pending_tasks(self) -> List[AgentTask]:
        """获取待执行任务"""
        agent = self.get_agent()
        if not agent:
            return []
        
        table_name = AgentTask._get_table_name(self.db)
        query = f"SELECT * FROM {table_name} WHERE agent_id = ? AND status = 'pending' ORDER BY priority DESC"
        results = self.db.fetch_all(query, (agent.id,))
        return [AgentTask._from_db_row(row) for row in results]
    
    def run_all_pending_tasks(self) -> List[AgentTask]:
        """执行所有待处理任务"""
        pending_tasks = self.get_pending_tasks()
        completed_tasks = []
        
        for task in pending_tasks:
            try:
                result = self.execute_task(task.task_code)
                completed_tasks.append(result)
            except Exception as e:
                logger.error(f"执行任务失败: {task.task_code}, 错误: {str(e)}")
        
        return completed_tasks
    
    def _format_logs(self, result: Dict[str, Any]) -> str:
        """格式化执行日志"""
        logs = []
        logs.append(f"执行时间: {datetime.now().isoformat()}")
        logs.append(f"目标表: {result.get('table_name', '未知')}")
        logs.append(f"执行结果: {'成功' if result['success'] else '失败'}")
        logs.append(f"消息: {result.get('message', '')}")
        logs.append("统计:")
        stats = result.get('stats', {})
        logs.append(f"  - 总数: {stats.get('total', 0)}")
        logs.append(f"  - 新增: {stats.get('inserted', 0)}")
        logs.append(f"  - 更新: {stats.get('updated', 0)}")
        logs.append(f"  - 失败: {stats.get('failed', 0)}")
        logs.append(f"耗时: {result.get('elapsed_time', 0):.2f}秒")
        return '\n'.join(logs)
    
    def start_agent(self):
        """启动Agent"""
        agent = self.get_agent()
        if agent:
            agent.status = 'running'
            agent.save(self.db)
            logger.info(f"JSON数据导入Agent已启动")
    
    def stop_agent(self):
        """停止Agent"""
        agent = self.get_agent()
        if agent:
            agent.status = 'stopped'
            agent.save(self.db)
            logger.info(f"JSON数据导入Agent已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        agent = self.get_agent()
        if not agent:
            return {
                'agent_name': self.AGENT_NAME,
                'agent_code': self.AGENT_CODE,
                'status': 'not_registered',
                'task_count': 0,
                'success_rate': 0.0
            }
        
        return {
            'agent_name': agent.agent_name,
            'agent_code': agent.agent_code,
            'status': agent.status,
            'task_count': agent.task_count,
            'success_rate': agent.success_rate,
            'last_run_at': agent.last_run_at,
            'cpu_usage': agent.cpu_usage,
            'memory_usage': agent.memory_usage
        }


json_import_agent_service = JsonImportAgentService()