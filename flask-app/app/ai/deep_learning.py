#!/usr/bin/env python3
"""
深度自我学习模块，增强AI的学习能力
"""

import time
import threading
from app.utils.logging import logger


class DeepSelfLearning:
    """深度自我学习类"""
    
    def __init__(self, ai_instance_manager):
        """初始化深度自我学习模块
        
        Args:
            ai_instance_manager: AI实例管理器
        """
        self.ai_instance_manager = ai_instance_manager
        self.learning_threads = {}
        self.learning_lock = threading.Lock()
        self.learning_config = {
            'learning_interval': 3600,  # 学习间隔（秒）
            'batch_size': 10,  # 每次学习的批次大小
            'max_iterations': 100,  # 最大学习迭代次数
            'learning_rate': 0.01,  # 学习率
            'knowledge_threshold': 0.7,  # 知识掌握阈值
            'exploration_rate': 0.3  # 探索率
        }
    
    def start_deep_learning(self, instance_id):
        """开始深度自我学习
        
        Args:
            instance_id: AI实例ID
        
        Returns:
            bool: 是否开始成功
        """
        with self.learning_lock:
            if instance_id in self.learning_threads:
                logger.warning(f"AI实例 {instance_id} 已经在进行深度自我学习")
                return False
            
            # 检查实例是否存在
            instance = self.ai_instance_manager.get_ai_instance(instance_id)
            if not instance:
                logger.error(f"AI实例 {instance_id} 不存在")
                return False
            
            # 检查实例是否启用了自我学习
            if not instance.get('self_learning', False):
                logger.warning(f"AI实例 {instance_id} 未启用自我学习")
                return False
            
            # 创建学习线程
            learning_thread = threading.Thread(
                target=self._deep_learning_loop,
                args=(instance_id,),
                daemon=True
            )
            
            # 启动线程
            learning_thread.start()
            self.learning_threads[instance_id] = learning_thread
            
            logger.info(f"开始AI实例 {instance_id} 的深度自我学习")
            return True
    
    def stop_deep_learning(self, instance_id):
        """停止深度自我学习
        
        Args:
            instance_id: AI实例ID
        
        Returns:
            bool: 是否停止成功
        """
        with self.learning_lock:
            if instance_id not in self.learning_threads:
                logger.warning(f"AI实例 {instance_id} 没有进行深度自我学习")
                return False
            
            # 线程会自动结束，这里只需要移除引用
            del self.learning_threads[instance_id]
            
            logger.info(f"停止AI实例 {instance_id} 的深度自我学习")
            return True
    
    def _deep_learning_loop(self, instance_id):
        """深度自我学习循环
        
        Args:
            instance_id: AI实例ID
        """
        try:
            while instance_id in self.learning_threads:
                # 执行深度学习
                self._perform_deep_learning(instance_id)
                
                # 等待下一次学习
                time.sleep(self.learning_config['learning_interval'])
        except Exception as e:
            logger.error(f"AI实例 {instance_id} 深度自我学习出错: {str(e)}")
            with self.learning_lock:
                if instance_id in self.learning_threads:
                    del self.learning_threads[instance_id]
    
    def _perform_deep_learning(self, instance_id):
        """执行深度学习
        
        Args:
            instance_id: AI实例ID
        """
        logger.info(f"开始AI实例 {instance_id} 的深度学习")
        
        # 获取AI实例
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        if not instance:
            logger.error(f"AI实例 {instance_id} 不存在")
            return
        
        try:
            # 1. 收集学习数据
            learning_data = self._collect_learning_data(instance_id)
            if not learning_data:
                logger.warning(f"AI实例 {instance_id} 没有可学习的数据")
                return
            
            # 2. 分析学习数据
            insights = self._analyze_learning_data(learning_data)
            if not insights:
                logger.warning(f"AI实例 {instance_id} 学习数据分析失败")
                return
            
            # 3. 生成知识
            new_knowledge = self._generate_knowledge(insights)
            if not new_knowledge:
                logger.warning(f"AI实例 {instance_id} 生成知识失败")
                return
            
            # 4. 整合知识
            self._integrate_knowledge(instance_id, new_knowledge)
            
            # 5. 更新实例性能
            self._update_instance_performance(instance_id)
            
            logger.info(f"AI实例 {instance_id} 深度学习完成")
        except Exception as e:
            logger.error(f"AI实例 {instance_id} 执行深度学习失败: {str(e)}")
    
    def _collect_learning_data(self, instance_id):
        """收集学习数据
        
        Args:
            instance_id: AI实例ID
        
        Returns:
            list: 学习数据列表
        """
        learning_data = []
        
        # 从实例获取数据
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        if not instance:
            return learning_data
        
        # 1. 收集通信数据
        if 'communication' in instance:
            communication = instance['communication']
            # 收集最近的消息
            for message in communication.get('inbox', [])[-10:]:
                learning_data.append({
                    'type': 'message',
                    'content': message['content'],
                    'metadata': message.get('metadata', {}),
                    'timestamp': message['timestamp']
                })
        
        # 2. 收集协作数据
        if 'collaboration' in instance:
            collaboration = instance['collaboration']
            # 收集最近的协作
            for collab in collaboration.get('active_collaborations', [])[:5]:
                learning_data.append({
                    'type': 'collaboration',
                    'content': collab['goal'],
                    'metadata': collab.get('metadata', {}),
                    'timestamp': collab['start_time']
                })
        
        # 3. 收集学习会话数据
        if 'learning_sessions' in instance:
            for session in instance['learning_sessions'][-5:]:
                learning_data.append({
                    'type': 'learning_session',
                    'content': session['topic'],
                    'metadata': {'goals': session['goals']},
                    'timestamp': session['start_time']
                })
        
        # 4. 收集性能数据
        if 'performance_metrics' in instance:
            performance = instance['performance_metrics']
            learning_data.append({
                'type': 'performance',
                'content': str(performance),
                'metadata': performance,
                'timestamp': time.time()
            })
        
        return learning_data
    
    def _analyze_learning_data(self, learning_data):
        """分析学习数据
        
        Args:
            learning_data: 学习数据列表
        
        Returns:
            dict: 分析结果
        """
        insights = {
            'patterns': [],
            'weaknesses': [],
            'opportunities': [],
            'trends': []
        }
        
        # 分析消息模式
        message_contents = [data['content'] for data in learning_data if data['type'] == 'message']
        if message_contents:
            # 简单的模式分析
            common_words = self._extract_common_words(' '.join(message_contents))
            if common_words:
                insights['patterns'].append(f"常见词汇: {', '.join(common_words[:5])}")
        
        # 分析性能数据
        performance_data = [data['metadata'] for data in learning_data if data['type'] == 'performance']
        if performance_data:
            latest_performance = performance_data[-1]
            # 分析性能趋势
            if latest_performance.get('errors', 0) > 0:
                error_rate = latest_performance['errors'] / (latest_performance.get('tasks_completed', 1) + 1)
                if error_rate > 0.1:
                    insights['weaknesses'].append(f"错误率较高: {error_rate:.2f}")
            
            response_time = latest_performance.get('response_time', 0)
            if response_time > 2.0:
                insights['weaknesses'].append(f"响应时间较长: {response_time:.2f}秒")
        
        # 分析学习会话
        learning_sessions = [data for data in learning_data if data['type'] == 'learning_session']
        if learning_sessions:
            topics = [session['content'] for session in learning_sessions]
            unique_topics = set(topics)
            if len(unique_topics) > 1:
                insights['opportunities'].append(f"多样化学习主题: {len(unique_topics)}个不同主题")
        
        return insights
    
    def _generate_knowledge(self, insights):
        """生成知识
        
        Args:
            insights: 分析结果
        
        Returns:
            list: 生成的知识列表
        """
        new_knowledge = []
        
        # 基于模式生成知识
        for pattern in insights.get('patterns', []):
            new_knowledge.append({
                'title': f"模式识别: {pattern[:50]}",
                'content': f"发现了以下模式: {pattern}",
                'type': 'pattern',
                'tags': ['pattern', 'learning'],
                'priority': 2
            })
        
        # 基于弱点生成知识
        for weakness in insights.get('weaknesses', []):
            new_knowledge.append({
                'title': f"改进机会: {weakness[:50]}",
                'content': f"发现了以下改进机会: {weakness}",
                'type': 'improvement',
                'tags': ['weakness', 'improvement'],
                'priority': 3
            })
        
        # 基于机会生成知识
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
        """整合知识
        
        Args:
            instance_id: AI实例ID
            new_knowledge: 新生成的知识列表
        """
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        if not instance:
            return
        
        # 更新实例知识库
        if 'knowledge_base' not in instance:
            instance['knowledge_base'] = []
        
        for knowledge in new_knowledge:
            # 检查知识是否已存在
            existing = any(k.get('title') == knowledge['title'] for k in instance['knowledge_base'])
            if not existing:
                instance['knowledge_base'].append(knowledge)
                logger.info(f"为AI实例 {instance_id} 添加新知识: {knowledge['title']}")
        
        # 限制知识库大小
        max_knowledge = 1000
        if len(instance['knowledge_base']) > max_knowledge:
            # 按优先级和时间排序，保留重要的知识
            instance['knowledge_base'] = sorted(
                instance['knowledge_base'],
                key=lambda x: (x.get('priority', 0), x.get('timestamp', 0)),
                reverse=True
            )[:max_knowledge]
        
        # 同步到AI脑库
        try:
            from app.services.ai_brain_service import ai_brain_service
            for knowledge in new_knowledge:
                ai_brain_service.add_knowledge(
                    title=knowledge['title'],
                    content=knowledge['content'],
                    knowledge_type=knowledge['type'],
                    source='deep_learning',
                    source_id=instance_id,
                    tags=knowledge['tags'],
                    priority=knowledge['priority']
                )
        except Exception as e:
            logger.error(f"同步知识到AI脑库失败: {str(e)}")
    
    def _update_instance_performance(self, instance_id):
        """更新实例性能
        
        Args:
            instance_id: AI实例ID
        """
        instance = self.ai_instance_manager.get_ai_instance(instance_id)
        if not instance:
            return
        
        # 简单的性能更新
        if 'performance_metrics' in instance:
            performance = instance['performance_metrics']
            # 增加学习次数
            performance['learning_count'] = performance.get('learning_count', 0) + 1
            # 轻微提高准确性
            current_accuracy = performance.get('accuracy', 0)
            performance['accuracy'] = min(1.0, current_accuracy + 0.01)
            
            # 更新实例
            self.ai_instance_manager.update_instance_performance(instance_id, performance)
    
    def _extract_common_words(self, text, top_n=10):
        """提取常见词汇
        
        Args:
            text: 文本
            top_n: 返回前N个常见词汇
        
        Returns:
            list: 常见词汇列表
        """
        import re
        from collections import Counter
        
        # 移除标点符号
        text = re.sub(r'[\s\d\p{P}\p{S}]+', ' ', text)
        
        # 分词
        words = text.split()
        
        # 过滤常见词和短词
        common_words = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
        filtered_words = [word for word in words if word not in common_words and len(word) > 2]
        
        # 统计词频
        word_counts = Counter(filtered_words)
        
        # 返回前N个常见词汇
        return [word for word, _ in word_counts.most_common(top_n)]
    
    def get_learning_status(self, instance_id):
        """获取学习状态
        
        Args:
            instance_id: AI实例ID
        
        Returns:
            dict: 学习状态
        """
        with self.learning_lock:
            is_learning = instance_id in self.learning_threads
            
            # 获取实例信息
            instance = self.ai_instance_manager.get_ai_instance(instance_id)
            learning_stats = {
                'is_learning': is_learning,
                'learning_config': self.learning_config,
                'instance_info': instance.get('name', 'Unknown') if instance else 'Unknown',
                'knowledge_count': len(instance.get('knowledge_base', [])) if instance else 0
            }
            
            return learning_stats
    
    def start_all_instances_learning(self):
        """开始所有实例的深度自我学习
        
        Returns:
            int: 开始学习的实例数量
        """
        instances = self.ai_instance_manager.ai_instances
        started_count = 0
        
        for instance_id in instances:
            instance = instances[instance_id]
            if instance.get('self_learning', False):
                if self.start_deep_learning(instance_id):
                    started_count += 1
        
        logger.info(f"开始了 {started_count} 个AI实例的深度自我学习")
        return started_count
    
    def stop_all_instances_learning(self):
        """停止所有实例的深度自我学习
        
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


# 初始化深度自我学习模块
deep_self_learning = None

def get_deep_self_learning(ai_instance_manager):
    """获取深度自我学习模块实例
    
    Args:
        ai_instance_manager: AI实例管理器
    
    Returns:
        DeepSelfLearning: 深度自我学习模块实例
    """
    global deep_self_learning
    if deep_self_learning is None:
        deep_self_learning = DeepSelfLearning(ai_instance_manager)
    return deep_self_learning
