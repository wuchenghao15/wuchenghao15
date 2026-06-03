# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI Learning and Self-Upgrading Module
This module enables AI models to learn from each other, accumulate knowledge,
and continuously upgrade themselves while preventing knowledge pollution.
"""

import os
import sys
import time
# JSON import removed - using database
import threading
import logging
import hashlib
from abc import ABC, abstractmethod
import json

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('ai_learning.log'),
                              logging.StreamHandler()])
logger = logging.getLogger('AI_Learning')

class KnowledgeBase:
    """Knowledge base class for storing and managing AI knowledge"""

    def __init__(self, knowledge_base_path='knowledge_base.json'):
        self.knowledge_base_path = knowledge_base_path
        self.knowledge = {}
        self.lock = threading.RLock()
        self.pollution_threshold = 0.3  # 知识污染阈值
        self.confidence_threshold = 0.7  # 知识置信度阈值

        # 加载知识库
        self.load_knowledge()
        logger.info(f"Knowledge Base initialized with {len(self.knowledge)} entries")

    def load_knowledge(self):
        """加载知识库"""
        try:
            if os.path.exists(self.knowledge_base_path):
                with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                    self.knowledge = json.load(f)
                logger.info(f"Loaded knowledge base from {self.knowledge_base_path}")
            else:
                self.knowledge = {
                    'metadata': {
                        'version': '1.0',
                        'last_updated': time.time(),
                        'total_entries': 0
                    },
                    'entries': {}
                }
                self.save_knowledge()
                logger.info(f"Created new knowledge base at {self.knowledge_base_path}")
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {str(e)}")
            self.knowledge = {
                'metadata': {
                    'version': '1.0',
                    'last_updated': time.time(),
                    'total_entries': 0
                },
                'entries': {}
            }

    def save_knowledge(self):
        """保存知识库"""
        try:
            self.knowledge['metadata']['last_updated'] = time.time()
            with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved knowledge base to {self.knowledge_base_path}")
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {str(e)}")

    def generate_knowledge_id(self, content):
        """生成知识条目ID"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def add_knowledge(self, content, source, confidence=0.8, tags=None, metadata=None):
        """添加知识条目"""
        with self.lock:
            try:
                knowledge_id = self.generate_knowledge_id(content)

                if knowledge_id in self.knowledge['entries']:
                    # 更新现有知识
                    existing_entry = self.knowledge['entries'][knowledge_id]
                    existing_entry['confidence'] = max(existing_entry['confidence'], confidence)
                    if source not in existing_entry['sources']:
                        existing_entry['sources'].append(source)
                    existing_entry['last_updated'] = time.time()
                    if tags:
                        for tag in tags:
                            if tag not in existing_entry['tags']:
                                existing_entry['tags'].append(tag)
                    if metadata:
                        existing_entry['metadata'].update(metadata)
                    existing_entry['update_count'] += 1
                    logger.debug(f"Updated existing knowledge entry: {knowledge_id}")
                else:
                    # 添加新知识
                    self.knowledge['entries'][knowledge_id] = {
                        'content': content,
                        'sources': [source],
                        'confidence': confidence,
                        'tags': tags if tags else [],
                        'metadata': metadata if metadata else {},
                        'created_at': time.time(),
                        'last_updated': time.time(),
                        'update_count': 1
                    }
                    logger.debug(f"Added new knowledge entry: {knowledge_id}")

                # 保存知识库
                self.save_knowledge()
                return True
            except Exception as e:
                logger.error(f"Failed to add knowledge: {str(e)}")
                return False

    def get_knowledge(self, knowledge_id):
        """获取知识条目"""
        return self.knowledge['entries'].get(knowledge_id, None)

    def search_knowledge(self, query, tags=None, confidence_threshold=None):
        """搜索知识库"""
        with self.lock:
            conf_threshold = confidence_threshold or self.confidence_threshold
            results = []
            
            for entry_id, entry in self.knowledge['entries'].items():
                # 检查置信度
                if entry['confidence'] < conf_threshold:
                    continue

                # 检查标签
                if tags:
                    entry_tags = entry['tags']
                    if not any(tag in entry_tags for tag in tags):
                        continue

                # 简单的文本匹配
                if query.lower() in entry['content'].lower():
                    results.append(entry)

            # 按置信度排序
            results.sort(key=lambda x: x['confidence'], reverse=True)
            return results

    def remove_knowledge(self, knowledge_id):
        """移除知识条目"""
        with self.lock:
            if knowledge_id in self.knowledge['entries']:
                del self.knowledge['entries'][knowledge_id]
                self.save_knowledge()
                return True
            return False

    def clean_polluted_knowledge(self):
        """清理污染的知识"""
        with self.lock:
            removed_count = 0
            for entry_id, entry in list(self.knowledge['entries'].items()):
                if entry['confidence'] < self.pollution_threshold:
                    del self.knowledge['entries'][entry_id]
                    removed_count += 1

            if removed_count > 0:
                logger.info(f"Cleaned {removed_count} polluted knowledge entries")
                self.save_knowledge()
            return removed_count

    def get_statistics(self):
        """获取知识库统计信息"""
        with self.lock:
            entries = self.knowledge['entries']
            total_entries = len(entries)

            if total_entries > 0:
                avg_confidence = sum(entry['confidence'] for entry in entries.values()) / total_entries
            else:
                avg_confidence = 0

            tag_counts = {}
            for entry in entries.values():
                for tag in entry['tags']:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            return {
                'total_entries': total_entries,
                'avg_confidence': avg_confidence,
                'total_sources': len(set(source for entry in entries.values() for source in entry['sources'])),
                'last_updated': self.knowledge['metadata']['last_updated'],
                'version': self.knowledge['metadata']['version']
            }

