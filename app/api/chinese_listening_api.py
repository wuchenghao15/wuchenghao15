#!/usr/bin/env python3
"""
语文听力API - 提供语文听写题目生成、词库管理、题目查询等功能
"""

import os
import json
import uuid
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin, allow_guest_access

chinese_listening_api = Blueprint('chinese_listening_api', __name__)


def _get_db_path():
    """获取题库数据库路径"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'split_databases', 'question.db')


def _execute_sql(sql, params=None):
    """执行SQL语句"""
    import sqlite3
    try:
        conn = sqlite3.connect(_get_db_path())
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"SQL执行失败: {e}")
        return False


def _fetch_all(sql, params=None):
    """执行查询并返回所有结果"""
    import sqlite3
    try:
        conn = sqlite3.connect(_get_db_path())
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"SQL查询失败: {e}")
        return []


def _fetch_one(sql, params=None):
    """执行查询并返回单条结果"""
    import sqlite3
    try:
        conn = sqlite3.connect(_get_db_path())
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchone()
        conn.close()
        return dict(zip(columns, result)) if result else None
    except Exception as e:
        print(f"SQL查询失败: {e}")
        return None


@chinese_listening_api.route('/api/chinese_dictation/words', methods=['GET'])
@allow_guest_access
def get_words():
    """获取词语词库列表"""
    difficulty = request.args.get('difficulty')
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    offset = (page - 1) * page_size
    
    sql = "SELECT * FROM chinese_dictation_words WHERE is_active = 1"
    params = []
    
    if difficulty:
        sql += " AND difficulty_level = ?"
        params.append(difficulty)
    if keyword:
        sql += " AND (word LIKE ? OR pinyin LIKE ? OR meaning LIKE ?)"
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])
    
    words = _fetch_all(sql, params)
    
    count_sql = "SELECT COUNT(*) as total FROM chinese_dictation_words WHERE is_active = 1"
    if difficulty:
        count_sql += " AND difficulty_level = ?"
    if keyword:
        count_sql += " AND (word LIKE ? OR pinyin LIKE ? OR meaning LIKE ?)"
    total = _fetch_one(count_sql, params[:-2])['total'] if params else _fetch_one(count_sql)['total']
    
    return jsonify({
        'success': True,
        'data': words,
        'total': total,
        'page': page,
        'page_size': page_size,
        'difficulty': difficulty
    })


@chinese_listening_api.route('/api/chinese_dictation/words/<int:word_id>', methods=['GET'])
@allow_guest_access
def get_word_detail(word_id):
    """获取单个词语详情"""
    word = _fetch_one("SELECT * FROM chinese_dictation_words WHERE id = ?", (word_id,))
    if not word:
        return jsonify({'success': False, 'error': '词语不存在'}), 404
    return jsonify({'success': True, 'data': word})


@chinese_listening_api.route('/api/chinese_dictation/words', methods=['POST'])
@require_admin
def add_word():
    """添加新词语"""
    data = request.get_json() or {}
    
    word = data.get('word')
    pinyin = data.get('pinyin')
    meaning = data.get('meaning')
    difficulty = data.get('difficulty', '小学低年级')
    
    if not word:
        return jsonify({'success': False, 'error': '词语不能为空'}), 400
    
    _execute_sql('''
        INSERT INTO chinese_dictation_words (word, pinyin, meaning, difficulty_level)
        VALUES (?, ?, ?, ?)
    ''', (word, pinyin, meaning, difficulty))
    
    return jsonify({'success': True, 'message': '词语添加成功'}), 201


@chinese_listening_api.route('/api/chinese_dictation/words/<int:word_id>', methods=['PUT'])
@require_admin
def update_word(word_id):
    """更新词语"""
    data = request.get_json() or {}
    
    word = data.get('word')
    pinyin = data.get('pinyin')
    meaning = data.get('meaning')
    difficulty = data.get('difficulty')
    
    updates = []
    params = []
    
    if word is not None:
        updates.append('word = ?')
        params.append(word)
    if pinyin is not None:
        updates.append('pinyin = ?')
        params.append(pinyin)
    if meaning is not None:
        updates.append('meaning = ?')
        params.append(meaning)
    if difficulty is not None:
        updates.append('difficulty_level = ?')
        params.append(difficulty)
    
    if not updates:
        return jsonify({'success': False, 'error': '没有需要更新的字段'}), 400
    
    params.append(word_id)
    sql = f"UPDATE chinese_dictation_words SET {', '.join(updates)} WHERE id = ?"
    _execute_sql(sql, params)
    
    return jsonify({'success': True, 'message': '词语更新成功'})


@chinese_listening_api.route('/api/chinese_dictation/words/<int:word_id>', methods=['DELETE'])
@require_admin
def delete_word(word_id):
    """删除词语"""
    _execute_sql("UPDATE chinese_dictation_words SET is_active = 0 WHERE id = ?", (word_id,))
    return jsonify({'success': True, 'message': '词语已禁用'})


@chinese_listening_api.route('/api/chinese_dictation/idioms', methods=['GET'])
@allow_guest_access
def get_idioms():
    """获取成语词库列表"""
    difficulty = request.args.get('difficulty')
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    offset = (page - 1) * page_size
    
    sql = "SELECT * FROM chinese_dictation_idioms WHERE is_active = 1"
    params = []
    
    if difficulty:
        sql += " AND difficulty_level = ?"
        params.append(difficulty)
    if keyword:
        sql += " AND (idiom LIKE ? OR pinyin LIKE ? OR meaning LIKE ?)"
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])
    
    idioms = _fetch_all(sql, params)
    
    count_sql = "SELECT COUNT(*) as total FROM chinese_dictation_idioms WHERE is_active = 1"
    if difficulty:
        count_sql += " AND difficulty_level = ?"
    if keyword:
        count_sql += " AND (idiom LIKE ? OR pinyin LIKE ? OR meaning LIKE ?)"
    total = _fetch_one(count_sql, params[:-2])['total'] if params else _fetch_one(count_sql)['total']
    
    return jsonify({
        'success': True,
        'data': idioms,
        'total': total,
        'page': page,
        'page_size': page_size,
        'difficulty': difficulty
    })


@chinese_listening_api.route('/api/chinese_dictation/idioms/<int:idiom_id>', methods=['GET'])
@allow_guest_access
def get_idiom_detail(idiom_id):
    """获取单个成语详情"""
    idiom = _fetch_one("SELECT * FROM chinese_dictation_idioms WHERE id = ?", (idiom_id,))
    if not idiom:
        return jsonify({'success': False, 'error': '成语不存在'}), 404
    return jsonify({'success': True, 'data': idiom})


@chinese_listening_api.route('/api/chinese_dictation/idioms', methods=['POST'])
@require_admin
def add_idiom():
    """添加新成语"""
    data = request.get_json() or {}
    
    idiom = data.get('idiom')
    pinyin = data.get('pinyin')
    meaning = data.get('meaning')
    difficulty = data.get('difficulty', '小学低年级')
    
    if not idiom:
        return jsonify({'success': False, 'error': '成语不能为空'}), 400
    
    _execute_sql('''
        INSERT INTO chinese_dictation_idioms (idiom, pinyin, meaning, difficulty_level)
        VALUES (?, ?, ?, ?)
    ''', (idiom, pinyin, meaning, difficulty))
    
    return jsonify({'success': True, 'message': '成语添加成功'}), 201


@chinese_listening_api.route('/api/chinese_dictation/poetry', methods=['GET'])
@allow_guest_access
def get_poetry():
    """获取古诗词列表"""
    difficulty = request.args.get('difficulty')
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    offset = (page - 1) * page_size
    
    sql = "SELECT * FROM chinese_dictation_poetry WHERE is_active = 1"
    params = []
    
    if difficulty:
        sql += " AND difficulty_level = ?"
        params.append(difficulty)
    if keyword:
        sql += " AND (title LIKE ? OR author LIKE ? OR content LIKE ?)"
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])
    
    poetry = _fetch_all(sql, params)
    
    count_sql = "SELECT COUNT(*) as total FROM chinese_dictation_poetry WHERE is_active = 1"
    if difficulty:
        count_sql += " AND difficulty_level = ?"
    if keyword:
        count_sql += " AND (title LIKE ? OR author LIKE ? OR content LIKE ?)"
    total = _fetch_one(count_sql, params[:-2])['total'] if params else _fetch_one(count_sql)['total']
    
    return jsonify({
        'success': True,
        'data': poetry,
        'total': total,
        'page': page,
        'page_size': page_size,
        'difficulty': difficulty
    })


@chinese_listening_api.route('/api/chinese_dictation/poetry/<int:poetry_id>', methods=['GET'])
@allow_guest_access
def get_poetry_detail(poetry_id):
    """获取单首古诗词详情"""
    poetry = _fetch_one("SELECT * FROM chinese_dictation_poetry WHERE id = ?", (poetry_id,))
    if not poetry:
        return jsonify({'success': False, 'error': '古诗词不存在'}), 404
    return jsonify({'success': True, 'data': poetry})


@chinese_listening_api.route('/api/chinese_dictation/poetry', methods=['POST'])
@require_admin
def add_poetry():
    """添加新古诗词"""
    data = request.get_json() or {}
    
    title = data.get('title')
    author = data.get('author')
    dynasty = data.get('dynasty')
    content = data.get('content')
    difficulty = data.get('difficulty', '小学低年级')
    
    if not title or not content:
        return jsonify({'success': False, 'error': '标题和内容不能为空'}), 400
    
    _execute_sql('''
        INSERT INTO chinese_dictation_poetry (title, author, dynasty, content, difficulty_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, author, dynasty, content, difficulty))
    
    return jsonify({'success': True, 'message': '古诗词添加成功'}), 201


@chinese_listening_api.route('/api/chinese_dictation/passages', methods=['GET'])
@allow_guest_access
def get_passages():
    """获取读文选段列表"""
    difficulty = request.args.get('difficulty')
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    offset = (page - 1) * page_size
    
    sql = "SELECT * FROM chinese_dictation_passages WHERE is_active = 1"
    params = []
    
    if difficulty:
        sql += " AND difficulty_level = ?"
        params.append(difficulty)
    if keyword:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])
    
    passages = _fetch_all(sql, params)
    
    count_sql = "SELECT COUNT(*) as total FROM chinese_dictation_passages WHERE is_active = 1"
    if difficulty:
        count_sql += " AND difficulty_level = ?"
    if keyword:
        count_sql += " AND (title LIKE ? OR content LIKE ?)"
    total = _fetch_one(count_sql, params[:-2])['total'] if params else _fetch_one(count_sql)['total']
    
    return jsonify({
        'success': True,
        'data': passages,
        'total': total,
        'page': page,
        'page_size': page_size,
        'difficulty': difficulty
    })


@chinese_listening_api.route('/api/chinese_dictation/passages/<int:passage_id>', methods=['GET'])
@allow_guest_access
def get_passage_detail(passage_id):
    """获取单篇读文选段详情"""
    passage = _fetch_one("SELECT * FROM chinese_dictation_passages WHERE id = ?", (passage_id,))
    if not passage:
        return jsonify({'success': False, 'error': '读文选段不存在'}), 404
    return jsonify({'success': True, 'data': passage})


@chinese_listening_api.route('/api/chinese_dictation/passages', methods=['POST'])
@require_admin
def add_passage():
    """添加新读文选段"""
    data = request.get_json() or {}
    
    title = data.get('title')
    content = data.get('content')
    keywords = data.get('keywords')
    difficulty = data.get('difficulty', '小学低年级')
    
    if not title or not content:
        return jsonify({'success': False, 'error': '标题和内容不能为空'}), 400
    
    word_count = len(content.replace(' ', '').replace('，', '').replace('。', '').replace('！', '').replace('？', ''))
    
    _execute_sql('''
        INSERT INTO chinese_dictation_passages (title, content, keywords, difficulty_level, word_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, content, keywords, difficulty, word_count))
    
    return jsonify({'success': True, 'message': '读文选段添加成功'}), 201


@chinese_listening_api.route('/api/chinese_listening/generate', methods=['POST'])
@require_login
def generate_listening_questions():
    """生成语文听力题目"""
    data = request.get_json() or {}
    
    dictation_type = data.get('dictation_type', 'word')
    count = int(data.get('count', 10))
    difficulty = data.get('difficulty', '小学低年级')
    
    results = []
    
    if dictation_type == 'word':
        words = _fetch_all("SELECT * FROM chinese_dictation_words WHERE is_active = 1 AND difficulty_level = ? LIMIT ?", (difficulty, count))
        for word in words:
            question = {
                'question_id': f'cq_{uuid.uuid4().hex[:8]}',
                'type': 'dictation',
                'category': 'chinese_dictation',
                'sub_category': 'word',
                'difficulty': difficulty,
                'content': f'请听词语并写出：{word["pinyin"]}',
                'correct_answer': word['word'],
                'explanation': f'词语：{word["word"]}\n拼音：{word["pinyin"]}\n释义：{word["meaning"]}',
                'analysis': f'考察词语听写能力，难度：{difficulty}',
                'tags': ['语文', '听写', '词语', difficulty],
                'knowledge_points': ['词语听写', difficulty],
                'score': 2.0 if difficulty == '小学低年级' else (3.0 if difficulty == '小学高年级' else (5.0 if difficulty == '初中' else 8.0)),
                'language': 'chinese',
                'accent': 'mandarin',
                'voice': 'female',
                'dictation_text': word['word'],
                'pinyin': word['pinyin'],
                'meaning': word['meaning'],
                'level': difficulty
            }
            results.append(question)
    
    elif dictation_type == 'idiom':
        idioms = _fetch_all("SELECT * FROM chinese_dictation_idioms WHERE is_active = 1 AND difficulty_level = ? LIMIT ?", (difficulty, count))
        for idiom in idioms:
            question = {
                'question_id': f'cq_{uuid.uuid4().hex[:8]}',
                'type': 'dictation',
                'category': 'chinese_dictation',
                'sub_category': 'idiom',
                'difficulty': difficulty,
                'content': f'请听成语并写出：{idiom["pinyin"]}',
                'correct_answer': idiom['idiom'],
                'explanation': f'成语：{idiom["idiom"]}\n拼音：{idiom["pinyin"]}\n释义：{idiom["meaning"]}',
                'analysis': f'考察成语听写能力，难度：{difficulty}',
                'tags': ['语文', '听写', '成语', difficulty],
                'knowledge_points': ['成语听写', difficulty],
                'score': 3.0 if difficulty == '小学低年级' else (5.0 if difficulty == '小学高年级' else (8.0 if difficulty == '初中' else 10.0)),
                'language': 'chinese',
                'accent': 'mandarin',
                'voice': 'female',
                'dictation_text': idiom['idiom'],
                'pinyin': idiom['pinyin'],
                'meaning': idiom['meaning'],
                'level': difficulty
            }
            results.append(question)
    
    elif dictation_type == 'poetry':
        poetry = _fetch_all("SELECT * FROM chinese_dictation_poetry WHERE is_active = 1 AND difficulty_level = ? LIMIT ?", (difficulty, count))
        for poem in poetry:
            lines = poem['content'].split('。')
            lines = [line.strip() for line in lines if line.strip()]
            dictation_text = '。'.join(lines[:2]) + '。' if len(lines) >= 2 else poem['content']
            
            question = {
                'question_id': f'cq_{uuid.uuid4().hex[:8]}',
                'type': 'dictation',
                'category': 'chinese_dictation',
                'sub_category': 'poetry',
                'difficulty': difficulty,
                'content': f'请听古诗词并写出：《{poem["title"]}》（{poem["author"]}）',
                'correct_answer': dictation_text,
                'explanation': f'诗名：《{poem["title"]}》\n作者：{poem["dynasty"]}·{poem["author"]}\n原文：{poem["content"]}',
                'analysis': f'考察古诗词听写能力，难度：{difficulty}',
                'tags': ['语文', '听写', '古诗词', difficulty, poem['title']],
                'knowledge_points': ['古诗词听写', poem['title']],
                'score': 5.0 if difficulty == '小学低年级' else (8.0 if difficulty == '小学高年级' else (10.0 if difficulty == '初中' else 15.0)),
                'language': 'chinese',
                'accent': 'mandarin',
                'voice': 'female',
                'dictation_text': dictation_text,
                'title': poem['title'],
                'author': poem['author'],
                'dynasty': poem['dynasty'],
                'full_content': poem['content'],
                'level': difficulty
            }
            results.append(question)
    
    elif dictation_type == 'passage':
        passages = _fetch_all("SELECT * FROM chinese_dictation_passages WHERE is_active = 1 AND difficulty_level = ? LIMIT ?", (difficulty, count))
        for passage in passages:
            question = {
                'question_id': f'cq_{uuid.uuid4().hex[:8]}',
                'type': 'dictation',
                'category': 'chinese_dictation',
                'sub_category': 'passage',
                'difficulty': difficulty,
                'content': f'请听文章选段并写出：《{passage["title"]}》',
                'correct_answer': passage['content'],
                'explanation': f'文章标题：《{passage["title"]}》\n内容：{passage["content"]}',
                'analysis': f'考察文章听写能力，难度：{difficulty}\n关键词：{passage.get("keywords", "")}',
                'tags': ['语文', '听写', '读文选段', difficulty, passage['title']],
                'knowledge_points': ['读文选段听写', passage['title']],
                'score': 10.0 if difficulty == '小学低年级' else (15.0 if difficulty == '小学高年级' else (20.0 if difficulty == '初中' else 25.0)),
                'language': 'chinese',
                'accent': 'mandarin',
                'voice': 'female',
                'dictation_text': passage['content'],
                'title': passage['title'],
                'keywords': passage.get('keywords', ''),
                'level': difficulty
            }
            results.append(question)
    
    else:
        return jsonify({'success': False, 'error': '不支持的听写类型'}), 400
    
    return jsonify({
        'success': True,
        'message': f'成功生成 {len(results)} 道语文听力题',
        'generated_count': len(results),
        'dictation_type': dictation_type,
        'difficulty': difficulty,
        'questions': results
    })


@chinese_listening_api.route('/api/chinese_listening/questions', methods=['GET'])
@require_login
def get_listening_questions():
    """获取已保存的语文听力题目"""
    sub_category = request.args.get('sub_category')
    difficulty = request.args.get('difficulty')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    offset = (page - 1) * page_size
    
    sql = "SELECT * FROM chinese_listening_questions WHERE is_active = 1"
    params = []
    
    if sub_category:
        sql += " AND sub_category = ?"
        params.append(sub_category)
    if difficulty:
        sql += " AND difficulty = ?"
        params.append(difficulty)
    
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])
    
    questions = _fetch_all(sql, params)
    
    count_sql = "SELECT COUNT(*) as total FROM chinese_listening_questions WHERE is_active = 1"
    if sub_category:
        count_sql += " AND sub_category = ?"
    if difficulty:
        count_sql += " AND difficulty = ?"
    total = _fetch_one(count_sql, params[:-2])['total'] if params else _fetch_one(count_sql)['total']
    
    return jsonify({
        'success': True,
        'data': questions,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@chinese_listening_api.route('/api/chinese_listening/questions/<question_id>', methods=['GET'])
@require_login
def get_listening_question_detail(question_id):
    """获取单个语文听力题目详情"""
    question = _fetch_one("SELECT * FROM chinese_listening_questions WHERE question_id = ?", (question_id,))
    if not question:
        return jsonify({'success': False, 'error': '题目不存在'}), 404
    return jsonify({'success': True, 'data': question})


@chinese_listening_api.route('/api/chinese_listening/questions', methods=['POST'])
@require_admin
def save_listening_question():
    """保存语文听力题目"""
    data = request.get_json() or {}
    
    question_id = data.get('question_id', f'cq_{uuid.uuid4().hex[:8]}')
    question = data.get('question')
    
    if not question:
        return jsonify({'success': False, 'error': '题目数据不能为空'}), 400
    
    _execute_sql('''
        INSERT OR REPLACE INTO chinese_listening_questions (
            question_id, type, category, sub_category, difficulty, content,
            correct_answer, explanation, analysis, tags, knowledge_points,
            score, language, accent, voice, dictation_text, pinyin, meaning,
            level, title, author, dynasty, full_content, keywords, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        question_id,
        question.get('type', 'dictation'),
        question.get('category', 'chinese_dictation'),
        question.get('sub_category', ''),
        question.get('difficulty', ''),
        question.get('content', ''),
        question.get('correct_answer', ''),
        question.get('explanation', ''),
        question.get('analysis', ''),
        json.dumps(question.get('tags', [])),
        json.dumps(question.get('knowledge_points', [])),
        question.get('score', 5.0),
        question.get('language', 'chinese'),
        question.get('accent', 'mandarin'),
        question.get('voice', 'female'),
        question.get('dictation_text', ''),
        question.get('pinyin', ''),
        question.get('meaning', ''),
        question.get('level', ''),
        question.get('title', ''),
        question.get('author', ''),
        question.get('dynasty', ''),
        question.get('full_content', ''),
        json.dumps(question.get('keywords', [])),
        1
    ))
    
    return jsonify({'success': True, 'message': '题目保存成功', 'question_id': question_id}), 201


@chinese_listening_api.route('/api/chinese_listening/questions/<question_id>', methods=['DELETE'])
@require_admin
def delete_listening_question(question_id):
    """删除语文听力题目"""
    _execute_sql("UPDATE chinese_listening_questions SET is_active = 0 WHERE question_id = ?", (question_id,))
    return jsonify({'success': True, 'message': '题目已禁用'})


@chinese_listening_api.route('/api/chinese_listening/stats', methods=['GET'])
@require_admin
def get_listening_stats():
    """获取语文听力统计数据"""
    word_count = _fetch_one("SELECT COUNT(*) as count FROM chinese_dictation_words WHERE is_active = 1")['count']
    idiom_count = _fetch_one("SELECT COUNT(*) as count FROM chinese_dictation_idioms WHERE is_active = 1")['count']
    poetry_count = _fetch_one("SELECT COUNT(*) as count FROM chinese_dictation_poetry WHERE is_active = 1")['count']
    passage_count = _fetch_one("SELECT COUNT(*) as count FROM chinese_dictation_passages WHERE is_active = 1")['count']
    question_count = _fetch_one("SELECT COUNT(*) as count FROM chinese_listening_questions WHERE is_active = 1")['count']
    
    word_by_level = _fetch_all("SELECT difficulty_level, COUNT(*) as count FROM chinese_dictation_words WHERE is_active = 1 GROUP BY difficulty_level")
    idiom_by_level = _fetch_all("SELECT difficulty_level, COUNT(*) as count FROM chinese_dictation_idioms WHERE is_active = 1 GROUP BY difficulty_level")
    poetry_by_level = _fetch_all("SELECT difficulty_level, COUNT(*) as count FROM chinese_dictation_poetry WHERE is_active = 1 GROUP BY difficulty_level")
    passage_by_level = _fetch_all("SELECT difficulty_level, COUNT(*) as count FROM chinese_dictation_passages WHERE is_active = 1 GROUP BY difficulty_level")
    
    return jsonify({
        'success': True,
        'data': {
            'total_words': word_count,
            'total_idioms': idiom_count,
            'total_poetry': poetry_count,
            'total_passages': passage_count,
            'total_questions': question_count,
            'words_by_level': word_by_level,
            'idioms_by_level': idiom_by_level,
            'poetry_by_level': poetry_by_level,
            'passages_by_level': passage_by_level
        }
    })


@chinese_listening_api.route('/api/chinese_listening/difficulty_levels', methods=['GET'])
@allow_guest_access
def get_difficulty_levels():
    """获取难度级别列表"""
    levels = [
        {'id': '小学低年级', 'name': '小学低年级', 'description': '适合小学1-3年级'},
        {'id': '小学高年级', 'name': '小学高年级', 'description': '适合小学4-6年级'},
        {'id': '初中', 'name': '初中', 'description': '适合初中学生'},
        {'id': '高中', 'name': '高中', 'description': '适合高中学生'}
    ]
    return jsonify({'success': True, 'data': levels})


@chinese_listening_api.route('/api/chinese_listening/types', methods=['GET'])
@allow_guest_access
def get_dictation_types():
    """获取听写类型列表"""
    types = [
        {'id': 'word', 'name': '词语听写', 'description': '听词语写出正确的汉字'},
        {'id': 'idiom', 'name': '成语听写', 'description': '听成语写出正确的汉字'},
        {'id': 'poetry', 'name': '古诗词听写', 'description': '听古诗词写出正确的汉字'},
        {'id': 'passage', 'name': '读文选段听写', 'description': '听文章选段写出正确的汉字'}
    ]
    return jsonify({'success': True, 'data': types})