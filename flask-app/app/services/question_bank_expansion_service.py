# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""题库扩展服务 - 管理各类题目源和专项题库"""

import os
import sqlite3
import uuid
import json
import logging
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(app_root, 'app.db')


class QuestionSourceType(Enum):
    """题目源类型枚举"""
    
    # 国内考试真题
    GAOKAO_ZHENTI = "gaokao_zhenti"
    ZHONGKAO_ZHENTI = "zhongkao_zhenti"
    GAOKAO_MONIAN = "gaokao_monian"
    ZHONGKAO_MONIAN = "zhongkao_monian"
    
    # 自主招生
    ZIZHU_ZHAOSHENG = "zizhu_zhaosheng"
    DAXUE_ZIZHU = "daxue_zizhu"
    TIANJIN_ZIZHU = "tianjin_zizhu"
    
    # 专项竞赛
    OLYMPIC_MATH = "olympic_math"
    OLYMPIC_PHYSICS = "olympic_physics"
    OLYMPIC_CHEMISTRY = "olympic_chemistry"
    OLYMPIC_BIOLOGY = "olympic_biology"
    OLYMPIC_INFORMATICS = "olympic_informatics"
    
    # 国外竞赛真题
    USAMO = "usamo"
    IMO = "imo"
    IPhO = "ipho"
    IChO = "icho"
    IOI = "ioi"
    
    # 国外高校自主招生
    SAT = "sat"
    ACT = "act"
    AP = "ap"
    A_LEVEL = "a_level"
    IB = "ib"
    
    # 国际竞赛真题
    INTERNATIONAL_OLYMPIC = "international_olympic"
    ASIA_PACIFIC = "asia_pacific"
    
    # 基础模型专项练习
    FOUNDATION_MODEL = "foundation_model"
    DEEP_LEARNING = "deep_learning"
    MACHINE_LEARNING = "machine_learning"
    
    # 经典案例题型
    CLASSIC_CASE = "classic_case"
    EXTENDED_CASE = "extended_case"
    
    # 各教育机构经典案例
    EDUCATION_INSTITUTION = "education_institution"
    NEW_ORIENTAL = "new_oriental"
    XUEERSI = "xueersi"
    
    # 基础公式运用
    FORMULA_APPLICATION = "formula_application"
    FORMULA_TRICKS = "formula_tricks"
    
    # 成人教育技能
    ADULT_EDUCATION = "adult_education"
    VOCATIONAL_SKILLS = "vocational_skills"
    
    # 文科经典案例
    CLASSIC_LITERATURE = "classic_literature"
    READING_COMPREHENSION = "reading_comprehension"
    
    # 高分作文试炼
    HIGH_SCORE_ESSAY = "high_score_essay"
    COLLEGE_ESSAY = "college_essay"
    
    # 古文古诗词
    ANCIENT_POETRY = "ancient_poetry"
    ANCIENT_PROSE = "ancient_prose"
    
    # 重点复习题
    KEY_REVIEW = "key_review"
    HOT_TOPICS = "hot_topics"


class QuestionSourceInfo:
    """题目源信息"""
    
    def __init__(self, source_type: QuestionSourceType, name: str, description: str,
                 subject: str = None, difficulty: str = None, tags: List[str] = None):
        self.source_type = source_type
        self.name = name
        self.description = description
        self.subject = subject
        self.difficulty = difficulty
        self.tags = tags or []
    
    def to_dict(self) -> Dict:
        return {
            'source_type': self.source_type.value,
            'name': self.name,
            'description': self.description,
            'subject': self.subject,
            'difficulty': self.difficulty,
            'tags': self.tags
        }


