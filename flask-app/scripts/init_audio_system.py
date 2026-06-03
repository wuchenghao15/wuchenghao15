# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
音频数据初始化脚本
"""
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.audio_manager import get_audio_manager
from datetime import datetime

if __name__ == '__main__':
    print('=' * 60)
    print('初始化音频管理系统')
    print('=' * 60)
    
    manager = get_audio_manager()
    print('1. 创建音频文件占位符和目录...')
    manager.create_audio_placeholder_files()
    
    print('2. 生成示例听力题数据...')
    manager.generate_sample_listening_questions()
    
    print('3. 验证数据...')
    with manager._connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM audio_metadata')
        audio_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM questions WHERE type = ?', ('listening',))
        question_count = cursor.fetchone()[0]
    
    print(f'   - 听力题数量: {question_count}')
    print(f'   - 音频文件记录数: {audio_count}')
    
    print('\n音频管理系统初始化完成!')
    print('=' * 60)
