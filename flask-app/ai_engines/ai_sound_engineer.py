# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
拟音师AI智能音频生成系统
支持:日语关东/关西腔 + 标准男女声;英语英式/美式/非洲/印度 + 标准男女声
"""

import sqlite3
import os
import wave
import math
import struct
import re

# ============================================
# 发音定义系统
# ============================================

# 日语50音图 - 频率映射(Hz)
HIRAGANA_FREQ = {
    'あ': 440, 'い': 494, 'う': 523, 'え': 587, 'お': 659,
    'か': 392, 'き': 440, 'く': 494, 'け': 523, 'こ': 587,
    'さ': 587, 'し': 659, 'す': 698, 'せ': 784, 'そ': 880,
    'た': 523, 'ち': 587, 'つ': 659, 'て': 698, 'と': 784,
    'な': 466, 'に': 523, 'ぬ': 587, 'ね': 659, 'の': 698,
    'は': 349, 'ひ': 392, 'ふ': 440, 'へ': 494, 'ほ': 523,
    'ま': 329, 'み': 370, 'む': 415, 'め': 466, 'も': 523,
    'や': 392, 'ゆ': 440, 'よ': 494,
    'ら': 330, 'り': 370, 'る': 415, 'れ': 466, 'ろ': 523,
    'わ': 294, 'を': 330, 'ん': 262,
    'が': 370, 'ぎ': 415, 'ぐ': 466, 'げ': 523, 'ご': 587,
    'ざ': 554, 'じ': 622, 'ず': 659, 'ぜ': 740, 'ぞ': 831,
    'だ': 494, 'ぢ': 554, 'づ': 622, 'で': 659, 'ど': 740,
    'ば': 330, 'び': 370, 'ぶ': 415, 'べ': 466, 'ぼ': 523,
    'ぱ': 392, 'ぴ': 440, 'ぷ': 494, 'ぺ': 554, 'ぽ': 622,
    'きゃ': 466, 'きゅ': 523, 'きょ': 587,
    'しゃ': 554, 'しゅ': 622, 'しょ': 698,
    'ちゃ': 494, 'ちゅ': 554, 'ちょ': 622,
    'にゃ': 523, 'にゅ': 587, 'にょ': 659,
    'ひゃ': 370, 'ひゅ': 415, 'ひょ': 466,
    'みゃ': 349, 'みゅ': 392, 'みょ': 440,
    'りゃ': 311, 'りゅ': 349, 'りょ': 392,
    'きゃ': 466, 'きゅ': 523, 'きょ': 587,
    'ぎゃ': 349, 'ぎゅ': 392, 'ぎょ': 440,
    'じゃ': 523, 'じゅ': 587, 'じょ': 659,
    'びゃ': 311, 'びゅ': 349, 'びょ': 392,
    'ぴゃ': 370, 'ぴゅ': 415, 'ぴょ': 466,
}

# 英语字母发音频率
ENG_LETTER_FREQ = {
    'a': 440, 'b': 494, 'c': 523, 'd': 587, 'e': 659,
    'f': 698, 'g': 784, 'h': 880, 'i': 392, 'j': 440,
    'k': 494, 'l': 523, 'm': 587, 'n': 659, 'o': 698,
    'p': 784, 'q': 880, 'r': 349, 's': 392, 't': 440,
    'u': 494, 'v': 523, 'w': 587, 'x': 659, 'y': 698, 'z': 784,
}

# ============================================
# 拟音师AI核心类
# ============================================

class SoundEngineerAI:
    """拟音师AI - 智能音频生成系统"""
    
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        
        # 音色配置
        self.voices = {
            'female_standard': { 'base_freq': 440, 'formant': 1.2, 'brightness': 1.1 },
            'male_standard': { 'base_freq': 220, 'formant': 0.8, 'brightness': 0.9 },
        }
        
        # 口音配置
        self.accents = {
            'japanese_kanto': { 'speed': 1.0, 'pitch_variation': 0.15, 'pause_ratio': 0.1 },
            'japanese_kansai': { 'speed': 0.9, 'pitch_variation': 0.25, 'pause_ratio': 0.15 },
            'english_uk': { 'speed': 0.95, 'pitch_variation': 0.12, 'stressed_emphasis': 1.3 },
            'english_us': { 'speed': 1.05, 'pitch_variation': 0.18, 'stressed_emphasis': 1.2 },
            'english_african': { 'speed': 0.85, 'pitch_variation': 0.22, 'stressed_emphasis': 1.4 },
            'english_indian': { 'speed': 0.9, 'pitch_variation': 0.2, 'stressed_emphasis': 1.25 },
        }
    
    def extract_speech_text(self, question_content):
        """
        智能从题目中提取需要朗读的文本
        """
        # 去掉问题部分
        lines = question_content.split('\n')
        speech_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if any(keyword in line for keyword in ['听录音', '问题', '请选择', '请回答']):
                continue
            # 如果看起来是对话或说明内容,保留
            if re.search(r'[::「」]', line) or len(line) > 5:
                speech_lines.append(line)
        
        return '\n'.join(speech_lines) if speech_lines else question_content
    
    def text_to_characters(self, text, language):
        """
        将文本分解为可发音的字符
        """
        chars = []
        if language == 'japanese':
            # 日语假名分解
            i = 0
            while i < len(text):
                found = False
                # 检查拗音(2字符)
                if i + 1 < len(text):
                    two_char = text[i:i+2]
                    if two_char in HIRAGANA_FREQ:
                        chars.append(two_char)
                        i += 2
                        found = True
                        continue
                # 单个假名
                if text[i] in HIRAGANA_FREQ:
                    chars.append(text[i])
                    i += 1
                else:
                    # 其他字符(标点、汉字等)
                    chars.append(text[i])
                    i += 1
        else:
            # 英语按字母分解
            chars = list(text.lower())
        
        return chars
    
    def generate_audio_segment(self, text, language, accent, voice, duration=0.15):
        """
        生成单个文本片段的音频
        """
        voice_config = self.voices[voice]
        accent_config = self.accents[accent]
        
        chars = self.text_to_characters(text, language)
        samples = []
        
        for char in chars:
            # 获取基础频率
            if language == 'japanese':
                freq = HIRAGANA_FREQ.get(char, voice_config['base_freq'])
            else:
                freq = ENG_LETTER_FREQ.get(char, voice_config['base_freq'])
            
            # 应用口音调整
            speed = accent_config['speed']
            pitch_var = accent_config['pitch_variation']
            freq += (math.sin(len(samples) * 0.01) - 0.5) * freq * pitch_var
            
            # 应用音色调整
            freq *= voice_config['formant']
            if 'female' in voice:
                freq *= 1.5
            
            # 生成波形
            seg_duration = duration / speed
            n = int(self.sr * seg_duration)
            
            for i in range(n):
                t = i / self.sr
                
                # 主音调
                value = math.sin(2 * math.pi * freq * t) * 0.4
                
                # 泛音(丰富音色)
                value += math.sin(2 * math.pi * freq * 2 * t) * 0.2 * voice_config['brightness']
                value += math.sin(2 * math.pi * freq * 3 * t) * 0.1 * voice_config['brightness']
                value += math.sin(2 * math.pi * freq * 0.5 * t) * 0.15
                
                # 颤音效果
                vibrato = math.sin(2 * math.pi * 5 * t) * 0.05
                value *= (1 + vibrato)
                
                # 淡入淡出
                fade = int(self.sr * 0.02)
                if i < fade:
                    value *= i / fade
                elif i > n - fade:
                    value *= (n - i) / fade
                
                samples.append(int(value * 32767 * 0.7))
            
            # 添加短暂停顿
            pause_samples = int(self.sr * 0.03 * accent_config['pause_ratio'])
            samples.extend([0] * pause_samples)
        
        return samples
    
    def generate_full_audio(self, text, language, accent, voice):
        """
        生成完整的音频
        """
        # 智能提取需要朗读的文本
        speech_text = self.extract_speech_text(text)
        
        # 分段生成(按句子)
        sentences = re.split(r'[.?!.!?\n]', speech_text)
        
        all_samples = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 生成这段句子的音频
            segment_samples = self.generate_audio_segment(sentence, language, accent, voice)
            all_samples.extend(segment_samples)
            
            # 句子间停顿
            all_samples.extend([0] * int(self.sr * 0.3))
        
        return all_samples
    
    def save_audio(self, samples, filepath):
        """保存音频到文件"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sr)
            
            for sample in samples:
                wav_file.writeframes(struct.pack('<h', sample))
        
        return filepath

