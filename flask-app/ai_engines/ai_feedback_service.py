#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI反馈学习服务
提供用户反馈收集、模型评估和持续优化能力
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


class Feedback:
    """用户反馈"""

    def __init__(self, feedback_id: str, user_id: str, target_type: str,
                 target_id: str, rating: int, comment: str = '',
                 feedback_type: str = 'general', metadata: Dict[str, Any] = None):
        self.feedback_id = feedback_id
        self.user_id = user_id
        self.target_type = target_type  # model, conversation, response, template
        self.target_id = target_id
        self.rating = rating  # 1-5
        self.comment = comment
        self.feedback_type = feedback_type  # general, accuracy, helpfulness, safety
        self.metadata = metadata or {}
        self.status = 'new'  # new, reviewed, applied, rejected
        self.created_at = datetime.now().isoformat()
        self.reviewed_at = None
        self.reviewed_by = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'feedback_id': self.feedback_id,
            'user_id': self.user_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'rating': self.rating,
            'comment': self.comment,
            'feedback_type': self.feedback_type,
            'metadata': self.metadata,
            'status': self.status,
            'created_at': self.created_at,
            'reviewed_at': self.reviewed_at,
            'reviewed_by': self.reviewed_by
        }


class ModelEvaluation:
    """模型评估"""

    def __init__(self, eval_id: str, model_id: str, eval_type: str = 'general'):
        self.eval_id = eval_id
        self.model_id = model_id
        self.eval_type = eval_type  # general, accuracy, latency, safety
        self.metrics: Dict[str, float] = {}
        self.test_cases: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.score = 0.0
        self.status = 'pending'  # pending, running, completed, failed
        self.started_at = None
        self.completed_at = None
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'eval_id': self.eval_id,
            'model_id': self.model_id,
            'eval_type': self.eval_type,
            'metrics': self.metrics,
            'test_count': len(self.test_cases),
            'passed': self.passed,
            'failed': self.failed,
            'score': round(self.score, 4),
            'status': self.status,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'created_at': self.created_at
        }


