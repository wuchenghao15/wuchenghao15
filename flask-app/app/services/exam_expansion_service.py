#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试系统拓展服务模块
提供考试预约、错题重做、考试笔记、考试收藏、成绩对比分析等功能
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.utils.logging import logger
from app.utils.db import db_manager


class ExamExpansionService:
    """考试系统拓展服务类"""

    def __init__(self):
        """初始化拓展服务"""
        self._init_tables()
        logger.info("考试系统拓展服务初始化完成")

    def _init_tables(self):
        """初始化数据库表"""
        try:
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exam_appointments (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    exam_id TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            """)

            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS wrong_question_reviews (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    exam_id TEXT NOT NULL,
                    review_count INTEGER NOT NULL DEFAULT 0,
                    last_review_time TEXT,
                    mastered INTEGER NOT NULL DEFAULT 0,
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            """)

            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exam_notes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    exam_id TEXT NOT NULL,
                    question_id TEXT,
                    content TEXT NOT NULL,
                    note_type TEXT NOT NULL DEFAULT 'general',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            """)

            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exam_favorites (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    exam_id TEXT NOT NULL,
                    folder_name TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id),
                    UNIQUE(user_id, exam_id)
                )
            """)

            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exam_score_comparisons (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    exam_id TEXT NOT NULL,
                    base_score REAL NOT NULL,
                    compare_score REAL NOT NULL,
                    improvement REAL NOT NULL,
                    analysis TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            """)

            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS exam_tags (
                    id TEXT PRIMARY KEY,
                    exam_id TEXT NOT NULL,
                    tag_name TEXT NOT NULL,
                    tag_color TEXT DEFAULT '#6366f1',
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            """)

            db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_appointments_user ON exam_appointments(user_id)
            """)
            db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_appointments_status ON exam_appointments(status)
            """)
            db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_wrong_reviews_user ON wrong_question_reviews(user_id)
            """)
            db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_exam_notes_user ON exam_notes(user_id)
            """)
            db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_exam_favorites_user ON exam_favorites(user_id)
            """)

            db_manager.commit()
            logger.info("考试系统拓展表初始化完成")
        except Exception as e:
            logger.error(f"初始化考试拓展表失败: {str(e)}")

    def create_appointment(self, user_id: str, exam_id: str, scheduled_time: str) -> str:
        """创建考试预约"""
        try:
            appointment_id = f"appt_{uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d')}"
            
            now = datetime.now(timezone.utc).isoformat()
            
            db_manager.execute("""
                INSERT INTO exam_appointments (id, user_id, exam_id, scheduled_time, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """, (appointment_id, user_id, exam_id, scheduled_time, now, now))
            
            db_manager.commit()
            logger.info(f"创建考试预约成功: {appointment_id}")
            return appointment_id
        except Exception as e:
            logger.error(f"创建考试预约失败: {str(e)}")
            return ''

    def get_user_appointments(self, user_id: str, status: str = None) -> List[Dict]:
        """获取用户预约列表"""
        try:
            if status:
                rows = db_manager.query("""
                    SELECT ea.*, e.title, e.duration, e.level
                    FROM exam_appointments ea
                    LEFT JOIN exams e ON ea.exam_id = e.id
                    WHERE ea.user_id = ? AND ea.status = ?
                    ORDER BY ea.scheduled_time DESC
                """, (user_id, status))
            else:
                rows = db_manager.query("""
                    SELECT ea.*, e.title, e.duration, e.level
                    FROM exam_appointments ea
                    LEFT JOIN exams e ON ea.exam_id = e.id
                    WHERE ea.user_id = ?
                    ORDER BY ea.scheduled_time DESC
                """, (user_id,))
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取用户预约失败: {str(e)}")
            return []

    def update_appointment_status(self, appointment_id: str, status: str) -> bool:
        """更新预约状态"""
        try:
            db_manager.execute("""
                UPDATE exam_appointments 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status, datetime.now(timezone.utc).isoformat(), appointment_id))
            
            db_manager.commit()
            logger.info(f"更新预约状态: {appointment_id} -> {status}")
            return True
        except Exception as e:
            logger.error(f"更新预约状态失败: {str(e)}")
            return False

    def delete_appointment(self, appointment_id: str) -> bool:
        """取消预约"""
        try:
            db_manager.execute("""
                DELETE FROM exam_appointments WHERE id = ?
            """, (appointment_id,))
            
            db_manager.commit()
            logger.info(f"取消预约: {appointment_id}")
            return True
        except Exception as e:
            logger.error(f"取消预约失败: {str(e)}")
            return False

    def get_wrong_questions_for_review(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取待复习错题"""
        try:
            rows = db_manager.query("""
                SELECT qr.*, q.question_text, q.question_type, q.options, q.correct_answer, q.difficulty
                FROM wrong_question_reviews qr
                LEFT JOIN questions q ON qr.question_id = q.id
                WHERE qr.user_id = ? AND qr.mastered = 0
                ORDER BY qr.last_review_time DESC NULLS FIRST, qr.review_count ASC
                LIMIT ?
            """, (user_id, limit))
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取待复习错题失败: {str(e)}")
            return []

    def record_wrong_question_review(self, user_id: str, question_id: str, exam_id: str, 
                                      mastered: bool = False, notes: str = '') -> bool:
        """记录错题复习"""
        try:
            now = datetime.now(timezone.utc).isoformat()
            
            rows = db_manager.query("""
                SELECT * FROM wrong_question_reviews WHERE user_id = ? AND question_id = ?
            """, (user_id, question_id))
            
            if rows:
                review = dict(rows[0])
                review_count = review['review_count'] + 1
                
                db_manager.execute("""
                    UPDATE wrong_question_reviews 
                    SET review_count = ?, last_review_time = ?, mastered = ?, notes = ?, updated_at = ?
                    WHERE user_id = ? AND question_id = ?
                """, (review_count, now, 1 if mastered else 0, notes, now, user_id, question_id))
            else:
                review_id = f"review_{uuid4().hex[:8]}"
                db_manager.execute("""
                    INSERT INTO wrong_question_reviews (id, user_id, question_id, exam_id, review_count, 
                                                      last_review_time, mastered, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                """, (review_id, user_id, question_id, exam_id, now, 1 if mastered else 0, notes, now, now))
            
            db_manager.commit()
            logger.info(f"记录错题复习: {question_id}, 掌握: {mastered}")
            return True
        except Exception as e:
            logger.error(f"记录错题复习失败: {str(e)}")
            return False

    def get_review_stats(self, user_id: str) -> Dict:
        """获取错题复习统计"""
        try:
            total = db_manager.query("""
                SELECT COUNT(*) as count FROM wrong_question_reviews WHERE user_id = ?
            """, (user_id,))
            mastered = db_manager.query("""
                SELECT COUNT(*) as count FROM wrong_question_reviews WHERE user_id = ? AND mastered = 1
            """, (user_id,))
            pending = db_manager.query("""
                SELECT COUNT(*) as count FROM wrong_question_reviews WHERE user_id = ? AND mastered = 0
            """, (user_id,))
            
            return {
                'total_wrong': total[0]['count'] if total else 0,
                'mastered': mastered[0]['count'] if mastered else 0,
                'pending_review': pending[0]['count'] if pending else 0,
                'mastery_rate': round((mastered[0]['count'] / total[0]['count']) * 100, 1) if total[0]['count'] > 0 else 0
            }
        except Exception as e:
            logger.error(f"获取错题复习统计失败: {str(e)}")
            return {}

    def add_exam_note(self, user_id: str, exam_id: str, content: str, 
                      question_id: str = None, note_type: str = 'general') -> str:
        """添加考试笔记"""
        try:
            note_id = f"note_{uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d')}"
            now = datetime.now(timezone.utc).isoformat()
            
            db_manager.execute("""
                INSERT INTO exam_notes (id, user_id, exam_id, question_id, content, note_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (note_id, user_id, exam_id, question_id, content, note_type, now, now))
            
            db_manager.commit()
            logger.info(f"添加考试笔记: {note_id}")
            return note_id
        except Exception as e:
            logger.error(f"添加考试笔记失败: {str(e)}")
            return ''

    def get_exam_notes(self, user_id: str, exam_id: str = None) -> List[Dict]:
        """获取考试笔记"""
        try:
            if exam_id:
                rows = db_manager.query("""
                    SELECT * FROM exam_notes WHERE user_id = ? AND exam_id = ?
                    ORDER BY created_at DESC
                """, (user_id, exam_id))
            else:
                rows = db_manager.query("""
                    SELECT en.*, e.title as exam_title
                    FROM exam_notes en
                    LEFT JOIN exams e ON en.exam_id = e.id
                    WHERE en.user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取考试笔记失败: {str(e)}")
            return []

    def delete_exam_note(self, note_id: str) -> bool:
        """删除考试笔记"""
        try:
            db_manager.execute("""
                DELETE FROM exam_notes WHERE id = ?
            """, (note_id,))
            
            db_manager.commit()
            logger.info(f"删除考试笔记: {note_id}")
            return True
        except Exception as e:
            logger.error(f"删除考试笔记失败: {str(e)}")
            return False

    def add_exam_favorite(self, user_id: str, exam_id: str, folder_name: str = '') -> bool:
        """收藏考试"""
        try:
            favorite_id = f"fav_{uuid4().hex[:8]}"
            now = datetime.now(timezone.utc).isoformat()
            
            db_manager.execute("""
                INSERT OR IGNORE INTO exam_favorites (id, user_id, exam_id, folder_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (favorite_id, user_id, exam_id, folder_name, now))
            
            db_manager.commit()
            logger.info(f"收藏考试: {exam_id}")
            return True
        except Exception as e:
            logger.error(f"收藏考试失败: {str(e)}")
            return False

    def remove_exam_favorite(self, user_id: str, exam_id: str) -> bool:
        """取消收藏考试"""
        try:
            db_manager.execute("""
                DELETE FROM exam_favorites WHERE user_id = ? AND exam_id = ?
            """, (user_id, exam_id))
            
            db_manager.commit()
            logger.info(f"取消收藏考试: {exam_id}")
            return True
        except Exception as e:
            logger.error(f"取消收藏考试失败: {str(e)}")
            return False

    def get_user_favorites(self, user_id: str, folder_name: str = '') -> List[Dict]:
        """获取用户收藏的考试"""
        try:
            if folder_name:
                rows = db_manager.query("""
                    SELECT ef.*, e.title, e.description, e.level, e.duration, e.question_count
                    FROM exam_favorites ef
                    LEFT JOIN exams e ON ef.exam_id = e.id
                    WHERE ef.user_id = ? AND ef.folder_name = ?
                    ORDER BY ef.created_at DESC
                """, (user_id, folder_name))
            else:
                rows = db_manager.query("""
                    SELECT ef.*, e.title, e.description, e.level, e.duration, e.question_count
                    FROM exam_favorites ef
                    LEFT JOIN exams e ON ef.exam_id = e.id
                    WHERE ef.user_id = ?
                    ORDER BY ef.created_at DESC
                """, (user_id,))
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取用户收藏失败: {str(e)}")
            return []

    def get_favorite_folders(self, user_id: str) -> List[str]:
        """获取收藏文件夹列表"""
        try:
            rows = db_manager.query("""
                SELECT DISTINCT folder_name FROM exam_favorites WHERE user_id = ? AND folder_name != ''
            """, (user_id,))
            
            return [row['folder_name'] for row in rows]
        except Exception as e:
            logger.error(f"获取收藏文件夹失败: {str(e)}")
            return []

    def compare_scores(self, user_id: str, exam_id: str, current_score: float) -> Dict:
        """成绩对比分析"""
        try:
            rows = db_manager.query("""
                SELECT score FROM exam_results WHERE user_id = ? AND exam_id = ?
                ORDER BY created_at DESC LIMIT 2
            """, (user_id, exam_id))
            
            if len(rows) >= 2:
                previous_score = rows[1]['score']
                improvement = round(current_score - previous_score, 2)
                
                analysis = self._generate_score_analysis(previous_score, current_score, improvement)
                
                comparison_id = f"comp_{uuid4().hex[:8]}"
                now = datetime.now(timezone.utc).isoformat()
                
                db_manager.execute("""
                    INSERT INTO exam_score_comparisons (id, user_id, exam_id, base_score, compare_score, 
                                                       improvement, analysis, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (comparison_id, user_id, exam_id, previous_score, current_score, improvement, analysis, now))
                
                db_manager.commit()
                
                return {
                    'success': True,
                    'previous_score': previous_score,
                    'current_score': current_score,
                    'improvement': improvement,
                    'improvement_percent': round((improvement / previous_score) * 100, 1) if previous_score > 0 else 0,
                    'analysis': analysis
                }
            else:
                return {
                    'success': False,
                    'message': '没有足够的历史成绩进行对比'
                }
        except Exception as e:
            logger.error(f"成绩对比分析失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _generate_score_analysis(self, previous: float, current: float, improvement: float) -> str:
        """生成成绩分析报告"""
        if improvement > 10:
            return f"🎉 优秀！成绩提升了 {improvement} 分，进步非常明显！继续保持这种学习势头，你正在稳步前进。"
        elif improvement > 5:
            return f"👍 不错的进步！成绩提升了 {improvement} 分，说明你的努力正在见效。再接再厉，争取更大的突破。"
        elif improvement > 0:
            return f"💪 小有进步！成绩提升了 {improvement} 分，虽然幅度不大，但每一步都是积累。保持耐心，持续改进。"
        elif improvement == 0:
            return f"📊 成绩持平。建议分析错题原因，针对性地进行复习，争取下次有所突破。"
        elif improvement > -5:
            return f"⚠️ 略有下降，成绩减少了 {abs(improvement)} 分。建议回顾近期学习状态，调整学习方法。"
        else:
            return f"🚨 成绩下降较多，减少了 {abs(improvement)} 分。建议认真分析错题，加强薄弱环节的练习。"

    def get_score_history(self, user_id: str, exam_id: str = None, limit: int = 10) -> List[Dict]:
        """获取成绩历史"""
        try:
            if exam_id:
                rows = db_manager.query("""
                    SELECT er.*, e.title
                    FROM exam_results er
                    LEFT JOIN exams e ON er.exam_id = e.id
                    WHERE er.user_id = ? AND er.exam_id = ?
                    ORDER BY er.created_at DESC LIMIT ?
                """, (user_id, exam_id, limit))
            else:
                rows = db_manager.query("""
                    SELECT er.*, e.title
                    FROM exam_results er
                    LEFT JOIN exams e ON er.exam_id = e.id
                    WHERE er.user_id = ?
                    ORDER BY er.created_at DESC LIMIT ?
                """, (user_id, limit))
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取成绩历史失败: {str(e)}")
            return []

    def add_exam_tag(self, exam_id: str, tag_name: str, tag_color: str = '#6366f1') -> bool:
        """添加考试标签"""
        try:
            tag_id = f"tag_{uuid4().hex[:8]}"
            
            db_manager.execute("""
                INSERT INTO exam_tags (id, exam_id, tag_name, tag_color)
                VALUES (?, ?, ?, ?)
            """, (tag_id, exam_id, tag_name, tag_color))
            
            db_manager.commit()
            logger.info(f"添加考试标签: {tag_name} -> {exam_id}")
            return True
        except Exception as e:
            logger.error(f"添加考试标签失败: {str(e)}")
            return False

    def get_exam_tags(self, exam_id: str) -> List[Dict]:
        """获取考试标签"""
        try:
            rows = db_manager.query("""
                SELECT * FROM exam_tags WHERE exam_id = ?
            """, (exam_id,))
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取考试标签失败: {str(e)}")
            return []

    def delete_exam_tag(self, tag_id: str) -> bool:
        """删除考试标签"""
        try:
            db_manager.execute("""
                DELETE FROM exam_tags WHERE id = ?
            """, (tag_id,))
            
            db_manager.commit()
            logger.info(f"删除考试标签: {tag_id}")
            return True
        except Exception as e:
            logger.error(f"删除考试标签失败: {str(e)}")
            return False


_exam_expansion_service = None


def get_exam_expansion_service() -> ExamExpansionService:
    """获取考试拓展服务实例（单例）"""
    global _exam_expansion_service
    if _exam_expansion_service is None:
        _exam_expansion_service = ExamExpansionService()
    return _exam_expansion_service