# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
AI集管理器
负责管理AI员工组和它们的协作
r"""

import logging
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(r'ai_collection_manager')


class AICollection:
    r"""AI集类:代表一组AI员工的集合r"""

    def __init__(self, collection_id: str, name: str, description: str = r""):
        r"""初始化AI集

        Args:
            collection_id: AI集ID
            name: AI集名称
            description: AI集描述
        r"""
        self.collection_id = collection_id
        self.name = name
        self.description = description
        self.status = r"active"
        self.created_at = datetime.now()
        self.last_updated_at = datetime.now()
        self.ai_employees: List[str] = []
        self.performance_metrics = {
            r"total_tasks": 0,
            r"completed_tasks": 0,
            r"success_rate": 1.0,
            r"average_response_time": 0.0,
            r"resource_utilization": 0.0
        }
        self.task_queue = []
        self.logger = logging.getLogger(fr"ai_collection_{collection_id}")
        self.logger.info(fr"✓ AI集 {name} 已初始化")

    def get_status(self) -> Dict:
        r"""获取AI集状态

        Returns:
            AI集状态信息
        r"""
        return {
            r'collection_id': self.collection_id,
            r'name': self.name,
            r'description': self.description,
            r'status': self.status,
            r'ai_employees_count': len(self.ai_employees),
            r'performance_metrics': self.performance_metrics,
            r'created_at': self.created_at.isoformat(),
            r'last_updated_at': self.last_updated_at.isoformat()
        }

    def add_ai_employee(self, ai_employee_id: str) -> bool:
        r"""添加AI员工到集合r"""
        if ai_employee_id not in self.ai_employees:
            self.ai_employees.append(ai_employee_id)
            self.last_updated_at = datetime.now()
            self.logger.info(fr"添加AI员工 {ai_employee_id} 到集合")
            return True
        return False

    def remove_ai_employee(self, ai_employee_id: str) -> bool:
        r"""从集合中移除AI员工r"""
        if ai_employee_id in self.ai_employees:
            self.ai_employees.remove(ai_employee_id)
            self.last_updated_at = datetime.now()
            self.logger.info(fr"从集合中移除AI员工 {ai_employee_id}")
            return True
        return False

    def execute_next_task(self, ai_employee_manager):
        r"""执行下一个任务r"""
        if self.task_queue:
            task = self.task_queue.pop(0)
            self.logger.info(fr"执行任务: {task}")
            return True
        return False


class AICollectionManager:
    r"""AI集管理器类r"""

    def __init__(self):
        r"""初始化AI集管理器r"""
        self.collections: Dict[str, AICollection] = {}
        self.collection_counter = 0
        self.logger = logging.getLogger(r"ai_collection_manager")
        self.logger.info(r"✓ AI集管理器已初始化")

        self.auto_management_thread = threading.Thread(target=self._auto_management_loop, daemon=True)
        self.auto_management_thread.start()
        self.logger.info(r"✓ 自动管理线程已启动")

    def _auto_management_loop(self) -> None:
        r"""自动管理循环:定期检查和维护AI集r"""
        while True:
            time.sleep(60)
            self._auto_manage_collections()

    def _auto_manage_collections(self) -> None:
        r"""自动管理AI集r"""
        self.logger.info(r"执行AI集自动管理...")

        for collection_id, collection in self.collections.items():
            if collection.task_queue and collection.status == r"active":
                try:
                    from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
                    ai_employee_manager = get_ai_employee_manager()
                    collection.execute_next_task(ai_employee_manager)
                except Exception as e:
                    self.logger.error(fr"管理AI集 {collection_id} 时发生异常: {str(e)}")

    def create_collection(self, name: str, description: str = r"") -> AICollection:
        r"""创建AI集

        Args:
            name: AI集名称
            description: AI集描述

        Returns:
            创建的AI集实例
        r"""
        self.collection_counter += 1
        collection_id = fr"collection_{self.collection_counter:04d}"

        collection = AICollection(collection_id, name, description)
        self.collections[collection_id] = collection
        self.logger.info(fr"✓ AI集 {name} 已创建,ID: {collection_id}")
        return collection

    def get_collection(self, collection_id: str) -> Optional[AICollection]:
        r"""获取AI集r"""
        return self.collections.get(collection_id)

    def delete_collection(self, collection_id: str) -> bool:
        r"""删除AI集r"""
        if collection_id in self.collections:
            del self.collections[collection_id]
            self.logger.info(fr"✓ AI集 {collection_id} 已删除")
            return True
        return False

    def get_all_collections(self) -> List[AICollection]:
        r"""获取所有AI集r"""
        return list(self.collections.values())

    def add_ai_to_collection(self, collection_id: str, ai_employee_id: str) -> bool:
        r"""将AI员工添加到AI集r"""
        collection = self.get_collection(collection_id)
        if collection:
            return collection.add_ai_employee(ai_employee_id)
        return False

    def remove_ai_from_collection(self, collection_id: str, ai_employee_id: str) -> bool:
        r"""从AI集中移除AI员工r"""
        collection = self.get_collection(collection_id)
        if collection:
            return collection.remove_ai_employee(ai_employee_id)
        return False
