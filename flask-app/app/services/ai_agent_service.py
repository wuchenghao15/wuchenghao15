#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent管理服务
实现AI员工和AI Agent的自动管理、自动计划和自动进程
"""

import os
import json
import sqlite3
import time
import threading
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum
from app.utils.logging import logger


class AgentStatus(Enum):
    """Agent状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class AgentType(Enum):
    """Agent类型"""
    AI_EMPLOYEE = "ai_employee"
    AI_AGENT = "ai_agent"
    SCHEDULER = "scheduler"
    WORKER = "worker"


class AIAgentService:
    """AI Agent管理服务"""
    
    def __init__(self):
        self._init_tables()
        self._init_default_agents()
        self._running_agents = {}
        self._agent_threads = {}
    
    def _init_tables(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    agent_code TEXT NOT NULL UNIQUE,
                    agent_type TEXT NOT NULL,
                    description TEXT,
                    capabilities TEXT,
                    config TEXT,
                    status TEXT DEFAULT 'inactive',
                    priority INTEGER DEFAULT 0,
                    max_concurrent INTEGER DEFAULT 5,
                    current_tasks INTEGER DEFAULT 0,
                    total_tasks INTEGER DEFAULT 0,
                    successful_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    last_run_time TEXT,
                    next_run_time TEXT,
                    schedule_type TEXT DEFAULT 'manual',
                    schedule_interval INTEGER DEFAULT 60,
                    is_enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    task_code TEXT NOT NULL UNIQUE,
                    task_type TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    description TEXT,
                    params TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    progress INTEGER DEFAULT 0,
                    result TEXT,
                    error_message TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    execution_time INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    schedule_type TEXT NOT NULL,
                    schedule_expression TEXT NOT NULL,
                    description TEXT,
                    is_enabled INTEGER DEFAULT 1,
                    last_executed TEXT,
                    next_execution TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    process_name TEXT NOT NULL,
                    process_pid INTEGER,
                    status TEXT DEFAULT 'stopped',
                    start_time TEXT,
                    end_time TEXT,
                    memory_usage INTEGER DEFAULT 0,
                    cpu_usage REAL DEFAULT 0.0,
                    log_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("AI Agent数据库表初始化完成")
    
    @staticmethod
    def _get_connection():
        """获取数据库连接"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_default_agents(self):
        """初始化默认AI Agent"""
        default_agents = [
            {
                'agent_name': '系统监控Agent',
                'agent_code': 'AGENT_MONITOR_001',
                'agent_type': 'ai_agent',
                'description': '监控系统运行状态、性能指标和异常情况',
                'capabilities': json.dumps(['系统监控', '性能分析', '异常检测', '告警通知']),
                'config': json.dumps({
                    'monitor_interval': 30,
                    'alert_thresholds': {'cpu': 80, 'memory': 85, 'disk': 90},
                    'alert_channels': ['log', 'webhook']
                }),
                'schedule_type': 'periodic',
                'schedule_interval': 60,
                'priority': 1
            },
            {
                'agent_name': '数据备份Agent',
                'agent_code': 'AGENT_BACKUP_001',
                'agent_type': 'ai_agent',
                'description': '自动执行数据库备份和文件备份任务',
                'capabilities': json.dumps(['数据库备份', '文件备份', '备份验证', '备份清理']),
                'config': json.dumps({
                    'backup_interval': 3600,
                    'backup_types': ['primary', 'secondary', 'tertiary'],
                    'retention_days': 7
                }),
                'schedule_type': 'periodic',
                'schedule_interval': 3600,
                'priority': 2
            },
            {
                'agent_name': '日志分析Agent',
                'agent_code': 'AGENT_LOG_001',
                'agent_type': 'ai_agent',
                'description': '分析系统日志，识别异常模式和潜在问题',
                'capabilities': json.dumps(['日志解析', '异常检测', '趋势分析', '报告生成']),
                'config': json.dumps({
                    'log_dir': 'logs/',
                    'analyze_interval': 1800,
                    'alert_level': 'warning'
                }),
                'schedule_type': 'periodic',
                'schedule_interval': 1800,
                'priority': 3
            },
            {
                'agent_name': '数据清理Agent',
                'agent_code': 'AGENT_CLEANUP_001',
                'agent_type': 'ai_agent',
                'description': '清理过期数据、临时文件和缓存',
                'capabilities': json.dumps(['数据清理', '缓存管理', '文件清理', '空间优化']),
                'config': json.dumps({
                    'cleanup_interval': 86400,
                    'cleanup_types': ['temp_files', 'old_logs', 'cache']
                }),
                'schedule_type': 'periodic',
                'schedule_interval': 86400,
                'priority': 4
            },
            {
                'agent_name': '性能优化Agent',
                'agent_code': 'AGENT_OPTIMIZE_001',
                'agent_type': 'ai_agent',
                'description': '自动优化系统性能，调整配置参数',
                'capabilities': json.dumps(['性能分析', '配置优化', '索引优化', '查询优化']),
                'config': json.dumps({
                    'optimize_interval': 86400,
                    'auto_apply': True
                }),
                'schedule_type': 'periodic',
                'schedule_interval': 86400,
                'priority': 5
            },
            {
                'agent_name': '智能调度器',
                'agent_code': 'SCHEDULER_MAIN_001',
                'agent_type': 'scheduler',
                'description': '管理所有Agent的定时任务调度',
                'capabilities': json.dumps(['任务调度', '时间管理', '依赖管理', '并发控制']),
                'config': json.dumps({
                    'check_interval': 30,
                    'max_concurrent_jobs': 10
                }),
                'schedule_type': 'continuous',
                'schedule_interval': 5,
                'priority': 0
            }
        ]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for agent_data in default_agents:
                cursor.execute("SELECT id FROM ai_agents WHERE agent_code = ?", (agent_data['agent_code'],))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO ai_agents 
                        (agent_name, agent_code, agent_type, description, capabilities, 
                         config, schedule_type, schedule_interval, priority)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        agent_data['agent_name'],
                        agent_data['agent_code'],
                        agent_data['agent_type'],
                        agent_data['description'],
                        agent_data['capabilities'],
                        agent_data['config'],
                        agent_data['schedule_type'],
                        agent_data['schedule_interval'],
                        agent_data['priority']
                    ))
    
    def create_agent(self, agent_data: Dict[str, Any]) -> int:
        """创建AI Agent"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_agents 
                    (agent_name, agent_code, agent_type, description, capabilities, 
                     config, schedule_type, schedule_interval, priority, is_enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent_data['agent_name'],
                    agent_data['agent_code'],
                    agent_data['agent_type'],
                    agent_data.get('description', ''),
                    json.dumps(agent_data.get('capabilities', []), ensure_ascii=False),
                    json.dumps(agent_data.get('config', {}), ensure_ascii=False),
                    agent_data.get('schedule_type', 'manual'),
                    agent_data.get('schedule_interval', 60),
                    agent_data.get('priority', 0),
                    agent_data.get('is_enabled', 1)
                ))
                agent_id = cursor.lastrowid
            
            logger.info(f"AI Agent已创建: {agent_data['agent_name']}")
            return agent_id
        except Exception as e:
            logger.error(f"创建AI Agent失败: {e}")
            return -1
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """获取所有AI Agent"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_agents ORDER BY priority, id")
            agents = []
            for row in cursor.fetchall():
                agent = dict(row)
                try:
                    agent['capabilities'] = json.loads(agent['capabilities']) if agent['capabilities'] else []
                    agent['config'] = json.loads(agent['config']) if agent['config'] else {}
                except:
                    agent['capabilities'] = []
                    agent['config'] = {}
                
                agent['schedule_interval'] = agent.get('schedule_interval', 60)
                agent['schedule_type'] = agent.get('schedule_type', 'manual')
                agent['status'] = agent.get('status', 'inactive')
                
                agents.append(agent)
            return agents
    
    def get_agent_by_code(self, agent_code: str) -> Dict[str, Any]:
        """通过代码获取Agent"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_agents WHERE agent_code = ?", (agent_code,))
            row = cursor.fetchone()
            if row:
                agent = dict(row)
                try:
                    agent['capabilities'] = json.loads(agent['capabilities']) if agent['capabilities'] else []
                    agent['config'] = json.loads(agent['config']) if agent['config'] else {}
                except:
                    agent['capabilities'] = []
                    agent['config'] = {}
                return agent
            return {}
    
    def update_agent_status(self, agent_id: int, status: str) -> bool:
        """更新Agent状态"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ai_agents SET status = ?, updated_at = ? WHERE id = ?
                ''', (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), agent_id))
            
            logger.info(f"Agent状态已更新: {agent_id} -> {status}")
            return True
        except Exception as e:
            logger.error(f"更新Agent状态失败: {e}")
            return False
    
    def start_agent(self, agent_id: int) -> bool:
        """启动Agent"""
        try:
            agent = self._get_agent_by_id(agent_id)
            if not agent:
                return False
            
            if agent['agent_code'] in self._running_agents:
                logger.warning(f"Agent已在运行: {agent['agent_name']}")
                return False
            
            self.update_agent_status(agent_id, 'running')
            
            thread = threading.Thread(target=self._run_agent, args=(agent_id,), daemon=True)
            thread.start()
            
            self._running_agents[agent['agent_code']] = {
                'agent_id': agent_id,
                'thread': thread,
                'start_time': datetime.now().isoformat()
            }
            self._agent_threads[agent_id] = thread
            
            logger.info(f"Agent已启动: {agent['agent_name']}")
            return True
        except Exception as e:
            logger.error(f"启动Agent失败: {e}")
            return False
    
    def _get_agent_by_id(self, agent_id: int) -> Dict[str, Any]:
        """通过ID获取Agent"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
            if row:
                agent = dict(row)
                try:
                    agent['capabilities'] = json.loads(agent['capabilities']) if agent['capabilities'] else []
                    agent['config'] = json.loads(agent['config']) if agent['config'] else {}
                except:
                    agent['capabilities'] = []
                    agent['config'] = {}
                return agent
            return {}
    
    def _run_agent(self, agent_id: int):
        """运行Agent"""
        agent = self._get_agent_by_id(agent_id)
        if not agent:
            return
        
        logger.info(f"Agent开始运行: {agent['agent_name']}")
        
        try:
            schedule_type = agent.get('schedule_type', 'manual')
            interval = agent.get('schedule_interval', 60)
            
            while agent['agent_code'] in self._running_agents:
                self._execute_agent_task(agent)
                
                if schedule_type == 'continuous':
                    time.sleep(5)
                elif schedule_type == 'periodic':
                    time.sleep(interval)
                else:
                    break
            
            self.update_agent_status(agent_id, 'stopped')
            if agent['agent_code'] in self._running_agents:
                del self._running_agents[agent['agent_code']]
            
        except Exception as e:
            logger.error(f"Agent运行出错: {agent['agent_name']} - {e}")
            self.update_agent_status(agent_id, 'error')
    
    def _execute_agent_task(self, agent: Dict[str, Any]):
        """执行Agent任务"""
        task_code = f"TASK_{agent['agent_code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task_id = self.create_task(
            agent_id=agent['id'],
            task_type='auto',
            task_name=f"{agent['agent_name']} 自动任务",
            params={'agent_config': agent['config']}
        )
        
        if task_id > 0:
            self.update_task_status(task_id, 'running')
            
            try:
                result = self._perform_agent_action(agent)
                self.update_task_result(task_id, 'completed', result)
                self._update_agent_stats(agent['id'], success=True)
            except Exception as e:
                self.update_task_result(task_id, 'failed', {'error': str(e)})
                self._update_agent_stats(agent['id'], success=False)
    
    def _perform_agent_action(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """执行Agent具体动作"""
        agent_code = agent['agent_code']
        
        if agent_code == 'AGENT_MONITOR_001':
            return self._monitor_system(agent)
        elif agent_code == 'AGENT_BACKUP_001':
            return self._perform_backup(agent)
        elif agent_code == 'AGENT_LOG_001':
            return self._analyze_logs(agent)
        elif agent_code == 'AGENT_CLEANUP_001':
            return self._cleanup_data(agent)
        elif agent_code == 'AGENT_OPTIMIZE_001':
            return self._optimize_system(agent)
        elif agent_code == 'SCHEDULER_MAIN_001':
            return self._run_scheduler(agent)
        
        return {'message': '未知Agent类型'}
    
    def _monitor_system(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """系统监控"""
        import psutil
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        thresholds = agent['config'].get('alert_thresholds', {'cpu': 80, 'memory': 85, 'disk': 90})
        
        alerts = []
        if cpu_percent > thresholds['cpu']:
            alerts.append(f"CPU使用率过高: {cpu_percent}%")
        if memory.percent > thresholds['memory']:
            alerts.append(f"内存使用率过高: {memory.percent}%")
        if disk.percent > thresholds['disk']:
            alerts.append(f"磁盘使用率过高: {disk.percent}%")
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available': round(memory.available / (1024 * 1024 * 1024), 2),
            'disk_percent': disk.percent,
            'disk_free': round(disk.free / (1024 * 1024 * 1024), 2),
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }
    
    def _perform_backup(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """执行备份"""
        from app.services.backup_service import backup_service
        
        backup_types = agent['config'].get('backup_types', ['primary', 'secondary', 'tertiary'])
        results = []
        
        for backup_type in backup_types:
            result = backup_service.create_backup(backup_type)
            results.append(result)
        
        return {'backup_results': results, 'timestamp': datetime.now().isoformat()}
    
    def _analyze_logs(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """分析日志"""
        log_dir = agent['config'].get('log_dir', 'logs/')
        log_files = []
        errors = []
        
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    log_files.append(filename)
                    file_path = os.path.join(log_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()[-50:]
                            for line in lines:
                                if 'ERROR' in line or 'error' in line.lower():
                                    errors.append({'file': filename, 'line': line.strip()[:200]})
                    except:
                        pass
        
        return {
            'log_files_found': len(log_files),
            'errors_found': len(errors),
            'error_samples': errors[:10],
            'timestamp': datetime.now().isoformat()
        }
    
    def _cleanup_data(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """清理数据"""
        cleanup_types = agent['config'].get('cleanup_types', ['temp_files', 'old_logs', 'cache'])
        cleaned_count = 0
        
        for cleanup_type in cleanup_types:
            if cleanup_type == 'temp_files':
                temp_dir = '/tmp'
                if os.path.exists(temp_dir):
                    for filename in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                file_mtime = os.path.getmtime(file_path)
                                if time.time() - file_mtime > 24 * 3600:
                                    os.remove(file_path)
                                    cleaned_count += 1
                        except:
                            pass
        
        return {
            'cleanup_types': cleanup_types,
            'cleaned_files': cleaned_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def _optimize_system(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """优化系统"""
        from app.models.database_version_manager import db_version_manager
        
        optimize_result = db_version_manager.optimize_database('vacuum')
        
        return {
            'optimization_type': 'vacuum',
            'space_saved': optimize_result.get('space_saved', 0),
            'execution_time': optimize_result.get('execution_time', 0),
            'success': optimize_result.get('success', False),
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_scheduler(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """运行调度器"""
        check_interval = agent['config'].get('check_interval', 30)
        
        agents = self.get_all_agents()
        scheduled_count = 0
        
        for ag in agents:
            if ag['id'] == agent['id']:
                continue
            
            if ag['is_enabled'] and ag['status'] == 'inactive':
                schedule_type = ag.get('schedule_type', 'manual')
                if schedule_type == 'periodic':
                    last_run = ag.get('last_run_time')
                    interval = ag.get('schedule_interval', 60)
                    
                    if not last_run or (time.time() - datetime.fromisoformat(last_run.replace('Z', '+00:00')).timestamp() >= interval):
                        self.start_agent(ag['id'])
                        scheduled_count += 1
        
        return {
            'agents_checked': len(agents),
            'agents_scheduled': scheduled_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def stop_agent(self, agent_id: int) -> bool:
        """停止Agent"""
        try:
            agent = self._get_agent_by_id(agent_id)
            if not agent:
                return False
            
            if agent['agent_code'] in self._running_agents:
                del self._running_agents[agent['agent_code']]
            
            if agent_id in self._agent_threads:
                self._agent_threads[agent_id].join(timeout=5)
                del self._agent_threads[agent_id]
            
            self.update_agent_status(agent_id, 'inactive')
            
            logger.info(f"Agent已停止: {agent['agent_name']}")
            return True
        except Exception as e:
            logger.error(f"停止Agent失败: {e}")
            return False
    
    def create_task(self, agent_id: int, task_type: str, task_name: str, 
                    params: Dict[str, Any] = None) -> int:
        """创建任务"""
        try:
            task_code = f"TASK_{agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO agent_tasks 
                    (agent_id, task_code, task_type, task_name, params)
                    VALUES (?, ?, ?, ?, ?)
                ''', (agent_id, task_code, task_type, task_name, json.dumps(params or {}, ensure_ascii=False)))
                
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return -1
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """更新任务状态"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE agent_tasks SET status = ?, updated_at = ? WHERE id = ?
                ''', (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), task_id))
            
            return True
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False
    
    def update_task_result(self, task_id: int, status: str, result: Dict[str, Any]) -> bool:
        """更新任务结果"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE agent_tasks SET status = ?, result = ?, end_time = ?, updated_at = ? WHERE id = ?
                ''', (status, json.dumps(result, ensure_ascii=False), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), task_id))
            
            return True
        except Exception as e:
            logger.error(f"更新任务结果失败: {e}")
            return False
    
    def _update_agent_stats(self, agent_id: int, success: bool) -> bool:
        """更新Agent统计"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if success:
                    cursor.execute('''
                        UPDATE ai_agents SET total_tasks = total_tasks + 1, successful_tasks = successful_tasks + 1, 
                        last_run_time = ?, updated_at = ? WHERE id = ?
                    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), agent_id))
                else:
                    cursor.execute('''
                        UPDATE ai_agents SET total_tasks = total_tasks + 1, failed_tasks = failed_tasks + 1, 
                        last_run_time = ?, updated_at = ? WHERE id = ?
                    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), agent_id))
            
            return True
        except Exception as e:
            logger.error(f"更新Agent统计失败: {e}")
            return False
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        agents = self.get_all_agents()
        
        status = {
            'total_agents': len(agents),
            'running_agents': len(self._running_agents),
            'agents_by_type': {},
            'agents_by_status': {},
            'running_details': {}
        }
        
        for agent in agents:
            agent_type = agent['agent_type']
            agent_status = agent['status']
            
            status['agents_by_type'][agent_type] = status['agents_by_type'].get(agent_type, 0) + 1
            status['agents_by_status'][agent_status] = status['agents_by_status'].get(agent_status, 0) + 1
            
            if agent['agent_code'] in self._running_agents:
                status['running_details'][agent['agent_name']] = {
                    'agent_code': agent['agent_code'],
                    'start_time': self._running_agents[agent['agent_code']]['start_time'],
                    'total_tasks': agent['total_tasks'],
                    'success_rate': round((agent['successful_tasks'] / max(agent['total_tasks'], 1)) * 100, 2)
                }
        
        return status
    
    def start_all_enabled_agents(self) -> int:
        """启动所有已启用的Agent"""
        agents = self.get_all_agents()
        started_count = 0
        
        for agent in agents:
            if agent['is_enabled'] and agent['status'] == 'inactive':
                if self.start_agent(agent['id']):
                    started_count += 1
        
        logger.info(f"已启动 {started_count} 个Agent")
        return started_count


ai_agent_service = AIAgentService()