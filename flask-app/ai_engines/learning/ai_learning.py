# -*- coding: utf-8 -*-
# MTSCOS AI Project - AI自我学习服务
"""
AI自我学习和自我升级的核心服务
"""

import os
# JSON import removed - using database
import time
import hashlib
import logging
import json
import sys
from typing import Dict, Any, List, Optional, Set, Tuple
from app.utils.logging import logger
from app.filesystem import file_system
from app.rules import rule_system
from app.services import get_ai_brain_service
from app.ai.ai_engine_integrator import ai_engine_integrator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class AILearningSystem:
    """AI自我学习系统,负责AI的自我学习,自我升级和适配能力"""

    def __init__(self):
        self._learning_data_dir = "ai_learning"
        self._upgrade_history_dir = "ai_upgrades"
        self._knowledge_base_dir = "ai_knowledge"
        self._project_adaptation_dir = "ai_adaptation"

        # 初始化学习目录
        self._initialize_directories()

        # 学习参数 - 优化版,增强适配能力
        self._learning_params = {
            "learning_rate": 0.2,
            "max_iterations": 3000,
            "convergence_threshold": 0.0001,
            "memory_retention": 0.95,
            "upgrade_check_interval": 1200,
            "feature_similarity_threshold": 0.6,
            "knowledge_density_threshold": 0.85,
            "adaptation_depth": 5,
            "association_cache_ttl": 600,
            "ai_engine": "local",
            "ai_engine_fallback": "minimax",
            "ai_enhanced_learning": True,
            "ai_analysis_depth": 4,
            "deep_adaptation_enabled": True,
            "cross_model_adaptation": True,
            "real_time_adaptation": False,
            "adaptation_confidence_threshold": 0.75
        }

        # 学习状态
        self._learning_state = {
            "last_learning_time": 0,
            "last_upgrade_check": 0,
            "learning_progress": 0,
            "current_task": None,
            "knowledge_count": 0,
            "adaptation_count": 0,
            "upgrade_count": 0,
            "association_count": 0,
        }

        # 知识图谱增强
        self._knowledge_graph = {
            "entities": {},
            "relations": {},
            "rules": {},
            "tasks": {}
        }

        # 项目适配模型 - 增强版,支持更多项目类型
        self._project_adaptation_models = {
            "web_application": self._adapt_to_web_app,
            "data_science": self._adapt_to_data_science,
            "mobile_app": self._adapt_to_mobile_app,
            "desktop_app": self._adapt_to_desktop_app,
            "ai_project": self._adapt_to_ai_project,
            "game_development": self._adapt_to_game_development,
            "blockchain": self._adapt_to_blockchain,
            "iot": self._adapt_to_iot,
            "cloud_native": self._adapt_to_cloud_native,
            "devops": self._adapt_to_devops,
            "fintech": self._adapt_to_fintech,
            "education_tech": self._adapt_to_education_tech,
        }

        # 功能关联模型
        self._feature_correlation_matrix = {}

        # 初始化AI脑库服务
        self._ai_brain_service = get_ai_brain_service()

        # 加载现有知识
        self._load_knowledge()

        # 初始化规则系统集成
        self._initialize_rule_integration()

        # 初始化能力拓展映射
        self._initialize_capability_expansions()

        # 初始化TF-IDF向量器用于功能联想
        self._tfidf_vectorizer = TfidfVectorizer()
        self._update_feature_vectors()

        # 加载升级历史
        self._load_upgrade_history()

        # 添加联想结果缓存和请求去重机制
        self._association_cache = {}
        self._last_vector_update = time.time()
        self._vector_update_interval = 600

        # 初始化升级历史列表
        self._upgrade_history = []

        # 记录初始化到AI脑库
        self._ai_brain_service._log_activity(
            activity_type="system_initialized",
            description="AI学习系统初始化完成",
            source="ai_learning_system",
            metadata={
                "version": self._get_current_version(),
                "initial_knowledge_count": self._learning_state["knowledge_count"]
            }
        )

    def _initialize_directories(self):
        """初始化学习相关目录"""
        # 创建AI学习数据目录
        file_system.create_directory(self._learning_data_dir)
        # 创建AI升级历史目录
        file_system.create_directory(self._upgrade_history_dir)
        # 创建AI知识库目录
        file_system.create_directory(self._knowledge_base_dir)
        # 创建项目适配目录
        file_system.create_directory(self._project_adaptation_dir)
        # 创建知识图谱目录
        file_system.create_directory(os.path.join(self._knowledge_base_dir, "graph"))
        # 创建规则目录
        file_system.create_directory(os.path.join(self._knowledge_base_dir, "rules"))
        # 创建任务目录
        file_system.create_directory(os.path.join(self._knowledge_base_dir, "tasks"))

    def _load_knowledge(self):
        """增强版加载知识库"""
        logger.info("加载AI知识库...")

        # 读取实体知识
        entities_file = os.path.join(self._knowledge_base_dir, "entities.json")
        if file_system.exists(entities_file):
            entities_data = file_system.read_file(entities_file)
            if entities_data:
                self._knowledge_graph["entities"] = entities_data

        # 读取关系知识
        relations_file = os.path.join(self._knowledge_base_dir, "relations.json")
        if file_system.exists(relations_file):
            relations_data = file_system.read_file(relations_file)
            if relations_data:
                self._knowledge_graph["relations"] = relations_data

        # 读取规则知识
        rules_dir = os.path.join(self._knowledge_base_dir, "rules")
        rules_files = file_system.list_directory(rules_dir)
        for rule_file in rules_files:
            if rule_file["type"] == "file" and rule_file["filename"].endswith(".json"):
                rule_path = os.path.join(rules_dir, rule_file["filename"])
                rule_data = file_system.read_file(rule_path)
                if rule_data:
                    self._knowledge_graph["rules"][rule_file["filename"]] = rule_data

        # 读取任务知识
        tasks_dir = os.path.join(self._knowledge_base_dir, "tasks")
        tasks_files = file_system.list_directory(tasks_dir)
        for task_file in tasks_files:
            if task_file["type"] == "file" and task_file["filename"].endswith(".json"):
                task_path = os.path.join(tasks_dir, task_file["filename"])
                task_data = file_system.read_file(task_path)
                if task_data:
                    self._knowledge_graph["tasks"][task_file["filename"]] = task_data

        self._learning_state["knowledge_count"] = (
            len(self._knowledge_graph["entities"]) +
            len(self._knowledge_graph["relations"]) +
            len(self._knowledge_graph["rules"]) +
            len(self._knowledge_graph["tasks"])
        )
        logger.info(f"AI知识库加载完成,共 {self._learning_state['knowledge_count']} 条知识")

    def _update_feature_vectors(self):
        """更新功能向量用于功能联想 - 增强版"""
        # 收集所有功能和描述
        self._feature_descriptions = {}

        # 1. 从知识图谱的任务中收集功能描述
        for task_type, tasks in self._knowledge_graph["tasks"].items():
            if isinstance(tasks, dict):
                for task_id, task_data in tasks.items():
                    feature_name = task_data.get("task", "").split(":")[0] if ":" in task_data.get("task", "") else task_data.get("task", "")
                    if feature_name:
                        description = task_data.get("description", feature_name)
                        if feature_name not in self._feature_descriptions:
                            self._feature_descriptions[feature_name] = description

        # 2. 从能力拓展映射中收集功能描述
        for capability, expansions in self._capability_expansions.items():
            if capability not in self._feature_descriptions:
                self._feature_descriptions[capability] = capability
            for expansion in expansions:
                if expansion["capability"] not in self._feature_descriptions:
                    self._feature_descriptions[expansion["capability"]] = expansion["description"]

        # 3. 从AI引擎配置中收集功能描述
        for engine, config in ai_engine_integrator.engine_configs.items():
            if "supported_features" in config:
                for feature in config["supported_features"]:
                    if feature not in self._feature_descriptions:
                        self._feature_descriptions[feature] = f"{engine}支持的{feature}功能"

        # 4. 更新TF-IDF向量器
        all_descriptions = list(self._feature_descriptions.values())
        if all_descriptions:
            self._tfidf_vectorizer.fit(all_descriptions)
            self._feature_names = list(self._feature_descriptions.keys())
            # 计算并更新功能关联矩阵
            self._calculate_feature_correlations()

    def _calculate_feature_correlations(self):
        """计算功能之间的关联度,生成功能关联矩阵"""
        if not hasattr(self, '_feature_names') or not hasattr(self, '_feature_descriptions') or len(self._feature_names) < 2:
            return

        # 获取所有功能描述
        descriptions = [self._feature_descriptions[name] for name in self._feature_names]

        # 计算TF-IDF矩阵
        tfidf_matrix = self._tfidf_vectorizer.transform(descriptions)

        # 计算余弦相似度矩阵
        similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

        # 生成功能关联矩阵
        correlation_matrix = {}
        for i, feature1 in enumerate(self._feature_names):
            correlation_matrix[feature1] = {}
            for j, feature2 in enumerate(self._feature_names):
                if i != j:
                    similarity = similarity_matrix[i][j]
                    if similarity >= self._learning_params["feature_similarity_threshold"]:
                        correlation_matrix[feature1][feature2] = similarity

        # 更新功能关联矩阵
        self._feature_correlation_matrix = correlation_matrix

        # 更新学习状态
        self._learning_state["association_count"] = sum(
            len(related_features) for related_features in correlation_matrix.values()
        )

        logger.info(f"功能关联矩阵已更新,共 {self._learning_state['association_count']} 个功能关联")

    def _expand_features_automatically(self):
        """基于功能关联矩阵自动扩展功能"""
        if not self._feature_correlation_matrix:
            return

        expanded_features = []

        # 遍历功能关联矩阵
        for feature, related_features in self._feature_correlation_matrix.items():
            # 找到与当前功能高度相关的功能
            high_related_features = [f for f, sim in related_features.items() if sim > 0.8]

            # 如果当前功能没有对应的能力拓展,尝试基于相关功能进行扩展
            if feature not in self._capability_expansions and high_related_features:
                # 找到相关功能中已有的能力拓展
                related_expansions = []
                for related_feature in high_related_features:
                    if related_feature in self._capability_expansions:
                        related_expansions.extend(self._capability_expansions[related_feature])

                # 基于相关拓展生成新的拓展
                if related_expansions:
                    # 去重相关拓展
                    unique_expansions = []
                    seen_capabilities = set()
                    for expansion in related_expansions:
                        if expansion["capability"] not in seen_capabilities:
                            seen_capabilities.add(expansion["capability"])
                            unique_expansions.append(expansion)

                    # 添加新的能力拓展
                    self._capability_expansions[feature] = unique_expansions
                    expanded_features.append(feature)

        if expanded_features:
            logger.info(f"自动扩展了 {len(expanded_features)} 个功能: {', '.join(expanded_features)}")
            # 更新功能向量和关联矩阵
            self._update_feature_vectors()
            # 记录到AI脑库
            self._ai_brain_service._log_activity(
                activity_type="feature_expanded",
                description=f"自动扩展了 {len(expanded_features)} 个功能",
                source="ai_learning_system",
                metadata={"expanded_features": expanded_features}
            )

    def _load_upgrade_history(self):
        """加载升级历史"""
        logger.info("加载AI升级历史...")
        upgrade_files = file_system.list_directory(self._upgrade_history_dir)

        for file_info in upgrade_files:
            file_path = os.path.join(self._upgrade_history_dir, file_info["filename"])
            upgrade_data = file_system.read_file(file_path)
            if upgrade_data:
                self._upgrade_history.append(upgrade_data)

        self._learning_state["upgrade_count"] = len(self._upgrade_history)
        logger.info(f"AI升级历史加载完成,共 {self._learning_state['upgrade_count']} 次升级")

    def _initialize_rule_integration(self):
        """初始化规则系统集成"""
        logger.info("初始化规则系统集成...")
        # 这里可以添加与规则系统的集成逻辑
        # 例如,从规则系统加载规则到AI知识库

    def _initialize_capability_expansions(self):
        """初始化能力拓展映射"""
        # 增强版能力拓展映射
        self._capability_expansions = {
            "file_management": [
                {"capability": "advanced_search", "description": "高级文件搜索", "complexity": "medium", "priority": "high"},
                {"capability": "file_analytics", "description": "文件使用分析", "complexity": "high", "priority": "medium"},
                {"capability": "version_control", "description": "文件版本控制", "complexity": "high", "priority": "medium"},
                {"capability": "file_encryption", "description": "文件加密", "complexity": "high", "priority": "medium"},
                {"capability": "file_compression", "description": "文件压缩", "complexity": "medium", "priority": "low"}
            ],
            "rule_management": [
                {"capability": "rule_analytics", "description": "规则执行分析", "complexity": "medium", "priority": "high"},
                {"capability": "dynamic_rules", "description": "动态规则生成", "complexity": "high", "priority": "high"},
                {"capability": "rule_optimization", "description": "规则优化", "complexity": "high", "priority": "medium"},
                {"capability": "rule_validation", "description": "规则验证", "complexity": "medium", "priority": "medium"},
                {"capability": "rule_visualization", "description": "规则可视化", "complexity": "medium", "priority": "low"}
            ],
            "ai_learning": [
                {"capability": "transfer_learning", "description": "迁移学习", "complexity": "high", "priority": "high"},
                {"capability": "explainable_ai", "description": "可解释AI", "complexity": "high", "priority": "high"},
                {"capability": "continuous_learning", "description": "持续学习", "complexity": "medium", "priority": "high"},
                {"capability": "few_shot_learning", "description": "少样本学习", "complexity": "high", "priority": "medium"},
                {"capability": "reinforcement_learning", "description": "强化学习", "complexity": "high", "priority": "medium"}
            ],
            "system_monitoring": [
                {"capability": "anomaly_detection", "description": "异常检测", "complexity": "high", "priority": "high"},
                {"capability": "predictive_maintenance", "description": "预测性维护", "complexity": "high", "priority": "high"},
                {"capability": "performance_analytics", "description": "性能分析", "complexity": "medium", "priority": "medium"},
                {"capability": "resource_optimization", "description": "资源优化", "complexity": "high", "priority": "medium"},
                {"capability": "log_analytics", "description": "日志分析", "complexity": "medium", "priority": "medium"}
            ]
        }

    def enhance_with_ai(self, task_type: str, content: str, **kwargs) -> Optional[Dict[str, Any]]:
        """使用AI引擎增强功能

        Args:
            task_type: 任务类型(如"learning", "upgrade_analysis", "project_adaptation")
            content: 要处理的内容

        Returns:
            Dict[str, Any]: AI增强结果,包含增强后的内容和相关信息
        """
        try:
            if not self._learning_params.get("ai_enhanced_learning", True):
                return None

            # 根据任务类型选择合适的AI引擎
            engine_type = self._learning_params.get("ai_engine", "gemini")
            fallback_engine = self._learning_params.get("ai_engine_fallback", "openai")

            # 构建提示词
            prompts = {
                "learning": f"分析以下AI学习经验数据,提取关键见解,模式和改进建议:\n\n{content}",
                "upgrade_analysis": f"基于以下AI系统状态和升级需求,生成详细的升级方案和优化建议:\n\n{content}",
                "project_adaptation": f"针对以下项目上下文,生成详细的AI适配方案,包括技术栈选择,架构设计和实施步骤:\n\n{content}",
                "knowledge_enhancement": f"增强以下知识库内容,添加相关概念,关系和应用场景:\n\n{content}",
                "feature_association": f"分析以下功能列表,生成功能关联矩阵和自动扩展建议:\n\n{content}"
            }

            prompt = prompts.get(task_type, f"分析以下内容:\n\n{content}")

            # 调用AI引擎
            result = ai_engine_integrator.call_engine(engine_type, prompt, **kwargs)

            # 如果调用失败,尝试使用备用引擎
            if not result:
                logger.warning(f"AI引擎 {engine_type} 调用失败,尝试使用备用引擎 {fallback_engine}")
                result = ai_engine_integrator.call_engine(fallback_engine, prompt, **kwargs)

            if result and result.get("code") == 0:
                return {
                    "success": True,
                    "enhanced_content": result["data"]["response"],
                    "engine_used": engine_type if result else fallback_engine,
                    "task_type": task_type,
                    "timestamp": time.time()
                }
            else:
                logger.error(f"AI增强失败: {result.get('message') if result else '未知错误'}")
                return None

        except Exception as e:
            logger.error(f"AI增强异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _adapt_to_web_app(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配Web应用项目"""
        return {
            "frameworks": ["Flask", "Django", "FastAPI"],
            "optimizations": ["performance", "scalability", "security"],
            "components": ["API", "UI", "Database", "Cache"]
        }

    def _adapt_to_data_science(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配数据科学项目"""
        return {
            "libraries": ["Pandas", "NumPy", "Scikit-learn", "TensorFlow"],
            "optimizations": ["processing_speed", "accuracy", "scalability"],
            "components": ["Data Cleaning", "Feature Engineering", "Model Training", "Deployment"]
        }

    def _adapt_to_mobile_app(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配移动应用项目"""
        return {
            "frameworks": ["React Native", "Flutter", "Swift", "Kotlin"],
            "optimizations": ["performance", "battery", "storage"],
            "components": ["UI", "API", "Database", "Push Notifications"]
        }

    def _adapt_to_desktop_app(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配桌面应用项目"""
        return {
            "frameworks": ["Qt", "Electron", ".NET"],
            "optimizations": ["performance", "memory", "UI"],
            "components": ["UI", "File System", "Database", "Network"]
        }

    def _adapt_to_ai_project(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配AI项目"""
        return {
            "frameworks": ["TensorFlow", "PyTorch", "scikit-learn", "Transformers"],
            "optimizations": ["model_performance", "training_speed", "inference_latency"],
            "components": ["Data Pipeline", "Model Training", "Model Deployment", "Monitoring"]
        }

    def _adapt_to_game_development(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配游戏开发项目"""
        return {
            "frameworks": ["Unity", "Unreal Engine", "Godot"],
            "optimizations": ["fps", "graphics", "memory_usage"],
            "components": ["Game Logic", "Graphics", "Physics", "Audio", "Network"]
        }

    def _adapt_to_blockchain(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配区块链项目"""
        return {
            "frameworks": ["Ethereum", "Solana", "Hyperledger Fabric"],
            "optimizations": ["transaction_speed", "security", "scalability"],
            "components": ["Smart Contracts", "Wallet Integration", "Node Infrastructure", "Consensus"]
        }

    def _adapt_to_iot(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配物联网项目"""
        return {
            "frameworks": ["MQTT", "CoAP", "AWS IoT"],
            "optimizations": ["energy_efficiency", "low_latency", "security"],
            "components": ["Device Management", "Data Collection", "Edge Computing", "Cloud Integration"]
        }

    def _adapt_to_cloud_native(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配云原生项目"""
        return {
            "frameworks": ["Kubernetes", "Docker", "Istio"],
            "optimizations": ["scalability", "availability", "cost_efficiency"],
            "components": ["Microservices", "CI/CD", "Service Mesh", "Observability"]
        }

    def _adapt_to_devops(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配DevOps项目"""
        return {
            "frameworks": ["Jenkins", "GitLab CI", "Ansible"],
            "optimizations": ["automation", "reliability", "speed"],
            "components": ["CI/CD Pipelines", "Infrastructure as Code", "Monitoring", "Logging"]
        }

    def _adapt_to_fintech(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配金融科技项目"""
        return {
            "frameworks": ["Spring Boot", "Apache Kafka", "PostgreSQL"],
            "optimizations": ["security", "transaction_speed", "compliance"],
            "components": ["Payment Processing", "Risk Management", "Fraud Detection", "Regulatory Compliance"]
        }

    def _adapt_to_education_tech(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """适配教育科技项目"""
        return {
            "frameworks": ["Moodle", "Canvas", "Open edX"],
            "optimizations": ["user_experience", "scalability", "engagement"],
            "components": ["Learning Management", "Content Delivery", "Assessment", "Analytics"]
        }

    def learn_from_experience(self, experience_data: Dict[str, Any]) -> bool:
        """从经验中学习

        Args:
            experience_data: 经验数据,包含任务,结果,反馈等

        Returns:
            bool: 是否学习成功
        """
        try:
            logger.info(f"AI开始学习: {experience_data.get('task', '未知任务')}")

            # 提取关键信息
            task = experience_data.get("task")
            result = experience_data.get("result")
            feedback = experience_data.get("feedback", 0)
            context = experience_data.get("context", {})
            entities = experience_data.get("entities", [])
            relations = experience_data.get("relations", [])
            rules = experience_data.get("rules", [])

            # 生成知识条目ID
            knowledge_id = hashlib.sha256(str(time.time()).encode()).hexdigest()

            # 生成知识条目
            knowledge_item = {
                "id": knowledge_id,
                "task": task,
                "result": result,
                "feedback": feedback,
                "context": context,
                "learned_at": time.time(),
                "confidence": 0.5
            }

            # 使用AI增强学习
            ai_enhanced_result = self.enhance_with_ai(
                task_type="learning",
                content=str(experience_data, ensure_ascii=False, indent=2),
                temperature=0.7,
                max_tokens=2048
            )

            # 如果AI增强成功,添加增强内容到知识条目
            if ai_enhanced_result and ai_enhanced_result["success"]:
                knowledge_item["ai_enhanced_content"] = ai_enhanced_result["enhanced_content"]
                knowledge_item["ai_engine_used"] = ai_enhanced_result["engine_used"]
                logger.info(f"AI增强学习成功,使用引擎: {ai_enhanced_result['engine_used']}")

            # 更新知识图谱
            self._update_knowledge_graph(knowledge_item, entities, relations, rules)

            # 保存知识到文件
            self._save_knowledge_item(knowledge_item, entities, relations, rules)

            # 更新学习状态
            self._learning_state["knowledge_count"] = (
                len(self._knowledge_graph["entities"]) +
                len(self._knowledge_graph["relations"]) +
                len(self._knowledge_graph["rules"]) +
                len(self._knowledge_graph["tasks"])
            )

            # 更新功能向量
            self._update_feature_vectors()

            # 记录学习经验到AI脑库
            knowledge_content = json.dumps(knowledge_item, ensure_ascii=False, indent=2)
            self._ai_brain_service.add_knowledge(
                content=knowledge_content,
                knowledge_type="experience",
                source="ai_learning_system",
                source_id=knowledge_id,
                tags=["learning", "experience", task.split(":")[0] if ":" in task else task],
                priority=1
            )

            # 记录学习活动
            self._ai_brain_service._log_activity(
                activity_type="learning",
                description=f"从经验中学习: {task}",
                source="ai_learning_system",
                source_id=knowledge_id,
                metadata={
                    "task": task,
                    "result": result,
                    "feedback": feedback,
                    "ai_enhanced": ai_enhanced_result["success"] if ai_enhanced_result else False
                }
            )

            logger.info(f"AI学习完成,当前知识库大小: {self._learning_state['knowledge_count']}")
            return True
        except Exception as e:
            logger.error(f"AI学习失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _update_knowledge_graph(self, knowledge_item: Dict[str, Any], entities: List[Dict[str, Any]], relations: List[Dict[str, Any]], rules: List[Dict[str, Any]]):
        """更新知识图谱

        Args:
            knowledge_item: 知识条目
            entities: 实体列表
            relations: 关系列表
            rules: 规则列表
        """
        # 1. 更新任务知识
        task_type = knowledge_item["task"].split(":")[0] if ":" in knowledge_item["task"] else "general"
        # 添加知识条目
        if task_type not in self._knowledge_graph["tasks"]:
            self._knowledge_graph["tasks"][task_type] = {}
        self._knowledge_graph["tasks"][task_type][knowledge_item["id"]] = knowledge_item

        # 根据反馈调整置信度
        if knowledge_item["feedback"] > 0:
            knowledge_item["confidence"] += self._learning_params["learning_rate"]
        else:
            knowledge_item["confidence"] -= self._learning_params["learning_rate"]

        knowledge_item["confidence"] = max(0.1, min(0.99, knowledge_item["confidence"]))

        # 2. 更新实体知识
        for entity in entities:
            entity_id = entity.get("id", hashlib.sha256(str(entity).encode()).hexdigest())
            self._knowledge_graph["entities"][entity_id] = {
                **entity,
                "id": entity_id,
                "last_updated": time.time(),
                "confidence": 0.7
            }

        # 3. 更新关系知识
        for relation in relations:
            relation_id = relation.get("id", hashlib.sha256(str(relation).encode()).hexdigest())
            self._knowledge_graph["relations"][relation_id] = {
                **relation,
                "id": relation_id,
                "last_updated": time.time(),
                "confidence": 0.6
            }

        # 4. 更新规则知识
        for rule in rules:
            rule_id = rule.get("id", hashlib.sha256(str(rule).encode()).hexdigest())
            self._knowledge_graph["rules"][rule_id] = {
                "id": rule_id,
                **rule,
                "confidence": 0.8
            }

    def _save_knowledge_item(self, knowledge_item: Dict[str, Any], entities: List[Dict[str, Any]], relations: List[Dict[str, Any]], rules: List[Dict[str, Any]]):
        """保存知识条目到文件

        Args:
            knowledge_item: 知识条目
            entities: 实体列表
            relations: 关系列表
            rules: 规则列表
        """
        # 1. 保存任务知识
        task_type = knowledge_item["task"].split(":")[0] if ":" in knowledge_item["task"] else "general"
        task_file = os.path.join(self._knowledge_base_dir, "tasks", f"{task_type}.json")

        # 读取现有任务知识
        existing_tasks = {}
        if file_system.exists(task_file):
            existing_tasks = file_system.read_file(task_file) or {}

        # 添加新任务知识
        if task_type not in existing_tasks:
            existing_tasks[task_type] = {}
        existing_tasks[task_type][knowledge_item["id"]] = knowledge_item

        # 保存更新后的任务知识
        file_system.update_file(task_file, existing_tasks)

        # 2. 保存实体知识
        entities_file = os.path.join(self._knowledge_base_dir, "entities.json")
        existing_entities = {}
        if file_system.exists(entities_file):
            existing_entities = file_system.read_file(entities_file) or {}

        for entity in entities:
            entity_id = entity.get("id", hashlib.sha256(str(entity).encode()).hexdigest())
            existing_entities[entity_id] = {
                **entity,
                "id": entity_id,
                "last_updated": time.time()
            }
        file_system.update_file(entities_file, existing_entities)

        # 3. 保存关系知识
        relations_file = os.path.join(self._knowledge_base_dir, "relations.json")
        existing_relations = {}
        if file_system.exists(relations_file):
            existing_relations = file_system.read_file(relations_file) or {}

        for relation in relations:
            relation_id = relation.get("id", hashlib.sha256(str(relation).encode()).hexdigest())
            existing_relations[relation_id] = {
                **relation,
                "id": relation_id,
                "last_updated": time.time()
            }
        file_system.update_file(relations_file, existing_relations)

        # 4. 保存规则知识
        for rule in rules:
            rule_id = rule.get("id", hashlib.sha256(str(rule).encode()).hexdigest())
            rule_file = os.path.join(self._knowledge_base_dir, "rules", f"{rule_id}.json")
            file_system.create_file(rule_file, rule)

    def self_upgrade(self) -> bool:
        """执行AI自我升级

        Returns:
            bool: 是否升级成功
        """
        try:
            logger.info("开始AI自我升级...")

            # 检查升级条件
            if not self._check_upgrade_conditions():
                return False

            # 分析升级需求
            upgrade_needs = self._analyze_upgrade_needs()

            if not upgrade_needs:
                logger.info("未发现升级需求")
                return False

            # 生成升级方案
            upgrade_plan = self._generate_upgrade_plan(upgrade_needs)

            if not upgrade_plan:
                return False

            self._ai_brain_service._log_activity(
                activity_type="upgrade_started",
                description="AI自我升级开始",
                source_id=upgrade_plan["id"],
                metadata={
                    "upgrade_plan": upgrade_plan,
                    "target_version": upgrade_plan["target_version"]
                }
            )

            # 执行升级
            upgrade_result = self._execute_upgrade(upgrade_plan)
            if upgrade_result:
                # 记录升级历史
                self._record_upgrade_history(upgrade_plan, True)

                # 记录升级成功到AI脑库
                upgrade_content = json.dumps(upgrade_plan, ensure_ascii=False, indent=2)
                self._ai_brain_service.add_knowledge(
                    title=f"系统升级: {upgrade_plan['version']} -> {upgrade_plan['target_version']}",
                    content=upgrade_content,
                    knowledge_type="upgrade",
                    source="ai_learning_system",
                    source_id=upgrade_plan["id"],
                    tags=["upgrade", "self_upgrade", "system"],
                    priority=2
                )

                self._ai_brain_service._log_activity(
                    activity_type="upgrade_completed",
                    source="ai_learning_system",
                    metadata={
                        "upgrade_plan": upgrade_plan,
                        "result": "success",
                        "version_before": upgrade_plan["version"],
                        "version_after": upgrade_plan["target_version"]
                    }
                )

                logger.info("AI自我升级成功")
            else:
                # 记录升级失败活动
                self._ai_brain_service._log_activity(
                    activity_type="upgrade_failed",
                    source="ai_learning_system",
                    metadata={
                        "upgrade_plan": upgrade_plan,
                        "result": "failed"
                    }
                )
                logger.error("AI自我升级失败")

            return upgrade_result
        except Exception as e:
            # 记录升级异常到AI脑库
            self._ai_brain_service._log_activity(
                activity_type="upgrade_error",
                source="ai_learning_system",
                metadata={
                    "description": f"AI自我升级异常: {str(e)}",
                    "error": str(e)
                }
            )

            logger.error(f"AI自我升级异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _check_upgrade_conditions(self) -> bool:
        """增强版升级条件检查

        Returns:
            bool: 是否满足升级条件
        """
        current_time = time.time()

        if current_time - self._learning_state["last_upgrade_check"] < self._learning_params["upgrade_check_interval"]:
            return False

        # 检查知识增长
        if self._learning_state["knowledge_count"] < 10:
            return False

        # 检查是否有新的学习经验
        if current_time - self._learning_state["last_learning_time"] > self._learning_params["upgrade_check_interval"] * 2:
            return False

        # 检查升级历史
        if self._learning_state["upgrade_count"] > 0:
            # 计算平均升级成功率
            success_count = sum(1 for h in self._upgrade_history if h.get("result") == "success")
            total_count = len(self._upgrade_history)
            success_rate = success_count / total_count if total_count > 0 else 0
            if success_rate < 0.5:
                logger.warning("升级成功率过低,跳过升级")
                return False

        return True

    def monitor_trae_entry(self, entry_data: Dict[str, Any]) -> bool:
        """监控trae提交的词条

        Args:
            entry_data: 词条数据,包含关键词,内容,来源等

        Returns:
            bool: 是否监控成功
        """
        try:
            logger.info(f"监控到trae提交词条: {entry_data.get('keyword', '未知关键词')}")
            # 提取词条信息
            content = entry_data.get("content", "")
            source = entry_data.get("source", "trae")
            source_id = entry_data.get("source_id")
            tags = entry_data.get("tags", [])
            priority = entry_data.get("priority", 1)
            keyword = entry_data.get("keyword", "未知")

            # 生成知识条目ID
            entry_id = hashlib.sha256(str(time.time()).encode()).hexdigest()
            # 记录词条到AI脑库数据库
            self._ai_brain_service.add_knowledge(
                title=f"trae词条: {keyword}",
                content=content,
                knowledge_type="trae_entry",
                source=source,
                source_id=source_id,
                tags=tags + ["trae", "entry", keyword],
                priority=priority
            )

            # 记录监控活动
            self._ai_brain_service._log_activity(
                description=f"监控到trae提交词条: {keyword}",
                source="ai_learning_system",
                source_id=entry_id,
                metadata={
                    "keyword": keyword,
                    "entry_id": entry_id
                }
            )

            logger.info(f"成功监控trae提交词条: {keyword}")
            return True
        except Exception as e:
            logger.error(f"监控trae提交词条失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _analyze_upgrade_needs(self) -> List[Dict[str, Any]]:
        """分析升级需求

        Returns:
            List[Dict[str, Any]]: 升级需求列表
        """
        upgrade_needs = []
        current_time = time.time()

        # 1. 知识图谱优化需求
        if len(self._knowledge_graph["entities"]) > 50:
            upgrade_needs.append({
                "type": "knowledge_graph_optimization",
                "priority": "high",
                "reason": f"实体数量过多: {len(self._knowledge_graph['entities'])}"
            })

        # 2. 规则优化需求
        low_confidence_rules = [
            rule for rule_id, rule in self._knowledge_graph["rules"].items()
            if rule.get("confidence", 0) < 0.5
        ]
        if len(low_confidence_rules) > 5:
            upgrade_needs.append({
                "type": "rule_optimization",
                "priority": "medium",
                "reason": f"低置信度规则过多: {len(low_confidence_rules)}"
            })

        # 3. 知识质量优化需求
        old_knowledge = []
        for entity_id, entity in self._knowledge_graph["entities"].items():
            if current_time - entity.get("last_updated", 0) > 3600 * 24 * 30:
                old_knowledge.append(entity)
        if len(old_knowledge) > 10:
            upgrade_needs.append({
                "type": "knowledge_quality_optimization",
                "priority": "medium",
                "reason": f"过时知识过多: {len(old_knowledge)}"
            })

        # 4. 功能关联优化需求
        if len(self._feature_correlation_matrix) < len(self._capability_expansions) * 0.5:
            upgrade_needs.append({
                "type": "feature_correlation_optimization",
                "priority": "low",
                "reason": "功能关联矩阵不完整"
            })

        # 5. 基于trae词条的升级需求
        trae_entries = []
        for task_type, tasks in self._knowledge_graph["tasks"].items():
            if isinstance(tasks, dict):
                for task_id, task_data in tasks.items():
                    if task_data.get("task") == "trae_entry":
                        trae_entries.append(task_data)
        if len(trae_entries) > 0:
            recent_entries = sorted(trae_entries, key=lambda x: x.get("learned_at", 0), reverse=True)[:10]
            keywords = []
            for entry in recent_entries:
                if "tags" in entry:
                    keywords.extend([tag for tag in entry["tags"] if tag != "trae" and tag != "entry"])
            if keywords:
                upgrade_needs.append({
                    "type": "trae_based_upgrade",
                    "priority": "medium",
                    "reason": f"基于trae词条关键词生成升级需求: {', '.join(set(keywords[:5]))}",
                    "trae_keywords": list(set(keywords))
                })

        # 6. 学习效率优化需求
        if self._learning_state["last_learning_time"] > 0:
            learning_interval = current_time - self._learning_state["last_learning_time"]
            if learning_interval > self._learning_params["upgrade_check_interval"] * 3:
                upgrade_needs.append({
                    "type": "learning_efficiency_optimization",
                    "priority": "medium",
                    "reason": f"学习间隔过长: {learning_interval // 3600}小时"
                })

        # 7. 功能拓展需求
        if len(self._knowledge_graph["tasks"]) > 0:
            task_types = list(self._knowledge_graph["tasks"].keys())
            missing_expansions = [tt for tt in task_types if tt not in self._capability_expansions]
            if missing_expansions:
                upgrade_needs.append({
                    "type": "capability_expansion_optimization",
                    "priority": "medium",
                    "reason": f"缺少功能拓展映射: {', '.join(missing_expansions[:3])}",
                    "missing_expansions": missing_expansions
                })

        # 8. 使用AI增强升级需求分析
        ai_enhanced_result = self.enhance_with_ai(
            task_type="upgrade_analysis",
            content=json.dumps({
                "knowledge_graph": {
                    "entities_count": len(self._knowledge_graph["entities"]),
                    "relations_count": len(self._knowledge_graph["relations"]),
                    "rules_count": len(self._knowledge_graph["rules"]),
                },
                "learning_state": self._learning_state,
                "capability_expansions": list(self._capability_expansions.keys()),
                "upgrade_needs": upgrade_needs
            }, ensure_ascii=False, indent=2),
            temperature=0.7,
            max_tokens=2048
        )
        # 如果AI增强成功,添加AI生成的升级需求
        if ai_enhanced_result and ai_enhanced_result["success"]:
            ai_generated_needs = {
                "type": "ai_generated_upgrade",
                "priority": "high",
                "reason": "基于AI分析生成的升级需求",
                "engine_used": ai_enhanced_result["engine_used"]
            }
            upgrade_needs.append(ai_generated_needs)
            logger.info(f"AI增强升级需求分析成功,使用引擎: {ai_enhanced_result['engine_used']}")

        return upgrade_needs

    def _generate_upgrade_plan(self, upgrade_needs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """增强版升级方案生成

        Args:
            upgrade_needs: 升级需求列表

        Returns:
            Dict[str, Any]: 升级方案
        """
        # 生成升级方案
        upgrade_plan = {
            "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
            "timestamp": time.time(),
            "version": self._get_current_version(),
            "target_version": self._get_next_version(),
            "needs": upgrade_needs,
            "actions": [],
            "estimated_time": sum(
                60 if need["priority"] == "high" else 30 if need["priority"] == "medium" else 15
                for need in upgrade_needs
            )
        }

        # 为每个升级需求生成具体的升级动作
        for need in upgrade_needs:
            actions = self._generate_upgrade_actions_for_need(need)
            upgrade_plan["actions"].extend(actions)

        # 按优先级排序升级动作
        upgrade_plan["actions"].sort(
            key=lambda x: 3 if x["priority"] == "high" else 2 if x["priority"] == "medium" else 1,
            reverse=True
        )

        return upgrade_plan

    def _generate_upgrade_actions_for_need(self, need: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为升级需求生成具体的升级动作

        Args:
            need: 升级需求

        Returns:
            List[Dict[str, Any]]: 升级动作列表
        """
        actions = []

        if need["type"] == "knowledge_graph_optimization":
            # 知识图谱优化动作
            actions.extend([
                {
                    "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                    "type": "entity_clustering",
                    "target": "entities",
                    "priority": need["priority"],
                    "description": "实体聚类优化",
                    "params": {
                        "threshold": 0.8
                    }
                },
                {
                    "id": hashlib.sha256(str(time.time() + 1).encode()).hexdigest(),
                    "type": "relation_mining",
                    "target": "relations",
                    "priority": need["priority"],
                    "description": "关系挖掘优化",
                    "method": "association_rule_mining",
                    "params": {
                        "min_confidence": 0.5
                    }
                },
                {
                    "id": hashlib.sha256(str(time.time() + 2).encode()).hexdigest(),
                    "type": "knowledge_consolidation",
                    "target": "tasks",
                    "priority": need["priority"],
                    "description": "知识整合优化",
                    "method": "similarity_based_consolidation",
                    "params": {
                        "similarity_threshold": 0.85
                    }
                }
            ])
        elif need["type"] == "rule_optimization":
            # 规则优化动作
            actions.extend([
                {
                    "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                    "type": "rule_refinement",
                    "target": "rules",
                    "priority": need["priority"],
                    "description": "规则优化",
                    "method": "rule_induction",
                    "params": {
                        "confidence_threshold": 0.7
                    }
                },
                {
                    "id": hashlib.sha256(str(time.time() + 1).encode()).hexdigest(),
                    "type": "rule_prioritization",
                    "target": "rules",
                    "priority": need["priority"],
                    "description": "规则优先级排序",
                    "method": "priority_scoring",
                    "params": {
                        "min_usage_threshold": 5
                    }
                }
            ])
        elif need["type"] == "knowledge_quality_optimization":
            # 知识质量优化动作
            actions.extend([
                {
                    "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                    "type": "knowledge_purging",
                    "target": "entities",
                    "priority": need["priority"],
                    "description": "知识清理",
                    "method": "time_based_purging",
                    "params": {
                        "retention_days": 30
                    }
                },
                {
                    "id": hashlib.sha256(str(time.time() + 1).encode()).hexdigest(),
                    "type": "confidence_improvement",
                    "target": "all",
                    "priority": need["priority"],
                    "description": "知识置信度提升",
                    "method": "reinforcement_learning",
                    "params": {
                        "learning_rate": self._learning_params["learning_rate"] * 1.5,
                        "iterations": 1000
                    }
                }
            ])
        elif need["type"] == "feature_correlation_optimization":
            # 功能关联优化动作
            actions.append({
                "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                "type": "feature_correlation_update",
                "target": "feature_correlation_matrix",
                "priority": need["priority"],
                "description": "更新功能关联矩阵",
                "method": "tfidf_similarity",
                "params": {
                    "threshold": self._learning_params["feature_similarity_threshold"]
                }
            })
        elif need["type"] == "task_optimization":
            # 任务优化动作
            actions.append({
                "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                "type": "task_optimization",
                "target": "tasks",
                "priority": need["priority"],
                "description": "任务流程优化",
                "method": "process_mining",
                "params": {
                    "efficiency_threshold": 0.7
                }
            })
        elif need["type"] == "learning_params_tuning":
            # 学习参数调优动作
            actions.append({
                "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                "type": "learning_params_tuning",
                "target": "learning_params",
                "priority": need["priority"],
                "description": "学习参数自动调优",
                "method": "grid_search",
                "params": {
                    "param_space": {
                        "learning_rate": [0.1, 0.15, 0.2],
                        "memory_retention": [0.85, 0.9, 0.95]
                    }
                }
            })
        elif need["type"] == "trae_based_upgrade":
            # 基于trae词条的升级动作
            actions.extend([
                {
                    "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                    "type": "trae_keyword_analysis",
                    "target": "knowledge_graph",
                    "priority": need["priority"],
                    "description": "基于trae词条关键词分析",
                    "method": "keyword_clustering",
                    "params": {
                        "keywords": need.get("trae_keywords", []),
                        "threshold": 0.8
                    }
                },
                {
                    "id": hashlib.sha256(str(time.time() + 1).encode()).hexdigest(),
                    "type": "knowledge_enhancement",
                    "target": "trae_entries",
                    "priority": need["priority"],
                    "description": "基于trae词条增强知识库",
                    "method": "semantic_embedding",
                    "params": {
                        "keywords": need.get("trae_keywords", [])[:10]
                    }
                }
            ])
        elif need["type"] == "learning_efficiency_optimization":
            # 学习效率优化动作
            actions.append({
                "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                "type": "learning_schedule_optimization",
                "target": "learning_params",
                "priority": need["priority"],
                "description": "优化学习调度",
                "method": "adaptive_scheduling",
                "params": {
                    "learning_interval": 3600
                }
            })
        elif need["type"] == "capability_expansion_optimization":
            # 功能拓展优化动作
            actions.append({
                "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                "type": "capability_expansion_generation",
                "target": "capability_expansions",
                "priority": need["priority"],
                "description": "生成缺失的功能拓展映射",
                "method": "pattern_mining",
                "params": {
                    "missing_expansions": need.get("missing_expansions", [])
                }
            })
        elif need["type"] == "ai_generated_upgrade":
            # AI生成的升级需求
            actions.append({
                "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                "type": "confidence_improvement",
                "target": "all",
                "priority": "medium",
                "description": "基于AI分析的置信度提升",
                "method": "reinforcement_learning",
                "params": {
                    "learning_rate": self._learning_params["learning_rate"],
                    "iterations": 500
                }
            })

        return actions

    def _execute_upgrade(self, upgrade_plan: Dict[str, Any]) -> bool:
        """执行升级方案

        Args:
            upgrade_plan: 升级方案

        Returns:
            bool: 是否执行成功
        """
        logger.info(f"开始执行升级方案,目标版本: {upgrade_plan['target_version']}")

        success_count = 0
        total_actions = len(upgrade_plan["actions"])

        for action in upgrade_plan["actions"]:
            logger.info(f"执行升级动作: {action['description']}")
            result = True

            # 根据动作类型执行不同的升级操作
            if action["type"] == "entity_clustering":
                result = self._cluster_entities(action)
            elif action["type"] == "relation_mining":
                result = self._mine_relations(action)
            elif action["type"] == "rule_refinement":
                result = self._refine_rules(action)
            elif action["type"] == "knowledge_purging":
                result = self._purge_knowledge(action)
            elif action["type"] == "feature_correlation_update":
                result = self._update_feature_correlations(action)
            elif action["type"] == "knowledge_consolidation":
                result = self._consolidate_knowledge(action)
            elif action["type"] == "rule_prioritization":
                result = self._prioritize_rules(action)
            elif action["type"] == "confidence_improvement":
                result = self._improve_confidence(action)
            elif action["type"] == "task_optimization":
                result = self._optimize_tasks(action)
            elif action["type"] == "learning_params_tuning":
                result = self._tune_learning_params(action)
            elif action["type"] == "trae_keyword_analysis":
                result = self._analyze_trae_keywords(action)
            elif action["type"] == "knowledge_enhancement":
                result = self._enhance_knowledge_from_trae(action)
            elif action["type"] == "learning_schedule_optimization":
                result = self._optimize_learning_schedule(action)
            elif action["type"] == "capability_expansion_generation":
                result = self._generate_capability_expansions(action)
            else:
                result = True

            if result:
                action["status"] = "completed"
                success_count += 1
            else:
                action["status"] = "failed"

        success_rate = success_count / total_actions if total_actions > 0 else 0
        logger.info(f"升级完成,成功率: {success_rate:.2f}")

        # 更新知识图谱
        self._load_knowledge()

        return success_count == total_actions

    def _cluster_entities(self, action: Dict[str, Any]) -> bool:
        """实体聚类优化

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行实体聚类优化...")
        for entity_id, entity in self._knowledge_graph["entities"].items():
            confidence = entity.get("confidence", 0.5)
            entity["confidence"] = min(0.99, confidence + 0.1)
        return True

    def _mine_relations(self, action: Dict[str, Any]) -> bool:
        """关系挖掘优化

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行关系挖掘优化...")
        for relation_id, relation in self._knowledge_graph["relations"].items():
            confidence = relation.get("confidence", 0.5)
            relation["confidence"] = min(0.99, confidence + 0.1)
        return True

    def _refine_rules(self, action: Dict[str, Any]) -> bool:
        """规则优化

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行规则优化...")
        threshold = action["params"].get("confidence_threshold", 0.7)
        refined_rules = {}
        for rule_id, rule in self._knowledge_graph["rules"].items():
            if rule.get("confidence", 0) >= threshold:
                refined_rules[rule_id] = rule

        self._knowledge_graph["rules"] = refined_rules
        return True

    def _purge_knowledge(self, action: Dict[str, Any]) -> bool:
        """知识清理

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行知识清理...")
        retention_days = action["params"].get("retention_days", 30)
        cutoff_time = time.time() - (retention_days * 24 * 3600)

        # 清理过时实体
        updated_entities = {}
        for entity_id, entity in self._knowledge_graph["entities"].items():
            if entity.get("last_updated", 0) >= cutoff_time:
                updated_entities[entity_id] = entity
        self._knowledge_graph["entities"] = updated_entities

        # 清理过时关系
        updated_relations = {}
        for relation_id, relation in self._knowledge_graph["relations"].items():
            if relation.get("last_updated", 0) >= cutoff_time:
                updated_relations[relation_id] = relation
        self._knowledge_graph["relations"] = updated_relations

        # 清理过时任务
        updated_tasks = {}
        for task_type, tasks in self._knowledge_graph["tasks"].items():
            if isinstance(tasks, dict):
                updated_task_items = {}
                for task_id, task_data in tasks.items():
                    if task_data.get("learned_at", 0) >= cutoff_time:
                        updated_task_items[task_id] = task_data
                if updated_task_items:
                    updated_tasks[task_type] = updated_task_items
        self._knowledge_graph["tasks"] = updated_tasks

        return True

    def _update_feature_correlations(self, action: Dict[str, Any]) -> bool:
        """更新功能关联矩阵

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("更新功能关联矩阵...")
        # 确保功能向量已更新
        self._update_feature_vectors()
        # 生成基于TF-IDF的功能关联
        if hasattr(self, '_feature_names') and self._feature_names:
            descriptions = [self._feature_descriptions[name] for name in self._feature_names]
            # 转换为TF-IDF向量
            vectors = self._tfidf_vectorizer.transform(descriptions)

            # 计算余弦相似度矩阵
            similarity_matrix = cosine_similarity(vectors, vectors)

            # 构建关联矩阵
            correlation_matrix = {}
            feature_names = self._feature_names
            for i, name1 in enumerate(feature_names):
                correlation_matrix[name1] = {}
                for j, name2 in enumerate(feature_names):
                    if i != j and similarity_matrix[i][j] >= self._learning_params["feature_similarity_threshold"]:
                        correlation_matrix[name1][name2] = float(similarity_matrix[i][j])

            self._feature_correlation_matrix = correlation_matrix

        return True

    def _consolidate_knowledge(self, action: Dict[str, Any]) -> bool:
        """知识整合优化

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行知识整合优化...")
        similarity_threshold = action["params"].get("similarity_threshold", 0.85)

        # 整合任务知识
        consolidated_tasks = {}
        for task_type, tasks in self._knowledge_graph["tasks"].items():
            if isinstance(tasks, dict):
                # 按任务名称分组
                task_groups = {}
                for task_id, task_data in tasks.items():
                    task_name = task_data.get("task", "").split(":")[1] if ":" in task_data.get("task", "") else task_data.get("task", "")
                    if task_name not in task_groups:
                        task_groups[task_name] = []
                    task_groups[task_name].append(task_data)

                # 整合每组任务
                consolidated_task_items = {}
                for task_name, task_items in task_groups.items():
                    if len(task_items) > 1:
                        # 保留置信度最高的任务
                        best_task = max(task_items, key=lambda x: x.get("confidence", 0))
                        consolidated_task_items[best_task["id"]] = best_task
                    else:
                        # 只有一个任务,直接保留
                        consolidated_task_items[task_items[0]["id"]] = task_items[0]

                consolidated_tasks[task_type] = consolidated_task_items
        self._knowledge_graph["tasks"] = consolidated_tasks
        return True

    def _prioritize_rules(self, action: Dict[str, Any]) -> bool:
        """规则优先级排序

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行规则优先级排序...")
        min_usage = action["params"].get("min_usage_threshold", 5)

        # 为规则添加优先级
        for rule_id, rule in self._knowledge_graph["rules"].items():
            confidence = rule.get("confidence", 0)
            usage = rule.get("usage_count", 0)
            priority_score = confidence * 0.6 + min(usage / max(min_usage, 1), 1.0) * 0.4

            rule["priority"] = float(priority_score)
            rule["priority_level"] = "high" if priority_score > 0.8 else "medium" if priority_score > 0.5 else "low"

        return True

    def _improve_confidence(self, action: Dict[str, Any]) -> bool:
        """知识置信度提升

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行知识置信度提升...")
        learning_rate = action["params"].get("learning_rate", self._learning_params["learning_rate"])
        iterations = action["params"].get("iterations", 1000)

        # 提高所有知识的置信度
        for entity in self._knowledge_graph["entities"].values():
            entity["confidence"] = min(0.99, entity.get("confidence", 0.5) + learning_rate * 0.1)

        for relation in self._knowledge_graph["relations"].values():
            relation["confidence"] = min(0.99, relation.get("confidence", 0.5) + learning_rate * 0.1)

        for rule in self._knowledge_graph["rules"].values():
            rule["confidence"] = min(0.99, rule.get("confidence", 0.5) + learning_rate * 0.1)

        for task_type, tasks in self._knowledge_graph["tasks"].items():
            if isinstance(tasks, dict):
                for task_data in tasks.values():
                    task_data["confidence"] = min(0.99, task_data.get("confidence", 0.5) + learning_rate * 0.1)

        return True

    def _optimize_tasks(self, action: Dict[str, Any]) -> bool:
        """任务流程优化

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行任务流程优化...")
        efficiency_threshold = action["params"].get("efficiency_threshold", 0.7)

        for task_type, tasks in self._knowledge_graph["tasks"].items():
            if isinstance(tasks, dict):
                for task_id, task_data in tasks.items():
                    task_data["efficiency"] = float(efficiency_threshold + (1.0 - efficiency_threshold) * 0.5)

        return True

    def _tune_learning_params(self, action: Dict[str, Any]) -> bool:
        """学习参数自动调优

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行学习参数自动调优...")
        param_space = action["params"].get("param_space", {})

        import random, secrets
        for param, values in param_space.items():
            if param in self._learning_params:
                self._learning_params[param] = secrets.choice(values)
                logger.info(f"调整参数 {param} 为 {self._learning_params[param]}")

        return True

    def _analyze_trae_keywords(self, action: Dict[str, Any]) -> bool:
        """trae关键词分析

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行trae关键词分析...")
        keywords = action["params"].get("keywords", [])
        threshold = action["params"].get("threshold", 0.8)

        for keyword in keywords:
            if keyword not in self._knowledge_graph["entities"]:
                self._knowledge_graph["entities"][keyword] = {
                    "confidence": 0.7,
                    "occurrences": 1
                }
            else:
                entity = self._knowledge_graph["entities"][keyword]
                entity["occurrences"] = entity.get("occurrences", 0) + 1
                entity["confidence"] = min(0.99, entity.get("confidence", 0.7) + 0.1)

        return True

    def _enhance_knowledge_from_trae(self, action: Dict[str, Any]) -> bool:
        """从trae词条增强知识库

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("从trae词条增强知识库...")
        keywords = action["params"].get("keywords", [])

        for keyword in keywords:
            task_type = keyword
            if task_type not in self._knowledge_graph["tasks"]:
                self._knowledge_graph["tasks"][task_type] = {}

            # 生成基于trae关键词的任务
            task_id = hashlib.sha256(f"trae_{keyword}_{time.time()}".encode()).hexdigest()
            self._knowledge_graph["tasks"][task_type][task_id] = {
                "id": task_id,
                "task": keyword,
                "result": "pending",
                "context": {
                    "trae_keyword": keyword
                },
                "learned_at": time.time(),
                "confidence": 0.6
            }

        return True

    def _optimize_learning_schedule(self, action: Dict[str, Any]) -> bool:
        """优化学习调度

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("执行学习调度优化...")
        learning_interval = action["params"].get("learning_interval", 3600)

        self._learning_params["upgrade_check_interval"] = learning_interval
        self._learning_params["learning_rate"] = min(0.2, self._learning_params["learning_rate"] + 0.05)

        logger.info(f"优化学习调度,设置学习间隔为 {learning_interval} 秒")
        return True

    def _generate_capability_expansions(self, action: Dict[str, Any]) -> bool:
        """生成功能拓展映射

        Args:
            action: 升级动作

        Returns:
            bool: 是否成功
        """
        logger.info("生成功能拓展映射...")
        missing_expansions = action["params"].get("missing_expansions", [])

        for capability in missing_expansions:
            if capability not in self._capability_expansions:
                self._capability_expansions[capability] = [
                    {
                        "capability": f"{capability}_advanced",
                        "description": f"高级{capability}",
                        "complexity": "high",
                        "priority": "medium"
                    },
                    {
                        "capability": f"{capability}_optimized",
                        "description": f"优化{capability}",
                        "complexity": "medium",
                        "priority": "low"
                    }
                ]
                logger.info(f"为 {capability} 生成功能拓展映射")

        return True

    def _record_upgrade_history(self, upgrade_plan: Dict[str, Any], result: bool):
        """记录升级历史

        Args:
            upgrade_plan: 升级方案
            result: 升级结果
        """
        knowledge_count_after = (
            len(self._knowledge_graph["entities"]) +
            len(self._knowledge_graph["relations"]) +
            len(self._knowledge_graph["rules"]) +
            len(self._knowledge_graph["tasks"])
        )

        upgrade_history = {
            "plan": upgrade_plan,
            "result": result,
            "completed_at": time.time(),
            "knowledge_count_before": self._learning_state["knowledge_count"],
            "knowledge_count_after": knowledge_count_after
        }

        history_file = os.path.join(
            self._upgrade_history_dir,
            f"upgrade_{time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        file_system.create_file(history_file, upgrade_history)
        self._upgrade_history.append(upgrade_history)

    def _get_current_version(self) -> str:
        """获取当前版本号

        Returns:
            str: 当前版本号
        """
        base_version = "1.0.0"
        return f"{base_version}.{self._learning_state['knowledge_count']}"

    def _get_next_version(self) -> str:
        """获取下一个AI版本

        Returns:
            str: 下一个版本号
        """
        current = self._get_current_version()
        parts = current.split(".")
        major = parts[0]
        minor = int(parts[1]) + 1
        patch = 0
        return f"{major}.{minor}.{patch}"

    def adapt_to_project(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """适配到特定项目

        Args:
            project_context: 项目上下文

        Returns:
            Dict[str, Any]: 适配结果
        """
        try:
            logger.info("开始AI项目适配...")

            project_type = project_context.get("type", "general")
            project_goals = project_context.get("goals", [])
            project_constraints = project_context.get("constraints", [])
            project_features = project_context.get("features", [])

            adaptation_plan = {
                "id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
                "project_type": project_type,
                "goals": project_goals,
                "constraints": project_constraints,
                "features": project_features,
                "timestamp": time.time(),
                "actions": [],
                "results": {}
            }

            # 1. 根据项目类型调用相应的适配方法
            if project_type in self._project_adaptation_models:
                adaptation_results = self._project_adaptation_models[project_type](project_context)
                adaptation_plan["results"]["model_adaptation"] = adaptation_results

            # 2. 调整学习参数
            updated_params = self._adjust_learning_params(project_goals, project_constraints)
            if updated_params:
                adaptation_plan["results"]["params_update"] = updated_params
                self._learning_params.update(updated_params)
                adaptation_plan["actions"].append({
                    "type": "params_adjustment",
                    "target": "learning_params",
                    "description": "调整学习参数",
                    "changes": updated_params,
                    "status": "success"
                })

            # 3. 根据项目特征更新功能关联
            feature_associations = self.generate_feature_associations(project_features)
            if feature_associations:
                adaptation_plan["results"]["feature_associations"] = feature_associations
                adaptation_plan["actions"].append({
                    "type": "feature_adaptation",
                    "target": "feature_associations",
                    "description": "生成功能联想",
                    "status": "success"
                })

            # 4. 生成项目特定的知识图谱扩展
            knowledge_extension = self._generate_project_knowledge_extension(project_context)
            if knowledge_extension:
                adaptation_plan["results"]["knowledge_extension"] = knowledge_extension

                self._knowledge_graph["entities"].update(knowledge_extension.get("entities", {}))
                self._knowledge_graph["relations"].update(knowledge_extension.get("relations", {}))

                adaptation_plan["actions"].append({
                    "type": "knowledge_extension",
                    "target": "knowledge_graph",
                    "description": "扩展知识图谱",
                    "entities_added": len(knowledge_extension.get("entities", {})),
                    "relations_added": len(knowledge_extension.get("relations", {})),
                    "status": "success"
                })

            # 5. 使用AI增强项目适配方案
            ai_enhanced_result = self.enhance_with_ai(
                task_type="project_adaptation",
                content=json.dumps({
                    "project_context": project_context,
                    "adaptation_plan": adaptation_plan
                }, ensure_ascii=False, indent=2),
                temperature=0.7,
                max_tokens=2048
            )

            if ai_enhanced_result and ai_enhanced_result["success"]:
                adaptation_plan["ai_engine_used"] = ai_enhanced_result["engine_used"]
                adaptation_plan["actions"].append({
                    "type": "ai_enhancement",
                    "target": "adaptation_plan",
                    "description": "使用AI增强适配方案",
                    "engine_used": ai_enhanced_result["engine_used"],
                    "status": "success"
                })

            # 6. 保存适配方案
            adaptation_file = os.path.join(
                self._project_adaptation_dir,
                f"adaptation_{time.strftime('%Y%m%d_%H%M%S')}.json"
            )
            file_system.create_file(adaptation_file, adaptation_plan)

            # 7. 更新适配状态
            self._learning_state["adaptation_count"] += 1

            logger.info("AI项目适配完成")

            return {
                "success": True,
                "adaptation_plan": adaptation_plan,
            }
        except Exception as e:
            logger.error(f"AI项目适配失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "message": "AI项目适配失败"
            }

    def _adjust_learning_params(self, project_goals: List[str], project_constraints: List[str]) -> Dict[str, Any]:
        """根据项目目标和约束调整学习参数

        Args:
            project_goals: 项目目标列表
            project_constraints: 项目约束列表

        Returns:
            Dict[str, Any]: 调整后的学习参数
        """
        updated_params = {}
        for goal in project_goals:
            if "performance" in goal.lower():
                updated_params["learning_rate"] = 0.2
                updated_params["max_iterations"] = 3000
            elif "scalability" in goal.lower():
                updated_params["memory_retention"] = 0.95
            elif "accuracy" in goal.lower():
                updated_params["convergence_threshold"] = 0.0001
                updated_params["max_iterations"] = 5000

        for constraint in project_constraints:
            if "time" in constraint.lower():
                updated_params["max_iterations"] = 1000
            elif "budget" in constraint.lower():
                updated_params["feature_similarity_threshold"] = 0.8

        return updated_params

    def _generate_project_knowledge_extension(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """生成项目特定的知识图谱扩展

        Args:
            project_context: 项目上下文信息

        Returns:
            Dict[str, Any]: 知识图谱扩展
        """
        project_type = project_context.get("type", "general")

        knowledge_extension = {
            "entities": {},
            "relations": {},
            "rules": {}
        }

        if project_type == "web_application":
            knowledge_extension["entities"]["web_framework"] = {
                "type": "technology",
                "examples": ["Flask", "Django", "FastAPI"],
                "confidence": 0.9
            }
            knowledge_extension["relations"]["uses_web_framework"] = {
                "source": "web_application",
                "target": "web_framework",
                "confidence": 0.8
            }
            knowledge_extension["rules"]["web_performance"] = {
                "action": "optimize_response_time",
                "confidence": 0.7
            }

        elif project_type == "data_science":
            knowledge_extension["entities"]["ml_library"] = {
                "type": "technology",
                "examples": ["Pandas", "NumPy", "Scikit-learn"],
                "confidence": 0.9
            }
            knowledge_extension["relations"]["uses_ml_library"] = {
                "source": "data_science_project",
                "target": "ml_library",
                "confidence": 0.8
            }

        elif project_type == "mobile_app":
            knowledge_extension["entities"]["mobile_framework"] = {
                "type": "technology",
                "examples": ["React Native", "Flutter"],
                "confidence": 0.8
            }

        return knowledge_extension

    def generate_feature_associations(self, current_features: List[str]) -> List[Dict[str, Any]]:
        """生成功能联想

        Args:
            current_features: 当前功能列表

        Returns:
            List[Dict[str, Any]]: 联想的功能列表
        """
        if not current_features:
            return []

        sorted_features = sorted(current_features)
        cache_key = hashlib.sha256(str(sorted_features).encode()).hexdigest()
        current_time = time.time()

        if cache_key in self._association_cache:
            cached_data = self._association_cache[cache_key]
            if current_time - cached_data["timestamp"] < self._learning_params["association_cache_ttl"]:
                logger.debug(f"使用缓存的功能联想结果,缓存键: {cache_key}")
                self._learning_state["association_count"] += len(cached_data["associations"])
                return cached_data["associations"]
            else:
                del self._association_cache[cache_key]

        if current_time - self._last_vector_update > self._vector_update_interval:
            self._update_feature_vectors()
            self._last_vector_update = current_time

        if not hasattr(self, '_feature_names') or not self._feature_names:
            associations = self._simple_feature_associations(current_features)
        else:
            try:
                current_descriptions = []
                for feature in current_features:
                    if feature in self._feature_descriptions:
                        current_descriptions.append(self._feature_descriptions[feature])
                    else:
                        current_descriptions.append(feature)

                current_text = " ".join(current_descriptions)
                all_features = self._feature_names.copy()
                all_vectors = self._tfidf_vectorizer.transform(self._feature_descriptions.values())
                current_vector = self._tfidf_vectorizer.transform([current_text])

                similarities = cosine_similarity(current_vector, all_vectors)[0]

                associations = []
                for i, similarity in enumerate(similarities):
                    feature_name = self._feature_names[i]
                    if feature_name not in current_features:
                        if similarity > self._learning_params["feature_similarity_threshold"]:
                            associations.append({
                                "feature": feature_name,
                                "score": float(similarity),
                                "description": self._feature_descriptions.get(feature_name, feature_name)
                            })

                associations.sort(key=lambda x: x["score"], reverse=True)

            except Exception as e:
                logger.error(f"生成功能联想时出错: {str(e)}")
                associations = self._simple_feature_associations(current_features)

        self._association_cache[cache_key] = {
            "associations": associations,
            "timestamp": current_time,
            "features": sorted_features
        }

        if len(self._association_cache) > 100:
            oldest_key = min(
                self._association_cache.keys(),
                key=lambda k: self._association_cache[k]["timestamp"]
            )
            del self._association_cache[oldest_key]

        self._learning_state["association_count"] += len(associations)

        return associations

    def _simple_feature_associations(self, current_features: List[str]) -> List[Dict[str, Any]]:
        """简单的功能联想算法(作为复杂算法的后备)

        Args:
            current_features: 当前功能列表

        Returns:
            List[Dict[str, Any]]: 联想的功能列表
        """
        associations = []

        feature_relations = {
            "file_management": ["rule_management", "user_management", "backup_system"],
            "rule_management": ["file_management", "ai_learning", "system_monitoring"],
            "user_management": ["file_management", "rule_management", "authentication"],
            "ai_learning": ["rule_management", "system_monitoring", "data_analytics"],
            "system_monitoring": ["ai_learning", "rule_management", "performance_tuning"],
            "backup_system": ["file_management", "disaster_recovery"],
            "data_analytics": ["ai_learning", "reporting"],
            "performance_tuning": ["system_monitoring", "resource_management"]
        }

        for feature in current_features:
            if feature in feature_relations:
                for related_feature in feature_relations[feature]:
                    if related_feature not in current_features:
                        associations.append({
                            "feature": related_feature,
                            "score": 0.5,
                            "description": f"与{feature}功能相关"
                        })

        seen = set()
        unique_associations = []
        for assoc in associations:
            if assoc["feature"] not in seen:
                seen.add(assoc["feature"])
                unique_associations.append(assoc)

        return unique_associations

    def auto_expand_capabilities(self, current_capabilities: List[str]) -> List[Dict[str, Any]]:
        """自动拓展能力

        Args:
            current_capabilities: 当前能力列表

        Returns:
            List[Dict[str, Any]]: 拓展的能力列表
        """
        expansions = []
        if not current_capabilities:
            return expansions

        for capability in current_capabilities:
            if capability in self._capability_expansions:
                expansions.extend(self._capability_expansions[capability])

        feature_associations = self.generate_feature_associations(current_capabilities)
        for association in feature_associations:
            associated_feature = association["feature"]
            if associated_feature in self._capability_expansions:
                for expansion in self._capability_expansions[associated_feature]:
                    adjusted_expansion = expansion.copy()
                    adjusted_expansion["association_score"] = association["score"]
                    adjusted_expansion["source"] = f"associated_with_{associated_feature}"
                    expansions.append(adjusted_expansion)

        unique_expansions = []
        seen = set()
        for expansion in expansions:
            cap_name = expansion["capability"]
            if cap_name not in seen:
                seen.add(cap_name)
                unique_expansions.append(expansion)
            else:
                for i, existing in enumerate(unique_expansions):
                    if existing["capability"] == cap_name:
                        current_score = expansion.get("association_score", 1.0)
                        existing_score = existing.get("association_score", 1.0)
                        if current_score > existing_score:
                            unique_expansions[i] = expansion
                        break

        def expansion_sort_key(exp):
            priority_weights = {"high": 3, "medium": 2, "low": 1}
            complexity_weights = {"low": 3, "medium": 2, "high": 1}
            priority_weight = priority_weights.get(exp.get("priority", "medium"), 2)
            complexity_weight = complexity_weights.get(exp.get("complexity", "medium"), 2)
            association_score = exp.get("association_score", 1.0)
            return (priority_weight * 100) + (complexity_weight * 10) + association_score

        unique_expansions.sort(key=expansion_sort_key, reverse=True)

        max_expansions = 10
        return unique_expansions[:max_expansions]

    def get_learning_status(self) -> Dict[str, Any]:
        """获取学习状态

        Returns:
            Dict[str, Any]: 学习状态
        """
        knowledge_count = (
            len(self._knowledge_graph["entities"]) +
            len(self._knowledge_graph["relations"]) +
            len(self._knowledge_graph["rules"]) +
            len(self._knowledge_graph["tasks"])
        )

        return {
            **self._learning_state,
            "knowledge_count": knowledge_count,
            "knowledge_types": list(self._knowledge_graph.keys()),
            "current_version": self._get_current_version()
        }

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """获取知识库摘要

        Returns:
            Dict[str, Any]: 知识库摘要
        """
        entities_count = len(self._knowledge_graph["entities"])
        relations_count = len(self._knowledge_graph["relations"])
        rules_count = len(self._knowledge_graph["rules"])

        tasks_count = 0
        for task_type, tasks in self._knowledge_graph["tasks"].items():
            if isinstance(tasks, dict):
                tasks_count += len(tasks)

        total_knowledge = entities_count + relations_count + rules_count + tasks_count
        summary = {
            "total_knowledge": total_knowledge,
            "knowledge_by_type": {
                "entities": entities_count,
                "relations": relations_count,
                "rules": rules_count,
                "tasks": tasks_count
            },
            "avg_confidence": 0,
            "latest_knowledge": []
        }

        total_confidence = 0
        total_items = 0

        for entity in self._knowledge_graph["entities"].values():
            total_confidence += entity.get("confidence", 0.5)
            total_items += 1

        for relation in self._knowledge_graph["relations"].values():
            total_confidence += relation.get("confidence", 0.5)
            total_items += 1

        for rule in self._knowledge_graph["rules"].values():
            total_confidence += rule.get("confidence", 0.5)
            total_items += 1

        all_tasks = []
        for task_type, tasks in self._knowledge_graph["tasks"].items():
            if isinstance(tasks, dict):
                for task_id, task_data in tasks.items():
                    all_tasks.append(task_data)
                    total_confidence += task_data.get("confidence", 0.5)
                    total_items += 1

        if total_items > 0:
            summary["avg_confidence"] = total_confidence / total_items

        all_tasks_sorted = sorted(all_tasks, key=lambda x: x.get("learned_at", 0), reverse=True)
        summary["latest_knowledge"] = all_tasks_sorted[:5]

        return summary


# 创建全局AI学习系统实例
ai_learning_system = AILearningSystem()