class QuestionBankExpansionService:
    """题库扩展服务 - 管理各类题目源和专项题库"""
    
    _instance = None
    _lock = __import__('threading').RLock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._init_tables()
        self._init_default_sources()
        
        logger.info("[题库扩展服务] 初始化完成")
        self._initialized = True
    
    def _init_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS question_sources (
            source_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            subject TEXT,
            difficulty TEXT,
            tags TEXT DEFAULT '[]',
            is_active INTEGER DEFAULT 1,
            created_by TEXT,
            created_at TEXT,
            updated_at TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS source_question_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES question_sources(source_id),
            FOREIGN KEY (question_id) REFERENCES exam_questions(question_id),
            UNIQUE(source_id, question_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS source_metadata (
            meta_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            FOREIGN KEY (source_id) REFERENCES question_sources(source_id),
            UNIQUE(source_id, key)
        )''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_qs_source_type ON question_sources(source_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_qs_subject ON question_sources(subject)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sqm_source ON source_question_mapping(source_id)')
        
        conn.commit()
        conn.close()
    
    def _init_default_sources(self):
        """初始化默认题目源"""
        default_sources = [
            QuestionSourceInfo(QuestionSourceType.GAOKAO_ZHENTI, "高考真题", 
                              "历年全国各省市高考真题", "综合", "hard", 
                              ["高考", "真题", "全国卷", "地方卷"]),
            QuestionSourceInfo(QuestionSourceType.ZHONGKAO_ZHENTI, "中考真题",
                              "历年全国各省市中考真题", "综合", "medium",
                              ["中考", "真题", "初中"]),
            QuestionSourceInfo(QuestionSourceType.GAOKAO_MONIAN, "高考模拟题",
                              "高考模拟试卷和练习题", "综合", "medium",
                              ["高考", "模拟", "练习"]),
            QuestionSourceInfo(QuestionSourceType.ZHONGKAO_MONIAN, "中考模拟题",
                              "中考模拟试卷和练习题", "综合", "easy",
                              ["中考", "模拟", "练习"]),
            QuestionSourceInfo(QuestionSourceType.ZIZHU_ZHAOSHENG, "自主招生",
                              "国内高校自主招生试题", "综合", "hard",
                              ["自主招生", "名校"]),
            QuestionSourceInfo(QuestionSourceType.DAXUE_ZIZHU, "大学自主招生",
                              "985/211高校自主招生试题", "综合", "hard",
                              ["985", "211", "自主招生"]),
            QuestionSourceInfo(QuestionSourceType.OLYMPIC_MATH, "数学竞赛",
                              "全国数学奥林匹克竞赛", "数学", "hard",
                              ["竞赛", "数学", "奥数"]),
            QuestionSourceInfo(QuestionSourceType.OLYMPIC_PHYSICS, "物理竞赛",
                              "全国物理奥林匹克竞赛", "物理", "hard",
                              ["竞赛", "物理", "奥物"]),
            QuestionSourceInfo(QuestionSourceType.OLYMPIC_CHEMISTRY, "化学竞赛",
                              "全国化学奥林匹克竞赛", "化学", "hard",
                              ["竞赛", "化学", "奥化"]),
            QuestionSourceInfo(QuestionSourceType.OLYMPIC_BIOLOGY, "生物竞赛",
                              "全国生物奥林匹克竞赛", "生物", "hard",
                              ["竞赛", "生物", "奥生"]),
            QuestionSourceInfo(QuestionSourceType.OLYMPIC_INFORMATICS, "信息学竞赛",
                              "全国信息学奥林匹克竞赛", "计算机", "hard",
                              ["竞赛", "信息学", "NOIP"]),
            QuestionSourceInfo(QuestionSourceType.USAMO, "USAMO",
                              "美国数学奥林匹克", "数学", "expert",
                              ["国际竞赛", "美国", "数学"]),
            QuestionSourceInfo(QuestionSourceType.IMO, "IMO",
                              "国际数学奥林匹克", "数学", "expert",
                              ["国际竞赛", "IMO", "数学"]),
            QuestionSourceInfo(QuestionSourceType.IPhO, "IPhO",
                              "国际物理奥林匹克", "物理", "expert",
                              ["国际竞赛", "IPhO", "物理"]),
            QuestionSourceInfo(QuestionSourceType.IChO, "IChO",
                              "国际化学奥林匹克", "化学", "expert",
                              ["国际竞赛", "IChO", "化学"]),
            QuestionSourceInfo(QuestionSourceType.IOI, "IOI",
                              "国际信息学奥林匹克", "计算机", "expert",
                              ["国际竞赛", "IOI", "信息学"]),
            QuestionSourceInfo(QuestionSourceType.SAT, "SAT",
                              "美国高考", "英语", "medium",
                              ["国外考试", "SAT", "美国"]),
            QuestionSourceInfo(QuestionSourceType.ACT, "ACT",
                              "美国大学入学考试", "英语", "medium",
                              ["国外考试", "ACT", "美国"]),
            QuestionSourceInfo(QuestionSourceType.AP, "AP",
                              "美国大学先修课程", "综合", "medium",
                              ["国外考试", "AP", "大学"]),
            QuestionSourceInfo(QuestionSourceType.A_LEVEL, "A-Level",
                              "英国高中课程", "综合", "medium",
                              ["国外考试", "A-Level", "英国"]),
            QuestionSourceInfo(QuestionSourceType.IB, "IB",
                              "国际文凭课程", "综合", "medium",
                              ["国外考试", "IB", "国际"]),
            QuestionSourceInfo(QuestionSourceType.FOUNDATION_MODEL, "基础模型",
                              "AI基础模型专项练习", "计算机", "medium",
                              ["AI", "深度学习", "基础"]),
            QuestionSourceInfo(QuestionSourceType.CLASSIC_CASE, "经典案例",
                              "各学科经典案例题目", "综合", "medium",
                              ["经典", "案例"]),
            QuestionSourceInfo(QuestionSourceType.FORMULA_APPLICATION, "公式运用",
                              "基础公式巧用与运用", "数学", "easy",
                              ["公式", "运用", "数学"]),
            QuestionSourceInfo(QuestionSourceType.ADULT_EDUCATION, "成人教育",
                              "成人教育技能题库", "综合", "easy",
                              ["成人", "技能"]),
            QuestionSourceInfo(QuestionSourceType.CLASSIC_LITERATURE, "经典文学",
                              "文科经典案例文章解析", "语文", "medium",
                              ["文学", "解析", "文科"]),
            QuestionSourceInfo(QuestionSourceType.HIGH_SCORE_ESSAY, "高分作文",
                              "高分作文试炼题库", "语文", "medium",
                              ["作文", "写作", "语文"]),
            QuestionSourceInfo(QuestionSourceType.ANCIENT_POETRY, "古文古诗词",
                              "古文古诗词解析与默写", "语文", "easy",
                              ["古文", "诗词", "语文"]),
            QuestionSourceInfo(QuestionSourceType.KEY_REVIEW, "重点复习",
                              "重点复习题目", "综合", "medium",
                              ["重点", "复习", "考点"]),
            QuestionSourceInfo(QuestionSourceType.INTERNATIONAL_OLYMPIC, "国际竞赛",
                              "各类国际竞赛真题", "综合", "expert",
                              ["国际", "竞赛", "真题"]),
            QuestionSourceInfo(QuestionSourceType.ASIA_PACIFIC, "亚太竞赛",
                              "亚太地区竞赛题目", "综合", "hard",
                              ["亚太", "竞赛"])
        ]
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            for source in default_sources:
                cursor.execute('SELECT source_id FROM question_sources WHERE source_type = ?',
                              (source.source_type.value,))
                if not cursor.fetchone():
                    source_id = str(uuid.uuid4())[:16]
                    cursor.execute('''
                        INSERT INTO question_sources
                        (source_id, source_type, name, description, subject,
                         difficulty, tags, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (source_id, source.source_type.value, source.name, source.description,
                          source.subject, source.difficulty, json.dumps(source.tags, ensure_ascii=False),
                          datetime.now().isoformat()))
            
            conn.commit()
    
    def create_source(self, name: str, source_type: str, description: str = '',
                      metadata: Dict = None, subject: str = None, difficulty: str = None,
                      tags: List[str] = None, created_by: str = None) -> str:
        """创建题目源"""
        source_id = str(uuid.uuid4())[:16]
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO question_sources
                (source_id, source_type, name, description, subject,
                 difficulty, tags, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (source_id, source_type, name, description, subject, difficulty,
                  json.dumps(tags or [], ensure_ascii=False), created_by, datetime.now().isoformat()))
            
            if metadata:
                for key, value in metadata.items():
                    cursor.execute('''
                        INSERT INTO source_metadata (meta_id, source_id, key, value)
                        VALUES (?, ?, ?, ?)
                    ''', (str(uuid.uuid4())[:16], source_id, key, str(value)))
            
            conn.commit()
        
        return source_id
    
    def get_all_sources(self) -> List[Dict]:
        """获取所有题目源"""
        return self.get_sources()
    
    def get_source(self, source_id: str) -> Optional[Dict]:
        """获取单个题目源"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM question_sources WHERE source_id = ?', (source_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            
            if row:
                item = dict(zip(columns, row))
                item['tags'] = json.loads(item.get('tags') or '[]')
                item['metadata'] = self.get_source_metadata(source_id)
                return item
            return None
    
    def update_source(self, source_id: str, name: str = None, description: str = None,
                      metadata: Dict = None, **kwargs) -> bool:
        """更新题目源"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            update_data = {}
            if name:
                update_data['name'] = name
            if description:
                update_data['description'] = description
            if 'tags' in kwargs:
                update_data['tags'] = json.dumps(kwargs['tags'], ensure_ascii=False)
            update_data.update({k: v for k, v in kwargs.items() if k not in ['tags']})
            update_data['updated_at'] = datetime.now().isoformat()
            
            if update_data:
                set_clause = ', '.join([f'{k} = ?' for k in update_data.keys()])
                params = list(update_data.values())
                params.append(source_id)
                cursor.execute(f'UPDATE question_sources SET {set_clause} WHERE source_id = ?', params)
            
            if metadata:
                for key, value in metadata.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO source_metadata (meta_id, source_id, key, value)
                        VALUES (?, ?, ?, ?)
                    ''', (str(uuid.uuid4())[:16], source_id, key, str(value)))
            
            conn.commit()
            
            return cursor.rowcount > 0
    
    def add_questions_to_source(self, source_id: str, question_ids: List[str]) -> None:
        """批量添加题目到题目源"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            for question_id in question_ids:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO source_question_mapping (source_id, question_id)
                        VALUES (?, ?)
                    ''', (source_id, question_id))
                except sqlite3.IntegrityError:
                    pass
            
            conn.commit()
    
    def get_questions_by_source(self, source_id: str) -> List[Dict]:
        """获取题目源下的题目"""
        return self.get_source_questions(source_id)
    
    def add_tag(self, tag_name: str, description: str = '') -> str:
        """添加题目标记"""
        tag_id = str(uuid.uuid4())[:16]
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('CREATE TABLE IF NOT EXISTS question_tags (tag_id TEXT PRIMARY KEY, name TEXT UNIQUE, description TEXT, created_at TEXT)')
            
            try:
                cursor.execute('INSERT INTO question_tags (tag_id, name, description, created_at) VALUES (?, ?, ?, ?)',
                              (tag_id, tag_name, description, datetime.now().isoformat()))
            except sqlite3.IntegrityError:
                cursor.execute('SELECT tag_id FROM question_tags WHERE name = ?', (tag_name,))
                row = cursor.fetchone()
                tag_id = row[0] if row else tag_id
            
            conn.commit()
        
        return tag_id
    
    def get_all_tags(self) -> List[Dict]:
        """获取所有题目标记"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('CREATE TABLE IF NOT EXISTS question_tags (tag_id TEXT PRIMARY KEY, name TEXT UNIQUE, description TEXT, created_at TEXT)')
            cursor.execute('SELECT * FROM question_tags ORDER BY name')
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_sources(self, source_type: str = None, subject: str = None,
                    is_active: int = None) -> List[Dict]:
        """获取题目源列表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM question_sources WHERE 1=1'
            params = []
            
            if source_type:
                query += ' AND source_type = ?'
                params.append(source_type)
            if subject:
                query += ' AND subject = ?'
                params.append(subject)
            if is_active is not None:
                query += ' AND is_active = ?'
                params.append(is_active)
            
            query += ' ORDER BY name'
            
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                item = dict(zip(columns, row))
                item['tags'] = json.loads(item.get('tags') or '[]')
                results.append(item)
            
            return results
    
    def get_source_by_type(self, source_type: QuestionSourceType) -> Optional[Dict]:
        """根据类型获取题目源"""
        sources = self.get_sources(source_type=source_type.value)
        return sources[0] if sources else None
    
    def update_source(self, source_id: str, **kwargs) -> bool:
        """更新题目源"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            if 'tags' in kwargs:
                kwargs['tags'] = json.dumps(kwargs['tags'], ensure_ascii=False)
            
            kwargs['updated_at'] = datetime.now().isoformat()
            
            set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
            params = list(kwargs.values())
            params.append(source_id)
            
            cursor.execute(f'UPDATE question_sources SET {set_clause} WHERE source_id = ?', params)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_source(self, source_id: str) -> bool:
        """删除题目源"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM source_question_mapping WHERE source_id = ?', (source_id,))
            cursor.execute('DELETE FROM source_metadata WHERE source_id = ?', (source_id,))
            cursor.execute('DELETE FROM question_sources WHERE source_id = ?', (source_id,))
            
            conn.commit()
            
            return cursor.rowcount > 0
    
    def add_question_to_source(self, source_id: str, question_id: str) -> bool:
        """将题目添加到题目源"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO source_question_mapping (source_id, question_id)
                    VALUES (?, ?)
                ''', (source_id, question_id))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def remove_question_from_source(self, source_id: str, question_id: str) -> bool:
        """从题目源移除题目"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM source_question_mapping WHERE source_id = ? AND question_id = ?
            ''', (source_id, question_id))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_source_questions(self, source_id: str) -> List[Dict]:
        """获取题目源中的题目"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT q.* FROM exam_questions q
                JOIN source_question_mapping m ON q.question_id = m.question_id
                WHERE m.source_id = ?
            ''', (source_id,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def set_source_metadata(self, source_id: str, key: str, value: str) -> bool:
        """设置题目源元数据"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO source_metadata (meta_id, source_id, key, value)
                VALUES (?, ?, ?, ?)
            ''', (str(uuid.uuid4())[:16], source_id, key, value))
            
            conn.commit()
            
            return True
    
    def get_source_metadata(self, source_id: str, key: str = None) -> Dict:
        """获取题目源元数据"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            if key:
                cursor.execute('''
                    SELECT key, value FROM source_metadata WHERE source_id = ? AND key = ?
                ''', (source_id, key))
                row = cursor.fetchone()
                return {row[0]: row[1]} if row else {}
            else:
                cursor.execute('''
                    SELECT key, value FROM source_metadata WHERE source_id = ?
                ''', (source_id,))
                return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_source_type_stats(self) -> Dict:
        """获取各类题目源统计"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT source_type, COUNT(*) FROM question_sources GROUP BY source_type')
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.execute('SELECT subject, COUNT(*) FROM question_sources GROUP BY subject')
            by_subject = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.execute('SELECT COUNT(*) FROM question_sources')
            total = cursor.fetchone()[0]
            
            return {
                'total_sources': total,
                'by_type': by_type,
                'by_subject': by_subject
            }
    
    def generate_questions_by_source(self, source_type: str, count: int = 10,
                                     difficulty: str = 'medium', subject: str = None) -> Dict:
        """按题目源类型生成题目"""
        from app.services.ai_question_generation_service import ai_question_generation_service
        
        source_info = self.get_source_by_type(QuestionSourceType(source_type))
        if not source_info:
            return {'success': False, 'message': '题目源不存在'}
        
        actual_subject = subject or source_info.get('subject', '综合')
        
        result = ai_question_generation_service.generate_questions(
            text=f"生成{source_info['name']}的{actual_subject}题目",
            count=count,
            difficulty=difficulty,
            subject=actual_subject
        )
        
        if result.get('success'):
            result['source_type'] = source_type
            result['source_name'] = source_info['name']
        
        return result


question_bank_expansion_service = QuestionBankExpansionService()