#!/usr/bin/env python3
"""
AI员工同步工具 - 将AI员工信息上传并同步到数据库
支持全量同步、增量同步、数量统计等功能
"""

import os
import sys
import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

AI_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases', 'ai.db')


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(AI_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_employee_table():
    """确保ai_employees表存在并添加必要的列"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            title TEXT DEFAULT '',
            description TEXT DEFAULT '',
            category TEXT DEFAULT '',
            capabilities TEXT DEFAULT '',
            efficiency INTEGER DEFAULT 0,
            workload INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            thinking_focus TEXT DEFAULT '',
            generation_source TEXT DEFAULT '',
            template_key TEXT DEFAULT '',
            employee_type TEXT DEFAULT 'general',
            level INTEGER DEFAULT 1,
            knowledge_domain TEXT DEFAULT '',
            personality_type TEXT DEFAULT '',
            total_tasks INTEGER DEFAULT 0,
            successful_tasks INTEGER DEFAULT 0,
            failed_tasks INTEGER DEFAULT 0,
            performance_score REAL DEFAULT 0.0,
            is_enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('PRAGMA table_info(ai_employees)')
    existing_cols = [col[1] for col in cursor.fetchall()]
    
    if 'employee_type' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN employee_type TEXT DEFAULT "general"')
    
    if 'level' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN level INTEGER DEFAULT 1')
    
    if 'knowledge_domain' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN knowledge_domain TEXT DEFAULT ""')
    
    if 'personality_type' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN personality_type TEXT DEFAULT ""')
    
    if 'total_tasks' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN total_tasks INTEGER DEFAULT 0')
    
    if 'successful_tasks' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN successful_tasks INTEGER DEFAULT 0')
    
    if 'failed_tasks' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN failed_tasks INTEGER DEFAULT 0')
    
    if 'performance_score' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN performance_score REAL DEFAULT 0.0')
    
    if 'is_enabled' not in existing_cols:
        cursor.execute('ALTER TABLE ai_employees ADD COLUMN is_enabled INTEGER DEFAULT 1')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ai_employees_employee_id ON ai_employees(employee_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ai_employees_type ON ai_employees(employee_type)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ai_employees_status ON ai_employees(status)
    ''')
    
    conn.commit()
    conn.close()


class AIEmployeeSync:
    """AI员工同步管理器"""
    
    def __init__(self):
        ensure_employee_table()
    
    def _get_employee_data(self, employee) -> Dict:
        """从员工对象提取数据"""
        emp_type = getattr(employee, 'type', 'general')
        status = getattr(employee, 'status', 'active')
        return {
            'employee_id': getattr(employee, 'employee_id', ''),
            'name': getattr(employee, 'name', 'Unknown'),
            'title': getattr(employee, 'name', ''),
            'description': getattr(employee, 'description', ''),
            'category': emp_type,
            'employee_type': emp_type,
            'level': getattr(employee, 'level', 1),
            'status': status,
            'knowledge_domain': getattr(employee, 'knowledge_domain', ''),
            'personality_type': getattr(employee, 'personality_type', ''),
            'total_tasks': getattr(employee, 'total_tasks', 0),
            'successful_tasks': getattr(employee, 'successful_tasks', 0),
            'failed_tasks': getattr(employee, 'failed_tasks', 0),
            'performance_score': getattr(employee, 'performance_score', 0.0),
            'efficiency': getattr(employee, 'efficiency', 0),
            'workload': getattr(employee, 'workload', 0),
            'is_enabled': 1 if status == 'active' else 0,
            'capabilities': json.dumps(getattr(employee, 'capabilities', [])),
        }
    
    def sync_employee(self, employee) -> Dict:
        """同步单个员工到数据库"""
        employee_data = self._get_employee_data(employee)
        
        if not employee_data['employee_id']:
            return {'success': False, 'error': '员工ID为空'}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT employee_id FROM ai_employees WHERE employee_id = ?
            ''', (employee_data['employee_id'],))
            existing = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if existing:
                cursor.execute('''
                    UPDATE ai_employees 
                    SET name = ?, title = ?, description = ?, category = ?,
                        capabilities = ?, efficiency = ?, workload = ?, status = ?,
                        employee_type = ?, level = ?, knowledge_domain = ?, 
                        personality_type = ?, total_tasks = ?, successful_tasks = ?, 
                        failed_tasks = ?, performance_score = ?, is_enabled = ?, 
                        updated_at = ?
                    WHERE employee_id = ?
                ''', (
                    employee_data['name'],
                    employee_data['title'],
                    employee_data['description'],
                    employee_data['category'],
                    employee_data['capabilities'],
                    employee_data['efficiency'],
                    employee_data['workload'],
                    employee_data['status'],
                    employee_data['employee_type'],
                    employee_data['level'],
                    employee_data['knowledge_domain'],
                    employee_data['personality_type'],
                    employee_data['total_tasks'],
                    employee_data['successful_tasks'],
                    employee_data['failed_tasks'],
                    employee_data['performance_score'],
                    employee_data['is_enabled'],
                    now,
                    employee_data['employee_id']
                ))
                conn.commit()
                result = {'success': True, 'action': 'updated', 'employee_id': employee_data['employee_id']}
            else:
                cursor.execute('''
                    INSERT INTO ai_employees 
                    (employee_id, name, title, description, category,
                     capabilities, efficiency, workload, status, employee_type,
                     level, knowledge_domain, personality_type, total_tasks,
                     successful_tasks, failed_tasks, performance_score, 
                     is_enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_data['employee_id'],
                    employee_data['name'],
                    employee_data['title'],
                    employee_data['description'],
                    employee_data['category'],
                    employee_data['capabilities'],
                    employee_data['efficiency'],
                    employee_data['workload'],
                    employee_data['status'],
                    employee_data['employee_type'],
                    employee_data['level'],
                    employee_data['knowledge_domain'],
                    employee_data['personality_type'],
                    employee_data['total_tasks'],
                    employee_data['successful_tasks'],
                    employee_data['failed_tasks'],
                    employee_data['performance_score'],
                    employee_data['is_enabled'],
                    now,
                    now
                ))
                conn.commit()
                result = {'success': True, 'action': 'created', 'employee_id': employee_data['employee_id']}
            
            return result
            
        except sqlite3.IntegrityError as e:
            return {'success': False, 'error': f'数据完整性错误: {e}'}
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def sync_all_employees(self, employees: Dict) -> Dict:
        """同步所有员工到数据库"""
        results = {
            'total': len(employees),
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for employee_id, employee in employees.items():
            result = self.sync_employee(employee)
            if result['success']:
                if result['action'] == 'created':
                    results['created'] += 1
                else:
                    results['updated'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'employee_id': employee_id,
                    'error': result['error']
                })
        
        return results
    
    def get_db_employee_count(self) -> int:
        """获取数据库中的员工数量"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ai_employees')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_memory_employee_count(self, employees: Dict) -> int:
        """获取内存中的员工数量"""
        return len(employees)
    
    def get_employee_stats(self, employees: Dict = None) -> Dict:
        """获取员工统计信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM ai_employees')
        stats['db_total'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE status = "active"')
        stats['db_active'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE status = "inactive"')
        stats['db_inactive'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT employee_type, COUNT(*) FROM ai_employees GROUP BY employee_type')
        stats['db_by_type'] = {row['employee_type']: row['COUNT(*)'] for row in cursor.fetchall()}
        
        cursor.execute('SELECT level, COUNT(*) FROM ai_employees GROUP BY level ORDER BY level')
        stats['db_by_level'] = {row['level']: row['COUNT(*)'] for row in cursor.fetchall()}
        
        if employees:
            stats['memory_total'] = len(employees)
            type_counts = {}
            level_counts = {}
            active_count = 0
            
            for emp in employees.values():
                emp_type = getattr(emp, 'type', 'general')
                level = getattr(emp, 'level', 1)
                status = getattr(emp, 'status', 'active')
                
                type_counts[emp_type] = type_counts.get(emp_type, 0) + 1
                level_counts[level] = level_counts.get(level, 0) + 1
                if status == 'active':
                    active_count += 1
            
            stats['memory_by_type'] = type_counts
            stats['memory_by_level'] = level_counts
            stats['memory_active'] = active_count
        
        conn.close()
        return stats
    
    def compare_and_sync(self, employees: Dict) -> Dict:
        """比较并同步员工数据"""
        stats_before = self.get_employee_stats(employees)
        
        sync_result = self.sync_all_employees(employees)
        
        stats_after = self.get_employee_stats(employees)
        
        return {
            'sync_result': sync_result,
            'stats_before': stats_before,
            'stats_after': stats_after,
            'sync_time': datetime.now().isoformat()
        }
    
    def export_employees(self, employees: Dict, output_file: str = None) -> Dict:
        """导出员工数据"""
        employee_list = []
        for employee_id, employee in employees.items():
            employee_data = self._get_employee_data(employee)
            employee_list.append(employee_data)
        
        result = {
            'export_time': datetime.now().isoformat(),
            'total_employees': len(employee_list),
            'employees': employee_list
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            result['output_file'] = output_file
        
        return result
    
    def import_employees(self, import_data: Dict) -> Dict:
        """导入员工数据"""
        results = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        employees = import_data.get('employees', [])
        results['total'] = len(employees)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        for emp_data in employees:
            try:
                cursor.execute('SELECT id FROM ai_employees WHERE employee_id = ?', 
                              (emp_data.get('employee_id', ''),))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                        UPDATE ai_employees 
                        SET name = ?, employee_type = ?, level = ?, status = ?,
                            knowledge_domain = ?, personality_type = ?,
                            total_tasks = ?, successful_tasks = ?, failed_tasks = ?,
                            performance_score = ?, is_enabled = ?, updated_at = ?
                        WHERE employee_id = ?
                    ''', (
                        emp_data.get('name', 'Unknown'),
                        emp_data.get('employee_type', 'general'),
                        emp_data.get('level', 1),
                        emp_data.get('status', 'active'),
                        emp_data.get('knowledge_domain', ''),
                        emp_data.get('personality_type', ''),
                        emp_data.get('total_tasks', 0),
                        emp_data.get('successful_tasks', 0),
                        emp_data.get('failed_tasks', 0),
                        emp_data.get('performance_score', 0.0),
                        emp_data.get('is_enabled', 1),
                        now,
                        emp_data.get('employee_id', '')
                    ))
                    results['updated'] += 1
                else:
                    cursor.execute('''
                        INSERT INTO ai_employees 
                        (employee_id, name, employee_type, level, status,
                         knowledge_domain, personality_type, total_tasks,
                         successful_tasks, failed_tasks, performance_score,
                         is_enabled, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        emp_data.get('employee_id', ''),
                        emp_data.get('name', 'Unknown'),
                        emp_data.get('employee_type', 'general'),
                        emp_data.get('level', 1),
                        emp_data.get('status', 'active'),
                        emp_data.get('knowledge_domain', ''),
                        emp_data.get('personality_type', ''),
                        emp_data.get('total_tasks', 0),
                        emp_data.get('successful_tasks', 0),
                        emp_data.get('failed_tasks', 0),
                        emp_data.get('performance_score', 0.0),
                        emp_data.get('is_enabled', 1),
                        now,
                        now
                    ))
                    results['created'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'employee_id': emp_data.get('employee_id', 'unknown'),
                    'error': str(e)
                })
        
        conn.commit()
        conn.close()
        return results
    
    def delete_employee(self, employee_id: str) -> bool:
        """删除员工"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM ai_employees WHERE employee_id = ?', (employee_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def cleanup_stale_records(self, active_employee_ids: List[str]) -> Dict:
        """清理数据库中不存在于内存中的记录"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join(['?'] * len(active_employee_ids))
            cursor.execute(f'''
                SELECT employee_id FROM ai_employees 
                WHERE employee_id NOT IN ({placeholders})
            ''', active_employee_ids)
            
            stale_ids = [row['employee_id'] for row in cursor.fetchall()]
            
            if stale_ids:
                placeholders = ','.join(['?'] * len(stale_ids))
                cursor.execute(f'''
                    DELETE FROM ai_employees 
                    WHERE employee_id IN ({placeholders})
                ''', stale_ids)
                conn.commit()
            
            return {
                'success': True,
                'deleted_count': len(stale_ids),
                'deleted_ids': stale_ids
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()


def main():
    if len(sys.argv) < 2:
        print("AI员工同步工具")
        print("用法: python3 ai_employee_sync.py <命令> [参数]")
        print()
        print("命令列表:")
        print("  init              - 初始化数据库表")
        print("  count             - 查看数据库中的员工数量")
        print("  stats             - 查看员工统计信息")
        print("  sync              - 同步员工到数据库(需要通过代码调用)")
        print("  export <file>     - 导出员工数据到文件")
        print("  import <file>     - 从文件导入员工数据")
        return
    
    sync_manager = AIEmployeeSync()
    command = sys.argv[1]
    
    if command == 'init':
        ensure_employee_table()
        print("数据库表初始化完成")
    
    elif command == 'count':
        count = sync_manager.get_db_employee_count()
        print(f"数据库中的AI员工数量: {count}")
    
    elif command == 'stats':
        stats = sync_manager.get_employee_stats()
        print("=" * 50)
        print("AI员工统计信息")
        print("=" * 50)
        print(f"数据库总数: {stats.get('db_total', 0)}")
        print(f"活跃状态: {stats.get('db_active', 0)}")
        print(f"非活跃状态: {stats.get('db_inactive', 0)}")
        print()
        print("按类型统计:")
        for emp_type, count in stats.get('db_by_type', {}).items():
            print(f"  {emp_type}: {count}")
        print()
        print("按级别统计:")
        for level, count in sorted(stats.get('db_by_level', {}).items()):
            print(f"  Level {level}: {count}")
    
    elif command == 'export':
        if len(sys.argv) < 3:
            print("用法: python3 ai_employee_sync.py export <output_file>")
            return
        output_file = sys.argv[2]
        from ai_engines.ai_employee_manager import AIEmployeeManager
        manager = AIEmployeeManager()
        employees = manager.employees
        result = sync_manager.export_employees(employees, output_file)
        print(f"导出完成: {result['total_employees']} 个员工")
        print(f"输出文件: {result['output_file']}")
    
    elif command == 'import':
        if len(sys.argv) < 3:
            print("用法: python3 ai_employee_sync.py import <input_file>")
            return
        input_file = sys.argv[2]
        with open(input_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        result = sync_manager.import_employees(import_data)
        print(f"导入完成:")
        print(f"  总数: {result['total']}")
        print(f"  新增: {result['created']}")
        print(f"  更新: {result['updated']}")
        print(f"  失败: {result['failed']}")
        if result['errors']:
            print("\n错误列表:")
            for error in result['errors']:
                print(f"  {error['employee_id']}: {error['error']}")
    
    else:
        print(f"未知命令: {command}")


if __name__ == '__main__':
    main()
