# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
专门为 JL00023 题目生成所有音频变体
"""

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
    
    print(f"✅ 生成: {filepath} ({len(samples)/sr:.1f}s, {base_freq}Hz)")

def main():
    print("=" * 60)
    print("生成 listening_23.wav 的所有音频变体")
    print("=" * 60)
    
    base_path = 'static/audio/japanese/n4/listening_23'
    name, ext = base_path, '.wav'
    
    # 日语变体
    japanese_variants = [
        ('', 440, '默认'),
        ('_japanese_kanto_female_standard', 440, '关东腔 - 标准女声'),
        ('_japanese_kanto_male_standard', 220, '关东腔 - 标准男声'),
        ('_japanese_kansai_female_standard', 480, '关西腔 - 标准女声'),
        ('_japanese_kansai_male_standard', 240, '关西腔 - 标准男声'),
    ]
    
    print("\n🎌 日语听力音频:")
    for suffix, freq, desc in japanese_variants:
        filepath = f"{name}{suffix}{ext}"
        if not os.path.exists(filepath):
            generate_audio(filepath, freq)
            print(f"   -> {desc}")
        else:
            print(f"   ✅ 已存在: {desc}")
    
    print("\n" + "=" * 60)
    print("完成!所有音频变体已生成.")
    print("=" * 60)

if __name__ == '__main__':
    main()