class AILearningAgent:
    """AI学习代理,负责模型之间的知识交流和学习"""

    def __init__(self, ai_service_manager, knowledge_base):
        self.ai_service_manager = ai_service_manager
        self.knowledge_base = knowledge_base
        self.learning_rate = 0.1
        self.exploration_rate = 0.3
        self.lock = threading.RLock()
        logger.info("AI Learning Agent initialized")

        """从一个模型学习到另一个模型"""
        try:
            logger.info(f"Starting learning process: {source_model_name} -> {target_model_name}")
            # 获取源模型状态
            source_status = self.ai_service_manager.get_model_status(source_model_name)
            if not source_status['success']:
                logger.error(f"Failed to get source model status: {source_model_name}")
                return False

            # 获取目标模型状态
            target_status = self.ai_service_manager.get_model_status(target_model_name)
            if not target_status['success']:
                logger.error(f"Failed to get target model status: {target_model_name}")
                return False

            # 这里可以添加更复杂的学习逻辑
            # 例如:获取源模型的知识,转换为目标模型的训练数据,然后升级目标模型

            # 模拟学习过程
            logger.info(f"Simulating learning from {source_model_name} to {target_model_name}")
            time.sleep(2)

            # 记录学习结果到知识库
            learning_content = f"Learned from {source_model_name} to {target_model_name}: Model improvement"
            self.knowledge_base.add_knowledge(
                content=learning_content,
                source="ai_learning_agent",
                confidence=0.85,
                tags={"learning", "model_upgrade"},
                metadata={
                    "source_model": source_model_name,
                    "target_model": target_model_name,
                    "learning_time": time.time()
                }
            )

            # 升级目标模型
            if success:
                logger.info(f"Successfully learned from {source_model_name} to {target_model_name}")
                return True
            else:
                logger.error(f"Failed to upgrade target model: {target_model_name}")
        except Exception as e:
            logger.error(f"Learning process failed: {str(e)}")

    def multi_ai_mutual_learning(self, model_names):
        try:
            logger.info(f"Starting multi-AI mutual learning with models: {model_names}")
            results = {}
            # 所有模型之间互相学习
            for i, source_model in enumerate(model_names):
                for j, target_model in enumerate(model_names):
                    if i != j:  # 不要自己学习自己
                        result = self.learn_from_model(source_model, target_model)
                        results[f"{source_model}->{target_model}"] = result

            logger.info(f"Multi-AI mutual learning completed: {results}")
            return results
        except Exception as e:
            logger.error(f"Multi-AI mutual learning failed: {str(e)}")
            return {}

    def self_upgrade_cycle(self):
        try:
            logger.info("Starting self-upgrade cycle")
            # 1. 获取所有模型
            model_names = self.ai_service_manager.list_models()
            if not model_names:
                logger.warning("No models available for self-upgrade")
                return False

            cleaned_count = self.knowledge_base.clean_polluted_knowledge()
            logger.info(f"Cleaned {cleaned_count} polluted knowledge entries before self-upgrade")
            # 3. 多AI相互学习
            learning_results = self.multi_ai_mutual_learning(model_names)

            # 4. 升级知识库
            self.upgrade_knowledge_base()

            success_count = sum(1 for result in learning_results.values() if result)
            total_count = len(learning_results)
            success_rate = success_count / total_count if total_count > 0 else 0

            logger.info(f"Self-upgrade cycle completed: {success_count}/{total_count} successful ({success_rate:.2%})")
            return True
        except Exception as e:
            logger.error(f"Self-upgrade cycle failed: {str(e)}")
            return False

    def upgrade_knowledge_base(self):
        """升级知识库"""
        try:
            logger.info("Upgrading knowledge base")
            # 这里可以添加更复杂的知识库升级逻辑

            # 模拟知识库升级
            time.sleep(1)

            # 更新知识库版本
            stats = self.knowledge_base.get_statistics()
            logger.info(f"Knowledge base upgraded: {stats}")
        except Exception as e:
            logger.error(f"Knowledge base upgrade failed: {str(e)}")
            return False

    def learn_from_external_data(self, data_source, data, confidence=0.7):
        """从外部数据学习"""
        try:
            # 将外部数据添加到知识库
            success = self.knowledge_base.add_knowledge(
                content=data,
                source=data_source,
                confidence=confidence,
                tags={"external_data", data_source},
                metadata={"import_time": time.time()}
            )

            if success:
                logger.info(f"Successfully learned from external data source: {data_source}")
                # 触发模型升级
                model_names = self.ai_service_manager.list_models()
                for model_name in model_names:
                    self.ai_service_manager.upgrade_model(model_name, training_data=data)
                return True
            else:
                logger.error(f"Failed to learn from external data source: {data_source}")
                return False
        except Exception as e:
            logger.error(f"Learning from external data failed: {str(e)}")
            return False

    def learn_from_test_results(self, test_results):
        """从用户测试结果中学习,优化试卷生成"""
        try:
            logger.info("Learning from user test results")
            # 分析测试结果,提取有用信息
            # 计算各题目的正确率
            question_analytics = {}
            for result in test_results:
                for question_id, answer_info in result['answers'].items():
                    if question_id not in question_analytics:
                        question_analytics[question_id] = {
                            'correct_attempts': 0,
                            'difficulty_feedback': 0,  # -1: too hard, 0: appropriate, 1: too easy
                            'question_data': answer_info['question']
                        }

                    question_analytics[question_id]['total_attempts'] += 1
                    if answer_info['is_correct']:
                        question_analytics[question_id]['correct_attempts'] += 1

                    # 收集难度反馈(如果有)
                    if 'difficulty_feedback' in answer_info:
                        question_analytics[question_id]['difficulty_feedback'] += answer_info['difficulty_feedback']
            # 生成学习内容
            learning_content = "\n".join([
                f"题目ID: {qid}, 正确率: {analytics['correct_attempts']/analytics['total_attempts']:.2f}, "
                f"难度反馈: {analytics['difficulty_feedback']}, 题目类型: {analytics['question_data']['category']}, "
                f"难度级别: {analytics['question_data']['difficulty']}"
                for qid, analytics in question_analytics.items()
            ])

            # 将分析结果添加到知识库
            success = self.knowledge_base.add_knowledge(
                content=learning_content,
                source="test_results_analysis",
                metadata={
                    "total_tests": len(test_results)
                }
            )
            if success:
                logger.info("Successfully learned from test results")
                # 触发模型升级,特别是文本生成模型,用于改进题目生成
                self.ai_service_manager.upgrade_model("default_text_gen", training_data=learning_content)
                return True
            else:
                logger.error("Failed to learn from test results")
                return False
        except Exception as e:
            logger.error(f"Learning from test results failed: {str(e)}")
            return False

    def optimize_paper_generation(self, user_preferences=None):
        """优化试卷生成策略"""
        try:
            # 从知识库中获取相关知识
            paper_generation_knowledge = self.knowledge_base.search_knowledge(
                query="paper generation strategy",
                tags={"test_analytics", "question_performance"},
            )

            if not paper_generation_knowledge:
                logger.warning("No relevant knowledge found for paper generation optimization")
                return False

            # 分析知识,生成优化建议
            optimization_suggestions = "\n".join([
                entry['content'] for entry in paper_generation_knowledge
            ])

            # 将优化建议添加到知识库
            success = self.knowledge_base.add_knowledge(
                content=f"Paper generation optimization suggestions: {optimization_suggestions}",
                source="optimization_engine",
                confidence=0.85,
                tags={"optimization", "paper_generation"},
                metadata={
                    "optimization_time": time.time(),
                }
            )

            if success:
                logger.info("Successfully optimized paper generation strategy")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Optimizing paper generation failed: {str(e)}")
            return False


