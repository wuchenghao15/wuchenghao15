# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
独立版AI脑图分布式管理系统

不依赖完整的Flask应用程序,直接实现AI脑图核心功能
"""

import logging
logger = logging.getLogger(__name__)
import threading
import time
import uuid
from collections import defaultdict
import sys
import os


class StandaloneAIBrainService:
    """独立版AI脑库服务"""

    def __init__(self):
        self.knowledge_base = []
        self.knowledge_id_counter = 1

    def add_knowledge(self, title, content, knowledge_type, tags=None):
        """添加知识"""
        knowledge = {
            "knowledge_id": f"knowledge_{self.knowledge_id_counter}",
            "title": title,
            "content": content,
            "knowledge_type": knowledge_type,
            "tags": tags or [],
            "is_active": True
        }
        self.knowledge_base.append(knowledge)
        self.knowledge_id_counter += 1
        return knowledge

    def search_knowledge_by_tags(self, tags):
        """根据标签搜索知识"""
        results = []
        for knowledge in self.knowledge_base:
            if any(tag in knowledge["tags"] for tag in tags):
                class KnowledgeObject:
                    def __init__(self, **kwargs):
                        self.__dict__.update(kwargs)

                knowledge_obj = KnowledgeObject(**knowledge)
                results.append(knowledge_obj)
        return results

    def get_knowledge_graph(self):
        """获取知识图谱"""
        graph = {
            "nodes": [],
            "edges": []
        }
        for knowledge in self.knowledge_base:
            graph["nodes"].append({
                "id": knowledge["knowledge_id"],
                "label": knowledge["title"],
                "type": knowledge["knowledge_type"],
                "tags": knowledge["tags"]
            })

        return graph


class StandaloneAIInstanceManager:
    """独立版AI实例管理器"""

    def __init__(self):
        self.ai_employees = {}
        self.ai_collections = {}

    def create_collection(self, collection_id, name, description, status="active"):
        """创建AI集"""
        collection = {
            "collection_id": collection_id,
            "name": name,
            "description": description,
            "status": status,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        self.ai_collections[collection_id] = collection
        return collection

    def get_all_collections(self):
        """获取所有AI集"""
        return list(self.ai_collections.values())

    def get_ai_instance(self, instance_id):
        """获取AI实例"""
        return None

    def update_ai_instance(self, instance_id, updates):
        """更新AI实例"""
        return True

    def create_ai_instance(self, instance_id, ai_type, name, description, functions=None,
                          responsibilities=None, config=None, collection_id=None):
        """创建AI实例"""
        return {
            "instance_id": instance_id,
            "ai_type": ai_type,
            "name": name,
            "description": description,
            "collection_id": collection_id,
            "status": "active"
        }

    def create_enhanced_ai_employee(self, name, ai_type, description, capabilities=None,
                                    status="active", config=None, brain_integration=True,
                                    system_access=True, adaptation_level=1):
        """创建强化版AI员工"""
        employee_id = f"employee_{uuid.uuid4().hex[:8]}"
        employee = {
            "employee_id": employee_id,
            "name": name,
            "ai_type": ai_type,
            "description": description,
            "capabilities": capabilities or [],
            "status": status,
            "config": config or {},
            "brain_integration": brain_integration,
            "system_access": system_access,
            "adaptation_level": adaptation_level,
            "created_at": time.time(),
        }
        self.ai_employees[employee_id] = employee
        return employee

    def get_enhanced_ai_employee(self, employee_id):
        """获取强化版AI员工"""
        return self.ai_employees.get(employee_id)

    def get_all_enhanced_ai_employees(self):
        """获取所有强化版AI员工"""
        return list(self.ai_employees.values())


class AIBrainMap:
    """AI脑图"""

    def __init__(self):
        self.ai_brain_service = StandaloneAIBrainService()
        self.ai_instance_manager = StandaloneAIInstanceManager()

        self.brain_map = {
            "nodes": [],
            "edges": [],
            "ai_collections": {},
            "ai_employees": {}
        }
        self.lock = threading.Lock()
        self.is_initialized = False

    def _add_initial_knowledge(self):
        """添加初始知识"""
        knowledge_items = [
            {
                "title": "AI集管理最佳实践",
                "content": "1. 定期同步AI实例知识到AI脑库\n2. 为AI集添加清晰的描述和标签\n3. 定期检查AI集状态\n4. 优化AI集配置\n5. 监控AI集性能\n6. 定期升级AI集",
                "knowledge_type": "experience",
                "tags": ["AI集", "管理", "最佳实践"]
            },
            {
                "title": "AI实例管理规则",
                "content": "1. 每个AI实例必须有唯一的ID\n2. AI实例必须分配到合适的AI集\n3. 定期检查AI实例状态\n4. 定期同步AI实例知识到AI脑库\n5. 定期清理长时间未使用的AI实例\n6. 定期升级AI实例配置",
                "knowledge_type": "rule",
                "tags": ["AI实例", "管理", "规则"]
            },
            {
                "title": "AI对话系统设计",
                "content": "1. 清晰的对话流程设计\n2. 自然语言理解\n3. 上下文管理\n4. 多轮对话支持\n5. 错误处理和恢复",
                "knowledge_type": "knowledge",
                "tags": ["AI", "对话", "设计"]
            },
            {
                "title": "系统优化技术",
                "content": "1. 性能监控和分析\n2. 资源优化\n3. 代码优化\n4. 数据库优化\n5. 缓存策略",
                "knowledge_type": "knowledge",
                "tags": ["系统", "优化", "技术"]
            }
        ]
        for item in knowledge_items:
            self.ai_brain_service.add_knowledge(**item)

    def initialize(self):
        """初始化AI脑图"""
        with self.lock:
            if self.is_initialized:
                return True

            print("开始初始化AI脑图分布式管理系统...")

            self._add_initial_knowledge()

            knowledge_graph = self.ai_brain_service.get_knowledge_graph()
            if knowledge_graph:
                self.brain_map["nodes"] = knowledge_graph["nodes"]
                self.brain_map["edges"] = knowledge_graph["edges"]
                print(f"成功加载知识图谱,包含 {len(self.brain_map['nodes'])} 个节点和 {len(self.brain_map['edges'])} 条边")
            else:
                print("无法从AI脑库获取知识图谱,将创建空脑图")

            self._load_existing_collections()
            self._load_existing_ai_employees()
            self._build_brain_map_connections()

            self.is_initialized = True
            print("AI脑图分布式管理系统初始化完成")
            return True

    def _load_existing_collections(self):
        """加载现有的AI集"""
        collections = self.ai_instance_manager.get_all_collections()
        for collection in collections:
            self.brain_map["ai_collections"][collection["collection_id"]] = collection
        print(f"成功加载 {len(self.brain_map['ai_collections'])} 个现有AI集")

    def _load_existing_ai_employees(self):
        """加载现有的AI员工"""
        ai_employees = self.ai_instance_manager.get_all_enhanced_ai_employees()
        for employee in ai_employees:
            self.brain_map["ai_employees"][employee["employee_id"]] = employee
        print(f"成功加载 {len(self.brain_map['ai_employees'])} 个现有AI员工")

    def _build_brain_map_connections(self):
        """建立脑图与AI集的关联"""
        for collection_id, collection in self.brain_map["ai_collections"].items():
            existing_node = next((node for node in self.brain_map["nodes"]
                                 if node.get("label") == collection["name"] and node.get("type") == "ai_collection"), None)

            if not existing_node:
                ai_collection_node = {
                    "id": f"collection_{collection_id}",
                    "label": collection["name"],
                    "type": "ai_collection",
                    "tags": ["ai_collection", collection["name"]],
                    "collection_id": collection_id
                }
                self.brain_map["nodes"].append(ai_collection_node)

    def create_distributed_ai_collection(self, name, description, knowledge_tags=None):
        """基于AI脑图创建分布式AI功能集"""
        with self.lock:
            print(f"开始基于AI脑图创建分布式AI功能集: {name}")

            collection_id = f"collection_{uuid.uuid4().hex[:8]}"

            related_knowledge = []
            if knowledge_tags:
                related_knowledge = self.ai_brain_service.search_knowledge_by_tags(knowledge_tags)
                print(f"找到 {len(related_knowledge)} 条与标签 {knowledge_tags} 相关的知识")

            collection = self.ai_instance_manager.create_collection(
                collection_id=collection_id,
                name=name,
                description=description,
                status="active"
            )

            if not collection:
                print(f"创建AI集 {name} 失败")
                return None

            self.brain_map["ai_collections"][collection_id] = collection

            ai_collection_node = {
                "id": f"collection_{collection_id}",
                "label": name,
                "type": "ai_collection",
                "tags": ["ai_collection", name] + (knowledge_tags or []),
                "collection_id": collection_id
            }
            self.brain_map["nodes"].append(ai_collection_node)

            for knowledge in related_knowledge:
                edge = {
                    "source": ai_collection_node["id"],
                    "target": knowledge.knowledge_id,
                    "type": "related_to"
                }
                self.brain_map["edges"].append(edge)

            return collection

    def assign_ai_employee_to_collection(self, employee_id, collection_id):
        """将AI员工分配到AI功能集"""
        with self.lock:
            print(f"开始将AI员工 {employee_id} 分配到AI功能集 {collection_id}")

            employee = self.brain_map["ai_employees"].get(employee_id)
            collection = self.brain_map["ai_collections"].get(collection_id)

            if not employee:
                print(f"AI员工 {employee_id} 不存在")
                return False
            if not collection:
                print(f"AI功能集 {collection_id} 不存在")
                return False

            ai_instance_id = f"instance_{employee_id}"
            existing_instance = self.ai_instance_manager.get_ai_instance(ai_instance_id)
            if existing_instance:
                self.ai_instance_manager.update_ai_instance(ai_instance_id, {
                    "collection_id": collection_id
                })
                print(f"已将现有AI实例 {ai_instance_id} 分配到AI功能集 {collection_id}")
            else:
                ai_instance = self.ai_instance_manager.create_ai_instance(
                    instance_id=ai_instance_id,
                    ai_type=employee["ai_type"],
                    name=employee["name"],
                    functions=employee.get("capabilities"),
                    responsibilities=employee.get("capabilities"),
                    config=employee.get("config"),
                    collection_id=collection_id
                )

            employee_node_id = f"employee_{employee_id}"
            collection_node_id = f"collection_{collection_id}"

            existing_edge = next((edge for edge in self.brain_map["edges"]
                                if edge.get("source") == employee_node_id and edge.get("target") == collection_node_id), None)

            if not existing_edge:
                edge = {
                    "source": employee_node_id,
                    "target": collection_node_id,
                    "type": "assigned_to"
                }
                self.brain_map["edges"].append(edge)

            return True

    def create_ai_employee_from_brain(self, name, ai_type, capabilities=None, knowledge_tags=None):
        """基于AI脑图知识创建AI员工"""
        with self.lock:
            print(f"开始基于AI脑图创建AI员工: {name}")

            enhanced_capabilities = capabilities or []
            if knowledge_tags:
                related_knowledge = self.ai_brain_service.search_knowledge_by_tags(knowledge_tags)
                for knowledge in related_knowledge:
                    if knowledge.content:
                        content_lower = knowledge.content.lower()
                        if "优化" in content_lower and "optimization" not in enhanced_capabilities:
                            enhanced_capabilities.append("optimization")
                        if "分析" in content_lower and "analysis" not in enhanced_capabilities:
                            enhanced_capabilities.append("analysis")
                        if "诊断" in content_lower and "diagnosis" not in enhanced_capabilities:
                            enhanced_capabilities.append("diagnosis")
                        if "修复" in content_lower and "fixing" not in enhanced_capabilities:
                            enhanced_capabilities.append("fixing")
                        if "管理" in content_lower and "management" not in enhanced_capabilities:
                            enhanced_capabilities.append("management")

            ai_employee = self.ai_instance_manager.create_enhanced_ai_employee(
                name=name,
                ai_type=ai_type,
                description=f"基于AI脑图知识创建的{ai_type}类型AI员工",
                capabilities=enhanced_capabilities,
                status="active",
                config={
                    "brain_integration": True,
                    "auto_adaptation": True,
                },
                brain_integration=True,
                system_access=True,
                adaptation_level=1
            )

            if not ai_employee:
                print(f"创建AI员工 {name} 失败")
                return None

            self.brain_map["ai_employees"][ai_employee["employee_id"]] = ai_employee

            ai_employee_node = {
                "id": f"employee_{ai_employee['employee_id']}",
                "label": name,
                "type": "ai_employee",
                "tags": ["ai_employee", ai_type] + enhanced_capabilities,
                "employee_id": ai_employee["employee_id"],
                "ai_type": ai_type
            }
            self.brain_map["nodes"].append(ai_employee_node)

            if knowledge_tags:
                related_knowledge = self.ai_brain_service.search_knowledge_by_tags(knowledge_tags)
                for knowledge in related_knowledge:
                    edge = {
                        "source": ai_employee_node["id"],
                        "target": knowledge.knowledge_id,
                        "type": "learned_from"
                    }
                    self.brain_map["edges"].append(edge)

            return ai_employee

    def distribute_ai_employees(self, knowledge_domain, ai_count=2):
        """基于AI脑图知识域分布式部署AI员工"""
        with self.lock:
            print(f"开始基于知识域 {knowledge_domain} 分布式部署 {ai_count} 个AI员工")

            collection = self.create_distributed_ai_collection(
                name=f"{knowledge_domain} 功能集",
                description=f"基于{knowledge_domain}知识域的分布式AI功能集",
                knowledge_tags=[knowledge_domain]
            )

            if not collection:
                print(f"创建{knowledge_domain}功能集失败")
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

            print(f"成功基于知识域 {knowledge_domain} 分布式部署 {len(deployed_employees)} 个AI员工")
            return deployed_employees

    def get_brain_map(self):
        """获取完整的AI脑图"""
        with self.lock:
            return self.brain_map

    def get_ai_collection_employees(self, collection_id):
        """获取AI功能集中的所有AI员工"""
        with self.lock:
            employees = []

            for edge in self.brain_map["edges"]:
                if edge.get("type") == "assigned_to" and edge.get("target") == f"collection_{collection_id}":
                    employee_node_id = edge["source"]
                    employee_node = next((node for node in self.brain_map["nodes"]
                                       if node.get("id") == employee_node_id), None)
                    if employee_node and "employee_id" in employee_node:
                        employee_id = employee_node["employee_id"]
                        employee = self.ai_instance_manager.get_enhanced_ai_employee(employee_id)
                        if employee:
                            employees.append(employee)
            return employees

    def optimize_brain_map(self):
        """优化AI脑图,重新分配AI资源"""
        with self.lock:
            print("开始优化AI脑图,重新分配AI资源")

            collection_employee_count = defaultdict(int)
            for edge in self.brain_map["edges"]:
                if edge.get("type") == "assigned_to":
                    collection_node_id = edge["target"]
                    collection_employee_count[collection_node_id] += 1

            for collection_id in self.brain_map["ai_collections"]:
                current_count = collection_employee_count.get(f"collection_{collection_id}", 0)
                if current_count < 2:
                    free_employees = []
                    for employee_id, employee in self.brain_map["ai_employees"].items():
                        is_assigned = any(edge.get("source") == f"employee_{employee_id}"
                                         and edge.get("type") == "assigned_to"
                                         for edge in self.brain_map["edges"])
                        if not is_assigned:
                            free_employees.append(employee)

                    for employee in free_employees[:2 - current_count]:
                        self.assign_ai_employee_to_collection(
                            employee_id=employee["employee_id"],
                            collection_id=collection_id
                        )

            print("AI脑图优化完成,AI资源已重新分配")
            return True

    def generate_brain_map_report(self):
        """生成AI脑图报告"""
        with self.lock:
            report = {
                "timestamp": time.time(),
                "total_nodes": len(self.brain_map["nodes"]),
                "total_edges": len(self.brain_map["edges"]),
                "ai_collections": len(self.brain_map["ai_collections"]),
                "ai_employees": len(self.brain_map["ai_employees"]),
                "node_types": defaultdict(int),
                "edge_types": defaultdict(int)
            }

            for node in self.brain_map["nodes"]:
                node_type = node.get("type", "unknown")
                report["node_types"][node_type] += 1

            for edge in self.brain_map["edges"]:
                edge_type = edge.get("type", "unknown")
                report["edge_types"][edge_type] += 1

            report["node_types"] = dict(report["node_types"])
            report["edge_types"] = dict(report["edge_types"])

            report["collection_employee_count"] = {}
            for collection_id in self.brain_map["ai_collections"]:
                employees = self.get_ai_collection_employees(collection_id)
                report["collection_employee_count"][collection_id] = len(employees)

            return report


def test_standalone_ai_brain_map():
    """测试独立版AI脑图分布式管理系统"""
    print("=" * 60)
    print("独立版AI脑图分布式管理系统测试")
    print("=" * 60)

    ai_brain_map = AIBrainMap()

    print("\n1. 初始化AI脑图...")
    success = ai_brain_map.initialize()
    if success:
        print("✅ AI脑图初始化成功")
    else:
        print("❌ AI脑图初始化失败")
        return False

    print("\n2. 创建分布式AI功能集...")
    collection = ai_brain_map.create_distributed_ai_collection(
        name="测试AI功能集",
        description="用于测试的分布式AI功能集",
        knowledge_tags=["AI", "管理", "优化"]
    )

    if collection:
        print(f"✅ 成功创建AI功能集: {collection['name']} (ID: {collection['collection_id']})")
    else:
        print("❌ 创建AI功能集失败")
        return False

    print("\n3. 基于AI脑图创建AI员工...")
    ai_employee = ai_brain_map.create_ai_employee_from_brain(
        name="测试AI员工",
        ai_type="general",
        capabilities=["对话交互", "信息查询", "任务执行"],
        knowledge_tags=["AI", "对话"]
    )

    if ai_employee:
        print(f"✅ 成功创建AI员工: {ai_employee['name']} (ID: {ai_employee['employee_id']})")
    else:
        print("❌ 创建AI员工失败")
        return False

    print("\n4. 将AI员工分配到AI功能集...")
    success = ai_brain_map.assign_ai_employee_to_collection(
        employee_id=ai_employee["employee_id"],
        collection_id=collection["collection_id"]
    )

    if success:
        print(f"✅ 成功将AI员工 {ai_employee['employee_id']} 分配到AI功能集 {collection['collection_id']}")
    else:
        print("❌ 分配AI员工失败")
        return False

    print("\n5. 生成AI脑图报告...")
    report = ai_brain_map.generate_brain_map_report()
    if report:
        print("✅ 成功生成AI脑图报告:")
        print(f"   - 时间戳: {report['timestamp']}")
        print(f"   - 总节点数: {report['total_nodes']}")
        print(f"   - 总边数: {report['total_edges']}")
        print(f"   - AI集数量: {report['ai_collections']}")
        print(f"   - AI员工数量: {report['ai_employees']}")
    else:
        print("❌ 生成AI脑图报告失败")

    print("\n" + "=" * 60)
    print("独立版AI脑图分布式管理系统测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    test_standalone_ai_brain_map()
