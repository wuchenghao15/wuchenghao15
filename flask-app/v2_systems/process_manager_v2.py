# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理系统 V2.0 (Process Manager)
增强版进程管理系统，支持进程池、进程组、监控和资源管理
"""

import os
import time
import uuid
import json
import signal
import logging
import threading
import subprocess
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable, Tuple
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ProcessManager')

class ProcessStatus(Enum):
    """进程状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"
    RESTARTING = "restarting"

class ProcessType(Enum):
    """进程类型枚举"""
    DAEMON = "daemon"
    WORKER = "worker"
    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"
    BATCH = "batch"

class RestartPolicy(Enum):
    """重启策略枚举"""
    NEVER = "never"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"
    ON_CRASH = "on_crash"

@dataclass
class ProcessConfig:
    """进程配置"""
    name: str
    command: str
    args: List[str] = None
    cwd: str = None
    env: Dict[str, str] = None
    stdout: str = None
    stderr: str = None
    process_type: ProcessType = ProcessType.WORKER
    restart_policy: RestartPolicy = RestartPolicy.ON_FAILURE
    max_restarts: int = 3
    restart_delay: int = 5
    timeout: int = 0
    resources: Dict = None
    auto_start: bool = True
    
    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.env is None:
            self.env = {}
        if self.resources is None:
            self.resources = {}

@dataclass
class ProcessInfo:
    """进程信息"""
    process_id: str
    config: ProcessConfig
    pid: Optional[int] = None
    status: ProcessStatus = ProcessStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    exit_code: Optional[int] = None
    restart_count: int = 0
    stdout_lines: List[str] = None
    stderr_lines: List[str] = None
    last_output_time: Optional[float] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    def __post_init__(self):
        if self.stdout_lines is None:
            self.stdout_lines = []
        if self.stderr_lines is None:
            self.stderr_lines = []

@dataclass
class ProcessGroup:
    """进程组"""
    group_id: str
    name: str
    processes: List[str] = None
    max_parallel: int = 10
    status: str = "running"
    
    def __post_init__(self):
        if self.processes is None:
            self.processes = []

