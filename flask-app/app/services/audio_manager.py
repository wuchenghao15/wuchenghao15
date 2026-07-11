import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
音频管理服务
支持日语和英语听力题的音频管理,包括多种口音和音色
"""
import sqlite3
import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Any

class AudioManager:
    """音频管理器"""
    
    # 日语配置
    JAPANESE_ACCENTS = {
        'kanto': '关东腔',
        'kansai': '关西腔'
    }
    
    # 英语配置
    ENGLISH_ACCENTS = {
        'uk': '英式发音',
        'us': '美式发音',
        'africa': '非洲英语',
        'india': '印度英语'
    }
    
    # 音色配置
    VOICES = {
        'female': '标准女声',
        'male': '标准男声'
    }
    
    def __init__(self, db_path: str = 'app.db'):
        self.db_path = db_path
        self.base_audio_dir = 'static/audio'
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 创建音频元数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_metadata (
                    id TEXT PRIMARY KEY,
                    question_id TEXT,
                    language TEXT,
                    accent TEXT,
                    voice TEXT,
                    file_path TEXT,
                    duration REAL,
                    transcript TEXT,
                    created_at TEXT,
                    FOREIGN KEY(question_id) REFERENCES questions(id)
                )
            ''')
            
            # 创建用户音频偏好表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_audio_preferences (
                    user_id INTEGER,
                    language TEXT,
                    accent TEXT,
                    voice TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    PRIMARY KEY(user_id, language)
                )
            ''')
            
            conn.commit()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def get_audio_path(self, language: str, accent: str, voice: str, question_id: str) -> str:
        """生成音频文件路径"""
        if language == 'japanese':
            return f'{self.base_audio_dir}/japanese/{accent}/{voice}/listening_{question_id}.mp3'
        elif language == 'english':
            return f'{self.base_audio_dir}/english/{accent}/{voice}/listening_{question_id}.mp3'
        return ''
    
    def get_available_audio_options(self, question_id: str) -> List[Dict]:
        """获取题目可用的音频选项"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT language, accent, voice, file_path, transcript, duration
                FROM audio_metadata
                WHERE question_id = ?
            ''', (question_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'language': row[0],
                    'accent': row[1],
                    'voice': row[2],
                    'file_path': row[3],
                    'transcript': row[4],
                    'duration': row[5]
                })
            
            return results
    
    def add_audio_for_question(self, question_id: str, language: str, 
                              accent: str, voice: str, file_path: str,
                              transcript: str, duration: float) -> bool:
        """为题目添加音频"""
        from datetime import datetime
        import hashlib
        
        audio_id = hashlib.md5(f'{question_id}_{language}_{accent}_{voice}'.encode()).hexdigest()
        
        with self._connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO audio_metadata
                    (id, question_id, language, accent, voice, file_path, duration, transcript, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (audio_id, question_id, language, accent, voice, file_path, duration, transcript, 
                      datetime.now().isoformat()))
                conn.commit()
                return True
            except Exception as e:
                print(f'添加音频失败: {e}')
                return False
    
    def set_user_preference(self, user_id: int, language: str, 
                           accent: str, voice: str) -> bool:
        """设置用户音频偏好"""
        from datetime import datetime
        
        with self._connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_audio_preferences
                    (user_id, language, accent, voice, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, language, accent, voice,
                      datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
                return True
            except Exception as e:
                print(f'设置用户偏好失败: {e}')
                return False
    
    def get_user_preference(self, user_id: int, language: str) -> Optional[Dict]:
        """获取用户音频偏好"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT accent, voice
                FROM user_audio_preferences
                WHERE user_id = ? AND language = ?
            ''', (user_id, language))
            
            row = cursor.fetchone()
            if row:
                return {
                    'accent': row[0],
                    'voice': row[1]
                }
            return None
    
    def get_default_audio(self, question_id: str, language: str) -> Optional[Dict]:
        """获取题目的默认音频(优先使用用户偏好)"""
        # 先获取所有可用音频
        options = self.get_available_audio_options(question_id)
        if not options:
            return None
        
        # 如果只有一个选项,直接返回
        if len(options) == 1:
            return options[0]
        
        # 根据语言选择默认
        if language == 'japanese':
            default_accent = 'kanto'
            default_voice = 'female'
        else:
            default_accent = 'us'
            default_voice = 'female'
        
        # 寻找匹配的选项
        for opt in options:
            if opt['accent'] == default_accent and opt['voice'] == default_voice:
                return opt
        
        # 如果没有,返回第一个
        return options[0]
    
    def generate_sample_listening_questions(self):
        """生成示例听力题和对应的音频文件占位符"""
        # 日语示例
        japanese_samples = [
            {
                'id': 'jpn_listen_001',
                'content': '听下面的对话,选择正确的答案.',
                'transcript': '「今日は天気がいいですね.公園に行きましょう.」',
                'options': json.dumps(['「雨です」', '「寒いです」', '「晴れです」', '「雪です」']),
                'correct_answer': '「晴れです」',
                'difficulty': 1,
                'points': 2.0
            },
            {
                'id': 'jpn_listen_002',
                'content': '听下面的句子,选择正确的翻译.',
                'transcript': '「私は学生です.」',
                'options': json.dumps(['我是老师', '我是学生', '我是医生', '我是律师']),
                'correct_answer': '我是学生',
                'difficulty': 1,
                'points': 2.0
            }
        ]
        
        # 英语示例
        english_samples = [
            {
                'id': 'eng_listen_001',
                'content': 'Listen to the dialogue and choose the correct answer.',
                'transcript': '"How are you today?" "I\'m fine, thank you!"',
                'options': json.dumps(['"I\'m sick."', '"I\'m fine."', '"I\'m tired."', '"I\'m busy."']),
                'correct_answer': '"I\'m fine."',
                'difficulty': 1,
                'points': 2.0
            },
            {
                'id': 'eng_listen_002',
                'content': 'Listen to the sentence and choose the correct meaning.',
                'transcript': '"The weather is beautiful today."',
                'options': json.dumps(['It\'s raining', 'It\'s beautiful', 'It\'s cold', 'It\'s windy']),
                'correct_answer': 'It\'s beautiful',
                'difficulty': 1,
                'points': 2.0
            }
        ]
        
        # 添加到数据库
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 日语
            for sample in japanese_samples:
                # 先确保题目标记为听力题
                cursor.execute('''
                    INSERT OR IGNORE INTO questions
                    (id, type, content, options, correct_answer, difficulty, points, tags, created_at)
                    VALUES (?, 'listening', ?, ?, ?, ?, ?, ?, ?)
                ''', (sample['id'], sample['content'], sample['options'], 
                      sample['correct_answer'], sample['difficulty'], sample['points'],
                      '["listening","japanese"]', datetime.now().isoformat()))
                
                # 添加各种口音和音色的音频
                for accent in self.JAPANESE_ACCENTS.keys():
                    for voice in self.VOICES.keys():
                        audio_path = self.get_audio_path('japanese', accent, voice, sample['id'])
                        self.add_audio_for_question(
                            sample['id'], 'japanese', accent, voice,
                            audio_path, sample['transcript'], 5.0
                        )
            
            # 英语
            for sample in english_samples:
                cursor.execute('''
                    INSERT OR IGNORE INTO questions
                    (id, type, content, options, correct_answer, difficulty, points, tags, created_at)
                    VALUES (?, 'listening', ?, ?, ?, ?, ?, ?, ?)
                ''', (sample['id'], sample['content'], sample['options'], 
                      sample['correct_answer'], sample['difficulty'], sample['points'],
                      '["listening","english"]', datetime.now().isoformat()))
                
                for accent in self.ENGLISH_ACCENTS.keys():
                    for voice in self.VOICES.keys():
                        audio_path = self.get_audio_path('english', accent, voice, sample['id'])
                        self.add_audio_for_question(
                            sample['id'], 'english', accent, voice,
                            audio_path, sample['transcript'], 5.0
                        )
            
            conn.commit()
    
    def create_audio_placeholder_files(self):
        """创建音频占位符文件"""
        # 创建一个简单的文本文件说明音频内容
        info_file = os.path.join(self.base_audio_dir, 'audio_readme.txt')
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write('''听力音频文件目录
=================

日语
---
- kanto/: 关东腔
  - female/: 标准女声
  - male/: 标准男声
- kansai/: 关西腔
  - female/: 标准女声
  - male/: 标准男声

英语
---
- uk/: 英式发音
  - female/: 标准女声
  - male/: 标准男声
- us/: 美式发音
  - female/: 标准女声
  - male/: 标准男声
- africa/: 非洲英语
  - female/: 标准女声
  - male/: 标准男声
- india/: 印度英语
  - female/: 标准女声
  - male/: 标准男声

注意:真实音频文件需要使用文本转语音服务生成
''')
        
        # 为每个目录创建一个占位符文件
        for lang, accents in [('japanese', self.JAPANESE_ACCENTS), 
                            ('english', self.ENGLISH_ACCENTS)]:
            for accent in accents.keys():
                for voice in self.VOICES.keys():
                    dir_path = os.path.join(self.base_audio_dir, lang, accent, voice)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                    
                    # 创建占位符文件
                    placeholder = os.path.join(dir_path, 'readme.txt')
                    with open(placeholder, 'w', encoding='utf-8') as f:
                        f.write(f'''{self.JAPANESE_ACCENTS.get(accent, self.ENGLISH_ACCENTS.get(accent, accent))} - {self.VOICES[voice]}
将实际的MP3文件放在此目录中
文件名格式:listening_<题目ID>.mp3
''')


# 单例
_audio_manager = None

def get_audio_manager() -> AudioManager:
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager


if __name__ == '__main__':
    from datetime import datetime
    manager = get_audio_manager()
    print('初始化音频管理器...')
    manager.create_audio_placeholder_files()
    manager.generate_sample_listening_questions()
    logger.info('完成!')
