# -*- coding: utf-8 -*-
"""
BaseCoreAgent - 核心Agent基类
定义所有核心Agent的通用接口和能力
"""
import os
import uuid
import json
import logging
import traceback
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class BaseCoreAgent(ABC):
    """核心Agent基类"""
    
    def __init__(self, agent_id: str, agent_name: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.status = 'idle'
        self.last_heartbeat = datetime.now()
        self.task_history: List[Dict] = []
    
    @abstractmethod
    def execute(self, context: Dict = None) -> Dict:
        """执行Agent核心逻辑"""
        pass
    
    def report_to_db(self, task_id: str, status: str, data: Dict = None):
        """上报任务结果到数据库"""
        try:
            import sqlite3
            app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(app_root, 'app.db')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS core_agent_tasks (
                    task_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    agent_name TEXT,
                    agent_type TEXT,
                    status TEXT,
                    data TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            cursor.execute('''
                INSERT OR REPLACE INTO core_agent_tasks 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                self.agent_id,
                self.agent_name,
                self.agent_type,
                status,
                json.dumps(data or {}, ensure_ascii=False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[{self.agent_name}] 任务 {task_id} 已上报数据库")
        except Exception as e:
            logger.error(f"[{self.agent_name}] 上报数据库失败: {e}")
    
    def trigger_rule(self, rule_name: str, context: Dict = None):
        """触发规则引擎中的规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            rule_engine = get_rule_engine()
            if rule_engine:
                context = context or {}
                context['trigger_source'] = self.agent_name
                rule_engine.evaluate_and_trigger(context)
                logger.info(f"[{self.agent_name}] 已触发规则: {rule_name}")
        except Exception as e:
            logger.error(f"[{self.agent_name}] 触发规则失败: {e}")
    
    def record_task(self, task_id: str, status: str, result: Dict = None):
        """记录任务历史"""
        task_record = {
            'task_id': task_id,
            'status': status,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        self.task_history.append(task_record)
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]
    
    def heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
    
    def get_status(self) -> Dict:
        """获取Agent状态"""
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'task_count': len(self.task_history)
        }
    
    def generate_task_id(self) -> str:
        """生成唯一任务ID"""
        return f"{self.agent_type}_{uuid.uuid4().hex[:8]}"
    
    def handle_error(self, error: Exception, task_id: str) -> Dict:
        """统一错误处理"""
        error_info = {
            'error': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
        self.report_to_db(task_id, 'failed', {'error': error_info})
        self.record_task(task_id, 'failed', {'error': str(error)})
        logger.error(f"[{self.agent_name}] 任务 {task_id} 失败: {error}")
        return {'success': False, 'error': str(error), 'task_id': task_id}
