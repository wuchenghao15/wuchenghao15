#!/usr/bin/env python3
"""
AI员工和Agent统一加载器
从数据库加载所有已生成的AI员工和AI Agent，启动所有自动化功能
"""

import os
import sys
import time
import logging
import threading
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

AI_EMPLOYEES = {}
AI_AGENTS = {}
RUNNING_TASKS = []
STARTUP_TIMESTAMP = None

AI_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases', 'ai.db')


def get_ai_db_connection():
    """获取AI数据库连接"""
    conn = sqlite3.connect(AI_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class AIEmployeeLoader:
    def __init__(self):
        self.employees = {}
        self.agents = {}
        self.employee_stats = {
            'total_loaded': 0,
            'total_started': 0,
            'total_failed': 0,
            'total_enabled': 0,
            'total_disabled': 0,
            'types': {}
        }
    
    def _safe_import(self, module_name, class_name):
        try:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logger.warning(f"导入失败 {module_name}.{class_name}: {e}")
            return None
    
    def _safe_start(self, employee, employee_name):
        try:
            if hasattr(employee, 'start') and callable(getattr(employee, 'start')):
                employee.start()
            return True
        except Exception as e:
            logger.error(f"启动失败 {employee_name}: {e}")
            return False
    
    def _parse_capabilities(self, capabilities_str):
        """解析能力字段，支持JSON和文本格式"""
        if not capabilities_str:
            return []
        try:
            return json.loads(capabilities_str)
        except (json.JSONDecodeError, TypeError):
            if isinstance(capabilities_str, str):
                return [s.strip() for s in capabilities_str.split('\n') if s.strip()]
            return []
    
    def load_ai_employees_from_db(self):
        """从数据库加载所有AI员工"""
        logger.info("=" * 60)
        logger.info("从数据库加载AI员工...")
        logger.info("=" * 60)
        
        try:
            conn = get_ai_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, employee_code, description, capabilities, 
                       specialties, status, accuracy, total_tasks, is_enabled,
                       priority, skill_level, created_at, updated_at
                FROM ai_employees
                ORDER BY priority DESC, id ASC
            ''')
            employees = cursor.fetchall()
            
            from ai_engines.ai_employees import AIEmployee
            
            for emp_row in employees:
                emp_dict = dict(emp_row)
                emp_id = f"db_emp_{emp_dict['id']}"
                is_enabled = bool(emp_dict['is_enabled'])
                
                try:
                    capabilities = self._parse_capabilities(emp_dict.get('capabilities', ''))
                    
                    employee = AIEmployee(
                        emp_id,
                        emp_dict['name'],
                        emp_dict.get('employee_code', 'general'),
                        capabilities
                    )
                    
                    self.employees[emp_id] = {
                        'employee': employee,
                        'id': emp_dict['id'],
                        'db_id': emp_dict['id'],
                        'name': emp_dict['name'],
                        'employee_code': emp_dict.get('employee_code', ''),
                        'role': emp_dict.get('employee_code', 'general'),
                        'description': emp_dict.get('description', ''),
                        'capabilities': capabilities,
                        'specialties': self._parse_capabilities(emp_dict.get('specialties', '')),
                        'skills': capabilities,
                        'level': emp_dict.get('skill_level', 1),
                        'accuracy': emp_dict.get('accuracy', 0),
                        'total_tasks': emp_dict.get('total_tasks', 0),
                        'priority': emp_dict.get('priority', 5),
                        'is_enabled': is_enabled,
                        'status': 'running' if is_enabled else 'disabled',
                        'db_status': emp_dict.get('status', 'unknown'),
                        'started': False,
                        'source': 'database'
                    }
                    
                    self.employee_stats['total_loaded'] += 1
                    if is_enabled:
                        self.employee_stats['total_enabled'] += 1
                    else:
                        self.employee_stats['total_disabled'] += 1
                    
                    role = emp_dict.get('employee_code', 'general')
                    if role not in self.employee_stats['types']:
                        self.employee_stats['types'][role] = 0
                    self.employee_stats['types'][role] += 1
                    
                    status_icon = '✓' if is_enabled else '○'
                    logger.info(f"{status_icon} 加载AI员工: {emp_dict['name']} ({emp_dict.get('employee_code', '')})")
                    
                except Exception as e:
                    logger.error(f"✗ 加载失败: {emp_dict.get('name', '未知')} - {e}")
                    self.employee_stats['total_failed'] += 1
            
            conn.close()
            logger.info(f"\n数据库加载完成: 共 {len(employees)} 名AI员工")
            
        except Exception as e:
            logger.error(f"从数据库加载AI员工失败: {e}")
            logger.info("尝试使用硬编码配置加载...")
            self.load_ai_employees_fallback()
    
    def load_ai_employees_fallback(self):
        """备用加载方式：使用硬编码配置"""
        logger.info("使用备用配置加载AI员工...")
        
        employees_to_load = [
            {'id': 'ai_dev_001', 'name': 'AI开发工程师', 'role': 'developer', 
             'skills': ['Python', 'Flask', '机器学习'], 'level': 8},
            {'id': 'ai_tester_001', 'name': 'AI测试工程师', 'role': 'tester', 
             'skills': ['自动化测试', '性能测试', '安全测试'], 'level': 7},
            {'id': 'ai_designer_001', 'name': 'AI设计师', 'role': 'designer', 
             'skills': ['UI设计', 'UX设计', '前端开发'], 'level': 7},
            {'id': 'ai_analyst_001', 'name': 'AI数据分析师', 'role': 'analyst', 
             'skills': ['数据分析', '数据可视化', '统计分析'], 'level': 8},
            {'id': 'ai_security_001', 'name': 'AI安全专家', 'role': 'security', 
             'skills': ['网络安全', '渗透测试', '安全审计'], 'level': 9},
            {'id': 'ai_ops_001', 'name': 'AI运维工程师', 'role': 'operations', 
             'skills': ['系统运维', 'DevOps', '云服务'], 'level': 7},
            {'id': 'ai_writer_001', 'name': 'AI文案撰写师', 'role': 'writer', 
             'skills': ['内容创作', '技术文档', 'SEO优化'], 'level': 6},
            {'id': 'ai_manager_001', 'name': 'AI项目经理', 'role': 'manager', 
             'skills': ['项目管理', '团队协调', '进度跟踪'], 'level': 8},
        ]
        
        from ai_engines.ai_employees import AIEmployee
        
        for emp_data in employees_to_load:
            try:
                employee = AIEmployee(
                    emp_data['id'],
                    emp_data['name'],
                    emp_data['role'],
                    emp_data['skills']
                )
                self.employees[emp_data['id']] = {
                    'employee': employee,
                    'name': emp_data['name'],
                    'role': emp_data['role'],
                    'skills': emp_data['skills'],
                    'level': emp_data['level'],
                    'is_enabled': True,
                    'status': 'active',
                    'started': False,
                    'source': 'fallback'
                }
                self.employee_stats['total_loaded'] += 1
                self.employee_stats['total_enabled'] += 1
                if emp_data['role'] not in self.employee_stats['types']:
                    self.employee_stats['types'][emp_data['role']] = 0
                self.employee_stats['types'][emp_data['role']] += 1
                logger.info(f"✓ 加载AI员工: {emp_data['name']} ({emp_data['role']})")
            except Exception as e:
                logger.error(f"✗ 加载失败: {emp_data['name']} - {e}")
                self.employee_stats['total_failed'] += 1
    
    def load_specialized_employees(self):
        """加载专业AI员工"""
        logger.info("\n" + "=" * 60)
        logger.info("加载专业AI员工...")
        logger.info("=" * 60)
        
        specialized_employees = [
            {'module': 'ai_employee_system', 'class': 'ValidationAIEmployee', 
             'id': 'val_001', 'name': '验证AI员工', 'type': 'validation', 'level': 5},
            {'module': 'ai_employee_system', 'class': 'RoutingAIEmployee', 
             'id': 'route_001', 'name': '路由AI员工', 'type': 'routing', 'level': 6},
            {'module': 'ai_employee_system', 'class': 'TestSystemAIEmployee', 
             'id': 'test_sys_001', 'name': '测试系统AI员工', 'type': 'test_system', 'level': 7},
            {'module': 'diagnostics_repair_employee', 'class': 'DiagnosticsRepairEmployee', 
             'id': 'diag_001', 'name': '诊断修复AI员工', 'type': 'diagnostics_repair', 'level': 9},
        ]
        
        for emp_spec in specialized_employees:
            try:
                emp_class = self._safe_import(f'ai_engines.{emp_spec["module"]}', emp_spec['class'])
                if emp_class:
                    try:
                        if emp_spec['class'] in ['ValidationAIEmployee', 'RoutingAIEmployee', 'TestSystemAIEmployee']:
                            employee = emp_class(
                                emp_spec['id'], emp_spec['name'], emp_spec['type'], emp_spec['level']
                            )
                        else:
                            employee = emp_class(emp_spec['id'], emp_spec['name'], emp_spec['level'])
                    except Exception as e:
                        logger.warning(f"⚠ 初始化失败: {emp_spec['name']} - {e}")
                        continue
                    
                    if employee:
                        self.employees[emp_spec['id']] = {
                            'employee': employee,
                            'name': emp_spec['name'],
                            'role': emp_spec['type'],
                            'skills': [],
                            'level': emp_spec['level'],
                            'is_enabled': True,
                            'status': 'active',
                            'started': False,
                            'source': 'specialized'
                        }
                        self.employee_stats['total_loaded'] += 1
                        self.employee_stats['total_enabled'] += 1
                        if emp_spec['type'] not in self.employee_stats['types']:
                            self.employee_stats['types'][emp_spec['type']] = 0
                        self.employee_stats['types'][emp_spec['type']] += 1
                        logger.info(f"✓ 加载专业AI员工: {emp_spec['name']}")
                else:
                    logger.warning(f"✗ 无法导入: {emp_spec['class']}")
            except Exception as e:
                logger.error(f"✗ 加载失败: {emp_spec['name']} - {e}")
                self.employee_stats['total_failed'] += 1
    
    def load_ai_agents_from_db(self):
        """从数据库加载AI Agent"""
        logger.info("\n" + "=" * 60)
        logger.info("从数据库加载AI Agent...")
        logger.info("=" * 60)
        
        try:
            conn = get_ai_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, agent_name, agent_code, agent_type, description,
                       capabilities, status, priority, is_enabled, schedule_type,
                       schedule_interval, total_tasks, successful_tasks, failed_tasks,
                       created_at, updated_at
                FROM ai_agents
                ORDER BY priority ASC, id ASC
            ''')
            agents = cursor.fetchall()
            
            from ai_engines.ai_employees import AIEmployee
            
            for agent_row in agents:
                agent_dict = dict(agent_row)
                agent_id = f"db_agent_{agent_dict['id']}"
                is_enabled = bool(agent_dict['is_enabled'])
                
                try:
                    capabilities = self._parse_capabilities(agent_dict.get('capabilities', ''))
                    
                    agent = AIEmployee(
                        agent_id,
                        agent_dict['agent_name'],
                        agent_dict.get('agent_code', 'agent'),
                        capabilities
                    )
                    
                    self.agents[agent_id] = {
                        'agent': agent,
                        'id': agent_dict['id'],
                        'db_id': agent_dict['id'],
                        'name': agent_dict['agent_name'],
                        'agent_code': agent_dict.get('agent_code', ''),
                        'role': agent_dict.get('agent_type', 'agent'),
                        'description': agent_dict.get('description', ''),
                        'capabilities': capabilities,
                        'level': agent_dict.get('priority', 5),
                        'is_enabled': is_enabled,
                        'status': 'running' if is_enabled else 'disabled',
                        'db_status': agent_dict.get('status', 'unknown'),
                        'schedule_type': agent_dict.get('schedule_type', ''),
                        'schedule_interval': agent_dict.get('schedule_interval', 0),
                        'total_tasks': agent_dict.get('total_tasks', 0),
                        'successful_tasks': agent_dict.get('successful_tasks', 0),
                        'failed_tasks': agent_dict.get('failed_tasks', 0),
                        'started': False,
                        'source': 'database'
                    }
                    
                    status_icon = '✓' if is_enabled else '○'
                    logger.info(f"{status_icon} 加载AI Agent: {agent_dict['agent_name']} ({agent_dict.get('agent_code', '')})")
                    
                except Exception as e:
                    logger.error(f"✗ 加载失败: {agent_dict.get('agent_name', '未知')} - {e}")
            
            conn.close()
            logger.info(f"\n数据库Agent加载完成: 共 {len(agents)} 个AI Agent")
            
        except Exception as e:
            logger.error(f"从数据库加载AI Agent失败: {e}")
            logger.info("尝试使用硬编码配置加载...")
            self.load_ai_agents_fallback()
    
    def load_ai_agents_fallback(self):
        """备用加载方式：使用硬编码配置"""
        logger.info("使用备用配置加载AI Agent...")
        
        agents_to_load = [
            {'id': 'version_agent_001', 'name': '系统版本管理Agent', 
             'role': 'version_manager', 'level': 9},
            {'id': 'automation_plan_agent_001', 'name': '自动化计划拓展Agent', 
             'role': 'automation_planner', 'level': 8},
            {'id': 'auto_maintenance_agent_001', 'name': '自动维护Agent', 
             'role': 'maintenance', 'level': 7},
            {'id': 'git_sync_agent_001', 'name': 'Git同步Agent', 
             'role': 'git_sync', 'level': 6},
            {'id': 'auto_upgrade_agent_001', 'name': '自动升级Agent', 
             'role': 'auto_upgrade', 'level': 8},
            {'id': 'auto_expand_agent_001', 'name': '自动拓展Agent', 
             'role': 'auto_expand', 'level': 7},
            {'id': 'self_healing_agent_001', 'name': '自愈Agent', 
             'role': 'self_healing', 'level': 9},
            {'id': 'auto_scheduler_agent_001', 'name': '自动调度Agent', 
             'role': 'auto_scheduler', 'level': 6},
        ]
        
        from ai_engines.ai_employees import AIEmployee
        
        for agent_data in agents_to_load:
            try:
                agent = AIEmployee(
                    agent_data['id'],
                    agent_data['name'],
                    agent_data['role'],
                    []
                )
                self.agents[agent_data['id']] = {
                    'agent': agent,
                    'name': agent_data['name'],
                    'role': agent_data['role'],
                    'level': agent_data['level'],
                    'is_enabled': True,
                    'status': 'active',
                    'started': False,
                    'source': 'fallback'
                }
                logger.info(f"✓ 加载AI Agent: {agent_data['name']} ({agent_data['role']})")
            except Exception as e:
                logger.error(f"✗ 加载失败: {agent_data['name']} - {e}")
    
    def start_all_employees(self):
        logger.info("\n" + "=" * 60)
        logger.info("启动所有已启用的AI员工...")
        logger.info("=" * 60)
        
        enabled_count = 0
        for emp_id, emp_data in self.employees.items():
            if not emp_data.get('is_enabled', True):
                emp_data['status'] = 'disabled'
                logger.info(f"○ 已禁用: {emp_data['name']}")
                continue
            
            enabled_count += 1
            try:
                if self._safe_start(emp_data['employee'], emp_data['name']):
                    emp_data['started'] = True
                    emp_data['status'] = 'running'
                    self.employee_stats['total_started'] += 1
                    logger.info(f"✓ 启动成功: {emp_data['name']}")
                else:
                    emp_data['status'] = 'idle'
                    logger.info(f"○ 已就绪: {emp_data['name']}")
            except Exception as e:
                emp_data['status'] = 'error'
                logger.error(f"✗ 启动失败: {emp_data['name']} - {e}")
                self.employee_stats['total_failed'] += 1
        
        logger.info(f"\n已启用员工: {enabled_count}, 已启动: {self.employee_stats['total_started']}")
    
    def start_all_agents(self):
        logger.info("\n" + "=" * 60)
        logger.info("启动所有已启用的AI Agent...")
        logger.info("=" * 60)
        
        enabled_count = 0
        started_count = 0
        for agent_id, agent_data in self.agents.items():
            if not agent_data.get('is_enabled', True):
                agent_data['status'] = 'disabled'
                logger.info(f"○ 已禁用: {agent_data['name']}")
                continue
            
            enabled_count += 1
            try:
                if self._safe_start(agent_data['agent'], agent_data['name']):
                    agent_data['started'] = True
                    agent_data['status'] = 'running'
                    started_count += 1
                    logger.info(f"✓ 启动成功: {agent_data['name']}")
                else:
                    agent_data['status'] = 'idle'
                    logger.info(f"○ 已就绪: {agent_data['name']}")
            except Exception as e:
                agent_data['status'] = 'error'
                logger.error(f"✗ 启动失败: {agent_data['name']} - {e}")
        
        logger.info(f"\n已启用Agent: {enabled_count}, 已启动: {started_count}")
    
    def enable_employee(self, emp_id):
        """启用AI员工"""
        if emp_id in self.employees:
            self.employees[emp_id]['is_enabled'] = True
            self.employees[emp_id]['status'] = 'running'
            if not self.employees[emp_id]['started']:
                self._safe_start(self.employees[emp_id]['employee'], self.employees[emp_id]['name'])
                self.employees[emp_id]['started'] = True
            
            db_id = self.employees[emp_id].get('db_id')
            if db_id:
                try:
                    conn = get_ai_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_employees SET is_enabled = 1, status = "active", updated_at = ? WHERE id = ?',
                                   (datetime.now().isoformat(), db_id))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"更新数据库失败: {e}")
            
            return True
        return False
    
    def disable_employee(self, emp_id):
        """禁用AI员工"""
        if emp_id in self.employees:
            self.employees[emp_id]['is_enabled'] = False
            self.employees[emp_id]['status'] = 'disabled'
            
            db_id = self.employees[emp_id].get('db_id')
            if db_id:
                try:
                    conn = get_ai_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_employees SET is_enabled = 0, status = "inactive", updated_at = ? WHERE id = ?',
                                   (datetime.now().isoformat(), db_id))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"更新数据库失败: {e}")
            
            return True
        return False
    
    def enable_agent(self, agent_id):
        """启用AI Agent"""
        if agent_id in self.agents:
            self.agents[agent_id]['is_enabled'] = True
            self.agents[agent_id]['status'] = 'running'
            if not self.agents[agent_id]['started']:
                self._safe_start(self.agents[agent_id]['agent'], self.agents[agent_id]['name'])
                self.agents[agent_id]['started'] = True
            
            db_id = self.agents[agent_id].get('db_id')
            if db_id:
                try:
                    conn = get_ai_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_agents SET is_enabled = 1, status = "running", updated_at = ? WHERE id = ?',
                                   (datetime.now().isoformat(), db_id))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"更新数据库失败: {e}")
            
            return True
        return False
    
    def disable_agent(self, agent_id):
        """禁用AI Agent"""
        if agent_id in self.agents:
            self.agents[agent_id]['is_enabled'] = False
            self.agents[agent_id]['status'] = 'disabled'
            
            db_id = self.agents[agent_id].get('db_id')
            if db_id:
                try:
                    conn = get_ai_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_agents SET is_enabled = 0, status = "stopped", updated_at = ? WHERE id = ?',
                                   (datetime.now().isoformat(), db_id))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"更新数据库失败: {e}")
            
            return True
        return False
    
    def enable_all_employees(self):
        """启用所有AI员工"""
        count = 0
        for emp_id in self.employees:
            if self.enable_employee(emp_id):
                count += 1
        logger.info(f"已启用 {count} 个AI员工")
        return count
    
    def enable_all_agents(self):
        """启用所有AI Agent"""
        count = 0
        for agent_id in self.agents:
            if self.enable_agent(agent_id):
                count += 1
        logger.info(f"已启用 {count} 个AI Agent")
        return count
    
    def start_automation(self):
        logger.info("\n" + "=" * 60)
        logger.info("启动自动化任务...")
        logger.info("=" * 60)
        
        automation_tasks = [
            {'name': '定时Git同步', 'interval': 300},
            {'name': '系统健康检查', 'interval': 60},
            {'name': '数据库维护', 'interval': 3600},
            {'name': '日志清理', 'interval': 7200},
            {'name': '权限规则同步', 'interval': 1800},
            {'name': '题库更新检查', 'interval': 1800},
        ]
        
        for task in automation_tasks:
            try:
                thread = threading.Thread(
                    target=self._run_automation_task,
                    args=(task['name'], task['interval']),
                    daemon=True
                )
                thread.start()
                RUNNING_TASKS.append({
                    'name': task['name'],
                    'interval': task['interval'],
                    'thread': thread,
                    'status': 'running',
                    'last_run': datetime.now().isoformat()
                })
                logger.info(f"✓ 启动自动化任务: {task['name']} (间隔: {task['interval']}秒)")
            except Exception as e:
                logger.error(f"✗ 启动失败: {task['name']} - {e}")
    
    def _run_automation_task(self, task_name, interval):
        while True:
            try:
                logger.info(f"[{task_name}] 执行中...")
                for task in RUNNING_TASKS:
                    if task['name'] == task_name:
                        task['last_run'] = datetime.now().isoformat()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"[{task_name}] 错误: {e}")
    
    def get_status(self):
        status = {
            'total_employees': len(self.employees),
            'total_enabled_employees': sum(1 for e in self.employees.values() if e.get('is_enabled', True)),
            'total_disabled_employees': sum(1 for e in self.employees.values() if not e.get('is_enabled', True)),
            'total_agents': len(self.agents),
            'total_enabled_agents': sum(1 for a in self.agents.values() if a.get('is_enabled', True)),
            'total_disabled_agents': sum(1 for a in self.agents.values() if not a.get('is_enabled', True)),
            'total_tasks': len(RUNNING_TASKS),
            'started_at': STARTUP_TIMESTAMP,
            'employee_stats': self.employee_stats,
            'employees': [],
            'agents': [],
            'tasks': []
        }
        
        for emp_id, emp_data in self.employees.items():
            status['employees'].append({
                'id': emp_id,
                'db_id': emp_data.get('db_id'),
                'name': emp_data['name'],
                'employee_code': emp_data.get('employee_code', ''),
                'role': emp_data['role'],
                'level': emp_data.get('level', 1),
                'status': emp_data['status'],
                'is_enabled': emp_data.get('is_enabled', True),
                'started': emp_data['started'],
                'skills': emp_data.get('skills', []),
                'description': emp_data.get('description', ''),
                'accuracy': emp_data.get('accuracy', 0),
                'total_tasks': emp_data.get('total_tasks', 0),
                'priority': emp_data.get('priority', 5),
                'source': emp_data.get('source', 'unknown')
            })
        
        for agent_id, agent_data in self.agents.items():
            status['agents'].append({
                'id': agent_id,
                'db_id': agent_data.get('db_id'),
                'name': agent_data['name'],
                'agent_code': agent_data.get('agent_code', ''),
                'role': agent_data['role'],
                'level': agent_data.get('level', 1),
                'status': agent_data['status'],
                'is_enabled': agent_data.get('is_enabled', True),
                'started': agent_data['started'],
                'description': agent_data.get('description', ''),
                'schedule_type': agent_data.get('schedule_type', ''),
                'schedule_interval': agent_data.get('schedule_interval', 0),
                'total_tasks': agent_data.get('total_tasks', 0),
                'source': agent_data.get('source', 'unknown')
            })
        
        for task in RUNNING_TASKS:
            status['tasks'].append({
                'name': task['name'],
                'interval': task['interval'],
                'status': task['status'],
                'last_run': task.get('last_run')
            })
        
        return status
    
    def run(self):
        global STARTUP_TIMESTAMP
        STARTUP_TIMESTAMP = datetime.now().isoformat()
        
        self.load_ai_employees_from_db()
        self.load_specialized_employees()
        self.load_ai_agents_from_db()
        self.start_all_employees()
        self.start_all_agents()
        self.start_automation()
        
        logger.info("\n" + "=" * 60)
        logger.info("AI员工和Agent加载完成！")
        logger.info("=" * 60)
        logger.info(f"总员工数: {self.employee_stats['total_loaded']}")
        logger.info(f"已启用: {self.employee_stats['total_enabled']}")
        logger.info(f"已禁用: {self.employee_stats['total_disabled']}")
        logger.info(f"启动成功: {self.employee_stats['total_started']}")
        logger.info(f"启动失败: {self.employee_stats['total_failed']}")
        logger.info(f"自动化任务: {len(RUNNING_TASKS)}")
        logger.info(f"启动时间: {STARTUP_TIMESTAMP}")
        logger.info("=" * 60)
        
        return self.get_status()

