#!/usr/bin/env python3
"""
后台自动挂载服务 (Background Auto-Mount Service)
==============================================
统一管理：任务调度、进程管理、事件Hook、AI Agent自动加载
支持应用启动时自动挂载、运行时动态管理、持久化状态
"""
import os
import sys
import json
import sqlite3
import logging
import threading
import time
import importlib
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger('AutoMountService')

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(_PROJECT_ROOT, 'app.db')


class BackgroundTask:
    """后台任务封装"""

    def __init__(self, task_id: str, func: Callable, name: str = '',
                 interval_seconds: float = 60, priority: int = 5,
                 max_retries: int = 3, timeout: float = 300):
        self.task_id = task_id
        self.name = name or task_id
        self.func = func
        self.interval = interval_seconds
        self.priority = priority
        self.max_retries = max_retries
        self.timeout = timeout
        self.is_running = False
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.error_count = 0
        self.last_error = None
        self._stop_event = threading.Event()

    def execute(self) -> Dict[str, Any]:
        """执行任务"""
        self.is_running = True
        self.last_run = datetime.now().isoformat()
        self.run_count += 1

        deadline = time.time() + self.timeout

        def target():
            try:
                self.func()
                self.error_count = 0
                self.last_error = None
            except Exception as e:
                self.error_count += 1
                self.last_error = str(e)
                logger.error(f"[Task:{self.task_id}] 执行失败: {e}")

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            logger.warning(f"[Task:{self.task_id}] 超时 ({self.timeout}s)")

        self.is_running = False
        self.next_run = time.time() + self.interval
        return {
            'task_id': self.task_id,
            'status': 'completed' if self.last_error is None else 'failed',
            'last_run': self.last_run,
            'error': self.last_error
        }

    def stop(self):
        """停止任务"""
        self._stop_event.set()
        self.is_running = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'interval': self.interval,
            'priority': self.priority,
            'is_running': self.is_running,
            'last_run': self.last_run,
            'next_run': self.next_run,
            'run_count': self.run_count,
            'error_count': self.error_count,
            'last_error': self.last_error
        }


class ProcessManager:
    """进程/线程管理器"""

    def __init__(self):
        self._processes: Dict[str, threading.Thread] = {}
        self._process_info: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def start_process(self, pid: str, target: Callable, name: str = '',
                      daemon: bool = True, args: tuple = ()) -> Dict[str, Any]:
        """启动一个后台进程/线程"""
        with self._lock:
            if pid in self._processes and self._processes[pid].is_alive():
                return {'success': False, 'error': f'进程 {pid} 已在运行'}

            thread = threading.Thread(target=target, name=name or pid,
                                      daemon=daemon, args=args)
            thread.start()
            self._processes[pid] = thread
            self._process_info[pid] = {
                'pid': pid,
                'name': name or pid,
                'started_at': datetime.now().isoformat(),
                'daemon': daemon,
                'alive': thread.is_alive(),
                'thread_id': thread.ident
            }
            logger.info(f"[ProcessManager] 启动进程 {pid}")
            return {'success': True, 'pid': pid}

    def stop_process(self, pid: str) -> Dict[str, Any]:
        """停止进程"""
        with self._lock:
            if pid not in self._processes:
                return {'success': False, 'error': f'进程 {pid} 不存在'}
            thread = self._processes[pid]
            if thread.is_alive():
                thread.join(timeout=5)
            del self._processes[pid]
            info = self._process_info.pop(pid, {})
            logger.info(f"[ProcessManager] 停止进程 {pid}")
            return {'success': True, 'pid': pid}

    def list_processes(self) -> List[Dict]:
        """列出所有进程"""
        with self._lock:
            result = []
            for pid, info in self._process_info.items():
                thread = self._processes.get(pid)
                info['alive'] = thread.is_alive() if thread else False
                result.append(info)
            return result

    def get_process(self, pid: str) -> Optional[Dict]:
        """获取单个进程信息"""
        with self._lock:
            info = self._process_info.get(pid)
            if info:
                thread = self._processes.get(pid)
                info['alive'] = thread.is_alive() if thread else False
                return info
            return None


