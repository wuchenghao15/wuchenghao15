#!/usr/bin/env python3
"""
AI请求分类和优先级中间件
根据请求的内容和上下文自动分类和优先级排序

import os
import time
# JSON import removed - using database
import logging
import threading
from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from app.utils.logging import logger
from flask import request, g

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AI Request Classifier - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_request_classifier.log'),
        logging.StreamHandler()
    ]
)

class AIRequestClassifier:
    """AI请求分类和优先级类"""

    def __init__(self):
        # 请求分类模型
        self.category_model = {
            'vectorizer': TfidfVectorizer(max_features=1000),
            'kmeans': KMeans(n_clusters=5, random_state=42),
            'is_trained': False
        }

        # 请求数据用于训练
        self.request_data = []
        # 请求优先级映射，格式：{request_signature: priority}
        self.request_priorities = {}
        # 请求分类历史，格式：{request_signature: category}
        self.request_categories = {}

        # 智能分类配置
        self.config = {
            'learning_interval': 3600,  # 学习间隔（秒）
            'min_training_samples': 50,  # 最小训练样本数
            'priority_levels': 5,  # 优先级级别数（1-5）
            'category_names': ['API', 'Web', 'Resource', 'Admin', 'Other'],  # 分类名称
            'admin_paths': ['/admin', '/api/admin'],  # 管理员路径
            'resource_paths': ['/static', '/images', '/files'],  # 资源路径
            'api_paths': ['/api'],  # API路径
            'web_paths': ['/', '/home', '/about', '/contact'],  # Web页面路径
            'priority_thresholds': {
                'high': 0.8,  # 高优先级阈值
                'medium': 0.5,  # 中优先级阈值
                'low': 0.2  # 低优先级阈值
            }
        # 启动AI学习线程
        self._start_learning_thread()

        logger.info("AI请求分类和优先级初始化完成")

    def _start_learning_thread(self):
        """启动AI学习线程"""
        def learn_request_patterns():
            while True:
                time.sleep(self.config['learning_interval'])
                self._learn_request_patterns()

        learning_thread = threading.Thread(target=learn_request_patterns, daemon=True)
        learning_thread.start()

    def _learn_request_patterns(self):
        """学习请求模式"""
        if len(self.request_data) < self.config['min_training_samples']:
            logger.debug(f"训练样本不足 ({len(self.request_data)} < {self.config['min_training_samples']})")
            return

        # 提取请求特征
        request_texts = [self._extract_request_features(req) for req in self.request_data]

        # 训练分类模型
        try:
            # 向量化请求文本
            X = self.category_model['vectorizer'].fit_transform(request_texts)
            # 聚类请求
            self.category_model['kmeans'].fit(X)
            self.category_model['is_trained'] = True

            logger.info(f"成功训练请求分类模型，样本数: {len(self.request_data)}")
        except Exception as e:
            logger.error(f"训练请求分类模型失败: {str(e)}")

    def _extract_request_features(self, request_info: Dict) -> str:
        """提取请求特征"""
        # 组合请求方法、路径、参数等作为特征
        features = [
            request_info['method'],
            request_info['path'],
            str(request_info['params']),
            str(request_info['headers'].get('User-Agent', '')),
            str(request_info['headers'].get('Content-Type', ''))
        ]
        return ' '.join(features)

    def _classify_request(self, request_info: Dict) -> Tuple[str, int]:
        """分类请求"""
        # 1. 基于路径的简单分类
        path = request_info['path']

        for admin_path in self.config['admin_paths']:
            if path.startswith(admin_path):
                return ('Admin', 4)  # 高优先级

        for api_path in self.config['api_paths']:
            if path.startswith(api_path):
                return ('API', 3)  # 中高优先级

        for resource_path in self.config['resource_paths']:
            if path.startswith(resource_path):
                return ('Resource', 2)  # 中优先级

        for web_path in self.config['web_paths']:
            if path.startswith(web_path):
                return ('Web', 2)  # 中优先级

        # 2. 使用AI模型分类（如果已训练）
        if self.category_model['is_trained']:
            try:
                request_text = self._extract_request_features(request_info)
                X = self.category_model['vectorizer'].transform([request_text])
                cluster = self.category_model['kmeans'].predict(X)[0]
                # 映射聚类结果到分类名称
                category = self.config['category_names'][min(cluster, len(self.config['category_names']) - 1)]
                return (category, 2)  # 默认中优先级
            except Exception as e:
                logger.error(f"AI分类请求失败: {str(e)}")

        # 默认分类
        return ('Other', 1)  # 低优先级
    def _calculate_priority(self, request_info: Dict, category: str) -> int:
        """计算请求优先级"""
        # 基础优先级基于分类
        base_priority = {
            'Admin': 4,
            'API': 3,
            'Resource': 2,
            'Web': 2,
            'Other': 1
        }.get(category, 1)

        # 动态调整优先级
        priority_score = base_priority

        # 1. 考虑请求方法
        if request_info['method'] in ['POST', 'PUT', 'DELETE']:
            priority_score += 0.5  # 写入操作优先级更高

        # 2. 考虑请求大小
        content_length = int(request_info['headers'].get('Content-Length', 0))
        if content_length > 1024 * 1024:  # 大于1MB的请求
            priority_score -= 0.5  # 大请求优先级降低

        # 3. 考虑用户代理
        user_agent = request_info['headers'].get('User-Agent', '')
        if 'bot' in user_agent.lower() or 'crawler' in user_agent.lower():
            priority_score -= 1.0  # 爬虫优先级降低

        # 4. 考虑认证状态
        if request_info['headers'].get('Authorization') or request_info['headers'].get('Cookie'):
            priority_score += 0.5  # 认证用户优先级更高

        # 确保优先级在1-5范围内
        final_priority = max(1, min(5, round(priority_score)))

        return final_priority

    def _get_request_signature(self):
        """生成请求签名"""
        return f"{request.method}:{request.path}:{request.remote_addr}"

    def ai_request_classifier_middleware(self, app):
        """AI请求分类和优先级中间件"""
        @app.before_request
        def before_request():
            # 收集请求信息
            request_info = {
                'method': request.method,
                'path': request.path,
                'params': request.args.to_dict(),
                'headers': dict(request.headers),
                'remote_addr': request.remote_addr,
                'timestamp': time.time()
            }

            request_signature = self._get_request_signature()

            # 分类请求
            category, base_priority = self._classify_request(request_info)

            # 计算优先级
            priority = self._calculate_priority(request_info, category)

            # 存储请求信息用于学习
            self.request_data.append(request_info)
            # 限制训练数据大小
            if len(self.request_data) > 1000:
                self.request_data = self.request_data[-1000:]

            # 存储请求分类和优先级
            self.request_categories[request_signature] = category
            self.request_priorities[request_signature] = priority

            # 将分类和优先级存储到g对象
            g.request_category = category
            g.request_priority = priority

            logger.debug(f"请求分类 - 签名: {request_signature}, 分类: {category}, 优先级: {priority}")

        @app.after_request
        def after_request(response):
            # 添加分类和优先级到响应头
            response.headers['X-Request-Category'] = g.request_category
            response.headers['X-Request-Priority'] = str(g.request_priority)

            return response

        # 添加请求分类统计API
        @app.route('/api/classification/stats')
        def get_classification_stats():
            """获取请求分类统计信息"""
            # 计算分类分布
            category_counts = {}
            for category in self.request_categories.values():
                category_counts[category] = category_counts.get(category, 0) + 1

            # 计算优先级分布
            priority_counts = {}
            for priority in self.request_priorities.values():
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            stats = {
                'category_distribution': category_counts,
                'priority_distribution': priority_counts,
                'total_requests': len(self.request_data),
                'model_trained': self.category_model['is_trained']
            }


        logger.info("AI请求分类和优先级中间件注册完成")
        return app

    def get_classification_stats(self) -> Dict:
        """获取分类统计信息"""
        category_counts = {}
        for category in self.request_categories.values():
            category_counts[category] = category_counts.get(category, 0) + 1

        return category_counts

    def get_priority_stats(self) -> Dict:
        """获取优先级统计信息"""
        for priority in self.request_priorities.values():


    def clear_stats(self):
        """清除统计信息"""
        self.request_data = []
        self.request_priorities = {}
        self.request_categories = {}

ai_request_classifier = AIRequestClassifier()
    """AI请求分类和优先级中间件"""
    return ai_request_classifier.ai_request_classifier_middleware(app)


# 优先级配置
ai_request_classifier_priority = 25
