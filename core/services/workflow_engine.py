#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS工作流引擎服务
提供自动化工作流管理和执行功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

logger = print

class WorkflowStep:
    """工作流步骤"""
    
    def __init__(self, step_id: str, name: str, action: str,
                 params: Dict[str, Any] = None, condition: str = None,
                 next_step: str = None, error_step: str = None):
        self.step_id = step_id
        self.name = name
        self.action = action
        self.params = params or {}
        self.condition = condition
        self.next_step = next_step
        self.error_step = error_step
        self.status = 'pending'
        self.execution_time = None
        self.error_message = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'step_id': self.step_id,
            'name': self.name,
            'action': self.action,
            'params': self.params,
            'condition': self.condition,
            'next_step': self.next_step,
            'error_step': self.error_step,
            'status': self.status,
            'execution_time': self.execution_time,
            'error_message': self.error_message
        }

class Workflow:
    """工作流"""
    
    def __init__(self, workflow_id: str, name: str, description: str = '',
                 steps: List[WorkflowStep] = None, enabled: bool = True,
                 created_at: str = None):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps = steps or []
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
        self.status = 'idle'
        self.current_step = None
        self.execution_count = 0
        self.last_execution = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'description': self.description,
            'steps': [step.to_dict() for step in self.steps],
            'enabled': self.enabled,
            'created_at': self.created_at,
            'status': self.status,
            'current_step': self.current_step,
            'execution_count': self.execution_count,
            'last_execution': self.last_execution
        }

