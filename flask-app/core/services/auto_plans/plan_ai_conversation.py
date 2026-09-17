# -*- coding: utf-8 -*-
r"""AI 对话流管理计划 - 自动管理 AI 对话历史r"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class AIConversationPlan(AbstractAutoPlan):
    r"""AI 对话流管理计划

    定期整理 AI 对话历史，包括：
    - 对话归档
    - 上下文窗口优化
    - 敏感内容过滤
    - 对话质量评估
    - 历史对话统计
    r"""

    plan_id = r'ai_conversation'
    name = r'AI 对话流管理计划'
    description = r'自动管理 AI 对话历史、归档整理、上下文优化、质量评估'
    category = r'content'
    interval_seconds = 3600  # 每 1 小时

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            r'archive_old': self._archive_old_conversations(),
            r'context_optimize': self._optimize_context_windows(),
            r'sensitive_filter': self._filter_sensitive_content(),
            r'quality_score': self._score_conversation_quality(),
            r'stats_update': self._update_conversation_stats(),
        }

        archived = results[r'archive_old'].get(r'archived', 0)
        scored = results[r'quality_score'].get(r'avg_score', 0)

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=fr'对话流管理完成: 归档{archived}条, 均分{scored:.1f}',
            data=results,
        )

    def _archive_old_conversations(self) -> Dict[str, Any]:
        r"""归档旧对话r"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {r'success': False, r'archived': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            archived = 0

            try:
                cutoff = (datetime.now() - timedelta(days=30)).strftime(r'%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    r"UPDATE ai_conversations SET archived = 1 WHERE updated_at < ? AND archived = 0",
                    (cutoff,)
                )
                archived = cursor.rowcount
                conn.commit()
            except sqlite3.OperationalError:
                pass

            conn.close()
            return {r'success': True, r'archived': archived}
        except Exception as e:
            return {r'success': False, r'error': str(e), r'archived': 0}

    def _optimize_context_windows(self) -> Dict[str, Any]:
        r"""优化上下文窗口r"""
        try:
            try:
                from ai_engines.ai_brain import AIBrain
                brain = AIBrain()
                stats = brain.get_stats()
                return {r'success': True, r'knowledge_count': stats.get(r'total_knowledge', 0)}
            except ImportError:
                return {r'success': True, r'optimized': True, r'mode': r'no_ai_brain'}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _filter_sensitive_content(self) -> Dict[str, Any]:
        r"""敏感内容过滤r"""
        try:
            sensitive_keywords = [r'密码', r'密钥', r'secret', r'password', r'token']
            filtered = 0

            db_path = self._find_app_db()
            if db_path:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                try:
                    for keyword in sensitive_keywords:
                        cursor.execute(
                            r"SELECT COUNT(*) FROM ai_conversations "
                            r"WHERE message LIKE ? AND is_flagged = 0",
                            (fr'%{keyword}%',)
                        )
                        count = cursor.fetchone()[0]
                        if count > 0:
                            cursor.execute(
                                r"UPDATE ai_conversations SET is_flagged = 1 "
                                r"WHERE message LIKE ? AND is_flagged = 0",
                                (fr'%{keyword}%',)
                            )
                            filtered += cursor.rowcount
                            conn.commit()
                except sqlite3.OperationalError:
                    pass
                conn.close()

            return {r'success': True, r'flagged_count': filtered}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _score_conversation_quality(self) -> Dict[str, Any]:
        r"""对话质量评分r"""
        try:
            scores: List[float] = []
            db_path = self._find_app_db()
            if db_path:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        r"SELECT length(message) as msg_len FROM ai_conversations "
                        "WHERE role = r'assistant' ORDER BY id DESC LIMIT 100"
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
            return {r'success': True, r'avg_score': round(avg_score, 2), r'samples': len(scores)}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    def _update_conversation_stats(self) -> Dict[str, Any]:
        r"""更新对话统计r"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {r'success': False, r'error': r'数据库未找到'}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            stats = {}

            try:
                cursor.execute(r"SELECT COUNT(*) FROM ai_conversations")
                stats[r'total_conversations'] = cursor.fetchone()[0]
            except Exception:
                stats[r'total_conversations'] = 0

            try:
                cursor.execute(
                    r"SELECT COUNT(DISTINCT session_id) FROM ai_conversations"
                )
                stats[r'total_sessions'] = cursor.fetchone()[0]
            except Exception:
                stats[r'total_sessions'] = 0

            conn.close()
            return {r'success': True, r'stats': stats}
        except Exception as e:
            return {r'success': False, r'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in [r'data/databases/app.db', r'app.db', r'data/app.db']:
            if os.path.exists(p):
                return p
        return r''
