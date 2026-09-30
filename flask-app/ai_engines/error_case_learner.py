# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
异常处理案例学习器模块
自动学习存储系统相关的异常处理方法案例,提供AI预测功能
r"""

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

logger = logging.getLogger(r'error_case_learner')


class ErrorCaseLearner:
    r"""异常处理案例学习器r"""

    def __init__(self, error_cases_file: str = None):
        r"""初始化异常处理案例学习器r"""
        self.error_cases_file = error_cases_file or os.path.join(
            os.path.dirname(__file__), r'brain', r'error_cases.json'
        )

        self.error_cases = []
        self.vectorizer = TfidfVectorizer(stop_words=r'english', max_features=1000)
        self.classifier = KNeighborsClassifier(n_neighbors=5)
        self.clusterer = KMeans(n_clusters=10, random_state=42)
        self.pipeline = Pipeline([
            (r'vectorizer', self.vectorizer),
            (r'classifier', self.classifier)
        ])

        self._load_error_cases()
        self._train_model()

        logger.info(r"异常处理案例学习器初始化完成")

    def _load_error_cases(self):
        r"""加载错误案例r"""
        try:
            if os.path.exists(self.error_cases_file):
                with open(self.error_cases_file, r'r', encoding=r'utf-8') as f:
                    self.error_cases = json.load(f)
                logger.info(fr"错误案例加载成功: {len(self.error_cases)} 条")
            else:
                logger.warning(fr"错误案例文件不存在: {self.error_cases_file}")
                self.error_cases = []
        except Exception as e:
            logger.error(fr"加载错误案例失败: {str(e)}")
            self.error_cases = []

    def _extract_features(self, error_case: Dict[str, Any]) -> str:
        r"""提取错误案例特征r"""
        text_parts = [
            error_case.get(r'title', r''),
            error_case.get(r'description', r''),
            error_case.get(r'solution', r'')
        ]

        text = r' '.join(text_parts)
        text = re.sub(r'[^a-zA-Z0-9\s]', r' ', text)
        text = re.sub(r'\s+', r' ', text).strip()

        return text

    def _extract_labels(self, error_case: Dict[str, Any]) -> str:
        r"""提取错误案例标签r"""
        return error_case.get(r'category', r'unknown')

    def _train_model(self):
        r"""训练模型r"""
        if not self.error_cases:
            logger.warning(r"没有足够的错误案例进行训练")
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
            logger.info(fr"模型训练完成,准确率: {accuracy:.2f}")

            report = classification_report(y_test, y_pred, zero_division=0)
            logger.debug(fr"分类报告:\n{report}")

            X = self.vectorizer.transform(texts)
            self.clusterer.fit(X)
            logger.info(fr"聚类分析完成,簇数: {self.clusterer.n_clusters}")

        except Exception as e:
            logger.error(fr"训练模型失败: {str(e)}")

    def predict_error_type(self, error_text: str) -> str:
        r"""预测错误类型r"""
        try:
            text = re.sub(r'[^a-zA-Z0-9\s]', r' ', error_text)
            text = re.sub(r'\s+', r' ', text).strip()

            prediction = self.pipeline.predict([text])
            return prediction[0]
        except Exception as e:
            logger.error(fr"预测错误类型失败: {str(e)}")
            return r"unknown"

    def update_model(self):
        r"""更新模型r"""
        try:
            self._load_error_cases()
            self._train_model()
            return True
        except Exception as e:
            logger.error(fr"更新模型失败: {str(e)}")
            return False
