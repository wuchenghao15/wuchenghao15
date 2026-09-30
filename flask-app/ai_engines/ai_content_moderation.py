#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI内容审核服务
提供文本和图片内容的安全检测
"""

import os
import sys
import json
import time
import re
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = print

# 敏感词库（示例）
SENSITIVE_WORDS = {
    'violence': ['暴力', '打杀', '攻击', '伤害', '武器', '炸弹', '枪支'],
    'pornography': ['色情', '裸体', '性', '成人'],
    'gambling': ['赌博', '赌场', '下注', '博彩', '赌资'],
    'drug': ['毒品', '大麻', '可卡因', '海洛因', '冰毒'],
    'insult': ['愚蠢', '白痴', '废物', '滚蛋', '去死'],
    'politics': ['反动', '颠覆', '分裂'],
    'advertising': ['免费领取', '点击链接', '加微信', '优惠折扣', '代购'],
}

# 正则规则
REGEX_PATTERNS = {
    'phone': re.compile(r'1[3-9]\d{9}'),
    'id_card': re.compile(r'\d{17}[\dXx]'),
    'bank_card': re.compile(r'\d{16,19}'),
    'email': re.compile(r'[\w.-]+@[\w.-]+\.\w+'),
    'url': re.compile(r'https?://[^\s]+'),
    'ip': re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
}


class ModerationResult:
    """审核结果"""

    def __init__(self, content_id: str, content: str,
                 content_type: str = 'text'):
        self.content_id = content_id
        self.content = content
        self.content_type = content_type
        self.is_safe = True
        self.risk_level = 'safe'  # safe, low, medium, high, critical
        self.risk_score = 0.0
        self.categories: List[Dict[str, Any]] = []
        self.matched_rules: List[Dict[str, Any]] = []
        self.privacy_issues: List[Dict[str, Any]] = []
        self.review_status = 'auto'  # auto, pending, approved, rejected
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content_id': self.content_id,
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'content_type': self.content_type,
            'is_safe': self.is_safe,
            'risk_level': self.risk_level,
            'risk_score': round(self.risk_score, 4),
            'categories': self.categories,
            'matched_rules': self.matched_rules,
            'privacy_issues': self.privacy_issues,
            'review_status': self.review_status,
            'created_at': self.created_at
        }


class AIContentModeration:
    """AI内容审核服务"""

    def __init__(self):
        self.results: Dict[str, ModerationResult] = {}
        self.custom_words: Dict[str, List[str]] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.max_history = 2000

        self.auto_block_threshold = 0.7
        self.auto_review_threshold = 0.3

        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_moderation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    is_safe INTEGER DEFAULT 1,
                    risk_level TEXT DEFAULT 'safe',
                    risk_score REAL DEFAULT 0,
                    categories TEXT,
                    matched_rules TEXT,
                    privacy_issues TEXT,
                    review_status TEXT DEFAULT 'auto',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_moderation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    is_enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_moderation_risk ON ai_moderation_results(risk_level)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[内容审核] 初始化数据库失败: {e}")

    def moderate_text(self, content: str, strict_mode: bool = False) -> Dict[str, Any]:
        """审核文本内容"""
        import uuid
        content_id = f"mod_{uuid.uuid4().hex[:12]}"

        result = ModerationResult(content_id, content, 'text')

        # 1. 敏感词检测
        all_words = {}
        all_words.update(SENSITIVE_WORDS)
        all_words.update(self.custom_words)

        for category, words in all_words.items():
            for word in words:
                if word in content:
                    result.matched_rules.append({
                        'type': 'keyword',
                        'category': category,
                        'pattern': word,
                        'weight': 1.0 if category in ('violence', 'pornography', 'drug') else 0.5
                    })

        # 2. 正则规则检测
        for rule_name, pattern in REGEX_PATTERNS.items():
            matches = pattern.findall(content)
            if matches:
                result.privacy_issues.append({
                    'type': rule_name,
                    'count': len(matches),
                    'severity': 'high' if rule_name in ('id_card', 'bank_card') else 'medium'
                })

        # 3. 计算风险分数
        total_score = 0.0
        category_scores: Dict[str, float] = {}

        for rule in result.matched_rules:
            cat = rule['category']
            category_scores[cat] = category_scores.get(cat, 0) + rule['weight']
            total_score += rule['weight']

        for issue in result.privacy_issues:
            severity_weight = 0.8 if issue['severity'] == 'high' else 0.4
            total_score += severity_weight

        # 归一化
        result.risk_score = min(total_score / 10.0, 1.0)

        # 风险级别
        if result.risk_score >= self.auto_block_threshold:
            result.risk_level = 'critical' if result.risk_score >= 0.9 else 'high'
            result.is_safe = False
            result.review_status = 'rejected'
        elif result.risk_score >= self.auto_review_threshold:
            result.risk_level = 'medium' if result.risk_score >= 0.5 else 'low'
            result.review_status = 'pending' if strict_mode else 'auto'
        else:
            result.risk_level = 'safe'
            result.is_safe = True
            result.review_status = 'approved'

        result.categories = [
            {'category': k, 'score': round(v, 2)}
            for k, v in sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        ]

        with self.lock:
            if len(self.results) >= self.max_history:
                oldest = min(self.results.values(), key=lambda r: r.created_at)
                self.results.pop(oldest.content_id, None)
            self.results[content_id] = result

        self._save_result_to_db(result)

        return result.to_dict()

    def moderate_image(self, image_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """审核图片内容（模拟）"""
        import uuid
        content_id = f"img_{uuid.uuid4().hex[:12]}"

        result = ModerationResult(content_id, image_url, 'image')

        # 模拟图片审核
        result.risk_score = 0.1
        result.risk_level = 'safe'
        result.is_safe = True
        result.review_status = 'approved'

        if metadata and metadata.get('source') == 'upload':
            result.risk_score = 0.2
            result.risk_level = 'low'
            result.review_status = 'auto'

        with self.lock:
            self.results[content_id] = result

        self._save_result_to_db(result)

        return result.to_dict()

    def _save_result_to_db(self, result: ModerationResult):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_moderation_results
                (content_id, content, content_type, is_safe, risk_level,
                 risk_score, categories, matched_rules, privacy_issues, review_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.content_id, result.content, result.content_type,
                1 if result.is_safe else 0, result.risk_level,
                result.risk_score, json.dumps(result.categories),
                json.dumps(result.matched_rules),
                json.dumps(result.privacy_issues),
                result.review_status
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[内容审核] 保存结果失败: {e}")

    def add_custom_words(self, category: str, words: List[str]):
        """添加自定义敏感词"""
        with self.lock:
            if category not in self.custom_words:
                self.custom_words[category] = []
            self.custom_words[category].extend(words)

        logger(f"[内容审核] 添加自定义词库: {category} ({len(words)} 个)")

    def batch_moderate(self, contents: List[str]) -> List[Dict[str, Any]]:
        """批量审核"""
        return [self.moderate_text(content) for content in contents]

    def get_result(self, content_id: str) -> Optional[Dict[str, Any]]:
        result = self.results.get(content_id)
        return result.to_dict() if result else None

    def get_results(self, risk_level: str = None, is_safe: bool = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        with self.lock:
            results = list(self.results.values())

            if risk_level:
                results = [r for r in results if r.risk_level == risk_level]
            if is_safe is not None:
                results = [r for r in results if r.is_safe == is_safe]

            results.sort(key=lambda r: r.created_at, reverse=True)
            return [r.to_dict() for r in results[:limit]]

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        with self.lock:
            total = len(self.results)
            safe = sum(1 for r in self.results.values() if r.is_safe)
            blocked = sum(1 for r in self.results.values() if r.review_status == 'rejected')
            pending = sum(1 for r in self.results.values() if r.review_status == 'pending')

            risk_dist = {}
            for r in self.results.values():
                risk_dist[r.risk_level] = risk_dist.get(r.risk_level, 0) + 1

            return {
                'total': total,
                'safe': safe,
                'blocked': blocked,
                'pending_review': pending,
                'block_rate': round(blocked / max(1, total) * 100, 2),
                'risk_distribution': risk_dist
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_results': len(self.results),
            'custom_categories': len(self.custom_words),
            'auto_block_threshold': self.auto_block_threshold
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[内容审核] 内容审核服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[内容审核] 内容审核服务已停止")


ai_content_moderation = AIContentModeration()
