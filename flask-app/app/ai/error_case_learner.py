#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理案例学习器模块
自动学习存储系统相关的异常处理方法案例，提供AI预测功能
"""

import os
import json
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

# 配置日志
logger = logging.getLogger('error_case_learner')

class ErrorCaseLearner:
    """异常处理案例学习器"""
    
    def __init__(self, error_cases_file: str = None):
        """初始化异常处理案例学习器"""
        # 错误案例文件路径
        self.error_cases_file = error_cases_file or os.path.join(
            os.path.dirname(__file__), 'brain', 'error_cases.json'
        )
        
        # 错误案例数据
        self.error_cases = []
        
        # 特征提取器
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        
        # 分类器
        self.classifier = KNeighborsClassifier(n_neighbors=5)
        
        # 聚类器
        self.clusterer = KMeans(n_clusters=10, random_state=42)
        
        # 训练管道
        self.pipeline = Pipeline([
            ('vectorizer', self.vectorizer),
            ('classifier', self.classifier)
        ])
        
        # 加载错误案例
        self._load_error_cases()
        
        # 训练模型
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
        # 提取标题、描述和解决方案中的文本
        text_parts = [
            error_case.get('title', ''),
            error_case.get('description', ''),
            error_case.get('solution', '')
        ]
        
        # 合并文本
        text = ' '.join(text_parts)
        
        # 清理文本
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_labels(self, error_case: Dict[str, Any]) -> str:
        """提取错误案例标签"""
        # 从标题中提取错误类型
        title = error_case.get('title', '')
        match = re.match(r'(.+?)异常:', title)
        if match:
            return match.group(1)
        return '未知错误'
    
    def _train_model(self):
        """训练模型"""
        if not self.error_cases:
            logger.warning("没有足够的错误案例进行训练")
            return
        
        try:
            # 提取特征和标签
            texts = []
            labels = []
            
            for case in self.error_cases:
                text = self._extract_features(case)
                label = self._extract_labels(case)
                texts.append(text)
                labels.append(label)
            
            # 分割训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42
            )
            
            # 训练模型
            self.pipeline.fit(X_train, y_train)
            
            # 评估模型
            y_pred = self.pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            logger.info(f"模型训练完成，准确率: {accuracy:.2f}")
            
            # 打印分类报告
            report = classification_report(y_test, y_pred, zero_division=0)
            logger.debug(f"分类报告:\n{report}")
            
            # 聚类分析
            X = self.vectorizer.transform(texts)
            self.clusterer.fit(X)
            logger.info(f"聚类分析完成，簇数: {self.clusterer.n_clusters}")
            
        except Exception as e:
            logger.error(f"训练模型失败: {str(e)}")
    
    def predict_error_type(self, error_text: str) -> str:
        """预测错误类型"""
        try:
            # 清理文本
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', error_text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 预测错误类型
            prediction = self.pipeline.predict([text])
            return prediction[0]
        except Exception as e:
            logger.error(f"预测错误类型失败: {str(e)}")
            return '未知错误'
    
    def predict_solution(self, error_text: str) -> str:
        """预测解决方案"""
        try:
            # 清理文本
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', error_text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 提取特征
            X = self.vectorizer.transform([text])
            
            # 找到最相似的错误案例
            distances, indices = self.classifier.kneighbors(X, n_neighbors=3)
            
            # 提取解决方案
            solutions = []
            for idx in indices[0]:
                if idx < len(self.error_cases):
                    solutions.append(self.error_cases[idx].get('solution', ''))
            
            # 合并解决方案
            if solutions:
                # 去重并排序
                unique_solutions = list(set(solutions))
                # 返回最常见的解决方案
                return unique_solutions[0]
            return "检查异常信息，根据具体情况进行修复"
        except Exception as e:
            logger.error(f"预测解决方案失败: {str(e)}")
            return "检查异常信息，根据具体情况进行修复"
    
    def cluster_analysis(self) -> Dict[str, Any]:
        """聚类分析"""
        try:
            if not self.error_cases:
                return {}
            
            # 提取特征
            texts = []
            for case in self.error_cases:
                text = self._extract_features(case)
                texts.append(text)
            
            X = self.vectorizer.transform(texts)
            
            # 聚类
            labels = self.clusterer.fit_predict(X)
            
            # 分析每个簇的特征
            clusters = {}
            for i, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(self.error_cases[i])
            
            # 生成聚类分析报告
            report = {
                'total_clusters': len(clusters),
                'clusters': {}
            }
            
            for cluster_id, cases in clusters.items():
                # 提取簇的特征
                cluster_texts = []
                for case in cases:
                    cluster_texts.append(self._extract_features(case))
                
                # 计算簇的中心
                cluster_center = self.clusterer.cluster_centers_[cluster_id]
                
                # 找出最接近中心的案例
                distances = np.linalg.norm(X.toarray() - cluster_center, axis=1)
                closest_idx = np.argmin(distances)
                closest_case = self.error_cases[closest_idx]
                
                report['clusters'][cluster_id] = {
                    'size': len(cases),
                    'representative_case': closest_case,
                    'error_types': list(set([self._extract_labels(case) for case in cases]))
                }
            
            return report
        except Exception as e:
            logger.error(f"聚类分析失败: {str(e)}")
            return {}
    
    def get_recommendations(self, error_text: str) -> List[Dict[str, Any]]:
        """获取推荐解决方案"""
        try:
            # 清理文本
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', error_text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 提取特征
            X = self.vectorizer.transform([text])
            
            # 找到最相似的错误案例
            distances, indices = self.classifier.kneighbors(X, n_neighbors=5)
            
            # 提取推荐案例
            recommendations = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.error_cases):
                    case = self.error_cases[idx]
                    recommendations.append({
                        'id': case.get('id'),
                        'title': case.get('title'),
                        'solution': case.get('solution'),
                        'similarity': 1 - distances[0][i]  # 转换为相似度
                    })
            
            # 按相似度排序
            recommendations.sort(key=lambda x: x['similarity'], reverse=True)
            
            return recommendations
        except Exception as e:
            logger.error(f"获取推荐解决方案失败: {str(e)}")
            return []
    
    def update_model(self):
        """更新模型"""
        try:
            # 重新加载错误案例
            self._load_error_cases()
            
            # 重新训练模型
            self._train_model()
            
            logger.info("模型更新完成")
            return True
        except Exception as e:
            logger.error(f"更新模型失败: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = {
                'total_cases': len(self.error_cases),
                'error_types': {},
                'last_updated': datetime.now().isoformat()
            }
            
            # 统计错误类型
            for case in self.error_cases:
                error_type = self._extract_labels(case)
                if error_type not in stats['error_types']:
                    stats['error_types'][error_type] = 0
                stats['error_types'][error_type] += 1
            
            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}

# 创建全局异常处理案例学习器实例
error_case_learner = ErrorCaseLearner()

if __name__ == '__main__':
    print("异常处理案例学习器初始化成功")
    print(f"错误案例数量: {len(error_case_learner.error_cases)}")
    
    # 测试预测功能
    test_error = "文件不存在: app/config/config.py"
    error_type = error_case_learner.predict_error_type(test_error)
    solution = error_case_learner.predict_solution(test_error)
    
    print(f"测试错误: {test_error}")
    print(f"预测错误类型: {error_type}")
    print(f"预测解决方案: {solution}")
    
    # 测试推荐功能
    recommendations = error_case_learner.get_recommendations(test_error)
    print(f"推荐解决方案数量: {len(recommendations)}")
    if recommendations:
        print("最相似的解决方案:")
        for i, rec in enumerate(recommendations[:3]):
            print(f"{i+1}. {rec['title']} (相似度: {rec['similarity']:.2f})")
            print(f"   解决方案: {rec['solution']}")
    
    # 测试聚类分析
    cluster_report = error_case_learner.cluster_analysis()
    print(f"聚类分析结果: {cluster_report.get('total_clusters', 0)} 个簇")
