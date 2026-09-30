from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 题库与教学大纲同步服务 实现题目与知识点的映射、同步和智能出题功能 """

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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'question_bank_sync.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('QuestionBankSync')


class QuestionBankSyncService:
    """题库与大纲同步服务"""

    def __init__(self):
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_kp_mapping ( id INTEGER PRIMARY KEY AUTOINCREMENT, question_id TEXT NOT NULL, kp_id TEXT NOT NULL, curriculum_id TEXT NOT NULL, mapping_type TEXT DEFAULT 'manual', confidence REAL DEFAULT 0.8, created_at TEXT, FOREIGN KEY (question_id) REFERENCES exam_questions(question_id), FOREIGN KEY (kp_id) REFERENCES curriculum_knowledge_points(kp_id), FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id), UNIQUE(question_id, kp_id) )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS exam_kp_mapping ( id INTEGER PRIMARY KEY AUTOINCREMENT, exam_id TEXT NOT NULL, kp_id TEXT NOT NULL, curriculum_id TEXT NOT NULL, question_count INTEGER DEFAULT 0, weight REAL DEFAULT 0, created_at TEXT, FOREIGN KEY (exam_id) REFERENCES exams(exam_id), FOREIGN KEY (kp_id) REFERENCES curriculum_knowledge_points(kp_id), FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id), UNIQUE(exam_id, kp_id) )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS sync_tasks ( task_id TEXT PRIMARY KEY, task_type TEXT NOT NULL, source TEXT NOT NULL, target TEXT NOT NULL, status TEXT DEFAULT 'pending', progress REAL DEFAULT 0, total_items INTEGER DEFAULT 0, completed_items INTEGER DEFAULT 0, error_message TEXT, created_at TEXT, started_at TEXT, completed_at TEXT )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS question_curriculum_stats ( stat_id TEXT PRIMARY KEY, curriculum_id TEXT NOT NULL, kp_id TEXT, total_questions INTEGER DEFAULT 0, easy_count INTEGER DEFAULT 0, medium_count INTEGER DEFAULT 0, hard_count INTEGER DEFAULT 0, avg_correct_rate REAL DEFAULT 0, last_updated TEXT, FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id), FOREIGN KEY (kp_id) REFERENCES curriculum_knowledge_points(kp_id) )''')

        conn.commit()
        conn.close()
        logger.info("题库同步数据库表初始化完成")

    def map_question_to_kp(self, question_id: str, kp_id: str, curriculum_id: str,
                           mapping_type: str = 'manual', confidence: float = 0.8) -> Dict[str, Any]:
        """将题目映射到知识点"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO question_kp_mapping  (question_id, kp_id, curriculum_id, mapping_type, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)''',
                          (question_id, kp_id, curriculum_id, mapping_type, confidence, datetime.now().isoformat()))
            conn.commit()
            logger.info(f"映射题目 {question_id} 到知识点 {kp_id}")
            return {'success': True, 'message': '映射成功'}
        except sqlite3.IntegrityError:
            conn.rollback()
            return {'success': False, 'error': '映射已存在'}
        except Exception as e:
            conn.rollback()
            logger.error(f"映射题目失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def batch_map_questions(self, question_ids: List[str], kp_id: str, curriculum_id: str) -> Dict[str, Any]:
        """批量映射题目到知识点"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        success_count = 0
        fail_count = 0
        try:
            for qid in question_ids:
                try:
                    cursor.execute('''INSERT INTO question_kp_mapping  (question_id, kp_id, curriculum_id, mapping_type, confidence, created_at) VALUES (?, ?, ?, 'batch', 0.7, ?)''',
                                  (qid, kp_id, curriculum_id, datetime.now().isoformat()))
                    success_count += 1
                except sqlite3.IntegrityError:
                    fail_count += 1
            conn.commit()
            logger.info(f"批量映射完成: {success_count}成功, {fail_count}失败")
            return {'success': True, 'success_count': success_count, 'fail_count': fail_count}
        except Exception as e:
            conn.rollback()
            logger.error(f"批量映射失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_questions_by_kp(self, kp_id: str, curriculum_id: str = None) -> List[Dict[str, Any]]:
        """获取知识点关联的题目"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        query = '''SELECT q.*, m.confidence, m.mapping_type FROM exam_questions q JOIN question_kp_mapping m ON q.question_id = m.question_id WHERE m.kp_id = ?'''
        params = [kp_id]
        if curriculum_id:
            query += ' AND m.curriculum_id = ?'
            params.append(curriculum_id)

        cursor.execute(query, params)
        questions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return questions

    def get_kps_by_question(self, question_id: str) -> List[Dict[str, Any]]:
        """获取题目关联的知识点"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''SELECT kp.*, m.confidence, m.mapping_type, c.name as chapter_name FROM curriculum_knowledge_points kp JOIN question_kp_mapping m ON kp.kp_id = m.kp_id LEFT JOIN curriculum_chapters c ON kp.chapter_id = c.chapter_id WHERE m.question_id = ?''', (question_id,))

        kps = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return kps

    def sync_exam_with_curriculum(self, exam_id: str, curriculum_id: str) -> Dict[str, Any]:
        """同步考试与教学大纲"""
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO sync_tasks (task_id, task_type, source, target, status, created_at, started_at) VALUES (?, 'exam_curriculum_sync', ?, ?, 'running', ?, ?)''',
                          (task_id, curriculum_id, exam_id, now, now))

            cursor.execute('SELECT kp_id FROM curriculum_knowledge_points WHERE curriculum_id = ?',
                          (curriculum_id,))
            kp_ids = [row[0] for row in cursor.fetchall()]

            for kp_id in kp_ids:
                cursor.execute('''SELECT COUNT(*) FROM question_kp_mapping  WHERE kp_id = ? AND curriculum_id = ?''', (kp_id, curriculum_id))
                question_count = cursor.fetchone()[0]

                try:
                    cursor.execute('''INSERT INTO exam_kp_mapping (exam_id, kp_id, curriculum_id, question_count, weight, created_at) VALUES (?, ?, ?, ?, 0, ?)''',
                                  (exam_id, kp_id, curriculum_id, question_count, now))
                except sqlite3.IntegrityError:
                    cursor.execute('''UPDATE exam_kp_mapping SET question_count = ?  WHERE exam_id = ? AND kp_id = ?''', (question_count, exam_id, kp_id))

            cursor.execute('UPDATE sync_tasks SET status = ?, progress = 100, completed_at = ? WHERE task_id = ?',
                          ('completed', datetime.now().isoformat(), task_id))
            conn.commit()

            logger.info(f"同步考试 {exam_id} 与大纲 {curriculum_id} 完成")
            return {'success': True, 'task_id': task_id, 'mapped_kps': len(kp_ids)}
        except Exception as e:
            cursor.execute('UPDATE sync_tasks SET status = ?, error_message = ? WHERE task_id = ?',
                          ('failed', str(e), task_id))
            conn.commit()
            logger.error(f"同步考试与大纲失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def generate_questions_by_kp(self, kp_id: str, count: int = 5,
                                  difficulty: str = 'medium') -> Dict[str, Any]:
        """根据知识点生成题目"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT name, knowledge_code, difficulty, description FROM curriculum_knowledge_points WHERE kp_id = ?',
                       (kp_id,))
        kp = cursor.fetchone()
        if not kp:
            conn.close()
            return {'success': False, 'error': '知识点不存在'}

        kp_name, kp_code, kp_difficulty, kp_desc = kp
        generated = []

        for i in range(count):
            question_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            question_text = f"关于{kp_name}的测试题{i+1}"
            options = ['选项A', '选项B', '选项C', '选项D']
            correct_answer = 'A'
            explanation = f"本题考察{kp_name}的理解与应用"

            cursor.execute('''INSERT INTO exam_questions (question_id, question_text, options, correct_answer, explanation, question_type, difficulty, subject, chapter, knowledge_point, analysis, source, created_at) VALUES (?, ?, ?, ?, ?, 'single_choice', ?, '数学', ?, ?, ?, 'curriculum_generated', ?)''',
                          (question_id, question_text, json.dumps(options), correct_answer, explanation,
                           difficulty, kp_name, kp_name, now))

            cursor.execute('''INSERT INTO question_kp_mapping (question_id, kp_id, curriculum_id, mapping_type, confidence, created_at) VALUES (?, ?, '', 'auto_generated', 0.9, ?)''', (question_id, kp_id, now))

            generated.append({'question_id': question_id, 'question_text': question_text})

        conn.commit()
        conn.close()
        logger.info(f"为知识点 {kp_id} 生成 {count} 道题目")
        return {'success': True, 'generated': generated}

    def generate_exam_by_curriculum(self, curriculum_id: str, exam_name: str,
                                    total_questions: int = 20, duration_minutes: int = 60,
                                    creator_id: int = None) -> Dict[str, Any]:
        """根据教学大纲生成考试"""
        exam_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT name, subject FROM curricula WHERE curriculum_id = ?', (curriculum_id,))
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': '大纲不存在'}

            cursor.execute('''INSERT INTO exams (exam_id, exam_name, exam_type, subject, grade, duration_minutes, total_score, passing_score, question_count, status, created_by, created_at) VALUES (?, ?, 'curriculum_based', ?, '', ?, 100, 60, ?, 'draft', ?, ?)''',
                          (exam_id, exam_name, row[1], duration_minutes, total_questions, creator_id, now))

            cursor.execute('''SELECT kp_id, difficulty, is_core  FROM curriculum_knowledge_points WHERE curriculum_id = ?''', (curriculum_id,))
            kps = cursor.fetchall()

            if not kps:
                return {'success': False, 'error': '大纲中没有知识点'}

            questions_per_kp = max(1, total_questions // len(kps))
            selected_questions = []

            for kp_id, kp_diff, is_core in kps:
                cursor.execute('''SELECT q.question_id FROM exam_questions q JOIN question_kp_mapping m ON q.question_id = m.question_id WHERE m.kp_id = ? ORDER BY RANDOM() LIMIT ?''', (kp_id, questions_per_kp))

                for q_row in cursor.fetchall():
                    selected_questions.append((exam_id, q_row[0], len(selected_questions) + 1))

                if len(selected_questions) >= total_questions:
                    break

            if selected_questions:
                cursor.executemany('''INSERT INTO exam_question_mapping (exam_id, question_id, question_order) VALUES (?, ?, ?)''', selected_questions)

            cursor.execute('''INSERT INTO exam_kp_mapping (exam_id, kp_id, curriculum_id, question_count, created_at)''')
            for kp_id, _, _ in kps:
                try:
                    cursor.execute('''INSERT INTO exam_kp_mapping (exam_id, kp_id, curriculum_id, question_count, created_at) VALUES (?, ?, ?, 0, ?)''', (exam_id, kp_id, curriculum_id, now))
                except sqlite3.IntegrityError:
                    pass

            cursor.execute('UPDATE exams SET status = ?, question_count = ? WHERE exam_id = ?',
                          ('scheduled', len(selected_questions), exam_id))
            conn.commit()

            logger.info(f"根据大纲 {curriculum_id} 生成考试 {exam_id}")
            return {'success': True, 'exam_id': exam_id, 'question_count': len(selected_questions)}
        except Exception as e:
            conn.rollback()
            logger.error(f"生成考试失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_curriculum_stats(self, curriculum_id: str) -> Dict[str, Any]:
        """获取大纲题库统计"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''SELECT  COUNT(DISTINCT m.question_id) as total_questions, SUM(CASE WHEN q.difficulty = 'easy' THEN 1 ELSE 0 END) as easy_count, SUM(CASE WHEN q.difficulty = 'medium' THEN 1 ELSE 0 END) as medium_count, SUM(CASE WHEN q.difficulty = 'hard' THEN 1 ELSE 0 END) as hard_count FROM question_kp_mapping m LEFT JOIN exam_questions q ON m.question_id = q.question_id WHERE m.curriculum_id = ?''', (curriculum_id,))

        stats = cursor.fetchone()
        if not stats:
            conn.close()
            return {'total_questions': 0, 'easy_count': 0, 'medium_count': 0, 'hard_count': 0}

        cursor.execute('''SELECT kp.kp_id, kp.name, COUNT(m.question_id) as question_count FROM curriculum_knowledge_points kp LEFT JOIN question_kp_mapping m ON kp.kp_id = m.kp_id WHERE kp.curriculum_id = ? GROUP BY kp.kp_id''', (curriculum_id,))

        kp_stats = [{'kp_id': row[0], 'kp_name': row[1], 'question_count': row[2]}
                    for row in cursor.fetchall()]

        conn.close()
        return {
            'total_questions': stats[0],
            'easy_count': stats[1],
            'medium_count': stats[2],
            'hard_count': stats[3],
            'kp_stats': kp_stats
        }

    def get_sync_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取同步任务状态"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM sync_tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_sync_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """列出同步任务"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        query = 'SELECT * FROM sync_tasks WHERE 1=1'
        params = []
        if status:
            query += ' AND status = ?'
            params.append(status)
        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks


question_bank_sync_service = QuestionBankSyncService()

if __name__ == '__main__':
    print("题库与大纲同步服务测试")
    print("服务初始化完成")
