#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI情感分析服务
提供用户情绪识别和舆情监控功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict

logger = print

# 情感词典
POSITIVE_WORDS = [
    '好', '优秀', '喜欢', '满意', '棒', '赞', '完美', '出色', '开心', '高兴',
    '感谢', '谢谢', '便捷', '快速', '高效', '稳定', '安全', '推荐', '支持', '方便',
    'nice', 'great', 'good', 'excellent', 'perfect', 'love', 'like', 'awesome'
]

NEGATIVE_WORDS = [
    '差', '糟糕', '讨厌', '不满', '失望', '愤怒', '生气', '烦', '卡', '慢',
    '崩溃', '错误', '失败', '问题', 'bug', '难用', '复杂', '危险', '拒绝', '投诉',
    'bad', 'terrible', 'hate', 'worst', 'broken', 'fail', 'error', 'slow'
]

NEUTRAL_WORDS = [
    '一般', '普通', '正常', '还行', '可以', '普通', '了解', '知道', '明白', '收到'
]

EMOTION_MAP = {
    'happy': ['开心', '高兴', '快乐', '兴奋', '满意', '喜欢'],
    'angry': ['愤怒', '生气', '恼火', '气愤', '烦躁'],
    'sad': ['伤心', '难过', '失望', '沮丧', '悲伤'],
    'surprised': ['惊讶', '震惊', '意外', '想不到'],
    'fearful': ['害怕', '担心', '恐惧', '忧虑'],
    'disgusted': ['厌恶', '反感', '恶心'],
}


class SentimentResult:
    """情感分析结果"""

    def __init__(self, result_id: str, text: str, source: str = ''):
        self.result_id = result_id
        self.text = text
        self.source = source
        self.sentiment = 'neutral'  # positive, negative, neutral
        self.sentiment_score = 0.0  # -1.0 to 1.0
        self.confidence = 0.0
        self.emotion = 'neutral'
        self.emotion_scores: Dict[str, float] = {}
        self.keywords: List[str] = []
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'text': self.text[:100] + '...' if len(self.text) > 100 else self.text,
            'source': self.source,
            'sentiment': self.sentiment,
            'sentiment_score': round(self.sentiment_score, 4),
            'confidence': round(self.confidence, 4),
            'emotion': self.emotion,
            'emotion_scores': {k: round(v, 4) for k, v in self.emotion_scores.items()},
            'keywords': self.keywords,
            'created_at': self.created_at
        }


