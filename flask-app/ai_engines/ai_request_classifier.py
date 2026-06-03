# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI请求分类和优先级中间件
根据请求的内容和上下文自动分类和优先级排序
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from app.utils.logging import logger
from flask import request, g

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AI Request Classifier - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_request_classifier.log'),
        logging.StreamHandler()
    ])

class AIRequestClassifier:
    """AI请求分类和优先级类"""

    def __init__(self):
        self.category_model = {
            'vectorizer': TfidfVectorizer(max_features=1000),
            'kmeans': KMeans(n_clusters=5, random_state=42),
            'is_trained': False
        }

        self.request_data = []
        self.request_priorities = {}
        self.request_categories = {}

        self.config = {
            'learning_interval': 3600,
            'min_training_samples': 50,
            'priority_levels': 5,
            'category_names': ['API', 'Web', 'Resource', 'Admin', 'Other'],
            'admin_paths': ['/admin', '/api/admin'],
            'resource_paths': ['/static', '/images', '/files'],
            'api_paths': ['/api'],
            'web_paths': ['/', '/home', '/about', '/contact'],
            'priority_thresholds': {
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2
            }
        }

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

        request_texts = [self._extract_request_features(req) for req in self.request_data]

        try:
            X = self.category_model['vectorizer'].fit_transform(request_texts)
            self.category_model['kmeans'].fit(X)
            self.category_model['is_trained'] = True

            logger.info(f"成功训练请求分类模型,样本数: {len(self.request_data)}")
        except Exception as e:
            logger.error(f"训练请求分类模型失败: {str(e)}")

    def _extract_request_features(self, request_info: Dict) -> str:
        """提取请求特征"""
        features = [
            request_info['method'],
            request_info['path'],
            str(request_info['params']),
            str(request_info['headers'].get('User-Agent', '')),
            str(request_info['headers'].get('Content-Type', ''))
        ]
        return ' '.join(features)

    def _get_request_signature(self):
        """生成请求签名"""
        return f"{request.method}:{request.path}:{request.remote_addr}"

    def _classify_request(self, request_info):
        """分类请求"""
        return "Other"

    def _calculate_priority(self, request_info, category):
        """计算优先级"""
        return 3

    def ai_request_classifier_middleware(self, app):
        """AI请求分类和优先级中间件"""
        @app.before_request
        def before_request():
            request_info = {
                'method': request.method,
                'path': request.path,
                'params': request.args.to_dict(),
                'headers': dict(request.headers),
                'remote_addr': request.remote_addr,
                'timestamp': time.time()
            }

            request_signature = self._get_request_signature()

            category, base_priority = self._classify_request(request_info), 3

            priority = self._calculate_priority(request_info, category)

            self.request_data.append(request_info)
            if len(self.request_data) > 1000:
                self.request_data = self.request_data[-1000:]

            self.request_categories[request_signature] = category
            self.request_priorities[request_signature] = priority

            g.request_category = category
            g.request_priority = priority

            logger.debug(f"请求分类 - 签名: {request_signature}, 分类: {category}, 优先级: {priority}")

        @app.after_request
        def after_request(response):
            response.headers['X-Request-Category'] = g.get('request_category', 'Unknown')
            response.headers['X-Request-Priority'] = str(g.get('request_priority', 3))

            return response

        def get_classification_stats():
            """获取请求分类统计信息"""
            category_counts = {}
            for category in self.request_categories.values():
                category_counts[category] = category_counts.get(category, 0) + 1

            priority_counts = {}
            for priority in self.request_priorities.values():
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            stats = {
                'category_distribution': category_counts,
                'priority_distribution': priority_counts,
                'total_requests': len(self.request_data),
                'model_trained': self.category_model['is_trained']
            }
            return stats

        logger.info("AI请求分类和优先级中间件注册完成")
        return app

    def clear_stats(self):
        """清除统计信息"""
        self.request_data = []
        self.request_priorities = {}
        self.request_categories = {}


ai_request_classifier = AIRequestClassifier()


def ai_request_classifier_middleware(app):
    """AI请求分类和优先级中间件"""
    return ai_request_classifier.ai_request_classifier_middleware(app)
