# -*- coding: utf-8 -*-
"""题库管理计划 - 自动管理和同步题库"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime
from typing import Any, Dict, List

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


@register_plan_class
class QuestionBankPlan(AbstractAutoPlan):
    """自动题库管理计划

    定期检查题库完整性、同步教辅题目、清理过期题目、
    执行题库质量评估和增量索引构建。
    """

    plan_id = 'question_bank'
    name = '题库管理计划'
    description = '自动检查题库完整性、同步题目、清理过期内容、评估题目质量'
    category = 'content'
    interval_seconds = 3600  # 每 1 小时

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            'integrity_check': self._check_integrity(),
            'sync_textbooks': self._sync_textbook_questions(),
            'cleanup_expired': self._cleanup_expired_questions(),
            'quality_assess': self._assess_quality(),
            'rebuild_index': self._rebuild_search_index(),
        }

        total_issues = sum(r.get('issues_found', 0) for r in results.values())
        fixed_issues = sum(r.get('issues_fixed', 0) for r in results.values())

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=f'题库管理完成: 发现{total_issues}问题, 修复{fixed_issues}',
            data=results,
        )

    def _check_integrity(self) -> Dict[str, Any]:
        """题库完整性检查"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'message': '数据库未找到', 'issues_found': 0, 'issues_fixed': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            checks = {
                'total_questions': 'SELECT COUNT(*) FROM questions',
                'active_questions': "SELECT COUNT(*) FROM questions WHERE is_active = 1",
                'questions_with_answer': 'SELECT COUNT(*) FROM questions WHERE answer IS NOT NULL AND answer != ""',
                'questions_with_knowledge': 'SELECT COUNT(*) FROM questions WHERE knowledge_points IS NOT NULL AND knowledge_points != ""',
                'question_categories': 'SELECT COUNT(DISTINCT category) FROM questions',
                'question_difficulties': 'SELECT COUNT(DISTINCT difficulty) FROM questions',
            }

            stats = {}
            for key, sql in checks.items():
                try:
                    cursor.execute(sql)
                    stats[key] = cursor.fetchone()[0]
                except Exception:
                    stats[key] = 0

            conn.close()

            issues = 0
            if stats.get('total_questions', 0) > 0:
                if stats.get('questions_with_answer', 0) / stats['total_questions'] < 0.9:
                    issues += 1
                if stats.get('questions_with_knowledge', 0) / stats['total_questions'] < 0.7:
                    issues += 1

            return {'success': True, 'stats': stats, 'issues_found': issues, 'issues_fixed': 0}
        except Exception as e:
            return {'success': False, 'error': str(e), 'issues_found': 0, 'issues_fixed': 0}

    def _sync_textbook_questions(self) -> Dict[str, Any]:
        """同步教辅题目"""
        try:
            synced = 0
            try:
                from core.services.question_bank_sync_service import QuestionBankSyncService
                svc = QuestionBankSyncService()
                result = svc.sync_textbook_questions()
                synced = result.get('synced', 0) if isinstance(result, dict) else 0
            except ImportError:
                synced = 0

            return {'success': True, 'synced_count': synced, 'issues_found': 0, 'issues_fixed': synced}
        except Exception as e:
            return {'success': False, 'error': str(e), 'issues_found': 1, 'issues_fixed': 0}

    def _cleanup_expired_questions(self) -> Dict[str, Any]:
        """清理过期/无效题目"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'issues_found': 0, 'issues_fixed': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            removed = 0

            try:
                cursor.execute("""
                    UPDATE questions SET is_active = 0
                    WHERE is_active = 1
                    AND (answer IS NULL OR answer = '')
                    AND created_at < datetime('now', '-30 days')
                """)
                removed = cursor.rowcount
                conn.commit()
            except Exception:
                pass

            conn.close()
            return {'success': True, 'questions_archived': removed, 'issues_found': removed, 'issues_fixed': removed}
        except Exception as e:
            return {'success': False, 'error': str(e), 'issues_found': 0, 'issues_fixed': 0}

    def _assess_quality(self) -> Dict[str, Any]:
        """题目质量评估"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'issues_found': 0, 'issues_fixed': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            quality_stats = {}
            for level_name, level_val in [('easy', 1), ('medium', 2), ('hard', 3), ('expert', 4)]:
                try:
                    cursor.execute(
                        "SELECT COUNT(*) FROM questions WHERE difficulty = ? AND is_active = 1",
                        (level_val,)
                    )
                    quality_stats[level_name] = cursor.fetchone()[0]
                except Exception:
                    quality_stats[level_name] = 0

            conn.close()
            return {'success': True, 'quality_distribution': quality_stats, 'issues_found': 0, 'issues_fixed': 0}
        except Exception as e:
            return {'success': False, 'error': str(e), 'issues_found': 0, 'issues_fixed': 0}

    def _rebuild_search_index(self) -> Dict[str, Any]:
        """重建题库搜索索引"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'issues_found': 0, 'issues_fixed': 0}

            conn = sqlite3.connect(db_path)
            try:
                conn.execute("PRAGMA optimize")
                conn.commit()
            except Exception:
                pass
            conn.close()

            return {'success': True, 'index_rebuilt': True, 'issues_found': 0, 'issues_fixed': 0}
        except Exception as e:
            return {'success': False, 'error': str(e), 'issues_found': 0, 'issues_fixed': 0}

    @staticmethod
    def _find_app_db() -> str:
        for p in ['data/databases/app.db', 'app.db', 'data/app.db']:
            if os.path.exists(p):
                return p
        return ''
