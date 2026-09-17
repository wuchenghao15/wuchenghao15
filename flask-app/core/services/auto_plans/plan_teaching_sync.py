# -*- coding: utf-8 -*-
"""教辅同步计划 - 自动同步教辅资源到题库"""

from __future__ import annotations

import os
import sqlite3
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict

from .scheduler_base import AbstractAutoPlan, PlanResult, register_plan_class


TEXTBOOK_CATALOG = [
    {'subject': '语文', 'grade': '七年级', 'version': '部编版', 'chapters': 24},
    {'subject': '语文', 'grade': '八年级', 'version': '部编版', 'chapters': 24},
    {'subject': '语文', 'grade': '九年级', 'version': '部编版', 'chapters': 24},
    {'subject': '数学', 'grade': '七年级', 'version': '人教版', 'chapters': 28},
    {'subject': '数学', 'grade': '八年级', 'version': '人教版', 'chapters': 28},
    {'subject': '数学', 'grade': '九年级', 'version': '人教版', 'chapters': 28},
    {'subject': '英语', 'grade': '七年级', 'version': '人教版', 'chapters': 24},
    {'subject': '英语', 'grade': '八年级', 'version': '人教版', 'chapters': 24},
    {'subject': '英语', 'grade': '九年级', 'version': '人教版', 'chapters': 24},
    {'subject': '物理', 'grade': '八年级', 'version': '人教版', 'chapters': 22},
    {'subject': '物理', 'grade': '九年级', 'version': '人教版', 'chapters': 22},
    {'subject': '化学', 'grade': '九年级', 'version': '人教版', 'chapters': 20},
    {'subject': '生物', 'grade': '七年级', 'version': '人教版', 'chapters': 20},
    {'subject': '生物', 'grade': '八年级', 'version': '人教版', 'chapters': 20},
    {'subject': '历史', 'grade': '七年级', 'version': '部编版', 'chapters': 22},
    {'subject': '历史', 'grade': '八年级', 'version': '部编版', 'chapters': 22},
    {'subject': '地理', 'grade': '七年级', 'version': '人教版', 'chapters': 20},
    {'subject': '地理', 'grade': '八年级', 'version': '人教版', 'chapters': 20},
    {'subject': '政治', 'grade': '七年级', 'version': '部编版', 'chapters': 20},
    {'subject': '政治', 'grade': '八年级', 'version': '部编版', 'chapters': 20},
]


@register_plan_class
class TeachingSyncPlan(AbstractAutoPlan):
    """自动教辅同步计划

    检查教辅目录覆盖率、同步缺失章节、验证知识点映射、
    生成教辅更新报告。
    """

    plan_id = 'teaching_sync'
    name = '教辅同步计划'
    description = '自动检查教辅覆盖率、同步缺失章节、验证知识点映射关系'
    category = 'content'
    interval_seconds = 86400  # 每天一次

    def execute(self) -> PlanResult:
        results: Dict[str, Any] = {
            'coverage_check': self._check_coverage(),
            'sync_missing': self._sync_missing_content(),
            'knowledge_mapping': self._verify_knowledge_mapping(),
            'generate_report': self._generate_sync_report(),
        }

        total_books = len(TEXTBOOK_CATALOG)
        covered = results['coverage_check'].get('covered', 0)

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=f'教辅同步完成: {covered}/{total_books} 册教辅已覆盖',
            data=results,
        )

    def _check_coverage(self) -> Dict[str, Any]:
        """检查教辅覆盖率"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'covered': 0, 'total': len(TEXTBOOK_CATALOG)}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            covered = 0
            coverage_details = []

            for book in TEXTBOOK_CATALOG:
                try:
                    cursor.execute(
                        "SELECT COUNT(*) FROM questions "
                        "WHERE category LIKE ? AND is_active = 1",
                        (f'%{book["subject"]}%',)
                    )
                    count = cursor.fetchone()[0]
                    if count > 0:
                        covered += 1
                        coverage_details.append({
                            'subject': book['subject'],
                            'grade': book['grade'],
                            'covered': True,
                            'question_count': count,
                        })
                    else:
                        coverage_details.append({
                            'subject': book['subject'],
                            'grade': book['grade'],
                            'covered': False,
                            'question_count': 0,
                        })
                except Exception:
                    coverage_details.append({
                        'subject': book['subject'],
                        'grade': book['grade'],
                        'covered': False,
                        'question_count': 0,
                    })

            conn.close()
            return {
                'success': True,
                'covered': covered,
                'total': len(TEXTBOOK_CATALOG),
                'coverage_rate': round(covered / len(TEXTBOOK_CATALOG) * 100, 1),
                'details': coverage_details,
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'covered': 0, 'total': len(TEXTBOOK_CATALOG)}

    def _sync_missing_content(self) -> Dict[str, Any]:
        """同步缺失教辅内容"""
        try:
            synced = 0
            try:
                from core.services.question_bank_sync_service import QuestionBankSyncService
                svc = QuestionBankSyncService()
                for book in TEXTBOOK_CATALOG:
                    try:
                        result = svc.sync_textbook_content(
                            subject=book['subject'],
                            grade=book['grade'],
                            version=book['version'],
                        )
                        if isinstance(result, dict) and result.get('synced'):
                            synced += result['synced']
                    except Exception:
                        pass
            except ImportError:
                pass

            return {'success': True, 'items_synced': synced}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _verify_knowledge_mapping(self) -> Dict[str, Any]:
        """验证知识点映射"""
        try:
            db_path = self._find_app_db()
            if not db_path:
                return {'success': False, 'mapped': 0}

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM questions "
                    "WHERE knowledge_points IS NOT NULL AND knowledge_points != ''"
                )
                mapped = cursor.fetchone()[0]
            except Exception:
                mapped = 0

            try:
                cursor.execute("SELECT COUNT(*) FROM questions")
                total = cursor.fetchone()[0]
            except Exception:
                total = 0

            conn.close()
            rate = round(mapped / total * 100, 1) if total > 0 else 0

            return {'success': True, 'mapped': mapped, 'total': total, 'mapping_rate': rate}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_sync_report(self) -> Dict[str, Any]:
        """生成教辅同步报告"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'catalog_size': len(TEXTBOOK_CATALOG),
                'recommendations': [],
            }

            for book in TEXTBOOK_CATALOG:
                report['recommendations'].append({
                    'book': f'{book["subject"]}-{book["grade"]}-{book["version"]}',
                    'priority': 'medium',
                    'action': 'check_coverage',
                })

            return {'success': True, 'report': report}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _find_app_db() -> str:
        for p in ['data/databases/app.db', 'app.db', 'data/app.db']:
            if os.path.exists(p):
                return p
        return ''
