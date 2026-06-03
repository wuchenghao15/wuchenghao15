# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
更新现有的placement_test_questions表数据
添加缺失的question_type、tags和audio_url信息
"""
import sqlite3
import json
import os

DB_PATH = 'app.db'

def update_existing_test_questions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有需要更新的题目
    cursor.execute('''
        SELECT ptq.id, ptq.test_id, ptq.question_id, q.type, q.tags, q.audio_url
        FROM placement_test_questions ptq
        JOIN questions q ON ptq.question_id = q.id
        WHERE ptq.question_type IS NULL OR ptq.question_type = ''
    ''')
    
    rows = cursor.fetchall()
    
    for row in rows:
        ptq_id, test_id, question_id, q_type, q_tags, q_audio_url = row
        
        cursor.execute('''
            UPDATE placement_test_questions
            SET question_type = ?, tags = ?, audio_url = ?
            WHERE id = ?
        ''', (q_type, q_tags, q_audio_url, ptq_id))
    
    conn.commit()
    print(f'更新了 {len(rows)} 道题目的数据')
    
    # 也检查还有多少道题没有填充
    cursor.execute('''
        SELECT COUNT(*) FROM placement_test_questions 
        WHERE question_type IS NULL OR question_type = ''
    ''')
    remaining = cursor.fetchone()[0]
    print(f'还有 {remaining} 道题目需要更新')
    
    conn.close()

if __name__ == '__main__':
    update_existing_test_questions()
