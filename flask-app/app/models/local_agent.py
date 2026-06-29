# -*- coding: utf-8 -*-
"""
本地Agent模型
用于管理本地智能体的注册、配置和状态
适配项目现有的DatabaseManager架构
"""

import os
import json
from datetime import datetime
from enum import Enum


class AgentStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    INITIALIZING = "initializing"


class AgentType(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    WORKER = "worker"
    MONITOR = "monitor"


class LocalAgent:
    """本地Agent模型"""
    
    TABLE_NAME = 'local_agents'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.agent_name = kwargs.get('agent_name', '')
        self.agent_code = kwargs.get('agent_code', '')
        self.agent_type = kwargs.get('agent_type', 'user')
        self.description = kwargs.get('description', '')
        self.config = kwargs.get('config', {})
        self.capabilities = kwargs.get('capabilities', [])
        self.tools = kwargs.get('tools', [])
        self.status = kwargs.get('status', AgentStatus.STOPPED.value)
        self.process_id = kwargs.get('process_id')
        self.port = kwargs.get('port')
        self.cpu_usage = kwargs.get('cpu_usage', 0.0)
        self.memory_usage = kwargs.get('memory_usage', 0.0)
        self.task_count = kwargs.get('task_count', 0)
        self.success_rate = kwargs.get('success_rate', 0.0)
        self.llm_model = kwargs.get('llm_model', 'local')
        self.temperature = kwargs.get('temperature', 0.7)
        self.requires_auth = kwargs.get('requires_auth', True)
        self.allowed_roles = kwargs.get('allowed_roles', [])
        self.created_by = kwargs.get('created_by')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
        self.last_run_at = kwargs.get('last_run_at')
    
    @classmethod
    def _get_table_name(cls, db_manager):
        """获取实际的表名（支持加密）"""
        try:
            from app.utils.table_encryption import table_encryption
            return table_encryption.encrypt_table_name(cls.TABLE_NAME)
        except Exception:
            return cls.TABLE_NAME
    
    @classmethod
    def create_table(cls, db_manager):
        """创建表"""
        columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'agent_name': 'TEXT NOT NULL',
            'agent_code': 'TEXT UNIQUE NOT NULL',
            'agent_type': 'TEXT DEFAULT "user"',
            'description': 'TEXT',
            'config': 'TEXT',
            'capabilities': 'TEXT',
            'tools': 'TEXT',
            'status': 'TEXT DEFAULT "stopped"',
            'process_id': 'INTEGER',
            'port': 'INTEGER',
            'cpu_usage': 'REAL DEFAULT 0.0',
            'memory_usage': 'REAL DEFAULT 0.0',
            'task_count': 'INTEGER DEFAULT 0',
            'success_rate': 'REAL DEFAULT 0.0',
            'llm_model': 'TEXT',
            'temperature': 'REAL DEFAULT 0.7',
            'requires_auth': 'INTEGER DEFAULT 1',
            'allowed_roles': 'TEXT',
            'created_by': 'INTEGER',
            'created_at': 'TEXT',
            'updated_at': 'TEXT',
            'last_run_at': 'TEXT'
        }
        db_manager.create_table(cls.TABLE_NAME, columns)
    
    @classmethod
    def get_by_code(cls, db_manager, agent_code):
        """通过代码获取Agent"""
        table_name = cls._get_table_name(db_manager)
        result = db_manager.fetch_one(
            f"SELECT * FROM {table_name} WHERE agent_code = ?",
            (agent_code,)
        )
        if result:
            return cls._from_db_row(result)
        return None
    
    @classmethod
    def get_all(cls, db_manager):
        """获取所有Agent"""
        table_name = cls._get_table_name(db_manager)
        results = db_manager.fetch_all(f"SELECT * FROM {table_name}")
        return [cls._from_db_row(row) for row in results]
    
    @classmethod
    def _from_db_row(cls, row):
        """从数据库行创建对象"""
        if isinstance(row, dict):
            return cls(
                id=row.get('id'),
                agent_name=row.get('agent_name', ''),
                agent_code=row.get('agent_code', ''),
                agent_type=row.get('agent_type', 'user'),
                description=row.get('description', ''),
                config=cls._parse_json(row.get('config', '{}')),
                capabilities=cls._parse_json(row.get('capabilities', '[]')),
                tools=cls._parse_json(row.get('tools', '[]')),
                status=row.get('status', 'stopped'),
                process_id=row.get('process_id'),
                port=row.get('port'),
                cpu_usage=row.get('cpu_usage', 0.0),
                memory_usage=row.get('memory_usage', 0.0),
                task_count=row.get('task_count', 0),
                success_rate=row.get('success_rate', 0.0),
                llm_model=row.get('llm_model', 'local'),
                temperature=row.get('temperature', 0.7),
                requires_auth=bool(row.get('requires_auth', 1)),
                allowed_roles=cls._parse_json(row.get('allowed_roles', '[]')),
                created_by=row.get('created_by'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
                last_run_at=row.get('last_run_at')
            )
        elif isinstance(row, (tuple, list)) and len(row) >= 23:
            return cls(
                id=row[0],
                agent_name=row[1] or '',
                agent_code=row[2] or '',
                agent_type=row[3] or 'user',
                description=row[4] or '',
                config=cls._parse_json(row[5] or '{}'),
                capabilities=cls._parse_json(row[6] or '[]'),
                tools=cls._parse_json(row[7] or '[]'),
                status=row[8] or 'stopped',
                process_id=row[9],
                port=row[10],
                cpu_usage=row[11] or 0.0,
                memory_usage=row[12] or 0.0,
                task_count=row[13] or 0,
                success_rate=row[14] or 0.0,
                llm_model=row[15] or 'local',
                temperature=row[16] or 0.7,
                requires_auth=bool(row[17]) if row[17] is not None else True,
                allowed_roles=cls._parse_json(row[18] or '[]'),
                created_by=row[19],
                created_at=row[20],
                updated_at=row[21],
                last_run_at=row[22]
            )
        return None
    
    @staticmethod
    def _parse_json(value):
        """解析JSON字符串"""
        if not value:
            return {} if isinstance(value, dict) else []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {} if '{' in value else []
        return value
    
    def save(self, db_manager):
        """保存到数据库"""
        now = datetime.now().isoformat()
        
        if self.id:
            data = {
                'agent_name': self.agent_name,
                'agent_type': self.agent_type,
                'description': self.description,
                'config': json.dumps(self.config, ensure_ascii=False),
                'capabilities': json.dumps(self.capabilities),
                'tools': json.dumps(self.tools),
                'status': self.status,
                'process_id': self.process_id,
                'port': self.port,
                'cpu_usage': self.cpu_usage,
                'memory_usage': self.memory_usage,
                'task_count': self.task_count,
                'success_rate': self.success_rate,
                'llm_model': self.llm_model,
                'temperature': self.temperature,
                'requires_auth': 1 if self.requires_auth else 0,
                'allowed_roles': json.dumps(self.allowed_roles),
                'updated_at': now
            }
            db_manager.update(self.TABLE_NAME, data, 'id = ?', (self.id,))
        else:
            data = {
                'agent_name': self.agent_name,
                'agent_code': self.agent_code,
                'agent_type': self.agent_type,
                'description': self.description,
                'config': json.dumps(self.config, ensure_ascii=False),
                'capabilities': json.dumps(self.capabilities),
                'tools': json.dumps(self.tools),
                'status': self.status,
                'llm_model': self.llm_model,
                'temperature': self.temperature,
                'requires_auth': 1 if self.requires_auth else 0,
                'allowed_roles': json.dumps(self.allowed_roles),
                'created_by': self.created_by,
                'created_at': now,
                'updated_at': now
            }
            self.id = db_manager.insert(self.TABLE_NAME, data)
        
        return self.id
    
    def delete(self, db_manager):
        """删除Agent"""
        if self.id:
            db_manager.delete(self.TABLE_NAME, 'id = ?', (self.id,))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'agent_name': self.agent_name,
            'agent_code': self.agent_code,
            'agent_type': self.agent_type,
            'description': self.description,
            'config': self.config,
            'capabilities': self.capabilities,
            'tools': self.tools,
            'status': self.status,
            'process_id': self.process_id,
            'port': self.port,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'task_count': self.task_count,
            'success_rate': self.success_rate,
            'llm_model': self.llm_model,
            'temperature': self.temperature,
            'requires_auth': self.requires_auth,
            'allowed_roles': self.allowed_roles,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_run_at': self.last_run_at
        }