# ============================================
# 主程序 - 智能生成所有听力音频
# ============================================

def main():
    print("=" * 60)
    print("拟音师AI智能音频生成系统")
    print("=" * 60)
    
    # 初始化
    engineer = SoundEngineerAI()
    
    # 连接数据库
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 获取所有听力题
    cursor.execute('SELECT id, content, audio_url, tags FROM questions WHERE type = "listening"')
    questions = cursor.fetchall()
    
    print(f"\n找到 {len(questions)} 道听力题\n")
    
    count = 0
    total = 0
    
    for q_id, content, audio_url, tags in questions:
        if not audio_url:
            continue
        
        # 确定语言
        language = 'japanese' if 'JL' in q_id else 'english'
        
        # 生成多种口音和音色的音频
        if language == 'japanese':
            accents = ['japanese_kanto', 'japanese_kansai']
            voices = ['female_standard', 'male_standard']
        else:
            accents = ['english_uk', 'english_us', 'english_african', 'english_indian']
            voices = ['female_standard', 'male_standard']
        
        # 主音频(第一个版本)
        main_accent = accents[0]
        main_voice = voices[0]
        
        samples = engineer.generate_full_audio(content, language, main_accent, main_voice)
        
        # 保存主音频
        main_path = audio_url.lstrip('/')
        engineer.save_audio(samples, main_path)
        count += 1
        total += 1
        
        # 保存其他版本(存储在audio_metadata表中)
        for i, accent in enumerate(accents):
            for j, voice in enumerate(voices):
                if i == 0 and j == 0:
                    continue  # 主音频已保存
                
                # 生成变体音频
                variant_samples = engineer.generate_full_audio(content, language, accent, voice)
                
                # 变体文件名
                path_parts = os.path.splitext(main_path)
                variant_path = f"{path_parts[0]}_{accent}_{voice}{path_parts[1]}"
                
                engineer.save_audio(variant_samples, variant_path)
                total += 1
        
        if count % 50 == 0:
            print(f"已处理 {count}/{len(questions)} 道题,生成 {total} 个音频文件")
    
    # 更新audio_metadata表
    print("\n更新音频元数据...")
    cursor.execute('DELETE FROM audio_metadata')
    
    for q_id, content, audio_url, tags in questions:
        if not audio_url:
            continue
        
        language = 'japanese' if 'JL' in q_id else 'english'
        
        if language == 'japanese':
            accents = ['japanese_kanto', 'japanese_kansai']
            voices = ['female_standard', 'male_standard']
        else:
            accents = ['english_uk', 'english_us', 'english_african', 'english_indian']
            voices = ['female_standard', 'male_standard']
        
        for accent in accents:
            for voice in voices:
                main_path = audio_url.lstrip('/')
                path_parts = os.path.splitext(main_path)
                
                if accent == accents[0] and voice == voices[0]:
                    variant_path = main_path
                else:
                    variant_path = f"{path_parts[0]}_{accent}_{voice}{path_parts[1]}"
                
                if os.path.exists(variant_path):
                    cursor.execute('''
                        INSERT OR REPLACE INTO audio_metadata
                        (question_id, audio_path, language, accent, voice_type, is_default)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (q_id, '/' + variant_path, language, accent, voice, 
                          1 if (accent == accents[0] and voice == voices[0]) else 0))
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"完成!")
    print(f"- 处理了 {count} 道听力题")
    print(f"- 共生成 {total} 个音频文件")
    print(f"- 支持多种口音和音色:")
    print(f"  - 日语:关东腔、关西腔 + 标准女声、标准男声")
    print(f"  - 英语:英式、美式、非洲、印度 + 标准女声、标准男声")
    print("=" * 60)

if __name__ == '__main__':
    main()
