#!/usr/bin/env python3
"""
音频字库API
提供发音素材管理和拟音师AI服务
"""
from flask import Blueprint, jsonify, request
import sqlite3
import os

pronunciation_api = Blueprint('pronunciation_api', __name__)

DB_PATH = 'app.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@pronunciation_api.route('/api/pronunciation/english', methods=['GET'])
def get_english_pronunciation():
    """获取英语发音素材列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        type_ = request.args.get('type')
        accent = request.args.get('accent')
        voice = request.args.get('voice')
        
        query = 'SELECT * FROM english_pronunciation WHERE 1=1'
        params = []
        
        if type_:
            query += ' AND type = ?'
            params.append(type_)
        if accent:
            query += ' AND accent = ?'
            params.append(accent)
        if voice:
            query += ' AND voice = ?'
            params.append(voice)
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pronunciation_api.route('/api/pronunciation/japanese', methods=['GET'])
def get_japanese_pronunciation():
    """获取日语发音素材列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        type_ = request.args.get('type')
        accent = request.args.get('accent')
        voice = request.args.get('voice')
        
        query = 'SELECT * FROM japanese_pronunciation WHERE 1=1'
        params = []
        
        if type_:
            query += ' AND type = ?'
            params.append(type_)
        if accent:
            query += ' AND accent = ?'
            params.append(accent)
        if voice:
            query += ' AND voice = ?'
            params.append(voice)
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pronunciation_api.route('/api/pronunciation/english', methods=['POST'])
def add_english_pronunciation():
    """添加英语发音素材"""
    try:
        data = request.get_json()
        
        required_fields = ['type', 'content', 'accent', 'voice', 'file_path']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要字段: {field}'
                }), 400
        
        from app.ai.sound_engineer_ai import SoundEngineerAI
        ai = SoundEngineerAI()
        ai.add_pronunciation_material(
            language='english',
            type_=data['type'],
            content=data['content'],
            accent=data['accent'],
            voice=data['voice'],
            file_path=data['file_path'],
            phonetic=data.get('phonetic')
        )
        
        return jsonify({
            'success': True,
            'message': '英语发音素材添加成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pronunciation_api.route('/api/pronunciation/japanese', methods=['POST'])
def add_japanese_pronunciation():
    """添加日语发音素材"""
    try:
        data = request.get_json()
        
        required_fields = ['type', 'content', 'accent', 'voice', 'file_path']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要字段: {field}'
                }), 400
        
        from app.ai.sound_engineer_ai import SoundEngineerAI
        ai = SoundEngineerAI()
        ai.add_pronunciation_material(
            language='japanese',
            type_=data['type'],
            content=data['content'],
            accent=data['accent'],
            voice=data['voice'],
            file_path=data['file_path'],
            hiragana=data.get('hiragana'),
            katakana=data.get('katakana'),
            romaji=data.get('romaji')
        )
        
        return jsonify({
            'success': True,
            'message': '日语发音素材添加成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pronunciation_api.route('/api/sound-engineer/enhance', methods=['POST'])
def enhance_pronunciation():
    """拟音师AI润色发音"""
    try:
        data = request.get_json()
        
        if 'text' not in data or 'language' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要字段: text 或 language'
            }), 400
        
        from app.ai.sound_engineer_ai import SoundEngineerAI
        ai = SoundEngineerAI()
        
        result = ai.enhance_pronunciation(
            input_text=data['text'],
            language=data['language'],
            accent=data.get('accent', 'standard'),
            voice=data.get('voice', 'female')
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pronunciation_api.route('/api/sound-engineer/compose', methods=['POST'])
def compose_audio():
    """拟音师AI智能组合音频"""
    try:
        data = request.get_json()
        
        if 'text' not in data or 'language' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要字段: text 或 language'
            }), 400
        
        from app.ai.sound_engineer_ai import SoundEngineerAI
        ai = SoundEngineerAI()
        
        result = ai.compose_audio(
            text=data['text'],
            language=data['language'],
            accent=data.get('accent', 'standard'),
            voice=data.get('voice', 'female'),
            quality=data.get('quality', 'high')
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pronunciation_api.route('/api/sound-engineer/statistics', methods=['GET'])
def get_statistics():
    """获取拟音师AI统计信息"""
    try:
        from app.ai.sound_engineer_ai import SoundEngineerAI
        ai = SoundEngineerAI()
        stats = ai.get_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pronunciation_api.route('/api/composition-rules', methods=['GET'])
def get_composition_rules():
    """获取音频组合规则"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        language = request.args.get('language')
        
        query = 'SELECT * FROM audio_composition_rules WHERE active = 1'
        params = []
        
        if language:
            query += ' AND language = ?'
            params.append(language)
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pronunciation_api.route('/api/composition-rules', methods=['POST'])
def add_composition_rule():
    """添加音频组合规则"""
    try:
        data = request.get_json()
        
        required_fields = ['language', 'rule_name', 'rule_pattern']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要字段: {field}'
                }), 400
        
        from app.ai.sound_engineer_ai import SoundEngineerAI
        ai = SoundEngineerAI()
        ai.add_composition_rule(
            language=data['language'],
            rule_name=data['rule_name'],
            rule_pattern=data['rule_pattern'],
            priority=data.get('priority', 1),
            description=data.get('description', '')
        )
        
        return jsonify({
            'success': True,
            'message': '组合规则添加成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500