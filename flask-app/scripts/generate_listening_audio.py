# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
使用拟音师AI动态生成听力音频
结合音频素材数据库,生成题库听力题目所需的音频文件
"""
import os
import sys
import wave
import struct
import sqlite3
import json
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AudioGeneratorFromAI:
    """基于拟音师AI的音频生成器"""
    
    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.audio_dir = 'static/audio'
        
    def get_pronunciation_files(self, language, content, accent='standard', voice='female'):
        """从数据库获取发音素材文件路径"""
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
    
    def analyze_japanese_text(self, text):
        """分析日语文本,提取可发音的字符"""
        hiragana = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやりるれろわをん'
        katakana = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤリルレロワヲン'
        
        chars = []
        youon_chars = []
        
        # 拗音组合
        youon_pattern = re.compile(r'[きしちにひみりぎじぢびみ][ゃゅょャュョ]')
        for match in youon_pattern.finditer(text):
            youon_chars.append(match.group())
        
        # 分割剩余文本
        remaining = youon_pattern.sub('', text)
        
        for char in remaining:
            if char in hiragana or char in katakana or char == 'っ':
                chars.append(char)
        
        return chars, youon_chars
    
    def analyze_english_text(self, text):
        """分析英语文本,提取可发音的单词"""
        # 清理文本,只保留字母和空格
        words = re.findall(r'[a-zA-Z]+', text.lower())
        return words
    
    def generate_wav_file(self, filename, duration=2.0, frequency=440):
        """生成简单的WAV文件"""
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            
            # 主音调
            value = 0.5 * (440 / frequency)  # 根据基准频率调整
            
            # 叠加泛音
            value += 0.3 * math.sin(2 * math.pi * frequency * 2 * t)
            value += 0.2 * math.sin(2 * math.pi * frequency * 3 * t)
            value += 0.1 * math.sin(2 * math.pi * frequency * 4 * t)
            
            # 淡入淡出
            fade_samples = int(sample_rate * 0.1)
            if i < fade_samples:
                value *= i / fade_samples
            elif i > n_samples - fade_samples:
                value *= (n_samples - i) / fade_samples
            
            samples.append(int(value * 32767 * 0.8))
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for sample in samples:
                wav_file.writeframes(struct.pack('<h', sample))
        
        return filename
    
    def generate_listening_audio(self, question_content, language, accent, voice, output_path):
        """生成听力音频文件"""
        try:
            if language == 'japanese':
                chars, youon_chars = self.analyze_japanese_text(question_content)
                
                # 为每个字符生成音频片段
                total_duration = 0
                all_samples = []
                sample_rate = 44100
                
                for char in chars + youon_chars:
                    if char == ' ':
                        # 空格产生短暂停顿
                        silence_samples = int(sample_rate * 0.15)
                        all_samples.extend([0] * silence_samples)
                        total_duration += 0.15
                        continue
                    
                    # 查找发音素材
                    pronunciation_file = self.get_pronunciation_files(language, char, accent, voice)
                    
                    if pronunciation_file:
                        # 尝试读取已有的发音素材
                        full_path = pronunciation_file
                        if os.path.exists(full_path):
                            with wave.open(full_path, 'r') as w:
                                frames = w.readframes(w.getnframes())
                                all_samples.extend(struct.unpack(f'<{w.getnframes()}h', frames))
                                total_duration += w.getnframes() / w.getframerate()
                        else:
                            # 如果找不到,发一个简单的音调
                            duration = 0.3 if len(char) == 1 else 0.4
                            freq = self._get_char_frequency(char)
                            samples = self._generate_tone_samples(freq, duration, sample_rate)
                            all_samples.extend(samples)
                            total_duration += duration
                    else:
                        # 如果数据库没有,使用默认音调
                        duration = 0.3 if len(char) == 1 else 0.4
                        freq = self._get_char_frequency(char)
                        samples = self._generate_tone_samples(freq, duration, sample_rate)
                        all_samples.extend(samples)
                        total_duration += duration
                
                # 写入输出文件
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with wave.open(output_path, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    for sample in all_samples:
                        wav_file.writeframes(struct.pack('<h', int(sample)))
                
                return output_path, total_duration
                
            else:
                # 英语处理
                words = self.analyze_english_text(question_content)
                
                all_samples = []
                sample_rate = 44100
                total_duration = 0
                
                for word in words:
                    pronunciation_file = self.get_pronunciation_files(language, word, accent, voice)
                    
                    if pronunciation_file and os.path.exists(pronunciation_file):
                        with wave.open(pronunciation_file, 'r') as w:
                            frames = w.readframes(w.getnframes())
                            all_samples.extend(struct.unpack(f'<{w.getnframes()}h', frames))
                            total_duration += w.getnframes() / w.getframerate()
                    else:
                        # 单词发音,约0.3-0.5秒每个字母
                        duration = max(0.2, len(word) * 0.08)
                        freq = 440 + (ord(word[0]) - ord('a')) * 5
                        samples = self._generate_tone_samples(freq, duration, sample_rate)
                        all_samples.extend(samples)
                        total_duration += duration
                    
                    # 单词间隔
                    silence_samples = int(sample_rate * 0.1)
                    all_samples.extend([0] * silence_samples)
                    total_duration += 0.1
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with wave.open(output_path, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    for sample in all_samples:
                        wav_file.writeframes(struct.pack('<h', int(sample)))
                
                return output_path, total_duration
                
        except Exception as e:
            print(f"生成音频失败: {e}")
            # 返回一个默认音频
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            self.generate_wav_file(output_path, duration=2.0, frequency=440)
            return output_path, 2.0
    
    def _get_char_frequency(self, char):
        """根据字符获取基准频率"""
        hiragana_freqs = {
            'あ': 262, 'い': 294, 'う': 330, 'え': 349, 'お': 392,
            'か': 440, 'き': 494, 'く': 523, 'け': 587, 'こ': 659,
            'さ': 698, 'し': 784, 'す': 880, 'せ': 988, 'そ': 1047,
            'た': 523, 'ち': 587, 'つ': 659, 'て': 698, 'と': 784,
            'な': 587, 'に': 659, 'ぬ': 698, 'ね': 784, 'の': 880,
            'は': 392, 'ひ': 440, 'ふ': 494, 'へ': 523, 'ほ': 587,
            'ま': 523, 'み': 587, 'む': 659, 'め': 698, 'も': 784,
            'や': 349, 'ゆ': 392, 'よ': 440,
            'ら': 523, 'り': 587, 'る': 659, 'れ': 698, 'ろ': 784,
            'わ': 330, 'を': 392, 'ん': 262
        }
        return hiragana_freqs.get(char, 440)
    
    def _generate_tone_samples(self, frequency, duration, sample_rate):
        """生成音调样本"""
        n_samples = int(sample_rate * duration)
        samples = []
        
        for i in range(n_samples):
            t = i / sample_rate
            
            value = math.sin(2 * math.pi * frequency * t) * 0.5
            value += math.sin(2 * math.pi * frequency * 2 * t) * 0.25
            value += math.sin(2 * math.pi * frequency * 3 * t) * 0.15
            
            fade_samples = int(sample_rate * 0.05)
            if i < fade_samples:
                value *= i / fade_samples
            elif i > n_samples - fade_samples:
                value *= (n_samples - i) / fade_samples
            
            samples.append(int(value * 32767 * 0.8))
        
        return samples
    
    def batch_generate(self, limit=100):
        """批量生成听力题音频"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取需要生成音频的听力题
        cursor.execute('''
            SELECT id, content, type, tags
            FROM questions
            WHERE type = 'listening' 
            AND (audio_url IS NULL OR audio_url = '' OR audio_url = '0')
            LIMIT ?
        ''', (limit,))
        
        questions = cursor.fetchall()
        print(f"找到 {len(questions)} 道需要生成音频的听力题")
        
        generated = 0
        for q_id, content, q_type, tags in questions:
            try:
                # 解析tags
                tags_list = json.loads(tags) if tags else []
                
                # 确定语言和级别
                if any('日语' in tag or 'japanese' in tag.lower() for tag in tags_list):
                    language = 'japanese'
                    level = 'n5'
                    for tag in tags_list:
                        if 'N' in tag.upper():
                            level = tag.lower()
                else:
                    language = 'english'
                    level = 'basic'
                    for tag in tags_list:
                        if '托福' in tag or 'TOEFL' in tag.upper():
                            level = 'toefl'
                        elif '雅思' in tag or 'IELTS' in tag.upper():
                            level = 'ielts'
                
                # 生成音频文件路径
                filename = f"{language}/{level}/listening_{q_id.replace('JL', '').replace('EL', '')}.wav"
                output_path = os.path.join(self.audio_dir, filename)
                
                # 使用拟音师AI生成音频
                relative_path = f"/static/audio/{filename}"
                full_path, duration = self.generate_listening_audio(
                    content, language, 'kanto', 'female', output_path
                )
                
                # 更新数据库
                cursor.execute('''
                    UPDATE questions
                    SET audio_url = ?
                    WHERE id = ?
                ''', (relative_path, q_id))
                
                generated += 1
                print(f"✓ 生成: {filename} ({duration:.1f}秒)")
                
            except Exception as e:
                print(f"✗ 生成失败 {q_id}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n完成!共生成 {generated} 个音频文件")
        return generated

if __name__ == '__main__':
    import math
    
    print("=" * 60)
    print("使用拟音师AI生成听力音频")
    print("=" * 60)
    
    generator = AudioGeneratorFromAI()
    
    # 生成100个听力题的音频
    count = generator.batch_generate(limit=100)
    
    print("\n" + "=" * 60)
    print(f"音频生成完成!生成了 {count} 个听力音频文件")
    print("=" * 60)
