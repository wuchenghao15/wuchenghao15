# -*- coding: utf-8 -*-
"""
批量任务管理器
支持Agent批量分派代码修复任务，并将结果上报数据库
"""

import os
import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)


class BatchTaskManager:
    """批量任务管理器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._batch_tasks = {}
        self._task_results = {}
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        self._db_path = db.db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batch_tasks (
                    batch_id TEXT PRIMARY KEY,
                    agent_code TEXT,
                    task_type TEXT,
                    status TEXT DEFAULT 'pending',
                    total_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    result_data TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batch_task_items (
                    item_id TEXT PRIMARY KEY,
                    batch_id TEXT,
                    task_index INTEGER,
                    task_data TEXT,
                    employee_id TEXT,
                    session_id TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    error TEXT,
                    created_at TEXT,
                    completed_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"初始化批量任务数据库失败: {e}")
    
    def create_batch_task(self, agent_code: str, task_type: str, 
                          tasks: List[Dict]) -> str:
        """创建批量任务"""
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        
        try:
            import sqlite3
            
            with self._lock:
                self._batch_tasks[batch_id] = {
                    'batch_id': batch_id,
                    'agent_code': agent_code,
                    'task_type': task_type,
                    'tasks': tasks,
                    'status': 'pending',
                    'total_tasks': len(tasks),
                    'completed_tasks': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO batch_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    batch_id,
                    agent_code,
                    task_type,
                    'pending',
                    len(tasks),
                    0,
                    0,
                    0,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps({'tasks': tasks}, ensure_ascii=False)
                ))
                
                conn.commit()
                conn.close()
                
            logger.info(f"批量任务创建成功: {batch_id}, 共 {len(tasks)} 个任务")
            
            return batch_id
            
        except Exception as e:
            logger.error(f"创建批量任务失败: {e}")
            return None
    
    def dispatch_batch_task(self, batch_id: str, employee_template: str = None) -> Dict:
        """分派批量任务给AI员工"""
        try:
            from app.agents.agent_ai_employee_integration import get_integration
            
            integration = get_integration()
            if not integration:
                return {'success': False, 'error': '集成控制器未初始化'}
            
            with self._lock:
                batch_info = self._batch_tasks.get(batch_id)
                if not batch_info:
                    return {'success': False, 'error': '批量任务不存在'}
                
                batch_info['status'] = 'processing'
            
            self._update_batch_status(batch_id, 'processing')
            
            results = []
            tasks = batch_info['tasks']
            agent_code = batch_info['agent_code']
            
            for i, task_data in enumerate(tasks):
                item_id = f"{batch_id}_item_{i:03d}"
                
                task = {
                    'task_type': batch_info['task_type'],
                    'task_data': task_data,
                    'agent_code': agent_code,
                    'batch_id': batch_id,
                    'item_id': item_id
                }
                
                result = integration.dispatch_task_to_employee(
                    agent_code,
                    task,
                    employee_template
                )
                
                if result.get('success'):
                    session_id = result.get('session_id')
                    employee_id = result.get('employee_id')
                    
                    self._save_task_item(batch_id, item_id, i, task_data, 
                                        employee_id, session_id, 'processing')
                    
                    results.append({
                        'item_id': item_id,
                        'task_index': i,
                        'success': True,
                        'session_id': session_id,
                        'employee_id': employee_id
                    })
                else:
                    self._save_task_item(batch_id, item_id, i, task_data, 
                                        None, None, 'failed', error=result.get('error'))
                    
                    results.append({
                        'item_id': item_id,
                        'task_index': i,
                        'success': False,
                        'error': result.get('error')
                    })
                
                self._update_batch_progress(batch_id)
            
            return {
                'success': True,
                'batch_id': batch_id,
                'total_tasks': len(tasks),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"分派批量任务失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_task_item(self, batch_id: str, item_id: str, task_index: int, 
                        task_data: Dict, employee_id: str, session_id: str,
                        status: str = 'pending', result: str = None, 
                        error: str = None):
        """保存任务项到数据库"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO batch_task_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id,
                batch_id,
                task_index,
                json.dumps(task_data, ensure_ascii=False),
                employee_id,
                session_id,
                status,
                result,
                error,
                datetime.now().isoformat(),
                datetime.now().isoformat() if status in ['completed', 'failed'] else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存任务项失败: {e}")
    
    def update_task_item_result(self, item_id: str, status: str, 
                                result: Dict = None, error: str = None):
        """更新任务项结果"""
        try:
            import sqlite3
            
            result_json = json.dumps(result, ensure_ascii=False) if result else None
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE batch_task_items SET status = ?, result = ?, error = ?, completed_at = ?
                WHERE item_id = ?
            ''', (
                status,
                result_json,
                error,
                datetime.now().isoformat(),
                item_id
            ))
            
            conn.commit()
            conn.close()
            
            batch_id = item_id.split('_item_')[0]
            self._update_batch_progress(batch_id)
            
        except Exception as e:
            logger.error(f"更新任务项结果失败: {e}")
    
    def _update_batch_progress(self, batch_id: str):
        """更新批量任务进度"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status FROM batch_task_items WHERE batch_id = ?
            ''', (batch_id,))
            
            rows = cursor.fetchall()
            
            completed_count = sum(1 for row in rows if row[0] == 'completed')
            failed_count = sum(1 for row in rows if row[0] == 'failed')
            total_count = len(rows)
            
            status = 'completed' if completed_count + failed_count == total_count else 'processing'
            
            cursor.execute('''
                UPDATE batch_tasks SET status = ?, completed_tasks = ?, 
                    success_count = ?, failed_count = ?, updated_at = ?
                WHERE batch_id = ?
            ''', (
                status,
                completed_count + failed_count,
                completed_count,
                failed_count,
                datetime.now().isoformat(),
                batch_id
            ))
            
            conn.commit()
            conn.close()
            
            with self._lock:
                if batch_id in self._batch_tasks:
                    self._batch_tasks[batch_id]['status'] = status
                    self._batch_tasks[batch_id]['completed_tasks'] = completed_count + failed_count
                    self._batch_tasks[batch_id]['success_count'] = completed_count
                    self._batch_tasks[batch_id]['failed_count'] = failed_count
            
            logger.info(f"批量任务进度更新: {batch_id} - {completed_count}/{total_count} 完成")
            
        except Exception as e:
            logger.error(f"更新批量任务进度失败: {e}")
    
    def _update_batch_status(self, batch_id: str, status: str):
        """更新批量任务状态"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE batch_tasks SET status = ?, updated_at = ? WHERE batch_id = ?
            ''', (status, datetime.now().isoformat(), batch_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新批量任务状态失败: {e}")
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """获取批量任务状态"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM batch_tasks WHERE batch_id = ?
            ''', (batch_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return {'success': False, 'error': '批量任务不存在'}
            
            columns = [desc[0] for desc in cursor.description]
            batch_info = dict(zip(columns, row))
            
            cursor.execute('''
                SELECT * FROM batch_task_items WHERE batch_id = ? ORDER BY task_index
            ''', (batch_id,))
            
            items = cursor.fetchall()
            item_columns = [desc[0] for desc in cursor.description]
            
            batch_info['items'] = [dict(zip(item_columns, item)) for item in items]
            
            conn.close()
            
            return {'success': True, 'data': batch_info}
            
        except Exception as e:
            logger.error(f"获取批量任务状态失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_batch_tasks(self, status: str = None) -> Dict:
        """获取所有批量任务"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM batch_tasks WHERE status = ? ORDER BY created_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT * FROM batch_tasks ORDER BY created_at DESC
                ''')
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            tasks = [dict(zip(columns, row)) for row in rows]
            
            conn.close()
            
            return {'success': True, 'data': tasks, 'total': len(tasks)}
            
        except Exception as e:
            logger.error(f"获取批量任务列表失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_rule_enhancement_batch(self, agent_code: str, 
                                      rule_configs: List[Dict]) -> Dict:
        """创建规则增强批量任务"""
        try:
            from app.agents.rule_auto_generator import get_rule_generator
            
            generator = get_rule_generator()
            if not generator:
                return {'success': False, 'error': '规则生成器未初始化'}
            
            batch_id = f"rule_batch_{uuid.uuid4().hex[:8]}"
            generated_rules = []
            failed_rules = []
            
            for i, config in enumerate(rule_configs):
                template_key = config.get('template_key')
                custom_params = config.get('custom_params')
                
                result = generator.generate_rules_from_template(
                    template_key, custom_params, agent_code, batch_id
                )
                
                if result.get('success'):
                    generated_rules.append({
                        'index': i,
                        'rule_id': result.get('rule_id'),
                        'template_key': template_key,
                        'generation_id': result.get('generation_id')
                    })
                else:
                    failed_rules.append({
                        'index': i,
                        'template_key': template_key,
                        'error': result.get('error')
                    })
            
            # 保存批量任务记录
            with self._lock:
                self._batch_tasks[batch_id] = {
                    'batch_id': batch_id,
                    'agent_code': agent_code,
                    'task_type': 'rule_enhancement',
                    'status': 'completed' if not failed_rules else 'partial',
                    'total_tasks': len(rule_configs),
                    'completed_tasks': len(rule_configs),
                    'success_count': len(generated_rules),
                    'failed_count': len(failed_rules),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                import sqlite3
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO batch_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    batch_id,
                    agent_code,
                    'rule_enhancement',
                    'completed' if not failed_rules else 'partial',
                    len(rule_configs),
                    len(rule_configs),
                    len(generated_rules),
                    len(failed_rules),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps({
                        'generated_rules': generated_rules,
                        'failed_rules': failed_rules,
                        'rule_configs': rule_configs
                    }, ensure_ascii=False)
                ))
                
                conn.commit()
                conn.close()
            
            logger.info(f"[规则增强] 批量任务创建完成: {batch_id}, 成功 {len(generated_rules)} 个, 失败 {len(failed_rules)} 个")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'generated_rules': generated_rules,
                'failed_rules': failed_rules,
                'total_generated': len(generated_rules),
                'total_failed': len(failed_rules),
                'message': '规则增强批量任务已创建并上报数据库'
            }
            
        except Exception as e:
            logger.error(f"[规则增强] 创建规则增强批量任务失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def auto_enhance_system_rules(self, categories: List[str] = None,
                                  agent_code: str = 'auto_rule_enhancer') -> Dict:
        """自动增强系统规则"""
        try:
            from app.agents.rule_auto_generator import get_rule_generator
            
            generator = get_rule_generator()
            if not generator:
                return {'success': False, 'error': '规则生成器未初始化'}
            
            results = []
            total_generated = 0
            total_failed = 0
            
            categories_to_process = categories or ['performance', 'task_management', 'health', 'ai_collaboration']
            
            for category in categories_to_process:
                result = generator.batch_generate_rules(category, agent_code)
                
                if result.get('success'):
                    results.append({
                        'category': category,
                        'batch_id': result.get('batch_id'),
                        'generated': result.get('total_generated', 0),
                        'failed': result.get('total_failed', 0),
                        'rules': result.get('generated_rules', [])
                    })
                    total_generated += result.get('total_generated', 0)
                    total_failed += result.get('total_failed', 0)
                else:
                    results.append({
                        'category': category,
                        'error': result.get('error')
                    })
                    total_failed += 1
            
            # 创建批量任务记录
            batch_id = f"auto_rule_enhance_{uuid.uuid4().hex[:8]}"
            
            with self._lock:
                import sqlite3
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO batch_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    batch_id,
                    agent_code,
                    'auto_rule_enhancement',
                    'completed',
                    len(categories_to_process),
                    len(categories_to_process),
                    total_generated,
                    total_failed,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps({
                        'categories': categories_to_process,
                        'results': results,
                        'total_generated': total_generated,
                        'total_failed': total_failed
                    }, ensure_ascii=False)
                ))
                
                conn.commit()
                conn.close()
            
            logger.info(f"[自动规则增强] 完成: 共生成 {total_generated} 条规则")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'results': results,
                'total_generated': total_generated,
                'total_failed': total_failed,
                'message': '系统规则自动增强完成，结果已上报数据库'
            }
            
        except Exception as e:
            logger.error(f"[自动规则增强] 自动增强系统规则失败: {e}")
            return {'success': False, 'error': str(e)}


_batch_manager_instance = None

def get_batch_manager():
    """获取批量任务管理器实例"""
    global _batch_manager_instance
    
    if _batch_manager_instance is None:
        _batch_manager_instance = BatchTaskManager()
    
    return _batch_manager_instance