# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建简单的音频文件占位符
实际上是创建文本文件作为示例,提示需要实际音频文件
"""
import os

def create_audio_placeholders():
    # 目录结构
    audio_dirs = [
        'static/audio/japanese/n5',
        'static/audio/english',
    ]
    
    for d in audio_dirs:
        os.makedirs(d, exist_ok=True)
    
    # 创建一些示例音频文件的占位符
    # 日语听力题
    japanese_audio_files = [
        f'listening_{i}.mp3' for i in range(1, 21)
    ]
    
    for file in japanese_audio_files:
        filepath = os.path.join('static/audio/japanese/n5', file)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write(f'这是听力音频文件 {file} 的占位符\n')
                f.write('请将实际的音频文件放在这里\n')
            print(f'创建了 {filepath}')
    
    print('\n音频占位符创建完成!')
    print('注意:这些只是文本文件,实际使用时需要替换为真实的音频文件')

if __name__ == '__main__':
    create_audio_placeholders()