class ProcessManager:
    """增强版进程管理系统"""
    
    def __init__(self):
        """初始化进程管理器"""
        self.processes: Dict[str, ProcessInfo] = {}
        self.groups: Dict[str, ProcessGroup] = {}
        self.process_to_group: Dict[str, str] = {}
        
        self.status = "running"
        self.is_running = True
        
        self.lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        self.stats = {
            "total_processes": 0,
            "running_processes": 0,
            "completed_processes": 0,
            "failed_processes": 0,
            "total_restarts": 0,
            "peak_processes": 0,
            "system_cpu_usage": 0.0,
            "system_memory_usage": 0.0
        }
        
        self._start_monitor()
        
        logger.info("进程管理器初始化完成")
    
    def _start_monitor(self):
        """启动监控线程"""
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="pm_monitor",
            daemon=True
        )
        self.monitor_thread.start()
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                self._update_process_statuses()
                self._collect_system_metrics()
                self._handle_restarts()
                time.sleep(2)
            except Exception as e:
                logger.error(f"监控线程错误: {str(e)}")
                time.sleep(2)
    
    def _update_process_statuses(self):
        """更新进程状态"""
        with self.lock:
            for process_id, info in list(self.processes.items()):
                if info.status == ProcessStatus.RUNNING and info.pid:
                    try:
                        os.kill(info.pid, 0)
                    except OSError:
                        info.status = ProcessStatus.STOPPED
                        info.end_time = time.time()
                        logger.info(f"进程已停止: {info.config.name} (PID: {info.pid})")
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            if os.name == 'posix':
                cpu_usage = self._get_cpu_usage()
                memory_usage = self._get_memory_usage()
                
                with self.stats_lock:
                    self.stats["system_cpu_usage"] = cpu_usage
                    self.stats["system_memory_usage"] = memory_usage
        except Exception as e:
            logger.debug(f"收集系统指标失败: {str(e)}")
    
    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            result = subprocess.run(
                ['top', '-bn1'],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if '%Cpu(s):' in line:
                    parts = line.split()
                    idle = float(parts[parts.index('id,') + 1])
                    return 100.0 - idle
        except Exception:
            pass
        return 0.0
    
    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        try:
            result = subprocess.run(
                ['free', '-m'],
                capture_output=True,
                text=True
            )
            lines = result.stdout.split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                total = int(parts[1])
                used = int(parts[2])
                return (used / total) * 100
        except Exception:
            pass
        return 0.0
    
    def _handle_restarts(self):
        """处理进程重启"""
        with self.lock:
            for process_id, info in list(self.processes.items()):
                if info.status == ProcessStatus.STOPPED or info.status == ProcessStatus.ERROR:
                    if info.config.restart_policy == RestartPolicy.ALWAYS or \
                       (info.config.restart_policy == RestartPolicy.ON_FAILURE and info.exit_code != 0) or \
                       (info.config.restart_policy == RestartPolicy.ON_CRASH and info.exit_code < 0):
                       
                        if info.restart_count < info.config.max_restarts:
                            self._schedule_restart(process_id)
    
    def _schedule_restart(self, process_id: str):
        """调度进程重启"""
        info = self.processes[process_id]
        
        def delayed_restart():
            time.sleep(info.config.restart_delay)
            self.restart_process(process_id)
        
        restart_thread = threading.Thread(
            target=delayed_restart,
            name=f"restart_{process_id}",
            daemon=True
        )
        restart_thread.start()
        
        info.status = ProcessStatus.RESTARTING
        info.restart_count += 1
        
        with self.stats_lock:
            self.stats["total_restarts"] += 1
        
        logger.info(f"计划重启进程: {info.config.name}, 第 {info.restart_count} 次")
    
    def create_process(self, config: ProcessConfig) -> str:
        """创建进程"""
        process_id = f"proc_{uuid.uuid4().hex[:8]}"
        
        info = ProcessInfo(
            process_id=process_id,
            config=config
        )
        
        with self.lock:
            self.processes[process_id] = info
            self.stats["total_processes"] += 1
        
        logger.info(f"创建进程: {config.name} ({process_id})")
        
        if config.auto_start:
            self.start_process(process_id)
        
        return process_id
    
    def start_process(self, process_id: str) -> bool:
        """启动进程"""
        with self.lock:
            info = self.processes.get(process_id)
            if not info:
                logger.error(f"进程不存在: {process_id}")
                return False
            
            if info.status == ProcessStatus.RUNNING:
                logger.warning(f"进程已在运行: {info.config.name}")
                return False
        
        try:
            env = os.environ.copy()
            env.update(info.config.env)
            
            stdout_handle = None
            stderr_handle = None
            
            if info.config.stdout:
                stdout_handle = open(info.config.stdout, 'a')
            else:
                stdout_handle = subprocess.PIPE
            
            if info.config.stderr:
                stderr_handle = open(info.config.stderr, 'a')
            else:
                stderr_handle = subprocess.PIPE
            
            process = subprocess.Popen(
                [info.config.command] + info.config.args,
                cwd=info.config.cwd or os.getcwd(),
                env=env,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                start_new_session=True
            )
            
            with self.lock:
                info.pid = process.pid
                info.status = ProcessStatus.RUNNING
                info.start_time = time.time()
                info.restart_count = 0
                
                self.stats["running_processes"] += 1
                if self.stats["running_processes"] > self.stats["peak_processes"]:
                    self.stats["peak_processes"] = self.stats["running_processes"]
            
            self._start_output_reader(process, process_id)
            
            logger.info(f"启动进程: {info.config.name}, PID: {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"启动进程失败: {info.config.name}, 错误: {str(e)}")
            with self.lock:
                info.status = ProcessStatus.ERROR
                info.exit_code = -1
            return False
    
    def _start_output_reader(self, process: subprocess.Popen, process_id: str):
        """启动输出读取线程"""
        def read_stdout():
            while process.poll() is None:
                try:
                    line = process.stdout.readline()
                    if line:
                        with self.lock:
                            info = self.processes.get(process_id)
                            if info:
                                info.stdout_lines.append(line.strip())
                                info.last_output_time = time.time()
                                if len(info.stdout_lines) > 1000:
                                    info.stdout_lines.pop(0)
                except Exception:
                    pass
        
        def read_stderr():
            while process.poll() is None:
                try:
                    line = process.stderr.readline()
                    if line:
                        with self.lock:
                            info = self.processes.get(process_id)
                            if info:
                                info.stderr_lines.append(line.strip())
                                info.last_output_time = time.time()
                                if len(info.stderr_lines) > 1000:
                                    info.stderr_lines.pop(0)
                except Exception:
                    pass
        
        if process.stdout:
            stdout_thread = threading.Thread(
                target=read_stdout,
                name=f"stdout_{process_id}",
                daemon=True
            )
            stdout_thread.start()
        
        if process.stderr:
            stderr_thread = threading.Thread(
                target=read_stderr,
                name=f"stderr_{process_id}",
                daemon=True
            )
            stderr_thread.start()
    
    def stop_process(self, process_id: str, force: bool = False) -> bool:
        """停止进程"""
        with self.lock:
            info = self.processes.get(process_id)
            if not info:
                logger.error(f"进程不存在: {process_id}")
                return False
            
            if info.status != ProcessStatus.RUNNING:
                logger.warning(f"进程未在运行: {info.config.name}")
                return False
            
            pid = info.pid
        
        try:
            if force:
                os.kill(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGTERM)
            
            timeout = 5
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except OSError:
                    break
            
            with self.lock:
                info.status = ProcessStatus.STOPPED
                info.end_time = time.time()
                info.exit_code = 0
                self.stats["running_processes"] -= 1
            
            logger.info(f"停止进程: {info.config.name}, PID: {pid}")
            return True
            
        except Exception as e:
            logger.error(f"停止进程失败: {info.config.name}, 错误: {str(e)}")
            return False
    
    def restart_process(self, process_id: str) -> bool:
        """重启进程"""
        if not self.stop_process(process_id):
            return False
        
        time.sleep(1)
        return self.start_process(process_id)
    
    def get_process_status(self, process_id: str) -> Optional[Dict]:
        """获取进程状态"""
        with self.lock:
            info = self.processes.get(process_id)
            if not info:
                return None
            
            return {
                "process_id": info.process_id,
                "name": info.config.name,
                "command": info.config.command,
                "status": info.status.value,
                "pid": info.pid,
                "start_time": info.start_time,
                "end_time": info.end_time,
                "exit_code": info.exit_code,
                "restart_count": info.restart_count,
                "max_restarts": info.config.max_restarts,
                "restart_policy": info.config.restart_policy.value,
                "process_type": info.config.process_type.value,
                "cpu_usage": info.cpu_usage,
                "memory_usage": info.memory_usage,
                "last_output_time": info.last_output_time
            }
    
    def list_processes(self, status_filter: Optional[str] = None) -> List[Dict]:
        """列出所有进程"""
        with self.lock:
            results = []
            for process_id, info in self.processes.items():
                if status_filter and info.status.value != status_filter:
                    continue
                
                results.append({
                    "process_id": info.process_id,
                    "name": info.config.name,
                    "status": info.status.value,
                    "pid": info.pid,
                    "start_time": info.start_time,
                    "restart_count": info.restart_count
                })
            return results
    
    def get_process_output(self, process_id: str, lines: int = 50) -> Dict:
        """获取进程输出"""
        with self.lock:
            info = self.processes.get(process_id)
            if not info:
                return {"error": "进程不存在"}
            
            return {
                "stdout": info.stdout_lines[-lines:],
                "stderr": info.stderr_lines[-lines:]
            }
    
    def create_group(self, name: str, max_parallel: int = 10) -> str:
        """创建进程组"""
        group_id = f"grp_{uuid.uuid4().hex[:8]}"
        
        group = ProcessGroup(
            group_id=group_id,
            name=name,
            max_parallel=max_parallel
        )
        
        with self.lock:
            self.groups[group_id] = group
        
        logger.info(f"创建进程组: {name} ({group_id})")
        return group_id
    
    def add_to_group(self, group_id: str, process_id: str) -> bool:
        """添加进程到组"""
        with self.lock:
            group = self.groups.get(group_id)
            if not group:
                logger.error(f"进程组不存在: {group_id}")
                return False
            
            info = self.processes.get(process_id)
            if not info:
                logger.error(f"进程不存在: {process_id}")
                return False
            
            if process_id in group.processes:
                logger.warning(f"进程已在组中: {process_id}")
                return False
            
            if len(group.processes) >= group.max_parallel:
                logger.error(f"进程组已满: {group.name}")
                return False
            
            group.processes.append(process_id)
            self.process_to_group[process_id] = group_id
        
        logger.info(f"添加进程到组: {info.config.name} -> {group.name}")
        return True
    
    def remove_from_group(self, group_id: str, process_id: str) -> bool:
        """从组中移除进程"""
        with self.lock:
            group = self.groups.get(group_id)
            if not group:
                logger.error(f"进程组不存在: {group_id}")
                return False
            
            if process_id not in group.processes:
                logger.warning(f"进程不在组中: {process_id}")
                return False
            
            group.processes.remove(process_id)
            self.process_to_group.pop(process_id, None)
        
        logger.info(f"从组中移除进程: {process_id}")
        return True
    
    def start_group(self, group_id: str) -> bool:
        """启动组内所有进程"""
        with self.lock:
            group = self.groups.get(group_id)
            if not group:
                logger.error(f"进程组不存在: {group_id}")
                return False
            
            success_count = 0
            for process_id in group.processes:
                if self.start_process(process_id):
                    success_count += 1
            
            logger.info(f"启动进程组: {group.name}, {success_count}/{len(group.processes)} 成功")
            return success_count > 0
    
    def stop_group(self, group_id: str, force: bool = False) -> bool:
        """停止组内所有进程"""
        with self.lock:
            group = self.groups.get(group_id)
            if not group:
                logger.error(f"进程组不存在: {group_id}")
                return False
            
            success_count = 0
            for process_id in group.processes:
                if self.stop_process(process_id, force):
                    success_count += 1
            
            logger.info(f"停止进程组: {group.name}, {success_count}/{len(group.processes)} 成功")
            return success_count > 0
    
    def get_group_status(self, group_id: str) -> Optional[Dict]:
        """获取进程组状态"""
        with self.lock:
            group = self.groups.get(group_id)
            if not group:
                return None
            
            running = 0
            stopped = 0
            
            for process_id in group.processes:
                info = self.processes.get(process_id)
                if info and info.status == ProcessStatus.RUNNING:
                    running += 1
                else:
                    stopped += 1
            
            return {
                "group_id": group.group_id,
                "name": group.name,
                "total_processes": len(group.processes),
                "running_processes": running,
                "stopped_processes": stopped,
                "max_parallel": group.max_parallel
            }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.stats_lock:
            return {
                "total_processes": self.stats["total_processes"],
                "running_processes": self.stats["running_processes"],
                "completed_processes": self.stats["completed_processes"],
                "failed_processes": self.stats["failed_processes"],
                "total_restarts": self.stats["total_restarts"],
                "peak_processes": self.stats["peak_processes"],
                "system_cpu_usage": self.stats["system_cpu_usage"],
                "system_memory_usage": self.stats["system_memory_usage"],
                "group_count": len(self.groups)
            }
    
    def shutdown(self, force: bool = False):
        """关闭进程管理器"""
        self.is_running = False
        self.status = "stopping"
        
        logger.info("正在停止所有进程...")
        
        for process_id in list(self.processes.keys()):
            self.stop_process(process_id, force)
        
        self.monitor_thread.join(timeout=5)
        
        self.status = "stopped"
        logger.info("进程管理器已关闭")
    
    def execute_command(self, command: str, args: List[str] = None, 
                       cwd: str = None, timeout: int = 30) -> Dict:
        """执行一次性命令"""
        if args is None:
            args = []
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [command] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": "命令超时",
                "duration": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "return_code": -2,
                "stdout": "",
                "stderr": str(e),
                "duration": time.time() - start_time
            }


def test_process_manager():
    """测试进程管理器"""
    print("进程管理器 V2.0 测试")
    print("=" * 60)
    
    pm = ProcessManager()
    
    print("创建测试进程...")
    config1 = ProcessConfig(
        name="测试进程1",
        command="python3",
        args=["-c", "import time; [print(f'Output {i}') or time.sleep(0.5) for i in range(5)]"],
        restart_policy=RestartPolicy.ON_FAILURE
    )
    
    config2 = ProcessConfig(
        name="测试进程2",
        command="python3",
        args=["-c", "print('Single output'); exit(0)"],
        auto_start=False
    )
    
    config3 = ProcessConfig(
        name="错误进程",
        command="python3",
        args=["-c", "raise ValueError('测试错误')"]
    )
    
    pid1 = pm.create_process(config1)
    pid2 = pm.create_process(config2)
    pid3 = pm.create_process(config3)
    
    print(f"已创建进程: {pid1}, {pid2}, {pid3}")
    
    print("\n等待进程执行 (3秒)...")
    time.sleep(3)
    
    print("\n进程状态:")
    for p in pm.list_processes():
        print(f"  {p['name']}: {p['status']}, PID: {p['pid']}")
    
    print("\n获取进程输出:")
    output = pm.get_process_output(pid1)
    print(f"  测试进程1 stdout: {len(output['stdout'])} 行")
    for line in output['stdout']:
        print(f"    {line}")
    
    print("\n创建进程组...")
    group_id = pm.create_group("测试组", max_parallel=5)
    pm.add_to_group(group_id, pid1)
    pm.add_to_group(group_id, pid2)
    
    print("\n进程组状态:")
    group_status = pm.get_group_status(group_id)
    print(f"  {group_status['name']}: {group_status['running_processes']}/{group_status['total_processes']} 运行中")
    
    print("\n启动进程2...")
    pm.start_process(pid2)
    time.sleep(1)
    
    print("\n统计信息:")
    stats = pm.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n执行一次性命令...")
    result = pm.execute_command("echo", ["Hello from Process Manager"])
    print(f"  命令执行结果: {'成功' if result['success'] else '失败'}")
    print(f"  输出: {result['stdout'].strip()}")
    
    print("\n停止所有进程...")
    pm.stop_process(pid1)
    pm.stop_process(pid2)
    
    print("\n关闭进程管理器...")
    pm.shutdown()
    
    print("\n进程管理器 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_process_manager()