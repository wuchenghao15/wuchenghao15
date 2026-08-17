# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI脑图分布式管理系统
基于AI脑库知识图谱, 实现分布式AI功能集创建,AI员工统管和脑图统一分配AI集
"""

import threading
import time
import uuid
from app.utils.logging import logger
from app.services.ai_brain_service import ai_brain_service
from app.ai.instances import ai_instance_manager
from app.models.ai import AIInstance, AICollection
from app.models.enhanced_ai_employee import EnhancedAIEmployee
import logging
import sys
import os


class AIBrainMap:
    """AI脑图分布式管理系统"""

    def __init__(self):
        self.brain_map = {
            "nodes": [],
            "edges": [],
            "ai_collections": {},
            "ai_employees": {}
        }
        self.lock = threading.Lock()
        self.is_initialized = False

    def initialize(self):
        """初始化AI脑图"""
        with self.lock:
            if self.is_initialized:
                logger.info("AI脑图已初始化, 跳过")
                return True

            try:
                self._load_existing_collections()
                self._load_existing_ai_employees()
                self._build_brain_map_connections()
                self.is_initialized = True
                logger.info("AI脑图初始化完成")
                return True
            except Exception as e:
                logger.error(f"AI脑图初始化失败: {str(e)}")
                return False

    def _load_existing_collections(self):
        """加载现有的AI集"""
        collections = ai_instance_manager.get_all_collections()
        for collection in collections:
            self.brain_map["ai_collections"][collection["collection_id"]] = collection
        logger.info(f"成功加载 {len(self.brain_map['ai_collections'])} 个现有AI集")

    def _load_existing_ai_employees(self):
        """加载现有的AI员工"""
        ai_employees = ai_instance_manager.get_all_enhanced_ai_employees()
        for employee in ai_employees:
            self.brain_map["ai_employees"][employee["employee_id"]] = employee
        logger.info(f"成功加载 {len(self.brain_map['ai_employees'])} 个现有AI员工")

    def _build_brain_map_connections(self):
        """建立脑图与AI集的关联"""
        for collection_id, collection in self.brain_map["ai_collections"].items():
            existing_node = next(
                (node for node in self.brain_map["nodes"]
                 if node["label"] == collection["name"] and node["type"] == "ai_collection"),
                None
            )

            if not existing_node:
                ai_collection_node = {
                    "id": f"collection_{collection_id}",
                    "label": collection["name"],
                    "type": "ai_collection",
                    "tags": ["ai_collection", collection["name"]],
                    "collection_id": collection_id
                }
                self.brain_map["nodes"].append(ai_collection_node)
                logger.info(f"为AI集 {collection_id} 创建脑图节点")

        for employee_id, employee in self.brain_map["ai_employees"].items():
            existing_node = next(
                (node for node in self.brain_map["nodes"]
                 if node["label"] == employee["name"] and node["type"] == "ai_employee"),
                None
            )

            if not existing_node:
                ai_employee_node = {
                    "id": f"employee_{employee_id}",
                    "label": employee["name"],
                    "type": "ai_employee",
                    "tags": ["ai_employee", employee["ai_type"]] + (employee["capabilities"] or []),
                    "employee_id": employee_id,
                    "ai_type": employee["ai_type"]
                }
                self.brain_map["nodes"].append(ai_employee_node)
                logger.info(f"为AI员工 {employee_id} 创建脑图节点")

    def create_distributed_ai_collection(self, name, description, knowledge_tags=None):
        """基于AI脑图创建分布式AI功能集

        Args:
            name: AI功能集名称
            description: AI功能集描述
            knowledge_tags: 关联的知识标签列表

        Returns:
            dict: 创建的AI功能集信息
        """
        with self.lock:
            logger.info(f"开始基于AI脑图创建分布式AI功能集: {name}")

            collection_id = str(uuid.uuid4())

            related_knowledge = []
            if knowledge_tags:
                related_knowledge = ai_brain_service.search_knowledge_by_tags(knowledge_tags)
                logger.info(f"找到 {len(related_knowledge)} 条与标签 {knowledge_tags} 相关的知识")

            collection = ai_instance_manager.create_collection(
                collection_id=collection_id,
                name=name,
                description=description,
                status="active"
            )

            if not collection:
                logger.error(f"创建AI集 {name} 失败")
                return None

            self.brain_map["ai_collections"][collection_id] = collection
            logger.info(f"AI功能集创建成功: {collection_id}")
            return collection

    def create_ai_employee_from_brain(self, name, ai_type, capabilities=None, knowledge_tags=None):
        """基于AI脑图知识创建AI员工

        Args:
            name: AI员工名称
            ai_type: AI员工类型
            capabilities: AI员工能力列表
            knowledge_tags: 关联的知识标签列表

        Returns:
            dict: 创建的AI员工信息
        """
        with self.lock:
            logger.info(f"开始基于AI脑图创建AI员工: {name}")

            enhanced_capabilities = capabilities or []
            if knowledge_tags:
                related_knowledge = ai_brain_service.search_knowledge_by_tags(knowledge_tags)
                for knowledge in related_knowledge:
                    content_lower = knowledge.content.lower()
                    if "优化" in content_lower and "optimization" not in enhanced_capabilities:
                        enhanced_capabilities.append("optimization")
                        enhanced_capabilities.append("analysis")
                    if "诊断" in content_lower and "diagnosis" not in enhanced_capabilities:
                        enhanced_capabilities.append("diagnosis")
                    if "修复" in content_lower and "fixing" not in enhanced_capabilities:
                        enhanced_capabilities.append("fixing")
                        enhanced_capabilities.append("management")

            ai_employee = ai_instance_manager.create_enhanced_ai_employee(
                name=name,
                ai_type=ai_type,
                description=f"基于AI脑图知识创建的{ai_type}类型AI员工",
                capabilities=enhanced_capabilities,
                status="active",
                config={
                    "auto_adaptation": True
                },
                brain_integration=True,
                system_access=True,
                adaptation_level=1
            )

            if not ai_employee:
                logger.error(f"创建AI员工 {name} 失败")
                return None

            self.brain_map["ai_employees"][ai_employee["employee_id"]] = ai_employee
            logger.info(f"AI员工创建成功: {ai_employee['employee_id']}")
            return ai_employee

    def distribute_ai_employees(self, knowledge_domain, ai_count=3):
        """基于知识域分布式部署AI员工

        Args:
            knowledge_domain: 知识域名称
            ai_count: 部署的AI员工数量

        Returns:
            list: 部署的AI员工列表
        """
        with self.lock:
            logger.info(f"开始基于知识域 {knowledge_domain} 分布式部署 {ai_count} 个AI员工")

            collection = self.create_distributed_ai_collection(
                name=f"{knowledge_domain}_collection",
                description=f"基于{knowledge_domain}知识域的分布式AI功能集",
                knowledge_tags=[knowledge_domain]
            )

            if not collection:
                logger.error(f"创建{knowledge_domain}功能集失败")
                return []

            deployed_employees = []
            ai_types = ["general", "technical", "creative", "research"][:ai_count]

            for i, ai_type in enumerate(ai_types):
                employee_name = f"{knowledge_domain}-{ai_type}-AI-{i+1}"
                ai_employee = self.create_ai_employee_from_brain(
                    name=employee_name,
                    ai_type=ai_type,
                    knowledge_tags=[knowledge_domain]
                )

                if ai_employee:
                    self.assign_ai_employee_to_collection(
                        employee_id=ai_employee["employee_id"],
                        collection_id=collection["collection_id"]
                    )
                    deployed_employees.append(ai_employee)

            logger.info(f"成功基于知识域 {knowledge_domain} 分布式部署 {len(deployed_employees)} 个AI员工")
            return deployed_employees

    def assign_ai_employee_to_collection(self, employee_id, collection_id):
        """将AI员工分配到AI功能集"""
        edge = {
            "source": f"employee_{employee_id}",
            "target": f"collection_{collection_id}",
            "type": "assigned_to"
        }
        self.brain_map["edges"].append(edge)
        logger.info(f"AI员工 {employee_id} 已分配到功能集 {collection_id}")

    def get_brain_map(self):
        """获取完整的AI脑图

        Returns:
            dict: AI脑图数据
        """
        with self.lock:
            return self.brain_map

    def get_ai_collection_employees(self, collection_id):
        """获取AI功能集中的所有AI员工

        Args:
            collection_id: AI功能集ID

        Returns:
            list: AI员工列表
        """
        with self.lock:
            employees = []
            collection_node_id = f"collection_{collection_id}"

            for edge in self.brain_map["edges"]:
                if edge["target"] == collection_node_id and edge["type"] == "assigned_to":
                    employee_node_id = edge["source"]
                    employee_node = next(
                        (node for node in self.brain_map["nodes"] if node["id"] == employee_node_id),
                        None
                    )
                    if employee_node and "employee_id" in employee_node:
                        employee_id = employee_node["employee_id"]
                        employee = ai_instance_manager.get_enhanced_ai_employee(employee_id)
                        if employee:
                            employees.append(employee)

            return employees

    def optimize_brain_map(self):
        """优化AI脑图: 重新分配AI资源

        Returns:
            bool: 是否优化成功
        """
        with self.lock:
            logger.info("开始优化AI脑图, 重新分配AI资源")

            collection_employee_count = {}
            for edge in self.brain_map["edges"]:
                if edge["type"] == "assigned_to":
                    collection_node_id = edge["target"]
                    if collection_node_id not in collection_employee_count:
                        collection_employee_count[collection_node_id] = 0
                    collection_employee_count[collection_node_id] += 1

            for collection_id, collection in self.brain_map["ai_collections"].items():
                current_count = collection_employee_count.get(f"collection_{collection_id}", 0)
                if current_count < 2:
                    free_employees = []
                    for employee_id, employee in self.brain_map["ai_employees"].items():
                        is_assigned = any(
                            edge["source"] == f"employee_{employee_id}" and edge["type"] == "assigned_to"
                            for edge in self.brain_map["edges"]
                        )
                        if not is_assigned:
                            free_employees.append(employee)

                    for employee in free_employees[:2 - current_count]:
                        self.assign_ai_employee_to_collection(
                            employee_id=employee["employee_id"],
                            collection_id=collection_id
                        )

            logger.info("AI脑图优化完成, AI资源已重新分配")
            return True

    def generate_brain_map_report(self):
        """生成AI脑图报告

        Returns:
            dict: AI脑图报告
        """
        with self.lock:
            report = {
                "timestamp": time.time(),
                "total_nodes": len(self.brain_map["nodes"]),
                "total_edges": len(self.brain_map["edges"]),
                "ai_collections": len(self.brain_map["ai_collections"]),
                "ai_employees": len(self.brain_map["ai_employees"]),
                "node_types": {},
                "edge_types": {}
            }

            for node in self.brain_map["nodes"]:
                node_type = node["type"]
                report["node_types"][node_type] = report["node_types"].get(node_type, 0) + 1

            for edge in self.brain_map["edges"]:
                edge_type = edge["type"]
                report["edge_types"][edge_type] = report["edge_types"].get(edge_type, 0) + 1

            report["collection_employee_count"] = {}
            for collection_id in self.brain_map["ai_collections"]:
                employees = self.get_ai_collection_employees(collection_id)
                report["collection_employee_count"][collection_id] = len(employees)

            return report


ai_brain_map = AIBrainMap()