class AILearningSystem:
    """AI学习系统,整合知识库和学习代理"""

    def __init__(self, ai_service_manager):
        self.ai_service_manager = ai_service_manager
        self.knowledge_base = KnowledgeBase()
        self.learning_agent = AILearningAgent(self.ai_service_manager, self.knowledge_base)
        self.auto_learning_enabled = True
        self.learning_interval = 3600  # 自动学习间隔(秒)
        self.last_learning_time = time.time()
        # 启动自动学习线程
        self._start_auto_learning_thread()

        logger.info("AI Learning System initialized successfully")

    def _start_auto_learning_thread(self):
        """启动自动学习线程"""
        def auto_learning():
            while True:
                time.sleep(60)  # 每分钟检查一次
                if self.auto_learning_enabled:
                    current_time = time.time()
                    if current_time - self.last_learning_time > self.learning_interval:
                        logger.info("Starting auto-learning cycle")
                        self.learning_agent.self_upgrade_cycle()
                        self.last_learning_time = current_time

        learning_thread = threading.Thread(target=auto_learning, daemon=True)
        learning_thread.start()

    def trigger_self_upgrade(self):
        """手动触发自我升级"""
        return self.learning_agent.self_upgrade_cycle()

    def add_knowledge(self, content, source, confidence=0.8, tags=None, metadata=None):
        """添加知识到知识库"""
        return self.knowledge_base.add_knowledge(content, source, confidence, tags, metadata)

    def search_knowledge(self, query, tags=None, confidence_threshold=None):
        """搜索知识库"""
        return self.knowledge_base.search_knowledge(query, tags, confidence_threshold)

    def get_knowledge_statistics(self):
        """获取知识库统计信息"""
        return self.knowledge_base.get_statistics()
    def set_auto_learning(self, enabled, interval=None):
        """设置自动学习"""
        logger.info(f"Auto-learning set to {enabled}, interval: {self.learning_interval} seconds")
    def learn_from_external_data(self, data_source, data, confidence=0.7):
        """从外部数据学习"""
        return self.learning_agent.learn_from_external_data(data_source, data, confidence)

    def learn_from_test_results(self, test_results):
        """从用户测试结果中学习,优化试卷生成"""
        return self.learning_agent.learn_from_test_results(test_results)
    def optimize_paper_generation(self, user_preferences=None):
        """优化试卷生成策略"""
        return self.learning_agent.optimize_paper_generation(user_preferences)

    def shutdown(self):
        """关闭学习系统"""
        logger.info("Shutting down AI Learning System...")
        self.auto_learning_enabled = False
        # 保存知识库
        self.knowledge_base.save_knowledge()
        return True

# 初始化学习系统(如果在主程序中运行)
if __name__ == "__main__":
    # 导入AI服务管理器

    # 初始化学习系统
    learning_system = AILearningSystem(ai_service_manager)

    # 测试添加知识
    learning_system.add_knowledge(
        content="Test knowledge content",
        source="test_source",
        confidence=0.9,
        tags={"test", "example"},
        metadata={"test_key": "test_value"}
    )

    # 测试搜索知识
    results = learning_system.search_knowledge("Test")
    logger.info(f"Knowledge search results: {results}")

    # 测试自我升级
    learning_system.trigger_self_upgrade()

    # 获取统计信息
    stats = learning_system.get_knowledge_statistics()
    logger.info(f"Knowledge base statistics: {str(stats, indent=2)}")

    logger.info("AI Learning System test completed!")