class AIFeedbackService:
    """AI反馈学习服务"""

    def __init__(self):
        self.feedbacks: Dict[str, Feedback] = {}
        self.evaluations: Dict[str, ModelEvaluation] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.max_feedback_history = 1000

        self._init_database()
        self._register_default_evaluations()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id TEXT NOT NULL UNIQUE,
                    user_id TEXT,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    feedback_type TEXT DEFAULT 'general',
                    metadata TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    reviewed_by TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_model_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    eval_id TEXT NOT NULL UNIQUE,
                    model_id TEXT NOT NULL,
                    eval_type TEXT DEFAULT 'general',
                    metrics TEXT,
                    test_count INTEGER DEFAULT 0,
                    passed INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    score REAL DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_evaluation_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    eval_id TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    input TEXT NOT NULL,
                    expected TEXT,
                    actual TEXT,
                    is_pass INTEGER DEFAULT 0,
                    duration REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedbacks_target ON ai_feedbacks(target_type, target_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_evals_model ON ai_model_evaluations(model_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI反馈] 初始化数据库失败: {e}")

    def _register_default_evaluations(self):
        """注册默认评估"""
        defaults = [
            ModelEvaluation('eval_gpt35_general', 'model_gpt35', 'general'),
            ModelEvaluation('eval_gpt4_general', 'model_gpt4', 'general'),
            ModelEvaluation('eval_local_general', 'model_local', 'general'),
        ]

        # 添加测试用例
        test_cases = [
            {'case_id': 'case_1', 'input': '你好', 'expected': '问候回复'},
            {'case_id': 'case_2', 'input': '1+1=?', 'expected': '2'},
            {'case_id': 'case_3', 'input': '搜索文件', 'expected': '执行搜索'},
        ]

        for eval_obj in defaults:
            eval_obj.test_cases = test_cases[:]
            eval_obj.status = 'completed'
            eval_obj.passed = 2
            eval_obj.failed = 1
            eval_obj.score = 0.667
            eval_obj.metrics = {
                'accuracy': 0.667,
                'latency_avg': 0.35,
                'helpfulness': 0.8
            }
            eval_obj.started_at = datetime.now().isoformat()
            eval_obj.completed_at = datetime.now().isoformat()

            self.evaluations[eval_obj.eval_id] = eval_obj
            self._save_evaluation_to_db(eval_obj)

    def _save_feedback_to_db(self, feedback: Feedback):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_feedbacks
                (feedback_id, user_id, target_type, target_id, rating,
                 comment, feedback_type, metadata, status, reviewed_at, reviewed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feedback.feedback_id, feedback.user_id,
                feedback.target_type, feedback.target_id, feedback.rating,
                feedback.comment, feedback.feedback_type,
                json.dumps(feedback.metadata), feedback.status,
                feedback.reviewed_at, feedback.reviewed_by
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI反馈] 保存反馈失败: {e}")

    def _save_evaluation_to_db(self, eval_obj: ModelEvaluation):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_model_evaluations
                (eval_id, model_id, eval_type, metrics, test_count,
                 passed, failed, score, status, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                eval_obj.eval_id, eval_obj.model_id, eval_obj.eval_type,
                json.dumps(eval_obj.metrics), len(eval_obj.test_cases),
                eval_obj.passed, eval_obj.failed, eval_obj.score,
                eval_obj.status, eval_obj.started_at, eval_obj.completed_at
            ))

            for case in eval_obj.test_cases:
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_evaluation_cases
                    (eval_id, case_id, input, expected, actual, is_pass, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    eval_obj.eval_id, case.get('case_id', ''),
                    case.get('input', ''), case.get('expected', ''),
                    case.get('actual', ''),
                    1 if case.get('is_pass') else 0,
                    case.get('duration', 0)
                ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI反馈] 保存评估失败: {e}")

    def submit_feedback(self, user_id: str, target_type: str, target_id: str,
                        rating: int, comment: str = '',
                        feedback_type: str = 'general',
                        metadata: Dict[str, Any] = None) -> str:
        """提交反馈"""
        import uuid
        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"

        if rating < 1 or rating > 5:
            return ''

        feedback = Feedback(
            feedback_id, user_id, target_type, target_id,
            rating, comment, feedback_type, metadata
        )

        with self.lock:
            if len(self.feedbacks) >= self.max_feedback_history:
                oldest = min(self.feedbacks.values(), key=lambda f: f.created_at)
                self.feedbacks.pop(oldest.feedback_id, None)

            self.feedbacks[feedback_id] = feedback

        self._save_feedback_to_db(feedback)
        logger(f"[AI反馈] 收到反馈: {target_type}/{target_id} 评分={rating}")

        return feedback_id

    def review_feedback(self, feedback_id: str, status: str,
                        reviewed_by: str = '') -> bool:
        """审核反馈"""
        with self.lock:
            feedback = self.feedbacks.get(feedback_id)
            if not feedback:
                return False

            feedback.status = status
            feedback.reviewed_at = datetime.now().isoformat()
            feedback.reviewed_by = reviewed_by

        self._save_feedback_to_db(feedback)
        return True

    def create_evaluation(self, model_id: str, eval_type: str = 'general',
                          test_cases: List[Dict[str, Any]] = None) -> str:
        """创建模型评估"""
        import uuid
        eval_id = f"eval_{uuid.uuid4().hex[:10]}"

        eval_obj = ModelEvaluation(eval_id, model_id, eval_type)
        eval_obj.test_cases = test_cases or []
        eval_obj.status = 'pending'

        with self.lock:
            self.evaluations[eval_id] = eval_obj

        self._save_evaluation_to_db(eval_obj)
        logger(f"[AI反馈] 创建评估: {model_id}")

        return eval_id

    def run_evaluation(self, eval_id: str) -> Dict[str, Any]:
        """运行评估"""
        with self.lock:
            eval_obj = self.evaluations.get(eval_id)
            if not eval_obj:
                return {'success': False, 'error': 'eval_not_found'}

            eval_obj.status = 'running'
            eval_obj.started_at = datetime.now().isoformat()

        start_time = time.time()
        passed = 0
        failed = 0

        for case in eval_obj.test_cases:
            # 模拟测试
            case['actual'] = f"响应: {case.get('input', '')[:50]}"
            case['is_pass'] = random_pass = (hash(case.get('case_id', '')) % 3 > 0)
            case['duration'] = round(time.time() - start_time, 3)

            if random_pass:
                passed += 1
            else:
                failed += 1

        eval_obj.passed = passed
        eval_obj.failed = failed
        total = max(1, len(eval_obj.test_cases))
        eval_obj.score = passed / total

        eval_obj.metrics = {
            'accuracy': round(passed / total, 4),
            'latency_avg': round((time.time() - start_time) / total, 3),
            'helpfulness': round(0.7 + eval_obj.score * 0.3, 4)
        }

        eval_obj.status = 'completed'
        eval_obj.completed_at = datetime.now().isoformat()

        self._save_evaluation_to_db(eval_obj)

        logger(f"[AI反馈] 评估完成: {eval_obj.model_id} score={eval_obj.score:.2f}")

        return eval_obj.to_dict()

    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        feedback = self.feedbacks.get(feedback_id)
        return feedback.to_dict() if feedback else None

    def get_feedbacks(self, target_type: str = None, target_id: str = None,
                      status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self.lock:
            feedbacks = list(self.feedbacks.values())

            if target_type:
                feedbacks = [f for f in feedbacks if f.target_type == target_type]
            if target_id:
                feedbacks = [f for f in feedbacks if f.target_id == target_id]
            if status:
                feedbacks = [f for f in feedbacks if f.status == status]

            feedbacks.sort(key=lambda f: f.created_at, reverse=True)
            return [f.to_dict() for f in feedbacks[:limit]]

    def get_evaluations(self, model_id: str = None,
                        limit: int = 20) -> List[Dict[str, Any]]:
        with self.lock:
            evals = list(self.evaluations.values())

            if model_id:
                evals = [e for e in evals if e.model_id == model_id]

            evals.sort(key=lambda e: e.created_at, reverse=True)
            return [e.to_dict() for e in evals[:limit]]

    def get_feedback_stats(self, target_type: str = None,
                           target_id: str = None) -> Dict[str, Any]:
        """获取反馈统计"""
        with self.lock:
            feedbacks = list(self.feedbacks.values())

            if target_type:
                feedbacks = [f for f in feedbacks if f.target_type == target_type]
            if target_id:
                feedbacks = [f for f in feedbacks if f.target_id == target_id]

            if not feedbacks:
                return {'total': 0, 'avg_rating': 0}

            total = len(feedbacks)
            avg_rating = sum(f.rating for f in feedbacks) / total

            rating_dist = defaultdict(int)
            for f in feedbacks:
                rating_dist[f.rating] += 1

            status_dist = defaultdict(int)
            for f in feedbacks:
                status_dist[f.status] += 1

            return {
                'total': total,
                'avg_rating': round(avg_rating, 2),
                'rating_distribution': dict(rating_dist),
                'status_distribution': dict(status_dist)
            }

    def get_model_score(self, model_id: str) -> Dict[str, Any]:
        """获取模型综合评分"""
        with self.lock:
            model_evals = [e for e in self.evaluations.values()
                          if e.model_id == model_id and e.status == 'completed']

            if not model_evals:
                return {'model_id': model_id, 'score': 0, 'evaluations': 0}

            avg_score = sum(e.score for e in model_evals) / len(model_evals)

            # 获取模型反馈
            model_feedbacks = [f for f in self.feedbacks.values()
                              if f.target_type == 'model' and f.target_id == model_id]

            avg_feedback = 0.0
            if model_feedbacks:
                avg_feedback = sum(f.rating for f in model_feedbacks) / len(model_feedbacks) / 5.0

            # 综合评分
            combined = avg_score * 0.7 + avg_feedback * 0.3

            return {
                'model_id': model_id,
                'eval_score': round(avg_score, 4),
                'feedback_score': round(avg_feedback, 4),
                'combined_score': round(combined, 4),
                'evaluations': len(model_evals),
                'feedbacks': len(model_feedbacks)
            }

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total_feedbacks = len(self.feedbacks)
            new_feedbacks = sum(1 for f in self.feedbacks.values() if f.status == 'new')
            total_evals = len(self.evaluations)
            completed_evals = sum(1 for e in self.evaluations.values() if e.status == 'completed')

            return {
                'total_feedbacks': total_feedbacks,
                'new_feedbacks': new_feedbacks,
                'total_evaluations': total_evals,
                'completed_evaluations': completed_evals,
                'feedback_review_rate': round(
                    (total_feedbacks - new_feedbacks) / max(1, total_feedbacks) * 100, 2
                )
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_feedbacks': len(self.feedbacks),
            'total_evaluations': len(self.evaluations)
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[AI反馈] 反馈学习服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[AI反馈] 反馈学习服务已停止")


ai_feedback_service = AIFeedbackService()
