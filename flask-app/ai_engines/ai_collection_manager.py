# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI集管理器
负责管理AI员工组和它们的协作
"""

import logging
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger('ai_collection_manager')


class AICollection:
    """AI集类:代表一组AI员工的集合"""

    def __init__(self, collection_id: str, name: str, description: str = ""):
        """初始化AI集

        Args:
            collection_id: AI集ID
            name: AI集名称
            description: AI集描述
        """
        self.collection_id = collection_id
        self.name = name
        self.description = description
        self.status = "active"
        self.created_at = datetime.now()
        self.last_updated_at = datetime.now()
        self.ai_employees: List[str] = []
        self.performance_metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "success_rate": 1.0,
            "average_response_time": 0.0,
            "resource_utilization": 0.0
        }
        self.task_queue = []
        self.logger = logging.getLogger(f"ai_collection_{collection_id}")
        self.logger.info(f"✓ AI集 {name} 已初始化")

    def get_status(self) -> Dict:
        """获取AI集状态

        Returns:
            AI集状态信息
        """
        return {
            'collection_id': self.collection_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'ai_employees_count': len(self.ai_employees),
            'performance_metrics': self.performance_metrics,
            'created_at': self.created_at.isoformat(),
            'last_updated_at': self.last_updated_at.isoformat()
        }

    def add_ai_employee(self, ai_employee_id: str) -> bool:
        """添加AI员工到集合"""
        if ai_employee_id not in self.ai_employees:
            self.ai_employees.append(ai_employee_id)
            self.last_updated_at = datetime.now()
            self.logger.info(f"添加AI员工 {ai_employee_id} 到集合")
            return True
        return False

    def remove_ai_employee(self, ai_employee_id: str) -> bool:
        """从集合中移除AI员工"""
        if ai_employee_id in self.ai_employees:
            self.ai_employees.remove(ai_employee_id)
            self.last_updated_at = datetime.now()
            self.logger.info(f"从集合中移除AI员工 {ai_employee_id}")
            return True
        return False

    def execute_next_task(self, ai_employee_manager):
        """执行下一个任务"""
        if self.task_queue:
            task = self.task_queue.pop(0)
            self.logger.info(f"执行任务: {task}")
            return True
        return False


class AICollectionManager:
    """AI集管理器类"""

    def __init__(self):
        """初始化AI集管理器"""
        self.collections: Dict[str, AICollection] = {}
        self.collection_counter = 0
        self.logger = logging.getLogger("ai_collection_manager")
        self.logger.info("✓ AI集管理器已初始化")

        self.auto_management_thread = threading.Thread(target=self._auto_management_loop, daemon=True)
        self.auto_management_thread.start()
        self.logger.info("✓ 自动管理线程已启动")

    def _auto_management_loop(self) -> None:
        """自动管理循环:定期检查和维护AI集"""
        while True:
            time.sleep(60)
            self._auto_manage_collections()

    def _auto_manage_collections(self) -> None:
        """自动管理AI集"""
        self.logger.info("执行AI集自动管理...")

        for collection_id, collection in self.collections.items():
            if collection.task_queue and collection.status == "active":
                try:
                    from app.ai.distributed_ai_employee_manager import get_ai_employee_manager
                    ai_employee_manager = get_ai_employee_manager()
                    collection.execute_next_task(ai_employee_manager)
                except Exception as e:
                    self.logger.error(f"管理AI集 {collection_id} 时发生异常: {str(e)}")

    def create_collection(self, name: str, description: str = "") -> AICollection:
        """创建AI集

        Args:
            name: AI集名称
            description: AI集描述

        Returns:
            创建的AI集实例
        """
        self.collection_counter += 1
        collection_id = f"collection_{self.collection_counter:04d}"

        collection = AICollection(collection_id, name, description)
        self.collections[collection_id] = collection
        self.logger.info(f"✓ AI集 {name} 已创建,ID: {collection_id}")
        return collection

    def get_collection(self, collection_id: str) -> Optional[AICollection]:
        """获取AI集"""
        return self.collections.get(collection_id)

    def delete_collection(self, collection_id: str) -> bool:
        """删除AI集"""
        if collection_id in self.collections:
            del self.collections[collection_id]
            self.logger.info(f"✓ AI集 {collection_id} 已删除")
            return True
        return False

    def get_all_collections(self) -> List[AICollection]:
        """获取所有AI集"""
        return list(self.collections.values())

    def add_ai_to_collection(self, collection_id: str, ai_employee_id: str) -> bool:
        """将AI员工添加到AI集"""
        collection = self.get_collection(collection_id)
        if collection:
            return collection.add_ai_employee(ai_employee_id)
        return False

    def remove_ai_from_collection(self, collection_id: str, ai_employee_id: str) -> bool:
        """从AI集中移除AI员工"""
        collection = self.get_collection(collection_id)
        if collection:
            return collection.remove_ai_employee(ai_employee_id)
        return False
