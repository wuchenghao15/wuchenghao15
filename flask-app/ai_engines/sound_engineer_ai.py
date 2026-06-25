import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
拟音师AI系统
负责音频润色、智能组合和发音优化
"""
import os
import json
import re
from datetime import datetime
import sqlite3

class SoundEngineerAI:
    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.english_pronunciation_cache = {}
        self.japanese_pronunciation_cache = {}
        self.composition_rules_cache = {}
        self._load_cache()
        
    def _load_cache(self):
        """加载缓存数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 加载英语发音素材缓存
            cursor.execute('SELECT type, content, file_path FROM english_pronunciation')
            for row in cursor.fetchall():
                key = f"{row[0]}_{row[1]}"
                self.english_pronunciation_cache[key] = row[2]
            
            # 加载日语发音素材缓存
            cursor.execute('SELECT type, content, file_path FROM japanese_pronunciation')
            for row in cursor.fetchall():
                key = f"{row[0]}_{row[1]}"
                self.japanese_pronunciation_cache[key] = row[2]
            
            # 加载组合规则缓存
            cursor.execute('SELECT language, rule_name, rule_pattern FROM audio_composition_rules WHERE active = 1')
            for row in cursor.fetchall():
                if row[0] not in self.composition_rules_cache:
                    self.composition_rules_cache[row[0]] = []
                self.composition_rules_cache[row[0]].append({
                    'name': row[1],
                    'pattern': row[2]
                })
            
            conn.close()
        except Exception as e:
            logger.info(f"加载缓存失败: {e}")
    
    def get_pronunciation(self, language, content, accent='standard', voice='female'):
        """获取发音素材路径"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if language == 'english':
            cursor.execute('''
                SELECT file_path FROM english_pronunciation
                WHERE content = ? AND accent = ? AND voice = ?
                LIMIT 1
            ''', (content, accent, voice))
        else:
            cursor.execute('''
                SELECT file_path FROM japanese_pronunciation
                WHERE content = ? AND accent = ? AND voice = ?
                LIMIT 1
            ''', (content, accent, voice))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def enhance_pronunciation(self, input_text, language, accent='standard', voice='female'):
        """
        润色发音,使发音更符合要求和特色
        :param input_text: 输入文本
        :param language: 语言类型 (english/japanese)
        :param accent: 口音类型
        :param voice: 音色类型
        :return: 润色后的文本和发音建议
        """
        result = {
            'original_text': input_text,
            'enhanced_text': input_text,
            'pronunciation_suggestions': [],
            'phonetic': '',
            'notes': []
        }
        
        if language == 'english':
            result = self._enhance_english(input_text, accent, result)
        else:
            result = self._enhance_japanese(input_text, accent, result)
        
        return result
    
    def _enhance_english(self, text, accent, result):
        """润色英语发音"""
        text = text.strip()
        
        # 根据口音调整发音
        if accent == 'uk':
            # 英式发音特色处理
            replacements = {
                'schedule': 'shed-yool',
                'either': 'ee-ther',
                'neither': 'nee-ther',
                'advertisement': 'ad-ver-tis-ment',
                'tomato': 'to-mah-to',
                'data': 'day-ta'
            }
            result['notes'].append('应用英式发音规则')
        elif accent == 'us':
            # 美式发音特色处理
            replacements = {
                'schedule': 'sked-yool',
                'either': 'i-ther',
                'neither': 'ni-ther',
                'advertisement': 'ad-ver-tis-ment',
                'tomato': 'to-may-to',
                'data': 'dat-uh'
            }
            result['notes'].append('应用美式发音规则')
        elif accent == 'africa':
            result['notes'].append('应用非洲英语发音规则')
        elif accent == 'india':
            result['notes'].append('应用印度英语发音规则')
        
        # 发音建议
        words = text.lower().split()
        for word in words:
            suggestion = self._analyze_english_word(word, accent)
            if suggestion:
                result['pronunciation_suggestions'].append(suggestion)
        
        return result
    
    def _enhance_japanese(self, text, accent, result):
        """润色日语发音"""
        text = text.strip()
        
        if accent == 'kansai':
            # 关西腔特色处理
            result['notes'].append('应用关西腔发音规则')
            # 关西腔特有发音
            replacements = {
                'は': 'わ',
                'へ': 'え',
                'を': 'お'
            }
            result['notes'].append('关西腔:は→わ, へ→え, を→お')
        else:
            # 关东腔标准发音
            result['notes'].append('应用关东腔发音规则')
        
        # 分析日语发音
        suggestions = self._analyze_japanese_text(text)
        result['pronunciation_suggestions'].extend(suggestions)
        
        return result
    
    def _analyze_english_word(self, word, accent):
        """分析英语单词发音"""
        suggestions = []
        
        # 常见发音规则
        rules = {
            'ough': ['/ˈʌf/', '/ˈoʊ/', '/ˈuː/'],
            'ough': ['tough', 'though', 'through'],
            'ea': ['/iː/', '/e/'],
            'th': ['/θ/', '/ð/']
        }
        
        # 检查特定发音模式
        if len(word) > 1:
            if word.endswith('tion'):
                suggestions.append(f"'{word}' - 发音: /ʃən/")
            elif word.endswith('sion'):
                suggestions.append(f"'{word}' - 发音: /ʒən/")
            elif 'ough' in word:
                suggestions.append(f"'{word}' - 'ough'组合需注意发音")
            elif word.startswith('th'):
                suggestions.append(f"'{word}' - 清辅音/θ/或浊辅音/ð/")
        
        return suggestions if suggestions else None
    
    def _analyze_japanese_text(self, text):
        """分析日语文本发音"""
        suggestions = []
        
        # 检查拗音
        youon_pattern = r'[きしちにひみりぎじぢびみキシチニヒミリギジヂビミ][ゃゅょャュョ]'
        matches = re.findall(youon_pattern, text)
        for match in matches:
            suggestions.append(f"'{match}' - 拗音发音")
        
        # 检查促音
        sokuon_pattern = r'っ[かきくけこさしすせそたちつてとはひふへほ]'
        matches = re.findall(sokuon_pattern, text)
        for match in matches:
            suggestions.append(f"'{match}' - 促音(っ)发音")
        
        # 检查长音
        chouon_pattern = r'ああ|いい|うう|ええ|おお|かあ|きい|くう|けえ|こお'
        matches = re.findall(chouon_pattern, text)
        for match in matches:
            suggestions.append(f"'{match}' - 长音发音")
        
        return suggestions
    
    def compose_audio(self, text, language, accent='standard', voice='female', quality='high'):
        """
        智能组合音频文件
        :param text: 输入文本
        :param language: 语言类型
        :param accent: 口音
        :param voice: 音色
        :param quality: 音质
        :return: 合成结果
        """
        result = {
            'success': False,
            'message': '',
            'audio_segments': [],
            'output_path': '',
            'duration': 0,
            'composition_log': []
        }
        
        try:
            if language == 'english':
                segments = self._compose_english_audio(text, accent, voice)
            else:
                segments = self._compose_japanese_audio(text, accent, voice)
            
            result['audio_segments'] = segments
            result['duration'] = sum(seg.get('duration', 0) for seg in segments)
            result['success'] = True
            result['message'] = '音频合成成功'
            
            # 生成输出路径
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"composed_{language}_{accent}_{voice}_{timestamp}.wav"
            result['output_path'] = f"audio/composed/{language}/{filename}"
            
            # 保存合成记录
            self._save_synthesis_record(text, language, accent, voice, result['output_path'], 
                                       result['duration'], quality, 'completed')
            
        except Exception as e:
            result['message'] = f'合成失败: {str(e)}'
            self._save_synthesis_record(text, language, accent, voice, '', 0, quality, 'failed', str(e))
        
        return result
    
    def _compose_english_audio(self, text, accent, voice):
        """组合英语音频"""
        segments = []
        text = text.strip().lower()
        
        # 分割文本为单词
        words = re.findall(r"[\w']+|[.,!?;]", text)
        
        for word in words:
            if word in ['.', ',', '!', '?', ';']:
                # 标点符号添加短暂停顿
                segments.append({
                    'type': 'pause',
                    'duration': 0.3,
                    'content': word
                })
                continue
            
            # 尝试获取单词发音
            file_path = self.get_pronunciation('english', word, accent, voice)
            if file_path:
                segments.append({
                    'type': 'word',
                    'content': word,
                    'file_path': file_path,
                    'duration': self._estimate_duration(word)
                })
            else:
                # 如果没有完整单词发音,尝试字母组合
                letters = list(word)
                for letter in letters:
                    letter_path = self.get_pronunciation('english', letter, accent, voice)
                    if letter_path:
                        segments.append({
                            'type': 'letter',
                            'content': letter,
                            'file_path': letter_path,
                            'duration': 0.15
                        })
        
        return segments
    
    def _compose_japanese_audio(self, text, accent, voice):
        """组合日语音频"""
        segments = []
        
        # 平假名和片假名正则
        hiragana_pattern = r'[あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんゃゅょっ]'
        katakana_pattern = r'[アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンャュョッ]'
        
        # 分解日语文本
        chars = []
        i = 0
        while i < len(text):
            # 检查拗音(2字符组合)
            if i + 1 < len(text):
                two_char = text[i:i+2]
                if re.match(hiragana_pattern + r'[ゃゅょ]', two_char) or re.match(katakana_pattern + r'[ャュョ]', two_char):
                    chars.append(two_char)
                    i += 2
                    continue
            
            chars.append(text[i])
            i += 1
        
        for char in chars:
            if char == ' ':
                segments.append({
                    'type': 'pause',
                    'duration': 0.2,
                    'content': ' '
                })
                continue
            
            file_path = self.get_pronunciation('japanese', char, accent, voice)
            if file_path:
                segments.append({
                    'type': 'character',
                    'content': char,
                    'file_path': file_path,
                    'duration': self._estimate_japanese_duration(char)
                })
            else:
                segments.append({
                    'type': 'unknown',
                    'content': char,
                    'duration': 0.2
                })
        
        return segments
    
    def _estimate_duration(self, word):
        """估算英语单词发音时长"""
        base_duration = 0.1  # 基础时长
        letter_duration = 0.05  # 每个字母增加的时长
        return base_duration + (len(word) * letter_duration)
    
    def _estimate_japanese_duration(self, char):
        """估算日语字符发音时长"""
        if char == 'っ':  # 促音
            return 0.1
        elif len(char) == 2:  # 拗音:
            return 0.35
        else:
            return 0.25
    
    def _save_synthesis_record(self, input_text, language, accent, voice, output_path, duration, quality, status, error_message=''):
        """保存合成记录到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO audio_synthesis_records
            (input_text, language, accent, voice, output_file_path, duration, quality, 
             status, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (input_text, language, accent, voice, output_path, duration, quality, 
              status, error_message, now, now))
        
        conn.commit()
        conn.close()
    
    def add_pronunciation_material(self, language, type_, content, accent, voice, file_path, 
                                   phonetic=None, hiragana=None, katakana=None, romaji=None):
        """添加发音素材"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        if language == 'english':
            cursor.execute('''
                INSERT OR REPLACE INTO english_pronunciation
                (type, content, phonetic, accent, voice, file_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (type_, content, phonetic, accent, voice, file_path, now, now))
        else:
            cursor.execute('''
                INSERT OR REPLACE INTO japanese_pronunciation
                (type, content, hiragana, katakana, romaji, accent, voice, file_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (type_, content, hiragana, katakana, romaji, accent, voice, file_path, now, now))
        
        conn.commit()
        conn.close()
        
        # 更新缓存
        key = f"{type_}_{content}"
        if language == 'english':
            self.english_pronunciation_cache[key] = file_path
        else:
            self.japanese_pronunciation_cache[key] = file_path
    
    def add_composition_rule(self, language, rule_name, rule_pattern, priority=1, description=''):
        """添加音频组合规则"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO audio_composition_rules
            (language, rule_name, rule_pattern, priority, description, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        ''', (language, rule_name, rule_pattern, priority, description, now, now))
        
        conn.commit()
        conn.close()
        
        # 更新缓存
        if language not in self.composition_rules_cache:
            self.composition_rules_cache[language] = []
        self.composition_rules_cache[language].append({
            'name': rule_name,
            'pattern': rule_pattern
        })
    
    def get_statistics(self):
        """获取发音素材统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM english_pronunciation')
        english_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM japanese_pronunciation')
        japanese_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM audio_composition_rules WHERE active = 1')
        rules_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM audio_synthesis_records WHERE status = "completed"')
        completed_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'english_pronunciation_count': english_count,
            'japanese_pronunciation_count': japanese_count,
            'active_rules_count': rules_count,
            'completed_synthesis_count': completed_count
        }
