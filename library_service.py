#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 图书馆服务 (v15.5.0)
====================================
提供图书管理、借阅、预约、推荐和阅读统计等综合服务。

核心能力：
1. 图书管理 - 图书入库、分类、检索
2. 借阅管理 - 借书、还书、续借、逾期
3. 预约管理 - 图书预约、到馆提醒
4. 阅读统计 - 借阅统计、阅读排行
5. 荐购管理 - 读者荐购、采购管理
6. 读者信用 - 信用积分、借阅权限
7. 成人图书馆 - 成人教育文献资源
8. K12图书馆 - 九年制义务教育图书
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Library')


# ========== 图书馆配置 ==========

# 图书分类
BOOK_CATEGORIES = {
    'literature': {'name': '文学', 'shelf': 'A区', 'loan_days': 30},
    'history': {'name': '历史', 'shelf': 'B区', 'loan_days': 30},
    'science': {'name': '科学', 'shelf': 'C区', 'loan_days': 30},
    'technology': {'name': '技术', 'shelf': 'D区', 'loan_days': 21},
    'education': {'name': '教育', 'shelf': 'E区', 'loan_days': 30},
    'language': {'name': '语言', 'shelf': 'F区', 'loan_days': 21},
    'art': {'name': '艺术', 'shelf': 'G区', 'loan_days': 30},
    'children': {'name': '儿童读物', 'shelf': 'H区', 'loan_days': 21},
    'reference': {'name': '参考书', 'shelf': 'I区', 'loan_days': 7},
    'magazine': {'name': '期刊杂志', 'shelf': 'J区', 'loan_days': 14},
    'test_prep': {'name': '考试用书', 'shelf': 'K区', 'loan_days': 14},
    'textbook': {'name': '教材', 'shelf': 'L区', 'loan_days': 90}
}

# 借阅状态
BORROW_STATUS = {
    'borrowed': {'name': '借阅中', 'color': '#1890ff'},
    'returned': {'name': '已归还', 'color': '#52c41a'},
    'overdue': {'name': '已逾期', 'color': '#f5222d'},
    'lost': {'name': '已丢失', 'color': '#8c8c8c'},
    'damaged': {'name': '已损坏', 'color': '#faad14'},
    'renewed': {'name': '已续借', 'color': '#722ed1'}
}

# 预约状态
RESERVE_STATUS = {
    'pending': {'name': '等待中', 'color': '#faad14'},
    'available': {'name': '可借阅', 'color': '#52c41a'},
    'picked_up': {'name': '已取书', 'color': '#1890ff'},
    'expired': {'name': '已过期', 'color': '#8c8c8c'},
    'cancelled': {'name': '已取消', 'color': '#f5222d'}
}

# 读者等级
READER_LEVELS = {
    1: {'name': '初级读者', 'max_borrow': 5, 'renew_times': 1, 'reserve_max': 3},
    2: {'name': '普通读者', 'max_borrow': 10, 'renew_times': 2, 'reserve_max': 5},
    3: {'name': '资深读者', 'max_borrow': 15, 'renew_times': 3, 'reserve_max': 8},
    4: {'name': '黄金读者', 'max_borrow': 20, 'renew_times': 5, 'reserve_max': 10},
    5: {'name': '钻石读者', 'max_borrow': 30, 'renew_times': 5, 'reserve_max': 15}
}

# 成人教育图书类型
ADULT_BOOK_TYPES = {
    'japanese': {'name': '日语学习', 'subtypes': ['教材', '听力', '语法', '阅读', '词汇', '能力考']},
    'english': {'name': '英语学习', 'subtypes': ['教材', '听力', '口语', '写作', '阅读', '词汇']},
    'business': {'name': '商务职场', 'subtypes': ['简历', '面试', '商务礼仪', '职业技能']},
    'exam': {'name': '考试辅导', 'subtypes': ['JLPT', 'J.TEST', '托业', '托福', '雅思']},
    'self_improvement': {'name': '自我提升', 'subtypes': ['心理', '沟通', '管理', '理财']}
}

