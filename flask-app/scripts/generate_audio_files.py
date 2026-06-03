# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
生成简单的音频文件用于测试
使用Python的wave模块生成简单的音调
"""
import os
import wave
import struct
import math

def generate_tone(filename, frequency=440, duration=1.0, sample_rate=44100):
    """生成一个简单的正弦波音调"""
    n_samples = int(sample_rate * duration)
    
    # 生成正弦波数据
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        # 使用多个频率叠加产生更丰富的声音
        value = math.sin(2 * math.pi * frequency * t) * 0.5
        value += math.sin(2 * math.pi * frequency * 2 * t) * 0.25
        value += math.sin(2 * math.pi * frequency * 0.5 * t) * 0.25
        # 添加淡入淡出效果
        if i < n_samples * 0.1:
            value *= i / (n_samples * 0.1)
        elif i > n_samples * 0.9:
            value *= (n_samples - i) / (n_samples * 0.1)
        samples.append(int(value * 32767 * 0.8))
    
    # 写入WAV文件
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16位
        wav_file.setframerate(sample_rate)
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))
    
    return filename

def create_audio_files():
    """创建所有需要的音频文件"""
    # 定义目录和文件
    audio_dirs = {
        'static/audio/japanese/n5': 20,
        'static/audio/japanese/n4': 20,
        'static/audio/japanese/n3': 20,
        'static/audio/english/basic': 50,
        'static/audio/english/toefl': 100,
        'static/audio/english/ielts': 100,
    }
    
    # 不同的频率代表不同的"声音"
    frequencies = [262, 294, 330, 349, 392, 440, 494, 523]  # C4到C5的音阶
    
    total_created = 0
    
    for dir_path, count in audio_dirs.items():
        os.makedirs(dir_path, exist_ok=True)
        
        for i in range(1, count + 1):
            filename = os.path.join(dir_path, f'listening_{i}.wav')
            if not os.path.exists(filename):
                # 使用不同的频率和持续时间
                freq = frequencies[i % len(frequencies)]
                duration = 2.0 + (i % 5) * 0.5  # 2-4秒
                generate_tone(filename, frequency=freq, duration=duration)
                total_created += 1
                print(f'创建: {filename}')
    
    print(f'\n总共创建了 {total_created} 个音频文件')

if __name__ == '__main__':
    create_audio_files()
