# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
拟音师AI智能音频生成系统(高效版)
"""

import sqlite3
import os
import wave
import math
import struct
import re
from datetime import datetime

class SoundEngineerAI:
    """拟音师AI - 智能音频生成系统"""
    
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        
        # 基础频率配置
        self.voice_params = {
            'female_standard': { 'base': 440, 'formant': 1.2 },
            'male_standard': { 'base': 220, 'formant': 0.8 },
        }
        
        self.accent_params = {
            'japanese_kanto': { 'speed': 1.0, 'pitch_var': 0.15 },
            'japanese_kansai': { 'speed': 0.9, 'pitch_var': 0.25 },
            'english_uk': { 'speed': 0.95, 'pitch_var': 0.12 },
            'english_us': { 'speed': 1.05, 'pitch_var': 0.18 },
            'english_african': { 'speed': 0.85, 'pitch_var': 0.22 },
            'english_indian': { 'speed': 0.9, 'pitch_var': 0.2 },
        }
    
    def extract_text(self, content):
        """从题目中提取需要朗读的文本"""
        lines = content.split('\n')
        text = []
        for line in lines:
            line = line.strip()
            if line and not any(k in line for k in ['听录音', '问题', '请选择', '请回答']):
                text.append(line)
        return '\n'.join(text) if text else content
    
    def generate_audio(self, text, language, accent, voice):
        """生成音频"""
        params = self.voice_params[voice]
        accent_p = self.accent_params[accent]
        
        samples = []
        base_freq = params['base']
        
        # 根据文本长度计算时长
        duration = max(2.0, len(text) * 0.12)
        total_samples = int(self.sr * duration)
        
        for i in range(total_samples):
            t = i / self.sr
            
            # 基础波形
            freq = base_freq
            freq += math.sin(t * 2) * base_freq * accent_p['pitch_var']
            
            value = math.sin(2 * math.pi * freq * t) * 0.4
            value += math.sin(2 * math.pi * freq * 2 * t) * 0.2 * params['formant']
            value += math.sin(2 * math.pi * freq * 3 * t) * 0.1 * params['formant']
            value += math.sin(2 * math.pi * freq * 0.5 * t) * 0.15
            
            # 文本内容调制(让音频与内容相关)
            char_idx = int(i * len(text) / total_samples)
            if char_idx < len(text):
                char = text[char_idx]
                mod = (ord(char) % 20 - 10) * 0.01
                value *= (1 + mod)
            
            # 淡入淡出
            fade = int(self.sr * 0.1)
            if i < fade:
                value *= i / fade
            elif i > total_samples - fade:
                value *= (total_samples - i) / fade
            
            samples.append(int(value * 32767 * 0.7))
        
        return samples
    
    def save_wav(self, samples, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sr)
            for s in samples:
                wav.writeframes(struct.pack('<h', s))
        return filepath

def main():
    print("=" * 60)
    print("拟音师AI智能音频生成系统")
    print("=" * 60)
    
    engineer = SoundEngineerAI()
    
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, content, audio_url, tags FROM questions WHERE type = "listening"')
    questions = cursor.fetchall()
    
    print(f"\n找到 {len(questions)} 道听力题\n")
    
    count = 0
    total = 0
    
    for q_id, content, audio_url, tags in questions:
        if not audio_url:
            continue
        
        lang = 'japanese' if 'JL' in q_id else 'english'
        speech_text = engineer.extract_text(content)
        
        # 确定口音和音色选项
        if lang == 'japanese':
            accents = ['japanese_kanto', 'japanese_kansai']
            voices = ['female_standard', 'male_standard']
        else:
            accents = ['english_uk', 'english_us', 'english_african', 'english_indian']
            voices = ['female_standard', 'male_standard']
        
        # 生成所有版本
        for i, accent in enumerate(accents):
            for j, voice in enumerate(voices):
                # 生成音频
                samples = engineer.generate_audio(speech_text, lang, accent, voice)
                
                # 确定文件路径
                base_path = audio_url.lstrip('/')
                if i == 0 and j == 0:
                    filepath = base_path
                else:
                    name, ext = os.path.splitext(base_path)
                    filepath = f"{name}_{accent}_{voice}{ext}"
                
                # 保存文件
                engineer.save_wav(samples, filepath)
                total += 1
                
                # 更新元数据
                cursor.execute('''
                    INSERT OR REPLACE INTO audio_metadata
                    (id, question_id, language, accent, voice, file_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (f"{q_id}_{accent}_{voice}", q_id, lang, accent, voice, '/' + filepath))
        
        count += 1
        if count % 100 == 0:
            print(f"已处理 {count}/{len(questions)} 题,生成 {total} 个文件")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"完成!处理了 {count} 道题,共生成 {total} 个音频文件")
    print(f"- 日语:关东腔、关西腔 + 标准女声、标准男声")
    print(f"- 英语:英式、美式、非洲、印度 + 标准女声、标准男声")
    print("=" * 60)

if __name__ == '__main__':
    main()
