# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
快速生成关键听力音频文件(用于测试)
"""

import sqlite3
import os
import wave
import math
import struct

def generate_audio(filepath, base_freq, duration=2.5):
    """生成音频文件"""
    sr = 44100
    samples = []
    
    total_samples = int(sr * duration)
    
    for i in range(total_samples):
        t = i / sr
        
        # 主波形
        value = math.sin(2 * math.pi * base_freq * t) * 0.4
        value += math.sin(2 * math.pi * base_freq * 2 * t) * 0.2
        value += math.sin(2 * math.pi * base_freq * 3 * t) * 0.1
        value += math.sin(2 * math.pi * base_freq * 0.5 * t) * 0.15
        
        # 淡入淡出
        fade = int(sr * 0.1)
        if i < fade:
            value *= i / fade
        elif i > total_samples - fade:
            value *= (total_samples - i) / fade
        
        samples.append(int(value * 32767 * 0.7))
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        for s in samples:
            wav.writeframes(struct.pack('<h', s))
    
    print(f"生成: {filepath} ({len(samples)/sr:.1f}s)")

def main():
    print("=" * 60)
    print("快速生成关键听力音频文件")
    print("=" * 60)
    
    # 获取听力题
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, audio_url FROM questions WHERE type = "listening" LIMIT 20')
    questions = cursor.fetchall()
    
    print(f"\n找到 {len(questions)} 道题,生成变体...\n")
    
    count = 0
    for q_id, audio_url in questions:
        if not audio_url:
            continue
        
        base_path = audio_url.lstrip('/')
        name, ext = os.path.splitext(base_path)
        
        is_japanese = 'JL' in q_id
        
        # 确定变体
        if is_japanese:
            variants = [
                ('', 440),
                ('_japanese_kanto_female_standard', 440),
                ('_japanese_kanto_male_standard', 220),
                ('_japanese_kansai_female_standard', 480),
                ('_japanese_kansai_male_standard', 240),
            ]
        else:
            variants = [
                ('', 523),
                ('_english_uk_female_standard', 523),
                ('_english_uk_male_standard', 261),
                ('_english_us_female_standard', 554),
                ('_english_us_male_standard', 277),
                ('_english_african_female_standard', 494),
                ('_english_african_male_standard', 247),
                ('_english_indian_female_standard', 587),
                ('_english_indian_male_standard', 293),
            ]
        
        # 生成所有变体
        for suffix, freq in variants:
            filepath = f"{name}{suffix}{ext}"
            if not os.path.exists(filepath):
                generate_audio(filepath, freq)
                count += 1
    
    print(f"\n完成!共生成 {count} 个音频文件")
    print("=" * 60)
    
    conn.close()

if __name__ == '__main__':
    main()