class AISentimentAnalysis:
    """AI情感分析服务"""

    def __init__(self):
        self.results: Dict[str, SentimentResult] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.max_history = 3000

        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_sentiment_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id TEXT NOT NULL UNIQUE,
                    text TEXT NOT NULL,
                    source TEXT,
                    sentiment TEXT DEFAULT 'neutral',
                    sentiment_score REAL DEFAULT 0,
                    confidence REAL DEFAULT 0,
                    emotion TEXT DEFAULT 'neutral',
                    emotion_scores TEXT,
                    keywords TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sentiment_result ON ai_sentiment_results(sentiment)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sentiment_source ON ai_sentiment_results(source)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[情感分析] 初始化数据库失败: {e}")

    def analyze(self, text: str, source: str = '') -> Dict[str, Any]:
        """分析文本情感"""
        import uuid
        result_id = f"sent_{uuid.uuid4().hex[:12]}"

        result = SentimentResult(result_id, text, source)

        text_lower = text.lower()

        # 1. 情感词匹配
        positive_count = sum(1 for w in POSITIVE_WORDS if w in text_lower)
        negative_count = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
        neutral_count = sum(1 for w in NEUTRAL_WORDS if w in text_lower)

        # 2. 计算情感分数
        total = positive_count + negative_count + neutral_count
        if total > 0:
            result.sentiment_score = (positive_count - negative_count) / total
        else:
            result.sentiment_score = 0.0

        # 3. 确定情感类别
        if result.sentiment_score > 0.2:
            result.sentiment = 'positive'
        elif result.sentiment_score < -0.2:
            result.sentiment = 'negative'
        else:
            result.sentiment = 'neutral'

        result.confidence = min(abs(result.sentiment_score) * 2, 1.0)

        # 4. 情绪识别
        emotion_scores = {}
        for emotion, words in EMOTION_MAP.items():
            score = sum(1 for w in words if w in text_lower)
            if score > 0:
                emotion_scores[emotion] = score / len(words)

        result.emotion_scores = emotion_scores

        if emotion_scores:
            result.emotion = max(emotion_scores, key=emotion_scores.get)
        else:
            result.emotion = 'neutral'

        # 5. 提取关键词
        all_words = POSITIVE_WORDS + NEGATIVE_WORDS + NEUTRAL_WORDS
        result.keywords = [w for w in all_words if w in text_lower]

        with self.lock:
            if len(self.results) >= self.max_history:
                oldest = min(self.results.values(), key=lambda r: r.created_at)
                self.results.pop(oldest.result_id, None)
            self.results[result_id] = result

        self._save_result_to_db(result)

        return result.to_dict()

    def batch_analyze(self, texts: List[str], source: str = '') -> List[Dict[str, Any]]:
        """批量分析"""
        return [self.analyze(text, source) for text in texts]

    def _save_result_to_db(self, result: SentimentResult):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_sentiment_results
                (result_id, text, source, sentiment, sentiment_score,
                 confidence, emotion, emotion_scores, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.result_id, result.text, result.source,
                result.sentiment, result.sentiment_score,
                result.confidence, result.emotion,
                json.dumps(result.emotion_scores),
                json.dumps(result.keywords)
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[情感分析] 保存结果失败: {e}")

    def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        result = self.results.get(result_id)
        return result.to_dict() if result else None

    def get_results(self, sentiment: str = None, source: str = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        with self.lock:
            results = list(self.results.values())

            if sentiment:
                results = [r for r in results if r.sentiment == sentiment]
            if source:
                results = [r for r in results if r.source == source]

            results.sort(key=lambda r: r.created_at, reverse=True)
            return [r.to_dict() for r in results[:limit]]

    def get_sentiment_stats(self, hours: int = 24,
                            source: str = None) -> Dict[str, Any]:
        """获取情感统计"""
        with self.lock:
            results = list(self.results.values())

            if source:
                results = [r for r in results if r.source == source]

            if not results:
                return {'total': 0}

            total = len(results)
            positive = sum(1 for r in results if r.sentiment == 'positive')
            negative = sum(1 for r in results if r.sentiment == 'negative')
            neutral = sum(1 for r in results if r.sentiment == 'neutral')

            avg_score = sum(r.sentiment_score for r in results) / total

            emotion_dist = defaultdict(int)
            for r in results:
                emotion_dist[r.emotion] += 1

            return {
                'total': total,
                'positive': positive,
                'negative': negative,
                'neutral': neutral,
                'positive_rate': round(positive / total * 100, 2),
                'negative_rate': round(negative / total * 100, 2),
                'avg_sentiment_score': round(avg_score, 4),
                'emotion_distribution': dict(emotion_dist)
            }

    def get_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取情感趋势"""
        with self.lock:
            trend = []
            now = datetime.now()

            for i in range(days):
                day = now - timedelta(days=i)
                day_str = day.strftime('%Y-%m-%d')

                day_results = [
                    r for r in self.results.values()
                    if r.created_at.startswith(day_str)
                ]

                if day_results:
                    avg_score = sum(r.sentiment_score for r in day_results) / len(day_results)
                    positive = sum(1 for r in day_results if r.sentiment == 'positive')
                else:
                    avg_score = 0
                    positive = 0

                trend.append({
                    'date': day_str,
                    'count': len(day_results),
                    'avg_score': round(avg_score, 4),
                    'positive_count': positive
                })

            trend.reverse()
            return trend

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_results': len(self.results)
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[情感分析] 情感分析服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[情感分析] 情感分析服务已停止")


ai_sentiment_analysis = AISentimentAnalysis()