class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.actions: Dict[str, Callable] = {}
        self.is_running = False
        self.execution_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._register_default_actions()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'workflow_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'max_concurrent_workflows': 10,
            'step_timeout': 300,
            'max_retries': 3,
            'retry_delay': 5
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'workflow_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    steps TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_step_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    execution_id INTEGER,
                    step_id TEXT NOT NULL,
                    step_name TEXT,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_workflows_id ON workflows(workflow_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow ON workflow_executions(workflow_id)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[工作流] 初始化数据库失败: {e}")
    
    def _register_default_actions(self):
        """注册默认动作"""
        self.actions['log'] = self._action_log
        self.actions['email'] = self._action_email
        self.actions['sms'] = self._action_sms
        self.actions['delay'] = self._action_delay
        self.actions['notification'] = self._action_notification
        self.actions['execute_skill'] = self._action_execute_skill
        self.actions['create_backup'] = self._action_create_backup
        self.actions['export_data'] = self._action_export_data
    
    def _action_log(self, params: Dict[str, Any]) -> bool:
        """日志动作"""
        try:
            from activity_log_service import activity_log_service
            activity_log_service.info('workflow', params.get('message', ''), source=params.get('source', 'workflow'))
            return True
        except:
            return False
    
    def _action_email(self, params: Dict[str, Any]) -> bool:
        """邮件动作"""
        try:
            from email_service import email_service
            email_service.send_email(
                to_email=params['to'],
                subject=params.get('subject', ''),
                content=params.get('content', ''),
                is_html=params.get('is_html', False)
            )
            return True
        except:
            return False
    
    def _action_sms(self, params: Dict[str, Any]) -> bool:
        """短信动作"""
        try:
            from sms_service import sms_service
            sms_service.send_sms(
                phone_number=params['phone'],
                message=params.get('message', '')
            )
            return True
        except:
            return False
    
    def _action_delay(self, params: Dict[str, Any]) -> bool:
        """延迟动作"""
        delay_seconds = params.get('seconds', 60)
        time.sleep(delay_seconds)
        return True
    
    def _action_notification(self, params: Dict[str, Any]) -> bool:
        """通知动作"""
        try:
            from notification_center import notification_center
            notification_center.add_notification(
                title=params.get('title', ''),
                content=params.get('content', ''),
                notification_type=params.get('type', 'info'),
                priority=params.get('priority', 'normal')
            )
            return True
        except:
            return False
    
    def _action_execute_skill(self, params: Dict[str, Any]) -> bool:
        """执行技能动作"""
        try:
            from skill_manager import skill_manager
            skill_manager.execute_skill(
                skill_id=params['skill_id'],
                **params.get('kwargs', {})
            )
            return True
        except:
            return False
    
    def _action_create_backup(self, params: Dict[str, Any]) -> bool:
        """创建备份动作"""
        try:
            from backup_manager import backup_manager
            backup_manager.create_backup(description=params.get('description', 'Workflow backup'))
            return True
        except:
            return False
    
    def _action_export_data(self, params: Dict[str, Any]) -> bool:
        """导出数据动作"""
        try:
            from data_export_service import data_export_service
            data_export_service.export_data(
                data=[],
                file_format=params.get('format', 'json'),
                filename=params.get('filename', 'export')
            )
            return True
        except:
            return False
    
    def register_action(self, action_name: str, action_func: Callable):
        """注册自定义动作"""
        self.actions[action_name] = action_func
        logger(f"[工作流] 注册动作: {action_name}")
    
    def unregister_action(self, action_name: str):
        """注销动作"""
        if action_name in self.actions:
            del self.actions[action_name]
            logger(f"[工作流] 注销动作: {action_name}")
    
    def add_workflow(self, workflow_id: str, name: str, steps: List[Dict[str, Any]],
                     description: str = '', enabled: bool = True) -> bool:
        """添加工作流"""
        if workflow_id in self.workflows:
            logger(f"[工作流] 工作流已存在: {workflow_id}")
            return False
        
        workflow_steps = []
        for step_data in steps:
            step = WorkflowStep(
                step_id=step_data['step_id'],
                name=step_data.get('name', step_data['step_id']),
                action=step_data['action'],
                params=step_data.get('params', {}),
                condition=step_data.get('condition'),
                next_step=step_data.get('next_step'),
                error_step=step_data.get('error_step')
            )
            workflow_steps.append(step)
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps,
            enabled=enabled
        )
        
        with self.lock:
            self.workflows[workflow_id] = workflow
        
        self._save_workflow_to_db(workflow)
        logger(f"[工作流] 添加工作流: {name}")
        
        return True
    
    def _save_workflow_to_db(self, workflow: Workflow):
        """保存工作流到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO workflows 
                (workflow_id, name, description, steps, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                workflow.workflow_id, workflow.name, workflow.description,
                json.dumps([step.to_dict() for step in workflow.steps]),
                1 if workflow.enabled else 0,
                workflow.created_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[工作流] 保存工作流失败: {e}")
    
    def update_workflow(self, workflow_id: str, **kwargs) -> bool:
        """更新工作流"""
        with self.lock:
            if workflow_id not in self.workflows:
                logger(f"[工作流] 工作流不存在: {workflow_id}")
                return False
            
            workflow = self.workflows[workflow_id]
            
            if 'name' in kwargs:
                workflow.name = kwargs['name']
            if 'description' in kwargs:
                workflow.description = kwargs['description']
            if 'enabled' in kwargs:
                workflow.enabled = kwargs['enabled']
            
            self._update_workflow_in_db(workflow_id, kwargs)
            logger(f"[工作流] 更新工作流: {workflow_id}")
            
            return True
    
    def _update_workflow_in_db(self, workflow_id: str, updates: Dict[str, Any]):
        """更新数据库中的工作流"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key == 'enabled':
                    set_clause.append(f"{key} = ?")
                    params.append(1 if value else 0)
                else:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
            
            params.append(workflow_id)
            
            cursor.execute(f'UPDATE workflows SET {", ".join(set_clause)} WHERE workflow_id = ?', params)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[工作流] 更新工作流失败: {e}")
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        with self.lock:
            if workflow_id not in self.workflows:
                logger(f"[工作流] 工作流不存在: {workflow_id}")
                return False
            
            del self.workflows[workflow_id]
        
        self._delete_workflow_from_db(workflow_id)
        logger(f"[工作流] 删除工作流: {workflow_id}")
        
        return True
    
    def _delete_workflow_from_db(self, workflow_id: str):
        """从数据库删除工作流"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM workflows WHERE workflow_id = ?', (workflow_id,))
            cursor.execute('DELETE FROM workflow_executions WHERE workflow_id = ?', (workflow_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[工作流] 删除工作流失败: {e}")
    
    def execute_workflow(self, workflow_id: str) -> bool:
        """执行工作流"""
        with self.lock:
            if workflow_id not in self.workflows:
                logger(f"[工作流] 工作流不存在: {workflow_id}")
                return False
            
            workflow = self.workflows[workflow_id]
            
            if not workflow.enabled:
                logger(f"[工作流] 工作流已禁用: {workflow_id}")
                return False
            
            if workflow.status == 'running':
                logger(f"[工作流] 工作流正在运行: {workflow_id}")
                return False
            
            workflow.status = 'running'
        
        def run_workflow():
            started_at = datetime.now()
            
            try:
                execution_id = self._start_execution(workflow_id, started_at)
                
                for step in workflow.steps:
                    step.status = 'running'
                    step_start = datetime.now()
                    
                    try:
                        if step.action in self.actions:
                            success = self.actions[step.action](step.params)
                        else:
                            logger(f"[工作流] 未知动作: {step.action}")
                            success = False
                        
                        step.status = 'success' if success else 'failed'
                        step.execution_time = (datetime.now() - step_start).total_seconds()
                        
                        self._log_step(workflow_id, execution_id, step)
                        
                        if not success and step.error_step:
                            self._execute_step(workflow_id, execution_id, step.error_step)
                            break
                        
                        if not step.next_step:
                            break
                    except Exception as e:
                        step.status = 'failed'
                        step.error_message = str(e)
                        step.execution_time = (datetime.now() - step_start).total_seconds()
                        
                        self._log_step(workflow_id, execution_id, step)
                        logger(f"[工作流] 步骤执行失败: {step.name} - {e}")
                        
                        if step.error_step:
                            self._execute_step(workflow_id, execution_id, step.error_step)
                        break
                
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                
                with self.lock:
                    workflow.status = 'idle'
                    workflow.execution_count += 1
                    workflow.last_execution = completed_at.isoformat()
                
                self._end_execution(execution_id, 'success', completed_at, duration)
                logger(f"[工作流] 工作流执行完成: {workflow.name}")
            except Exception as e:
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                
                with self.lock:
                    workflow.status = 'idle'
                
                self._end_execution(execution_id, 'failed', completed_at, duration, str(e))
                logger(f"[工作流] 工作流执行失败: {workflow.name} - {e}")
        
        thread = threading.Thread(target=run_workflow, daemon=True)
        thread.start()
        
        return True
    
    def _execute_step(self, workflow_id: str, execution_id: int, step_id: str):
        """执行指定步骤"""
        pass
    
    def _start_execution(self, workflow_id: str, started_at: datetime) -> int:
        """开始执行记录"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO workflow_executions (workflow_id, status, started_at)
                VALUES (?, ?, ?)
            ''', (workflow_id, 'running', started_at.isoformat()))
            
            execution_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return execution_id
        except Exception as e:
            logger(f"[工作流] 开始执行记录失败: {e}")
            return 0
    
    def _end_execution(self, execution_id: int, status: str, completed_at: datetime,
                      duration: float, error_message: str = None):
        """结束执行记录"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE workflow_executions 
                SET status = ?, completed_at = ?, duration = ?, error_message = ?
                WHERE id = ?
            ''', (status, completed_at.isoformat(), duration, error_message, execution_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[工作流] 结束执行记录失败: {e}")
    
    def _log_step(self, workflow_id: str, execution_id: int, step: WorkflowStep):
        """记录步骤日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO workflow_step_logs 
                (workflow_id, execution_id, step_id, step_name, status, started_at, completed_at, duration,
                error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                workflow_id, execution_id, step.step_id, step.name,
                step.status, step.execution_time, step.execution_time,
                step.execution_time, step.error_message
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[工作流] 记录步骤日志失败: {e}")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self.workflows.get(workflow_id)
    
    def get_workflows(self, enabled_only: bool = False) -> List[Workflow]:
        """获取工作流列表"""
        with self.lock:
            if enabled_only:
                return [w for w in self.workflows.values() if w.enabled]
            return list(self.workflows.values())
    
    def get_executions(self, workflow_id: str = None, status: str = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """获取执行记录"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM workflow_executions WHERE 1=1'
            params = []
            
            if workflow_id:
                query += ' AND workflow_id = ?'
                params.append(workflow_id)
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY started_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            executions = []
            
            for row in cursor.fetchall():
                executions.append(dict(zip(columns, row)))
            
            conn.close()
            return executions
        except Exception as e:
            logger(f"[工作流] 获取执行记录失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            running_count = sum(1 for w in self.workflows.values() if w.status == 'running')
            enabled_count = sum(1 for w in self.workflows.values() if w.enabled)
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_workflows': len(self.workflows),
                'enabled_workflows': enabled_count,
                'running_workflows': running_count,
                'available_actions': list(self.actions.keys()),
                'max_concurrent_workflows': self.config['max_concurrent_workflows']
            }
    
    def start(self):
        """启动工作流引擎"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[工作流] 工作流引擎服务已启动")
    
    def stop(self):
        """停止工作流引擎"""
        self.is_running = False
        logger(f"[工作流] 工作流引擎服务已停止")

workflow_engine = WorkflowEngine()