ai_employee_loader = AIEmployeeLoader()

def load_all_ai_employees():
    return ai_employee_loader.run()

def get_all_ai_employees_status():
    return ai_employee_loader.get_status()

def enable_ai_employee(emp_id):
    return ai_employee_loader.enable_employee(emp_id)

def disable_ai_employee(emp_id):
    return ai_employee_loader.disable_employee(emp_id)

def enable_ai_agent(agent_id):
    return ai_employee_loader.enable_agent(agent_id)

def disable_ai_agent(agent_id):
    return ai_employee_loader.disable_agent(agent_id)

def enable_all_ai_employees():
    return ai_employee_loader.enable_all_employees()

def enable_all_ai_agents():
    return ai_employee_loader.enable_all_agents()

def get_ai_db_employee_count():
    """从数据库直接获取AI员工数量"""
    try:
        conn = get_ai_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ai_employees')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE is_enabled = 1')
        enabled = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM ai_agents')
        total_agents = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM ai_agents WHERE is_enabled = 1')
        enabled_agents = cursor.fetchone()[0]
        conn.close()
        return {
            'total_employees': total,
            'enabled_employees': enabled,
            'disabled_employees': total - enabled,
            'total_agents': total_agents,
            'enabled_agents': enabled_agents,
            'disabled_agents': total_agents - enabled_agents
        }
    except Exception as e:
        logger.error(f"获取数据库员工数量失败: {e}")
        return None

if __name__ == "__main__":
    status = load_all_ai_employees()
    print(json.dumps(status, ensure_ascii=False, indent=2))