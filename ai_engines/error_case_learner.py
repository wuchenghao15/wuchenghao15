# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理案例学习器模块
自动学习存储系统相关的异常处理方法案例,提供AI预测功能
"""

import os
import logging
import re
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import json

logger = logging.getLogger('error_case_learner')


class ErrorCaseLearner:
    """异常处理案例学习器"""

    def __init__(self, error_cases_file: str = None):
        """初始化异常处理案例学习器"""
        self.error_cases_file = error_cases_file or os.path.join(
            os.path.dirname(__file__), 'brain', 'error_cases.json'
        )

        self.error_cases = []
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.classifier = KNeighborsClassifier(n_neighbors=5)
        self.clusterer = KMeans(n_clusters=10, random_state=42)
        self.pipeline = Pipeline([
            ('vectorizer', self.vectorizer),
            ('classifier', self.classifier)
        ])

        self._load_error_cases()
        self._train_model()

        logger.info("异常处理案例学习器初始化完成")

    def _load_error_cases(self):
        """加载错误案例"""
        try:
            if os.path.exists(self.error_cases_file):
                with open(self.error_cases_file, 'r', encoding='utf-8') as f:
                    self.error_cases = json.load(f)
                logger.info(f"错误案例加载成功: {len(self.error_cases)} 条")
            else:
                logger.warning(f"错误案例文件不存在: {self.error_cases_file}")
                self.error_cases = []
        except Exception as e:
            logger.error(f"加载错误案例失败: {str(e)}")
            self.error_cases = []

    def _extract_features(self, error_case: Dict[str, Any]) -> str:
        """提取错误案例特征"""
        text_parts = [
            error_case.get('title', ''),
            error_case.get('description', ''),
            error_case.get('solution', '')
        ]

        text = ' '.join(text_parts)
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _extract_labels(self, error_case: Dict[str, Any]) -> str:
        """提取错误案例标签"""
        return error_case.get('category', 'unknown')

    def _train_model(self):
        """训练模型"""
        if not self.error_cases:
            logger.warning("没有足够的错误案例进行训练")
            return

        try:
            texts = []
            labels = []

            for case in self.error_cases:
                text = self._extract_features(case)
                label = self._extract_labels(case)
                texts.append(text)
                labels.append(label)

            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42
            )

            self.pipeline.fit(X_train, y_train)

            y_pred = self.pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            logger.info(f"模型训练完成,准确率: {accuracy:.2f}")

            report = classification_report(y_test, y_pred, zero_division=0)
            logger.debug(f"分类报告:\n{report}")

            X = self.vectorizer.transform(texts)
            self.clusterer.fit(X)
            logger.info(f"聚类分析完成,簇数: {self.clusterer.n_clusters}")

        except Exception as e:
            logger.error(f"训练模型失败: {str(e)}")

    def predict_error_type(self, error_text: str) -> str:
        """预测错误类型"""
        try:
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', error_text)
            text = re.sub(r'\s+', ' ', text).strip()

            prediction = self.pipeline.predict([text])
            return prediction[0]
        except Exception as e:
            logger.error(f"预测错误类型失败: {str(e)}")
            return "unknown"

    def update_model(self):
        """更新模型"""
        try:
            self._load_error_cases()
            self._train_model()
            return True
        except Exception as e:
            logger.error(f"更新模型失败: {str(e)}")
            return False