class EventHookSystem:
    """事件Hook系统 - 发布/订阅模式"""

    def __init__(self):
        self._listeners: Dict[str, List[Dict[str, Any]]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 1000
        self._lock = threading.Lock()

    def subscribe(self, event: str, handler: Callable,
                  priority: int = 10, once: bool = False) -> str:
        """订阅事件"""
        import uuid
        sub_id = f"sub_{uuid.uuid4().hex[:12]}"
        with self._lock:
            if event not in self._listeners:
                self._listeners[event] = []
            self._listeners[event].append({
                'id': sub_id,
                'handler': handler,
                'priority': priority,
                'once': once,
                'created_at': datetime.now().isoformat()
            })
            self._listeners[event].sort(key=lambda x: x['priority'])
        logger.info(f"[HookSystem] 订阅事件 '{event}' (sub_id={sub_id}, 优先级={priority})")
        return sub_id

    def unsubscribe(self, event: str, sub_id: str) -> bool:
        """取消订阅"""
        with self._lock:
            if event in self._listeners:
                before = len(self._listeners[event])
                self._listeners[event] = [
                    s for s in self._listeners[event] if s['id'] != sub_id
                ]
                return len(self._listeners[event]) < before
        return False

    def emit(self, event: str, **kwargs) -> List[Dict[str, Any]]:
        """发射事件"""
        results = []
        self._record_event(event, kwargs)

        with self._lock:
            listeners = list(self._listeners.get(event, []))

        for listener in listeners:
            try:
                result = listener['handler'](**kwargs)
                results.append({
                    'sub_id': listener['id'],
                    'success': True,
                    'result': result
                })
                if listener.get('once'):
                    self.unsubscribe(event, listener['id'])
            except Exception as e:
                results.append({
                    'sub_id': listener['id'],
                    'success': False,
                    'error': str(e)
                })
                logger.error(f"[HookSystem] 事件 '{event}' 处理器 {listener['id']} 失败: {e}")

        return results

    def _record_event(self, event: str, data: Dict):
        """记录事件历史"""
        self._event_history.append({
            'event': event,
            'data': {k: str(v)[:100] for k, v in data.items()},
            'timestamp': datetime.now().isoformat(),
            'listener_count': len(self._listeners.get(event, []))
        })
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    def get_event_history(self, event: str = '', limit: int = 50) -> List[Dict]:
        """获取事件历史"""
        result = self._event_history
        if event:
            result = [e for e in result if e['event'] == event]
        return result[-limit:]

    def list_events(self) -> Dict[str, int]:
        """列出所有事件类型及其订阅数"""
        return {event: len(subs) for event, subs in self._listeners.items() if subs}

    def clear(self):
        """清除所有Hook"""
        with self._lock:
            self._listeners.clear()
            self._event_history.clear()


class AIAgentLoader:
    """AI Agent自动加载器"""

    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._agent_meta: Dict[str, Dict] = {}
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS ai_agent_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT UNIQUE,
                        agent_name TEXT NOT NULL,
                        module_path TEXT,
                        class_name TEXT,
                        agent_type TEXT DEFAULT 'employee',
                        is_auto_load INTEGER DEFAULT 1,
                        load_order INTEGER DEFAULT 100,
                        status TEXT DEFAULT 'registered',
                        capabilities TEXT,
                        config TEXT,
                        created_at TEXT,
                        last_loaded_at TEXT,
                        load_count INTEGER DEFAULT 0
                    )
                ''')
                conn.execute("CREATE INDEX IF NOT EXISTS idx_aar_type ON ai_agent_registry(agent_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_aar_autoload ON ai_agent_registry(is_auto_load)")
                conn.commit()
        except Exception as e:
            logger.error(f"[AIAgentLoader] 初始化数据库失败: {e}")

    def register_agent(self, agent_id: str, agent_name: str,
                        module_path: str, class_name: str,
                        agent_type: str = 'employee',
                        auto_load: bool = True,
                        load_order: int = 100,
                        capabilities: List[str] = None,
                        config: Dict = None) -> Dict[str, Any]:
        """注册AI Agent"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO ai_agent_registry
                    (agent_id, agent_name, module_path, class_name, agent_type,
                     is_auto_load, load_order, status, capabilities, config, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'registered', ?, ?, ?)
                ''', (
                    agent_id, agent_name, module_path, class_name,
                    agent_type, 1 if auto_load else 0, load_order,
                    json.dumps(capabilities or [], ensure_ascii=False),
                    json.dumps(config or {}, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()

            self._agent_meta[agent_id] = {
                'agent_id': agent_id,
                'agent_name': agent_name,
                'module_path': module_path,
                'class_name': class_name,
                'agent_type': agent_type,
                'auto_load': auto_load,
                'load_order': load_order,
                'capabilities': capabilities or [],
                'config': config or {}
            }

            logger.info(f"[AIAgentLoader] 注册Agent: {agent_id} ({agent_name})")
            return {'success': True, 'agent_id': agent_id}
        except Exception as e:
            logger.error(f"[AIAgentLoader] 注册Agent失败: {e}")
            return {'success': False, 'error': str(e)}

    def load_agent(self, agent_id: str) -> Dict[str, Any]:
        """加载并实例化AI Agent"""
        meta = self._agent_meta.get(agent_id)
        if not meta:
            # 从数据库加载
            meta = self._load_meta_from_db(agent_id)
        if not meta:
            return {'success': False, 'error': f'Agent {agent_id} 未注册'}

        try:
            module = importlib.import_module(meta['module_path'])
            cls = getattr(module, meta['class_name'])
            agent_instance = cls()

            self._agents[agent_id] = agent_instance
            self._agent_meta[agent_id]['status'] = 'loaded'

            # 更新数据库
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    UPDATE ai_agent_registry
                    SET status = 'loaded', last_loaded_at = ?, load_count = load_count + 1
                    WHERE agent_id = ?
                ''', (datetime.now().isoformat(), agent_id))
                conn.commit()

            logger.info(f"[AIAgentLoader] 加载Agent成功: {agent_id}")
            return {'success': True, 'agent_id': agent_id}
        except Exception as e:
            logger.error(f"[AIAgentLoader] 加载Agent失败 {agent_id}: {e}")
            return {'success': False, 'error': str(e)}

    def _load_meta_from_db(self, agent_id: str) -> Optional[Dict]:
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ai_agent_registry WHERE agent_id = ?", (agent_id,))
                row = cursor.fetchone()
                if row:
                    meta = dict(row)
                    meta['capabilities'] = json.loads(meta.get('capabilities') or '[]')
                    meta['config'] = json.loads(meta.get('config') or '{}')
                    self._agent_meta[agent_id] = meta
                    return meta
        except Exception:
            pass
        return None

    def auto_load_all(self) -> Dict[str, Any]:
        """自动加载所有标记为 auto_load 的Agent"""
        results = {'loaded': [], 'failed': []}
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT agent_id FROM ai_agent_registry
                    WHERE is_auto_load = 1
                    ORDER BY load_order ASC
                ''')
                agent_ids = [row['agent_id'] for row in cursor.fetchall()]

            for agent_id in agent_ids:
                result = self.load_agent(agent_id)
                if result.get('success'):
                    results['loaded'].append(agent_id)
                else:
                    results['failed'].append({'agent_id': agent_id, 'error': result.get('error')})

        except Exception as e:
            logger.error(f"[AIAgentLoader] 自动加载失败: {e}")

        logger.info(f"[AIAgentLoader] 自动加载完成: {len(results['loaded'])}成功, {len(results['failed'])}失败")
        return results

    def get_agent(self, agent_id: str) -> Optional[Any]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """列出所有注册的Agent"""
        agents = []
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ai_agent_registry ORDER BY load_order")
                for row in cursor.fetchall():
                    a = dict(row)
                    a['capabilities'] = json.loads(a.get('capabilities') or '[]')
                    agents.append(a)
        except Exception:
            pass
        return agents


class BackgroundAutoMountService:
    """后台自动挂载服务 - 统一入口"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tasks: Dict[str, BackgroundTask] = {}
        self._process_mgr = ProcessManager()
        self._hook_system = EventHookSystem()
        self._agent_loader = AIAgentLoader()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._mounted = False
        self._init_db()
        self._register_default_hooks()
        logger.info("[AutoMountService] 初始化完成")

    def _init_db(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS background_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT UNIQUE,
                        name TEXT,
                        module_path TEXT,
                        func_name TEXT,
                        interval_seconds REAL DEFAULT 60,
                        priority INTEGER DEFAULT 5,
                        is_active INTEGER DEFAULT 1,
                        last_run TEXT,
                        next_run TEXT,
                        run_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        config TEXT,
                        created_at TEXT
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_events_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT,
                        event_data TEXT,
                        source TEXT,
                        handled_by TEXT,
                        result TEXT,
                        created_at TEXT
                    )
                ''')
                conn.execute("CREATE INDEX IF NOT EXISTS idx_bt_status ON background_tasks(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sel_type ON system_events_log(event_type)")
                conn.commit()
        except Exception as e:
            logger.error(f"[AutoMountService] 初始化数据库失败: {e}")

    def _register_default_hooks(self):
        """注册默认事件Hook"""
        # 系统事件
        self._hook_system.subscribe('system.startup', self._on_system_startup, priority=1)
        self._hook_system.subscribe('system.shutdown', self._on_system_shutdown, priority=1)
        self._hook_system.subscribe('user.login', self._on_user_login, priority=5)
        self._hook_system.subscribe('user.logout', self._on_user_logout, priority=5)
        self._hook_system.subscribe('error.occurred', self._on_error, priority=10)
        self._hook_system.subscribe('task.completed', self._on_task_completed, priority=5)
        self._hook_system.subscribe('task.failed', self._on_task_failed, priority=5)
        logger.info("[AutoMountService] 默认Hook注册完成")

    # ============ 启动/停止 ============

    def mount_all(self) -> Dict[str, Any]:
        """挂载所有后台组件"""
        if self._mounted:
            return {'success': True, 'message': '已挂载'}

        results = {
            'tasks': [],
            'processes': [],
            'agents': [],
            'hooks': []
        }

        # 1. 加载持久化任务
        tasks = self._load_tasks_from_db()
        for task_data in tasks:
            ok = self._mount_task(task_data)
            results['tasks'].append({'id': task_data['task_id'], 'mounted': ok})

        # 2. 启动调度线程
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name='AutoMountScheduler',
            daemon=True
        )
        self._scheduler_thread.start()
        results['processes'].append({'pid': 'scheduler', 'started': True})

        # 3. 自动加载AI Agent
        agent_result = self._agent_loader.auto_load_all()
        results['agents'] = agent_result

        # 4. 触发启动事件
        self._hook_system.emit('system.startup',
                               mounted_tasks=len(self._tasks),
                               mounted_agents=len(self._agent_loader._agents))

        self._mounted = True
        logger.info(f"[AutoMountService] 挂载完成: {len(self._tasks)}任务, "
                   f"{len(self._agent_loader._agents)}Agent")
        return {'success': True, 'results': results}

    def unmount_all(self):
        """卸载所有后台组件"""
        self._stop_event.set()
        for task_id, task in list(self._tasks.items()):
            task.stop()
        self._tasks.clear()
        self._process_mgr.stop_process('scheduler')
        self._mounted = False
        self._hook_system.emit('system.shutdown')
        logger.info("[AutoMountService] 全部卸载完成")

    def is_mounted(self) -> bool:
        return self._mounted

    # ============ 任务管理 ============

    def register_task(self, task_id: str, module_path: str, func_name: str,
                       name: str = '', interval: float = 60,
                       priority: int = 5, config: Dict = None) -> Dict[str, Any]:
        """注册一个后台任务"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO background_tasks
                    (task_id, name, module_path, func_name, interval_seconds,
                     priority, is_active, status, config, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, 'registered', ?, ?)
                ''', (
                    task_id, name or task_id, module_path, func_name,
                    interval, priority,
                    json.dumps(config or {}, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()

            task_data = {
                'task_id': task_id,
                'name': name or task_id,
                'module_path': module_path,
                'func_name': func_name,
                'interval': interval,
                'priority': priority,
                'config': config or {}
            }

            if self._mounted:
                self._mount_task(task_data)

            logger.info(f"[AutoMountService] 注册任务: {task_id}")
            return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f"[AutoMountService] 注册任务失败: {e}")
            return {'success': False, 'error': str(e)}

    def _mount_task(self, task_data: Dict) -> bool:
        """挂载单个任务"""
        try:
            module = importlib.import_module(task_data['module_path'])
            func = getattr(module, task_data['func_name'])

            task = BackgroundTask(
                task_id=task_data['task_id'],
                func=func,
                name=task_data.get('name', task_data['task_id']),
                interval_seconds=task_data.get('interval', 60),
                priority=task_data.get('priority', 5)
            )
            self._tasks[task_data['task_id']] = task
            logger.info(f"[AutoMountService] 挂载任务: {task_data['task_id']}")
            return True
        except Exception as e:
            logger.error(f"[AutoMountService] 挂载任务失败 {task_data['task_id']}: {e}")
            return False

    def _load_tasks_from_db(self) -> List[Dict]:
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM background_tasks WHERE is_active = 1")
                tasks = []
                for row in cursor.fetchall():
                    t = dict(row)
                    t['config'] = json.loads(t.get('config') or '{}')
                    tasks.append(t)
                return tasks
        except Exception:
            return []

    def list_tasks(self) -> List[Dict]:
        result = []
        for tid, task in self._tasks.items():
            result.append(task.to_dict())
        # 也加入数据库中未挂载的
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT task_id FROM background_tasks WHERE is_active = 0")
                for row in cursor.fetchall():
                    result.append({'task_id': row[0], 'status': 'inactive'})
        except Exception:
            pass
        return result

    def run_task_now(self, task_id: str) -> Dict[str, Any]:
        """立即运行指定任务"""
        task = self._tasks.get(task_id)
        if task:
            return task.execute()
        return {'success': False, 'error': f'任务 {task_id} 未挂载'}

    # ============ Agent管理 ============

    def register_and_load_agent(self, agent_id: str, agent_name: str,
                                  module_path: str, class_name: str,
                                  agent_type: str = 'employee',
                                  auto_load: bool = True) -> Dict[str, Any]:
        """注册并加载AI Agent"""
        reg_result = self._agent_loader.register_agent(
            agent_id, agent_name, module_path, class_name,
            agent_type=agent_type, auto_load=auto_load
        )
        if reg_result.get('success') and self._mounted:
            load_result = self._agent_loader.load_agent(agent_id)
            reg_result['load'] = load_result
        return reg_result

    def list_agents(self) -> List[Dict]:
        return self._agent_loader.list_agents()

    def get_agent(self, agent_id: str):
        return self._agent_loader.get_agent(agent_id)

    # ============ Hook管理 ============

    def subscribe_event(self, event: str, handler: Callable,
                        priority: int = 10) -> str:
        return self._hook_system.subscribe(event, handler, priority)

    def emit_event(self, event: str, **kwargs) -> List[Dict]:
        results = self._hook_system.emit(event, **kwargs)
        # 记录事件
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT INTO system_events_log
                    (event_type, event_data, source, handled_by, result, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    event,
                    json.dumps({k: str(v)[:200] for k, v in kwargs.items()}, ensure_ascii=False),
                    'auto_mount_service',
                    ','.join(r['sub_id'] for r in results if r.get('success')) or 'none',
                    json.dumps(results, ensure_ascii=False)[:500],
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass
        return results

    def list_events(self) -> Dict[str, int]:
        return self._hook_system.list_events()

    def get_event_history(self, event: str = '', limit: int = 50) -> List[Dict]:
        return self._hook_system.get_event_history(event, limit)

    # ============ 进程管理 ============

    def start_background_process(self, pid: str, target: Callable,
                                  name: str = '', args: tuple = ()) -> Dict:
        return self._process_mgr.start_process(pid, target, name, args=args)

    def stop_background_process(self, pid: str) -> Dict:
        return self._process_mgr.stop_process(pid)

    def list_background_processes(self) -> List[Dict]:
        return self._process_mgr.list_processes()

    # ============ 内部方法 ============

    def _scheduler_loop(self):
        """调度主循环"""
        logger.info("[AutoMountService] 调度循环启动")
        while not self._stop_event.is_set():
            now = time.time()
            for task_id, task in list(self._tasks.items()):
                if task.is_running:
                    continue
                if task.next_run is None or now >= task.next_run:
                    task.execute()
            time.sleep(1)

    def _on_system_startup(self, **kwargs):
        logger.info("[AutoMountService] 系统启动事件触发")

    def _on_system_shutdown(self, **kwargs):
        logger.info("[AutoMountService] 系统关闭事件触发")

    def _on_user_login(self, **kwargs):
        logger.info(f"[AutoMountService] 用户登录: {kwargs.get('user_id', 'unknown')}")

    def _on_user_logout(self, **kwargs):
        logger.info(f"[AutoMountService] 用户登出: {kwargs.get('user_id', 'unknown')}")

    def _on_error(self, **kwargs):
        logger.error(f"[AutoMountService] 错误事件: {kwargs.get('error', 'unknown')}")

    def _on_task_completed(self, **kwargs):
        logger.info(f"[AutoMountService] 任务完成: {kwargs.get('task_id', 'unknown')}")

    def _on_task_failed(self, **kwargs):
        logger.warning(f"[AutoMountService] 任务失败: {kwargs.get('task_id', 'unknown')}")

    def get_state(self) -> Dict[str, Any]:
        """获取服务状态总览 (别名)"""
        status = self.get_status()
        # 添加 hooks 字段方便上层调用
        try:
            events = self._hook_system.list_events()
            status['hooks'] = {'events': events}
        except Exception:
            status['hooks'] = {'events': {}}
        try:
            procs = self._process_mgr.list_processes()
            status['processes'] = {p.get('pid', i): p for i, p in enumerate(procs)}
        except Exception:
            status['processes'] = {}
        return status

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态总览"""
        return {
            'mounted': self._mounted,
            'tasks': {
                'total': len(self._tasks),
                'running': sum(1 for t in self._tasks.values() if t.is_running),
                'ids': list(self._tasks.keys())
            },
            'processes': self._process_mgr.list_processes(),
            'agents': {
                'total': len(self._agent_loader._agent_meta),
                'loaded': len(self._agent_loader._agents)
            },
            'events': {
                'types': self._hook_system.list_events(),
                'history_count': len(self._hook_system._event_history)
            },
            'uptime_since': getattr(self, '_mount_time', None)
        }


# 全局单例
auto_mount_service = BackgroundAutoMountService()
