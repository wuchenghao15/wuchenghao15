# -*- coding: utf-8 -*-
"""
自动规则引擎
支持AI员工自动触发规则执行操作，实现自动化运维和任务处理
"""

import os
import json
import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)


class RuleCondition:
    """规则条件"""
    
    OPERATORS = {
        'equals': lambda a, b: a == b,
        'not_equals': lambda a, b: a != b,
        'greater_than': lambda a, b: a > b if a is not None else False,
        'less_than': lambda a, b: a < b if a is not None else False,
        'greater_or_equal': lambda a, b: a >= b if a is not None else False,
        'less_or_equal': lambda a, b: a <= b if a is not None else False,
        'contains': lambda a, b: b in str(a) if a is not None else False,
        'not_contains': lambda a, b: b not in str(a) if a is not None else True,
        'regex_match': lambda a, b: bool(__import__('re').search(str(b), str(a))) if a is not None else False,
        'exists': lambda a, b: a is not None,
        'not_exists': lambda a, b: a is None,
        'in_list': lambda a, b: a in b if a is not None else False,
        'not_in_list': lambda a, b: a not in b if a is not None else True,
        'between': lambda a, b: b[0] <= a <= b[1] if a is not None else False
    }
    
    def __init__(self, field: str, operator: str, value: Any):
        self.field = field
        self.operator = operator
        self.value = value
    
    def evaluate(self, context: Dict) -> bool:
        """评估条件是否满足"""
        try:
            field_value = context.get(self.field)
            
            # 处理字段不存在于上下文中的情况
            if field_value is None and self.field not in context:
                # 如果字段不存在，根据操作符类型决定返回值
                if self.operator in ['not_exists', 'equals']:
                    # 对于 not_exists 操作，字段不存在应返回 True
                    # 对于 equals 操作，如果期望值也是 None，则为 True
                    if self.operator == 'equals' and self.value is None:
                        return True
                    # 其他情况下，字段不存在返回 False
                    return False
            
            op_func = self.OPERATORS.get(self.operator)
            if not op_func:
                logger.error(f"未知操作符: {self.operator}")
                return False
            
            return op_func(field_value, self.value)
        
        except Exception as e:
            logger.error(f"条件评估失败: {e}")
            return False


