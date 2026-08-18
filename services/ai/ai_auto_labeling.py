#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI自动标注服务
提供基于规则和模型的自动标注、预标注功能
"""

import os
import sys
import json
import time
import re
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

# 标注规则库
LABELING_RULES = {
    'intent': {
        'question': [r'怎么', r'如何', r'什么', r'为什么', r'哪个', r'是否', r'吗', r'\?'],
        'command': [r'执行', r'运行', r'创建', r'删除', r'修改', r'更新', r'设置', r'启动'],
        'search': [r'搜索', r'查找', r'找', r'查询', r'检索'],
        'chat': [r'你好', r'hello', r'hi', r'谢谢', r'再见'],
    },
    'sentiment': {
        'positive': [r'好', r'优秀', r'满意', r'喜欢', r'棒', r'赞'],
        'negative': [r'差', r'糟糕', r'不满', r'失望', r'错误', r'失败'],
        'neutral': [r'一般', r'普通', r'正常', r'还行'],
    },
    'category': {
        'tech': [r'python', r'代码', r'程序', r'系统', r'api', r'数据库', r'服务器'],
        'business': [r'订单', r'客户', r'销售', r'收入', r'报表', r'统计'],
        'education': [r'课程', r'学习', r'考试', r'题目', r'知识点', r'教学'],
        'support': [r'帮助', r'问题', r'故障', r'修复', r'联系', r'客服'],
    },
    'priority': {
        'urgent': [r'紧急', r'立即', r'马上', r'critical', r'urgent'],
        'high': [r'重要', r'尽快', r'优先', r'high'],
        'normal': [r'一般', r'普通', r'normal'],
        'low': [r'不急', r'稍后', r'low'],
    },
    'language': {
        'zh': [r'[\u4e00-\u9fff]'],
        'en': [r'[a-zA-Z]'],
        'code': [r'```', r'def ', r'function', r'import ', r'var '],
    },
}


class LabelingResult:
    """标注结果"""

    def __init__(self, result_id: str, content: str):
        self.result_id = result_id
        self.content = content
        self.labels: Dict[str, Dict[str, float]] = {}
        self.primary_labels: Dict[str, str] = {}
        self.confidence: float = 0.0
        self.method: str = 'rule'  # rule, model, hybrid
        self.needs_review: bool = False
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'labels': self.labels,
            'primary_labels': self.primary_labels,
            'confidence': round(self.confidence, 4),
            'method': self.method,
            'needs_review': self.needs_review,
            'created_at': self.created_at
        }


class AIAutoLabeling:
    """AI自动标注服务"""

    def __init__(self):
        self.results: Dict[str, LabelingResult] = {}
        self.custom_rules: Dict[str, Dict[str, List[str]]] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.max_history = 2000

        self.review_threshold = 0.5  # 低于此置信度需人工审核

        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_labeling_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    labels TEXT,
                    primary_labels TEXT,
                    confidence REAL DEFAULT 0,
                    method TEXT DEFAULT 'rule',
                    needs_review INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_labeling_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL UNIQUE,
                    label_type TEXT NOT NULL,
                    label_value TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    is_enabled INTEGER DEFAULT 1
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[自动标注] 初始化数据库失败: {e}")

    def label(self, content: str, label_types: List[str] = None,
              method: str = 'rule') -> Dict[str, Any]:
        """自动标注"""
        import uuid
        result_id = f"lab_{uuid.uuid4().hex[:12]}"

        result = LabelingResult(result_id, content)
        result.method = method

        all_rules = {}
        all_rules.update(LABELING_RULES)
        all_rules.update(self.custom_rules)

        if label_types is None:
            label_types = list(all_rules.keys())

        for label_type in label_types:
            if label_type not in all_rules:
                continue

            type_scores: Dict[str, float] = {}
            type_rules = all_rules[label_type]

            for label_value, patterns in type_rules.items():
                score = 0.0

                for pattern in patterns:
                    try:
                        if re.search(pattern, content, re.IGNORECASE):
                            score += 1.0
                    except:
                        if pattern.lower() in content.lower():
                            score += 1.0

                if score > 0:
                    type_scores[label_value] = score

            if type_scores:
                # 归一化
                total = sum(type_scores.values())
                result.labels[label_type] = {
                    k: round(v / total, 4) for k, v in type_scores.items()
                }

                # 主标签
                primary = max(type_scores, key=type_scores.get)
                result.primary_labels[label_type] = primary

        # 计算总体置信度
        if result.primary_labels:
            avg_conf = sum(
                max(result.labels[lt].values())
                for lt in result.labels
            ) / len(result.labels)
            result.confidence = avg_conf

        # 是否需要人工审核
        result.needs_review = result.confidence < self.review_threshold

        with self.lock:
            if len(self.results) >= self.max_history:
                oldest = min(self.results.values(), key=lambda r: r.created_at)
                self.results.pop(oldest.result_id, None)
            self.results[result_id] = result

        self._save_result_to_db(result)

        return result.to_dict()

    def batch_label(self, contents: List[str],
                    label_types: List[str] = None) -> List[Dict[str, Any]]:
        """批量标注"""
        return [self.label(content, label_types) for content in contents]

    def _save_result_to_db(self, result: LabelingResult):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_labeling_results
                (result_id, content, labels, primary_labels,
                 confidence, method, needs_review)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.result_id, result.content,
                json.dumps(result.labels),
                json.dumps(result.primary_labels),
                result.confidence, result.method,
                1 if result.needs_review else 0
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[自动标注] 保存结果失败: {e}")

    def add_custom_rule(self, label_type: str, label_value: str,
                        patterns: List[str], weight: float = 1.0):
        """添加自定义标注规则"""
        with self.lock:
            if label_type not in self.custom_rules:
                self.custom_rules[label_type] = {}
            if label_value not in self.custom_rules[label_type]:
                self.custom_rules[label_type][label_value] = []

            self.custom_rules[label_type][label_value].extend(patterns)

        # 保存到数据库
        try:
            import uuid
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            for pattern in patterns:
                rule_id = f"rule_{uuid.uuid4().hex[:8]}"
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_labeling_rules
                    (rule_id, label_type, label_value, pattern, weight)
                    VALUES (?, ?, ?, ?, ?)
                ''', (rule_id, label_type, label_value, pattern, weight))

            conn.commit()
            conn.close()
        except:
            pass

        logger(f"[自动标注] 添加规则: {label_type}/{label_value}")

    def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        result = self.results.get(result_id)
        return result.to_dict() if result else None

    def get_results(self, label_type: str = None, needs_review: bool = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        with self.lock:
            results = list(self.results.values())

            if needs_review is not None:
                results = [r for r in results if r.needs_review == needs_review]

            if label_type:
                results = [r for r in results if label_type in r.primary_labels]

            results.sort(key=lambda r: r.created_at, reverse=True)
            return [r.to_dict() for r in results[:limit]]

    def get_label_distribution(self, label_type: str = None) -> Dict[str, Any]:
        """获取标签分布"""
        with self.lock:
            dist: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

            for result in self.results.values():
                for lt, primary in result.primary_labels.items():
                    if label_type and lt != label_type:
                        continue
                    dist[lt][primary] += 1

            return {
                lt: dict(v) for lt, v in dist.items()
            }

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total = len(self.results)
            reviewed = sum(1 for r in self.results.values() if not r.needs_review)
            pending = sum(1 for r in self.results.values() if r.needs_review)

            avg_conf = 0.0
            if results := list(self.results.values()):
                avg_conf = sum(r.confidence for r in results) / len(results)

            return {
                'total_labeled': total,
                'auto_approved': reviewed,
                'needs_review': pending,
                'review_rate': round(pending / max(1, total) * 100, 2),
                'avg_confidence': round(avg_conf, 4),
                'custom_rule_types': len(self.custom_rules)
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_results': len(self.results),
            'review_threshold': self.review_threshold
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[自动标注] 自动标注服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[自动标注] 自动标注服务已停止")


ai_auto_labeling = AIAutoLabeling()
