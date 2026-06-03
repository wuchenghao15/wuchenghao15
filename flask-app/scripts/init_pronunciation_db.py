# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
音频字库数据库初始化脚本
创建英语和日语发音素材数据库表
"""
import sqlite3
import os

DB_PATH = 'app.db'

def init_pronunciation_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建英语发音素材表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS english_pronunciation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            phonetic TEXT,
            accent TEXT NOT NULL,
            voice TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration REAL,
            sample_rate INTEGER,
            bit_rate INTEGER,
            quality TEXT DEFAULT 'standard',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 创建日语发音素材表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS japanese_pronunciation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            hiragana TEXT,
            katakana TEXT,
            romaji TEXT,
            accent TEXT NOT NULL,
            voice TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration REAL,
            sample_rate INTEGER,
            bit_rate INTEGER,
            quality TEXT DEFAULT 'standard',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 创建音频组合规则表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio_composition_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            rule_pattern TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            description TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 创建音频合成记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio_synthesis_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT NOT NULL,
            language TEXT NOT NULL,
            accent TEXT,
            voice TEXT,
            output_file_path TEXT,
            duration REAL,
            quality TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_english_type ON english_pronunciation(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_english_accent ON english_pronunciation(accent)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_japanese_type ON japanese_pronunciation(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_japanese_accent ON japanese_pronunciation(accent)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_composition_language ON audio_composition_rules(language)')
    
    conn.commit()
    conn.close()
    print("✓ 音频字库数据库表结构创建完成")

if __name__ == '__main__':
    init_pronunciation_database()