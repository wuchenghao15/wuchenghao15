# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
音频管理API
"""
from flask import Blueprint, jsonify, request, session
import sqlite3
import os

audio_api = Blueprint('audio_api', __name__)

DB_PATH = 'app.db'

# 配置
JAPANESE_ACCENTS = {
    'kanto': '关东腔',
    'kansai': '关西腔'
}

ENGLISH_ACCENTS = {
    'uk': '英式发音',
    'us': '美式发音',
    'africa': '非洲英语',
    'india': '印度英语'
}

VOICES = {
    'female': '标准女声',
    'male': '标准男声'
}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@audio_api.route('/api/audio/question/<question_id>', methods=['GET'])
def get_audio_options(question_id):
    """获取题目的所有音频选项"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, language, accent, voice, file_path, transcript, duration
            FROM audio_metadata
            WHERE question_id = ?
            ORDER BY language, accent, voice
        ''', (question_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'language': row['language'],
                'accent': row['accent'],
                'accent_name': JAPANESE_ACCENTS.get(row['accent'], 
                                                  ENGLISH_ACCENTS.get(row['accent'], 
                                                                    row['accent'])),
                'voice': row['voice'],
                'voice_name': VOICES.get(row['voice'], row['voice']),
                'file_path': row['file_path'],
                'transcript': row['transcript'],
                'duration': row['duration']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'question_id': question_id,
            'audio_options': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@audio_api.route('/api/audio/question/<question_id>/default', methods=['GET'])
def get_default_audio(question_id):
    """获取题目的默认音频"""
    try:
        # 先获取题目信息,判断语言
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT tags FROM questions WHERE id = ?', (question_id,))
        row = cursor.fetchone()
        
        language = 'english'
        if row:
            import json
            tags = json.loads(row['tags']) if row['tags'] else []
            if 'japanese' in tags:
                language = 'japanese'
        
        # 获取该语言的默认音频
        default_accent = 'kanto' if language == 'japanese' else 'us'
        default_voice = 'female'
        
        cursor.execute('''
            SELECT id, language, accent, voice, file_path, transcript, duration
            FROM audio_metadata
            WHERE question_id = ? AND accent = ? AND voice = ?
        ''', (question_id, default_accent, default_voice))
        
        audio = cursor.fetchone()
        
        if not audio:
            # 如果没有找到默认,取第一个
            cursor.execute('''
                SELECT id, language, accent, voice, file_path, transcript, duration
                FROM audio_metadata
                WHERE question_id = ?
                LIMIT 1
            ''', (question_id,))
            audio = cursor.fetchone()
        
        conn.close()
        
        if audio:
            return jsonify({
                'success': True,
                'question_id': question_id,
                'audio': {
                    'id': audio['id'],
                    'language': audio['language'],
                    'accent': audio['accent'],
                    'accent_name': JAPANESE_ACCENTS.get(audio['accent'], 
                                                      ENGLISH_ACCENTS.get(audio['accent'], 
                                                                        audio['accent'])),
                    'voice': audio['voice'],
                    'voice_name': VOICES.get(audio['voice'], audio['voice']),
                    'file_path': audio['file_path'],
                    'transcript': audio['transcript'],
                    'duration': audio['duration']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No audio found for this question'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@audio_api.route('/api/audio/preferences', methods=['GET'])
def get_audio_preferences():
    """获取用户的音频偏好"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not logged in'
        }), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT language, accent, voice
            FROM user_audio_preferences
            WHERE user_id = ?
        ''', (user_id,))
        
        preferences = {}
        for row in cursor.fetchall():
            preferences[row['language']] = {
                'accent': row['accent'],
                'voice': row['voice']
            }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'preferences': preferences
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@audio_api.route('/api/audio/preferences', methods=['POST'])
def set_audio_preferences():
    """设置用户的音频偏好"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not logged in'
        }), 401
    
    try:
        data = request.get_json()
        language = data.get('language')
        accent = data.get('accent')
        voice = data.get('voice')
        
        if not language or not accent or not voice:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # 验证参数
        valid_accents = JAPANESE_ACCENTS if language == 'japanese' else ENGLISH_ACCENTS
        if accent not in valid_accents or voice not in VOICES:
            return jsonify({
                'success': False,
                'error': 'Invalid parameter values'
            }), 400
        
        from datetime import datetime
        now = datetime.now().isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_audio_preferences
            (user_id, language, accent, voice, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, language, accent, voice, now, now))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Audio preferences updated',
            'preferences': {
                'language': language,
                'accent': accent,
                'voice': voice
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@audio_api.route('/api/audio/config', methods=['GET'])
def get_audio_config():
    """获取音频配置(可用的口音和音色)"""
    return jsonify({
        'success': True,
        'config': {
            'japanese': {
                'accents': JAPANESE_ACCENTS,
                'voices': VOICES
            },
            'english': {
                'accents': ENGLISH_ACCENTS,
                'voices': VOICES
            }
        }
    })
