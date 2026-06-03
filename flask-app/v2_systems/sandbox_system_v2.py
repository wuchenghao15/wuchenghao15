# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沙盒系统 V2.0 (Sandbox System)
增强版沙盒系统，支持多类型隔离、文件操作、安全策略和资源限制
"""

import os
import sys
import time
import uuid
import json
import shutil
import hashlib
import logging
import tempfile
import threading
import sqlite3
import subprocess
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sandbox_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SandboxSystem')

class SandboxType(Enum):
    """沙盒类型枚举"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SHELL = "shell"
    SQL = "sql"
    HTML = "html"
    DOCKER = "docker"

class SandboxStatus(Enum):
    """沙盒状态枚举"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    TIMEOUT = "timeout"
    ERROR = "error"
    DESTROYED = "destroyed"

class SecurityLevel(Enum):
    """安全级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SandboxConfig:
    """沙盒配置"""
    config_id: str
    name: str
    sandbox_type: SandboxType
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    timeout: int = 30
    max_memory: int = 512
    max_cpu: float = 2.0
    max_disk: int = 100
    max_network: bool = True
    allow_filesystem: bool = False
    allowed_paths: List[str] = None
    blocked_modules: List[str] = None
    environment: Dict = None
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.allowed_paths is None:
            self.allowed_paths = []
        if self.blocked_modules is None:
            self.blocked_modules = []
        if self.environment is None:
            self.environment = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class Sandbox:
    """沙盒实例"""
    sandbox_id: str
    config: SandboxConfig
    status: SandboxStatus = SandboxStatus.CREATED
    workspace_path: str = ""
    pid: Optional[int] = None
    start_time: float = 0.0
    end_time: float = 0.0
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    resources_used: Dict = None
    
    def __post_init__(self):
        if self.resources_used is None:
            self.resources_used = {}
        if self.start_time == 0.0:
            self.start_time = time.time()

@dataclass
class ExecutionResult:
    """执行结果"""
    result_id: str
    sandbox_id: str
    code: str
    output: str
    error: str
    exit_code: int
    execution_time: float
    memory_used: float
    cpu_time: float
    timestamp: float
    success: bool

