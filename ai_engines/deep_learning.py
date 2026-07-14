#!/usr/bin/env python3
"""
深度自我学习模块 - 增强AI的学习能力
"""

import time
import threading
from app.utils.logging import logger


class DeepSelfLearning:
    """深度自我学习类"""

    def __init__(self, ai_instance_manager):
        """
        初始化深度自我学习模块

        Args:
            ai_instance_manager: AI实例管理器
        """
        self.ai_instance_manager = ai_instance_manager
        self.learning_threads = {}
        self.learning_lock = threading.Lock()
        self.learning_config = {
            'learning_interval': 3600,
            'batch_size': 10,
            'max_iterations': 100,
            'learning_rate': 0.01,
            'knowledge_threshold': 0.7,
            'exploration_rate': 0.3
        }

    def start_deep_learning(self, instance_id):
        """
        开始深度自我学习

        Args:
            instance_id: AI实例ID

        Returns:
            bool: 是否开始成功
        """
        with self.learning_lock:
            if instance_id in self.learning_threads:
                logger.warning(f"AI实例 {instance_id} 已经在进行深度自我学习")
                return False

            learning_thread = threading.Thread(
                target=self._deep_learning_loop,
                args=(instance_id,),
                daemon=True
            )
            learning_thread.start()
            self.learning_threads[instance_id] = learning_thread
            logger.info(f"AI实例 {instance_id} 开始深度自我学习")
            return True

    def stop_deep_learning(self, instance_id):
        """
        停止深度自我学习

        Args:
            instance_id: AI实例ID

        Returns:
            bool: 是否停止成功
        """
        with self.learning_lock:
            if instance_id not in self.learning_threads:
                logger.warning(f"AI实例 {instance_id} 没有进行深度自我学习")
                return False

            del self.learning_threads[instance_id]
            logger.info(f"AI实例 {instance_id} 已停止深度自我学习")
            return True

    def _deep_learning_loop(self, instance_id):
        """
        深度自我学习循环

        Args:
            instance_id: AI实例ID
        """
        try:
            while instance_id in self.learning_threads:
                self._perform_deep_learning(instance_id)
                time.sleep(self.learning_config['learning_interval'])
        except Exception as e:
            logger.error(f"AI实例 {instance_id} 深度自我学习出错: {str(e)}")
            with self.learning_lock:
                if instance_id in self.learning_threads:
                    del self.learning_threads[instance_id]

    def _perform_deep_learning(self, instance_id):
        """
        执行深度学习

        Args:
            instance_id: AI实例ID
        """
        logger.info(f"开始AI实例 {instance_id} 的深度学习")

        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        if not instance:
            logger.error(f"AI实例 {instance_id} 不存在")
            return

        try:
            learning_data = self._collect_learning_data(instance_id)
            if not learning_data:
                logger.warning(f"AI实例 {instance_id} 没有可学习的数据")
                return

            insights = self._analyze_learning_data(learning_data)
            if not insights:
                return

            new_knowledge = self._generate_knowledge(insights)
            if not new_knowledge:
                logger.warning(f"AI实例 {instance_id} 生成知识失败")
                return

            self._integrate_knowledge(instance_id, new_knowledge)
            self._update_instance_performance(instance_id)

            logger.info(f"AI实例 {instance_id} 深度学习完成")
        except Exception as e:
            logger.error(f"AI实例 {instance_id} 执行深度学习失败: {str(e)}")

    def _collect_learning_data(self, instance_id):
        """
        收集学习数据

        Args:
            instance_id: AI实例ID

        Returns:
            list: 学习数据列表
        """
        learning_data = []
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        if not instance:
            return learning_data

        if hasattr(instance, 'get_learning_data'):
            learning_data = instance.get_learning_data()

        return learning_data

    def _analyze_learning_data(self, learning_data):
        """
        分析学习数据

        Args:
            learning_data: 学习数据

        Returns:
            dict: 分析结果
        """
        if not learning_data:
            return {}

        insights = {
            'patterns': [],
            'weaknesses': [],
            'opportunities': []
        }

        for data in learning_data:
            if isinstance(data, dict):
                if 'pattern' in data:
                    insights['patterns'].append(data['pattern'])
                if 'weakness' in data:
                    insights['weaknesses'].append(data['weakness'])
                if 'opportunity' in data:
                    insights['opportunities'].append(data['opportunity'])

        return insights

    def _generate_knowledge(self, insights):
        """
        生成知识

        Args:
            insights: 分析结果

        Returns:
            list: 生成的知识列表
        """
        new_knowledge = []

        for pattern in insights.get('patterns', []):
            new_knowledge.append({
                'title': f"模式识别: {pattern[:50]}",
                'content': f"发现了以下模式: {pattern}",
                'type': 'pattern',
                'tags': ['pattern', 'learning'],
                'priority': 2
            })

        for weakness in insights.get('weaknesses', []):
            new_knowledge.append({
                'title': f"改进机会: {weakness[:50]}",
                'content': f"发现了以下改进机会: {weakness}",
                'type': 'improvement',
                'tags': ['weakness', 'improvement'],
                'priority': 3
            })

        for opportunity in insights.get('opportunities', []):
            new_knowledge.append({
                'title': f"学习机会: {opportunity[:50]}",
                'content': f"发现了以下学习机会: {opportunity}",
                'type': 'opportunity',
                'tags': ['opportunity', 'learning'],
                'priority': 2
            })

        return new_knowledge

    def _integrate_knowledge(self, instance_id, new_knowledge):
        """
        整合知识

        Args:
            instance_id: AI实例ID
            new_knowledge: 新生成的知识列表
        """
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        if not instance:
            return

        if 'knowledge_base' not in instance:
            instance['knowledge_base'] = []

        for knowledge in new_knowledge:
            existing = any(k.get('title') == knowledge['title'] for k in instance['knowledge_base'])
            if not existing:
                instance['knowledge_base'].append(knowledge)
                logger.info(f"为AI实例 {instance_id} 添加新知识: {knowledge['title']}")

        max_knowledge = 1000
        if len(instance['knowledge_base']) > max_knowledge:
            instance['knowledge_base'] = sorted(
                instance['knowledge_base'],
                key=lambda x: (x.get('priority', 0), x.get('timestamp', 0)),
                reverse=True
            )[:max_knowledge]

        try:
            from app.services.ai_brain_service import ai_brain_service
            from app.models.ai_brain import AIBrainKnowledge

            for knowledge in new_knowledge:
                ai_brain_service.add_knowledge(
                    AIBrainKnowledge(
                        title=knowledge['title'],
                        content=knowledge['content'],
                        knowledge_type=knowledge['type'],
                        source='deep_learning',
                        source_id=instance_id,
                        priority=knowledge['priority']
                    )
                )
        except Exception as e:
            logger.error(f"同步知识到AI脑库失败: {str(e)}")

    def _update_instance_performance(self, instance_id):
        """
        更新实例性能

        Args:
            instance_id: AI实例ID
        """
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        if not instance:
            return

        if 'performance_metrics' in instance:
            performance = instance['performance_metrics']
            performance['learning_count'] = performance.get('learning_count', 0) + 1

            current_accuracy = performance.get('accuracy', 0.5)
            performance['accuracy'] = min(1.0, current_accuracy + 0.01)

            self.ai_instance_manager.update_instance_performance(instance_id, performance)

    def _extract_common_words(self, text, top_n=10):
        """
        提取常见词汇

        Args:
            text: 文本
            top_n: 返回前N个词汇

        Returns:
            list: 常见词汇列表
        """
        import re
        from collections import Counter

        words = text.split()

        common_words = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
        filtered_words = [word for word in words if word not in common_words and len(word) > 2]

        word_counts = Counter(filtered_words)
        return word_counts.most_common(top_n)

    def get_learning_status(self, instance_id):
        """
        获取学习状态

        Args:
            instance_id: AI实例ID

        Returns:
            dict: 学习状态
        """
        with self.learning_lock:
            is_learning = instance_id in self.learning_threads

            instance = self.ai_instance_manager.get_ai_instance(instance_id)

            learning_stats = {
                'is_learning': is_learning,
                'learning_config': self.learning_config,
                'instance_exists': instance is not None
            }

            return learning_stats

    def start_all_instances_learning(self):
        """
        开始所有实例的深度自我学习

        Returns:
            int: 开始学习的实例数量
        """
        instances = self.ai_instance_manager.ai_instances
        started_count = 0

        for instance_id, instance in instances.items():
            if instance.get('self_learning', False):
                if self.start_deep_learning(instance_id):
                    started_count += 1

        logger.info(f"开始了 {started_count} 个AI实例的深度自我学习")
        return started_count

    def stop_all_instances_learning(self):
        """
        停止所有实例的深度自我学习

        Returns:
            int: 停止学习的实例数量
        """
        with self.learning_lock:
            instance_ids = list(self.learning_threads.keys())
            stopped_count = 0

            for instance_id in instance_ids:
                if self.stop_deep_learning(instance_id):
                    stopped_count += 1

            logger.info(f"停止了 {stopped_count} 个AI实例的深度自我学习")
            return stopped_count


deep_self_learning = None


def get_deep_self_learning(ai_instance_manager):
    """
    获取深度自我学习模块实例

    Args:
        ai_instance_manager: AI实例管理器

    Returns:
        DeepSelfLearning: 深度自我学习模块实例
    """
    global deep_self_learning
    if deep_self_learning is None:
        deep_self_learning = DeepSelfLearning(ai_instance_manager)
    return deep_self_learning
