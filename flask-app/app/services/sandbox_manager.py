# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""沙盒管理服务 - 增强版"""
import os
import sys
import io
import uuid
import time
import json
import sqlite3
import threading
import subprocess
import tempfile
from enum import Enum
from typing import Dict, Any, List, Optional
from contextlib import redirect_stdout, redirect_stderr


class SandboxType(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SHELL = "shell"
    RESTRICTED = "restricted"


class ExecutionMode(Enum):
    SYNC = "sync"
    ASYNC = "async"
    TIMEOUT = "timeout"


class FileAccessMode(Enum):
    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"
    READ_WRITE = "read_write"
    NONE = "none"


class SandboxManager:
    def __init__(self):
        self.sandboxes = {}
        self.execution_results = {}
        self.lock = threading.Lock()
        
        self._init_database()
        
        self.max_execution_time = 30
        self.max_memory_mb = 128
        self.max_output_size = 1024 * 1024
        self.allowed_modules = ['math', 'random', 'json', 'datetime', 're', 'collections']
        self.forbidden_modules = ['os', 'sys', 'subprocess', 'socket', 'pickle', 'ctypes']
        self.allowed_commands = ['echo', 'cat', 'ls', 'pwd', 'date']

    def _init_database(self):
        """初始化数据库"""
        try:
            db_path = 'sandbox_manager.db'
            self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sandboxes (
                    sandbox_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sandbox_type TEXT NOT NULL,
                    description TEXT,
                    config TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at REAL,
                    last_used_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_records (
                    record_id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    result TEXT,
                    error TEXT,
                    execution_time REAL,
                    memory_usage REAL,
                    status TEXT NOT NULL,
                    created_at REAL,
                    FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_operations (
                    operation_id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    content TEXT,
                    created_at REAL,
                    FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sandboxes_type ON sandboxes(sandbox_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_records_sandbox ON execution_records(sandbox_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_records_status ON execution_records(status)')
            
            self.db_conn.commit()
        except Exception as e:
            print(f"沙盒管理数据库初始化失败: {str(e)}")

    def create_sandbox(self, name: str, sandbox_type: SandboxType = SandboxType.PYTHON,
                       description: str = "", config: Dict = None) -> str:
        """创建沙盒"""
        if config is None:
            config = {}
        
        sandbox_id = f"sandbox_{uuid.uuid4().hex[:8]}"
        
        sandbox_config = {
            'max_execution_time': config.get('max_execution_time', self.max_execution_time),
            'max_memory_mb': config.get('max_memory_mb', self.max_memory_mb),
            'max_output_size': config.get('max_output_size', self.max_output_size),
            'allowed_modules': config.get('allowed_modules', self.allowed_modules),
            'forbidden_modules': config.get('forbidden_modules', self.forbidden_modules),
            'allowed_commands': config.get('allowed_commands', self.allowed_commands),
            'file_access_mode': config.get('file_access_mode', FileAccessMode.NONE.value),
            'working_directory': config.get('working_directory', '')
        }
        
        sandbox = {
            'sandbox_id': sandbox_id,
            'name': name,
            'sandbox_type': sandbox_type.value,
            'description': description,
            'config': json.dumps(sandbox_config),
            'is_active': True,
            'created_at': time.time(),
            'last_used_at': 0
        }
        
        with self.lock:
            self.sandboxes[sandbox_id] = sandbox
            self._save_sandbox(sandbox)
        
        return sandbox_id

    def _save_sandbox(self, sandbox: Dict):
        """保存沙盒到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sandboxes 
                (sandbox_id, name, sandbox_type, description, config, is_active, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sandbox['sandbox_id'],
                sandbox['name'],
                sandbox['sandbox_type'],
                sandbox['description'],
                sandbox['config'],
                sandbox.get('is_active', True),
                sandbox.get('created_at', time.time()),
                sandbox.get('last_used_at', 0)
            ))
            self.db_conn.commit()
        except Exception as e:
            print(f"保存沙盒失败: {str(e)}")

    def get_sandbox(self, sandbox_id: str) -> Optional[Dict]:
        """获取沙盒"""
        with self.lock:
            return self.sandboxes.get(sandbox_id)

    def update_sandbox(self, sandbox_id: str, **kwargs) -> bool:
        """更新沙盒"""
        with self.lock:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                return False
            
            if 'name' in kwargs:
                sandbox['name'] = kwargs['name']
            if 'description' in kwargs:
                sandbox['description'] = kwargs['description']
            if 'config' in kwargs:
                sandbox['config'] = json.dumps(kwargs['config'])
            if 'is_active' in kwargs:
                sandbox['is_active'] = kwargs['is_active']
            
            self._save_sandbox(sandbox)
        
        return True

    def delete_sandbox(self, sandbox_id: str) -> bool:
        """删除沙盒"""
        with self.lock:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                return False
            
            del self.sandboxes[sandbox_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM sandboxes WHERE sandbox_id = ?', (sandbox_id,))
            cursor.execute('DELETE FROM execution_records WHERE sandbox_id = ?', (sandbox_id,))
            cursor.execute('DELETE FROM file_operations WHERE sandbox_id = ?', (sandbox_id,))
            self.db_conn.commit()
        
        return True

    def list_sandboxes(self) -> List[Dict]:
        """列出所有沙盒"""
        with self.lock:
            return [{
                'sandbox_id': sandbox['sandbox_id'],
                'name': sandbox['name'],
                'sandbox_type': sandbox['sandbox_type'],
                'description': sandbox['description'],
                'is_active': sandbox.get('is_active', True),
                'created_at': sandbox.get('created_at', 0),
                'last_used_at': sandbox.get('last_used_at', 0)
            } for sandbox in self.sandboxes.values()]

    def execute_code(self, sandbox_id: str, code: str, 
                    execution_mode: ExecutionMode = ExecutionMode.SYNC) -> Dict:
        """执行代码"""
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return {'status': 'error', 'error': '沙盒不存在'}
        
        if not sandbox.get('is_active', True):
            return {'status': 'error', 'error': '沙盒未激活'}
        
        config = json.loads(sandbox['config'])
        sandbox_type = sandbox['sandbox_type']
        
        record_id = f"exec_{uuid.uuid4().hex[:8]}"
        result = {
            'record_id': record_id,
            'sandbox_id': sandbox_id,
            'status': 'running',
            'result': None,
            'error': None,
            'execution_time': 0,
            'memory_usage': 0
        }
        
        start_time = time.time()
        
        try:
            if sandbox_type == SandboxType.PYTHON.value:
                output = self._execute_python(code, config)
            elif sandbox_type == SandboxType.JAVASCRIPT.value:
                output = self._execute_javascript(code, config)
            elif sandbox_type == SandboxType.SHELL.value:
                output = self._execute_shell(code, config)
            else:
                output = {'status': 'error', 'error': '不支持的沙盒类型'}
            
            result.update(output)
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        result['execution_time'] = time.time() - start_time
        
        with self.lock:
            sandbox['last_used_at'] = time.time()
            self._save_sandbox(sandbox)
            
            self.execution_results[record_id] = result
            self._save_execution_record(result)
        
        return result

    def _execute_python(self, code: str, config: Dict) -> Dict:
        """执行Python代码"""
        for module in config.get('forbidden_modules', []):
            if f'import {module}' in code or f'from {module}' in code:
                return {'status': 'error', 'error': f'禁止导入模块: {module}'}
        
        local_vars = {}
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        allowed_globals = {
            '__builtins__': __builtins__,
            'math': __import__('math'),
            'random': __import__('random'),
            'json': __import__('json'),
            'datetime': __import__('datetime'),
            're': __import__('re'),
            'collections': __import__('collections')
        }
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, allowed_globals, local_vars)
            
            stdout = stdout_capture.getvalue()
            stderr = stderr_capture.getvalue()
            
            if len(stdout) > config.get('max_output_size', self.max_output_size):
                stdout = stdout[:config['max_output_size']] + '... (truncated)'
            
            result = {'status': 'success', 'result': stdout}
            if stderr:
                result['error'] = stderr
            
            return result
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _execute_javascript(self, code: str, config: Dict) -> Dict:
        """执行JavaScript代码"""
        try:
            result = subprocess.run(
                ['node', '-e', code],
                capture_output=True,
                text=True,
                timeout=config.get('max_execution_time', self.max_execution_time)
            )
            
            if result.returncode != 0:
                return {'status': 'error', 'error': result.stderr}
            
            return {'status': 'success', 'result': result.stdout}
            
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'error': '执行超时'}
        except FileNotFoundError:
            return {'status': 'error', 'error': 'Node.js未安装'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _execute_shell(self, code: str, config: Dict) -> Dict:
        """执行Shell命令"""
        commands = code.strip().split('\n')
        for cmd in commands:
            cmd_name = cmd.split()[0] if cmd.strip() else ''
            if cmd_name and cmd_name not in config.get('allowed_commands', []):
                return {'status': 'error', 'error': f'禁止的命令: {cmd_name}'}
        
        try:
            result = subprocess.run(
                ['bash', '-c', code],
                capture_output=True,
                text=True,
                timeout=config.get('max_execution_time', self.max_execution_time)
            )
            
            if result.returncode != 0:
                return {'status': 'error', 'error': result.stderr}
            
            return {'status': 'success', 'result': result.stdout}
            
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'error': '执行超时'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _save_execution_record(self, result: Dict):
        """保存执行记录到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO execution_records 
                (record_id, sandbox_id, code, result, error, execution_time, memory_usage, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['record_id'],
                result['sandbox_id'],
                '',
                str(result.get('result', '')),
                str(result.get('error', '')),
                result.get('execution_time', 0),
                result.get('memory_usage', 0),
                result.get('status', 'unknown'),
                time.time()
            ))
            self.db_conn.commit()
        except Exception as e:
            print(f"保存执行记录失败: {str(e)}")

    def list_execution_records(self, sandbox_id: str = None, status: str = None) -> List[Dict]:
        """列出执行记录"""
        query = 'SELECT * FROM execution_records WHERE 1=1'
        params = []
        
        if sandbox_id:
            query += ' AND sandbox_id = ?'
            params.append(sandbox_id)
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY created_at DESC LIMIT 100'
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'record_id': row[0],
                'sandbox_id': row[1],
                'code': row[2],
                'result': row[3],
                'error': row[4],
                'execution_time': row[5],
                'memory_usage': row[6],
                'status': row[7],
                'created_at': row[8]
            })
        
        return records

    def create_file(self, sandbox_id: str, file_path: str, content: str = "") -> bool:
        """创建文件"""
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return False
        
        config = json.loads(sandbox['config'])
        if config.get('file_access_mode') not in [FileAccessMode.WRITE_ONLY.value, FileAccessMode.READ_WRITE.value]:
            return False
        
        try:
            full_path = os.path.join(config.get('working_directory', ''), file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            self._save_file_operation(sandbox_id, 'create', file_path, content)
            return True
            
        except Exception as e:
            print(f"创建文件失败: {str(e)}")
            return False

    def read_file(self, sandbox_id: str, file_path: str) -> Optional[str]:
        """读取文件"""
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return None
        
        config = json.loads(sandbox['config'])
        if config.get('file_access_mode') not in [FileAccessMode.READ_ONLY.value, FileAccessMode.READ_WRITE.value]:
            return None
        
        try:
            full_path = os.path.join(config.get('working_directory', ''), file_path)
            
            with open(full_path, 'r') as f:
                content = f.read()
            
            self._save_file_operation(sandbox_id, 'read', file_path)
            return content
            
        except Exception as e:
            print(f"读取文件失败: {str(e)}")
            return None

    def delete_file(self, sandbox_id: str, file_path: str) -> bool:
        """删除文件"""
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return False
        
        config = json.loads(sandbox['config'])
        if config.get('file_access_mode') not in [FileAccessMode.WRITE_ONLY.value, FileAccessMode.READ_WRITE.value]:
            return False
        
        try:
            full_path = os.path.join(config.get('working_directory', ''), file_path)
            os.remove(full_path)
            
            self._save_file_operation(sandbox_id, 'delete', file_path)
            return True
            
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False

    def _save_file_operation(self, sandbox_id: str, operation_type: str, file_path: str, content: str = ""):
        """保存文件操作记录"""
        try:
            operation_id = f"op_{uuid.uuid4().hex[:8]}"
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO file_operations 
                (operation_id, sandbox_id, operation_type, file_path, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                operation_id,
                sandbox_id,
                operation_type,
                file_path,
                content[:1000] if len(content) > 1000 else content,
                time.time()
            ))
            self.db_conn.commit()
        except Exception as e:
            print(f"保存文件操作记录失败: {str(e)}")

    def get_sandbox_stats(self) -> Dict:
        """获取沙盒统计信息"""
        with self.lock:
            total_sandboxes = len(self.sandboxes)
            active_sandboxes = sum(1 for s in self.sandboxes.values() if s.get('is_active', True))
            
            type_counts = {}
            for sandbox in self.sandboxes.values():
                stype = sandbox['sandbox_type']
                type_counts[stype] = type_counts.get(stype, 0) + 1
        
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM execution_records')
        total_executions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM execution_records WHERE status = "success"')
        success_executions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM execution_records WHERE status = "error"')
        error_executions = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(execution_time) FROM execution_records')
        avg_execution_time = cursor.fetchone()[0] or 0
        
        return {
            'total_sandboxes': total_sandboxes,
            'active_sandboxes': active_sandboxes,
            'sandboxes_by_type': type_counts,
            'total_executions': total_executions,
            'success_executions': success_executions,
            'error_executions': error_executions,
            'avg_execution_time': round(avg_execution_time, 2)
        }


sandbox_manager = SandboxManager()