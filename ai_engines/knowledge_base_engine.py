# -*- coding: utf-8 -*-
"""
智能知识库引擎
知识条目管理与语义检索系统：
- 多学科知识条目管理（知识点、概念、公式、定理、解题方法）
- 多层级知识分类与关联
- 关键词/语义检索
- 知识溯源与引用管理
- 知识点难度与重要性分级
- 知识学习进度追踪
- 知识图谱构建接口
- 知识版本管理
"""

import os
import sys
import json
import time
import hashlib
import re
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('knowledge_base_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('KnowledgeBaseEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 知识条目类型
KNOWLEDGE_TYPES = {
    'concept': {'name': '概念', 'icon': 'book', 'description': '基础概念定义'},
    'formula': {'name': '公式', 'icon': 'calculator', 'description': '数学/物理公式'},
    'theorem': {'name': '定理', 'icon': 'award', 'description': '定理定律'},
    'method': {'name': '解题方法', 'icon': 'lightbulb', 'description': '解题思路与方法'},
    'example': {'name': '典型例题', 'icon': 'file-text', 'description': '典型例题解析'},
    'summary': {'name': '知识总结', 'icon': 'layers', 'description': '知识点归纳总结'},
    'experiment': {'name': '实验', 'icon': 'flask', 'description': '实验原理与步骤'},
    'vocabulary': {'name': '词汇', 'icon': 'type', 'description': '词汇与短语'}
}

# 重要性等级
IMPORTANCE_LEVELS = {
    'core': {'name': '核心', 'weight': 1.0, 'color': '#ef4444'},
    'important': {'name': '重要', 'weight': 0.7, 'color': '#f97316'},
    'general': {'name': '一般', 'weight': 0.4, 'color': '#eab308'},
    'understanding': {'name': '了解', 'weight': 0.2, 'color': '#22c55e'}
}

# 难度等级
DIFFICULTY_LEVELS = {
    'easy': {'name': '简单', 'value': 1},
    'medium': {'name': '中等', 'value': 2},
    'hard': {'name': '困难', 'value': 3},
    'expert': {'name': '专家级', 'value': 4}
}


class KnowledgeBaseEngine:
    """智能知识库引擎 - 知识条目管理与语义检索"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._init_database()
        self._initialized = True
        logger.info("KnowledgeBaseEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 知识条目主表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_entries (
                        entry_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        summary TEXT,
                        knowledge_type TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        grade TEXT,
                        chapter TEXT,
                        section TEXT,
                        importance TEXT DEFAULT 'general',
                        difficulty TEXT DEFAULT 'medium',
                        tags TEXT DEFAULT '[]',
                        keywords TEXT DEFAULT '[]',
                        prerequisites TEXT DEFAULT '[]',
                        related_entries TEXT DEFAULT '[]',
                        examples TEXT DEFAULT '[]',
                        sources TEXT DEFAULT '[]',
                        version INTEGER DEFAULT 1,
                        author_id TEXT,
                        view_count INTEGER DEFAULT 0,
                        learn_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'published',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. 知识分类目录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_categories (
                        category_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        parent_id TEXT,
                        subject TEXT,
                        grade TEXT,
                        description TEXT,
                        sort_order INTEGER DEFAULT 0,
                        entry_count INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (parent_id) REFERENCES knowledge_categories(category_id)
                    )
                ''')

                # 3. 知识关联表（知识图谱边）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_relations (
                        relation_id TEXT PRIMARY KEY,
                        source_id TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        relation_type TEXT DEFAULT 'related',
                        strength REAL DEFAULT 0.5,
                        description TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(source_id, target_id, relation_type)
                    )
                ''')
                # 迁移：检查 source_id 列是否存在
                try:
                    cursor.execute('PRAGMA table_info(knowledge_relations)')
                    cols = {row[1] for row in cursor.fetchall()}
                    if 'source_id' not in cols:
                        cursor.execute('ALTER TABLE knowledge_relations ADD COLUMN source_id TEXT')
                    if 'target_id' not in cols:
                        cursor.execute('ALTER TABLE knowledge_relations ADD COLUMN target_id TEXT')
                    if 'relation_type' not in cols:
                        cursor.execute('ALTER TABLE knowledge_relations ADD COLUMN relation_type TEXT DEFAULT \'related\'')
                    if 'strength' not in cols:
                        cursor.execute('ALTER TABLE knowledge_relations ADD COLUMN strength REAL DEFAULT 0.5')
                    if 'description' not in cols:
                        cursor.execute('ALTER TABLE knowledge_relations ADD COLUMN description TEXT')
                except Exception as me:
                    logger.warning(f"knowledge_relations 迁移跳过: {me}")

                # 4. 用户知识学习记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_learning_log (
                        log_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        entry_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        duration INTEGER DEFAULT 0,
                        understanding_score REAL,
                        note TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 5. 知识检索索引表（倒排索引简化版）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_index (
                        index_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT NOT NULL,
                        entry_id TEXT NOT NULL,
                        weight REAL DEFAULT 1.0,
                        FOREIGN KEY (entry_id) REFERENCES knowledge_entries(entry_id)
                    )
                ''')

                # 6. 知识版本历史表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_version_history (
                        version_id TEXT PRIMARY KEY,
                        entry_id TEXT NOT NULL,
                        version INTEGER NOT NULL,
                        title TEXT,
                        content TEXT,
                        change_summary TEXT,
                        changed_by TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (entry_id) REFERENCES knowledge_entries(entry_id)
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ke_subject ON knowledge_entries(subject)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ke_type ON knowledge_entries(knowledge_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ke_importance ON knowledge_entries(importance)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ke_status ON knowledge_entries(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kc_subject ON knowledge_categories(subject)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kr_source ON knowledge_relations(source_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kr_target ON knowledge_relations(target_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kll_user ON knowledge_learning_log(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kll_entry ON knowledge_learning_log(entry_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ki_keyword ON knowledge_index(keyword)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ki_entry ON knowledge_index(entry_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化知识库引擎数据库失败: {e}")

    # ==================== 知识条目管理 ====================

    def add_entry(self, title: str, content: str, knowledge_type: str,
                  subject: str, summary: str = None, grade: str = None,
                  chapter: str = None, section: str = None,
                  importance: str = 'general', difficulty: str = 'medium',
                  tags: List[str] = None, prerequisites: List[str] = None,
                  related_entries: List[str] = None, examples: List[str] = None,
                  sources: List[str] = None, author_id: str = None) -> Dict[str, Any]:
        """添加知识条目"""
        with self._lock:
            try:
                if knowledge_type not in KNOWLEDGE_TYPES:
                    return {'success': False, 'error': f'不支持的知识类型: {knowledge_type}'}
                entry_id = f"ke_{int(time.time() * 1000)}"
                keywords = self._extract_keywords(title + ' ' + content)
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO knowledge_entries
                        (entry_id, title, content, summary, knowledge_type, subject,
                         grade, chapter, section, importance, difficulty,
                         tags, keywords, prerequisites, related_entries, examples,
                         sources, author_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (entry_id, title, content, summary, knowledge_type, subject,
                          grade, chapter, section, importance, difficulty,
                          json.dumps(tags or [], ensure_ascii=False),
                          json.dumps(keywords, ensure_ascii=False),
                          json.dumps(prerequisites or [], ensure_ascii=False),
                          json.dumps(related_entries or [], ensure_ascii=False),
                          json.dumps(examples or [], ensure_ascii=False),
                          json.dumps(sources or [], ensure_ascii=False),
                          author_id))
                    # 构建倒排索引
                    for kw in keywords:
                        cursor.execute('''
                            INSERT INTO knowledge_index (keyword, entry_id, weight)
                            VALUES (?, ?, ?)
                        ''', (kw, entry_id, 1.0))
                    # 添加相关条目关联
                    if related_entries:
                        for rel_id in related_entries:
                            cursor.execute('''
                                INSERT OR IGNORE INTO knowledge_relations
                                (relation_id, source_id, target_id, relation_type, strength)
                                VALUES (?, ?, ?, 'related', 0.7)
                            ''', (f"kr_{entry_id}_{rel_id}", entry_id, rel_id))
                    conn.commit()
                return {'success': True, 'entry_id': entry_id, 'title': title}
            except Exception as e:
                logger.error(f"添加知识条目失败: {e}")
                return {'success': False, 'error': str(e)}

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简化版）"""
        if not text:
            return []
        # 去除标点
        cleaned = re.sub(r'[，。、？！；：（）【】《》\s,.?!;:\'\"()\[\]]+', ' ', text)
        # 按空格和中文切分，取长度>=2的词
        words = [w for w in cleaned.split() if len(w) >= 2]
        # 去重并限制数量
        seen = set()
        keywords = []
        for w in words:
            if w not in seen and len(keywords) < 20:
                seen.add(w)
                keywords.append(w)
        return keywords

    def update_entry(self, entry_id: str, changed_by: str = None,
                     changes: Dict = None) -> Dict[str, Any]:
        """更新知识条目（带版本管理）"""
        with self._lock:
            try:
                if not changes:
                    return {'success': False, 'error': '没有更新内容'}
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM knowledge_entries WHERE entry_id = ?', (entry_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '知识条目不存在'}
                    # 保存旧版本
                    cursor.execute('SELECT version FROM knowledge_entries WHERE entry_id = ?', (entry_id,))
                    old_version = cursor.fetchone()[0] or 1
                    new_version = old_version + 1
                    # 保存历史版本
                    version_id = f"kv_{int(time.time() * 1000)}"
                    cursor.execute('''
                        INSERT INTO knowledge_version_history
                        (version_id, entry_id, version, title, content, change_summary, changed_by)
                        SELECT ?, ?, version, title, content, ?, ?
                        FROM knowledge_entries WHERE entry_id = ?
                    ''', (version_id, entry_id, old_version,
                          changes.get('change_summary', '更新条目'), changed_by, entry_id))
                    # 更新条目
                    set_clauses = []
                    params = []
                    for key, value in changes.items():
                        if key in ('title', 'content', 'summary', 'knowledge_type',
                                   'subject', 'grade', 'chapter', 'section',
                                   'importance', 'difficulty'):
                            set_clauses.append(f"{key} = ?")
                            params.append(value)
                        elif key in ('tags', 'keywords', 'prerequisites',
                                     'related_entries', 'examples', 'sources'):
                            set_clauses.append(f"{key} = ?")
                            params.append(json.dumps(value, ensure_ascii=False))
                    if set_clauses:
                        set_clauses.append("version = ?")
                        params.append(new_version)
                        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                        params.append(entry_id)
                        cursor.execute(f'''
                            UPDATE knowledge_entries
                            SET {', '.join(set_clauses)}
                            WHERE entry_id = ?
                        ''', params)
                        # 重新构建索引（如果内容或标题变更）
                        if 'title' in changes or 'content' in changes:
                            cursor.execute('DELETE FROM knowledge_index WHERE entry_id = ?', (entry_id,))
                            new_content = changes.get('content', row[2])
                            new_title = changes.get('title', row[1])
                            keywords = self._extract_keywords(new_title + ' ' + new_content)
                            for kw in keywords:
                                cursor.execute('''
                                    INSERT INTO knowledge_index (keyword, entry_id, weight)
                                    VALUES (?, ?, ?)
                                ''', (kw, entry_id, 1.0))
                    conn.commit()
                return {'success': True, 'entry_id': entry_id, 'version': new_version}
            except Exception as e:
                logger.error(f"更新知识条目失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_entry(self, entry_id: str, user_id: str = None) -> Dict[str, Any]:
        """获取知识条目详情"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM knowledge_entries WHERE entry_id = ?', (entry_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '知识条目不存在'}
                    entry = dict(row)
                    # 解析JSON字段
                    for key in ['tags', 'keywords', 'prerequisites', 'related_entries',
                                'examples', 'sources']:
                        entry[key] = json.loads(entry.get(key) or '[]')
                    # 增加浏览次数
                    cursor.execute('UPDATE knowledge_entries SET view_count = view_count + 1 WHERE entry_id = ?',
                                   (entry_id,))
                    # 记录学习日志
                    if user_id:
                        log_id = f"kll_{int(time.time() * 1000)}"
                        cursor.execute('''
                            INSERT INTO knowledge_learning_log
                            (log_id, user_id, entry_id, action)
                            VALUES (?, ?, ?, 'view')
                        ''', (log_id, user_id, entry_id))
                    # 获取关联条目
                    cursor.execute('''
                        SELECT k.entry_id, k.title, k.knowledge_type, k.importance
                        FROM knowledge_relations r
                        JOIN knowledge_entries k ON r.target_id = k.entry_id
                        WHERE r.source_id = ?
                        LIMIT 10
                    ''', (entry_id,))
                    related = [dict(r) for r in cursor.fetchall()]
                    entry['related_items'] = related
                    conn.commit()
                    return {'success': True, 'entry': entry}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def list_entries(self, subject: str = None, knowledge_type: str = None,
                     importance: str = None, grade: str = None,
                     chapter: str = None, keyword: str = None,
                     status: str = 'published', limit: int = 50,
                     offset: int = 0) -> Dict[str, Any]:
        """列出知识条目"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql = 'SELECT * FROM knowledge_entries WHERE status = ?'
                    params = [status]
                    if subject:
                        sql += ' AND subject = ?'
                        params.append(subject)
                    if knowledge_type:
                        sql += ' AND knowledge_type = ?'
                        params.append(knowledge_type)
                    if importance:
                        sql += ' AND importance = ?'
                        params.append(importance)
                    if grade:
                        sql += ' AND grade = ?'
                        params.append(grade)
                    if chapter:
                        sql += ' AND chapter = ?'
                        params.append(chapter)
                    if keyword:
                        sql += ' AND (title LIKE ? OR content LIKE ? OR keywords LIKE ?)'
                        like = f'%{keyword}%'
                        params.extend([like, like, like])
                    sql += ' ORDER BY importance DESC, view_count DESC LIMIT ? OFFSET ?'
                    params.extend([limit, offset])
                    cursor.execute(sql, params)
                    entries = []
                    for r in cursor.fetchall():
                        e = dict(r)
                        e['tags'] = json.loads(e.get('tags') or '[]')
                        entries.append(e)
                    # 总数
                    cursor.execute('SELECT COUNT(*) FROM knowledge_entries WHERE status = ?', (status,))
                    total = cursor.fetchone()[0]
                    return {'success': True, 'entries': entries, 'count': len(entries), 'total': total}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 语义检索 ====================

    def search(self, query: str, subject: str = None,
               knowledge_type: str = None, limit: int = 20) -> Dict[str, Any]:
        """智能搜索（关键词+语义关联）"""
        with self._lock:
            try:
                query_keywords = self._extract_keywords(query)
                if not query_keywords:
                    return self.list_entries(subject=subject, knowledge_type=knowledge_type, limit=limit)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    # 1. 通过倒排索引查找
                    placeholders = ','.join(['?' for _ in query_keywords])
                    cursor.execute(f'''
                        SELECT entry_id, SUM(weight) as score
                        FROM knowledge_index
                        WHERE keyword IN ({placeholders})
                        GROUP BY entry_id
                        ORDER BY score DESC
                        LIMIT ?
                    ''', query_keywords + [limit * 2])
                    index_results = {r[0]: r[1] for r in cursor.fetchall()}

                    # 2. 标题/内容模糊匹配
                    like_query = f'%{query}%'
                    sql = '''
                        SELECT entry_id, title, content, knowledge_type,
                               subject, importance, difficulty, summary, view_count
                        FROM knowledge_entries
                        WHERE status = 'published'
                    '''
                    params = []
                    if subject:
                        sql += ' AND subject = ?'
                        params.append(subject)
                    if knowledge_type:
                        sql += ' AND knowledge_type = ?'
                        params.append(knowledge_type)
                    sql += ' AND (title LIKE ? OR content LIKE ?)'
                    params.extend([like_query, like_query])
                    sql += ' ORDER BY view_count DESC LIMIT ?'
                    params.append(limit * 2)
                    cursor.execute(sql, params)
                    text_results = [dict(r) for r in cursor.fetchall()]

                    # 3. 合并结果并排序
                    scored = {}
                    for e in text_results:
                        eid = e['entry_id']
                        score = index_results.get(eid, 0) * 2
                        # 标题匹配加分
                        if query in e.get('title', ''):
                            score += 10
                        # 重要性加权
                        imp_weight = IMPORTANCE_LEVELS.get(e.get('importance'), {}).get('weight', 0.4)
                        score *= (0.5 + imp_weight)
                        scored[eid] = {'entry': e, 'score': score}

                    # 添加只有索引匹配的结果
                    for eid, idx_score in index_results.items():
                        if eid not in scored:
                            cursor.execute('''
                                SELECT entry_id, title, content, knowledge_type,
                                       subject, importance, difficulty, summary
                                FROM knowledge_entries WHERE entry_id = ? AND status = 'published'
                            ''', (eid,))
                            e = cursor.fetchone()
                            if e:
                                scored[eid] = {
                                    'entry': dict(e),
                                    'score': idx_score
                                }

                    # 按分数排序
                    sorted_results = sorted(scored.values(), key=lambda x: x['score'], reverse=True)[:limit]

                    return {
                        'success': True,
                        'query': query,
                        'results': [r['entry'] for r in sorted_results],
                        'count': len(sorted_results),
                        'query_keywords': query_keywords
                    }
            except Exception as e:
                logger.error(f"搜索失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 知识分类 ====================

    def add_category(self, name: str, subject: str = None,
                     parent_id: str = None, description: str = None,
                     grade: str = None, sort_order: int = 0) -> Dict[str, Any]:
        with self._lock:
            try:
                cat_id = f"kc_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO knowledge_categories
                        (category_id, name, parent_id, subject, description, grade, sort_order)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (cat_id, name, parent_id, subject, description, grade, sort_order))
                    conn.commit()
                return {'success': True, 'category_id': cat_id, 'name': name}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def list_categories(self, subject: str = None,
                        parent_id: str = None) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql = 'SELECT * FROM knowledge_categories WHERE 1=1'
                    params = []
                    if subject:
                        sql += ' AND subject = ?'
                        params.append(subject)
                    if parent_id:
                        sql += ' AND parent_id = ?'
                        params.append(parent_id)
                    elif parent_id is None and subject:
                        sql += ' AND parent_id IS NULL'
                    sql += ' ORDER BY sort_order, name'
                    cursor.execute(sql, params)
                    categories = [dict(r) for r in cursor.fetchall()]
                    return {'success': True, 'categories': categories, 'count': len(categories)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 学习记录 ====================

    def record_learning(self, user_id: str, entry_id: str,
                        action: str = 'learn', duration: int = 0,
                        understanding_score: float = None,
                        note: str = None) -> Dict[str, Any]:
        """记录学习行为"""
        with self._lock:
            try:
                log_id = f"kll_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO knowledge_learning_log
                        (log_id, user_id, entry_id, action, duration,
                         understanding_score, note)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, user_id, entry_id, action, duration,
                          understanding_score, note))
                    if action == 'learn':
                        cursor.execute(
                            'UPDATE knowledge_entries SET learn_count = learn_count + 1 WHERE entry_id = ?',
                            (entry_id,))
                    conn.commit()
                return {'success': True, 'log_id': log_id}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_user_learning_progress(self, user_id: str,
                                    subject: str = None) -> Dict[str, Any]:
        """获取用户知识学习进度"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    # 已学条目数
                    if subject:
                        cursor.execute('''
                            SELECT COUNT(DISTINCT l.entry_id) as cnt
                            FROM knowledge_learning_log l
                            JOIN knowledge_entries e ON l.entry_id = e.entry_id
                            WHERE l.user_id = ? AND e.subject = ?
                        ''', (user_id, subject))
                    else:
                        cursor.execute(
                            'SELECT COUNT(DISTINCT entry_id) as cnt FROM knowledge_learning_log WHERE user_id = ?',
                            (user_id,))
                    learned = cursor.fetchone()[0] or 0
                    # 总条目数
                    if subject:
                        cursor.execute(
                            'SELECT COUNT(*) as cnt FROM knowledge_entries WHERE subject = ? AND status = ?',
                            (subject, 'published'))
                    else:
                        cursor.execute(
                            "SELECT COUNT(*) as cnt FROM knowledge_entries WHERE status = 'published'")
                    total = cursor.fetchone()[0] or 1
                    # 学习时长
                    cursor.execute('''
                        SELECT COALESCE(SUM(duration), 0) as total_time
                        FROM knowledge_learning_log WHERE user_id = ?
                    ''', (user_id,))
                    total_time = cursor.fetchone()[0] or 0
                    # 最近学习记录
                    cursor.execute('''
                        SELECT l.*, e.title, e.subject
                        FROM knowledge_learning_log l
                        JOIN knowledge_entries e ON l.entry_id = e.entry_id
                        WHERE l.user_id = ?
                        ORDER BY l.created_at DESC LIMIT 10
                    ''', (user_id,))
                    recent = [dict(r) for r in cursor.fetchall()]
                    progress = round(learned / total * 100, 2)
                    return {
                        'success': True,
                        'user_id': user_id,
                        'learned_count': learned,
                        'total_entries': total,
                        'progress_percent': progress,
                        'total_study_time': total_time,
                        'recent_activities': recent
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 知识图谱 ====================

    def add_relation(self, source_id: str, target_id: str,
                     relation_type: str = 'related',
                     strength: float = 0.5, description: str = None) -> Dict[str, Any]:
        with self._lock:
            try:
                rel_id = f"kr_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_relations
                        (relation_id, source_id, target_id, relation_type, strength, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (rel_id, source_id, target_id, relation_type, strength, description))
                    conn.commit()
                return {'success': True, 'relation_id': rel_id}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_knowledge_graph(self, entry_id: str, depth: int = 2) -> Dict[str, Any]:
        """获取以某知识点为中心的知识图谱"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    nodes = {}
                    edges = []
                    visited = set()
                    to_visit = [(entry_id, 0)]
                    while to_visit:
                        eid, level = to_visit.pop(0)
                        if eid in visited or level > depth:
                            continue
                        visited.add(eid)
                        # 获取节点信息
                        cursor.execute('''
                            SELECT entry_id, title, knowledge_type, subject,
                                   importance, difficulty
                            FROM knowledge_entries WHERE entry_id = ?
                        ''', (eid,))
                        node = cursor.fetchone()
                        if node:
                            nodes[eid] = dict(node)
                        # 获取关联
                        cursor.execute('''
                            SELECT target_id, relation_type, strength
                            FROM knowledge_relations WHERE source_id = ?
                        ''', (eid,))
                        for rel in cursor.fetchall():
                            edges.append({
                                'source': eid,
                                'target': rel['target_id'],
                                'type': rel['relation_type'],
                                'strength': rel['strength']
                            })
                            if rel['target_id'] not in visited:
                                to_visit.append((rel['target_id'], level + 1))
                    return {
                        'success': True,
                        'center': entry_id,
                        'nodes': list(nodes.values()),
                        'edges': edges,
                        'node_count': len(nodes),
                        'edge_count': len(edges)
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 统计接口 ====================

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM knowledge_entries WHERE status = ?', ('published',))
                    total_entries = cursor.fetchone()[0]
                    cursor.execute('SELECT knowledge_type, COUNT(*) FROM knowledge_entries WHERE status = ? GROUP BY knowledge_type',
                                   ('published',))
                    type_stats = {r[0]: r[1] for r in cursor.fetchall()}
                    cursor.execute('SELECT subject, COUNT(*) FROM knowledge_entries WHERE status = ? GROUP BY subject',
                                   ('published',))
                    subject_stats = {r[0]: r[1] for r in cursor.fetchall()}
                    cursor.execute('SELECT COUNT(*) FROM knowledge_categories')
                    total_categories = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM knowledge_relations')
                    total_relations = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM knowledge_learning_log')
                    active_users = cursor.fetchone()[0]
                    cursor.execute('SELECT SUM(view_count) FROM knowledge_entries')
                    total_views = cursor.fetchone()[0] or 0
                    return {
                        'success': True,
                        'total_entries': total_entries,
                        'type_distribution': type_stats,
                        'subject_distribution': subject_stats,
                        'total_categories': total_categories,
                        'total_relations': total_relations,
                        'active_users': active_users,
                        'total_views': total_views
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_knowledge_types(self) -> Dict[str, Any]:
        return {'success': True, 'types': KNOWLEDGE_TYPES}

    def get_importance_levels(self) -> Dict[str, Any]:
        return {'success': True, 'levels': IMPORTANCE_LEVELS}

    def get_difficulty_levels(self) -> Dict[str, Any]:
        return {'success': True, 'levels': DIFFICULTY_LEVELS}


# 单例
knowledge_base_engine = KnowledgeBaseEngine()