# K12图书类型
K12_BOOK_TYPES = {
    'textbook': {'name': '教材教辅', 'grades': ['小学', '初中', '高中']},
    'extracurricular': {'name': '课外读物', 'subtypes': ['文学', '科普', '历史', '传记']},
    'exam': {'name': '升学考试', 'subtypes': ['中考', '高考', '小升初']},
    'comic': {'name': '漫画绘本', 'subtypes': ['绘本', '漫画', '故事']},
    'reference': {'name': '工具书', 'subtypes': ['字典', '词典', '百科']}
}

# 逾期罚款规则
OVERDUE_FINE_RULE = {
    'per_day': 0.1,
    'max_amount': 50.0,
    'grace_days': 2
}


class LibraryService:
    """图书馆服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS books (
                        book_id TEXT PRIMARY KEY,
                        isbn TEXT,
                        title TEXT NOT NULL,
                        subtitle TEXT,
                        author TEXT,
                        publisher TEXT,
                        publish_date TEXT,
                        category TEXT,
                        book_type TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        total_pages INTEGER,
                        total_copies INTEGER DEFAULT 1,
                        available_copies INTEGER DEFAULT 1,
                        current_borrowed INTEGER DEFAULT 0,
                        shelf_location TEXT,
                        price REAL DEFAULT 0,
                        language TEXT DEFAULT '中文',
                        summary TEXT,
                        tags TEXT,
                        cover_url TEXT,
                        times_borrowed INTEGER DEFAULT 0,
                        times_reserved INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0,
                        rating_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'available',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS borrow_records (
                        borrow_id TEXT PRIMARY KEY,
                        book_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        borrow_date TEXT NOT NULL,
                        due_date TEXT NOT NULL,
                        return_date TEXT,
                        actual_days INTEGER,
                        overdue_days INTEGER DEFAULT 0,
                        fine_amount REAL DEFAULT 0,
                        fine_paid INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'borrowed',
                        renewed_times INTEGER DEFAULT 0,
                        operator_borrow TEXT,
                        operator_return TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS book_reservations (
                        reservation_id TEXT PRIMARY KEY,
                        book_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        reservation_date TEXT NOT NULL,
                        available_date TEXT,
                        expire_date TEXT,
                        status TEXT DEFAULT 'pending',
                        picked_up INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reader_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE NOT NULL,
                        reader_name TEXT,
                        level INTEGER DEFAULT 1,
                        credit_score INTEGER DEFAULT 100,
                        total_borrowed INTEGER DEFAULT 0,
                        total_returned INTEGER DEFAULT 0,
                        total_overdue INTEGER DEFAULT 0,
                        total_lost INTEGER DEFAULT 0,
                        current_borrowed INTEGER DEFAULT 0,
                        current_reserved INTEGER DEFAULT 0,
                        joined_date TEXT,
                        last_visit TEXT,
                        favorite_categories TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS book_reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        book_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        rating INTEGER NOT NULL,
                        review TEXT,
                        is_visible INTEGER DEFAULT 1,
                        likes INTEGER DEFAULT 0,
                        created_at TEXT,
                        UNIQUE(book_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS book_recommendations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        book_id TEXT NOT NULL,
                        reason TEXT,
                        score REAL DEFAULT 0,
                        source TEXT,
                        is_shown INTEGER DEFAULT 0,
                        created_at TEXT,
                        UNIQUE(user_id, book_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS book_purchase_requests (
                        request_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        book_title TEXT NOT NULL,
                        author TEXT,
                        isbn TEXT,
                        publisher TEXT,
                        reason TEXT,
                        status TEXT DEFAULT 'pending',
                        reviewer_id INTEGER,
                        review_comment TEXT,
                        reviewed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reading_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stat_date TEXT NOT NULL,
                        education_type TEXT,
                        total_borrow_count INTEGER DEFAULT 0,
                        total_return_count INTEGER DEFAULT 0,
                        total_reserve_count INTEGER DEFAULT 0,
                        most_borrowed_category TEXT,
                        most_popular_book TEXT,
                        active_readers INTEGER DEFAULT 0,
                        updated_at TEXT,
                        UNIQUE(stat_date, education_type)
                    )
                ''')
                conn.commit()
                logger.info('图书馆服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def add_book(self, title: str, author: str, category: str, **kwargs) -> Dict[str, Any]:
        try:
            book_id = f"bk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            cat_config = BOOK_CATEGORIES.get(category, {})
            tags = json.dumps(kwargs.get('tags'), ensure_ascii=False) if kwargs.get('tags') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO books (
                            book_id, isbn, title, subtitle, author, publisher, publish_date,
                            category, book_type, education_type, grade_level, total_pages,
                            total_copies, available_copies, shelf_location, price,
                            language, summary, tags, cover_url, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?)
                    ''', (book_id, kwargs.get('isbn'), title, kwargs.get('subtitle'),
                          author, kwargs.get('publisher'), kwargs.get('publish_date'),
                          category, kwargs.get('book_type'), kwargs.get('education_type'),
                          kwargs.get('grade_level'), kwargs.get('total_pages'),
                          kwargs.get('total_copies', 1), kwargs.get('total_copies', 1),
                          kwargs.get('shelf_location', cat_config.get('shelf', '')),
                          kwargs.get('price', 0), kwargs.get('language', '中文'),
                          kwargs.get('summary'), tags, kwargs.get('cover_url'), now, now))
                    conn.commit()
                    logger.info(f'添加图书: {title} ({book_id})')
                    return {'success': True, 'book_id': book_id}
        except Exception as e:
            logger.error(f'添加图书失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM books WHERE book_id = ?', (book_id,))
                row = cursor.fetchone()
                if row:
                    book = dict(row)
                    if book.get('tags'):
                        book['tags'] = json.loads(book['tags'])
                    return book
                return None
        except Exception as e:
            logger.error(f'获取图书失败: {e}')
            return None

    def search_books(self, keyword: str = None, category: str = None,
                      education_type: str = None, author: str = None,
                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM books WHERE 1=1'
                params = []
                if keyword:
                    query += ' AND (title LIKE ? OR author LIKE ? OR isbn LIKE ? OR summary LIKE ?)'
                    kw = f'%{keyword}%'
                    params.extend([kw, kw, kw, kw])
                if category:
                    query += ' AND category = ?'
                    params.append(category)
                if education_type:
                    query += ' AND (education_type = ? OR education_type IS NULL)'
                    params.append(education_type)
                if author:
                    query += ' AND author LIKE ?'
                    params.append(f'%{author}%')
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY times_borrowed DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                books = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'books': books, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索图书失败: {e}')
            return {'success': False, 'error': str(e)}

    def borrow_book(self, book_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            borrow_id = f"bw_{uuid.uuid4().hex[:12]}"
            now = datetime.now()
            borrow_date = now.isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT available_copies, category, title FROM books WHERE book_id = ?', (book_id,))
                    book = cursor.fetchone()
                    if not book:
                        return {'success': False, 'error': '图书不存在'}
                    if book[0] <= 0:
                        return {'success': False, 'error': '该图书已全部借出'}
                    cursor.execute('SELECT level, current_borrowed FROM reader_profiles WHERE user_id = ?', (user_id,))
                    reader = cursor.fetchone()
                    if not reader:
                        self._init_reader(cursor, user_id, kwargs.get('user_name'))
                        reader = (1, 0)
                    level_config = READER_LEVELS.get(reader[0], READER_LEVELS[1])
                    if reader[1] >= level_config['max_borrow']:
                        return {'success': False, 'error': f'已达最大借阅数量{level_config["max_borrow"]}本'}
                    cat_config = BOOK_CATEGORIES.get(book[1], {})
                    loan_days = cat_config.get('loan_days', 30)
                    due_date = (now + timedelta(days=loan_days)).isoformat()
                    cursor.execute('''
                        INSERT INTO borrow_records (
                            borrow_id, book_id, user_id, user_name, borrow_date,
                            due_date, status, renewed_times, operator_borrow, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'borrowed', 0, ?, ?)
                    ''', (borrow_id, book_id, user_id, kwargs.get('user_name'),
                          borrow_date, due_date, kwargs.get('operator_name'), borrow_date))
                    cursor.execute('''
                        UPDATE books SET available_copies = available_copies - 1,
                            current_borrowed = current_borrowed + 1,
                            times_borrowed = times_borrowed + 1,
                            updated_at = ?
                        WHERE book_id = ? AND available_copies > 0
                    ''', (now.isoformat(), book_id))
                    cursor.execute('''
                        INSERT INTO reader_profiles (user_id, reader_name, current_borrowed, total_borrowed, created_at, updated_at)
                        VALUES (?, ?, 1, 1, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            current_borrowed = current_borrowed + 1,
                            total_borrowed = total_borrowed + 1,
                            last_visit = ?,
                            updated_at = ?
                    ''', (user_id, kwargs.get('user_name', ''), borrow_date, borrow_date, borrow_date, borrow_date))
                    conn.commit()
                    logger.info(f'借阅图书: {book[2]} ({book_id}) -> 用户{user_id}')
                    return {'success': True, 'borrow_id': borrow_id, 'due_date': due_date}
        except Exception as e:
            logger.error(f'借阅图书失败: {e}')
            return {'success': False, 'error': str(e)}

    def _init_reader(self, cursor, user_id: int, user_name: str = None):
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO reader_profiles (user_id, reader_name, level, credit_score, current_borrowed, total_borrowed, joined_date, last_visit, created_at, updated_at)
            VALUES (?, ?, 1, 100, 0, 0, ?, ?, ?, ?)
        ''', (user_id, user_name or '', now, now, now, now))

    def return_book(self, borrow_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT book_id, user_id, due_date, borrow_date FROM borrow_records WHERE borrow_id = ? AND status IN (?, ?, ?)',
                                 (borrow_id, 'borrowed', 'renewed', 'overdue'))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '借阅记录不存在或已归还'}
                    book_id, user_id, due_date_str, borrow_date_str = record
                    try:
                        due_date = datetime.fromisoformat(due_date_str)
                        borrow_date = datetime.fromisoformat(borrow_date_str)
                    except:
                        due_date = now
                        borrow_date = now
                    actual_days = (now - borrow_date).days
                    overdue_days = max(0, (now - due_date).days - OVERDUE_FINE_RULE.get('grace_days', 0))
                    fine_amount = min(overdue_days * OVERDUE_FINE_RULE['per_day'], OVERDUE_FINE_RULE['max_amount']) if overdue_days > 0 else 0
                    status = 'overdue' if overdue_days > 0 else 'returned'
                    cursor.execute('''
                        UPDATE borrow_records SET
                            return_date = ?, actual_days = ?, overdue_days = ?,
                            fine_amount = ?, status = ?, operator_return = ?
                        WHERE borrow_id = ?
                    ''', (now.isoformat(), actual_days, overdue_days, fine_amount,
                          status, kwargs.get('operator_name'), borrow_id))
                    cursor.execute('''
                        UPDATE books SET available_copies = available_copies + 1,
                            current_borrowed = MAX(current_borrowed - 1, 0),
                            updated_at = ?
                        WHERE book_id = ?
                    ''', (now.isoformat(), book_id))
                    cursor.execute('''
                        UPDATE reader_profiles SET
                            current_borrowed = MAX(current_borrowed - 1, 0),
                            total_returned = total_returned + 1,
                            total_overdue = total_overdue + ?,
                            last_visit = ?,
                            updated_at = ?
                        WHERE user_id = ?
                    ''', (1 if overdue_days > 0 else 0, now.isoformat(), now.isoformat(), user_id))
                    if overdue_days > 0:
                        cursor.execute('''
                            UPDATE reader_profiles SET credit_score = MAX(credit_score - ?, 0) WHERE user_id = ?
                        ''', (min(overdue_days, 10), user_id))
                    self._check_reservations(cursor, book_id)
                    conn.commit()
                    logger.info(f'归还图书: {borrow_id}, 逾期{overdue_days}天, 罚款{fine_amount}元')
                    return {'success': True, 'actual_days': actual_days, 'overdue_days': overdue_days, 'fine_amount': fine_amount}
        except Exception as e:
            logger.error(f'归还图书失败: {e}')
            return {'success': False, 'error': str(e)}

    def _check_reservations(self, cursor, book_id: str):
        cursor.execute('''
            SELECT reservation_id, user_id FROM book_reservations
            WHERE book_id = ? AND status = 'pending'
            ORDER BY reservation_date LIMIT 1
        ''', (book_id,))
        reservation = cursor.fetchone()
        if reservation:
            now = datetime.now()
            expire_date = (now + timedelta(days=3)).isoformat()
            cursor.execute('''
                UPDATE book_reservations SET status = 'available', available_date = ?, expire_date = ?
                WHERE reservation_id = ?
            ''', (now.isoformat(), expire_date, reservation[0]))

    def renew_book(self, borrow_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT book_id, user_id, due_date, renewed_times, status FROM borrow_records WHERE borrow_id = ?', (borrow_id,))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '借阅记录不存在'}
                    book_id, user_id, due_date_str, renewed_times, status = record
                    if status not in ('borrowed', 'renewed'):
                        return {'success': False, 'error': f'当前状态不允许续借: {status}'}
                    cursor.execute('SELECT level FROM reader_profiles WHERE user_id = ?', (user_id,))
                    reader = cursor.fetchone()
                    level = reader[0] if reader else 1
                    max_renew = READER_LEVELS.get(level, READER_LEVELS[1])['renew_times']
                    if renewed_times >= max_renew:
                        return {'success': False, 'error': f'已达最大续借次数{max_renew}次'}
                    cursor.execute('SELECT category FROM books WHERE book_id = ?', (book_id,))
                    book = cursor.fetchone()
                    cat_config = BOOK_CATEGORIES.get(book[0], {})
                    loan_days = cat_config.get('loan_days', 30)
                    new_due_date = (now + timedelta(days=loan_days)).isoformat()
                    cursor.execute('''
                        UPDATE borrow_records SET due_date = ?, renewed_times = renewed_times + 1, status = 'renewed'
                        WHERE borrow_id = ?
                    ''', (new_due_date, borrow_id))
                    conn.commit()
                    return {'success': True, 'new_due_date': new_due_date, 'remaining_renews': max_renew - renewed_times - 1}
        except Exception as e:
            logger.error(f'续借图书失败: {e}')
            return {'success': False, 'error': str(e)}

    def reserve_book(self, book_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            reservation_id = f"rsv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT available_copies, title FROM books WHERE book_id = ?', (book_id,))
                    book = cursor.fetchone()
                    if not book:
                        return {'success': False, 'error': '图书不存在'}
                    if book[0] > 0:
                        return {'success': False, 'error': '该书目前有库存，可直接借阅'}
                    cursor.execute('SELECT current_reserved, level FROM reader_profiles WHERE user_id = ?', (user_id,))
                    reader = cursor.fetchone()
                    if not reader:
                        self._init_reader(cursor, user_id, kwargs.get('user_name'))
                        current_reserved = 0
                        level = 1
                    else:
                        current_reserved, level = reader
                    max_reserve = READER_LEVELS.get(level, READER_LEVELS[1])['reserve_max']
                    if current_reserved >= max_reserve:
                        return {'success': False, 'error': f'已达最大预约数量{max_reserve}本'}
                    expire_date = (datetime.now() + timedelta(days=30)).isoformat()
                    cursor.execute('''
                        INSERT INTO book_reservations (
                            reservation_id, book_id, user_id, user_name,
                            reservation_date, expire_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (reservation_id, book_id, user_id, kwargs.get('user_name'),
                          now, expire_date, now))
                    cursor.execute('''
                        UPDATE books SET times_reserved = times_reserved + 1, updated_at = ? WHERE book_id = ?
                    ''', (now, book_id))
                    cursor.execute('''
                        UPDATE reader_profiles SET current_reserved = current_reserved + 1, updated_at = ? WHERE user_id = ?
                    ''', (now, user_id))
                    conn.commit()
                    logger.info(f'预约图书: {book[1]} ({book_id}) -> 用户{user_id}')
                    return {'success': True, 'reservation_id': reservation_id}
        except Exception as e:
            logger.error(f'预约图书失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_borrow_records(self, user_id: int = None, status: str = None,
                            book_id: str = None, page: int = 1,
                            page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT br.*, b.title, b.author, b.cover_url
                    FROM borrow_records br
                    JOIN books b ON br.book_id = b.book_id
                    WHERE 1=1
                '''
                params = []
                if user_id:
                    query += ' AND br.user_id = ?'
                    params.append(user_id)
                if status:
                    query += ' AND br.status = ?'
                    params.append(status)
                if book_id:
                    query += ' AND br.book_id = ?'
                    params.append(book_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY br.borrow_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取借阅记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_reader_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM reader_profiles WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    profile = dict(row)
                    if profile.get('favorite_categories'):
                        profile['favorite_categories'] = json.loads(profile['favorite_categories'])
                    return profile
                return None
        except Exception as e:
            logger.error(f'获取读者档案失败: {e}')
            return None

    def review_book(self, book_id: str, user_id: int, rating: int, review: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO book_reviews (book_id, user_id, rating, review, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(book_id, user_id) DO UPDATE SET
                            rating = excluded.rating,
                            review = excluded.review
                    ''', (book_id, user_id, rating, review, now))
                    cursor.execute('''
                        UPDATE books SET rating = (
                            SELECT AVG(rating) FROM book_reviews WHERE book_id = ? AND is_visible = 1
                        ), rating_count = (
                            SELECT COUNT(*) FROM book_reviews WHERE book_id = ? AND is_visible = 1
                        ), updated_at = ? WHERE book_id = ?
                    ''', (book_id, book_id, now, book_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'评价图书失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_popular_books(self, education_type: str = None, limit: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM books WHERE status = ?'
                params = ['available']
                if education_type:
                    query += ' AND (education_type = ? OR education_type IS NULL)'
                    params.append(education_type)
                query += ' ORDER BY times_borrowed DESC, rating DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                books = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'books': books}
        except Exception as e:
            logger.error(f'获取热门图书失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_new_books(self, education_type: str = None, days: int = 30, limit: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                query = 'SELECT * FROM books WHERE created_at >= ?'
                params = [start_date]
                if education_type:
                    query += ' AND (education_type = ? OR education_type IS NULL)'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                books = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'books': books}
        except Exception as e:
            logger.error(f'获取新书失败: {e}')
            return {'success': False, 'error': str(e)}

    def request_purchase(self, user_id: int, book_title: str, **kwargs) -> Dict[str, Any]:
        try:
            request_id = f"pur_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO book_purchase_requests (
                            request_id, user_id, book_title, author, isbn,
                            publisher, reason, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (request_id, user_id, book_title, kwargs.get('author'),
                          kwargs.get('isbn'), kwargs.get('publisher'),
                          kwargs.get('reason'), now))
                    conn.commit()
                    logger.info(f'荐购申请: {request_id}')
                    return {'success': True, 'request_id': request_id}
        except Exception as e:
            logger.error(f'荐购申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_reading_statistics(self, user_id: int = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute('SELECT * FROM reader_profiles WHERE user_id = ?', (user_id,))
                    profile = cursor.fetchone()
                    cursor.execute('SELECT COUNT(*) FROM borrow_records WHERE user_id = ? AND status = ?', (user_id, 'borrowed'))
                    current = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(DISTINCT category) FROM borrow_records br JOIN books b ON br.book_id = b.book_id WHERE br.user_id = ?', (user_id,))
                    cat_count = cursor.fetchone()[0]
                    cursor.execute('SELECT SUM(CASE WHEN status = "returned" THEN actual_days ELSE 0 END) FROM borrow_records WHERE user_id = ?', (user_id,))
                    total_days = cursor.fetchone()[0] or 0
                    return {
                        'success': True,
                        'profile': {
                            'level': profile[2] if profile else 1,
                            'credit_score': profile[3] if profile else 100,
                            'total_borrowed': profile[4] if profile else 0,
                            'current_borrowed': current,
                            'category_count': cat_count,
                            'total_reading_days': total_days
                        }
                    }
                else:
                    cursor.execute('SELECT COUNT(*) FROM books')
                    total_books = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM borrow_records')
                    total_readers = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM borrow_records')
                    total_borrows = cursor.fetchone()[0]
                    return {
                        'success': True,
                        'stats': {
                            'total_books': total_books,
                            'total_readers': total_readers,
                            'total_borrows': total_borrows
                        }
                    }
        except Exception as e:
            logger.error(f'获取阅读统计失败: {e}')
            return {'success': False, 'error': str(e)}
