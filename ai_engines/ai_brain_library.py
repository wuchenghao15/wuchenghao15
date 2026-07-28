# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI脑库管理系统 - 负责管理AI脑库、知识库、特征库和能力库,并提供自动升级功能
"""

# JSON import removed - using database
import time
import uuid
import logging
from datetime import datetime
import os
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_brain_library.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ai_brain_library')

class AIBrainLibrary:
    """AI脑库管理系统"""

    def __init__(self):
        self.libraries = {
            "brain_map": [],        # AI脑图库
            "knowledge": [],        # 知识库
            "features": [],         # 特征库
            "capabilities": []      # 能力库
        }
        self.library_versions = {
            "brain_map": "1.0.0",
            "knowledge": "1.0.0",
            "features": "1.0.0",
            "capabilities": "1.0.0"
        }
        self.performance_metrics = {}  # 性能指标

        # 初始化库
        self._initialize_libraries()

    def _initialize_libraries(self):
        """初始化AI脑库"""
        logger.info("初始化AI脑库...")

        # 加载现有库数据(如果存在)
        self.load_libraries()

        # 如果库为空,创建初始库数据
        if not self.libraries["brain_map"]:
            self._create_initial_brain_map()
        if not self.libraries["knowledge"]:
            self._create_initial_knowledge()
        if not self.libraries["features"]:
            self._create_initial_features()
        if not self.libraries["capabilities"]:
            self._create_initial_capabilities()

        logger.info("AI脑库初始化完成")

    def _create_initial_brain_map(self):
        """创建初始AI脑图"""
        initial_brain_maps = [
            {
                "id": f"brain_{uuid.uuid4().hex[:8]}",
                "name": "听力题生成AI脑图",
                "type": "listening_generation",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": f"brain_{uuid.uuid4().hex[:8]}",
                "name": "题目生成AI脑图",
                "type": "question_generation",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": "active"
            }
        ]
        self.libraries["brain_map"].extend(initial_brain_maps)

    def _create_initial_knowledge(self):
        initial_knowledge = [
            {
                "id": f"knowledge_{uuid.uuid4().hex[:8]}",
                "title": "英语语法基础",
                "category": "english_grammar",
                "difficulty": "beginner",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": f"knowledge_{uuid.uuid4().hex[:8]}",
                "title": "日语N5词汇",
                "category": "japanese_n5",
                "difficulty": "beginner",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        ]
        self.libraries["knowledge"].extend(initial_knowledge)

    def _create_initial_features(self):
        """创建初始特征库"""
        initial_features = [
            {
                "id": f"feature_{uuid.uuid4().hex[:8]}",
                "name": "词汇难度评估",
                "category": "vocabulary",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": f"feature_{uuid.uuid4().hex[:8]}",
                "name": "句子复杂度分析",
                "category": "sentence_analysis",
                "description": "分析句子的语法复杂度",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        ]
        self.libraries["features"].extend(initial_features)

    def _create_initial_capabilities(self):
        initial_capabilities = [
            {
                "id": f"capability_{uuid.uuid4().hex[:8]}",
                "name": "自动生成题目",
                "category": "question_generation",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": f"capability_{uuid.uuid4().hex[:8]}",
                "name": "智能推荐题目",
                "category": "question_recommendation",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": "active"
            }
        ]
        self.libraries["capabilities"].extend(initial_capabilities)

    def add_to_library(self, library_type, item):
        if library_type not in self.libraries:
            raise ValueError(f"未知的库类型: {library_type}")
        # 确保项目有必要的字段
        if "id" not in item:
            item["id"] = f"{library_type}_{uuid.uuid4().hex[:8]}"
        if "created_at" not in item:
            item["created_at"] = datetime.now().isoformat()

        self.libraries[library_type].append(item)
        self.save_libraries()


    def update_library_item(self, library_type, item_id, updates):
        if library_type not in self.libraries:
            raise ValueError(f"未知的库类型: {library_type}")
        for i, item in enumerate(self.libraries[library_type]):
            if item["id"] == item_id:
                # 更新项目
                self.libraries[library_type][i].update(updates)

                self.save_libraries()
                return True

        return False

        """从库中移除项目"""
        if library_type not in self.libraries:
            raise ValueError(f"未知的库类型: {library_type}")

        original_length = len(self.libraries[library_type])
        self.libraries[library_type] = [item for item in self.libraries[library_type] if item["id"] != item_id]

        if len(self.libraries[library_type]) < original_length:
            self.save_libraries()
            return True

        return False

    def get_library_items(self, library_type, filters=None):
        """获取库中的项目,支持过滤"""
        if library_type not in self.libraries:
            raise ValueError(f"未知的库类型: {library_type}")

        items = self.libraries[library_type]

        if filters:
            filtered_items = []
            for item in items:
                match = True
                for key, value in filters.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                if match:
                    filtered_items.append(item)
            return filtered_items
        return items
    def upgrade_library(self, library_type, target_version=None):
        """升级指定的库"""
        if library_type not in self.libraries:
            raise ValueError(f"未知的库类型: {library_type}")

        logger.info(f"开始升级{library_type}库...")

        # 记录升级前的版本
        old_version = self.library_versions[library_type]

        # 生成新的版本号
        if target_version:
            new_version = target_version
            # 自动生成新的版本号(增加小版本号)
            version_parts = old_version.split('.')

        # 执行升级逻辑
        upgrade_results = self._perform_library_upgrade(library_type, old_version, new_version)

        # 更新库版本
        self.library_versions[library_type] = new_version

        # 保存升级结果


        return {
            "success": True,
            "old_version": old_version,
            "new_version": new_version,
            "upgrade_results": upgrade_results
        }

    def _perform_library_upgrade(self, library_type, old_version, new_version):
        """执行库升级的具体逻辑"""
        results = {
            "added_items": 0,
            "removed_items": 0,
            "details": []
        }

        # 根据库类型执行不同的升级逻辑
        if library_type == "brain_map":
            # 升级AI脑图
                self.libraries["brain_map"][i]["version"] = new_version
                self.libraries["brain_map"][i]["last_updated"] = datetime.now().isoformat()
                results["upgraded_items"] += 1
                results["details"].append(f"升级AI脑图: {brain_map['name']}")
        elif library_type == "knowledge":
            # 升级知识库
            for i, knowledge in enumerate(self.libraries["knowledge"]):
                # 更新版本号
                self.libraries["knowledge"][i]["version"] = new_version
                self.libraries["knowledge"][i]["last_updated"] = datetime.now().isoformat()
                results["upgraded_items"] += 1
                # 安全获取标题,防止KeyError
                title = knowledge.get("title", "未知标题")
                results["details"].append(f"升级知识库: {title}")

        elif library_type == "features":
            # 升级特征库
            for i, feature in enumerate(self.libraries["features"]):
                # 更新版本号
                self.libraries["features"][i]["version"] = new_version
                self.libraries["features"][i]["last_updated"] = datetime.now().isoformat()
                results["upgraded_items"] += 1
                results["details"].append(f"升级特征库: {feature['name']}")

        elif library_type == "capabilities":
            # 升级能力库
            for i, capability in enumerate(self.libraries["capabilities"]):
                # 更新版本号
                self.libraries["capabilities"][i]["version"] = new_version
                self.libraries["capabilities"][i]["last_updated"] = datetime.now().isoformat()
                results["upgraded_items"] += 1
                results["details"].append(f"升级能力库: {capability['name']}")

        return results

    def upgrade_all_libraries(self, target_version=None):
        """升级所有库"""
        results = {}

        for library_type in self.libraries.keys():
            results[library_type] = self.upgrade_library(library_type, target_version)

        return results

    def learn_from_data(self, data, library_type):
        """从数据中学习并更新库"""
        if library_type not in self.libraries:
            raise ValueError(f"未知的库类型: {library_type}")

        logger.info(f"从数据中学习并更新{library_type}库...")

        # 这里可以添加具体的学习逻辑,根据数据类型和库类型执行不同的学习算法
        # 例如,从测试结果中学习,从用户反馈中学习,从新数据中学习等

        # 简单示例:添加新的知识条目
        if library_type == "knowledge":
            new_knowledge = {
                "name": "从数据学习到的新知识",
                "category": "learned_knowledge",
                "content": f"从数据中学习到的新内容: {str(data)[:100]}...",
                "difficulty": "intermediate",
                "version": self.library_versions[library_type]
            }
            self.add_to_library(library_type, new_knowledge)
        # 记录学习历史
        learning_record = {
            "library_type": library_type,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        self.learning_history.append(learning_record)

        logger.info(f"从数据中学习完成,更新了{library_type}库")

    def save_libraries(self):
        """保存库到文件"""
        try:
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            # 保存库数据
            with open(os.path.join(config_dir, 'ai_brain_libraries.json'), 'w', encoding='utf-8') as f:
                data_to_save = {
                    "libraries": self.libraries,
                    "library_versions": self.library_versions,
                }
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logger.error(f"保存AI脑库失败: {str(e)}")
            return False

    def load_libraries(self):
        try:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'ai_brain_libraries.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    self.libraries = loaded_data.get("libraries", self.libraries)
                logger.info("AI脑库已从文件加载")
                return True
        except Exception as e:
            logger.error(f"加载AI脑库失败: {str(e)}")

        return False

    def get_performance_metrics(self):
        """获取性能指标"""
        return self.performance_metrics

    def update_performance_metrics(self, metrics):
        """更新性能指标"""
        self.performance_metrics.update(metrics)
        self.save_libraries()

    def get_learning_history(self):
        """获取学习历史"""
        return self.learning_history
    def clear_libraries(self):
        """清空所有库"""
        for library_type in self.libraries.keys():
            self.libraries[library_type].clear()

        self.learning_history.clear()
        self.performance_metrics.clear()

# 测试代码
if __name__ == "__main__":
    # 创建AI脑库管理系统
    brain_library = AIBrainLibrary()

    print("AI脑库管理系统已创建")

    # 显示初始库内容
    print("\n初始AI脑图:")
    for brain_map in brain_library.get_library_items("brain_map"):
        print(f"- {brain_map['name']} ({brain_map['type']}) - 版本 {brain_map['version']}")

    print("\n初始知识库:")
    for knowledge in brain_library.get_library_items("knowledge"):
        print(f"- {knowledge['title']} ({knowledge['category']}) - 难度 {knowledge['difficulty']}")

    print("\n初始特征库:")
    for feature in brain_library.get_library_items("features"):
        print(f"- {feature['name']} ({feature['category']})")

    print("\n初始能力库:")
    for capability in brain_library.get_library_items("capabilities"):
        print(f"- {capability['name']} ({capability['category']})")

    # 测试升级功能
    print("\n升级知识库:")
    result = brain_library.upgrade_library("knowledge")
    print(f"升级结果: {'成功' if result['success'] else '失败'}")
    print(f"从版本 {result['old_version']} 升级到 {result['new_version']}")

    # 测试学习功能
    print("\n测试从数据中学习:")
    test_data = {"test_result": "success", "accuracy": 0.95, "topic": "english_grammar"}
    brain_library.learn_from_data(test_data, "knowledge")

    # 显示更新后的知识库
    print("\n更新后的知识库:")
    for knowledge in brain_library.get_library_items("knowledge"):
        print(f"- {knowledge['title']} ({knowledge['category']}) - 难度 {knowledge['difficulty']} - 版本 {knowledge['version']}")

    print("\nAI脑库管理系统测试完成")
