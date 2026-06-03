#!/usr/bin/env python3
"""
学习系统AI员工初始化脚本
为学习系统创建专门的AI员工配置
"""

import sqlite3
import json
from datetime import datetime

def init_learning_ai_employees():
    """初始化学习系统的AI员工"""
    
    db_path = 'mtcos_system.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 确保AI员工表存在
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            avatar TEXT,
            capabilities TEXT,
            status TEXT DEFAULT 'active',
            performance_score REAL DEFAULT 0.0,
            tasks_completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_active TEXT
        )
    ''')
    
    # 检查是否已经有学习系统的AI员工
    cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE department = '学习中心'")
    learning_center_count = cursor.fetchone()[0]
    
    if learning_center_count < 8:  # 如果不够，添加新的AI员工
        learning_employees = [
            ('学习小助手', '学习导航助手', '学习中心', '📚', 
             json.dumps(['课程推荐', '学习规划', '进度跟踪', '答疑解惑']), 94.5, 189),
            
            ('数学小博士', '数学辅导老师', '学习中心', '🔢',
             json.dumps(['数学教学', '解题指导', '错题分析', '公式讲解']), 95.2, 167),
            
            ('语文小仙女', '语文辅导老师', '学习中心', '📖',
             json.dumps(['语文教学', '阅读理解', '写作指导', '古诗文赏析']), 93.8, 145),
            
            ('英语翻译官', '英语学习顾问', '学习中心', '🌍',
             json.dumps(['英语教学', '口语练习', '听力训练', '写作批改']), 94.7, 178),
            
            ('日语达人', '日语学习教练', '学习中心', '🗾',
             json.dumps(['日语教学', 'JLPT备考', '会话练习', '文化讲解']), 92.9, 134),
            
            ('编程极客', '编程辅导老师', '学习中心', '💻',
             json.dumps(['编程教学', '代码指导', '算法讲解', '项目实战']), 96.1, 198),
            
            ('AI学习伙伴', 'AI自适应学习教练', '学习中心', '🤖',
             json.dumps(['智能辅导', '学习推荐', '进度分析', '能力评估']), 96.8, 223),
            
            ('时间规划师', '学习效率顾问', '学习中心', '⏰',
             json.dumps(['时间管理', '学习计划', '效率提升', '习惯养成']), 91.5, 87)
        ]
        
        # 插入AI员工
        for emp in learning_employees:
            cursor.execute('''
                INSERT OR REPLACE INTO ai_employees 
                (name, role, department, avatar, capabilities, performance_score, tasks_completed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', emp)
        
        print("✅ 学习系统AI员工初始化完成！")
        print(f"📊 添加了 {len(learning_employees)} 位AI学习助手")
    else:
        print("ℹ️  学习系统AI员工已存在，无需重复添加")
    
    # 显示所有学习中心的AI员工
    print("\n🎓 学习中心AI员工列表:")
    print("=" * 80)
    
    cursor.execute("SELECT name, role, avatar FROM ai_employees WHERE department = '学习中心'")
    for emp in cursor.fetchall():
        print(f"{emp[2]} {emp[0]} - {emp[1]}")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 学习系统AI员工准备就绪！")

if __name__ == '__main__':
    print("=" * 80)
    print("MTSCOS 学习系统 - AI员工初始化")
    print("=" * 80)
    init_learning_ai_employees()
