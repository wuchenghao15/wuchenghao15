from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学大纲管理服务
支持K12和成人教育教学大纲的管理、版本控制、知识点映射和同步
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'curriculum_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CurriculumService')


class CurriculumService:
    """教学大纲管理服务"""

    def __init__(self):
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS curricula (
            curriculum_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            education_level TEXT NOT NULL,
            grade TEXT,
            version TEXT DEFAULT '1.0',
            status TEXT DEFAULT 'active',
            description TEXT,
            created_by TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(name, subject, education_level, grade, version)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS curriculum_chapters (
            chapter_id TEXT PRIMARY KEY,
            curriculum_id TEXT NOT NULL,
            name TEXT NOT NULL,
            chapter_number INTEGER DEFAULT 0,
            description TEXT,
            estimated_hours REAL DEFAULT 0,
            prerequisite_chapter TEXT,
            is_required INTEGER DEFAULT 1,
            created_at TEXT,
            FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id),
            FOREIGN KEY (prerequisite_chapter) REFERENCES curriculum_chapters(chapter_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS curriculum_knowledge_points (
            kp_id TEXT PRIMARY KEY,
            chapter_id TEXT NOT NULL,
            curriculum_id TEXT NOT NULL,
            name TEXT NOT NULL,
            knowledge_code TEXT,
            difficulty TEXT DEFAULT 'medium',
            mastery_level TEXT DEFAULT 'basic',
            description TEXT,
            learning_objectives TEXT,
            teaching_hours REAL DEFAULT 1,
            assessment_method TEXT,
            sequence_number INTEGER DEFAULT 0,
            is_core INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (chapter_id) REFERENCES curriculum_chapters(chapter_id),
            FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS curriculum_standards (
            standard_id TEXT PRIMARY KEY,
            curriculum_id TEXT NOT NULL,
            standard_code TEXT NOT NULL,
            standard_name TEXT NOT NULL,
            description TEXT,
            domain TEXT,
            cluster TEXT,
            created_at TEXT,
            FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id),
            UNIQUE(curriculum_id, standard_code)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS curriculum_kp_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curriculum_id TEXT NOT NULL,
            kp_id TEXT NOT NULL,
            standard_id TEXT,
            question_category TEXT,
            exam_weight REAL DEFAULT 0,
            FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id),
            FOREIGN KEY (kp_id) REFERENCES curriculum_knowledge_points(kp_id),
            FOREIGN KEY (standard_id) REFERENCES curriculum_standards(standard_id),
            UNIQUE(kp_id, standard_id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS curriculum_version_history (
            history_id TEXT PRIMARY KEY,
            curriculum_id TEXT NOT NULL,
            version TEXT NOT NULL,
            change_type TEXT NOT NULL,
            change_description TEXT,
            changed_by TEXT,
            changed_at TEXT,
            FOREIGN KEY (curriculum_id) REFERENCES curricula(curriculum_id)
        )''')

        conn.commit()
        conn.close()
        logger.info("教学大纲数据库表初始化完成")

    def create_curriculum(self, name: str, subject: str, education_level: str, grade: str = None,
                          description: str = '', created_by: str = None) -> Dict[str, Any]:
        """创建教学大纲"""
        curriculum_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO curricula
                (curriculum_id, name, subject, education_level, grade, version,
                 description, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, '1.0', ?, ?, ?, ?)''',
                          (curriculum_id, name, subject, education_level, grade,
                           description, created_by, now, now))

            cursor.execute('''INSERT INTO curriculum_version_history
                (history_id, curriculum_id, version, change_type, change_description, changed_by, changed_at)
                VALUES (?, ?, '1.0', 'create', '创建教学大纲', ?, ?)''',
                          (str(uuid.uuid4()), curriculum_id, created_by, now))

            conn.commit()
            logger.info(f"创建教学大纲: {name} ({subject})")
            return {'success': True, 'curriculum_id': curriculum_id, 'message': '创建成功'}
        except sqlite3.IntegrityError:
            conn.rollback()
            return {'success': False, 'error': '该大纲已存在'}
        except Exception as e:
            conn.rollback()
            logger.error(f"创建教学大纲失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def add_chapter(self, curriculum_id: str, name: str, chapter_number: int = 0,
                    description: str = '', estimated_hours: float = 0,
                    prerequisite_chapter: str = None, is_required: bool = True) -> Dict[str, Any]:
        """添加章节"""
        chapter_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO curriculum_chapters
                (chapter_id, curriculum_id, name, chapter_number, description,
                 estimated_hours, prerequisite_chapter, is_required, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (chapter_id, curriculum_id, name, chapter_number, description,
                           estimated_hours, prerequisite_chapter, 1 if is_required else 0, now))
            conn.commit()
            logger.info(f"添加章节: {name} 到大纲 {curriculum_id}")
            return {'success': True, 'chapter_id': chapter_id, 'message': '添加成功'}
        except Exception as e:
            conn.rollback()
            logger.error(f"添加章节失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def add_knowledge_point(self, chapter_id: str, curriculum_id: str, name: str,
                            knowledge_code: str = '', difficulty: str = 'medium',
                            mastery_level: str = 'basic', description: str = '',
                            learning_objectives: str = '', teaching_hours: float = 1,
                            assessment_method: str = '', sequence_number: int = 0,
                            is_core: bool = False) -> Dict[str, Any]:
        """添加知识点"""
        kp_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO curriculum_knowledge_points
                (kp_id, chapter_id, curriculum_id, name, knowledge_code, difficulty,
                 mastery_level, description, learning_objectives, teaching_hours,
                 assessment_method, sequence_number, is_core, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (kp_id, chapter_id, curriculum_id, name, knowledge_code, difficulty,
                           mastery_level, description, learning_objectives, teaching_hours,
                           assessment_method, sequence_number, 1 if is_core else 0, now))
            conn.commit()
            logger.info(f"添加知识点: {name} 到章节 {chapter_id}")
            return {'success': True, 'kp_id': kp_id, 'message': '添加成功'}
        except Exception as e:
            conn.rollback()
            logger.error(f"添加知识点失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def add_standard(self, curriculum_id: str, standard_code: str, standard_name: str,
                     description: str = '', domain: str = '', cluster: str = '') -> Dict[str, Any]:
        """添加课程标准"""
        standard_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO curriculum_standards
                (standard_id, curriculum_id, standard_code, standard_name, description, domain, cluster, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (standard_id, curriculum_id, standard_code, standard_name, description, domain, cluster, now))
            conn.commit()
            logger.info(f"添加课程标准: {standard_code} 到大纲 {curriculum_id}")
            return {'success': True, 'standard_id': standard_id, 'message': '添加成功'}
        except sqlite3.IntegrityError:
            conn.rollback()
            return {'success': False, 'error': '该标准已存在'}
        except Exception as e:
            conn.rollback()
            logger.error(f"添加课程标准失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def map_kp_to_standard(self, kp_id: str, standard_id: str, curriculum_id: str,
                           question_category: str = '', exam_weight: float = 0) -> Dict[str, Any]:
        """将知识点映射到课程标准"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO curriculum_kp_mapping
                (curriculum_id, kp_id, standard_id, question_category, exam_weight)
                VALUES (?, ?, ?, ?, ?)''',
                          (curriculum_id, kp_id, standard_id, question_category, exam_weight))
            conn.commit()
            logger.info(f"映射知识点 {kp_id} 到标准 {standard_id}")
            return {'success': True, 'message': '映射成功'}
        except sqlite3.IntegrityError:
            conn.rollback()
            return {'success': False, 'error': '映射已存在'}
        except Exception as e:
            conn.rollback()
            logger.error(f"映射知识点失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_curriculum(self, curriculum_id: str) -> Optional[Dict[str, Any]]:
        """获取教学大纲详情"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM curricula WHERE curriculum_id = ?', (curriculum_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        curriculum = dict(row)

        cursor.execute('SELECT * FROM curriculum_chapters WHERE curriculum_id = ? ORDER BY chapter_number',
                       (curriculum_id,))
        chapters = []
        for chapter_row in cursor.fetchall():
            chapter = dict(chapter_row)
            cursor.execute('SELECT * FROM curriculum_knowledge_points WHERE chapter_id = ? ORDER BY sequence_number',
                           (chapter['chapter_id'],))
            chapter['knowledge_points'] = [dict(kp) for kp in cursor.fetchall()]
            chapters.append(chapter)
        curriculum['chapters'] = chapters

        cursor.execute('SELECT * FROM curriculum_standards WHERE curriculum_id = ?', (curriculum_id,))
        curriculum['standards'] = [dict(s) for s in cursor.fetchall()]

        conn.close()
        return curriculum

    def list_curricula(self, subject: str = None, education_level: str = None,
                       grade: str = None) -> List[Dict[str, Any]]:
        """列出教学大纲"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        query = 'SELECT * FROM curricula WHERE 1=1'
        params = []
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        if education_level:
            query += ' AND education_level = ?'
            params.append(education_level)
        if grade:
            query += ' AND grade = ?'
            params.append(grade)
        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        curricula = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return curricula

    def get_knowledge_points_by_curriculum(self, curriculum_id: str) -> List[Dict[str, Any]]:
        """获取大纲下所有知识点"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''SELECT kp.*, c.name as chapter_name
            FROM curriculum_knowledge_points kp
            JOIN curriculum_chapters c ON kp.chapter_id = c.chapter_id
            WHERE kp.curriculum_id = ?
            ORDER BY c.chapter_number, kp.sequence_number''', (curriculum_id,))

        kps = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return kps

    def get_kp_mapping(self, kp_id: str) -> List[Dict[str, Any]]:
        """获取知识点的映射关系"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''SELECT m.*, s.standard_code, s.standard_name
            FROM curriculum_kp_mapping m
            LEFT JOIN curriculum_standards s ON m.standard_id = s.standard_id
            WHERE m.kp_id = ?''', (kp_id,))

        mappings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return mappings

    def update_curriculum(self, curriculum_id: str, **kwargs) -> Dict[str, Any]:
        """更新教学大纲"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            allowed_columns = ['name', 'subject', 'education_level', 'grade', 'description', 'status', 'version',
            'updated_by']
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in allowed_columns}
            if not filtered_kwargs:
                return {'success': False, 'error': '没有有效的更新字段'}
            set_clause = ', '.join([f'{k} = ?' for k in filtered_kwargs.keys()])
            params = list(filtered_kwargs.values()) + [curriculum_id]

            cursor.execute(f'UPDATE curricula SET {set_clause} WHERE curriculum_id = ?', params)
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"更新教学大纲: {curriculum_id}")
                return {'success': True, 'message': '更新成功'}
            else:
                return {'success': False, 'error': '大纲不存在'}
        except Exception as e:
            conn.rollback()
            logger.error(f"更新教学大纲失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def delete_curriculum(self, curriculum_id: str) -> Dict[str, Any]:
        """删除教学大纲"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM curriculum_kp_mapping WHERE curriculum_id = ?', (curriculum_id,))
            cursor.execute('DELETE FROM curriculum_standards WHERE curriculum_id = ?', (curriculum_id,))
            cursor.execute('DELETE FROM curriculum_knowledge_points WHERE curriculum_id = ?', (curriculum_id,))
            cursor.execute('DELETE FROM curriculum_chapters WHERE curriculum_id = ?', (curriculum_id,))
            cursor.execute('DELETE FROM curriculum_version_history WHERE curriculum_id = ?', (curriculum_id,))
            cursor.execute('DELETE FROM curricula WHERE curriculum_id = ?', (curriculum_id,))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"删除教学大纲: {curriculum_id}")
                return {'success': True, 'message': '删除成功'}
            else:
                return {'success': False, 'error': '大纲不存在'}
        except Exception as e:
            conn.rollback()
            logger.error(f"删除教学大纲失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def generate_version(self, curriculum_id: str, change_description: str, changed_by: str = None) -> Dict[str, Any]:
        """生成新版本"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT version FROM curricula WHERE curriculum_id = ?', (curriculum_id,))
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': '大纲不存在'}

            current_version = row[0]
            major, minor = map(int, current_version.split('.'))
            new_version = f"{major}.{minor + 1}"

            cursor.execute('UPDATE curricula SET version = ?, updated_at = ? WHERE curriculum_id = ?',
                          (new_version, datetime.now().isoformat(), curriculum_id))

            cursor.execute('''INSERT INTO curriculum_version_history
                (history_id, curriculum_id, version, change_type, change_description, changed_by, changed_at)
                VALUES (?, ?, ?, 'update', ?, ?, ?)''',
                          (str(uuid.uuid4()), curriculum_id, new_version, change_description,
                           changed_by, datetime.now().isoformat()))

            conn.commit()
            logger.info(f"生成新版本 {new_version} 用于大纲 {curriculum_id}")
            return {'success': True, 'version': new_version, 'message': '版本升级成功'}
        except Exception as e:
            conn.rollback()
            logger.error(f"生成版本失败: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_version_history(self, curriculum_id: str) -> List[Dict[str, Any]]:
        """获取版本历史"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM curriculum_version_history WHERE curriculum_id = ? ORDER BY changed_at DESC',
                       (curriculum_id,))
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history


curriculum_service = CurriculumService()

if __name__ == '__main__':
    print("教学大纲管理服务测试")
    result = curriculum_service.create_curriculum(
        name="高中数学必修一",
        subject="数学",
        education_level="k12",
        grade="高一",
        description="高中数学第一学期教学大纲"
    )
    print("创建大纲:", result)
