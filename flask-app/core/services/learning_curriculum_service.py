from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习与教学大纲追踪服务
追踪学生学习进度与教学大纲的匹配度，生成学习建议
"""

import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'learning_curriculum.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LearningCurriculum')


class LearningCurriculumService:
    """学习与大纲追踪服务"""

    def __init__(self):
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS learner_curriculum_progress (
            progress_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            curriculum_id TEXT NOT NULL,
            overall_progress REAL DEFAULT 0,
            status TEXT DEFAULT 'in_progress',
            started_at TEXT,
            completed_at TEXT,
            last_updated TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id),
            UNIQUE(user_id, curriculum_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS learner_kp_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            progress_id TEXT NOT NULL,
            kp_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            mastery_level TEXT DEFAULT 'not_started',
            progress REAL DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0,
            last_practiced TEXT,
            next_review TEXT,
            FOREIGN KEY (progress_id) REFERENCES learner_curriculum_progress(progress_id),
            FOREIGN KEY (kp_id) REFERENCES curriculum_knowledge_points(kp_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, kp_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS learner_chapter_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            progress_id TEXT NOT NULL,
            chapter_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            progress REAL DEFAULT 0,
            status TEXT DEFAULT 'not_started',
            completed_at TEXT,
            FOREIGN KEY (progress_id) REFERENCES learner_curriculum_progress(progress_id),
            FOREIGN KEY (chapter_id) REFERENCES curriculum_chapters(chapter_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, chapter_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS learner_curriculum_recommendations (
            rec_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            curriculum_id TEXT NOT NULL,
            kp_id TEXT NOT NULL,
            recommendation_type TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            reason TEXT,
            suggested_action TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id),
            FOREIGN KEY (kp_id) REFERENCES curriculum_knowledge_points(kp_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS curriculum_assessment_results (
            result_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            curriculum_id TEXT NOT NULL,
            exam_id TEXT,
            overall_score REAL DEFAULT 0,
            kp_scores TEXT,
            strengths TEXT,
            weaknesses TEXT,
            recommendations TEXT,
            assessed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id),
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
        )''')

        conn.commit()
        conn.close()
        logger.info("学习与大纲追踪数据库表初始化完成")

    def start_curriculum(self, user_id: int, curriculum_id: str) -> Dict[str, Any]:
        """开始学习教学大纲"""
        progress_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO learner_curriculum_progress
                (progress_id, user_id, curriculum_id, overall_progress, status, started_at, last_updated)
                VALUES (?, ?, ?, 0, 'in_progress', ?, ?)''',
                          (progress_id, user_id, curriculum_id, now, now))

            cursor.execute('SELECT chapter_id FROM curriculum_chapters WHERE curriculum_id = ? ORDER BY chapter_number',
                           (curriculum_id,))
            chapters = [row[0] for row in cursor.fetchall()]

            cursor.execute('SELECT kp_id FROM curriculum_knowledge_points WHERE curriculum_id = ?',
                           (curriculum_id,))
            kps = [row[0] for row in cursor.fetchall()]

            for chapter_id in chapters:
                cursor.execute('''INSERT INTO learner_chapter_progress
                    (progress_id, chapter_id, user_id, progress, status)
                    VALUES (?, ?, ?, 0, 'not_started')''', (progress_id, chapter_id, user_id))

            for kp_id in kps:
                cursor.execute('''INSERT INTO learner_kp_progress
                    (progress_id, kp_id, user_id, mastery_level, progress)
                    VALUES (?, ?, ?, 'not_started', 0)''', (progress_id, kp_id, user_id))

            conn.commit()
            logger.info(f"用户 {user_id} 开始学习大纲 {curriculum_id}")
            return {'success': True, 'progress_id': progress_id, 'message': '开始学习成功'}
        except sqlite3.IntegrityError:
            conn.rollback()
            cursor.execute(
            'SELECT progress_id FROM learner_curriculum_progress WHERE user_id = ? AND curriculum_id = ?',
                           (user_id, curriculum_id))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {'success': False, 'error': '已在学习中', 'progress_id': row[0]}
            return {'success': False, 'error': '学习记录已存在'}
        except Exception as e:
            conn.rollback()
            logger.error(f"开始学习失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def update_kp_progress(self, user_id: int, kp_id: str, correct: bool,
                           total_attempts: int = 1) -> Dict[str, Any]:
        """更新知识点学习进度"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT correct_count, total_count, progress FROM learner_kp_progress
                WHERE user_id = ? AND kp_id = ?''', (user_id, kp_id))
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': '学习记录不存在'}

            correct_count, total_count, progress = row
            new_total = total_count + total_attempts
            new_correct = correct_count + (1 if correct else 0)
            new_progress = (new_correct / new_total) * 100 if new_total > 0 else 0

            mastery_level = 'not_started'
            if new_progress >= 90:
                mastery_level = 'mastered'
            elif new_progress >= 70:
                mastery_level = 'proficient'
            elif new_progress >= 50:
                mastery_level = 'learning'
            elif new_progress > 0:
                mastery_level = 'started'

            cursor.execute('''UPDATE learner_kp_progress SET
                correct_count = ?, total_count = ?, progress = ?,
                mastery_level = ?, last_practiced = ?, next_review = ?
                WHERE user_id = ? AND kp_id = ?''',
                          (new_correct, new_total, new_progress, mastery_level,
                           datetime.now().isoformat(),
                           (datetime.now() + timedelta(days=1)).isoformat() if new_progress < 90 else None,
                           user_id, kp_id))

            self._update_curriculum_overall_progress(conn, user_id)
            conn.commit()

            logger.info(f"更新知识点 {kp_id} 进度: {new_progress:.1f}%")
            return {
                'success': True,
                'progress': new_progress,
                'mastery_level': mastery_level,
                'correct_count': new_correct,
                'total_count': new_total
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"更新知识点进度失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def _update_curriculum_overall_progress(self, conn, user_id: int):
        """更新大纲整体进度"""
        cursor = conn.cursor()

        cursor.execute('''SELECT cp.progress_id, cp.curriculum_id,
            AVG(kp.progress) as avg_progress
            FROM learner_curriculum_progress cp
            JOIN learner_kp_progress kp ON cp.progress_id = kp.progress_id
            WHERE cp.user_id = ? AND cp.status = 'in_progress'
            GROUP BY cp.progress_id''', (user_id,))

        for row in cursor.fetchall():
            progress_id, curriculum_id, avg_progress = row
            cursor.execute('''UPDATE learner_curriculum_progress
                SET overall_progress = ?, last_updated = ?
                WHERE progress_id = ?''',
                          (avg_progress, datetime.now().isoformat(), progress_id))

            if avg_progress >= 100:
                cursor.execute('''UPDATE learner_curriculum_progress
                    SET status = 'completed', completed_at = ?
                    WHERE progress_id = ?''',
                              (datetime.now().isoformat(), progress_id))

    def update_chapter_progress(self, user_id: int, chapter_id: str, progress: float) -> Dict[str, Any]:
        """更新章节学习进度"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            status = 'completed' if progress >= 100 else 'in_progress'

            cursor.execute('''UPDATE learner_chapter_progress SET
                progress = ?, status = ?, completed_at = ?
                WHERE user_id = ? AND chapter_id = ?''',
                          (progress, status, datetime.now().isoformat() if progress >= 100 else None,
                           user_id, chapter_id))

            self._update_curriculum_overall_progress(conn, user_id)
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"更新章节 {chapter_id} 进度: {progress:.1f}%")
                return {'success': True, 'progress': progress, 'status': status}
            else:
                return {'success': False, 'error': '章节学习记录不存在'}
        except Exception as e:
            conn.rollback()
            logger.error(f"更新章节进度失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_curriculum_progress(self, user_id: int, curriculum_id: str = None) -> Dict[str, Any]:
        """获取教学大纲学习进度"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        query = '''SELECT cp.*, c.name as curriculum_name, c.subject, c.grade
            FROM learner_curriculum_progress cp
            JOIN curricula c ON cp.curriculum_id = c.curriculum_id
            WHERE cp.user_id = ?'''
        params = [user_id]
        if curriculum_id:
            query += ' AND cp.curriculum_id = ?'
            params.append(curriculum_id)

        cursor.execute(query, params)
        progress = cursor.fetchone()

        if not progress:
            conn.close()
            return {'success': False, 'error': '学习记录不存在'}

        result = dict(progress)

        cursor.execute('''SELECT lcp.*, cc.name as chapter_name, cc.chapter_number
            FROM learner_chapter_progress lcp
            JOIN curriculum_chapters cc ON lcp.chapter_id = cc.chapter_id
            WHERE lcp.user_id = ?''', (user_id,))
        if curriculum_id:
            cursor.execute('''SELECT lcp.*, cc.name as chapter_name, cc.chapter_number
                FROM learner_chapter_progress lcp
                JOIN curriculum_chapters cc ON lcp.chapter_id = cc.chapter_id
                WHERE lcp.user_id = ? AND cc.curriculum_id = ?''', (user_id, curriculum_id))

        chapters = []
        for ch_row in cursor.fetchall():
            chapter = dict(ch_row)
            cursor.execute('''SELECT lkp.*, kp.name as kp_name, kp.difficulty, kp.is_core
                FROM learner_kp_progress lkp
                JOIN curriculum_knowledge_points kp ON lkp.kp_id = kp.kp_id
                WHERE lkp.user_id = ? AND kp.chapter_id = ?''', (user_id, chapter['chapter_id']))
            chapter['knowledge_points'] = [dict(kp) for kp in cursor.fetchall()]
            chapters.append(chapter)
        result['chapters'] = chapters

        conn.close()
        return {'success': True, 'data': result}

    def get_kp_progress(self, user_id: int, kp_id: str = None) -> Dict[str, Any]:
        """获取知识点学习进度"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        query = '''SELECT lkp.*, kp.name as kp_name, kp.difficulty, kp.is_core, cc.name as chapter_name
            FROM learner_kp_progress lkp
            JOIN curriculum_knowledge_points kp ON lkp.kp_id = kp.kp_id
            LEFT JOIN curriculum_chapters cc ON kp.chapter_id = cc.chapter_id
            WHERE lkp.user_id = ?'''
        params = [user_id]
        if kp_id:
            query += ' AND lkp.kp_id = ?'
            params.append(kp_id)

        cursor.execute(query, params)
        progress = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {'success': True, 'data': progress}

    def generate_recommendations(self, user_id: int, curriculum_id: str) -> Dict[str, Any]:
        """生成学习建议"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        recommendations = []

        try:
            cursor.execute('''SELECT lkp.kp_id, lkp.progress, lkp.mastery_level,
                kp.name, kp.difficulty, kp.is_core
                FROM learner_kp_progress lkp
                JOIN curriculum_knowledge_points kp ON lkp.kp_id = kp.kp_id
                WHERE lkp.user_id = ? AND kp.curriculum_id = ?
                ORDER BY lkp.progress ASC''', (user_id, curriculum_id))

            low_progress_kps = cursor.fetchmany(5)
            for kp_id, progress, mastery, kp_name, difficulty, is_core in low_progress_kps:
                if progress < 50:
                    rec_id = str(uuid.uuid4())
                    recommendations.append({
                        'kp_id': kp_id,
                        'kp_name': kp_name,
                        'type': 'weakness',
                        'priority': 1 if is_core else 2,
                        'reason': f'掌握度较低 ({progress:.1f}%)',
                        'action': '建议加强练习该知识点'
                    })

                    cursor.execute('''INSERT INTO learner_curriculum_recommendations
                        (rec_id, user_id, curriculum_id, kp_id, recommendation_type,
                         priority, reason, suggested_action, created_at)
                        VALUES (?, ?, ?, ?, 'weakness', ?, ?, ?, ?)''',
                                  (rec_id, user_id, curriculum_id, kp_id,
                                   1 if is_core else 2,
                                   f'掌握度较低 ({progress:.1f}%)',
                                   '建议加强练习该知识点',
                                   datetime.now().isoformat()))

            conn.commit()
            logger.info(f"为用户 {user_id} 生成 {len(recommendations)} 条学习建议")
            return {'success': True, 'recommendations': recommendations}
        except Exception as e:
            conn.rollback()
            logger.error(f"生成学习建议失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_recommendations(self, user_id: int, curriculum_id: str = None) -> Dict[str, Any]:
        """获取学习建议"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        query = '''SELECT r.*, kp.name as kp_name
            FROM learner_curriculum_recommendations r
            JOIN curriculum_knowledge_points kp ON r.kp_id = kp.kp_id
            WHERE r.user_id = ?'''
        params = [user_id]
        if curriculum_id:
            query += ' AND r.curriculum_id = ?'
            params.append(curriculum_id)
        query += ' ORDER BY priority ASC, created_at DESC'

        cursor.execute(query, params)
        recommendations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {'success': True, 'data': recommendations}

    def record_assessment(self, user_id: int, curriculum_id: str, exam_id: str = None,
                          overall_score: float = 0, kp_scores: Dict[str, float] = None,
                          strengths: List[str] = None, weaknesses: List[str] = None,
                          recommendations: List[str] = None) -> Dict[str, Any]:
        """记录评估结果"""
        result_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO curriculum_assessment_results
                (result_id, user_id, curriculum_id, exam_id, overall_score,
                 kp_scores, strengths, weaknesses, recommendations, assessed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (result_id, user_id, curriculum_id, exam_id, overall_score,
                           json.dumps(kp_scores) if kp_scores else '{}',
                           json.dumps(strengths) if strengths else '[]',
                           json.dumps(weaknesses) if weaknesses else '[]',
                           json.dumps(recommendations) if recommendations else '[]',
                           now))
            conn.commit()
            logger.info(f"记录评估结果 {result_id} 用于用户 {user_id}")
            return {'success': True, 'result_id': result_id, 'message': '记录成功'}
        except Exception as e:
            conn.rollback()
            logger.error(f"记录评估结果失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_assessment_history(self, user_id: int, curriculum_id: str = None) -> Dict[str, Any]:
        """获取评估历史"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        query = 'SELECT * FROM curriculum_assessment_results WHERE user_id = ?'
        params = [user_id]
        if curriculum_id:
            query += ' AND curriculum_id = ?'
            params.append(curriculum_id)
        query += ' ORDER BY assessed_at DESC'

        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['kp_scores'] = json.loads(result.get('kp_scores', '{}'))
            result['strengths'] = json.loads(result.get('strengths', '[]'))
            result['weaknesses'] = json.loads(result.get('weaknesses', '[]'))
            result['recommendations'] = json.loads(result.get('recommendations', '[]'))
            results.append(result)

        conn.close()
        return {'success': True, 'data': results}

    def get_curriculum_stats_for_user(self, user_id: int) -> Dict[str, Any]:
        """获取用户学习大纲统计"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''SELECT COUNT(*) as total_courses,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_courses,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_courses
            FROM learner_curriculum_progress WHERE user_id = ?''', (user_id,))

        stats = cursor.fetchone()

        cursor.execute('''SELECT AVG(overall_progress) as avg_progress
            FROM learner_curriculum_progress WHERE user_id = ?''', (user_id,))
        avg_progress = cursor.fetchone()[0]

        cursor.execute('''SELECT COUNT(*) as mastered_kps,
            SUM(CASE WHEN mastery_level = 'proficient' THEN 1 ELSE 0 END) as proficient_kps,
            SUM(CASE WHEN mastery_level = 'learning' THEN 1 ELSE 0 END) as learning_kps,
            SUM(CASE WHEN mastery_level = 'started' THEN 1 ELSE 0 END) as started_kps
            FROM learner_kp_progress WHERE user_id = ?''', (user_id,))
        kp_stats = cursor.fetchone()

        conn.close()

        return {
            'total_courses': stats[0],
            'completed_courses': stats[1],
            'in_progress_courses': stats[2],
            'avg_progress': avg_progress or 0,
            'mastered_kps': kp_stats[0],
            'proficient_kps': kp_stats[1],
            'learning_kps': kp_stats[2],
            'started_kps': kp_stats[3]
        }


from datetime import timedelta

learning_curriculum_service = LearningCurriculumService()

if __name__ == '__main__':
    print("学习与大纲追踪服务测试")
    print("服务初始化完成")
