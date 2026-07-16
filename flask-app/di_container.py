#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS依赖注入容器
统一管理50+服务模块的依赖关系和生命周期
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Type, TypeVar

logger = print

T = TypeVar('T')


class ServiceDescriptor:
    """服务描述符"""

    def __init__(self, service_id: str, service_type: str,
                 factory: Callable = None, instance: Any = None,
                 dependencies: List[str] = None,
                 lifecycle: str = 'singleton',
                 is_started: bool = False):
        self.service_id = service_id
        self.service_type = service_type
        self.factory = factory
        self.instance = instance
        self.dependencies = dependencies or []
        self.lifecycle = lifecycle  # singleton, transient, scoped
        self.is_started = is_started
        self.created_at = datetime.now().isoformat()
        self.start_order = 0
        self.stop_order = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_id': self.service_id,
            'service_type': self.service_type,
            'dependencies': self.dependencies,
            'lifecycle': self.lifecycle,
            'is_started': self.is_started,
            'created_at': self.created_at,
            'start_order': self.start_order,
            'stop_order': self.stop_order,
            'has_instance': self.instance is not None
        }


class DIContainer:
    """依赖注入容器"""

    def __init__(self):
        self.services: Dict[str, ServiceDescriptor] = {}
        self.instances: Dict[str, Any] = {}
        self.is_running = False
        self.lock = threading.RLock()
        self._start_counter = 0
        self._stop_counter = 0

        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS di_services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_id TEXT NOT NULL UNIQUE,
                    service_type TEXT NOT NULL,
                    dependencies TEXT,
                    lifecycle TEXT DEFAULT 'singleton',
                    start_order INTEGER DEFAULT 0,
                    stop_order INTEGER DEFAULT 0,
                    is_started INTEGER DEFAULT 0,
                    registered_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_di_services_id ON di_services(service_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[DI容器] 初始化数据库失败: {e}")

    def register(self, service_id: str, service_type: str = '',
                 factory: Callable = None, instance: Any = None,
                 dependencies: List[str] = None,
                 lifecycle: str = 'singleton') -> str:
        """注册服务"""
        with self.lock:
            if service_id in self.services:
                logger(f"[DI容器] 服务已存在,更新: {service_id}")

            descriptor = ServiceDescriptor(
                service_id=service_id,
                service_type=service_type or service_id,
                factory=factory,
                instance=instance,
                dependencies=dependencies or [],
                lifecycle=lifecycle
            )

            self.services[service_id] = descriptor

            if instance is not None:
                self.instances[service_id] = instance

        self._save_to_db(descriptor)
        logger(f"[DI容器] 注册服务: {service_id}")
        return service_id

    def register_instance(self, service_id: str, instance: Any,
                          dependencies: List[str] = None) -> str:
        """注册单例实例"""
        return self.register(
            service_id=service_id,
            service_type=type(instance).__name__,
            instance=instance,
            dependencies=dependencies,
            lifecycle='singleton'
        )

    def _save_to_db(self, descriptor: ServiceDescriptor):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO di_services
                (service_id, service_type, dependencies, lifecycle,
                 start_order, stop_order, is_started)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                descriptor.service_id, descriptor.service_type,
                json.dumps(descriptor.dependencies),
                descriptor.lifecycle,
                descriptor.start_order, descriptor.stop_order,
                1 if descriptor.is_started else 0
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[DI容器] 保存服务失败: {e}")

    def resolve(self, service_id: str) -> Optional[Any]:
        """解析服务"""
        with self.lock:
            descriptor = self.services.get(service_id)
            if not descriptor:
                logger(f"[DI容器] 服务未注册: {service_id}")
                return None

            if descriptor.lifecycle == 'singleton':
                if service_id in self.instances:
                    return self.instances[service_id]

                if descriptor.factory:
                    deps = {}
                    for dep_id in descriptor.dependencies:
                        dep = self.resolve(dep_id)
                        if dep is not None:
                            deps[dep_id] = dep

                    try:
                        instance = descriptor.factory(**deps)
                    except TypeError:
                        instance = descriptor.factory()

                    self.instances[service_id] = instance
                    descriptor.instance = instance
                    return instance

                return descriptor.instance

            elif descriptor.lifecycle == 'transient':
                if descriptor.factory:
                    try:
                        return descriptor.factory()
                    except:
                        return None
                return None

            return descriptor.instance

    def resolve_type(self, service_type: Type[T]) -> Optional[T]:
        """按类型解析服务"""
        with self.lock:
            for sid, descriptor in self.services.items():
                if descriptor.service_type == service_type.__name__:
                    return self.resolve(sid)
        return None

    def is_registered(self, service_id: str) -> bool:
        return service_id in self.services

    def get_dependencies(self, service_id: str) -> List[str]:
        descriptor = self.services.get(service_id)
        if descriptor:
            return descriptor.dependencies
        return []

    def get_dependents(self, service_id: str) -> List[str]:
        """获取依赖此服务的所有服务"""
        dependents = []
        for sid, descriptor in self.services.items():
            if service_id in descriptor.dependencies:
                dependents.append(sid)
        return dependents

    def _topological_sort(self) -> List[str]:
        """拓扑排序（按依赖关系排序）"""
        visited = set()
        temp_visited = set()
        result = []

        def visit(sid: str):
            if sid in visited:
                return
            if sid in temp_visited:
                logger(f"[DI容器] 检测到循环依赖: {sid}")
                return

            temp_visited.add(sid)

            descriptor = self.services.get(sid)
            if descriptor:
                for dep in descriptor.dependencies:
                    if dep in self.services:
                        visit(dep)

            temp_visited.discard(sid)
            visited.add(sid)
            result.append(sid)

        for sid in self.services:
            visit(sid)

        return result

    def start_all(self) -> Dict[str, bool]:
        """按依赖顺序启动所有服务"""
        results = {}
        order = self._topological_sort()

        with self.lock:
            self._start_counter = 0

            for sid in order:
                descriptor = self.services.get(sid)
                if not descriptor:
                    continue

                instance = self.resolve(sid)

                if instance and hasattr(instance, 'start') and not descriptor.is_started:
                    try:
                        instance.start()
                        descriptor.is_started = True
                        descriptor.start_order = self._start_counter
                        self._start_counter += 1
                        self._save_to_db(descriptor)
                        results[sid] = True
                        logger(f"[DI容器] 启动服务 ({descriptor.start_order}): {sid}")
                    except Exception as e:
                        results[sid] = False
                        logger(f"[DI容器] 启动失败 {sid}: {e}")
                else:
                    results[sid] = True

        self.is_running = True
        return results

    def stop_all(self) -> Dict[str, bool]:
        """按依赖逆序停止所有服务"""
        results = {}
        order = self._topological_sort()
        order.reverse()

        with self.lock:
            self._stop_counter = 0

            for sid in order:
                descriptor = self.services.get(sid)
                if not descriptor or not descriptor.is_started:
                    continue

                instance = self.instances.get(sid) or descriptor.instance

                if instance and hasattr(instance, 'stop'):
                    try:
                        instance.stop()
                        descriptor.is_started = False
                        descriptor.stop_order = self._stop_counter
                        self._stop_counter += 1
                        self._save_to_db(descriptor)
                        results[sid] = True
                        logger(f"[DI容器] 停止服务 ({descriptor.stop_order}): {sid}")
                    except Exception as e:
                        results[sid] = False
                        logger(f"[DI容器] 停止失败 {sid}: {e}")

        self.is_running = False
        return results

    def unregister(self, service_id: str) -> bool:
        """注销服务"""
        with self.lock:
            dependents = self.get_dependents(service_id)
            if dependents:
                logger(f"[DI容器] 无法注销, 被依赖: {dependents}")
                return False

            descriptor = self.services.pop(service_id, None)
            self.instances.pop(service_id, None)

            if descriptor and descriptor.is_started:
                instance = self.instances.get(service_id)
                if instance and hasattr(instance, 'stop'):
                    try:
                        instance.stop()
                    except:
                        pass

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM di_services WHERE service_id = ?', (service_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[DI容器] 删除服务记录失败: {e}")

        return True

    def get_service_info(self, service_id: str) -> Optional[Dict[str, Any]]:
        descriptor = self.services.get(service_id)
        if not descriptor:
            return None
        return descriptor.to_dict()

    def list_services(self, started_only: bool = False) -> List[Dict[str, Any]]:
        with self.lock:
            descriptors = list(self.services.values())

            if started_only:
                descriptors = [d for d in descriptors if d.is_started]

            return [d.to_dict() for d in descriptors]

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖图"""
        with self.lock:
            return {
                sid: desc.dependencies
                for sid, desc in self.services.items()
            }

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            started = sum(1 for d in self.services.values() if d.is_started)

            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_services': len(self.services),
                'started_services': started,
                'instances': len(self.instances),
                'has_circular_deps': self._check_circular_deps()
            }

    def _check_circular_deps(self) -> bool:
        """检查是否有循环依赖"""
        visited = set()
        rec_stack = set()

        def has_cycle(sid: str) -> bool:
            visited.add(sid)
            rec_stack.add(sid)

            descriptor = self.services.get(sid)
            if descriptor:
                for dep in descriptor.dependencies:
                    if dep not in self.services:
                        continue
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.discard(sid)
            return False

        for sid in self.services:
            if sid not in visited:
                if has_cycle(sid):
                    return True

        return False

    def start(self):
        if self.is_running:
            return
        self.start_all()

    def stop(self):
        if not self.is_running:
            return
        self.stop_all()


di_container = DIContainer()
