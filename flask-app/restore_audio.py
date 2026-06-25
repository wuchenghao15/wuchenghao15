#!/usr/bin/env python3
"""
MTSCOS AI Project - 音频文件恢复脚本
从ai_engines目录恢复误删的听力音频文件
"""

import os
import shutil
from pathlib import Path
import re

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

def restore_audio_files():
    """恢复音频文件"""
    print("="*60)
    print("MTSCOS AI Project - 音频文件恢复脚本")
    print("="*60)
    
    # 源目录（ai_engines备份）
    ai_engines_dir = PROJECT_ROOT / "flask-app" / "ai_engines"
    
    # 目标目录
    target_dirs = {
        'n4': PROJECT_ROOT / "flask-app" / "static" / "audio" / "japanese" / "n4",
        'n5': PROJECT_ROOT / "flask-app" / "static" / "audio" / "japanese" / "n5",
    }
    
    # 创建目标目录
    for level, target_dir in target_dirs.items():
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n创建目录: {target_dir}")
    
    # 恢复统计
    stats = {
        'total': 0,
        'n4': 0,
        'n5': 0,
        'failed': 0
    }
    
    # 扫描ai_engines目录下的音频文件
    if not ai_engines_dir.exists():
        print(f"错误: ai_engines目录不存在: {ai_engines_dir}")
        return
    
    print(f"\n扫描源目录: {ai_engines_dir}")
    
    # 匹配模式：listening_数字_japanese_...
    pattern = r'listening_(\d+)_japanese_.*\.wav'
    
    for file in os.listdir(ai_engines_dir):
        if not file.endswith('.wav'):
            continue
        
        # 提取编号
        match = re.match(pattern, file)
        if not match:
            continue
        
        num = int(match.group(1))
        
        # 根据编号分配到n4或n5（假设1-100是n5，101-200是n4）
        if num <= 100:
            level = 'n5'
        else:
            level = 'n4'
        
        # 目标文件名：listening_编号.wav
        target_filename = f"listening_{num}.wav"
        target_path = target_dirs[level] / target_filename
        
        # 复制文件
        source_path = ai_engines_dir / file
        
        try:
            shutil.copy2(source_path, target_path)
            stats[level] += 1
            stats['total'] += 1
            print(f"  ✓ 恢复: {file} -> {level}/{target_filename}")
        except Exception as e:
            stats['failed'] += 1
            print(f"  ✗ 失败: {file} - {e}")
    
    # 输出统计
    print("\n" + "="*60)
    print("恢复完成统计")
    print("="*60)
    print(f"总恢复文件数: {stats['total']}")
    print(f"  N5级别: {stats['n5']} 文件")
    print(f"  N4级别: {stats['n4']} 文件")
    print(f"失败数: {stats['failed']}")
    
    # 检查目标目录文件数
    for level, target_dir in target_dirs.items():
        if target_dir.exists():
            count = len([f for f in os.listdir(target_dir) if f.endswith('.wav')])
            print(f"\n{level}目录文件数: {count}")

if __name__ == '__main__':
    restore_audio_files()