# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
AI请求分类和优先级中间件
根据请求的内容和上下文自动分类和优先级排序
r"""

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

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - AI Request Classifier - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'logs/ai_request_classifier.log'),
        logging.StreamHandler()
    ])

class AIRequestClassifier:
    r"""AI请求分类和优先级类r"""

    def __init__(self):
        self.category_model = {
            r'vectorizer': TfidfVectorizer(max_features=1000),
            r'kmeans': KMeans(n_clusters=5, random_state=42),
            r'is_trained': False
        }

        self.request_data = []
        self.request_priorities = {}
        self.request_categories = {}

        self.config = {
            r'learning_interval': 3600,
            r'min_training_samples': 50,
            r'priority_levels': 5,
            r'category_names': [r'API', r'Web', r'Resource', r'Admin', r'Other'],
            r'admin_paths': [r'/admin', r'/api/admin'],
            r'resource_paths': [r'/static', r'/images', r'/files'],
            r'api_paths': [r'/api'],
            r'web_paths': [r'/', r'/home', r'/about', r'/contact'],
            r'priority_thresholds': {
                r'high': 0.8,
                r'medium': 0.5,
                r'low': 0.2
            }
        }

        self._start_learning_thread()

        logger.info(r"AI请求分类和优先级初始化完成")

    def _start_learning_thread(self):
        r"""启动AI学习线程r"""
        def learn_request_patterns():
            while True:
                time.sleep(self.config[r'learning_interval'])
                self._learn_request_patterns()

        learning_thread = threading.Thread(target=learn_request_patterns, daemon=True)
        learning_thread.start()

    def _learn_request_patterns(self):
        r"""学习请求模式r"""
        if len(self.request_data) < self.config[r'min_training_samples']:
            logger.debug(f"训练样本不足 ({len(self.request_data)} < {self.config[r'min_training_samples']})")
            return

        request_texts = [self._extract_request_features(req) for req in self.request_data]

        try:
            X = self.category_model[r'vectorizer'].fit_transform(request_texts)
            self.category_model[r'kmeans'].fit(X)
            self.category_model[r'is_trained'] = True

            logger.info(fr"成功训练请求分类模型,样本数: {len(self.request_data)}")
        except Exception as e:
            logger.error(fr"训练请求分类模型失败: {str(e)}")

    def _extract_request_features(self, request_info: Dict) -> str:
        r"""提取请求特征r"""
        features = [
            request_info[r'method'],
            request_info[r'path'],
            str(request_info[r'params']),
            str(request_info[r'headers'].get(r'User-Agent', r'')),
            str(request_info[r'headers'].get(r'Content-Type', r''))
        ]
        return r' '.join(features)

    def _get_request_signature(self):
        r"""生成请求签名r"""
        return fr"{request.method}:{request.path}:{request.remote_addr}"

    def _classify_request(self, request_info):
        r"""分类请求r"""
        return r"Other"

    def _calculate_priority(self, request_info, category):
        r"""计算优先级r"""
        return 3

    def ai_request_classifier_middleware(self, app):
        r"""AI请求分类和优先级中间件r"""
        @app.before_request
        def before_request():
            request_info = {
                r'method': request.method,
                r'path': request.path,
                r'params': request.args.to_dict(),
                r'headers': dict(request.headers),
                r'remote_addr': request.remote_addr,
                r'timestamp': time.time()
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

            logger.debug(fr"请求分类 - 签名: {request_signature}, 分类: {category}, 优先级: {priority}")

        @app.after_request
        def after_request(response):
            response.headers[r'X-Request-Category'] = g.get(r'request_category', r'Unknown')
            response.headers[r'X-Request-Priority'] = str(g.get(r'request_priority', 3))

            return response

        def get_classification_stats():
            r"""获取请求分类统计信息r"""
            category_counts = {}
            for category in self.request_categories.values():
                category_counts[category] = category_counts.get(category, 0) + 1

            priority_counts = {}
            for priority in self.request_priorities.values():
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            stats = {
                r'category_distribution': category_counts,
                r'priority_distribution': priority_counts,
                r'total_requests': len(self.request_data),
                r'model_trained': self.category_model[r'is_trained']
            }
            return stats

        logger.info(r"AI请求分类和优先级中间件注册完成")
        return app

    def clear_stats(self):
        r"""清除统计信息r"""
        self.request_data = []
        self.request_priorities = {}
        self.request_categories = {}


ai_request_classifier = AIRequestClassifier()


def ai_request_classifier_middleware(app):
    r"""AI请求分类和优先级中间件r"""
    return ai_request_classifier.ai_request_classifier_middleware(app)
