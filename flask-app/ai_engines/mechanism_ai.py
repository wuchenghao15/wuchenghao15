# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机制AI - 用于管理系统锁定和超时机制
"""

import time
import threading
import queue
from app.utils.logging import logger
from app.models.logs import LogEntry
from app.models.user_snapshots import UserSnapshot
import logging


class MechanismAI:
    """机制AI: 负责管理系统锁定和超时机制"""

    def __init__(self):
        self.instance_id = f"mechanism_ai_{id(self)}"
        self.name = "机制AI"
        self.description = "负责管理系统锁定和超时机制"
        self.status = "active"
        self.logger = logger
        self.logger.info(f"初始化机制AI: {self.instance_id}")

        self.mechanism_config = {
            "enabled": True,
            "lock_timeout": 300,
            "session_timeout": 1800,
            "vikey_lock_timeout": 60,
            "max_concurrent_sessions": 10,
            "lock_strategy": "exclusive",
            "auto_unlock": True,
            "unlock_on_activity": True,
            "auxiliary_threads": {
                "enabled": True,
                "priority_offset": 1,
                "max_threads": 5,
                "thread_types": ["script", "version", "cache", "log", "action"]
            }
        }

        self.locks = {}
        self.sessions = {}
        self.vikey_sessions = {}
        self.auxiliary_threads = {}
        self.task_queue = queue.Queue()

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loops, daemon=True)
        self.monitor_thread.start()
        self.aux_thread_manager = threading.Thread(target=self._manage_auxiliary_threads, daemon=True)
        self.aux_thread_manager.start()
        self.task_processor = threading.Thread(target=self._process_tasks, daemon=True)
        self.task_processor.start()

    def _monitor_loops(self):
        """监控循环: 定期检查锁定和会话状态"""
        while self.running:
            try:
                self._check_locks()
                self._check_sessions()
                self._check_vikey_sessions()
                time.sleep(10)
            except Exception as e:
                self.logger.error(f"机制AI监控循环出错: {e}")

    def _check_locks(self):
        """检查锁定状态: 自动解锁超时锁定"""
        current_time = time.time()
        for lock_id, lock_data in list(self.locks.items()):
            if current_time - lock_data["created_at"] > self.mechanism_config["lock_timeout"]:
                self.unlock(lock_id, "timeout")

    def _check_sessions(self):
        """检查会话状态: 自动过期超时会话"""
        current_time = time.time()
        for session_id, session_data in list(self.sessions.items()):
            if current_time - session_data["last_activity"] > self.mechanism_config["session_timeout"]:
                self.expire_session(session_id)

    def _check_vikey_sessions(self):
        """检查Vikey会话状态: 自动处理异常情况"""
        current_time = time.time()
        for session_id, session_data in list(self.vikey_sessions.items()):
            if current_time - session_data["last_activity"] > self.mechanism_config["vikey_lock_timeout"]:
                self.handle_vikey_timeout(session_id)

    def lock(self, resource_id, lock_type="exclusive", user_id=None, metadata=None):
        """锁定资源"""
        lock_id = f"{resource_id}_{time.time()}"
        self.locks[lock_id] = {
            "lock_id": lock_id,
            "resource_id": resource_id,
            "lock_type": lock_type,
            "user_id": user_id,
            "created_at": time.time(),
            "last_updated": time.time(),
            "metadata": metadata or {}
        }

        self.logger.info(f"资源已锁定: {lock_id}, 资源ID: {resource_id}")
        return lock_id

    def unlock(self, lock_id, reason="user_request"):
        """解锁资源"""
        if lock_id in self.locks:
            lock_data = self.locks[lock_id]
            self.logger.info(f"资源已解锁: {lock_id}, 资源ID: {lock_data['resource_id']}, 原因: {reason}")
            del self.locks[lock_id]
            return True
        return False

    def extend_lock(self, lock_id, extension_time=60):
        """延长锁定时间"""
        if lock_id in self.locks:
            self.locks[lock_id]["last_updated"] = time.time()
            self.logger.info(f"锁定时间已延长: {lock_id}")
            return True
        return False

    def get_lock_status(self, resource_id):
        """获取资源锁定状态"""
        locks = [lock for lock in self.locks.values() if lock["resource_id"] == resource_id]
        return {"resource_id": resource_id, "locks": locks, "is_locked": len(locks) > 0}

    def create_session(self, session_id, user_id, metadata=None):
        """创建会话"""
        self.sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "metadata": metadata or {}
        }

        self.logger.info(f"会话已创建: {session_id}, 用户ID: {user_id}")
        return session_id

    def expire_session(self, session_id):
        """过期会话"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            self.logger.info(f"会话已过期: {session_id}, 用户ID: {session_data['user_id']}")
            del self.sessions[session_id]
            return True
        return False

    def get_session_status(self, session_id):
        """获取会话状态"""
        return self.sessions.get(session_id)

    def create_vikey_session(self, session_id, user_id, vikey_info, metadata=None):
        """创建Vikey会话"""
        self.vikey_sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "vikey_info": vikey_info,
            "created_at": time.time(),
            "last_activity": time.time(),
            "metadata": metadata or {}
        }

        self.logger.info(f"Vikey会话已创建: {session_id}, 用户ID: {user_id}")
        return session_id

    def handle_vikey_removal(self, session_id, vikey_info):
        """处理Vikey硬件拔出"""
        if session_id in self.vikey_sessions:
            vikey_data = self.vikey_sessions[session_id]
            user_id = vikey_data.get('user_id')
            hardware_id = vikey_info.get('hardwareId')

            self.logger.warning(f"Vikey硬件已拔出: {session_id}, 用户ID: {user_id}, 硬件ID: {hardware_id}")

            try:
                self._clear_user_traces(user_id, session_id)

                log_data = {
                    'user_id': user_id,
                    'vikey_hardware_id': hardware_id,
                    'timestamp': time.time(),
                    'details': {
                        'action': 'auto_clear_traces',
                        'status': 'success'
                    }
                }
                self.logger.info(f"Vikey移除日志已记录: {log_data}")

                self._force_exit_user(user_id, session_id, "vikey_removed")

                self._notify_ai_instances('vikey_removed', {
                    'session_id': session_id,
                    'vikey_info': vikey_info
                })

            except Exception as e:
                self.logger.error(f"处理Vikey硬件拔出时出错: {e}")
            finally:
                del self.vikey_sessions[session_id]

            return True
        return False

    def handle_vikey_timeout(self, session_id):
        """处理Vikey会话超时"""
        if session_id in self.vikey_sessions:
            vikey_data = self.vikey_sessions[session_id]
            self.logger.warning(f"Vikey会话超时: {session_id}")
            del self.vikey_sessions[session_id]
            return True
        return False

    def _clear_user_traces(self, user_id, session_id):
        """清除用户痕迹"""
        self.logger.info(f"清除用户痕迹: 用户ID: {user_id}, 会话ID: {session_id}")

    def _force_exit_user(self, user_id, session_id, reason):
        """强制退出用户"""
        self.logger.info(f"强制退出用户: 用户ID: {user_id}, 会话ID: {session_id}, 原因: {reason}")

        if session_id in self.sessions:
            self.sessions[session_id].update({
                'status': 'force_exited',
                'exit_time': time.time()
            })

        if session_id in self.vikey_sessions:
            del self.vikey_sessions[session_id]

    def _notify_ai_instances(self, event_type, event_data):
        """通知相关AI实例"""
        self.logger.info(f"通知AI实例: 事件类型: {event_type}, 数据: {event_data}")

    def _take_user_snapshot(self, user_id, session_id):
        """拍摄用户快照"""
        snapshot_data = {
            'user_id': user_id,
            'timestamp': time.time(),
            'snapshot_type': 'pre_vikey_switch',
            'data': {
                'current_page': 'dashboard',
                'session_state': self.sessions.get(session_id, {}),
                'active_tasks': []
            }
        }

        try:
            snapshot = UserSnapshot.create(**snapshot_data)
            return snapshot.snapshot_id
        except Exception as e:
            self.logger.error(f"拍摄用户快照失败: {e}")
            return None

    def _verify_vikey_user(self, vikey_info):
        """验证Vikey硬件用户信息"""
        return {"verified": True, "user_id": "vikey_user"}

    def _switch_to_vikey_user(self, current_user_id, vikey_user_info, session_id, snapshot_id):
        """切换到Vikey用户状态"""
        self.logger.info(f"切换到Vikey用户: 当前用户ID: {current_user_id}, Vikey用户ID: {vikey_user_info.get('user_id')}, 会话ID: {session_id}")

        if session_id in self.sessions:
            self.sessions[session_id].update({
                'original_user_id': current_user_id,
                'current_user_id': vikey_user_info.get('user_id'),
                'snapshot_id': snapshot_id,
                'status': 'switched_to_vikey',
                'last_activity': time.time()
            })

        self.create_vikey_session(
            session_id=session_id,
            user_id=vikey_user_info.get('user_id'),
            vikey_info={
                'hardwareId': vikey_user_info.get('vikey_hardware_id'),
                'user_info': vikey_user_info
            },
            metadata={
                'original_user_id': current_user_id,
            }
        )

    def _manage_auxiliary_threads(self):
        """管理辅助AI线程"""
        while self.running:
            try:
                if self.mechanism_config['auxiliary_threads']['enabled']:
                    current_threads = len(self.auxiliary_threads)
                    max_threads = self.mechanism_config['auxiliary_threads']['max_threads']

                    if current_threads < max_threads:
                        for thread_type in self.mechanism_config['auxiliary_threads']['thread_types']:
                            if thread_type not in self.auxiliary_threads:
                                self._start_auxiliary_thread(thread_type)

                time.sleep(60)
            except Exception as e:
                self.logger.error(f"管理辅助线程时出错: {e}")

    def _start_auxiliary_thread(self, thread_type):
        """启动辅助AI线程"""
        thread = threading.Thread(
            target=self._auxiliary_thread_worker,
            args=(thread_type,),
            daemon=True,
            name=f"aux_{thread_type}_thread"
        )

        thread.start()

        self.auxiliary_threads[thread_type] = {
            'thread': thread,
            'type': thread_type,
            'status': 'running',
            'last_activity': time.time()
        }

        self.logger.info(f"辅助AI线程已启动: {thread_type}")

    def _auxiliary_thread_worker(self, thread_type):
        """辅助线程工作函数"""
        self.logger.info(f"辅助AI线程开始工作: 类型: {thread_type}")

        try:
            while self.running:
                if thread_type == 'script':
                    self._execute_script_ai_tasks()
                elif thread_type == 'version':
                    self._execute_version_ai_tasks()
                elif thread_type == 'cache':
                    self._execute_cache_ai_tasks()
                elif thread_type == 'log':
                    self._execute_log_ai_tasks()
                elif thread_type == 'action':
                    self._execute_action_ai_tasks()

                if thread_type in self.auxiliary_threads:
                    self.auxiliary_threads[thread_type]['last_activity'] = time.time()

                time.sleep(30)
        except Exception as e:
            self.logger.error(f"辅助AI线程出错: {thread_type}, 错误: {e}")
            if thread_type in self.auxiliary_threads:
                self.auxiliary_threads[thread_type]['status'] = 'failed'

    def _execute_script_ai_tasks(self):
        """执行脚本AI任务"""
        pass

    def _execute_version_ai_tasks(self):
        """执行版本AI任务"""
        pass

    def _execute_cache_ai_tasks(self):
        """执行缓存AI任务"""
        pass

    def _execute_log_ai_tasks(self):
        """执行日志AI任务"""
        pass

    def _execute_action_ai_tasks(self):
        """执行动作记录AI任务"""
        pass

    def _process_tasks(self):
        """处理任务队列中的任务"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=5)
                self._execute_task(task)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"处理任务时出错: {e}")

    def _execute_task(self, task):
        """执行具体任务"""
        self.logger.info(f"执行任务: {task}")

    def get_vikey_session_status(self, session_id):
        """获取Vikey会话状态"""
        return self.vikey_sessions.get(session_id)

    def get_stats(self):
        """获取统计信息"""
        return {
            "active_locks": len(self.locks),
            "active_sessions": len(self.sessions),
            "active_vikey_sessions": len(self.vikey_sessions),
            "active_auxiliary_threads": len(self.auxiliary_threads)
        }

    def update_config(self, new_config):
        """更新配置"""
        self.mechanism_config.update(new_config)
        self.logger.info(f"机制AI配置已更新: {new_config}")
        return True

    def stop(self):
        """停止机制AI"""
        self.running = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join()
        self.logger.info(f"机制AI已停止: {self.instance_id}")


mechanism_ai = MechanismAI()