@dataclass
class FileOperation:
    """文件操作"""
    operation_id: str
    sandbox_id: str
    operation: str
    path: str
    size: int
    allowed: bool
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class SandboxSystem:
    """增强版沙盒系统"""
    
    def __init__(self):
        """初始化沙盒系统"""
        self.sandboxes: Dict[str, Sandbox] = {}
        self.configs: Dict[str, SandboxConfig] = {}
        self.results: Dict[str, ExecutionResult] = {}
        self.file_operations: Dict[str, FileOperation] = {}
        
        self.base_workspace = tempfile.mkdtemp(prefix="sandbox_")
        
        self.lock = threading.Lock()
        
        self._init_database()
        self._init_default_configs()
        
        self._start_resource_monitor()
        
        logger.info("沙盒系统初始化完成")
        logger.info(f"工作空间目录: {self.base_workspace}")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_conn = sqlite3.connect('sandbox_system.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sandbox_configs (
                    config_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sandbox_type TEXT NOT NULL,
                    security_level TEXT DEFAULT 'medium',
                    timeout INTEGER DEFAULT 30,
                    max_memory INTEGER DEFAULT 512,
                    max_cpu REAL DEFAULT 2.0,
                    max_disk INTEGER DEFAULT 100,
                    max_network BOOLEAN DEFAULT TRUE,
                    allow_filesystem BOOLEAN DEFAULT FALSE,
                    allowed_paths TEXT,
                    blocked_modules TEXT,
                    environment TEXT,
                    created_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sandboxes (
                    sandbox_id TEXT PRIMARY KEY,
                    config_id TEXT NOT NULL,
                    status TEXT DEFAULT 'created',
                    workspace_path TEXT,
                    pid INTEGER,
                    start_time REAL,
                    end_time REAL,
                    exit_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    resources_used TEXT,
                    FOREIGN KEY (config_id) REFERENCES sandbox_configs(config_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_results (
                    result_id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    output TEXT,
                    error TEXT,
                    exit_code INTEGER,
                    execution_time REAL,
                    memory_used REAL,
                    cpu_time REAL,
                    timestamp REAL,
                    success BOOLEAN,
                    FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_operations (
                    operation_id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size INTEGER DEFAULT 0,
                    timestamp REAL,
                    allowed BOOLEAN,
                    FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id)
                )
            ''')
            
            self.db_conn.commit()
            logger.info("沙盒系统数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def _init_default_configs(self):
        """初始化默认沙盒配置"""
        default_configs = [
            SandboxConfig(
                config_id="config_python_safe",
                name="Python安全沙盒",
                sandbox_type=SandboxType.PYTHON,
                security_level=SecurityLevel.HIGH,
                timeout=10,
                max_memory=256,
                max_cpu=1.0,
                allow_filesystem=False,
                blocked_modules=["os", "sys", "subprocess", "socket", "urllib"]
            ),
            SandboxConfig(
                config_id="config_python_full",
                name="Python完整沙盒",
                sandbox_type=SandboxType.PYTHON,
                security_level=SecurityLevel.MEDIUM,
                timeout=30,
                max_memory=512,
                max_cpu=2.0,
                allow_filesystem=True,
                blocked_modules=["subprocess", "socket"]
            ),
            SandboxConfig(
                config_id="config_shell",
                name="Shell沙盒",
                sandbox_type=SandboxType.SHELL,
                security_level=SecurityLevel.MEDIUM,
                timeout=5,
                max_memory=128,
                max_cpu=1.0,
                allow_filesystem=True,
                blocked_modules=["rm", "dd", "mkfs", "fdisk"]
            ),
            SandboxConfig(
                config_id="config_sql",
                name="SQL沙盒",
                sandbox_type=SandboxType.SQL,
                security_level=SecurityLevel.HIGH,
                timeout=10,
                blocked_modules=["DROP", "DELETE", "TRUNCATE", "ALTER"]
            ),
            SandboxConfig(
                config_id="config_html",
                name="HTML沙盒",
                sandbox_type=SandboxType.HTML,
                security_level=SecurityLevel.MEDIUM,
                timeout=5,
                allow_filesystem=False
            )
        ]
        
        with self.lock:
            for config in default_configs:
                if config.config_id not in self.configs:
                    self.configs[config.config_id] = config
                    self._save_config(config)
    
    def _save_config(self, config: SandboxConfig):
        """保存配置到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sandbox_configs
                (config_id, name, sandbox_type, security_level, timeout, max_memory, 
                 max_cpu, max_disk, max_network, allow_filesystem, allowed_paths, 
                 blocked_modules, environment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.config_id, config.name, config.sandbox_type.value,
                config.security_level.value, config.timeout, config.max_memory,
                config.max_cpu, config.max_disk, config.max_network,
                config.allow_filesystem, json.dumps(config.allowed_paths),
                json.dumps(config.blocked_modules), json.dumps(config.environment),
                config.created_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
    
    def create_config(self, name: str, sandbox_type: SandboxType,
                     security_level: SecurityLevel = SecurityLevel.MEDIUM,
                     timeout: int = 30, max_memory: int = 512,
                     max_cpu: float = 2.0, **kwargs) -> str:
        """创建沙盒配置"""
        config_id = f"config_{uuid.uuid4().hex[:8]}"
        
        config = SandboxConfig(
            config_id=config_id,
            name=name,
            sandbox_type=sandbox_type,
            security_level=security_level,
            timeout=timeout,
            max_memory=max_memory,
            max_cpu=max_cpu,
            **kwargs
        )
        
        with self.lock:
            self.configs[config_id] = config
            self._save_config(config)
        
        logger.info(f"创建沙盒配置: {name} ({config_id})")
        return config_id
    
    def get_config(self, config_id: str) -> Optional[SandboxConfig]:
        """获取沙盒配置"""
        with self.lock:
            return self.configs.get(config_id)
    
    def list_configs(self) -> List[Dict]:
        """列出沙盒配置"""
        with self.lock:
            return [{
                "config_id": c.config_id,
                "name": c.name,
                "sandbox_type": c.sandbox_type.value,
                "security_level": c.security_level.value,
                "timeout": c.timeout,
                "max_memory": c.max_memory
            } for c in self.configs.values()]
    
    def create_sandbox(self, config_id: str) -> str:
        """创建沙盒实例"""
        with self.lock:
            config = self.configs.get(config_id)
            if not config:
                raise ValueError(f"配置不存在: {config_id}")
            
            sandbox_id = f"sbox_{uuid.uuid4().hex[:8]}"
            workspace_path = os.path.join(self.base_workspace, sandbox_id)
            os.makedirs(workspace_path, exist_ok=True)
            
            sandbox = Sandbox(
                sandbox_id=sandbox_id,
                config=config,
                workspace_path=workspace_path
            )
            
            self.sandboxes[sandbox_id] = sandbox
            self._save_sandbox(sandbox)
        
        logger.info(f"创建沙盒: {sandbox_id}")
        return sandbox_id
    
    def _save_sandbox(self, sandbox: Sandbox):
        """保存沙盒到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sandboxes
                (sandbox_id, config_id, status, workspace_path, pid, start_time, 
                 end_time, exit_code, stdout, stderr, resources_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sandbox.sandbox_id, sandbox.config.config_id, sandbox.status.value,
                sandbox.workspace_path, sandbox.pid, sandbox.start_time,
                sandbox.end_time, sandbox.exit_code, sandbox.stdout,
                sandbox.stderr, json.dumps(sandbox.resources_used)
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存沙盒失败: {str(e)}")
    
    def execute_code(self, sandbox_id: str, code: str) -> str:
        """执行代码"""
        with self.lock:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                raise ValueError(f"沙盒不存在: {sandbox_id}")
            
            if sandbox.status == SandboxStatus.RUNNING:
                raise ValueError("沙盒正在运行中")
            
            sandbox.status = SandboxStatus.RUNNING
            sandbox.start_time = time.time()
            sandbox.stdout = ""
            sandbox.stderr = ""
            self._save_sandbox(sandbox)
        
        result_id = f"res_{uuid.uuid4().hex[:8]}"
        
        threading.Thread(
            target=self._execute_in_sandbox,
            args=(sandbox_id, code, result_id),
            daemon=True
        ).start()
        
        logger.info(f"提交执行任务: {sandbox_id} -> {result_id}")
        return result_id
    
    def _execute_in_sandbox(self, sandbox_id: str, code: str, result_id: str):
        """在沙盒中执行代码"""
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return
        
        start_time = time.time()
        output = ""
        error = ""
        exit_code = 0
        success = True
        
        try:
            if sandbox.config.sandbox_type == SandboxType.PYTHON:
                output, error, exit_code = self._execute_python(sandbox, code)
            elif sandbox.config.sandbox_type == SandboxType.SHELL:
                output, error, exit_code = self._execute_shell(sandbox, code)
            elif sandbox.config.sandbox_type == SandboxType.SQL:
                output, error, exit_code = self._execute_sql(sandbox, code)
            elif sandbox.config.sandbox_type == SandboxType.HTML:
                output, error, exit_code = self._execute_html(sandbox, code)
            else:
                output = f"不支持的沙盒类型: {sandbox.config.sandbox_type.value}"
                exit_code = 1
        
        except Exception as e:
            error = str(e)
            exit_code = 1
            success = False
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        result = ExecutionResult(
            result_id=result_id,
            sandbox_id=sandbox_id,
            code=code,
            output=output,
            error=error,
            exit_code=exit_code,
            execution_time=execution_time,
            memory_used=0,
            cpu_time=execution_time,
            timestamp=end_time,
            success=success
        )
        
        with self.lock:
            self.results[result_id] = result
            sandbox.status = SandboxStatus.STOPPED
            sandbox.end_time = end_time
            sandbox.exit_code = exit_code
            sandbox.stdout = output
            sandbox.stderr = error
            self._save_sandbox(sandbox)
            self._save_result(result)
    
    def _execute_python(self, sandbox: Sandbox, code: str) -> tuple:
        """执行Python代码"""
        temp_file = os.path.join(sandbox.workspace_path, "temp_script.py")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=sandbox.config.timeout,
                cwd=sandbox.workspace_path
            )
            
            os.remove(temp_file)
            
            return result.stdout, result.stderr, result.returncode
        
        except subprocess.TimeoutExpired:
            return "", "执行超时", -1
        except Exception as e:
            return "", str(e), 1
    
    def _execute_shell(self, sandbox: Sandbox, code: str) -> tuple:
        """执行Shell代码"""
        try:
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=sandbox.config.timeout,
                cwd=sandbox.workspace_path
            )
            
            return result.stdout, result.stderr, result.returncode
        
        except subprocess.TimeoutExpired:
            return "", "执行超时", -1
        except Exception as e:
            return "", str(e), 1
    
    def _execute_sql(self, sandbox: Sandbox, code: str) -> tuple:
        """执行SQL代码"""
        blocked_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
        
        code_upper = code.upper()
        for keyword in blocked_keywords:
            if keyword in code_upper:
                return "", f"禁止的操作: {keyword}", 1
        
        return f"[SQL模拟执行] {code}", "", 0
    
    def _execute_html(self, sandbox: Sandbox, code: str) -> tuple:
        """执行HTML代码"""
        return f"[HTML预览] 代码长度: {len(code)} 字符", "", 0
    
    def _save_result(self, result: ExecutionResult):
        """保存执行结果"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO execution_results
                (result_id, sandbox_id, code, output, error, exit_code, 
                 execution_time, memory_used, cpu_time, timestamp, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.result_id, result.sandbox_id, result.code, result.output,
                result.error, result.exit_code, result.execution_time,
                result.memory_used, result.cpu_time, result.timestamp, result.success
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存结果失败: {str(e)}")
    
    def get_result(self, result_id: str) -> Optional[ExecutionResult]:
        """获取执行结果"""
        with self.lock:
            return self.results.get(result_id)
    
    def wait_for_result(self, result_id: str, timeout: int = 30) -> Optional[ExecutionResult]:
        """等待执行结果"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self.lock:
                result = self.results.get(result_id)
                if result:
                    return result
            time.sleep(0.1)
        
        return None
    
    def pause_sandbox(self, sandbox_id: str) -> bool:
        """暂停沙盒"""
        with self.lock:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox or sandbox.status != SandboxStatus.RUNNING:
                return False
            
            sandbox.status = SandboxStatus.PAUSED
            self._save_sandbox(sandbox)
        
        logger.info(f"暂停沙盒: {sandbox_id}")
        return True
    
    def resume_sandbox(self, sandbox_id: str) -> bool:
        """恢复沙盒"""
        with self.lock:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox or sandbox.status != SandboxStatus.PAUSED:
                return False
            
            sandbox.status = SandboxStatus.RUNNING
            self._save_sandbox(sandbox)
        
        logger.info(f"恢复沙盒: {sandbox_id}")
        return True
    
    def stop_sandbox(self, sandbox_id: str) -> bool:
        """停止沙盒"""
        with self.lock:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                return False
            
            sandbox.status = SandboxStatus.STOPPED
            sandbox.end_time = time.time()
            
            if sandbox.pid:
                try:
                    os.kill(sandbox.pid, 9)
                except Exception:
                    pass
            
            self._save_sandbox(sandbox)
        
        logger.info(f"停止沙盒: {sandbox_id}")
        return True
    
    def destroy_sandbox(self, sandbox_id: str) -> bool:
        """销毁沙盒"""
        with self.lock:
            sandbox = self.sandboxes.get(sandbox_id)
            if not sandbox:
                return False
            
            if sandbox.workspace_path and os.path.exists(sandbox.workspace_path):
                shutil.rmtree(sandbox.workspace_path, ignore_errors=True)
            
            sandbox.status = SandboxStatus.DESTROYED
            del self.sandboxes[sandbox_id]
        
        logger.info(f"销毁沙盒: {sandbox_id}")
        return True
    
    def get_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        """获取沙盒"""
        with self.lock:
            return self.sandboxes.get(sandbox_id)
    
    def list_sandboxes(self, status: SandboxStatus = None) -> List[Dict]:
        """列出沙盒"""
        with self.lock:
            result = []
            for sandbox_id, sandbox in self.sandboxes.items():
                if status and sandbox.status != status:
                    continue
                
                result.append({
                    "sandbox_id": sandbox.sandbox_id,
                    "config_name": sandbox.config.name,
                    "sandbox_type": sandbox.config.sandbox_type.value,
                    "status": sandbox.status.value,
                    "start_time": sandbox.start_time,
                    "workspace_path": sandbox.workspace_path
                })
            return result
    
    def write_file(self, sandbox_id: str, path: str, content: str) -> bool:
        """写入文件"""
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return False
        
        if not sandbox.config.allow_filesystem:
            self._log_file_operation(sandbox_id, "write", path, len(content), False)
            return False
        
        try:
            file_path = os.path.join(sandbox.workspace_path, path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_file_operation(sandbox_id, "write", path, len(content), True)
            logger.debug(f"写入文件: {sandbox_id}/{path}")
            return True
        
        except Exception as e:
            logger.error(f"写入文件失败: {str(e)}")
            self._log_file_operation(sandbox_id, "write", path, 0, False)
            return False
    
    def read_file(self, sandbox_id: str, path: str) -> Optional[str]:
        """读取文件"""
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return None
        
        try:
            file_path = os.path.join(sandbox.workspace_path, path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self._log_file_operation(sandbox_id, "read", path, len(content), True)
            return content
        
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            self._log_file_operation(sandbox_id, "read", path, 0, False)
            return None
    
    def list_files(self, sandbox_id: str, path: str = "") -> List[Dict]:
        """列出文件"""
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return []
        
        try:
            dir_path = os.path.join(sandbox.workspace_path, path)
            
            if not os.path.exists(dir_path):
                return []
            
            files = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                stat = os.stat(item_path)
                
                files.append({
                    "name": item,
                    "path": os.path.join(path, item),
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": stat.st_size if os.path.isfile(item_path) else 0,
                    "modified": stat.st_mtime
                })
            
            return files
        
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
            return []
    
    def _log_file_operation(self, sandbox_id: str, operation: str, path: str, size: int, allowed: bool):
        """记录文件操作"""
        operation_id = f"fop_{uuid.uuid4().hex[:8]}"
        
        op = FileOperation(
            operation_id=operation_id,
            sandbox_id=sandbox_id,
            operation=operation,
            path=path,
            size=size,
            allowed=allowed
        )
        
        with self.lock:
            self.file_operations[operation_id] = op
            
            try:
                cursor = self.db_conn.cursor()
                cursor.execute('''
                    INSERT INTO file_operations
                    (operation_id, sandbox_id, operation, path, size, timestamp, allowed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    op.operation_id, op.sandbox_id, op.operation,
                    op.path, op.size, op.timestamp, op.allowed
                ))
                self.db_conn.commit()
            except Exception as e:
                logger.error(f"记录文件操作失败: {str(e)}")
    
    def _start_resource_monitor(self):
        """启动资源监控线程"""
        self.resource_monitor = threading.Thread(
            target=self._resource_monitor_loop,
            name="sandbox_resource_monitor",
            daemon=True
        )
        self.resource_monitor.start()
    
    def _resource_monitor_loop(self):
        """资源监控循环"""
        while True:
            try:
                self._check_sandbox_resources()
                time.sleep(5)
            except Exception as e:
                logger.error(f"资源监控错误: {str(e)}")
                time.sleep(30)
    
    def _check_sandbox_resources(self):
        """检查沙盒资源使用"""
        with self.lock:
            for sandbox_id, sandbox in self.sandboxes.items():
                if sandbox.status != SandboxStatus.RUNNING:
                    continue
                
                if sandbox.start_time > 0:
                    elapsed = time.time() - sandbox.start_time
                    if elapsed > sandbox.config.timeout:
                        sandbox.status = SandboxStatus.TIMEOUT
                        self._save_sandbox(sandbox)
                        logger.warning(f"沙盒超时: {sandbox_id}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            total_sandboxes = len(self.sandboxes)
            running_sandboxes = sum(1 for s in self.sandboxes.values() 
                                  if s.status == SandboxStatus.RUNNING)
            
            total_results = len(self.results)
            successful_results = sum(1 for r in self.results.values() if r.success)
            
            file_operations = len(self.file_operations)
            blocked_operations = sum(1 for op in self.file_operations.values() if not op.allowed)
            
            return {
                "total_configs": len(self.configs),
                "total_sandboxes": total_sandboxes,
                "running_sandboxes": running_sandboxes,
                "stopped_sandboxes": total_sandboxes - running_sandboxes,
                "total_executions": total_results,
                "successful_executions": successful_results,
                "failed_executions": total_results - successful_results,
                "total_file_operations": file_operations,
                "blocked_file_operations": blocked_operations,
                "workspace_size": self._get_workspace_size()
            }
    
    def _get_workspace_size(self) -> int:
        """获取工作空间大小"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.base_workspace):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(file_path)
            return total_size
        except Exception:
            return 0
    
    def cleanup_old_sandboxes(self, max_age: int = 3600):
        """清理旧沙盒"""
        current_time = time.time()
        cleaned = 0
        
        with self.lock:
            to_remove = []
            
            for sandbox_id, sandbox in self.sandboxes.items():
                if sandbox.status in [SandboxStatus.STOPPED, SandboxStatus.ERROR, SandboxStatus.TIMEOUT]:
                    if sandbox.end_time and (current_time - sandbox.end_time) > max_age:
                        to_remove.append(sandbox_id)
            
            for sandbox_id in to_remove:
                self.destroy_sandbox(sandbox_id)
                cleaned += 1
        
        logger.info(f"清理旧沙盒: {cleaned} 个")
        return cleaned
    
    def shutdown(self):
        """关闭沙盒系统"""
        logger.info("关闭沙盒系统...")
        
        with self.lock:
            for sandbox_id in list(self.sandboxes.keys()):
                self.destroy_sandbox(sandbox_id)
        
        if os.path.exists(self.base_workspace):
            shutil.rmtree(self.base_workspace, ignore_errors=True)
        
        self.db_conn.close()
        
        logger.info("沙盒系统已关闭")


def test_sandbox_system():
    """测试沙盒系统"""
    print("沙盒系统 V2.0 测试")
    print("=" * 60)
    
    sandbox = SandboxSystem()
    
    print("列出默认配置:")
    configs = sandbox.list_configs()
    for config in configs:
        print(f"  {config['name']}: {config['sandbox_type']} ({config['security_level']})")
    
    print("\n创建沙盒配置:")
    new_config_id = sandbox.create_config(
        name="测试配置",
        sandbox_type=SandboxType.PYTHON,
        security_level=SecurityLevel.HIGH,
        timeout=10
    )
    print(f"  创建配置: {new_config_id}")
    
    print("\n创建沙盒:")
    sandbox_id = sandbox.create_sandbox("config_python_safe")
    print(f"  创建沙盒: {sandbox_id}")
    
    print("\n列出沙盒:")
    sandboxes = sandbox.list_sandboxes()
    for s in sandboxes:
        print(f"  {s['sandbox_id']}: {s['status']} ({s['sandbox_type']})")
    
    print("\n执行Python代码:")
    code = '''
print("Hello from sandbox!")
for i in range(3):
    print(f"Count: {i}")
'''
    result_id = sandbox.execute_code(sandbox_id, code)
    print(f"  提交执行: {result_id}")
    
    time.sleep(2)
    
    result = sandbox.wait_for_result(result_id, timeout=10)
    if result:
        print(f"  执行结果: {'成功' if result.success else '失败'}")
        print(f"  输出: {result.output[:100]}...")
        print(f"  执行时间: {result.execution_time:.4f}s")
    
    print("\n执行Shell代码:")
    shell_sandbox_id = sandbox.create_sandbox("config_shell")
    shell_result_id = sandbox.execute_code(shell_sandbox_id, "echo 'Hello Shell'; date")
    time.sleep(1)
    
    shell_result = sandbox.wait_for_result(shell_result_id, timeout=5)
    if shell_result:
        print(f"  输出: {shell_result.output.strip()}")
    
    print("\n写入文件测试:")
    if sandbox.write_file(sandbox_id, "test.txt", "Hello World"):
        print("  文件写入成功")
        
        content = sandbox.read_file(sandbox_id, "test.txt")
        print(f"  文件内容: {content}")
        
        files = sandbox.list_files(sandbox_id)
        print(f"  文件列表: {len(files)} 个文件")
    
    print("\n系统统计:")
    stats = sandbox.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n清理旧沙盒:")
    cleaned = sandbox.cleanup_old_sandboxes(max_age=0)
    print(f"  清理: {cleaned} 个")
    
    print("\n沙盒系统 V2.0 测试完成")
    print("=" * 60)
    
    sandbox.shutdown()


if __name__ == "__main__":
    test_sandbox_system()