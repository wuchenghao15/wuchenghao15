# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intelligence Engine - 智能分析引擎
提供高级数据分析和模式识别能力
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import hashlib
import os

class PatternAnalyzer:
    """模式分析器 - 识别数据中的模式和趋势"""
    
    def __init__(self):
        self.patterns = []
        self.sequences = defaultdict(list)
    
    def detect_sequence(self, data: List[Any]) -> Dict[str, Any]:
        """检测序列模式"""
        if len(data) < 3:
            return {"pattern": "insufficient_data", "confidence": 0}
        
        # 检查等差数列
        if self._is_arithmetic(data):
            return {
                "pattern": "arithmetic",
                "difference": data[1] - data[0],
                "confidence": 0.95
            }
        
        # 检查等比数列
        if self._is_geometric(data):
            return {
                "pattern": "geometric",
                "ratio": data[1] / data[0] if data[0] != 0 else 0,
                "confidence": 0.95
            }
        
        # 检查周期性
        cycle = self._detect_periodicity(data)
        if cycle:
            return {
                "pattern": "periodic",
                "period": cycle,
                "confidence": 0.85
            }
        
        return {"pattern": "unknown", "confidence": 0}
    
    def _is_arithmetic(self, data: List) -> bool:
        """检查是否为等差数列"""
        if len(data) < 3:
            return False
        diff = data[1] - data[0]
        return all(data[i] - data[i-1] == diff for i in range(2, len(data)))
    
    def _is_geometric(self, data: List) -> bool:
        """检查是否为等比数列"""
        if len(data) < 3 or data[0] == 0:
            return False
        ratio = data[1] / data[0]
        return all(abs(data[i] / data[i-1] - ratio) < 0.0001 for i in range(2, len(data)))
    
    def _detect_periodicity(self, data: List) -> Optional[int]:
        """检测周期性"""
        n = len(data)
        for period in range(2, n // 2 + 1):
            matches = 0
            for i in range(n - period):
                if data[i] == data[i + period]:
                    matches += 1
            if matches >= (n - period) * 0.8:
                return period
        return None
    
    def analyze_frequency(self, data: List[Any]) -> Dict[str, Any]:
        """频率分析"""
        counter = Counter(data)
        total = len(data)
        
        return {
            "total_items": total,
            "unique_items": len(counter),
            "most_common": counter.most_common(10),
            "frequency_distribution": {
                item: count / total for item, count in counter.items()
            }
        }
    
    def detect_anomalies(self, data: List[float], threshold: float = 2.0) -> List[int]:
        """基于统计的异常检测"""
        if len(data) < 3:
            return []
        
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std_dev = variance ** 0.5
        
        anomalies = []
        for i, value in enumerate(data):
            z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
            if z_score > threshold:
                anomalies.append(i)
        
        return anomalies


class TextAnalyzer:
    """文本分析器 - 文本处理和分析"""
    
    def __init__(self):
        self.stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么'
        ])
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """提取关键词"""
        words = self._tokenize(text)
        words = [w for w in words if w not in self.stopwords and len(w) > 1]
        
        counter = Counter(words)
        total = sum(counter.values())
        
        keywords = []
        for word, count in counter.most_common(top_n):
            tf = count / total
            idf = 1.0
            score = tf * idf
            keywords.append((word, score))
        
        return keywords
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """简单摘要"""
        sentences = re.split(r'[。！？\n]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) <= max_sentences:
            return '。'.join(sentences)
        
        # 选择最长的句子作为摘要
        scored_sentences = [(s, len(s)) for s in sentences]
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        return '。'.join([s[0] for s in scored_sentences[:max_sentences]])
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """情感分析（简化版）"""
        positive_words = ['好', '优秀', '棒', '喜欢', '满意', '高兴', '开心', '赞', '支持', '感谢']
        negative_words = ['差', '糟糕', '坏', '不喜欢', '失望', '不满', '生气', '讨厌', '反对', '垃圾']
        
        words = self._tokenize(text)
        
        positive_count = sum(1 for w in words if w in positive_words)
        negative_count = sum(1 for w in words if w in negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            return {"sentiment": "neutral", "score": 0}
        
        score = (positive_count - negative_count) / total
        
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": score,
            "positive_count": positive_count,
            "negative_count": negative_count
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """实体提取（简化版）"""
        entities = {
            "person": [],
            "organization": [],
            "location": [],
            "time": []
        }
        
        # 简单的时间表达式
        time_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{1,2}月\d{1,2}日',
            r'\d+天',
            r'\d+小时'
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            entities["time"].extend(matches)
        
        # 简单的地名检测
        locations = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆']
        for loc in locations:
            if loc in text:
                entities["location"].append(loc)
        
        # 简单的人名检测（假设以先生/女士结尾）
        person_pattern = r'[\u4e00-\u9fa5]{2,4}(先生|女士|老师|教授)'
        matches = re.findall(person_pattern, text)
        entities["person"].extend([m[0] for m in matches])
        
        return entities


class DataClassifier:
    """数据分类器 - 自动分类和标签"""
    
    def __init__(self):
        self.categories = {
            "技术": ["代码", "程序", "系统", "算法", "数据库", "网络", "软件", "硬件"],
            "教育": ["学习", "课程", "教学", "学生", "老师", "学校", "考试", "作业"],
            "商业": ["公司", "市场", "销售", "客户", "产品", "服务", "营销", "利润"],
            "生活": ["生活", "家庭", "健康", "娱乐", "旅游", "购物", "美食", "运动"],
            "金融": ["投资", "股票", "基金", "银行", "保险", "理财", "财务", "资产"]
        }
    
    def classify(self, text: str) -> Dict[str, Any]:
        """文本分类"""
        words = set(text)
        scores = {}
        
        for category, keywords in self.categories.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score
        
        if not scores or max(scores.values()) == 0:
            return {"category": "未分类", "confidence": 0, "scores": scores}
        
        best_category = max(scores.items(), key=lambda x: x[1])
        
        return {
            "category": best_category[0],
            "confidence": best_category[1] / sum(scores.values()) if sum(scores.values()) > 0 else 0,
            "scores": scores
        }
    
    def suggest_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """建议标签"""
        all_keywords = []
        for keywords in self.categories.values():
            all_keywords.extend(keywords)
        
        tags = [kw for kw in all_keywords if kw in text]
        return tags[:max_tags]


class IntelligenceEngine:
    """智能分析引擎 - 统一接口"""
    
    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
        self.text_analyzer = TextAnalyzer()
        self.classifier = DataClassifier()
        self.cache = {}
    
    def analyze_data(self, data: List[Any], analysis_type: str = "auto") -> Dict[str, Any]:
        """综合数据分析"""
        if analysis_type == "auto":
            if all(isinstance(x, (int, float)) for x in data):
                analysis_type = "numeric"
            elif all(isinstance(x, str) for x in data):
                analysis_type = "text"
            else:
                analysis_type = "mixed"
        
        result = {
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "data_size": len(data)
        }
        
        if analysis_type == "numeric":
            result["sequence"] = self.pattern_analyzer.detect_sequence(data)
            result["frequency"] = self.pattern_analyzer.analyze_frequency(data)
            result["anomalies"] = self.pattern_analyzer.detect_anomalies(data)
            result["statistics"] = self._calculate_statistics(data)
        
        elif analysis_type == "text":
            combined_text = " ".join(data)
            result["keywords"] = self.text_analyzer.extract_keywords(combined_text)
            result["entities"] = self.text_analyzer.extract_entities(combined_text)
            result["sentiment"] = self.text_analyzer.analyze_sentiment(combined_text)
        
        elif analysis_type == "mixed":
            result["frequency"] = self.pattern_analyzer.analyze_frequency(data)
        
        return result
    
    def _calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """计算统计信息"""
        if not data:
            return {}
        
        sorted_data = sorted(data)
        n = len(data)
        
        mean = sum(data) / n
        variance = sum((x - mean) ** 2 for x in data) / n
        std_dev = variance ** 0.5
        
        median = sorted_data[n // 2] if n % 2 == 1 else (sorted_data[n//2-1] + sorted_data[n//2]) / 2
        
        return {
            "mean": mean,
            "median": median,
            "std_dev": std_dev,
            "min": min(data),
            "max": max(data),
            "range": max(data) - min(data)
        }
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """处理文本"""
        return {
            "keywords": self.text_analyzer.extract_keywords(text),
            "entities": self.text_analyzer.extract_entities(text),
            "sentiment": self.text_analyzer.analyze_sentiment(text),
            "classification": self.classifier.classify(text),
            "tags": self.classifier.suggest_tags(text),
            "summary": self.text_analyzer.summarize(text)
        }
    
    def predict_next_value(self, data: List[float], steps: int = 1) -> List[float]:
        """预测下一个值"""
        if len(data) < 3:
            return []
        
        # 检测等差数列
        if self.pattern_analyzer._is_arithmetic(data):
            diff = data[1] - data[0]
            predictions = []
            last = data[-1]
            for _ in range(steps):
                last += diff
                predictions.append(last)
            return predictions
        
        # 检测等比数列
        if self.pattern_analyzer._is_geometric(data):
            ratio = data[1] / data[0] if data[0] != 0 else 0
            predictions = []
            last = data[-1]
            for _ in range(steps):
                last *= ratio
                predictions.append(last)
            return predictions
        
        # 线性回归
        n = len(data)
        x_mean = sum(range(n)) / n
        y_mean = sum(data) / n
        
        numerator = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return [data[-1]] * steps
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        predictions = []
        for i in range(steps):
            predictions.append(slope * (n + i) + intercept)
        
        return predictions


# 全局实例
intelligence = IntelligenceEngine()
