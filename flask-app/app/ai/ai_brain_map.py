#!/usr/bin/env python3
"""
AI脑图分布式管理系统

基于AI脑库知识图谱，实现分布式AI功能集创建、AI员工统管和脑图统一分配AI集

import threading
import time
import uuid
from app.utils.logging import logger
from app.services.ai_brain_service import ai_brain_service
from app.ai.instances import ai_instance_manager
from app.models.ai import AIInstance, AICollection
from app.models.enhanced_ai_employee import EnhancedAIEmployee


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
                logger.info("AI脑图已初始化，跳过")
                return True

            logger.info("开始初始化AI脑图分布式管理系统...")

            # 1. 从AI脑库获取知识图谱
            knowledge_graph = ai_brain_service.get_knowledge_graph()
            if knowledge_graph:
                self.brain_map["nodes"] = knowledge_graph["nodes"]
                self.brain_map["edges"] = knowledge_graph["edges"]
                logger.info(f"成功加载知识图谱，包含 {len(self.brain_map['nodes'])} 个节点和 {len(self.brain_map['edges'])} 条边")
            else:
                logger.warning("无法从AI脑库获取知识图谱，将创建空脑图")

            # 2. 加载现有的AI集和AI员工
            self._load_existing_collections()
            self._load_existing_ai_employees()

            # 3. 建立脑图与AI集的关联
            self._build_brain_map_connections()

            self.is_initialized = True
            logger.info("AI脑图分布式管理系统初始化完成")
            return True
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
        # 为每个AI集创建脑图节点
        for collection_id, collection in self.brain_map["ai_collections"].items():
            # 检查是否已存在该AI集的脑图节点
            existing_node = next((node for node in self.brain_map["nodes"]
                                 if node["label"] == collection["name"] and node["type"] == "ai_collection"), None)

            if not existing_node:
                # 创建新的AI集脑图节点
                ai_collection_node = {
                    "id": f"collection_{collection_id}",
                    "label": collection["name"],
                    "type": "ai_collection",
                    "tags": ["ai_collection", collection["name"]],
                    "collection_id": collection_id
                }
                logger.info(f"为AI集 {collection_id} 创建脑图节点")

        # 为每个AI员工创建脑图节点
        for employee_id, employee in self.brain_map["ai_employees"].items():
            # 检查是否已存在该AI员工的脑图节点
            existing_node = next((node for node in self.brain_map["nodes"]
                                 if node["label"] == employee["name"] and node["type"] == "ai_employee"), None)

                # 创建新的AI员工脑图节点
                ai_employee_node = {
                    "id": f"employee_{employee_id}",
                    "type": "ai_employee",
                    "tags": ["ai_employee", employee["ai_type"]] + (employee["capabilities"] or []),
                    "employee_id": employee_id,
                    "ai_type": employee["ai_type"]
                }
                logger.info(f"为AI员工 {employee_id} 创建脑图节点")

    def create_distributed_ai_collection(self, name, description, knowledge_tags=None):
        """基于AI脑图创建分布式AI功能集

        Args:
            name: AI功能集名称
            description: AI功能集描述
            knowledge_tags: 关联的知识标签列表

        Returns:
            dict: 创建的AI功能集信息
        with self.lock:
            logger.info(f"开始基于AI脑图创建分布式AI功能集: {name}")

            # 1. 生成唯一的AI集ID

            # 2. 基于知识标签查找相关知识
            related_knowledge = []
            if knowledge_tags:
                related_knowledge = ai_brain_service.search_knowledge_by_tags(knowledge_tags)
                logger.info(f"找到 {len(related_knowledge)} 条与标签 {knowledge_tags} 相关的知识")

            # 3. 创建AI集
            collection = ai_instance_manager.create_collection(
                collection_id=collection_id,
                name=name,
                description=description,
                status="active"
            )

            if not collection:
                logger.error(f"创建AI集 {name} 失败")
                return None

            # 4. 将AI集添加到脑图
            self.brain_map["ai_collections"][collection_id] = collection

            # 5. 创建AI集脑图节点
            ai_collection_node = {
                "id": f"collection_{collection_id}",
                "label": name,
                "type": "ai_collection",
                "tags": ["ai_collection", name] + (knowledge_tags or []),
                "collection_id": collection_id
            }
            self.brain_map["nodes"].append(ai_collection_node)
            for knowledge in related_knowledge:
                    "source": ai_collection_node["id"],
                    "target": knowledge.knowledge_id,
                }
                self.brain_map["edges"].append(edge)
            return collection

        """将AI员工分配到AI功能集

        Args:
            employee_id: AI员工ID
            collection_id: AI功能集ID

        Returns:
            bool: 是否分配成功
        with self.lock:
            logger.info(f"开始将AI员工 {employee_id} 分配到AI功能集 {collection_id}")

            # 1. 检查AI员工和AI集是否存在
            employee = self.brain_map["ai_employees"].get(employee_id)
            collection = self.brain_map["ai_collections"].get(collection_id)

                logger.error(f"AI员工 {employee_id} 不存在")
                return False
            if not collection:
                logger.error(f"AI功能集 {collection_id} 不存在")
                return False

            # 2. 创建AI实例并分配到AI集
            # 首先检查是否已有对应的AI实例
            ai_instance_id = f"ai_{employee_id}"
            existing_instance = ai_instance_manager.get_ai_instance(ai_instance_id)

            if existing_instance:
                # 更新现有实例的AI集
                ai_instance_manager.update_ai_instance(ai_instance_id, {
                    "collection_id": collection_id
                })
                logger.info(f"已将现有AI实例 {ai_instance_id} 分配到AI功能集 {collection_id}")
            else:
                # 创建新的AI实例
                ai_instance = ai_instance_manager.create_ai_instance(
                    ai_type=employee["ai_type"],
                    name=employee["name"],
                    functions=employee["capabilities"],
                    responsibilities=employee["capabilities"],
                    config=employee["config"],
                )
                logger.info(f"已创建AI实例 {ai_instance_id} 并分配到AI功能集 {collection_id}")
            # 3. 建立AI员工与AI集的脑图关联
            employee_node_id = f"employee_{employee_id}"
            collection_node_id = f"collection_{collection_id}"

            # 检查边是否已存在
            existing_edge = next((edge for edge in self.brain_map["edges"]
                                if edge["source"] == employee_node_id and edge["target"] == collection_node_id), None)

            if not existing_edge:
                edge = {
                    "source": employee_node_id,
                    "target": collection_node_id,
                    "type": "assigned_to"
                }
                self.brain_map["edges"].append(edge)

            return True

    def create_ai_employee_from_brain(self, name, ai_type, capabilities=None, knowledge_tags=None):
        """基于AI脑图知识创建AI员工

        Args:
            name: AI员工名称
            ai_type: AI员工类型
            capabilities: AI员工能力列表
            knowledge_tags: 关联的知识标签列表
        Returns:
            dict: 创建的AI员工信息
        with self.lock:
            logger.info(f"开始基于AI脑图创建AI员工: {name}")
            # 1. 基于知识标签查找相关知识，增强AI员工能力
            enhanced_capabilities = capabilities or []
            if knowledge_tags:
                related_knowledge = ai_brain_service.search_knowledge_by_tags(knowledge_tags)
                for knowledge in related_knowledge:
                        content_lower = knowledge.content.lower()
                        # 简单的关键词匹配，实际应用中可以使用更复杂的NLP方法
                        if "优化" in content_lower and "optimization" not in enhanced_capabilities:
                            enhanced_capabilities.append("optimization")
                            enhanced_capabilities.append("analysis")
                        if "诊断" in content_lower and "diagnosis" not in enhanced_capabilities:
                            enhanced_capabilities.append("diagnosis")
                        if "修复" in content_lower and "fixing" not in enhanced_capabilities:
                            enhanced_capabilities.append("fixing")
                            enhanced_capabilities.append("management")

            # 2. 创建强化版AI员工
            ai_employee = ai_instance_manager.create_enhanced_ai_employee(
                name=name,
                ai_type=ai_type,
                description=f"基于AI脑图知识创建的{ai_type}类型AI员工",
                capabilities=enhanced_capabilities,
                status="active",
                config={
                    "auto_adaptation": True,
                },
                brain_integration=True,
                system_access=True,
                adaptation_level=1
            )

            if not ai_employee:
                logger.error(f"创建AI员工 {name} 失败")
                return None

            # 3. 将AI员工添加到脑图
            self.brain_map["ai_employees"][ai_employee["employee_id"]] = ai_employee

            # 4. 创建AI员工脑图节点
            ai_employee_node = {
                "id": f"employee_{ai_employee['employee_id']}",
                "label": name,
                "type": "ai_employee",
                "employee_id": ai_employee["employee_id"],
                "ai_type": ai_type
            }
            self.brain_map["nodes"].append(ai_employee_node)

            # 5. 建立AI员工与相关知识的关联
                related_knowledge = ai_brain_service.search_knowledge_by_tags(knowledge_tags)
                for knowledge in related_knowledge:
                    edge = {
                        "source": ai_employee_node["id"],
                        "target": knowledge.knowledge_id,
                        "type": "learned_from"
                    }
                    self.brain_map["edges"].append(edge)

            logger.info(f"成功基于AI脑图创建AI员工: {name} (ID: {ai_employee['employee_id']})")

    def distribute_ai_employees(self, knowledge_domain, ai_count=3):

            knowledge_domain: 知识域名称

        Returns:
            list: 部署的AI员工列表
        with self.lock:
            logger.info(f"开始基于知识域 {knowledge_domain} 分布式部署 {ai_count} 个AI员工")
            # 1. 创建知识域对应的AI功能集
            collection = self.create_distributed_ai_collection(
                description=f"基于{knowledge_domain}知识域的分布式AI功能集",
                knowledge_tags=[knowledge_domain]
            )
            if not collection:
                logger.error(f"创建{knowledge_domain}功能集失败")
            # 2. 分布式部署AI员工
            deployed_employees = []
            ai_types = ["general", "technical", "creative", "research"][:ai_count]

            for i, ai_type in enumerate(ai_types):
                employee_name = f"{knowledge_domain}-{ai_type}-AI-{i+1}"
                # 基于知识域创建AI员工
                ai_employee = self.create_ai_employee_from_brain(
                    knowledge_tags=[knowledge_domain]
                )

                    # 将AI员工分配到AI功能集
                    self.assign_ai_employee_to_collection(
                        employee_id=ai_employee["employee_id"],
                    )
                    deployed_employees.append(ai_employee)

            logger.info(f"成功基于知识域 {knowledge_domain} 分布式部署 {len(deployed_employees)} 个AI员工")
            return deployed_employees

    def get_brain_map(self):
        """获取完整的AI脑图

        Returns:
            dict: AI脑图数据
        with self.lock:
            return self.brain_map

    def get_ai_collection_employees(self, collection_id):
        """获取AI功能集中的所有AI员工
        Args:
            collection_id: AI功能集ID

        Returns:
            list: AI员工列表
        with self.lock:
            employees = []

            # 查找分配到该AI功能集的所有AI员工节点
            for edge in self.brain_map["edges"]:
                if edge["target"] == collection_node_id and edge["type"] == "assigned_to":
                    employee_node_id = edge["source"]
                    # 查找对应的AI员工节点
                    employee_node = next((node for node in self.brain_map["nodes"]
                                       if node["id"] == employee_node_id), None)
                    if employee_node and "employee_id" in employee_node:
                        employee_id = employee_node["employee_id"]
                        employee = ai_instance_manager.get_enhanced_ai_employee(employee_id)
                            employees.append(employee)

            return employees

    def optimize_brain_map(self):
        """优化AI脑图，重新分配AI资源

            bool: 是否优化成功
            logger.info("开始优化AI脑图，重新分配AI资源")

            # 1. 分析AI功能集和AI员工的关联关系
            for edge in self.brain_map["edges"]:
                if edge["type"] == "assigned_to":
                    collection_node_id = edge["target"]
                    if collection_node_id not in collection_employee_count:
                        collection_node_id[collection_node_id] = 0
                    collection_node_id[collection_node_id] += 1

            # 2. 平衡AI员工分配
            # 简单的平衡策略：将员工数量较少的功能集优先分配
            for collection_id, collection in self.brain_map["ai_collections"].items():
                # 如果AI功能集没有分配足够的AI员工，尝试分配
                if current_count < 2:  # 每个功能集至少2个AI员工
                    # 查找空闲的AI员工
                    free_employees = []
                    for employee_id, employee in self.brain_map["ai_employees"].items():
                        # 检查员工是否已分配
                        is_assigned = any(edge["source"] == f"employee_{employee_id}"
                                         and edge["type"] == "assigned_to"
                                         for edge in self.brain_map["edges"])
                        if not is_assigned:
                            free_employees.append(employee)
                    # 分配空闲AI员工到AI功能集
                    for employee in free_employees[:2 - current_count]:
                        self.assign_ai_employee_to_collection(
                            employee_id=employee["employee_id"],
                            collection_id=collection_id
                        )

            logger.info("AI脑图优化完成，AI资源已重新分配")

    def generate_brain_map_report(self):

        Returns:
            dict: AI脑图报告
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
                report["edge_types"][edge_type] = report["edge_types"].get(edge_type, 0) + 1

            # 统计每个AI功能集的AI员工数量
            report["collection_employee_count"] = {}
            for collection_id in self.brain_map["ai_collections"]:
                employees = self.get_ai_collection_employees(collection_id)
                report["collection_employee_count"][collection_id] = len(employees)

            return report


# 初始化AI脑图分布式管理系统
ai_brain_map = AIBrainMap()

# 自动初始化AI脑图
if not ai_brain_map.is_initialized:
    ai_brain_map.initialize()