class RuleAction:
    """规则动作"""
    
    ACTION_TYPES = [
        'dispatch_task',
        'send_message',
        'create_employee',
        'trigger_batch_task',
        'update_status',
        'notify_admin',
        'execute_shell',
        'call_api'
    ]
    
    def __init__(self, action_type: str, params: Dict):
        self.action_type = action_type
        self.params = params
    
    def execute(self, context: Dict) -> Dict:
        """执行动作"""
        try:
            if self.action_type == 'dispatch_task':
                return self._execute_dispatch_task(context)
            elif self.action_type == 'send_message':
                return self._execute_send_message(context)
            elif self.action_type == 'create_employee':
                return self._execute_create_employee(context)
            elif self.action_type == 'trigger_batch_task':
                return self._execute_trigger_batch_task(context)
            elif self.action_type == 'update_status':
                return self._execute_update_status(context)
            elif self.action_type == 'notify_admin':
                return self._execute_notify_admin(context)
            elif self.action_type == 'execute_shell':
                return self._execute_execute_shell(context)
            elif self.action_type == 'call_api':
                return self._execute_call_api(context)
            else:
                return {'success': False, 'error': f"未知动作类型: {self.action_type}"}
        
        except Exception as e:
            logger.error(f"动作执行失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_dispatch_task(self, context: Dict) -> Dict:
        """分派任务给AI员工"""
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            if not integration:
                return {'success': False, 'error': '集成控制器未初始化'}
            
            task_type = self.params.get('task_type', 'general')
            task_data = self.params.get('task_data', {})
            employee_template = self.params.get('employee_template')
            
            task_data.update({
                'triggered_by_rule': True,
                'rule_context': context
            })
            
            task = {
                'task_type': task_type,
                'task_data': task_data,
                'agent_code': 'auto_rule_engine',
                'timestamp': datetime.now().isoformat()
            }
            
            result = integration.dispatch_task_to_employee(
                'auto_rule_engine',
                task,
                employee_template
            )
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_send_message(self, context: Dict) -> Dict:
        """发送消息"""
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            if not integration:
                return {'success': False, 'error': '集成控制器未初始化'}
            
            to_employee_id = self.params.get('to_employee_id')
            message_type = self.params.get('message_type', 'knowledge_share')
            content = self.params.get('content', {})
            
            content.update({
                'triggered_by_rule': True,
                'rule_context': context
            })
            
            message = {
                'type': message_type,
                'content': content,
                'from': 'auto_rule_engine',
                'timestamp': datetime.now().isoformat()
            }
            
            result = integration.send_message_between_agents(
                'auto_rule_engine',
                to_employee_id,
                message
            )
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_create_employee(self, context: Dict) -> Dict:
        """创建AI员工"""
        try:
            from app.ai.ai_employee_enhanced_system import get_enhanced_system
            
            system = get_enhanced_system()
            if not system:
                return {'success': False, 'error': 'AI员工系统未初始化'}
            
            template_key = self.params.get('template_key', 'code_fixer')
            level = self.params.get('level', 'specialist')
            
            result = system.create_full_employee(template_key, level)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_trigger_batch_task(self, context: Dict) -> Dict:
        """触发批量任务"""
        try:
            from app.agents.batch_task_manager import get_batch_manager
            
            manager = get_batch_manager()
            
            task_type = self.params.get('task_type', 'code_fix')
            tasks = self.params.get('tasks', [])
            employee_template = self.params.get('employee_template')
            
            batch_id = manager.create_batch_task(
                agent_code='auto_rule_engine',
                task_type=task_type,
                tasks=tasks
            )
            
            if not batch_id:
                return {'success': False, 'error': '创建批量任务失败'}
            
            dispatch_result = manager.dispatch_batch_task(batch_id, employee_template)
            
            return {
                'success': True,
                'batch_id': batch_id,
                'dispatch_result': dispatch_result
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_update_status(self, context: Dict) -> Dict:
        """更新状态"""
        try:
            return {
                'success': True,
                'action': 'update_status',
                'params': self.params,
                'context': context
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_notify_admin(self, context: Dict) -> Dict:
        """通知管理员"""
        try:
            logger.info(f"[规则引擎] 管理员通知: {self.params.get('message', '系统异常')}")
            return {
                'success': True,
                'action': 'notify_admin',
                'message': self.params.get('message', '系统异常'),
                'context': context
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_execute_shell(self, context: Dict) -> Dict:
        """执行Shell命令"""
        try:
            import subprocess
            
            command = self.params.get('command', '')
            if not command:
                return {'success': False, 'error': '命令不能为空'}
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_call_api(self, context: Dict) -> Dict:
        """调用API"""
        try:
            import requests
            
            url = self.params.get('url', '')
            method = self.params.get('method', 'GET')
            headers = self.params.get('headers', {})
            data = self.params.get('data', {})
            
            if not url:
                return {'success': False, 'error': 'URL不能为空'}
            
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
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response': response_json
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


class AutoRule:
    """自动规则"""
    
    def __init__(self, rule_id: str, name: str, conditions: List[RuleCondition],
                 actions: List[RuleAction], priority: int = 0, 
                 enabled: bool = True, description: str = ''):
        self.rule_id = rule_id
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.priority = priority
        self.enabled = enabled
        self.description = description
        self.trigger_count = 0
        self.last_triggered_at = None
    
    def evaluate(self, context: Dict) -> bool:
        """评估规则是否满足条件"""
        if not self.enabled:
            return False
        
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False
        
        return True
    
    def execute(self, context: Dict) -> List[Dict]:
        """执行规则动作"""
        results = []
        
        for action in self.actions:
            result = action.execute(context)
            results.append(result)
        
        self.trigger_count += 1
        self.last_triggered_at = datetime.now().isoformat()
        
        return results
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'priority': self.priority,
            'enabled': self.enabled,
            'trigger_count': self.trigger_count,
            'last_triggered_at': self.last_triggered_at,
            'conditions': [
                {'field': c.field, 'operator': c.operator, 'value': c.value}
                for c in self.conditions
            ],
            'actions': [
                {'action_type': a.action_type, 'params': a.params}
                for a in self.actions
            ]
        }


class AutoRuleEngine:
    """自动规则引擎"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._rules = {}
        self._running = False
        self._monitor_thread = None
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        self._db_path = db.db_path
        self._init_database()
        self._load_rules()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    conditions TEXT,
                    actions TEXT,
                    priority INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    trigger_count INTEGER DEFAULT 0,
                    last_triggered_at TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rule_trigger_history (
                    trigger_id TEXT PRIMARY KEY,
                    rule_id TEXT,
                    context TEXT,
                    results TEXT,
                    triggered_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"初始化规则数据库失败: {e}")
    
    def _load_rules(self):
        """加载规则"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM auto_rules WHERE enabled = 1
            ''')
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            for row in rows:
                rule_data = dict(zip(columns, row))
                self._add_rule_from_db(rule_data)
            
            conn.close()
            
            logger.info(f"已加载 {len(self._rules)} 条规则")
            
        except Exception as e:
            logger.error(f"加载规则失败: {e}")
    
    def _add_rule_from_db(self, rule_data: Dict):
        """从数据库数据创建规则"""
        try:
            conditions = json.loads(rule_data.get('conditions', '[]'))
            actions = json.loads(rule_data.get('actions', '[]'))
            
            rule_conditions = [
                RuleCondition(c['field'], c['operator'], c['value'])
                for c in conditions
            ]
            
            rule_actions = [
                RuleAction(a['action_type'], a['params'])
                for a in actions
            ]
            
            rule = AutoRule(
                rule_id=rule_data['rule_id'],
                name=rule_data['name'],
                conditions=rule_conditions,
                actions=rule_actions,
                priority=rule_data.get('priority', 0),
                enabled=bool(rule_data.get('enabled', 1)),
                description=rule_data.get('description', '')
            )
            
            rule.trigger_count = rule_data.get('trigger_count', 0)
            rule.last_triggered_at = rule_data.get('last_triggered_at')
            
            self._rules[rule.rule_id] = rule
            
        except Exception as e:
            logger.error(f"创建规则失败: {e}")
    
    def add_rule(self, name: str, conditions: List[Dict], actions: List[Dict],
                 priority: int = 0, description: str = '') -> str:
        """添加规则"""
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        
        try:
            rule_conditions = [
                RuleCondition(c['field'], c['operator'], c['value'])
                for c in conditions
            ]
            
            rule_actions = [
                RuleAction(a['action_type'], a['params'])
                for a in actions
            ]
            
            rule = AutoRule(
                rule_id=rule_id,
                name=name,
                conditions=rule_conditions,
                actions=rule_actions,
                priority=priority,
                enabled=True,
                description=description
            )
            
            with self._lock:
                self._rules[rule_id] = rule
            
            self._save_rule_to_db(rule)
            
            logger.info(f"规则添加成功: {rule_id} - {name}")
            
            return rule_id
            
        except Exception as e:
            logger.error(f"添加规则失败: {e}")
            return None
    
    def _save_rule_to_db(self, rule: AutoRule):
        """保存规则到数据库"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO auto_rules VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule.rule_id,
                rule.name,
                rule.description,
                json.dumps([
                    {'field': c.field, 'operator': c.operator, 'value': c.value}
                    for c in rule.conditions
                ], ensure_ascii=False),
                json.dumps([
                    {'action_type': a.action_type, 'params': a.params}
                    for a in rule.actions
                ], ensure_ascii=False),
                rule.priority,
                1 if rule.enabled else 0,
                rule.trigger_count,
                rule.last_triggered_at,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存规则失败: {e}")
    
    def update_rule(self, rule_id: str, **kwargs):
        """更新规则"""
        try:
            with self._lock:
                rule = self._rules.get(rule_id)
                if not rule:
                    return {'success': False, 'error': '规则不存在'}
                
                if 'name' in kwargs:
                    rule.name = kwargs['name']
                if 'description' in kwargs:
                    rule.description = kwargs['description']
                if 'priority' in kwargs:
                    rule.priority = kwargs['priority']
                if 'enabled' in kwargs:
                    rule.enabled = kwargs['enabled']
                
                if 'conditions' in kwargs:
                    rule.conditions = [
                        RuleCondition(c['field'], c['operator'], c['value'])
                        for c in kwargs['conditions']
                    ]
                
                if 'actions' in kwargs:
                    rule.actions = [
                        RuleAction(a['action_type'], a['params'])
                        for a in kwargs['actions']
                    ]
            
            self._save_rule_to_db(rule)
            
            return {'success': True, 'message': '规则更新成功'}
            
        except Exception as e:
            logger.error(f"更新规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_rule(self, rule_id: str) -> Dict:
        """删除规则"""
        try:
            with self._lock:
                if rule_id not in self._rules:
                    return {'success': False, 'error': '规则不存在'}
                
                del self._rules[rule_id]
            
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM auto_rules WHERE rule_id = ?
            ''', (rule_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '规则删除成功'}
            
        except Exception as e:
            logger.error(f"删除规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_rule(self, rule_id: str) -> Dict:
        """获取规则"""
        try:
            rule = self._rules.get(rule_id)
            if not rule:
                return {'success': False, 'error': '规则不存在'}
            
            return {'success': True, 'data': rule.to_dict()}
            
        except Exception as e:
            logger.error(f"获取规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_rules(self) -> Dict:
        """获取所有规则"""
        try:
            rules = [rule.to_dict() for rule in self._rules.values()]
            rules.sort(key=lambda x: -x['priority'])
            
            return {'success': True, 'data': rules, 'total': len(rules)}
            
        except Exception as e:
            logger.error(f"获取规则列表失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def evaluate_and_trigger(self, context: Dict) -> List[Dict]:
        """评估并触发规则"""
        results = []
        
        with self._lock:
            rules = sorted(self._rules.values(), key=lambda x: -x.priority)
            
            for rule in rules:
                if rule.evaluate(context):
                    logger.info(f"规则触发: {rule.rule_id} - {rule.name}")
                    
                    action_results = rule.execute(context)
                    
                    self._save_trigger_history(rule.rule_id, context, action_results)
                    self._save_rule_to_db(rule)
                    
                    results.append({
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name,
                        'success': all(r.get('success', False) for r in action_results),
                        'action_results': action_results
                    })
        
        return results
    
    def _save_trigger_history(self, rule_id: str, context: Dict, results: List[Dict]):
        """保存触发历史"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO rule_trigger_history VALUES (?, ?, ?, ?, ?)
            ''', (
                f"trigger_{uuid.uuid4().hex[:8]}",
                rule_id,
                json.dumps(context, ensure_ascii=False),
                json.dumps(results, ensure_ascii=False),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存触发历史失败: {e}")
    
    def get_trigger_history(self, rule_id: str = None, limit: int = 50) -> Dict:
        """获取触发历史"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            if rule_id:
                cursor.execute('''
                    SELECT * FROM rule_trigger_history WHERE rule_id = ? ORDER BY triggered_at DESC LIMIT ?
                ''', (rule_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM rule_trigger_history ORDER BY triggered_at DESC LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            history = [dict(zip(columns, row)) for row in rows]
            
            conn.close()
            
            return {'success': True, 'data': history, 'total': len(history)}
            
        except Exception as e:
            logger.error(f"获取触发历史失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def start_monitor(self, interval: int = 60):
        """启动监控线程"""
        if self._running:
            return
        
        self._running = True
        
        def monitor_loop():
            while self._running:
                try:
                    self._check_system_state()
                except Exception as e:
                    logger.error(f"监控循环异常: {e}")
                
                time.sleep(interval)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("规则引擎监控线程已启动")
    
    def stop_monitor(self):
        """停止监控线程"""
        self._running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("规则引擎监控线程已停止")
    
    def _check_system_state(self):
        """检查系统状态并触发规则"""
        try:
            context = self._collect_system_context()
            self.evaluate_and_trigger(context)
        except Exception as e:
            logger.error(f"检查系统状态失败: {e}")
    
    def _collect_system_context(self) -> Dict:
        """收集系统上下文信息"""
        try:
            import psutil
            
            context = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids()),
                
                'running_agents': self._get_running_agents_count(),
                'active_collaborations': self._get_active_collaborations_count(),
                'pending_tasks': self._get_pending_tasks_count()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"收集系统上下文失败: {e}")
            return {'timestamp': datetime.now().isoformat()}
    
    def _get_running_agents_count(self) -> int:
        """获取运行中的Agent数量"""
        try:
            from app.agents.agent_manager import get_agent_manager
            
            manager = get_agent_manager()
            if manager:
                status = manager.get_status()
                return status.get('running_agents', 0)
            return 0
            
        except Exception as e:
            return 0
    
    def _get_active_collaborations_count(self) -> int:
        """获取活跃协作数量"""
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            if integration:
                collaborations = integration.get_active_collaborations()
                return len(collaborations.get('collaborations', []))
            return 0
            
        except Exception as e:
            return 0
    
    def _get_pending_tasks_count(self) -> int:
        """获取待处理任务数量"""
        try:
            from app.agents.collaborative_task_scheduler import get_task_scheduler
            
            scheduler = get_task_scheduler()
            if scheduler:
                stats = scheduler.get_scheduler_stats()
                return stats.get('queued_tasks', 0)
            return 0
            
        except Exception as e:
            return 0


_rule_engine_instance = None

def get_rule_engine():
    """获取规则引擎实例"""
    global _rule_engine_instance
    
    if _rule_engine_instance is None:
        _rule_engine_instance = AutoRuleEngine()
    
    return _rule_engine_instance


def init_rule_engine():
    """初始化规则引擎并启动监控"""
    engine = get_rule_engine()
    engine.start_monitor(interval=30)
    logger.info("[自动规则引擎] 初始化完成，监控线程已启动")
    return engine