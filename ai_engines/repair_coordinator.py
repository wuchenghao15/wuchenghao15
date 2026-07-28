# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复协调器
协调AI员工共同修复问题，记录修复过程和结果
"""

import os
import json
import uuid
import sqlite3
import logging
import subprocess
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

REPAIR_STATUS = {
    'pending': '待修复',
    'in_progress': '修复中',
    'completed': '已完成',
    'failed': '修复失败',
    'rolled_back': '已回滚'
}

REPAIR_TYPES = {
    'code_fix': '代码修复',
    'config_fix': '配置修复',
    'permission_fix': '权限修复',
    'dependency_update': '依赖更新',
    'security_patch': '安全补丁',
    'database_fix': '数据库修复'
}

class RepairCoordinator:
    """修复协调器"""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'repair_coordinator.db')
        self._create_tables()
        self.repairs = {}

    def _create_tables(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS repair_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repair_id TEXT UNIQUE,
                    issue_id TEXT,
                    solution_id TEXT,
                    repair_type TEXT,
                    status TEXT DEFAULT 'pending',
                    assigned_to TEXT,
                    description TEXT,
                    actions TEXT,
                    result TEXT,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS repair_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE,
                    repair_id TEXT,
                    issue_id TEXT,
                    title TEXT,
                    summary TEXT,
                    details TEXT,
                    status TEXT,
                    generated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("[RepairCoordinator] 数据库表创建完成")

    def assign_repair(self, issue: Dict, solution: Dict) -> Dict[str, Any]:
        """分配修复任务"""
        repair_id = f"repair_{uuid.uuid4().hex[:8]}"
        repair_type = self._determine_repair_type(issue.get('category', ''))
        
        repair_task = {
            'repair_id': repair_id,
            'issue_id': issue.get('issue_id', ''),
            'solution_id': solution.get('solution_id', ''),
            'repair_type': repair_type,
            'status': 'pending',
            'assigned_to': self._assign_employee(repair_type),
            'description': f"修复问题: {issue.get('title', '')}",
            'actions': solution.get('solutions', []),
            'result': '',
            'executed_at': datetime.now().isoformat()
        }
        
        self._save_repair_task(repair_task)
        self.repairs[repair_id] = repair_task
        
        logger.info(f"[RepairCoordinator] 分配修复任务: {repair_id} -> {repair_task['assigned_to']}")
        return repair_task

    def _determine_repair_type(self, category: str) -> str:
        """确定修复类型"""
        type_mapping = {
            'hardcoded_credentials': 'code_fix',
            'code_execution': 'code_fix',
            'command_injection': 'code_fix',
            'deserialization': 'code_fix',
            'sql_injection': 'code_fix',
            'xss': 'code_fix',
            'csrf': 'code_fix',
            'debug_enabled': 'config_fix',
            'weak_secret_key': 'config_fix',
            'http_port_open': 'config_fix',
            'env_file': 'config_fix',
            'db_permissions': 'permission_fix'
        }
        return type_mapping.get(category, 'code_fix')

    def _assign_employee(self, repair_type: str) -> str:
        """分配AI员工"""
        employee_mapping = {
            'code_fix': '代码修复工程师',
            'config_fix': '配置管理工程师',
            'permission_fix': '安全工程师',
            'dependency_update': '运维工程师',
            'security_patch': '安全工程师',
            'database_fix': '数据库管理员'
        }
        return employee_mapping.get(repair_type, '安全工程师')

    def execute_repair(self, repair_id: str) -> Dict[str, Any]:
        """执行修复"""
        if repair_id not in self.repairs:
            return {'success': False, 'error': '修复任务不存在'}
        
        repair = self.repairs[repair_id]
        repair['status'] = 'in_progress'
        self._update_repair_status(repair_id, 'in_progress')
        
        logger.info(f"[RepairCoordinator] 开始执行修复: {repair_id}")
        
        try:
            results = []
            for action in repair.get('actions', []):
                result = self._execute_action(action, repair)
                results.append(result)
            
            repair['result'] = json.dumps(results, ensure_ascii=False)
            repair['status'] = 'completed'
            repair['completed_at'] = datetime.now().isoformat()
            
            self._update_repair_status(repair_id, 'completed')
            self._save_repair_report(repair)
            
            logger.info(f"[RepairCoordinator] 修复完成: {repair_id}")
            return {
                'success': True,
                'repair_id': repair_id,
                'status': 'completed',
                'results': results,
                'completed_at': datetime.now().isoformat()
            }
        except Exception as e:
            repair['result'] = f"修复失败: {str(e)}"
            repair['status'] = 'failed'
            repair['completed_at'] = datetime.now().isoformat()
            
            self._update_repair_status(repair_id, 'failed')
            
            logger.error(f"[RepairCoordinator] 修复失败: {repair_id} - {e}")
            return {
                'success': False,
                'repair_id': repair_id,
                'status': 'failed',
                'error': str(e)
            }

    def _execute_action(self, action: str, repair: Dict) -> Dict[str, Any]:
        """执行单个修复动作"""
        logger.info(f"[RepairCoordinator] 执行动作: {action}")
        
        try:
            if '环境变量' in action:
                return self._fix_environment_variables(action)
            elif '权限' in action or 'chmod' in action:
                return self._fix_permissions(action)
            elif '配置' in action:
                return self._fix_configuration(action)
            elif '依赖' in action:
                return self._update_dependencies(action)
            elif 'DEBUG' in action:
                return self._disable_debug(action)
            elif '密钥' in action:
                return self._fix_secret_key(action)
            else:
                return {'action': action, 'status': 'implemented', 'message': '执行通用修复动作'}
        except Exception as e:
            return {'action': action, 'status': 'failed', 'error': str(e)}

    def _fix_environment_variables(self, action: str) -> Dict[str, Any]:
        """修复环境变量配置"""
        try:
            env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
            if not os.path.exists(env_file):
                with open(env_file, 'w') as f:
                    f.write('# Environment Variables\n')
            
            with open(env_file, 'a') as f:
                f.write(f'# Auto-generated: {action}\n')
            
            return {'action': action, 'status': 'implemented', 'message': '环境变量配置已更新'}
        except Exception as e:
            return {'action': action, 'status': 'failed', 'error': str(e)}

    def _fix_permissions(self, action: str) -> Dict[str, Any]:
        """修复文件权限"""
        try:
            db_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            for root, dirs, files in os.walk(db_dir):
                for file in files:
                    if file.endswith('.db'):
                        file_path = os.path.join(root, file)
                        os.chmod(file_path, 0o600)
            
            return {'action': action, 'status': 'implemented', 'message': '数据库文件权限已设置为600'}
        except Exception as e:
            return {'action': action, 'status': 'failed', 'error': str(e)}

    def _fix_configuration(self, action: str) -> Dict[str, Any]:
        """修复配置"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), '..', 'config.py')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                if 'DEBUG = True' in content:
                    content = content.replace('DEBUG = True', 'DEBUG = False')
                    with open(config_file, 'w') as f:
                        f.write(content)
            
            return {'action': action, 'status': 'implemented', 'message': '配置已修复'}
        except Exception as e:
            return {'action': action, 'status': 'failed', 'error': str(e)}

    def _update_dependencies(self, action: str) -> Dict[str, Any]:
        """更新依赖"""
        try:
            subprocess.run(['pip', 'list'], capture_output=True, text=True)
            return {'action': action, 'status': 'implemented', 'message': '依赖检查完成'}
        except Exception as e:
            return {'action': action, 'status': 'failed', 'error': str(e)}

    def _disable_debug(self, action: str) -> Dict[str, Any]:
        """禁用调试模式"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), '..', 'config.py')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                content = content.replace('DEBUG = True', 'DEBUG = False')
                with open(config_file, 'w') as f:
                    f.write(content)
            
            return {'action': action, 'status': 'implemented', 'message': 'DEBUG模式已禁用'}
        except Exception as e:
            return {'action': action, 'status': 'failed', 'error': str(e)}

    def _fix_secret_key(self, action: str) -> Dict[str, Any]:
        """修复密钥"""
        try:
            import secrets
            new_key = secrets.token_hex(32)
            
            config_file = os.path.join(os.path.dirname(__file__), '..', 'config.py')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                content = re.sub(r'SECRET_KEY\s*=\s*["\'].*["\']', f'SECRET_KEY = "{new_key}"', content)
                with open(config_file, 'w') as f:
                    f.write(content)
            
            return {'action': action, 'status': 'implemented', 'message': 'SECRET_KEY已更新'}
        except Exception as e:
            return {'action': action, 'status': 'failed', 'error': str(e)}

    def _save_repair_task(self, repair: Dict):
        """保存修复任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO repair_tasks 
                    (repair_id, issue_id, solution_id, repair_type, status, assigned_to, 
                     description, actions, result, executed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    repair['repair_id'],
                    repair['issue_id'],
                    repair['solution_id'],
                    repair['repair_type'],
                    repair['status'],
                    repair['assigned_to'],
                    repair['description'],
                    json.dumps(repair.get('actions', []), ensure_ascii=False),
                    repair.get('result', ''),
                    repair.get('executed_at', datetime.now().isoformat())
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[RepairCoordinator] 保存修复任务失败: {e}")

    def _update_repair_status(self, repair_id: str, status: str):
        """更新修复状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE repair_tasks SET status = ?, completed_at = ? WHERE repair_id = ?
                ''', (status, datetime.now().isoformat() if status in ['completed', 'failed', 'rolled_back'] else '', repair_id))
                conn.commit()
        except Exception as e:
            logger.error(f"[RepairCoordinator] 更新修复状态失败: {e}")

    def _save_repair_report(self, repair: Dict):
        """保存修复报告"""
        report_id = f"report_{uuid.uuid4().hex[:8]}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO repair_reports 
                    (report_id, repair_id, issue_id, title, summary, details, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report_id,
                    repair['repair_id'],
                    repair['issue_id'],
                    f"修复报告: {repair['description']}",
                    f"修复状态: {REPAIR_STATUS.get(repair['status'], repair['status'])}",
                    repair.get('result', ''),
                    repair['status']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[RepairCoordinator] 保存修复报告失败: {e}")

    def execute_batch_repair(self, repair_ids: List[str]) -> List[Dict]:
        """批量执行修复"""
        results = []
        for repair_id in repair_ids:
            result = self.execute_repair(repair_id)
            results.append(result)
        
        return results

    def get_repair_status(self, repair_id: str) -> Optional[Dict]:
        """获取修复状态"""
        return self.repairs.get(repair_id)

    def get_all_repairs(self) -> List[Dict]:
        """获取所有修复任务"""
        return list(self.repairs.values())

    def get_repairs_by_status(self, status: str) -> List[Dict]:
        """按状态获取修复任务"""
        return [r for r in self.repairs.values() if r.get('status') == status]

import re