class AgentTask:
    """Agent任务模型"""
    
    TABLE_NAME = 'agent_tasks'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.task_code = kwargs.get('task_code', '')
        self.agent_id = kwargs.get('agent_id')
        self.parent_task_id = kwargs.get('parent_task_id')
        self.task_type = kwargs.get('task_type', '')
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        self.input_data = kwargs.get('input_data', {})
        self.expected_output = kwargs.get('expected_output', {})
        self.status = kwargs.get('status', 'pending')
        self.priority = kwargs.get('priority', 0)
        self.start_time = kwargs.get('start_time')
        self.end_time = kwargs.get('end_time')
        self.execution_time = kwargs.get('execution_time')
        self.output_data = kwargs.get('output_data', {})
        self.is_successful = kwargs.get('is_successful', False)
        self.error_message = kwargs.get('error_message', '')
        self.logs = kwargs.get('logs', '')
        self.created_by = kwargs.get('created_by')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def _get_table_name(cls, db_manager):
        """获取实际的表名（支持加密）"""
        try:
            from app.utils.table_encryption import table_encryption
            return table_encryption.encrypt_table_name(cls.TABLE_NAME)
        except Exception:
            return cls.TABLE_NAME
    
    @classmethod
    def create_table(cls, db_manager):
        """创建表"""
        columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'task_code': 'TEXT UNIQUE NOT NULL',
            'agent_id': 'INTEGER NOT NULL',
            'parent_task_id': 'INTEGER',
            'task_type': 'TEXT',
            'title': 'TEXT NOT NULL',
            'description': 'TEXT',
            'input_data': 'TEXT',
            'expected_output': 'TEXT',
            'status': 'TEXT DEFAULT "pending"',
            'priority': 'INTEGER DEFAULT 0',
            'start_time': 'TEXT',
            'end_time': 'TEXT',
            'execution_time': 'REAL',
            'output_data': 'TEXT',
            'is_successful': 'INTEGER DEFAULT 0',
            'error_message': 'TEXT',
            'logs': 'TEXT',
            'created_by': 'INTEGER',
            'created_at': 'TEXT',
            'updated_at': 'TEXT'
        }
        db_manager.create_table(cls.TABLE_NAME, columns)
    
    @classmethod
    def get_by_code(cls, db_manager, task_code):
        """通过代码获取任务"""
        table_name = cls._get_table_name(db_manager)
        result = db_manager.fetch_one(
            f"SELECT * FROM {table_name} WHERE task_code = ?",
            (task_code,)
        )
        if result:
            return cls._from_db_row(result)
        return None
    
    @classmethod
    def _from_db_row(cls, row):
        """从数据库行创建对象"""
        if isinstance(row, dict):
            return cls(
                id=row.get('id'),
                task_code=row.get('task_code', ''),
                agent_id=row.get('agent_id'),
                parent_task_id=row.get('parent_task_id'),
                task_type=row.get('task_type', ''),
                title=row.get('title', ''),
                description=row.get('description', ''),
                input_data=LocalAgent._parse_json(row.get('input_data', '{}')),
                expected_output=LocalAgent._parse_json(row.get('expected_output', '{}')),
                status=row.get('status', 'pending'),
                priority=row.get('priority', 0),
                start_time=row.get('start_time'),
                end_time=row.get('end_time'),
                execution_time=row.get('execution_time'),
                output_data=LocalAgent._parse_json(row.get('output_data', '{}')),
                is_successful=bool(row.get('is_successful', 0)),
                error_message=row.get('error_message', ''),
                logs=row.get('logs', ''),
                created_by=row.get('created_by'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at')
            )
        elif isinstance(row, (tuple, list)) and len(row) >= 20:
            return cls(
                id=row[0],
                task_code=row[1] or '',
                agent_id=row[2],
                parent_task_id=row[3],
                task_type=row[4] or '',
                title=row[5] or '',
                description=row[6] or '',
                input_data=LocalAgent._parse_json(row[7] or '{}'),
                expected_output=LocalAgent._parse_json(row[8] or '{}'),
                status=row[9] or 'pending',
                priority=row[10] or 0,
                start_time=row[11],
                end_time=row[12],
                execution_time=row[13],
                output_data=LocalAgent._parse_json(row[14] or '{}'),
                is_successful=bool(row[15]) if row[15] is not None else False,
                error_message=row[16] or '',
                logs=row[17] or '',
                created_by=row[18],
                created_at=row[19],
                updated_at=row[20] if len(row) > 20 else None
            )
        return None
    
    def save(self, db_manager):
        """保存到数据库"""
        now = datetime.now().isoformat()
        
        if self.id:
            data = {
                'task_type': self.task_type,
                'title': self.title,
                'description': self.description,
                'input_data': json.dumps(self.input_data),
                'expected_output': json.dumps(self.expected_output),
                'status': self.status,
                'priority': self.priority,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'execution_time': self.execution_time,
                'output_data': json.dumps(self.output_data),
                'is_successful': 1 if self.is_successful else 0,
                'error_message': self.error_message,
                'logs': self.logs,
                'updated_at': now
            }
            db_manager.update(self.TABLE_NAME, data, 'id = ?', (self.id,))
        else:
            data = {
                'task_code': self.task_code,
                'agent_id': self.agent_id,
                'parent_task_id': self.parent_task_id,
                'task_type': self.task_type,
                'title': self.title,
                'description': self.description,
                'input_data': json.dumps(self.input_data),
                'expected_output': json.dumps(self.expected_output),
                'priority': self.priority,
                'created_by': self.created_by,
                'created_at': now,
                'updated_at': now
            }
            self.id = db_manager.insert(self.TABLE_NAME, data)
        
        return self.id
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_code': self.task_code,
            'agent_id': self.agent_id,
            'parent_task_id': self.parent_task_id,
            'task_type': self.task_type,
            'title': self.title,
            'description': self.description,
            'input_data': self.input_data,
            'expected_output': self.expected_output,
            'status': self.status,
            'priority': self.priority,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'execution_time': self.execution_time,
            'output_data': self.output_data,
            'is_successful': self.is_successful,
            'error_message': self.error_message,
            'logs': self.logs,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class AgentConversation:
    """Agent对话记录模型"""
    
    TABLE_NAME = 'agent_conversations'
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.conversation_id = kwargs.get('conversation_id', '')
        self.agent_id = kwargs.get('agent_id')
        self.user_id = kwargs.get('user_id')
        self.messages = kwargs.get('messages', [])
        self.context = kwargs.get('context', {})
        self.summary = kwargs.get('summary', '')
        self.is_active = kwargs.get('is_active', True)
        self.message_count = kwargs.get('message_count', 0)
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
        self.last_message_at = kwargs.get('last_message_at')
    
    @classmethod
    def _get_table_name(cls, db_manager):
        """获取实际的表名（支持加密）"""
        try:
            from app.utils.table_encryption import table_encryption
            return table_encryption.encrypt_table_name(cls.TABLE_NAME)
        except Exception:
            return cls.TABLE_NAME
    
    @classmethod
    def create_table(cls, db_manager):
        """创建表"""
        columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'conversation_id': 'TEXT UNIQUE NOT NULL',
            'agent_id': 'INTEGER NOT NULL',
            'user_id': 'INTEGER',
            'messages': 'TEXT',
            'context': 'TEXT',
            'summary': 'TEXT',
            'is_active': 'INTEGER DEFAULT 1',
            'message_count': 'INTEGER DEFAULT 0',
            'created_at': 'TEXT',
            'updated_at': 'TEXT',
            'last_message_at': 'TEXT'
        }
        db_manager.create_table(cls.TABLE_NAME, columns)
    
    @classmethod
    def get_by_id(cls, db_manager, conversation_id):
        """通过ID获取对话"""
        table_name = cls._get_table_name(db_manager)
        result = db_manager.fetch_one(
            f"SELECT * FROM {table_name} WHERE conversation_id = ?",
            (conversation_id,)
        )
        if result:
            return cls._from_db_row(result)
        return None
    
    @classmethod
    def get_by_agent(cls, db_manager, agent_id):
        """获取Agent的所有对话"""
        table_name = cls._get_table_name(db_manager)
        results = db_manager.fetch_all(
            f"SELECT * FROM {table_name} WHERE agent_id = ? AND is_active = 1",
            (agent_id,)
        )
        return [cls._from_db_row(row) for row in results]
    
    @classmethod
    def _from_db_row(cls, row):
        """从数据库行创建对象"""
        if isinstance(row, dict):
            return cls(
                id=row.get('id'),
                conversation_id=row.get('conversation_id', ''),
                agent_id=row.get('agent_id'),
                user_id=row.get('user_id'),
                messages=LocalAgent._parse_json(row.get('messages', '[]')),
                context=LocalAgent._parse_json(row.get('context', '{}')),
                summary=row.get('summary', ''),
                is_active=bool(row.get('is_active', 1)),
                message_count=row.get('message_count', 0),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
                last_message_at=row.get('last_message_at')
            )
        elif isinstance(row, (tuple, list)) and len(row) >= 12:
            return cls(
                id=row[0],
                conversation_id=row[1] or '',
                agent_id=row[2],
                user_id=row[3],
                messages=LocalAgent._parse_json(row[4] or '[]'),
                context=LocalAgent._parse_json(row[5] or '{}'),
                summary=row[6] or '',
                is_active=bool(row[7]) if row[7] is not None else True,
                message_count=row[8] or 0,
                created_at=row[9],
                updated_at=row[10],
                last_message_at=row[11]
            )
        return None
    
    def save(self, db_manager):
        """保存到数据库"""
        now = datetime.now().isoformat()
        
        if self.id:
            data = {
                'messages': json.dumps(self.messages),
                'context': json.dumps(self.context),
                'summary': self.summary,
                'is_active': 1 if self.is_active else 0,
                'message_count': self.message_count,
                'updated_at': now,
                'last_message_at': self.last_message_at
            }
            db_manager.update(self.TABLE_NAME, data, 'id = ?', (self.id,))
        else:
            data = {
                'conversation_id': self.conversation_id,
                'agent_id': self.agent_id,
                'user_id': self.user_id,
                'messages': json.dumps(self.messages),
                'context': json.dumps(self.context),
                'created_at': now,
                'updated_at': now,
                'last_message_at': now
            }
            self.id = db_manager.insert(self.TABLE_NAME, data)
        
        return self.id
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'agent_id': self.agent_id,
            'user_id': self.user_id,
            'messages': self.messages,
            'context': self.context,
            'summary': self.summary,
            'is_active': self.is_active,
            'message_count': self.message_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_message_at': self.last_message_at
        }


