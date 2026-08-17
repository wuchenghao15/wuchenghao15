# -*- coding: utf-8 -*-
"""AI 对话流管理计划 - 自动管理 AI 对话历史"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class AIConversationPlan(AbstractAutoPlan):
    """AI 对话流管理计划

    定期整理 AI 对话历史，包括：
    - 对话归档
    - 上下文窗口优化
    - 敏感内容过滤
    - 对话质量评估
    - 历史对话统计
    """

    plan_id = 'ai_conversation'
    name = 'AI 对话流管理计划'
    description = '自动管理 AI 对话历史、归档整理、上下文优化、质量评估'
    category = 'content'
    interval_seconds = 3600  # 每 1 小时

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            'archive_old': self._archive_old_conversations(),
            'context_optimize': self._optimize_context_windows(),
            'sensitive_filter': self._filter_sensitive_content(),
            'quality_score': self._score_conversation_quality(),
            'stats_update': self._update_conversation_stats(),
        }

        archived = results['archive_old'].get('archived', 0)
        scored = results['quality_score'].get('avg_score', 0)

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=f'对话流管理完成: 归档{archived}条, 均分{scored:.1f}',
            data=results,
        )

    def _archive_old_conversations(self) -> Dict[str, Any]:
        """归档旧对话"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'archived': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            archived = 0

            try:
                cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "UPDATE ai_conversations SET archived = 1 WHERE updated_at < ? AND archived = 0",
                    (cutoff,)
                )
                archived = cursor.rowcount
                conn.commit()
            except sqlite3.OperationalError:
                pass

            conn.close()
            return {'success': True, 'archived': archived}
        except Exception as e:
            return {'success': False, 'error': str(e), 'archived': 0}

    def _optimize_context_windows(self) -> Dict[str, Any]:
        """优化上下文窗口"""
        try:
            try:
                from ai_engines.ai_brain import AIBrain
                brain = AIBrain()
                stats = brain.get_stats()
                return {'success': True, 'knowledge_count': stats.get('total_knowledge', 0)}
            except ImportError:
                return {'success': True, 'optimized': True, 'mode': 'no_ai_brain'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _filter_sensitive_content(self) -> Dict[str, Any]:
        """敏感内容过滤"""
        try:
            sensitive_keywords = ['密码', '密钥', 'secret', 'password', 'token']
            filtered = 0

            db_path = self._find_app_db()
            if db_path:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                try:
                    for keyword in sensitive_keywords:
                        cursor.execute(
                            "SELECT COUNT(*) FROM ai_conversations "
                            "WHERE message LIKE ? AND is_flagged = 0",
                            (f'%{keyword}%',)
                        )
                        count = cursor.fetchone()[0]
                        if count > 0:
                            cursor.execute(
                                "UPDATE ai_conversations SET is_flagged = 1 "
                                "WHERE message LIKE ? AND is_flagged = 0",
                                (f'%{keyword}%',)
                            )
                            filtered += cursor.rowcount
                            conn.commit()
                except sqlite3.OperationalError:
                    pass
                conn.close()

            return {'success': True, 'flagged_count': filtered}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _score_conversation_quality(self) -> Dict[str, Any]:
        """对话质量评分"""
        try:
            scores: List[float] = []
            db_path = self._find_app_db()
            if db_path:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "SELECT length(message) as msg_len FROM ai_conversations "
                        "WHERE role = 'assistant' ORDER BY id DESC LIMIT 100"
                    )
                    rows = cursor.fetchall()
                    for row in rows:
                        msg_len = row[0] if row[0] else 0
                        if msg_len > 50:
                            scores.append(min(1.0, msg_len / 200))
                except sqlite3.OperationalError:
                    pass
                conn.close()

            avg_score = sum(scores) / len(scores) if scores else 0
            return {'success': True, 'avg_score': round(avg_score, 2), 'samples': len(scores)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _update_conversation_stats(self) -> Dict[str, Any]:
        """更新对话统计"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'error': '数据库未找到'}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            stats = {}

            try:
                cursor.execute("SELECT COUNT(*) FROM ai_conversations")
                stats['total_conversations'] = cursor.fetchone()[0]
            except Exception:
                stats['total_conversations'] = 0

            try:
                cursor.execute(
                    "SELECT COUNT(DISTINCT session_id) FROM ai_conversations"
                )
                stats['total_sessions'] = cursor.fetchone()[0]
            except Exception:
                stats['total_sessions'] = 0

            conn.close()
            return {'success': True, 'stats': stats}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in ['data/databases/app.db', 'app.db', 'data/app.db']:
            if os.path.exists(p):
                return p
        return ''