def init_local_agent_tables(db_manager):
    """初始化本地Agent相关的数据库表"""
    LocalAgent.create_table(db_manager)
    AgentTask.create_table(db_manager)
    AgentConversation.create_table(db_manager)
    
    init_default_agents(db_manager)


def init_default_agents(db_manager):
    """初始化默认的本地Agent"""
    default_agents = [
        {
            'agent_name': '系统管理员助手',
            'agent_code': 'AGENT_SYS_ADMIN_001',
            'agent_type': 'system',
            'description': '帮助管理系统配置、监控系统状态的AI助手',
            'capabilities': ['system_command', 'database_access', 'api_call', 'report_generation'],
            'tools': ['system_status', 'config_management', 'log_viewer', 'health_check'],
            'status': 'stopped',
            'llm_model': 'local',
            'temperature': 0.5,
            'requires_auth': True,
            'allowed_roles': ['super_admin', 'admin']
        },
        {
            'agent_name': '代码开发助手',
            'agent_code': 'AGENT_DEV_HELPER_001',
            'agent_type': 'worker',
            'description': '辅助代码开发、调试和优化的AI助手',
            'capabilities': ['code_execution', 'file_management', 'ai_chat', 'data_analysis'],
            'tools': ['code_editor', 'file_browser', 'terminal', 'debugger'],
            'status': 'stopped',
            'llm_model': 'local',
            'temperature': 0.7,
            'requires_auth': True,
            'allowed_roles': ['super_admin', 'admin', 'researcher', 'designer']
        },
        {
            'agent_name': '学习分析助手',
            'agent_code': 'AGENT_LEARNING_001',
            'agent_type': 'assistant',
            'description': '分析学生学习数据、生成学习建议的AI助手',
            'capabilities': ['database_access', 'data_analysis', 'report_generation', 'ai_chat'],
            'tools': ['student_analytics', 'learning_path', 'knowledge_graph', 'recommendation'],
            'status': 'stopped',
            'llm_model': 'local',
            'temperature': 0.6,
            'requires_auth': True,
            'allowed_roles': ['teacher', 'admin', 'super_admin']
        },
        {
            'agent_name': '题库管理助手',
            'agent_code': 'AGENT_QB_HELPER_001',
            'agent_type': 'worker',
            'description': '管理题库、生成题目、优化试题的AI助手',
            'capabilities': ['database_access', 'ai_chat', 'data_analysis', 'report_generation'],
            'tools': ['question_bank', 'question_generator', 'difficulty_analyzer', 'tag_manager'],
            'status': 'stopped',
            'llm_model': 'local',
            'temperature': 0.65,
            'requires_auth': True,
            'allowed_roles': ['teacher', 'admin', 'super_admin']
        },
        {
            'agent_name': '系统监控Agent',
            'agent_code': 'AGENT_MONITOR_001',
            'agent_type': 'monitor',
            'description': '实时监控系统资源使用、检测异常的Agent',
            'capabilities': ['system_command', 'api_call', 'data_analysis'],
            'tools': ['resource_monitor', 'anomaly_detector', 'alert_system', 'performance_tracker'],
            'status': 'stopped',
            'llm_model': 'local',
            'temperature': 0.3,
            'requires_auth': True,
            'allowed_roles': ['super_admin', 'admin']
        }
    ]
    
    for agent_data in default_agents:
        existing = LocalAgent.get_by_code(db_manager, agent_data['agent_code'])
        if not existing:
            agent = LocalAgent(**agent_data)
            agent.save(db_manager)